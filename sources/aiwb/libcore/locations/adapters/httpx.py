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


_module_name = __name__.replace( f"{__package__}.", '' )
_entity_name = f"location access adapter '{_module_name}'"


__.AccessImplement.register( _httpx.URL )


class _Common:
    # TODO: Immutable class and object attributes.

    implement: _httpx.URL
    url: __.Url

    @classmethod
    def is_cache_manager( selfclass ) -> bool: return False

    def __init__( self, url: __.Url ):
        if url.scheme not in ( 'http', 'https' ):
            raise __.UrlSchemeAssertionError(
                entity_name = _entity_name, url = url )
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
        inode = await self._examine( pursue_indirection = pursue_indirection )
        if __.LocationSpecies.Void is inode.species:
            raise __.LocationExamineFailure(
                self.url, reason = "Location does not exist." )
        return inode

    def expose_implement( self ) -> __.AccessImplement:
        return __.a.cast( __.AccessImplement, self.implement )

    async def _examine( self, pursue_indirection: bool = True ) -> __.Inode:
        async with _httpx.AsyncClient(
            follow_redirects = pursue_indirection
        ) as client:
            inode_absent = __.Inode(
                mimetype = '#NOTHING#',
                permissions = __.Permissions.Abstain,
                species = __.LocationSpecies.Void,
                supplement = HttpInode.as_empty( ) )
            species, permissions = await self._inspect_permissions( client )
            if __.LocationSpecies.Void is species: return inode_absent
            if not __.Permissions.Retrieve & permissions:
                raise __.LocationExamineFailure(
                    self.url, reason = "Retrieval request not allowed." )
            response = await client.head( self.implement )
            try: response.raise_for_status( )
            except _httpx.HTTPStatusError as exc:
                from http import HTTPStatus
                if HTTPStatus.NOT_FOUND == exc.response.status_code:
                    return inode_absent
                raise __.LocationExamineFailure(
                    self.url, reason = exc ) from exc
            mimetype = response.headers.get(
                'Content-Type', 'application/octet-stream' )
            inode = _http_inode_from_response( response )
            return __.Inode(
                mimetype = mimetype,
                permissions = permissions,
                species = species,
                supplement = inode
            )

    async def _inspect_permissions(
        self, client: _httpx.AsynClient
    ) -> ( __.LocationSpecies, __.Permissions ):
        response = await client.options( self.implement )
        try: response.raise_for_status( )
        except _httpx.HTTPStatusError as exc:
            from http import HTTPStatus
            if HTTPStatus.NOT_FOUND == exc.response.status_code:
                return __.LocationSpecies.Void, __.Permissions.Abstain
            raise __.LocationExamineFailure(
                self.url, reason = exc ) from exc
        species = __.LocationSpecies.File
        methods = frozenset( map(
            str.upper, response.headers.get( 'Allow', '' ).split( ', ' ) ) )
        return species, _methods_to_permissions( methods )


