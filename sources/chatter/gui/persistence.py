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


''' Persistence functions for Holoviz Panel GUI. '''


from . import base as __


def collect_conversation( gui ):
    from .layouts import conversation_layout, conversation_control_layout
    layout = dict( **conversation_layout, **conversation_control_layout )
    state = { }
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        component = getattr( gui, name )
        if hasattr( component, 'on_click' ): continue
        elif hasattr( component, 'objects' ):
            if 'persistence_functions' not in data: continue
            saver_name = data[ 'persistence_functions' ][ 'save' ]
            saver = globals( )[ saver_name ]
            state.update( saver( gui, name ) )
        elif hasattr( component, 'value' ):
            state[ name ] = dict( value = component.value )
        elif hasattr( component, 'object' ):
            state[ name ] = dict( value = component.object )
        else: continue
    return state


def inject_conversation( gui, state ):
    from .layouts import conversation_layout, conversation_control_layout
    from .updaters import update_token_count, update_run_tool_button
    layout = dict( **conversation_layout, **conversation_control_layout )
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        if name not in state: continue # allows new UI features
        component = getattr( gui, name )
        if hasattr( component, 'on_click' ): continue
        elif hasattr( component, 'objects' ):
            if 'persistence_functions' not in data: continue
            restorer_name = data[ 'persistence_functions' ][ 'restore' ]
            restorer = globals( )[ restorer_name ]
            restorer( gui, name, state )
        elif hasattr( component, 'value' ):
            component.value = state[ name ][ 'value' ]
        elif hasattr( component, 'object' ):
            component.object = state[ name ][ 'value' ]
        else: continue
    update_token_count( gui )
    update_run_tool_button( gui ) # No autorun here; can lead to bad state.


def restore_conversation( gui ):
    from json import load
    path = __.calculate_conversations_path( gui ) / f"{gui.identity__}.json"
    with path.open( ) as file: state = load( file )
    inject_conversation( gui, state )


def restore_conversation_messages( gui, column_name, state ):
    from .updaters import add_message
    column = getattr( gui, column_name )
    column.clear( )
    for row_state in state.get( column_name, [ ] ):
        actor_name = row_state.get( 'actor-name' )
        behaviors = row_state[ 'behaviors' ]
        content = row_state[ 'content' ]
        mime_type = row_state[ 'mime-type' ]
        role = row_state[ 'role' ]
        add_message(
            gui, role, content,
            actor_name = actor_name,
            behaviors = behaviors,
            mime_type = mime_type )


def restore_conversations_index( gui ):
    from .classes import ConversationDescriptor
    from .updaters import (
        add_conversation_indicator,
        sort_conversations_index,
    )
    conversations_path = __.calculate_conversations_path( gui )
    index_path = conversations_path / 'index.toml'
    if not index_path.exists( ): return save_conversations_index( gui )
    from tomli import load
    with index_path.open( 'rb' ) as file:
        descriptors = load( file )[ 'descriptors' ]
    for descriptor in descriptors:
        identity = descriptor[ 'identity' ]
        conversation_path = conversations_path / f"{identity}.json"
        # Conversation may have disappeared for some reason.
        if not conversation_path.exists( ): continue
        add_conversation_indicator(
            gui, ConversationDescriptor( **descriptor ), position = 'END' )
    sort_conversations_index( gui ) # extra sanity
    save_conversations_index( gui )


def restore_prompt_variables( gui, row_name, state ):
    for widget_state, widget in zip(
        state.get( row_name, ( ) ), getattr( gui, row_name )
    ):
        # TODO: Sanity check widget names.
        widget.value = widget_state[ 'value' ]


def save_conversation( gui ):
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    # Do not save conversation before first chat completion.
    if descriptor.identity not in conversations.descriptors__: return
    # Do not save conversation while populating it.
    if descriptor.identity != gui.identity__: return
    from json import dump
    state = collect_conversation( gui )
    path = __.calculate_conversations_path( gui ) / f"{gui.identity__}.json"
    with path.open( 'w' ) as file: dump( state, file, indent = 2 )


def save_conversation_messages( gui, column_name ):
    state = [ ]
    for row in getattr( gui, column_name ):
        message_gui = row.auxdata__[ 'gui' ]
        behaviors = [ ]
        for behavior in ( 'active', 'pinned' ):
            if getattr( message_gui, f"toggle_{behavior}" ).value:
                behaviors.append( behavior )
        substate = {
            'behaviors': behaviors,
            'content': message_gui.text_message.object,
        }
        substate.update( {
            key: value for key, value in row.auxdata__.items( )
            if key in ( 'actor-name', 'mime-type', 'role' )
        } )
        state.append( substate )
    return { column_name: state }


def save_conversations_index( gui ):
    conversations_path = __.calculate_conversations_path( gui )
    conversations_path.mkdir( exist_ok = True, parents = True )
    index_path = conversations_path / 'index.toml'
    conversations = gui.column_conversations_indicators
    # Do not serialize GUI.
    descriptors = [
        dict(
            identity = descriptor.identity,
            timestamp = descriptor.timestamp,
            title = descriptor.title,
            labels = descriptor.labels,
        )
        for descriptor in conversations.descriptors__.values( )
    ]
    from tomli_w import dump
    with index_path.open( 'wb' ) as file:
        dump( { 'format-version': 1, 'descriptors': descriptors }, file )


def save_prompt_variables( gui, row_name ):
    state = [ ]
    for widget in getattr( gui, row_name ):
        state.append( { 'name': widget.name, 'value': widget.value } )
    return { row_name: state }
