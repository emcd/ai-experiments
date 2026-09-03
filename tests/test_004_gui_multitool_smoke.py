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


''' OpenSpec task 4.1 GUI-path mock multi-tool smoke.

    Exercises extract_invocation_requests → gather_async →
    _deduplicate_invocations with mock converser and mock invokers.
    Covers parallel calls, name/arguments-only IoContentDeduplicator
    supersession, correlation-ID result linkage (positional fallback
    secondary), whole-invocation deactivation, and GUI display
    projection excluding provider supplements by default.
'''


from __future__ import annotations

import dataclasses as _dcls
import types as _types
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from sources.aiwb.gui import actions as _actions
from sources.aiwb.gui import invocables as _gui_invocables
from sources.aiwb.gui import projections as _projections
from sources.aiwb.invocables.core import Invoker
from sources.aiwb.invocables.ensembles.io.deduplicators import (
    IoContentDeduplicator,
)
from sources.aiwb.messages.core import (
    InvocationCanister,
    ResultCanister,
)
from sources.aiwb.providers import __ as _prov
from sources.aiwb.providers import core as _core
from sources.aiwb.providers import utilities as _utilities


class _Ensemble:
    name = 'smoke'


async def _read_invocable( context, arguments ):
    return {
        'tool': 'read',
        'location': arguments[ 'location' ],
        'correlation_id': context.correlation_id,
    }


async def _write_invocable( context, arguments ):
    return {
        'tool': 'write_file',
        'location': arguments[ 'location' ],
        'correlation_id': context.correlation_id,
    }


_READ_SCHEMA = {
    'type': 'object',
    'properties': { 'location': { 'type': 'string' } },
    'required': [ 'location' ],
}
_WRITE_SCHEMA = {
    'type': 'object',
    'properties': {
        'location': { 'type': 'string' },
        'content': { 'type': 'string' },
    },
    'required': [ 'location', 'content' ],
}


def _build_invokers( ) -> dict[ str, Invoker ]:
    return {
        'read': Invoker(
            name = 'read',
            ensemble = _Ensemble( ),  # type: ignore[arg-type]
            invocable = _read_invocable,
            argschema = dict( _READ_SCHEMA ),
            deduplicator_class = IoContentDeduplicator,
        ),
        'write_file': Invoker(
            name = 'write_file',
            ensemble = _Ensemble( ),  # type: ignore[arg-type]
            invocable = _write_invocable,
            argschema = dict( _WRITE_SCHEMA ),
            deduplicator_class = IoContentDeduplicator,
        ),
    }


def _tool_call(
    call_id: str, name: str, arguments_json: str,
) -> dict[ str, Any ]:
    return {
        'type': 'function',
        'id': call_id,
        'function': { 'name': name, 'arguments': arguments_json },
    }


class _MockConversers:
    ''' Mock converser mirroring OpenAI extract/execute contract surface. '''

    def requests_from_canister(
        self,
        model,
        auxdata, *,
        supplements,
        canister,
        invocables,
        ignore_invalid_canister = False,
    ):
        supplements[ 'model' ] = model
        model_context = getattr( canister.attributes, 'model_context', { } )
        if model.provider.name != model_context.get( 'provider' ):
            if ignore_invalid_canister: return [ ]
            raise AssertionError( 'provider mismatch in mock' )
        requests = _utilities.invocation_requests_from_canister(
            auxdata = auxdata,
            supplements = supplements,
            canister = canister,
            invocables = invocables,
            ignore_invalid_canister = ignore_invalid_canister )
        supplement = model_context.get( 'supplement', { } )
        tool_calls = supplement.get( 'tool_calls' ) or [ ]
        if len( requests ) != len( tool_calls ):
            raise AssertionError( 'request/tool_call length mismatch' )
        return tuple(
            _dcls.replace(
                request,
                supplement = _core.InvocationSupplement.from_mapping(
                    envelope ),
            )
            for request, envelope in zip(
                requests, tool_calls, strict = True )
        )

    async def execute_invocation( self, model, request ):
        content = await request.invocation( )
        canister = ResultCanister( )
        canister.add_content(
            str( content ), mimetype = 'application/json' )
        canister.attributes.correlation_id = request.correlation_id
        canister.attributes.model_context = {
            'provider': model.provider.name,
            'model': model.name,
            'supplement': {
                'tool_call_id': request.supplement.payload.get( 'id' ),
                'role': 'tool',
            },
        }
        return canister


