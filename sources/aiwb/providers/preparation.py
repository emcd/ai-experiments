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


''' Preparation of AI providers. '''


from . import __
from . import interfaces as _interfaces
from . import registries as _registries


def descriptors_from_configuration(
    auxdata: __.CoreGlobals
) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
    ''' Validates and returns descriptors from configuration. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = [ ]
    for descriptor in auxdata.configuration.get( 'providers', ( ) ):
        if 'name' not in descriptor:
            auxdata.notifications.enqueue_error(
                ValueError( "Descriptor missing name." ),
                "Could not load AI provider from configuration.",
                details = descriptor,
                scribe = scribe )
            continue
        if not descriptor.get( 'enable', True ): continue
        descriptors.append( descriptor )
    return tuple( descriptors )


async def prepare( auxdata: __.CoreGlobals ) -> __.AccretiveDictionary:
    ''' Prepares clients from configuration and returns futures to them. '''
    # TODO: Return clients and models.
    factories = await prepare_factories( auxdata )
    clients = await prepare_clients( auxdata, factories )
    #for client_name, client in clients.items( ):
    #    ic( client_name, await client.survey_models( auxdata ) )
    return clients


async def prepare_clients(
    auxdata: __.CoreGlobals,
    factories: __.AbstractDictionary[ str, _interfaces.Factory ],
) -> __.AbstractDictionary[ str, _interfaces.Client ]:
    ''' Prepares clients from configuration. '''
    # TODO: Return futures for background loading.
    #       https://docs.python.org/3/library/asyncio-future.html#asyncio.Future
    scribe = __.acquire_scribe( __package__ )
    clients = __.AccretiveDictionary( )
    descriptors = descriptors_from_configuration( auxdata )
    names = tuple( descriptor[ 'name' ] for descriptor in descriptors )
    factories_per_client = tuple(
        factories[ descriptor.get( 'factory', name ) ]
        for name, descriptor in zip( names, descriptors ) )
    results = await __.gather_async(
        *(  factory.produce_client( auxdata, descriptor )
            for factory, descriptor
            in zip( factories_per_client, descriptors ) ),
        return_exceptions = True )
    for name, descriptor, result in zip( names, descriptors, results ):
        match result:
            case __.g.Error( error ):
                summary = f"Could not load AI provider {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( client ):
                clients[ name ] = client
    return clients


async def prepare_factories(
    auxdata: __.CoreGlobals
) -> __.AbstractDictionary[ str, _interfaces.Factory ]:
    ''' Prepares factories from configuration. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = descriptors_from_configuration( auxdata )
    names = frozenset(
        descriptor.get( 'factory', descriptor[ 'name' ] )
        for descriptor in descriptors )
    preparers = __.DictionaryProxy(
        {   name: _registries.preparers_registry[ name ]( auxdata )
            for name in names } )
    results = await __.gather_async(
        *preparers.values( ), return_exceptions = True )
    factories = { }
    for name, result in zip( preparers.keys( ), results ):
        match result:
            case __.g.Error( error ):
                summary = f"Could not prepare AI provider factory {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( factory ):
                factories[ name ] = factory
    return factories
