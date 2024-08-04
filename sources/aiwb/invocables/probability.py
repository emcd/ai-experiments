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


''' Collection of AI functions related to probability. '''


from . import __


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
def roll_dice( context__, /, specs ):
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
