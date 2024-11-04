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
from . import components as _components
from . import conversations as _conversations
from . import invocables as _invocables
from . import providers as _providers
from . import state as _state


def add_conversation_indicator( components, descriptor, position = 0 ):
    ''' Adds conversation indicator to conversations index. '''
    from .classes import ConversationIndicator
    from .events import on_select_conversation
    from .layouts import conversation_indicator_layout as layout
    container_components = __.SimpleNamespace(
        parent__ = components, identity__ = descriptor.identity )
    _components.generate( container_components, layout, 'column_indicator' )
    container_components.rehtml_indicator = indicator = (
        ConversationIndicator( container_components ) )
    container_components.text_title.object = descriptor.title
    indicator.param.watch(
        __.partial_function( on_select_conversation, components ), 'clicked' )
    _components.register_event_reactors(
        container_components, layout, 'column_indicator' )
    conversations = components.column_conversations_indicators
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


_roles_emoji = {
    __.MessageRole.Assistant: '🤖',
    __.MessageRole.Document: '📄',
    __.MessageRole.Invocation: '\N{Hammer and Wrench}\uFE0F',
    __.MessageRole.Result: '📦',
    __.MessageRole.User: '🧑',
}
_roles_styles = {
    # TODO: Use style variables.
    __.MessageRole.Assistant: {
        'background-color': 'WhiteSmoke',
    },
    __.MessageRole.Document: {
        'background-color': 'White',
        'border-top': '2px dashed LightGray',
        'padding': '3px',
    },
    __.MessageRole.Invocation: {
        'background-color': 'WhiteSmoke',
    },
    __.MessageRole.Result: {
        'background-color': 'White',
        #'border-top': '2px dashed LightGray',
        #'padding': '3px',
    },
    __.MessageRole.User: {
        'background-color': 'White',
    },
}
def configure_message_interface( canister_gui, dto ):
    ''' Styles message cell appropriately. '''
#    from .invocables import extract_invocation_requests
#    gui = canister_gui.parent__
    canister = canister_gui.row_canister
    behaviors = dto.attributes.behaviors
    role = dto.role
    canister.styles.update( _roles_styles[ role ] )
    # TODO: Use user-supplied logos, when available.
    canister_gui.toggle_active.name = _roles_emoji[ role ]
    match role:
        case __.MessageRole.Assistant:
            canister_gui.button_fork.visible = True
#            try:
#                irequests = await extract_invocation_requests(
#                    gui,
#                    component = canister,
#                    silent_extraction_failure = True )
#            # TODO: No debug prints if model mismatch.
#            except Exception as exc: ic( __.exception_to_str( exc ) )
#            else: canister_gui.button_invoke.visible = bool( irequests )
        case __.MessageRole.Document:
            canister_gui.button_delete.visible = True
        case __.MessageRole.Invocation:
            # TODO: Only enable 'Invoke' button if model supports invocations.
            canister_gui.button_invoke.visible = True
        case __.MessageRole.Result: pass
        case __.MessageRole.User:
            canister_gui.button_edit.visible = True
    for behavior in behaviors:
        getattr( canister_gui, f"toggle_{behavior}" ).value = True


async def create_and_display_conversation( components, state = None ):
    ''' Creates new conversation in memory and displays it. '''
    from .classes import ConversationDescriptor
    descriptor = ConversationDescriptor( )
    components_ = (
        await create_conversation( components, descriptor, state = state ) )
    await update_conversation( components_, select_defaults = True )
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
        _components.generate( components_, layout, f"column_{component_name}" )
    components_.auxdata__ = components.auxdata__
    components_.identity__ = descriptor.identity
    components_.mutex__ = __.MutexAsync( )
    components_.parent__ = components
    descriptor.gui = components_
    async with components_.mutex__:
        await populate_conversation( components_ )
        if state: await inject_conversation( components_, state )
    return components_


