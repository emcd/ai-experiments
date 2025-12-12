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


''' Core implementations for Anthropic AI provider. '''


from . import __


# We do not want to import 'anthropic' package on module initialization,
# as it is not guaranteed to be available then. However, we can appease
# typecheckers by pretending as though it is available.
if __.typx.TYPE_CHECKING:
    from anthropic import AsyncAnthropic as _AsyncAnthropic  # type: ignore
else:
    _AsyncAnthropic: __.typx.TypeAlias = __.typx.Any


ClientDescriptor: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]


_model_genera = frozenset( (
    __.ModelGenera.Converser,
) )


class ProviderVariants( __.enum.Enum ):
    ''' Anthropic provider variants. '''

    Anthropic =     'anthropic'
    AwsBedrock =    'aws-bedrock'
    GoogleVertex =  'google-vertex'

    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        provider: 'Provider',
        descriptor: ClientDescriptor,
    ) -> 'Client':
        match self:
            case ProviderVariants.Anthropic:
                client_class = AnthropicClient
            # TODO: Other variants.
        # TODO: Return future.
        return await client_class.from_descriptor(
            auxdata = auxdata, provider = provider, descriptor = descriptor )


class Client( __.Client ):

    def produce_model(
        self,
        genus: __.ModelGenera,
        name: str,
        descriptor: __.ModelDescriptor,
    ) -> __.Model:
        match genus:
            case __.ModelGenera.Converser:
                from . import conversers
                return conversers.Model.from_descriptor(
                    client = self, name = name, descriptor = descriptor )
        raise NotImplementedError( f"Unsupported genus {genus.value!r}." )

    async def survey_models(
        self,
        auxdata: __.CoreGlobals,
        genus: __.Absential[ __.ModelGenera ] = __.absent,
    ) -> __.cabc.Sequence[ __.Model ]:
        if __.absent is genus: genera = _model_genera
        else:
            genus = __.typx.cast( __.ModelGenera, genus )
            genera = frozenset( { genus } ) & _model_genera
        return await __.memcache_acquire_models(
            auxdata,
            client = self,
            genera = genera,
            acquirer = __.funct.partial(
                __.cache_acquire_model_names,
                acquirer = self._acquire_model_names ) )

    @__.abc.abstractmethod
    async def _acquire_model_names( self ) -> __.cabc.Sequence[ str ]:
        ''' Acquires model names from API or other source. '''
        raise NotImplementedError


class AnthropicClient( Client ):
    ''' Client which talks to native Anthropic service. '''

    @classmethod
    async def assert_environment( selfclass, auxdata: __.CoreGlobals ):
        from os import environ
        api_key_name = 'ANTHROPIC_API_KEY'
        if api_key_name not in environ:
            raise __.ProviderCredentialsInavailability(
                'anthropic', api_key_name )

    @classmethod
    async def from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        provider: __.Provider,
        descriptor: __.cabc.Mapping[ str, __.typx.Any ],
    ) -> __.typx.Self:
        await selfclass.assert_environment( auxdata )
        # TODO: Return future which acquires models in background.
        return selfclass( **(
            super( ).init_args_from_descriptor(
                auxdata = auxdata,
                provider = provider,
                descriptor = descriptor ) ) )

    def produce_implement( self ) -> _AsyncAnthropic:
        from anthropic import AsyncAnthropic
        return AsyncAnthropic( )

    @property
    def variant( self ) -> ProviderVariants:
        return ProviderVariants.Anthropic

    async def _acquire_model_names( self ) -> __.cabc.Sequence[ str ]:
        aliases = (
            'claude-3-opus-latest',
            'claude-3-5-haiku-latest',
            'claude-3-7-sonnet-latest',
            'claude-opus-4-0',
            'claude-sonnet-4-0',
            'claude-sonnet-4-5',
            'claude-haiku-4-5',
            'claude-opus-4-5',
            'claude-opus-4-1',
        )
        results = tuple(
            model.id for model
            in ( await self.produce_implement( ).models.list( ) ).data
            if 'model' == model.type )
        return sorted( frozenset( ( *aliases, *results ) ) )


# TODO: AwsBedrockClient


# TODO: GoogleVertexClient


class Provider( __.Provider ):

    async def produce_client(
        self, auxdata: __.CoreGlobals, descriptor: ClientDescriptor
    ) -> Client:
        variant = ProviderVariants( descriptor.get( 'variant', 'anthropic' ) )
        return await variant.produce_client(
            auxdata, provider = self, descriptor = descriptor )


# https://docs.anthropic.com/en/docs/about-claude/models
# https://docs.anthropic.com/en/docs/resources/model-deprecations
# TODO: Move lists of models to providers data.
_model_names = __.types.MappingProxyType( {
    ProviderVariants.Anthropic: (
        'claude-2.0',
        'claude-2.1',
        'claude-3-haiku-20240307',
        'claude-3-opus-20240229',
        'claude-3-opus-latest',
        'claude-3-sonnet-20240229',
        'claude-3-5-haiku-20241022',
        'claude-3-5-haiku-latest',
        'claude-3-7-sonnet-20250219',
        'claude-3-7-sonnet-latest',
        'claude-opus-4-20250514',
        'claude-sonnet-4-20250514',
        'claude-sonnet-4-5-20250929',
        'claude-haiku-4-5-20251001',
        'claude-opus-4-5-20251101',
        'claude-opus-4-1-20250805',
    ),
    ProviderVariants.AwsBedrock: (
        'anthropic.claude-3-haiku-20240307-v1:0',
        'anthropic.claude-3-opus-20240229-v1:0',
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3-5-haiku-20241022-v1:0',
        'anthropic.claude-3-7-sonnet-20250219-v1:0',
        'anthropic.claude-opus-4-20250514-v1:0',
        'anthropic.claude-sonnet-4-20250514-v1:0',
        'anthropic.claude-sonnet-4-5-20250929-v1:0',
        'anthropic.claude-haiku-4-5-20251001-v1:0',
        'anthropic.claude-opus-4-5-20251101-v1:0',
        'anthropic.claude-opus-4-1-20250805-v1:0',
    ),
    ProviderVariants.GoogleVertex: (
        'claude-3-haiku@20240307',
        'claude-3-opus@20240229',
        'claude-3-sonnet@20240229',
        'claude-3-5-haiku@20241022',
        'claude-3-7-sonnet@20250219',
        'claude-opus-4@20250514',
        'claude-sonnet-4@20250514',
        'claude-sonnet-4-5@20250929',
        'claude-haiku-4-5@20251001',
        'claude-opus-4-5@20251101',
        'claude-opus-4-1@20250805',
    ),
} )
# TODO? Use for AWS Bedrock and Google Vertex.
async def _acquire_model_names(
    auxdata: __.CoreGlobals, client: Client
) -> __.cabc.Sequence[ str ]:
    return _model_names[ client.variant ]
