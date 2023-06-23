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
    row = __.param.Parameter( )

    _template = (
        '''<div id="ConversationIndicator" onclick="${_div_click}">'''
        '''${row}</div>''' )

    def __init__( self, title, identity, **params ):
        from .layouts import conversation_indicator_layout as layout
        components = { }
        row = generate_component( components, layout, 'row_indicator' )
        row_gui = __.SimpleNamespace( **components )
        row_gui.text_title.object = title
        self.gui = row_gui
        self.row = row
        self.identity = identity
        super( ).__init__( **params )

    def _div_click( self, event ):
        # Cannot run callback directly. Trigger via Event parameter.
        self.clicked = True


def add_conversation_indicator( gui, descriptor, position = 0 ):
    # TODO: Handle style to indicate active/previous/unloaded conversation.
    indicator = ConversationIndicator(
        descriptor.title, descriptor.identity,
        height_policy = 'fit',
        width_policy = 'max' )
    indicator.param.watch(
        lambda event: select_conversation( gui, event ), 'clicked' )
    conversations = gui.column_conversations_indicators
    if 'END' == position: conversations.append( indicator )
    else: conversations.insert( position, indicator )
    conversations.descriptors__[ descriptor.identity ] = descriptor
    descriptor.indicator = indicator


def add_conversation_indicator_if_necessary( gui ):
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    if descriptor.identity in conversations.descriptors__: return
    summarization_prompt = gui.selector_summarization_prompt.metadata__[
        'Title + Labels' ][ 'template' ]
    messages = [
        generate_messages( gui )[ 1 ],
        { 'role': 'user', 'content': summarization_prompt }
    ]
    provider_name = gui.selector_provider.value
    provider = gui.selector_provider.auxiliary_data__[ provider_name ]
    model = gui.selector_model.value
    controls = dict( temperature = gui.slider_temperature.value )
    chat_runner = provider[ 'chat-runner' ]
    from json import loads
    try: response = loads( chat_runner( model, messages, **controls ) )
    # TODO: Find a way to signal that the title could not be generated.
    except ChatCompletionError as exc: return
    descriptor.title = response[ 'title' ]
    descriptor.labels = response[ 'labels' ]
    add_conversation_indicator( gui, descriptor  )


def add_message( gui, role, content, behaviors = ( '💬', ) ):
    from ..messages import count_tokens
    styles = { 'background-color': 'White' }
    if 'Document' == role:
        content = f'''## Supplement ##\n\n{content}'''
        emoji = '📄'
        styles.update( {
            'border-top': '2px dashed LightGray',
            'padding': '3px'
        } )
    elif 'AI' == role:
        emoji = '🤖'
        styles.update( { 'background-color': 'WhiteSmoke' } )
    else: emoji = '🧑'
    # TODO: Choose layout based on MIME type of content rather than role.
    if role in ( 'Document', ):
        from .layouts import plain_conversation_message_layout as layout
    else:
        from .layouts import rich_conversation_message_layout as layout
    components = { }
    row = generate_component( components, layout, 'row_message' )
    row.styles = styles
    row_gui = __.SimpleNamespace( **components )
    row.auxiliary_data__ = {
        'gui': row_gui,
        'role': role,
        'token_count': count_tokens( content ),
    }
    row_gui.label_role.value = emoji
    row_gui.text_message.object = content
    row_gui.checkbuttons_behaviors.value = behaviors
    row_gui.checkbuttons_behaviors.param.watch(
        lambda event: update_and_save_conversation( gui ), 'value' )
    gui.column_conversation_history.append( row )
    return row_gui


def create_and_display_conversation( gui ):
    descriptor = ConversationDescriptor( )
    create_conversation( gui, descriptor )
    display_conversation( gui, descriptor )


def create_conversation( gui, descriptor ):
    from .layouts import dashboard_layout as layout
    components = gui.__dict__.copy( )
    generate_component( components, layout, 'column_conversation' )
    generate_component( components, layout, 'column_conversation_control' )
    pane_gui = __.SimpleNamespace( **components )
    pane_gui.auxiliary_data__ = gui.auxiliary_data__
    pane_gui.identity__ = descriptor.identity
    descriptor.gui = pane_gui
    populate_conversation( pane_gui )
    register_conversation_callbacks( pane_gui )
    return pane_gui


def display_conversation( gui, descriptor ):
    conversations = gui.column_conversations_indicators
    conversations.current_descriptor__ = descriptor
    gui.__dict__.update( descriptor.gui.__dict__ )
    gui.dashboard.clear( )
    gui.dashboard.extend( (
        gui.column_conversations_manager,
        gui.column_conversation,
        gui.column_conversation_control ) )


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


