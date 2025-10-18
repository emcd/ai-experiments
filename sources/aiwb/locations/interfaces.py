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


from . import __
from . import core as _core
from . import exceptions as _exceptions


class _Common(
    __.immut.Protocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Common functionality across all accessors. '''

    def __str__( self ) -> str: return str( self.as_url( ) )

    @__.abc.abstractmethod
    def as_url( self ) -> _core.Url:
        ''' Returns URL associated with location. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def check_access(
        self,
        permissions: _core.Permissions,
        pursue_indirection: bool = True,
    ) -> bool:
        ''' Does current process have access to location? '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        ''' Does location exist? '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def examine(
        self,
        attributes: _core.InodeAttributes = _core.InodeAttributes.Nothing,
        pursue_indirection: bool = True,
    ) -> _core.Inode:
        ''' Returns inode-like object for location. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def expose_implement( self ) -> _core.AccessImplement:
        ''' Exposes concrete implement used to perform operations. '''
        raise NotImplementedError

    # TODO: register_notifier


class AdapterBase(
    _Common, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Common functionality for all access adapters. '''

    @classmethod
    @__.abc.abstractmethod
    def is_cache_manager( selfclass ) -> bool:
        ''' Is access adapter a cache manager for itself?

            For cases like Git, Github, Mercurial, etc.... '''
        raise NotImplementedError


class CacheBase(
    _Common, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Common functionality for all caches. '''


@__.typx.runtime_checkable
class Filter( __.typx.Protocol ):
    ''' Determines if directory entry should be filtered. '''

    @__.abc.abstractmethod
    async def __call__( self, dirent: _core.DirectoryEntry ) -> bool:
        raise NotImplementedError


class DirectoryOperations(
    __.immut.Protocol,
    __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Standard operations on directories. '''

    @__.abc.abstractmethod
    async def create_directory(
        self,
        name: 'PossibleRelativeLocator',
        permissions: _core.Permissions | _core.PermissionsTable,
        exist_ok: bool = True,
        parents: 'CreateParentsArgument' = True,
    ) -> 'DirectoryAccessor':
        ''' Creates directory relative to URL of this accessor. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def create_file(
        self,
        name: 'PossibleRelativeLocator',
        permissions: _core.Permissions | _core.PermissionsTable,
        exist_ok: bool = True,
        parents: 'CreateParentsArgument' = True,
    ) -> 'FileAccessor':
        ''' Creates file relative to URL of this accessor. '''
        raise NotImplementedError

    # TODO: create_indirection

    @__.abc.abstractmethod
    async def delete_directory(
        self,
        name: 'PossibleRelativeLocator',
        absent_ok: bool = True,
        recurse: bool = True,
        safe: bool = True, # TODO? safeties enum
    ):
        ''' Deletes directory relative to URL of this accessor. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def delete_file(
        self,
        name: 'PossibleRelativeLocator',
        absent_ok: bool = True,
        safe: bool = True, # TODO? safeties enum
    ):
        ''' Deletes file relative to URL of this accessor. '''

    # TODO: delete_indirection

    @__.abc.abstractmethod
    def produce_entry_accessor(
        self, name: 'PossibleRelativeLocator'
    ) -> 'GeneralAccessor':
        ''' Derives new accessor relative to URL of this accessor. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def survey_entries(
        self,
        attributes: _core.InodeAttributes = _core.InodeAttributes.Nothing,
        filters: __.Absential[
            __.cabc.Iterable[ 'PossibleFilter' ]
        ] = __.absent,
        recurse: bool = True,
    ) -> __.cabc.Sequence[ _core.DirectoryEntry ]:
        ''' Returns list of directory entries, subject to filtering. '''
        raise NotImplementedError


class FileOperations(
    __.immut.Protocol,
    __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Standard operations on files. '''

    @__.abc.abstractmethod
    async def acquire_content( self ) -> bytes:
        ''' Returns content of file as raw bytes. '''
        raise NotImplementedError

    # TODO: acquire_content_continuous
    #       Returns iterator which has inode attribute.

    @__.abc.abstractmethod
    async def acquire_content_result(
        self,
        attributes: _core.InodeAttributes = _core.InodeAttributes.Nothing,
    ) -> _core.AcquireContentBytesResult:
        ''' Returns inode and content of file as raw bytes. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def update_content(
        self,
        content: bytes,
        attributes: _core.InodeAttributes = _core.InodeAttributes.Nothing,
        options: _core.FileUpdateOptions = _core.FileUpdateOptions.Defaults,
    ) -> _core.Inode:
        ''' Updates content of file from raw bytes. Returns inode. '''
        raise NotImplementedError

    # TODO: update_content_continuous


class GeneralOperations(
    __.immut.Protocol,
    __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Standard operations on locations of indeterminate species. '''

    @__.abc.abstractmethod
    def as_directory( self ) -> 'DirectoryAccessor':
        ''' Returns directory accessor without sanity checks.

            Only use this if you are certain that the entity is a directory.
        '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def as_file( self ) -> 'FileAccessor':
        ''' Returns file accessor without sanity checks.

            Only use this if you are certain that the entity is a file.
        '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def as_specific(
        self,
        force: bool = False,
        pursue_indirection: bool = True,
        species: __.Absential[ _core.LocationSpecies ] = __.absent,
    ) -> 'SpecificAccessor':
        ''' Discovers appropriate specific accessor for location. '''
        raise NotImplementedError

    async def discover_species(
        self,
        pursue_indirection: bool = True,
        species: __.Absential[ _core.LocationSpecies ] = __.absent,
    ) -> _core.LocationSpecies:
        ''' Discovers or asserts species of location. '''
        Error = __.funct.partial(
            _exceptions.LocationSpeciesAssertionError, url = self.as_url( ) )
        try:
            species_ = (
                ( await self.examine(
                    pursue_indirection = pursue_indirection ) ).species )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        if _core.LocationSpecies.Void is not species_: # exists
            if __.absent is not species and species is not species_:
                reason = (
                    f"Requested species, '{species}', "
                    f"does not match actual species, '{species_}'." )
                raise Error( reason = reason )
            return species_
        return species

    @__.abc.abstractmethod
    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        ''' Is location a directory? '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        ''' Is location a regular file? '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def is_indirection( self ) -> bool:
        ''' Does location provide indirection to another location? '''
        raise NotImplementedError


