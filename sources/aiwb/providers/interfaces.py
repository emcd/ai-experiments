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
@__.substandard_dataclass
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


@__.a.runtime_checkable
@__.standard_dataclass
class ControlsProcessor( __.a.Protocol ):
    ''' Handles model controls. '''
    # TODO: Immutable class attributes.

    client: Client
    name: str
    attributes: ModelAttributes
    controls: __.AbstractSequence[ __.Control ] = ( )

    @classmethod
    def from_descriptor(
        selfclass,
        client: Client,
        name: str,
        attributes: ModelAttributes,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces model controls processor from descriptor dictionary. '''
        args = selfclass.init_args_from_descriptor(
            client = client,
            name = name,
            attributes = attributes,
            descriptor = descriptor )
        return selfclass( **args )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        client: Client,
        name: str,
        attributes: ModelAttributes,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.AccretiveDictionary(
            client = client, name = name, attributes = attributes )
        # TODO: Control descriptors to definitions.
        args[ 'controls' ] = descriptor.get( 'controls', ( ) )
        return args

    @property
    def control_names( self ) -> frozenset[ str ]:
        ''' Names of available controls. '''
        # TODO: Cache.
        # TODO: Recursively gather control names. (Requires instantiation.)
        # TODO: Use 'control.name'. (Requires instantiation.)
        return frozenset( { control[ 'name' ] for control in self.controls } )

    @__.abstract_member_function
    def nativize_controls(
        self,
        controls: __.AbstractDictionary[ str, __.Control.Instance ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Converts normalized controls into native arguments. '''
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
class InvocationsProcessor( __.a.Protocol ):
    ''' Handles everything related to invocations. '''
    # TODO: Immutable class attributes.

    model: ConverserModel

    @__.abstract_member_function
    async def __call__(
        self,
        # TODO: Use InvocationRequest instance as argument.
        request: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.MessageCanister:
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
        invocables: __.AbstractIterable[ __.Invocable ],
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


@__.a.runtime_checkable
@__.substandard_dataclass
class Model( __.a.Protocol ):
    ''' Represents an AI model. '''
    # TODO: Immutable class attributes.

    client: Client
    name: str
    attributes: ModelAttributes
    attendants: ModelAttendants

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
        args[ 'attendants' ] = (
            classes.attendants
            .from_descriptor( descriptor = descriptor, **args ) )
        return __.AccretiveDictionary( **args )

    @classmethod
    @__.abstract_member_function
    def provide_classes( selfclass ) -> ModelAttributesClasses:
        ''' Returns classes for model attributes and attendants collection. '''
        raise NotImplementedError


@__.a.runtime_checkable
@__.substandard_dataclass
class ModelAttendants( __.a.Protocol ):
    ''' Attendants to assist all genera of models. '''
    # TODO: Immutable class attributes.

    controls: ControlsProcessor

    @classmethod
    def from_descriptor(
        selfclass,
        client: Client,
        name: str,
        attributes: ModelAttributes,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces model attendants from descriptor dictionary. '''
        args = (
            selfclass.init_args_from_descriptor(
                client = client,
                name = name,
                attributes = attributes,
                descriptor = descriptor ) )
        return selfclass( **args )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        client: Client,
        name: str,
        attributes: ModelAttributes,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.AccretiveDictionary( )
        args_ = __.AccretiveDictionary(
            client = client, name = name, attributes = attributes )
        classes = selfclass.provide_classes( )
        args[ 'controls' ] = (
            classes.controls
            .from_descriptor( descriptor = descriptor, **args_ ) )
        return args

    @classmethod
    @__.abstract_member_function
    def provide_classes( selfclass ) -> ModelAttendantsClasses:
        ''' Returns classes for model attendants. '''
        raise NotImplementedError


@__.standard_dataclass
class ModelAttendantsClasses:
    ''' Classes for model attendants. '''

    controls: type[ ControlsProcessor ]


@__.standard_dataclass
class ModelAttributesClasses:
    ''' Classes for model attributes and attendants collection. '''
    # TODO: Immutable class attributes.

    attributes: type[ ModelAttributes ]
    attendants: type[ ModelAttendants ]


@__.a.runtime_checkable
@__.substandard_dataclass
class ModelAttributes( __.a.Protocol ):
    ''' Attributes for all genera of AI models. '''
    # TODO: Immutable class attributes.

    client: Client
    name: str

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
        return __.AccretiveDictionary( client = client, name = name )


@__.a.runtime_checkable
@__.substandard_dataclass
class ConverserModel( Model, __.a.Protocol ):
    ''' Represents an AI chat model. '''

    @__.abstract_member_function
    def produce_invocations_processor( self ) -> InvocationsProcessor:
        ''' Provides invocations processor for model. '''
        raise NotImplementedError

    @__.abstract_member_function
    def produce_tokenizer( self ) -> ConversationTokenizer:
        ''' Provides appropriate tokenizer for conversations. '''
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

    @__.abstract_member_function
    def nativize_messages_v0(
        self,
        messages: __.AbstractIterable[ __.MessageCanister ],
    ):
        ''' Converts normalized message canisters into native messages. '''
        raise NotImplementedError


@__.a.runtime_checkable
@__.substandard_dataclass
class ConverserAttendants( ModelAttendants, __.a.Protocol ):
    ''' Attendants to assist converser models. '''
    # TODO: Immutable class attributes.

    serde: ConverserSerdeProcessor

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        client: Client,
        name: str,
        attributes: ModelAttributes,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = (
            super( ).init_args_from_descriptor(
                client = client,
                name = name,
                attributes = attributes,
                descriptor = descriptor ) )
        args_ = __.AccretiveDictionary(
            client = client, name = name, attributes = attributes )
        classes = selfclass.provide_classes( )
        args[ 'serde' ] = (
            classes.serde
            .from_descriptor( descriptor = descriptor, **args_ ) )
        return args


@__.standard_dataclass
class ConverserAttendantsClasses( ModelAttendantsClasses ):
    ''' Classes for converser attributes and attendants. '''

    # TODO: invocations
    # TODO: messages
    serde: type[ ConverserSerdeProcessor ]


@__.substandard_dataclass
class ConverserAttributes( ModelAttributes ):
    ''' Common attributes for AI chat models. '''
    # TODO: Immutable class attributes.

    accepts_supervisor_instructions: bool = False
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
        args[ 'modalities' ] = tuple(
            _core.ConverserModalities( modality )
            for modality in descriptor.get( 'modalities', ( ) ) )
        args[ 'tokens_limits' ] = (
            _core.ConverserTokensLimits.from_descriptor(
                descriptor.get( 'tokens-limits', { } ) ) )
        return args


@__.a.runtime_checkable
@__.standard_dataclass
class ConverserSerdeProcessor( __.a.Protocol ):
    ''' Serialization/deserialization in preferred formats for model. '''
    # TODO: Immutable class attributes.

    client: Client
    name: str
    attributes: ConverserAttributes
    preferences: _core.ConverserFormatPreferences

    @classmethod
    def from_descriptor(
        selfclass,
        client: Client,
        name: str,
        attributes: ConverserAttributes,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces model controls processor from descriptor dictionary. '''
        args = (
            selfclass.init_args_from_descriptor(
                client = client,
                name = name,
                attributes = attributes,
                descriptor = descriptor ) )
        return selfclass( **args )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        client: Client,
        name: str,
        attributes: ConverserAttributes,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.AccretiveDictionary(
            client = client, name = name, attributes = attributes )
        args[ 'preferences' ] = (
            _core.ConverserFormatPreferences.from_descriptor(
                descriptor.get( 'format-preferences', { } ) ) )
        return args

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
