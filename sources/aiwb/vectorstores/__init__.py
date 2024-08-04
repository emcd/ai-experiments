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


''' Functionality for various vectorstores. '''


from .. import libcore as _libcore
from . import __


@__.dataclass( frozen = True, kw_only = True, slots = True )
class StoreDescriptor:
    ''' Vectorstore name and data, including provider. '''

    name: str
    data: dict
    provider: __.Module

    @classmethod
    def from_dictionary( selfclass, data: __.AbstractDictionary ):
        ''' Constructs store descriptor from dictionary, loading provider. '''
        from importlib import import_module
        name = data[ 'name' ]
        data = data
        # TODO? Cache module imports to avoid redundant imports.
        provider = import_module(
            ".{name}".format( name = data[ 'provider' ] ), __package__ )
        return selfclass( name = name, data = data, provider = provider )


async def prepare( auxdata: _libcore.Globals ) -> __.AccretiveDictionary:
    ''' Ensures requested providers exist and returns vectorstore futures. '''
    # TODO: https://docs.python.org/3/library/asyncio-future.html#asyncio.Future
    scribe = __.acquire_scribe( __package__ )
    registry = __.AccretiveDictionary( )
    stores = tuple(
        StoreDescriptor.from_dictionary( data )
        for data in auxdata.configuration.get( 'vectorstores', ( ) ) )
    results = await __.gather_async(
        *( store.provider.restore( auxdata, store ) for store in stores ),
        return_exceptions = True )
    for store, result in zip( stores, results ):
        match result:
            case __.g.Error( error ):
                summary = (
                    f"Could not load vectorstore {store.name!r}. "
                    f"Reason: {error}" )
                scribe.error( summary )
                auxdata.notifications.put( error )
            case __.g.Value( future ):
                # TODO: Implement futures.
                store_data = dict(
                    name = store.name,
                    data = store.data,
                    instance = future,
                )
                registry[ store.name ] = store_data
    # TODO? Notify if empty registry.
    return registry
