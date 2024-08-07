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


''' Core functions for prompts. '''


from __future__ import annotations

from . import __


@__.a.runtime_checkable
class Definition( __.a.Protocol ):

    @__.a.runtime_checkable
    @__.dataclass( kw_only = True, slots = True )
    #@__.dataclass( frozen = True, kw_only = True, slots = True )
    class Instance( __.a.Protocol ):

        definition: Definition

        def render( self, auxdata: __.Globals ) -> str:
            ''' Renders prompt as string. '''
            raise NotImplementedError

        def serialize( self ) -> dict:
            ''' Serializes prompt as dictionary. '''
            raise NotImplementedError

    @classmethod
    def instantiate_descriptor(
        selfclass,
        manager: Manager,
        location: __.Location,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        return selfclass( manager, location, **descriptor )

    def __init__( self, manager, location, name ):
        self.name = name
        self.manager = manager
        self.location = location

    def create_prompt( self, values = None ):
        ''' Produces prompt instance. '''
        # TODO? Rename to 'produce_prompt'.
        return self.Instance( definition = self, values = values )

    def deserialize( self, data ):
        ''' Deserializes prompt instance from initial values. '''
        return self.Instance( definition = self, values = data )


@__.a.runtime_checkable
class Manager( __.a.Protocol ):
    ''' Manages prompts in store. '''

    @classmethod
    @__.abstract_member_function
    async def prepare( selfclass, auxdata: __.Globals ) -> __.a.Self:
        raise NotImplementedError

    @__.abstract_member_function
    async def acquire_definitions(
        self,
        auxdata: __.Globals,
        location: __.Location,
    ) -> __.AbstractDictionary[ str, Definition ]:
        ''' Loads prompt definitions from store. '''
        raise NotImplementedError


@__.dataclass( frozen = True, kw_only = True, slots = True )
class Store:
    ''' Record for prompt store. '''

    name: str
    manager: Manager
    location: __.Location
    definitions: __.AbstractDictionary[ str, Definition ]

    @classmethod
    async def prepare(
        selfclass,
        auxdata: __.Globals,
        descriptor: dict[ str, __.a.Any ]
    ) -> __.a.Self:
        ''' Converts descriptor dictionary into record. '''
        distribution = auxdata.distribution
        name = descriptor[ 'name' ]
        manager = await produce_manager(
            auxdata, descriptor.get( 'manager', 'native' ) )
        location = __.parse_url( descriptor[ 'location' ].format(
            application_name = distribution.name,
            custom_data = auxdata.provide_data_location( ),
            distribution_data = distribution.provide_data_location( ),
            user_data = auxdata.directories.user_data_path,
            user_home = __.Path.home( ) ) )
        definitions = await manager.acquire_definitions( auxdata, location )
        return selfclass(
            name = name,
            manager = manager,
            location = location,
            definitions = definitions )


async def acquire_promptstores( auxdata ):
    ''' Load configured promptstores. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = auxdata.configuration.get( 'promptstores', ( ) )
    results = await __.gather_async(
        *(  Store.prepare( auxdata, descriptor )
            for descriptor in descriptors ),
        return_exceptions = True )
    stores = { }
    for result in results:
        match result:
            case __.g.Error( error ):
                summary = f"Could not load prompt store."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( store ):
                stores[ store.name ] = store
    return __.DictionaryProxy( stores )


async def prepare( auxdata ):
    ''' Load prompt stores and definitions. '''
    stores = await acquire_promptstores( auxdata )
    definitions = __.DictionaryProxy( {
        definition.name: definition
        for store in stores.values( )
        for definition in store.definitions.values( ) } )
    return __.AccretiveNamespace( stores = stores, definitions = definitions )


# TODO: @__.memoize
#       May need custom caching because auxdata contains dictionaries
#       which do not hash.
async def produce_manager(
    auxdata: __.Globals,
    name: str
) -> Manager:
    ''' Creates prompts manager if it does not already exist. '''
    from importlib import import_module
    scribe = __.acquire_scribe( __package__ )
    with auxdata.notifications.enqueue_on_error(
        f"Could not create prompts manager {name!r}.", scribe = scribe
    ):
        module = import_module( f".flavors.{name}", __package__ )
        return await module.prepare( auxdata )
