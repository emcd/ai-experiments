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


from . import base as __


def add_conversation_indicator( gui, descriptor, position = 0 ):
    from .classes import ConversationIndicator
    from .events import on_select_conversation
    from .layouts import conversation_indicator_layout as layout
    indicator = ConversationIndicator( descriptor.title, descriptor.identity )
    indicator.param.watch(
        lambda event: on_select_conversation( gui, event ), 'clicked' )
    indicator.gui__.parent__ = gui
    __.register_event_callbacks( indicator.gui__, layout, 'column_indicator' )
    conversations = gui.column_conversations_indicators
    if 'END' == position: conversations.append( indicator )
    else: conversations.insert( position, indicator )
    conversations.descriptors__[ descriptor.identity ] = descriptor
    descriptor.indicator = indicator


def add_conversation_indicator_if_necessary( gui ):
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    if descriptor.identity in conversations.descriptors__: return
    # Do not proceed if we are in a function invocation. Wait for result.
    # Also, some models (e.g., GPT-4) are confused by the invocation.
    try: __.extract_function_invocation_request( gui )
    except Exception as exc: pass
    else: return
    try: title, labels = _generate_conversation_title( gui )
    except Exception as exc: return
    descriptor.title = title
    descriptor.labels = labels
    add_conversation_indicator( gui, descriptor  )
    update_conversation_hilite( gui, new_descriptor = descriptor )


# TODO: Mostly fold into initializer for ConversationMessage.
#       Leave append operation on the conversation history.
def add_message(
    gui, role, content,
    actor_name = None,
    behaviors = ( 'active', ),
    mime_type = 'text/markdown',
):
    from .classes import ConversationMessage
    rehtml_message = ConversationMessage(
        role, mime_type, actor_name = actor_name,
        height_policy = 'auto', margin = 0, width_policy = 'max' )
    message_gui = rehtml_message.gui__
    message_gui.parent__ = gui
    message_gui.index__ = len( gui.column_conversation_history )
    # TODO: Less intrusive supplementation.
    #       Consider multi-part MIME attachment encoding from SMTP.
    #       May need this as GPT-4 does not like consecutive user messages.
    if 'AI' == role:
        message_gui.button_fork.visible = True
    elif 'Document' == role:
        content = f'''## Supplement ##\n\n{content}'''
        message_gui.button_delete.visible = True
    elif 'Human' == role:
        message_gui.button_edit.visible = True
    text_message = message_gui.text_message
    if hasattr( text_message, 'value' ): text_message.value = content
    else: text_message.object = content
    for behavior in behaviors:
        getattr( message_gui, f"toggle_{behavior}" ).value = True
    __.register_event_callbacks(
        message_gui, message_gui.layout__, 'row_message' )
    gui.column_conversation_history.append( rehtml_message )
    return rehtml_message


def create_and_display_conversation( gui, state = None ):
    from .classes import ConversationDescriptor
    descriptor = ConversationDescriptor( )
    create_conversation( gui, descriptor, state = state )
    update_conversation_hilite( gui, new_descriptor = descriptor )
    display_conversation( gui, descriptor )


def create_conversation( gui, descriptor, state = None ):
    from . import layouts
    from .layouts import conversation_container_names
    from .persistence import inject_conversation
    # TODO: Restrict GUI namespace to conversation components.
    pane_gui = __.SimpleNamespace( **gui.__dict__ )
    for component_name in conversation_container_names:
        layout = getattr( layouts, f"{component_name}_layout" )
        __.generate_component( pane_gui, layout, f"column_{component_name}" )
    pane_gui.auxdata__ = gui.auxdata__
    pane_gui.identity__ = descriptor.identity
    pane_gui.parent__ = gui
    descriptor.gui = pane_gui
    populate_conversation( pane_gui )
    if state: inject_conversation( pane_gui, state )
    return pane_gui


