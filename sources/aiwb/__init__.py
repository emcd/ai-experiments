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


''' Support for interactions with generative artificial intelligences. '''


__version__ = '1.0a202404271857'


from . import ai
from . import controls
from . import gui
from . import messages
from . import prompts


def main( ):
    configuration, directories = prepare( )
    gui_ns = gui.prepare( configuration, directories )
    gui_ns.template__.show( title = 'AI Workbench' )


def prepare( ):
    from pathlib import Path
    # TODO: Determine main path from perspective of installed package.
    #       Or use 'importlib.resources'.
    main_path = Path( __file__ ).parent.parent.parent.resolve( strict = True )
    from platformdirs import PlatformDirs
    # TODO: Change directories anchor to 'aiwb'.
    directories = PlatformDirs( 'llm-chatter', 'emcd', ensure_exists = True )
    configuration = provide_configuration( main_path, directories )
    configuration[ 'main-path' ] = main_path
    prepare_environment( configuration, directories )
    prepare_inscribers( configuration, directories )
    return configuration, directories


def prepare_environment( configuration, directories ):
    from pathlib import Path
    path = Path( configuration[ 'locations' ][ 'environment-file' ].format(
        user_configuration_path = directories.user_config_path,
        main_path = configuration[ 'main-path' ] ) )
    if not path.exists( ): return
    from dotenv import load_dotenv
    with path.open( ) as environment_file:
        load_dotenv( stream = environment_file )


def prepare_inscribers( configuration, directories ):
    from icecream import ic, install
    from rich.pretty import pretty_repr
    ic.configureOutput(
        argToStringFunction = pretty_repr,
        includeContext = True,
        prefix = 'DEBUG    ', )
    install( )
    import logging
    from rich.console import Console
    from rich.logging import RichHandler
    # TODO: Get log level from environment.
    rich_handler = RichHandler(
        console = Console( stderr = True ),
        rich_tracebacks = True,
        show_time = False )
    logging.basicConfig(
        format = '%(name)s: %(message)s',
        handlers = [ rich_handler ],
        level = logging.INFO )
    logging.captureWarnings( True )
    logging.debug( 'Logging initialized.' )
    # TODO? Configure OpenTelemetry emitter.
    #       Can use flame graph of locally-collected traces for profiling.


def provide_configuration( main_path, directories ):
    from shutil import copyfile
    from tomli import load
    configuration_path = directories.user_config_path / 'general.toml'
    if not configuration_path.exists( ):
        # TODO: Copy configuration from under 'data' rather than '.local/data'.
        copyfile(
            str( main_path / '.local/data/configuration/general.toml' ),
            str( configuration_path ) )
    with configuration_path.open( 'rb' ) as file: return load( file )
