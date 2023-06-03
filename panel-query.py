def add_to_conversation( role, content, gui, kind = '' ):
    from panel import Column, Row
    from panel.pane import Markdown
    from panel.widgets import Checkbox, StaticText
    conversation_history = gui.column_conversation_history
    if 'supplement' == kind:
        content = f'''## Supplement ##\n\n{content}'''
        emoji = '📄'
        message_cell = StaticText(
            value = content,
            height_policy = 'fit',
            sizing_mode = 'stretch_width',
            style = { 'background-color': 'WhiteSmoke' } )
    else:
        if 'AI' == role:
            emoji = '🤖'
            style = {
                'border': '2px solid LightGray',
                'padding': '3px',
            }
        else:
            emoji = '🧑'
            style = { 'background-color': 'White' }
        message_cell = Markdown(
            content,
            height_policy = 'fit',
            sizing_mode = 'stretch_width',
            style = style )
    message_cell.metadata = {
        'role': role,
        'token_count': count_tokens( content ),
    }
    checkbox = Checkbox( name = emoji, value = True, width = 40 )
    checkbox.param.watch( lambda event: update_token_count( gui ), 'value' )
    new_item = Row(
        checkbox,
        message_cell,
        # TODO: Copy button, edit button, etc...
    )
    conversation_history.append( new_item )
    return new_item


def count_tokens( content ):
    from tiktoken import get_encoding
    encoding = get_encoding( 'cl100k_base' )
    return len( encoding.encode( content ) )


SYSTEM_MESSAGE_AWARE_MODELS = frozenset( ( 'gpt-4', ) )
def generate_messages( gui ):
    system_message = gui.text_input_system.value
    model = gui.selector_model.value
    if model not in SYSTEM_MESSAGE_AWARE_MODELS: role = 'user'
    else: role = 'system'
    messages = [ { 'role': role, 'content': system_message } ]
    for item in gui.column_conversation_history:
        if not item[ 0 ].value: continue # if checkbox is not checked
        role = (
            'user' if item[ 1 ].metadata[ 'role' ] in ( 'Human', 'Document' )
            else 'assistant' )
        content = item[ 1 ].object
        messages.append( { 'role': role, 'content': content } )
    return messages


def layout_gui( real, spec, index ):
    entry = spec[ index ]
    elements = [ ]
    for element_index in entry.get( 'contains', ( ) ):
        elements.append( layout_gui( real, spec, element_index ) )
    component_class = entry[ 'component_class' ]
    component_arguments = entry.get( 'component_arguments', { } )
    component = component_class( *elements, **component_arguments )
    real[ index ] = component
    return component


def load_vectorstore( ):
    from pathlib import Path
    from pickle import load
    vectorstore_path = Path( 'vectorstore.pypickle' )
    with vectorstore_path.open( 'rb' ) as file: vectorstore = load( file )
    return vectorstore


def main( ):
    from types import SimpleNamespace
    import openai
    import panel
    openai_credentials = provide_credentials( )
    openai.api_key = openai_credentials[ 'openai_api_key' ]
    openai.organization = openai_credentials[ 'openai_organization' ]
    gui = { }
    dashboard = layout_gui( gui, prepare_gui_layout( ), 'dashboard' )
    gui = SimpleNamespace( **gui )
    populate_models_selection( gui )
    vectorstore = load_vectorstore( )
    register_gui_callbacks( gui, vectorstore )
    panel.serve( dashboard, start = True )


def populate_models_selection( gui ):
    # TODO: Use API-appropriate call.
    from operator import itemgetter
    import openai
    models = sorted( map(
        itemgetter( 'id' ),
        openai.Model.list( ).to_dict_recursive( )[ 'data' ] ) )
    gui.selector_model.options = models


