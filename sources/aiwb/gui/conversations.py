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


def assimilate_canister_dto_from_gui( canister_components ):
    ''' Assimilates message canister from GUI display. '''
    dto = canister_components.canister__
    behaviors = [ ]
    for behavior in ( 'active', 'pinned' ):
        if getattr( canister_components, f"toggle_{behavior}" ).value:
            behaviors.append( behavior )
    dto.attributes.behaviors = behaviors
    # TODO: Implement full array support.
    data = (
        canister_components.text_message.object
        if hasattr( canister_components.text_message, 'object' )
        else canister_components.text_message.value )
    dto[ 0 ].data = data


def assimilate_canister_dto_to_gui( canister_components ):
    ''' Assimilates GUI display of message from canister. '''
    dto = canister_components.canister__
    # TODO: Implement full array support.
    canister_components.text_message.object = dto[ 0 ].data
    behaviors = getattr( dto.attributes, 'behaviors', [ ] )
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