def generate_messages( gui ):
    system_message = gui.text_system_prompt.object
    sysprompt_honor = gui.selector_model.metadata__[
        gui.selector_model.value ][ 'honors-system-prompt' ]
    role = 'system' if sysprompt_honor else 'user'
    messages = [ { 'role': role, 'content': system_message } ]
    for message_gui in map(
        lambda row: row.auxiliary_data__[ 'gui' ],
        gui.column_conversation_history
    ):
        if '💬' not in message_gui.checkbuttons_behaviors.value: continue
        role = message_gui.row_message.auxiliary_data__[ 'role' ]
        role = 'user' if role in ( 'Human', 'Document' ) else 'assistant'
        content = message_gui.text_message.object
        messages.append( { 'role': role, 'content': content } )
    return messages


def populate_conversation( gui ):
    populate_providers_selector( gui )
    populate_models_selector( gui )
    populate_system_prompts_selector( gui )
    populate_summarization_prompts_selector( gui )
    populate_vectorstores_selector(
        gui, gui.auxiliary_data__[ 'vectorstores' ] )


def populate_dashboard( gui ):
    conversations = gui.column_conversations_indicators
    conversations.descriptors__ = { }
    conversations.current_descriptor__ = ConversationDescriptor( )
    restore_conversations_index( gui )
    create_and_display_conversation( gui )


def populate_models_selector( gui ):
    provider = gui.selector_provider.auxiliary_data__[
        gui.selector_provider.value ][ 'model-provider' ]
    models = provider( )
    gui.selector_model.options = list( models.keys( ) )
    gui.selector_model.metadata__ = models


def populate_providers_selector( gui ):
    from ..ai import registry
    gui.selector_provider.options = list( registry.keys( ) )
    gui.selector_provider.auxiliary_data__ = registry


def populate_system_prompts_selector( gui ):
    _populate_prompts_selector(
        gui.selector_system_prompt,
        __.Path( '.local/data/system-prompts' ) )
    update_system_prompt_variables( gui )


def populate_summarization_prompts_selector( gui ):
    _populate_prompts_selector(
        gui.selector_summarization_prompt,
        __.Path( '.local/data/summarization-prompts' ) )
    update_summarization_prompt_variables( gui )


def populate_vectorstores_selector( gui, vectorstores ):
    gui.selector_vectorstore.metadata__ = vectorstores
    gui.selector_vectorstore.options = list( vectorstores.keys( ) )


def register_conversation_callbacks( gui ):
    gui.button_chat.on_click( lambda event: run_chat( gui ) )
    gui.button_query.on_click( lambda event: run_query( gui ) )
    gui.checkbox_display_system_prompt.param.watch(
        lambda event: toggle_system_prompt_display( gui ), 'value' )
    gui.checkbox_summarize.param.watch(
        lambda event: toggle_summarization_prompt_display( gui ), 'value' )
    gui.selector_summarization_prompt.param.watch(
        lambda event: update_summarization_prompt_variables( gui ), 'value' )
    gui.selector_system_prompt.param.watch(
        lambda event: update_system_prompt_variables( gui ), 'value' )
    gui.text_input_user.param.watch(
        lambda event: update_and_save_conversation( gui ), 'value' )


def register_dashboard_callbacks( gui ):
    gui.button_new_conversation.on_click(
        lambda event: create_and_display_conversation( gui ) )


def restore_conversation( gui ):
    from json import load
    from .layouts import conversation_layout, conversation_control_layout
    layout = dict( **conversation_layout, **conversation_control_layout )
    path = __.calculate_conversations_path( gui ) / f"{gui.identity__}.json"
    with path.open( ) as file: state = load( file )
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        component_class = data[ 'component_class' ]
        if component_class in ( __.Button, __.HSpacer ):
            continue
        component = getattr( gui, name )
        if component_class in ( __.Column, __.Row ):
            if 'persistence_functions' not in data: continue
            restorer_name = data[ 'persistence_functions' ][ 'restore' ]
            restorer = globals( )[ restorer_name ]
            restorer( gui, component, state )
        elif hasattr( component, 'value' ):
            component.value = state[ name ][ 'value' ]
        elif hasattr( component, 'object' ):
            component.object = state[ name ][ 'value' ]
        else:
            raise ValueError(
                f"Unrecognized component class '{component_class}' "
                f"for component '{name}'." )
    update_token_count( gui )


