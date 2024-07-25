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


def entrypoint( ):
    ''' Schedules main function with an event loop. '''
    # TODO: Enable event loop execution once we can support it.
    #       Probably after a migration off of Panel.
    # TODO: Consider 'aiomisc.entrypoint'.
    #from asyncio import get_event_loop
    #return get_event_loop( ).run_until_complete( main( ) )
    return main( )


def main( ):
    ''' Prepares and executes GUI. '''
    from .. import core
    auxdata = core.prepare( )
    gui = prepare( auxdata )
    gui.template__.show( autoreload = True, title = 'AI Workbench' )
    return 0


def prepare( auxdata ) -> __.SimpleNamespace:
    ''' Prepares everything related to the GUI. '''
    # Designs and Themes: https://panel.holoviz.org/api/panel.theme.html
    from panel.theme import Native
    from . import components
    from .base import generate_component
    from .layouts import dashboard_layout as layout
    from .templates.default import DefaultTemplate
    from .updaters import populate_dashboard
    auxdata.gui = __.AccretiveNamespace( )
    components.prepare( auxdata )
    gui = __.SimpleNamespace( auxdata__ = auxdata )
    gui.template__ = DefaultTemplate( design = Native )
    _prepare_favicon( gui )
    generate_component( gui, layout, 'dashboard' )
    populate_dashboard( gui )
    return gui


def _prepare_favicon( gui ):
    from panel.pane import panel
    from panel.pane.image import ImageBase
    template = gui.template__
    path = gui.auxdata__.distribution.location / 'data/icons/favicon-32.png'
    image = panel( path )
    if not isinstance( image, ImageBase ):
        # TODO: Log warning.
        return
    # pylint: disable=protected-access
    favicon = image._b64( image._data( image.object ) )
    # pylint: enable=protected-access
    template.add_variable( 'app_favicon', favicon )
    template.add_variable( 'favicon_type', 'image/png' )


if '__main__' == __name__: entrypoint( )
