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


''' Caching location accessor. '''


from __future__ import annotations

from . import __


# TODO: Edits happen on cache and are only committed to source when explicitly
#       requested. Useful for 'git', 'github', 'hg', etc... protocol schemes.
#       AI invocables can use cache accessors to be safe, even with local
#       files.
#       Cache can have expiry or TTL to trigger refreshes on operations
#       or maybe async scheduled callbacks. Use for performance enhancement
#       scenarios.


class _Common:

    adapter: __.AdapterBase
    cache: __.Cache

    def as_url( self ): return self.adapter.as_url( )

    async def check_access(
        self,
        permissions: __.Permissions,
        pursue_indirection: bool = True,
    ) -> bool:
        # TODO: Check cache.
        return await self.adapter.check_access(
            permissions = permissions,
            pursue_indirection = pursue_indirection )

    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        # TODO: Invalidate cache entry, if necessary.
        return await self.adapter.check_existence( )

    async def examine( self, pursue_indirection: bool = True ) -> __.Inode:
        # TODO: Invalidate cache entry, if necessary.
        return await self.adapter.examine( )

    def expose_implement( self ) -> __.AccessImplement:
        return self.adapter.expose_implement( )


class GeneralAccessor( _Common, __.GeneralAccessor ):
    ''' Caching general location accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.GeneralAdapter

    @classmethod
    def from_url(
        selfclass,
        url: __.PossibleUrl,
        cache: __.Optional[ __.PossibleCache ] = __.absent,
    ) -> __.a.Self:
        adapter = __.adapter_from_url( url = url )
        if not cache: cache = str( adapter )
        if isinstance( cache, __.PathLike ): cache = cache.__fspath__( )
        if isinstance( cache, ( bytes, str ) ):
            cache = __.caches_registry[ 'localfs' ]( cache )
        # TODO: assert cache type
        return selfclass( adapter = adapter, cache = cache )

    def __init__( self, adapter: __.GeneralAdapter, cache: __.Cache ):
        self.adapter = adapter
        self.cache = cache

    async def as_specific(
        self,
        species: __.Optional[ __.LocationSpecies ] = __.absent,
    ) -> __.SpecificAccessor:
        adapter = await self.adapter.as_specific( species = species )
        # TODO? match adapter.species
        if isinstance( adapter, __.DirectoryAdapter ):
            return DirectoryAccessor( adapter = adapter, cache = self.cache )
        elif isinstance( adapter, __.FileAdapter ):
            return FileAccessor( adapter = adapter, cache = self.cache )
        # TODO: assert specific accessor type

    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        # TODO: Invalidate cache entry, if necessary.
        return await self.adapter.is_directory(
            pursue_indirection = pursue_indirection )

    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        # TODO: Invalidate cache entry, if necessary.
        return await self.adapter.is_file(
            pursue_indirection = pursue_indirection )

    async def is_indirection( self ) -> bool:
        return await self.adapter.is_indirection( )

__.accessors_registry[ 'cache' ] = GeneralAccessor


class DirectoryAccessor( _Common, __.DirectoryAccessor ):
    ''' Simple directory accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.DirectoryAdapter

    def __init__(
        self,
        adapter: __.DirectoryAdapter,
        cache: __.Cache,
    ):
        self.adapter = adapter
        self.cache = cache

    async def survey_entries(
        self,
        filters: __.Optional[
            __.AbstractIterable[ __.PossibleFilter ]
        ] = __.absent,
        recurse: bool = True
    ) -> __.AbstractSequence[ __.DirectoryEntry ]:
        # TODO: Invalidate cache entries, if necessary.
        return await self.adapter.survey_entries(
            filters = filters, recurse = recurse )


class FileAccessor( _Common, __.FileAccessor ):
    ''' Simple file accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.FileAdapter

    def __init__(
        self,
        adapter: __.FileAdapter,
        cache: __.Cache,
    ):
        self.adapter = adapter
        self.cache = cache

    async def acquire_content(
        self,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.AcquireContentTextResult:
        # TODO: Handle cache.
        return await self.adapter.acquire_content(
            charset = charset,
            charset_errors = charset_errors,
            newline = newline )

    async def acquire_content_bytes( self ) -> __.AcquireContentBytesResult:
        # TODO: Handle cache.
        return await self.adapter.acquire_content_bytes( )

    async def update_content(
        self,
        content: str,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.UpdateContentResult:
        # TODO: Handle cache.
        return await self.adapter.update_content(
            content,
            options = options,
            charset = charset,
            charset_errors = charset_errors,
            newline = newline )

    async def update_content_bytes(
        self,
        content: bytes,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
    ) -> __.UpdateContentResult:
        # TODO: Handle cache.
        return await self.adapter.update_content_bytes(
            content, options = options )
