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


from os import stat_result as _StatResult

from . import __


_module_name = __name__.replace( f"{__package__}.", '' )
_entity_name = f"location access adapter '{_module_name}'"


__.AccessImplement.register( __.Path )


class _Common( __.AdapterBase ):
    # TODO: Immutable instance attributes.

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
        if __.Permissions_CUD & permissions: mode |= W_OK
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

    async def examine(
        self,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        pursue_indirection: bool = True,
    ) -> __.Inode:
        Error = __.funct.partial(
            __.LocationExamineFailure, url = self.url )
        try:
            from os.path import realpath
            # TODO? Resolve path async.
            #       aiofiles does not support realpath
            location = realpath( self.implement, strict = True )
            from aiofiles.os import stat
            stat = await stat( location, follow_symlinks = False )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        inode_s = _inode_from_stat( stat )
        if (    __.LocationSpecies.File is inode_s.species
                and __.InodeAttributes.Mimetype & attributes
        ):
            from magic import from_file
            mimetype = from_file( str( self.implement ), mime = True )
            inode = inode_s.with_attributes( mimetype = mimetype )
        # TODO? Probe block devices with 'blkid' or similar.
        else: inode = inode_s
        return __.honor_inode_attributes(
            inode = inode, attributes = attributes, error_to_raise = Error )

    def expose_implement( self ) -> __.AccessImplement:
        # Cast because we do not have a common protocol.
        return __.typx.cast( __.AccessImplement, self.implement )


class GeneralAdapter( _Common, __.GeneralAdapter ):
    ''' General location access adapter with aiofiles and pathlib. '''
    # TODO: Immutable instance attributes.

    @classmethod
    def from_url( selfclass, url: __.PossibleUrl ) -> __.typx.Self:
        return selfclass( url = __.Url.from_url( url ) )

    def as_directory( self ) -> '__.DirectoryAdapter':
        return DirectoryAdapter( url = self.url )

    def as_file( self ) -> '__.FileAdapter':
        return FileAdapter( url = self.url )

    async def as_specific(
        self,
        force: bool = False,
        pursue_indirection: bool = True,
        species: __.Absential[ __.LocationSpecies ] = __.absent,
    ) -> __.SpecificAdapter:
        Error = __.funct.partial(
            __.LocationAccessorDerivationFailure,
            entity_name = _entity_name, url = self.url )
        try:
            species_ = species if force else await self.discover_species(
                pursue_indirection = pursue_indirection, species = species )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        match species_:
            case __.LocationSpecies.Directory:
                return DirectoryAdapter( url = self.url )
            case __.LocationSpecies.File:
                return FileAdapter( url = self.url )
            case _:
                reason = (
                    "No derivative available for species "
                    f"{species_.value!r}." )
                raise Error( reason = reason )

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


