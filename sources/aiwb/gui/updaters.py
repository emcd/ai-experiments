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


''' Populators and value updaters for Holoviz Panel GUI. '''


from . import __
from . import core as _core


def add_conversation_indicator( gui, descriptor, position = 0 ):
    from .classes import ConversationIndicator
    from .events import on_select_conversation
    from .layouts import conversation_indicator_layout as layout
    container_gui = __.SimpleNamespace(
        parent__ = gui, identity__ = descriptor.identity )
    container = __.generate_component(
        container_gui, layout, 'column_indicator' )
    container_gui.rehtml_indicator = indicator = (
        ConversationIndicator( container_gui ) )
    container_gui.text_title.object = descriptor.title
    indicator.param.watch(
        lambda event: on_select_conversation( gui, event ), 'clicked' )
    __.register_event_callbacks( container_gui, layout, 'column_indicator' )
    conversations = gui.column_conversations_indicators
    if 'END' == position: conversations.append( indicator )
    else: conversations.insert( position, indicator )
    conversations.descriptors__[ descriptor.identity ] = descriptor
    descriptor.indicator = indicator


def add_message( gui, dto ):
    gui_ = create_message( gui, dto )
    gui_.index__ = len( gui.column_conversation_history )
    widget = gui_.row_canister
    gui.column_conversation_history.append( widget )
    return gui_


def autoscroll_document( gui ):
    if 'manual' == gui.text_autoscroll_status.value: return
    # Trigger JS callback to scroll and then reset state.
    gui.text_autoscroll_status.value = 'scrolling'
    gui.text_autoscroll_status.value = 'automatic'


def configure_message_interface( canister_gui, dto ):
    gui = canister_gui.parent__
    canister = canister_gui.row_canister
    behaviors = dto.attributes.behaviors
    role = dto.role
    canister.styles.update( __.roles_styles[ role ] )
    # TODO: Use user-supplied logos, when available.
    canister_gui.toggle_active.name = __.roles_emoji[ role ]
    if 'AI' == role:
        canister_gui.button_fork.visible = True
        try: __.extract_invocation_requests( gui, component = canister )
        except: pass
        else: canister_gui.button_invoke.visible = True
    elif 'Document' == role:
        canister_gui.button_delete.visible = True
    elif 'Human' == role:
        canister_gui.button_edit.visible = True
    for behavior in behaviors:
        getattr( canister_gui, f"toggle_{behavior}" ).value = True


async def create_and_display_conversation( components, state = None ):
    ''' Creates new conversation in memory and displays it. '''
    from .classes import ConversationDescriptor
    descriptor = ConversationDescriptor( )
    await create_conversation( components, descriptor, state = state )
    # TODO: Async lock conversations index.
    update_conversation_hilite( components, new_descriptor = descriptor )
    display_conversation( components, descriptor )


async def create_conversation( components, descriptor, state = None ):
    ''' Creates new conversation, populating its components. '''
    from . import layouts
    from .layouts import conversation_container_names
    from .persistence import inject_conversation
    # TODO: Restrict GUI namespace to conversation components.
    components_ = __.SimpleNamespace( **components.__dict__ )
    for component_name in conversation_container_names:
        layout = getattr( layouts, f"{component_name}_layout" )
        __.generate_component(
            components_, layout, f"column_{component_name}" )
    components_.auxdata__ = components.auxdata__
    components_.identity__ = descriptor.identity
    components_.parent__ = components
    descriptor.gui = components_
    populate_conversation( components_ ) # TODO: async
    if state: inject_conversation( components_, state ) # TODO: async
    return components_


