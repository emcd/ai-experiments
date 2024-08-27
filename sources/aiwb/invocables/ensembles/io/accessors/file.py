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


''' Implementation of filesystem I/O operations. '''


from . import __


@__.standard_dataclass
class Accessor( __.Accessor ):

    async def acquire_contents(
        self, context: __.Context, arguments: __.AcquireContentsArguments
    ) -> __.AbstractDictionary:
        # TODO: Implement.
        raise NotImplementedError

    async def survey_directory(
        self, context: __.Context, arguments: __.SurveyDirectoryArguments
    ) -> __.AbstractDictionary:
        return await survey_directory(
            location = arguments.location.produce_accessor( ),
            context = context,
            arguments = arguments )

    async def update_contents(
        self, context: __.Context, arguments: __.UpdateContentsArguments
    ) -> __.AbstractDictionary:
        # TODO: Implement.
        raise NotImplementedError

__.accessors[ '' ] = Accessor
__.accessors[ 'file' ] = Accessor


async def survey_directory(
    location: __.PathLike,
    context: __.Context,
    arguments: __.SurveyDirectoryArguments,
) -> __.AbstractDictionary:
    ''' Lists directory at filesystem path. '''
    from itertools import chain
    # TODO? Python 3.12: aiopath.AsyncPath.scandir or anyio.Path.walk
    from aiofiles.os import scandir
    from gitignorefile import Cache as GitIgnorer
    from magic import from_file
    filters = frozenset( arguments.filters )
    # TODO: Build dictionary of ignorers from filters set.
    ignorers = { 'gitignore': GitIgnorer( ) }
    scanners = [ ]
    results = [ ]
    with await scandir( location ) as dirents:
        for dirent in dirents:
            if filters and _decide_filter_dirent( dirent, filters, ignorers ):
                continue
            if dirent.is_dir( follow_symlinks = False ):
                if arguments.recursive:
                    scanners.append(
                        survey_directory( dirent.path, context, arguments ) )
                if not arguments.return_directories: continue
                mimetype = 'inode/directory'
            elif dirent.is_file( follow_symlinks = False ):
                #inode = dirent.stat( follow_symlinks = False )
                #if arguments.file_size_maximum < inode.st_size: continue
                mimetype = from_file( dirent.path, mime = True )
            elif dirent.is_symlink( ):
                if not arguments.return_symlinks: continue
                mimetype = 'inode/symlink'
            elif arguments.return_special_entities:
                mimetype = from_file( dirent.path, mime = True )
            else: continue
            results.append( dict(
                location = dirent.path, mimetype = mimetype ) )
        if arguments.recursive:
            results.extend( chain.from_iterable(
                await __.gather_async( *scanners ) ) )
    return results


_vcs_control_directories = frozenset( (
    'BitKeeper', 'CVS', 'RCS', 'SCCS',
    '_darcs', '.bzr', '.git', '.hg', '.svn' ) )
def _decide_filter_dirent(
    dirent: __.DirEntry,
    filters: __.AbstractCollection[ str ],
    ignorers: __.AbstractDictionary[ str, __.a.Any ],
) -> bool:
    if dirent.is_dir( ):
        if 'vcs' in filters and dirent.name in _vcs_control_directories:
            return True
    if 'gitignore' in filters and ignorers[ 'gitignore' ]( dirent.path ):
        return True
    return False
