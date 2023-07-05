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


''' Callbacks and their helpers for Panel GUI. '''


from . import base as __


@__.dataclass
class ConversationDescriptor:

    identity: str = (
        __.dataclasses.field( default_factory = lambda: __.uuid4( ).hex ) )
    timestamp: int = (
        __.dataclasses.field( default_factory = __.time_ns ) )
    title: __.typ.Optional[ str ] = None
    labels: __.AbstractMutableSequence[ str ] = (
        __.dataclasses.field( default_factory = list ) )
    gui: __.typ.Optional[ __.SimpleNamespace ] = None
    indicator: __.typ.Optional[ __.Row ] = None


class ConversationIndicator( __.ReactiveHTML ):

    clicked = __.param.Event( default = False )
    row__ = __.param.Parameter( )

    _template = (
        '''<div id="ConversationIndicator" '''
        '''onclick="${_div_click}" '''
        '''onmouseenter="${_div_mouseenter}" '''
        '''onmouseleave="${_div_mouseleave}" '''
        '''>${row__}</div>''' )

    def __init__( self, title, identity, **params ):
        from .layouts import conversation_indicator_layout as layout
        components = { }
        row = __.generate_component( components, layout, 'column_indicator' )
        row_gui = __.SimpleNamespace( **components )
        row_gui.rehtml_indicator = self
        row_gui.text_title.object = title
        self.gui__ = row_gui
        self.row__ = row
        self.identity__ = identity
        super( ).__init__( **params )

    def _div_click( self, event ):
        # TODO: Suppress event propagation from buttons contained in this.
        #       Especially for 'delete' button as this results in a
        #       'bokeh.core.serialization.DeserializationError' from
        #       an unresolved reference after deletion.
        # Cannot run callback directly. Trigger via Event parameter.
        self.clicked = True

    def _div_mouseenter( self, event ):
        self.gui__.row_actions.visible = True

    def _div_mouseleave( self, event ):
        self.gui__.row_actions.visible = False


class ConversationMessage( __.ReactiveHTML ):

    row__ = __.param.Parameter( )

    _template = (
        '''<div id="ConversationMessage" '''
        '''onmouseenter="${_div_mouseenter}" '''
        '''onmouseleave="${_div_mouseleave}" '''
        '''>${row__}</div>''' )

    def __init__( self, role, mime_type, actor_name = None, **params ):
        emoji = __.roles_emoji[ role ]
        styles = __.roles_styles[ role ]
        if 'text/plain' == mime_type:
            from .layouts import plain_conversation_message_layout as layout
        elif 'application/json' == mime_type:
            from .layouts import json_conversation_message_layout as layout
        else:
            from .layouts import rich_conversation_message_layout as layout
        components = { }
        row = __.generate_component( components, layout, 'row_message' )
        row.styles.update( styles )
        row_gui = __.SimpleNamespace( **components )
        row_gui.rehtml_message = self
        self.auxdata__ = {
            'gui': row_gui,
            'mime-type': mime_type,
            'role': role,
        }
        if actor_name: self.auxdata__[ 'actor-name' ] = actor_name
        row_gui.label_role.value = emoji
        self.gui__ = row_gui
        self.row__ = row
        super( ).__init__( **params )

    def _div_mouseenter( self, event ):
        self.gui__.row_actions.visible = True

    def _div_mouseleave( self, event ):
        self.gui__.row_actions.visible = False


def add_conversation_indicator( gui, descriptor, position = 0 ):
    indicator = ConversationIndicator( descriptor.title, descriptor.identity )
    indicator.param.watch(
        lambda event: select_conversation( gui, event ), 'clicked' )
    indicator.gui__.button_delete.on_click(
        lambda event: delete_conversation( gui, descriptor ) )
    conversations = gui.column_conversations_indicators
    if 'END' == position: conversations.append( indicator )
    else: conversations.insert( position, indicator )
    conversations.descriptors__[ descriptor.identity ] = descriptor
    descriptor.indicator = indicator


