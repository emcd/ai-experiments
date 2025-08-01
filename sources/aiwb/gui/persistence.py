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


from . import __
from . import conversations as _conversations
from . import state as _state


async def collect_conversation( components ):
    ''' Collects state to save from current conversation. '''
    from . import layouts
    from .layouts import conversation_container_names
    layout = { }
    for container_name in conversation_container_names:
        layout.update( getattr( layouts, f"{container_name}_layout" ) )
    state = { }
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        if not hasattr( components, name ): continue
        component = getattr( components, name )
        if hasattr( component, 'on_click' ): continue
        if hasattr( component, 'objects' ):
            if 'persistence_functions' not in data: continue
            saver_data = data[ 'persistence_functions' ][ 'save' ]
            if isinstance( saver_data, str ):
                saver_name, saver_extras = saver_data, { }
            else: saver_name, saver_extras = saver_data
            saver = globals( )[ saver_name ]
            state.update( await saver( components, name, **saver_extras ) )
        elif hasattr( component, 'value' ):
            state[ name ] = dict( value = component.value )
        elif hasattr( component, 'object' ):
            state[ name ] = dict( value = component.object )
        else: continue
    return state


async def inject_conversation( components, state ):
    ''' Injects saved state into current conversation. '''
    from . import layouts
    from .layouts import conversation_container_names
    layout = { }
    for container_name in conversation_container_names:
        layout.update( getattr( layouts, f"{container_name}_layout" ) )
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        if name not in state: continue # allows new UI features
        if not hasattr( components, name ): continue
        component = getattr( components, name )
        if hasattr( component, 'on_click' ): continue
        if hasattr( component, 'objects' ):
            if 'persistence_functions' not in data: continue
            restorer_data = data[ 'persistence_functions' ][ 'restore' ]
            if isinstance( restorer_data, str ):
                restorer_name, restorer_extras = restorer_data, { }
            else: restorer_name, restorer_extras = restorer_data
            restorer = globals( )[ restorer_name ]
            await restorer( components, name, state, **restorer_extras )
        elif hasattr( component, 'value' ):
            component.value = state[ name ][ 'value' ]
        elif hasattr( component, 'object' ):
            component.object = state[ name ][ 'value' ]
        else: continue


async def remove_orphans( components ):
    ''' Removes orphan messages from contents store. '''
    from itertools import chain
    from shutil import rmtree
    from aiofiles import open as open_
    from tomli import loads
    auxdata = components.auxdata__
    conversations_location = auxdata.provide_state_location( 'conversations' )
    index_file = conversations_location / 'index.toml'
    async with open_( index_file ) as stream:
        index = loads( await stream.read( ) )
    conversations_locations = tuple(
        conversations_location / "{}.json".format( descriptor[ 'identity' ] )
        for descriptor in index[ 'descriptors' ] )
    # TODO: Delete orphan conversations.
    # TODO: Consider format version.
    collectors = tuple(
        _collect_content_ids_from_conversation( components, location )
        for location in conversations_locations )
    extant_ids = frozenset( chain.from_iterable(
        await __.gather_async( *collectors ) ) )
    extant_ids_prefixes = frozenset(
        identity[ : 4 ] for identity in extant_ids )
    ic( len( extant_ids_prefixes ) )
    contents_location = auxdata.provide_state_location( 'contents' )
    actual_ids_prefixes = frozenset(
        location.stem for location in contents_location.iterdir( )
        if location.is_dir( ) and not location.stem.startswith( '.' ) )
    ic( len( actual_ids_prefixes ) )
    orphan_ids_prefixes = actual_ids_prefixes - extant_ids_prefixes
    ic( len( orphan_ids_prefixes ) )
    assert not orphan_ids_prefixes & extant_ids_prefixes
    for id_prefix in orphan_ids_prefixes:
        location = contents_location / id_prefix
        ic( location )
        try: rmtree( location )
        except Exception: continue
    actual_ids = frozenset(
        location.stem
        for id_prefix in actual_ids_prefixes
        for location in ( contents_location / id_prefix ).iterdir( )
        if ( contents_location / id_prefix ).is_dir( )
        and location.is_dir( ) and not location.stem.startswith( '.' ) )
    ic( len( extant_ids ) )
    ic( len( actual_ids ) )
    orphan_ids = actual_ids - extant_ids
    ic( len( orphan_ids ) )
    assert not orphan_ids & extant_ids
    for identity in orphan_ids:
        location = contents_location / identity[ : 4 ] / identity
        ic( location )
        try: rmtree( location )
        except Exception: continue


