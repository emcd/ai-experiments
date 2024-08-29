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

    def expose_implement( self ) -> Implement:
        ''' Exposes concrete implement used to perform operations. '''
        return self.adapter.expose_implement( )


@__.a.runtime_checkable
class Adapter( __.a.Protocol ):
    ''' Location access adapter. Wraps concrete implement for access. '''
    # TODO: Immutable class and object attributes.

    url: Url

    @classmethod
    def from_url( selfclass, url: UrlLike ) -> __.a.Self:
        ''' Produces adapter from URL. '''
        return selfclass( url = Url.from_url( url ) )

    def __str__( self ) -> str: return str( self.url )

    def __init__( self, url: Url ): self.url = url

    @__.abstract_member_function
    def expose_implement( self ) -> Implement:
        ''' Exposes concrete implement used to perform operations. '''


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
