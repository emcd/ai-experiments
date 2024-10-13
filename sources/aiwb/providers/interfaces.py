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


''' Abstract base classes and interfaces. '''


from __future__ import annotations

from . import __
from . import core as _core


@__.a.runtime_checkable
@__.standard_dataclass
class Client( __.a.Protocol ):
    ''' Interacts with AI provider. '''
    # TODO: Immutable class attributes.

    ModelGenera: __.a.ClassVar[ type[ _core.ModelGenera ] ] = (
        _core.ModelGenera )

    name: str
    attributes: _core.ClientAttributes
    factory: Factory

    @classmethod
    @__.abstract_member_function
    async def assert_environment(
        selfclass,
        auxdata: __.CoreGlobals,
    ):
        ''' Asserts necessary environment for client. '''
        raise NotImplementedError

    @classmethod
    @__.abstract_member_function
    async def from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        factory: Factory,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        factory: Factory,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        descriptor_ = dict( descriptor )
        # TODO: Raise error on missing name.
        name = descriptor_.pop( 'name' )
        attributes = _core.ClientAttributes.from_descriptor( descriptor_ )
        return __.AccretiveDictionary(
            name = name, attributes = attributes, factory = factory )

    @__.abstract_member_function
    async def access_model(
        self,
        auxdata: __.CoreGlobals,
        genus: _core.ModelGenera,
        name: str,
    ) -> Model:
        ''' Returns named model available from provider, if it exists. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def access_model_default(
        self,
        auxdata: __.CoreGlobals,
        genus: _core.ModelGenera,
    ) -> Model:
        ''' Returns default model available from provider, if it exists. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def survey_models(
        self,
        auxdata: __.CoreGlobals,
        genus: __.Optional[ _core.ModelGenera ] = __.absent,
    ) -> __.AbstractSequence[ Model ]:
        ''' Returns models available from provider.

            Accepts optional model genus as filter. If not supplied, then
            models from all genera are returned.
        '''
        raise NotImplementedError


@__.a.runtime_checkable
@__.standard_dataclass
class ConversationTokenizer( __.a.Protocol ):
    ''' Tokenizes conversation or piece of text for counting. '''
    # TODO: Immutable class attributes.

    model: ConverserModel

    # TODO: count_conversation_tokens

    @__.abstract_member_function
    def count_text_tokens( self, text: str ) -> int:
        ''' Counts tokens, using tokenizer for model, in text. '''
        raise NotImplementedError

    ## v0 Compatibility Functions ##
    # TODO: Remove once cutover to conversation objects is complete.

    @__.abstract_member_function
    def count_conversation_tokens_v0( self, messages, special_data ) -> int:
        ''' Counts tokens across entire conversation. '''
        raise NotImplementedError


@__.a.runtime_checkable
@__.standard_dataclass
class Factory( __.a.Protocol ):
    ''' Produces clients. '''
    # TODO: Immutable class attributes.

    name: str
    # TODO: Regenerative dictionary for configuration.
    configuration: __.AbstractDictionary[ str, __.a.Any ]

    @__.abstract_member_function
    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ) -> Client:
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError


@__.a.runtime_checkable
@__.standard_dataclass
class Model( __.a.Protocol ):
    ''' Represents an AI model. '''
    # TODO: Immutable class attributes.

    name: str
    client: Client


@__.a.runtime_checkable
@__.standard_dataclass
class ConverserModel( Model, __.a.Protocol ):
    ''' Represents an AI chat model. '''

    attributes: _core.ConverserAttributes

    @__.abstract_member_function
    def deserialize_data( self, data: str ) -> __.a.Any:
        ''' Deserializes text in preferred format of model to data. '''
        raise NotImplementedError

    @__.abstract_member_function
    def serialize_data( self, data: __.a.Any ) -> str:
        ''' Serializes data to text in preferred format of model. '''
        raise NotImplementedError

    @__.abstract_member_function
    def extract_invocation_requests(
        self,
        auxdata: __.CoreGlobals,
        supplements: __.AccretiveDictionary,
        canister: __.MessageCanister,
        invocables: __.AbstractIterable[ __.Invocable ],
    ):
        ''' Converts invocation requests into invoker coroutines. '''
        # TODO: Return InvocationRequest instance.
        raise NotImplementedError

    @__.abstract_member_function
    def produce_tokenizer( self ) -> ConversationTokenizer:
        ''' Provides appropriate tokenizer for conversations. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def use_invocable(
        self,
        # TODO: Use InvocationRequest instance as argument.
        request: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.MessageCanister:
        ''' Uses invocable to produce result for conversation. '''
        raise NotImplementedError

    ## v0 Compatibility Functions ##
    # TODO: Remove once cutover to conversation objects is complete.

    @__.abstract_member_function
    async def converse_v0(
        self,
        messages: __.AbstractSequence[ __.MessageCanister ],
        controls: __.AbstractDictionary[ str, __.Control ],
        specials, # TODO: Annotate.
        callbacks, # TODO: Annotate.
    ):
        ''' Interacts with model to complete a round of conversation. '''
        raise NotImplementedError

    @__.abstract_member_function
    def nativize_invocable_v0(
        self,
        invocable, # TODO: Signature
    ):
        ''' Converts normalized invocable into native tool call. '''
        raise NotImplementedError

    @__.abstract_member_function
    def nativize_messages_v0(
        self,
        messages: __.AbstractIterable[ __.MessageCanister ],
    ):
        ''' Converts normalized message canisters into native messages. '''
        raise NotImplementedError
