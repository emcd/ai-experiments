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


from . import __


async def analyze(
    context: __.Context, arguments: __.Arguments
) -> __.AbstractSequence:
    ''' Reads URL or filesystem path and analyzes contents with an AI agent.

        AI agent analyzes contents according to instructions and returns
        analysis as a list of one or more chunks, depending on size of entity
        to be analyzed.
    '''
    operators = __.SimpleNamespace(
        from_directory = _list_directory_as_cell,
        from_file = _analyze_file,
        from_http = _analyze_http,
        tokens_counter = None,
    )
    return await _operate(
        context.auxdata,
        arguments[ 'source' ],
        operators,
        control = arguments.get( 'control' ) )


def _access_tokens_limit( auxdata ):
    provider = auxdata.providers[ auxdata.controls[ 'provider' ] ]
    model_name = auxdata.controls[ 'model' ]
    return provider.access_model_data( model_name, 'tokens-limit' )


async def _analyze_file( auxdata, path, control = None ):
    from ....messages import Canister
    from ....providers import chat_callbacks_minimal
    ai_messages = [ ]
    provider = auxdata.providers[ auxdata.controls[ 'provider' ] ]
    provider_format_name = provider.provide_format_name( auxdata.controls )
    summarization_prompt = (
        auxdata.prompts.definitions[ 'Concatenate: AI Responses' ]
        .produce_prompt( ) )
    supervisor_prompt = (
        auxdata.prompts.definitions[ 'Automation: File Analysis' ]
        .produce_prompt( values = { 'format': provider_format_name } ) )
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
        _, content = _render_analysis_prompt(
            auxdata, control, chunk, mime_type )
        messages.append( Canister( role = 'Human' ).add_content( content ) )
        ai_canister = await provider.chat(
            messages, { }, auxdata.controls, chat_callbacks_minimal )
        # TODO: Handle combination of analysis and metadata.
        ai_messages.append( ai_canister[ 0 ].data )
    return ai_messages


async def _analyze_http( auxdata, url, control = None ):
    file_name = _read_http_core( auxdata, url )
    return await _analyze_file( auxdata, file_name, control = control )


def _count_tokens( auxdata, content ):
    provider = auxdata.providers[ auxdata.controls[ 'provider' ] ]
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


async def _discriminate_dirents( auxdata, dirents, control = None ):
    from ....messages import Canister
    from ....providers import chat_callbacks_minimal
    provider = auxdata.providers[ auxdata.controls[ 'provider' ] ]
    provider_format_name = provider.provide_format_name( auxdata.controls )
    prompt = (
        auxdata.prompts.definitions[ 'Discriminate Directory Entries' ]
        .produce_prompt( values = { 'format': provider_format_name } ) )
    supervisor_message = prompt.render( auxdata )
    complete_result = [ ]
    # TODO: Python 3.12: itertools.batches
    batch_size = 70 # TODO: Base on output tokens limit.
    batches_count = len( dirents ) // batch_size + 1
    for batch_n in range( batches_count ):
        dirents_batch = dirents[
            ( batch_n * batch_size ) : ( ( batch_n + 1 ) * batch_size ) ]
        messages = [
            Canister( role = 'Supervisor' ).add_content( supervisor_message )
        ]
        _, content = _render_analysis_prompt(
            auxdata, control, dirents_batch, 'directory-entries' )
        messages.append( Canister( role = 'Human' ).add_content( content ) )
        ai_canister = await provider.chat(
            messages, { }, auxdata.controls, chat_callbacks_minimal )
        #ic( ai_canister[ 0 ].data )
        result = provider.parse_data( ai_canister[ 0 ].data, auxdata.controls )
        ic( result[ 'blacklist' ] )
        complete_result.extend( result[ 'whitelist' ] )
    return complete_result


async def _list_directory( auxdata, path, control = None ):
    # TODO: Configurable filter behavior.
    from os import walk # TODO: Python 3.12: Use 'Pathlib.walk'.
    from gitignorefile import Cache
    from magic import from_file
    dirents = [ ]
    ignorer = Cache( )
    for base_directory, directories_names, dirents_names in walk( path ):
        if '.git' in directories_names: directories_names.remove( '.git' )
        for dirent_name in dirents_names:
            dirent = __.Path( base_directory ) / dirent_name
            if not dirent.exists( ): continue # Gracefully handle races.
            dirent_fqname = str( dirent )
            if ignorer( dirent_fqname ): continue
            inode = dirent.stat( )
            if 40000 < inode.st_size: continue
            dirents.append( dict(
                location = dirent_fqname,
                mime_type = from_file( dirent, mime = True ) ) )
    return await _discriminate_dirents( auxdata, dirents, control = control )


async def _list_directory_as_cell( *posargs, **nomargs ):
    return [ await _list_directory( *posargs, **nomargs ) ]


async def _operate( auxdata, source, operators, control = None ):
    # TODO: Support wildcards.
    tokens_total = 0
    tokens_max = _access_tokens_limit( auxdata ) * 3 // 4
    components = __.urlparse( source )
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
        result = await operator( auxdata, path, control = control )
        if operators.tokens_counter:
            tokens_total += operators.tokens_counter( auxdata, result )
            if tokens_total > tokens_max:
                return (
                    f"Error: Input is {tokens_total} tokens in size, "
                    f"which exceeds the safe limit, {tokens_max}." )
        return result
    if components.scheme in ( 'http', 'https', ):
        return await operators.from_http( auxdata, source, control = control )
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


async def _read_file( auxdata, dirent ):
    from aiofiles import open as open_
    file = __.Path( dirent[ 'location' ] )
    try:
        async with open_( file ) as stream:
            contents = await stream.read( )
        if 'mime_type' not in dirent:
            from magic import from_buffer
            dirent[ 'mime_type' ] = from_buffer( contents, mime = True )
        return dict( contents = contents, **dirent )
    except Exception as exc:
        exc_type = type( exc ).__qualname__
        return dict( error = f"{exc_type}: {exc}", **dirent )


async def _read_http( auxdata, url ):
    from aiofiles import open as open_
    dirent = dict( location = url )
    try:
        file_name = _read_http_core( auxdata, url )
        async with open_( file_name ) as stream:
            contents = await stream.read( )
        from magic import from_buffer
        dirent[ 'mime_type' ] = from_buffer( contents, mime = True )
        return dict( contents = contents, **dirent )
    except Exception as exc:
        exc_type = type( exc ).__qualname__
        return dict( error = f"{exc_type}: {exc}", **dirent )


def _read_http_core( auxdata, url ):
    # TODO: async - aiohttp
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


def _render_analysis_prompt( auxdata, control, content, mime_type ):
    control = control or { }
    instructions = control.get( 'instructions', '' )
    if control.get( 'mode', 'supplement' ):
        instructions = (
            auxdata.prompts.definitions[ 'Analyze Content' ]
            .produce_prompt(
                values = dict(
                    mime_type = mime_type, instructions = instructions ) )
            .render( auxdata ) )
    provider = auxdata.providers[ auxdata.controls[ 'provider' ] ]
    return provider.render_data(
        dict( content = content, instructions = instructions ),
        auxdata.controls )
