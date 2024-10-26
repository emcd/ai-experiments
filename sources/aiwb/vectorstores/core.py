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


class Factory(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolClass,
    class_decorators = ( __.standard_dataclass, __.a.runtime_checkable ),
):
    ''' Produces clients. '''

    @__.abstract_member_function
    async def client_from_descriptor(
        self,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ):
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError


# TODO: Use accretive validator dictionary for preparers registry.
preparers = __.AccretiveDictionary( )


def derive_vectorstores_location( auxdata: __.Globals, url: str ) -> __.Path:
    ''' Derives vectorstore location from configuration and URL. '''
    parts = __.urlparse( url )
    match parts.scheme:
        case '' | 'file':
            return __.Path( parts.path.format(
                application_name = auxdata.application.name,
                custom_data = auxdata.provide_data_location( ),
                user_data = auxdata.directories.user_data_path ),
                user_home = __.Path.home( ) ) / 'vectorstores'
        case _: raise NotImplementedError


def descriptors_from_configuration(
    auxdata: __.Globals
) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
    ''' Validates and returns descriptors from configuration. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = [ ]
    for descriptor in auxdata.configuration.get( 'vectorstores', ( ) ):
        if 'name' not in descriptor:
            auxdata.notifications.enqueue_error(
                ValueError( "Descriptor missing name." ),
                "Could not load vectorstore from configuration.",
                details = descriptor,
                scribe = scribe )
            continue
        if not descriptor.get( 'enable', True ): continue
        descriptors.append( descriptor )
    return tuple( descriptors )


async def prepare( auxdata: __.Globals ) -> __.AccretiveDictionary:
    ''' Prepares clients from configuration and returns futures to them. '''
    factories = await prepare_factories( auxdata )
    return await prepare_clients( auxdata, factories )


async def prepare_clients(
    auxdata: __.Globals, factories: __.AccretiveDictionary
):
    ''' Prepares clients from configuration. '''
    # TODO: Return futures for background loading.
    #       https://docs.python.org/3/library/asyncio-future.html#asyncio.Future
    scribe = __.acquire_scribe( __package__ )
    clients = __.AccretiveDictionary( )
    descriptors = descriptors_from_configuration( auxdata )
    names = tuple( descriptor[ 'name' ] for descriptor in descriptors )
    factories_per_client = tuple(
        factories[ descriptor[ 'factory' ] ] for descriptor in descriptors )
    results = await __.gather_async(
        *(  factory.client_from_descriptor( auxdata, descriptor )
            for factory, descriptor
            in zip( factories_per_client, descriptors ) ),
        return_exceptions = True )
    for name, descriptor, result in zip( names, descriptors, results ):
        match result:
            case __.g.Error( error ):
                summary = f"Could not load vectorstore {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( future ):
                clients[ name ] = dict(
                    name = name, data = descriptor, instance = future )
    return clients


async def prepare_factories(
    auxdata: __.Globals
) -> __.AbstractDictionary[ str, Factory ]:
    ''' Prepares factories from configuration. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = descriptors_from_configuration( auxdata )
    names = frozenset(
        descriptor[ 'factory' ] for descriptor in descriptors )
    preparers_ = __.DictionaryProxy(
        { name: preparers[ name ]( auxdata ) for name in names } )
    results = await __.gather_async(
        *preparers_.values( ), return_exceptions = True )
    factories = { }
    for name, result in zip( preparers_.keys( ), results ):
        match result:
            case __.g.Error( error ):
                summary = "Could not prepare vectorstore factory {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( factory ):
                factories[ name ] = factory
    return factories
