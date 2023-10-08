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


def main( ):
    configuration, gui = prepare( )
    gui.template__.show( )


def prepare( ):
    from pathlib import Path
    from sys import path as module_search_paths
    main_path = Path( __file__ ).parent.resolve( strict = True )
    library_path = main_path / 'sources'
    module_search_paths.insert( 0, str( library_path ) )
    from platformdirs import PlatformDirs
    directories = PlatformDirs( 'llm-chatter', 'emcd', ensure_exists = True )
    configuration = provide_configuration( main_path, directories )
    configuration[ 'main-path' ] = main_path
    prepare_environment( configuration, directories )
    prepare_inscribers( configuration, directories )
    from chatter.gui import prepare as prepare_gui
    gui = prepare_gui( configuration, directories )
    return configuration, gui


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
    from icecream import install
    install( )
    import logging
    # TODO: Get log level from environment.
    logging.basicConfig(
        format = '%(levelname)s %(name)s: %(message)s', level = logging.INFO )
    logging.captureWarnings( True )
    logging.debug( 'Logging initialized.' )
    # TODO? Configure OpenTelemetry emitter.
    #       Can use flame graph of locally-collected traces for profiling.


def provide_configuration( main_path, directories ):
    from shutil import copyfile
    from tomli import load
    configuration_path = directories.user_config_path / 'general.toml'
    if not configuration_path.exists( ):
        copyfile(
            str( main_path / '.local/data/configuration/general.toml' ),
            str( configuration_path ) )
    with configuration_path.open( 'rb' ) as file: return load( file )


if __name__ == "__main__": main( )