async def restore_conversation( components ):
    ''' Restores contents of conversation from persistent storage. '''
    from json import loads
    from aiofiles import open as open_
    file = (
        _conversations.provide_location(
            components, f"{components.identity__}.json" ) )
    async with open_( file ) as stream:
        state = loads( await stream.read( ) )
    await inject_conversation( components, state )


async def restore_conversation_messages( components, column_name, state ):
    ''' Restores conversation messages from persistent storage. '''
    from ..messages.core import DirectoryManager, restore_canister
    from .updaters import add_message
    manager = DirectoryManager( auxdata = components.auxdata__ )
    column = getattr( components, column_name )
    canister_states = state.get( column_name, ( ) )
    restorers = tuple(
        restore_canister( manager, canister_state )
        for canister_state in canister_states )
    canisters = await __.gather_async( *restorers )
    # TODO: Prepare messages en masse and then swap .objects on column.
    column.clear( )
    for canister in canisters:
        add_message( components, canister )


async def restore_conversations_index( auxdata: _state.Globals ):
    ''' Restores index of conversations from persistent storage. '''
    from aiofiles import open as open_
    from tomli import loads
    from .classes import ConversationDescriptor
    from .updaters import (
        add_conversation_indicator,
        sort_conversations_index,
    )
    components = auxdata.gui.components
    conversations_path = _conversations.provide_location( components )
    index_path = conversations_path / 'index.toml'
    if not index_path.exists( ):
        return await save_conversations_index( components )
    async with open_( index_path ) as file:
        descriptors = loads( await file.read( ) )[ 'descriptors' ]
    # TODO: Check conversation indicators concurrently.
    #       (asyncio.gather aiofiles.os.path.isfile)
    #       Then, add as array of objects.
    for descriptor in descriptors:
        identity = descriptor[ 'identity' ]
        conversation_path = conversations_path / f"{identity}.json"
        # Conversation may have disappeared for some reason.
        if not conversation_path.exists( ): continue
        add_conversation_indicator(
            components,
            ConversationDescriptor( **descriptor ),
            position = 'END' )
    sort_conversations_index( components ) # extra sanity
    return await save_conversations_index( components )


async def restore_prompt_variables( components, row_name, state, species ):
    ''' Restores prompt variables from loaded state. '''
    from .updaters import populate_prompt_variables
    container_state = state.get( row_name )
    if not isinstance( container_state, __.cabc.Mapping ):
        container_state = _restore_prompt_variables_v0(
            components, container_state, species = species )
    await populate_prompt_variables(
        components, species = species, data = container_state )


async def save_conversation( components ):
    ''' Saves contents of conversation to persistent storage. '''
    from json import dumps
    from aiofiles import open as open_
    conversations = components.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    # Do not save conversation before first chat completion.
    if descriptor.identity not in conversations.descriptors__: return
    # Do not save conversation while populating it.
    if descriptor.identity != components.identity__: return
    state = await collect_conversation( components )
    file = (
        _conversations.provide_location(
            components, f"{components.identity__}.json" ) )
    async with open_( file, 'w' ) as stream:
        await stream.write( dumps( state, indent = 2 ) )


async def save_conversation_messages( components, column_name ):
    ''' Saves conversation messages to persistent storage. '''
    from ..messages.core import DirectoryManager
    manager = DirectoryManager( auxdata = components.auxdata__ )
    canisters_components = tuple(
        canister.gui__
        for canister in getattr( components, column_name, ( ) ) )
    for canister_components in canisters_components:
        _conversations.assimilate_canister_dto_from_gui( canister_components )
    savers = tuple(
        canister_components.canister__.save( manager )
        for canister_components in canisters_components )
    state = await __.gather_async( *savers )
    return { column_name: state }