def add_conversation_indicator_if_necessary( gui ):
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    if descriptor.identity in conversations.descriptors__: return
    # TODO: Encapsulate in provider as response format may vary by provider.
    canned_prompt = gui.selector_canned_prompt.auxdata__[
        'JSON: Title + Labels' ][ 'template' ]
    messages = [
        # TODO? Regen title from more mature conversation.
        generate_messages( gui )[ 1 ],
        { 'role': 'user', 'content': canned_prompt }
    ]
    provider_name = gui.selector_provider.value
    provider = gui.selector_provider.auxdata__[ provider_name ]
    controls = dict(
        model = gui.selector_model.value,
        temperature = gui.slider_temperature.value,
    )
    chat_runner = provider.chat
    from json import loads
    from chatter.ai import ChatCallbacks, ChatCompletionError
    callbacks = ChatCallbacks(
        allocator = ( lambda mime_type: [ ] ),
        updater = ( lambda handle, content: handle.append( content ) ),
    )
    try: handle = provider.chat( messages, { }, controls, callbacks )
    # TODO: Use callbacks to signal that the title could not be generated.
    except ChatCompletionError as exc: return
    response = loads( ''.join( handle ) )
    descriptor.title = response[ 'title' ]
    descriptor.labels = response[ 'labels' ]
    add_conversation_indicator( gui, descriptor  )
    update_conversation_hilite( gui, new_descriptor = descriptor )


# TODO: Fold into initializer for ConversationMessage.
def add_message(
    gui, role, content,
    actor_name = None,
    behaviors = ( 'active', ),
    mime_type = 'text/markdown',
):
    rehtml_message = ConversationMessage(
        role, mime_type, actor_name = actor_name,
        height_policy = 'auto', margin = 0, width_policy = 'max' )
    message_gui = rehtml_message.gui__
    message_gui.parent__ = gui
    # TODO: Less intrusive supplementation.
    #       Consider multi-part MIME attachment encoding from SMTP.
    if 'Document' == role:
        content = f'''## Supplement ##\n\n{content}'''
    message_gui.text_message.object = content
    for behavior in behaviors:
        getattr( message_gui, f"toggle_{behavior}" ).value = True
    from ..messages import count_tokens
    rehtml_message.auxdata__[ 'token_count' ] = count_tokens( content )
    message_gui.toggle_active.param.watch(
        lambda event: on_toggle_message_active( message_gui, event ), 'value' )
    message_gui.toggle_pinned.param.watch(
        lambda event: on_toggle_message_pinned( message_gui, event ), 'value' )
    gui.column_conversation_history.append( rehtml_message )
    return rehtml_message


def chat( gui ):
    gui.text_status.value = 'OK'
    if gui.toggle_canned_prompt_active.value:
        prompt = gui.text_canned_prompt.object
    else:
        prompt = gui.text_input_user.value
        gui.text_input_user.value = ''
    if prompt: add_message( gui, 'Human', prompt )
    from chatter.ai import ChatCompletionError
    try: message_component = _chat( gui )
    except ChatCompletionError as exc: pass
    else:
        update_message( message_component )
        add_conversation_indicator_if_necessary( gui )
        update_and_save_conversations_index( gui )
        if gui.toggle_canned_prompt_active.value:
            gui.toggle_canned_prompt_active.value = False
            if gui.checkbox_summarize.value:
                _update_messages_post_summarization( gui )
    update_and_save_conversation( gui )


def _chat( gui ):
    messages = generate_messages( gui )
    controls = dict(
        model = gui.selector_model.value,
        temperature = gui.slider_temperature.value,
    )
    special_data = { }
    supports_functions = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'supports-functions' ]
    if supports_functions:
        special_data[ 'ai-functions' ] = _provide_active_ai_functions( gui )
    from chatter.ai import ChatCallbacks
    callbacks = ChatCallbacks(
        allocator = (
            lambda mime_type:
            add_message(
                gui, 'AI', '', behaviors = ( ), mime_type = mime_type ) ),
        deallocator = (
            lambda handle: gui.column_conversation_history.pop( -1 ) ),
        failure_notifier = (
            lambda status: setattr( gui.text_status, 'value', status ) ),
        updater = (
            lambda handle, content:
            setattr(
                handle.gui__.text_message, 'object',
                getattr( handle.gui__.text_message, 'object' ) + content ) ),
    )
    provider = gui.selector_provider.auxdata__[ gui.selector_provider.value ]
    return provider.chat( messages, special_data, controls, callbacks )


