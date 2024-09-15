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


''' Abstract base classes and interfaces. '''

# TODO: Filesystem information objects from accessors.
#       For Git and other VCS schemes, provides discoverability for branches,
#       which can be used to shape cache interactions.
#       For Github and other VCS wrapper schemes, provides repository metadata,
#       possibly including workflows.
#       For local filesystems could include snapshots (ZFS, Time Machine,
#       etc...).


from __future__ import annotations

from . import __
from . import core as _core
from . import exceptions as _exceptions


class _Common( __.a.Protocol ):

    def __str__( self ) -> str: return str( self.as_url( ) )

    @__.abstract_member_function
    def as_url( self ) -> _core.Url:
        ''' Returns URL associated with location. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def check_access(
        self,
        permissions: _core.Permissions,
        pursue_indirection: bool = True,
    ) -> bool:
        ''' Does current process have access to location? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        ''' Does location exist? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def examine(
        self, pursue_indirection: bool = True
    ) -> _core.Inode:
        ''' Returns inode-like object for location. '''
        raise NotImplementedError

    @__.abstract_member_function
    def expose_implement( self ) -> _core.AccessImplement:
        ''' Exposes concrete implement used to perform operations. '''
        raise NotImplementedError

    # TODO: register_notifier


@__.a.runtime_checkable
class AdapterBase( _Common, __.a.Protocol ):
    ''' Common functionality for all access adapters. '''

    @classmethod
    @__.abstract_member_function
    def is_cache_manager( selfclass ) -> bool:
        ''' Is access adapter a cache manager for itself?

            For cases like Git, Github, Mercurial, etc.... '''
        raise NotImplementedError


@__.a.runtime_checkable
class CacheBase( _Common, __.a.Protocol ):
    ''' Common functionality for all caches. '''

    manager: CacheManager


@__.a.runtime_checkable
class Filter( __.a.Protocol ):
    ''' Determines if directory entry should be filtered. '''

    @__.abstract_member_function
    async def __call__( self, dirent: _core.DirectoryEntry ) -> bool:
        raise NotImplementedError


@__.a.runtime_checkable
class DirectoryOperations( __.a.Protocol ):
    ''' Standard operations on directories. '''

    async def create_directory(
        self,
        name: PossibleRelativeLocator,
        permissions: _core.Permissions | _core.PermissionsTable,
        exist_ok: bool = True,
        parents: CreateParentsArgument = True,
    ) -> DirectoryAccessor:
        ''' Creates directory relative to URL of this accessor. '''
        raise NotImplementedError

    async def create_file(
        self,
        name: PossibleRelativeLocator,
        permissions: _core.Permissions | _core.PermissionsTable,
        exist_ok: bool = True,
        parents: CreateParentsArgument = True,
    ) -> FileAccessor:
        ''' Creates file relative to URL of this accessor. '''
        raise NotImplementedError

    # TODO: create_indirection

    async def delete_directory(
        self,
        name: PossibleRelativeLocator,
        absent_ok: bool = True,
        recurse: bool = True,
        safe: bool = True, # TODO? safeties enum
    ):
        ''' Deletes directory relative to URL of this accessor. '''
        raise NotImplementedError

    async def delete_file(
        self,
        name: PossibleRelativeLocator,
        absent_ok: bool = True,
        safe: bool = True, # TODO? safeties enum
    ):
        ''' Deletes file relative to URL of this accessor. '''

    # TODO: delete_indirection

    def produce_entry_accessor(
        self, name: PossibleRelativeLocator
    ) -> GeneralAccessor:
        ''' Derives new accessor relative to URL of this accessor. '''
        raise NotImplementedError

    async def survey_entries(
        self,
        filters: __.Optional[
            __.AbstractIterable[ PossibleFilter ]
        ] = __.absent,
        recurse: bool = True,
    ) -> __.AbstractSequence[ _core.DirectoryEntry ]:
        ''' Returns list of directory entries, subject to filtering. '''
        raise NotImplementedError


@__.a.runtime_checkable
class FileOperations( __.a.Protocol ):
    ''' Standard operations on files. '''

    async def acquire_content(
        self,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> _core.AcquireContentTextResult:
        ''' Returns complete content of file as Unicode string. '''
        raise NotImplementedError

    # TODO: acquire_content_continuous

    async def acquire_content_bytes(
        self
    ) -> _core.AcquireContentBytesResult:
        ''' Returns complete content of file as raw bytes. '''
        raise NotImplementedError

    # TODO: acquire_content_bytes_continuous

    async def update_content(
        self,
        content: str,
        options: _core.FileUpdateOptions = _core.FileUpdateOptions.Defaults,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> _core.UpdateContentResult:
        ''' Updates content of file from Unicode string. '''
        raise NotImplementedError

    # TODO: update_content_continuous

    async def update_content_bytes(
        self,
        content: bytes,
        options: _core.FileUpdateOptions = _core.FileUpdateOptions.Defaults,
    ) -> _core.UpdateContentResult:
        ''' Updates content of file from raw bytes. '''

    # TODO: update_content_bytes_continuous


@__.a.runtime_checkable
class GeneralOperations( __.a.Protocol ):
    ''' Standard operations on locations of indeterminate species. '''

    async def discover_species(
        self,
        pursue_indirection: bool = True,
        species: __.Optional[ _core.LocationSpecies ] = __.absent,
    ) -> _core.LocationSpecies:
        ''' Discovers or asserts species of location. '''
        Error = __.partial_function(
            _exceptions.LocationSpeciesAssertionError, url = self.as_url( ) )
        exists = (
            await self.check_existence(
                pursue_indirection = pursue_indirection ) )
        if exists:
            species_ = (
                ( await self.examine(
                    pursue_indirection = pursue_indirection ) ).species )
            if __.absent is not species and species is not species_:
                reason = (
                    f"Requested species, '{species}', "
                    f"does not match actual species, '{species_}'." )
                raise Error( reason = reason )
            return species_
        return species

    @__.abstract_member_function
    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        ''' Is location a directory? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        ''' Is location a regular file? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def is_indirection( self ) -> bool:
        ''' Does location provide indirection to another location? '''
        raise NotImplementedError


@__.a.runtime_checkable
class ReconciliationOperations( __.a.Protocol ):
    ''' Standard operations for cache reconciliation. '''

    # TODO? is_cache_valid

    # TODO: commit_to_source

    # TODO: difference_with_source

    # TODO: update_from_source


@__.a.runtime_checkable
class GeneralAdapter( AdapterBase, GeneralOperations, __.a.Protocol ):
    ''' General location access adapter. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    @__.abstract_member_function
    def from_url( selfclass, url: _core.PossibleUrl ) -> __.a.Self:
        ''' Produces adapter from URL. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def as_specific(
        self,
        force: bool = False,
        pursue_indirection: bool = True,
        species: __.Optional[ _core.LocationSpecies ] = __.absent,
    ) -> SpecificAdapter:
        ''' Returns appropriate specific adapter for location. '''
        raise NotImplementedError


@__.a.runtime_checkable
class DirectoryAdapter( AdapterBase, DirectoryOperations, __.a.Protocol ):
    ''' Directory access adapter. '''
    # TODO: Immutable class and object attributes.


@__.a.runtime_checkable
class FileAdapter( AdapterBase, FileOperations, __.a.Protocol ):
    ''' File access adapter. '''
    # TODO: Immutable class and object attributes.


@__.a.runtime_checkable
class GeneralCache( CacheBase, GeneralOperations, __.a.Protocol ):
    ''' General location cache. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    @__.abstract_member_function
    def from_url( selfclass, url: _core.PossibleUrl ) -> __.a.Self:
        ''' Produces cache from URL. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def as_specific(
        self,
        species: __.Optional[ _core.LocationSpecies ] = __.absent,
    ) -> SpecificAdapter:
        ''' Returns appropriate specific cache for location. '''
        raise NotImplementedError


@__.a.runtime_checkable
class DirectoryCache( CacheBase, DirectoryOperations, __.a.Protocol ):
    ''' Directory cache. '''
    # TODO: Immutable class and object attributes.


@__.a.runtime_checkable
class FileCache( CacheBase, FileOperations, __.a.Protocol ):
    ''' File cache. '''
    # TODO: Immutable class and object attributes.


@__.a.runtime_checkable
class CacheManager( ReconciliationOperations, __.a.Protocol ):
    ''' Manager for collection of caches.

        Typically maintains an anchor path, associated with the root of a
        directory tree, such as the clone of a VCS repository. Shared among all
        cache objects within the tree. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    @__.abstract_member_function
    async def from_url( selfclass, url: __.PossibleUrl ) -> __.a.Self:
        ''' Produces cache manager from storage location URL. '''
        raise NotImplementedError

    @__.abstract_member_function
    def as_url( self ) -> _core.Url:
        ''' Returns URL associated with cache storage location. '''
        raise NotImplementedError

    @__.abstract_member_function
    def produce_cache( self, adapter: GeneralAdapter ) -> GeneralCache:
        ''' Produces cache from general location access adapter. '''
        raise NotImplementedError


# TODO: Python 3.12: type statement for aliases

DirectoryAccessor: __.a.TypeAlias = DirectoryAdapter | DirectoryCache
FileAccessor: __.a.TypeAlias = FileAdapter | FileCache
GeneralAccessor: __.a.TypeAlias = GeneralAdapter | GeneralCache
PossibleFilter: __.a.TypeAlias = bytes | str | Filter
PossibleRelativeLocator: __.a.TypeAlias = (
    __.PossiblePath | __.AbstractIterable[ __.PossiblePath ] )
SpecificAccessor: __.a.TypeAlias = DirectoryAccessor | FileAccessor
SpecificAdapter: __.a.TypeAlias = DirectoryAdapter | FileAdapter
SpecificCache: __.a.TypeAlias = DirectoryCache | FileCache

CreateParentsArgument: __.a.TypeAlias = __.a.Annotation[
    bool, __.a.Doc( ''' Create parent directories if they do not exist. ''' )
]
