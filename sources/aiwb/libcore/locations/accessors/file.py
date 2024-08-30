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


''' Local filesystem location accessor. '''


from __future__ import annotations

from . import __


@__.standard_dataclass
class Accessor( __.Accessor ):
    ''' Local filesystem location accessor. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def provide_adapter_class( selfclass ) -> type[ __.Adapter ]:
        return __.adapters_registry[ 'pathlib+aiofiles' ]

    def as_directory_accessor( self ) -> DirectoryAccessor:
        return DirectoryAccessor(
            adapter = self.adapter.as_directory_adapter( ) )

    def as_file_accessor( self ) -> FileAccessor:
        return FileAccessor(
            adapter = self.adapter.as_file_adapter( ) )

    async def check_access( self ) -> bool:
        return await self.adapter.check_access( )

    async def check_existence( self ) -> bool:
        return await self.adapter.check_existence( )

    async def is_directory( self ) -> bool:
        return await self.adapter.is_directory( )

    async def is_file( self ) -> bool:
        return await self.adapter.is_file( )

    async def is_symlink( self ) -> bool:
        return await self.adapter.is_symlink( )


@__.standard_dataclass
class DirectoryAccessor( __.DirectoryAccessor ):
    ''' Local filesystem directory accessor. '''

    async def check_access( self ) -> bool:
        return await self.adapter.check_access( )

    async def check_existence( self ) -> bool:
        return await self.adapter.check_existence( )


@__.standard_dataclass
class FileAccessor( __.FileAccessor ):
    ''' Local filesystem file accessor. '''

    async def check_access( self ) -> bool:
        return await self.adapter.check_access( )

    async def check_existence( self ) -> bool:
        return await self.adapter.check_existence( )


__.accessors_registry[ '' ] = Accessor
__.accessors_registry[ 'file' ] = Accessor
