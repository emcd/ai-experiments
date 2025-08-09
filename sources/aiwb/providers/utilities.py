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


''' Utilities for AI providers. '''


from . import __
from . import core as _core
from . import exceptions as _exceptions
from . import interfaces as _interfaces


async def acquire_provider_configuration(
    auxdata: __.CoreGlobals, name: str
) -> __.cabc.Mapping[ str, __.typx.Any ]:
    ''' Returns configuration dictionary for AI provider. '''
    directory = auxdata.distribution.provide_data_location( 'providers', name )
    # TODO: Raise error if provider data directory does not exist.
    configuration = { }
    for configuration_ in await __.asyncf.gather_async(
        _acquire_configuration( auxdata, directory ),
        _acquire_configurations( auxdata, directory, 'model-families' ),
        _acquire_configurations( auxdata, directory, 'models' )
    ): configuration.update( configuration_ )
    # Extend from custom configuration.
    for index_name in ( 'model-families', 'models', ):
        configurations_ = _copy_custom_provider_configurations(
            auxdata, provider_name = name, index_name = index_name )
        # TODO: Raise error if no name in an entry.
        configuration[ index_name ] = tuple( sorted(
            configuration[ index_name ] + configurations_,
            key = lambda cfg: cfg[ 'name' ] ) )
    return __.types.MappingProxyType( configuration )


async def acquire_models_integrators(
    auxdata: __.CoreGlobals, name: str
) -> _core.ModelsIntegratorsByGenus:
    ''' Returns models integrators, general to specific, by genus. '''
    # TODO: Use provider configuration directly rather than loading.
    p_configuration = await acquire_provider_configuration( auxdata, name )
    # Longest model family names go last under the assumption that they are
    # more specific than shorter model family names with the same prefix and
    # thus should override them.
    mf_configurations = sorted(
        p_configuration.get( 'model-families', ( ) ),
        key = lambda mfc: len( mfc[ 'name' ] ) )
    m_configurations = p_configuration.get( 'models', ( ) )
    # Model families always go after the provider.
    # Specific models (and their aliases) always go after model families.
    configurations = ( p_configuration, *mf_configurations, *m_configurations )
    from collections import defaultdict
    integrators = defaultdict( list )
    for configuration in configurations:
        for genus in _core.ModelGenera:
            descriptor = configuration.get( genus.value )
            if not descriptor: continue
            # TODO: Improve error handling.
            #       Catch regex errors and provide proper context.
            integrators[ genus ].append(
                _core.ModelsIntegrator.from_descriptor( descriptor ) )
    return __.types.MappingProxyType( {
        genus: tuple( sequence ) for genus, sequence
        in integrators.items( ) } )


async def cache_acquire_model_names(
    auxdata: __.CoreGlobals,
    client: _interfaces.Client,
    acquirer: __.typx.Callable[
        [ ],
        __.cabc.Coroutine[ __.typx.Any, __.typx.Any, __.cabc.Sequence[ str ] ],
    ],
) -> __.cabc.Sequence[ str ]:
    ''' Acquires model names with persistent caching. '''
    # TODO? Use cache accessor from libcore.locations.
    from json import dumps, loads
    from aiofiles import open as open_
    scribe = __.acquire_scribe( __package__ )
    file = auxdata.provide_cache_location(
        'providers',
        client.provider.name,
        f'models--{client.variant.name}.json' )
    if file.is_file( ):
        # TODO: Get cache expiration interval from configuration.
        interval = __.TimeDelta( seconds = 4 * 60 * 60 ) # 4 hours
        then = ( __.DateTime.now( __.TimeZone.utc ) - interval ).timestamp( )
        if file.stat( ).st_mtime > then:
            async with open_( file ) as stream:
                return loads( await stream.read( ) )
    try: models = await acquirer( )
    except Exception as exc:
        if not file.is_file( ): raise
        auxdata.notifications.enqueue_apprisal(
            summary = "Connection error. Loading stale models cache.",
            exception = exc,
            scribe = scribe )
        async with open_( file ) as stream:
            return loads( await stream.read( ) )
    file.parent.mkdir( exist_ok = True, parents = True )
    async with open_( file, 'w' ) as stream:
        await stream.write( dumps( models, indent = 4 ) )
    return models


def invocation_requests_from_canister(
    auxdata: __.CoreGlobals,
    supplements: __.accret.Dictionary,
    canister: __.MessageCanister,
    invocables: __.accret.Namespace,
    ignore_invalid_canister: bool = False,
) -> _core.InvocationsRequests:
    Error = _exceptions.InvocationFormatError
    if not hasattr( canister.attributes, 'invocation_data' ):
        if ignore_invalid_canister: return [ ]
        raise Error( "Missing invocation data." ) # TODO: Better error.
    descriptors = canister.attributes.invocation_data
    if not isinstance( descriptors, __.cabc.Sequence ):
        if ignore_invalid_canister: return [ ]
        raise Error( "Invocations requests is not sequence." )
    # TODO: Construct context at caller.
    invokers = invocables.invokers
    context = __.accret.Namespace(
        auxdata = auxdata, invokers = invokers, supplements = supplements )
    # TODO: Handle errors from construction attempts.
    return tuple(
        _core.InvocationRequest.from_descriptor(
            descriptor = descriptor, context = context )
        for descriptor in descriptors )


