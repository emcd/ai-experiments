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
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Smoke tests for invocation data contract surfaces. '''


from typing import Any

from sources.aiwb.providers import core as _core
from sources.aiwb.providers import exceptions as _exceptions


class _StubInvoker:
    ''' Minimal callable stub that satisfies the Invoker duck-type. '''

    def __init__( self, name: str ):
        self.name = name
        self.calls: list[ dict[ str, Any ] ] = [ ]

    async def __call__(
        self,
        auxdata: Any,
        arguments: dict[ str, Any ],
        *,
        supplements: Any = None,
        correlation_id: str | None = None,
    ) -> dict[ str, Any ]:
        self.calls.append( {
            'arguments': arguments,
            'correlation_id': correlation_id,
        } )
        return { 'result': 'ok' }


def _make_context( invokers: dict[ str, _StubInvoker ] ):
    from sources.aiwb.providers import __
    return __.accret.Namespace(
        auxdata = None,
        invokers = invokers,
        supplements = __.accret.Dictionary( ),
    )


def test_001_supplement_round_trips_envelope( ) -> None:
    ''' Supplement preserves envelope as opaque MappingProxyType payload. '''
    import types as _types
    envelope = {
        'type': 'function',
        'id': 'call_abc123',
        'function': { 'name': 'greet', 'arguments': '{"who":"world"}' },
    }
    supplement = _core.InvocationSupplement.from_mapping( envelope )
    assert isinstance( supplement.payload, _types.MappingProxyType )
    assert supplement.payload[ 'id' ] == 'call_abc123'
    assert supplement.payload[ 'function' ][ 'name' ] == 'greet'
    # Mutating the original envelope must not affect the supplement.
    envelope[ 'id' ] = 'changed'
    assert supplement.payload[ 'id' ] == 'call_abc123'


def test_002_supplement_default_is_empty( ) -> None:
    ''' Default supplement carries an empty opaque payload. '''
    supplement = _core.InvocationSupplement( )
    assert len( supplement.payload ) == 0


def test_003_request_mints_harness_correlation_id( ) -> None:
    ''' InvocationRequest.from_descriptor mints a UUID4 hex correlation id. '''
    import re
    invokers = { 'greet': _StubInvoker( 'greet' ) }
    context = _make_context( invokers )
    request = _core.InvocationRequest.from_descriptor(
        descriptor = { 'name': 'greet', 'arguments': { 'who': 'world' } },
        context = context )
    assert re.match( r'^[0-9a-f]{32}$', request.correlation_id ), (
        f"Expected 32-char hex, got {request.correlation_id!r}" )


def test_004_request_default_processor_is_application( ) -> None:
    ''' Default processor for descriptor without explicit processor field. '''
    invokers = { 'greet': _StubInvoker( 'greet' ) }
    context = _make_context( invokers )
    request = _core.InvocationRequest.from_descriptor(
        descriptor = { 'name': 'greet', 'arguments': { } },
        context = context )
    assert (
        request.processor == _core.InvocationProcessor.Application )


def test_005_request_explicit_processor_round_trips( ) -> None:
    ''' Descriptor with provider processor is honored. '''
    invokers = { 'code_interpreter': _StubInvoker( 'code_interpreter' ) }
    context = _make_context( invokers )
    request = _core.InvocationRequest.from_descriptor(
        descriptor = {
            'name': 'code_interpreter',
            'arguments': { 'code': 'print(1)' },
            'processor': 'provider',
        },
        context = context )
    assert request.processor == _core.InvocationProcessor.Provider


def test_006_request_invalid_processor_raises( ) -> None:
    ''' Descriptor with invalid processor value raises fail-closed. '''
    invokers = { 'greet': _StubInvoker( 'greet' ) }
    context = _make_context( invokers )
    try:
        _core.InvocationRequest.from_descriptor(
            descriptor = {
                'name': 'greet',
                'arguments': { },
                'processor': 'bogus',
            },
            context = context )
    except _exceptions.InvocationProcessorInvalidity:
        return
    raise AssertionError( 'Expected InvocationProcessorInvalidity.' )


def test_007_request_missing_name_raises( ) -> None:
    ''' Descriptor without name field raises fail-closed. '''
    context = _make_context( { } )
    try:
        _core.InvocationRequest.from_descriptor(
            descriptor = { 'arguments': { } },
            context = context )
    except _exceptions.InvocationFieldAbsence as exc:
        assert exc.args[ 0 ].endswith( "'name'." )
        return
    raise AssertionError( 'Expected InvocationFieldAbsence.' )


def test_008_request_inaccessible_invoker_raises( ) -> None:
    ''' Descriptor referencing unknown invoker raises fail-closed. '''
    context = _make_context( { 'greet': _StubInvoker( 'greet' ) } )
    try:
        _core.InvocationRequest.from_descriptor(
            descriptor = { 'name': 'unknown_tool', 'arguments': { } },
            context = context )
    except _exceptions.InvocableInaccessibility:
        return
    raise AssertionError( 'Expected InvocableInaccessibility.' )


def test_009_request_correlation_ids_are_unique( ) -> None:
    ''' Two requests from the same descriptor get distinct correlation ids. '''
    invokers = { 'greet': _StubInvoker( 'greet' ) }
    context = _make_context( invokers )
    request_a = _core.InvocationRequest.from_descriptor(
        descriptor = { 'name': 'greet', 'arguments': { } },
        context = context )
    request_b = _core.InvocationRequest.from_descriptor(
        descriptor = { 'name': 'greet', 'arguments': { } },
        context = context )
    assert request_a.correlation_id != request_b.correlation_id