def create_message( gui, dto ):
    # TODO: Handle content arrays properly.
    layout = determine_message_layout( dto )
    gui_ = __.SimpleNamespace(
        canister__ = dto,
        index__ = None,
        layout__ = layout,
        parent__ = gui )
    widget = __.generate_component( gui_, layout, 'row_canister' )
    widget.gui__ = gui_
    gui_.row_content.gui__ = gui_
    # TODO: Handle non-textual messages and text messages with attachments.
    content = dto[ 0 ].data
    text_message = gui_.text_message
    if hasattr( text_message, 'value' ): text_message.value = content
    else: text_message.object = content
    dto.attributes.behaviors = getattr(
        dto.attributes, 'behaviors', [ 'active' ] )
    configure_message_interface( gui_, dto )
    __.register_event_callbacks( gui_, layout, 'row_canister' )
    return gui_


async def delete_conversation( components, descriptor ):
    ''' Removes conversation from index and flushes it. '''
    # TODO: Confirmation modal dialog.
    from .persistence import save_conversations_index
    conversations = components.column_conversations_indicators
    if descriptor is conversations.current_descriptor__:
        await create_and_display_conversation( components )
    # TODO: Async lock conversations index.
    conversations.descriptors__.pop( descriptor.identity )
    descriptor.gui = None # break possible GC cycles
    indicators = [
        indicator for indicator in conversations
        if indicator.identity__ != descriptor.identity ]
    conversations.objects = indicators
    descriptor.indicator = None # break possible GC cycles
    path = __.calculate_conversations_path( components ).joinpath(
        f"{descriptor.identity}.json" )
    if path.exists( ): path.unlink( )
    await save_conversations_index( components.auxdata__ )


def determine_message_layout( dto ):
    # TODO: Consider contents array.
    mimetype = dto[ 0 ].mimetype
    # TODO: Handle layouts for pictorial messages.
    if 'text/plain' == mimetype:
        from .layouts import plain_conversation_message_layout as layout
    elif 'application/json' == mimetype:
        from .layouts import json_conversation_message_layout as layout
    else:
        from .layouts import rich_conversation_message_layout as layout
    return layout


def display_conversation( gui, descriptor ):
    from .layouts import conversation_container_names
    conversations = gui.column_conversations_indicators
    conversations.current_descriptor__ = descriptor
    for component_name in conversation_container_names:
        getattr( gui, f"interpolant_{component_name}" ).objects = [
            getattr( descriptor.gui, f"column_{component_name}" ) ]
    gui.identity__ = descriptor.gui.identity__
    autoscroll_document( descriptor.gui )


async def fork_conversation( components, index: int ):
    ''' Copies messages history up to index into new conversation. '''
    from .persistence import collect_conversation
    state = collect_conversation( components )
    state[ 'column_conversation_history' ] = (
        state[ 'column_conversation_history' ][ 0 : index + 1 ] )
    await create_and_display_conversation( components, state = state )


def populate_conversation( gui ):
    from . import layouts
    from .layouts import conversation_container_names
    for component_name in conversation_container_names:
        layout = getattr( layouts, f"{component_name}_layout" )
        __.populate_component( gui, layout, f"column_{component_name}" )
    for component_name in conversation_container_names:
        layout = getattr( layouts, f"{component_name}_layout" )
        __.register_event_callbacks( gui, layout, f"column_{component_name}" )
    update_conversation_postpopulate( gui )


async def populate_dashboard( auxdata: _core.Globals ):
    ''' Populates entire conversations dashboard. '''
    from .classes import ConversationDescriptor
    from .layouts import conversations_manager_layout, dashboard_layout
    from .persistence import restore_conversations_index
    components = auxdata.gui.components
    __.generate_component( components, dashboard_layout, 'dashboard' )
    conversations = components.column_conversations_indicators
    conversations.descriptors__ = { }
    conversations.current_descriptor__ = ConversationDescriptor( )
    await restore_conversations_index( auxdata )
    if auxdata.configuration.get( 'maintenance-mode', False ):
        components.button_upgrade_conversations.visible = True
    __.register_event_callbacks(
        components,
        conversations_manager_layout,
        'column_conversations_manager' )
    await create_and_display_conversation( components )