def create_and_display_conversation( gui ):
    descriptor = ConversationDescriptor( )
    create_conversation( gui, descriptor )
    update_conversation_hilite( gui, new_descriptor = descriptor )
    display_conversation( gui, descriptor )


def create_conversation( gui, descriptor ):
    from .layouts import dashboard_layout as layout
    components = gui.__dict__.copy( )
    __.generate_component( components, layout, 'column_conversation' )
    __.generate_component( components, layout, 'column_conversation_control' )
    pane_gui = __.SimpleNamespace( **components )
    pane_gui.auxdata__ = gui.auxdata__
    pane_gui.identity__ = descriptor.identity
    descriptor.gui = pane_gui
    populate_conversation( pane_gui )
    return pane_gui


def delete_conversation( gui, descriptor ):
    # TODO: Confirmation modal dialog:
    #   https://discourse.holoviz.org/t/can-i-use-create-a-modal-dialog-in-panel/1207/4
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
    conversations = gui.column_conversations_indicators
    conversations.current_descriptor__ = descriptor
    gui.__dict__.update( descriptor.gui.__dict__ )
    gui.dashboard.clear( )
    gui.dashboard.extend( (
        gui.column_conversations_manager,
        gui.column_conversation,
        gui.column_conversation_control ) )


# TODO: Provide as callback to provider-specific chat implementation.
def generate_messages( gui ):
    messages = [ ]
    model_data = gui.selector_model.auxdata__[ gui.selector_model.value ]
    if gui.toggle_system_prompt_active.value:
        system_message = gui.text_system_prompt.object
        sysprompt_honor = model_data[ 'honors-system-prompt' ]
        role = 'system' if sysprompt_honor else 'user'
        messages.append( { 'role': role, 'content': system_message } )
    supports_functions = model_data[ 'supports-functions' ]
    for row in gui.column_conversation_history:
        message_gui = row.auxdata__[ 'gui' ]
        if not message_gui.toggle_active.value: continue
        role = row.auxdata__[ 'role' ]
        # TODO? Map to provider-specific role names.
        if supports_functions and 'Function' == role: role = 'function'
        elif role in ( 'Human', 'Document', 'Function' ): role = 'user'
        else: role = 'assistant'
        message = dict(
            content = message_gui.text_message.object,
            role = role,
        )
        if 'actor-name' in row.auxdata__:
            message[ 'name' ] = row.auxdata__[ 'actor-name' ]
        messages.append( message )
    return messages


def on_canned_prompt_selection( gui, event ):
    populate_canned_prompt_variables( gui )


def on_chat_click( gui, event ): chat( gui )


def on_create_conversation( gui, event ):
    create_and_display_conversation( gui )


def on_customize_canned_prompt( gui, event ):
    gui.text_input_user.value = str( gui.text_canned_prompt.object )


def on_functions_selection( gui, event ): update_active_functions( gui )


def on_model_selection( gui, event ):
    # TODO: For models which do not explicitly support functions,
    #       weave selected functions into system prompt.
    #       Then, functions prompt row should always be visible.
    supports_functions = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'supports-functions' ]
    gui.row_functions_prompt.visible = supports_functions
    update_functions_prompt( gui )


def on_run_tool_click( gui, event ): run_tool( gui )


def on_system_prompt_selection( gui, event ):
    populate_system_prompt_variables( gui )
    update_functions_prompt( gui )


def on_search_click( gui, event ): search( gui )


def on_toggle_canned_prompt_active( gui, event ):
    canned_state = gui.toggle_canned_prompt_active.value
    user_state = gui.toggle_user_prompt_active.value
    if canned_state == user_state:
        gui.toggle_user_prompt_active.value = not canned_state
        update_and_save_conversation( gui )


