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


class Definition(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolClass,
    protocol_class_enhancements = (
        __.ProtocolClassEnhancements.RuntimeCheckable ),
):
    ''' Definition of prompt. Produces prompt instances. '''
    # TODO: Immutability of instances.

    name: str
    store: Store

    __slots__ = ( 'name', 'store', )

    class Instance(
        __.a.Protocol,
        metaclass = __.ImmutableProtocolClass,
        protocol_class_enhancements = (
            __.ProtocolClassEnhancements.RuntimeCheckable ),
    ):
        ''' Renderable instance of prompt. '''
        # TODO: Immutability of instances.

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


class Store(
    __.a.Protocol,
    metaclass = __.ImmutableProtocolDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
    protocol_class_enhancements = (
        __.ProtocolClassEnhancements.RuntimeCheckable ),
):
    ''' Record for prompt store. '''

    name: str
    location: __.LocationAccessImplement

    @classmethod
    async def prepare(
        selfclass,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        args = selfclass.init_args_from_descriptor( auxdata, descriptor )
        return selfclass( **args )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        distribution = auxdata.distribution
        name = descriptor[ 'name' ]
        location = __.location_adapter_from_url(
            descriptor[ 'location' ].format(
                application_name = auxdata.application.name,
                custom_data = auxdata.provide_data_location( ),
                distribution_data = distribution.provide_data_location( ),
                user_data = auxdata.directories.user_data_path,
                user_home = __.Path.home( ) ) ).expose_implement( )
        return __.AccretiveDictionary( name = name, location = location )

    @__.abstract_member_function
    async def acquire_definitions(
        self,
        auxdata: __.Globals,
    ) -> __.AbstractDictionary[ str, Definition ]:
        raise NotImplementedError


# TODO: Use accretive validator dictionary for flavors registry.
flavors = __.AccretiveDictionary( )


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
                summary = "Could not load prompt definition."
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
    descriptors = descriptors_from_configuration( auxdata )
    names = tuple( descriptor[ 'name' ] for descriptor in descriptors )
    preparers = tuple(
        flavors[ descriptor.get( 'flavor', 'native' ) ]
        .prepare( auxdata, descriptor )
        for descriptor in descriptors )
    results = await __.gather_async( *preparers, return_exceptions = True )
    stores = { }
    for name, descriptor, result in zip( names, descriptors, results ):
        match result:
            case __.g.Error( error ):
                summary = f"Could not load prompts store {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, details = descriptor, scribe = scribe )
            case __.g.Value( store ):
                stores[ store.name ] = store
    return __.DictionaryProxy( stores )


def descriptors_from_configuration(
    auxdata: __.Globals
) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
    ''' Validates and returns descriptors from configuration. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = [ ]
    for descriptor in auxdata.configuration.get( 'promptstores', ( ) ):
        if 'name' not in descriptor:
            auxdata.notifications.enqueue_error(
                ValueError( "Descriptor missing name." ),
                "Could not load prompts store from configuration.",
                details = descriptor,
                scribe = scribe )
            continue
        if not descriptor.get( 'enable', True ): continue
        flavor = descriptor.get( 'flavor', 'native' )
        if flavor not in flavors:
            auxdata.notifications.enqueue_error(
                ValueError( f"Unknown flavor: {flavor}" ),
                "Could not load prompts store {name!r}.",
                details = descriptor,
                scribe = scribe )
            continue
        descriptors.append( descriptor )
    return tuple( descriptors )


async def prepare( auxdata ):
    ''' Load prompt stores and definitions. '''
    stores = await acquire_stores( auxdata )
    definitions = await acquire_definitions( auxdata, stores )
    return __.AccretiveNamespace( stores = stores, definitions = definitions )
