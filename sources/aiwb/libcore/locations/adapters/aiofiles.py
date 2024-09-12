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


_module_name = __name__.replace( f"{__package__}.", '' )
_entity_name = f"location access adapter '{_module_name}'"


_Permissions_CUD = (
    __.Permissions.Create | __.Permissions.Update | __.Permissions.Delete )


__.AccessImplement.register( __.Path )


class _Common:
    # TODO: Immutable class and object attributes.

    implement: __.Path
    url: __.Url

    @classmethod
    def is_cache_manager( selfclass ) -> bool: return False

    def __init__( self, url: __.Url ):
        if url.scheme not in ( '', 'file' ):
            raise __.UrlSchemeAssertionError(
                entity_name = _entity_name, url = url )
        for part_name in ( 'fragment', 'netloc', 'params', 'query' ):
            if getattr( url, part_name, '' ):
                raise __.UrlPartAssertionError(
                    entity_name = _entity_name,
                    part_name = part_name,
                    url = url )
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
        mode = F_OK
        if __.Permissions.Retrieve & permissions: mode |= R_OK
        if _Permissions_CUD & permissions: mode |= W_OK
        if __.Permissions.Execute & permissions: mode |= X_OK
        try:
            from aiofiles.os import access
            return await access(
                self.implement, mode, follow_symlinks = pursue_indirection )
        except Exception as exc:
            raise __.LocationCheckAccessFailure(
                url = self.url, reason = str( exc ) ) from exc

    async def check_existence(
        self, pursue_indirection: bool = True
    ) -> bool:
        try:
            from aiofiles.os import path
            return await path.exists( self.implement )
        except Exception as exc:
            raise __.LocationCheckExistenceFailure(
                url = self.url, reason = str( exc ) ) from exc

    async def examine( self, pursue_indirection: bool = True ) -> __.Inode:
        from os.path import realpath
        try:
            from aiofiles.os import stat
            # TODO? Resolve path async.
            #       aiofiles does not support realpath
            location = realpath( self.implement, strict = True )
            inode = await stat( location, follow_symlinks = False )
        except Exception as exc:
            raise __.LocationExamineFailure(
                url = self.url, reason = str( exc ) ) from exc
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

    async def as_specific(
        self,
        species: __.Optional[ __.LocationSpecies ] = __.absent,
    ) -> __.SpecificAdapter:
        exists = await self.check_existence( pursue_indirection = True )
        if exists:
            species_ = (
                ( await self.examine( pursue_indirection = True ) ).species )
            if __.absent is not species and species is not species_:
                reason = (
                    f"Requested species, '{species}', "
                    f"does not match actual species, '{species_}'." )
                raise __.LocationAdapterDerivationFailure(
                    url = self.url, reason = reason )
            species = species_
        match species:
            case __.LocationSpecies.Directory:
                return DirectoryAdapter( url = self.url )
            case __.LocationSpecies.File:
                return FileAdapter( url = self.url )
            case _:
                reason = (
                    f"No derivative available for species {species.value!r}." )
                raise __.LocationAdapterDerivationFailure(
                    url = self.url, reason = reason )

    async def is_directory( self, pursue_indirection: bool = True ) -> bool:
        from aiofiles.os import path
        try:
            if not pursue_indirection and await path.islink( self.implement ):
                return False
            return await path.isdir( self.implement )
        except Exception as exc:
            raise __.LocationIsDirectoryFailure(
                url = self.url, reason = str( exc ) ) from exc

    async def is_file( self, pursue_indirection: bool = True ) -> bool:
        from aiofiles.os import path
        try:
            if not pursue_indirection and await path.islink( self.implement ):
                return False
            return await path.isfile( self.implement )
        except Exception as exc:
            raise __.LocationIsFileFailure(
                url = self.url, reason = str( exc ) ) from exc

    async def is_indirection( self ) -> bool:
        from aiofiles.os import path
        try: return await path.islink( self.implement )
        except Exception as exc:
            raise __.LocationIsIndirectionFailure(
                url = self.url, reason = str( exc ) ) from exc

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
        # TODO: Handle scandir exceptions.
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
                        .survey_entries(
                            filters = filters, recurse = recurse ) )
                results.append( dirent_ )
            if recurse:
                results.extend( __.chain.from_iterable(
                    await __.gather_async( *scanners ) ) )
        return results

    async def create_entry(
        self,
        name: __.RelativeLocation,
        species: __.LocationSpecies,
        permissions: __.Permissions,
        exist_ok: bool = True,
        parents: __.CreateParentsArgument = True,
    ) -> __.DirectoryEntry:
        try: accessor = self.produce_entry_accessor( name )
        except Exception as exc:
            raise __.LocationCreateFailure(
                url = self.url, reason = str( exc ) ) from exc
        url = accessor.as_url( )
        Error = __.partial_function( __.LocationCreateFailure, url = url )
        exists = await accessor.check_existence( pursue_indirection = False )
        if exists:
            if not exist_ok: raise Error( reason = "Entry already exists." )
            inode = await accessor.examine( puruse_indirection = False )
            if species is not inode.species:
                reason = (
                    f"Entry already exists as {inode.species.value}. "
                    f"Creation request is for {species.value}." )
                raise Error( reason = reason )
            # TODO? Compare permissions: chmod or error
            return __.DirectoryEntry( inode = inode, url = url )
        return await self._create_entry(
            accessor, species, permissions, parents )

    async def delete_entry(
        self,
        name: __.RelativeLocation,
        absent_ok: bool = True,
        recurse: __.RecurseArgument = True,
    ):
        # TODO: Implement.
        pass

    async def produce_entry_accessor(
        self, name: __.RelativeLocation
    ) -> __.GeneralAccessor:
        if isinstance( name, __.PossiblePath ): name = ( name, )
        if isinstance( name, __.AbstractIterable[ __.PossiblePath ] ):
            return __.adapter_from_url(
                self.url.with_path(
                    __.Path( self.url.path ).joinpath( *name ) ) )
        raise __.RelativeLocationClassValidityError( type( name ) )

    async def _create_entry(
        self,
        accessor: __.GeneralAdapter,
        species: __.LocationSpecies,
        permissions: __.Permissions,
        parents: bool,
    ) -> __.DirectoryEntry:
        from aiofiles.os import makedirs, mkdir
        url = accessor.as_url( )
        path = __.Path( url.path )
        Error = __.partial_function( __.LocationCreateFailure, url = url )
        mode = 0o660 # TODO: translate from permissions
        if parents:
            try: await makedirs( path.parent, exist_ok = True )
            except Exception as exc:
                raise Error( reason = str( exc ) ) from exc
        # Note: aiofiles does not wrap os.mknod.
        match species:
            case __.LocationSpecies.Directory:
                try: await mkdir( path, mode = 0o770 ) # TODO: correct mode
                except Exception as exc:
                    raise Error( reason = str( exc ) ) from exc
            case __.LocationSpecies.File:
                try: path.touch( mode = mode )
                except Exception as exc:
                    raise Error( reason = str( exc ) ) from exc
            case _:
                reason = f"Creation of {species.value} is not implemented."
                raise Error( reason = reason )
        return await accessor.examine( pursue_indirection = False )


