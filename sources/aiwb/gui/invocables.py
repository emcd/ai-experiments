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
from . import providers as _providers


async def extract_invocation_requests(
    components,
    component = None,
    silent_extraction_failure: bool = False,
):
    ''' Extracts invocation requests from message canister GUI component. '''
    if None is component:
        component = components.column_conversation_history[ -1 ]
    canister = component.gui__.canister__
    # TODO: Use selected multichoice values instead of all possible.
    invocables = components.auxdata__.invocables
    # TODO: Provide supplements based on specification from invocable.
    supplements = __.accret.Dictionary(
        controls = _providers.package_controls( components ) )
    model = await _providers.access_model_selection( components )
    requests = model.invocations_processor.requests_from_canister(
        auxdata = components.auxdata__,
        supplements = supplements,
        canister = canister,
        invocables = invocables,
        ignore_invalid_canister = silent_extraction_failure )
    return requests


async def package_invocables( components ):
    ''' Packages special data from GUI to ship to AI provider. '''
    special_data = { }
    supports_invocations = (
        ( await _providers.access_model_selection( components ) )
        .attributes.supports_invocations )
    if supports_invocations:
        invokers = provide_invokers_selection( components )
        if invokers: special_data[ 'invokers' ] = invokers
    return special_data


def provide_invokers_selection( components ):
    ''' Returns invokers for currently selected invocables. '''
    # TODO: Remove visibility restriction once fill of system prompt
    #       is implemented for non-functions-supporting models.
    if not components.row_functions_prompt.visible: return [ ]
    if not components.toggle_functions_active.value: return [ ]
    if not components.multichoice_functions.value: return [ ]
    invokers = components.auxdata__.invocables.invokers
    return tuple(
        invoker for name, invoker in invokers.items( )
        if name in components.multichoice_functions.value )
