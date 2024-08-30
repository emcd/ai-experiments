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


''' Location access adapter with aiofiles and pathlib. '''


from __future__ import annotations

from . import __


__.Implement.register( __.Path )


class _Common:
    # TODO: Immutable class and object attributes.

    implement: __.Path

    def __init__( self, url: __.Url ):
        # TODO: Assert file or empty scheme.
        if url.netloc or url.params or url.query or url.fragment:
            # TODO: Raise more specific exception.
            raise NotImplementedError(
                f"Only scheme and path supported in file URLs. URL: {url}" )
        # Cast because we do not have a common protocol.
        self.implement = __.a.cast( __.Implement, __.Path( url.path ) )
        super( ).__init__( url = url )

    async def check_access( self ) -> bool:
        from os import F_OK # TODO: Use proper mode from configuration.
        from aiofiles.os import access
        mode = F_OK
        return await access( self.implement, mode )

    async def check_existence( self ) -> bool:
        from aiofiles.os.path import exists
        return await exists( self.implement )

    def expose_implement( self ) -> __.Implement:
        return self.implement


class Adapter( _Common, __.Adapter ):
    ''' Location access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.

    def as_directory_adapter( self ) -> DirectoryAdapter:
        return DirectoryAdapter( url = self.url )

    def as_file_adapter( self ) -> FileAdapter:
        return FileAdapter( url = self.url )

    async def is_directory( self ) -> bool:
        from aiofiles.os.path import isdir
        return await isdir( self.implement )

    async def is_file( self ) -> bool:
        from aiofiles.os.path import isfile
        return await isfile( self.implement )

    async def is_symlink( self ) -> bool:
        from aiofiles.os.path import islink
        return await islink( self.implement )


class DirectoryAdapter( _Common, __.DirectoryAdapter ):
    ''' Directory access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.


class FileAdapter( _Common, __.FileAdapter ):
    ''' File access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.


__.adapters_registry[ 'pathlib+aiofiles' ] = Adapter
