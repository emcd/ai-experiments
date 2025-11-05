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


''' Available probability calculations. '''


from . import __
from . import exceptions as _exceptions


DICE_SIDES_MINIMUM = 4


async def roll_dice(
    context: __.Context, arguments: __.Arguments
) -> __.cabc.Sequence:
    ''' Returns results of rolls for each named dice specification. '''
    return tuple(
        { spec[ 'name' ]: _roll_dice( spec[ 'dice' ] ) }
        for spec in arguments[ 'specs' ] )


def _roll_dice( dice ):
    import re
    from random import randint
    regex = re.compile(
        r'''(?P<number>\d+)d(?P<sides>\d+)(?P<offset>[+\-]\d+)?''' )
    match = regex.match( dice )
    if not match:
        raise _exceptions.DiceSpecificationInvalidity(
            dice, "does not match format" )
    number = int( match.group( 'number' ) )
    sides = int( match.group( 'sides' ) )
    offset = match.group( 'offset' )
    offset = int( offset ) if offset else 0
    if (    number < 1 or sides < DICE_SIDES_MINIMUM
            or sides % 2 == 1 or number + offset < 1
    ):
        raise _exceptions.DiceSpecificationInvalidity(
            dice, "invalid constraints" )
    return sum(
        randint( 1, sides )
        for _ in range( number ) ) + offset
