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


from . import __


# TODO: 'prepare' function for provider
#       Install dependencies in isolated environment.


async def restore( auxdata, store ):
    # https://python.langchain.com/v0.2/docs/integrations/text_embedding/openai/
    # https://python.langchain.com/v0.2/docs/integrations/vectorstores/chroma/
    # https://docs.trychroma.com/reference/py-client
    # TODO? Remove dependency on Langchain.
    # TODO: Configurable embedding function.
    from chromadb import PersistentClient
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    embedder = OpenAIEmbeddings( )
    data = store.data
    arguments = data.get( 'arguments', { } )
    collection_name = arguments[ 'collection' ]
    location_info = __.urlparse( data[ 'location' ] )
    if 'file' == location_info.scheme:
        location = __.derive_vectorstores_location( auxdata, location_info )
        client = PersistentClient( path = str( location ) )
        client.get_or_create_collection( collection_name )
        return Chroma(
            client = client,
            collection_name = collection_name,
            embedding_function = embedder )
    # TODO: Run local server containers, where relevant.
    # TODO: Setup clients for server connections, where relevant.
