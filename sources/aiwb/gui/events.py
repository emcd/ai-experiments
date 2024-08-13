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


# Note: Cyclic imports are at runtime after module initialization.
# pylint: disable=cyclic-import


_document_autoscroller_code = '''
if (component.value == 'scrolling')
    window.scrollTo(0, document.body.scrollHeight);'''
def generate_document_autoscroller( gui, layout, component_name ):
    if not hasattr( gui, component_name ): return
    component = getattr( gui, component_name )
    return dict(
        value = _document_autoscroller_code,
        args = dict( component = component ) )


# TODO: Handle non-text data.
_message_copier_code = '''
navigator.clipboard.writeText(component.value).then(function() {
    console.log('Text copied to clipboard');
}, function(err) {
    console.error('Error in copying text: ', err);
});'''
def generate_message_copier( gui, layout, component_name ):
    # Note: We use a Javascript callback rather than Python library,
    #       because we want to use the clipboard of the browser's host OS
    #       and not the clipboard of the OS under which the Python code
    #       is running. E.g., consider the Windows Subsystem for Linux case:
    #       no X server and no direct access to Windows API.
    if not hasattr( gui, component_name ): return
    component = getattr( gui, component_name )
    return dict(
        value = _message_copier_code,
        args = dict( component = component ) )


def on_adjust_documents_count( gui, event ):
    from .updaters import update_search_button
    update_search_button( gui )


def on_change_freeform_prompt( gui, event ):
    from .updaters import (
        update_search_button,
        update_token_count,
    )
    update_token_count( gui )
    update_search_button( gui )


async def on_click_chat( components, event ):
    from .actions import chat
    await chat( components )


def on_click_copy_message( gui, event ):
    # TODO: Handle non-text data.
    # Layer of convolution because not all panes have a value parameter
    # that is registered as a JS-serializable Parameter object.
    gui.parent__.text_clipboard_export.value = str( gui.text_message.object )


async def on_click_create_conversation( components, event ):
    from .updaters import create_and_display_conversation
    await create_and_display_conversation( components )


async def on_click_delete_conversation( components, event ):
    from .updaters import delete_conversation
    conversations = components.parent__.column_conversations_indicators
    identity = components.rehtml_indicator.identity__
    descriptor = conversations.descriptors__[ identity ]
    await delete_conversation( components.parent__, descriptor )


async def on_click_fork_conversation( components, event ):
    from .updaters import fork_conversation
    await fork_conversation( components.parent__, components.index__ )


def on_click_invoke_function( gui, event ):
    from .actions import invoke_functions
    invoke_functions( gui.parent__, gui.index__ )


async def on_click_search( components, event ):
    from .actions import search
    await search( components )


def on_click_uncan_prompt( gui, event ):
    gui.text_freeform_prompt.value = str( gui.text_canned_prompt.object )
    gui.selector_user_prompt_class.value = 'freeform'


def on_click_upgrade_conversations( gui, event ):
    from .persistence import upgrade_conversations
    upgrade_conversations( gui )


def on_select_canned_prompt( gui, event ):
    from .updaters import populate_prompt_variables
    populate_prompt_variables( gui, species = 'user' )


def on_select_conversation( components, event ):
    # TODO: async, after fix for https://github.com/holoviz/panel/issues/7142
    from .updaters import select_conversation
    #await select_conversation( components, event.obj.identity__ )
    # TEMP HACK
    from asyncio import get_running_loop
    get_running_loop( ).create_task(
        select_conversation( components, event.obj.identity__ ) )


def on_select_functions( gui, event ):
    from .updaters import update_active_functions
    update_active_functions( gui )


def on_select_model( gui, event ):
    from .updaters import update_functions_prompt
    update_functions_prompt( gui )


def on_select_system_prompt( gui, event ):
    from .updaters import populate_prompt_variables, update_functions_prompt
    populate_prompt_variables( gui, species = 'supervisor' )
    update_functions_prompt( gui )


def on_select_user_prompt_class( components, event ):
    # TODO: async, after fix for https://github.com/holoviz/panel/issues/7142
    from .updaters import (
        update_and_save_conversation,
        update_chat_button,
        update_summarization_toggle,
    )
    freeform = 'freeform' == components.selector_user_prompt_class.value
    components.column_canned_prompt.visible = False
    components.column_freeform_prompt.visible = False
    components.column_canned_prompt.visible = not freeform
    components.column_freeform_prompt.visible = freeform
    update_chat_button( components )
    update_summarization_toggle( components )
    #await update_and_save_conversation( components )
    # TEMP HACK
    from asyncio import get_running_loop
    get_running_loop( ).create_task(
        update_and_save_conversation( components ) )


def on_submit_freeform_prompt( components, event ):
    # TODO: async, after fix for https://github.com/holoviz/panel/issues/7142
    source = components.text_freeform_prompt
    if not source.submission_value: return
    source.submission_value = ''
    from .actions import chat
    # await chat( components )
    # TEMP HACK
    from asyncio import get_running_loop
    get_running_loop( ).create_task( chat( components ) )


def on_toggle_canned_prompt_display( gui, event ):
    gui.text_canned_prompt.visible = gui.toggle_canned_prompt_display.value


async def on_toggle_functions_active( components, event ):
    from .updaters import update_and_save_conversation
    await update_and_save_conversation( components )


def on_toggle_functions_display( gui, event ):
    gui.column_functions_json.visible = gui.toggle_functions_display.value


async def on_toggle_message_active( message_components, event ):
    from .updaters import update_and_save_conversation
    if not message_components.toggle_active.value:
        message_components.toggle_pinned.value = False
    await update_and_save_conversation( message_components.parent__ )


def on_toggle_message_pinned( message_gui, event ):
    if message_gui.toggle_pinned.value:
        message_gui.toggle_active.value = True


async def on_toggle_system_prompt_active( components, event ):
    from .updaters import update_and_save_conversation
    await update_and_save_conversation( components )


def on_toggle_system_prompt_display( gui, event ):
    gui.text_system_prompt.visible = gui.toggle_system_prompt_display.value
