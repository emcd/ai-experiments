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


''' Functionality for various vectorstores. '''


from . import chroma
from . import faiss


def prepare( configuration, directories ):
    from tomli import load as load_toml
    manifest_path = directories.user_config_path / 'vectorstores.toml'
    stores = { }
    if not manifest_path.exists( ): return stores
    with manifest_path.open( 'rb' ) as manifest_stream:
        manifest = load_toml( manifest_stream )
    for data in manifest.get( 'stores', ( ) ):
        store_name = data[ 'name' ]
        stores[ store_name ] = data.copy( )
        provider_name = data[ 'provider' ]
        if provider_name not in globals( ):
            # TODO: Improve error signaling.
            raise ValueError(
                f"Unknown vectorstore provider, '{provider_name}', "
                f"for vectorstore '{store_name}'." )
        instance = globals( )[ provider_name ].restore(
            configuration, directories, data )
        stores[ store_name ][ 'instance' ] = instance
    return stores
