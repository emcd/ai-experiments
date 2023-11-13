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
    special_data = _canonicalize_special_data( special_data, controls )
    controls = _canonicalize_controls( controls )
    response = _chat( messages, special_data, controls, callbacks )
    if not controls.get( 'stream', True ):
        message = response.choices[ 0 ].message
        if message.content:
            handle = callbacks.allocator( 'text/markdown' )
            callbacks.updater( handle, message.content )
        elif message.function_call:
            handle = callbacks.allocator( 'application/json' )
            callbacks.updater(
                handle, _reconstitute_invocations(
                    [ message.function_call ] ) )
        # TODO: Map tool calls array to invocations format.
        return handle
    from openai import OpenAIError
    from itertools import chain
    try: # streaming mode
        chunks = [ ]
        while True:
            chunk = next( response )
            chunks.append( chunk )
            delta = chunk.choices[ 0 ].delta
            if delta.content: break
            elif delta.function_call: break
            elif delta.tool_calls: break
        response_ = chain( chunks, response )
        if delta.tool_calls:
            handle = callbacks.allocator( 'application/json' )
            _gather_tool_calls_chunks( response_, handle, callbacks )
        elif delta.function_call:
            handle = callbacks.allocator( 'application/json' )
            _gather_tool_call_chunks_legacy( response_, handle, callbacks )
        else:
            handle = callbacks.allocator( 'text/markdown' )
            _stream_content_chunks( response_, handle, callbacks )
    except OpenAIError as exc:
        callbacks.deallocator( handle )
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
            if not isinstance( value, str ): value = dumps( value )
            tokens_count += count_text_tokens( value, model_name )
            if 'name' == index: tokens_count += tokens_per_name
    for function in special_data.get( 'ai-functions', [ ] ):
        tokens_count += count_text_tokens( dumps( function ), model_name )
        # TODO: Determine if metadata from multifunctions adds more tokens.
    return tokens_count


def count_text_tokens( text, model_name ):
    from tiktoken import encoding_for_model, get_encoding
    try: encoding = encoding_for_model( model_name )
    # TODO: Warn about unknown model via callback.
    except KeyError: encoding = get_encoding( 'cl100k_base' )
    return len( encoding.encode( text ) )


def extract_invocation_requests( message, auxdata, ai_functions ):
    from ...codecs.json import loads
    try: requests = loads( message )
    except: raise ValueError( 'Malformed JSON payload in message.' )
    if not isinstance( requests, __.AbstractDictionary ):
        raise ValueError( 'Function invocation requests is not dictionary.' )
    if 'tool_calls' in requests: requests = requests[ 'tool_calls' ]
    elif 'name' in requests: requests = [ requests ]
    for request in requests:
        if not isinstance( request, __.AbstractDictionary ):
            raise ValueError(
                'Function invocation request is not dictionary.' )
        if 'function' in request: function = request[ 'function' ]
        else: function = request
        if 'name' not in function:
            raise ValueError(
                'Function name is absent from invocation request.' )
        name = function[ 'name' ]
        if name not in ai_functions:
            raise ValueError( 'Function name in request is not available.' )
        arguments = function.get( 'arguments', { } )
        request[ 'invocable__' ] = __.partial_function(
            ai_functions[ name ], auxdata, **arguments )
    return requests


def invoke_function( request, controls ):
    result = request[ 'invocable__' ]( )
    if 'id' in request:
        context = dict(
            name = request[ 'function' ][ 'name' ],
            role = 'tool',
            tool_call_id = request[ 'id' ],
        )
    else: context = dict( name = request[ 'name' ], role = 'function' )
    mime_type, message = render_data( result, controls )
    control = __.SimpleNamespace( context = context, mime_type = mime_type )
    return control, message


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


def provide_format_mime_type( controls ): return 'application/json'


def provide_format_name( controls ): return 'JSON'


def parse_data( content, controls ):
    mime_type = provide_format_mime_type( controls )
    if 'application/json' == mime_type:
        from chatter.codecs.json import loads
        text = loads( content )
    else: raise NotImplementedError( f"Cannot parse '{mime_type}'." )
    return text


