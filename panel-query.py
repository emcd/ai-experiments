def load_vectorstore( ):
    from pathlib import Path
    from pickle import load
    vectorstore_path = Path( 'vectorstore.pypickle' )
    with vectorstore_path.open( 'rb' ) as file: vectorstore = load( file )
    return vectorstore


def create_prompt( layout_items, docs ):
    query = layout_items[ 'left' ][ 'text_input_user' ].value
    system_message = layout_items[ 'left' ][ 'text_input_system' ].value
    prompt = [ system_message ]
    prompt.append(
        "Additionally, you have the following pieces of supplemental "
        "information available to help you accurately respond:" )
    for i, doc in enumerate( docs ):
        prompt.append( f"## Supplement {i + 1}\n{doc.page_content}" )
    system_message = '\n\n'.join( prompt )
    messages = [ { 'role' : 'system', 'content' : system_message } ]
    for item in layout_items[ 'right' ][ 'conversation_history' ]:
        if item[ 0 ].value:  # if checkbox is checked
            role = 'user' if item[ 1 ].object == 'Human' else 'assistant'
            content = item[ 2 ].object
            messages.append( { 'role': role, 'content': content } )
    return messages


def add_to_conversation( role, content, layout_items ):
    from panel import Row
    from panel.pane import Markdown
    from panel.widgets import Checkbox
    conversation_history = layout_items[ 'right' ][ 'conversation_history' ]
    token_count = count_tokens( content )
    checkbox = Checkbox( value = True, width = 20 )
    checkbox.param.watch(
        lambda event: update_token_count( layout_items ), 'value' )
    message_cell = Markdown( content, width = 500 )
    message_cell.metadata = { 'tokens': count_tokens( content ) }
    new_item = Row( checkbox, role, message_cell )
    conversation_history.append( new_item )
    return new_item


def count_tokens( content ):
    from tiktoken import get_encoding
    encoding = get_encoding( 'cl100k_base' )
    return len( encoding.encode( content ) )


def update_token_count( layout_items ):
    total_tokens = 0
    for item in layout_items[ 'right' ][ 'conversation_history' ]:
        checkbox, _, message_cell = item
        if checkbox.value:
            total_tokens += message_cell.metadata[ 'tokens' ]
    total_tokens += count_tokens(
        layout_items[ 'left' ][ 'text_input_user' ].value )
    total_tokens += count_tokens(
        layout_items[ 'left' ][ 'text_input_system' ].value )
    layout_items[ 'left' ][ 'token_counter' ].value = total_tokens


def run_query( event, layout_items, vectorstore ):
    from openai import ChatCompletion
    query = layout_items[ 'left' ][ 'text_input_user' ].value
    add_to_conversation( 'Human', query, layout_items )
    rows_results = layout_items[ 'left' ][ 'rows_results' ]
    docs = vectorstore.similarity_search( query, k = len( rows_results ) )
    for i, doc in enumerate( docs ):
        rows_results[ i ][ 1 ].value = doc.page_content
    messages = create_prompt( layout_items, docs )
    response = ChatCompletion.create(
        model = 'gpt-3.5-turbo',
        messages = messages,
        temperature = 0,
    )
    add_to_conversation(
        'AI', response.choices[ 0 ].message[ 'content' ], layout_items )
    layout_items[ 'left' ][ 'text_input_user' ].value = ''


def layout_gui( vectorstore, number_of_results ):
    from panel import Column, Row
    from panel.widgets import Button, IntInput, TextInput
    layout_items = {
        'left': {
            'text_input_user': TextInput(
                value = '', placeholder = 'Enter user message here...' ),
            'text_input_system': TextInput(
                value = '', placeholder = 'Enter system message here...' ),
            'button_run': Button( name = 'Run Query' ),
            'rows_results': Column(
                *( Row( str( i ), TextInput( value = '', width = 640 ) )
                for i in range( number_of_results ) ) ),
            'token_counter': IntInput(
                name = 'Token Counter', value = 0, disabled = True ),
        },
        'right': {
            'conversation_history': Column(
                sizing_mode = 'stretch_height', width = 640 ),
        },
    }
    layout_items[ 'left' ][ 'text_input_user' ].param.watch(
        lambda event: update_token_count( layout_items ), 'value' )
    layout_items[ 'left' ][ 'text_input_system' ].param.watch(
        lambda event: update_token_count( layout_items ), 'value' )
    layout_items[ 'left' ][ 'button_run' ].on_click(
        lambda event: run_query( event, layout_items, vectorstore ) )
    dashboard = Row(
        Column( *layout_items[ 'left' ].values( ) ),
        layout_items[ 'right' ][ 'conversation_history' ],
    )
    return dashboard


#def run_query( event, layout_items, vectorstore ):
#    from openai import ChatCompletion
#    query = layout_items[ 'text_input_user' ].value
#    system_message = layout_items[ 'text_input_system' ].value
#    rows_results = layout_items[ 'rows_results' ]
#    docs = vectorstore.similarity_search( query, k = len( rows_results ) )
#    for i, doc in enumerate( docs ):
#        rows_results[ i ][ 1 ].object = doc.page_content
#    messages = create_prompt( query, docs, system_message )
#    response = ChatCompletion.create(
#        model = 'gpt-3.5-turbo',
#        messages = messages,
#        temperature = 0, )
#    layout_items[ 'token_counter' ].value = response.usage[ 'total_tokens' ]
#    layout_items[ 'answer_display' ].object = (
#        response.choices[ 0 ].message[ 'content' ] )
#
#
#def layout_gui( vectorstore, number_of_results ):
#    from panel import Column, Row
#    from panel.pane import Markdown
#    from panel.widgets import Button, IntInput, TextInput
#    layout_items = dict(
#        text_input_user = TextInput(
#            value = '', placeholder = 'Enter user message here...' ),
#        text_input_system = TextInput(
#            value = '', placeholder = 'Enter system message here...' ),
#        button_run = Button( name = 'Run Query' ),
#        rows_results = Column(
#            *(Row( f"{i}", Markdown( '', width = 640, ) )
#              for i in range( number_of_results ) ) ),
#        token_counter = IntInput(
#            name = 'Token Counter', value = 0, disabled = True, ),
#        answer_display = Markdown( '', width = 640, ),
#    )
#    dashboard = Column( *layout_items.values( ) )
#    layout_items[ 'button_run' ].on_click(
#        lambda event : run_query( event, layout_items, vectorstore ) )
#    return dashboard


def provide_credentials( ):
    import tomli as tomllib
    with open(
        '.local/configuration/credentials.toml', 'rb'
    ) as credentials_file: credentials = tomllib.load( credentials_file )
    return dict(
        openai_api_key = credentials[ 'openai' ][ 'token' ],
        openai_organization = credentials[ 'openai' ][ 'organization' ] )


def main( ):
    import openai
    import panel
    openai_credentials = provide_credentials( )
    openai.api_key = openai_credentials[ 'openai_api_key' ]
    openai.organization = openai_credentials[ 'openai_organization' ]
    vectorstore = load_vectorstore( )
    dashboard = layout_gui(
        vectorstore = load_vectorstore( ), number_of_results = 3 )
    panel.serve( dashboard, start = True )


if __name__ == "__main__": main( )
