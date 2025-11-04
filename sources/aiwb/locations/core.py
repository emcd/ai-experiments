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


''' Fundamental data structures and enumerations. '''


from urllib.parse import ParseResult as _UrlParts

from . import __


# TODO: Replace with type variable for generics.
class AccessImplement( metaclass = __.abc.ABCMeta ):
    ''' Abstract base class for location access implements. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.
    #       Functions which return implements should cast.


class AdapterInode( metaclass = __.abc.ABCMeta ):
    ''' Abstract base class for adapter-specific location information. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.
    #       Functions which return implements should cast.

    # git/hg: relevant branches and tags?


class AcquireContentResult( __.immut.DataclassObject ):
    ''' Inode and arbitrary content from acquisition operation. '''

    content: __.typx.Any
    inode: 'Inode'


class AcquireContentBytesResult( AcquireContentResult ):
    ''' Inode and content, as raw bytes, from acquisition operation. '''

    content: bytes


class AcquireContentTextResult( AcquireContentResult ):
    ''' Inode and content, as Unicode string, from acquisition operation. '''

    content: str


class AlienResolutionActions( __.enum.Enum ): # TODO: Python 3.11: StrEnum
    ''' Which action to take when unregistered cache entity is encountered.

        Simple caches might not have the concept of aliens. However, they are
        useful for VCS-backed edit caches which have the concept of a staging
        index and tracked files (e.g., Git).

        Not all resolution actions are necessarily valid for certain
        reconciliation operations with certain cache managers. Expect that
        errors will be raised in these cases.

        Custom behaviors should be specified on cache manager initialization or
        via optional argument to function.
    '''

    Custom = 'custom'   # honor accessor-specific behavior
    Delete = 'delete'   # delete unregistered entity before reconciliation
    Error = 'error'     # raise error
    Ignore = 'ignore'   # do not reconcile with sources
    Include = 'include' # reconcile with sources

    # For a Git-backed cache manager, custom alien resolution might look like:
    #   git stash push --include-untracked -- <paths>


class CacheDifferenceBase:
    ''' Base for various kinds of cache differences. '''

    # TODO: Possible subclasses:
    #   ContentCacheDifference
    #   DirentsCacheDifference
    #   InodeCacheDifference (bytes_count, content_id, mtime, species, etc...)


class ConflictResolutionActions( __.enum.Enum ): # TODO: Python 3.11: StrEnum
    ''' Which action to take upon conflict between cache and sources.

        Custom behaviors should be specified on cache manager initialization or
        via optional argument to function.
    '''

    Accept = 'accept'   # honor source differences as authoritative
    Custom = 'custom'   # honor accessor-specific behavior
    Error = 'error'     # raise error
    Reject = 'reject'   # honor cache differences as authoritative

    # For a Git-backed cache manager, the 'Accept' action might be equivalent
    # to:
    #   git fetch <remote> <branch>
    #   git merge --strategy=recursive --strategy-option=theirs \
    #       <remote>/<branch>


class DirectoryEntry(
    __.immut.DataclassObject
):
    ''' Location plus information about it. '''

    inode: 'Inode'
    url: 'Url'

    def is_directory( self ) -> bool:
        ''' Is entry a directory? '''
        return self.inode.is_directory( )

    def is_file( self ) -> bool:
        ''' Is entry a regular file? '''
        return self.inode.is_file( )

    def is_indirection( self ) -> bool:
        ''' Is entry an indirection? '''
        return self.inode.is_indirection( )


class FileUpdateOptions( __.enum.IntFlag ):
    ''' File update options bits. '''

    Defaults = 0  # create (if not exists), truncate
    Append = __.enum.auto( ) # append
    Absence = __.enum.auto( ) # error (if exists)


class ImpurityResolutionActions( __.enum.Enum ): # TODO: Python 3.11: StrEnum
    ''' Which action to take when cache has unregistered alterations.

        Simple caches might not have the concept of impurities. However, they
        are useful for VCS-backed edit caches which have the concept of a
        staging index (e.g., Git).

        Not all resolution actions are necessarily valid for certain
        reconciliation operations with certain cache managers. Expect that
        errors will be raised in these cases.

        Custom behaviors should be specified on cache manager initialization or
        via optional argument to function.
    '''

    Custom = 'custom'   # honor accessor-specific behavior
    Erase = 'erase'     # erase unregistered alterations before reconciliation
    Error = 'error'     # raise error
    Ignore = 'ignore'   # do not reconcile with sources
    Include = 'include' # reconcile with sources

    # For a Git-backed cache manager, custom alien resolution might look like:
    #   git stash push --keep-index -- <paths>


