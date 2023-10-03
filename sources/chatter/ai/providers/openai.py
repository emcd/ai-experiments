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


_NAME = 'OpenAI'


_models = { } # TODO: Hide models cache in closure cell.


def access_model_data( model_name, data_name ):
    return _models[ model_name ][ data_name ]


def chat( messages, special_data, controls, callbacks ):
    messages = _canonicalize_messages( messages, controls[ 'model' ] )
    special_data = _canonicalize_special_data( special_data )
    controls = _canonicalize_controls( controls )
    response = _chat( messages, special_data, controls, callbacks )
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
    from openai import OpenAIError
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



def count_conversation_tokens( messages, special_data, controls ):
    from json import dumps
    model_name = controls[ 'model' ]
    # Adapted from https://github.com/openai/openai-cookbook/blob/2e9704b3b34302c30174e7d8e7211cb8da603ca9/examples/How_to_count_tokens_with_tiktoken.ipynb
    if 'gpt-3.5-turbo-0301' == model_name:
        tokens_per_message, tokens_per_name = 4, -1
    elif model_name in (
        'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k-0613',
        'gpt-4-0314', 'gpt-4-32k-0314',
        'gpt-4-0613', 'gpt-4-32k-0613',
    ):
        tokens_per_message, tokens_per_name = 3, 1
    elif model_name.startswith( ( 'gpt-3.5-turbo', 'gpt-4', ) ):
        # TODO: Use callback to warn about unknown model.
        tokens_per_message, tokens_per_name = 3, 1
    else: raise NotImplementedError( f"Unsupported model: {model_name}" )
    tokens_count = 0
    for message in _canonicalize_messages( messages, model_name ):
        tokens_count += tokens_per_message
        for index, value in message.items( ):
            tokens_count += count_text_tokens( value, model_name )
            if 'name' == index: tokens_count += tokens_per_name
    for function in special_data.get( 'ai-functions', [ ] ):
        tokens_count += count_text_tokens( dumps( function ), model_name )
    return tokens_count


def count_text_tokens( text, model_name ):
    from tiktoken import encoding_for_model, get_encoding
    try: encoding = encoding_for_model( model_name )
    # TODO: Warn about unknown model via callback.
    except KeyError: encoding = get_encoding( 'cl100k_base' )
    return len( encoding.encode( text ) )


def prepare( configuration, directories ):
    from os import environ as cpe  # current process environment
    if 'OPENAI_API_KEY' in cpe:
        import openai
        openai.api_key = cpe[ 'OPENAI_API_KEY' ]
        if 'OPENAI_ORGANIZATION_ID' in cpe:
            openai.organization = cpe[ 'OPENAI_ORGANIZATION_ID' ]
    else: raise LookupError( f"Missing 'OPENAI_API_KEY'." )
    _models.update( _provide_models( ) )
    return _NAME


def provide_chat_models( ):
    return {
        name: attributes for name, attributes in _models.items( )
        if name.startswith( ( 'gpt-3.5-turbo', 'gpt-4', ) )
    }


def provide_format_name( controls ):
    return 'JSON'


def render_data( content, controls ):
    from json import dumps
    return dumps( content )


def select_default_model( models, auxdata ):
    configuration = auxdata.configuration
    try:
        return configuration[
            'providers' ][ _NAME.lower( ) ][ 'default-model' ]
    except KeyError: pass
    for model_name in ( 'gpt-4', 'gpt-3.5.-turbo-16k', 'gpt-3.5-turbo', ):
        if model_name in models: return model_name
    return next( iter( models ) )


def _canonicalize_controls( controls ):
    nomargs = {
        name: value for name, value in controls.items( )
        if name in ( 'model', 'temperature', )
    }
    nomargs[ 'stream' ] = True
    return nomargs


def _canonicalize_messages( ix_messages, model_name ):
    honors_sysprompt = _models[ model_name ][ 'honors-system-prompt' ]
    supports_functions = _models[ model_name ][ 'supports-functions' ]
    messages = [ ]
    for ix_message in ix_messages:
        ix_role = ix_message[ 'role' ]
        if 'Supervisor' == ix_role:
            role = 'system' if honors_sysprompt else 'user'
        elif supports_functions and 'Function' == ix_role:
            role = 'function'
        elif ix_role in ( 'Human', 'Document', 'Function' ):
            role = 'user'
        else: role = 'assistant'
        name = ix_message.get( 'actor-name' )
        # Merge messages if role and name are the same.
        if (    messages
            and role == messages[ -1 ][ 'role' ]
            and name == messages[ -1 ].get( 'name' )
        ):
            message = messages[ -1 ]
            message[ 'content' ] = '\n\n'.join( (
                message[ 'content' ], ix_message[ 'content' ] ) )
        # Merge document into previous user message.
        # TODO: Convert to MIME-like format and update sysprompt accordingly.
        elif (    messages
              and 'user' == messages[ -1 ][ 'role' ]
              and 'Document' == ix_role
        ):
            message = messages[ -1 ]
            message[ 'content' ] = '\n\n'.join( (
                message[ 'content' ],
                '## Supplemental Information ##',
                ix_message[ 'content' ] ) )
        # Else, create and append new message.
        else:
            message = dict( content = ix_message[ 'content' ], role = role )
            if 'actor-name' in ix_message:
                message[ 'name' ] = ix_message[ 'actor-name' ]
            messages.append( message )
    return messages


def _canonicalize_special_data( data ):
    nomargs = { }
    if 'ai-functions' in data:
        nomargs[ 'functions' ] = data[ 'ai-functions' ]
    return nomargs


def _chat( messages, special_data, controls, callbacks ):
    from time import sleep
    from openai import ChatCompletion, OpenAIError
    from openai.error import RateLimitError
    attempts_limit = 3
    for attempts_count in range( attempts_limit ):
        try:
            return ChatCompletion.create(
                messages = messages, **special_data, **controls )
        except RateLimitError as exc:
            ic( exc )
            ic( dir( exc ) )
            sleep( 30 ) # TODO: Use retry value from exception.
            continue
        except OpenAIError as exc:
            callbacks.failure_notifier( f"Error: {exc}" )
            raise __.ChatCompletionError( f"Error: {exc}" ) from exc
    error = f"Exhausted {attempts_limit} retries with OpenAI API."
    callbacks.failure_notifier( error )
    raise __.ChatCompletionError( error )


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


def _provide_models( ):
    if _models: return _models.copy( )
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