def create_message( gui, dto ):
    # TODO: Handle content arrays properly.
    layout = determine_message_layout( dto )
    gui_ = __.SimpleNamespace(
        canister__ = dto,
        index__ = None,
        layout__ = layout,
        parent__ = gui )
    widget = _components.generate( gui_, layout, 'row_canister' )
    widget.gui__ = gui_
    gui_.row_content.gui__ = gui_
    # TODO: Handle non-textual messages and text messages with attachments.
    if dto: content = dto[ 0 ].data
    elif hasattr( dto.attributes, 'invocation_data' ):
        content = dto.attributes.invocation_data
    else: content = ''
    text_message = gui_.text_message
    if hasattr( text_message, 'value' ): text_message.value = content
    else: text_message.object = content
    dto.attributes.behaviors = getattr(
        dto.attributes, 'behaviors', [ 'active' ] )
    configure_message_interface( gui_, dto )
    _components.register_event_reactors( gui_, layout, 'row_canister' )
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
    path = (
        _conversations.provide_location(
            components, f"{descriptor.identity}.json" ) )
    if path.exists( ): path.unlink( )
    await save_conversations_index( components )


def determine_message_layout( dto ):
    # TODO: Consider contents array.
    if dto: mimetype = dto[ 0 ].mimetype
    elif hasattr( dto.attributes, 'invocation_data' ):
        mimetype = 'application/json'
    else: mimetype = 'text/plain' # TODO? Raise error.
    # TODO: Handle layouts for pictorial messages.
    match mimetype:
        case 'application/json':
            from .layouts import json_conversation_message_layout as layout
        case 'text/plain':
            from .layouts import plain_conversation_message_layout as layout
        case _:
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
    state = await collect_conversation( components )
    state[ 'column_conversation_history' ] = (
        state[ 'column_conversation_history' ][ 0 : index + 1 ] )
    await create_and_display_conversation( components, state = state )


async def populate_conversation( components ):
    ''' Populates entire conversation history. '''
    from . import layouts
    from .layouts import conversation_container_names
    for component_name in conversation_container_names:
        layout = getattr( layouts, f"{component_name}_layout" )
        await _components.populate(
            components, layout, f"column_{component_name}" )
    for component_name in conversation_container_names:
        layout = getattr( layouts, f"{component_name}_layout" )
        _components.register_event_reactors(
            components, layout, f"column_{component_name}" )
    await update_conversation_postpopulate( components )


async def populate_dashboard( auxdata: _state.Globals ):
    ''' Populates entire conversations dashboard. '''
    from .classes import ConversationDescriptor
    from .layouts import conversations_manager_layout, dashboard_layout
    from .persistence import restore_conversations_index
    components = auxdata.gui.components
    _components.generate( components, dashboard_layout, 'dashboard' )
    conversations = components.column_conversations_indicators
    conversations.descriptors__ = { }
    conversations.current_descriptor__ = ConversationDescriptor( )
    await restore_conversations_index( auxdata )
    if auxdata.configuration.get( 'maintenance-mode', False ):
        components.button_remove_orphans.visible = True
        components.button_upgrade_conversations.visible = True
    _components.register_event_reactors(
        components,
        conversations_manager_layout,
        'column_conversations_manager' )
    await create_and_display_conversation( components )


async def populate_models_selector( components, select_default = False ):
    ''' Populates selector with available models for current provider. '''
    # TODO: Different models selectors per model genus.
    from .providers import (
        access_provider_selection, mutex_models, mutex_providers )
    auxdata = components.auxdata__
    genus = __.AiModelGenera.Converser
    selector = components.selector_model
    async with mutex_models:
        provider = (
            await access_provider_selection(
                components, ignore_mutex = mutex_providers.locked( ) ) )
        models = (
            await provider.survey_models( auxdata = auxdata, genus = genus ) )
        model_names = tuple( model.name for model in models )
        selector.auxdata__ = { model.name: model for model in models }
        select_default = select_default or selector.value not in model_names
        selector.options = list( model_names )
        if select_default:
            selector.value = (
                await provider.access_model_default(
                    auxdata = auxdata, genus = genus ) ).name


