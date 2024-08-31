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


''' Core entities for use with workbench GUI. '''


from . import __
from .. import appcore as _appcore


@__.dataclass( frozen = True, kw_only = True, slots = True )
class Globals( _appcore.Globals ):
    ''' Immutable global data. Required by many GUI functions. '''

    api: __.AccretiveDictionary
    gui: __.AccretiveDictionary

    @classmethod
    async def prepare( selfclass, base: _appcore.Globals ) -> __.a.Self:
        ''' Acquires data to create DTO. '''
        from asyncio import gather # TODO: Python 3.11: TaskGroup
        from dataclasses import fields
        from importlib import import_module
        preparers = dict(
            api = import_module( '.server', __package__ ).prepare( base ),
            gui = _prepare_server( base ) )
        attributes = await gather( *preparers.values( ) )
        instance = selfclass(
            **{ field.name: getattr( base, field.name )
                for field in fields( base ) },
            **dict( zip( preparers.keys( ), attributes ) ) )
        instance.gui.components.auxdata__ = instance # Hack for legacy.
        await _prepare_server_complete( instance )
        return instance


async def prepare( exits: __.Exits ) -> Globals:
    ''' Prepares everything related to the GUI. '''
    auxdata_base = await _appcore.prepare( exits = exits )
    return await Globals.prepare( auxdata_base )


async def _prepare_favicon( auxdata: Globals ):
    # https://github.com/holoviz/panel/blob/2bacc0ee8162b962537ca8ba71fa302ba01a57f5/panel/template/base.py#L789-L792
    # https://news.ycombinator.com/item?id=30347043
    from base64 import b64encode
    from aiofiles import open as open_
    path = auxdata.distribution.provide_data_location( 'icons/favicon-32.png' )
    async with open_( path, 'rb' ) as stream:
        icon = await stream.read( )
    icon_b64 = b64encode( icon ).decode( )
    icon_uri = f"data:image/png;base64,{icon_b64}"
    template = auxdata.gui.components.template__
    template.add_variable( 'app_favicon', icon_uri )
    template.add_variable( 'favicon_type', 'image/png' )


async def _prepare_server( auxdata: _appcore.Globals ):
    ''' Prepares GUI server foundation. '''
    # Designs and Themes: https://panel.holoviz.org/api/panel.theme.html
    from panel.theme import Native
    from .templates.default import DefaultTemplate
    server = __.AccretiveNamespace( )
    server.components = __.SimpleNamespace(
        template__ = DefaultTemplate( design = Native ) )
    return server


async def _prepare_server_complete( auxdata: Globals ):
    ''' Finishes preparation of GUI server. '''
    from asyncio import gather # TODO: Python 3.11: TaskGroup
    from . import components
    from .updaters import populate_dashboard
    await gather(
        _prepare_favicon( auxdata ),
        components.prepare( auxdata ) )
    await populate_dashboard( auxdata )
