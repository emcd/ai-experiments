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


''' Collection of AI functions for I/O. '''


from . import base as __


@__.register_function( {
    'name': 'read_file',
    'description': '''
Reads a file and passes its contents to an AI agent to analyze according to a
given set of instructions. Returns the analysis of the file. ''',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'Path to the file to be read.'
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
        'required': [ 'path' ],
    },
} )
# TODO: Process URI rather than just path.
def read_file( auxdata, /, path, control = None ):
    from chatter.messages import render_prompt_template
    ai_messages = [ ]
    summarization_prompt = render_prompt_template(
        auxdata.prompt_templates.canned[
            'Concatenate: AI Responses' ][ 'template' ],
        controls = auxdata.controls )
    supervisor_prompt = render_prompt_template(
        auxdata.prompt_templates.system[
            'Automation: File Analysis' ][ 'template' ],
        controls = auxdata.controls )
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
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
        messages.append( dict(
            content = _render_prompt( auxdata, control, chunk, mime_type ),
            role = 'User' ) )
        from chatter.ai.providers import ChatCallbacks
        callbacks = ChatCallbacks(
            allocator = ( lambda mime_type: [ ] ),
            updater = ( lambda handle, content: handle.append( content ) ),
        )
        handle = provider.chat( messages, { }, auxdata.controls, callbacks )
        ai_messages.append( ''.join( handle ) )
    return ai_messages


@__.register_function( {
    'name': 'write_file',
    'description': '''
Writes provided contents to the given file. Returns the number of characters
written. ''',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'Path to the file to be written.'
            },
            'contents': {
                'type': 'string',
            },
            'mode': {
                'type': 'string',
                'enum': [ 'append', 'truncate' ],
                'default': 'truncate',
            },
        },
        'required': [ 'path', 'contents' ],
    },
} )
def write_file( auxdata, /, path, contents, mode = 'truncate' ):
    with open( path, { 'append': 'a', 'truncate': 'w' }[ mode] ) as file:
        return file.write( contents )


# TODO: Process path, URI, or bytes buffer.
def _determine_chunk_reader( path, mime_type = None ):
    from magic import from_file
    # TODO? Consider encoding.
    if not mime_type: mime_type = from_file( path, mime = True )
    if mime_type.startswith( 'text/x-script' ): reader = _read_chunks_naively
    elif mime_type in ( 'text/x-python', ): reader = _read_chunks_naively
    else: reader = _read_chunks_destructured
    ic( path, mime_type )
    return reader, mime_type


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


def _render_prompt( auxdata, control, content, mime_type ):
    from .prompts import select_default_instructions
    control = control or { }
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    instructions = control.get( 'instructions', '' )
    if control.get( 'mode', 'supplement' ):
        instructions = ' '.join( filter( None, (
            select_default_instructions( mime_type ), instructions ) ) )
    return provider.render_as_preferred_structure(
        dict( content = content, instructions = instructions ),
        auxdata.controls )
