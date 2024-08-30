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

# TODO: Allow configuration for 'check_access' methods.
#       Follow symlinks. Read/write/execute.
#       For HTTP: maybe read -> GET, write -> PUT, execute -> POST.
#       For HTTP: maybe follow symlinks -> redirect.
# TODO: Add symlink checking option to 'is_directory' and 'is_file' methods.


from __future__ import annotations

from urllib.parse import ParseResult as _UrlParts

from . import __


# TODO: Python 3.12: type statement for aliases
UrlLike: __.a.TypeAlias = bytes | str | __.PathLike | _UrlParts


class InvalidUrlClassError( __.Omniexception, TypeError, ValueError ):
    ''' Attempt to supply an invalid class of object as a URL. '''

    def __init__( self, class_ ):
        # TODO: Interpolate fqname of class.
        super( ).__init__(
            f"Cannot use instances of class {class_!r} as URLs." )


class NoUrlSchemeSupportError( __.Omniexception, NotImplementedError ):
    ''' Attempt to use URL scheme which has no implementation. '''

    def __init__( self, url ):
        super( ).__init__(
            f"URL scheme {url.scheme!r} not supported. URL: {url}" )


@__.a.runtime_checkable
@__.standard_dataclass
class Accessor( __.a.Protocol ):
    ''' Location accessor. '''

    adapter: Adapter

    @classmethod
    def from_url(
        selfclass,
        url: UrlLike,
        adapter_class: __.Optional[ type[ Adapter ] ] = __.absent,
    ) -> __.a.Self:
        ''' Produces location accessor from URL. '''
        adapter_class = adapter_class or selfclass.provide_adapter_class( )
        return selfclass( adapter = adapter_class.from_url( url ) )

    @classmethod
    @__.abstract_member_function
    def provide_adapter_class( selfclass ) -> type[ Adapter ]:
        ''' Provides default adapter class. '''
        raise NotImplementedError

    def __str__( self ) -> str: return str( self.adapter )

    @__.abstract_member_function
    def as_directory_accessor( self ) -> DirectoryAccessor:
        ''' Returns directory accessor for location. '''
        raise NotImplementedError

    @__.abstract_member_function
    def as_file_accessor( self ) -> FileAccessor:
        ''' Returns file accessor for location. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def check_access( self ) -> bool:
        ''' Does current process have access to location? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def check_existence( self ) -> bool:
        ''' Does location exist? '''
        raise NotImplementedError

    def expose_implement( self ) -> Implement:
        ''' Exposes concrete implement used to perform operations. '''
        return self.adapter.expose_implement( )

    @__.abstract_member_function
    async def is_directory( self ) -> bool:
        ''' Is location a directory? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def is_file( self ) -> bool:
        ''' Is location a regular file? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def is_symlink( self ) -> bool:
        ''' Is location a symbolic link? '''
        raise NotImplementedError


@__.a.runtime_checkable
@__.standard_dataclass
class DirectoryAccessor( __.a.Protocol ):
    ''' Directory accessor for location. '''

    adapter: DirectoryAdapter

    def __str__( self ) -> str: return str( self.adapter )

    @__.abstract_member_function
    async def check_access( self ) -> bool:
        ''' Does current process have access to location? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def check_existence( self ) -> bool:
        ''' Does location exist? '''
        raise NotImplementedError

    def expose_implement( self ) -> Implement:
        ''' Exposes concrete implement used to perform operations. '''
        return self.adapter.expose_implement( )

    # TODO: survey

    # TODO: create_entry

    # TODO: delete_entry

    # TODO: register_notifier


@__.a.runtime_checkable
@__.standard_dataclass
class FileAccessor( __.a.Protocol ):
    ''' File accessor for location. '''

    adapter: FileAdapter

    def __str__( self ) -> str: return str( self.adapter )

    @__.abstract_member_function
    async def check_access( self ) -> bool:
        ''' Does current process have access to location? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def check_existence( self ) -> bool:
        ''' Does location exist? '''
        raise NotImplementedError

    def expose_implement( self ) -> Implement:
        ''' Exposes concrete implement used to perform operations. '''
        return self.adapter.expose_implement( )

    # TODO: report_mimetype

    # TODO: acquire_content

    # TODO: acquire_content_continuous

    # TODO: acquire_content_bytes

    # TODO: acquire_content_bytes_continuous

    # TODO: update_content

    # TODO: update_content_continuous

    # TODO: update_content_bytes

    # TODO: update_content_bytes_continuous

    # TODO: register_notifier


