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


''' Converser models for OpenAI AI provider. '''

from __future__ import annotations

from . import __


# TODO: Python 3.12: Use type statement for aliases.
# TODO? Use typing.TypedDictionary.
AttributesDescriptor: __.a.TypeAlias = __.AbstractDictionary[ str, __.a.Any ]
ModelDescriptor: __.a.TypeAlias = __.AbstractDictionary[ str, __.a.Any ]
OpenAiControls: __.a.TypeAlias = dict[ str, __.a.Any ]
OpenAiMessage: __.a.TypeAlias = dict[ str, __.a.Any ]
OpenAiMessageContent: __.a.TypeAlias = str | list[ dict[ str, __.a.Any ] ]


class InvocationsSupportLevels( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Degree to which invocations are supported. '''

    Single      = 'single'      # Mid-2023.
    Concurrent  = 'concurrent'  # Late 2023 and beyond.


class NativeMessageRefinementActions( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Which action to perform on native message under refinement cursor. '''

    Retain      = 'retain'
    Merge       = 'merge'


class Attributes(
    __.ConverserAttributes, class_decorators = ( __.standard_dataclass, )
):
    ''' Common attributes for OpenAI chat models. '''

    extra_tokens_for_actor_name: int = 0
    extra_tokens_per_message: int = 0
    honors_supervisor_instructions: bool = False
    invocations_support_level: InvocationsSupportLevels = (
        InvocationsSupportLevels.Single )
    supports_duplex_exchanges: bool = False

    @classmethod
    def from_descriptor(
        selfclass, descriptor: AttributesDescriptor
    ) -> __.a.Self:
        args = super( ).init_args_from_descriptor( descriptor )
        sdescriptor = descriptor.get( 'special', { } )
        for arg_name in (
            'extra-tokens-for-actor-name',
            'extra-tokens-per-message',
            'honors-supervisor-instructions',
            'supports-duplex-exchanges',
        ):
            arg = sdescriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        if 'invocations-support-level' in sdescriptor:
            args[ 'invocations_support_level' ] = (
                InvocationsSupportLevels(
                    sdescriptor[ 'invocations-support-level' ] ) )
        return selfclass( **args )


class ControlsProcessor(
    __.ControlsProcessor, class_decorators = ( __.standard_dataclass, )
 ):
    ''' Controls nativization for OpenAI chat models. '''

    def nativize_controls(
        self, controls: __.ControlsInstancesByName
    ) -> OpenAiControls:
        # TODO: Assert model name matches.
        args: OpenAiControls = dict( model = controls[ 'model' ] )
        args.update( {
            name.replace( '-', '_' ): value
            for name, value in controls.items( )
            if name in self.control_names } )
        if self.model.attributes.supports_continuous_response:
            args[ 'stream' ] = True
        return args


class InvocationsProcessor(
    __.InvocationsProcessor, class_decorators = ( __.standard_dataclass, )
):
    ''' Handles functions and tool calls for OpenAI chat models. '''

    async def __call__(
        self, request: __.InvocationRequest
    ) -> __.MessageCanister:
        result = await request.invocation( )
        specifics = request.specifics
        if 'id' in specifics: # late 2023+ format: parallel tool calls
            result_context = dict(
                name = specifics[ 'function' ][ 'name' ],
                role = 'tool',
                tool_call_id = specifics[ 'id' ] )
        else: # mid-2023 format: single function call
            result_context = dict( name = request.name, role = 'function' )
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
        return dict(
            name = invoker.name,
            description = invoker.invocable.__doc__,
            parameters = invoker.argschema )

    def nativize_invocables(
        self,
        invokers: __.AbstractIterable[ __.Invoker ],
    ) -> __.a.Any:
        if not self.model.attributes.supports_invocations: return { }
        args = { }
        match self.model.attributes.invocations_support_level:
            case InvocationsSupportLevels.Concurrent:
                args[ 'tools' ] = [
                    {   'type': 'function',
                        'function': self.nativize_invocable( invoker ) }
                    for invoker in invokers ]
            case InvocationsSupportLevels.Single:
                args[ 'functions' ] = [
                    self.nativize_invocable( invoker )
                    for invoker in invokers ]
        return args

    def requests_from_canister(
        self,
        auxdata: __.CoreGlobals, *,
        supplements: __.AccretiveDictionary,
        canister: __.MessageCanister,
        invocables: __.AccretiveNamespace,
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
        if ( specifics := supplement.get( 'function_call' ) ):
            if 1 != len( requests ):
                raise __.InvocationFormatError(
                    "Can only have one invocation request "
                    "with legacy function." )
            requests[ 0 ].specifics.update( specifics )
        elif ( specifics := supplement.get( 'tool_calls' ) ):
            if len( requests ) != len( specifics ):
                raise __.InvocationFormatError(
                    "Number of invocation requests must match "
                    "number of tool calls." )
            for i, request in enumerate( requests ):
                request.specifics.update( specifics[ i ] )
        return requests


class MessagesProcessor(
    __.MessagesProcessor, class_decorators = ( __.standard_dataclass, )
):
    ''' Handles conversation messages in OpenAI format. '''

    def nativize_messages_v0(
        self, canisters: __.MessagesCanisters
    ) -> list[ OpenAiMessage ]:
        messages_pre: list[ OpenAiMessage ] = [ ]
        for canister in canisters:
            if _decide_exclude_message( self.model, canister ): continue
            message = _nativize_message( self.model, canister )
            messages_pre.append( message )
        return _refine_native_messages( self.model, messages_pre )


class Model(
    __.ConverserModel, class_decorators = ( __.standard_dataclass, )
):
    ''' OpenAI chat model. '''

    @classmethod
    def from_descriptor(
        selfclass, client: __.Client, name: str, descriptor: ModelDescriptor
    ) -> __.a.Self:
        args = __.AccretiveDictionary( client = client, name = name )
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
    def serde_processor( self ) -> SerdeProcessor:
        return SerdeProcessor( model = self )

    @property
    def tokenizer( self ) -> Tokenizer:
        return Tokenizer( model = self )

    async def converse_v0(
        self,
        messages: __.MessagesCanisters,
        supplements,
        controls: __.ControlsInstancesByName,
        reactors, # TODO? Accept context manager with reactor functions.
    ):
        messages_native = (
            self.messages_processor.nativize_messages_v0( messages ) )
        #ic( messages_native )
        controls_native = (
            self.controls_processor.nativize_controls( controls ) )
        supplements_native = _nativize_supplements_v0( self, supplements )
        client = self.client.produce_implement( )
        from openai import OpenAIError
        try:
            response = await client.chat.completions.create(
                messages = messages_native,
                **supplements_native, **controls_native )
        except OpenAIError as exc:
            raise __.ModelOperateFailure(
                model = self, operation = 'chat completion', cause = exc
            ) from exc
        should_stream = controls_native.get( 'stream', True )
        if self.attributes.supports_continuous_response and should_stream:
            return (
                await _process_iterative_response_v0(
                    self, response, reactors ) )
        return _process_complete_response_v0( self, response, reactors )


class SerdeProcessor(
    __.ConverserSerdeProcessor, class_decorators = ( __.standard_dataclass, )
):
    ''' (De)serialization for OpenAI chat models. '''

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


class Tokenizer(
    __.ConversationTokenizer, class_decorators = ( __.standard_dataclass, )
):
    ''' Tokenizes conversations and text with OpenAI tokenizers. '''

    def count_text_tokens( self, text: str ) -> int:
        from tiktoken import encoding_for_model, get_encoding
        try: encoding = encoding_for_model( self.model.name )
        # TODO? Warn about unknown model via callback.
        except KeyError: encoding = get_encoding( 'cl100k_base' )
        return len( encoding.encode( text ) )

    def count_conversation_tokens_v0(
        self, messages: __.MessagesCanisters, supplements
    ) -> int:
        # https://github.com/openai/openai-cookbook/blob/2e9704b3b34302c30174e7d8e7211cb8da603ca9/examples/How_to_count_tokens_with_tiktoken.ipynb
        from json import dumps
        model = self.model
        tokens_per_message = model.attributes.extra_tokens_per_message
        tokens_for_actor_name = model.attributes.extra_tokens_for_actor_name
        tokens_count = 0
        for message in (
            model.messages_processor.nativize_messages_v0( messages )
        ):
            tokens_count += tokens_per_message
            for index, value in message.items( ):
                value_ = value if isinstance( value, str ) else dumps( value )
                tokens_count += self.count_text_tokens( value_ )
                if 'name' == index: tokens_count += tokens_for_actor_name
        iprocessor = self.model.invocations_processor
        for invoker in supplements.get( 'invokers', ( ) ):
            tokens_count += (
                self.count_text_tokens( dumps(
                    iprocessor.nativize_invocable( invoker ) ) ) )
            # TODO: Determine if metadata from multifunctions adds more tokens.
        return tokens_count


def _canister_from_response_element( model, element ):
    # TODO: Appropriate error classes.
    if ( delta := hasattr( element, 'delta' ) ): message = element.delta
    else: message = element.message
    attributes = __.SimpleNamespace(
        behaviors = [ ],
        model_context = {
            'provider': model.provider.name,
            'client': model.client.name,
            'model': model.name,
        },
    )
    if message.content:
        content = '' if delta else message.content
        # TODO: Lookup MIME type from model response format preferences.
        mimetype = 'text/markdown'
        return (
            __.MessageRole.Assistant
            .produce_canister( attributes = attributes )
            .add_content( content, mimetype = mimetype ) )
    if message.function_call or message.tool_calls:
        attributes.invocation_data = [ ]
        return (
            __.MessageRole.Invocation
            .produce_canister( attributes = attributes ) )
    raise AssertionError(
        "Cannot create message canister from unknown message species." )


def _collect_response_as_content_v0(
    model, indices, index, delta, reactors
):
    if not delta.content: return
    canister = indices.canisters[ index ]
    canister[ 0 ].data += delta.content
    reactors.updater( indices.references[ index ] )


def _collect_response_as_invocations_v0(
    model, indices, index, delta, reactors
):
    if not delta.tool_calls: return
    from collections import defaultdict
    if index not in indices.records:
        indices.records[ index ] = dict( tool_calls = [ ] )
    calls = indices.records[ index ][ 'tool_calls' ]
    for tool_call in delta.tool_calls:
        if tool_call.index == len( calls ):
            calls.append( {
                'type': 'function', 'function': defaultdict( str ) } )
        call = calls[ tool_call.index ]
        if tool_call.id: call[ 'id' ] = tool_call.id
        if tool_call.function:
            function = call[ 'function' ]
            if tool_call.function.name:
                function[ 'name' ] = tool_call.function.name
            if tool_call.function.arguments:
                function[ 'arguments' ] += tool_call.function.arguments


def _collect_response_as_legacy_invocation_v0(
    model, indices, index, delta, reactors
):
    if not delta.function_call: return
    from collections import defaultdict
    if index not in indices.records:
        indices.records[ index ] = dict( function_call = defaultdict( str ) )
    call = indices.records[ index ][ 'function_call' ]
    if delta.function_call.name:
        call[ 'name' ] = delta.function_call.name
    if delta.function_call.arguments:
        call[ 'arguments' ] += delta.function_call.arguments


def _decide_exclude_message(
    model: Model, canister: __.MessageCanister
) -> bool:
    role = __.MessageRole.from_canister( canister )
    if not model.attributes.accepts_supervisor_instructions:
        if __.MessageRole.Supervisor is role: return True
    return False


def _merge_native_message(
    model: Model,
    anchor: OpenAiMessage,
    cursor: OpenAiMessage,
    indicate_elision: bool = False,
):
    anchor_content = anchor[ 'content' ]
    if isinstance( anchor_content, str ):
        anchor_content = [ { 'type': 'text', 'text': anchor_content } ]
        anchor[ 'content' ] = anchor_content
    cursor_content = cursor[ 'content' ]
    if isinstance( cursor_content, str ):
        cursor_content = [ { 'type': 'text', 'text': cursor_content } ]
        cursor[ 'content' ] = cursor_content
    anchor_role = anchor[ 'role' ]
    match anchor_role:
        case 'assistant': elision_role = 'user'
        case _: elision_role = 'assistant'
    if indicate_elision:
        join_content = [ {
            'type': 'text',
            'text': f"... <elided {elision_role} response> ..."
        } ]
        anchor_content.extend( join_content )
    anchor_content.extend( cursor_content )
    # TODO? Merge multiple texts into single one.
    # TODO? Error if refusal message part encountered.


def _nativize_assistant_message(
    model: Model, canister: __.MessageCanister
) -> OpenAiMessage:
    content: OpenAiMessageContent
    context = { 'role': 'assistant' }
    content = _nativize_message_content( model, canister )
    if hasattr( canister.attributes, 'invocation_data' ):
        context = _nativize_invocation_message( model, canister )
        if ( extra_content := context.pop( 'content', None ) ):
            if isinstance( content, str ):
                content = "{content_0}\n\n{content_f}".format(
                    content_0 = content, content_f = extra_content )
            else: content.append( { 'type': 'text', 'text': extra_content } )
    return dict( content = content, **context )


def _nativize_document_message(
    model: Model, canister: __.MessageCanister
) -> OpenAiMessage:
    context = { 'role': 'user' }
    content = '\n\n'.join( (
        '## Supplemental Information ##', canister[ 0 ].data ) )
    return dict( content = content, **context )


def _nativize_invocation_message(
    model: Model, canister: __.MessageCanister
) -> OpenAiMessage:
    attributes = canister.attributes
    content: OpenAiMessageContent
    context = { 'role': 'assistant' }
    model_context = getattr( attributes, 'model_context', { } ).copy( )
    supplement = model_context.get( 'supplement', { } )
    supports_invocations = (
            model.attributes.supports_invocations
        and model.provider.name == model_context.get( 'provider' )
        and { 'function_call', 'tool_calls' } & supplement.keys( ) )
    if (    supports_invocations
        and ( calls := supplement.get( 'tool_calls', ( ) ) )
    ): supports_invocations = all( 'id' in call for call in calls )
    if supports_invocations:
        match model.attributes.invocations_support_level:
            case InvocationsSupportLevels.Single:
                supports_invocations = 'function_call' in supplement
            case InvocationsSupportLevels.Concurrent: pass
    if not supports_invocations:
        from json import dumps
        content = '\n\n'.join( (
            '## Functions Invocation Request ##',
            dumps( canister.attributes.invocation_data ) ) )
        return dict( content = content, **context )
    context.update( supplement )
    return context


def _nativize_message(
    model: Model, canister: __.MessageCanister
) -> OpenAiMessage:
    role = __.MessageRole.from_canister( canister )
    match role:
        case __.MessageRole.Assistant:
            return _nativize_assistant_message( model, canister )
        case __.MessageRole.Document:
            return _nativize_document_message( model, canister )
        case __.MessageRole.Invocation:
            return _nativize_invocation_message( model, canister )
        case __.MessageRole.Result:
            return _nativize_result_message( model, canister )
        case __.MessageRole.Supervisor:
            return _nativize_supervisor_message( model, canister )
        case __.MessageRole.User:
            return _nativize_user_message( model, canister )
    raise __.ProviderIncompatibilityError(
        provider = model.provider, entity_name = f"role {role.value!r}" )


def _nativize_message_content(
    model: Model, canister: __.MessageCanister
) -> OpenAiMessageContent:
    # TODO: Handle audio and image contents.
    match len( canister ):
        case 0: return ''
        case 1: return canister[ 0 ].data
        case _:
            # Build multipart message.
            return [
                { 'type': 'text', 'text': content.data }
                for content in canister ]


def _nativize_result_message(
    model: Model, canister: __.MessageCanister
) -> OpenAiMessage:
    attributes = canister.attributes
    content: OpenAiMessageContent
    context = { 'role': 'user' }
    model_context = getattr( attributes, 'model_context', { } ).copy( )
    supports_invocations = (
            model.attributes.supports_invocations
        and model.provider.name == model_context[ 'provider' ] )
    supplement = model_context[ 'supplement' ]
    if supports_invocations:
        role = supplement.get(
            'role', 'tool' if 'tool_call_id' in supplement else 'function' )
        supplement[ 'role' ] = role
        supports_invocations = (
                ( 'function' == role and 'tool_call_id' not in supplement )
            or  ( 'tool' == role and 'tool_call_id' in supplement ) )
    if supports_invocations:
        match model.attributes.invocations_support_level:
            case InvocationsSupportLevels.Single:
                supports_invocations = 'function' == role
            case InvocationsSupportLevels.Concurrent: pass
    if not supports_invocations:
        content = '\n\n'.join( (
            '## Functions Invocation Result ##', canister[ 0 ].data ) )
        return dict( content = content, **context )
    context.update( supplement )
    content = _nativize_message_content( model, canister )
    return dict( content = content, **context )


def _nativize_supervisor_message(
    model: Model, canister: __.MessageCanister
) -> OpenAiMessage:
    content: OpenAiMessageContent
    if model.attributes.honors_supervisor_instructions: role = 'system'
    else: role = 'user' # TODO? Add 'name' field to indicate supervisor.
    context = { 'role': role }
    content = _nativize_message_content( model, canister )
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
) -> OpenAiMessage:
    content: OpenAiMessageContent
    context = { 'role': 'user' }
    content = _nativize_message_content( model, canister )
    return dict( content = content, **context )


def _postprocess_response_canisters( model, indices, reactors ):
    # TODO: Callbacks support for response arrays.
    for index, canister in indices.canisters.items( ):
        if index: continue
        if not ( record := indices.records.get( index ) ): continue
        canister.attributes.model_context[ 'supplement' ] = record
        if 'tool_calls' in record:
            invocation_data = _reconstitute_invocations( record )
        elif 'function_call' in record:
            invocation_data = _reconstitute_legacy_invocation( record )
        else: invocation_data = None
        if invocation_data:
            canister.attributes.invocation_data = invocation_data
        reactors.updater( indices.references[ index ] )


def _process_complete_response_v0( model, response, reactors ):
    # TODO? Collect usage stats.
    indices = __.AccretiveNamespace(
        canisters = __.AccretiveDictionary( ),
        records = __.AccretiveDictionary( ),
        references = __.AccretiveDictionary( ) )
    indices.canisters.update( {
        element.index: _canister_from_response_element( model, element )
        for element in response.choices } )
    indices.records.update( {
        element.index: dict( function_call = element.message.function_call )
        for element in response.choices if element.message.function_call } )
    indices.records.update( {
        element.index: dict( tool_calls = element.message.tool_calls )
        for element in response.choices if element.message.tool_calls } )
    # TODO: Callbacks support for response arrays.
    indices.references.update( {
        index: reactors.allocator( canister ) for index, canister
        in indices.canisters.items( ) if not index } )
    _postprocess_response_canisters( model, indices, reactors )
    return indices.references[ 0 ]


async def _process_iterative_response_v0( model, response, reactors ):
    # TODO? Collect usage stats.
    indices = __.AccretiveNamespace(
        canisters = __.AccretiveDictionary( ),
        records = __.AccretiveDictionary( ),
        references = __.AccretiveDictionary( ) )
    async for segment in response:
        for element in segment.choices:
            try:
                _process_iterative_response_element_v0(
                    model, indices, element, reactors )
            except Exception:
                for reference in indices.references:
                    reactors.deallocator( reference )
                raise
    _postprocess_response_canisters( model, indices, reactors )
    # TODO: Callbacks support for response arrays.
    return indices.references[ 0 ]


def _process_iterative_response_element_v0(
    model, indices, element, reactors
):
    delta = element.delta
    if not (
        delta.content or delta.function_call or delta.tool_calls
    ): return # Fast forward until we know response species.
    if ( index := element.index ) not in indices.canisters:
        indices.canisters[ index ] = canister = (
            _canister_from_response_element( model, element ) )
        indices.references[ index ] = reactors.allocator( canister )
    canister = indices.canisters[ index ]
    if index: return # TODO: Callbacks support for response arrays.
    if delta.tool_calls:
        _collect_response_as_invocations_v0(
            model, indices, index, delta, reactors )
    elif delta.function_call:
        _collect_response_as_legacy_invocation_v0(
            model, indices, index, delta, reactors )
    elif delta.content:
        _collect_response_as_content_v0(
            model, indices, index, delta, reactors )


def _reconstitute_legacy_invocation( record ):
    from json import loads
    invocation = record[ 'function_call' ]
    return [ dict(
        name = invocation[ 'name' ],
        arguments = loads( invocation[ 'arguments' ] ),
    ) ]


def _reconstitute_invocations( record ):
    from json import loads
    invocations = record[ 'tool_calls' ]
    invocations_ = [ ]
    for invocation in invocations:
        function = invocation[ 'function' ]
        invocations_.append( dict(
            name = function[ 'name' ],
            arguments = loads( function[ 'arguments' ] ),
        ) )
    return invocations_


def _refine_native_assistant_message(
    model: Model, anchor: OpenAiMessage, cursor: OpenAiMessage
) -> NativeMessageRefinementActions:
    anchor_role = anchor[ 'role' ]
    cursor_role = cursor[ 'role' ]
    anchor_name = anchor.get( 'name' )
    cursor_name = cursor.get( 'name' )
    if anchor_role == cursor_role and anchor_name == cursor_name:
        _merge_native_message(
            model, anchor, cursor, indicate_elision = True )
        return NativeMessageRefinementActions.Merge
    return NativeMessageRefinementActions.Retain


def _refine_native_function_message(
    model: Model, anchor: OpenAiMessage, cursor: OpenAiMessage
) -> NativeMessageRefinementActions:
    # TODO: Appropriate error classes.
    cursor_role = cursor[ 'role' ]
    match cursor_role:
        case 'function':
            raise AssertionError(
                "Adjacent function results detected." )
        case 'tool':
            raise AssertionError(
                "Mixed function and tool call results detected." )
    return NativeMessageRefinementActions.Retain


def _refine_native_message(
    model: Model, anchor: OpenAiMessage, cursor: OpenAiMessage
) -> NativeMessageRefinementActions:
    # TODO: Appropriate error classes.
    # TODO? Consider models which allow some adjaceny. (gpt-3.5-turbo)
    anchor_role = anchor[ 'role' ]
    match anchor_role:
        case 'assistant':
            return _refine_native_assistant_message( model, anchor, cursor )
        case 'function':
            return _refine_native_function_message( model, anchor, cursor )
        case 'system': return NativeMessageRefinementActions.Retain
        case 'tool':
            return _refine_native_tool_message( model, anchor, cursor )
        case 'user':
            return _refine_native_user_message( model, anchor, cursor )
    raise AssertionError( f"Unknown anchor role: {anchor_role!r}" )


def _refine_native_messages(
    model: Model, messages_pre: list[ OpenAiMessage ]
) -> list[ OpenAiMessage ]:
    anchor = None
    messages: list[ OpenAiMessage ] = [ ]
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
    return messages


def _refine_native_tool_message(
    model: Model, anchor: OpenAiMessage, cursor: OpenAiMessage
) -> NativeMessageRefinementActions:
    # TODO: Appropriate error classes.
    cursor_role = cursor[ 'role' ]
    if 'function' == cursor_role:
        raise AssertionError(
            "Mixed function and tool call results detected." )
    return NativeMessageRefinementActions.Retain


def _refine_native_user_message(
    model: Model, anchor: OpenAiMessage, cursor: OpenAiMessage
) -> NativeMessageRefinementActions:
    # TODO: Appropriate error classes.
    anchor_role = anchor[ 'role' ]
    cursor_role = cursor[ 'role' ]
    anchor_name = anchor.get( 'name' )
    cursor_name = cursor.get( 'name' )
    if anchor_role == cursor_role and anchor_name == cursor_name:
        _merge_native_message(
            model, anchor, cursor, indicate_elision = True )
        return NativeMessageRefinementActions.Merge
    return NativeMessageRefinementActions.Retain
