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
            acquirer = _acquire_model_names )


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


# TODO: AwsBedrockClient


# TODO: GoogleVertexClient


class Provider( __.Provider, class_decorators = ( __.standard_dataclass, ) ):

    async def produce_client(
        self, auxdata: __.CoreGlobals, descriptor: ClientDescriptor
    ) -> Client:
        variant = ProviderVariants( descriptor.get( 'variant', 'anthropic' ) )
        return await variant.produce_client(
            auxdata, provider = self, descriptor = descriptor )


# TODO: Move lists of models to providers data.
_model_names = __.DictionaryProxy( {
    ProviderVariants.Anthropic: (
        'claude-3-haiku-20240307',
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3-5-sonnet-20240620',
        'claude-3.5-sonnet-20241022',
    ),
    ProviderVariants.AwsBedrock: (
        'anthropic.claude-3-haiku-20240307-v1:0',
        'anthropic.claude-3-opus-20240229-v1:0',
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3-5-sonnet-20240620-v1:0',
        'anthropic.claude-3.5-sonnet-20241022-v2:0',
    ),
    ProviderVariants.GoogleVertex: (
        'claude-3-haiku@20240307',
        'claude-3-opus@20240229',
        'claude-3-sonnet@20240229',
        'claude-3-5-sonnet@20240620',
        'claude-3-5-sonnet-v2@20241022',
    ),
} )
async def _acquire_model_names(
    auxdata: __.CoreGlobals, client: Client
) -> __.AbstractSequence[ str ]:
    return _model_names[ client.variant ]


_models_by_client = __.AccretiveDictionary( )
async def _memcache_acquire_models(
    auxdata: __.CoreGlobals,
    client: Client,
    genera: __.AbstractCollection[ __.ModelGenera ],
    acquirer: __.a.Callable, # TODO: Full signature.
) -> __.AbstractSequence[ __.Model ]:
    # TODO: Consider cache expiration.
    if client.name in _models_by_client:
        models_by_genus = _models_by_client[ client.name ]
        if all( genus in models_by_genus for genus in genera ):
            return tuple( __.chain.from_iterable(
                models_by_genus[ genus ] for genus in genera ) )
    else:
        _models_by_client[ client.name ] = (
            __.AccretiveProducerDictionary( list ) )
    models_by_genus = _models_by_client[ client.name ]
    integrators = (
        await __.memcache_acquire_models_integrators(
            auxdata, provider = client.provider ) )
    names = await acquirer( auxdata, client )
    for genus in genera:
        models_by_genus[ genus ].clear( )
        for name in names:
            descriptor: __.AbstractDictionary[ str, __.a.Any ] = { }
            for integrator in integrators[ genus ]:
                # TODO: Pass client to get variant.
                descriptor = integrator( name, descriptor )
            if not descriptor: continue
            model = client.produce_model(
                name = name, genus = genus, descriptor = descriptor )
            models_by_genus[ genus ].append( model )
    return tuple( __.chain.from_iterable(
        models_by_genus[ genus ] for genus in genera ) )
