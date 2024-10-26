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


''' Implementation of interface to FAISS. '''


from .. import core as _core
from . import __


async def prepare( auxdata: __.Globals ):
    ''' Installs dependencies and returns factory. '''
    # TODO: Install dependencies in isolated environment, if necessary.
    return Factory( )

_core.preparers[ 'faiss' ] = prepare


class Factory( _core.Factory, class_decorators = ( __.standard_dataclass, ) ):
    # https://python.langchain.com/v0.2/docs/integrations/text_embedding/openai/
    # https://python.langchain.com/v0.2/docs/integrations/vectorstores/faiss/
    # https://api.python.langchain.com/en/latest/vectorstores/langchain_community.vectorstores.faiss.FAISS.html

    # TODO: Wrap in decorator to execute with isolated imports context.
    async def client_from_descriptor(
        self,
        auxdata: __.Globals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        # TODO: Return future.
        # TODO? Remove dependency on Langchain.
        # TODO: Configurable embedding function.
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        embedder = OpenAIEmbeddings( )
        arguments = descriptor.get( 'arguments', { } )
        location = _core.derive_vectorstores_location(
            auxdata, descriptor[ 'location' ] )
        if isinstance( location, __.Path ):
            return FAISS.load_local(
                folder_path = str( location ),
                embeddings = embedder,
                index_name = arguments[ 'index' ] )