def prepare_gui_layout( ):
    from panel import Column, Row
    from panel.layout import HSpacer
    from panel.widgets import Button, FloatSlider, IntSlider, Select
    from panel.widgets.input import StaticText, TextAreaInput
    return {
        'dashboard': dict(
            component_class = Row,
            contains = [
                'left_pane',
                'left_spacer',
                'center_pane',
                'right_spacer',
                'right_pane',
            ]
        ),
        'left_pane': dict(
            component_class = Column,
            component_arguments = dict( width = 640 ),
            contains = [
                'button_new_conversation',
                'column_conversations_index',
            ],
        ),
        'left_spacer': dict( component_class = HSpacer ),
        'center_pane': dict(
            component_class = Column,
            component_arguments = dict(
                sizing_mode = 'stretch_height', width = 1024,
            ),
            contains = [
                'row_system_prompt',
                'column_conversation_history',
                'row_user_prompt',
                'row_actions',
            ],
        ),
        'right_spacer': dict( component_class = HSpacer ),
        'right_pane': dict(
            component_class = Column,
            contains = [
                'selector_model',
                'slider_temperature',
                'slider_documents_count',
                'text_tokens_total',
                'text_status',
            ],
        ),
        'button_new_conversation': dict(
            component_class = Button,
            component_arguments = dict(
                name = 'New Conversation',
                width_policy = 'min',
            ),
        ),
        'column_conversations_index': dict( component_class = Column ),
        'row_system_prompt': dict(
            component_class = Row,
            contains = [ 'label_system', 'text_input_system' ],
        ),
        'column_conversation_history': dict(
            component_class = Column,
            component_arguments = dict( sizing_mode = 'stretch_both' ),
        ),
        'row_user_prompt': dict(
            component_class = Row,
            contains = [ 'label_user', 'text_input_user' ],
        ),
        'row_actions': dict(
            component_class = Row,
            contains = [ 'button_chat', 'button_query' ],
        ),
        'selector_model': dict(
            component_class = Select,
            component_arguments = dict(
                name = 'Model',
                options = [ 'gpt-3.5-turbo' ],
                value = 'gpt-3.5-turbo',
            ),
        ),
        'slider_temperature': dict(
            component_class = FloatSlider,
            component_arguments = dict(
                name = 'Temperature',
                start = 0, end = 2, step = 0.1, value = 0,
            ),
        ),
        'slider_documents_count': dict(
            component_class = IntSlider,
            component_arguments = dict(
                name = 'Number of Documents',
                start = 0, end = 5, step = 1, value = 3,
            ),
        ),
        'text_tokens_total': dict(
            component_class = StaticText,
            component_arguments = dict( name = 'Token Counter', value = '0', ),
        ),
        'text_status': dict(
            component_class = StaticText,
            component_arguments = dict( name = 'Status', value = 'OK', ),
        ),
        'label_system': dict(
            component_class = StaticText,
            component_arguments = dict( value = '💬📏', width = 40, ),
        ),
        'text_input_system': dict(
            component_class = TextAreaInput,
            component_arguments = dict(
                height_policy = 'fit',
                max_height = 480,
                placeholder = 'Enter system message here...',
                value = '',
                width_policy = 'max',
            ),
        ),
        'label_user': dict(
            component_class = StaticText,
            component_arguments = dict( value = '💬🧑', width = 40, ),
        ),
        'text_input_user': dict(
            component_class = TextAreaInput,
            component_arguments = dict(
                height_policy = 'fit',
                max_height = 480,
                placeholder = 'Enter user message here...',
                value = '',
                width_policy = 'max',
            ),
        ),
        'button_chat': dict(
            component_class = Button,
            component_arguments = dict( name = 'Chat' ),
        ),
        'button_query': dict(
            component_class = Button,
            component_arguments = dict( name = 'Query' ),
        ),
    }


def provide_credentials( ):
    import tomli as tomllib
    with open(
        '.local/configuration/credentials.toml', 'rb'
    ) as credentials_file: credentials = tomllib.load( credentials_file )
    return dict(
        openai_api_key = credentials[ 'openai' ][ 'token' ],
        openai_organization = credentials[ 'openai' ][ 'organization' ] )


def register_gui_callbacks( gui, vectorstore ):
    gui.button_chat.on_click( lambda event: run_chat( event, gui ) )
    gui.button_query.on_click(
        lambda event: run_query( event, gui, vectorstore ) )
    gui.text_input_system.param.watch(
        lambda event: update_token_count( gui ), 'value' )
    gui.text_input_user.param.watch(
        lambda event: update_token_count( gui ), 'value' )


def run_chat( event, gui ):
    gui.text_status.value = 'OK'
    from openai import ChatCompletion, OpenAIError
    query = gui.text_input_user.value
    if query:
        add_to_conversation( 'Human', query, gui )
        gui.text_input_user.value = ''
    messages = generate_messages( gui )
    try:
        response = ChatCompletion.create(
            messages = messages,
            model = gui.selector_model.value,
            temperature = gui.slider_temperature.value )
        add_to_conversation(
            'AI', response.choices[ 0 ].message[ 'content' ].strip( ), gui )
    except OpenAIError as exc: gui.text_status.value = f"Error: {exc}"
    update_token_count( gui )


def run_query( event, gui, vectorstore ):
    gui.text_status.value = 'OK'
    query = gui.text_input_user.value
    if not query: return
    add_to_conversation( 'Human', query, gui )
    gui.text_input_user.value = ''
    documents_count = gui.slider_documents_count.value
    if not documents_count: return
    documents = vectorstore.similarity_search( query, k = documents_count )
    for document in documents:
        add_to_conversation(
            'Human', document.page_content, gui, kind = 'supplement' )
    update_token_count( gui )


def update_token_count( gui ):
    total_tokens = 0
    for item in gui.column_conversation_history:
        checkbox, message_cell = item
        if checkbox.value:
            total_tokens += message_cell.metadata[ 'token_count' ]
    total_tokens += count_tokens( gui.text_input_user.value )
    total_tokens += count_tokens( gui.text_input_system.value )
    gui.text_tokens_total.value = str( total_tokens )


if __name__ == "__main__": main( )
