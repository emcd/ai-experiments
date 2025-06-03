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


from __future__ import annotations

from . import __


# We do not want to import 'anthropic' package on module initialization,
# as it is not guaranteed to be available then. However, we can appease
# typecheckers by pretending as though it is available.
if __.a.TYPE_CHECKING:
    from anthropic import AsyncAnthropic as _AsyncAnthropic  # type: ignore
else:
    _AsyncAnthropic: __.a.TypeAlias = __.a.Any


ClientDescriptor: __.a.TypeAlias = __.AbstractDictionary[ str, __.a.Any ]


_model_genera = frozenset( (
    __.ModelGenera.Converser,
) )


class ProviderVariants( __.Enum ):
    ''' Anthropic provider variants. '''

    Anthropic =     'anthropic'
    AwsBedrock =    'aws-bedrock'
    GoogleVertex =  'google-vertex'

    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        provider: Provider,
        descriptor: ClientDescriptor,
    ) -> Client:
        match self:
            case ProviderVariants.Anthropic:
                client_class = AnthropicClient
            # TODO: Other variants.
        # TODO: Return future.
        return await client_class.from_descriptor(
            auxdata = auxdata, provider = provider, descriptor = descriptor )


class Client( __.Client, class_decorators = ( __.standard_dataclass, ) ):

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
        genus: __.Optional[ __.ModelGenera ] = __.absent,
    ) -> __.AbstractSequence[ __.Model ]:
        if __.absent is genus: genera = _model_genera
        else:
            genus = __.a.cast( __.ModelGenera, genus )
            genera = frozenset( { genus } ) & _model_genera
        return await __.memcache_acquire_models(
            auxdata,
            client = self,
            genera = genera,
            acquirer = __.partial_function(
                __.cache_acquire_model_names,
                acquirer = self._acquire_model_names ) )

    @__.abstract_member_function
    async def _acquire_model_names( self ) -> __.AbstractSequence[ str ]:
        ''' Acquires model names from API or other source. '''
        raise NotImplementedError


class AnthropicClient( Client, class_decorators = ( __.standard_dataclass, ) ):
    ''' Client which talks to native Anthropic service. '''

    @classmethod
    async def assert_environment( selfclass, auxdata: __.CoreGlobals ):
        from os import environ
        api_key_name = 'ANTHROPIC_API_KEY'
        if api_key_name not in environ:
            # TODO: Raise appropriate error.
            raise LookupError( f"Missing {api_key_name!r}." )

    @classmethod
    async def from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        provider: __.Provider,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
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

    async def _acquire_model_names( self ) -> __.AbstractSequence[ str ]:
        aliases = (
            'claude-3-opus-latest',
            'claude-3-5-haiku-latest',
            'claude-3-5-sonnet-latest',
            'claude-3-7-sonnet-latest',
            'claude-opus-4-0',
            'claude-sonnet-4-0',
        )
        results = tuple(
            model.id for model
            in ( await self.produce_implement( ).models.list( ) ).data
            if 'model' == model.type ) # pylint: disable=magic-value-comparison
        return sorted( frozenset( ( *aliases, *results ) ) )


# TODO: AwsBedrockClient


# TODO: GoogleVertexClient


class Provider( __.Provider, class_decorators = ( __.standard_dataclass, ) ):

    async def produce_client(
        self, auxdata: __.CoreGlobals, descriptor: ClientDescriptor
    ) -> Client:
        variant = ProviderVariants( descriptor.get( 'variant', 'anthropic' ) )
        return await variant.produce_client(
            auxdata, provider = self, descriptor = descriptor )


# https://docs.anthropic.com/en/docs/about-claude/models
# https://docs.anthropic.com/en/docs/resources/model-deprecations
# TODO: Move lists of models to providers data.
_model_names = __.DictionaryProxy( {
    ProviderVariants.Anthropic: (
        'claude-2.0',
        'claude-2.1',
        'claude-3-haiku-20240307',
        'claude-3-opus-20240229',
        'claude-3-opus-latest',
        'claude-3-sonnet-20240229',
        'claude-3-5-haiku-20241022',
        'claude-3-5-haiku-latest',
        'claude-3-5-sonnet-20240620',
        'claude-3-5-sonnet-20241022',
        'claude-3-5-sonnet-latest',
        'claude-3-7-sonnet-20250219',
        'claude-3-7-sonnet-latest',
        'claude-opus-4-0',
        'claude-opus-4-20250514',
        'claude-sonnet-4-0',
        'claude-sonnet-4-20250514',
    ),
    ProviderVariants.AwsBedrock: (
        'anthropic.claude-3-haiku-20240307-v1:0',
        'anthropic.claude-3-opus-20240229-v1:0',
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3-5-haiku-20241022-v1:0',
        'anthropic.claude-3-5-sonnet-20240620-v1:0',
        'anthropic.claude-3-5-sonnet-20241022-v2:0',
        'anthropic.claude-3-7-sonnet-20250219-v1:0',
        'anthropic.claude-opus-4-20250514-v1:0',
        'anthropic.claude-sonnet-4-20250514-v1:0',
    ),
    ProviderVariants.GoogleVertex: (
        'claude-3-haiku@20240307',
        'claude-3-opus@20240229',
        'claude-3-sonnet@20240229',
        'claude-3-5-haiku@20241022',
        'claude-3-5-sonnet@20240620',
        'claude-3-5-sonnet-v2@20241022',
        'claude-3-7-sonnet@20250219',
        'claude-opus-4@20250514',
        'claude-sonnet-4@20250514',
    ),
} )
# TODO? Use for AWS Bedrock and Google Vertex.
async def _acquire_model_names(
    auxdata: __.CoreGlobals, client: Client
) -> __.AbstractSequence[ str ]:
    return _model_names[ client.variant ]
