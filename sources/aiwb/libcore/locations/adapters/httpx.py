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
        Error = __.partial_function(
            __.LocationCheckAccessFailure, url = self.url )
        try:
            inode = await self._inspect_permissions(
                pursue_indirection = pursue_indirection )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        if __.Permissions.Abstain == permissions: return True
        return permissions == permissions & inode.permissions

    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        from http import HTTPStatus
        async with _httpx.AsyncClient(
            follow_redirects = pursue_indirection
        ) as client: response = await client.head( self.implement )
        return HTTPStatus.OK == response.status_code

    async def examine(
        self,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        pursue_indirection: bool = True,
    ) -> __.Inode:
        inode = await self._examine(
            attributes = attributes,
            pursue_indirection = pursue_indirection )
        if __.LocationSpecies.Void is inode.species:
            raise __.LocationExamineFailure(
                self.url, reason = "Location does not exist." )
        return inode

    def expose_implement( self ) -> __.AccessImplement:
        return __.a.cast( __.AccessImplement, self.implement )

    async def _examine(
        self,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        pursue_indirection: bool = True,
    ) -> __.Inode:
        Error = __.partial_function(
            __.LocationExamineFailure, url = self.url )
        try:
            inode = await self._inspect_permissions(
                pursue_indirection = pursue_indirection )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        return __.honor_inode_attributes(
            inode = inode, attributes = attributes, error_to_raise = Error )

    async def _inspect_permissions(
        self, pursue_indirection: bool = True
    ) -> __.Inode:
        from http import HTTPStatus
        inode_absent = __.Inode(
            permissions = __.Permissions.Abstain,
            species = __.LocationSpecies.Void,
            supplement = { } )
        async with _httpx.AsyncClient(
            follow_redirects = pursue_indirection
        ) as client:
            response_h = await client.head( self.implement )
            if HTTPStatus.NOT_FOUND == response_h.status_code:
                return inode_absent
            else: response_h.raise_for_status( )
            response_o = await client.options( self.implement )
        species = __.LocationSpecies.File
        if HTTPStatus.OK != response_o.status_code:
            return __.Inode(
                permissions = __.Permissions.Retrieve,
                species = species,
                supplement = response_h.headers )
        methods = frozenset( map(
            str.upper, response_o.headers.get( 'Allow', '' ).split( ', ' ) ) )
        permissions = _methods_to_permissions( methods )
        return __.Inode(
            permissions = permissions,
            species = species,
            supplement = response_h.headers )


class GeneralAdapter( _Common, __.GeneralAdapter ):
    ''' General location access adapter with httpx. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def from_url( selfclass, url: __.PossibleUrl ) -> __.a.Self:
        return selfclass( url = __.Url.from_url( url ) )

    def as_directory( self ) -> __.DirectoryAdapter:
        Error = __.partial_function(
            __.LocationAccessorDerivationFailure,
            entity_name = _entity_name, url = self.url )
        reason = "No derivative available for directory."
        raise Error( reason = reason )

    def as_file( self ) -> __.FileAdapter:
        return FileAdapter( url = self.url )

    async def as_specific(
        self,
        force: bool = False,
        pursue_indirection: bool = True,
        species: __.Optional[ __.LocationSpecies ] = __.absent,
    ) -> __.SpecificAdapter:
        Error = __.partial_function(
            __.LocationAccessorDerivationFailure,
            entity_name = _entity_name, url = self.url )
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


class FileAdapter( _Common, __.FileAdapter ):
    ''' File access adapter with httpx. '''
    # TODO: Immutable class and object attributes.

    async def acquire_content( self ) -> bytes:
        return ( await self.acquire_content_result( ) ).content

    async def acquire_content_result(
        self, attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
    ) -> __.AcquireContentBytesResult:
        Error = __.partial_function(
            __.LocationAcquireContentFailure, url = self.url )
        async with _httpx.AsyncClient( ) as client:
            response = await client.get( self.implement )
        try: response.raise_for_status( )
        except _httpx.HTTPStatusError as exc:
            raise Error( reason = str( exc ) ) from exc
        inode_h = _inode_from_headers(
            headers = response.headers,
            permissions = __.Permissions.Retrieve, # at least
            species = __.LocationSpecies.File )
        inode = __.honor_inode_attributes(
            inode = inode_h,
            attributes = attributes,
            error_to_raise = Error,
            content = response.content )
        return __.AcquireContentBytesResult(
            content = response.content, inode = inode )

    async def update_content(
        self,
        content: bytes,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
    ) -> __.Inode:
        Error = __.partial_function(
            __.LocationUpdateContentFailure, url = self.url )
        try: inode_ = await self._examine( )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        headers = _headers_from_file_update_options( options, inode_, content )
        async with _httpx.AsyncClient( ) as client:
            response = await client.put(
                self.implement, content, headers = headers )
        try: response.raise_for_status( )
        except _httpx.HTTPStatusError as exc:
            _react_http_status_error( exc, headers, Error )
            raise Error( reason = str( exc ) ) from exc
        inode_h = _inode_from_headers(
            headers = response.headers,
            permissions = inode_.permissions,
            species = inode_.species )
        return __.honor_inode_attributes(
            inode = inode_h,
            attributes = attributes,
            error_to_raise = Error,
            content = content )


async def register_defaults( ):
    for scheme in ( 'http', 'https' ):
        if scheme in __.adapters_registry: continue
        __.adapters_registry[ scheme ] = GeneralAdapter


def _expiration_from_headers(
    headers: __.AbstractDictionary[ str, str ]
) -> __.a.Nullable[ __.DateTime ]:
    from email.utils import parsedate_to_datetime
    cache_control = headers.get( 'Cache-Control' )
    expires = headers.get( 'Expires' )
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
        size = inode.bytes_count
        if size:
            delta = len( content )
            start, end = size, size + delta - 1
            size_new = size + delta
            headers[ 'Content-Range' ] = f"bytes {start}-{end}/{size_new}"
    return __.DictionaryProxy( headers )


def _inode_from_headers(
    headers: __.AbstractDictionary[ str, str ],
    permissions: __.Permissions,
    species: __.LocationSpecies,
) -> __.Inode:
    from email.utils import parsedate_to_datetime
    bytes_count = headers.get( 'Content-Length' )
    if bytes_count: bytes_count = int( bytes_count )
    content_id = None
    if ( etag := headers.get( 'ETag' ) ): content_id = f"etag:{etag}"
    content_type = headers.get( 'Content-Type', '' )
    mimetype, _, params = content_type.partition( ';' )
    charset = None
    if mimetype.startswith( 'text/' ) and 'charset=' in params:
        charset = params.split( 'charset=' )[ -1 ].strip( )
    mimetype = mimetype or None
    mtime = headers.get( 'Last-Modified' )
    if mtime: mtime = parsedate_to_datetime( mtime )
    etime = _expiration_from_headers( headers )
    supplement = dict( headers )
    return __.Inode(
        permissions = permissions, species = species,
        supplement = supplement,
        bytes_count = bytes_count,
        content_id = content_id,
        mimetype = mimetype, charset = charset,
        mtime = mtime, etime = etime )


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
