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


def on_canned_prompt_selection( gui, event ):
    from .updaters import populate_canned_prompt_variables
    populate_canned_prompt_variables( gui )


def on_chat_click( gui, event ):
    from .actions import chat
    chat( gui )


def on_conversation_fork_click( gui, event ):
    from .updaters import fork_conversation
    fork_conversation( gui.parent__, gui.index__ )


def on_create_conversation( gui, event ):
    from .updaters import create_and_display_conversation
    create_and_display_conversation( gui )


def on_customize_canned_prompt( gui, event ):
    gui.text_input_user.value = str( gui.text_canned_prompt.object )


def on_documents_count_adjustment( gui, event ):
    from .updaters import update_search_button
    update_search_button( gui )


def on_functions_selection( gui, event ):
    from .updaters import update_active_functions
    update_active_functions( gui )


def on_model_selection( gui, event ):
    from .updaters import update_functions_prompt
    # TODO: For models which do not explicitly support functions,
    #       weave selected functions into system prompt.
    #       Then, functions prompt row should always be visible.
    supports_functions = gui.selector_model.auxdata__[
        gui.selector_model.value ][ 'supports-functions' ]
    gui.row_functions_prompt.visible = supports_functions
    update_functions_prompt( gui )


def on_run_tool_click( gui, event ):
    from .actions import run_tool
    run_tool( gui )


def on_system_prompt_selection( gui, event ):
    from .updaters import (
        populate_system_prompt_variables,
        update_functions_prompt,
    )
    populate_system_prompt_variables( gui )
    update_functions_prompt( gui )


def on_search_click( gui, event ):
    from .actions import search
    search( gui )


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


# TODO: Ensure that this handler is triggered.
#       According to https://github.com/holoviz/panel/issues/1882,
#       this should work. But, it does not.
#       Possible workaround: https://discourse.holoviz.org/t/catching-textinput-value-while-the-user-is-typing/1652/2
def on_user_prompt_input( gui, event ):
    from .updaters import (
        update_search_button,
        update_token_count,
    )
    update_token_count( gui )
    update_search_button( gui )


def on_user_prompt_input_finish( gui, event ):
    from .updaters import (
        update_and_save_conversation,
        update_search_button,
    )
    update_and_save_conversation( gui )
    update_search_button( gui )