def on_toggle_canned_prompt_display( gui, event ):
    gui.text_canned_prompt.visible = gui.toggle_canned_prompt_display.value


def on_toggle_functions_active( gui, event ):
    update_and_save_conversation( gui )


def on_toggle_functions_display( gui, event ):
    gui.column_functions_json.visible = gui.toggle_functions_display.value


def on_toggle_message_active( message_gui, event ):
    if not message_gui.toggle_active.value:
        message_gui.toggle_pinned.value = False
    update_and_save_conversation( message_gui.parent__ )


def on_toggle_message_pinned( message_gui, event ):
    if message_gui.toggle_pinned.value:
        message_gui.toggle_active.value = True


def on_toggle_system_prompt_active( gui, event ):
    update_and_save_conversation( gui )


def on_toggle_system_prompt_display( gui, event ):
    gui.text_system_prompt.visible = gui.toggle_system_prompt_display.value


def on_toggle_user_prompt_active( gui, event ):
    canned_state = gui.toggle_canned_prompt_active.value
    user_state = gui.toggle_user_prompt_active.value
    if canned_state == user_state:
        gui.toggle_canned_prompt_active.value = not user_state
        update_and_save_conversation( gui )


def on_user_prompt_input( gui, event ): update_and_save_conversation( gui )


def populate_conversation( gui ):
    populate_providers_selector( gui )
    populate_models_selector( gui )
    populate_system_prompts_selector( gui )
    populate_canned_prompts_selector( gui )
    populate_vectorstores_selector( gui )
    from .layouts import conversation_layout, conversation_control_layout
    register_event_callbacks(
        gui, conversation_layout, 'column_conversation' )
    register_event_callbacks(
        gui, conversation_control_layout, 'column_conversation_control' )


def populate_dashboard( gui ):
    conversations = gui.column_conversations_indicators
    conversations.descriptors__ = { }
    conversations.current_descriptor__ = ConversationDescriptor( )
    restore_conversations_index( gui )
    from .layouts import conversations_manager_layout
    register_event_callbacks(
        gui, conversations_manager_layout, 'column_conversations_manager' )
    create_and_display_conversation( gui )


def populate_models_selector( gui ):
    provider = gui.selector_provider.auxdata__[
        gui.selector_provider.value ].provide_models
    models = provider( )
    gui.selector_model.options = list( models.keys( ) )
    gui.selector_model.auxdata__ = models


def populate_providers_selector( gui ):
    from ..ai import registry
    gui.selector_provider.options = list( registry.keys( ) )
    gui.selector_provider.auxdata__ = registry


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
    _populate_prompts_selector(
        gui.selector_system_prompt, __.Path( '.local/data/system-prompts' ) )
    populate_system_prompt_variables( gui )


def populate_canned_prompt_variables( gui ):
    _populate_prompt_variables(
        gui,
        'row_canned_prompt_variables',
        'selector_canned_prompt',
        update_canned_prompt_text )
    update_summarization_toggle( gui )


def populate_canned_prompts_selector( gui ):
    _populate_prompts_selector(
        gui.selector_canned_prompt, __.Path( '.local/data/canned-prompts' ) )
    populate_canned_prompt_variables( gui )


def populate_vectorstores_selector( gui ):
    vectorstores = gui.auxdata__[ 'vectorstores' ]
    gui.selector_vectorstore.options = list( vectorstores.keys( ) )


def register_event_callbacks( gui, layout, component_name ):
    entry = layout[ component_name ]
    elements = [ ]
    for element_name in entry.get( 'contains', ( ) ):
        register_event_callbacks( gui, layout, element_name )
    component = getattr( gui, component_name )
    functions = entry.get( 'event_functions', { } )
    for event_name, function_name in functions.items( ):
        # TODO: Use passed registry rather than current module attributes.
        function = globals( )[ function_name ]
        if 'on_click' == event_name:
            component.on_click( lambda event: function( gui, event ) )
            continue
        component.param.watch(
            lambda event: function( gui, event ), event_name )


