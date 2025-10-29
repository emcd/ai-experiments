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


from . import __


_document_autoscroller_code = '''
if (component.value == 'scrolling')
    window.scrollTo(0, document.body.scrollHeight);'''
def generate_document_autoscroller( components, layout, component_name ):
    if not hasattr( components, component_name ): return None
    component = getattr( components, component_name )
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
def generate_message_copier( components, layout, component_name ):
    # Note: We use a Javascript callback rather than Python library,
    #       because we want to use the clipboard of the browser's host OS
    #       and not the clipboard of the OS under which the Python code
    #       is running. E.g., consider the Windows Subsystem for Linux case:
    #       no X server and no direct access to Windows API.
    if not hasattr( components, component_name ): return None
    component = getattr( components, component_name )
    return dict(
        value = _message_copier_code,
        args = dict( component = component ) )


# TODO: Make focus switching work.
_title_edit_focus_code = '''
if (component.visible)
    setTimeout(function() {
        component.focus();
    }, 0);
'''
def generate_title_edit_focus( components, layout, component_name ):
    if not hasattr( components, component_name ): return None
    component = getattr( components, component_name )
    return dict(
        value = _title_edit_focus_code,
        args = dict( component = component ) )


async def on_adjust_documents_count( components, event ):
    if components.mutex__.locked( ): return
    from .updaters import update_search_button
    update_search_button( components )


async def on_change_canned_prompt( components, event ):
    if components.mutex__.locked( ): return
    from .updaters import update_prompt_text
    await update_prompt_text( components, species = 'user' )


async def on_change_freeform_prompt( components, event ):
    if not event.new: return
    if components.mutex__.locked( ): return
    from .updaters import update_search_button, update_token_count
    source = components.text_freeform_prompt
    source.content_update_event = False
    await update_token_count( components )
    update_search_button( components )


async def on_change_message_edit( message_components, event ):
    if not event.new: return
    if message_components.parent__.mutex__.locked( ): return
    source = message_components.text_message_edit
    source.content_update_event = False
    # TODO? Update token counts.


async def on_change_system_prompt( components, event ):
    if components.mutex__.locked( ): return
    from .updaters import update_prompt_text
    await update_prompt_text( components, species = 'supervisor' )


async def on_click_chat( components, event ):
    if components.mutex__.locked( ): return
    from .actions import chat
    await chat( components )


async def on_click_copy_message( message_components, event ):
    if message_components.parent__.mutex__.locked( ): return
    # TODO: Handle non-text data.
    # Layer of convolution because not all panes have a value parameter
    # that is registered as a JS-serializable Parameter object.
    message_components.parent__.text_clipboard_export.value = (
        str( message_components.text_message.object ) )


async def on_click_create_conversation( components, event ):
    from .updaters import create_and_display_conversation
    await create_and_display_conversation( components )


async def on_click_delete_conversation( components, event ):
    from .updaters import delete_conversation
    conversations = components.parent__.column_conversations_indicators
    identity = components.rehtml_indicator.identity__
    descriptor = conversations.descriptors__[ identity ]
    await delete_conversation( components.parent__, descriptor )


async def on_click_fork_conversation( message_components, event ):
    if message_components.parent__.mutex__.locked( ): return
    from .updaters import fork_conversation
    await fork_conversation(
        message_components.parent__, message_components.index__ )


async def on_click_message_edit( message_components, event ):
    if message_components.parent__.mutex__.locked( ): return
    from .conversations import alter_message_edit_mode
    from .utilities import access_text_component_value
    message_components.text_message_edit.value_to_ingest = (
        access_text_component_value( message_components.text_message ) )
    alter_message_edit_mode( message_components, True )


async def on_click_message_edit_cancel( message_components, event ):
    if message_components.parent__.mutex__.locked( ): return
    from .conversations import alter_message_edit_mode
    alter_message_edit_mode( message_components, False )


async def on_click_message_edit_submit( message_components, event ):
    if message_components.parent__.mutex__.locked( ): return
    from .actions import chat
    from .conversations import alter_message_edit_mode
    from .updaters import truncate_conversation
    from .utilities import assign_text_component_value
    assign_text_component_value(
        message_components.text_message,
        message_components.text_message_edit.value )
    alter_message_edit_mode( message_components, False )
    components = message_components.parent__
    truncate_conversation( components, message_components.index__ )
    await chat( components )


async def on_click_remove_orphans( components, event ):
    from .persistence import remove_orphans
    await remove_orphans( components )


async def on_click_search( components, event ):
    if components.mutex__.locked( ): return
    from .actions import search
    await search( components )


async def on_click_title_edit( indicator_components, event ):
    from .conversations import alter_title_edit_mode
    from .utilities import access_text_component_value
    indicator_components.text_title_edit.value = (
        access_text_component_value( indicator_components.text_title ) )
    alter_title_edit_mode( indicator_components, True )


