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


''' Simple (direct) location accessor. '''


from __future__ import annotations

from . import __


class GeneralAccessor( __.GeneralAccessor ):
    ''' Simple general location accessor. '''
    # TODO: Immutable class and object attributes.

    adapters_registry: __.a.ClassVar[
        __.AbstractDictionary[ str, __.GeneralAdapter ]
    ] = __.AccretiveDictionary( )

    adapter: __.GeneralAdapter

    @classmethod
    def from_url(
        selfclass,
        url: __.UrlLike,
        adapter_class: __.Optional[ type[ __.GeneralAdapter ] ] = __.absent,
    ) -> __.a.Self:
        adapter_class = (
            adapter_class
            or __.registrant_from_url(
                registry = selfclass.adapters_registry, url = url ) )
        return selfclass( adapter = adapter_class.from_url( url ) )

    def __init__( self, adapter: __.GeneralAdapter ): self.adapter = adapter

    async def as_specific( self ) -> __.SpecificAccessor:
        adapter = await self.adapter.as_specific( )
        if isinstance( adapter, __.DirectoryAdapter ):
            return DirectoryAccessor( adapter = adapter )
        elif isinstance( adapter, __.FileAdapter ):
            return FileAccessor( adapter = adapter )
        # TODO: assert

    def as_url( self ): return self.adapter.as_url( )

    async def check_access( self ) -> bool:
        return await self.adapter.check_access( )

    async def check_existence( self ) -> bool:
        return await self.adapter.check_existence( )

    def expose_implement( self ) -> __.Implement:
        return self.adapter.expose_implement( )

    async def is_directory( self ) -> bool:
        return await self.adapter.is_directory( )

    async def is_file( self ) -> bool:
        return await self.adapter.is_file( )

    async def is_indirection( self ) -> bool:
        return await self.adapter.is_indirection( )

__.accessors_registry[ 'simple' ] = GeneralAccessor


class DirectoryAccessor( __.DirectoryAccessor ):
    ''' Simple directory accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.DirectoryAdapter

    def __init__( self, adapter: __.DirectoryAdapter ): self.adapter = adapter

    def as_url( self ): return self.adapter.as_url( )

    async def check_access( self ) -> bool:
        return await self.adapter.check_access( )

    async def check_existence( self ) -> bool:
        return await self.adapter.check_existence( )

    def expose_implement( self ) -> __.Implement:
        return self.adapter.expose_implement( )


class FileAccessor( __.FileAccessor ):
    ''' Simple file accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.FileAdapter

    def __init__( self, adapter: __.FileAdapter ): self.adapter = adapter

    def as_url( self ): return self.adapter.as_url( )

    async def check_access( self ) -> bool:
        return await self.adapter.check_access( )

    async def check_existence( self ) -> bool:
        return await self.adapter.check_existence( )

    def expose_implement( self ) -> __.Implement:
        return self.adapter.expose_implement( )