def render_data( content, controls ):
    mime_type = provide_format_mime_type( controls )
    if 'application/json' == mime_type:
        from json import dumps
        text = dumps( content )
    else: raise NotImplementedError( f"Cannot render '{mime_type}' as text." )
    return mime_type, text


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
    from json import dumps, loads
    messages = [ ]
    for ix_message in ix_messages:
        if messages and _merge_canonical_messages_contingent(
            ix_message, messages[ -1 ], model_name
        ): continue
        content = ix_message[ 'content' ]
        context = ix_message.get( 'context', { } ).copy( )
        if 'role' not in context:
            context[ 'role' ] = _canonicalize_message_role(
                ix_message, model_name )
        # Hack for reconstituting AI-recognized tools calls.
        if 'assistant' == context[ 'role' ]:
            try: tool_calls = loads( content )
            except: pass
            else:
                if 'tool_calls' in tool_calls:
                    for tool_call in tool_calls[ 'tool_calls' ]:
                        tool_call[ 'function' ][ 'arguments' ] = (
                            dumps( tool_call[ 'function' ][ 'arguments' ] ) )
                    context.update( tool_calls )
                    content = None
        messages.append( dict( content = content, **context ) )
    return messages


def _canonicalize_message_role( ix_message, model_name ):
    ix_role = ix_message[ 'role' ]
    if 'Supervisor' == ix_role:
        if access_model_data( model_name, 'honors-system-prompt' ):
            return 'system'
        return 'user'
    if 'Function' == ix_role: # Context probably overrides.
        if access_model_data( model_name, 'supports-multifunctions' ):
            return 'tool'
        if access_model_data( model_name, 'supports-functions' ):
            return 'function'
    if ix_role in ( 'Human', 'Document', 'Function' ): return 'user'
    if 'AI' == ix_role: return 'assistant'
    raise ValueError( f"Invalid role '{ix_role}'." )


def _canonicalize_special_data( data, controls ):
    model_name = controls[ 'model' ]
    nomargs = { }
    if 'ai-functions' in data:
        if access_model_data( model_name, 'supports-multifunctions' ):
            nomargs[ 'tools' ] = [
                { 'type': 'function', 'function': function }
                for function in data[ 'ai-functions' ] ]
        elif access_model_data( model_name, 'supports-functions' ):
            nomargs[ 'functions' ] = data[ 'ai-functions' ]
    return nomargs


def _chat( messages, special_data, controls, callbacks ):
    from time import sleep
    from openai import OpenAI, OpenAIError, RateLimitError
    client = OpenAI( ) # TODO: Cache client.
    attempts_limit = 3
    for attempts_count in range( attempts_limit ):
        try:
            return client.chat.completions.create(
                messages = messages, **special_data, **controls )
        except RateLimitError as exc:
            ic( exc )
            ic( dir( exc ) )
            sleep( 30 ) # TODO: Use retry value from exception.
            continue
        except OpenAIError as exc:
            raise __.ChatCompletionError( f"Error: {exc}" ) from exc
    raise __.ChatCompletionError(
        f"Exhausted {attempts_limit} retries with OpenAI API." )


def _gather_tool_call_chunks_legacy( response, handle, callbacks ):
    from collections import defaultdict
    tool_call = defaultdict( str )
    for chunk in response:
        delta = chunk.choices[ 0 ].delta
        if not delta: break
        if not delta.function_call: break
        if delta.function_call.name:
            tool_call[ 'name' ] = delta.function_call.name
        if delta.function_call.arguments:
            tool_call[ 'arguments' ] += delta.function_call.arguments
    callbacks.updater( handle, _reconstitute_invocation_legacy( tool_call ) )


def _gather_tool_calls_chunks( response, handle, callbacks ):
    from collections import defaultdict
    tool_calls = [ ]
    index = 0
    start = True
    for chunk in response:
        delta = chunk.choices[ 0 ].delta
        if not delta: break
        if not delta.tool_calls:
            if start: continue # Can have a blank chunk at start.
            else: break
        start = False
        tool_call = delta.tool_calls[ 0 ]
        index = tool_call.index
        if index == len( tool_calls ):
            tool_calls.append( {
                'type': 'function', 'function': defaultdict( str ) } )
        tool_calls[ index ][ 'type' ] = 'function'
        if tool_call.id:
            tool_calls[ index ][ 'id' ] = tool_call.id
        if tool_call.function:
            function = tool_calls[ index ][ 'function' ]
            if tool_call.function.name:
                function[ 'name' ] = tool_call.function.name
            if tool_call.function.arguments:
                function[ 'arguments' ] += tool_call.function.arguments
    callbacks.updater( handle, _reconstitute_invocations( {
        'tool_calls': tool_calls } ) )


