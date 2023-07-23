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


def prepare( configuration, directories ):
    from pathlib import Path
    from tomli import load as load_toml
    registry_path = directories.user_config_path / 'vectorstores.toml'
    stores = { }
    if not registry_path.exists( ): return stores
    with registry_path.open( 'rb' ) as registry_file:
        registry = load_toml( registry_file )
    for data in registry.get( 'stores', ( ) ):
        store_name = data[ 'name' ]
        stores[ store_name ] = data.copy( )
        provider_name = data[ 'provider' ]
        if provider_name not in _registry:
            # TODO: Improve error signaling.
            raise ValueError(
                f"Unknown vectorstore provider, '{provider_name}', "
                f"for vectorstore '{store_name}'." )
        instance = _registry[ provider_name ](
            configuration, directories, data )
        stores[ store_name ][ 'instance' ] = instance
        # TODO: Run local server containers, where relevant.
        # TODO: Setup clients for server connections, where relevant.
    return stores


def restore_chroma( configuration, directories, data ):
    from pathlib import Path
    from urllib.parse import urlparse
    from chromadb import Client
    from chromadb.config import Settings
    arguments = data.get( 'arguments', { } )
    location_info = urlparse( data[ 'location' ] )
    if 'file' == location_info.scheme:
        location = Path( location_info.path.format(
            **_derive_standard_file_paths( configuration, directories ) ) )
        client = Client( Settings(
            chroma_db_impl  = data[ 'format' ],
            persist_directory = str( location ) ) )
        return client.get_collection( arguments[ 'collection' ] )


def restore_faiss( configuration, directories, data ):
    from urllib.parse import urlparse
    from pickle import load as unpickle
    location_info = urlparse( data[ 'location' ] )
    if 'file' == location_info.scheme:
        location = Path( location_info.path.format(
            **_derive_standard_file_paths( configuration, directories ) ) )
        format_ = data[ 'format' ]
        if 'python-pickle' == format_:
            with location.open( 'rb' ) as store_file:
                return unpickle( store_file )


# TODO: Use accretive dictionary instead of fully-mutable one.
_registry = {
    'chroma': restore_chroma,
    'faiss': restore_faiss,
}


def _derive_standard_file_paths( configuration, directories ):
    from pathlib import Path
    return dict(
        data_path = Path(
            configuration[ 'locations' ][ 'data' ] ) / 'vectorstores',
    )