async def populate_providers_selector( components, select_default = False ):
    ''' Populates selector with available provider clients. '''
    from .providers import mutex_providers
    auxdata = components.auxdata__
    providers = auxdata.providers
    selector = components.selector_provider
    names = list( providers.keys( ) )
    async with mutex_providers:
        # TODO: Drop this auxdata and rely on main GUI auxdata instead.
        selector.auxdata__ = providers
        select_default = select_default or selector.value not in names
        selector.options = names
        if select_default:
            selector.value = (
                __.access_ai_provider_client_default(
                    auxdata, providers ) ).name
        await populate_models_selector(
            components, select_default = select_default )


async def populate_prompt_variables( components, species, data = None ):
    ''' Populates relevant controls for prompt variables. '''
    from .controls import ContainerManager
    # TODO: Rename selectors to match species.
    # TEMP HACK: Use selector name as key until cutover to unified dict.
    template_class = 'system' if 'supervisor' == species else 'canned'
    row_name = f"row_{template_class}_prompt_variables"
    selector_name = f"selector_{template_class}_prompt"
    selector = getattr( components, selector_name )
    name = selector.value
    if name not in selector.options:
        selector.value = name = next( iter( selector.options ) )
    definition = components.auxdata__.prompts.definitions[ name ]
    prompts_cache = selector.auxdata__.prompts_cache
    if None is not data: prompts_cache[ name ] = definition.deserialize( data )
    prompt = prompts_cache.get( name )
    if None is prompt:
        prompts_cache[ name ] = prompt = definition.produce_prompt( )
    row = getattr( components, row_name )
    match species:
        case 'supervisor':
            from .events import on_change_system_prompt
            event_reactor = __.partial_function(
                on_change_system_prompt, components )
            postpopulator = postpopulate_system_prompt_variables
        case _: # user
            from .events import on_change_canned_prompt
            event_reactor = __.partial_function(
                on_change_canned_prompt, components )
            postpopulator = postpopulate_canned_prompt_variables
    ContainerManager( row, prompt.controls.values( ), event_reactor )
    await update_prompt_text( components, species = species )
    await postpopulator( components )


async def populate_supervisor_prompts_selector( components ):
    _populate_prompts_selector( components, species = 'supervisor' )
    await populate_prompt_variables( components, species = 'supervisor' )


async def populate_canned_prompts_selector( components ):
    # TODO? Rename 'canned' to 'user'.
    _populate_prompts_selector( components, species = 'user' )
    await populate_prompt_variables( components, species = 'user' )


async def populate_vectorstores_selector( components ):
    vectorstores = components.auxdata__.vectorstores
    components.selector_vectorstore.options = list( vectorstores.keys( ) )
    update_search_button( components )


async def postpopulate_canned_prompt_variables( components ):
    ''' Updates default summarization action for user prompt. '''
    update_summarization_toggle( components )


