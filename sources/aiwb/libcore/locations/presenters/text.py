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


''' Location access adapter with aiofiles and pathlib. '''


from __future__ import annotations

from . import __


_module_name = __name__.replace( f"{__package__}.", '' )
_entity_name = f"location content presenter '{_module_name}'"


@__.standard_dataclass
class FilePresenter( __.FilePresenter ):
    ''' Presenter with standard operations on text files. '''

    charset: __.a.Nullable[ str ] = None
    charset_errors: str = 'strict'
    newline: __.a.Nullable[ str ] = None

    async def acquire_content( self ) -> str:
        return ( await self.acquire_content_result( ) ).content

    async def acquire_content_result(
        self, *,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
    ) -> __.AcquireContentTextResult:
        Error = __.partial_function(
            __.LocationAcquireContentFailure, url = self.accessor.as_url( ) )
        attributes |= __.InodeAttributes.Mimetype
        if '#DETECT#' == self.charset:
            attributes |= __.InodeAttributes.Charset
            charset = None
        else: charset = self.charset
        bytes_result = await self.accessor.acquire_content_result(
            attributes = attributes )
        mimetype = bytes_result.inode.mimetype
        if not mimetype.startswith( 'text/' ):
            reason = f"File content is not text. MIME Type: {mimetype!r}"
            raise Error( reason = reason )
        charset = charset or bytes_result.inode.charset
        if not charset:
            from locale import getpreferredencoding
            charset = getpreferredencoding( )
        try:
            content = bytes_result.content.decode(
                charset, errors = self.charset_errors )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        try: content_nl = self._normalize_newlines( content )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        inode = bytes_result.inode.with_attributes( charset = charset )
        return __.AcquireContentTextResult(
            content = content_nl, inode = inode )

    async def update_content(
        self,
        content: str,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
    ) -> __.Inode:
        Error = __.partial_function(
            __.LocationUpdateContentFailure, url = self.accessor.as_url( ) )
        content_nl = self._nativize_newlines( content )
        # Charset detection is meaningless for output.
        if '#DETECT#' == self.charset: charset = None
        else: charset = self.charset
        if not charset:
            from locale import getpreferredencoding
            charset = getpreferredencoding( )
        try:
            content_bytes = content_nl.encode(
                charset, errors = self.charset_errors )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        inode = await self.accessor.update_content(
            content_bytes, attributes = attributes, options = options )
        return inode.with_attributes( charset = charset )

    # TODO: Streaming codecs for reduced memory footprint.
    #       Not zero-copy, but can use constant-sized memory window.
    #       For charset encoding/decoding and newlines
    #       nativization/normalization.

    def _nativize_newlines( self, content: str ) -> str:
        match self.newline:
            case '' | '\n': return content
            case None:
                from os import linesep
                newline = linesep
            case '\r' | '\r\n': newline = self.newline
            # TODO: Error on invalid case.
        return newline.join( content.split( '\n' ) )

    def _normalize_newlines( self, content: str ) -> str:
        match self.newline:
            case '': return content
            case None | '\n':
                return content.replace( '\r\n', '\n' ).replace( '\r', '\n' )
            case '\r':
                return content.replace( '\r\n', '\r' ).replace( '\n', '\r' )
            case '\r\n':
                return (
                    content.replace( '\r\n', '\r' ).replace( '\n', '\r' )
                    .replace( '\r', '\r\n' ) )
            # TODO: Error on invalid case.


async def register_defaults( ):
    for mimetype in ( 'text/*', ):
        if mimetype in __.file_presenters_registry: continue
        __.file_presenters_registry[ mimetype ] = FilePresenter
