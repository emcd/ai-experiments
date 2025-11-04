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


''' Management of conversations for Holoviz Panel GUI. '''


#from . import __


def alter_message_edit_mode( message_components, mode ):
    ''' Enables or disables edit mode for message. '''
    message_components.button_edit.enabled = not mode
    message_components.text_message.visible = not mode
    message_components.column_edit.visible = mode


def alter_title_edit_mode( indicator_components, mode ):
    ''' Enables or disables edit mode for conversation title. '''
    indicator_components.text_title.visible = not mode
    indicator_components.column_title_edit.visible = mode
    if mode: indicator_components.interceptor_actions.visible = False


def assimilate_canister_dto_from_gui( canister_components ):
    ''' Assimilates message canister from GUI display. '''
    canister = canister_components.canister__
    behaviors = [ ]
    for behavior in ( 'active', 'pinned' ):
        if getattr( canister_components, f"toggle_{behavior}" ).value:
            behaviors.append( behavior ) # noqa: PERF401
    canister.attributes.behaviors = behaviors
    # TODO: Implement full array support.
    if canister:
        data = (
            canister_components.text_message.object
            if hasattr( canister_components.text_message, 'object' )
            else canister_components.text_message.value )
        canister[ 0 ].data = data


def assimilate_canister_dto_to_gui( canister_components ):
    ''' Assimilates GUI display of message from canister. '''
    canister = canister_components.canister__
    # TODO: Implement full array support.
    if canister:
        canister_components.text_message.object = canister[ 0 ].data
    elif hasattr( canister.attributes, 'invocation_data' ):
        canister_components.text_message.object = (
            canister.attributes.invocation_data )
    behaviors = getattr( canister.attributes, 'behaviors', [ ] )
    for behavior in ( 'active', 'pinned' ):
        value = behavior in behaviors
        getattr( canister_components, f"toggle_{behavior}" ).value = value


def provide_location( components, *appendages ):
    # TODO: Use aiwb.messages.DirectoryManager instead.
    location = components.auxdata__.provide_state_location( 'conversations' )
    if not appendages: return location
    return location.joinpath( *appendages )


def package_messages( components ):
    ''' Packages GUI display of conversation into normalized objects. '''
    # TODO: Use an underlying conversation model.
    #       Do not pull values from GUI.
    from ..messages.core import SupervisorCanister
    canisters = [ ]
    if components.toggle_system_prompt_active.value:
        canisters.append(
            SupervisorCanister( )
            .add_content( components.text_system_prompt.object ) )
    for canister in components.column_conversation_history:
        canister_gui = canister.gui__
        if not canister_gui.toggle_active.value: continue
        assimilate_canister_dto_from_gui( canister_gui )
        canisters.append( canister_gui.canister__ )
    return canisters