@__.a.runtime_checkable
class Adapter( __.a.Protocol ):
    ''' Location access adapter. Wraps concrete implement for access. '''
    # TODO: Immutable class and object attributes.

    url: Url

    @classmethod
    def from_url( selfclass, url: UrlLike ) -> __.a.Self:
        ''' Produces adapter from URL. '''
        return selfclass( url = Url.from_url( url ) )

    def __init__( self, url: Url ): self.url = url

    def __str__( self ) -> str: return str( self.url )

    @__.abstract_member_function
    def as_directory_adapter( self ) -> DirectoryAdapter:
        ''' Returns directory adapter for location. '''
        raise NotImplementedError

    @__.abstract_member_function
    def as_file_adapter( self ) -> FileAdapter:
        ''' Returns file adapter for location. '''
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

    @__.abstract_member_function
    async def is_directory( self ) -> bool:
        ''' Is location a directory? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def is_file( self ) -> bool:
        ''' Is location a regular file? '''
        raise NotImplementedError

    @__.abstract_member_function
    async def is_symlink( self ) -> bool:
        ''' Is location a symbolic link? '''
        raise NotImplementedError


@__.a.runtime_checkable
class DirectoryAdapter( __.a.Protocol ):
    ''' Directory access adapter. Wraps concrete implement for access. '''
    # TODO: Immutable class and object attributes.

    url: Url

    @classmethod
    def from_url( selfclass, url: UrlLike ) -> __.a.Self:
        ''' Produces adapter from URL. '''
        return selfclass( url = Url.from_url( url ) )

    def __init__( self, url: Url ): self.url = url

    def __str__( self ) -> str: return str( self.url )

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

    # TODO: survey

    # TODO: create_entry

    # TODO: delete_entry

    # TODO: register_notifier


@__.a.runtime_checkable
class FileAdapter( __.a.Protocol ):
    ''' File access adapter. Wraps concrete implement for access. '''
    # TODO: Immutable class and object attributes.

    url: Url

    @classmethod
    def from_url( selfclass, url: UrlLike ) -> __.a.Self:
        ''' Produces adapter from URL. '''
        return selfclass( url = Url.from_url( url ) )

    def __init__( self, url: Url ): self.url = url

    def __str__( self ) -> str: return str( self.url )

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

    # TODO: report_mimetype

    # TODO: acquire_content

    # TODO: acquire_content_continuous

    # TODO: acquire_content_bytes

    # TODO: acquire_content_bytes_continuous

    # TODO: update_content

    # TODO: update_content_continuous

    # TODO: update_content_bytes

    # TODO: update_content_bytes_continuous

    # TODO: register_notifier


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
        raise InvalidUrlClassError( type( url ) )

    def __repr__( self ) -> str: return super( ).__repr__( )

    def __str__( self ) -> str: return self.geturl( )


# TODO: Use validator accretive dictionaries for registries.
accessors_registry = __.AccretiveDictionary( )
adapters_registry = __.AccretiveDictionary( )


def accessor_from_url( url: UrlLike ) -> Accessor:
    ''' Produces location accessor from URL. '''
    url = Url.from_url( url )
    scheme = url.scheme
    if scheme in accessors_registry:
        return accessors_registry[ scheme ].from_url( url = url )
    raise NoUrlSchemeSupportError( url )
