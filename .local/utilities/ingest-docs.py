''' Load documentation from sources. '''


from dataclasses import dataclass
from functools import partial as partial_function
from sys import stderr


@dataclass
class EmbeddingData:
    doc_id: str
    document: object
    embedding: list = None


def count_tokens( content ):
    from tiktoken import get_encoding
    encoding = get_encoding( 'cl100k_base' )
    return len( encoding.encode( content ) )


eprint = partial_function( print, file = stderr )


def provide_openai_credentials( ):
    from pathlib import Path
    from dotenv import dotenv_values
    environment = dotenv_values( str(
        ( Path.home( ) / '.config/llm-chatter/environment' ).resolve( ) ) )
    import openai
    openai.api_key = environment[ 'OPENAI_API_KEY' ]
    openai.organization = environment[ 'OPENAI_ORGANIZATION_ID' ]
    return dict(
        openai_api_key = environment[ 'OPENAI_API_KEY' ],
        openai_organization = environment[ 'OPENAI_ORGANIZATION_ID' ] )


def _provide_delegate_loaders( ):
    from types import MappingProxyType as DictionaryProxy
    return DictionaryProxy( {
        '**/*.ipynb': dict(
            loader_class = 'NotebookLoader',
            splitter = {
                'class': 'RecursiveCharacterTextSplitter',
                'args': { 'chunk_size': 1000, 'chunk_overlap': 200 },
            } ),
        '**/*.md': dict(
            loader_class = 'UnstructuredMarkdownLoader',
            splitter = {
                'class': 'RecursiveCharacterTextSplitter',
                'args': { 'chunk_size': 1000, 'chunk_overlap': 200 },
            } ),
        '**/*.py': dict(
            loader_class = 'PythonLoader',
            splitter = {
                'class': 'PythonCodeTextSplitter',
                'args': { 'chunk_size': 30, 'chunk_overlap': 0 },
            } ),
        '**/*.rst': dict(
            loader_class = 'UnstructuredFileLoader',
            splitter = {
                'class': 'RecursiveCharacterTextSplitter',
                'args': { 'chunk_size': 1000, 'chunk_overlap': 200 },
            } ),
    } )

DELEGATE_LOADERS = _provide_delegate_loaders( )


def generate_and_store_embeddings( embedder, vectorstore, documents ):
    tokens_total = 0
    interval_i = interval_f = 0
    tokens_max = 1_000_000
    documents_max = 2048
    timeout = 60
    embeddings_data = [
        EmbeddingData( doc_id = str(i), document = document, embedding = None )
        for i, document in enumerate( documents ) ]
    faulty_embeddings_data = [ ]
    for i, data in enumerate( embeddings_data ):
        tokens_count = count_tokens( data.document.page_content )
        if tokens_count >= 8191: raise ValueError( 'Document too large!' )
        if (
                tokens_max > tokens_total + tokens_count
            and documents_max > i - interval_i
        ):
            tokens_total += tokens_count
            continue
        interval_f = i
        batch = embeddings_data[ interval_i : interval_f ]
        faulty_embeddings_data.extend( _generate_and_store_embeddings(
            embedder, vectorstore, batch, timeout, tokens_total ) )
        interval_i = i
        tokens_total = 0
    # process the last batch if it does not reach the max thresholds
    interval_f = len( embeddings_data )
    if interval_i != interval_f:
        batch = embeddings_data[ interval_i : ]
        faulty_embeddings_data.extend(
            _generate_and_store_embeddings(
                embedder, vectorstore, batch, timeout, tokens_total ) )
    # Retry for failed embeddings
    while faulty_embeddings_data:
        eprint( 'Retrying for failed embeddings...' )
        faulty_embeddings_data_remainder = _generate_and_store_embeddings(
            embedder, vectorstore, faulty_embeddings_data, timeout, -1 )
        faulty_embeddings_data = faulty_embeddings_data_remainder


def _generate_and_store_embeddings(
        embedder, vectorstore, data, timeout, tokens_total
):
    from time import sleep
    eprint(
        "Embedding {tokens_total} tokens "
        "from {documents_total} documents.".format(
            tokens_total = tokens_total,
            documents_total = len( data ) ) )
    faulty_data = generate_embeddings( embedder, data )
    store_embeddings( vectorstore, data )
    eprint( f"Sleeping {timeout} seconds." )
    sleep( timeout )
    return faulty_data


def generate_embeddings( embedder, embeddings_data ):
    import numpy as np
    from openai import Embedding
    docs_to_embed = [
        data for data in embeddings_data if data.embedding is None ]
    if not docs_to_embed: return [ ]
    response = Embedding.create(
        input = [ data.document.page_content for data in docs_to_embed ],
        model = 'text-embedding-ada-002' )
    faulty_embeddings_data = [ ]
    for i, data in enumerate( response.data ):
        embedding = data.embedding
        if len( embedding ) == 1536 and not np.isnan( embedding ).any( ):
            docs_to_embed[ i ].embedding = embedding
        else: faulty_embeddings_data.append( docs_to_embed[ i ] )
    return faulty_embeddings_data


