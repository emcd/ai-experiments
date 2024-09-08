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

from os import stat_result as _StatResult

from . import __


_Permissions_CUD = (
    __.Permissions.Create | __.Permissions.Update | __.Permissions.Delete )


__.AccessImplement.register( __.Path )


class _Common:
    # TODO: Immutable class and object attributes.

    implement: __.Path
    url: __.Url

    def __init__( self, url: __.Url ):
        # TODO: Assert file or empty scheme.
        if url.netloc or url.params or url.query or url.fragment:
            # TODO: Raise more specific exception.
            raise NotImplementedError(
                f"Only scheme and path supported in file URLs. URL: {url}" )
        self.implement = __.Path( url.path )
        self.url = url
        super( ).__init__( )

    def as_url( self ) -> __.Url: return self.url

    async def check_access(
        self,
        permissions: __.Permissions,
        pursue_indirection: bool = True,
    ) -> bool:
        from os import F_OK, R_OK, W_OK, X_OK
        from aiofiles.os import access
        mode = F_OK
        if __.Permissions.Retrieve & permissions: mode |= R_OK
        if _Permissions_CUD & permissions: mode |= W_OK
        if __.Permissions.Execute & permissions: mode |= X_OK
        return await access(
            self.implement, mode, follow_symlinks = pursue_indirection )

    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        from aiofiles.os import path
        # TODO? Resolve symlinks async.
        location = (
            self.implement.resolve( ) if pursue_indirection
            else self.implement )
        return await path.exists( location )

    async def examine( self, pursue_indirection: bool = True ) -> __.Inode:
        from aiofiles.os import stat
        # TODO? Resolve symlinks async.
        location = (
            self.implement.resolve( ) if pursue_indirection
            else self.implement )
        inode = await stat( location )
        permissions = _permissions_from_stat( inode )
        species = _species_from_stat( inode )
        mimetype = _derive_mimetype( location, species )
        return __.Inode(
            mimetype = mimetype,
            permissions = permissions,
            species = species,
            supplement = inode )

    def expose_implement( self ) -> __.AccessImplement:
        # Cast because we do not have a common protocol.
        return __.a.cast( __.AccessImplement, self.implement )


class GeneralAdapter( _Common, __.GeneralAdapter ):
    ''' General location access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.

    @classmethod
    def from_url( selfclass, url: __.PossibleUrl ) -> __.a.Self:
        return selfclass( url = __.Url.from_url( url ) )

    async def as_specific( self ) -> __.SpecificAdapter:
        # TODO: match await self.adapter.stat( ).species
        if await self.is_directory( ):
            return DirectoryAdapter( url = self.url )
        elif await self.is_file( ):
            return FileAdapter( url = self.url )
        # TODO: assert selection of adapter species
        raise AssertionError( "Could not match location species." )

    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        from aiofiles.os import path
        if not pursue_indirection and await path.islink( self.implement ):
            return False
        return await path.isdir( self.implement )

    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        from aiofiles.os import path
        if not pursue_indirection and await path.islink( self.implement ):
            return False
        return await path.isfile( self.implement )

    async def is_indirection( self ) -> bool:
        from aiofiles.os import path
        return await path.islink( self.implement )

# TODO? Perform registrations as part of module preparation function.
__.adapters_registry[ '' ] = GeneralAdapter
__.adapters_registry[ 'file' ] = GeneralAdapter


class DirectoryAdapter( _Common, __.DirectoryAdapter ):
    ''' Directory access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.

    async def survey_entries(
        self,
        filters: __.Optional[
            __.AbstractIterable[ __.PossibleFilter ]
        ] = __.absent,
        recurse: bool = True
    ) -> __.AbstractSequence[ __.DirectoryEntry ]:
        from aiofiles.os import scandir
        if filters: filters = __.filters_from_specifiers( filters )
        scanners = [ ]
        results = [ ]
        with await scandir( self.implement ) as dirents:
            # TODO: Process dirents concurrently.
            for dirent in dirents:
                url = __.Url.from_url( dirent.path )
                inode = (
                    await GeneralAdapter( url = url )
                    .examine( pursue_indirection = False ) )
                dirent_ = __.DirectoryEntry( inode = inode, url = url )
                if filters and await __.apply_filters( dirent_, filters ):
                    continue
                if recurse and inode.is_directory( ):
                    scanners.append(
                        DirectoryAdapter( url = url )
                        .survey( filters = filters, recurse = recurse ) )
                results.append( dirent_ )
            if recurse:
                results.extend( __.chain.from_iterable(
                    await __.gather_async( *scanners ) ) )
        return results


