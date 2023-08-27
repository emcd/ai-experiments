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


''' Collection of AI functions.

    (Temporary home for proof-of-concept. Will load definitions from separate
    directories in the longer term.) '''


from . import base as __
from .base import survey_functions


@__.register_function( {
    'name': 'roll_dice',
    'description': '''
Given a list of name and specification pairs for dice rolls,
returns a list with the results of each roll, associated with its name. ''',
    'parameters': {
        'type': 'object',
        'properties': {
            'specs': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': '''
Name of the dice roll. Note that this may be duplicate across list items. This
allows for scenarios, like D&D ability scores, where more than one independent
roll may be used to determine the same score. '''
                        },
                        'dice': {
                            'type': 'string',
                            'description': '''
A dice specification, such as '1d10' or '3d6+2'. The pattern comprises the
number of dice, the type of dice (i.e., the number of sides, which must be even
and greater than 3), and an optional offset which can be positive or negative.
The offset is added to the total roll of the dice and does not have an upper
limit, but a negative offset must not reduce the total roll to less than 1. For
instance, '1d4-1' is illegal because a roll of 1 would result in a total value
of 0. '''
                        },
                    },
                    'required': [ 'name', 'dice' ],
                },
                'minItems': 1,
            }
        },
        'required': [ 'specs' ],
    }
} )
def roll_dice( specs ):
    results = [ ]
    for spec in specs:
        results.append( { spec[ 'name' ]: _roll_dice( spec[ 'dice' ] ) } )
    return results


def _roll_dice( dice ):
    import re
    from random import randint
    regex = re.compile(
        r'''(?P<number>\d+)d(?P<sides>\d+)(?P<offset>[+\-]\d+)?''' )
    match = regex.match( dice )
    if not match: raise ValueError( f"Invalid dice spec, '{dice}'." )
    number = int( match.group( 'number' ) )
    sides = int( match.group( 'sides' ) )
    offset = match.group( 'offset' )
    offset = int( offset ) if offset else 0
    if number < 1 or sides < 4 or sides % 2 == 1 or number + offset < 1:
        raise ValueError( f"Invalid dice spec, '{dice}'." )
    return sum( randint( 1, sides ) for _ in range( number ) ) + offset


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
def read_file_chunk( path, offset = 0, line_number = 1, tokens_max = 1024 ):
    from itertools import count
    from ...messages import count_tokens
    lines = { }
    tokens_total = 0
    with open( path, 'rb' ) as file:
        file.seek( offset )
        for line_number in count( line_number ):
            line = file.readline( ).decode( )
            if not line: return dict( lines = lines )
            tokens_count = count_tokens( line )
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
def write_file( path, contents, mode = 'truncate' ):
    with open( path, { 'append': 'a', 'truncate': 'w' }[ mode] ) as file:
        return file.write( contents )
