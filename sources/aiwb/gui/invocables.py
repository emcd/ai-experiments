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


''' Functionality related to callable tools in GUI. '''


from . import __


def extract_invocation_requests(
    components, component = None, close_invokers = False
):
    ''' Extracts invocation requests from message canister GUI component. '''
    from dataclasses import fields
    if None is component:
        component = components.column_conversation_history[ -1 ]
    canister = component.gui__.canister__
    # TODO: Use selected multichoice values instead of all possible.
    invocables = components.auxdata__.invocables
    auxdata = __.SimpleNamespace(
        controls = __.package_controls( components ),
        **{ field.name: getattr( components.auxdata__, field.name )
            for field in fields( components.auxdata__ ) } )
    provider = __.access_ai_provider_current( components )
    requests = provider.extract_invocation_requests(
        canister, auxdata, invocables )
    if close_invokers:
        for request in requests:
            request[ 'invocable__' ].close( )
    return requests


def provide_active_invocables( components ):
    ''' Returns currently selected invocables. '''
    # TODO: Remove visibility restriction once fill of system prompt
    #       is implemented for non-functions-supporting models.
    if not components.row_functions_prompt.visible: return [ ]
    if not components.toggle_functions_active.value: return [ ]
    if not components.multichoice_functions.value: return [ ]
    invokers = components.auxdata__.invocables.invokers
    return tuple(
        invoker for name, invoker in invokers.items( )
        if name in components.multichoice_functions.value )