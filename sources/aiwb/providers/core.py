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


''' Core classes and functions for AI providers. '''


from __future__ import annotations

from . import __


@__.a.runtime_checkable
@__.dataclass( frozen = True, kw_only = True, slots = True )
class Client( __.a.Protocol ):
    ''' Interacts with AI provider. '''

    name: str

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        return __.AccretiveDictionary( name = descriptor[ 'name' ] )

    @classmethod
    @__.abstract_member_function
    async def assert_environment(
        selfclass,
        auxdata: __.Globals,
    ):
        ''' Asserts necessary environment for client. '''
        raise NotImplementedError

    @classmethod
    @__.abstract_member_function
    async def prepare(
        selfclass,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError


@__.a.runtime_checkable
@__.dataclass( frozen = True, kw_only = True, slots = True )
class Factory( __.a.Protocol ):
    ''' Produces clients. '''

    @__.abstract_member_function
    async def client_from_descriptor(
        self,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ) -> Client:
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError


class ChatCompletionError( Exception ): pass


@__.dataclass( frozen = True, kw_only = True, slots = True )
class ChatCallbacks:
    ''' Callbacks for AI provider to correspond with caller. '''

    allocator: __.a.Callable[ [ __.Canister ], __.a.Any ] = (
        lambda canister: canister )
    deallocator: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda handle: None )
    failure_notifier: __.a.Callable[ [ str ], None ] = (
        lambda status: None )
    progress_notifier: __.a.Callable[ [ int ], None ] = (
        lambda tokens_count: None )
    success_notifier: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda status: None )
    updater: __.a.Callable[ [ __.a.Any, str ], None ] = (
        lambda handle: None )


chat_callbacks_minimal = ChatCallbacks( )
# TODO: Use accretive validator dictionary for preparers registry.
preparers = __.AccretiveDictionary( )


def descriptors_from_configuration(
    auxdata: __.Globals
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
        if not descriptor.get( 'enable', False ): continue
        descriptors.append( descriptor )
    return tuple( descriptors )


async def prepare( auxdata: __.Globals ) -> __.AccretiveDictionary:
    ''' Prepares clients from configuration and returns futures to them. '''
    factories = await prepare_factories( auxdata )
    return await prepare_clients( auxdata, factories )


async def prepare_clients(
    auxdata: __.Globals,
    factories: __.AbstractDictionary[ str, Factory ],
) -> __.AbstractDictionary[ str, Client ]:
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
        *(  factory.client_from_descriptor( auxdata, descriptor )
            for factory, descriptor
            in zip( factories_per_client, descriptors ) ),
        return_exceptions = True )
    for name, descriptor, result in zip( names, descriptors, results ):
        match result:
            case __.g.Error( error ):
                summary = f"Could not load AI provider {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( future ):
                # TODO: Register client future rather than module.
                clients[ name ] = future.module
    return clients


async def prepare_factories(
    auxdata: __.Globals
) -> __.AbstractDictionary[ str, Factory ]:
    ''' Prepares factories from configuration. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = descriptors_from_configuration( auxdata )
    names = frozenset(
        descriptor.get( 'factory', descriptor[ 'name' ] )
        for descriptor in descriptors )
    preparers_ = __.DictionaryProxy(
        { name: preparers[ name ]( auxdata ) for name in names } )
    results = await __.gather_async(
        *preparers_.values( ), return_exceptions = True )
    factories = { }
    for name, result in zip( preparers_.keys( ), results ):
        match result:
            case __.g.Error( error ):
                summary = "Could not prepare AI provider factory {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( factory ):
                factories[ name ] = factory
    return factories
