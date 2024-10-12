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


''' CLI for executing, inspecting, and testing API server. '''


from __future__ import annotations

from . import __
from . import server as _server
from . import state as _state


@__.standard_dataclass
class Cli( __.ApplicationCli ):
    ''' CLI for execution, inspection, and tests of API server. '''

    apiserver: _server.Control = _server.Control( )
    command: __.a.Union[
        __.a.Annotation[
            __.CoreCliInspectCommand,
            __.tyro.conf.subcommand( 'inspect', prefix_name = False ),
        ],
        __.a.Annotation[
            ExecuteServerCommand,
            __.tyro.conf.subcommand( 'execute', prefix_name = False ),
        ],
    ]

    async def __call__( self ):
        ''' Invokes command after API server preparation. '''
        nomargs = self.prepare_invocation_args( )
        from .preparation import prepare
        async with __.ExitsAsync( ) as exits:
            auxdata = await prepare( exits = exits, **nomargs )
            await self.command( auxdata = auxdata, display = self.display )

    def prepare_invocation_args(
        self,
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        args = __.ApplicationCli.prepare_invocation_args( self )
        args[ 'apiserver' ] = self.apiserver
        return args


@__.standard_dataclass
class ExecuteServerCommand( __.ApplicationCliExecuteServerCommand ):
    ''' Runs API server until signal. '''

    async def __call__(
        self,
        auxdata: _state.Globals,
        display: __.CliConsoleDisplay,
    ):
        scribe = __.acquire_scribe( __package__ )
        await self.execute_until_signal(
            auxdata = auxdata, display = display, scribe = scribe )


def execute_cli( ):
    from asyncio import run
    config = (
        #__.tyro.conf.OmitSubcommandPrefixes,
        __.tyro.conf.EnumChoicesFromValues,
    )
    default = Cli(
        application = __.ApplicationInformation( ),
        configuration = __.ApplicationCliConfigurationModifiers( ),
        display = __.CliConsoleDisplay( ),
        inscription = __.InscriptionControl( mode = __.InscriptionModes.Rich ),
        command = ExecuteServerCommand( ),
    )
    run( __.tyro.cli( Cli, config = config, default = default )( ) )
