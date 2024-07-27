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


''' GUI with Panel widgets. '''


from . import __


def main( ):
    ''' Prepares and executes GUI. '''
    # Note: Cannot be async because Hatch does not support async entrypoints.
    #       Also, the Bokeh Tornado server used by Panel has problems
    #       launching from inside an async caller.
    # TODO? aiomisc.entrypoint
    from asyncio import run
    from time import sleep
    auxdata = run( prepare( ) )
    components = auxdata.gui.components
    server_context = auxdata.gui.server_context
    server_context.thread.start( )
    try:
        while not server_context.server.started: sleep( 0.001 )
        components.template__.show( autoreload = True, title = 'AI Workbench' )
    finally:
        server_context.server.should_exit = True
        server_context.thread.join( )


async def prepare( ) -> __.AccretiveNamespace:
    ''' Prepares everything related to the GUI. '''
    from asyncio import gather # TODO: Python 3.11: TaskGroup
    from ..core import prepare as prepare_core
    from .base import generate_component
    from .components import prepare as prepare_components
    from .layouts import dashboard_layout as layout
    from .server import prepare as prepare_server
    from .updaters import populate_dashboard
    auxdata = await prepare_core( )
    auxdata.gui = gui = __.AccretiveNamespace( )
    await gather( *(
        preparer( auxdata ) for preparer
        in ( prepare_components, prepare_server, _prepare_favicon ) ) )
    generate_component( gui.components, layout, 'dashboard' )
    populate_dashboard( gui.components )
    return auxdata


async def _prepare_favicon( auxdata ):
    # https://github.com/holoviz/panel/blob/2bacc0ee8162b962537ca8ba71fa302ba01a57f5/panel/template/base.py#L789-L792
    # https://news.ycombinator.com/item?id=30347043
    from base64 import b64encode
    from aiofiles import open as open_async
    path = auxdata.distribution.location / 'data/icons/favicon-32.png'
    async with open_async( path, 'rb' ) as stream:
        icon = await stream.read( )
    icon_b64 = b64encode( icon ).decode( )
    icon_uri = f"data:image/png;base64,{icon_b64}"
    template = auxdata.gui.components.template__
    template.add_variable( 'app_favicon', icon_uri )
    template.add_variable( 'favicon_type', 'image/png' )


if '__main__' == __name__: main( )