async def postpopulate_system_prompt_variables( components ):
    ''' Updates preferred user prompt for supervisor prompt. '''
    # TODO: Fix bug where canned prompt variables are not selected on init.
    can_update = hasattr( components.selector_canned_prompt, 'auxdata__' )
    # If there is a canned prompt preference, then update accordingly.
    definition = (
        components.auxdata__.prompts
        .definitions[ components.selector_system_prompt.value ] )
    attributes = definition.attributes
    user_prompt_preference = attributes.get( 'user-prompt-preference' )
    if can_update and None is not user_prompt_preference:
        components.selector_canned_prompt.value = (
            user_prompt_preference[ 'name' ] )
        await populate_prompt_variables(
            components, species = 'user',
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
        async with components_.mutex__:
            await restore_conversation( components_ )
        await update_conversation( components_ )
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


async def update_and_save_conversation( components ):
    ''' Updates conversation state and then saves it. '''
    from .persistence import save_conversation
    await update_token_count( components ) # TODO? async lock
    await save_conversation( components )


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


async def update_conversation( components, select_defaults = False ):
    ''' Updates GUI to match conversation state.

        Useful after event handlers have been disarmed, such as during
        conversation restoration.
    '''
    await populate_providers_selector(
        components, select_default = select_defaults )
    await update_conversation_postpopulate( components )
    await update_token_count( components )


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


async def update_conversation_postpopulate( components ):
    ''' Finalize conversation presentation after loading messages. '''
    await update_invocations_prompt( components )
    await update_supervisor_prompt( components )


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


async def update_invocables_selection( components ):
    ''' Reflect selected invocables in schemata display. '''
    invokers = components.auxdata__.invocables.invokers
    # TODO: Construct components from layout.
    from panel.pane import JSON
    from .layouts import _message_column_width_attributes, sizes
    components.column_functions_json.objects = [
        JSON(
            invoker.argschema,
            depth = -1, theme = 'light',
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            styles = { 'overflow': 'auto' },
            **_message_column_width_attributes,
        )
        for name, invoker in invokers.items( )
        if name in components.multichoice_functions.value ]
    await update_token_count( components )


async def update_invocations_prompt( components ):
    ''' Updates available invocables according to model and other factors. '''
    from .providers import access_model_selection
    supports_invocations = (
        ( await access_model_selection( components ) )
        .attributes.supports_invocations )
    components.row_functions_prompt.visible = supports_invocations
    if supports_invocations:
        attributes = components.auxdata__.prompts.definitions[
            components.selector_system_prompt.value ].attributes
        associated_functions = attributes.get( 'functions', { } )
    else: associated_functions = { } # TODO? Return instead of blanking.
    invokers = components.auxdata__.invocables.invokers
    multiselect = components.multichoice_functions
    names = [
        name for name in invokers.keys( ) if name in associated_functions ]
    multiselect.value = [ # Preserve previous selections if possible.
        element for element in multiselect.value if element in names ]
    multiselect.options = names
    if not multiselect.value:
        multiselect.value = [
            name for name in invokers.keys( )
            if associated_functions.get( name, False ) ]
    await update_invocables_selection( components )


async def update_supervisor_prompt( components ):
    ''' Updates supervisor message according to model. '''
    from .providers import access_model_selection
    accepts_instructions = (
        ( await access_model_selection( components ) )
        .attributes.accepts_supervisor_instructions )
    components.row_system_prompt.visible = accepts_instructions


def update_messages_post_summarization( gui ):
    ''' Exclude conversation items above summarization request. '''
    # TODO: Account for documents.
    for i in range( len( gui.column_conversation_history ) - 2 ):
        message_gui = gui.column_conversation_history[ i ].gui__
        if not message_gui.toggle_active.value: continue # already inactive
        if message_gui.toggle_pinned.value: continue # skip pinned messages
        message_gui.toggle_active.value = False


async def update_prompt_text( components, species ):
    ''' Renders prompt from template and variables. '''
    # TODO: Rename selectors to match species.
    template_class = 'system' if 'supervisor' == species else 'canned'
    selector = getattr( components, f"selector_{template_class}_prompt" )
    container = getattr( components, f"row_{template_class}_prompt_variables" )
    container.auxdata__.manager.assimilate( )
    prompt = selector.auxdata__.prompts_cache[ selector.value ]
    text_prompt = getattr( components, f"text_{template_class}_prompt" )
    text_prompt.object = prompt.render( components.auxdata__ )
    await update_token_count( components )


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


async def update_token_count( components ):
    ''' Displays current token usage against context window maximum. '''
    if components.mutex__.locked( ): return
    if not components.selector_provider.options: return
    if not components.selector_model.options: return
    messages = _conversations.package_messages( components )
    if 'freeform' == components.selector_user_prompt_class.value:
        content = components.text_freeform_prompt.value
    else: content = components.text_canned_prompt.object
    if content:
        messages.append( __.UserMessageCanister( ).add_content( content ) )
    special_data = await _invocables.package_invocables( components )
    model = await _providers.access_model_selection( components )
    tokens_count = (
        await model.tokenizer
        .count_conversation_tokens_v0( messages, special_data ) )
    tokens_limit = model.attributes.tokens_limits.total
    tokens_report = f"{tokens_count} / {tokens_limit}"
    tokens_usage = tokens_count / tokens_limit
    if tokens_usage >= 1:
        tokens_report = f"{tokens_report} 🚫"
    elif tokens_usage >= 0.75:
        tokens_report = f"{tokens_report} \N{Warning Sign}\uFE0F"
    else: tokens_report = f"{tokens_report} 👌"
    components.text_tokens_total.value = tokens_report
    update_chat_button( components )


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
