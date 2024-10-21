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
# TODO? Use typed dictionary for OpenAiMessage.
OpenAiMessage: __.a.TypeAlias = dict[ str, __.a.Any ]


class InvocationsSupportLevel( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Degree to which invocations are supported. '''

    Single      = 'single'      # Mid-2023.
    Concurrent  = 'concurrent'  # Late 2023 and beyond.


class Attributes(
    __.ConverserAttributes,
    dataclass_arguments = __.standard_dataclass_arguments,
):
    ''' Common attributes for OpenAI chat models. '''

    extra_tokens_for_actor_name: int = 0
    extra_tokens_per_message: int = 0
    honors_supervisor_instructions: bool = False
    invocations_support_level: InvocationsSupportLevel = (
        InvocationsSupportLevel.Single )

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        args = super( ).init_args_from_descriptor( descriptor )
        sdescriptor = descriptor.get( 'special', { } )
        for arg_name in (
            'extra-tokens-for-actor-name',
            'extra-tokens-per-message',
            'honors-supervisor-instructions',
        ):
            arg = sdescriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        if 'invocations-support-level' in sdescriptor:
            args[ 'invocations_support_level' ] = (
                InvocationsSupportLevel(
                    sdescriptor[ 'invocations-support-level' ] ) )
        return selfclass( **args )


class ControlsProcessor(
    __.ControlsProcessor,
    dataclass_arguments = __.standard_dataclass_arguments,
 ):

    def nativize_controls(
        self,
        controls: __.AbstractDictionary[ str, __.Control.Instance ],
    ) -> dict[ str, __.a.Any ]:
        # TODO: Assert model name matches.
        args: dict[ str, __.a.Any ] = dict( model = controls[ 'model' ] )
        args.update( {
            name.replace( '-', '_' ): value
            for name, value in controls.items( )
            if name in self.control_names } )
        if self.model.attributes.supports_continuous_response:
            args[ 'stream' ] = True
        return args


class SerdeProcessor(
    __.ConverserSerdeProcessor,
    dataclass_arguments = __.standard_dataclass_arguments,
):

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


class Model(
    __.ConverserModel,
    dataclass_arguments = __.standard_dataclass_arguments,
):

    @classmethod
    def from_descriptor(
        selfclass,
        client: __.Client,
        name: str,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        args = __.AccretiveDictionary( client = client, name = name )
        args[ 'attributes' ] = (
            Attributes.from_descriptor( descriptor ) )
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
        messages: __.AbstractSequence[ __.MessageCanister ],
        supplements,
        controls: __.AbstractDictionary[ str, __.Control.Instance ],
        reactors,
    ):
        messages_native = (
            self.messages_processor.nativize_messages_v0( messages ) )
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
            raise __.ChatCompletionError( f"Error: {exc}" ) from exc
        should_stream = controls_native.get( 'stream', True )
        # TODO: Port from v0.
        from . import v0
        if self.attributes.supports_continuous_response and should_stream:
            return (
                await v0._process_iterative_chat_response(
                    response, reactors ) )
        return v0._process_complete_chat_response( response, reactors )


class InvocationsProcessor(
    __.InvocationsProcessor,
    dataclass_arguments = __.standard_dataclass_arguments,
):
    ''' Handles functions and tool calls. '''

    async def __call__(
        self,
        # TODO: Use InvocationRequest instance as argument.
        request: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.MessageCanister:
        request_context = request[ 'context__' ]
        result = await request[ 'invocable__' ]( )
        # TODO? Include provider and model in result context.
        if 'id' in request_context: # late 2023+ format: parallel tool calls
            result_context = dict(
                name = request_context[ 'function' ][ 'name' ],
                role = 'tool',
                tool_call_id = request_context[ 'id' ] )
        else: # mid-2023 format: single function call
            result_context = dict(
                name = request[ 'name' ], role = 'function' )
        from json import dumps
        message = dumps( result )
        canister = __.MessageCanister( 'Function' )
        canister.add_content( message, mimetype = 'application/json' )
        canister.attributes.model_context = result_context # TODO? Immutable
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
            case InvocationsSupportLevel.Concurrent:
                args[ 'tools' ] = [
                    {   'type': 'function',
                        'function': self.nativize_invocable( invoker ) }
                    for invoker in invokers ]
            case InvocationsSupportLevel.Single:
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
    ) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
        return __.invocation_requests_from_canister(
            processor = self,
            auxdata = auxdata,
            supplements = supplements,
            canister = canister,
            invocables = invocables,
            ignore_invalid_canister = ignore_invalid_canister )

    def validate_request(
        self,
        request: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        # TODO: Implement.
        return request


class MessagesProcessor(
    __.MessagesProcessor,
    dataclass_arguments = __.standard_dataclass_arguments,
):
    ''' Handles conversation messages in OpenAI format. '''

    def nativize_messages_v0(
        self,
        canisters: __.AbstractIterable[ __.MessageCanister ],
    ) -> list[ OpenAiMessage ]:
        messages_pre: list[ OpenAiMessage ] = [ ]
        for canister in canisters:
            if _decide_exclude_message( self.model, canister ): continue
            message = _nativize_message( self.model, canister )
            messages_pre.append( message )
        return _refine_native_messages( self.model, messages_pre )


def _decide_exclude_message(
    model: Model, canister: __.MessageCanister
) -> bool:
    if not model.attributes.accepts_supervisor_instructions:
        if 'Supervisor' == canister.role: return True
    return False


def _merge_native_message(
    model: Model, anchor: OpenAiMessage, cursor: OpenAiMessage
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
    join_content = [ {
        'type': 'text', 'text': f"... <elided {elision_role} response> ..."
    } ]
    anchor_content.extend( join_content )
    anchor_content.extend( cursor_content )
    # TODO? Merge multiple texts into single one.
    # TODO? Error if refusal message part encountered.


def _nativize_message(
    model: Model, canister: __.MessageCanister
) -> OpenAiMessage:
    attributes = canister.attributes
    # TODO: Account for provider which supplied context.
    # TODO: Appropriate error classes.
    context = getattr( attributes, 'model_context', { } ).copy( )
    if not ( role := context.get( 'role' ) ):
        role = _nativize_message_role( model, canister )
        context[ 'role' ] = role
    response_class = getattr( attributes, 'response_class', '' )
    if 'Document' == canister.role:
        content = '\n\n'.join( (
            '## Supplemental Information ##', canister[ 0 ].data ) )
        return dict( content = content, **context )
    if (    'Function' == canister.role
        and not model.attributes.supports_invocations
    ):
        content = '\n\n'.join( (
            '## Tool Call Result ##', canister[ 0 ].data ) )
        return dict( content = content, **context )
    if 'assistant' == role and 'invocation' == response_class:
        if 'tool_calls' in context:
            if not model.attributes.supports_invocations:
                context.pop( 'tool_calls' )
                content = '\n\n'.join( (
                    '## Tool Calls Request ##', canister[ 0 ].data ) )
                return dict( content = content, **context )
            return context
        if 'function_call' in context:
            if not model.attributes.supports_invocations:
                context.pop( 'function_call' )
                content = '\n\n'.join( (
                    '## Tool Call Request ##', canister[ 0 ].data ) )
                return dict( content = content, **context )
            return context
        raise AssertionError( "Invocation request with no context detected." )
    # TODO: Handle audio and image contents.
    if 1 == len( canister ): content = canister[ 0 ].data
    else:
        content = [
            { 'type': 'text', 'text': content_.data }
            for content_ in canister ]
    return dict( content = content, **context )


def _nativize_message_role(
    model: Model, canister: __.MessageCanister
) -> str:
    match canister.role:
        case 'Supervisor':
            if model.attributes.honors_supervisor_instructions:
                return 'system'
            return 'user'
        case 'Function':
            if model.attributes.supports_invocations:
                match model.attributes.invocations_support_level:
                    case InvocationsSupportLevel.Concurrent: return 'tool'
                    case InvocationsSupportLevel.Single: return 'function'
        case 'AI': return 'assistant'
        case _: return 'user'
    # TODO: Raise proper error.
    raise ValueError( f"Invalid role '{canister.role}'." )


def _refine_native_message(
    model: Model, anchor: OpenAiMessage, cursor: OpenAiMessage
) -> str:
    # TODO: Appropriate error classes.
    # TODO: Consider models which allow some adjaceny. (gpt-3.5-turbo)
    anchor_role = anchor[ 'role' ]
    cursor_role = cursor[ 'role' ]
    anchor_name = anchor.get( 'name' )
    cursor_name = cursor.get( 'name' )
    match anchor_role:
        case 'assistant':
            anchor_invocation = 'content' not in anchor
            cursor_invocation = 'content' not in cursor
            if anchor_role == cursor_role:
                if anchor_invocation or cursor_invocation:
                    raise AssertionError(
                        "Mixed assistant completion and invocation detected." )
                if anchor_name == cursor_name:
                    _merge_native_message( model, anchor, cursor )
                    return 'merge'
            return 'retain'
        case 'function':
            if 'function' == cursor_role:
                raise AssertionError( "Adjacent function results detected." )
            if 'tool' == cursor_role:
                raise AssertionError(
                    "Mixed function and tool call results detected." )
            return 'retain'
        case 'system': return 'retain'
        case 'tool':
            if 'function' == cursor_role:
                raise AssertionError(
                    "Mixed function and tool call results detected." )
            return 'retain'
        case 'user':
            if anchor_role == cursor_role and anchor_name == cursor_name:
                _merge_native_message( model, anchor, cursor )
                return 'merge'
            if '#document#' == cursor_role:
                cursor[ 'role' ] = 'user'
                _merge_native_message( model, anchor, cursor )
                return 'merge'
            return 'retain'
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
        if 'merge' == action: continue
        messages.append( anchor )
        anchor = cursor
    if anchor: messages.append( anchor )
    return messages


class Tokenizer(
    __.ConversationTokenizer,
    dataclass_arguments = __.standard_dataclass_arguments,
):

    def count_text_tokens( self, text: str ) -> int:
        from tiktoken import encoding_for_model, get_encoding
        try: encoding = encoding_for_model( self.model.name )
        # TODO? Warn about unknown model via callback.
        except KeyError: encoding = get_encoding( 'cl100k_base' )
        return len( encoding.encode( text ) )

    def count_conversation_tokens_v0( self, messages, special_data ) -> int:
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
        for invoker in special_data.get( 'invokers', ( ) ):
            tokens_count += (
                self.count_text_tokens( dumps(
                    iprocessor.nativize_invocable( invoker ) ) ) )
            # TODO: Determine if metadata from multifunctions adds more tokens.
        return tokens_count


def _nativize_supplements_v0( model: Model, supplements ):
    nomargs = { }
    if 'invokers' in supplements:
        nomargs.update(
            model.invocations_processor
            .nativize_invocables( supplements[ 'invokers' ] ) )
    return nomargs
