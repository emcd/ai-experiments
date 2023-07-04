# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


from . import base as __


name = 'OpenAI'


def provide_models( ):
    from collections import defaultdict
    from operator import itemgetter
    import openai
    # TODO: Only call API when explicitly desired. Should persist to disk.
    model_names = sorted( map(
        itemgetter( 'id' ),
        openai.Model.list( ).to_dict_recursive( )[ 'data' ] ) )
    sysprompt_honor = defaultdict( lambda: False )
    sysprompt_honor.update( {
        #'gpt-3.5-turbo-0613': True,
        #'gpt-3.5-turbo-16k-0613': True,
        'gpt-4': True,
        'gpt-4-32k': True,
        'gpt-4-0613': True,
        'gpt-4-32k-0613': True,
    } )
    function_support = defaultdict( lambda: False )
    function_support.update( {
        'gpt-3.5-turbo-0613': True,
        'gpt-3.5-turbo-16k-0613': True,
        'gpt-4-0613': True,
        'gpt-4-32k-0613': True,
    } )
    tokens_limits = defaultdict( lambda: 4096 ) # Some are 4097... _shrug_.
    tokens_limits.update( {
        'code-davinci-002': 8000,
        'gpt-3.5-turbo-16k': 16384,
        'gpt-3.5-turbo-16k-0613': 16384,
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-4-0613': 8192,
        'gpt-4-32k-0613': 32768,
    } )
    return {
        model_name: {
            'honors-system-prompt': sysprompt_honor[ model_name ],
            'supports-functions': function_support[ model_name ],
            'tokens-limit': tokens_limits[ model_name ],
        }
        for model_name in model_names
    }


def chat( messages, special_data, controls, callbacks ):
    special_data = _canonicalize_special_data( special_data )
    controls = _canonicalize_controls( controls )
    from openai import ChatCompletion, OpenAIError
    try:
        response = ChatCompletion.create(
            messages = messages, **special_data, **controls )
    except OpenAIError as exc:
        callbacks.failure_notifier( f"Error: {exc}" )
        raise __.ChatCompletionError( f"Error: {exc}" ) from exc
    if not controls.get( 'stream', True ):
        message = response.choices[ 0 ].message
        if 'content' in message:
            handle = callbacks.allocator( 'text/markdown' )
            callbacks.updater( handle, message.content )
        elif 'function_call' in message:
            handle = callbacks.allocator( 'application/json' )
            callbacks.updater(
                handle, _reconstitute_function_call( message.function_call ) )
        return handle
    try: # streaming mode
        chunk0 = next( response )
        delta = chunk0.choices[ 0 ].delta
        if delta.get( 'function_call' ):
            handle = callbacks.allocator( 'application/json' )
            _gather_function_chunks( chunk0, response, handle, callbacks )
        else:
            handle = callbacks.allocator( 'text/markdown' )
            _stream_content_chunks( chunk0, response, handle, callbacks )
    except OpenAIError as exc:
        callbacks.deallocator( handle )
        callbacks.failure_notifier( f"Error: {exc}" )
        raise __.ChatCompletionError( f"Error: {exc}" ) from exc
    return handle


def _canonicalize_controls( controls ):
    nomargs = {
        name: value for name, value in controls.items( )
        if name in ( 'model', 'temperature', )
    }
    nomargs[ 'stream' ] = True
    return nomargs


def _canonicalize_special_data( data ):
    nomargs = { }
    if 'ai-functions' in data:
        nomargs[ 'functions' ] = data[ 'ai-functions' ]
    return nomargs


def _gather_function_chunks( chunk0, response, handle, callbacks ):
    from collections import defaultdict
    from itertools import chain
    function_call = defaultdict( str )
    for chunk in chain( ( chunk0, ), response ):
        delta = chunk.choices[ 0 ].delta
        if not delta: break
        if 'name' in delta.function_call:
            function_call[ 'name' ] = delta.function_call[ 'name' ]
        if 'arguments' in delta.function_call:
            function_call[ 'arguments' ] += delta.function_call[ 'arguments' ]
    callbacks.updater( handle, _reconstitute_function_call( function_call ) )


def _reconstitute_function_call( function_call ):
    from json import dumps, loads
    function_call[ 'arguments' ] = loads( function_call[ 'arguments' ] )
    return dumps( function_call )


def _stream_content_chunks( chunk0, response, handle, callbacks ):
    from itertools import chain
    for chunk in chain( ( chunk0, ), response ):
        delta = chunk.choices[ 0 ].delta
        if not delta: break
        if not delta.get( 'content' ): continue
        callbacks.updater( handle, delta.content )
