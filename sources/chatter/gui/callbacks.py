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


def _provide_auxiliary_classes( ):
    from collections import namedtuple
    return (
        namedtuple(
            'ConversationTuple', ( 'checkbox_inclusion', 'text_message' ) ),
    )

ConversationTuple, = _provide_auxiliary_classes( )


def add_message( gui, role, content, include = True ):
    from panel import Column, Row
    from panel.pane import Markdown
    from panel.widgets import Checkbox, StaticText
    from ..messages import count_tokens
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
    checkbox = Checkbox( name = emoji, value = include, width = 40 )
    checkbox.param.watch( lambda event: update_token_count( gui ), 'value' )
    row = Row(
        checkbox,
        message_cell,
        # TODO: Copy button, edit button, etc...
    )
    conversation_history.append( row )
    return ConversationTuple( *row )


def generate_messages( gui ):
    system_message = gui.text_system_prompt.object
    sysprompt_honor = gui.selector_model.metadata__[
        gui.selector_model.value ][ 'honors-system-prompt' ]
    role = 'system' if sysprompt_honor else 'user'
    messages = [ { 'role': role, 'content': system_message } ]
    for item in gui.column_conversation_history:
        if not item[ 0 ].value: continue # if checkbox is not checked
        role = (
            'user' if item[ 1 ].metadata__[ 'role' ] in ( 'Human', 'Document' )
            else 'assistant' )
        content = item[ 1 ].object
        messages.append( { 'role': role, 'content': content } )
    return messages


def register( gui ):
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
        lambda event: update_token_count( gui ), 'value' )


def run_chat( gui ):
    gui.text_status.value = 'OK'
    if gui.checkbox_summarize.value:
        query = gui.text_summarization_prompt.object
    else:
        query = gui.text_input_user.value
        gui.text_input_user.value = ''
    if query: add_message( gui, 'Human', query )
    messages = generate_messages( gui )
    # TODO: Choose completion function according to provider.
    from openai import ChatCompletion, OpenAIError
    try:
        # TODO: Support streaming operation.
        response = ChatCompletion.create(
            messages = messages,
            model = gui.selector_model.value,
            temperature = gui.slider_temperature.value )
        add_message(
            gui, 'AI', response.choices[ 0 ].message[ 'content' ].strip( ) )
    except OpenAIError as exc: gui.text_status.value = f"Error: {exc}"
    else:
        save_conversation( gui )
        if gui.checkbox_summarize.value:
            gui.checkbox_summarize.value = False
            # Exclude conversation items above summarization.
            for i in range( len( gui.column_conversation_history ) - 2 ):
                conversation_tuple = ConversationTuple(
                    *gui.column_conversation_history[ i ] )
                conversation_tuple.checkbox_inclusion.value = False
    update_token_count( gui )


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
    update_token_count( gui )


def save_conversation( gui ):
    ai_message_count = sum(
        1 for conversation_tuple
        in map(
            lambda row: ConversationTuple( *row ),
            gui.column_conversation_history )
        if conversation_tuple.checkbox_inclusion.value
        and 'AI' == conversation_tuple.text_message.metadata__[ 'role' ] )
    if 1 == ai_message_count:
        # TODO: Generate blurb.
        # TODO: add_conversation_to_index( gui )
        pass
    from pathlib import Path
    from .state import save_conversation as save
    conversations_path = (
        Path( __file__ ).parent.resolve( strict = True )
        / '.local/state/conversations' )
    conversations_path.mkdir( exist_ok = True, parents = True )
    save( gui, Path( '.local/state/conversations/test.json' ) )


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
    from ..messages import count_tokens
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
    tokens_limit = gui.selector_model.metadata__[
        gui.selector_model.value ][ 'tokens-limit' ]
    # TODO: Change color of text, depending on percentage of tokens limit.
    gui.text_tokens_total.value = f"{total_tokens} / {tokens_limit}"
