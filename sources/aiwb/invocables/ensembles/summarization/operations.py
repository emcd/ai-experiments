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


FILE_SIZE_MAXIMUM = 40000


async def analyze(
    context: __.Context, arguments: __.Arguments
) -> __.cabc.Sequence:
    ''' Reads URL or filesystem path and analyzes contents with an AI agent.

        AI agent analyzes contents according to instructions and returns
        analysis as a list of one or more chunks, depending on size of entity
        to be analyzed.
    '''
    operators = __.types.SimpleNamespace(
        from_directory = _list_directory_as_cell,
        from_file = _analyze_file,
        from_http = _analyze_http,
        tokens_counter = None,
    )
    return await _operate(
        context,
        arguments[ 'source' ],
        operators,
        control = arguments.get( 'control' ) )


def _access_tokens_limit( context ):
    model = context.supplements[ 'model' ]
    return model.attributes.tokens_limits.total


async def _analyze_file( context, path, control = None ):
    from ....messages import (
        AssistantCanister, Canister, SupervisorCanister, UserCanister )
    from ....providers import conversation_reactors_minimal
    auxdata = context.auxdata
    controls = context.supplements[ 'controls' ]
    model = context.supplements[ 'model' ]
    ai_messages = [ ]
    format_name = model.attributes.format_preferences.request_data.value
    summarization_prompt = (
        auxdata.prompts.definitions[ 'Concatenate: AI Responses' ]
        .produce_prompt( ) )
    supervisor_prompt = (
        auxdata.prompts.definitions[ 'Automation: File Analysis' ]
        .produce_prompt( values = { 'format': format_name } ) )
    chunk_reader, mime_type = _determine_chunk_reader( path )
    for chunk in await chunk_reader( auxdata, path ):
        messages: list[ Canister ] = [
            SupervisorCanister( ).add_content(
                supervisor_prompt.render( auxdata ) ) ]
        # TODO: Check if above high water mark for tokens count.
        #       Drop earliest messages from history, if so.
        if ai_messages:
            messages.append(
                UserCanister( )
                .add_content( summarization_prompt.render( auxdata ) ) )
            messages.append(
                AssistantCanister( )
                .add_content( '\n\n'.join( ai_messages ) ) )
        _, content = _render_analysis_prompt(
            context, control, chunk, mime_type )
        messages.append( UserCanister( ).add_content( content ) )
        ai_canister = await model.converse_v0(
            messages, { }, controls, conversation_reactors_minimal )
        # TODO: Handle combination of analysis and metadata.
        ai_messages.append( ai_canister[ 0 ].data )
    return ai_messages


async def _analyze_http( context, url, control = None ):
    file_name = await _read_http_core( context, url )
    return await _analyze_file( context, file_name, control = control )


async def _count_tokens( context, content ):
    model = context.supplements[ 'model' ]
    return await model.tokenizer.count_text_tokens( str( content ) )


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


async def _discriminate_dirents( context, dirents, control = None ):
    from ....messages import Canister, SupervisorCanister, UserCanister
    from ....providers import conversation_reactors_minimal
    auxdata = context.auxdata
    controls = context.supplements[ 'controls' ]
    model = context.supplements[ 'model' ]
    format_name = model.attributes.format_preferences.request_data.value
    prompt = (
        auxdata.prompts.definitions[ 'Discriminate Directory Entries' ]
        .produce_prompt( values = { 'format': format_name } ) )
    supervisor_message = prompt.render( auxdata )
    complete_result = [ ]
    # TODO: Python 3.12: itertools.batches
    batch_size = 70 # TODO: Base on output tokens limit.
    batches_count = len( dirents ) // batch_size + 1
    for batch_n in range( batches_count ):
        dirents_batch = dirents[
            ( batch_n * batch_size ) : ( ( batch_n + 1 ) * batch_size ) ]
        messages: list[ Canister ] = [
            SupervisorCanister( ).add_content( supervisor_message ) ]
        _, content = _render_analysis_prompt(
            context, control, dirents_batch, 'directory-entries' )
        messages.append( UserCanister( ).add_content( content ) )
        ai_canister = await model.converse_v0(
            messages, { }, controls, conversation_reactors_minimal )
        #ic( ai_canister[ 0 ].data )
        result = (
            model.serde_processor.deserialize_data( ai_canister[ 0 ].data ) )
        ic( result[ 'blacklist' ] )
        complete_result.extend( result[ 'whitelist' ] )
    return complete_result


async def _list_directory( context, path, control = None ):
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
            if FILE_SIZE_MAXIMUM < inode.st_size: continue
            dirents.append( dict(
                location = dirent_fqname,
                mime_type = from_file( dirent, mime = True ) ) )
    return await _discriminate_dirents( context, dirents, control = control )


async def _list_directory_as_cell( *posargs, **nomargs ):
    return [ await _list_directory( *posargs, **nomargs ) ]


async def _operate( context, source, operators, control = None ):  # noqa: PLR0911
    # TODO: Support wildcards.
    tokens_total = 0
    tokens_max = _access_tokens_limit( context ) * 3 // 4
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
        result = await operator( context, path, control = control )
        if operators.tokens_counter:
            tokens_total += operators.tokens_counter( context, result )
            if tokens_total > tokens_max:
                return (
                    f"Error: Input is {tokens_total} tokens in size, "
                    f"which exceeds the safe limit, {tokens_max}." )
        return result
    if components.scheme in ( 'http', 'https', ):
        return await operators.from_http( context, source, control = control )
    return f"Error: URL scheme, '{components.scheme}', not supported."


# TODO: Process stream.
async def _read_chunks_destructured( context, path ):
    tokens_max = _access_tokens_limit( context ) // 4
    blocks = [ ]
    tokens_total = 0
    hint = 'first chunk'
    from unstructured.partition.auto import partition
    for element in partition( filename = str( path ) ):
        tokens_count = await _count_tokens( context, element )
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
async def _read_chunks_naively( context, path ):
    tokens_max = _access_tokens_limit( context ) // 4
    lines = [ ]
    tokens_total = 0
    hint = 'first chunk'
    with path.open( ) as file:
        for line_number, line in enumerate( file, start = 1 ):
            tokens_count = await _count_tokens( context, line )
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


async def _read_http_core( context, url ):
    from tempfile import NamedTemporaryFile
    # TODO: Write to conversation cache with file name.
    # TODO? Pass stream to reader function rather than re-open tempfile.
    accessor = __.file_adapter_from_url( url )
    with NamedTemporaryFile( delete = False ) as file:
        file.write( await accessor.acquire_content( ) )
    return file.name


def _render_analysis_prompt( context, control, content, mime_type ):
    auxdata = context.auxdata
    model = context.supplements[ 'model' ]
    control = control or { }
    instructions = control.get( 'instructions', '' )
    if control.get( 'mode', 'supplement' ):
        instructions = (
            auxdata.prompts.definitions[ 'Analyze Content' ]
            .produce_prompt(
                values = dict(
                    mime_type = mime_type, instructions = instructions ) )
            .render( auxdata ) )
    return model.serde_processor.serialize_data(
        dict( content = content, instructions = instructions ) )