def populate_models_selector( gui ):
    provider = gui.selector_provider.auxdata__[ gui.selector_provider.value ]
    models = provider.provide_chat_models( )
    # TODO: Provide image-to-text, and text-to-image, text-to-speech models.
    gui.selector_model.auxdata__ = models
    gui.selector_model.value = None
    gui.selector_model.options = list( models.keys( ) )
    gui.selector_model.value = provider.select_default_model(
        models, gui.auxdata__ )


def populate_providers_selector( gui ):
    providers = gui.auxdata__.providers
    # TODO: Drop this auxdata and rely on main GUI auxdata instead.
    gui.selector_provider.auxdata__ = providers
    gui.selector_provider.value = None
    names = list( providers.keys( ) )
    gui.selector_provider.options = names
    gui.selector_provider.value = next( iter( names ) )


def populate_prompt_variables( gui, species, data = None ):
    from .controls import ContainerManager
    # TODO: Rename selectors to match species.
    # TEMP HACK: Use selector name as key until cutover to unified dict.
    template_class = 'system' if 'supervisor' == species else 'canned'
    row_name = f"row_{template_class}_prompt_variables"
    selector_name = f"selector_{template_class}_prompt"
    text_prompt_name = f"text_{template_class}_prompt"
    selector = getattr( gui, selector_name )
    name = selector.value
    if name not in selector.options:
        selector.value = name = next( iter( selector.options ) )
    definition = gui.auxdata__.prompts.definitions[ name ]
    prompts_cache = selector.auxdata__.prompts_cache
    if None is not data: prompts_cache[ name ] = definition.deserialize( data )
    prompt = prompts_cache.get( name )
    if None is prompt:
        prompts_cache[ name ] = prompt = definition.produce_prompt( )
    callback = ( lambda event: _update_prompt_text( gui, species = species ) )
    row = getattr( gui, row_name )
    ContainerManager( row, prompt.controls.values( ), callback )
    _update_prompt_text( gui, species = species )
    if 'user' == species: postpopulate_canned_prompt_variables( gui )
    elif 'supervisor' == species: postpopulate_system_prompt_variables( gui )


def populate_system_prompts_selector( gui ):
    _populate_prompts_selector( gui, species = 'supervisor' )
    populate_prompt_variables( gui, species = 'supervisor' )


def populate_canned_prompts_selector( gui ):
    _populate_prompts_selector( gui, species = 'user' )
    populate_prompt_variables( gui, species = 'user' )


def populate_vectorstores_selector( gui ):
    vectorstores = gui.auxdata__.vectorstores
    gui.selector_vectorstore.options = list( vectorstores.keys( ) )
    update_search_button( gui )


def postpopulate_canned_prompt_variables( gui ):
    update_summarization_toggle( gui )


def postpopulate_system_prompt_variables( gui ):
    # TODO: Fix bug where canned prompt variables are not selected on init.
    can_update = hasattr( gui.selector_canned_prompt, 'auxdata__' )
    # If there is a canned prompt preference, then update accordingly.
    definition = (
        gui.auxdata__.prompts.definitions[ gui.selector_system_prompt.value ] )
    attributes = definition.attributes
    user_prompt_preference = attributes.get( 'user-prompt-preference' )
    if can_update and None is not user_prompt_preference:
        gui.selector_canned_prompt.value = user_prompt_preference[ 'name' ]
        populate_prompt_variables(
            gui, species = 'user',
            data = user_prompt_preference.get( 'defaults', { } ) )


async def select_conversation( components, identity ):
    ''' Displays selected conversation, creating it if necessary. '''
    conversations = components.column_conversations_indicators
    old_descriptor = conversations.current_descriptor__
    new_descriptor = conversations.descriptors__[ identity ]
    if old_descriptor.identity == identity: return
    from .persistence import restore_conversation
    if None is new_descriptor.gui:
        components_ = await create_conversation( components, new_descriptor )
        restore_conversation( components_ )
        new_descriptor.gui = components_
    # TODO: Async lock conversations index.
    update_conversation_hilite( components, new_descriptor = new_descriptor )
    display_conversation( components, new_descriptor )


