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


''' Core classes and functions for vectorstores. '''


from __future__ import annotations

from . import __


# TODO: Use accretive validator dictionaries for registries.
client_preparers = __.AccretiveDictionary( )
server_preparers = __.AccretiveDictionary( )


@__.a.runtime_checkable
@__.dataclass( frozen = True, kw_only = True, slots = True )
class Provider( __.a.Protocol ):

    @__.abstract_member_function
    async def client_from_descriptor(
        self,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        raise NotImplementedError


def derive_vectorstores_location( auxdata: __.Globals, url: str ) -> __.Path:
    ''' Derives vectorstore location from configuration and URL. '''
    parts = __.urlparse( url )
    match parts.scheme:
        case '' | 'file':
            return __.Path( parts.path.format(
                application_name = auxdata.distribution.name,
                custom_data = auxdata.provide_data_location( ),
                user_data = auxdata.directories.user_data_path ),
                user_home = __.Path.home( ) ) / 'vectorstores'
        case _: raise NotImplementedError


async def prepare( auxdata: __.Globals ) -> __.AccretiveDictionary:
    ''' Ensures requested providers exist and returns vectorstore futures. '''
    client_providers = await prepare_client_providers( auxdata )
    return await prepare_clients( auxdata, client_providers )


async def prepare_clients(
    auxdata: __.Globals, providers: __.AccretiveDictionary
):
    ''' Prepares clients, including in-memory stores. '''
    # TODO: Return futures for background loading.
    #       https://docs.python.org/3/library/asyncio-future.html#asyncio.Future
    scribe = __.acquire_scribe( __package__ )
    registry = __.AccretiveDictionary( )
    descriptors = auxdata.configuration.get( 'vectorstores', ( ) )
    names = tuple( descriptor[ 'name' ] for descriptor in descriptors )
    providers_ = tuple(
        providers[ descriptor[ 'provider' ] ] for descriptor in descriptors )
    results = await __.gather_async(
        *(  provider.client_from_descriptor( auxdata, descriptor )
            for provider, descriptor in zip( providers_, descriptors ) ),
        return_exceptions = True )
    for name, descriptor, result in zip( names, descriptors, results ):
        match result:
            case __.g.Error( error ):
                summary = f"Could not load vectorstore {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( future ):
                registry[ name ] = dict(
                    name = name, data = descriptor, instance = future )
    return registry


async def prepare_client_providers( auxdata: __.Globals ):
    ''' Prepares client providers. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = auxdata.configuration.get( 'vectorstores', ( ) )
    names = frozenset(
        descriptor[ 'provider' ] for descriptor in descriptors )
    preparers = __.DictionaryProxy(
        { name: client_preparers[ name ]( auxdata ) for name in names } )
    results = await __.gather_async(
        *preparers.values( ), return_exceptions = True )
    providers = { }
    for name, result in zip( preparers.keys( ), results ):
        match result:
            case __.g.Error( error ):
                summary = (
                    "Could not prepare vectorstore client provider "
                    f"{name!r}." )
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( provider ):
                providers[ name ] = provider
    return providers
