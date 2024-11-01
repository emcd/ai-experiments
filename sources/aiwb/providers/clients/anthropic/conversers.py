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


# TODO: Python 3.12: Use type statement for aliases.
# TODO? Use typing.TypedDictionary.
AnthropicControls: __.a.TypeAlias = dict[ str, __.a.Any ]
AnthropicMessage: __.a.TypeAlias = dict[ str, __.a.Any ]
AnthropicMessageContent: __.a.TypeAlias = str | list[ dict[ str, __.a.Any ] ]
AttributesDescriptor: __.a.TypeAlias = __.AbstractDictionary[ str, __.a.Any ]
ModelDescriptor: __.a.TypeAlias = __.AbstractDictionary[ str, __.a.Any ]


class Attributes(
    __.ConverserAttributes, class_decorators = ( __.standard_dataclass, )
):
    ''' Common attributes for Anthropic chat models. '''

    extra_tokens_per_message: int = 0
    supports_computer_use: bool = False

    @classmethod
    def from_descriptor(
        selfclass, descriptor: AttributesDescriptor
    ) -> __.a.Self:
        args = super( ).init_args_from_descriptor( descriptor )
        sdescriptor = descriptor.get( 'special', { } )
        for arg_name in (
            'extra-tokens-per-message',
            'supports-computer-use',
        ):
            arg = sdescriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        return selfclass( **args )


class ControlsProcessor(
    __.ControlsProcessor, class_decorators = ( __.standard_dataclass, )
 ):
    ''' Controls nativization for Anthropic chat models. '''

    def nativize_controls(
        self, controls: __.ControlsInstancesByName
    ) -> AnthropicControls:
        # TODO: Assert model name matches between object and controls.
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


class InvocationsProcessor(
    __.InvocationsProcessor, class_decorators = ( __.standard_dataclass, )
):
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
        return dict( tools = tools )

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
        specifics = supplement.get( 'specifics', [ ] )
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
    ''' Handles conversation messages in Anthropic format. '''

    def nativize_messages_v0(
        self, canisters: __.MessagesCanisters
    ) -> list[ AnthropicMessage ]:
        # TODO: return type: list[ anthropic.types.MessageParam ]
        messages_pre: list[ AnthropicMessage ] = [ ]
        for canister in canisters:
            if _decide_exclude_message( self.model, canister ): continue
            message = _nativize_message( self.model, canister )
            messages_pre.append( message )
        # TODO: Merge and refine.
        return messages_pre


class Model(
    __.ConverserModel, class_decorators = ( __.standard_dataclass, )
):
    ''' Anthropic chat model. '''

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
        Error = __.partial_function(
            __.ModelOperateFailure,
            model = self, operation = 'chat completion' )
        messages_native = (
            self.messages_processor.nativize_messages_v0( messages ) )
        ic( messages_native )
        # TODO: Collect supervisor instructions.
        controls_native = (
            self.controls_processor.nativize_controls( controls ) )
        #supplements_native = _nativize_supplements_v0( self, supplements )
        args = dict( # TODO: invocations and supervisor instructions
            messages = messages_native, **controls_native )
        client = self.client.produce_implement( )
        #should_stream = self.attributes.supports_continuous_response
        should_stream = False
        from anthropic import AnthropicError
        if should_stream:
            try: response = await client.messages.stream( **args )
            except AnthropicError as exc: raise Error( cause = exc ) from exc
            # TODO: Collect streaming response.
        else:
            try: response = await client.messages.create( **args )
            except AnthropicError as exc: raise Error( cause = exc ) from exc
            # TODO: Process complete response.
        ic( response )
        assert False


class SerdeProcessor(
    __.ConverserSerdeProcessor, class_decorators = ( __.standard_dataclass, )
):
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


