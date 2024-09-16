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


from __future__ import annotations

from urllib.parse import ParseResult as _UrlParts

from . import __


class AccessImplement( metaclass = __.ABCFactory ):
    ''' Abstract base class for location access implements. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.
    #       Functions which return implements should cast.


class AdapterInode( metaclass = __.ABCFactory ):
    ''' Abstract base class for adapter-specific location information. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.
    #       Functions which return implements should cast.

    # git/hg: relevant branches and tags?


@__.standard_dataclass
class AcquireContentBytesResult:
    ''' Result, as raw bytes, from content acquisition operation. '''

    content: bytes
    inode: Inode


@__.standard_dataclass
class AcquireContentTextResult:
    ''' Result, as Unicode string, from content acquisition operation. '''

    content: str
    inode: Inode


@__.standard_dataclass
class DirectoryEntry:
    ''' Location plus information about it. '''

    inode: Inode
    url: Url

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
    Append = __.produce_enumeration_value( ) # append
    Absence = __.produce_enumeration_value( ) # error (if exists)


@__.standard_dataclass
class Inode:
    ''' Information about location. '''

    species: LocationSpecies
    permissions: Permissions
    supplement: AdapterInode
    bytes_count: __.Nullable[ int ] = None
    content_id: __.Nullable[ str ] = None
    mimetype: __.Nullable[ str ] = None
    charset: __.Nullable[ str ] = None
    mtime: __.Nullable[ __.DateTime ] = None # modification time
    etime: __.Nullable[ __.DateTime ] = None # expiration time

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

    def with_attributes(
        self,
        bytes_count: __.Optional[ __.a.Nullable[ int ] ] = __.absent,
        content_id: __.Optional[ __.a.Nullable[ str ] ] = __.absent,
        mimetype: __.Optional[ __.a.Nullable[ str ] ] = __.absent,
        charset: __.Optional[ __.a.Nullable[ str ] ] = __.absent,
        mtime: __.Optional[ __.a.Nullable[ __.DateTime ] ] = __.absent,
        etime: __.Optional[ __.a.Nullable[ __.DateTime ] ] = __.absent,
    ) -> __.a.Self:
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
    BytesCount = __.produce_enumeration_value( )
    ContentId = __.produce_enumeration_value( )
    Mimetype = __.produce_enumeration_value( )
    Charset = __.produce_enumeration_value( )
    Mtime = __.produce_enumeration_value( ) # modification time
    Etime = __.produce_enumeration_value( ) # expiration time


class LocationSpecies( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Species of entity at location. '''
    # TODO: Windows-specific and other OS-specific entities.
    # TODO? Forks.

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
    Retrieve = __.produce_enumeration_value( )
    Create = __.produce_enumeration_value( )
    Update = __.produce_enumeration_value( )
    Delete = __.produce_enumeration_value( )
    Execute = __.produce_enumeration_value( )

Permissions_CUD = Permissions.Create | Permissions.Update | Permissions.Delete
Permissions_RCUD = Permissions_CUD | Permissions.Retrieve
Permissions_RCUDX = Permissions_RCUD | Permissions.Execute


class Possessor( __.Enum ):
    ''' Representation of potential owner of location. '''

    CurrentUser = 'current user'
    CurrentPopulation = 'current user population' # aka., group
    Omnipopulation = 'everyone'


class Url( _UrlParts, metaclass = __.AccretiveClass ):
    ''' Tracks URL components separately. Displays as original string. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def from_url( selfclass, url: PossibleUrl ) -> __.a.Self:
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

    def with_path( self, path: __.PossiblePath ) -> __.a.Self:
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
PermissionsTable: __.a.TypeAlias = (
    __.AbstractDictionary[ Possessor, Permissions ] )
PossibleUrl: __.a.TypeAlias = bytes | str | __.PathLike | _UrlParts
