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


from . import __


class Accessor( __.immut.DataclassObject ):
    ''' Accessor for server properties and thread. '''

    components: __.types.SimpleNamespace
    control: 'Control'

    async def execute( self, auxdata: __.ApiServerGlobals ):
        ''' Runs server in thread. '''
        await auxdata.exits.enter_async_context(
            _execute_server_thread(
                components = self.components,
                control = self.control ) )


class Control( __.immut.DataclassObject ):
    ''' Binding address and port, etc... for server. '''

    address: __.typx.Annotated[
        str, __.tyro.conf.arg( name = 'gui-address', prefix_name = False )
    ] = '127.0.0.1'
    open_browser: __.typx.Annotated[
        bool, __.tyro.conf.arg( prefix_name = False )
    ] = True
    port: __.typx.Annotated[
        int, __.tyro.conf.arg( name = 'gui-port', prefix_name = False )
    ] = 0
    reload: __.typx.Annotated[
        bool, __.tyro.conf.arg( name = 'gui-reload', prefix_name = False )
    ] = False

    def with_address_and_port( self, address: str, port: int ) -> __.typx.Self:
        ''' Returns new instance with mutated address and port. '''
        # TODO: Generic 'with_attributes' method.
        return type( self )(
            address = address, port = port,
            open_browser = self.open_browser, reload = self.reload )


@__.ctxl.asynccontextmanager
async def _execute_server_thread(
    components: __.types.SimpleNamespace, control: Control
) -> __.cabc.AsyncGenerator:
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
    components: __.types.SimpleNamespace, control: Control
) -> __.typx.Any: # TODO: Proper type.
    return components.template__.show(
        address = control.address,
        autoreload = control.reload,
        open = control.open_browser,
        port = control.port,
        threaded = True,
        title = 'AI Workbench' )
