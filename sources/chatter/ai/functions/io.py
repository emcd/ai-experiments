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
    context__, /, path, offset = 0, line_number = 1, tokens_max = 1024
):
    from ..providers import registry as providers
    provider = providers[ context__[ 'provider' ] ]
    model_name = context__[ 'model' ]
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
def write_file( context__, /, path, contents, mode = 'truncate' ):
    with open( path, { 'append': 'a', 'truncate': 'w' }[ mode] ) as file:
        return file.write( contents )
