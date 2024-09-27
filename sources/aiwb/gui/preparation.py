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


''' Preparation of GUI. '''


from . import __
from . import server as _server
from . import state as _state


@__.standard_dataclass
class Manager:
    ''' Manager for GUI components and server. '''

    components: __.SimpleNamespace
    server: _server.Accessor
    transformers: __.AccretiveDictionary


async def prepare(
    exits: __.ExitsAsync, *,
    apiserver: __.ApiServerControl = __.ApiServerControl( ),
    application: __.ApplicationInformation = __.ApplicationInformation( ),
    configedits: __.DictionaryEdits = ( ),
    configfile: __.Optional[ __.Url ] = __.absent,
    environment: bool = True,
    guiserver: _server.Control = _server.Control,
    inscription: __.InscriptionControl = (
        __.InscriptionControl( mode = __.InscriptionModes.Rich ) ),
) -> _state.Globals:
    ''' Prepares GUI. '''
    auxdata_base = await __.prepare_apiserver(
        apiserver = apiserver,
        application = application,
        configedits = configedits,
        configfile = configfile,
        environment = environment,
        exits = exits,
        inscription = inscription )
    components = await _prepare_components_base( auxdata_base )
    server = await _server.prepare(
        auxdata_base, components = components, control = guiserver )
    manager = Manager(
        components = components,
        server = server,
        transformers = __.AccretiveDictionary( ),
    )
    auxdata = _state.Globals.from_base( auxdata_base, gui = manager )
    components.auxdata__ = auxdata # Hack for legacy.
    await _prepare_components_complete( auxdata )
    return auxdata


async def _prepare_components_base(
    auxdata: __.ApiServerGlobals,
) -> __.SimpleNamespace:
    ''' Prepares foundation for GUI components tracker. '''
    # Designs and Themes: https://panel.holoviz.org/api/panel.theme.html
    from panel.theme import Native
    from .templates.default import DefaultTemplate
    template = DefaultTemplate( design = Native )
    await _prepare_favicon( auxdata, template = template )
    return __.SimpleNamespace( template__ = template )


async def _prepare_components_complete( auxdata: _state.Globals ):
    ''' Finishes preparation of GUI components tracker. '''
    from . import components
    from .updaters import populate_dashboard
    await components.prepare( auxdata )
    await populate_dashboard( auxdata )


async def _prepare_favicon(
    auxdata: __.ApiServerGlobals,
    template: __.a.Any, # TODO: Proper type.
):
    ''' Loads favicon for browser tab. '''
    # https://github.com/holoviz/panel/blob/2bacc0ee8162b962537ca8ba71fa302ba01a57f5/panel/template/base.py#L789-L792
    # https://news.ycombinator.com/item?id=30347043
    file = (
        await __.location_adapter_from_url(
            auxdata.distribution.provide_data_location(
                'icons/favicon-32.png' ) )
        .as_specific( species = __.LocationSpecies.File ) )
    icon = ( await file.acquire_content_bytes( ) ).content
    from base64 import b64encode
    icon_b64 = b64encode( icon ).decode( )
    icon_uri = f"data:image/png;base64,{icon_b64}"
    template.add_variable( 'app_favicon', icon_uri )
    template.add_variable( 'favicon_type', 'image/png' )
