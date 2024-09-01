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


''' Abstract base classes and factories for locations. '''

# TODO: Split into 'arguments' and 'interfaces' modules.
# TODO: Caching variant of accessors has source adapter and cache adapter and
#       'commit_to_source', 'difference_with_source', and 'update_from_source'
#       methods.
#       Edits happen on cache and are only committed to source when explicitly
#       requested. Useful for 'git', 'github', 'hg', etc... protocol schemes.
#       AI invocables can use cache accessors to be safe, even with local
#       files.
#       Cache will be created in temporary file or directory on instantiation
#       of caching accessor; will last lifetime of accessor which holds context
#       manager for the temporary. Cache adapter will be provided URL to
#       temporary.
#       Cache can have expiry or TTL to trigger refreshes on operations
#       or maybe async scheduled callbacks. Use for performance enhancement
#       scenarios.
# TODO: Filesystem information objects from accessors.
#       For Git and other VCS schemes, provides discoverability for branches,
#       which can be used to shape cache interactions.
#       For Github and other VCS wrapper schemes, provides repository metadata,
#       possibly including workflows.
#       For local filesystems could include snapshots (ZFS, Time Machine,
#       etc...).
# TODO: Arguments DTO for 'check_access' methods.
#       * pursue_indirection: (defaults to true)
#           - local fs: follow symlinks
#           - HTTP: follow redirects
#       * mode bits: acquire/create/update/delete/execute
#           - local fs: R_OK/W_OK/W_OK/W_OK/X_OK
#           - HTTP: GET/PUT/PATCH/DELETE/POST
# TODO: Add indirection pursuit option to 'is_directory' and 'is_file' methods.


from __future__ import annotations

from urllib.parse import ParseResult as _UrlParts

from . import __


class _Common( __.a.Protocol ):

    def __str__( self ) -> str: return str( self.as_url( ) )

    @__.abstract_member_function
    def as_url( self ) -> Url:
        ''' Returns URL associated with location. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def check_access( self ) -> bool:
        ''' Does current process have access to location? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def check_existence( self ) -> bool:
        ''' Does location exist? '''
        raise NotImplementedError

    @__.abstract_member_function
    def expose_implement( self ) -> Implement:
        ''' Exposes concrete implement used to perform operations. '''
        raise NotImplementedError

    # TODO: register_notifier


class AccessorBase( _Common, __.a.Protocol ):
    ''' Common functionality for all accessors. '''


class AdapterBase( _Common, __.a.Protocol ):
    ''' Common functionality for all access adapters. '''


@__.a.runtime_checkable
class GeneralOperations( __.a.Protocol ):
    ''' Standard operations on locations of indeterminate species. '''

    @__.abstract_member_function
    async def is_directory( self ) -> bool:
        ''' Is location a directory? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def is_file( self ) -> bool:
        ''' Is location a regular file? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def is_indirection( self ) -> bool:
        ''' Does location provide indirection to another location? '''
        raise NotImplementedError

    # TODO: stat


@__.a.runtime_checkable
class DirectoryOperations( __.a.Protocol ):
    ''' Standard operations on directories. '''

    # TODO: survey_entries

    # TODO: create_entry

    # TODO: delete_entry

    # TODO: produce_entry_accessor


@__.a.runtime_checkable
class FileOperations( __.a.Protocol ):
    ''' Standard operations on files. '''

    # TODO: report_mimetype

    # TODO: acquire_content

    # TODO: acquire_content_continuous

    # TODO: acquire_content_bytes

    # TODO: acquire_content_bytes_continuous

    # TODO: update_content

    # TODO: update_content_continuous

    # TODO: update_content_bytes

    # TODO: update_content_bytes_continuous


@__.a.runtime_checkable
class GeneralAccessor( AccessorBase, GeneralOperations, __.a.Protocol ):
    ''' General location accessor. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    @__.abstract_member_function
    def from_url( selfclass, url: UrlLike ) -> __.a.Self:
        ''' Produces accessor from URL. '''
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
    def from_url( selfclass, url: UrlLike ) -> __.a.Self:
        ''' Produces adapter from URL. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def as_specific( self ) -> SpecificAdapter:
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


class Implement( metaclass = __.ABCFactory ):
    ''' Abstract base class for location implement types. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.
    #       Functions which return implements should cast.


class Url( _UrlParts, metaclass = __.AccretiveClass ):
    ''' Tracks URL components separately. Displays as original string. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def from_url( selfclass, url: UrlLike ) -> __.a.Self:
        ''' Produces canonical URL instance from URL-like object. '''
        if isinstance( url, __.PathLike ): url = url.__fspath__( )
        if isinstance( url, ( str, bytes ) ): url = __.urlparse( url )
        if isinstance( url, _UrlParts ):
            return selfclass(
                scheme = url.scheme,
                netloc = url.netloc,
                path = url.path,
                params = url.params,
                query = url.query,
                fragment = url.fragment )
        from .exceptions import InvalidUrlClassError
        raise InvalidUrlClassError( type( url ) )

    def __repr__( self ) -> str: return super( ).__repr__( )

    def __str__( self ) -> str: return self.geturl( )


# TODO: Python 3.12: type statement for aliases
SpecificAccessor: __.a.TypeAlias = DirectoryAccessor | FileAccessor
SpecificAdapter: __.a.TypeAlias = DirectoryAdapter | FileAdapter
UrlLike: __.a.TypeAlias = bytes | str | __.PathLike | _UrlParts


# TODO: Use validator accretive dictionaries for registries.
accessors_registry = __.AccretiveDictionary( )


def accessor_from_url(
    url: UrlLike, species: str = 'simple'
) -> GeneralAccessor:
    ''' Produces location accessor from URL. '''
    # TODO: Use enum for accessor species.
    return accessors_registry[ species ].from_url( url = url )


def registrant_from_url(
    registry: __.AbstractDictionary[ str, __.a.Any ],
    url: UrlLike,
) -> __.a.Any:
    ''' Returns entry from registry if URL scheme matches. '''
    url = Url.from_url( url )
    scheme = url.scheme
    if scheme in registry: return registry[ scheme ]
    from .exceptions import NoUrlSchemeSupportError
    raise NoUrlSchemeSupportError( url )
