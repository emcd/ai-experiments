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


''' Standard ensemble for I/O. '''


from __future__ import annotations

from . import __
from .read import analyze, analyze_model, read, read_model
from .write import write_file, write_file_model


_name = __package__.rsplit( '.', maxsplit = 1 )[ -1 ]


async def prepare(
    auxdata: __.Globals,
    descriptor: __.AbstractDictionary[ str, __.a.Any ],
) -> Ensemble:
    ''' Installs dependencies and returns ensemble. '''
    # TODO: Install dependencies: aiohttp / httpx, github, etc....
    return Ensemble( name = _name )


__.preparers[ _name ] = prepare


@__.standard_dataclass
class Ensemble( __.Ensemble ):

    async def prepare_invokers(
        self, auxdata: __.Globals
    ) -> __.AbstractDictionary[ str, __.Invoker ]:
        # TODO: Use any filter information from descriptor for registration.
        invokers = (
            __.Invoker.from_invocable(
                ensemble = self, invocable = invocable, model = model )
            for invocable, model in _invocables )
        return __.DictionaryProxy( {
            invoker.name: invoker for invoker in invokers } )


_invocables = (
    ( analyze, analyze_model ),
    ( read, read_model ),
    ( write_file, write_file_model ),
)
