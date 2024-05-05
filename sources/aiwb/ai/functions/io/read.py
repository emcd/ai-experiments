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


''' AI functionality for reading from various sources. '''


from . import base as __


@__.register_function( {
    'name': 'analyze',
    'description': '''
Reads a URL or local filesystem path and passes its contents to an AI agent to
analyze according to a given set of instructions. Returns an analysis of the
contents as a list of one or more chunks, depending on the size of the entity
to be analyzed.
''',
    'parameters': {
        'type': 'object',
        'properties': {
            'source': {
                'type': 'string',
                'description': 'URL or local filesystem path to be read.'
            },
            'control': {
                'type': 'object',
                'description': '''
Special instructions to AI agent to replace or supplement its default
instructions. If not supplied, the agent will use only its default
instructions. ''',
                'properties': {
                    'mode': {
                        'type': 'string',
                        'description': '''
Replace or supplement default instructions of AI agent with given
instructions? ''',
                        'enum': [ 'replace', 'supplement' ],
                        'default': 'supplement',
                    },
                    'instructions': {
                        'type': 'string',
                        'description': '''
Analysis instructions for AI. Should not be empty in replace mode. '''
                    },
                },
            },
        },
        'required': [ 'source' ],
    },
} )
def analyze( auxdata, /, source, control = None ):
    operators = __.SimpleNamespace(
        from_directory = (
            lambda *posargs, **nomargs:
            [ _list_directory( *posargs, **nomargs) ] ),
        from_file = _analyze_file,
        from_http = _analyze_http,
        tokens_counter = None,
    )
    return _operate( auxdata, source, operators, control = None )


@__.register_function( {
    'name': 'read',
    'description': '''
Reads a URL or local file system path and returns the path, its MIME type, and
contents. If the location is a directory, then all of its entries are
recursively scanned and their relevance is determined by an AI agent. All
relevant entries will be returned as list of mappings, having location, MIME
type, and content triples. Custom instructions may optionally be supplied to
the AI agent which determines the relevance of directory entries.
''',
    'parameters': {
        'type': 'object',
        'properties': {
            'source': {
                'type': 'string',
                'description': 'URL or local filesystem path to be read.'
            },
            'control': {
                'type': 'object',
                'description': '''
Special instructions to AI agent to replace or supplement its default
instructions. If not supplied, the agent will use only its default
instructions. ''',
                'properties': {
                    'mode': {
                        'type': 'string',
                        'description': '''
Replace or supplement default instructions of AI agent with given
instructions? ''',
                        'enum': [ 'replace', 'supplement' ],
                        'default': 'supplement',
                    },
                    'instructions': {
                        'type': 'string',
                        'description': '''
Analysis instructions for AI. Should not be empty in replace mode. '''
                    },
                },
            },
        },
        'required': [ 'source' ],
    },
} )
def read( auxdata, /, source, control = None ):
    operators = __.SimpleNamespace(
        from_directory = _read_recursive,
        from_file = (
            lambda auxdata_, path, **nomargs:
            _read_file( auxdata_, dict( location = str( path ) ) ) ),
        from_http = (
            lambda auxdata_, url, **nomargs:
            _read_http( auxdata_, url ) ),
        tokens_counter = _count_tokens,
    )
    return _operate( auxdata, source, operators, control = control )


def _read_recursive( auxdata, path, control = None ):
    results = [ ]
    for dirent in _list_directory( auxdata, path, control = control ):
        result = _read_file( auxdata, dirent )
        if isinstance( result, str ):
            results.append( dict( error = result, **dirent ) )
        else: results.append( result )
    return results


def _access_tokens_limit( auxdata ):
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    model_name = auxdata.controls[ 'model' ]
    return provider.access_model_data( model_name, 'tokens-limit' )