def delete_conversation( gui, descriptor ):
    # TODO: Confirmation modal dialog.
    from .persistence import save_conversations_index
    conversations = gui.column_conversations_indicators
    if descriptor is conversations.current_descriptor__:
        create_and_display_conversation( gui )
    conversations.descriptors__.pop( descriptor.identity )
    descriptor.gui = None # break possible GC cycles
    indicators = [
        indicator for indicator in conversations
        if indicator.identity__ != descriptor.identity ]
    conversations.objects = indicators
    descriptor.indicator = None # break possible GC cycles
    path = __.calculate_conversations_path( gui ).joinpath(
        f"{descriptor.identity}.json" )
    if path.exists( ): path.unlink( )
    save_conversations_index( gui )


def display_conversation( gui, descriptor ):
    from .layouts import conversation_container_names
    conversations = gui.column_conversations_indicators
    conversations.current_descriptor__ = descriptor
    for component_name in conversation_container_names:
        getattr( gui, f"interpolant_{component_name}" ).objects = [
            getattr( descriptor.gui, f"column_{component_name}" ) ]
    gui.identity__ = descriptor.gui.identity__


def fork_conversation( gui, index ):
    from .persistence import collect_conversation
    state = collect_conversation( gui )
    state[ 'column_conversation_history' ] = (
        state[ 'column_conversation_history' ][ 0 : index + 1 ] )
    create_and_display_conversation( gui, state = state )


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


def populate_dashboard( gui ):
    from .classes import ConversationDescriptor
    from .layouts import conversations_manager_layout
    from .persistence import restore_conversations_index
    conversations = gui.column_conversations_indicators
    conversations.descriptors__ = { }
    conversations.current_descriptor__ = ConversationDescriptor( )
    restore_conversations_index( gui )
    __.register_event_callbacks(
        gui, conversations_manager_layout, 'column_conversations_manager' )
    create_and_display_conversation( gui )


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
    providers = gui.auxdata__.ai_providers
    gui.selector_provider.options = list( providers.keys( ) )
    # TODO: Drop this auxdata and rely on main GUI auxdata instead.
    gui.selector_provider.auxdata__ = providers


def populate_system_prompt_variables( gui ):
    _populate_prompt_variables(
        gui,
        'row_system_prompt_variables',
        'selector_system_prompt',
        update_system_prompt_text )
    # If there is a canned prompt preference, then update accordingly.
    can_update = hasattr( gui.selector_canned_prompt, 'auxdata__' )
    summarization = gui.selector_system_prompt.auxdata__[
        gui.selector_system_prompt.value ].get( 'summarization-preference' )
    if can_update and None is not summarization:
        gui.selector_canned_prompt.value = summarization[ 'id' ]
        defaults = summarization.get( 'defaults', { } )
        for i, variable in enumerate(
            gui.selector_canned_prompt.auxdata__[
                gui.selector_canned_prompt.value ].get( 'variables', ( ) )
        ):
            variable_id = variable[ 'id' ]
            if variable_id not in defaults: continue
            gui.row_canned_prompt_variables[ i ].value = defaults[
                variable_id ]


def populate_system_prompts_selector( gui ):
    _populate_prompts_selector( gui, 'system' )
    populate_system_prompt_variables( gui )


def populate_canned_prompt_variables( gui ):
    _populate_prompt_variables(
        gui,
        'row_canned_prompt_variables',
        'selector_canned_prompt',
        update_canned_prompt_text )
    update_summarization_toggle( gui )


def populate_canned_prompts_selector( gui ):
    _populate_prompts_selector( gui, 'canned' )
    populate_canned_prompt_variables( gui )


def populate_vectorstores_selector( gui ):
    vectorstores = gui.auxdata__.vectorstores
    gui.selector_vectorstore.options = list( vectorstores.keys( ) )
    update_search_button( gui )


def select_conversation( gui, identity ):
    conversations = gui.column_conversations_indicators
    old_descriptor = conversations.current_descriptor__
    new_descriptor = conversations.descriptors__[ identity ]
    if old_descriptor.identity == identity: return
    from .persistence import restore_conversation
    if None is new_descriptor.gui:
        new_pane_gui = create_conversation( gui, new_descriptor )
        restore_conversation( new_pane_gui )
        new_descriptor.gui = new_pane_gui
    update_conversation_hilite( gui, new_descriptor = new_descriptor )
    display_conversation( gui, new_descriptor )


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


