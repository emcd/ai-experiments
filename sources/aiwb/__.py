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


''' Base functionality to support AI workbench. '''


from pathlib import Path

from aiofiles import open as open_async
from accretive.qaliases import AccretiveNamespace


package_distributor = 'emcd'


def prepare( ) -> AccretiveNamespace:
    ''' Initializes fundamental parts of application. '''
    from platformdirs import PlatformDirs
    distribution = discover_distribution_information( )
    directories = PlatformDirs(
        distribution.name, package_distributor, ensure_exists = True )
    configuration = _provide_configuration( distribution, directories )
    auxdata = AccretiveNamespace(
        configuration = configuration,
        directories = directories,
        distribution = distribution )
    _acquire_environment( auxdata )
    _prepare_scribes( auxdata )
    return auxdata


def discover_distribution_information( ) -> AccretiveNamespace:
    ''' Discovers information about our package distribution. '''
    from importlib.metadata import files, packages_distributions
    from tomli import load
    # https://github.com/pypa/packaging-problems/issues/609
    name = packages_distributions( ).get( __package__ )
    if None is name: # Development sources rather than distribution package.
        editable = True # Implies no use of importlib.resources.
        location = Path( __file__ ).parents[ 2 ].resolve( strict = True )
        with ( location / 'pyproject.toml' ).open( 'rb' ) as file:
            pyproject = load( file )
        name = pyproject[ 'project' ][ 'name' ]
    else:
        editable = False
        location = next(
            file for file in files( __package__ )
            if f"{__package__}/__init__.py" == str( file ) ).locate( ).parent
    return AccretiveNamespace(
        editable = editable, location = location, name = name )


def provide_cache_location( auxdata, *appendages ):
    ''' Provides cache location from configuration. '''
    spec = auxdata.configuration.get( 'locations', { } ).get( 'cache' )
    if not spec: base = auxdata.directories.user_cache_path
    else:
        base = Path( spec.format(
            user_cache = auxdata.directories.user_cache_dir,
            application_name = auxdata.distribution.name ) )
    if appendages: return base.joinpath( *appendages )
    return base


def provide_data_location( auxdata, *appendages ):
    ''' Provides data location from configuration. '''
    spec = auxdata.configuration.get( 'locations', { } ).get( 'data' )
    if not spec: base = auxdata.directories.user_data_path
    else:
        base = Path( spec.format(
            user_data = auxdata.directories.user_data_dir,
            application_name = auxdata.distribution.name ) )
    if appendages: return base.joinpath( *appendages )
    return base


def provide_state_location( auxdata, *appendages ):
    ''' Provides state location from configuration. '''
    spec = auxdata.configuration.get( 'locations', { } ).get( 'state' )
    if not spec: base = auxdata.directories.user_state_path
    else:
        base = Path( spec.format(
            user_state = auxdata.directories.user_state_dir,
            application_name = auxdata.distribution.name ) )
    if appendages: return base.joinpath( *appendages )
    return base


def _acquire_environment( auxdata ):
    locations = auxdata.configuration[ 'locations' ]
    path = Path( ) / '.env'
    if not path.exists( ) and auxdata.distribution.editable:
        path = Path( auxdata.distribution.location ) / '.env'
    if not path.exists( ) and 'environment-file' in locations:
        path = Path( locations[ 'environment-file' ].format(
            user_configuration = auxdata.directories.user_config_path ) )
    if not path.exists( ): return
    from dotenv import load_dotenv
    with path.open( ) as environment_file:
        load_dotenv( stream = environment_file )


def _prepare_scribes( auxdata ):
    from icecream import ic, install
    from rich.pretty import pretty_repr
    ic.configureOutput(
        argToStringFunction = pretty_repr,
        includeContext = True,
        prefix = 'DEBUG    ', )
    install( )
    from os import environ
    envvar_name = "{name}_LOG_LEVEL".format(
        name = auxdata.distribution.name.upper( ) )
    level_name = environ.get( envvar_name, 'INFO' )
    import logging
    from rich.console import Console
    from rich.logging import RichHandler
    rich_handler = RichHandler(
        console = Console( stderr = True ),
        rich_tracebacks = True,
        show_time = False )
    logging.basicConfig(
        format = '%(name)s: %(message)s',
        handlers = [ rich_handler ],
        level = getattr( logging, level_name ) )
    logging.captureWarnings( True )
    logging.debug( 'Logging initialized.' )
    # TODO? Configure OpenTelemetry emitter.
    #       Can use flame graph of locally-collected traces for profiling.


def _provide_configuration( distribution, directories ):
    from shutil import copyfile
    from tomli import load
    location = directories.user_config_path / 'general.toml'
    if not location.exists( ):
        copyfile(
            str( distribution.location / 'data/configuration/general.toml' ),
            str( location ) )
    with location.open( 'rb' ) as file: return load( file )
