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


''' Clients for OpenAI AI provider. '''


from __future__ import annotations

from . import __


# We do not want to import 'openai' package on module initialization,
# as it is not guaranteed to be available then. However, we can appease
# typecheckers by pretending as though it is available.
if __.a.TYPE_CHECKING:
    from openai import AsyncOpenAI as _AsyncOpenAI # type: ignore
else:
    _AsyncOpenAI: __.a.TypeAlias = __.a.Any


ClientDescriptor: __.a.TypeAlias = __.AbstractDictionary[ str, __.a.Any ]


_model_genera = frozenset( (
    __.ModelGenera.Converser,
) )


class ProviderVariants( __.Enum ):
    ''' OpenAI client variants. '''

    OpenAi =            'openai'
    MicrosoftAzure =    'microsoft-azure'

    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        provider: 'Provider',
        descriptor: ClientDescriptor,
    ) -> 'Client':
        match self:
            case ProviderVariants.OpenAi:
                client_class = OpenAiClient
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


# TODO: MicrosoftAzureClient


class OpenAiClient( Client ):
    ''' Client which talks to native OpenAI service. '''

    @classmethod
    async def assert_environment( selfclass, auxdata: __.CoreGlobals ):
        from os import environ
        api_key_name = 'OPENAI_API_KEY'
        if api_key_name not in environ:
            # TODO: Raise appropriate error.
            raise LookupError( f"Missing {api_key_name!r}." )
        # TODO: Warn on missing 'OPENAI_ORG_ID' and 'OPENAI_PROJECT_ID'.

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

    def produce_implement( self ) -> _AsyncOpenAI:
        from openai import AsyncOpenAI
        return AsyncOpenAI( )

    @property
    def variant( self ) -> ProviderVariants:
        return ProviderVariants.OpenAi

    async def _acquire_model_names( self ) -> __.AbstractSequence[ str ]:
        return sorted( map(
            lambda model: model.id,
            ( await self.produce_implement( ).models.list( ) ).data ) )


class Provider( __.Provider ):

    async def produce_client(
        self, auxdata: __.CoreGlobals, descriptor: ClientDescriptor
    ) -> Client:
        variant = ProviderVariants( descriptor.get( 'variant', 'openai' ) )
        return await variant.produce_client(
            auxdata, provider = self, descriptor = descriptor )
