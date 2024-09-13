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
    # TODO: Immutable class and object attributes.

    adapter: __.AdapterBase
    cache_url: __.Url

    def __init__( self, adapter: __.AdapterBase, cache_url: __.Url ):
        self.adapter = adapter
        self.cache_url = cache_url
        super( ).__init__( )

    def as_url( self ) -> __.Url: return self.adapter.as_url( )

    async def check_access(
        self,
        permissions: __.Permissions,
        pursue_indirection: bool = True,
    ) -> bool:
        Error = __.partial_function(
            __.CacheOperationFailure( url = self.adapter.as_url( ) ) )
        cache_adapter = __.adapter_from_url( self.cache_url )
        await self._ingest_if_absent( pursue_indirection = pursue_indirection )
        try:
            return cache_adapter.check_access(
                permissions = permissions,
                pursue_indirection = pursue_indirection )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc

    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        source_adapter = self.adapter
        Error = __.partial_function(
            __.CacheOperationFailure( url = source_adapter.as_url( ) ) )
        cache_adapter = __.adapter_from_url( self.cache_url )
        try:
            cache_exists = await cache_adapter.check_existence(
                pursue_indirection = pursue_indirection )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        if not cache_exists:
            try:
                source_exists = await source_adapter.check_existence(
                    pursue_indirection = pursue_indirection )
            except Exception as exc:
                raise Error( reason = str( exc ) ) from exc
        if source_exists:
            await self._ingest( pursue_indirection = pursue_indirection )
        return source_exists

    async def examine( self, pursue_indirection: bool = True ) -> __.Inode:
        Error = __.partial_function(
            __.CacheOperationFailure( url = self.adapter.as_url( ) ) )
        cache_adapter = __.adapter_from_url( self.cache_url )
        await self._ingest_if_absent( pursue_indirection = pursue_indirection )
        try:
            return cache_adapter.examine(
                pursue_indirection = pursue_indirection )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc

    def expose_implement( self ) -> __.AccessImplement:
        # Cast because we do not have a common protocol.
        return __.a.cast(
            __.AccessImplement, self.adapter.expose_implement( ) )

    async def _ingest( self, pursue_indirection: bool ):
        # TODO: Implement:
        #       Examine source URL to get inode.
        #       (Properly handle indirection.)
        #       Clone permissions mapped to current user and group.
        #       Create directory entry according location species.
        #       Recursively populate if directory.
        #       Acquire content bytes if file.
        #       (Raise CacheOperationFailure on any error.)
        pass

    async def _ingest_if_absent( self, pursue_indirection: bool ):
        Error = __.partial_function(
            __.CacheOperationFailure( url = self.adapter.as_url( ) ) )
        cache_adapter = __.adapter_from_url( self.cache_url )
        try:
            exists = await cache_adapter.check_existence(
                pursue_indirection = False )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        if not exists:
            await self._ingest( pursue_indirection = pursue_indirection )


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

    def as_url( self ) -> __.Url: return self.adapter.as_url( )

    def produce_cache(
        self, source_adapter: __.GeneralAdapter
    ) -> __.GeneralCache:
        cache_url = self._calculate_cache_url(
            source_adapter = source_adapter )
        return GeneralCache(
            adapter = source_adapter, cache_url = cache_url )

    def _calculate_cache_url(
        self, source_adapter: __.AdapterBase
    ) -> __.Url:
        source_url = source_adapter.as_url( )
        cache_url_base = self.as_url( )
        cache_path = (
            __.Path( cache_url_base.path )
            .joinpath(
                # If scheme is missing, fill in 'file' for uniformity.
                source_url.scheme or 'file',
                # If netloc is missing, fill in 'localhost' for uniformity.
                source_url.netloc or 'localhost',
                # Strip leading '/' to prevent anchor path overrides.
                source_url.path.lstrip( '/' ) ) )
        return cache_url_base.with_path( cache_path )


class GeneralCache( _Common, __.GeneralCache ):
    ''' Simple cache for general location. '''
    # TODO: Immutable class and object attributes.

    adapter: __.GeneralAdapter

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
