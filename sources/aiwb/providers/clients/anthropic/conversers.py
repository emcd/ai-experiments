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


''' Converser models for Anthropic AI provider. '''

from __future__ import annotations

from . import __

# TODO: Revisit caching. May need notion of keepalive chat completions
#       to maintain cache warmth when user is formulating a long response.


# TODO: Python 3.12: Use type statement for aliases.
# TODO? Use typing.TypedDictionary.
AnthropicControls: __.a.TypeAlias = dict[ str, __.a.Any ]
AnthropicMessage: __.a.TypeAlias = dict[ str, __.a.Any ]
AnthropicMessageContent: __.a.TypeAlias = str | list[ dict[ str, __.a.Any ] ]
AttributesDescriptor: __.a.TypeAlias = __.AbstractDictionary[ str, __.a.Any ]
ModelDescriptor: __.a.TypeAlias = __.AbstractDictionary[ str, __.a.Any ]


class NativeMessageRefinementActions( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Which action to perform on native message under refinement cursor. '''

    Retain      = 'retain'
    Merge       = 'merge'


class Attributes( __.ConverserAttributes ):
    ''' Common attributes for Anthropic chat models. '''

    supports_computer_use: bool = False

    @classmethod
    def from_descriptor(
        selfclass, descriptor: AttributesDescriptor
    ) -> __.a.Self:
        args = super( ).init_args_from_descriptor( descriptor )
        sdescriptor = descriptor.get( 'special', { } )
        for arg_name in (
            'supports-computer-use',
        ):
            arg = sdescriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        return selfclass( **args )


class ControlsProcessor( __.ControlsProcessor ):
    ''' Controls nativization for Anthropic chat models. '''

    def nativize_controls(
        self, controls: __.ControlsInstancesByName
    ) -> AnthropicControls:
        # TODO: https://docs.anthropic.com/en/api/rate-limits#updated-rate-limits
        #       Cap max tokens by per-tier rate limits.
        #       (Need to add tier awareness and custom configs.)
        #assert self.model.name == controls[ 'model' ] # TODO: enable for -O
        args: AnthropicControls = dict(
            max_tokens = self.model.attributes.tokens_limits.per_response,
            model = self.model.name )
        args.update( {
            name.replace( '-', '_' ): value
            for name, value in controls.items( )
            if name in self.control_names } )
        #if self.model.attributes.supports_continuous_response:
        #    args[ 'stream' ] = True
        return args


class InvocationsProcessor( __.InvocationsProcessor ):
    ''' Handles tool calls for Anthropic chat models. '''

    async def __call__(
        self, request: __.InvocationRequest
    ) -> __.MessageCanister:
        result = await request.invocation( )
        specifics = request.specifics
        result_context = {
            'tool_use_id': specifics[ 'id' ], 'type': 'tool_result' }
        from json import dumps
        message = dumps( result )
        canister = (
            __.ResultMessageCanister( )
            .add_content( message, mimetype = 'application/json' ) )
        canister.attributes.model_context = {
            'provider': self.model.provider.name,
            'model': self.model.name,
            'supplement': result_context,
        } # TODO? Immutable
        return canister

    def nativize_invocable( self, invoker: __.Invoker ) -> __.a.Any:
        # TODO: return type: anthropic.types.ToolParam
        return dict(
            name = invoker.name,
            description = invoker.invocable.__doc__,
            input_schema = invoker.argschema )

    def nativize_invocables(
        self,
        invokers: __.AbstractIterable[ __.Invoker ],
    ) -> __.a.Any:
        # TODO: return type: list[ anthropic.types.ToolParam ]
        tools = [ self.nativize_invocable( invoker ) for invoker in invokers ]
        # Note: Caching of invocables is not worth it in sporadic
        #       conversational contexts. Only worthwhile when tools are being
        #       continuously shared by multiple conversational contexts.
        #if tools: tools[ -1 ][ 'cache_control' ] = { 'type': 'ephemeral' }
        return dict( tools = tools )

    def requests_from_canister(
        self,
        auxdata: __.CoreGlobals, *,
        supplements: __.accret.Dictionary,
        canister: __.MessageCanister,
        invocables: __.accret.Namespace,
        ignore_invalid_canister: bool = False,
    ) -> __.InvocationsRequests:
        # TODO: Provide supplements based on specification from invocable.
        supplements[ 'model' ] = self.model
        model_context = getattr( canister.attributes, 'model_context', { } )
        if self.model.provider.name != model_context.get( 'provider' ):
            if ignore_invalid_canister: return [ ]
            raise __.ProviderIncompatibilityError(
                provider = self.model.provider,
                entity_name = "foreign invocation requests" )
        requests = __.invocation_requests_from_canister(
            auxdata = auxdata,
            supplements = supplements,
            canister = canister,
            invocables = invocables,
            ignore_invalid_canister = ignore_invalid_canister )
        supplement = model_context.get( 'supplement', { } )
        specifics = supplement.get( 'tool_use', [ ] )
        if len( requests ) != len( specifics ):
            raise __.InvocationFormatError(
                "Number of invocation requests must match "
                "number of tool calls." )
        for i, request in enumerate( requests ):
            request.specifics.update( specifics[ i ] )
        return requests


class MessagesProcessor( __.MessagesProcessor ):
    ''' Handles conversation messages in Anthropic format. '''

    def nativize_messages_v0(
        self, canisters: __.MessagesCanisters, supplements
    ) -> list[ AnthropicMessage ]:
        # TODO: return type: list[ anthropic.types.MessageParam ]
        messages_pre: list[ AnthropicMessage ] = [ ]
        for canister in canisters:
            if _decide_exclude_message( self.model, canister ): continue
            message = _nativize_message(
                self.model, canister, supplements )
            messages_pre.append( message )
        return _refine_native_messages( self.model, messages_pre )


class Model( __.ConverserModel ):
    ''' Anthropic chat model. '''

    @classmethod
    def from_descriptor(
        selfclass, client: __.Client, name: str, descriptor: ModelDescriptor
    ) -> __.a.Self:
        args = __.accret.Dictionary( client = client, name = name )
        args[ 'attributes' ] = Attributes.from_descriptor( descriptor )
        return selfclass( **args )

    @property
    def controls_processor( self ) -> ControlsProcessor:
        return ControlsProcessor( model = self )

    @property
    def invocations_processor( self ) -> InvocationsProcessor:
        return InvocationsProcessor( model = self )

    @property
    def messages_processor( self ) -> MessagesProcessor:
        return MessagesProcessor( model = self )

    @property
    def serde_processor( self ) -> 'SerdeProcessor':
        return SerdeProcessor( model = self )

    @property
    def tokenizer( self ) -> 'Tokenizer':
        return Tokenizer( model = self )

    async def converse_v0(
        self,
        messages: __.MessagesCanisters,
        supplements,
        controls: __.ControlsInstancesByName,
        reactors, # TODO? Accept context manager with reactor functions.
    ):
        args = _prepare_client_arguments(
            model = self,
            messages = messages,
            supplements = supplements,
            controls = controls )
        should_stream = (
                self.attributes.supports_continuous_response
            and args.get( 'stream', True ) )
        if should_stream:
            return await _converse_continuous_v0( self, args, reactors )
        return await _converse_complete_v0( self, args, reactors )


class SerdeProcessor( __.ConverserSerdeProcessor ):
    ''' (De)serialization for Anthropic chat models. '''

    def deserialize_data( self, data: str ) -> __.a.Any:
        data_format = self.model.attributes.format_preferences.response_data
        match data_format:
            case __.DataFormatPreferences.JSON:
                from ....codecs.json import loads
                return loads( data )
        raise __.SupportError(
            f"Cannot deserialize data from {data_format.value} format." )

    def serialize_data( self, data: __.a.Any ) -> str:
        data_format = self.model.attributes.format_preferences.request_data
        match data_format:
            case __.DataFormatPreferences.JSON:
                from json import dumps
                return dumps( data )
        raise __.SupportError(
            f"Cannot serialize data to {data_format.value} format." )


class Tokenizer( __.ConversationTokenizer ):
    ''' Tokenizes conversations and text with Anthropic tokenizers. '''

    async def count_text_tokens( self, text: str ) -> int:
        # TODO: Caching.
        # TODO? Client-side rate-limiting.
        client = self.model.client.produce_implement( )
        messages, extra_count = _sanitize_messages_for_tokenization(
            dict( messages = [ { 'role': 'user', 'content': text } ] ) )
        try:
            response = await client.beta.messages.count_tokens(
                messages = messages, model = self.model.name )
        except Exception as exc:
            # TODO? Use client-side fallback counting method.
            raise __.ModelOperateFailure(
                model = self.model,
                operation = 'count text tokens',
                cause = exc ) from exc
        return response.input_tokens - extra_count

    async def count_conversation_tokens_v0(
        self, messages: __.MessagesCanisters, supplements
    ) -> int:
        # TODO: Caching.
        # TODO? Client-side rate-limiting.
        args = _prepare_client_arguments(
            model = self.model,
            messages = messages,
            supplements = supplements,
            controls = { } )
        args.pop( 'max_tokens', None )
        args.pop( 'stream', None )
        messages_, extra_count = _sanitize_messages_for_tokenization( args )
        args[ 'messages' ] = messages_
        client = self.model.client.produce_implement( )
        try: response = await client.beta.messages.count_tokens( **args )
        except Exception as exc:
            # TODO? Use client-side fallback counting method.
            raise __.ModelOperateFailure(
                model = self.model,
                operation = 'count conversation tokens',
                cause = exc ) from exc
        return response.input_tokens - extra_count


def _sanitize_messages_for_tokenization(
    arguments: __.AbstractDictionary[ str, __.a.Any ]
) -> tuple[ list[ AnthropicMessage ], int ]:
    messages = list( arguments[ 'messages' ] )
    # [anthropic.BadRequestError] Error code: 400
    # all messages must have non-empty content except for the optional
    # final assistant message
    # [anthropic.BadRequestError] Error code: 400
    # text content blocks must contain non-whitespace text
    extra_message = { 'role': 'user', 'content': 'I' }
    extra_count = 0
    if not messages:
        # [anthropic.BadRequestError] Error code: 400
        # at least one message is required
        extra_count += 1
        return [ extra_message ], extra_count
    message = messages[ -1 ]
    # [anthropic.BadRequestError] Error code: 400
    # When using tools, pre-filling the `assistant` response is
    # not supported.
    if 'tools' in arguments and 'assistant' == message[ 'role' ]:
        messages.append( extra_message )
        extra_count += 1
    return messages, extra_count


def _append_user_cache_control_watermarks(
    messages: list[ AnthropicMessage ]
) -> list[ AnthropicMessage ]:
    ''' Adds cache control to last two user messages in conversation. '''
    # Note: Caching of user messages is not worth it in sporadic
    #       conversational contexts. Only worthwhile when messages are
    #       being continuously shared by multiple conversational contexts
    #       or conversation frequency is higher than once per 5 minutes.
    #       We could consider a heuristic with tool use detection, since that
    #       typically indicates higher frequency.
    return messages
#    for i, message in enumerate( reversed( messages ) ):
#        if 1 < i: break
#        if 'user' != message[ 'role' ]: continue
#        content = message[ 'content' ]
#        if isinstance( content, str ):
#            content = [ { 'text': content, 'type': 'text' } ]
#            message[ 'content' ] = content
#        for block in reversed( content ):
#            if block[ 'type' ] not in ( 'text', 'base64' ): continue
#            block[ 'cache_control' ] = { 'type': 'ephemeral' }
#            break
#    return messages


def _canister_from_response_element( model, element ):
    # TODO: Appropriate error classes.
    attributes = __.SimpleNamespace(
        behaviors = [ ],
        model_context = {
            'provider': model.provider.name,
            'client': model.client.name,
            'model': model.name,
        },
    )
    match element.type:
        case 'text':
            content = element.text
            # TODO: Lookup MIME type from model response format preferences.
            mimetype = 'text/markdown'
            return (
                __.MessageRole.Assistant
                .produce_canister( attributes = attributes )
                .add_content( content, mimetype = mimetype ) )
        case 'tool_use':
            attributes.invocation_data = [ ]
            return (
                __.MessageRole.Invocation
                .produce_canister( attributes = attributes ) )
    raise AssertionError(
        "Cannot create message canister from unknown message species." )


def _collect_response_as_content_v0( model, indices, event, reactors ):
    index = event.index
    if not ( content := event.delta.text ): return
    indices.canisters[ index ][ 0 ].data += content
    if index: return # TODO: Support response arrays.
    reactors.updater( indices.references[ index ] )


def _collect_supervisor_instructions(
    model: Model, canisters: __.MessagesCanisters
) -> dict[ str, str ]:
    instructions = [ ]
    for canister in canisters:
        if __.MessageRole.Supervisor is not canister.role: continue
        instructions.append( canister[ 0 ].data )
    if not instructions: return { }
    return dict( system = [ {
        'type': 'text',
        'text': '\n\n'.join( instructions ),
        # Note: Caching of supervisor instructions is not worth it in sporadic
        #       conversational contexts. Only worthwhile when instructions are
        #       being continuously shared by multiple conversational contexts.
        #'cache_control': { 'type': 'ephemeral' },
    } ] )


async def _converse_complete_v0(
    model: Model, arguments: dict[ str, __.a.Any ], reactors
): # TODO: return signature
    error = __.partial_function(
        __.ModelOperateFailure, model = model, operation = 'chat completion' )
    client = model.client.produce_implement( )
    from anthropic import AnthropicError
    try: response = await client.messages.create( **arguments )
    except AnthropicError as exc: raise error( cause = exc ) from exc
    return _process_complete_response_v0( model, response, reactors )


async def _converse_continuous_v0(
    model: Model, arguments: dict[ str, __.a.Any ], reactors
): # TODO: return signature
    error = __.partial_function(
        __.ModelOperateFailure, model = model, operation = 'chat completion' )
    client = model.client.produce_implement( )
    from anthropic import AnthropicError
    try:
        async with client.messages.stream( **arguments ) as response:
            return await _process_continuous_response_v0(
                model, response, reactors )
    except AnthropicError as exc: raise error( cause = exc ) from exc


def _decide_exclude_message(
    model: Model, canister: __.MessageCanister
) -> bool:
    match canister.role:
        case __.MessageRole.Supervisor:
            # We collect system instructions separately,
            # since there is not an Anthropic message type for them.
            return True
    return False


def _finalize_response_event_capture_v0( model, indices, event, reactors ):
    index = event.index
    match event.content_block.type:
        case 'text': return # Already accumulated.
        case 'tool_use':
            indices.records[ index ] = dict( tool_use = event.content_block )


def _initialize_response_event_capture_v0( model, indices, event, reactors ):
    index = event.index
    if index in indices.canisters: return
    match event.content_block.type:
        case 'text': pass
        case 'tool_use':
            if indices.canisters: return # subordinate to text
    indices.canisters[ index ] = canister = (
        _canister_from_response_element( model, event.content_block ) )
    indices.references[ index ] = reactors.allocator( canister )


def _merge_native_message(
    model: Model,
    anchor: AnthropicMessage,
    cursor: AnthropicMessage,
    indicate_elision: bool = False,
):
    ''' Merges cursor message into anchor message. '''
    if not isinstance( anchor[ 'content' ], list ):
        anchor[ 'content' ] = (
            [ { 'text': anchor[ 'content' ], 'type': 'text' } ] )
    if not isinstance( cursor[ 'content' ], list ):
        cursor[ 'content' ] = (
            [ { 'text': cursor[ 'content' ], 'type': 'text' } ] )
    anchor[ 'content' ].extend( cursor[ 'content' ] )


def _nativize_assistant_message(
    model: Model, canister: __.MessageCanister, supplements
) -> AnthropicMessage:
    context = { 'role': 'assistant' }
    content = _nativize_message_content( model, canister )
    if hasattr( canister.attributes, 'invocation_data' ):
        context = _nativize_invocation_message( model, canister, supplements )
        if ( extra_content := context.pop( 'content', None ) ):
            if isinstance( content, str ):
                content = [ { 'text': content, 'type': 'text' } ]
            content.extend( extra_content )
    return dict( content = content, **context )


def _nativize_document_message(
    model: Model, canister: __.MessageCanister
) -> AnthropicMessage:
    context = { 'role': 'user' }
    content = '\n\n'.join( (
        '## Supplemental Information ##', canister[ 0 ].data ) )
    return dict( content = content, **context )


def _nativize_invocation_message(
    model: Model, canister: __.MessageCanister, supplements
) -> AnthropicMessage:
    attributes = canister.attributes
    content: AnthropicMessageContent
    context = { 'role': 'assistant' }
    model_context = getattr( attributes, 'model_context', { } ).copy( )
    supplement = model_context.get( 'supplement', { } )
    # When no invocables are supplied, but previous invocations were
    # made, then we need to appease the following quirk:
    #     [anthropic.BadRequestError] Error code: 400 -
    #     Requests which include `tool_use` or `tool_result` blocks must
    #     define tools.
    supports_invocations = (
            model.attributes.supports_invocations
        and model.provider.name == model_context.get( 'provider' )
        and 'invokers' in supplements
        and 'tool_use' in supplement )
    if not supports_invocations:
        # TODO? Customizable elision text.
        text = '(Note: Functions invocation elided from conversation.)'
        content = [ { 'text': text, 'type': 'text' } ]
    else: content = supplement[ 'tool_use' ]
    return dict( content = content, **context )


def _nativize_message(
    model: Model, canister: __.MessageCanister, supplements
) -> AnthropicMessage:
    role = canister.role
    match role:
        case __.MessageRole.Assistant:
            return _nativize_assistant_message( model, canister, supplements )
        case __.MessageRole.Document:
            return _nativize_document_message( model, canister )
        case __.MessageRole.Invocation:
            return _nativize_invocation_message( model, canister, supplements )
        case __.MessageRole.Result:
            return _nativize_result_message( model, canister, supplements )
        case __.MessageRole.User:
            return _nativize_user_message( model, canister )
    raise __.ProviderIncompatibilityError(
        provider = model.provider, entity_name = f"role {role.value!r}" )


def _nativize_message_content(
    model: Model, canister: __.MessageCanister
) -> AnthropicMessageContent:
    # TODO: Handle audio and image contents.
    match len( canister ):
        case 0: return ''
        case 1: return canister[ 0 ].data
        case _:
            # Build multipart message.
            return [
                { 'text': content.data, 'type': 'text' }
                for content in canister ]


def _nativize_result_message(
    model: Model, canister: __.MessageCanister, supplements
) -> AnthropicMessage:
    attributes = canister.attributes
    content: AnthropicMessageContent
    context = { 'role': 'user' }
    model_context = getattr( attributes, 'model_context', { } ).copy( )
    # When no invocables are supplied, but previous invocations were
    # made, then we need to appease the following quirk:
    #     [anthropic.BadRequestError] Error code: 400 -
    #     Requests which include `tool_use` or `tool_result` blocks must
    #     define tools.
    supports_invocations = (
            model.attributes.supports_invocations
        and model.provider.name == model_context.get( 'provider' )
        and 'invokers' in supplements )
    supplement = model_context[ 'supplement' ]
    if not supports_invocations:
        content = '\n\n'.join( (
            '## Functions Invocation Result ##', canister[ 0 ].data ) )
        content = [ { 'text': content, 'type': 'text' } ]
    else:
        content = [ {
            'content': _nativize_message_content( model, canister ),
            **supplement } ]
    return dict( content = content, **context )


def _nativize_supplements_v0( model: Model, supplements ):
    nomargs = { }
    if 'invokers' in supplements:
        nomargs.update(
            model.invocations_processor
            .nativize_invocables( supplements[ 'invokers' ] ) )
    return nomargs


def _nativize_user_message(
    model: Model, canister: __.MessageCanister
) -> AnthropicMessage:
    content: AnthropicMessageContent
    context = { 'role': 'user' }
    content = _nativize_message_content( model, canister )
    return dict( content = content, **context )


def _perform_response_event_capture_v0( model, indices, event, reactors ):
    match event.delta.type:
        case 'input_json_delta': return # Accumulate via SDK.
        case 'text_delta':
            _collect_response_as_content_v0( model, indices, event, reactors )


def _postprocess_response_canisters( model, indices, reactors ):
    # TODO? Deduplicate tool use from multiple responses.
    invocation_data = supplement = None
    if indices.records:
        invocation_data = _reconstitute_invocations( indices.records )
        tool_uses = [
            record[ 'tool_use' ].to_dict( )
            for record in indices.records.values( )
            if 'tool_use' in record ]
        # TODO? Record other Anthropic-specific parts of response.
        supplement = dict( tool_use = tool_uses )
    # TODO: Callbacks support for response arrays.
    for index, canister in indices.canisters.items( ):
        if index: continue
        if invocation_data and supplement:
            canister.attributes.invocation_data = invocation_data
            canister.attributes.model_context[ 'supplement' ] = supplement
            reactors.updater( indices.references[ index ] )


def _prepare_client_arguments(
    model: Model,
    messages: __.MessagesCanisters,
    supplements,
    controls: __.ControlsInstancesByName,
) -> dict[ str, __.a.Any ]:
    controls_native = model.controls_processor.nativize_controls( controls )
    supervisor_instructions = (
        _collect_supervisor_instructions( model, messages ) )
    supplements_native = _nativize_supplements_v0( model, supplements )
    messages_native = (
        model.messages_processor.nativize_messages_v0(
            messages, supplements ) )
    return dict(
        messages = messages_native,
        **supervisor_instructions, **supplements_native, **controls_native )


def _process_complete_response_v0( model, response, reactors ):
    indices = __.accret.Namespace(
        canisters = __.accret.Dictionary( ),
        records = __.accret.Dictionary( ),
        references = __.accret.Dictionary( ) )
    indices.canisters.update( {
        i: _canister_from_response_element( model, element )
        for i, element in enumerate( response.content ) } )
    indices.records.update( {
        i: dict( tool_use = element )
        for i, element in enumerate( response.content )
        if 'tool_use' == element.type } )
    # TODO: Callbacks support for response arrays.
    indices.references.update( {
        index: reactors.allocator( canister ) for index, canister
        in indices.canisters.items( ) if not index } )
    _postprocess_response_canisters( model, indices, reactors )
    return indices.references[ 0 ]


async def _process_continuous_response_v0( model, response, reactors ):
    indices = __.accret.Namespace(
        canisters = __.accret.Dictionary( ),
        records = __.accret.Dictionary( ),
        references = __.accret.Dictionary( ) )
    async for event in response:
        #ic( event )
        try:
            _process_response_event_v0( model, indices, event, reactors )
        except Exception:
            for reference in indices.references.values( ):
                reactors.deallocator( reference )
            raise
    _postprocess_response_canisters( model, indices, reactors )
    # TODO: Callbacks support for response arrays.
    return indices.references[ 0 ]


def _process_response_event_v0( model, indices, event, reactors ):
    match event.type:
        case 'content_block_delta':
            _perform_response_event_capture_v0(
                model, indices, event, reactors )
        case 'content_block_start':
            _initialize_response_event_capture_v0(
                model, indices, event, reactors )
        case 'content_block_stop':
            _finalize_response_event_capture_v0(
                model, indices, event, reactors )
        case 'input_json': pass # Content block delta has index field.
        case 'message_delta': pass # Content block delta has index field.
        case 'message_start': pass # Content block delta has index field.
        case 'message_stop': pass # TODO? Inspect 'stop_reason' and 'usage'.
        case 'text': pass # Content block delta has index field.


def _reconstitute_invocations( records ):
    invocations = [ ]
    for record in records.values( ):
        if 'tool_use' not in record: continue
        tool_use = record[ 'tool_use' ]
        name = tool_use.name
        arguments = dict( tool_use.input )
        invocations.append( dict( name = name, arguments = arguments ) )
    return invocations


def _refine_native_message(
    model: Model,
    anchor: AnthropicMessage,
    cursor: AnthropicMessage,
) -> NativeMessageRefinementActions:
    ''' Determines how to handle cursor message relative to anchor. '''
    anchor_role = anchor[ 'role' ]
    cursor_role = cursor[ 'role' ]
    if 'user' == anchor_role == cursor_role:
        # Check if both messages contain tool results.
        anchor_has_tool = any(
            isinstance( block, dict ) and 'type' in block
            and 'tool_result' == block[ 'type' ]
            for block in anchor[ 'content' ]
            if isinstance( anchor[ 'content' ], list ) )
        cursor_has_tool = any(
            isinstance( block, dict ) and 'type' in block
            and 'tool_result' == block[ 'type' ]
            for block in cursor[ 'content' ]
            if isinstance( cursor[ 'content' ], list ) )
        if anchor_has_tool and cursor_has_tool:
            _merge_native_message( model, anchor, cursor )
            return NativeMessageRefinementActions.Merge
    return NativeMessageRefinementActions.Retain


def _filter_unmatched_tool_uses(
    messages: list[ AnthropicMessage ]
) -> list[ AnthropicMessage ]:
    ''' Filters out tool use blocks that have no matching result. '''
    tool_result_ids = set( )
    filtered_messages: list[ AnthropicMessage ] = [ ]
    for message in reversed( messages ):
        content = message[ 'content' ]
        if not isinstance( content, list ):
            filtered_messages.append( message )
            continue
        filtered_blocks = [ ]
        for block in content:
            if not isinstance( block, dict ):
                filtered_blocks.append( block )
                continue
            match block.get( 'type' ):
                case 'tool_result':
                    if 'tool_use_id' in block:
                        tool_result_ids.add( block[ 'tool_use_id' ] )
                    filtered_blocks.append( block )
                case 'tool_use':
                    if block.get( 'id' ) in tool_result_ids:
                        filtered_blocks.append( block )
                case _:
                    filtered_blocks.append( block )
        if filtered_blocks:
            message_filtered = dict( message )
            message_filtered[ 'content' ] = filtered_blocks
            filtered_messages.append( message_filtered )
    return list( reversed( filtered_messages ) )


def _refine_native_messages(
    model: Model,
    messages_pre: list[ AnthropicMessage ],
) -> list[ AnthropicMessage ]:
    ''' Refines sequence of native messages. '''
    anchor = None
    messages: list[ AnthropicMessage ] = [ ]
    messages_pre = _filter_unmatched_tool_uses( messages_pre )
    for message_pre in messages_pre:
        cursor = dict( message_pre )
        if not anchor:
            anchor = cursor
            continue
        action = _refine_native_message( model, anchor, cursor )
        match action:
            case NativeMessageRefinementActions.Merge: continue
        messages.append( anchor )
        anchor = cursor
    if anchor: messages.append( anchor )
    return _append_user_cache_control_watermarks( messages )
