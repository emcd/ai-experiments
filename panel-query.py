def add_to_conversation( role, content, gui ):
    from panel import Column, Row
    from panel.pane import Markdown
    from panel.widgets import Checkbox, StaticText
    conversation_history = gui.column_conversation_history
    if 'Document' == role:
        content = f'''## Supplement ##\n\n{content}'''
        emoji = '📄'
        style = { 'background-color': 'WhiteSmoke' }
    elif 'AI' == role:
        emoji = '🤖'
        style = { 'border': '2px solid LightGray', 'padding': '3px' }
    else:
        emoji = '🧑'
        style = { 'background-color': 'White' }
    # TODO: Create cell based on MIME type of content rather than role.
    if role in ( 'Document', ):
        message_cell = StaticText(
            value = content,
            height_policy = 'fit',
            sizing_mode = 'stretch_width',
            style = style )
    else:
        message_cell = Markdown(
            content,
            height_policy = 'fit',
            sizing_mode = 'stretch_width',
            style = style )
    message_cell.metadata__ = {
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
    system_message = gui.text_system_prompt.object
    model = gui.selector_model.value
    if model not in SYSTEM_MESSAGE_AWARE_MODELS: role = 'user'
    else: role = 'system'
    messages = [ { 'role': role, 'content': system_message } ]
    for item in gui.column_conversation_history:
        if not item[ 0 ].value: continue # if checkbox is not checked
        role = (
            'user' if item[ 1 ].metadata__[ 'role' ] in ( 'Human', 'Document' )
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
    prepare( )
    from types import SimpleNamespace
    import panel
    from chatter.gui import layout as gui_layout
    gui = { }
    dashboard = layout_gui( gui, gui_layout, 'dashboard' )
    gui = SimpleNamespace( **gui )
    populate_models_selection( gui )
    populate_system_prompts_selection( gui )
    populate_summarization_prompts_selection( gui )
    vectorstore = load_vectorstore( )
    register_gui_callbacks( gui, vectorstore )
    panel.serve( dashboard, start = True )


def populate_models_selection( gui ):
    # TODO: Use provider-appropriate call.
    from operator import itemgetter
    import openai
    models = sorted( map(
        itemgetter( 'id' ),
        openai.Model.list( ).to_dict_recursive( )[ 'data' ] ) )
    gui.selector_model.options = models


def populate_prompts_selection( gui_selector, prompts_directory ):
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


def populate_system_prompts_selection( gui ):
    from pathlib import Path
    populate_prompts_selection(
        gui.selector_system_prompt,
        Path( '.local/data/system-prompts' ) )
    update_system_prompt_variables( gui )


def populate_summarization_prompts_selection( gui ):
    from pathlib import Path
    populate_prompts_selection(
        gui.selector_summarization_prompt,
        Path( '.local/data/summarization-prompts' ) )
    update_summarization_prompt_variables( gui )


def prepare( ):
    from pathlib import Path
    from sys import path as module_search_paths
    project_path = Path( __file__ ).parent.resolve( strict = True )
    library_path = project_path / 'sources'
    module_search_paths.insert( 0, str( library_path ) )
    configuration = provide_configuration( project_path )
    from dotenv import load_dotenv
    with (
        project_path / '.local/configuration/environment'
    ).open( ) as environment_file: load_dotenv( stream = environment_file )
    prepare_api_clients( )


def prepare_api_clients( ):
    from os import environ as cpe  # current process environment
    if 'OPENAI_API_KEY' in cpe:
        import openai
        openai.api_key = cpe[ 'OPENAI_API_KEY' ]
        if 'OPENAI_ORGANIZATION_ID' in cpe:
            openai.organization = cpe[ 'OPENAI_ORGANIZATION_ID' ]


def provide_configuration( project_path ):
    from shutil import copyfile
    import tomli as tomllib
    path = project_path / '.local/configuration/general.toml'
    if not path.exists( ):
        copyfile(
            str( project_path / '.local/data/configuration/general.toml' ),
            str( path ) )
    with path.open( 'rb' ) as file: return tomllib.load( file )


def register_gui_callbacks( gui, vectorstore ):
    gui.button_chat.on_click( lambda event: run_chat( gui ) )
    gui.button_query.on_click( lambda event: run_query( gui, vectorstore ) )
    gui.checkbox_display_system_prompt.param.watch(
        lambda event: toggle_system_prompt_display( gui ), 'value' )
    gui.checkbox_summarize.param.watch(
        lambda event: toggle_summarization_prompt_display( gui ), 'value' )
    gui.selector_summarization_prompt.param.watch(
        lambda event: update_summarization_prompt_variables( gui ), 'value' )
    gui.selector_system_prompt.param.watch(
        lambda event: update_system_prompt_variables( gui ), 'value' )
    gui.text_input_user.param.watch(
        lambda event: update_token_count( gui ), 'value' )


def run_chat( gui ):
    gui.text_status.value = 'OK'
    from openai import ChatCompletion, OpenAIError
    if gui.checkbox_summarize.value:
        query = gui.text_summarization_prompt.object
    else:
        query = gui.text_input_user.value
        gui.text_input_user.value = ''
    if query: add_to_conversation( 'Human', query, gui )
    messages = generate_messages( gui )
    try:
        response = ChatCompletion.create(
            messages = messages,
            model = gui.selector_model.value,
            temperature = gui.slider_temperature.value )
        add_to_conversation(
            'AI', response.choices[ 0 ].message[ 'content' ].strip( ), gui )
    except OpenAIError as exc: gui.text_status.value = f"Error: {exc}"
    else:
        save_conversation( gui )
        if gui.checkbox_summarize.value:
            gui.checkbox_summarize.value = False
            # Uncheck conversation items above summarization.
            for i in range( len( gui.column_conversation_history ) - 2 ):
                gui.column_conversation_history[ i ][ 0 ].value = False
    update_token_count( gui )


def run_query( gui, vectorstore ):
    gui.text_status.value = 'OK'
    query = gui.text_input_user.value
    gui.text_input_user.value = ''
    if not query: return
    add_to_conversation( 'Human', query, gui )
    documents_count = gui.slider_documents_count.value
    if not documents_count: return
    documents = vectorstore.similarity_search( query, k = documents_count )
    for document in documents:
        add_to_conversation( 'Document', document.page_content, gui )
    update_token_count( gui )


def save_conversation( gui ):
    ai_message_count = sum(
        1 for row in gui.column_conversation_history
        if row[ 0 ].value and 'AI' == row[ 1 ].metadata__[ 'role' ] )
    if 1 == ai_message_count:
        # TODO: Generate blurb.
        # TODO: add_conversation_to_index( gui )
        pass
    from pathlib import Path
    from chatter.gui import save_conversation as save
    conversations_path = (
        Path( __file__ ).parent.resolve( strict = True )
        / '.local/state/conversations' )
    conversations_path.mkdir( exist_ok = True, parents = True )
    save( gui, { }, Path( '.local/state/conversations/test.json' ) )


def toggle_summarization_prompt_display( gui ):
    gui.text_summarization_prompt.visible = gui.checkbox_summarize.value
    update_token_count( gui )


def toggle_system_prompt_display( gui ):
    gui.text_system_prompt.visible = gui.checkbox_display_system_prompt.value


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
    update_token_count( gui )


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
    total_tokens = 0
    for item in gui.column_conversation_history:
        checkbox, message_cell = item
        if checkbox.value:
            total_tokens += message_cell.metadata__[ 'token_count' ]
    if gui.checkbox_summarize.value:
        total_tokens += count_tokens( gui.text_summarization_prompt.object )
    else:
        total_tokens += count_tokens( gui.text_input_user.value )
    total_tokens += count_tokens( gui.text_system_prompt.object )
    gui.text_tokens_total.value = str( total_tokens )


if __name__ == "__main__": main( )
