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


from . import __


# We do not want to import 'openai' package on module initialization,
# as it is not guaranteed to be available then. However, we can appease
# typecheckers by pretending as though it is available.
if __.a.TYPE_CHECKING:
    from openai import AsyncOpenAI as _AsyncOpenAI # type: ignore
else:
    _AsyncOpenAI: __.a.TypeAlias = __.a.Any


_supported_model_genera = frozenset( (
    __.ModelGenera.Converser,
) )


class Client(
    __.Client, dataclass_arguments = __.standard_dataclass_arguments
):

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

    async def survey_models(
        self,
        auxdata: __.CoreGlobals,
        genus: __.Optional[ __.ModelGenera ] = __.absent,
    ) -> __.AbstractSequence[ __.Model ]:
        supported_genera = (
            _supported_model_genera if __.absent is genus
            else frozenset(
                genus for genus_ in _supported_model_genera
                if genus is genus_ ) )
        in_cache, models = _consult_models_cache( self, supported_genera )
        if in_cache: return models
        models = [ ]
        integrators = await _cache_acquire_models_integrators( auxdata )
        names = await _cache_acquire_models( auxdata, self )
        for name in names:
            for genus_ in supported_genera:
                descriptor: __.AbstractDictionary[ str, __.a.Any ] = { }
                for integrator in integrators[ genus_ ]:
                    descriptor = integrator( name, descriptor )
                if not descriptor: continue
                #ic( name, descriptor )
                models.append( self._model_from_descriptor(
                    name = name,
                    genus = genus_,
                    descriptor = descriptor ) )
                _models_cache[ self.name ][ genus_ ].append( models[ -1 ] )
        return tuple( models )

    def _model_from_descriptor(
        self,
        name: str,
        genus: __.ModelGenera,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.Model:
        match genus:
            case __.ModelGenera.Converser:
                from . import conversers
                return conversers.Model.from_descriptor(
                    client = self, name = name, descriptor = descriptor )
        # TODO: Raise error on unmatched case.


# TODO: AzureClient


class OpenAIClient(
    Client,
    dataclass_arguments = __.standard_dataclass_arguments,
):

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
        factory: __.Factory,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        await selfclass.assert_environment( auxdata )
        # TODO: Return future which acquires models in background.
        return selfclass( **(
            super( ).init_args_from_descriptor(
                auxdata = auxdata,
                factory = factory,
                descriptor = descriptor ) ) )

    def produce_implement( self ) -> _AsyncOpenAI:
        from openai import AsyncOpenAI
        return AsyncOpenAI( )


class Factory(
    __.Factory, dataclass_arguments = __.standard_dataclass_arguments
):

    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        #variant = descriptor.get( 'variant' )
        # TODO: Produce Azure variant, if requested.
        client_class = OpenAIClient
        # TODO: Return future.
        return await client_class.from_descriptor(
            auxdata = auxdata, factory = self, descriptor = descriptor )


async def _cache_acquire_models(
    auxdata: __.CoreGlobals, client: Client
):
    # TODO? Use cache accessor from libcore.locations.
    from json import dumps, loads
    from operator import attrgetter
    from aiofiles import open as open_
    from openai import APIError
    scribe = __.acquire_scribe( __package__ )
    file = auxdata.provide_cache_location(
        'providers', 'openai', 'models.json' )
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


# TODO? models integrators cache as cell variable of wrapper function
_models_integrators_cache = { }


async def _cache_acquire_models_integrators(
    auxdata: __.CoreGlobals, force: bool = False
):
    # TODO: Register watcher on package data directory to flag updates.
    #       Maybe 'watchfiles.awatch' as asyncio callback with this function.
    # TODO? async mutex in case of clear-update during access
    if force or not _models_integrators_cache:
        _models_integrators_cache.clear( )
        _models_integrators_cache.update(
            await __.acquire_models_integrators( auxdata, __.provider_name ) )
    return __.DictionaryProxy( _models_integrators_cache )


_models_cache = __.AccretiveDictionary( )


def _consult_models_cache(
    client: Client, genera: frozenset[ __.ModelGenera ]
) -> tuple[ bool, tuple[ __.Model, ... ] ]:
    from accretive import ProducerDictionary
    # TODO: Consider cache expiration.
    if client.name in _models_cache:
        caches_by_genus = _models_cache[ client.name ]
        if all(
            genus in caches_by_genus for genus in __.ModelGenera
            if genus in genera
        ):
            return (
                True,
                tuple( __.chain.from_iterable(
                    caches_by_genus[ genus ]
                    for genus in __.ModelGenera if genus in genera ) ) )
    _models_cache[ client.name ] = ProducerDictionary( list )
    return False, ( )
