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


def prepare( configuration, directories ):
    from types import SimpleNamespace
    from .base import generate_component
    from .layouts import dashboard_layout as layout
    from .templates.default import DefaultTemplate
    from .updaters import populate_dashboard
    gui = SimpleNamespace( )
    gui.auxdata__ = prepare_auxdata( configuration, directories )
    gui.template__ = template = DefaultTemplate( )
    prepare_favicon( gui )
    generate_component( gui, layout, 'dashboard' )
    populate_dashboard( gui )
    return gui


# TODO: Support async loading.
def prepare_auxdata( configuration, directories ):
    from types import SimpleNamespace
    from ..ai.providers import prepare as prepare_ai_providers
    from ..ai.functions import prepare as prepare_ai_functions
    from ..prompts.core import prepare as prepare_prompt_definitions
    from ..vectorstores import prepare as prepare_vectorstores
    auxdata = SimpleNamespace(
        configuration = configuration, directories = directories )
    auxdata.ai_functions = prepare_ai_functions( configuration, directories )
    auxdata.ai_providers = prepare_ai_providers( configuration, directories )
    auxdata.prompt_definitions = prepare_prompt_definitions( auxdata )
    auxdata.vectorstores = prepare_vectorstores( configuration, directories )
    return auxdata # TODO: Return immutable namespace.


def prepare_favicon( gui ):
    from panel.pane import panel
    from panel.pane.image import ImageBase
    template = gui.template__
    path = gui.auxdata__.configuration[ 'main-path' ].joinpath(
        '.local/data/favicon-32.png' )
    image = panel( path )
    if not isinstance( image, ImageBase ):
        # TODO: Log warning.
        return
    # pylint: disable=protected-access
    favicon = image._b64( image._data( image.object ) )
    # pylint: enable=protected-access
    template.add_variable( 'app_favicon', favicon )
    template.add_variable( 'favicon_type', 'image/png' )