def _merge_canonical_messages_contingent( ix_message, message, model_name ):
    if 'user' != message[ 'role' ]: return False
    ix_role = ix_message[ 'role' ]
    if 'Document' == ix_role:
        # Merge document into previous user message.
        # TODO? Convert to MIME-like format. Update sysprompt accordingly.
        message[ 'content' ] = '\n\n'.join( (
            message[ 'content' ],
            '## Supplemental Information ##',
            ix_message[ 'content' ] ) )
        return True
    if 'Human' == ix_role and not access_model_data(
        model_name, 'allows-adjacent-users'
    ):
        # Merge adjacent user messages, if model rejects them.
        message[ 'content' ] = '\n\n'.join( (
            message[ 'content' ], ix_message[ 'content' ] ) )
        return True
    return False


def _provide_models( ):
    if _models: return _models.copy( )
    from collections import defaultdict
    from operator import attrgetter
    import openai
    # TODO: Only call API when explicitly desired. Should persist to disk.
    model_names = sorted( map(
        attrgetter( 'id' ), openai.models.list( ).data ) )
    adjacent_users = defaultdict( lambda: False )
    adjacent_users.update( {
        model_name: True for model_name in model_names
        if model_name.startswith( 'gpt-3.5-turbo' ) } )
    sysprompt_honor = defaultdict( lambda: False )
    sysprompt_honor.update( {
        #'gpt-3.5-turbo-0613': True,
        #'gpt-3.5-turbo-16k-0613': True,
        model_name: True for model_name in model_names
        if model_name.startswith( 'gpt-4' ) } )
    function_support = defaultdict( lambda: False )
    function_support.update( {
        model_name: True for model_name in model_names
        if model_name.endswith( ( '-0613', '-1106', '-preview', ) )
           or model_name in ( 'gpt-4', 'gpt-4-32k', ) } )
    multifunction_support = defaultdict( lambda: False )
    multifunction_support.update( {
        model_name: True for model_name in model_names
        if model_name.endswith( ( '-1106', '-preview', ) ) } )
    # Some of the legacy models have 4097 or 8001 tokens limits,
    # but we ignore them. 'gpt-3.5-turbo' has a 4096 tokens limit.
    tokens_limits = defaultdict( lambda: 4096 )
    tokens_limits.update( {
        'code-davinci-002': 8001,
        'gpt-3.5-turbo-16k': 16385,
        'gpt-3.5-turbo-16k-0613': 16385,
        'gpt-3.5-turbo-1106': 16385,
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-4-0613': 8192,
        'gpt-4-32k-0613': 32768,
        'gpt-4-1106-preview': 128000,
        'gpt-4-vision-preview': 128000,
    } )
    return {
        model_name: {
            'allows-adjacent-users': adjacent_users[ model_name ],
            'honors-system-prompt': sysprompt_honor[ model_name ],
            'supports-functions': function_support[ model_name ],
            'supports-multifunctions': multifunction_support[ model_name ],
            'tokens-limit': tokens_limits[ model_name ],
        }
        for model_name in model_names
    }


def _reconstitute_invocation_legacy( invocation ):
    from json import dumps, loads
    invocation[ 'arguments' ] = loads( invocation[ 'arguments' ] )
    return dumps( invocation )


def _reconstitute_invocations( invocations ):
    from json import dumps, loads
    for invocation in invocations[ 'tool_calls' ]:
        function = invocation[ 'function' ]
        function[ 'arguments' ] = loads( function[ 'arguments' ] )
    return dumps( invocations )


def _stream_content_chunks( response, handle, callbacks ):
    for chunk in response:
        delta = chunk.choices[ 0 ].delta
        if not delta: break
        if not delta.content: continue
        callbacks.updater( handle, delta.content )