def _analyze_file( auxdata, path, control = None ):
    from ....messages.core import Canister
    from ...providers import chat_callbacks_minimal
    ai_messages = [ ]
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    provider_format_name = provider.provide_format_name( auxdata.controls )
    summarization_prompt = (
        auxdata.prompt_definitions[ 'Concatenate: AI Responses' ]
        .create_prompt( ) )
    supervisor_prompt = (
        auxdata.prompt_definitions[ 'Automation: File Analysis' ]
        .create_prompt( values = { 'format': provider_format_name } ) )
    chunk_reader, mime_type = _determine_chunk_reader( path )
    for chunk in chunk_reader( auxdata, path ):
        messages = [
            Canister( role = 'Supervisor' ).add_content(
                supervisor_prompt.render( auxdata ) ) ]
        # TODO: Check if above high water mark for tokens count.
        #       Drop earliest messages from history, if so.
        if ai_messages:
            messages.append( Canister( role = 'Human' ).add_content(
                summarization_prompt.render( auxdata ) ) )
            messages.append( Canister( role = 'AI' ).add_content(
                '\n\n'.join( ai_messages ) ) )
        _, content = __.render_prompt( auxdata, control, chunk, mime_type )
        messages.append( Canister( role = 'Human' ).add_content( content ) )
        ai_canister = provider.chat(
            messages, { }, auxdata.controls, chat_callbacks_minimal )
        # TODO: Handle combination of analysis and metadata.
        ai_messages.append( ai_canister[ 0 ].data )
    return ai_messages


def _analyze_http( auxdata, url, control = None ):
    file_name = _read_http_core( auxdata, url )
    return _analyze_file( auxdata, file_name, control = control )


def _count_tokens( auxdata, content ):
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    model_name = auxdata.controls[ 'model' ]
    return provider.count_text_tokens( str( content ), model_name )


# TODO: Process bytes buffer.
def _determine_chunk_reader( path, mime_type = None ):
    from magic import from_file
    # TODO? Consider encoding.
    if not mime_type: mime_type = from_file( path, mime = True )
    # TODO: Smarter reading of code chunks.
    if mime_type.startswith( 'text/x-script.' ): reader = _read_chunks_naively
    elif mime_type in ( 'text/x-python', ): reader = _read_chunks_naively
    # TODO: Smarter reading of HTML and Markdown chunks.
    elif mime_type.startswith( 'text/' ): reader = _read_chunks_naively
    else: reader = _read_chunks_destructured
    ic( path, mime_type )
    return reader, mime_type


def _discriminate_dirents( auxdata, dirents, control = None ):
    from ....messages.core import Canister
    from ...providers import chat_callbacks_minimal
    # TODO: Chunk the directory analysis.
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    provider_format_name = provider.provide_format_name( auxdata.controls )
    prompt = (
        auxdata.prompt_definitions[ 'Discriminate Directory Entries' ]
        .create_prompt( values = { 'format': provider_format_name } ) )
    messages = [
        Canister( role = 'Supervisor' ).add_content( prompt.render( auxdata ) )
    ]
    _, content = __.render_prompt(
        auxdata, control, dirents, 'directory-entries' )
    messages.append( Canister( role = 'Human' ).add_content( content ) )
    ai_canister = provider.chat(
        messages, { }, auxdata.controls, chat_callbacks_minimal )
    result = provider.parse_data( ai_canister[ 0 ].data, auxdata.controls )
    ic( result[ 'blacklist' ] )
    return result[ 'whitelist' ]


def _list_directory( auxdata, path, control = None ):
    from os import walk # TODO: Python 3.12: Use 'Pathlib.walk'.
    from magic import from_file
    dirents = [ ]
    # Do not look directly at subdirectories. Walk them instead.
    for base_directory, _, dirents_names in walk( path ):
        for dirent_name in dirents_names:
            dirent = __.Path( base_directory ) / dirent_name
            if not dirent.exists( ): continue
            dirents.append( dict(
                location = str( dirent ),
                mime_type = from_file( dirent, mime = True ) ) )
    return _discriminate_dirents( auxdata, dirents, control = control )