_models_caches = __.accret.Dictionary( )
async def memcache_acquire_models(
    auxdata: __.CoreGlobals,
    client: _interfaces.Client,
    genera: __.cabc.Collection[ _core.ModelGenera ],
    acquirer: __.typx.Callable, # TODO: Full signature.
) -> __.cabc.Sequence[ _interfaces.Model ]:
    ''' Caches models in memory, as necessary. '''
    provider_name = client.provider.name
    if provider_name not in _models_caches:
        _models_caches[ provider_name ] = __.accret.Dictionary( )
    models_by_client = _models_caches[ provider_name ]
    client_name = client.name
    # TODO: Consider cache expiration.
    if client_name in models_by_client:
        models_by_genus = models_by_client[ client_name ]
        if all( genus in models_by_genus for genus in genera ):
            return tuple( __.chain.from_iterable(
                models_by_genus[ genus ] for genus in genera ) )
    else:
        models_by_client[ client_name ] = (
            __.accret.ProducerDictionary( list ) )
    models_by_genus = models_by_client[ client.name ]
    # TODO? async mutex in case of clear-update during access
    return await _memcache_acquire_models(
        auxdata, client = client, genera = genera, acquirer = acquirer )


_models_integrators_caches: __.cabc.Mapping[
    str, _core.ModelsIntegratorsByGenusMutable
] = __.accret.Dictionary( )
async def memcache_acquire_models_integrators(
    auxdata: __.CoreGlobals,
    provider: _interfaces.Provider,
    force: bool = False,
) -> _core.ModelsIntegratorsByGenus:
    ''' Caches models integrators in memory, as necessary. '''
    # TODO: Register watcher on package data directory to flag updates.
    #       Maybe 'watchfiles.awatch' as asyncio callback with this function.
    name = provider.name
    if name not in _models_integrators_caches:
        _models_integrators_caches[ name ] = { }
    cache = _models_integrators_caches[ name ]
    if force or not cache:
        # TODO? async mutex in case of clear-update during access
        cache.clear( )
        cache.update( await acquire_models_integrators( auxdata, name ) )
    return __.types.MappingProxyType( cache )


async def _acquire_configuration(
    auxdata: __.CoreGlobals, directory: __.Path
) -> __.cabc.Mapping[ str, __.typx.Any ]:
    from tomli import loads
    files = directory.glob( '*.toml' )
    acquirers = tuple(
        __.text_file_presenter_from_url( file ).acquire_content( )
        for file in files )
    configuration = { }
    for content in await __.asyncf.gather_async( *acquirers ):
        configuration.update( loads( content ) )
    return configuration


async def _acquire_configurations(
    auxdata: __.CoreGlobals, directory: __.Path, index_name: str
) -> __.cabc.Mapping[ str, __.typx.Any ]:
    subdirectories = tuple(
        entity for entity in directory.rglob( f"{index_name}/*" )
        if entity.is_dir( ) )
    acquirers = tuple(
        _acquire_configuration( auxdata, subdirectory )
        for subdirectory in subdirectories )
    configurations = await __.asyncf.gather_async( *acquirers )
    configurations_ = [ ]
    for subdirectory, configuration in zip( subdirectories, configurations ):
        configuration_ = { 'name': subdirectory.name }
        configuration_.update( configuration )
        configurations_.append( __.types.MappingProxyType( configuration_ ) )
    return __.types.MappingProxyType( { index_name: tuple( configurations_ ) } )


def _copy_custom_provider_configurations(
    auxdata: __.CoreGlobals, provider_name: str, index_name: str
) -> __.cabc.Sequence[ __.cabc.Mapping[ str, __.typx.Any ] ]:
    factory_descriptors = (
        auxdata.configuration.get( 'provider-factories', ( ) ) )
    try:
        configurations = next(
            descriptor for descriptor in factory_descriptors
            if provider_name == descriptor[ 'name' ] )
    except StopIteration: configurations = { }
    return tuple( configurations.get( index_name, ( ) ) )


async def _memcache_acquire_models(
    auxdata: __.CoreGlobals,
    client: _interfaces.Client,
    genera: __.cabc.Collection[ _core.ModelGenera ],
    acquirer: __.typx.Callable, # TODO: Full signature.
) -> __.cabc.Sequence[ _interfaces.Model ]:
    models_by_genus = _models_caches[ client.provider.name ][ client.name ]
    integrators = (
        await memcache_acquire_models_integrators(
            auxdata, provider = client.provider ) )
    names = await acquirer( auxdata, client )
    for genus in genera:
        models_by_genus[ genus ].clear( )
        for name in names:
            descriptor: __.cabc.Mapping[ str, __.typx.Any ] = { }
            for integrator in integrators[ genus ]:
                # TODO: Pass client to get variant.
                descriptor = integrator( name, descriptor )
            if not descriptor: continue
            model = client.produce_model(
                name = name, genus = genus, descriptor = descriptor )
            models_by_genus[ genus ].append( model )
    return tuple( __.chain.from_iterable(
        models_by_genus[ genus ] for genus in genera ) )
