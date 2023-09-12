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
    configuration, template = prepare( )
    #import panel
    #panel.serve( gui.dashboard, start = True )
    template.show( )


def prepare( ):
    from pathlib import Path
    from sys import path as module_search_paths
    main_path = Path( __file__ ).parent.parent.resolve( strict = True )
    library_path = main_path / 'sources'
    module_search_paths.insert( 0, str( library_path ) )
    from platformdirs import PlatformDirs
    directories = PlatformDirs( 'llm-chatter', 'emcd', ensure_exists = True )
    configuration = provide_configuration( main_path, directories )
    configuration[ 'main-path' ] = main_path
    #prepare_environment( configuration, directories )
    prepare_inscribers( configuration, directories )
    #from chatter.gui import prepare as prepare_gui
    template = prepare_gui( configuration, directories )
    return configuration, template


def prepare_gui( configuration, directories ):
    from panel.layout import Column, Row
    from panel.widgets import Button
    from chatter.gui.templates.default import DefaultTemplate
    template = DefaultTemplate( )
    template.add_panel( 'left', Column( Button( name = 'Left' ) ) )
    template.add_panel( 'top', Column( Button( name = 'Top' ) ) )
    template.add_panel( 'main', Column( Button( name = 'Main' ) ) )
    template.add_panel( 'bottom', Column( Button( name = 'Bottom' ) ) )
    template.add_panel( 'right', Column( Button( name = 'Right' ) ) )
    return template


def prepare_inscribers( configuration, directories ):
    from icecream import install
    install( )


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
