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
#  distributed under the License is distributed on an "AS IS" BASIS,        #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and        #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' FE Web section 3.2 Provider-processor seam: focused invariants.

    Per OpenSpec define-invocation-data-contract section 3.2
    (Three-Layer Tool-Source Model): Provider-processor descriptors
    are reserved for future provider-native tools whose supersession is
    server-side. The FE GUI must therefore exclude them from the
    Application dedup/supersession pool, must not let them contribute
    to whole-canister Application dedup deactivation, and must not
    let them appear in the selectable invocable selector.

    No actual Provider invoker is registered today. The invariants
    below exercise the seam with synthesized Provider descriptors on an
    Application invoker registry, which is the closest
    test-observable surface available without modifying provider
    extraction/execution or persistence migration. '''


from __future__ import annotations

import asyncio
import types as _types
from uuid import uuid4

from sources.aiwb.invocables.core import Invoker
from sources.aiwb.invocables.ensembles.io.deduplicators import (
    IoContentDeduplicator,
)
from sources.aiwb.messages.core import (
    InvocationCanister,
    ResultCanister,
)


class _Ensemble:
    name = 'smoke'


async def _read_invocable( context, arguments ):
    return {
        'tool': 'read',
        'location': arguments[ 'location' ],
        'correlation_id': context.correlation_id,
    }


_READ_SCHEMA = {
    'type': 'object',
    'properties': { 'location': { 'type': 'string' } },
    'required': [ 'location' ],
}


def _build_application_invoker( name ):
    return Invoker(
        name = name,
        ensemble = _Ensemble( ),  # type: ignore[arg-type]
        invocable = _read_invocable,
        argschema = dict( _READ_SCHEMA ),
        deduplicator_class = IoContentDeduplicator,
        processor = 'application',
    )


def _history_entry(
    canister, *, active = True, pinned = False,
):
    return _types.SimpleNamespace(
        gui__ = _types.SimpleNamespace(
            canister__ = canister,
            toggle_active = _types.SimpleNamespace( value = active ),
            toggle_pinned = _types.SimpleNamespace( value = pinned ),
            toggle_details = _types.SimpleNamespace( value = False ),
            text_message = _types.SimpleNamespace( object = None ),
        )
    )


def _invocation_canister( descriptors ):
    canister = InvocationCanister( )
    canister.attributes.invocation_data = descriptors
    canister.attributes.behaviors = [ 'active' ]
    return canister


def _result_canister( correlation_id ):
    canister = ResultCanister( )
    canister.add_content( '{}', mimetype = 'application/json' )
    canister.attributes.correlation_id = correlation_id
    canister.attributes.behaviors = [ 'active' ]
    return canister


def _components(
    history, invokers, *, configuration = None, dedupe = True,
):
    configuration = (
        { } if configuration is None else dict( configuration ) )
    return _types.SimpleNamespace(
        column_conversation_history = history,
        auxdata__ = _types.SimpleNamespace(
            invocables = _types.SimpleNamespace( invokers = invokers ),
            configuration = configuration,
        ),
        checkbox_deduplicate_invocations = _types.SimpleNamespace(
            value = dedupe ),
    )


async def _do_dedup( history, invokers ):
    from sources.aiwb.gui import actions as _actions
    return await _actions._deduplicate_invocations(
        _components( history, invokers ) )


def _do_provide_selection( invokers, *, configuration = None ):
    ''' Runs ``update_invocations_prompt``'s selectable filter in
        isolation against the provided invokers and reports the names
        that survive into ``multichoice_functions.options``. '''
    from sources.aiwb.gui import updaters as _updaters
    associated_functions = { name: True for name in invokers }
    return _updaters._selectable_invoker_names(
        invokers, associated_functions )


# -- Dedup invariants ----------------------------------------------------

async def test_provider_does_not_match_application( ):
    ''' Newer Provider + older Application (same name, same args).
        The Provider processor is filtered out of the dedup pool, so
        the older Application does NOT match it and is NOT superseded.
        Result: no deactivations. '''
    cid_app_older = uuid4( ).hex
    cid_provider = uuid4( ).hex
    invokers = { 'read': _build_application_invoker( 'read' ) }
    older_app = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://same' },
        'correlation_id': cid_app_older,
        'processor': 'application',
    } ] )
    older_result = _result_canister( cid_app_older )
    newer_provider = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://same' },
        'correlation_id': cid_provider,
        'processor': 'provider',
    } ] )
    newer_provider_result = _result_canister( cid_provider )
    history = [
        _history_entry( older_app ),
        _history_entry( older_result ),
        _history_entry( newer_provider ),
        _history_entry( newer_provider_result ),
    ]
    deactivations = await _do_dedup( history, invokers )
    # Provider was filtered; older did not match anything.
    assert deactivations == ( )


async def test_application_does_not_match_provider( ):
    ''' Newer Application + older Provider (same name, same args).
        The older Provider processor is filtered out of the dedup pool,
        so it does NOT register as a dedup candidate and the newer
        Application does not match it. Result: no deactivations. '''
    cid_provider_older = uuid4( ).hex
    cid_app_newer = uuid4( ).hex
    invokers = { 'read': _build_application_invoker( 'read' ) }
    older_provider = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://same' },
        'correlation_id': cid_provider_older,
        'processor': 'provider',
    } ] )
    older_result = _result_canister( cid_provider_older )
    newer_app = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://same' },
        'correlation_id': cid_app_newer,
        'processor': 'application',
    } ] )
    newer_app_result = _result_canister( cid_app_newer )
    history = [
        _history_entry( older_provider ),
        _history_entry( older_result ),
        _history_entry( newer_app ),
        _history_entry( newer_app_result ),
    ]
    deactivations = await _do_dedup( history, invokers )
    assert deactivations == ( )


async def test_provider_does_not_trigger_whole_canister( ):
    ''' A canister whose only descriptor is Provider-processor must
        NOT be deactivated wholesale by the whole-canister shortcut,
        even when no dedup match occurred. The Provider descriptor is
        excluded from the Application dedup pool entirely. '''
    cid_provider = uuid4( ).hex
    invokers = { 'read': _build_application_invoker( 'read' ) }
    provider_only = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://provider-only' },
        'correlation_id': cid_provider,
        'processor': 'provider',
    } ] )
    provider_result = _result_canister( cid_provider )
    history = [
        _history_entry( provider_only ),
        _history_entry( provider_result ),
    ]
    deactivations = await _do_dedup( history, invokers )
    # Provider descriptor is filtered out of all_duplicates accounting,
    # so whole-canister deactivation does not fire.
    assert 0 not in deactivations
    assert 1 not in deactivations


async def test_mixed_canister_provider_does_not_drag( ):
    ''' A canister with one matched Application call and one Provider
        call must NOT be deactivated wholesale. The matched Application
        call's result IS deactivated, but the Provider descriptor does
        not contribute to the "all duplicates" accounting, so
        all_duplicates stays False. '''
    cid_app_older = uuid4( ).hex
    cid_provider = uuid4( ).hex
    cid_app_newer = uuid4( ).hex
    invokers = { 'read': _build_application_invoker( 'read' ) }
    older_mixed = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://same' },
        'correlation_id': cid_app_older,
        'processor': 'application',
    }, {
        'name': 'read',
        'arguments': { 'location': 'mock://provider-only' },
        'correlation_id': cid_provider,
        'processor': 'provider',
    } ] )
    older_app_result = _result_canister( cid_app_older )
    provider_result = _result_canister( cid_provider )
    newer_app = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://same' },
        'correlation_id': cid_app_newer,
        'processor': 'application',
    } ] )
    newer_app_result = _result_canister( cid_app_newer )
    history = [
        _history_entry( older_mixed ),
        _history_entry( older_app_result ),
        _history_entry( provider_result ),
        _history_entry( newer_app ),
        _history_entry( newer_app_result ),
    ]
    deactivations = await _do_dedup( history, invokers )
    # The Application call's result (index 1) IS superseded by the
    # newer App call. The whole older canister (index 0) is NOT
    # deactivated wholesale because all_duplicates is False (the
    # Provider descriptor does not contribute).
    assert 1 in deactivations
    assert 0 not in deactivations


async def test_application_only_whole_canister_still_works( ):
    ''' A canister with only matched Application calls must continue to
        be deactivated wholesale. The Provider filter must not break
        the historical Application-only path. '''
    cid_old = uuid4( ).hex
    cid_new = uuid4( ).hex
    invokers = { 'read': _build_application_invoker( 'read' ) }
    older = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://file' },
        'correlation_id': cid_old,
        'processor': 'application',
    } ] )
    newer = _invocation_canister( [ {
        'name': 'read',
        'arguments': { 'location': 'mock://file' },
        'correlation_id': cid_new,
        'processor': 'application',
    } ] )
    history = [
        _history_entry( older ),
        _history_entry( _result_canister( cid_old ) ),
        _history_entry( newer ),
        _history_entry( _result_canister( cid_new ) ),
    ]
    deactivations = await _do_dedup( history, invokers )
    assert 1 in deactivations  # older result
    assert 0 in deactivations  # whole older invocation canister


# -- Selector invariants --------------------------------------------------

def _build_provider_invoker( name ):
    return Invoker(
        name = name,
        ensemble = _Ensemble( ),  # type: ignore[arg-type]
        invocable = _read_invocable,
        argschema = dict( _READ_SCHEMA ),
        deduplicator_class = IoContentDeduplicator,
        processor = 'provider',
    )


def test_provider_excluded_from_selectable( ):
    ''' A Provider-processor invoker must NOT appear in the selectable
        options even when associated with the prompt's ``functions``
        set. The Application invoker remains selectable. '''
    invokers = {
        'read': _build_application_invoker( 'read' ),
        'code_interpreter': _build_provider_invoker( 'code_interpreter' ),
    }
    options = _do_provide_selection( invokers )
    assert 'read' in options
    assert 'code_interpreter' not in options


def test_provider_excluded_under_include_policy( ):
    ''' Even when ``provider_native_tools_policy`` is set to ``include``
        (the future "visible-but-disabled" mode), the current seam
        keeps Provider invokers out of the selectable options. The
        disabled-row rendering is the next phase of section 3.2. '''
    invokers = {
        'code_interpreter': _build_provider_invoker( 'code_interpreter' ),
    }
    options = _do_provide_selection(
        invokers,
        configuration = { 'provider_native_tools_policy': 'include' } )
    # The seam is conservative: regardless of policy value, the
    # Provider invoker is excluded until the disabled-row rendering
    # lands.
    assert 'code_interpreter' not in options


# -- Display projection invariant -----------------------------------------

def test_default_projection_carries_provider_label( ):
    ''' The default user-visible projection renders the ``processor``
        label so users see Provider invocations distinguished from
        Application ones, but it must not include the supplement or
        provider call ids. '''
    from sources.aiwb.gui import projections as _projections
    cid = uuid4( ).hex
    record = {
        'name': 'code_interpreter',
        'arguments': { 'code': 'print(1)' },
        'correlation_id': cid,
        'processor': 'provider',
        'supplement': { 'id': 'toolu_provider_secret' },
    }
    payload = _projections.display_payload( record )
    assert payload[ 'processor' ] == 'provider'
    assert 'supplement' not in payload
    rendered = _projections.render_projection( record )
    assert cid in rendered
    assert 'toolu_provider_secret' not in rendered
    # Parallel blocks stay discrete; processor labels remain visible.
    other = {
        'name': 'read',
        'arguments': { 'location': 'mock://p' },
        'correlation_id': uuid4( ).hex,
        'processor': 'application',
    }
    multi = _projections.render_invocation_data_projection(
        [ record, other ] )
    assert multi.count( '**Processor**' ) == 2
    assert '`provider`' in multi
    assert '`application`' in multi


# -- Smoke runner --------------------------------------------------------

def _run( coroutine ):
    loop = asyncio.new_event_loop( )
    try: return loop.run_until_complete( coroutine )
    finally: loop.close( )


def test_001_provider_does_not_match_application( ):
    _run( test_provider_does_not_match_application( ) )


def test_002_application_does_not_match_provider( ):
    _run( test_application_does_not_match_provider( ) )


def test_003_provider_does_not_trigger_whole_canister( ):
    _run( test_provider_does_not_trigger_whole_canister( ) )


def test_004_mixed_canister_provider_does_not_drag( ):
    _run( test_mixed_canister_provider_does_not_drag( ) )


def test_005_application_only_still_works( ):
    _run( test_application_only_whole_canister_still_works( ) )


def test_006_provider_excluded_from_selectable( ):
    test_provider_excluded_from_selectable( )


def test_007_provider_excluded_under_include_policy( ):
    test_provider_excluded_under_include_policy( )


def test_008_default_projection_carries_provider_label( ):
    test_default_projection_carries_provider_label( )
