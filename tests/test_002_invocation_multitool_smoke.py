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


''' Mock multi-tool invocation smoke (OpenSpec task 4.1 application path).

    Covers extraction → async gather → correlation-ID pairing → IoContent
    dedup supersession → normalized display projection without GUI/Panel,
    credentials, or application inspection of provider supplements.

    GUI-owned steps still pending FE Web (tasks 1.4-1.6): correlation-ID
    pairing inside gui/actions._deactivate_duplicate_invocations, and the
    production display_payload renderer. This module documents those
    contracts with pure helpers and exercises the provider/invocables seams
    available on master ce30edd.
'''


from __future__ import annotations

import dataclasses as _dcls
import types as _types
from typing import Any

from sources.aiwb.invocables.core import Invoker
from sources.aiwb.invocables.ensembles.io.deduplicators import (
    IoContentDeduplicator,
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


def _make_canister(
    invocation_data: list[ dict[ str, Any ] ],
    tool_calls: list[ dict[ str, Any ] ],
    *,
    provider: str = 'mock-provider',
) -> _types.SimpleNamespace:
    return _types.SimpleNamespace(
        attributes = _types.SimpleNamespace(
            invocation_data = invocation_data,
            model_context = {
                'provider': provider,
                'model': 'mock-model',
                'supplement': { 'tool_calls': tool_calls },
            },
        )
    )


def _tool_call(
    call_id: str, name: str, arguments_json: str,
) -> dict[ str, Any ]:
    return {
        'type': 'function',
        'id': call_id,
        'function': { 'name': name, 'arguments': arguments_json },
    }


def _extract_requests(
    canister: _types.SimpleNamespace,
    invokers: dict[ str, Invoker ],
) -> tuple[ _core.InvocationRequest, ... ]:
    ''' Mirrors OpenAI ``requests_from_canister`` without a live model. '''
    invocables = _prov.accret.Namespace( invokers = invokers )
    supplements = _prov.accret.Dictionary( )
    requests = _utilities.invocation_requests_from_canister(
        auxdata = None,
        supplements = supplements,
        canister = canister,
        invocables = invocables,
        ignore_invalid_canister = False,
    )
    model_context = canister.attributes.model_context
    tool_calls = model_context[ 'supplement' ][ 'tool_calls' ]
    if len( requests ) != len( tool_calls ):
        raise AssertionError( 'request/tool_call length mismatch' )
    return tuple(
        _dcls.replace(
            request,
            supplement = _core.InvocationSupplement.from_mapping( envelope ),
        )
        for request, envelope in zip( requests, tool_calls, strict = True )
    )


async def _execute_invocation(
    request: _core.InvocationRequest,
) -> _types.SimpleNamespace:
    ''' Application-side execute: run invocable; pair via correlation_id. '''
    content = await request.invocation( )
    return _types.SimpleNamespace(
        correlation_id = request.correlation_id,
        name = request.name,
        content = content,
        # Provider envelope retained only for same-provider replay tests;
        # application pairing and display must not inspect it.
        provider_supplement = request.supplement,
    )


def project_invocation_display(
    request: _core.InvocationRequest,
) -> dict[ str, Any ]:
    ''' Normalized display projection contract (GUI renderer pending FE). '''
    return {
        'name': request.name,
        'arguments': dict( request.arguments ),
        'correlation_id': request.correlation_id,
    }


def deactivate_duplicates_by_correlation(
    records: list[ dict[ str, Any ] ],
    invokers: dict[ str, Invoker ],
) -> tuple[ str, ... ]:
    ''' Correlation-ID dedup supersession (target shape for GUI task 1.5).

        ``records`` is newest-first or processed newest-last reverse order
        as GUI history does. Returns correlation IDs of superseded older
        invocations (not result history indices).
    '''
    deduplicators: dict[ str, list[ Any ] ] = { }
    deactivated: list[ str ] = [ ]
    # Process newest → oldest (same direction as gui/actions reverse scan
    # when walking history from the end; here records are chronological and
    # we reverse).
    for record in reversed( records ):
        name = record[ 'name' ]
        arguments = record[ 'arguments' ]
        correlation_id = record[ 'correlation_id' ]
        invoker = invokers.get( name )
        if invoker is None or invoker.deduplicator_class is None:
            continue
        superseded = False
        for dedup in deduplicators.get( name, [ ] ):
            if dedup.is_duplicate( name, arguments ):
                deactivated.append( correlation_id )
                superseded = True
                break
        if superseded:
            continue
        dedup = invoker.deduplicator_class(
            invocable_name = name, arguments = arguments )
        for name_ in invoker.deduplicator_class.provide_invocable_names( ):
            deduplicators.setdefault( name_, [ ] ).append( dedup )
    return tuple( deactivated )


def test_001_parallel_extract_gather_and_correlation_pairing( ) -> None:
    ''' Parallel tool calls mint distinct IDs and pair results by them. '''
    import asyncio

    invokers = _build_invokers( )
    invocation_data = [
        { 'name': 'read', 'arguments': { 'location': 'mock://a.txt' } },
        { 'name': 'write_file', 'arguments': {
            'location': 'mock://b.txt', 'content': 'x',
        } },
        { 'name': 'read', 'arguments': { 'location': 'mock://c.txt' } },
    ]
    tool_calls = [
        _tool_call( 'call_a', 'read', '{"location":"mock://a.txt"}' ),
        _tool_call(
            'call_b', 'write_file',
            '{"location":"mock://b.txt","content":"x"}' ),
        _tool_call( 'call_c', 'read', '{"location":"mock://c.txt"}' ),
    ]
    canister = _make_canister( invocation_data, tool_calls )
    requests = _extract_requests( canister, invokers )
    assert len( requests ) == 3
    ids = [ request.correlation_id for request in requests ]
    assert len( set( ids ) ) == 3
    for request in requests:
        assert len( request.correlation_id ) == 32
        assert request.processor is _core.InvocationProcessor.Application
        # Provider call id is in supplement only, never the app correlation id.
        assert request.correlation_id != request.supplement.payload[ 'id' ]

    async def _run( ):
        return await _prov.asyncf.gather_async(
            *( _execute_invocation( request ) for request in requests ) )

    results = asyncio.get_event_loop( ).run_until_complete( _run( ) )
    assert len( results ) == 3
    by_id = { result.correlation_id: result for result in results }
    for request in requests:
        result = by_id[ request.correlation_id ]
        assert result.name == request.name
        assert result.content[ 'correlation_id' ] == request.correlation_id


def test_002_display_projection_excludes_provider_supplement( ) -> None:
    ''' Display projection exposes only normalized fields. '''
    invokers = _build_invokers( )
    canister = _make_canister(
        [ { 'name': 'read', 'arguments': { 'location': '/x' } } ],
        [ _tool_call( 'call_x', 'read', '{"location":"/x"}' ) ],
    )
    request, = _extract_requests( canister, invokers )
    payload = project_invocation_display( request )
    assert set( payload ) == { 'name', 'arguments', 'correlation_id' }
    assert payload[ 'name' ] == 'read'
    assert payload[ 'arguments' ] == { 'location': '/x' }
    assert payload[ 'correlation_id' ] == request.correlation_id
    assert 'supplement' not in payload
    assert 'tool_calls' not in payload
    assert 'id' not in payload
    assert 'function' not in payload
    # Application boundary: pairing/display do not read supplement payload.
    assert request.supplement.payload[ 'id' ] == 'call_x'


def test_003_io_content_dedup_supersession_by_correlation_id( ) -> None:
    ''' Newer read supersedes older read at same path via correlation ID. '''
    invokers = _build_invokers( )
    # Chronological: older read, write elsewhere, newer read same path.
    invocation_data = [
        { 'name': 'read', 'arguments': { 'location': '/same' } },
        {
            'name': 'write_file',
            'arguments': { 'location': '/other', 'content': 'n' },
        },
        { 'name': 'read', 'arguments': { 'location': '/same' } },
    ]
    tool_calls = [
        _tool_call( 'call_old', 'read', '{"location":"/same"}' ),
        _tool_call(
            'call_w', 'write_file',
            '{"location":"/other","content":"n"}' ),
        _tool_call( 'call_new', 'read', '{"location":"/same"}' ),
    ]
    requests = _extract_requests(
        _make_canister( invocation_data, tool_calls ), invokers )
    records = [
        {
            'name': request.name,
            'arguments': dict( request.arguments ),
            'correlation_id': request.correlation_id,
        }
        for request in requests
    ]
    deactivated = deactivate_duplicates_by_correlation( records, invokers )
    # Newest read supersedes oldest read; write is independent.
    assert requests[ 0 ].correlation_id in deactivated
    assert requests[ 1 ].correlation_id not in deactivated
    assert requests[ 2 ].correlation_id not in deactivated


def test_004_write_file_supersedes_prior_read_same_location( ) -> None:
    ''' write_file supersedes earlier read on the same location. '''
    invokers = _build_invokers( )
    invocation_data = [
        { 'name': 'read', 'arguments': { 'location': '/file' } },
        {
            'name': 'write_file',
            'arguments': { 'location': '/file', 'content': 'new' },
        },
    ]
    tool_calls = [
        _tool_call( 'c1', 'read', '{"location":"/file"}' ),
        _tool_call(
            'c2', 'write_file',
            '{"location":"/file","content":"new"}' ),
    ]
    requests = _extract_requests(
        _make_canister( invocation_data, tool_calls ), invokers )
    records = [
        {
            'name': r.name,
            'arguments': dict( r.arguments ),
            'correlation_id': r.correlation_id,
        }
        for r in requests
    ]
    deactivated = deactivate_duplicates_by_correlation( records, invokers )
    assert requests[ 0 ].correlation_id in deactivated
    assert requests[ 1 ].correlation_id not in deactivated


def test_005_application_path_ignores_supplement_for_control_flow( ) -> None:
    ''' Dedup and display use only name/arguments/correlation_id. '''
    invokers = _build_invokers( )
    invocation_data = [
        { 'name': 'read', 'arguments': { 'location': '/z' } },
    ]
    # Malicious-looking nested keys must not leak into display or pairing.
    tool_calls = [ {
        'type': 'function',
        'id': 'provider-secret-id',
        'function': {
            'name': 'read',
            'arguments': '{"location":"/z"}',
            'provider_only': True,
        },
        'session': { 'opaque': 'nope' },
    } ]
    request, = _extract_requests(
        _make_canister( invocation_data, tool_calls ), invokers )
    display = project_invocation_display( request )
    serialized = repr( display )
    assert 'provider-secret-id' not in serialized
    assert 'provider_only' not in serialized
    assert 'opaque' not in serialized
    assert display[ 'correlation_id' ] != 'provider-secret-id'


def test_006_descriptor_correlation_id_preserved_through_pair( ) -> None:
    ''' Durable descriptor correlation_id survives extract and result pair. '''
    import asyncio
    from uuid import uuid4

    invokers = _build_invokers( )
    stable_a = uuid4( ).hex
    stable_b = uuid4( ).hex
    invocation_data = [
        {
            'name': 'read',
            'arguments': { 'location': 'mock://d.txt' },
            'correlation_id': stable_a,
        },
        {
            'name': 'write_file',
            'arguments': {
                'location': 'mock://e.txt', 'content': 'y',
            },
            'correlation_id': stable_b,
        },
    ]
    tool_calls = [
        _tool_call( 'call_d', 'read', '{"location":"mock://d.txt"}' ),
        _tool_call(
            'call_e', 'write_file',
            '{"location":"mock://e.txt","content":"y"}' ),
    ]
    requests = _extract_requests(
        _make_canister( invocation_data, tool_calls ), invokers )
    assert requests[ 0 ].correlation_id == stable_a
    assert requests[ 1 ].correlation_id == stable_b
    assert requests[ 0 ].supplement.payload[ 'id' ] == 'call_d'
    assert requests[ 0 ].correlation_id != 'call_d'

    async def _run( ):
        return await _prov.asyncf.gather_async(
            *( _execute_invocation( request ) for request in requests ) )

    results = asyncio.get_event_loop( ).run_until_complete( _run( ) )
    by_id = { result.correlation_id: result for result in results }
    assert set( by_id ) == { stable_a, stable_b }
    assert by_id[ stable_a ].content[ 'correlation_id' ] == stable_a
    assert by_id[ stable_b ].content[ 'correlation_id' ] == stable_b
    for request in requests:
        display = project_invocation_display( request )
        assert display[ 'correlation_id' ] in { stable_a, stable_b }
        assert 'call_d' not in repr( display )
        assert 'call_e' not in repr( display )
