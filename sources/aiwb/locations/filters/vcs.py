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


''' Filter which ignores VCS-related directories. '''


from . import __


_names = __.types.MappingProxyType( {
    'BitKeeper':    'bk',
    'Bazaar':       'bzr',
    'CVS':          'cvs',
    'Darcs':        'darcs',
    'Fossil':       'fossil',
    'Git':          'git',
    'Mercurial':    'hg',
    'RCS':          'rcs',
    'SCCS':         'sccs',
    'Subversion':   'svn',
} )
_aliases = frozenset( _names.values( ) )
_defaults = frozenset( ( 'git', 'hg', 'svn' ) )
_filter_name = '+vcs'


class Filter( __.Filter ):
    ''' Filters version control records and state.

        Arguments are colon-separated (':') in specifiers. With no arguments,
        default set of matchers will be applied. First argument is set of
        matchers to include. May be empty, '*', or a comma-separated list of
        matcher names. The wildcard ('*') implies all available matchers. Empty
        implies the default set of matchers. Second argument is set of matchers
        to exclude. May be a comma-separated list of matcher names. If not
        supplied, then nothing is excluded.
    '''
    # TODO: Immutable class and instance attributes.

    matchers: __.cabc.Sequence[ str ]

    def __init__( self, *arguments ):
        arguments_count = len( arguments )
        match arguments_count:
            case 2: includes, excludes = arguments
            case 1: includes, excludes = arguments[ 0 ], ''
            case 0: includes, excludes = '', ''
        match includes:
            case '*': includes = _aliases
            case '': includes = _defaults
            case _:
                includes = frozenset(
                    _validate_name( name )
                    for name in filter( None, includes.split( ',' ) ) )
        excludes = frozenset(
            _validate_name( name )
            for name in filter( None, excludes.split( ',' ) ) )
        matchers = tuple( includes - excludes )
        if not matchers:
            specifier = ':'.join( _filter_name, *arguments )
            raise __.FilterSpecifierValidityError(
                specifier = specifier,
                reason = "Evaluates to empty set of matchers." )
        self.matchers = matchers

    async def __call__( self, dirent: __.DirectoryEntry ) -> bool:
        path = __.Path( dirent.url.path )
        name = path.name
        isdir = dirent.is_directory( )
        isfile = dirent.is_file( )
        for matcher in self.matchers:
            match matcher:
                case 'bk':
                    if isdir and 'BitKeeper' == name: return True
                case 'bzr':
                    if isdir and '.bzr' == name: return True
                case 'cvs':
                    if isdir and 'CVS' == name: return True
                case 'darcs':
                    if isdir and '_darcs' == name: return True
                case 'fossil':
                    if isfile and '_FOSSIL_' == name: return True
                case 'git':
                    if isdir and _match_git_dir( path ): return True
                case 'hg':
                    if isdir and '.hg' == name: return True
                case 'rcs':
                    if isdir and 'RCS' == name: return True
                    # Do not ignore '*,v' files in case of explicit listing.
                case 'sccs':
                    if isdir and 'SCCS' == name: return True
                    # Do not ignore 's.*' files in case of explicit listing.
                case 'svn':
                    if isdir and '.svn' == name: return True
        return False

# TODO: Convert into docstring template and pass 'available' and 'default' via
#       'docstring_arguments' metaclass argument for 'ImmutableClass'.
Filter.__doc__ += (
    "\n\nAvailable Matchers: {available}\nDefault Matchers: {default}".format(
        available = ', '.join( _aliases ), default = ', '.join( _defaults ) ) )
__.filters_registry[ _filter_name ] = Filter


def _match_git_dir( path: __.Path ):
    from os import environ
    # TODO? Consider relative paths and symlinks.
    if 'GIT_DIR' in environ:
        git_dir = __.Path( environ[ 'GIT_DIR' ] )
        if git_dir == path: return True
    if '.git' == path.name: return True # noqa: SIM103
    return False


def _validate_name( name ) -> str:
    if name in _names: return _names[ name ]
    if name in _aliases: return name
    raise __.FilterArgumentSupportError( _filter_name, name )
