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


''' Implemenation of OpenAI AI provider. '''


from . import __
from . import core as _core


class Provider( _core.Provider ):
    ''' Model management, etc... '''

    name = 'openai' # TODO: Derive from subpackage.
    proper_name = 'OpenAI'


# TODO: Maintain models with ModelsManager class.
#       Use RegenerativeDictionary with populator function.
_models = { }


def access_model_data( model_name, data_name ):
    return _models[ model_name ][ data_name ]


def chat( messages, special_data, controls, callbacks ):
    messages = _nativize_messages( messages, controls[ 'model' ] )
    special_data = _nativize_special_data( special_data, controls )
    controls = _nativize_controls( controls )
    response = _chat( messages, special_data, controls, callbacks )
    if controls.get( 'stream', True ):
        return _process_iterative_chat_response( response, callbacks )
    return _process_complete_chat_response( response, callbacks )


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
    for message in _nativize_messages( messages, model_name ):
        tokens_count += tokens_per_message
        for index, value in message.items( ):
            value_ = value if isinstance( value, str ) else dumps( value )
            tokens_count += count_text_tokens( value_, model_name )
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


def extract_invocation_requests( canister, auxdata, ai_functions ):
    from ..codecs.json import loads
    try: requests = loads( canister[ 0 ].data )
    except Exception as exc:
        raise ValueError( 'Malformed JSON payload in message.' ) from exc
    if not isinstance( requests, __.AbstractSequence ):
        raise ValueError( 'Function invocation requests is not sequence.' )
    model_context = getattr( canister.attributes, 'model_context', { } )
    tool_calls = model_context.get( 'tool_calls' )
    for i, request in enumerate( requests ):
        if not isinstance( request, __.AbstractDictionary ):
            raise ValueError(
                'Function invocation request is not dictionary.' )
        if 'name' not in request:
            raise ValueError(
                'Function name is absent from invocation request.' )
        name = request[ 'name' ]
        if name not in ai_functions:
            raise ValueError( 'Function name in request is not available.' )
        arguments = request.get( 'arguments', { } )
        request[ 'invocable__' ] = __.partial_function(
            ai_functions[ name ], auxdata, **arguments )
        if tool_calls: request[ 'context__' ] = tool_calls[ i ]
    return requests


def invoke_function( request, controls ):
    from ..messages.core import Canister
    request_context = request[ 'context__' ]
    result = request[ 'invocable__' ]( )
    if 'id' in request_context:
        result_context = dict(
            name = request_context[ 'function' ][ 'name' ],
            role = 'tool',
            tool_call_id = request_context[ 'id' ],
        )
    else: result_context = dict( name = request[ 'name' ], role = 'function' )
    mimetype, message = render_data( result, controls )
    canister = Canister( 'Function' )
    canister.add_content( message, mimetype = mimetype )
    canister.attributes.model_context = result_context
    return canister


async def prepare( auxdata ):
    from os import environ
    if 'OPENAI_API_KEY' not in environ:
        raise LookupError( "Missing 'OPENAI_API_KEY'." )
    # TODO: Warn on missing 'OPENAI_ORG_ID' and 'OPENAI_PROJECT_ID'.
    _models.update( await _cache_acquire_models( auxdata ) )
    return Provider( )


def provide_chat_models( ):
    return {
        name: attributes for name, attributes in _models.items( )
        if name.startswith( ( 'gpt-3.5-turbo', 'gpt-4', ) )
           and not name.startswith( ( 'gpt-3.5-turbo-instruct', ) )
    }


def provide_format_mime_type( controls ): return 'application/json'


def provide_format_name( controls ): return 'JSON'


def parse_data( content, controls ):
    mime_type = provide_format_mime_type( controls )
    if 'application/json' == mime_type:
        from ..codecs.json import loads
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
    # TODO: Merge configuration on provider instantiation.
    try:
        return (
            configuration[ 'providers' ][ Provider.name ][ 'default-model' ] )
    except KeyError: pass
    for model_name in ( 'gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo', ):
        if model_name in models: return model_name
    return next( iter( models ) )


