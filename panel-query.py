def load_vectorstore( ):
    from pathlib import Path
    from pickle import load
    vectorstore_path = Path( 'vectorstore.pypickle' )
    with vectorstore_path.open( 'rb' ) as file: vectorstore = load( file )
    return vectorstore


def create_prompt( query, docs, initial_system_message ):
    prompt = [ initial_system_message ]
    prompt.append(
        "Additionally, you have the following pieces of supplemental "
        "information available to help you accurately respond:" )
    for i, doc in enumerate( docs ):
        prompt.append( f"## Supplement {i + 1}\n{doc.page_content}" )
    system_message = '\n\n'.join( prompt )
    messages = [
        { 'role' : 'system', 'content' : system_message },
        { 'role' : 'user', 'content' : query },
    ]
    return messages


def run_query( event, layout_items, vectorstore ):
    from openai import ChatCompletion
    query = layout_items[ 'text_input_user' ].value
    system_message = layout_items[ 'text_input_system' ].value
    rows_results = layout_items[ 'rows_results' ]
    docs = vectorstore.similarity_search( query, k = len( rows_results ) )
    for i, doc in enumerate( docs ):
        rows_results[ i ][ 1 ].object = doc.page_content
    messages = create_prompt( query, docs, system_message )
    response = ChatCompletion.create(
        model = 'gpt-3.5-turbo',
        messages = messages,
        temperature = 0, )
    layout_items[ 'token_counter' ].value = response.usage[ 'total_tokens' ]
    layout_items[ 'answer_display' ].object = (
        response.choices[ 0 ].message[ 'content' ] )


def layout_gui( vectorstore, number_of_results ):
    from panel import Column, Row
    from panel.pane import Markdown
    from panel.widgets import Button, IntInput, TextInput
    layout_items = dict(
        text_input_user = TextInput(
            value = '', placeholder = 'Enter user message here...' ),
        text_input_system = TextInput(
            value = '', placeholder = 'Enter system message here...' ),
        button_run = Button( name = 'Run Query' ),
        rows_results = Column(
            *(Row( f"{i}", Markdown( '', width = 640, ) )
              for i in range( number_of_results ) ) ),
        token_counter = IntInput(
            name = 'Token Counter', value = 0, disabled = True, ),
        answer_display = Markdown( '', width = 640, ),
    )
    dashboard = Column( *layout_items.values( ) )
    layout_items[ 'button_run' ].on_click(
        lambda event : run_query( event, layout_items, vectorstore ) )
    return dashboard


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
