''' Load documentation from sources. '''


def provide_openai_credentials( ):
    import tomli as tomllib
    with open(
        '.local/configuration/credentials.toml', 'rb'
    ) as credentials_file: credentials = tomllib.load(credentials_file)
    return dict(
        openai_api_key = credentials['openai']['token'],
        openai_organization = credentials['openai']['organization'] )


def ingest_directory( location ):
    from langchain.document_loaders import DirectoryLoader
    documents = [ ]
    for glob, control in DELEGATE_LOADERS.items( ):
        subloader_class = control[ 'loader_class' ]
        splitter = control[ 'splitter' ]
        loader = DirectoryLoader(
            location, glob = glob, loader_cls = subloader_class )
        documents.extend( splitter.split_documents( loader.load( ) ) )
    return documents


def _provide_delegate_loaders( ):
    from types import MappingProxyType as DictionaryProxy
    from langchain.document_loaders import(
        NotebookLoader,
        PythonLoader,
        UnstructuredFileLoader,
        UnstructuredMarkdownLoader,
    )
    from langchain.text_splitter import (
        PythonCodeTextSplitter,
        RecursiveCharacterTextSplitter,
    )
    python_splitter = PythonCodeTextSplitter(
        chunk_size = 30, chunk_overlap = 0 )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000, chunk_overlap = 200 )
    return DictionaryProxy( {
        '**/*.ipynb': DictionaryProxy( dict(
            loader_class = NotebookLoader,
            splitter = text_splitter, ) ),
        '**/*.md': DictionaryProxy( dict(
            loader_class = UnstructuredMarkdownLoader,
            splitter = text_splitter, ) ),
        '**/*.py': DictionaryProxy( dict(
            loader_class = PythonLoader,
            splitter = python_splitter, ) ),
        '**/*.rst': DictionaryProxy( dict(
            loader_class = UnstructuredFileLoader,
            splitter = text_splitter, ) ),
    } )

DELEGATE_LOADERS = _provide_delegate_loaders( )


def store_embeddings( documents ):
    from pathlib import Path
    from pickle import dump, load
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores.faiss import FAISS
    vectorstore_path = Path( 'vectorstore.pypickle' )
    embeddings = OpenAIEmbeddings( **provide_openai_credentials( ) )
    vectorstore = FAISS.from_documents( documents, embeddings )
    if vectorstore_path.exists( ):
        with vectorstore_path.open( 'rb' ) as file:
            vectorstore.merge_from( load( file ) )
    with vectorstore_path.open( 'wb' ) as file:
        dump( vectorstore, file )


def main( ):
    from pprint import pprint
    openai_credentials = provide_openai_credentials( )
    # TODO: Loop over entries in a manifest file,
    #       which specify locations in the 'data-sources' directory
    #       or perhaps OpenAPI or GraphQL schema endpoints.
    documents = ingest_directory( '../THIRD_PARTY/langchain/docs' )
    from tiktoken import get_encoding
    encoding = get_encoding( 'cl100k_base' )
    print( sum(
        len( encoding.encode( document.page_content ) )
        for document in documents ) )
    store_embeddings( documents )


if '__main__' == __name__: main( )