async def _cache_acquire_models( auxdata ):
    from json import dumps, loads
    from aiofiles import open as open_
    path = auxdata.provide_cache_location(
        'providers', Provider.name, 'models.json' )
    if path.is_file( ):
        # TODO: Get cache expiration interval from configuration.
        interval = __.TimeDelta( seconds = 4 * 60 * 60 ) # 4 hours
        then = ( __.DateTime.now( __.TimeZone.utc ) - interval ).timestamp( )
        if path.stat( ).st_mtime > then:
            async with open_( path ) as file:
                return loads( await file.read( ) )
    models = await _discover_models_from_api( )
    path.parent.mkdir( exist_ok = True, parents = True )
    async with open_( path, 'w' ) as file:
        await file.write( dumps( models, indent = 4 ) )
    return models


def _chat( messages, special_data, controls, callbacks ):
    # TODO: Operate asynchronously.
    # TODO? Remove rate limit handling, since newer client does this.
    from time import sleep
    from openai import OpenAI, OpenAIError, RateLimitError
    from .core import ChatCompletionError
    client = OpenAI( ) # TODO: Use async client.
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
            raise ChatCompletionError( f"Error: {exc}" ) from exc
    raise ChatCompletionError(
        f"Exhausted {attempts_limit} retries with OpenAI API." )


def _create_canister_from_response( response ):
    from ..messages.core import Canister
    attributes = __.SimpleNamespace( behaviors = [ ] )
    if response.content: mimetype = 'text/markdown'
    else:
        mimetype = 'application/json'
        attributes.response_class = 'invocation'
    return Canister(
        role = 'AI', attributes = attributes ).add_content(
            '', mimetype = mimetype )


# TODO: Move attribute associations to data file.
# https://platform.openai.com/docs/guides/function-calling/supported-models
_function_support_models = frozenset( (
    'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
    'gpt-4', 'gpt-4-32k', 'gpt-4-turbo', 'gpt-4o',
    'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0125',
    'gpt-3.5-turbo-16k-0613',
    'gpt-4-0613', 'gpt-4-1106-preview', 'gpt-4-0125-preview',
    'gpt-4-32k-0613',
    'gpt-4-vision-preview', 'gpt-4-1106-vision-preview',
    'gpt-4-turbo-2024-04-09', 'gpt-4-turbo-preview',
    'gpt-4o-2024-05-13',
) )
_multifunction_support_models = frozenset( (
    'gpt-3.5.-turbo', 'gpt-4-turbo', 'gpt-4o',
    'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0125',
    'gpt-4-1106-preview', 'gpt-4-0125-preview',
    'gpt-4-vision-preview', 'gpt-4-1106-vision-preview',
    'gpt-4-turbo-2024-04-09', 'gpt-4-turbo-preview',
    'gpt-4o-2024-05-13',
) )
# https://platform.openai.com/docs/models
_model_family_context_window_sizes = __.DictionaryProxy( {
    'gpt-3.5-turbo': 16_385,
    'gpt-4-32k': 32_768,
    'gpt-4-0125': 128_000,
    'gpt-4-1106': 128_000,
    'gpt-4-turbo': 128_000,
    'gpt-4-vision': 128_000,
    'gpt-4o': 128_000,
} )
_model_context_window_sizes = {
    'gpt-3.5-turbo-0301': 4_096,
    'gpt-3.5-turbo-0613': 4_096,
}
async def _discover_models_from_api( ):
    from operator import attrgetter
    from accretive import ProducerDictionary
    from openai import AsyncOpenAI
    model_names = sorted( map(
        attrgetter( 'id' ), ( await AsyncOpenAI( ).models.list( ) ).data ) )
    # TODO? Reevaluate current status 3.5 Turbo sysprompt adherence.
    sysprompt_honor = ProducerDictionary( lambda: False )
    sysprompt_honor.update( {
        #'gpt-3.5-turbo-0613': True,
        #'gpt-3.5-turbo-16k-0613': True,
        model_name: True for model_name in model_names
        if model_name.startswith( 'gpt-4' ) } )
    function_support = ProducerDictionary( lambda: False )
    function_support.update( {
        model_name: True for model_name in model_names
        if model_name in _function_support_models } )
    multifunction_support = ProducerDictionary( lambda: False )
    multifunction_support.update( {
        model_name: True for model_name in model_names
        if model_name in _multifunction_support_models } )
    # Legacy 'gpt-3.5-turbo' has a 4096 tokens limit.
    tokens_limits = ProducerDictionary( lambda: 4096 )
    for model_name in model_names:
        if model_name in _model_context_window_sizes:
            tokens_limits[ model_name ] = (
                _model_context_window_sizes[ model_name ] )
            continue
        for model_family_name, tokens_limit \
        in _model_family_context_window_sizes.items( ):
            if model_name.startswith( model_family_name ):
                tokens_limits[ model_name ] = tokens_limit
    return {
        model_name: {
            'honors-system-prompt': sysprompt_honor[ model_name ],
            'supports-functions': function_support[ model_name ],
            'supports-multifunctions': multifunction_support[ model_name ],
            'tokens-limit': tokens_limits[ model_name ],
        }
        for model_name in model_names
    }


