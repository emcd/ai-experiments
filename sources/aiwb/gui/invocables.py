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
    component_ = (
        components.column_conversation_history[ -1 ]
        if component is None else component )
    if component_ is None: return ( )
    canister = component_.gui__.canister__
    # TODO: Use selected multichoice values instead of all possible.
    invocables = components.auxdata__.invocables
    # TODO: Provide supplements based on specification from invocable.
    supplements = __.accret.Dictionary(
        controls = _providers.package_controls( components ) )
    model = await _providers.access_model_selection( components )
    requests = model.client.conversers.requests_from_canister(
        model,
        auxdata = components.auxdata__,
        supplements = supplements,
        canister = canister,
        invocables = invocables,
        ignore_invalid_canister = silent_extraction_failure )
    return requests  # noqa: RET504


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


def provide_invoker_metadata( components ):
    ''' Returns per-invoker metadata for the invocable selector.

        Per OpenSpec define-invocation-data-contract (Three-Layer Tool-
        Source Model, requirement, scenario "Processor-aware rendering
        in the invocable selector"): each selector row is labeled with
        provenance (MCP badge for MCP-sourced Application tools) and
        rendered with respect to processor (Application selectable;
        Provider visible-but-disabled with a server-side execution
        tooltip). All current invokers are Application; the Provider
        branch is reserved for a future provider-native invoker and
        not exercised in R2.

        Yields ``(name, processor, provenance)`` tuples covering every
        invoker registered with the harness, regardless of the current
        selector value, so callers can render the full visible-but-
        disabled state even when no tool is currently checked. '''
    invokers = components.auxdata__.invocables.invokers
    rows = [ ]
    for name, invoker in invokers.items( ):
        processor = getattr( invoker, 'processor', 'application' )
        provenance = getattr( invoker, 'provenance', None )
        provenance_str = getattr( provenance, 'value', None ) or (
            provenance if isinstance( provenance, str ) else 'local' )
        rows.append( dict(
            name = name, processor = processor, provenance = provenance_str ) )
    return tuple( rows )