class DirectoryAdapter( _Common, __.DirectoryAdapter ):
    ''' Directory access adapter with aiofiles and pathlib. '''
    # TODO: Immutable instance attributes.
    # TODO: Deletion safety.
    #       Refuse to delete /<dir>/<entity> if safe.
    #       Refuse to delete <dir>/<entity> if safe and at root.
    #       Refuse to delete certain device nodes if safe on Unix.
    #       Refuse to delete anything if safe and superuser.

    async def create_directory(
        self,
        name: __.PossibleRelativeLocator,
        permissions: __.Permissions | __.PermissionsTable,
        exist_ok: bool = True,
        parents: __.CreateParentsArgument = True,
    ) -> __.DirectoryAccessor:
        try: accessor = self.produce_entry_accessor( name )
        except Exception as exc:
            raise __.LocationCreateFailure(
                url = self.url, reason = str( exc ) ) from exc
        url = accessor.as_url( )
        Error = __.funct.partial( __.LocationCreateFailure, url = url )
        exists = await _probe_accessor_if_exists(
            accessor,
            species = __.LocationSpecies.Directory,
            permissions = permissions,
            error_to_raise = Error,
            exist_ok = exist_ok )
        if not exists:
            if parents:
                await _create_parent_directories(
                    url, permissions, error_to_raise = Error )
            mode = _access_mode_from_permissions( permissions )
            from aiofiles.os import mkdir
            try: await mkdir( url.path, mode = mode )
            except Exception as exc:
                raise Error( reason = str( exc ) ) from exc
        return await accessor.as_specific(
            species = __.LocationSpecies.Directory )

    async def create_file(
        self,
        name: __.PossibleRelativeLocator,
        permissions: __.Permissions | __.PermissionsTable,
        exist_ok: bool = True,
        parents: __.CreateParentsArgument = True,
    ) -> __.FileAccessor:
        try: accessor = self.produce_entry_accessor( name )
        except Exception as exc:
            raise __.LocationCreateFailure(
                url = self.url, reason = str( exc ) ) from exc
        url = accessor.as_url( )
        Error = __.funct.partial( __.LocationCreateFailure, url = url )
        exists = await _probe_accessor_if_exists(
            accessor,
            species = __.LocationSpecies.File,
            permissions = permissions,
            error_to_raise = Error,
            exist_ok = exist_ok )
        if not exists:
            if parents:
                await _create_parent_directories(
                    url, permissions, error_to_raise = Error )
            mode = _access_mode_from_permissions( permissions )
            # Note: aiofiles does not wrap os.mknod or pathlib.Path.touch.
            try: __.Path( url.path ).touch( mode = mode )
            except Exception as exc:
                raise Error( reason = str( exc ) ) from exc
        return await accessor.as_specific(
            species = __.LocationSpecies.File )

    # TODO: create_indirection

    async def delete_directory(
        self,
        name: __.PossibleRelativeLocator,
        absent_ok: bool = True,
        recurse: bool = True,
        safe: bool = True,
    ):
        # TODO: Implement.
        #       Refuse to delete $HOME or ~ if safe.
        pass

    async def delete_file(
        self,
        name: __.PossibleRelativeLocator,
        absent_ok: bool = True,
        safe: bool = True,
    ):
        # TODO: Implement.
        pass

    # TODO: delete_indirection

    async def produce_entry_accessor(
        self, name: __.PossibleRelativeLocator
    ) -> __.GeneralAccessor:
        if isinstance( name, __.PossiblePath ): name = ( name, )
        if isinstance( name, __.cabc.Iterable[ __.PossiblePath ] ):
            return __.adapter_from_url(
                self.url.with_path(
                    __.Path( self.url.path ).joinpath( *name ) ) )
        raise __.RelativeLocatorClassValidityError( type( name ) )

    async def survey_entries(
        self,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        filters: __.Absential[
            __.cabc.Iterable[ __.PossibleFilter ]
        ] = __.absent,
        recurse: bool = True
    ) -> __.cabc.Sequence[ __.DirectoryEntry ]:
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
                    .examine(
                        attributes = attributes,
                        pursue_indirection = False ) )
                dirent_ = __.DirectoryEntry( inode = inode, url = url )
                if filters and await __.apply_filters( dirent_, filters ):
                    continue
                if recurse and inode.is_directory( ):
                    scanners.append(
                        DirectoryAdapter( url = url )
                        .survey_entries(
                            attributes = attributes,
                            filters = filters,
                            recurse = recurse ) )
                results.append( dirent_ )
            if recurse:
                results.extend( __.chain.from_iterable(
                    await __.asyncf.gather_async( *scanners ) ) )
        return results


class FileAdapter( _Common, __.FileAdapter ):
    ''' File access adapter with aiofiles and pathlib. '''
    # TODO: Immutable instance attributes.

    async def acquire_content( self ) -> bytes:
        return ( await self.acquire_content_result( ) ).content

    async def acquire_content_result(
        self, attributes: __.InodeAttributes = __.InodeAttributes.Nothing
    ) -> __.AcquireContentBytesResult:
        Error = __.funct.partial(
            __.LocationAcquireContentFailure, url = self.url )
        try:
            from os import fstat
            from aiofiles import open as open_
            async with open_( self.implement, 'rb' ) as stream:
                content = await stream.read( )
                stat = fstat( stream.fileno( ) )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        inode_s = _inode_from_stat( stat )
        inode = __.honor_inode_attributes(
            inode = inode_s,
            attributes = attributes,
            error_to_raise = Error,
            content = content )
        return __.AcquireContentBytesResult( content = content, inode = inode )

    async def update_content(
        self,
        content: bytes,
        attributes: __.InodeAttributes = __.InodeAttributes.Nothing,
        options: __.FileUpdateOptions = __.FileUpdateOptions.Defaults,
    ) -> __.Inode:
        Error = __.funct.partial(
            __.LocationUpdateContentFailure, url = self.url )
        flags = _flags_from_file_update_options( options )
        await _create_parent_directories(
            self.url, __.Permissions_RCUD, error_to_raise = Error )
        try:
            from os import fstat
            from aiofiles import open as open_
            async with open_( self.implement, f"{flags}b" ) as stream:
                await stream.write( content )
                await stream.flush( ) # Cannot use bytes count in append mode.
                stat = fstat( stream.fileno( ) )
        except Exception as exc: raise Error( reason = str( exc ) ) from exc
        inode_s = _inode_from_stat( stat )
        return __.honor_inode_attributes(
            inode = inode_s,
            attributes = attributes,
            error_to_raise = Error,
            content = content )


async def register_defaults( ):
    for scheme in ( '', 'file' ):
        if scheme in __.adapters_registry: continue
        __.adapters_registry[ scheme ] = GeneralAdapter


def _access_mode_from_permissions(
    permissions: '__.Permisisons | __.PermissionsTable'
) -> int:
    from os import R_OK, W_OK, X_OK
    table = _tabulate_permissions( permissions )
    mode_bitshifts = set( )
    mode = 0
    for possessor, permissions_ in table.items( ):
        match possessor:
            case __.Possessor.Omnipopulation: mode_bitshifts.add( 0 )
            case __.Possessor.CurrentPopulation: mode_bitshifts.add( 3 )
            case __.Possessor.CurrentUser: mode_bitshifts.add( 6 )
        for bitshift in mode_bitshifts:
            if __.Permissions.Retrieve & permissions_:
                mode |= ( R_OK << bitshift )
            if __.Permissions_CUD & permissions_:
                mode |= ( W_OK << bitshift )
            if __.Permissions.Execute & permissions_:
                mode |= ( X_OK << bitshift )
    return mode


