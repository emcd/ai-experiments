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


from . import __
from . import core as _core
from . import exceptions as _exceptions


ModelDescriptor = __.typx.TypeVar(
    'ModelDescriptor' ) # TODO? Typed dictionary.


class Provider(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Produces clients. '''

    name: str
    # TODO: Reingester dictionary for configuration.
    configuration: __.cabc.Mapping[ str, __.typx.Any ]

    def __str__( self ) -> str: return f"AI provider {self.name!r}"

    @__.abc.abstractmethod
    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.cabc.Mapping[ str, __.typx.Any ]
    ) -> 'Client':
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError


class Client(
    __.immut.DataclassProtocol,
    __.typx.Protocol[ _core.ClientImplement, _core.ProviderVariants ],
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Interacts with AI provider. '''

    ModelGenera: __.typx.ClassVar[ type[ _core.ModelGenera ] ] = (
        _core.ModelGenera )

    name: str
    attributes: _core.ClientAttributes
    provider: 'Provider'

    @classmethod
    @__.abc.abstractmethod
    async def assert_environment(
        selfclass,
        auxdata: __.CoreGlobals,
    ):
        ''' Asserts necessary environment for client. '''
        raise NotImplementedError

    @classmethod
    @__.abc.abstractmethod
    async def from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        provider: 'Provider',
        descriptor: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> __.typx.Self:
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        provider: 'Provider',
        descriptor: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> __.NominativeArguments:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        descriptor_ = dict( descriptor )
        # TODO: Raise error on missing name.
        name = descriptor_.pop( 'name' )
        attributes = _core.ClientAttributes.from_descriptor( descriptor_ )
        return __.accret.Dictionary(
            name = name, attributes = attributes, provider = provider )

    def __str__( self ) -> str:
        return f"{self.provider} client {self.name!r}"

    async def access_model(
        self,
        auxdata: __.CoreGlobals,
        genus: _core.ModelGenera,
        name: str,
    ) -> 'Model':
        ''' Returns named model available from provider, if it exists. '''
        try:
            return next(
                model for model
                in await self.survey_models( auxdata, genus = genus )
                if name == model.name )
        except StopIteration:
            raise _exceptions.ModelInaccessibility(
                self.name, genus, name ) from None

    async def access_model_default(
        self,
        auxdata: __.CoreGlobals,
        genus: _core.ModelGenera,
    ) -> 'Model':
        ''' Returns default model available from provider, if it exists. '''
        defaults = getattr( self.attributes.defaults, f"{genus.value}_model" )
        models = await self.survey_models( auxdata = auxdata, genus = genus )
        models_by_name = __.types.MappingProxyType( {
            model.name: model for model in models } )
        # TODO: Default defaults from provider configuration.
        defaults = defaults or models_by_name
        try:
            return next(
                models_by_name[ default ] for default in defaults
                if default in models_by_name )
        except StopIteration:
            raise _exceptions.ModelInaccessibility(
                self.name, genus ) from None

    @__.abc.abstractmethod
    def produce_implement( self ) -> _core.ClientImplement:
        ''' Produces client implement to interact with provider. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def produce_model(
        self,
        genus: _core.ModelGenera,
        name: str,
        descriptor: ModelDescriptor,
    ) -> 'Model':
        ''' Produces model from descriptor. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def survey_models(
        self,
        auxdata: __.CoreGlobals,
        genus: __.Absential[ _core.ModelGenera ] = __.absent,
    ) -> __.cabc.Sequence[ 'Model' ]:
        ''' Returns models available from provider.

            Accepts optional model genus as filter. If not supplied, then
            models from all supported genera are returned.
        '''
        raise NotImplementedError

    @property
    @__.abc.abstractmethod
    def variant( self ) -> _core.ProviderVariants:
        ''' Provider variant. '''
        raise NotImplementedError


class ControlsProcessor(
    __.immut.DataclassProtocol, __.typx.Protocol[ _core.NativeControls ],
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Handles model controls. '''

    model: 'Model'

    @property
    def controls( self ) -> __.cabc.Sequence[ __.Control ]:
        ''' Array of controls available to model. '''
        return self.model.attributes.controls

    @property
    def control_names( self ) -> frozenset[ str ]:
        ''' Names of controls available to model. '''
        # TODO? Cache.
        # TODO: Recursively gather control names. (Requires definitions.)
        # TODO: Use 'control.name'. (Requires definitions.)
        return frozenset( { control[ 'name' ] for control in self.controls } )

    @__.abc.abstractmethod
    def nativize_controls(
        self,
        controls: __.cabc.Mapping[ str, __.Control.Instance ],
    ) -> _core.NativeControls:
        ''' Converts normalized controls into native arguments. '''
        raise NotImplementedError


class ConversationTokenizer(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Tokenizes conversation or piece of text for counting. '''

    model: 'ConverserModel'

    # TODO: count_conversation_tokens

    @__.abc.abstractmethod
    async def count_text_tokens( self, text: str ) -> int:
        ''' Counts tokens, using tokenizer for model, in text. '''
        raise NotImplementedError

    ## v0 Compatibility Functions ##
    # TODO: Remove once cutover to conversation objects is complete.

    @__.abc.abstractmethod
    async def count_conversation_tokens_v0(
        self, messages: __.MessagesCanisters, supplements
    ) -> int:
        ''' Counts tokens across entire conversation. '''
        raise NotImplementedError


class InvocationsProcessor(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Handles everything related to invocations. '''

    model: 'Model'

    @__.abc.abstractmethod
    async def __call__(
        self, request: _core.InvocationRequest
    ) -> __.MessageCanister: # TODO? Return InvocationResult.
        ''' Uses invocable to produce result for conversation. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def nativize_invocable( self, invoker: __.Invoker ) -> __.typx.Any:
        ''' Converts normalized invocable into native tool call. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def nativize_invocables(
        self,
        invokers: __.cabc.Iterable[ __.Invoker ],
    ) -> __.typx.Any:
        ''' Converts normalized invocables into native tool calls. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def requests_from_canister(
        self,
        auxdata: __.CoreGlobals, *,
        supplements: __.accret.Dictionary,
        canister: __.MessageCanister,
        invocables: __.accret.Namespace,
        ignore_invalid_canister: bool = False,
    ) -> _core.InvocationsRequests:
        ''' Converts invocation requests into invoker coroutines. '''
        # TODO: Return InvocationRequest instance.
        raise NotImplementedError


class MessagesProcessor(
    __.immut.DataclassProtocol, __.typx.Protocol[ _core.NativeMessages ],
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Handles everything related to messages. '''

    model: 'Model'

    # TODO: nativize_messages

    ## v0 Compatibility Functions ##
    # TODO: Remove once cutover to conversation objects is complete.

    @__.abc.abstractmethod
    def nativize_messages_v0(
        self,
        canisters: __.MessagesCanisters,
        supplements,
    ) -> _core.NativeMessages:
        ''' Converts normalized message canisters into native messages. '''
        raise NotImplementedError


class Model(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Represents an AI model. '''

    # TODO? Move client and name to ModelAddress class.
    #       Subclass from ModelAddress class.
    client: 'Client'
    name: str
    attributes: 'ModelAttributes'

    def __str__( self ) -> str:
        return f"{self.client} model {self.name!r}"

    @classmethod
    @__.abc.abstractmethod
    def from_descriptor(
        selfclass,
        client: 'Client',
        name: str,
        descriptor: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> __.typx.Self:
        ''' Produces model from descriptor dictionary. '''
        raise NotImplementedError

    @property
    @__.abc.abstractmethod
    def controls_processor( self ) -> 'ControlsProcessor':
        ''' Controls processor for model. '''
        raise NotImplementedError

    @property
    def provider( self ) -> 'Provider':
        ''' Provider for model. '''
        return self.client.provider


class ModelAttributes(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Attributes for all genera of AI models. '''

    controls: __.cabc.Sequence[ __.Control ] = ( )

    @classmethod
    @__.abc.abstractmethod
    def from_descriptor(
        selfclass,
        descriptor: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> __.typx.Self:
        ''' Produces model attributes from descriptor dictionary. '''
        raise NotImplementedError

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        descriptor: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> __.NominativeArguments:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.accret.Dictionary( )
        # TODO: Control descriptors to definitions.
        args[ 'controls' ] = descriptor.get( 'controls', ( ) )
        return args


class ConverserModel(
    Model, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Represents AI chat model. '''

    @property
    @__.abc.abstractmethod
    def invocations_processor( self ) -> 'InvocationsProcessor':
        ''' Invocations processor for model. '''
        raise NotImplementedError

    @property
    @__.abc.abstractmethod
    def messages_processor( self ) -> 'MessagesProcessor':
        ''' Conversation messages processor for model. '''
        raise NotImplementedError

    @property
    @__.abc.abstractmethod
    def serde_processor( self ) -> 'ConverserSerdeProcessor':
        ''' (De)serialization processor for model. '''
        raise NotImplementedError

    @property
    @__.abc.abstractmethod
    def tokenizer( self ) -> 'ConversationTokenizer':
        ''' Appropriate tokenizer for conversations. '''
        raise NotImplementedError

    ## v0 Compatibility Functions ##
    # TODO: Remove once cutover to conversation objects is complete.

    @__.abc.abstractmethod
    async def converse_v0(
        self,
        messages: __.cabc.Sequence[ __.MessageCanister ],
        supplements, # TODO: Annotate.
        controls: __.cabc.Mapping[ str, __.Control.Instance ],
        reactors, # TODO: Annotate.
    ):
        ''' Interacts with model to complete a round of conversation. '''
        raise NotImplementedError


class ConverserAttributes( ModelAttributes ):
    ''' Common attributes for AI chat models. '''

    accepts_supervisor_instructions: bool = False
    format_preferences: _core.ConverserFormatPreferences = (
        _core.ConverserFormatPreferences( ) )
    modalities: __.cabc.Sequence[ _core.ConverserModalities ] = (
        _core.ConverserModalities.Text, )
    supports_continuous_response: bool = False
    supports_invocations: bool = False
    tokens_limits: _core.ConverserTokensLimits = (
        _core.ConverserTokensLimits( ) )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        descriptor: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> __.NominativeArguments:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = super( ).init_args_from_descriptor( descriptor )
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
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' (De)serialization in preferred formats for converser model. '''

    model: 'ConverserModel'

    @__.abc.abstractmethod
    def deserialize_data( self, data: str ) -> __.typx.Any:
        ''' Deserializes text in preferred format of model to data. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def serialize_data( self, data: __.typx.Any ) -> str:
        ''' Serializes data to text in preferred format of model. '''
        raise NotImplementedError

    # TODO: deserialize_math / serialize_math

    # TODO: deserialize_text / serialize_text


# TODO: Python 3.12: Use type statement for aliases.
ClientsByName: __.typx.TypeAlias = __.cabc.Mapping[ str, Client ]
