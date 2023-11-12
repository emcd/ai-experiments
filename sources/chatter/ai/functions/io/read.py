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
            'url': {
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
        'required': [ 'url' ],
    },
} )
def analyze( auxdata, /, url, control = None ):
    # TODO: Support wildcards.
    from urllib.parse import urlparse
    components = urlparse( url )
    has_file_scheme = not components.scheme or 'file' == components.scheme
    if has_file_scheme:
        if not components.path:
            return 'Error: No file path provided with file scheme URL.'
        path = __.Path( components.path )
        if not path.exists( ): return f"Error: Nothing exists at '{path}'."
        if path.is_file( ):
            # TODO: Work with 'pathlib.Path'.
            return _analyze_file( auxdata, components.path, control = control )
        if path.is_dir( ):
            return [ _list_directory(
                auxdata, path, control = control, recursive = True ) ]
        return f"Error: Type of entity at '{path}' not supported."
        # TODO: Handle symlinks, named pipes, etc....
    elif components.scheme in ( 'http', 'https', ):
        return _analyze_http( auxdata, url, control = control )
    return f"Error: URL scheme, '{components.scheme}', not supported."


@__.register_function( {
    'name': 'read',
    'description': '''
Reads a URL or local file system path and returns the path, its MIME type,
and contents. If the path is a directory, then all of its entries are
recursively scanned and their relevance is determined by an AI agent. All
relevant entries will be returned as list of mappings, having path, MIME type,
and content triples. Custom instructions may optionally be supplied to the AI
agent which determines the relevance of directory entries.
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
    # TODO: Count tokens. Return error if source is too large for model.
    # TODO: Support wildcards.
    from urllib.parse import urlparse
    components = urlparse( source )
    has_file_scheme = not components.scheme or 'file' == components.scheme
    if has_file_scheme:
        if not components.path:
            return 'Error: No file path provided with file scheme URL.'
        path = __.Path( components.path )
        if not path.exists( ): return f"Error: Nothing exists at '{path}'."
        if path.is_file( ):
            path_ = str( path )
            dirent = dict(
                path = path_, mime_type = from_file( path_, mime = True ) )
            return _read_file( auxdata, dirent )
        if path.is_dir( ):
            return [
                _read_file( auxdata, dirent ) for dirent in
                _list_directory(
                    auxdata, path, control = control, recursive = True ) ]
        return f"Error: Type of entity at '{path}' not supported."
        # TODO: Handle symlinks, named pipes, etc....
    elif components.scheme in ( 'http', 'https', ):
        return _read_http( auxdata, source )
    return f"Error: URL scheme, '{components.scheme}', not supported."


def _analyze_file( auxdata, /, path, control = None ):
    from chatter.ai.providers import ChatCallbacks
    from chatter.messages import render_prompt_template
    ai_messages = [ ]
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    summarization_prompt = render_prompt_template(
        auxdata.prompt_templates.canned[
            'Concatenate: AI Responses' ][ 'template' ],
        controls = auxdata.controls )
    supervisor_prompt = render_prompt_template(
        auxdata.prompt_templates.system[
            'Automation: File Analysis' ][ 'template' ],
        controls = auxdata.controls,
        variables = dict(
            format_name = provider.provide_format_name( auxdata.controls ),
        ) )
    chunk_reader, mime_type = _determine_chunk_reader( path )
    for chunk in chunk_reader( auxdata, path ):
        messages = [ dict( content = supervisor_prompt, role = 'Supervisor' ) ]
        # TODO: Check if above high water mark for tokens count.
        #       Drop earliest messages from history, if so.
        if ai_messages:
            messages.append( dict(
                content = summarization_prompt, role = 'User' ) )
            messages.append( dict(
                content = '\n\n'.join( ai_messages ), role ='AI' ) )
        _, content = __.render_prompt( auxdata, control, chunk, mime_type )
        messages.append( dict( content = content, role = 'User' ) )
        callbacks = ChatCallbacks(
            allocator = ( lambda mime_type: [ ] ),
            updater = ( lambda handle, content: handle.append( content ) ),
        )
        handle = provider.chat( messages, { }, auxdata.controls, callbacks )
        # TODO: Handle combination of analysis and metadata.
        ai_messages.append( ''.join( handle ) )
    return ai_messages


def _analyze_http( auxdata, /, url, control = None ):
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
    return _analyze_file( auxdata, file.name, control = control )


# TODO: Process path or bytes buffer.
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
    from chatter.ai.providers import ChatCallbacks
    from chatter.messages import render_prompt_template
    # TODO: Chunk the directory analysis.
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    supervisor_prompt = render_prompt_template(
        auxdata.prompt_templates.system[
            'Automation: Discriminate Directory Entries' ][ 'template' ],
        controls = auxdata.controls,
        variables = dict(
            format_name = provider.provide_format_name( auxdata.controls ),
        ) )
    messages = [ dict( content = supervisor_prompt, role = 'Supervisor' ) ]
    _, content = __.render_prompt(
        auxdata, control, dirents, 'directory-entries' )
    messages.append( dict( content = content, role = 'User' ) )
    callbacks = ChatCallbacks(
        allocator = ( lambda mime_type: [ ] ),
        updater = ( lambda handle, content: handle.append( content ) ),
    )
    handle = provider.chat( messages, { }, auxdata.controls, callbacks )
    return provider.parse_data( ''.join( handle ), auxdata.controls )


def _list_directory( auxdata, /, path, control = None, recursive = False ):
    from os import walk # TODO: Python 3.12: Use 'Pathlib.walk'.
    from magic import from_file
    dirents = [ ]
    # Ignore directory names if in recursive mode.
    for base_directory, directories_names, dirents_names in walk( path ):
        for dirent_name in dirents_names:
            dirent = __.Path( base_directory ) / dirent_name
            if not dirent.exists( ): continue
            dirent_ = str( dirent )
            if dirent.is_dir( ):
                if not recursive:
                    dirents.append( dict(
                        path = dirent_, description = 'directory' ) )
                continue
            dirents.append( dict(
                path = dirent_,
                mime_type = from_file( dirent_, mime = True ) ) )
    return _discriminate_dirents( auxdata, dirents, control = control )


# TODO: Process stream.
def _read_chunks_destructured( auxdata, path ):
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    model_name = auxdata.controls[ 'model' ]
    tokens_max = provider.access_model_data( model_name, 'tokens-limit' ) // 4
    blocks = [ ]
    tokens_total = 0
    hint = 'first chunk'
    from unstructured.partition.auto import partition
    for element in partition( filename = path ):
        tokens_count = provider.count_text_tokens( str( element ), model_name )
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
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    model_name = auxdata.controls[ 'model' ]
    tokens_max = provider.access_model_data( model_name, 'tokens-limit' ) // 4
    lines = [ ]
    tokens_total = 0
    hint = 'first chunk'
    with open( path ) as file:
        for line_number, line in enumerate( file, start = 1 ):
            tokens_count = provider.count_text_tokens( line, model_name )
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
    # TODO: Return tokens count.
    path = __.Path( dirent[ 'path' ] )
    try:
        with path.open( ) as file:
            return dict( contents = file.read( ), **dirent )
    except Exception as exc:
        exc_type = type( exc ).__qualname__
        return dict( error = f"{exc_type}: {exc}", **dirent )
