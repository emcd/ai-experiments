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


__.AccessImplement.register( _httpx.URL )


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
        self,
        permissions: __.Permissions,
        pursue_indirection: bool = True,
    ) -> bool:
        async with _httpx.AsyncClient(
            follow_redirects = pursue_indirection
        ) as client: response = await client.options( self.implement )
        try: response.raise_for_status( )
        except _httpx.HTTPStatusError as exc:
            raise __.LocationCheckAccessFailure(
                self.url, reason = exc ) from exc
        if __.Permissions.Abstain == permissions: return True
        allowed_methods = frozenset( map(
            str.upper, response.headers.get( 'Allow', '' ).split( ', ' ) ) )
        required_methods = _permissions_to_methods( permissions )
        return required_methods == required_methods & allowed_methods

    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        from http import HTTPStatus
        async with _httpx.AsyncClient(
            follow_redirects = pursue_indirection
        ) as client: response = await client.head( self.implement )
        return HTTPStatus.OK == response.status_code

    async def examine( self, pursue_indirection: bool = True ) -> __.Inode:
        async with _httpx.AsyncClient(
            follow_redirects = pursue_indirection
        ) as client:
            permissions = await self._inspect_permissions( client )
            if not __.Permissions.Retrieve & permissions:
                raise __.LocationExamineFailure(
                    self.url, reason = "Retrieval request not allowed." )
            try:
                response = await client.head( self.implement )
                response.raise_for_status( )
            except _httpx.HTTPStatusError as exc:
                raise __.LocationExamineFailure(
                    self.url, reason = exc ) from exc
            mimetype = response.headers.get(
                'Content-Type', 'application/octet-stream' )
            inode = _http_inode_from_response( response )
            return __.Inode(
                mimetype = mimetype,
                permissions = permissions,
                species = __.LocationSpecies.File,
                supplement = inode
            )

    def expose_implement( self ) -> __.AccessImplement:
        return __.a.cast( __.AccessImplement, self.implement )

    async def _inspect_permissions(
        self, client: _httpx.AsynClient
    ) -> __.Permissions:
        try:
            response = await client.options( self.implement )
            response.raise_for_status( )
        except _httpx.HTTPStatusError as exc:
            raise __.LocationExamineFailure(
                self.url, reason = exc ) from exc
        methods = frozenset( map(
            str.upper, response.headers.get( 'Allow', '' ).split( ', ' ) ) )
        return _methods_to_permissions( methods )


class GeneralAdapter( _Common, __.GeneralAdapter ):
    ''' General location access adapter with httpx. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def from_url( selfclass, url: __.PossibleUrl ) -> __.a.Self:
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
        async with _httpx.AsyncClient( ) as client:
            response = await client.head( self.implement )
            return response.is_redirect

# TODO? Perform registrations as part of module preparation function.
__.adapters_registry[ 'http' ] = GeneralAdapter
__.adapters_registry[ 'https' ] = GeneralAdapter


class FileAdapter( _Common, __.FileAdapter ):
    ''' File access adapter with httpx. '''
    # TODO: Immutable class and object attributes.

    async def acquire_content(
        self,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> str:
        async with _httpx.AsyncClient( ) as client:
            response = await client.get( self.implement )
        response.raise_for_status( ) # TODO: Exception handling.
        content_type = response.headers.get( 'Content-Type', '' )
        mimetype, _, params = content_type.partition( ';' )
        if not mimetype:
            from magic import from_buffer
            mimetype = from_buffer( response.content, mime = True )
        if charset in ( __.absent, '#DETECT#' ) and 'charset=' in params:
            charset = params.split( 'charset=' )[ -1 ].strip( )
        if charset in ( __.absent, '#DETECT#' ):
            from chardet import detect
            charset = detect( response.content )[ 'encoding' ]
        # TODO: Newline translation.
        content = response.content.decode( charset, errors = charset_errors )
        return __.ContentTextResult(
            content = content, mimetype = mimetype, charset = charset )
        #return response.text

    async def acquire_content_bytes( self ) -> bytes:
        async with _httpx.AsyncClient( ) as client:
            response = await client.get( self.implement )
        response.raise_for_status( ) # TODO: Exception handling.
        content_type = response.headers.get( 'Content-Type', '' )
        mimetype, _, _ = content_type.partition( ';' )
        if not mimetype:
            from magic import from_buffer
            mimetype = from_buffer( response.content, mime = True )
        return __.ContentBytesReesult(
            content = response.content, mimetype = mimetype )


@__.standard_dataclass
class HttpInode( __.AdapterInode ):
    ''' HTTP-specific information of relevance for location. '''

    etag: str | None
    expiration: __.DateTime | None
    mtime: __.DateTime | None


def _expiration_from_response( response: _httpx.Response ) -> __.DateTime:
    from email.utils import parsedate_to_datetime
    cache_control = response.headers.get( 'Cache-Control' )
    expires = response.headers.get( 'Expires' )
    expiration = None
    if cache_control:
        directives = dict(
            directive.split( '=' )
            for directive in cache_control.split( ', ' )
            if '=' in directive )
        max_age = directives.get( 'max-age' )
        if max_age:
            expiration = (
                __.DateTime.utcnow( )
                + __.TimeDelta( seconds = int( max_age ) ) )
    if not expiration and expires:
        expiration = parsedate_to_datetime( expires )
    return expiration


def _http_inode_from_response( response: _httpx.Response ) -> HttpInode:
    from email.utils import parsedate_to_datetime
    etag = response.headers.get( 'ETag' )
    mtime = response.headers.get( 'Last-Modified' )
    if mtime: mtime = parsedate_to_datetime( mtime )
    expiration = _expiration_from_response( response )
    return HttpInode( etag = etag, expiration = expiration, mtime = mtime )


def _methods_to_permissions(
    methods: __.AbstractCollection[ str ]
) -> __.Permissions:
    permissions = __.Permissions.Abstain
    if 'GET' in methods:
        permissions |= __.Permissions.Retrieve
    if 'PUT' in methods:
        permissions |= ( __.Permissions.Create | __.Permissions.Update )
    if 'PATCH' in methods:
        permissions |= __.Permissions.Update
    if 'DELETE' in methods:
        permissions |= __.Permissions.Delete
    if 'POST' in methods:
        permissions |= __.Permissions.Execute
    return permissions


def _permissions_to_methods(
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
