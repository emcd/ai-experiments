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


ModelConfiguration: __.typx.TypeAlias = (
    __.cabc.Mapping[ str, __.typx.Any ] ) # TODO? Typed dictionary.
ConverserModelT = __.typx.TypeVar(
    'ConverserModelT', bound = 'ConverserModel', contravariant = True )


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
        descriptor: ModelConfiguration,
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
    def conversers( self ) -> 'ConverserOperations':
        ''' Operations for conversation models served by this client. '''
        raise NotImplementedError

    @property
    @__.abc.abstractmethod
    def variant( self ) -> _core.ProviderVariants:
        ''' Provider variant. '''
        raise NotImplementedError


class Model(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Represents an AI model. '''

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
    def address( self ) -> _core.ModelAddress:
        ''' Stable identity of model. '''
        return _core.ModelAddress(
            provider = self.provider.name,
            client = self.client.name,
            genus = self.genus,
            name = self.name )

    @property
    def descriptor( self ) -> _core.ModelDescriptor:
        ''' Runtime descriptor for model operations. '''
        return _core.ModelDescriptor(
            address = self.address,
            client = self.client,
            attributes = self.attributes )

    @property
    @__.abc.abstractmethod
    def genus( self ) -> _core.ModelGenera:
        ''' Model genus. '''
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
        args: __.NominativeArguments = __.accret.Dictionary( )
        # TODO: Control descriptors to definitions.
        args[ 'controls' ] = descriptor.get( 'controls', ( ) )
        return args


class ConverserModel(
    Model, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Represents AI chat model. '''

    attributes: 'ConverserAttributes'

    @property
    def genus( self ) -> _core.ModelGenera:
        ''' Model genus. '''
        return _core.ModelGenera.Converser


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
        args = __.accret.Dictionary(
            super( ).init_args_from_descriptor( descriptor ) )
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


class ConverserOperations(
    __.typx.Protocol[ ConverserModelT ],
):
    ''' Client-owned operations for conversation models. '''

    def nativize_controls(
        self,
        model: ConverserModelT,
        controls: __.cabc.Mapping[ str, __.Control.Instance ],
    ) -> __.typx.Any:
        ''' Converts normalized controls into native arguments. '''
        raise NotImplementedError

    def nativize_invocable(
        self, model: ConverserModelT, invoker: __.Invoker
    ) -> __.typx.Any:
        ''' Converts normalized invocable into native tool call. '''
        raise NotImplementedError

    def nativize_invocables(
        self,
        model: ConverserModelT,
        invokers: __.cabc.Iterable[ __.Invoker ],
    ) -> __.typx.Any:
        ''' Converts normalized invocables into native tool calls. '''
        raise NotImplementedError

    def requests_from_canister(  # noqa: PLR0913
        self,
        model: ConverserModelT,
        auxdata: __.CoreGlobals, *,
        supplements: __.accret.Dictionary,
        canister: __.MessageCanister,
        invocables: __.accret.Namespace,
        ignore_invalid_canister: bool = False,
    ) -> _core.InvocationsRequests:
        ''' Converts invocation requests into invoker coroutines. '''
        raise NotImplementedError

    async def execute_invocation(
        self, model: ConverserModelT, request: _core.InvocationRequest
    ) -> __.MessageCanister:
        ''' Uses invocable to produce result for conversation. '''
        raise NotImplementedError

    def nativize_messages_v0(
        self,
        model: ConverserModelT,
        canisters: __.MessagesCanisters,
        supplements,
    ) -> __.typx.Any:
        ''' Converts normalized message canisters into native messages. '''
        raise NotImplementedError

    def deserialize_data(
        self, model: ConverserModelT, data: str
    ) -> __.typx.Any:
        ''' Deserializes text in preferred format of model to data. '''
        raise NotImplementedError

    def serialize_data(
        self, model: ConverserModelT, data: __.typx.Any
    ) -> str:
        ''' Serializes data to text in preferred format of model. '''
        raise NotImplementedError

    async def count_text_tokens(
        self, model: ConverserModelT, text: str
    ) -> int:
        ''' Counts tokens, using tokenizer for model, in text. '''
        raise NotImplementedError

    async def count_conversation_tokens_v0(
        self, model: ConverserModelT, messages: __.MessagesCanisters,
        supplements,
    ) -> int:
        ''' Counts tokens across entire conversation. '''
        raise NotImplementedError

    async def converse_v0(
        self,
        model: ConverserModelT,
        messages: __.MessagesCanisters,
        supplements,
        controls: __.cabc.Mapping[ str, __.Control.Instance ],
        reactors,
    ):
        ''' Interacts with model to complete a round of conversation. '''
        raise NotImplementedError


# TODO: Python 3.12: Use type statement for aliases.
ClientsByName: __.typx.TypeAlias = __.cabc.Mapping[ str, Client ]