class Inode(
    __.immut.DataclassObject
):
    ''' Information about location. '''

    species: 'LocationSpecies'
    permissions: 'Permissions'
    supplement: AdapterInode
    bytes_count: __.typx.Optional[ int ] = None
    content_id: __.typx.Optional[ str ] = None
    mimetype: __.typx.Optional[ str ] = None
    charset: __.typx.Optional[ str ] = None
    mtime: __.typx.Optional[ __.DateTime ] = None # modification time
    etime: __.typx.Optional[ __.DateTime ] = None # expiration time

    def is_directory( self ) -> bool:
        ''' Does inode represent a directory? '''
        return LocationSpecies.Directory is self.species

    def is_file( self ) -> bool:
        ''' Does inode represent a regular file? '''
        return LocationSpecies.File is self.species

    def is_indirection( self ) -> bool:
        ''' Does inode represent an indirection? '''
        return LocationSpecies.Symlink is self.species

    def is_void( self ) -> bool:
        ''' Does inode represent nothing? '''
        return LocationSpecies.Void is self.species

    def with_attributes(  # noqa: PLR0913
        self,
        bytes_count: __.Absential[ __.typx.Optional[ int ] ] = __.absent,
        content_id: __.Absential[ __.typx.Optional[ str ] ] = __.absent,
        mimetype: __.Absential[ __.typx.Optional[ str ] ] = __.absent,
        charset: __.Absential[ __.typx.Optional[ str ] ] = __.absent,
        mtime: __.Absential[ __.typx.Optional[ __.DateTime ] ] = __.absent,
        etime: __.Absential[ __.typx.Optional[ __.DateTime ] ] = __.absent,
    ) -> __.typx.Self:
        ''' Returns copy with updated attributes. '''
        return type( self )(
            species = self.species,
            permissions = self.permissions,
            supplement = self.supplement,
            bytes_count = (
                self.bytes_count if __.absent is bytes_count
                else bytes_count ),
            content_id = (
                self.content_id if __.absent is content_id
                else content_id ),
            mimetype = self.mimetype if __.absent is mimetype else mimetype,
            charset = self.charset if __.absent is charset else charset,
            mtime = self.mtime if __.absent is mtime else mtime,
            etime = self.etime if __.absent is etime else etime )


class InodeAttributes( __.enum.IntFlag ):
    ''' Which nullable attributes to fill when requesting an inode. '''

    Nothing = 0
    BytesCount = __.enum.auto( )
    ContentId = __.enum.auto( )
    Mimetype = __.enum.auto( )
    Charset = __.enum.auto( )
    Mtime = __.enum.auto( ) # modification time
    Etime = __.enum.auto( ) # expiration time


class LocationSpecies( __.enum.Enum ): # TODO: Python 3.11: StrEnum
    ''' Species of entity at location. '''
    # TODO? Solaris doors, etc...

    Blocks = 'blocks' # e.g., block device
    Directory = 'directory'
    File = 'file'
    Pipe = 'pipe' # e.g., FIFO, named pipe
    Socket = 'socket' # Unix domain socket in filesystem
    Stream = 'stream' # e.g., character device
    Symlink = 'symlink'
    Void = 'void'


class Permissions( __.enum.IntFlag ):
    ''' Permissions bits to report or test access. '''

    Abstain = 0
    Retrieve = __.enum.auto( )
    Create = __.enum.auto( )
    Update = __.enum.auto( )
    Delete = __.enum.auto( )
    Execute = __.enum.auto( )

Permissions_CUD = Permissions.Create | Permissions.Update | Permissions.Delete
Permissions_RCUD = Permissions_CUD | Permissions.Retrieve
Permissions_RCUDX = Permissions_RCUD | Permissions.Execute


class Possessor( __.enum.Enum ):
    ''' Representation of potential owner of location. '''

    CurrentUser = 'current user'
    CurrentPopulation = 'current user population' # aka., group
    Omnipopulation = 'everyone'


class Url(
    __.immut.Object, _UrlParts, instances_ignore_init_arguments = True
):
    ''' Tracks URL components separately. Displays as original string. '''

    # Add explicit type annotations for ParseResult fields to fix Tyro
    # compatibility
    scheme: str
    netloc: str
    path: str
    params: str
    query: str
    fragment: str

    @classmethod
    def from_url( selfclass, url: 'PossibleUrl' ) -> __.typx.Self:
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
        from .exceptions import UrlClassValidityError
        raise UrlClassValidityError( type( url ) )

    def __repr__( self ) -> str: return super( ).__repr__( )

    def __str__( self ) -> str: return self.geturl( )

    def with_path( self, path: __.PossiblePath ) -> __.typx.Self:
        ''' Returns copy of URL with path part altered. '''
        if isinstance( path, bytes ):
            # Cannot use os.fsdecode because that is not platform-neutral,
            # which would be required for HTTP, etc....
            path = path.decode( )
        return type( self )(
            scheme = self.scheme,
            netloc = self.netloc,
            path = str( path ),
            params = self.params,
            query = self.query,
            fragment = self.fragment )


# TODO: Python 3.12: type statement for aliases
AlienResolutionActionsTable: __.typx.TypeAlias = (
    __.cabc.Mapping[ Url, AlienResolutionActions ] )
ConflictResolutionActionsTable: __.typx.TypeAlias = (
    __.cabc.Mapping[ Url, ConflictResolutionActions ] )
ImpurityResolutionActionsTable: __.typx.TypeAlias = (
    __.cabc.Mapping[ Url, ImpurityResolutionActions ] )
PermissionsTable: __.typx.TypeAlias = (
    __.cabc.Mapping[ Possessor, Permissions ] )
PossibleUrl: __.typx.TypeAlias = bytes | str | __.PathLike | _UrlParts


def is_permissions_table( table: __.typx.Any ) -> bool:
    ''' Validates table is mapping from possessors to permissions. '''
    if not isinstance( table, __.cabc.Mapping ): return False
    return all(
        isinstance( name, Possessor ) and isinstance( value, Permissions )
        for name, value in table.items( ) )