async def on_click_title_edit_submit( indicator_components, event ):
    from .conversations import alter_title_edit_mode
    from .persistence import save_conversations_index
    from .utilities import assign_text_component_value
    assign_text_component_value(
        indicator_components.text_title,
        indicator_components.text_title_edit.value )
    alter_title_edit_mode( indicator_components, False )
    components = indicator_components.parent__
    conversations = components.column_conversations_indicators
    descriptor = conversations.descriptors__[ indicator_components.identity__ ]
    descriptor.title = indicator_components.text_title_edit.value
    await save_conversations_index( components )


async def on_click_title_edit_cancel( indicator_components, event ):
    from .conversations import alter_title_edit_mode
    alter_title_edit_mode( indicator_components, False )


async def on_click_title_regenerate( indicator_components, event ):
    from .actions import generate_conversation_title
    from .persistence import save_conversations_index
    from .utilities import assign_text_component_value
    components = indicator_components.parent__
    conversations = components.column_conversations_indicators
    descriptor = conversations.descriptors__[ indicator_components.identity__ ]
    try: title, labels = await generate_conversation_title( descriptor.gui )
    except Exception as exc:
        ic( __.exception_to_str( exc ) )
        return
    assign_text_component_value( indicator_components.text_title, title )
    descriptor.title = title
    descriptor.labels = labels
    await save_conversations_index( components )


async def on_click_uncan_prompt( components, event ):
    if components.mutex__.locked( ): return
    components.text_freeform_prompt.value_to_ingest = (
        str( components.text_canned_prompt.object ) )
    components.selector_user_prompt_class.value = 'freeform'


async def on_click_upgrade_conversations( components, event ):
    from .persistence import upgrade_conversations
    await upgrade_conversations( components )


async def on_click_use_invocables( message_components, event ):
    if message_components.parent__.mutex__.locked( ): return
    from .actions import use_invocables
    await use_invocables(
        message_components.parent__, message_components.index__ )


async def on_select_canned_prompt( components, event ):
    if components.mutex__.locked( ): return
    from .updaters import populate_prompt_variables
    await populate_prompt_variables( components, species = 'user' )


async def on_select_conversation( components, event ):
    from .updaters import select_conversation
    await select_conversation( components, event.obj.identity__ )


async def on_select_invocables( components, event ):
    if components.mutex__.locked( ): return
    from .updaters import update_invocables_selection
    await update_invocables_selection( components )


async def on_select_model( components, event ):
    if None is event.new: return
    if components.mutex__.locked( ): return
    from .updaters import update_conversation_postpopulate
    await update_conversation_postpopulate( components )


async def on_select_provider( components, event ):
    if None is event.new: return
    if components.mutex__.locked( ): return
    # TODO: on_select_provider_client
    from .updaters import populate_models_selector
    await populate_models_selector( components )


async def on_select_system_prompt( components, event ):
    if components.mutex__.locked( ): return
    from .updaters import (
        populate_prompt_variables, update_invocations_prompt )
    await populate_prompt_variables( components, species = 'supervisor' )
    await update_invocations_prompt( components )


async def on_select_user_prompt_class( components, event ):
    if components.mutex__.locked( ): return
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
    await update_and_save_conversation( components )


async def on_submit_freeform_prompt( components, event ):
    if not event.new: return
    if components.mutex__.locked( ): return
    source = components.text_freeform_prompt
    if not source.value: return
    source.submission_event = False
    # Handle submission same as clicking chat button.
    await on_click_chat( components, event )


async def on_submit_message_edit( message_components, event ):
    if not event.new: return
    if message_components.parent__.mutex__.locked( ): return
    source = message_components.text_message_edit
    if not source.value: return
    source.submission_event = False
    # Handle submission same as clicking submit button.
    await on_click_message_edit_submit( message_components, event )


async def on_toggle_canned_prompt_display( components, event ):
    if components.mutex__.locked( ): return
    components.text_canned_prompt.visible = (
        components.toggle_canned_prompt_display.value )


async def on_toggle_functions_active( components, event ):
    if components.mutex__.locked( ): return
    from .updaters import update_and_save_conversation
    await update_and_save_conversation( components )


async def on_toggle_functions_display( components, event ):
    if components.mutex__.locked( ): return
    components.column_functions_json.visible = (
        components.toggle_functions_display.value )


async def on_toggle_message_active( message_components, event ):
    if message_components.parent__.mutex__.locked( ): return
    from .updaters import update_and_save_conversation
    if not message_components.toggle_active.value:
        message_components.toggle_pinned.value = False
    await update_and_save_conversation( message_components.parent__ )


async def on_toggle_message_pinned( message_components, event ):
    if message_components.parent__.mutex__.locked( ): return
    if message_components.toggle_pinned.value:
        message_components.toggle_active.value = True


async def on_toggle_system_prompt_active( components, event ):
    if components.mutex__.locked( ): return
    from .updaters import update_and_save_conversation
    await update_and_save_conversation( components )


async def on_toggle_system_prompt_display( components, event ):
    if components.mutex__.locked( ): return
    components.text_system_prompt.visible = (
        components.toggle_system_prompt_display.value )