class FileAdapter( _Common, __.FileAdapter ):
    ''' File access adapter with aiofiles and pathlib. '''
    # TODO: Immutable class and object attributes.

    async def acquire_content(
        self,
        charset: __.Optional[ str ] = __.absent,
        charset_errors: __.Optional[ str ] = __.absent,
        newline: __.Optional[ str ] = __.absent,
    ) -> __.AcquireContentTextResult:
        Error = __.partial_function(
            __.LocationAcquireContentFailure, url = self.url )
        bytes_result = await self.acquire_content_bytes( )
        mimetype = bytes_result.mimetype
        try:
            content = __.decode_content(
                bytes_result.content,
                charset = charset,
                charset_errors = charset_errors )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        try: content_nl = __.normalize_newlines( content, newline = newline )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        return __.AcquireContentTextResult(
            content = content_nl, mimetype = mimetype, charset = charset )

    async def acquire_content_bytes( self ) -> __.AcquireContentBytesResult:
        Error = __.partial_function(
            __.LocationAcquireContentFailure, url = self.url )
        try:
            from aiofiles import open as open_
            async with open_( self.implement, 'rb' ) as stream:
                content = await stream.read( )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        try:
            from magic import from_buffer
            mimetype = from_buffer( content, mime = True )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        return __.AcquireContentBytesResult(
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
        content_nl = _nativize_newlines( content, newline = newline )
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
        flags = _flags_from_file_update_options( options )
        try:
            from aiofiles import open as open_
            async with open_( self.implement, f"{flags}b" ) as stream:
                count = await stream.write( content )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        try:
            from magic import from_buffer
            mimetype = from_buffer( content, mime = True )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        return __.UpdateContentResult(
            count = count, mimetype = mimetype, charset = None )


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
            return '#NOTHING#'
        case _:
            raise __.LocationSpeciesSupportError(
                entity_name = _entity_name, species = species )


def _flags_from_file_update_options( options: __.FileUpdateOptions ) -> str:
    flags = [ ]
    if __.FileUpdateOptions.Append & options: flags.append( 'a' )
    else: flags.append( 'w' )
    if __.FileUpdateOptions.Absence & options: flags.append( 'x' )
    return ''.join( flags )


def _nativize_newlines(
    content: str, newline: __.Optional[ str ] = __.absent
) -> str:
    # TODO: Streaming version.
    if newline in ( '', '\n' ): return content
    if __.absent is newline:
        from os import linesep
        newline = linesep
    return newline.join( content.split( '\n' ) )


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
    # TODO: import constants from stdlib 'stat' module
    inode_type = inode.st_mode & 0o170000
    match inode_type:
        case 0o010000: return __.LocationSpecies.Pipe
        case 0o020000: return __.LocationSpecies.Stream
        case 0o040000: return __.LocationSpecies.Directory
        case 0o060000: return __.LocationSpecies.Blocks
        case 0o100000: return __.LocationSpecies.File
        case 0o120000: return __.LocationSpecies.Symlink
        case 0o140000: return __.LocationSpecies.Socket
        case _:
            raise __.SupportError(
                f"Inode type {inode_type!r} not supported by {_entity_name}." )
