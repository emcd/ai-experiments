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


''' Persistent and active process environment values. '''


from . import __
from . import state as _state


async def update( auxdata: _state.Globals ):
    ''' Updates process environment from dot files. '''
    locations = auxdata.configuration.get( 'locations', { } )
    location = __.Path( ) / '.env'
    if not location.exists( ) and auxdata.distribution.editable:
        location = __.Path( auxdata.distribution.location ) / '.env'
    if not location.exists( ) and 'environment' in locations:
        location = __.Path( locations[ 'environment' ].format(
            user_configuration = auxdata.directories.user_config_path,
            user_home = __.Path.home( ) ) )
    if not location.exists( ): return
    files = (
        location.glob( '*.env' ) if location.is_dir( ) else ( location, ) )
    await __.read_files_async(
        *( file for file in files ), deserializer = _inject_dotenv_data )


def _inject_dotenv_data( data: str ) -> dict:
    from io import StringIO
    from dotenv import load_dotenv
    return load_dotenv( stream = StringIO( data ) )
