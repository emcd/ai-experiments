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


''' User actions in Holoviz Panel GUI. '''


from . import base as __


def chat( gui ):
    from ..ai.providers import ChatCompletionError
    from .updaters import (
        add_conversation_indicator_if_necessary,
        add_message,
        update_and_save_conversation,
        update_and_save_conversations_index,
        update_message,
        update_messages_post_summarization,
        update_run_tool_button,
    )
    gui.text_status.value = 'OK'
    summarization = gui.toggle_summarize.value
    if gui.toggle_canned_prompt_active.value:
        prompt = gui.text_canned_prompt.object
        gui.toggle_canned_prompt_active.value = False
    else:
        prompt = gui.text_input_user.value
        gui.text_input_user.value = ''
    if prompt: add_message( gui, 'Human', prompt )
    try: message_component = _chat( gui )
    except ChatCompletionError as exc: pass
    else:
        update_message( message_component )
        add_conversation_indicator_if_necessary( gui )
        update_and_save_conversations_index( gui )
        if summarization:
            update_messages_post_summarization( gui )
            gui.toggle_summarize.value = False
    update_and_save_conversation( gui )
    update_run_tool_button( gui, allow_autorun = True )


def _chat( gui ):
    from ..ai.providers import ChatCallbacks
    from .updaters import add_message
    messages = __.package_messages( gui )
    controls = __.package_controls( gui )
    special_data = __.package_special_data( gui )
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


def run_tool( gui ):
    try: name, function = __.extract_function_invocation_request( gui )
    except ValueError as exc:
        gui.text_status.value = str( exc )
        return
    try: result = function( )
    except ValueError as exc:
        gui.text_status.value = str( exc )
        return
    from json import dumps
    from .updaters import add_message
    add_message(
        gui, 'Function', dumps( result ),
        actor_name = name,
        mime_type = 'application/json' )
    chat( gui )
    if gui.checkbox_elide_function_history.value:
        message_rows = gui.column_conversation_history
        message_rows[ -3 ].gui__.toggle_active.value = (
            message_rows[ -3 ].gui__.toggle_pinned.value )
        message_rows[ -2 ].gui__.toggle_active.value = (
            message_rows[ -2 ].gui__.toggle_pinned.value )


def search( gui ):
    from .updaters import add_message, update_and_save_conversation
    gui.text_status.value = 'OK'
    prompt = gui.text_input_user.value
    gui.text_input_user.value = ''
    add_message( gui, 'Human', prompt )
    documents_count = gui.slider_documents_count.value
    vectorstore = gui.auxdata__.vectorstores[
        gui.selector_vectorstore.value ][ 'instance' ]
    documents = vectorstore.similarity_search( prompt, k = documents_count )
    for document in documents:
        mime_type = document.metadata.get( 'mime_type', 'text/plain' )
        add_message(
            gui, 'Document', document.page_content, mime_type = mime_type )
    update_and_save_conversation( gui )
