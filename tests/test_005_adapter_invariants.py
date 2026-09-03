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


''' Offline invariant coverage for OpenAI/Anthropic invocation adapters. '''


from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any
from uuid import UUID

from sources.aiwb.messages.core import Role as MessageRole
from sources.aiwb.providers import __
from sources.aiwb.providers import core as _core
from sources.aiwb.providers.clients.anthropic import conversers as _anthropic
from sources.aiwb.providers.clients.openai import conversers as _openai


def _assert_canonical_uuid4_hex( value: object ) -> str:
    ''' Assert value is canonical lowercase UUID4 .hex; return it. '''
    assert isinstance( value, str ), f'expected str, got {type( value )!r}'
    try: parsed = UUID( hex = value )
    except ( TypeError, ValueError ) as exc:
        raise AssertionError(
            f'not a UUID hex string: {value!r}' ) from exc
    assert 4 == parsed.version, (
        f'expected UUID version 4, got {parsed.version}' )
    assert parsed.hex == value, (
        f'expected canonical lowercase .hex, got {value!r}' )
    return value


class _StubProvider:
    def __init__( self, name: str ):
        self.name = name


class _StubAttributes:
    supports_invocations = True


class _StubModel:
    def __init__( self, provider_name: str, model_name: str ):
        self.provider = _StubProvider( provider_name )
        self.name = model_name
        self.attributes = _StubAttributes( )


class _StubInvoker:
    def __init__( self, name: str ):
        self.name = name
        self.processor = _core.InvocationProcessor.Application.value

    async def __call__(
        self, *posargs: Any, **nomargs: Any
    ) -> dict[ str, Any ]:
        return { 'ok': True, 'name': self.name }


def _make_openai_request(
    *,
    correlation_id: str,
    provider_call_id: str,
    name: str = 'greet',
) -> _core.InvocationRequest:
    async def _invoke( ) -> dict[ str, Any ]:
        return { 'result': 'ok' }

    return _core.InvocationRequest(
        name = name,
        arguments = { },
        invocation = _invoke,
        correlation_id = correlation_id,
        supplement = _core.InvocationSupplement.from_mapping( {
            'id': provider_call_id,
            'type': 'function',
            'function': { 'name': name, 'arguments': '{}' },
        } ),
    )


def _make_anthropic_request(
    *,
    correlation_id: str,
    provider_call_id: str,
    name: str = 'greet',
) -> _core.InvocationRequest:
    async def _invoke( ) -> dict[ str, Any ]:
        return { 'result': 'ok' }

    return _core.InvocationRequest(
        name = name,
        arguments = { },
        invocation = _invoke,
        correlation_id = correlation_id,
        supplement = _core.InvocationSupplement.from_mapping( {
            'id': provider_call_id,
            'name': name,
            'input': { },
        } ),
    )


def test_001_openai_execute_one_result_with_request_correlation( ) -> None:
    ''' OpenAI execute_invocation: one result, request correlation_id only. '''
    import asyncio

    cid = _core.produce_invocation_correlation_id( )
    provider_id = 'call_provider_only'
    request = _make_openai_request(
        correlation_id = cid, provider_call_id = provider_id )
    model = _StubModel( 'openai', 'gpt-test' )
    canister = asyncio.get_event_loop( ).run_until_complete(
        _openai.Conversers( ).execute_invocation( model, request ) )
    assert MessageRole.Result is canister.role
    assert canister.attributes.correlation_id == cid
    _assert_canonical_uuid4_hex( canister.attributes.correlation_id )
    assert canister.attributes.correlation_id != provider_id
    supplement = canister.attributes.model_context[ 'supplement' ]
    assert supplement[ 'tool_call_id' ] == provider_id
    assert supplement[ 'role' ] == 'tool'
    assert 'correlation_id' not in supplement
    assert len( canister ) == 1


def test_002_anthropic_execute_one_result_with_request_correlation( ) -> None:
    ''' Anthropic execute_invocation: one result, request correlation_id. '''
    import asyncio

    cid = _core.produce_invocation_correlation_id( )
    provider_id = 'toolu_provider_only'
    request = _make_anthropic_request(
        correlation_id = cid, provider_call_id = provider_id )
    model = _StubModel( 'anthropic', 'claude-test' )
    canister = asyncio.get_event_loop( ).run_until_complete(
        _anthropic.Conversers( ).execute_invocation( model, request ) )
    assert MessageRole.Result is canister.role
    assert canister.attributes.correlation_id == cid
    _assert_canonical_uuid4_hex( canister.attributes.correlation_id )
    assert canister.attributes.correlation_id != provider_id
    supplement = canister.attributes.model_context[ 'supplement' ]
    assert supplement[ 'tool_use_id' ] == provider_id
    assert supplement[ 'type' ] == 'tool_result'
    assert 'correlation_id' not in supplement
    assert len( canister ) == 1


