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

''' Location access adapter with httpx. '''


from __future__ import annotations

import httpx as _httpx

from . import __


__.Implement.register( _httpx.URL )


class _Common:
    # TODO: Immutable class and object attributes.

    implement: _httpx.URL
    url: __.Url

    def __init__( self, url: __.Url ):
        self.implement = _httpx.URL( url.geturl( ) )
        self.url = url
        super().__init__()

    def as_url( self ) -> __.Url:
        return self.url

    async def check_access(
        self, arguments: __.CheckAccessArguments
    ) -> bool:
        from .exceptions import CheckAccessOperationFailure
        permissions = arguments.permissions
        async with _httpx.AsyncClient(
            follow_redirects = arguments.pursue_indirection
        ) as client: response = await client.options( self.implement )
        try: response.raise_for_status( )
        except _httpx.HTTPStatusError as exc:
            raise CheckAccessOperationFailure(
                self.url, reason = exc ) from exc
        if __.Permissions.Abstain == permissions: return True
        allowed_methods = frozenset( map(
            str.upper, response.headers.get( 'allow', '' ).split( ', ' ) ) )
        required_methods = _map_permissions_to_methods( permissions )
        return required_methods == required_methods & allowed_methods

    async def check_existence( self ) -> bool:
        async with _httpx.AsyncClient() as client:
            response = await client.head( self.implement )
        return 200 == response.status_code

    def expose_implement( self ) -> __.Implement:
        return __.a.cast( __.Implement, self.implement )


class GeneralAdapter( _Common, __.GeneralAdapter ):
    ''' General location access adapter with httpx. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def from_url( selfclass, url: __.UrlLike ) -> __.a.Self:
        return selfclass( url = __.Url.from_url( url ) )

    async def as_specific( self ) -> __.SpecificAdapter:
        return FileAdapter( url = self.url )

    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        # HTTP locations are not directories.
        return False

    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        # Every HTTP location is treated as a file.
        return True

    async def is_indirection( self ) -> bool:
        # HTTP locations can be redirects.
        async with _httpx.AsyncClient() as client:
            response = await client.head( self.implement )
            return response.is_redirect

# TODO? Perform registrations as part of module preparation function.
__.adapters_registry[ 'http' ] = GeneralAdapter
__.adapters_registry[ 'https' ] = GeneralAdapter


class FileAdapter( _Common, __.FileAdapter ):
    ''' File access adapter with httpx. '''


def _map_permissions_to_methods(
    permissions: __.Permissions
) -> frozenset[ str ]:
    methods = set( )
    if permissions & __.Permissions.Retrieve:
        methods.add( 'GET' )
    if permissions & __.Permissions.Create:
        methods.add( 'PUT' )
    if permissions & __.Permissions.Update:
        methods.update( ( 'PUT', 'PATCH' ) )
    if permissions & __.Permissions.Delete:
        methods.add( 'DELETE' )
    if permissions & __.Permissions.Execute:
        methods.add( 'POST' )
    return frozenset( methods )
