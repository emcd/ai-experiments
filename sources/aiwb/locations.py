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


''' Abstraction and common implementations for various kinds of location. '''


from __future__ import annotations

from urllib.parse import ParseResult as _UrlParts

from . import __


class Accessor( metaclass = __.ABCFactory ):
    ''' Dynamically-registered superclass for location accessor types. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.

Accessor.register( __.Path )


@__.a.runtime_checkable
@__.standard_dataclass
class Location( __.a.Protocol ):
    ''' Abstract location. '''

    url: Url

    @__.abstract_member_function
    def produce_accessor( self ) -> Accessor:
        ''' Produces accessor for location. '''
        # TODO? Option for async.
        raise NotImplementedError


@__.standard_dataclass
class FsLocation( Location ):
    ''' Filesystem location. '''

    def __post_init__( self ):
        netloc = self.url.netloc
        if netloc and '.' != netloc:
            raise NotImplementedError(
                f"Shares not supported in file URLs. URL: {self.url}" )

    def produce_accessor( self ) -> Accessor:
        url = self.url
        if '.' == url.netloc: accessor = __.Path( ) / url.path
        else: accessor = __.Path( url.path )
        # Cast because we do not have a common protocol.
        return __.a.cast( Accessor, accessor )


class Url( _UrlParts ):
    ''' Extension of standard library URL parse result. '''

    def __repr__( self ) -> str: return super( ).__repr__( )

    def __str__( self ) -> str: return self.geturl( )


# TODO: Use validator accretive dictionary for location classes registry.
location_classes = __.AccretiveDictionary( )
location_classes[ '' ] = FsLocation
location_classes[ 'file' ] = FsLocation
# TODO: http / https


def location_from_url( url: str | _UrlParts | Url ) -> Location:
    ''' Produces location from URL. '''
    if isinstance( url, str ): url = __.urlparse( url )
    if not isinstance( url, Url ) and isinstance( url, _UrlParts ):
        url = Url(
            url.scheme, url.netloc, url.path,
            url.params, url.query, url.fragment )
    # TODO: Error on invalid URL type.
    scheme = url.scheme
    if scheme in location_classes:
        return location_classes[ scheme ]( url = url )
    raise NotImplementedError(
        f"URL scheme {scheme!r} not supported. URL: {url}" )
