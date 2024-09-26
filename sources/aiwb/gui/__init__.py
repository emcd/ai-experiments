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


''' GUI with Holoviz Panel widgets. '''


from . import __
from . import core


def main( ):
    ''' Prepares and executes GUI. '''
    # Note: Cannot be async because Hatch does not support async entrypoints.
    # TODO? aiomisc.entrypoint
    from asyncio import run
    run( _main( ) )


async def _main( ):
    # TODO: Setup API and GUI servers in context manager.
    scribe = __.acquire_scribe( __package__ )
    from asyncio import Future, get_running_loop, sleep
    from signal import SIGINT, SIGTERM
    loop = get_running_loop( )
    signal_future = Future( )

    def handler( signum ):
        scribe.info( f"Received signal {signum.name!r} ({signum.value!r})." )
        signal_future.set_result( signum )

    async with __.ExitsAsync( ) as exits:
        auxdata = await core.prepare( exits = exits )
        api = auxdata.api
        api.thread.start( )
        try:
            scribe.info( "Waiting for API server to start." )
            while not api.server.started: await sleep( 0.001 )
            scribe.info( "Waiting for GUI server to start." )
            gui_thread = (
                await loop.run_in_executor( None, _start_gui, auxdata ) )
        except Exception:
            # TODO: Notify of error.
            _stop_api( auxdata )
            return
        for signum in ( SIGINT, SIGTERM, ):
            loop.add_signal_handler( signum, handler, signum )
        try: await signal_future
        # TODO: Notify of error.
        finally:
            scribe.info( "Waiting for GUI server to stop." )
            gui_thread.stop( )
            _stop_api( auxdata )


def _start_gui( auxdata ):
    return auxdata.gui.components.template__.show(
        autoreload = True, threaded = True, title = 'AI Workbench' )

def _stop_api( auxdata ):
    scribe = __.acquire_scribe( __package__ )
    scribe.info( "Waiting for API server to stop." )
    api = auxdata.api
    api.server.should_exit = True
    api.thread.join( )


__.reclassify_modules( globals( ) )
__class__ = __.AccretiveModule


if '__main__' == __name__: main( )
