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


# TODO: Python 3.12: type statement for aliases
PossibleUrl: __.a.TypeAlias = bytes | str | __.PathLike | _UrlParts


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

    # Maybe return inode on completion of whole file operations?
    # Would be a useful streamline for cache management.


@__.standard_dataclass
class AcquireContentBytesResult:
    ''' Result, as raw bytes, from content acquisition operation. '''

    content: bytes
    mimetype: str


@__.standard_dataclass
class AcquireContentTextResult:
    ''' Result, as Unicode string, from content acquisition operation. '''

    charset: str
    content: str
    mimetype: str


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

    mimetype: str
    permissions: Permissions
    species: LocationSpecies
    supplement: AdapterInode

    def is_directory( self ) -> bool:
        ''' Does inode represent a directory? '''
        return LocationSpecies.Directory is self.species

    def is_file( self ) -> bool:
        ''' Does inode represent a regular file? '''
        return LocationSpecies.File is self.species

    def is_indirection( self ) -> bool:
        ''' Does inode represent an indirection? '''
        return LocationSpecies.Symlink is self.species


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


@__.standard_dataclass
class UpdateContentResult:
    ''' Result of content update operation. '''

    charset: __.a.Nullable[ str ]
    count: int
    mimetype: str


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


# TODO: Streaming codecs for reduced memory footprint.
#       Not zero-copy, but can use constant-sized memory window.


def decode_content(
    content: bytes,
    charset: __.Optional[ str ] = __.absent,
    charset_errors: __.Optional[ str ] = __.absent,
) -> str:
    match charset:
        case __.absent:
            from locale import getpreferredencoding
            charset = getpreferredencoding( )
        case '#DETECT#':
            from chardet import detect
            charset = detect( content )[ 'encoding' ]
    if __.absent is charset_errors: charset_errors = 'strict'
    return content.decode( charset, errors = charset_errors )


def encode_content(
    content: str,
    charset: __.Optional[ str ] = __.absent,
    charset_errors: __.Optional[ str ] = __.absent,
) -> ( bytes, str ):
    if __.absent is charset:
        from locale import getpreferredencoding
        charset = getpreferredencoding( )
    if __.absent is charset_errors: charset_errors = 'strict'
    content_bytes = content.encode( charset, errors = charset_errors )
    return content_bytes, charset


def normalize_newlines(
    content: str, newline: __.Optional[ str ] = __.absent
) -> str:
    if '' == newline: return content
    match newline:
        case __.absent | '\n':
            return content.replace( '\r\n', '\n' ).replace( '\r', '\n' )
        case '\r':
            return content.replace( '\r\n', '\r' ).replace( '\n', '\r' )
        case '\r\n':
            return (
                content.replace( '\r\n', '\r' ).replace( '\n', '\r' )
                .replace( '\r', '\r\n' ) )
        # TODO: Error.
