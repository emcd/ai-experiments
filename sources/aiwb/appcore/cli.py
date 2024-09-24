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


''' CLI for configuring, inspecting, and testing application. '''


from __future__ import annotations

from . import __


@__.standard_dataclass
class Cli( __.Cli ):
    ''' Utility for inspection and tests of library core. '''

    # TODO: Add configuration injectors.


def execute_cli( ):
    from asyncio import run
    config = (
        #__.tyro.conf.OmitSubcommandPrefixes,
        __.tyro.conf.SelectFromEnumValues,
    )
    default = Cli(
        application = __.ApplicationInformation( ),
        display = __.CliConsoleDisplay( ),
        inscription = __.InscriptionControl( mode = __.InscriptionModes.Rich ),
        command = __.CliInspectCommand( ),
    )
    run( __.tyro.cli( Cli, config = config, default = default )( ) )
