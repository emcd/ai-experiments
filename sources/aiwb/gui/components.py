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


''' Customization of Holoviz Panel GUI components. '''


from . import __
from . import state as _state


def generate( components, layout, component_name ):
    ''' Recursively generates components from layout specification. '''
    entry = layout[ component_name ]
    elements = [ ]
    for element_name in entry.get( 'contains', ( ) ):
        elements.append( generate( components, layout, element_name ) )
    if entry.get( 'virtual', False ): return None
    component_class = entry[ 'component_class' ]
    component_arguments = entry.get( 'component_arguments', { } )
    auxdata = (
        components.auxdata__ if hasattr( components, 'auxdata__' )
        else components.parent__.auxdata__ )
    for transformer in auxdata.gui.transformers.values( ):
        component_class, component_arguments = (
            transformer( auxdata, component_class, component_arguments ) )
    component = component_class( *elements, **component_arguments )
    setattr( components, component_name, component )
    interpolant_id = entry.get( 'interpolant_id' )
    if interpolant_id:
        components.template__.add_panel( interpolant_id, component )
    return component


async def populate( components, layout, component_name ):
    ''' Recursively populates components with values. '''
    from . import updaters as registry
    entry = layout[ component_name ]
    # TODO: Parallel fanout once we can guarantee dependency ordering.
    #populators = (
    #    populate( components, layout, element_name )
    #    for element_name in entry.get( 'contains', ( ) ) )
    #await __.gather_async( *populators )
    for element_name in entry.get( 'contains', ( ) ):
        await populate( components, layout, element_name )
    function_name = entry.get( 'populator_function' )
    if None is function_name: return
    function = getattr( registry, function_name )
    await function( components )


async def prepare( auxdata: _state.Globals ):
    ''' Registers component inspectors and transformers. '''
    await _prepare_icons_cache( auxdata )
    _register_transformers( auxdata )


def register_event_reactors( components, layout, component_name ):
    ''' Recursively registers callbacks for components. '''
    from . import events as registry
    entry = layout[ component_name ]
    for element_name in entry.get( 'contains', ( ) ):
        register_event_reactors( components, layout, element_name )
    if not hasattr( components, component_name ): return
    component = getattr( components, component_name )
    functions = entry.get( 'event_functions', { } )
    for event_name, function_name in functions.items( ):
        function = __.partial_function(
            getattr( registry, function_name ), components )
        if 'on_click' == event_name:
            component.on_click( function )
            continue
        component.param.watch( function, event_name )
    function_name = entry.get( 'javascript_cb_generator' )
    if function_name:
        cb_generator = getattr( registry, function_name )
        component.jscallback(
            **cb_generator( components, layout, component_name ) )


_icons_cache = __.AccretiveDictionary( )
async def _prepare_icons_cache( auxdata ):
    directory = auxdata.distribution.provide_data_location( 'icons' )
    files = tuple( directory.glob( '*.svg' ) )
    icons = await __.read_files_async( *files )
    _icons_cache.update( zip( ( file.stem for file in files ), icons ) )


def _register_transformers( auxdata ):
    auxdata.gui.transformers.update( {
        name: transformer for name, transformer
        in (
            ( 'use-local-icon', _use_local_icon ),
            #( 'transform-font', _transform_font ),
        )
    } )


def _transform_font( auxdata, class_, arguments ):
    from panel.layout import Column, Row
    from panel.pane import Markdown
    from panel.reactive import ReactiveHTML
    styles = arguments.get( 'styles', { } )
    if 'font-family' in styles: pass # Respect explicit configuration.
    elif issubclass( class_, ( Column, Row ) ): pass
    # TODO: Analyze auxiliary attributes in component arguments.
    #       If 'use-special-fonts' absent, then apply sans serif fonts.
    elif not issubclass( class_, ( Markdown, ReactiveHTML ) ):
        styles[ 'font-family' ] = 'var(--sans-serif-fonts)'
        arguments[ 'styles' ] = styles
    return class_, arguments


def _use_local_icon( auxdata, class_, arguments ):
    icon = arguments.get( 'icon' )
    if None is icon: pass
    elif icon.startswith( '<svg' ) and icon.endswith( '</svg>' ): pass
    elif icon in _icons_cache: arguments[ 'icon' ] = _icons_cache[ icon ]
    return class_, arguments
