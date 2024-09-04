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

    # http/https: cache etag and TTL?
    # git/hg: relevant branches and tags?

    # Maybe return inode on completion of whole file operations?
    # Would be a useful streamline for cache management.


class LocationSpecies( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Species of entity at location. '''
    # TODO: Windows-specific and other OS-specific entities.
    # TODO? Forks.

    Bareblocks = 'bareblocks' # e.g., block device
    Bytestream = 'bytestream' # e.g., character device
    Directory = 'directory'
    File = 'file'
    Pipe = 'pipe' # e.g., FIFO, named pipe
    Socket = 'socket' # Unix domain socket in filesystem
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
        from .exceptions import InvalidUrlClassError
        raise InvalidUrlClassError( type( url ) )

    def __repr__( self ) -> str: return super( ).__repr__( )

    def __str__( self ) -> str: return self.geturl( )
