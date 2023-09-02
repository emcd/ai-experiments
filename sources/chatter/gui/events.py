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


''' Event handlers for Holoviz Panel GUI. '''


from . import base as __


def on_adjust_documents_count( gui, event ):
    from .updaters import update_search_button
    update_search_button( gui )


def on_click_chat( gui, event ):
    from .actions import chat
    chat( gui )


def on_click_create_conversation( gui, event ):
    from .updaters import create_and_display_conversation
    create_and_display_conversation( gui )


def on_click_delete_conversation( gui, event ):
    from .updaters import delete_conversation
    conversations = gui.parent__.column_conversations_indicators
    identity = gui.rehtml_indicator.identity__
    descriptor = conversations.descriptors__[ identity ]
    delete_conversation( gui.parent__, descriptor )


def on_click_fork_conversation( gui, event ):
    from .updaters import fork_conversation
    fork_conversation( gui.parent__, gui.index__ )


def on_click_run_tool( gui, event ):
    from .actions import run_tool
    run_tool( gui )


def on_click_search( gui, event ):
    from .actions import search
    search( gui )


def on_click_uncan_prompt( gui, event ):
    gui.text_input_user.value = str( gui.text_canned_prompt.object )


# TODO: Ensure that this handler is triggered.
#       According to https://github.com/holoviz/panel/issues/1882,
#       this should work. But, it does not.
#       Possible workaround: https://discourse.holoviz.org/t/catching-textinput-value-while-the-user-is-typing/1652/2
def on_input_user_prompt( gui, event ):
    from .updaters import (
        update_search_button,
        update_token_count,
    )
    update_token_count( gui )
    update_search_button( gui )


def on_input_finish_user_prompt( gui, event ):
    from .updaters import (
        update_and_save_conversation,
        update_search_button,
    )
    update_and_save_conversation( gui )
    update_search_button( gui )


def on_select_canned_prompt( gui, event ):
    from .updaters import populate_canned_prompt_variables
    populate_canned_prompt_variables( gui )


def on_select_conversation( gui, event ):
    from .updaters import select_conversation
    select_conversation( gui, event.obj.identity__ )


def on_select_functions( gui, event ):
    from .updaters import update_active_functions
    update_active_functions( gui )


def on_select_model( gui, event ):
    from .updaters import update_functions_prompt
    update_functions_prompt( gui )


def on_select_system_prompt( gui, event ):
    from .updaters import (
        populate_system_prompt_variables,
        update_functions_prompt,
    )
    populate_system_prompt_variables( gui )
    update_functions_prompt( gui )


def on_toggle_canned_prompt_active( gui, event ):
    from .updaters import (
        update_and_save_conversation,
        update_chat_button,
        update_summarization_toggle,
    )
    canned_state = gui.toggle_canned_prompt_active.value
    user_state = gui.toggle_user_prompt_active.value
    if canned_state == user_state:
        gui.toggle_user_prompt_active.value = not canned_state
        update_and_save_conversation( gui )
    update_chat_button( gui )
    update_summarization_toggle( gui )


def on_toggle_canned_prompt_display( gui, event ):
    gui.text_canned_prompt.visible = gui.toggle_canned_prompt_display.value


def on_toggle_functions_active( gui, event ):
    from .updaters import update_and_save_conversation
    update_and_save_conversation( gui )


def on_toggle_functions_display( gui, event ):
    gui.column_functions_json.visible = gui.toggle_functions_display.value


def on_toggle_message_active( message_gui, event ):
    from .updaters import update_and_save_conversation
    if not message_gui.toggle_active.value:
        message_gui.toggle_pinned.value = False
    update_and_save_conversation( message_gui.parent__ )


def on_toggle_message_pinned( message_gui, event ):
    if message_gui.toggle_pinned.value:
        message_gui.toggle_active.value = True


def on_toggle_system_prompt_active( gui, event ):
    from .updaters import update_and_save_conversation
    update_and_save_conversation( gui )


def on_toggle_system_prompt_display( gui, event ):
    gui.text_system_prompt.visible = gui.toggle_system_prompt_display.value


def on_toggle_user_prompt_active( gui, event ):
    from .updaters import update_and_save_conversation
    canned_state = gui.toggle_canned_prompt_active.value
    user_state = gui.toggle_user_prompt_active.value
    if canned_state == user_state:
        gui.toggle_canned_prompt_active.value = not user_state
        update_and_save_conversation( gui )
