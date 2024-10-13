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


class InvocationsSupportLevel( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Degree to which invocations are supported. '''

    Single      = 'single'      # Mid-2023.
    Concurrent  = 'concurrent'  # Late 2023 and beyond.


@__.standard_dataclass
class Attributes( __.ConverserAttributes ):
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
        args = (
            super( Attributes, Attributes )
            .init_args_from_descriptor( descriptor ) )
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


@__.standard_dataclass
class Model( __.ConverserModel ):

    @classmethod
    def from_descriptor(
        selfclass,
        client: __.Client,
        name: str,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        descriptor_ = dict( descriptor )
        attributes = Attributes.from_descriptor( descriptor_ )
        return selfclass(
            name = name, client = client, attributes = attributes )

    def deserialize_data( self, data: str ) -> __.a.Any:
        data_format = self.attributes.format_preferences.response_data
        match data_format:
            case __.DataFormatPreferences.JSON:
                from ....codecs.json import loads
                return loads( data )
        raise __.SupportError(
            f"Cannot deserialize data from {data_format.value} format." )

    def serialize_data( self, data: __.a.Any ) -> str:
        data_format = self.attributes.format_preferences.request_data
        match data_format:
            case __.DataFormatPreferences.JSON:
                from json import dumps
                return dumps( data )
        raise __.SupportError(
            f"Cannot serialize data to {data_format.value} format." )

    def extract_invocation_requests(
        self,
        auxdata: __.CoreGlobals,
        supplements: __.AccretiveDictionary,
        canister: __.MessageCanister,
        invocables: __.AbstractIterable[ __.Invocable ],
    ) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
        # TODO? Generalize - most does not need to be provider-specific.
        supplements[ 'model' ] = self
        from ....codecs.json import loads
        Error = __.InvocationFormatError
        try: requests = loads( canister[ 0 ].data )
        except Exception as exc: raise Error( str( exc ) ) from exc
        if not isinstance( requests, __.AbstractSequence ):
            raise Error( 'Tool use requests is not sequence.' )
        invokers = invocables.invokers
        model_context = getattr( canister.attributes, 'model_context', { } )
        tool_calls = model_context.get( 'tool_calls' )
        requests_ = [ ]
        for i, request in enumerate( requests ):
            if not isinstance( request, __.AbstractDictionary ):
                raise Error( 'Tool use request is not dictionary.' )
            if 'name' not in request:
                raise Error( 'Name is missing from tool use request.' )
            request_ = dict( request )
            name = request[ 'name' ]
            if name not in invokers:
                raise Error( f"Tool {name!r} is not available." )
            arguments = request.get( 'arguments', { } )
            request_[ 'invocable__' ] = __.partial_function(
                invokers[ name ],
                auxdata = auxdata,
                arguments = arguments,
                supplements = supplements )
            # TODO: Validate tool calls with model.
            if tool_calls: request_[ 'context__' ] = tool_calls[ i ]
            requests_.append( request_ )
        return requests_

    def produce_tokenizer( self ) -> Tokenizer:
        return Tokenizer( model = self )

    async def use_invocable(
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

    async def converse_v0(
        self,
        messages: __.AbstractSequence[ __.MessageCanister ],
        controls: __.AbstractDictionary[ str, __.Control ],
        specials,
        callbacks,
    ):
        # TODO: Implement.
        pass

    def nativize_invocable_v0(
        self,
        invocable, # TODO: Signature
    ):
        # TODO: Port from v0.
        from . import v0
        return v0._nativize_invocable( invocable, model_name = self.name )

    def nativize_messages_v0(
        self,
        messages: __.AbstractIterable[ __.MessageCanister ],
    ):
        # TODO: Port from v0.
        from . import v0
        return v0._nativize_messages( messages, model_name = self.name )


@__.standard_dataclass
class Tokenizer( __.ConversationTokenizer ):

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
        for message in model.nativize_messages_v0( messages ):
            tokens_count += tokens_per_message
            for index, value in message.items( ):
                value_ = value if isinstance( value, str ) else dumps( value )
                tokens_count += self.count_text_tokens( value_ )
                if 'name' == index: tokens_count += tokens_for_actor_name
        for invoker in special_data.get( 'invocables', ( ) ):
            tokens_count += (
                self.count_text_tokens( dumps(
                    model.nativize_invocable_v0( invoker ) ) ) )
            # TODO: Determine if metadata from multifunctions adds more tokens.
        return tokens_count