def _operate( auxdata, source, operators, control = None ):
    # TODO: Support wildcards.
    from urllib.parse import urlparse
    tokens_total = 0
    tokens_max = _access_tokens_limit( auxdata ) * 3 // 4
    components = urlparse( source )
    has_file_scheme = not components.scheme or 'file' == components.scheme
    if has_file_scheme:
        if not components.path:
            return 'Error: No file path provided with file scheme URL.'
        path = __.Path( components.path )
        if not path.exists( ): return f"Error: Nothing exists at '{path}'."
        if path.is_file( ): operator = operators.from_file
        elif path.is_dir( ): operator = operators.from_directory
        # TODO: Handle symlinks, named pipes, etc....
        else: return f"Error: Type of entity at '{path}' not supported."
        result = operator( auxdata, path, control = control )
        if operators.tokens_counter:
            tokens_total += operators.tokens_counter( auxdata, result )
            if tokens_total > tokens_max:
                return (
                    f"Error: Input is {tokens_total} tokens in size, "
                    f"which exceeds the safe limit, {tokens_max}." )
        return result
    if components.scheme in ( 'http', 'https', ):
        return operators.from_http( auxdata, source, control = control )
    return f"Error: URL scheme, '{components.scheme}', not supported."


# TODO: Process stream.
def _read_chunks_destructured( auxdata, path ):
    tokens_max = _access_tokens_limit( auxdata ) // 4
    blocks = [ ]
    tokens_total = 0
    hint = 'first chunk'
    from unstructured.partition.auto import partition
    for element in partition( filename = str( path ) ):
        tokens_count = _count_tokens( auxdata, element )
        if tokens_max < tokens_total + tokens_count:
            ic( path, hint, tokens_total )
            yield dict( content = blocks, hint = hint )
            tokens_total = 0
            blocks.clear( )
            hint = 'inner chunk'
        blocks.append( dict(
            species = type( element ).__name__, entity = str( element ) ) )
        tokens_total += tokens_count
    ic( path, hint, tokens_total )
    yield dict( content = blocks, hint = 'last chunk' )


# TODO: Process stream.
def _read_chunks_naively( auxdata, path ):
    tokens_max = _access_tokens_limit( auxdata ) // 4
    lines = [ ]
    tokens_total = 0
    hint = 'first chunk'
    with path.open( ) as file:
        for line_number, line in enumerate( file, start = 1 ):
            tokens_count = _count_tokens( auxdata, line )
            if tokens_max < tokens_total + tokens_count:
                ic( path, hint, tokens_total )
                yield dict( content = ''.join( lines ), hint = hint )
                tokens_total = 0
                lines.clear( )
                hint = 'inner chunk'
            lines.append( line )
            tokens_total += tokens_count
    ic( path, hint, tokens_total )
    yield dict( content = ''.join( lines ), hint = 'last chunk' )


def _read_file( auxdata, dirent ):
    path = __.Path( dirent[ 'location' ] )
    try:
        with path.open( ) as file: contents = file.read( )
        if 'mime_type' not in dirent:
            from magic import from_buffer
            dirent[ 'mime_type' ] = from_buffer( contents, mime = True )
        return dict( contents = contents, **dirent )
    except Exception as exc:
        exc_type = type( exc ).__qualname__
        return dict( error = f"{exc_type}: {exc}", **dirent )


def _read_http( auxdata, url ):
    dirent = dict( location = url )
    try:
        file_name = _read_http_core( auxdata, url )
        with open( file_name ) as file: contents = file.read( )
        from magic import from_buffer
        dirent[ 'mime_type' ] = from_buffer( contents, mime = True )
        return dict( contents = contents, **dirent )
    except Exception as exc:
        exc_type = type( exc ).__qualname__
        return dict( error = f"{exc_type}: {exc}", **dirent )


def _read_http_core( auxdata, url ):
    from shutil import copyfileobj
    from tempfile import NamedTemporaryFile
    from urllib.request import Request, urlopen
    request = Request( url )
    # TODO: Write to conversation cache with file name.
    # TODO? Pass stream to reader function rather than re-open tempfile.
    with NamedTemporaryFile( delete = False ) as file:
        # TODO: Retry on rate limits and timeouts.
        with urlopen( request ) as response:
            copyfileobj( response, file )
    return file.name
