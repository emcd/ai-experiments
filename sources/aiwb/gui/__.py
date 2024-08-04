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


''' Common constants, imports, and utilities for GUI. '''

# pylint: disable=unused-import


from ..__ import *


scribe = acquire_scribe( __package__ ) # TODO: Not on module import.


roles_emoji = {
    'AI': '🤖',
    'Document': '📄',
    'Function': '\N{Hammer and Wrench}\uFE0F',
    'Human': '🧑',
}

roles_styles = {
    # TODO: Use style variables.
    'AI': {
        'background-color': 'WhiteSmoke',
    },
    'Document': {
        'background-color': 'White',
        'border-top': '2px dashed LightGray',
        'padding': '3px',
    },
    'Function': {
        'background-color': 'White',
        #'border-top': '2px dashed LightGray',
        #'padding': '3px',
    },
    'Human': {
        'background-color': 'White',
    },
}


def access_ai_provider_current( gui ):
    # TODO: Move to aiwb.gui.providers.
    return gui.auxdata__.providers[ gui.selector_provider.value ]


def assimilate_canister_dto_from_gui( canister_gui ):
    # TODO: Move to aiwb.gui.messages.
    dto = canister_gui.canister__
    behaviors = [ ]
    for behavior in ( 'active', 'pinned' ):
        if getattr( canister_gui, f"toggle_{behavior}" ).value:
            behaviors.append( behavior )
    dto.attributes.behaviors = behaviors
    # TODO: Implement full array support.
    dto[ 0 ].data = canister_gui.text_message.object


def assimilate_canister_dto_to_gui( canister_gui ):
    # TODO: Move to aiwb.gui.messages.
    dto = canister_gui.canister__
    # TODO: Implement full array support.
    canister_gui.text_message.object = dto[ 0 ].data
    behaviors = getattr( dto.attributes, 'behaviors', [ ] )
    for behavior in ( 'active', 'pinned' ):
        value = behavior in behaviors
        getattr( canister_gui, f"toggle_{behavior}" ).value = value


def calculate_conversations_path( gui ):
    # TODO: Use aiwb.messages.DirectoryManager instead.
    configuration = gui.auxdata__.configuration
    directories = gui.auxdata__.directories
    state_path = Path( configuration[ 'locations' ][ 'state' ].format(
        user_state = directories.user_state_path ) )
    return state_path / 'conversations'


def extract_invocation_requests( gui, component = None ):
    # TODO: Move to aiwb.gui.invocables.
    if None is component: component = gui.column_conversation_history[ -1 ]
    canister = component.gui__.canister__
    # TODO: Use selected multichoice values instead of all possible.
    ai_functions = gui.auxdata__.invocables
    auxdata = SimpleNamespace(
        controls = package_controls( gui ), **gui.auxdata__.__dict__ )
    provider = access_ai_provider_current( gui )
    return provider.extract_invocation_requests(
        canister, auxdata, ai_functions )


def generate_component( gui, layout, component_name ):
    # TODO: Move to aiwb.gui.components.
    entry = layout[ component_name ]
    elements = [ ]
    for element_name in entry.get( 'contains', ( ) ):
        elements.append( generate_component( gui, layout, element_name ) )
    if entry.get( 'virtual', False ): return None
    component_class = entry[ 'component_class' ]
    component_arguments = entry.get( 'component_arguments', { } )
    auxdata = (
        gui.auxdata__ if hasattr( gui, 'auxdata__' )
        else gui.parent__.auxdata__ )
    for transformer in auxdata.gui.transformers.values( ):
        component_class, component_arguments = (
            transformer( auxdata, component_class, component_arguments ) )
    component = component_class( *elements, **component_arguments )
    setattr( gui, component_name, component )
    interpolant_id = entry.get( 'interpolant_id' )
    if interpolant_id: gui.template__.add_panel( interpolant_id, component )
    return component


def package_controls( gui ):
    # TODO: Move to aiwb.gui.controls.
    return dict(
        provider = gui.selector_provider.value,
        model = gui.selector_model.value,
        temperature = gui.slider_temperature.value,
    )


def package_messages( gui ):
    # TODO: Move to aiwb.gui.messages.
    from ..messages.core import Canister
    canisters = [ ]
    if gui.toggle_system_prompt_active.value:
        canisters.append(
            Canister( role = 'Supervisor' ).add_content(
                gui.text_system_prompt.object ) )
    for canister in gui.column_conversation_history:
        canister_gui = canister.gui__
        if not canister_gui.toggle_active.value: continue
        assimilate_canister_dto_from_gui( canister_gui )
        canisters.append( canister_gui.canister__ )
    return canisters


def package_special_data( gui ):
    # TODO: Move to aiwb.gui.invocables.
    special_data = { }
    supports_functions = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'supports-functions' ]
    if supports_functions:
        ai_functions = _provide_active_ai_functions( gui )
        if ai_functions: special_data[ 'ai-functions' ] = ai_functions
    return special_data


def populate_component( gui, layout, component_name ):
    # TODO: Move to aiwb.gui.components.
    from . import updaters as registry # pylint: disable=cyclic-import
    entry = layout[ component_name ]
    for element_name in entry.get( 'contains', ( ) ):
        populate_component( gui, layout, element_name )
    function_name = entry.get( 'populator_function' )
    if None is function_name: return
    function = getattr( registry, function_name )
    function( gui )


def register_event_callbacks( gui, layout, component_name ):
    # TODO: Move to aiwb.gui.components.
    from . import events as registry # pylint: disable=cyclic-import
    entry = layout[ component_name ]
    for element_name in entry.get( 'contains', ( ) ):
        register_event_callbacks( gui, layout, element_name )
    if not hasattr( gui, component_name ): return
    component = getattr( gui, component_name )
    functions = entry.get( 'event_functions', { } )
    for event_name, function_name in functions.items( ):
        function = partial_function( getattr( registry, function_name ), gui )
        if 'on_click' == event_name:
            component.on_click( function )
            continue
        component.param.watch( function, event_name )
    function_name = entry.get( 'javascript_cb_generator' )
    if function_name:
        cb_generator = getattr( registry, function_name )
        component.jscallback( **cb_generator( gui, layout, component_name ) )


def _provide_active_ai_functions( gui ):
    # TODO: Move to aiwb.gui.invocables.
    from json import loads
    # TODO: Remove visibility restriction once fill of system prompt
    #       is implemented for non-functions-supporting models.
    if not gui.row_functions_prompt.visible: return [ ]
    if not gui.toggle_functions_active.value: return [ ]
    if not gui.multichoice_functions.value: return [ ]
    return [
        loads( function.__doc__ )
        for name, function in gui.auxdata__.invocables.items( )
        if name in gui.multichoice_functions.value ]
