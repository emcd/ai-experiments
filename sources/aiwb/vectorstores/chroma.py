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


''' Implementation of interface to ChromaDB. '''


from . import base as __


def restore( configuration, directories, data ):
    # TODO: Adapt to new Langchain interface or remove Langchain dependency.
    #       https://python.langchain.com/docs/modules/data_connection/vectorstores/#get-started
    # TODO: Configurable embedding function.
    from langchain.embeddings.openai import OpenAIEmbeddings
    from langchain.vectorstores import ( # pylint: disable=no-name-in-module
        Chroma,
    )
    embedder = OpenAIEmbeddings( )
    arguments = data.get( 'arguments', { } )
    location_info = __.urlparse( data[ 'location' ] )
    if 'file' == location_info.scheme:
        location = __.Path( location_info.path.format(
            **__.derive_standard_file_paths( configuration, directories ) ) )
        return Chroma(
            collection_name = arguments[ 'collection' ],
            embedding_function = embedder,
            persist_directory = str( location ) )
    # TODO: Run local server containers, where relevant.
    # TODO: Setup clients for server connections, where relevant.
