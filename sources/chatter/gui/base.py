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


''' Classes, constants, and utilities common to the GUI. '''


import dataclasses
import typing as typ

from collections import namedtuple
from collections.abc import (
    Mapping as AbstractDictionary,
    MutableSequence as AbstractMutableSequence,
    Sequence as AbstractSequence,
)
from dataclasses import dataclass
from datetime import (
    datetime as DateTime,
    timezone as TimeZone,
)
from functools import partial as partial_function
from pathlib import Path
from time import time_ns
from types import SimpleNamespace
from uuid import uuid4

import param

from panel.layout import Column, Row
from panel.reactive import ReactiveHTML


roles_emoji = {
    'AI': '🤖',
    'Document': '📄',
    'Function': '\N{Hammer and Wrench}\uFE0F',
    'Human': '🧑',
}

# TODO: Use style variables.
roles_styles = {
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


def calculate_conversations_path( gui ):
    configuration = gui.auxdata__[ 'configuration' ]
    directories = gui.auxdata__[ 'directories' ]
    state_path = Path( configuration[ 'locations' ][ 'state' ].format(
        user_state_path = directories.user_state_path ) )
    return state_path / 'conversations'


def extract_function_invocation_request( gui ):
    rehtml_message = gui.column_conversation_history[ -1 ]
    message = rehtml_message.gui__.text_message.object
    # TODO: Handle multipart MIME.
    from json import loads
    try: data = loads( message )
    except: raise ValueError( 'Malformed JSON payload in message.' )
    if not isinstance( data, AbstractDictionary ):
        raise ValueError( 'Function invocation request is not dictionary.' )
    if 'name' not in data:
        raise ValueError( 'Function name is absent from invocation request.' )
    name = data[ 'name' ]
    arguments = data.get( 'arguments', { } )
    ai_functions = gui.auxdata__[ 'ai-functions' ]
    # TODO: Check against multichoice values instead.
    if name not in ai_functions:
        raise ValueError( 'Function name in request is not available.' )
    return name, partial_function( ai_functions[ name ], **arguments )


def generate_component( components, layout, component_name ):
    entry = layout[ component_name ]
    elements = [ ]
    for element_name in entry.get( 'contains', ( ) ):
        elements.append( generate_component(
            components, layout, element_name ) )
    component_class = entry[ 'component_class' ]
    component_arguments = entry.get( 'component_arguments', { } )
    component = component_class( *elements, **component_arguments )
    components[ component_name ] = component
    return component


def package_controls( gui ):
    return dict(
        model = gui.selector_model.value,
        temperature = gui.slider_temperature.value,
    )


def package_messages( gui ):
    messages = [ ]
    if gui.toggle_system_prompt_active.value:
        messages.append( dict(
            content = gui.text_system_prompt.object, role = 'Supervisor' ) )
    for row in gui.column_conversation_history:
        message_gui = row.auxdata__[ 'gui' ]
        if not message_gui.toggle_active.value: continue
        role = row.auxdata__[ 'role' ]
        message = dict(
            content = message_gui.text_message.object,
            role = role,
        )
        if 'actor-name' in row.auxdata__:
            message[ 'actor-name' ] = row.auxdata__[ 'actor-name' ]
        messages.append( message )
    return messages


def package_special_data( gui ):
    special_data = { }
    supports_functions = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'supports-functions' ]
    if supports_functions:
        ai_functions = _provide_active_ai_functions( gui )
        if ai_functions: special_data[ 'ai-functions' ] = ai_functions
    return special_data


def populate_component( gui, layout, component_name ):
    from . import updaters as registry
    entry = layout[ component_name ]
    elements = [ ]
    for element_name in entry.get( 'contains', ( ) ):
        populate_component( gui, layout, element_name )
    function_name = entry.get( 'populator_function' )
    if None is function_name: return
    function = getattr( registry, function_name )
    function( gui )


def register_event_callbacks( gui, layout, component_name ):
    from . import events as registry
    entry = layout[ component_name ]
    elements = [ ]
    for element_name in entry.get( 'contains', ( ) ):
        register_event_callbacks( gui, layout, element_name )
    component = getattr( gui, component_name )
    functions = entry.get( 'event_functions', { } )
    for event_name, function_name in functions.items( ):
        function = getattr( registry, function_name )
        if 'on_click' == event_name:
            component.on_click( lambda event: function( gui, event ) )
            continue
        component.param.watch(
            lambda event: function( gui, event ), event_name )


def _provide_active_ai_functions( gui ):
    from json import loads
    # TODO: Remove visibility restriction once fill of system prompt
    #       is implemented for non-functions-supporting models.
    if not gui.row_functions_prompt.visible: return [ ]
    if not gui.toggle_functions_active.value: return [ ]
    if not gui.multichoice_functions.value: return [ ]
    return [
        loads( function.__doc__ )
        for name, function in gui.auxdata__[ 'ai-functions' ].items( )
        if name in gui.multichoice_functions.value ]