def test_003_openai_requests_from_canister_detach_and_pair( ) -> None:
    ''' OpenAI extract attaches detached envelopes; keeps harness IDs. '''
    cid_a = _core.produce_invocation_correlation_id( )
    cid_b = _core.produce_invocation_correlation_id( )
    tool_calls = [
        {
            'id': 'call_a',
            'type': 'function',
            'function': {
                'name': 'greet',
                'arguments': '{"who":"a"}',
                'nested': { 'k': 'v' },
            },
        },
        {
            'id': 'call_b',
            'type': 'function',
            'function': {
                'name': 'greet',
                'arguments': '{"who":"b"}',
                'nested': { 'k': 'v' },
            },
        },
    ]
    attributes = SimpleNamespace(
        invocation_data = [
            {
                'name': 'greet',
                'arguments': { 'who': 'a' },
                'correlation_id': cid_a,
                'processor': 'application',
            },
            {
                'name': 'greet',
                'arguments': { 'who': 'b' },
                'correlation_id': cid_b,
                'processor': 'application',
            },
        ],
        model_context = {
            'provider': 'openai',
            'model': 'gpt-test',
            'supplement': { 'tool_calls': tool_calls },
        },
    )
    canister = MessageRole.Invocation.produce_canister(
        attributes = attributes )
    invocables = __.accret.Namespace(
        invokers = { 'greet': _StubInvoker( 'greet' ) } )
    requests = _openai.Conversers( ).requests_from_canister(
        _StubModel( 'openai', 'gpt-test' ),
        None,
        supplements = __.accret.Dictionary( ),
        canister = canister,
        invocables = invocables,
    )
    assert len( requests ) == 2
    assert requests[ 0 ].correlation_id == cid_a
    assert requests[ 1 ].correlation_id == cid_b
    assert requests[ 0 ].supplement.payload[ 'id' ] == 'call_a'
    assert requests[ 1 ].supplement.payload[ 'id' ] == 'call_b'
    assert requests[ 0 ].correlation_id != 'call_a'
    assert requests[ 1 ].correlation_id != 'call_b'
    # Deep-detach: mutate source envelope nested data after extract.
    tool_calls[ 0 ][ 'id' ] = 'mutated'
    tool_calls[ 0 ][ 'function' ][ 'nested' ][ 'k' ] = 'tampered'
    assert requests[ 0 ].supplement.payload[ 'id' ] == 'call_a'
    assert (
        requests[ 0 ].supplement.payload[ 'function' ][ 'nested' ][ 'k' ]
        == 'v' )


def test_004_anthropic_requests_from_canister_detach_and_pair( ) -> None:
    ''' Anthropic extract attaches detached envelopes; keeps harness IDs. '''
    cid_a = _core.produce_invocation_correlation_id( )
    cid_b = _core.produce_invocation_correlation_id( )
    tool_uses = [
        {
            'id': 'toolu_a',
            'name': 'greet',
            'input': { 'who': 'a', 'nested': { 'k': 'v' } },
        },
        {
            'id': 'toolu_b',
            'name': 'greet',
            'input': { 'who': 'b', 'nested': { 'k': 'v' } },
        },
    ]
    attributes = SimpleNamespace(
        invocation_data = [
            {
                'name': 'greet',
                'arguments': { 'who': 'a' },
                'correlation_id': cid_a,
                'processor': 'application',
            },
            {
                'name': 'greet',
                'arguments': { 'who': 'b' },
                'correlation_id': cid_b,
                'processor': 'application',
            },
        ],
        model_context = {
            'provider': 'anthropic',
            'model': 'claude-test',
            'supplement': { 'tool_use': tool_uses },
        },
    )
    canister = MessageRole.Invocation.produce_canister(
        attributes = attributes )
    invocables = __.accret.Namespace(
        invokers = { 'greet': _StubInvoker( 'greet' ) } )
    requests = _anthropic.Conversers( ).requests_from_canister(
        _StubModel( 'anthropic', 'claude-test' ),
        None,
        supplements = __.accret.Dictionary( ),
        canister = canister,
        invocables = invocables,
    )
    assert len( requests ) == 2
    assert requests[ 0 ].correlation_id == cid_a
    assert requests[ 1 ].correlation_id == cid_b
    assert requests[ 0 ].supplement.payload[ 'id' ] == 'toolu_a'
    assert requests[ 1 ].supplement.payload[ 'id' ] == 'toolu_b'
    assert requests[ 0 ].correlation_id != 'toolu_a'
    tool_uses[ 0 ][ 'id' ] = 'mutated'
    tool_uses[ 0 ][ 'input' ][ 'nested' ][ 'k' ] = 'tampered'
    assert requests[ 0 ].supplement.payload[ 'id' ] == 'toolu_a'
    assert (
        requests[ 0 ].supplement.payload[ 'input' ][ 'nested' ][ 'k' ] == 'v' )