def _gather_tool_call_chunks_legacy( canister, response, handle, callbacks ):
    from collections import defaultdict
    tool_call = defaultdict( str )
    for chunk in response:
        delta = chunk.choices[ 0 ].delta
        if not delta: break # TODO: Look for non-null finish reason.
        if not delta.function_call: break
        if delta.function_call.name:
            tool_call[ 'name' ] = delta.function_call.name
        if delta.function_call.arguments:
            tool_call[ 'arguments' ] += delta.function_call.arguments
    canister.attributes.model_context = tool_call
    canister[ 0 ].data = _reconstitute_invocation_legacy( tool_call )
    callbacks.updater( handle )


def _gather_tool_calls_chunks( canister, response, handle, callbacks ):
    from collections import defaultdict
    tool_calls = [ ]
    index = 0
    start = True # TODO: Look for non-null finish reason.
    for chunk in response:
        delta = chunk.choices[ 0 ].delta # TODO: Handle array of responses.
        if not delta: break
        if not delta.tool_calls:
            if start: continue # Can have a blank chunk at start.
            break
        start = False
        tool_call = delta.tool_calls[ 0 ]
        index = tool_call.index
        if index == len( tool_calls ):
            tool_calls.append( {
                'type': 'function', 'function': defaultdict( str ) } )
        tool_calls[ index ][ 'type' ] = 'function'
        if tool_call.id: tool_calls[ index ][ 'id' ] = tool_call.id
        if tool_call.function:
            function = tool_calls[ index ][ 'function' ]
            if tool_call.function.name:
                function[ 'name' ] = tool_call.function.name
            if tool_call.function.arguments:
                function[ 'arguments' ] += tool_call.function.arguments
    canister.attributes.model_context = dict( tool_calls = tool_calls )
    canister[ 0 ].data = _reconstitute_invocations( tool_calls )
    callbacks.updater( handle )


def _merge_messages_contingent( canister, message, model_name ):
    # TODO: Take advantage of array syntax for content in OpenAI API,
    #       rather than merging strings. Will need to do this for image data
    #       anyway; might be able to do this for text data for consistency.
    if 'user' != message[ 'role' ]: return False
    # TODO: Handle content arrays.
    content = canister[ 0 ].data
    if 'Document' == canister.role:
        # Merge document into previous user message.
        message[ 'content' ] = '\n\n'.join( (
            message[ 'content' ],
            '## Supplemental Information ##',
            content ) )
        return True
    if 'Human' == canister.role:
        # Merge adjacent user messages.
        message[ 'content' ] = '\n\n'.join( (
            message[ 'content' ], content ) )
        return True
    return False


def _nativize_controls( controls ):
    nomargs = {
        name: value for name, value in controls.items( )
        if name in ( 'model', 'temperature', )
    }
    nomargs[ 'stream' ] = True
    return nomargs


