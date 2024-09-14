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


def _ensures_cache( function: __.a.Callable ):
    ''' Decorator which ensures cache is filled before operation. '''
    from functools import wraps

    @wraps( function )
    async def invoker( cache: _Common, *posargs, **nomargs ):
        await cache._ingest_if_absent( )
        return await function( cache, *posargs, **nomargs )

    return invoker


class _Common( __.a.Protocol ):
    # TODO: Immutable class and object attributes.

    adapter: __.AdapterBase
    cache_url: __.Url

    def __init__( self, adapter: __.AdapterBase, cache_url: __.Url ):
        self.adapter = adapter
        self.cache_url = cache_url
        super( ).__init__( )

    def as_url( self ) -> __.Url: return self.adapter.as_url( )

    @_ensures_cache
    async def check_access(
        self,
        permissions: __.Permissions,
        pursue_indirection: bool = True,
    ) -> bool:
        Error = __.partial_function(
            __.CacheOperationFailure( url = self.adapter.as_url( ) ) )
        cache_adapter = __.adapter_from_url( self.cache_url )
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

    @_ensures_cache
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

    @__.abstract_member_function
    async def _ingest( self ):
        # TODO: Implement:
        #       Examine source URL to get inode.
        #       (Properly handle indirection.)
        #       Clone permissions mapped to current user and group.
        #       Create directory entry according location species.
        #       Recursively populate if directory.
        #       Acquire content bytes if file.
        #       (Raise CacheOperationFailure on any error.)
        raise NotImplementedError

    async def _ingest_if_absent( self ):
        Error = __.partial_function(
            __.CacheOperationFailure( url = self.adapter.as_url( ) ) )
        cache_adapter = __.adapter_from_url( self.cache_url )
        try: exists = await cache_adapter.check_existence( )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        if not exists: await self._ingest( )


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
        force: bool = False,
        pursue_indirection: bool = True,
        species: __.Optional[ __.LocationSpecies ] = __.absent,
    ) -> __.SpecificCache:
        Error = __.partial_function(
            __.LocationCacheDerivationFailure, url = self.cache_url )
        try:
            species_ = species if force else await self.discover_species(
                pursue_indirection = pursue_indirection, species = species )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        adapter = await self.adapter.as_specific(
            force = True,
            pursue_indirection = pursue_indirection,
            species = species_ )
        match species_:
            case __.LocationSpecies.Directory:
                return DirectoryCache(
                    adapter = adapter, cache_url = self.cache_url )
            case __.LocationSpecies.File:
                return FileCache(
                    adapter = adapter, cache_url = self.cache_url )
            case _:
                reason = (
                    "No derivative available for species "
                    f"{species_.value!r}." )
                raise Error( reason = reason )

    @_ensures_cache
    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.is_directory(
            pursue_indirection = pursue_indirection )

    @_ensures_cache
    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.is_file(
            pursue_indirection = pursue_indirection )

    @_ensures_cache
    async def is_indirection( self ) -> bool:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.is_indirection( )

    async def _ingest( self ):
        Error = __.partial_function(
            __.CacheOperationFailure( url = self.adapter.as_url( ) ) )
        try: adapter = await self.adapter.as_specific( )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        if isinstance( adapter, __.DirectoryAdapter ):
            cache = DirectoryCache(
                adapter = adapter, cache_url = self.cache_url )
        elif isinstance( adapter, __.FileAdapter ):
            cache = FileCache(
                adapter = adapter, cache_url = self.cache_url )
        else:
            reason = "Cannot ingest entities of species {species_.value!r}."
            raise Error( reason = reason )
        await cache._ingest( )


class DirectoryCache( _Common, __.DirectoryCache ):
    ''' Simple cache for directory. '''
    # TODO: Immutable class and object attributes.

    adapter: __.DirectoryAdapter

    @_ensures_cache
    async def create_directory(
        self,
        name: __.PossibleRelativeLocator,
        permissions: __.Permissions | __.PermissionsTable,
        exist_ok: bool = True,
        parents: __.CreateParentsArgument = True,
    ) -> __.DirectoryAccessor:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.create_directory(
            name = name,
            permissions = permissions,
            exist_ok = exist_ok,
            parents = parents )

    # TODO: create_file

    @_ensures_cache
    async def delete_directory(
        self,
        name: __.PossibleRelativeLocator,
        absent_ok: bool = True,
        recurse: bool = True,
        safe: bool = True,
    ):
        cache_adapter = __.adapter_from_url( self.cache_url )
        # TODO? Record deletion for commit.
        return await cache_adapter.delete_directory(
            name = name,
            absent_ok = absent_ok,
            recurse = recurse,
            safe = safe )

    async def produce_entry_accessor(
        self, name: __.PossibleRelativeLocator
    ) -> __.GeneralAccessor:
        if isinstance( name, __.PossiblePath ): name = ( name, )
        if isinstance( name, __.AbstractIterable[ __.PossiblePath ] ):
            source_base_url = self.adapter.as_url( )
            source_url = source_base_url.with_path(
                __.Path( source_base_url.path ).joinpath( *name ) )
            source_adapter = __.adapter_from_url( source_url )
            cache_url = self.cache_url.with_path(
                __.Path( self.cache_url.path ).joinpath( *name ) )
            return GeneralCache(
                adapter = source_adapter, cache_url = cache_url )
        raise __.RelativeLocatorClassValidityError( type( name ) )

    @_ensures_cache
    async def survey_entries(
        self,
        filters: __.Optional[
            __.AbstractIterable[ __.PossibleFilter ]
        ] = __.absent,
        recurse: bool = True
    ) -> __.AbstractSequence[ __.DirectoryEntry ]:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.survey_entries(
            filters = filters, recurse = recurse )

    async def _ingest( self ):
        cache_adapter = __.adapter_from_url( self.cache_url )
        # TODO: Handle exceptions.
        cache_adapter.create_directory(
            name = '.',
            permissions = __.AccretiveDictionary( {
                __.Possessor.CurrentPopulation: __.Permissions_RCUDX,
                __.Possessor.CurrentUser: __.Permissions_RCUDX } ),
            exist_ok = True,
            parents = True )
        source_base_url = self.adapter.as_url( )
        # TODO: Parallel async fanout for entry ingestion.
        for dirent in self.adapter.survey_entries(
            filters = ( ), recurse = False
        ):
            name = (
                __.Path( dirent.url.path )
                .relative_to( source_base_url.path ) )
            entry_accessor = self.produce_entry_accessor( name )
            await entry_accessor._ingest( )


class FileCache( _Common, __.FileCache ):
    ''' Simple cache for file. '''
    # TODO: Immutable class and object attributes.

    adapter: __.DirectoryAdapter

    async def acquire_content(
        self,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.AcquireContentTextResult:
        # TODO: Implement.
        pass

    async def acquire_content_bytes( self ) -> __.AcquireContentBytesResult:
        # TODO: Implement.
        pass

    async def update_content(
        self,
        content: str,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.UpdateContentResult:
        # TODO: Implement.
        pass

    async def update_content_bytes(
        self,
        content: bytes,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
    ) -> __.UpdateContentResult:
        # TODO: Implement.
        pass