class Tokenizer(
    __.ConversationTokenizer, class_decorators = ( __.standard_dataclass, )
):
    ''' Tokenizes conversations and text with Anthropic tokenizers. '''
    # TODO: async counter methods
    # Note: As of 2024-10-30, Anthropic has not released its tokenizer for the
    #       newer models. We, therefore, approximate as best we are able.
    #       Known reverse engineering attempts:
    #           https://github.com/javirandor/anthropic-tokenizer
    #           https://www.beren.io/2024-07-07-Right-to-Left-Integer-Tokenization/

    def count_text_tokens( self, text: str ) -> int:
        client = self.model.client.provide_implement( )
        from asyncio import get_running_loop
        from time import sleep
        task = get_running_loop( ).create_task( client.count_tokens( text ) )
        while not task.done( ): sleep( 0.001 )
        return task.result( )

    def count_conversation_tokens_v0(
        self, messages: __.MessagesCanisters, supplements
    ) -> int:
        # https://github.com/openai/openai-cookbook/blob/2e9704b3b34302c30174e7d8e7211cb8da603ca9/examples/How_to_count_tokens_with_tiktoken.ipynb
        #from json import dumps
        #model = self.model
        #tokens_per_message = model.attributes.extra_tokens_per_message
        tokens_count = 0
        # TODO: Implement.
        return tokens_count


def _decide_exclude_message(
    model: Model, canister: __.MessageCanister
) -> bool:
    role = __.MessageRole.from_canister( canister )
    match role:
        case __.MessageRole.Supervisor:
            # We collect system instructions separately,
            # since there is not an Anthropic message type for them.
            return True
    return False


def _nativize_assistant_message(
    model: Model, canister: __.MessageCanister
) -> AnthropicMessage:
    context = { 'role': 'assistant' }
    content = _nativize_message_content( model, canister )
    if hasattr( canister.attributes, 'invocation_data' ):
        context = _nativize_invocation_message( model, canister )
        if ( extra_content := context.pop( 'content', None ) ):
            if isinstance( content, str ):
                content = [ { 'text': content, 'type': 'text' } ]
            content.extend( extra_content )
#            if isinstance( content, str ):
#                if isinstance( extra_content, str ):
#                    content = "{content_0}\n\n{content_f}".format(
#                        content_0 = content, content_f = extra_content )
#                else:
#                    content = [
#                        { 'text': content, 'type': 'text' }, *extra_content ]
#            elif isinstance( extra_content, str ):
#                content.append( { 'text': extra_content, 'type': 'text' } )
#            else: content.extend( extra_content )
    return dict( content = content, **context )


def _nativize_document_message(
    model: Model, canister: __.MessageCanister
) -> AnthropicMessage:
    context = { 'role': 'user' }
    content = '\n\n'.join( (
        '## Supplemental Information ##', canister[ 0 ].data ) )
    return dict( content = content, **context )


def _nativize_invocation_message(
    model: Model, canister: __.MessageCanister
) -> AnthropicMessage:
    attributes = canister.attributes
    content: AnthropicMessageContent
    context = { 'role': 'assistant' }
    model_context = getattr( attributes, 'model_context', { } ).copy( )
    supplement = model_context.get( 'supplement', { } )
    supports_invocations = (
            model.attributes.supports_invocations
        and model.provider.name == model_context.get( 'provider' )
        and 'tool_use' in supplement )
    if not supports_invocations:
        from json import dumps
        content = '\n\n'.join( (
            '## Functions Invocation Request ##',
            dumps( canister.attributes.invocation_data ) ) )
        content = [ { 'text': content, 'type': 'text' } ]
    else: content = supplement[ 'tool_use' ]
    return dict( content = content, **context )


def _nativize_message(
    model: Model, canister: __.MessageCanister
) -> AnthropicMessage:
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
    model: Model, canister: __.MessageCanister
) -> AnthropicMessage:
    attributes = canister.attributes
    content: AnthropicMessageContent
    context = { 'role': 'user' }
    model_context = getattr( attributes, 'model_context', { } ).copy( )
    supports_invocations = (
            model.attributes.supports_invocations
        and model.provider.name == model_context.get( 'provider' ) )
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


def _nativize_user_message(
    model: Model, canister: __.MessageCanister
) -> AnthropicMessage:
    content: AnthropicMessageContent
    context = { 'role': 'user' }
    content = _nativize_message_content( model, canister )
    return dict( content = content, **context )