def update_active_functions( gui ):
    available_functions = gui.auxdata__.ai_functions
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


def update_and_save_conversation( gui ):
    from .persistence import save_conversation
    update_token_count( gui )
    save_conversation( gui )


def update_and_save_conversations_index( gui ):
    from .persistence import save_conversations_index
    update_conversation_timestamp( gui )
    update_conversation_hilite( gui )
    save_conversations_index( gui )


def update_canned_prompt_text( gui ):
    _update_prompt_text(
        gui,
        'row_canned_prompt_variables',
        'selector_canned_prompt',
        'text_canned_prompt' )
    if gui.toggle_canned_prompt_active.value:
        update_and_save_conversation( gui )


def update_chat_button( gui ):
    gui.button_chat.disabled = not (
            not gui.text_tokens_total.value.endswith( '🚫' )
        and (   gui.toggle_canned_prompt_active.value
             or gui.text_input_user.value ) )


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
    # Hack: Reload indicators to force repaint.
    indicators = [ indicator for indicator in conversations ]
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
            text = str( text )
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
        associated_functions = gui.selector_system_prompt.auxdata__[
            gui.selector_system_prompt.value ].get(
                'associated-functions', { } )
    else: associated_functions = { }
    available_functions = gui.auxdata__.ai_functions
    gui.multichoice_functions.value = [ ]
    gui.multichoice_functions.options = [
        function_name for function_name in available_functions.keys( )
        if function_name in associated_functions ]
    gui.multichoice_functions.value = [
        function_name for function_name in available_functions.keys( )
        if associated_functions.get( function_name, False ) ]
    update_active_functions( gui )


def update_message( message_row, behaviors = ( 'active', ) ):
    message_gui = message_row.gui__
    for behavior in ( 'active', 'pinned' ):
        getattr( message_gui, f"toggle_{behavior}" ).value = (
            behavior in behaviors )
    content = message_gui.text_message.object


def update_messages_post_summarization( gui ):
    ''' Exclude conversation items above summarization request. '''
    # TODO: Account for documents.
    for i in range( len( gui.column_conversation_history ) - 2 ):
        message_gui = gui.column_conversation_history[ i ].auxdata__[ 'gui' ]
        if not message_gui.toggle_active.value: continue # already inactive
        if message_gui.toggle_pinned.value: continue # skip pinned messages
        message_gui.toggle_active.value = False


def update_run_tool_button( gui, allow_autorun = False ):
    disabled = 0 == len( gui.column_conversation_history )
    if not disabled:
        rehtml_message = gui.column_conversation_history[ -1 ]
        disabled = 'AI' != rehtml_message.auxdata__[ 'role' ]
    if not disabled:
        message_gui = rehtml_message.gui__
        disabled = not message_gui.toggle_active.value
    if not disabled:
        try: __.extract_function_invocation_request( gui )
        except ValueError: disabled = True
    from .actions import run_tool
    allow_autorun = allow_autorun and gui.checkbox_auto_functions.value
    if not disabled and allow_autorun:
        gui.button_run_tool.disabled = True
        run_tool( gui )
    else: gui.button_run_tool.disabled = disabled


def update_search_button( gui ):
    gui.button_search.disabled = not (
            gui.selector_vectorstore.value
        and gui.slider_documents_count.value
        and gui.text_input_user.value )


def update_summarization_toggle( gui ):
    summarizes = gui.selector_canned_prompt.auxdata__[
        gui.selector_canned_prompt.value ].get( 'summarizes', False )
    gui.toggle_summarize.value = (
        gui.toggle_canned_prompt_active.value and summarizes )


def update_system_prompt_text( gui ):
    _update_prompt_text(
        gui,
        'row_system_prompt_variables',
        'selector_system_prompt',
        'text_system_prompt' )
    if gui.toggle_system_prompt_active.value:
        update_and_save_conversation( gui )


