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


''' Data structures and utilities for API server. '''


from __future__ import annotations

from . import __


class Accessor(
    __.immut.DataclassObject
):
    ''' Accessor for server properties and thread. '''

    components: __.SimpleNamespace
    control: Control

    async def execute( self, auxdata: __.ApiServerGlobals ):
        ''' Runs server in thread. '''
        await auxdata.exits.enter_async_context(
            _execute_server_thread(
                components = self.components,
                control = self.control ) )


class Control(
    __.immut.DataclassObject
):
    ''' Binding address and port, etc... for server. '''

    address: str = '127.0.0.1'
    port: int = 0
    reload: bool = False

    def with_address_and_port( self, address: str, port: int ) -> __.a.Self:
        ''' Returns new instance with mutated address and port. '''
        # TODO: Generic 'with_attributes' method.
        return type( self )(
            address = address, port = port, reload = self.reload )


@__.exit_manager_async
async def _execute_server_thread(
    components: __.SimpleNamespace, control: Control
) -> __.AbstractGenerator:
    scribe = __.acquire_scribe( __package__ )
    from asyncio import get_running_loop, sleep
    loop = get_running_loop( )
    scribe.info( "Waiting for GUI server to start." )
    thread = await loop.run_in_executor(
        None, _start_gui, components, control )
    while not thread.is_alive( ): await sleep( 0.001 )
    yield thread
    scribe.info( "Waiting for GUI server to stop." )
    thread.stop( )
    thread.join( )


def _start_gui(
    components: __.SimpleNamespace, control: Control
) -> __.a.Any: # TODO: Proper type.
    # TODO: Honor address and port for listener socket binding.
    return components.template__.show(
        autoreload = control.reload,
        threaded = True,
        title = 'AI Workbench' )