def restore_conversation( gui ):
    from json import load
    from .layouts import conversation_layout, conversation_control_layout
    layout = dict( **conversation_layout, **conversation_control_layout )
    path = __.calculate_conversations_path( gui ) / f"{gui.identity__}.json"
    with path.open( ) as file: state = load( file )
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


def restore_conversation_messages( gui, column_name, state ):
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
    conversations_path = __.calculate_conversations_path( gui )
    index_path = conversations_path / 'index.toml'
    if not index_path.exists( ): return save_conversations_index( gui )
    from tomli import load
    with index_path.open( 'rb' ) as file:
        descriptors = load( file )[ 'descriptors' ]
    for descriptor in descriptors:
        add_conversation_indicator(
            gui, ConversationDescriptor( **descriptor ), position = 'END' )
    sort_conversations_index( gui ) # extra sanity


def restore_prompt_variables( gui, row_name, state ):
    for widget_state, widget in zip(
        state.get( row_name, ( ) ), getattr( gui, row_name )
    ):
        # TODO: Sanity check widget names.
        widget.value = widget_state[ 'value' ]


# TODO: Report and display proper errors.
def run_tool( gui ):
    # TODO: Disable button when it should not be able to be run.
    #       Then we can remove the checks here.
    if 0 == len( gui.column_conversation_history ): raise RuntimeError
    rehtml_message = gui.column_conversation_history[ -1 ]
    role = rehtml_message.auxdata__[ 'role' ]
    if 'AI' != role: raise RuntimeError
    message = rehtml_message.gui__.text_message.object
    # TODO: Handle multipart MIME.
    from json import dumps, loads
    try: data = loads( message )
    except: raise ValueError
    if not isinstance( data, __.AbstractDictionary ): raise ValueError
    if 'name' not in data: raise ValueError
    name = data[ 'name' ]
    arguments = data.get( 'arguments', { } )
    ai_functions = gui.auxdata__[ 'ai-functions' ]
    # TODO: Check against multichoice values instead.
    if name not in ai_functions: raise ValueError
    result = ai_functions[ name ]( **arguments )
    add_message(
        gui, 'Function', dumps( result ),
        actor_name = name,
        mime_type = 'application/json' )
    chat( gui )


def save_conversation( gui ):
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    # Do not save conversation before first chat completion.
    if descriptor.identity not in conversations.descriptors__: return
    # Do not save conversation while populating it.
    if descriptor.identity != gui.identity__: return
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
    from json import dump
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


def search( gui ):
    # TODO: Disable button if no vectorstore available.
    if not gui.selector_vectorstore.value: return
    gui.text_status.value = 'OK'
    prompt = gui.text_input_user.value
    gui.text_input_user.value = ''
    if not prompt: return
    add_message( gui, 'Human', prompt )
    documents_count = gui.slider_documents_count.value
    if not documents_count: return
    vectorstore = gui.auxdata__[ 'vectorstores' ][
        gui.selector_vectorstore.value ][ 'instance' ]
    documents = vectorstore.similarity_search( prompt, k = documents_count )
    for document in documents:
        # TODO: Determine MIME type from document metadata, if available.
        add_message(
            gui, 'Document', document.page_content, mime_type = 'text/plain' )
    update_and_save_conversation( gui )


def select_conversation( gui, event ):
    conversations = gui.column_conversations_indicators
    old_descriptor = conversations.current_descriptor__
    new_id = event.obj.identity__
    new_descriptor = conversations.descriptors__[ new_id ]
    if old_descriptor.identity == new_id: return
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
    available_functions = gui.auxdata__[ 'ai-functions' ]
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
    update_token_count( gui )
    save_conversation( gui )


def update_and_save_conversations_index( gui ):
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


def update_conversation_timestamp( gui ):
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    descriptor.timestamp = __.time_ns( )
    # If already at top, no need to sort again.
    if conversations[ 0 ] is descriptor.indicator: return
    sort_conversations_index( gui )


