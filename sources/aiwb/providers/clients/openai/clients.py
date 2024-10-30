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
        provider: Provider,
        descriptor: ClientDescriptor,
    ) -> Client:
        match self:
            case ProviderVariants.OpenAi:
                client_class = OpenAiClient
            # TODO: Other variants.
        # TODO: Return future.
        return await client_class.from_descriptor(
            auxdata = auxdata, provider = provider, descriptor = descriptor )


class Client( __.Client, class_decorators = ( __.standard_dataclass, ) ):

    async def access_model(
        self,
        auxdata: __.CoreGlobals,
        genus: __.ModelGenera,
        name: str,
    ) -> __.Model:
        # TODO? Cache nested dictionary of models for performance.
        try:
            return next(
                model for model
                in await self.survey_models( auxdata, genus = genus )
                if name == model.name )
        except StopIteration:
            # TODO: Raise appropriate type of error.
            raise LookupError(
                f"Could not access {genus.value} model {name!r} "
                f"on provider {self.name!r}." ) from None

    async def access_model_default(
        self,
        auxdata: __.CoreGlobals,
        genus: __.ModelGenera,
    ) -> __.Model:
        defaults = getattr( self.attributes.defaults, f"{genus.value}_model" )
        models = await self.survey_models( auxdata = auxdata, genus = genus )
        models_by_name = __.DictionaryProxy( {
            model.name: model for model in models } )
        try:
            return next(
                models_by_name[ default ] for default in defaults
                if default in models_by_name )
        except StopIteration:
            # TODO: Raise appropriate type of error.
            raise LookupError(
                f"Could not access default {genus.value} model "
                f"on provider {self.name!r}." ) from None

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
            acquirer = _cache_acquire_model_names )


# TODO: MicrosoftAzureClient


class OpenAiClient( Client, class_decorators = ( __.standard_dataclass, ) ):

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


class Provider( __.Provider, class_decorators = ( __.standard_dataclass, ) ):

    async def produce_client(
        self, auxdata: __.CoreGlobals, descriptor: ClientDescriptor
    ) -> Client:
        variant = ProviderVariants( descriptor.get( 'variant', 'openai' ) )
        return await variant.produce_client(
            auxdata, provider = self, descriptor = descriptor )


async def _cache_acquire_model_names(
    auxdata: __.CoreGlobals, client: Client
) -> __.AbstractSequence[ str ]:
    # TODO? Use cache accessor from libcore.locations.
    from json import dumps, loads
    from operator import attrgetter
    from aiofiles import open as open_
    from openai import APIError
    scribe = __.acquire_scribe( __package__ )
    # TODO: Per-client cache.
    file = auxdata.provide_cache_location(
        'providers', __.provider_name, 'models.json' )
    if file.is_file( ):
        # TODO: Get cache expiration interval from configuration.
        interval = __.TimeDelta( seconds = 4 * 60 * 60 ) # 4 hours
        then = ( __.DateTime.now( __.TimeZone.utc ) - interval ).timestamp( )
        if file.stat( ).st_mtime > then:
            async with open_( file ) as stream:
                return loads( await stream.read( ) )
    try:
        models = sorted( map(
            attrgetter( 'id' ),
            ( await client.produce_implement( ).models.list( ) ).data ) )
    except APIError as exc:
        if file.is_file( ):
            auxdata.notifications.enqueue_apprisal(
                summary = "Connection error. Loading stale models cache.",
                exception = exc,
                scribe = scribe )
            async with open_( file ) as stream:
                return loads( await stream.read( ) )
        raise
    file.parent.mkdir( exist_ok = True, parents = True )
    async with open_( file, 'w' ) as stream:
        await stream.write( dumps( models, indent = 4 ) )
    return models
