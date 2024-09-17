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


''' Simple cache which uses separate storage adapter.

    Limitations:
    * Does not track indirection (symlinks, redirects, etc...). Always caches
      location referenced by fully-resolved URL.
    * Does not track upstream expiries (e.g., HTTP cache controls).
    * Does not track upstream MIME type or charset hints (e.g., HTTP
      'Content-Type' headers).
'''


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
        cache_adapter = __.adapter_from_url( self.cache_url )
        return cache_adapter.check_access(
            permissions = permissions,
            pursue_indirection = pursue_indirection )

    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        source_adapter = self.adapter
        cache_adapter = __.adapter_from_url( self.cache_url )
        cache_exists = await cache_adapter.check_existence(
            pursue_indirection = pursue_indirection )
        if cache_exists: return True
        source_exists = await source_adapter.check_existence(
            pursue_indirection = pursue_indirection )
        if source_exists: await self._ingest( )
        return source_exists

    @_ensures_cache
    async def examine(
        self,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        pursue_indirection: bool = True,
    ) -> __.Inode:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return cache_adapter.examine(
            attributes = attributes,
            pursue_indirection = pursue_indirection )

    def expose_implement( self ) -> __.AccessImplement:
        return self.adapter.expose_implement( )

    @__.abstract_member_function
    async def _ingest( self ):
        raise NotImplementedError

    async def _ingest_if_absent( self ):
        Error = __.partial_function(
            __.LocationCacheIngestFailure,
            source_url = self.adapter.as_url( ), cache_url = self.cache_url )
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

    async def commit(
        self, *,
        aliens: __.AlienResolutionActions
            = __.AlienResolutionActions.Ignore,
        conflicts: __.ConflictResolutionActions
            = __.ConflictResolutionActions.Error,
        impurities: __.ImpurityResolutionActions
            = __.ImpurityResolutionActions.Ignore,
    ) -> __.a.Self:
        # No concept of aliens or impurities. Everything is considered.
        # TODO: Implement.
        pass

    async def difference(
        self
    ) -> __.AbstractSequence[ __.CacheDifferenceBase ]:
        # No concept of aliens or impurities. Everything is considered.
        # TODO: Implement.
        pass

    async def is_divergent( self ) -> bool:
        # No concept of aliens or impurities. Everything is considered.
        # TODO: Survey directory.
        #       Derive source URL from cache URL.
        #       Compare entries in source directories versus cache directories.
        #       Compare contents of source files versus cache files.
        pass

    def produce_cache(
        self, source_adapter: __.GeneralAdapter
    ) -> __.GeneralCache:
        cache_url = self._calculate_cache_url(
            source_adapter = source_adapter )
        return GeneralCache(
            adapter = source_adapter, cache_url = cache_url )

    async def reingest(
        self, *,
        aliens: __.AlienResolutionActions
            = __.AlienResolutionActions.Ignore,
        conflicts: __.ConflictResolutionActions
            = __.ConflictResolutionActions.Error,
        impurities: __.ImpurityResolutionActions
            = __.ImpurityResolutionActions.Ignore,
    ) -> __.a.Self:
        # No concept of aliens or impurities. Everything is considered.
        # TODO: Implement.
        pass

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
            __.LocationAccessorDerivationFailure,
            entity_name = _entity_name, url = self.cache_url )
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
            __.LocationCacheIngestFailure,
            source_url = self.adapter.as_url( ), cache_url = self.cache_url )
        try: adapter = await self.adapter.as_specific( )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        if isinstance( adapter, __.DirectoryAdapter ):
            cache = DirectoryCache(
                adapter = adapter, cache_url = self.cache_url )
        elif isinstance( adapter, __.FileAdapter ):
            cache = FileCache(
                adapter = adapter, cache_url = self.cache_url )
        else:
            species = ( await adapter.examine( ) ).inode.species
            reason = f"Cannot ingest entities of species {species.value!r}."
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

    @_ensures_cache
    async def create_file(
        self,
        name: __.PossibleRelativeLocator,
        permissions: __.Permissions | __.PermissionsTable,
        exist_ok: bool = True,
        parents: __.CreateParentsArgument = True,
    ) -> __.FileAccessor:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.create_file(
            name = name,
            permissions = permissions,
            exist_ok = exist_ok,
            parents = parents )

    async def delete_directory(
        self,
        name: __.PossibleRelativeLocator,
        absent_ok: bool = True,
        recurse: bool = True,
        safe: bool = True,
    ):
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.delete_directory(
            name = name,
            absent_ok = absent_ok,
            recurse = recurse,
            safe = safe )

    async def delete_file(
        self,
        name: __.PossibleRelativeLocator,
        absent_ok: bool = True,
        recurse: bool = True,
        safe: bool = True,
    ):
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.delete_file(
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
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        filters: __.Optional[
            __.AbstractIterable[ __.PossibleFilter ]
        ] = __.absent,
        recurse: bool = True
    ) -> __.AbstractSequence[ __.DirectoryEntry ]:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.survey_entries(
            attributes = attributes, filters = filters, recurse = recurse )

    async def _ingest( self ):
        Error = __.partial_function(
            __.LocationCacheIngestFailure,
            source_url = self.adapter.as_url( ), cache_url = self.cache_url )
        cache_adapter = __.adapter_from_url( self.cache_url )
        try:
            await cache_adapter.create_directory(
                name = '.',
                permissions = __.AccretiveDictionary( {
                    __.Possessor.CurrentPopulation: __.Permissions_RCUDX,
                    __.Possessor.CurrentUser: __.Permissions_RCUDX } ),
                exist_ok = True,
                parents = True )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        source_base_url = self.adapter.as_url( )
        # TODO: Parallel async fanout for entry ingestion.
        for dirent in await self.adapter.survey_entries(
            filters = ( ), recurse = False
        ):
            name = (
                __.Path( dirent.url.path )
                .relative_to( source_base_url.path ) )
            try:
                entry_accessor = self.produce_entry_accessor( name )
                await entry_accessor._ingest( )
            except Exception as exc:
                raise Error( reason = str( exc ) ) from exc


