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
    url: __.Url

    def __init__( self, url: __.Url ):
        # TODO: Assert file or empty scheme.
        if url.netloc or url.params or url.query or url.fragment:
            # TODO: Raise more specific exception.
            raise NotImplementedError(
                f"Only scheme and path supported in file URLs. URL: {url}" )
        self.implement = __.Path( url.path )
        self.url = url
        super( ).__init__( )

    def as_url( self ) -> __.Url: return self.url

    async def check_access( self ) -> bool:
        from os import F_OK # TODO: Use proper mode from configuration.
        from aiofiles.os import access
        mode = F_OK
        return await access( self.implement, mode )

    async def check_existence( self ) -> bool:
        from aiofiles.os.path import exists
        return await exists( self.implement )

    def expose_implement( self ) -> __.Implement:
        # Cast because we do not have a common protocol.
        return __.a.cast( __.Implement, self.implement )


class GeneralAdapter( _Common, __.GeneralAdapter ):
    ''' General location access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def from_url( selfclass, url: __.UrlLike ) -> __.a.Self:
        return selfclass( url = __.Url.from_url( url ) )

    async def as_specific( self ) -> __.SpecificAdapter:
        # TODO: match await self.adapter.stat( ).species
        if await self.is_directory( ):
            return DirectoryAdapter( url = self.url )
        elif await self.is_file( ):
            return FileAdapter( url = self.url )
        # TODO: assert

    async def is_directory( self ) -> bool:
        from aiofiles.os.path import isdir
        return await isdir( self.implement )

    async def is_file( self ) -> bool:
        from aiofiles.os.path import isfile
        return await isfile( self.implement )

    async def is_indirection( self ) -> bool:
        from aiofiles.os.path import islink
        return await islink( self.implement )

# TODO? Perform registrations as part of module preparation function.
_simple_class = __.accessors_registry[ 'simple' ]
#_cache_class = __.accessors.registry[ 'cache' ]
for _scheme in ( '', 'file' ):
    _simple_class.adapters_registry[ _scheme ] = GeneralAdapter
    #_cache_class.cache_adapters_registry[ _scheme ] = GeneralAdapter
    #_cache_class.source_adapters_registry[ _scheme ] = GeneralAdapter


class DirectoryAdapter( _Common, __.DirectoryAdapter ):
    ''' Directory access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.


class FileAdapter( _Common, __.FileAdapter ):
    ''' File access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.
