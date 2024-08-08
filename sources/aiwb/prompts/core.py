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


''' Core classes and functions for prompts. '''


from __future__ import annotations

from . import __


# TODO: Use accretive validator dictionary for flavors registry.
flavors = __.AccretiveDictionary( )


@__.a.runtime_checkable
class Definition( __.a.Protocol ):
    ''' Definition of prompt. Produces prompt instances. '''
    # TODO: Immutability of class and instances.

    name: str
    store: Store

    __slots__ = ( 'name', 'store', )

    @__.a.runtime_checkable
    class Instance( __.a.Protocol ):
        ''' Renderable instance of prompt. '''
        # TODO: Immutability of class and instances.

        __slots__ = ( 'definition', )

        definition: Definition

        def __init__( self, definition: Definition ):
            self.definition = definition

        def render( self, auxdata: __.Globals ) -> str:
            ''' Renders prompt as string. '''
            raise NotImplementedError

        def serialize( self ) -> dict:
            ''' Serializes prompt as dictionary. '''
            raise NotImplementedError

    @classmethod
    def instantiate_descriptor(
        selfclass,
        store: Store,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        return selfclass( store, **descriptor )

    def __init__( self, store: Store, name: str ):
        self.name = name
        self.store = store

    def produce_prompt( self, values = None ):
        ''' Produces prompt instance. '''
        return self.Instance( definition = self, values = values )

    def deserialize( self, data ):
        ''' Deserializes prompt instance from initial values. '''
        return self.Instance( definition = self, values = data )


@__.a.runtime_checkable
@__.dataclass( frozen = True, kw_only = True, slots = True )
class Store( __.a.Protocol ):
    ''' Record for prompt store. '''

    name: str
    location: __.Location

    @classmethod
    async def prepare(
        selfclass,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        args = selfclass.descriptor_to_base_init_args( auxdata, descriptor )
        return selfclass( **args )

    @classmethod
    def descriptor_to_base_init_args(
        selfclass,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AccretiveDictionary:
        distribution = auxdata.distribution
        name = descriptor[ 'name' ]
        location = __.parse_url( descriptor[ 'location' ].format(
            application_name = distribution.name,
            custom_data = auxdata.provide_data_location( ),
            distribution_data = distribution.provide_data_location( ),
            user_data = auxdata.directories.user_data_path,
            user_home = __.Path.home( ) ) )
        return __.AccretiveDictionary( name = name, location = location )

    @__.abstract_member_function
    async def acquire_definitions(
        self,
        auxdata: __.Globals,
    ) -> __.AbstractDictionary[ str, Definition ]:
        raise NotImplementedError


async def acquire_definitions(
    auxdata: __.Globals,
    stores: __.AbstractDictionary[ str, Store ],
) -> __.AbstractDictionary[ str, Definition ]:
    ''' Loads prompt definitions from stores. '''
    scribe = __.acquire_scribe( __package__ )
    results = await __.gather_async(
        *(  store.acquire_definitions( auxdata )
            for store in stores.values( ) ),
        return_exceptions = True )
    definitions = { }
    for result in results:
        match result:
            case __.g.Error( error ):
                summary = f"Could not load prompt definition."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( definitions_ ):
                definitions.update( definitions_ )
    return __.DictionaryProxy( definitions )


async def acquire_stores(
    auxdata: __.Globals,
) -> __.AbstractDictionary[ str, Store ]:
    ''' Loads configured promptstores. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = auxdata.configuration.get( 'promptstores', ( ) )
    preparers = [ ]
    for descriptor in descriptors:
        flavor = descriptor.get( 'flavor', 'native' )
        with auxdata.notifications.enqueue_on_error(
            f"Could not load prompts store.",
            scribe = scribe
            # TODO: Add descriptor as detail.
        ):
            preparers.append(
                flavors[ flavor ].prepare( auxdata, descriptor ) )
    results = await __.gather_async( *preparers, return_exceptions = True )
    stores = { }
    for result in results:
        match result:
            case __.g.Error( error ):
                summary = f"Could not load prompts store."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( store ):
                stores[ store.name ] = store
    return __.DictionaryProxy( stores )


async def prepare( auxdata ):
    ''' Load prompt stores and definitions. '''
    stores = await acquire_stores( auxdata )
    definitions = await acquire_definitions( auxdata, stores )
    return __.AccretiveNamespace( stores = stores, definitions = definitions )