def _make_model( ):
    provider = _types.SimpleNamespace( name = 'mock-provider' )
    conversers = _MockConversers( )
    client = _types.SimpleNamespace( conversers = conversers )
    return _types.SimpleNamespace(
        provider = provider,
        name = 'mock-model',
        client = client,
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


def _invocation_canister(
    descriptors: list[ dict[ str, Any ] ],
    tool_calls: list[ dict[ str, Any ] ],
) -> InvocationCanister:
    canister = InvocationCanister( )
    canister.attributes.invocation_data = descriptors
    canister.attributes.model_context = {
        'provider': 'mock-provider',
        'model': 'mock-model',
        'supplement': {
            'tool_calls': tool_calls,
            'secret_provider_key': 'must-not-leak-to-default-display',
        },
    }
    canister.attributes.behaviors = [ 'active' ]
    return canister


def _result_canister( correlation_id: str ) -> ResultCanister:
    canister = ResultCanister( )
    canister.add_content( '{}', mimetype = 'application/json' )
    canister.attributes.correlation_id = correlation_id
    canister.attributes.behaviors = [ 'active' ]
    return canister


def _components(
    history: list,
    invokers: dict[ str, Invoker ],
    *,
    dedupe = True,
):
    return _types.SimpleNamespace(
        column_conversation_history = history,
        auxdata__ = _types.SimpleNamespace(
            invocables = _types.SimpleNamespace( invokers = invokers ),
        ),
        checkbox_deduplicate_invocations = _types.SimpleNamespace(
            value = dedupe ),
    )


def test_001_extract_gather_pair_by_correlation_id( ) -> None:
    ''' extract → gather → results carry matching harness correlation IDs. '''
    import asyncio

    invokers = _build_invokers( )
    cid_a = uuid4( ).hex
    cid_b = uuid4( ).hex
    descriptors = [
        {
            'name': 'read',
            'arguments': { 'location': 'mock://a' },
            'correlation_id': cid_a,
            'processor': 'application',
        },
        {
            'name': 'write_file',
            'arguments': {
                'location': 'mock://b', 'content': 'x',
            },
            'correlation_id': cid_b,
            'processor': 'application',
        },
    ]
    tool_calls = [
        _tool_call( 'call_a', 'read', '{"location":"mock://a"}' ),
        _tool_call(
            'call_b', 'write_file',
            '{"location":"mock://b","content":"x"}' ),
    ]
    inv_canister = _invocation_canister( descriptors, tool_calls )
    history = [ _history_entry( inv_canister ) ]
    components = _components( history, invokers )
    model = _make_model( )

    async def _run( ):
        with (
            patch.object(
                _gui_invocables._providers, 'package_controls',
                return_value = { },
            ),
            patch.object(
                _gui_invocables._providers, 'access_model_selection',
                new = AsyncMock( return_value = model ),
            ),
        ):
            requests = await _gui_invocables.extract_invocation_requests(
                components )
        assert len( requests ) == 2
        assert requests[ 0 ].correlation_id == cid_a
        assert requests[ 1 ].correlation_id == cid_b
        assert requests[ 0 ].supplement.payload[ 'id' ] == 'call_a'
        assert requests[ 0 ].correlation_id != 'call_a'
        results = await _prov.asyncf.gather_async(
            *( model.client.conversers.execute_invocation(
                model, request ) for request in requests ) )
        return requests, results

    requests, results = asyncio.get_event_loop( ).run_until_complete( _run( ) )
    by_id = {
        result.attributes.correlation_id: result for result in results
    }
    assert set( by_id ) == { cid_a, cid_b }
    for request in requests:
        assert by_id[ request.correlation_id ] is not None


def test_002_dedup_by_correlation_id_and_name_arguments( ) -> None:
    ''' Newer read supersedes older same-path read via correlation_id. '''
    import asyncio

    invokers = _build_invokers( )
    cid_old = uuid4( ).hex
    cid_write = uuid4( ).hex
    cid_new = uuid4( ).hex
    # History: older multi-tool inv + results, then newer inv + result.
    older = _invocation_canister(
        [
            {
                'name': 'read',
                'arguments': { 'location': 'mock://same' },
                'correlation_id': cid_old,
                'processor': 'application',
            },
            {
                'name': 'write_file',
                'arguments': {
                    'location': 'mock://other', 'content': 'n',
                },
                'correlation_id': cid_write,
                'processor': 'application',
            },
        ],
        [
            _tool_call( 'c_old', 'read', '{"location":"mock://same"}' ),
            _tool_call(
                'c_w', 'write_file',
                '{"location":"mock://other","content":"n"}' ),
        ],
    )
    newer = _invocation_canister(
        [
            {
                'name': 'read',
                'arguments': { 'location': 'mock://same' },
                'correlation_id': cid_new,
                'processor': 'application',
            },
        ],
        [ _tool_call( 'c_new', 'read', '{"location":"mock://same"}' ) ],
    )
    history = [
        _history_entry( older ),
        _history_entry( _result_canister( cid_old ) ),
        _history_entry( _result_canister( cid_write ) ),
        _history_entry( newer ),
        _history_entry( _result_canister( cid_new ) ),
    ]
    components = _components( history, invokers )

    async def _run( ):
        return await _actions._deduplicate_invocations( components )

    deactivations = asyncio.get_event_loop( ).run_until_complete( _run( ) )
    # Older read's result (index 1) superseded; write result kept; newer kept.
    assert 1 in deactivations
    assert 2 not in deactivations
    assert 4 not in deactivations
    # Whole older invocation canister not fully superseded (write remains).
    assert 0 not in deactivations


def test_003_whole_invocation_deactivation_when_all_calls_superseded(
) -> None:
    ''' Invocation canister deactivates when every call is a duplicate. '''
    import asyncio

    invokers = _build_invokers( )
    cid_old = uuid4( ).hex
    cid_new = uuid4( ).hex
    older = _invocation_canister(
        [
            {
                'name': 'read',
                'arguments': { 'location': 'mock://file' },
                'correlation_id': cid_old,
                'processor': 'application',
            },
        ],
        [ _tool_call( 'c1', 'read', '{"location":"mock://file"}' ) ],
    )
    newer = _invocation_canister(
        [
            {
                'name': 'read',
                'arguments': { 'location': 'mock://file' },
                'correlation_id': cid_new,
                'processor': 'application',
            },
        ],
        [ _tool_call( 'c2', 'read', '{"location":"mock://file"}' ) ],
    )
    history = [
        _history_entry( older ),
        _history_entry( _result_canister( cid_old ) ),
        _history_entry( newer ),
        _history_entry( _result_canister( cid_new ) ),
    ]
    components = _components( history, invokers )

    async def _run( ):
        return await _actions._deduplicate_invocations( components )

    deactivations = asyncio.get_event_loop( ).run_until_complete( _run( ) )
    assert 1 in deactivations  # older result
    assert 0 in deactivations  # whole older invocation canister


def test_004_legacy_positional_fallback_when_correlation_id_missing(
) -> None:
    ''' Pre-R2 descriptors without correlation_id still pair positionally. '''
    import asyncio

    invokers = _build_invokers( )
    cid_new = uuid4( ).hex
    # Older descriptor intentionally omits correlation_id (legacy shape).
    older = _invocation_canister(
        [
            {
                'name': 'read',
                'arguments': { 'location': 'mock://legacy' },
                'processor': 'application',
            },
        ],
        [ _tool_call( 'c_leg', 'read', '{"location":"mock://legacy"}' ) ],
    )
    # Result sits at i+j+1 = 0+0+1 = 1 without correlation_id on attributes.
    legacy_result = ResultCanister( )
    legacy_result.add_content( '{}', mimetype = 'application/json' )
    legacy_result.attributes.behaviors = [ 'active' ]
    newer = _invocation_canister(
        [
            {
                'name': 'read',
                'arguments': { 'location': 'mock://legacy' },
                'correlation_id': cid_new,
                'processor': 'application',
            },
        ],
        [ _tool_call( 'c_new', 'read', '{"location":"mock://legacy"}' ) ],
    )
    history = [
        _history_entry( older ),
        _history_entry( legacy_result ),
        _history_entry( newer ),
        _history_entry( _result_canister( cid_new ) ),
    ]
    components = _components( history, invokers )

    async def _run( ):
        return await _actions._deduplicate_invocations( components )

    deactivations = asyncio.get_event_loop( ).run_until_complete( _run( ) )
    assert 1 in deactivations
    assert 0 in deactivations


def test_005_display_projection_excludes_provider_supplement( ) -> None:
    ''' Default GUI projection shows normalized fields only. '''
    cid = uuid4( ).hex
    record = {
        'name': 'read',
        'arguments': { 'location': 'mock://z' },
        'correlation_id': cid,
        'processor': 'application',
        # Should never appear in default projection even if present.
        'supplement': { 'id': 'call_secret' },
    }
    payload = _projections.display_payload( record )
    assert set( payload ) == {
        'name', 'arguments', 'correlation_id', 'processor',
    }
    assert payload[ 'name' ] == 'read'
    assert payload[ 'correlation_id' ] == cid
    assert 'supplement' not in payload
    assert 'call_secret' not in repr( payload )
    rendered = _projections.render_projection( record )
    assert cid in rendered
    assert 'call_secret' not in rendered
    assert 'must-not-leak' not in rendered
    # Parallel blocks stay discrete and normalized.
    multi = _projections.render_invocation_data_projection(
        [ record, {
            'name': 'write_file',
            'arguments': { 'location': 'mock://y', 'content': 'q' },
            'correlation_id': uuid4( ).hex,
            'processor': 'application',
        } ] )
    assert multi.count( '**Invocation**' ) == 2
    assert '---' in multi
    # Opt-in raw envelope may include supplement; default path must not.
    canister = _invocation_canister(
        [ record ],
        [ _tool_call( 'call_secret', 'read', '{"location":"mock://z"}' ) ],
    )
    raw = _projections.render_raw_envelope( canister )
    assert 'must-not-leak-to-default-display' in raw
    assert 'call_secret' in raw
    default_body = _projections.render_invocation_data_projection(
        canister.attributes.invocation_data )
    assert 'must-not-leak-to-default-display' not in default_body
    assert 'call_secret' not in default_body


def test_006_end_to_end_extract_gather_dedup_projection( ) -> None:
    ''' Full 4.1 path: extract, gather, history dedup, projection boundary. '''
    import asyncio

    invokers = _build_invokers( )
    cid_a = uuid4( ).hex
    cid_b = uuid4( ).hex
    descriptors = [
        {
            'name': 'read',
            'arguments': { 'location': 'mock://e2e' },
            'correlation_id': cid_a,
            'processor': 'application',
        },
        {
            'name': 'read',
            'arguments': { 'location': 'mock://e2e' },
            'correlation_id': cid_b,
            'processor': 'application',
        },
    ]
    tool_calls = [
        _tool_call( 'call_1', 'read', '{"location":"mock://e2e"}' ),
        _tool_call( 'call_2', 'read', '{"location":"mock://e2e"}' ),
    ]
    # Two sequential invocation turns, each with one call (parallel batch
    # of two on one canister also works for extract; for dedup we need
    # newer vs older canisters).
    first = _invocation_canister(
        [ descriptors[ 0 ] ], [ tool_calls[ 0 ] ] )
    second = _invocation_canister(
        [ descriptors[ 1 ] ], [ tool_calls[ 1 ] ] )
    model = _make_model( )

    async def _run( ):
        history = [ _history_entry( first ) ]
        components = _components( history, invokers )
        with (
            patch.object(
                _gui_invocables._providers, 'package_controls',
                return_value = { },
            ),
            patch.object(
                _gui_invocables._providers, 'access_model_selection',
                new = AsyncMock( return_value = model ),
            ),
        ):
            reqs_first = await _gui_invocables.extract_invocation_requests(
                components )
        results_first = await _prov.asyncf.gather_async(
            *( model.client.conversers.execute_invocation( model, r )
               for r in reqs_first ) )
        history.extend(
            _history_entry( result ) for result in results_first )
        history.append( _history_entry( second ) )
        components = _components( history, invokers )
        with (
            patch.object(
                _gui_invocables._providers, 'package_controls',
                return_value = { },
            ),
            patch.object(
                _gui_invocables._providers, 'access_model_selection',
                new = AsyncMock( return_value = model ),
            ),
        ):
            reqs_second = await _gui_invocables.extract_invocation_requests(
                components )
        results_second = await _prov.asyncf.gather_async(
            *( model.client.conversers.execute_invocation( model, r )
               for r in reqs_second ) )
        history.extend(
            _history_entry( result ) for result in results_second )
        components = _components( history, invokers )
        deactivations = await _actions._deduplicate_invocations(
            components )
        return reqs_first, reqs_second, deactivations

    reqs_first, reqs_second, deactivations = (
        asyncio.get_event_loop( ).run_until_complete( _run( ) ) )
    assert reqs_first[ 0 ].correlation_id == cid_a
    assert reqs_second[ 0 ].correlation_id == cid_b
    # First result (index 1) superseded by second read same path.
    assert 1 in deactivations
    assert 0 in deactivations  # whole first invocation
    # Default projection never includes provider call ids from supplements.
    body = _projections.render_invocation_data_projection(
        first.attributes.invocation_data )
    assert cid_a in body
    assert 'call_1' not in body
    assert 'must-not-leak' not in body
