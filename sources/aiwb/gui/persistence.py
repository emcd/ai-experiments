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

# Note: Cyclic imports are at runtime and not during module initialization.
# pylint: disable=cyclic-import


from . import base as __


def collect_conversation( gui ):
    from . import layouts
    from .layouts import conversation_container_names
    layout = { }
    for container_name in conversation_container_names:
        layout.update( getattr( layouts, f"{container_name}_layout" ) )
    state = { }
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        if not hasattr( gui, name ): continue
        component = getattr( gui, name )
        if hasattr( component, 'on_click' ): continue
        if hasattr( component, 'objects' ):
            if 'persistence_functions' not in data: continue
            saver_data = data[ 'persistence_functions' ][ 'save' ]
            if isinstance( saver_data, str ):
                saver_name, saver_extras = saver_data, { }
            else: saver_name, saver_extras = saver_data
            saver = globals( )[ saver_name ]
            state.update( saver( gui, name, **saver_extras ) )
        elif hasattr( component, 'value' ):
            state[ name ] = dict( value = component.value )
        elif hasattr( component, 'object' ):
            state[ name ] = dict( value = component.object )
        else: continue
    return state


def inject_conversation( gui, state ):
    from . import layouts
    from .layouts import conversation_container_names
    from .updaters import update_token_count
    layout = { }
    for container_name in conversation_container_names:
        layout.update( getattr( layouts, f"{container_name}_layout" ) )
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        if name not in state: continue # allows new UI features
        if not hasattr( gui, name ): continue
        component = getattr( gui, name )
        if hasattr( component, 'on_click' ): continue
        if hasattr( component, 'objects' ):
            if 'persistence_functions' not in data: continue
            restorer_data = data[ 'persistence_functions' ][ 'restore' ]
            if isinstance( restorer_data, str ):
                restorer_name, restorer_extras = restorer_data, { }
            else: restorer_name, restorer_extras = restorer_data
            restorer = globals( )[ restorer_name ]
            restorer( gui, name, state, **restorer_extras )
        elif hasattr( component, 'value' ):
            component.value = state[ name ][ 'value' ]
        elif hasattr( component, 'object' ):
            component.object = state[ name ][ 'value' ]
        else: continue
    update_token_count( gui )


def restore_conversation( gui ):
    from json import load
    path = __.calculate_conversations_path( gui ) / f"{gui.identity__}.json"
    with path.open( ) as file: state = load( file )
    inject_conversation( gui, state )


def restore_conversation_messages( gui, column_name, state ):
    from ..messages.core import DirectoryManager, restore_canister
    from .updaters import add_message
    column = getattr( gui, column_name )
    column.clear( )
    for canister_state in state.get( column_name, [ ] ):
        if 'mime-type' in canister_state:
            canister = _restore_conversation_message_v0( canister_state )
        else:
            manager = DirectoryManager( gui.auxdata__ )
            canister = restore_canister( manager, canister_state )
        add_message( gui, canister )


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


def restore_prompt_variables( gui, row_name, state, species ):
    from .updaters import populate_prompt_variables
    container_state = state.get( row_name )
    if not isinstance( container_state, __.AbstractDictionary ):
        container_state = _restore_prompt_variables_v0(
            gui, container_state, species = species )
    populate_prompt_variables( gui, species = species, data = container_state )


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
    from ..messages.core import DirectoryManager
    from .base import assimilate_canister_dto_from_gui
    manager = DirectoryManager( gui.auxdata__ )
    state = [ ]
    for canister in getattr( gui, column_name ):
        canister_gui = canister.gui__
        assimilate_canister_dto_from_gui( canister_gui )
        state.append( canister_gui.canister__.save( manager ) )
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


def save_prompt_variables( gui, row_name, species ):
    # TEMP HACK: Use selector name as key until cutover to unified dict.
    template_class = 'system' if 'supervisor' == species else 'canned'
    selector = getattr( gui, f"selector_{template_class}_prompt" )
    prompt_name = selector.value
    prompt = selector.auxdata__.prompts_cache[ prompt_name ]
    container = getattr( gui, row_name )
    container.auxdata__.manager.assimilate( )
    return { row_name: prompt.serialize( ) }


