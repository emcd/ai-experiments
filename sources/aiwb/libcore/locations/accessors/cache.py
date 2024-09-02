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
        self, arguments: __.CheckAccessArguments
    ) -> bool: return await self.adapter.check_access( arguments )

    async def check_existence( self ) -> bool:
        # TODO: Invalidate cache entry, if necessary.
        return await self.adapter.check_existence( )

    def expose_implement( self ) -> __.Implement:
        return self.adapter.expose_implement( )


class GeneralAccessor( _Common, __.GeneralAccessor ):
    ''' Caching general location accessor. '''
    # TODO: Immutable class and object attributes.

    adapter: __.GeneralAdapter

    @classmethod
    def from_url(
        selfclass,
        url: __.UrlLike,
        cache: __.Optional[ __.CacheLike ] = __.absent,
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

    async def as_specific( self ) -> __.SpecificAccessor:
        adapter = await self.adapter.as_specific( )
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