class FileCache( _Common, __.FileCache ):
    ''' Simple cache for file. '''
    # TODO: Immutable class and object attributes.

    adapter: __.DirectoryAdapter

    @_ensures_cache
    async def acquire_content(
        self,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.AcquireContentTextResult:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return await cache_adapter.acquire_content(
            attributes = attributes,
            charset = charset,
            charset_errors = charset_errors,
            newline = newline )

    @_ensures_cache
    async def acquire_content_bytes(
        self, attributes: __.InodeAttributes = __.InodeAttributes.Nothing
    ) -> __.AcquireContentBytesResult:
        cache_adapter = __.adapter_from_url( self.cache_url )
        return (
            await cache_adapter.acquire_content_bytes(
                attributes = attributes ) )

    async def update_content(
        self,
        content: str,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
    ) -> __.Inode:
        cache_adapter = await self._create_cache_file_if_absent( )
        return await cache_adapter.update_content(
            content,
            attributes = attributes,
            charset = charset,
            charset_errors = charset_errors,
            newline = newline,
            options = options )

    async def update_content_bytes(
        self,
        content: bytes,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
    ) -> __.Inode:
        cache_adapter = await self._create_cache_file_if_absent( )
        return await cache_adapter.update_content_bytes(
            content, attributes = attributes, options = options )

    async def _ingest( self ):
        Error = __.partial_function(
            __.LocationCacheIngestFailure,
            source_url = self.adapter.as_url( ), cache_url = self.cache_url )
        try:
            cache_adapter = await self._create_cache_file_if_absent( )
            acquisition = await self.adapter.acquire_content_bytes( )
            await cache_adapter.update_content_bytes( acquisition.content )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc

    async def _create_cache_file_if_absent( self ) -> __.FileAdapter:
        path = __.Path( self.cache_url.path )
        parent_url = self.cache_url.with_path( path.parent )
        parent_adapter = __.adapter_from_url( parent_url )
        return await parent_adapter.create_file(
            name = path.name,
            permissions = __.AccretiveDictionary( {
                __.Possessor.CurrentPopulation: __.Permissions_RCUD,
                __.Possessor.CurrentUser: __.Permissions_RCUD } ),
            exist_ok = True,
            parents = True )
