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


def prepare( configuration, directories, ai_functions, vectorstores ):
    from types import SimpleNamespace
    from .callbacks import (
        generate_component,
        populate_dashboard,
        register_dashboard_callbacks,
    )
    from .layouts import dashboard_layout as layout
    components = { }
    generate_component( components, layout, 'dashboard' )
    gui = SimpleNamespace( **components )
    gui.auxdata__ = {
        'ai-functions': ai_functions,
        'configuration': configuration,
        'directories': directories,
        'vectorstores': vectorstores,
    }
    populate_dashboard( gui )
    register_dashboard_callbacks( gui )
    return gui