class FileAdapter( _Common, __.FileAdapter ):
    ''' File access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.

    async def acquire_content(
        self,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.ContentTextResult:
        from aiofiles import open as open_
        # TODO: Exception handling.
        async with open_( self.implement, 'rb' ) as stream:
            content_bytes = await stream.read( )
        from magic import from_buffer
        mimetype = from_buffer( content_bytes, mime = True )
        match charset:
            case __.absent:
                from locale import getpreferredencoding
                charset = getpreferredencoding( )
            case '#DETECT#':
                from chardet import detect
                charset = detect( content_bytes )[ 'encoding' ]
        if __.absent is charset_errors: charset_errors = 'strict'
        if __.absent is newline: newline = None
        # TODO: Newline translation.
        content = content_bytes.decode( charset, errors = charset_errors )
        return __.ContentTextResult(
            content = content, mimetype = mimetype, charset = charset )
#        async with open_( # TODO: Exception handling.
#            self.implement,
#            encoding = codec_name,
#            errors = codec_errors,
#            newline = newline,
#        ) as stream: return await stream.read( )

    async def acquire_content_bytes( self ) -> __.ContentBytesResult:
        from aiofiles import open as open_
        async with open_( self.implement, 'rb' ) as stream:
            content = await stream.read( )
        from magic import from_buffer
        mimetype = from_buffer( content, mime = True )
        return __.ContentBytesResult( content = content, mimetype = mimetype )


def _derive_mimetype(
    implement: __.AccessImplement,
    species: __.LocationSpecies,
) -> str:
    from magic import from_file
    match species:
        case __.LocationSpecies.Blocks:
            # TODO? Sniff first 4K and use magic.from_buffer on that.
            #       Or, use 'blkinfo' package or similar.
            return 'inode/blockdevice'
        case __.LocationSpecies.Directory:
            return 'inode/directory'
        case __.LocationSpecies.File:
            try: return from_file( str( implement ), mime = True )
            except Exception: return 'application/octet-stream'
        case __.LocationSpecies.Pipe:
            return 'inode/fifo'
        case __.LocationSpecies.Socket:
            return 'inode/socket'
        case __.LocationSpecies.Stream:
            return 'inode/chardevice'
        case __.LocationSpecies.Symlink:
            return 'inode/symlink'
        case __.LocationSpecies.Void:
            return 'NOTHING'
    # TODO: assert valid species
    return 'application/octet-stream'


def _permissions_from_stat( inode: _StatResult ) -> __.Permissions:
    import os
    from os import R_OK, W_OK, X_OK
    gid = os.getgid( ) if hasattr( os, 'getgid' ) else None
    uid = os.getuid( ) if hasattr( os, 'getuid' ) else None
    permissions = __.Permissions.Abstain
    mode_bitshifts = frozenset( (
        0,
        3 * int( gid == inode.st_gid ),
        6 * int( uid == inode.st_uid ) ) )
    for bitshift in mode_bitshifts:
        if ( R_OK << bitshift ) & inode.st_mode:
            permissions |= __.Permissions.Retrieve
        if ( W_OK << bitshift ) & inode.st_mode:
            permissions |= _Permissions_CUD
        if ( X_OK << bitshift ) & inode.st_mode:
            permissions |= __.Permissions.Execute
    return permissions


def _species_from_stat( inode: _StatResult ) -> __.LocationSpecies:
    match inode.st_mode & 0o170000:
        case 0o010000: return __.LocationSpecies.Pipe
        case 0o020000: return __.LocationSpecies.Stream
        case 0o040000: return __.LocationSpecies.Directory
        case 0o060000: return __.LocationSpecies.Blocks
        case 0o100000: return __.LocationSpecies.File
        case 0o120000: return __.LocationSpecies.Symlink
        case 0o140000: return __.LocationSpecies.Socket
    # TODO: assert valid species
    return __.LocationSpecies.Void