def update_functions_prompt( gui ):
    gui.multichoice_functions.value = [ ]
    sprompt_data = gui.selector_system_prompt.auxdata__[
        gui.selector_system_prompt.value ]
    available_functions = gui.auxdata__[ 'ai-functions' ]
    associated_functions = sprompt_data.get( 'associated-functions', { } )
    gui.multichoice_functions.options = [
        function_name for function_name in available_functions.keys( )
        if function_name in associated_functions ]
    gui.multichoice_functions.value = [
        function_name for function_name in available_functions.keys( )
        if associated_functions.get( function_name, False ) ]
    update_active_functions( gui )


def update_summarization_toggle( gui ):
    gui.checkbox_summarize.value = gui.selector_canned_prompt.auxdata__[
        gui.selector_canned_prompt.value ].get( 'summarizes', False )


def update_message( message_row, behaviors = ( 'active', ) ):
    message_gui = message_row.gui__
    for behavior in ( 'active', 'pinned' ):
        getattr( message_gui, f"toggle_{behavior}" ).value = (
            behavior in behaviors )
    content = message_gui.text_message.object
    from ..messages import count_tokens
    message_row.auxdata__[ 'token_count' ] = count_tokens( content )


def update_system_prompt_text( gui ):
    _update_prompt_text(
        gui,
        'row_system_prompt_variables',
        'selector_system_prompt',
        'text_system_prompt' )
    if gui.toggle_system_prompt_active.value:
        update_and_save_conversation( gui )


def update_token_count( gui ):
    from ..messages import count_tokens
    tokens_total = 0
    if gui.toggle_system_prompt_active.value:
        tokens_total += count_tokens( gui.text_system_prompt.object )
    supports_functions = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'supports-functions' ]
    if supports_functions and gui.toggle_functions_active.value:
        for pane in gui.column_functions_json:
            tokens_total += count_tokens( pane.object )
    # else, included as part of system prompt
    for row in gui.column_conversation_history:
        message_gui = row.gui__
        if message_gui.toggle_active.value:
            tokens_total += row.auxdata__[ 'token_count' ]
    if gui.toggle_canned_prompt_active.value:
        tokens_total += count_tokens( gui.text_canned_prompt.object )
    if gui.toggle_user_prompt_active.value:
        tokens_total += count_tokens( gui.text_input_user.value )
    tokens_limit = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'tokens-limit' ]
    # TODO: Change color of text, depending on percentage of tokens limit.
    gui.text_tokens_total.value = f"{tokens_total} / {tokens_limit}"


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
        default = variable[ 'default' ]
        if 'text' == species:
            component = TextInput( name = label, value = default )
        elif 'boolean' == species:
            component = Checkbox( name = label, value = default )
        elif 'options' == species:
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


def _populate_prompts_selector( gui_selector, prompts_directory ):
    from yaml import safe_load
    auxdata = { }; prompt_names = [ ]
    for prompt_path in (
        prompts_directory.resolve( strict = True ).glob( '*.yaml' )
    ):
        with prompt_path.open( ) as file:
            contents = safe_load( file )
            id_ = contents[ 'id' ]
            auxdata[ id_ ] = contents
            prompt_names.append( id_ )
    gui_selector.auxdata__ = auxdata
    gui_selector.options = prompt_names


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


def _update_messages_post_summarization( gui ):
    ''' Exclude conversation items above summarization request. '''
    # TODO: Account for documents.
    for i in range( len( gui.column_conversation_history ) - 2 ):
        message_gui = gui.column_conversation_history[ i ].auxdata__[ 'gui' ]
        if not message_gui.toggle_active.value: continue # already inactive
        if message_gui.toggle_pinned.value: continue # skip pinned messages
        message_gui.toggle_active.value = False


def _update_prompt_text( gui, row_name, selector_name, text_prompt_name ):
    row = getattr( gui, row_name )
    selector = getattr( gui, selector_name )
    text_prompt = getattr( gui, text_prompt_name )
    template = selector.auxdata__[ selector.value ][ 'template' ]
    variables = { element.auxdata__[ 'id' ]: element.value for element in row }
    from mako.template import Template
    text_prompt.object = Template( template ).render( **variables )