def store_embeddings( vectorstore, embeddings_data ):
    docs_to_store = [
        data for data in embeddings_data if data.embedding is not None ]
    if not docs_to_store: return
    vectorstore.add(
        documents = [ data.document.page_content for data in docs_to_store ],
        embeddings = [ data.embedding for data in docs_to_store ],
        ids = [ data.doc_id for data in docs_to_store ],
        metadatas = [ data.document.metadata for data in docs_to_store ] )


def load_manifest_file( manifest_path ):
    import tomli as tomllib
    with open( manifest_path, 'rb' ) as manifest_file:
        manifest = tomllib.load( manifest_file )
    return manifest[ 'repositories' ]


def ingest_source( source_config ):
    source_type = source_config[ 'type' ]
    source_path = source_config[ 'path' ]
    delegate_loaders = DELEGATE_LOADERS.copy( )
    if 'config' in source_config:
        for pattern, config in source_config[ 'config' ].items( ):
            delegate_loaders[ pattern ] = config
    for pattern, control in delegate_loaders.items( ):
        splitter = _instantiate_splitter( control[ 'splitter' ] )
        control[ 'splitter' ] = splitter
        loader_class = _get_loader_class( control[ 'loader_class' ] )
        control[ 'loader_class' ] = loader_class
    if source_type == 'websites':
        return ingest_websites( source_path )
    elif source_type == 'directory':
        return ingest_directory( source_path, delegate_loaders )
    elif source_type in { 'openapi', 'graphql' }:
        # TODO: Handle remote URLs for OpenAPI/GraphQL schemas
        pass
    else: raise ValueError( f"Unsupported source type: {source_type}" )


def ingest_directory( location, delegate_loaders ):
    from langchain.document_loaders import DirectoryLoader
    documents = [ ]
    for glob, control in delegate_loaders.items( ):
        subloader_class = control[ 'loader_class' ]
        splitter = control[ 'splitter' ]
        loader = DirectoryLoader(
            location, glob = glob, loader_cls = subloader_class )
        documents.extend( splitter.split_documents( loader.load( ) ) )
    return documents


def ingest_websites( file_path ):
    from json import load
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    with open( file_path, 'r' ) as file: scraped_data = load( file )
    contents = [ ]
    metadatas = [ ]
    for data in scraped_data:
        contents.append( data[ 'content' ] )
        metadata = { 'url': data[ 'url' ], 'title': data[ 'title' ] }
        metadatas.append( metadata )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000, chunk_overlap = 200 )
    documents = splitter.create_documents( contents, metadatas = metadatas )
    return documents


def prepare_vectorstore( ):
    from chromadb import Client
    from chromadb.config import Settings
    # TODO: Pull configuration from file.
    client = Client( Settings(
        chroma_db_impl = 'duckdb+parquet',
        persist_directory =
            '/mnt/d/Dropbox/common/data/llm-chatter/vectorstores/chromadb' ) )
    collection_name = 'sphinx-documentation'
    collection_names = set(
        collection.name for collection in client.list_collections( ) )
    if collection_name in collection_names:
        client.delete_collection( collection_name )
    return client.create_collection( collection_name )


def _get_loader_class( class_name ):
    from importlib import import_module
    module = import_module( 'langchain.document_loaders' )
    return getattr( module, class_name )


def _instantiate_splitter( info ):
    from importlib import import_module
    module = import_module( 'langchain.text_splitter' )
    return getattr( module, info[ 'class' ] )( **info[ 'args' ] )


COST_PER_THOUSAND_TOKENS = 0.0001

def main( ):
    openai_credentials = provide_openai_credentials( )
    manifest_path = 'data-sources/manifest.toml'
    repositories = load_manifest_file( manifest_path )
    # TODO: One vectorstore per repo.
    vectorstore = prepare_vectorstore( )
    from tiktoken import get_encoding
    encoding = get_encoding( 'cl100k_base' )
    for repo_config in repositories:
        documents = ingest_source( repo_config )
        total_tokens = sum(
            len( encoding.encode( document.page_content ) )
            for document in documents )
        cost = ( total_tokens / 1000 ) * COST_PER_THOUSAND_TOKENS
        print( f"Total Tokens: {total_tokens}; Cost to Embed: ${cost:.4f}" )
        confirmation = input( "Proceed with embedding? (y/n): " ).lower( )
        if 'y' == confirmation:
            generate_and_store_embeddings( None, vectorstore, documents )
        else: print( "Embedding skipped." )


if '__main__' == __name__: main( )
