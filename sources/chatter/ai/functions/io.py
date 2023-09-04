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
Reads a file and passes its contents to an AI to analyze according to a given
set of instructions. Returns the analysis of the file. ''',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'Path to the file to be read.'
            },
            'instructions': {
                'type': 'string',
                'description': 'Analysis instructions for AI.'
            },
        },
        'required': [ 'path', 'instructions' ],
    },
} )
def read_file( auxdata, /, path, instructions ):
    from ...messages import render_prompt_template
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
    cursor = dict( line_number = 1, offset = 0 )
    while cursor:
        chunk_info = read_file_chunk( auxdata, path, **cursor )
        messages = [ dict( content = supervisor_prompt, role = 'Supervisor' ) ]
        # TODO: Check if above high water mark for tokens count.
        #       Drop earliest messages from history, if so.
        if ai_messages:
            messages.append( dict(
                content = summarization_prompt, role = 'User' ) )
            messages.append( dict(
                content = '\n\n'.join( ai_messages ), role ='AI' ) )
        messages.append( dict(
            content = _render_read_file_prompt(
                auxdata, instructions, chunk_info[ 'lines' ] ),
            role = 'User' ) )
        from ..providers import ChatCallbacks
        callbacks = ChatCallbacks(
            allocator = ( lambda mime_type: [ ] ),
            updater = ( lambda handle, content: handle.append( content ) ),
        )
        handle = provider.chat( messages, { }, auxdata.controls, callbacks )
        ai_messages.append( ''.join( handle ) )
        cursor = {
            key: chunk_info[ key ] for key in ( 'line_number', 'offset', )
            if key in chunk_info
        }
    return ai_messages


def _render_read_file_prompt( auxdata, instructions, content ):
    from ...messages import render_prompt_template
    instructions_prompt_template = auxdata.prompt_templates.canned[
        'Instructions + Content' ][ 'template' ]
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    content = provider.render_as_preferred_structure(
        content, auxdata.controls )
    return render_prompt_template(
        instructions_prompt_template,
        controls = auxdata.controls,
        variables = dict( content = content, instructions = instructions ) )


@__.register_function( {
    'name': 'read_file_chunk',
    'description': '''
Reads no more than the specified number of tokens from a file, starting from
an optional line number and byte offset. Returns an ordered mapping of line
numbers to lines. If a line would be truncated by the tokens limit, then it is
not included in the results and its number and byte offset are also returned.
This allows for paginated iteration over a file with subsequent function
calls. If no line number and offset are returned, then end of file has been
reached. ''',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'Path to the file to be read.'
            },
            'offset': {
                'type': 'integer',
                'description': 'File position from which to start reading.',
                'default': 0
            },
            'line_number': {
                'type': 'integer',
                'description': 'Line number corresponding to offset.',
                'default': 1
            },
            'tokens_max': {
                'type': 'integer',
                'description': 'Maximum number of tokens to read.',
                'default': 1024
            },
        },
        'required': [ 'path' ],
    },
} )
def read_file_chunk(
    auxdata, /, path, offset = 0, line_number = 1, tokens_max = 1024
):
    provider = auxdata.ai_providers[ auxdata.controls[ 'provider' ] ]
    model_name = auxdata.controls[ 'model' ]
    from itertools import count
    lines = { }
    tokens_total = 0
    with open( path, 'rb' ) as file:
        file.seek( offset )
        for line_number in count( line_number ):
            line = file.readline( ).decode( )
            if not line: return dict( lines = lines )
            tokens_count = provider.count_text_tokens( line, model_name )
            if tokens_max < tokens_total + tokens_count: break
            tokens_total += tokens_count
            offset = file.tell( )
            lines[ line_number ] = line
    return dict(
        lines = lines, line_number = line_number + 1, offset = offset )


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
})
def write_file( auxdata, /, path, contents, mode = 'truncate' ):
    with open( path, { 'append': 'a', 'truncate': 'w' }[ mode] ) as file:
        return file.write( contents )