def test_005_openai_result_nativize_keeps_canister_supplement( ) -> None:
    ''' OpenAI result replay copies before adding wire-only role. '''
    model = _StubModel( 'openai', 'gpt-test' )
    supplement = { 'name': 'greet', 'tool_call_id': 'call_x' }
    attributes = SimpleNamespace(
        model_context = {
            'provider': 'openai',
            'model': 'gpt-test',
            'supplement': dict( supplement ),
        } )
    canister = (
        MessageRole.Result.produce_canister( attributes = attributes )
        .add_content( '{"ok":true}', mimetype = 'application/json' ) )
    before = copy.deepcopy( canister.attributes.model_context )
    wire = _openai._nativize_result_message( model, canister )
    assert wire[ 'role' ] == 'tool'
    assert wire[ 'tool_call_id' ] == 'call_x'
    assert canister.attributes.model_context == before
    assert 'role' not in canister.attributes.model_context[ 'supplement' ]


def test_006_anthropic_result_nativize_keeps_canister_supplement( ) -> None:
    ''' Anthropic result replay spreads supplement without mutation. '''
    model = _StubModel( 'anthropic', 'claude-test' )
    supplement = { 'tool_use_id': 'toolu_x', 'type': 'tool_result' }
    attributes = SimpleNamespace(
        model_context = {
            'provider': 'anthropic',
            'model': 'claude-test',
            'supplement': dict( supplement ),
        } )
    canister = (
        MessageRole.Result.produce_canister( attributes = attributes )
        .add_content( '{"ok":true}', mimetype = 'application/json' ) )
    before = copy.deepcopy( canister.attributes.model_context )
    wire = _anthropic._nativize_result_message(
        model, canister, { 'invokers': { } } )
    assert wire[ 'role' ] == 'user'
    assert wire[ 'content' ][ 0 ][ 'tool_use_id' ] == 'toolu_x'
    assert canister.attributes.model_context == before


def test_007_openai_invocation_nativize_provider_ids_only( ) -> None:
    ''' OpenAI invocation replay wires provider IDs, not harness IDs. '''
    model = _StubModel( 'openai', 'gpt-test' )
    harness_id = _core.produce_invocation_correlation_id( )
    tool_calls = [ {
        'id': 'call_wire',
        'type': 'function',
        'function': { 'name': 'greet', 'arguments': '{}' },
    } ]
    attributes = SimpleNamespace(
        invocation_data = [ {
            'name': 'greet',
            'arguments': { },
            'correlation_id': harness_id,
            'processor': 'application',
        } ],
        model_context = {
            'provider': 'openai',
            'model': 'gpt-test',
            'supplement': { 'tool_calls': tool_calls },
        },
    )
    canister = MessageRole.Invocation.produce_canister(
        attributes = attributes )
    wire = _openai._nativize_invocation_message( model, canister )
    assert wire[ 'role' ] == 'assistant'
    assert wire[ 'tool_calls' ][ 0 ][ 'id' ] == 'call_wire'
    assert harness_id not in str( wire )
    # Application pairing field stays on canister only.
    assert attributes.invocation_data[ 0 ][ 'correlation_id' ] == harness_id


