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


''' Simple cache which uses separate storage adapter. '''


from __future__ import annotations

from . import __


_module_name = __name__.replace( f"{__package__}.", '' )
_entity_name = f"cache '{_module_name}'"


class _Common:

    # TODO: Implement.
    pass


@__.standard_dataclass
class CacheManager( __.CacheManager ):
    ''' Simple cache manager which uses separate storage adapter. '''
    # TODO: Immutable class and object attributes.

    adapter: __.DirectoryAdapter # for storage not source

    @classmethod
    async def from_url( selfclass, url: __.PossibleUrl ) -> __.a.Self:
        adapter = (
            await __.adapter_from_url( url )
            .as_specific( species = __.LocationSpecies.Directory ) )
        return selfclass( adapter = adapter )

    async def produce_cache(
        self, source_adapter: __.GeneralAdapter
    ) -> __.GeneralCache:
        return GeneralCache( source_adapter = source_adapter, manager = self )


class GeneralCache( _Common, __.GeneralCache ):
    ''' Simple cache for general location. '''
    # TODO: Immutable class and object attributes.

    adapter: __.GeneralAdapter
    manager: __.CacheManager

    async def as_specific(
        self,
        species: __.Optional[ __.LocationSpecies ] = __.absent,
    ) -> __.SpecificCache:
        # TODO: Implement.
        pass

    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        # TODO: Implement.
        pass

    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        # TODO: Implement.
        pass

    async def is_indirection( self ) -> bool:
        # TODO: Implement.
        pass
