''' Load documentation from sources. '''


def provide_openai_credentials( ):
    import tomli as tomllib
    with open(
        '.local/configuration/credentials.toml', 'rb'
    ) as credentials_file: credentials = tomllib.load(credentials_file)
    return dict(
        openai_api_key = credentials['openai']['token'],
        openai_organization = credentials['openai']['organization'] )


def _provide_delegate_loaders( ):
    from types import MappingProxyType as DictionaryProxy
    return DictionaryProxy( {
        '**/*.ipynb': DictionaryProxy( dict(
            loader_class = 'NotebookLoader',
            splitter = {
                'class': 'RecursiveCharacterTextSplitter',
                'args': { 'chunk_size': 1000, 'chunk_overlap': 200 },
            } ) ),
        '**/*.md': DictionaryProxy( dict(
            loader_class = 'UnstructuredMarkdownLoader',
            splitter = {
                'class': 'RecursiveCharacterTextSplitter',
                'args': { 'chunk_size': 1000, 'chunk_overlap': 200 },
            } ) ),
        '**/*.py': DictionaryProxy( dict(
            loader_class = 'PythonLoader',
            splitter = {
                'class': 'PythonCodeTextSplitter',
                'args': { 'chunk_size': 30, 'chunk_overlap': 0 },
            } ) ),
        '**/*.rst': DictionaryProxy( dict(
            loader_class = 'UnstructuredFileLoader',
            splitter = {
                'class': 'RecursiveCharacterTextSplitter',
                'args': { 'chunk_size': 1000, 'chunk_overlap': 200 },
            } ) ),
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
    if source_type == 'directory':
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


def _get_loader_class( class_name ):
    from importlib import import_module
    module = import_module( 'langchain.document_loaders' )
    return getattr( module, class_name )


def _instantiate_splitter( info ):
    from importlib import import_module
    module = import_module( 'langchain.text_splitter' )
    return getattr( module, info[ 'class' ] )( **info[ 'args' ] )


def main( ):
    openai_credentials = provide_openai_credentials( )
    manifest_path = 'data-sources/manifest.toml'
    repositories = load_manifest_file( manifest_path )
    from tiktoken import get_encoding
    encoding = get_encoding( 'cl100k_base' )
    for repo_config in repositories:
        documents = ingest_source( repo_config )
        print( sum(
            len( encoding.encode( document.page_content ) )
            for document in documents ) )
        store_embeddings( documents )


if '__main__' == __name__: main( )
