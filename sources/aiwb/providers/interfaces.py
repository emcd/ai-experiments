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


class Client(
    __.a.Protocol[ _core.ClientImplement ],
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Interacts with AI provider. '''

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
    def produce_implement( self ) -> _core.ClientImplement:
        ''' Produces client implement to interact with provider. '''
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


class ControlsProcessor(
    __.a.Protocol[ _core.NativeControls ],
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Handles model controls. '''

    model: Model

    @property
    def controls( self ) -> __.AbstractSequence[ __.Control ]:
        ''' Array of controls available to model. '''
        return self.model.attributes.controls

    @property
    def control_names( self ) -> frozenset[ str ]:
        ''' Names of controls available to model. '''
        # TODO? Cache.
        # TODO: Recursively gather control names. (Requires definitions.)
        # TODO: Use 'control.name'. (Requires definitions.)
        return frozenset( { control[ 'name' ] for control in self.controls } )

    @__.abstract_member_function
    def nativize_controls(
        self,
        controls: __.AbstractDictionary[ str, __.Control.Instance ],
    ) -> _core.NativeControls:
        ''' Converts normalized controls into native arguments. '''
        raise NotImplementedError


class ConversationTokenizer(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Tokenizes conversation or piece of text for counting. '''

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


class Factory(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Produces clients. '''

    name: str
    # TODO: Reingester dictionary for configuration.
    configuration: __.AbstractDictionary[ str, __.a.Any ]

    @__.abstract_member_function
    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ) -> Client:
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError


class InvocationsProcessor(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Handles everything related to invocations. '''

    model: Model

    @__.abstract_member_function
    async def __call__(
        self,
        # TODO: Use InvocationRequest instance as argument.
        request: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.MessageCanister: # TODO? Return InvocationResult.
        ''' Uses invocable to produce result for conversation. '''
        raise NotImplementedError

    @__.abstract_member_function
    def nativize_invocable( self, invoker: __.Invoker ) -> __.a.Any:
        ''' Converts normalized invocable into native tool call. '''
        raise NotImplementedError

    @__.abstract_member_function
    def nativize_invocables(
        self,
        invokers: __.AbstractIterable[ __.Invoker ],
    ) -> __.a.Any:
        ''' Converts normalized invocables into native tool calls. '''
        raise NotImplementedError

    @__.abstract_member_function
    def requests_from_canister(
        self,
        auxdata: __.CoreGlobals, *,
        supplements: __.AccretiveDictionary,
        canister: __.MessageCanister,
        invocables: __.AccretiveNamespace,
        ignore_invalid_canister: bool = False,
    ):
        ''' Converts invocation requests into invoker coroutines. '''
        # TODO: Return InvocationRequest instance.
        raise NotImplementedError

    @__.abstract_member_function
    def validate_request(
        self,
        request: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Validates provider-specific portion of invocation request. '''
        raise NotImplementedError


class MessagesProcessor(
    __.a.Protocol[ _core.NativeMessages ],
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Handles everything related to messages. '''

    model: Model

    # TODO: nativize_messages

    ## v0 Compatibility Functions ##
    # TODO: Remove once cutover to conversation objects is complete.

    @__.abstract_member_function
    def nativize_messages_v0(
        self,
        messages: __.AbstractIterable[ __.MessageCanister ],
    ) -> _core.NativeMessages:
        ''' Converts normalized message canisters into native messages. '''
        raise NotImplementedError


class Model(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Represents an AI model. '''

    # TODO: Move client and name to ModelAddress class.
    #       Subclass from ModelAddress class.
    client: Client
    name: str
    attributes: ModelAttributes

    @classmethod
    @__.abstract_member_function
    def from_descriptor(
        selfclass,
        client: Client,
        name: str,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces model from descriptor dictionary. '''
        raise NotImplementedError

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        client: Client,
        name: str,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.AccretiveDictionary( client = client, name = name )
        classes = selfclass.provide_classes( )
        args[ 'attributes' ] = (
            classes.attributes
            .from_descriptor( descriptor = descriptor, **args ) )
        return __.AccretiveDictionary( **args )

    @property
    @__.abstract_member_function
    def controls_processor( self ) -> ControlsProcessor:
        ''' Controls processor for model. '''
        raise NotImplementedError

    @classmethod
    @__.abstract_member_function
    def provide_classes( selfclass ) -> ModelAttributesClasses:
        ''' Returns classes for model attributes. '''
        # TODO: Remove.
        raise NotImplementedError


class ModelAttributesClasses(
    metaclass = __.ImmutableDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
):
    ''' Classes for model attributes. '''

    attributes: type[ ModelAttributes ]


class ModelAttributes(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Attributes for all genera of AI models. '''

    client: Client
    name: str
    controls: __.AbstractSequence[ __.Control ] = ( )

    @classmethod
    @__.abstract_member_function
    def from_descriptor(
        selfclass,
        client: Client,
        name: str,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces model attributes from descriptor dictionary. '''
        raise NotImplementedError

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        client: Client,
        name: str,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.AccretiveDictionary( client = client, name = name )
        # TODO: Control descriptors to definitions.
        args[ 'controls' ] = descriptor.get( 'controls', ( ) )
        return args


class ConverserModel(
    Model, __.a.Protocol,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' Represents AI chat model. '''

    @property
    @__.abstract_member_function
    def invocations_processor( self ) -> InvocationsProcessor:
        ''' Invocations processor for model. '''
        raise NotImplementedError

    @property
    @__.abstract_member_function
    def messages_processor( self ) -> MessagesProcessor:
        ''' Conversation messages processor for model. '''
        raise NotImplementedError

    @property
    @__.abstract_member_function
    def serde_processor( self ) -> ConverserSerdeProcessor:
        ''' (De)serialization processor for model. '''
        raise NotImplementedError

    @property
    @__.abstract_member_function
    def tokenizer( self ) -> ConversationTokenizer:
        ''' Appropriate tokenizer for conversations. '''
        raise NotImplementedError

    ## v0 Compatibility Functions ##
    # TODO: Remove once cutover to conversation objects is complete.

    @__.abstract_member_function
    async def converse_v0(
        self,
        messages: __.AbstractSequence[ __.MessageCanister ],
        supplements, # TODO: Annotate.
        controls: __.AbstractDictionary[ str, __.Control.Instance ],
        reactors, # TODO: Annotate.
    ):
        ''' Interacts with model to complete a round of conversation. '''
        raise NotImplementedError


class ConverserAttributes(
    ModelAttributes,
    dataclass_arguments = __.standard_dataclass_arguments,
):
    ''' Common attributes for AI chat models. '''

    accepts_supervisor_instructions: bool = False
    format_preferences: _core.ConverserFormatPreferences = (
        _core.ConverserFormatPreferences( ) )
    modalities: __.AbstractSequence[ _core.ConverserModalities ] = (
        _core.ConverserModalities.Text, )
    supports_continuous_response: bool = False
    supports_invocations: bool = False
    tokens_limits: _core.ConverserTokensLimits = (
        _core.ConverserTokensLimits( ) )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        client: Client,
        name: str,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = (
            super( ).init_args_from_descriptor(
                client = client, name = name, descriptor = descriptor ) )
        for arg_name in (
            'accepts-supervisor-instructions',
            'supports-continuous-response',
            'supports-invocations',
        ):
            arg = descriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        args[ 'format_preferences' ] = (
            _core.ConverserFormatPreferences.from_descriptor(
                descriptor.get( 'format-preferences', { } ) ) )
        args[ 'modalities' ] = tuple(
            _core.ConverserModalities( modality )
            for modality in descriptor.get( 'modalities', ( ) ) )
        args[ 'tokens_limits' ] = (
            _core.ConverserTokensLimits.from_descriptor(
                descriptor.get( 'tokens-limits', { } ) ) )
        return args


class ConverserSerdeProcessor(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    runtime_checkable = True,
):
    ''' (De)serialization in preferred formats for converser model. '''

    model: ConverserModel

    @__.abstract_member_function
    def deserialize_data( self, data: str ) -> __.a.Any:
        ''' Deserializes text in preferred format of model to data. '''
        raise NotImplementedError

    @__.abstract_member_function
    def serialize_data( self, data: __.a.Any ) -> str:
        ''' Serializes data to text in preferred format of model. '''
        raise NotImplementedError

    # TODO: deserialize_math / serialize_math

    # TODO: deserialize_text / serialize_text
