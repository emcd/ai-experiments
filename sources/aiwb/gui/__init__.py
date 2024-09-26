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
    from asyncio import get_running_loop, sleep
    loop = get_running_loop( )
    #async with __.ExitsAsync( ) as exits:
    with __.Exits( ) as exits:
        auxdata = await core.prepare( exits = exits )
        api = auxdata.api
        api.thread.start( )
        try:
            while not api.server.started: await sleep( 0.001 )
            gui_thread = (
                await loop.run_in_executor( None, _start_gui, auxdata ) )
        except Exception:
            _stop_api( auxdata )
            return
        try:
            while True: await sleep( 0.5 )
        finally:
            gui_thread.stop( )
            _stop_api( auxdata )


def _start_gui( auxdata ):
    return auxdata.gui.components.template__.show(
        autoreload = True, threaded = True, title = 'AI Workbench' )

def _stop_api( auxdata ):
    api = auxdata.api
    api.server.should_exit = True
    api.thread.join( )


__.reclassify_modules( globals( ) )
__class__ = __.AccretiveModule


if '__main__' == __name__: main( )
