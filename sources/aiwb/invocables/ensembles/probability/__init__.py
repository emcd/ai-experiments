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


''' Standard ensemble for probability. '''

# ruff: noqa: F401,F403
# pylint: disable=unused-import


from __future__ import annotations

from . import __
from .argschemata import named_dice_specs_argschema
from .calculations import roll_dice


_name = __package__.rsplit( '.', maxsplit = 1 )[ -1 ]


async def prepare(
    auxdata: __.Globals,
    descriptor: __.AbstractDictionary[ str, __.a.Any ],
) -> Ensemble:
    ''' Returns ensemble. '''
    return Ensemble( name = _name )

__.preparers[ _name ] = prepare


@__.standard_dataclass
class Ensemble( __.Ensemble ):

    async def prepare_invokers(
        self, auxdata: __.Globals
    ) -> __.AbstractDictionary[ str, __.Invoker ]:
        return self.produce_invokers_from_registry( auxdata, _invocables )


_invocables = (
    ( roll_dice, named_dice_specs_argschema ),
)


__.reclassify_modules( globals( ) )