async def _create_parent_directories(
    url: __.Url,
    permissions: __.Permissions | __.PermissionsTable,
    error_to_raise: __.LocationOperateFailure,
):
    from aiofiles.os import makedirs
    path = __.Path( url.path )
    permissions_table = __.accret.Dictionary( {
        possessor: permissions_ | __.Permissions.Execute
        for possessor, permissions_
        in _tabulate_permissions( permissions ).items( ) } )
    mode = _access_mode_from_permissions( permissions_table )
    try: await makedirs( path.parent, mode = mode, exist_ok = True )
    except Exception as exc:
        raise error_to_raise( reason = str( exc ) ) from exc


def _derive_mimetype( species: __.LocationSpecies ) -> __.typx.Optional[ str ]:
    match species:
        case __.LocationSpecies.Blocks:     return 'inode/blockdevice'
        case __.LocationSpecies.Directory:  return 'inode/directory'
        case __.LocationSpecies.File:       return None
        case __.LocationSpecies.Pipe:       return 'inode/fifo'
        case __.LocationSpecies.Socket:     return 'inode/socket'
        case __.LocationSpecies.Stream:     return 'inode/chardevice'
        case __.LocationSpecies.Symlink:    return 'inode/symlink'
        case __.LocationSpecies.Void:       return None
    return None


def _flags_from_file_update_options( options: __.FileUpdateOptions ) -> str:
    flags = [ ]
    if __.FileUpdateOptions.Append & options: flags.append( 'a' )
    else: flags.append( 'w' )
    if __.FileUpdateOptions.Absence & options: flags.append( 'x' )
    return ''.join( flags )


def _inode_from_stat( stat: _StatResult ) -> __.Inode:
    permissions = _permissions_from_stat( stat )
    species = _species_from_stat( stat )
    supplement = stat
    bytes_count = stat.st_size
    content_id = None
    mimetype = _derive_mimetype( species )
    charset = None
    mtime = __.DateTime.fromtimestamp( stat.st_mtime, __.TimeZone.utc )
    etime = None
    return __.Inode(
        permissions = permissions, species = species,
        supplement = supplement,
        bytes_count = bytes_count,
        content_id = content_id,
        mimetype = mimetype, charset = charset,
        mtime = mtime, etime = etime )


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
            permissions |= __.Permissions_CUD
        if ( X_OK << bitshift ) & inode.st_mode:
            permissions |= __.Permissions.Execute
    return permissions


async def _probe_accessor_if_exists(
    accessor: __.GeneralAccessor,
    species: __.LocationSpecies,
    permissions: __.Permissions | __.PermissionsTable,
    error_to_raise: __.LocationOperateFailure,
    exist_ok = True,
) -> bool:
    exists = await accessor.check_existence( pursue_indirection = False )
    if exists:
        if not exist_ok:
            raise error_to_raise( reason = "Entry already exists." )
        inode = await accessor.examine( puruse_indirection = False )
        if species is not inode.species:
            reason = (
                f"Entry already exists as {inode.species.value}. "
                f"Creation request is for {species.value}." )
            raise error_to_raise( reason = reason )
        # TODO? Compare permissions: chmod or error
        return True
    return False


def _species_from_stat( stat: _StatResult ) -> __.LocationSpecies:
    from stat import (
        S_IFMT,
        S_ISBLK, S_ISCHR, S_ISDIR, S_ISFIFO, S_ISLNK, S_ISREG, S_ISSOCK
    )
    mode = stat.st_mode
    if S_ISREG( mode ):     return __.LocationSpecies.File
    if S_ISLNK( mode ):     return __.LocationSpecies.Symlink
    if S_ISDIR( mode ):     return __.LocationSpecies.Directory
    if S_ISBLK( mode ):     return __.LocationSpecies.Blocks
    if S_ISFIFO( mode ):    return __.LocationSpecies.Pipe
    if S_ISSOCK( mode ):    return __.LocationSpecies.Socket
    if S_ISCHR( mode ):     return __.LocationSpecies.Stream
    inode_type = mode & S_IFMT
    # TODO? Other entities: doors, etc....
    raise __.SupportError(
        f"Inode type {inode_type!r} not supported by {_entity_name}." )


def _tabulate_permissions(
    permissions: __.Permissions | __.PermissionsTable
) -> __.PermissionsTable:
    if isinstance( permissions, __.Permissions ):
        return __.accret.Dictionary( {
            __.Possessor.CurrentUser: permissions,
            __.Possessor.CurrentPopulation: permissions,
        } )
    if __.is_permissions_table( permissions ): return permissions
    raise __.PermissionsClassValidityError( type( permissions ) )