class GeneralAdapter( _Common, __.GeneralAdapter ):
    ''' General location access adapter with httpx. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def from_url( selfclass, url: __.PossibleUrl ) -> __.a.Self:
        return selfclass( url = __.Url.from_url( url ) )

    async def as_specific(
        self,
        force: bool = False,
        pursue_indirection: bool = True,
        species: __.Optional[ __.LocationSpecies ] = __.absent,
    ) -> __.SpecificAdapter:
        Error = __.partial_function(
            __.LocationAdapterDerivationFailure, url = self.url )
        try:
            species_ = species if force else await self.discover_species(
                pursue_indirection = pursue_indirection, species = species )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        match species_:
            case __.LocationSpecies.File:
                return FileAdapter( url = self.url )
            case _:
                reason = (
                    "No derivative available for species "
                    f"{species_.value!r}." )
                raise Error( reason = reason )

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
    ) -> __.AcquireContentTextResult:
        Error = __.partial_function(
            __.LocationAcquireContentFailure, url = self.url )
        content_bytes, mimetype, charset_ = (
            await self._acquire_content_bytes( ) )
        if charset in ( __.absent, '#DETECT#' ): charset = charset_
        try:
            content = __.decode_content(
                content_bytes,
                charset = charset,
                charset_errors = charset_errors )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        try: content_nl = __.normalize_newlines( content, newline = newline )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        return __.AcquireContentTextResult(
            content = content_nl, mimetype = mimetype, charset = charset )

    async def acquire_content_bytes( self ) -> __.AcquireContentBytesResult:
        content, mimetype, _ = await self._acquire_content_bytes( )
        return __.AcquireContentBytesReesult(
            content = content, mimetype = mimetype )

    async def update_content(
        self,
        content: str,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.UpdateContentResult:
        Error = __.partial_function(
            __.LocationUpdateContentFailure, url = self.url )
        content_nl = _translate_newlines( content, newline = newline )
        try:
            content_bytes, charset = __.encode_content(
                content_nl,
                charset = charset,
                charset_errors = charset_errors )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        bytes_result = await self.update_content_bytes(
            content_bytes, options = options )
        return __.UpdateContentResult(
            count = bytes_result.count,
            mimetype = bytes_result.mimetype,
            charset = charset )

    async def update_content_bytes(
        self,
        content: bytes,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
    ) -> __.UpdateContentResult:
        Error = __.partial_function(
            __.LocationUpdateContentFailure, url = self.url )
        try: inode = await self._examine( )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        headers = _headers_from_file_update_options( options, inode, content )
        async with _httpx.AsyncClient( ) as client:
            response = await client.put(
                self.implement, content, headers = headers )
        try: response.raise_for_status( )
        except _httpx.HTTPStatusError as exc:
            _react_http_status_error( exc, headers, Error )
            raise Error( reason = str( exc ) ) from exc
        count, mimetype, charset = (
            _result_from_headers( response.headers, content, Error ) )
        return __.UpdateContentResult(
            count = count, mimetype = mimetype, charset = charset )

    async def _acquire_content_bytes(
        self
    ) -> ( bytes, str, str ):
        Error = __.partial_function(
            __.LocationAcquireContentFailure, url = self.url )
        async with _httpx.AsyncClient( ) as client:
            response = await client.get( self.implement )
        try: response.raise_for_status( )
        except _httpx.HTTPStatusError as exc:
            raise Error( reason = str( exc ) ) from exc
        count, mimetype, charset = (
            _result_from_headers( response.headers, response.content, Error ) )
        return response.content, mimetype, charset


@__.standard_dataclass
class HttpInode( __.AdapterInode ):
    ''' HTTP-specific information of relevance for location. '''

    etag: __.a.Nullable[ str ]
    expiration: __.a.Nullable[ __.DateTime ]
    mtime: __.a.Nullable[ __.DateTime ]
    size: __.a.Nullable[ int ]

    @classmethod
    def as_empty( selfclass ) -> __.a.Self:
        return selfclass(
            etag = None,
            expiration = None,
            mtime = None,
            size = None )


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


def _headers_from_file_update_options(
    options: __.FileUpdateOptions, inode: __.Inode, content: bytes
) -> __.AbstractDictionary[ str, str ]:
    is_void = __.LocationSpecies.Void is inode.species
    headers = { }
    if __.FileUpdateOptions.Absence & options:
        # TODO? Check if location species is Void instead.
        headers[ 'If-None-Match' ] = '*'
    if __.FileUpdateOptions.Append & options and not is_void:
        size = inode.supplement.size
        if size:
            delta = len( content )
            start, end = size, size + delta - 1
            size_new = size + delta
            headers[ 'Content-Range' ] = f"bytes {start}-{end}/{size_new}"
    return __.DictionaryProxy( headers )


def _http_inode_from_response( response: _httpx.Response ) -> HttpInode:
    from email.utils import parsedate_to_datetime
    etag = response.headers.get( 'ETag' )
    mtime = response.headers.get( 'Last-Modified' )
    if mtime: mtime = parsedate_to_datetime( mtime )
    expiration = _expiration_from_response( response )
    size = response.headers.get( 'Content-Length' )
    return HttpInode(
        etag = etag, expiration = expiration, mtime = mtime, size = size )


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


def _translate_newlines(
    content: str, newline: __.Optional[ str ] = __.absent
) -> str:
    # TODO: Streaming version.
    if newline in ( __.absent, '', '\n' ): return content
    return newline.join( content.split( '\n' ) )


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


def _react_http_status_error( response_error, headers, error_to_raise ):
    from http import HTTPStatus
    match response_error.response.status_code:
        case HTTPStatus.PRECONDITION_FAILED:
            if 'If-None-Match' in headers:
                reason = (
                    "Upstream content already exists. "
                    "Cannot replace with absence option enabled." )
                raise error_to_raise( reason = reason )
        case HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE:
            if 'Content-Range' in headers:
                reason = "Server does not support append operation."
                raise error_to_raise( reason = reason )


def _result_from_headers(
    headers, content, error_to_raise
) -> ( int, str, str ):
    count = int( headers.get( 'Content-Length', len( content ) ) )
    content_type = headers.get( 'Content-Type', '' )
    mimetype, _, params = content_type.partition( ';' )
    if not mimetype:
        try:
            from magic import from_buffer
            mimetype = from_buffer( content, mime = True )
        except Exception as exc:
            raise error_to_raise( reason = str( exc ) ) from exc
    charset = None
    if mimetype.startswith( 'text/' ):
        if 'charset=' in params:
            charset = params.split( 'charset=' )[ -1 ].strip( )
        if not charset:
            try:
                from chardet import detect
                charset = detect( content )[ 'encoding' ]
            except Exception as exc:
                raise error_to_raise( reason = str( exc ) ) from exc
    return count, mimetype, charset
