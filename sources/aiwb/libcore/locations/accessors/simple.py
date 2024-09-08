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


class _Common:

    adapter: __.AdapterBase

    def as_url( self ): return self.adapter.as_url( )

    async def check_access(
        self,
        permissions: __.Permissions,
        pursue_indirection: bool = True,
    ) -> bool:
        return await self.adapter.check_access(
            permissions = permissions,
            pursue_indirection = pursue_indirection )

    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        return await self.adapter.check_existence(
            pursue_indirection = pursue_indirection )

    async def examine( self, pursue_indirection: bool = True ) -> __.Inode:
        return await self.adapter.examine( )

    def expose_implement( self ) -> __.AccessImplement:
        return self.adapter.expose_implement( )


class GeneralAccessor( _Common, __.GeneralAccessor ):
    ''' Simple general location accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.GeneralAdapter

    @classmethod
    def from_url( selfclass, url: __.PossibleUrl ) -> __.a.Self:
        adapter = __.adapter_from_url( url = url )
        return selfclass( adapter = adapter )

    def __init__( self, adapter: __.GeneralAdapter ):
        self.adapter = adapter
        super( ).__init__( )

    async def as_specific( self ) -> __.SpecificAccessor:
        adapter = await self.adapter.as_specific( )
        # TODO? match adapter.species
        if isinstance( adapter, __.DirectoryAdapter ):
            return DirectoryAccessor( adapter = adapter )
        elif isinstance( adapter, __.FileAdapter ):
            return FileAccessor( adapter = adapter )
        # TODO: assert

    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        return await self.adapter.is_directory(
            pursue_indirection = pursue_indirection )

    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        return await self.adapter.is_file(
            pursue_indirection = pursue_indirection )

    async def is_indirection( self ) -> bool:
        return await self.adapter.is_indirection( )

__.accessors_registry[ 'simple' ] = GeneralAccessor


class DirectoryAccessor( _Common, __.DirectoryAccessor ):
    ''' Simple directory accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.DirectoryAdapter

    def __init__( self, adapter: __.DirectoryAdapter ):
        self.adapter = adapter
        super( ).__init__( )

    async def survey_entries(
        self,
        filters: __.Optional[
            __.AbstractIterable[ __.PossibleFilter ]
        ] = __.absent,
        recurse: bool = True,
    ) -> __.AbstractSequence[ __.DirectoryEntry ]:
        return await self.adapter.survey_entries(
            filters = filters, recurse = recurse )


class FileAccessor( _Common, __.FileAccessor ):
    ''' Simple file accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.FileAdapter

    def __init__( self, adapter: __.FileAdapter ):
        self.adapter = adapter
        super( ).__init__( )

    async def acquire_content(
        self,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.ContentTextResult:
        return await self.adapter.acquire_content(
            charset = charset,
            charset_errors = charset_errors,
            newline = newline )

    async def acquire_content_bytes( self ) -> __.ContentBytesResult:
        return await self.adapter.acquire_content_bytes( )