def upgrade_conversation( gui, identity ):
    import json
    from ..messages.core import DirectoryManager, restore_canister
    directory_manager = DirectoryManager( gui.auxdata__ )
    # TODO: Use directory manager for conversation location.
    conversations_path = __.calculate_conversations_path( gui )
    path = conversations_path / f"{identity}.json"
    # Conversation may have disappeared for some reason.
    if not path.exists( ): return
    ic( path )
    with path.open( ) as file:
        try: state = json.load( file )
        except json.JSONDecodeError: state = None
    if None is state:
        path.unlink( )
        return
    # TODO: Consider format version.
    history_original = state.get( 'column_conversation_history', [ ] )
    history_upgrade = [ ]
    for canister_state in history_original:
        if 'mime-type' in canister_state:
            canister = _restore_conversation_message_v0( canister_state )
        else: canister = restore_canister( directory_manager, canister_state )
        history_upgrade.append( canister.save( directory_manager ) )
    state[ 'column_conversation_history' ] = history_upgrade
    with path.open( 'w' ) as file: json.dump( state, file, indent = 2 )


def upgrade_conversations( gui ):
    conversations_path = __.calculate_conversations_path( gui )
    index_path = conversations_path / 'index.toml'
    from tomli import load
    with index_path.open( 'rb' ) as file: index = load( file )
    # TODO: Consider format version.
    for descriptor in index[ 'descriptors' ]:
        identity = descriptor[ 'identity' ]
        upgrade_conversation( gui, identity )


def _restore_conversation_message_v0( canister_state ):
    from ..messages.core import Canister
    role = canister_state[ 'role' ]
    attributes = __.SimpleNamespace(
        behaviors = canister_state[ 'behaviors' ] )
    context = canister_state.get( 'context', { } )
    if 'actor-name' in canister_state: # Deprecated field.
        context[ 'name' ] = canister_state[ 'actor-name' ]
    if 'AI' == role:
        content, extra_context = _standardize_invocation_requests_v0(
            canister_state )
        if extra_context: attributes.response_class = 'invocation'
        context.update( extra_context )
    else: content = canister_state[ 'content' ]
    if context: attributes.model_context = context
    return Canister( role, attributes = attributes ).add_content(
        content, mimetype = canister_state[ 'mime-type' ] )


def _restore_prompt_variables_v0( gui, state, species ):
    from ..controls.core import FlexArray
    # TEMP HACK: Use selector name as key until cutover to unified dict.
    template_class = 'system' if 'supervisor' == species else 'canned'
    selector = getattr( gui, f"selector_{template_class}_prompt" )
    definition = gui.auxdata__.prompts[ selector.value ]
    variables = definition.variables
    data = { }
    for substate in state:
        name = substate[ 'name' ]
        value = substate[ 'value' ]
        if name not in variables: continue
        variable = variables[ name ]
        if isinstance( variable, FlexArray ): value = [ value ]
        data[ name ] = value
    return __.DictionaryProxy( data )


def _standardize_invocation_requests_v0( canister_state ):
    from json import dumps, loads
    content = canister_state[ 'content' ]
    try: extra_context = loads( content )
    except: return content, { }
    requests = [ ]
    if 'tool_calls' in extra_context:
        for tool_call in extra_context[ 'tool_calls' ]:
            function = tool_call[ 'function' ]
            requests.append( dict(
                name = function[ 'name' ],
                arguments = function[ 'arguments' ].copy( )
            ) )
            function[ 'arguments' ] = dumps( function[ 'arguments' ] )
        return dumps( requests ), extra_context
    if 'name' in extra_context and 'arguments' in extra_context:
        requests.append( dict(
            name = extra_context[ 'name' ],
            arguments = extra_context[ 'arguments' ].copy( )
        ) )
        extra_context[ 'arguments' ] = dumps( extra_context[ 'arguments' ] )
        return dumps( requests ), extra_context
    return content, { }