def sort_conversations_index( gui ):
    conversations = gui.column_conversations_indicators
    conversations.descriptors__ = dict( sorted(
        conversations.descriptors__.items( ),
        key = lambda pair: pair[ 1 ].timestamp,
        reverse = True ) )
    conversations.clear( )
    conversations.extend( (
        desc.indicator for desc in conversations.descriptors__.values( )
        if None is not desc.indicator ) )


def truncate_conversation( gui, index ):
    # TODO: Present warning dialog if messages past index.
    history = gui.column_conversation_history
    history.objects = history[ 0 : index + 1 ]


def update_active_functions( gui ):
    available_functions = gui.auxdata__.invocables
    # TODO: Construct components from layout.
    from panel.pane import JSON
    from .layouts import _message_column_width_attributes, sizes
    gui.column_functions_json.objects = [
        JSON(
            function.__doc__,
            depth = -1, theme = 'light',
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            styles = { 'overflow': 'auto' },
            **_message_column_width_attributes,
        )
        for name, function in available_functions.items( )
        if name in gui.multichoice_functions.value ]
    update_token_count( gui )


async def update_and_save_conversation( components ):
    from .persistence import save_conversation
    update_token_count( components ) # TODO? async lock
    save_conversation( components ) # TODO: async


async def update_and_save_conversations_index( components ):
    from .persistence import save_conversations_index
    update_conversation_timestamp( components )
    update_conversation_hilite( components )
    await save_conversations_index( components )


def update_chat_button( gui ):
    gui.button_chat.disabled = not (
            not gui.text_tokens_total.value.endswith( '🚫' )
        and (   'canned' == gui.selector_user_prompt_class.value
             or gui.text_freeform_prompt.value ) )


def update_conversation_hilite( gui, new_descriptor = None ):
    conversations = gui.column_conversations_indicators
    old_descriptor = conversations.current_descriptor__
    if None is new_descriptor: new_descriptor = old_descriptor
    if new_descriptor is not old_descriptor:
        if None is not old_descriptor.indicator:
            # TODO: Cycle to a "previously seen" background color.
            old_descriptor.indicator.styles.pop( 'background', None )
    if None is not new_descriptor.indicator:
        # TODO: Use style variable rather than hard-coded value.
        new_descriptor.indicator.styles.update(
            { 'background': 'LightGray' } )
    # TODO: Try using 'view.resize_layout()' in custom JS for proper fix.
    # Hack: Reload indicators to force repaint.
    indicators = list( conversations )
    conversations.clear( )
    conversations.extend( indicators )


def update_conversation_postpopulate( gui ):
    update_functions_prompt( gui )


def update_conversation_status( gui, text = None, progress = False ):
    gui.spinner_ai_progress.value = False
    gui.spinner_ai_progress.visible = False
    gui.text_conversation_status.visible = False
    # TODO: Hide retry and stack trace inspection buttons.
    if progress:
        gui.spinner_ai_progress.name = text
        gui.spinner_ai_progress.visible = True
        gui.spinner_ai_progress.value = True
    elif None is not text:
        if isinstance( text, Exception ):
            # TODO: Add stack trace inspection button.
            # TODO: If retryable exception, add a retry button.
            text = "{exc_class}: {exc}".format(
                exc_class = type( text ), exc = text )
        gui.text_conversation_status.value = text
        gui.text_conversation_status.visible = True


def update_conversation_timestamp( gui ):
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    descriptor.timestamp = __.time_ns( )
    # If already at top, no need to sort again.
    if conversations[ 0 ] is descriptor.indicator: return
    sort_conversations_index( gui )