def restore_conversation_messages( gui, column, state ):
    column.clear( )
    for row_state in state.get( 'column_conversation_history', [ ] ):
        role = row_state[ 'role' ]
        content = row_state[ 'content' ]
        behaviors = row_state[ 'behaviors' ]
        add_message( gui, role, content, behaviors = behaviors )


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


def run_chat( gui ):
    gui.text_status.value = 'OK'
    if gui.checkbox_summarize.value:
        query = gui.text_summarization_prompt.object
    else:
        query = gui.text_input_user.value
        gui.text_input_user.value = ''
    if query: add_message( gui, 'Human', query )
    messages = generate_messages( gui )
    message_gui = add_message( gui, 'AI', '', behaviors = ( ) )
    status = _run_chat( gui, message_gui, messages )
    gui.text_status.value = status
    if 'OK' == status:
        update_message( message_gui )
        add_conversation_indicator_if_necessary( gui )
        update_and_save_conversations_index( gui )
        if gui.checkbox_summarize.value:
            gui.checkbox_summarize.value = False
            _update_messages_post_summarization( gui )
    # Retract AI message display on error.
    else: gui.column_conversation_history.pop( -1 )
    update_and_save_conversation( gui )


def run_query( gui ):
    gui.text_status.value = 'OK'
    query = gui.text_input_user.value
    gui.text_input_user.value = ''
    if not query: return
    add_message( gui, 'Human', query )
    documents_count = gui.slider_documents_count.value
    if not documents_count: return
    vectorstore = gui.selector_vectorstore.metadata__[
        gui.selector_vectorstore.value ][ 'instance' ]
    documents = vectorstore.similarity_search( query, k = documents_count )
    for document in documents:
        add_message( gui, 'Document', document.page_content )
    update_and_save_conversation( gui )


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
        component_class = data[ 'component_class' ]
        if component_class in ( __.Button, __.HSpacer ):
            continue
        component = getattr( gui, name )
        if component_class in ( __.Column, __.Row ):
            if 'persistence_functions' not in data: continue
            saver_name = data[ 'persistence_functions' ][ 'save' ]
            saver = globals( )[ saver_name ]
            state.update( saver( component ) )
        elif hasattr( component, 'value' ):
            state[ name ] = dict( value = component.value )
        elif hasattr( component, 'object' ):
            state[ name ] = dict( value = component.object )
        else:
            raise ValueError(
                f"Unrecognized component class '{component_class}' "
                f"for component '{name}'." )
    from json import dump
    path = __.calculate_conversations_path( gui ) / f"{gui.identity__}.json"
    with path.open( 'w' ) as file: dump( state, file, indent = 2 )


def save_conversation_messages( column ):
    state = [ ]
    for row in column:
        message_gui = row.auxiliary_data__[ 'gui' ]
        state.append( {
            'role': row.auxiliary_data__[ 'role' ],
            # TODO: Save MIME type of content.
            'content': message_gui.text_message.object,
            'behaviors': message_gui.checkbuttons_behaviors.value,
        } )
    return { 'column_conversation_history': state }


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


def select_conversation( gui, event ):
    conversations = gui.column_conversations_indicators
    old_descriptor = conversations.current_descriptor__
    new_id = event.obj.identity
    new_descriptor = conversations.descriptors__[ new_id ]
    if old_descriptor.identity == new_id: return
    if None is new_descriptor.gui:
        new_pane_gui = create_conversation( gui, new_descriptor )
        restore_conversation( new_pane_gui )
        new_descriptor.gui = new_pane_gui
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


def toggle_summarization_prompt_display( gui ):
    gui.text_summarization_prompt.visible = gui.checkbox_summarize.value
    update_and_save_conversation( gui )


def toggle_system_prompt_display( gui ):
    gui.text_system_prompt.visible = gui.checkbox_display_system_prompt.value


def update_and_save_conversation( gui ):
    update_token_count( gui )
    save_conversation( gui )


def update_and_save_conversations_index( gui ):
    update_conversation_timestamp( gui )
    save_conversations_index( gui )


def update_conversation_timestamp( gui ):
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    descriptor.timestamp = __.time_ns( )
    # If already at top, no need to sort again.
    if conversations[ 0 ] is descriptor.indicator: return
    sort_conversations_index( gui )


def update_message( message_gui, behaviors = ( '💬', ) ):
    from ..messages import count_tokens
    message_gui.checkbuttons_behaviors.value = behaviors
    content = message_gui.text_message.object
    message_gui.row_message.auxiliary_data__[ 'token_count' ] = (
        count_tokens( content ) )


