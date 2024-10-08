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


''' Common constants, imports, and utilities for GUI. '''

# ruff: noqa: F403,F405
# pylint: disable=unused-import
# TODO: Revist Ruff F405 after refactor.


from ..__ import *
from ..apiserver.qaliases import *
from ..appcore.qaliases import *
from ..libcore.qaliases import *
from ..providers.qaliases import *


scribe = acquire_scribe( __package__ ) # TODO: Not on module import.


roles_emoji = {
    'AI': '🤖',
    'Document': '📄',
    'Function': '\N{Hammer and Wrench}\uFE0F',
    'Human': '🧑',
}

roles_styles = {
    # TODO: Use style variables.
    'AI': {
        'background-color': 'WhiteSmoke',
    },
    'Document': {
        'background-color': 'White',
        'border-top': '2px dashed LightGray',
        'padding': '3px',
    },
    'Function': {
        'background-color': 'White',
        #'border-top': '2px dashed LightGray',
        #'padding': '3px',
    },
    'Human': {
        'background-color': 'White',
    },
}


def access_ai_provider_current( gui ):
    # TODO: Move to aiwb.gui.providers.
    return gui.auxdata__.providers[ gui.selector_provider.value ]


def assimilate_canister_dto_from_gui( canister_gui ):
    # TODO: Move to aiwb.gui.messages.
    dto = canister_gui.canister__
    behaviors = [ ]
    for behavior in ( 'active', 'pinned' ):
        if getattr( canister_gui, f"toggle_{behavior}" ).value:
            behaviors.append( behavior )
    dto.attributes.behaviors = behaviors
    # TODO: Implement full array support.
    data = (
        canister_gui.text_message.object
        if hasattr( canister_gui.text_message, 'object' )
        else canister_gui.text_message.value )
    dto[ 0 ].data = data


def assimilate_canister_dto_to_gui( canister_gui ):
    # TODO: Move to aiwb.gui.messages.
    dto = canister_gui.canister__
    # TODO: Implement full array support.
    canister_gui.text_message.object = dto[ 0 ].data
    behaviors = getattr( dto.attributes, 'behaviors', [ ] )
    for behavior in ( 'active', 'pinned' ):
        value = behavior in behaviors
        getattr( canister_gui, f"toggle_{behavior}" ).value = value


def calculate_conversations_path( gui ):
    # TODO: Use aiwb.messages.DirectoryManager instead.
    return gui.auxdata__.provide_state_location( 'conversations' )


def package_controls( gui ):
    # TODO: Move to aiwb.gui.controls.
    return dict(
        provider = gui.selector_provider.value,
        model = gui.selector_model.value,
        temperature = gui.slider_temperature.value,
    )


def package_messages( gui ):
    # TODO: Move to aiwb.gui.messages.
    from ..messages.core import Canister
    canisters = [ ]
    if gui.toggle_system_prompt_active.value:
        canisters.append(
            Canister( role = 'Supervisor' ).add_content(
                gui.text_system_prompt.object ) )
    for canister in gui.column_conversation_history:
        canister_gui = canister.gui__
        if not canister_gui.toggle_active.value: continue
        assimilate_canister_dto_from_gui( canister_gui )
        canisters.append( canister_gui.canister__ )
    return canisters


def package_special_data( components ):
    ''' Packages special data from GUI to ship to AI provider. '''
    # TODO: Move to aiwb.gui.invocables.
    from .invocables import provide_active_invocables
    special_data = { }
    supports_invocations = (
        components.selector_model.auxdata__[ components.selector_model.value ]
        .attributes.supports_invocations )
    if supports_invocations:
        invocables = provide_active_invocables( components )
        if invocables: special_data[ 'invocables' ] = invocables
    return special_data