def update_functions_prompt( gui ):
    # TODO: For models which do not explicitly support functions,
    #       weave selected functions into system prompt.
    #       Then, functions prompt row should always be visible.
    supports_functions = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'supports-functions' ]
    gui.row_functions_prompt.visible = supports_functions
    if supports_functions:
        attributes = gui.auxdata__.prompts.definitions[
            gui.selector_system_prompt.value ].attributes
        associated_functions = attributes.get( 'functions', { } )
    else: associated_functions = { }
    available_functions = gui.auxdata__.invocables
    gui.multichoice_functions.value = [ ]
    gui.multichoice_functions.options = [
        function_name for function_name in available_functions.keys( )
        if function_name in associated_functions ]
    gui.multichoice_functions.value = [
        function_name for function_name in available_functions.keys( )
        if associated_functions.get( function_name, False ) ]
    update_active_functions( gui )


def update_messages_post_summarization( gui ):
    ''' Exclude conversation items above summarization request. '''
    # TODO: Account for documents.
    for i in range( len( gui.column_conversation_history ) - 2 ):
        message_gui = gui.column_conversation_history[ i ].gui__
        if not message_gui.toggle_active.value: continue # already inactive
        if message_gui.toggle_pinned.value: continue # skip pinned messages
        message_gui.toggle_active.value = False


def update_search_button( gui ):
    gui.button_search.disabled = not (
            gui.selector_vectorstore.value
        and gui.slider_documents_count.value
        and gui.text_freeform_prompt.value )


def update_summarization_toggle( gui ):
    prompt_name = gui.selector_canned_prompt.value
    attributes = gui.auxdata__.prompts.definitions[ prompt_name ].attributes
    summarizes = attributes.get( 'summarizes', False )
    gui.toggle_summarize.value = (
        'canned' == gui.selector_user_prompt_class.value and summarizes )


def update_token_count( gui ):
    if not gui.selector_provider.options: return
    if not gui.selector_model.options: return
    from ..messages.core import Canister
    messages = __.package_messages( gui )
    if 'freeform' == gui.selector_user_prompt_class.value:
        content = gui.text_freeform_prompt.value
    else: content = gui.text_canned_prompt.object
    messages.append( Canister( role = 'Human' ).add_content( content ) )
    controls = __.package_controls( gui )
    special_data = __.package_special_data( gui )
    provider = gui.auxdata__.providers[ gui.selector_provider.value ]
    tokens_count = provider.count_conversation_tokens(
        messages, special_data, controls )
    tokens_limit = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'tokens-limit' ]
    tokens_report = f"{tokens_count} / {tokens_limit}"
    tokens_usage = tokens_count / tokens_limit
    if tokens_usage >= 1:
        tokens_report = f"{tokens_report} 🚫"
    elif tokens_usage >= 0.75:
        tokens_report = f"{tokens_report} \N{Warning Sign}\uFE0F"
    else: tokens_report = f"{tokens_report} 👌"
    gui.text_tokens_total.value = tokens_report
    update_chat_button( gui )


def _populate_prompts_selector( gui, species ):
    # TODO: Rename selectors to match species.
    template_class = 'system' if 'supervisor' == species else 'canned'
    selector = getattr( gui, f"selector_{template_class}_prompt" )
    names = list( sorted( # Panel explicitly needs a list or dict.
        name for name, definition
        in gui.auxdata__.prompts.definitions.items( )
        if      species == definition.species
            and not definition.attributes.get( 'conceal', False ) ) )
    selector.options = names
    selector.auxdata__ = getattr(
        selector, 'auxdata__', __.SimpleNamespace( prompts_cache = { } ) )


def _update_prompt_text( gui, species ):
    # TODO: Rename selectors to match species.
    template_class = 'system' if 'supervisor' == species else 'canned'
    selector = getattr( gui, f"selector_{template_class}_prompt" )
    container = getattr( gui, f"row_{template_class}_prompt_variables" )
    container.auxdata__.manager.assimilate( )
    prompt = selector.auxdata__.prompts_cache[ selector.value ]
    text_prompt = getattr( gui, f"text_{template_class}_prompt" )
    text_prompt.object = prompt.render( gui.auxdata__ )
    update_token_count( gui )
