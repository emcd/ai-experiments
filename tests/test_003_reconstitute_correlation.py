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


''' Durable correlation_id minting in provider reconstitute paths. '''


from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

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


def test_001_openai_parallel_descriptors_mint_distinct_harness_ids( ) -> None:
    ''' OpenAI reconstitute mints distinct harness correlation IDs. '''
    record = {
        'tool_calls': [
            {
                'id': 'call_provider_alpha',
                'type': 'function',
                'function': {
                    'name': 'list_folder',
                    'arguments': '{"location":"."}',
                },
            },
            {
                'id': 'call_provider_beta',
                'type': 'function',
                'function': {
                    'name': 'read',
                    'arguments': '{"location":"README.md"}',
                },
            },
        ],
    }
    descriptors = _openai._reconstitute_invocations( record )
    assert len( descriptors ) == 2
    ids = [
        _assert_canonical_uuid4_hex( d[ 'correlation_id' ] )
        for d in descriptors ]
    assert ids[ 0 ] != ids[ 1 ]
    assert descriptors[ 0 ][ 'name' ] == 'list_folder'
    assert descriptors[ 1 ][ 'name' ] == 'read'
    assert descriptors[ 0 ][ 'arguments' ] == { 'location': '.' }
    assert descriptors[ 1 ][ 'arguments' ] == { 'location': 'README.md' }
    for descriptor in descriptors:
        assert (
            descriptor[ 'processor' ]
            == _core.InvocationProcessor.Application.value )


def test_002_openai_provider_ids_never_become_correlation_ids( ) -> None:
    ''' OpenAI provider tool_call ids stay out of correlation_id. '''
    provider_id = 'call_not_a_harness_uuid'
    record = {
        'tool_calls': [ {
            'id': provider_id,
            'type': 'function',
            'function': {
                'name': 'greet',
                'arguments': '{"who":"world"}',
            },
        } ],
    }
    descriptors = _openai._reconstitute_invocations( record )
    assert len( descriptors ) == 1
    cid = _assert_canonical_uuid4_hex( descriptors[ 0 ][ 'correlation_id' ] )
    assert cid != provider_id
    assert 'call_' not in cid
    # Envelope provider id remains only on the source record, not descriptor.
    assert 'id' not in descriptors[ 0 ]
    assert record[ 'tool_calls' ][ 0 ][ 'id' ] == provider_id


def test_003_anthropic_parallel_mints_distinct_harness_ids( ) -> None:
    ''' Anthropic reconstitute mints distinct harness correlation IDs. '''
    records = {
        0: {
            'tool_use': SimpleNamespace(
                id = 'toolu_provider_alpha',
                name = 'list_folder',
                input = { 'location': '.' },
            ),
        },
        1: {
            'tool_use': SimpleNamespace(
                id = 'toolu_provider_beta',
                name = 'read',
                input = { 'location': 'README.md' },
            ),
        },
    }
    descriptors = _anthropic._reconstitute_invocations( records )
    assert len( descriptors ) == 2
    ids = [
        _assert_canonical_uuid4_hex( d[ 'correlation_id' ] )
        for d in descriptors ]
    assert ids[ 0 ] != ids[ 1 ]
    assert descriptors[ 0 ][ 'name' ] == 'list_folder'
    assert descriptors[ 1 ][ 'name' ] == 'read'
    for descriptor in descriptors:
        assert (
            descriptor[ 'processor' ]
            == _core.InvocationProcessor.Application.value )


def test_004_anthropic_provider_ids_never_become_correlation_ids( ) -> None:
    ''' Anthropic provider tool_use ids stay out of correlation_id. '''
    provider_id = 'toolu_not_a_harness_uuid'
    records = {
        0: {
            'tool_use': SimpleNamespace(
                id = provider_id,
                name = 'greet',
                input = { 'who': 'world' },
            ),
        },
    }
    descriptors = _anthropic._reconstitute_invocations( records )
    assert len( descriptors ) == 1
    cid = _assert_canonical_uuid4_hex( descriptors[ 0 ][ 'correlation_id' ] )
    assert cid != provider_id
    assert 'toolu_' not in cid
    assert 'id' not in descriptors[ 0 ]


def test_005_openai_descriptor_survives_from_descriptor_reuse( ) -> None:
    ''' Reconstitute correlation_id is reused by from_descriptor (step 1). '''
    from sources.aiwb.providers import __

    class _StubInvoker:
        def __init__( self, name: str ):
            self.name = name

        async def __call__( self, *posargs, **nomargs ):
            return { 'ok': True }

    record = {
        'tool_calls': [ {
            'id': 'call_provider_only',
            'type': 'function',
            'function': {
                'name': 'greet',
                'arguments': '{"who":"world"}',
            },
        } ],
    }
    descriptors = _openai._reconstitute_invocations( record )
    minted = _assert_canonical_uuid4_hex(
        descriptors[ 0 ][ 'correlation_id' ] )
    context = __.accret.Namespace(
        auxdata = None,
        invokers = { 'greet': _StubInvoker( 'greet' ) },
        supplements = __.accret.Dictionary( ),
    )
    request = _core.InvocationRequest.from_descriptor(
        descriptor = descriptors[ 0 ],
        context = context )
    assert request.correlation_id == minted
    assert request.processor is _core.InvocationProcessor.Application
    assert request.name == 'greet'
    assert request.arguments == { 'who': 'world' }