def test_008_openai_requests_from_canister_refuses_provider_collision(
) -> None:
    ''' OpenAI extract refuses Provider descriptor name collision. '''
    from sources.aiwb.providers import exceptions as _exceptions

    class _TrackingInvoker( _StubInvoker ):
        def __init__( self, name: str ):
            super( ).__init__( name )
            self.calls = 0

        async def __call__( self, *posargs: Any, **nomargs: Any ):
            self.calls += 1
            return await super( ).__call__( *posargs, **nomargs )

    invoker = _TrackingInvoker( 'read' )
    attributes = SimpleNamespace(
        invocation_data = [ {
            'name': 'read',
            'arguments': { 'location': 'mock://x' },
            'processor': 'provider',
        } ],
        model_context = {
            'provider': 'openai',
            'model': 'gpt-test',
            'supplement': { 'tool_calls': [ {
                'id': 'call_provider_native',
                'type': 'function',
                'function': {
                    'name': 'read',
                    'arguments': '{"location":"mock://x"}',
                },
            } ] },
        },
    )
    canister = MessageRole.Invocation.produce_canister(
        attributes = attributes )
    try:
        _openai.Conversers( ).requests_from_canister(
            _StubModel( 'openai', 'gpt-test' ),
            None,
            supplements = __.accret.Dictionary( ),
            canister = canister,
            invocables = __.accret.Namespace(
                invokers = { 'read': invoker } ),
        )
    except _exceptions.ProviderInvocationLocalExecution as exc:
        assert 'read' in str( exc )
        assert 0 == invoker.calls
        return
    raise AssertionError( 'Expected ProviderInvocationLocalExecution.' )


def test_009_anthropic_requests_from_canister_refuses_provider_collision(
) -> None:
    ''' Anthropic extract refuses Provider descriptor name collision. '''
    from sources.aiwb.providers import exceptions as _exceptions

    class _TrackingInvoker( _StubInvoker ):
        def __init__( self, name: str ):
            super( ).__init__( name )
            self.calls = 0

        async def __call__( self, *posargs: Any, **nomargs: Any ):
            self.calls += 1
            return await super( ).__call__( *posargs, **nomargs )

    invoker = _TrackingInvoker( 'read' )
    attributes = SimpleNamespace(
        invocation_data = [ {
            'name': 'read',
            'arguments': { 'location': 'mock://x' },
            'processor': 'provider',
        } ],
        model_context = {
            'provider': 'anthropic',
            'model': 'claude-test',
            'supplement': { 'tool_use': [ {
                'id': 'toolu_provider_native',
                'name': 'read',
                'input': { 'location': 'mock://x' },
            } ] },
        },
    )
    canister = MessageRole.Invocation.produce_canister(
        attributes = attributes )
    try:
        _anthropic.Conversers( ).requests_from_canister(
            _StubModel( 'anthropic', 'claude-test' ),
            None,
            supplements = __.accret.Dictionary( ),
            canister = canister,
            invocables = __.accret.Namespace(
                invokers = { 'read': invoker } ),
        )
    except _exceptions.ProviderInvocationLocalExecution as exc:
        assert 'read' in str( exc )
        assert 0 == invoker.calls
        return
    raise AssertionError( 'Expected ProviderInvocationLocalExecution.' )


def test_010_gui_extract_refuses_provider_collision_before_execute(
) -> None:
    ''' GUI extract_invocation_requests fails closed before local execute. '''
    import asyncio
    from unittest.mock import AsyncMock, patch

    from sources.aiwb.gui import invocables as _gui_invocables
    from sources.aiwb.providers import exceptions as _exceptions

    class _TrackingInvoker( _StubInvoker ):
        def __init__( self, name: str ):
            super( ).__init__( name )
            self.calls = 0

        async def __call__( self, *posargs: Any, **nomargs: Any ):
            self.calls += 1
            return await super( ).__call__( *posargs, **nomargs )

    invoker = _TrackingInvoker( 'read' )
    attributes = SimpleNamespace(
        invocation_data = [ {
            'name': 'read',
            'arguments': { 'location': 'mock://gui' },
            'processor': 'provider',
        } ],
        model_context = {
            'provider': 'openai',
            'model': 'gpt-test',
            'supplement': { 'tool_calls': [ {
                'id': 'call_gui_collision',
                'type': 'function',
                'function': {
                    'name': 'read',
                    'arguments': '{"location":"mock://gui"}',
                },
            } ] },
        },
    )
    canister = MessageRole.Invocation.produce_canister(
        attributes = attributes )
    history_entry = SimpleNamespace(
        gui__ = SimpleNamespace( canister__ = canister ) )
    components = SimpleNamespace(
        column_conversation_history = [ history_entry ],
        auxdata__ = SimpleNamespace(
            invocables = __.accret.Namespace(
                invokers = { 'read': invoker } ),
        ),
    )
    model = _StubModel( 'openai', 'gpt-test' )
    model.client = SimpleNamespace( conversers = _openai.Conversers( ) )

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
            return await _gui_invocables.extract_invocation_requests(
                components )

    try:
        asyncio.get_event_loop( ).run_until_complete( _run( ) )
    except _exceptions.ProviderInvocationLocalExecution as exc:
        assert 'read' in str( exc )
        assert 0 == invoker.calls
        return
    raise AssertionError( 'Expected ProviderInvocationLocalExecution.' )