def _nativize_messages( canisters, model_name ):
    messages = [ ]
    for canister in canisters:
        if messages and _merge_messages_contingent(
            canister, messages[ -1 ], model_name
        ): continue
        # TODO: Handle content arrays.
        content = canister[ 0 ].data
        attributes = canister.attributes
        context = getattr( attributes, 'model_context', { } ).copy( )
        role = context.get( 'role' )
        if not role:
            role = _nativize_message_role( canister, model_name )
            context[ 'role' ] = role
        if 'assistant' == role:
            content, extra_context = (
                _nativize_multifunction_invocation_contingent( canister ) )
            context.update( extra_context )
        messages.append( dict( content = content, **context ) )
    return messages


def _nativize_message_role( canister, model_name ):
    if 'Supervisor' == canister.role:
        if access_model_data( model_name, 'honors-system-prompt' ):
            return 'system'
        return 'user'
    if 'Function' == canister.role: # Context probably overrides.
        if access_model_data( model_name, 'supports-multifunctions' ):
            return 'tool'
        if access_model_data( model_name, 'supports-functions' ):
            return 'function'
    if canister.role in ( 'Human', 'Document', 'Function' ): return 'user'
    if 'AI' == canister.role: return 'assistant'
    raise ValueError( f"Invalid role '{canister.role}'." )


def _nativize_multifunction_invocation_contingent( canister ):
    attributes = canister.attributes
    content = canister[ 0 ].data
    if 'invocation' == getattr( attributes, 'response_class', '' ):
        if hasattr( attributes, 'model_context' ):
            if 'tool_calls' in attributes.model_context:
                return None, attributes.model_context
    return content, { }


def _nativize_special_data( data, controls ):
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


def _process_complete_chat_response( response, callbacks ):
    # TODO: Handle response arrays.
    message = response.choices[ 0 ].message
    canister = _create_canister_from_response( message )
    handle = callbacks.allocator( canister )
    if message.content: canister[ 0 ].data = message.content
    # TODO: Remap batch response invocations to intermediate dictionaries.
    # TODO: Separate 'model_context' attribute and content.
    elif message.function_call:
        canister[ 0 ].data = _reconstitute_invocation_legacy(
            message.function_call )
    elif message.tool_calls:
        canister[ 0 ].data = _reconstitute_invocations( message.tool_calls )
    callbacks.updater( handle )
    return handle


def _process_iterative_chat_response( response, callbacks ):
    # TODO: Handle response arrays.
    from openai import OpenAIError
    from itertools import chain
    from .core import ChatCompletionError
    handle = None
    try:
        chunks = [ ]
        while True:
            try: chunk = next( response )
            except StopIteration as exc:
                raise ChatCompletionError(
                    'Error: Empty response from AI.' ) from exc
            chunks.append( chunk )
            delta = chunk.choices[ 0 ].delta
            if delta.content or delta.function_call or delta.tool_calls: break
        response_ = chain( chunks, response )
        canister = _create_canister_from_response( delta )
        handle = callbacks.allocator( canister )
        if delta.tool_calls:
            _gather_tool_calls_chunks( canister, response_, handle, callbacks )
        elif delta.function_call:
            _gather_tool_call_chunks_legacy(
                canister, response_, handle, callbacks )
        else: _stream_content_chunks( canister, response_, handle, callbacks )
    except OpenAIError as exc:
        if handle: callbacks.deallocator( handle )
        raise ChatCompletionError( f"Error: {exc}" ) from exc
    return handle


def _reconstitute_invocation_legacy( invocation ):
    from json import dumps, loads
    return dumps( [ dict(
        name = invocation[ 'name' ],
        arguments = loads( invocation[ 'arguments' ] ),
    ) ] )


def _reconstitute_invocations( invocations ):
    from json import dumps, loads
    invocations_ = [ ]
    for invocation in invocations:
        function = invocation[ 'function' ]
        invocations_.append( dict(
            name = function[ 'name' ],
            arguments = loads( function[ 'arguments' ] ),
        ) )
    return dumps( invocations_ )


def _stream_content_chunks( canister, response, handle, callbacks ):
    # TODO: Handle content arrays.
    for chunk in response:
        delta = chunk.choices[ 0 ].delta
        # TODO: Detect finish reason.
        if not delta: break
        if not delta.content: continue
        canister[ 0 ].data += delta.content
        callbacks.updater( handle )
