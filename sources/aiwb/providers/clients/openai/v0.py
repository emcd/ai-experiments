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


''' "Legacy" implementation of interface to OpenAI. '''
# TODO: Replace this module with per-client and per-model methods.


from . import __


models_ = { }


def access_model_data( model_name, data_name ):
    return models_[ model_name ][ data_name ]


async def chat( messages, special_data, controls, callbacks ):
    model = controls[ 'model' ]
    messages = _nativize_messages( messages, controls[ 'model' ] )
    special_data = _nativize_special_data( special_data, controls )
    controls = _nativize_controls( controls )
    response = await _chat( messages, special_data, controls, callbacks )
    # TODO: Check 'supports_streaming' attribute.
    if not model.startswith( 'o1-' ) and controls.get( 'stream', True ):
        return await _process_iterative_chat_response( response, callbacks )
    return _process_complete_chat_response( response, callbacks )


async def _chat( messages, special_data, controls, callbacks ):
    from openai import AsyncOpenAI, OpenAIError
    client = AsyncOpenAI( )
    try:
        return await client.chat.completions.create(
            messages = messages, **special_data, **controls )
    except OpenAIError as exc:
        raise __.ChatCompletionError( f"Error: {exc}" ) from exc


def _create_canister_from_response( response ):
    attributes = __.SimpleNamespace( behaviors = [ ] )
    if response.content: mimetype = 'text/markdown'
    else:
        mimetype = 'application/json'
        attributes.response_class = 'invocation'
    return __.MessageCanister(
        role = 'AI', attributes = attributes ).add_content(
            '', mimetype = mimetype )


def _filter_messages_contingent( canister, model_name ):
    # TODO: Consider 'ignores-system-prompt' attribute.
    if model_name.startswith( 'o1-' ):
        if 'Supervisor' == canister.role: return True
    return False


async def _gather_tool_call_chunks_legacy(
    canister, response, handle, callbacks
):
    from collections import defaultdict
    tool_call = defaultdict( str )
    async for chunk in response:
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


async def _gather_tool_calls_chunks(
    canister, response, handle, callbacks
):
    from collections import defaultdict
    tool_calls = [ ]
    index = 0
    start = True # TODO: Look for non-null finish reason.
    async for chunk in response:
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
    # TODO: Handle content arrays.
    content = canister[ 0 ].data
    attributes = canister.attributes
    context = getattr( attributes, 'model_context', { } ).copy( )
    if 'user' != message[ 'role' ]: return False
    # TODO: Consider 'ignores-invocations' attribute.
    if model_name.startswith( 'o1-' ):
        if context:
            # Merge invocation into previous user message.
            message[ 'content' ] = '\n\n'.join( (
                message[ 'content' ],
                '## Tool Call ##',
                content ) )
            return True
        if 'Function' == canister.role:
            # Merge invocation result into previous user message.
            message[ 'content' ] = '\n\n'.join( (
                message[ 'content' ],
                '## Tool Call Output ##',
                content ) )
            return True
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
    model = nomargs[ 'model' ]
    # TODO: Check for 'supports_streaming' attribute.
    if not model.startswith( 'o1-' ): nomargs[ 'stream' ] = True
    else: nomargs.pop( 'temperature', None )
    return nomargs


def _nativize_invocable( invoker, model_name ):
    return dict(
        name = invoker.name,
        description = invoker.invocable.__doc__,
        parameters = invoker.argschema )


def _nativize_messages( canisters, model_name ):
    messages = [ ]
    for canister in canisters:
        if not messages and _filter_messages_contingent(
            canister, model_name
        ): continue
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
    if 'invocables' in data:
        if access_model_data( model_name, 'supports-multifunctions' ):
            nomargs[ 'tools' ] = [
                {   'type': 'function',
                    'function': _nativize_invocable( invoker, model_name ) }
                for invoker in data[ 'invocables' ] ]
        elif access_model_data( model_name, 'supports-functions' ):
            nomargs[ 'functions' ] = [
                _nativize_invocable( invoker, model_name )
                for invoker in data[ 'invocables' ] ]
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


async def _process_iterative_chat_response( response, callbacks ):
    # TODO: Handle response arrays.
    from openai import OpenAIError
    handle = None
    try:
        chunks = [ ]
        while True:
            try: chunk = await anext( response )
            except StopIteration as exc:
                raise __.ChatCompletionError(
                    'Error: Empty response from AI.' ) from exc
            chunks.append( chunk )
            delta = chunk.choices[ 0 ].delta
            if delta.content or delta.function_call or delta.tool_calls: break
        response_ = __.chain_async( chunks, response )
        canister = _create_canister_from_response( delta )
        handle = callbacks.allocator( canister )
        if delta.tool_calls:
            await _gather_tool_calls_chunks(
                canister, response_, handle, callbacks )
        elif delta.function_call:
            await _gather_tool_call_chunks_legacy(
                canister, response_, handle, callbacks )
        else:
            await _stream_content_chunks(
                canister, response_, handle, callbacks )
    except OpenAIError as exc:
        if handle: callbacks.deallocator( handle )
        raise __.ChatCompletionError( f"Error: {exc}" ) from exc
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


async def _stream_content_chunks(
    canister, response, handle, callbacks
):
    # TODO: Handle content arrays.
    async for chunk in response:
        delta = chunk.choices[ 0 ].delta
        # TODO: Detect finish reason.
        if not delta: break
        if not delta.content: continue
        canister[ 0 ].data += delta.content
        callbacks.updater( handle )