class ReconciliationOperations(
    __.immut.Protocol,
    __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Standard operations for cache reconciliation. '''

    # TODO? Allow aliens, conflicts, and impurities arguments to be single enum
    #       applied to all objects in reconciliation operation or to be a table
    #       of URL-to-action entries for finer-grained control.

    # TODO? clear

    @__.abc.abstractmethod
    async def commit(
        self, *,
        aliens: _core.AlienResolutionActions
            = _core.AlienResolutionActions.Ignore,
        conflicts: _core.ConflictResolutionActions
            = _core.ConflictResolutionActions.Error,
        impurities: _core.ImpurityResolutionActions
            = _core.ImpurityResolutionActions.Ignore,
    ) -> __.typx.Self: # TODO: Return dirents of affected locations.
        ''' Commits cache to sources. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def difference(
        self
    ) -> __.cabc.Sequence[ _core.CacheDifferenceBase ]:
        ''' Reports differences between cache and sources. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def is_divergent( self ) -> bool:
        ''' Checks if cache matches sources. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def reingest(
        self, *,
        aliens: _core.AlienResolutionActions
            = _core.AlienResolutionActions.Ignore,
        conflicts: _core.ConflictResolutionActions
            = _core.ConflictResolutionActions.Error,
        impurities: _core.ImpurityResolutionActions
            = _core.ImpurityResolutionActions.Ignore,
    ) -> __.typx.Self: # TODO: Return dirents of affected locations.
        ''' Reingests cache from sources. '''
        raise NotImplementedError


class DirectoryAdapter(
    AdapterBase, DirectoryOperations, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Directory access adapter. '''


class FileAdapter(
    AdapterBase, FileOperations, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' File access adapter. '''


class GeneralAdapter(
    AdapterBase, GeneralOperations, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' General location access adapter. '''

    @classmethod
    @__.abc.abstractmethod
    def from_url( selfclass, url: _core.PossibleUrl ) -> __.typx.Self:
        ''' Produces adapter from URL. '''
        raise NotImplementedError


class CacheManager(
    ReconciliationOperations, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Manager for collection of caches.

        Typically maintains an anchor path, associated with the root of a
        directory tree, such as the clone of a VCS repository. '''
    # TODO: Immutable instance attributes.

    @classmethod
    @__.abc.abstractmethod
    async def from_url( selfclass, url: _core.PossibleUrl ) -> __.typx.Self:
        ''' Produces cache manager from storage location URL. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def as_url( self ) -> _core.Url:
        ''' Returns URL associated with cache storage location. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    def produce_cache( self, adapter: 'GeneralAdapter' ) -> 'GeneralCache':
        ''' Produces cache from general location access adapter. '''
        raise NotImplementedError


class DirectoryCache(
    CacheBase, DirectoryOperations, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' Directory cache. '''


class FileCache(
    CacheBase, FileOperations, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' File cache. '''


class GeneralCache(
    CacheBase, GeneralOperations, __.typx.Protocol,
    class_decorators = ( __.typx.runtime_checkable, ),
):
    ''' General location cache. '''

    @classmethod
    @__.abc.abstractmethod
    def from_url( selfclass, url: _core.PossibleUrl ) -> __.typx.Self:
        ''' Produces cache from URL. '''
        raise NotImplementedError


class FilePresenter(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Presenter with standard operations on files. '''

    accessor: 'FileAccessor'

    @__.abc.abstractmethod
    async def acquire_content( self ) -> __.typx.Any:
        ''' Returns content of file as specific type. '''
        raise NotImplementedError

    # TODO: acquire_content_continuous
    #       Returns iterator which has inode attribute.

    @__.abc.abstractmethod
    async def acquire_content_result(
        self, *,
        attributes: _core.InodeAttributes = _core.InodeAttributes.Nothing,
    ) -> _core.AcquireContentResult:
        ''' Returns inode and content of file as specific type. '''
        raise NotImplementedError

    @__.abc.abstractmethod
    async def update_content(
        self,
        content: __.typx.Any,
        attributes: _core.InodeAttributes = _core.InodeAttributes.Nothing,
        options: _core.FileUpdateOptions = _core.FileUpdateOptions.Defaults,
    ) -> _core.Inode:
        ''' Updates content of file from specific type. Returns inode. '''
        raise NotImplementedError

    # TODO: update_content_continuous


# TODO: Python 3.12: type statement for aliases

DirectoryAccessor: __.typx.TypeAlias = DirectoryAdapter | DirectoryCache
FileAccessor: __.typx.TypeAlias = FileAdapter | FileCache
GeneralAccessor: __.typx.TypeAlias = GeneralAdapter | GeneralCache
PossibleFilter: __.typx.TypeAlias = bytes | str | Filter
PossibleRelativeLocator: __.typx.TypeAlias = (
    __.PossiblePath | __.cabc.Iterable[ __.PossiblePath ] )
SpecificAccessor: __.typx.TypeAlias = DirectoryAccessor | FileAccessor
SpecificAdapter: __.typx.TypeAlias = DirectoryAdapter | FileAdapter
SpecificCache: __.typx.TypeAlias = DirectoryCache | FileCache

CreateParentsArgument: __.typx.TypeAlias = __.typx.Annotated[
    bool,
    __.typx.Doc( ''' Create parent directories if they do not exist. ''' ),
]