async def save_conversations_index( components ):
    ''' Saves index of conversations to persistent storage. '''
    from aiofiles import open as open_
    from tomli_w import dumps
    conversations_path = _conversations.provide_location( components )
    conversations_path.mkdir( exist_ok = True, parents = True )
    index_file = conversations_path / 'index.toml'
    conversations = components.column_conversations_indicators
    # Do not serialize GUI components with index.
    descriptors = [
        dict(
            identity = descriptor.identity,
            timestamp = descriptor.timestamp,
            title = descriptor.title,
            labels = descriptor.labels,
        )
        for descriptor in conversations.descriptors__.values( )
    ]
    async with open_( index_file, 'w' ) as stream:
        await stream.write( dumps(
            { 'format-version': 1, 'descriptors': descriptors } ) )


async def save_prompt_variables( components, row_name, species ):
    ''' Records prompt variables into state to be saved. '''
    # TEMP HACK: Use selector name as key until cutover to unified dict.
    template_class = 'system' if 'supervisor' == species else 'canned'
    selector = getattr( components, f"selector_{template_class}_prompt" )
    prompt_name = selector.value
    prompt = selector.auxdata__.prompts_cache[ prompt_name ]
    container = getattr( components, row_name )
    container.auxdata__.manager.assimilate( )
    return { row_name: prompt.serialize( ) }


async def upgrade_conversation( components, identity ):
    ''' Upgrades conversation from older formats to latest format. '''
    from json import JSONDecodeError, dumps, loads
    from aiofiles import open as open_
    from ..messages.core import DirectoryManager, restore_canister
    directory_manager = DirectoryManager( auxdata = components.auxdata__ )
    # TODO: Use directory manager for conversation location.
    conversations_location = _conversations.provide_location( components )
    file = conversations_location / f"{identity}.json"
    # Conversation may have disappeared for some reason.
    if not file.exists( ): return
    ic( file )
    async with open_( file ) as stream:
        try: state = loads( await stream.read( ) )
        except JSONDecodeError: state = None
    if None is state:
        file.unlink( )
        return
    # TODO: Consider format version.
    restorers = tuple(
        restore_canister( directory_manager, canister_state )
        for canister_state in state.get( 'column_conversation_history', ( ) ) )
    canisters = await __.gather_async( *restorers )
    savers = tuple(
        canister.save( directory_manager ) for canister in canisters )
    history_upgrade = await __.gather_async( *savers )
    state[ 'column_conversation_history' ] = history_upgrade
    async with open_( file, 'w' ) as stream:
        await stream.write( dumps( state, indent = 2 ) )


async def upgrade_conversations( components ):
    ''' Upgrades conversations from older formats to latest format. '''
    from aiofiles import open as open_
    from tomli import loads
    conversations_location = _conversations.provide_location( components )
    index_file = conversations_location / 'index.toml'
    async with open_( index_file ) as stream:
        index = loads( await stream.read( ) )
    # TODO: Consider format version.
    upgraders = tuple(
        upgrade_conversation( components, descriptor[ 'identity' ] )
        for descriptor in index[ 'descriptors' ] )
    # TODO: Submit upgrades to queue to prevent fd exhaustion.
    #await __.gather_async( *upgraders )
    for upgrader in upgraders: await upgrader


async def _collect_content_ids_from_conversation(
    components, conversation_location
):
    from itertools import chain
    from json import loads
    from aiofiles import open as open_
    async with open_( conversation_location ) as stream:
        state = loads( await( stream.read( ) ) )
    return tuple( chain.from_iterable(
        canister.get( 'contents', ( ) )
        for canister in state.get( 'column_conversation_history' ) ) )


def _restore_prompt_variables_v0( gui, state, species ):
    from ..controls.core import FlexArray
    # TEMP HACK: Use selector name as key until cutover to unified dict.
    template_class = 'system' if 'supervisor' == species else 'canned'
    selector = getattr( gui, f"selector_{template_class}_prompt" )
    definition = gui.auxdata__.prompts.definitions[ selector.value ]
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
    except Exception: return content, { }
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