def update_token_count( gui ):
    if not gui.selector_provider.options: return
    if not gui.selector_model.options: return
    messages = __.package_messages( gui )
    if gui.toggle_canned_prompt_active.value:
        messages.append( dict(
            content = gui.text_canned_prompt.object, role = 'Human',
        ) )
    elif gui.toggle_user_prompt_active.value:
        messages.append( dict(
            content = gui.text_input_user.value, role = 'Human',
        ) )
    controls = __.package_controls( gui )
    special_data = __.package_special_data( gui )
    provider = gui.auxdata__.ai_providers[ gui.selector_provider.value ]
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


def _generate_conversation_title( gui ):
    # TODO: Use model-preferred serialization format for title and labels.
    from json import JSONDecodeError, loads
    from ..ai.providers import ChatCallbacks, ChatCompletionError
    from ..messages import render_prompt_template
    template = gui.selector_canned_prompt.auxdata__[
        'JSON: Title + Labels' ][ 'template' ]
    controls = __.package_controls( gui )
    prompt = render_prompt_template( template, controls )
    messages = [
        *__.package_messages( gui )[ 1 : ],
        { 'role': 'Human', 'content': prompt }
    ]
    provider = gui.selector_provider.auxdata__[
        gui.selector_provider.value ]
    # TODO: Use standard set of text capture callbacks.
    callbacks = ChatCallbacks(
        allocator = ( lambda mime_type: [ ] ),
        updater = ( lambda handle, content: handle.append( content ) ),
    )
    update_conversation_status(
        gui, text = 'Generating conversation title...', progress = True )
    try: handle = provider.chat( messages, { }, controls, callbacks )
    except ChatCompletionError as exc:
        update_conversation_status( gui, text = exc )
        raise
    try: response = loads( ''.join( handle ) )
    except JSONDecodeError as exc:
        update_conversation_status( gui, text = exc )
        raise
    update_conversation_status( gui )
    return response[ 'title' ], response[ 'labels' ]


def _populate_prompt_variables( gui, row_name, selector_name, callback ):
    from panel.widgets import Checkbox, Select, TextInput
    row = getattr( gui, row_name )
    selector = getattr( gui, selector_name )
    row.clear( )
    variables = selector.auxdata__[ selector.value ].get( 'variables', ( ) )
    for variable in variables:
        # TODO: Validation of template variables.
        species = variable.get( 'species', 'text' )
        label = variable[ 'label' ]
        if 'text' == species:
            default = variable.get( 'default', '' )
            component = TextInput( name = label, value = default )
        elif 'boolean' == species:
            default = variable.get( 'default', False )
            component = Checkbox( name = label, value = default )
        elif 'options' == species:
            default = variable.get( 'default', variable[ 'options' ][ 0 ] )
            component = Select(
                name = label,
                options = variable[ 'options' ],
                value = default )
        else:
            raise ValueError(
                f"Invalid component species, '{species}', "
                f"for prompt variable '{name}'." )
        component.param.watch( lambda event: callback( gui ), 'value' )
        component.auxdata__ = variable
        row.append( component )
    callback( gui )


def _populate_prompts_selector( gui, template_class ):
    selector = getattr( gui, f"selector_{template_class}_prompt" )
    templates = getattr( gui.auxdata__.prompt_templates, template_class )
    selector.auxdata__ = templates # TODO: Remove this reference.
    prompt_names = [ ]
    for name, data in templates.items( ):
        if data.get( 'conceal', False ): continue
        prompt_names.append( name )
    prompt_names.sort( )
    selector.options = prompt_names


def _update_prompt_text( gui, row_name, selector_name, text_prompt_name ):
    row = getattr( gui, row_name )
    selector = getattr( gui, selector_name )
    text_prompt = getattr( gui, text_prompt_name )
    template = selector.auxdata__[ selector.value ][ 'template' ]
    controls = __.package_controls( gui )
    variables = { element.auxdata__[ 'id' ]: element.value for element in row }
    from ..messages import render_prompt_template
    text_prompt.object = render_prompt_template(
        template, controls, variables )