def update_prompt_text( gui, row_name, selector_name, text_prompt_name ):
    row = getattr( gui, row_name )
    selector = getattr( gui, selector_name )
    text_prompt = getattr( gui, text_prompt_name )
    template = selector.metadata__[ selector.value ][ 'template' ]
    variables = {
        element.metadata__[ 'id' ]: element.value for element in row
    }
    # TODO: Support alternative template types.
    text_prompt.object = template.format( **variables )


def update_summarization_prompt_text( gui ):
    update_prompt_text(
        gui,
        'row_summarization_prompt_variables',
        'selector_summarization_prompt',
        'text_summarization_prompt' )


def update_system_prompt_text( gui ):
    update_prompt_text(
        gui,
        'row_system_prompt_variables',
        'selector_system_prompt',
        'text_system_prompt' )
    update_and_save_conversation( gui )


def update_prompt_variables( gui, row_name, selector_name, callback ):
    from panel.widgets import TextInput
    row = getattr( gui, row_name )
    selector = getattr( gui, selector_name )
    row.clear( )
    variables = selector.metadata__[ selector.value ].get( 'variables', ( ) )
    for variable in variables:
        # TODO: Support other widget types, such as selectors and checkboxes.
        text_input = TextInput(
            name = variable[ 'label' ], value = variable[ 'default' ] )
        text_input.metadata__ = variable
        text_input.param.watch( lambda event: callback( gui ), 'value' )
        row.append( text_input )
    callback( gui )


def update_summarization_prompt_variables( gui ):
    update_prompt_variables(
        gui,
        'row_summarization_prompt_variables',
        'selector_summarization_prompt',
        update_summarization_prompt_text )


def update_system_prompt_variables( gui ):
    update_prompt_variables(
        gui,
        'row_system_prompt_variables',
        'selector_system_prompt',
        update_system_prompt_text )


def update_token_count( gui ):
    from ..messages import count_tokens
    total_tokens = 0
    for row in gui.column_conversation_history:
        message_gui = row.auxiliary_data__[ 'gui' ]
        if '💬' in message_gui.checkbuttons_behaviors.value:
            total_tokens += row.auxiliary_data__[ 'token_count' ]
    if gui.checkbox_summarize.value:
        total_tokens += count_tokens( gui.text_summarization_prompt.object )
    else:
        total_tokens += count_tokens( gui.text_input_user.value )
    total_tokens += count_tokens( gui.text_system_prompt.object )
    tokens_limit = gui.selector_model.metadata__[
        gui.selector_model.value ][ 'tokens-limit' ]
    # TODO: Change color of text, depending on percentage of tokens limit.
    gui.text_tokens_total.value = f"{total_tokens} / {tokens_limit}"


def _populate_prompts_selector( gui_selector, prompts_directory ):
    from yaml import safe_load
    metadata = { }; prompt_names = [ ]
    for prompt_path in (
        prompts_directory.resolve( strict = True ).glob( '*.yaml' )
    ):
        with prompt_path.open( ) as file:
            contents = safe_load( file )
            id_ = contents[ 'id' ]
            metadata[ id_ ] = contents
            prompt_names.append( id_ )
    gui_selector.metadata__ = metadata
    gui_selector.options = prompt_names


def _run_chat( gui, message_gui, messages ):
    from ..ai import ChatCompletionError
    provider_name = gui.selector_provider.value
    provider = gui.selector_provider.auxiliary_data__[ provider_name ]
    model = gui.selector_model.value
    controls = dict( temperature = gui.slider_temperature.value )
    chat_runner = provider.get( 'streaming-chat-runner' )
    if None is chat_runner:
        chat_runner = provider[ 'chat-runner' ]
        try:
            response = chat_runner( model, messages, **controls )
            message_gui.text_message.object = response
        except ChatCompletionError as exc: return str( exc )
    else:
        try:
            response = chat_runner( model, messages, **controls )
            for chunk in response:
                message_gui.text_message.object += chunk
        except ChatCompletionError as exc: return str( exc )
    return 'OK'


def _update_messages_post_summarization( gui ):
    ''' Exclude conversation items above summarization request. '''
    # TODO: Account for documents.
    for i in range( len( gui.column_conversation_history ) - 2 ):
        row_gui = (
            gui.column_conversation_history[ i ].auxiliary_data__[ 'gui' ] )
        behaviors = row_gui.checkbuttons_behaviors.value
        if '💬' not in behaviors: continue # already inactive, nothing to do
        if '📌' in behaviors: continue # skip pinned messages
        behaviors.remove( '💬' )
