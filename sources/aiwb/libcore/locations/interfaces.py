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


class AccessorBase( _Common, __.a.Protocol ):
    ''' Common functionality for all accessors. '''


class AdapterBase( _Common, __.a.Protocol ):
    ''' Common functionality for all access adapters. '''


@__.a.runtime_checkable
class Cache( __.a.Protocol ):
    ''' Standard operations on cache. '''

    # TODO? clear

    # TODO? report_modifications


@__.a.runtime_checkable
class Filter( __.a.Protocol ):
    ''' Determines if directory entry should be filtered. '''

    @__.abstract_member_function
    async def __call__( self, dirent: _core.DirectoryEntry ) -> bool:
        raise NotImplementedError


@__.a.runtime_checkable
class DirectoryOperations( __.a.Protocol ):
    ''' Standard operations on directories. '''

    async def survey_entries(
        self,
        filters: __.Optional[
            __.AbstractIterable[ PossibleFilter ]
        ] = __.absent,
        recurse: bool = True,
    ) -> __.AbstractSequence[ _core.DirectoryEntry ]:
        ''' Returns list of directory entries, subject to filtering. '''
        raise NotImplementedError

    # TODO: create_entry

    # TODO: delete_entry

    # TODO: produce_entry_accessor


@__.a.runtime_checkable
class FileOperations( __.a.Protocol ):
    ''' Standard operations on files. '''

    async def acquire_content(
        self,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> _core.ContentTextResult:
        ''' Returns complete content of file as Unicode string. '''
        raise NotImplementedError

    # TODO: acquire_content_continuous

    async def acquire_content_bytes( self ) -> _core.ContentBytesResult:
        ''' Returns complete content of file as raw bytes. '''
        raise NotImplementedError

    # TODO: acquire_content_bytes_continuous

    # TODO: update_content

    # TODO: update_content_continuous

    # TODO: update_content_bytes

    # TODO: update_content_bytes_continuous


@__.a.runtime_checkable
class GeneralOperations( __.a.Protocol ):
    ''' Standard operations on locations of indeterminate species. '''

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

    # TODO: is_cache_valid

    # TODO: commit_to_source

    # TODO: difference_with_source

    # TODO: update_from_source


@__.a.runtime_checkable
class GeneralAccessor( AccessorBase, GeneralOperations, __.a.Protocol ):
    ''' General location accessor. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    @__.abstract_member_function
    def from_url( selfclass, url: _core.PossibleUrl ) -> __.a.Self:
        ''' Produces accessor from URL. '''
        # TODO? Remove from interface specification.
        raise NotImplementedError

    @__.abstract_member_function
    async def as_specific( self ) -> SpecificAccessor:
        ''' Returns appropriate specific accessor for location. '''
        raise NotImplementedError


@__.a.runtime_checkable
class DirectoryAccessor( AccessorBase, DirectoryOperations, __.a.Protocol ):
    ''' Directory accessor for location. '''
    # TODO: Immutable class and object attributes.


@__.a.runtime_checkable
class FileAccessor( AccessorBase, FileOperations, __.a.Protocol ):
    ''' File accessor for location. '''
    # TODO: Immutable class and object attributes.


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
    async def as_specific( self ) -> SpecificAdapter:
        ''' Returns appropriate specific adapter for location. '''
        raise NotImplementedError

    # TODO: classmethod is_cache_manager


@__.a.runtime_checkable
class DirectoryAdapter( AdapterBase, DirectoryOperations, __.a.Protocol ):
    ''' Directory access adapter. '''
    # TODO: Immutable class and object attributes.


@__.a.runtime_checkable
class FileAdapter( AdapterBase, FileOperations, __.a.Protocol ):
    ''' File access adapter. '''
    # TODO: Immutable class and object attributes.


# TODO: Python 3.12: type statement for aliases
PossibleCache: __.a.TypeAlias = bytes | str | __.PathLike | Cache
PossibleFilter: __.a.TypeAlias = bytes | str | Filter
SpecificAccessor: __.a.TypeAlias = DirectoryAccessor | FileAccessor
SpecificAdapter: __.a.TypeAlias = DirectoryAdapter | FileAdapter
