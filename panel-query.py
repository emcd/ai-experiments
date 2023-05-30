def add_to_conversation( role, content, gui_items, kind = '' ):
    from panel import Column, Row
    from panel.pane import Markdown
    from panel.widgets import Checkbox, StaticText
    conversation_history = gui_items[ 'center' ][ 'conversation_history' ]
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
                'border-left': '2px solid LightGray',
                'border-right': '2px solid LightGray',
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
    checkbox.param.watch(
        lambda event: update_token_count( gui_items ), 'value' )
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


def create_dashboard( gui_items ):
    from panel import Column, Row
    from panel.layout import HSpacer
    return Row(
        Column( *gui_items[ 'left' ].values( ), width = 640 ),
        Row(
            HSpacer( ),
            Column(
                *gui_items[ 'center' ].values( ),
                sizing_mode = 'stretch_height', width = 1024 ),
            HSpacer( ),
            Column( *gui_items[ 'right' ].values( ) ),
        )
    )


SYSTEM_MESSAGE_AWARE_MODELS = frozenset( ( 'gpt-4', ) )
def generate_messages( gui_items ):
    system_message = gui_items[ 'center' ][ 'text_input_system' ].value
    model = gui_items[ 'right' ][ 'selector_model' ].value
    if model not in SYSTEM_MESSAGE_AWARE_MODELS: role = 'user'
    else: role = 'system'
    messages = [ { 'role': role, 'content': system_message } ]
    for item in gui_items[ 'center' ][ 'conversation_history' ]:
        if not item[ 0 ].value: continue # if checkbox is not checked
        role = (
            'user' if item[ 1 ].metadata[ 'role' ] in ( 'Human', 'Document' )
            else 'assistant' )
        content = item[ 1 ].object
        messages.append( { 'role': role, 'content': content } )
    return messages


def layout_gui( ):
    from panel import Column
    from panel.widgets import Button, FloatSlider, IntSlider, Select
    from panel.widgets.input import StaticText, TextAreaInput
    gui_items = {
        'left': {
            'conversations_index': Column( ),
        },
        'center': {
            'text_input_system': TextAreaInput(
                height_policy = 'fit',
                max_height = 480,
                name = 'System Message',
                placeholder = 'Enter system message here...', value = '' ),
            'conversation_history': Column( sizing_mode = 'stretch_both' ),
            'text_input_user': TextAreaInput(
                align = ( 'start', 'end' ),
                height_policy = 'fit',
                max_height = 480,
                name = 'User Message',
                placeholder = 'Enter user message here...', value = '' ),
        },
        'right': {
            'selector_model': Select(
                name = 'Model',
                options = [ 'gpt-3.5-turbo' ], value = 'gpt-3.5-turbo' ),
            'slider_temperature': FloatSlider(
                name = 'Temperature',
                start = 0, end = 2, step = 0.1, value = 0 ),
            # TODO: Move buttons to bottom of center panel.
            'button_chat': Button( name = 'Chat' ),
            'button_query': Button( name = 'Query' ),
            'slider_documents_count': IntSlider(
                name = 'Number of Documents',
                start = 0, end = 5, step = 1, value = 3 ),
            'token_counter': StaticText( name = 'Token Counter', value = '0' ),
            'status': StaticText( name = 'Status', value = 'OK' ),
        },
    }
    return create_dashboard( gui_items ), gui_items


def load_vectorstore( ):
    from pathlib import Path
    from pickle import load
    vectorstore_path = Path( 'vectorstore.pypickle' )
    with vectorstore_path.open( 'rb' ) as file: vectorstore = load( file )
    return vectorstore


def main( ):
    import openai
    import panel
    openai_credentials = provide_credentials( )
    openai.api_key = openai_credentials[ 'openai_api_key' ]
    openai.organization = openai_credentials[ 'openai_organization' ]
    dashboard, gui_items = layout_gui( )
    populate_models_selection( gui_items )
    vectorstore = load_vectorstore( )
    register_gui_callbacks( gui_items, vectorstore )
    panel.serve( dashboard, start = True )


def populate_models_selection( gui_items ):
    # TODO: Use API-appropriate call.
    from operator import itemgetter
    import openai
    models = sorted( map(
        itemgetter( 'id' ),
        openai.Model.list( ).to_dict_recursive( )[ 'data' ] ) )
    gui_items[ 'right' ][ 'selector_model' ].options = models


def provide_credentials( ):
    import tomli as tomllib
    with open(
        '.local/configuration/credentials.toml', 'rb'
    ) as credentials_file: credentials = tomllib.load( credentials_file )
    return dict(
        openai_api_key = credentials[ 'openai' ][ 'token' ],
        openai_organization = credentials[ 'openai' ][ 'organization' ] )


def register_gui_callbacks( gui_items, vectorstore ):
    gui_items[ 'right' ][ 'button_chat' ].on_click(
        lambda event: run_chat( event, gui_items ) )
    gui_items[ 'right' ][ 'button_query' ].on_click(
        lambda event: run_query( event, gui_items, vectorstore ) )
    gui_items[ 'center' ][ 'text_input_system' ].param.watch(
        lambda event: update_token_count( gui_items ), 'value' )
    gui_items[ 'center' ][ 'text_input_user' ].param.watch(
        lambda event: update_token_count( gui_items ), 'value' )


def run_chat( event, gui_items ):
    gui_items[ 'right' ][ 'status' ].object = 'OK'
    from openai import ChatCompletion, OpenAIError
    query = gui_items[ 'center' ][ 'text_input_user' ].value
    if query:
        add_to_conversation( 'Human', query, gui_items )
        gui_items[ 'center' ][ 'text_input_user' ].value = ''
    messages = generate_messages( gui_items )
    try:
        response = ChatCompletion.create(
            messages = messages,
            model = gui_items[ 'right' ][ 'selector_model' ].value,
            temperature = gui_items[ 'right' ][ 'slider_temperature' ].value )
        add_to_conversation(
            'AI', response.choices[ 0 ].message[ 'content' ].strip( ),
            gui_items )
    except OpenAIError as exc:
        gui_items[ 'right' ][ 'status' ].object = f"Error: {exc}"
    update_token_count( gui_items )


def run_query( event, gui_items, vectorstore ):
    gui_items[ 'right' ][ 'status' ].object = 'OK'
    query = gui_items[ 'center' ][ 'text_input_user' ].value
    if not query: return
    add_to_conversation( 'Human', query, gui_items )
    gui_items[ 'center' ][ 'text_input_user' ].value = ''
    documents_count = gui_items[ 'right' ][ 'slider_documents_count' ].value
    if not documents_count: return
    documents = vectorstore.similarity_search( query, k = documents_count )
    for document in documents:
        add_to_conversation(
            'Human', document.page_content, gui_items, kind = 'supplement' )
    update_token_count( gui_items )


def update_token_count( gui_items ):
    total_tokens = 0
    for item in gui_items[ 'center' ][ 'conversation_history' ]:
        checkbox, message_cell = item
        if checkbox.value:
            total_tokens += message_cell.metadata[ 'token_count' ]
    total_tokens += count_tokens(
        gui_items[ 'center' ][ 'text_input_user' ].value )
    total_tokens += count_tokens(
        gui_items[ 'center' ][ 'text_input_system' ].value )
    gui_items[ 'right' ][ 'token_counter' ].value = str( total_tokens )


if __name__ == "__main__": main( )
