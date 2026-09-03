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


''' OpenAI complete-response tool_call Mapping coercion.

    Coverage for ``todos/providers/9``.
'''


from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

from sources.aiwb.providers.clients.openai import conversers as _openai


class _SdkFunction:
    ''' Minimal non-Mapping stand-in for SDK Function. '''

    def __init__( self, name: str, arguments: str ):
        self.name = name
        self.arguments = arguments


class _SdkToolCall:
    ''' Minimal non-Mapping stand-in without model_dump (attr path). '''

    def __init__( self, call_id: str, name: str, arguments: str ):
        self.id = call_id
        self.type = 'function'
        self.function = _SdkFunction( name, arguments )


class _SdkToolCallWithDump:
    ''' SDK stand-in exposing model_dump like Pydantic v2. '''

    def __init__( self, call_id: str, name: str, arguments: str ):
        self.id = call_id
        self.type = 'function'
        self.function = _SdkFunction( name, arguments )

    def model_dump( self ) -> dict[ str, Any ]:
        return {
            'id': self.id,
            'type': self.type,
            'function': {
                'name': self.function.name,
                'arguments': self.function.arguments,
            },
        }


def test_001_sdk_object_without_mapping_protocol_coerces( ) -> None:
    ''' Attribute-only SDK object becomes stream-shaped plain dict. '''
    sdk = _SdkToolCall( 'call_x', 'greet', '{"who":"a"}' )
    assert not isinstance( sdk, Mapping )
    native = _openai._nativize_tool_call_mapping( sdk )
    assert isinstance( native, dict )
    assert native == {
        'id': 'call_x',
        'type': 'function',
        'function': {
            'name': 'greet',
            'arguments': '{"who":"a"}',
        },
    }
    # Subscriptable for reconstitution.
    assert native[ 'function' ][ 'name' ] == 'greet'


def test_002_sdk_object_with_model_dump_coerces( ) -> None:
    ''' Pydantic-style model_dump path yields the same plain dict. '''
    sdk = _SdkToolCallWithDump( 'call_y', 'read', '{"location":"x"}' )
    native = _openai._nativize_tool_call_mapping( sdk )
    assert native[ 'id' ] == 'call_y'
    assert native[ 'function' ][ 'arguments' ] == '{"location":"x"}'


def test_003_plain_mapping_pass_through_shape( ) -> None:
    ''' Stream-built dicts remain Mapping and keep wire arguments string. '''
    stream_shape = {
        'id': 'call_z',
        'type': 'function',
        'function': {
            'name': 'list_folder',
            'arguments': '{"location":"."}',
        },
    }
    native = _openai._nativize_tool_call_mapping( stream_shape )
    assert native == stream_shape
    # Mutating source must not alias if we dict()-copied.
    stream_shape[ 'id' ] = 'mutated'
    assert native[ 'id' ] == 'call_z'


def test_004_complete_response_stores_plain_dict_tool_calls( ) -> None:
    ''' _process_complete_response_v0 stores coerced dicts in supplement. '''
    sdk_calls = [
        _SdkToolCall( 'call_a', 'greet', '{"who":"a"}' ),
        _SdkToolCallWithDump( 'call_b', 'read', '{"location":"b"}' ),
    ]
    message = SimpleNamespace(
        content = None,
        tool_calls = sdk_calls,
    )
    # No ``delta`` attribute: complete-response path uses ``message``.
    choice = SimpleNamespace( index = 0, message = message )
    response = SimpleNamespace( choices = [ choice ] )

    class _Attrs:
        supports_invocations = True
        accepts_supervisor_instructions = True

    class _Prov:
        name = 'openai'

    class _Client:
        name = 'openai'

    class _Model:
        name = 'gpt-test'
        provider = _Prov( )
        client = _Client( )
        attributes = _Attrs( )

    allocated: list = [ ]
    updated: list = [ ]

    def _allocate( canister ):
        allocated.append( canister )
        return canister

    def _update( ref ):
        updated.append( ref )

    reactors = SimpleNamespace(
        allocator = _allocate,
        deallocator = lambda ref: None,
        updater = _update,
    )
    ref = _openai._process_complete_response_v0(
        _Model( ), response, reactors )
    assert ref is allocated[ 0 ]
    supplement = ref.attributes.model_context[ 'supplement' ]
    tool_calls = supplement[ 'tool_calls' ]
    assert len( tool_calls ) == 2
    assert all( isinstance( call, dict ) for call in tool_calls )
    assert all( isinstance( call, Mapping ) for call in tool_calls )
    assert tool_calls[ 0 ][ 'id' ] == 'call_a'
    assert tool_calls[ 0 ][ 'function' ][ 'name' ] == 'greet'
    assert tool_calls[ 1 ][ 'function' ][ 'arguments' ] == '{"location":"b"}'
    # Reconstitution must succeed (Mapping subscripts + JSON args).
    data = ref.attributes.invocation_data
    assert len( data ) == 2
    assert data[ 0 ][ 'name' ] == 'greet'
    assert data[ 0 ][ 'arguments' ] == { 'who': 'a' }
    assert data[ 1 ][ 'name' ] == 'read'
    assert 'correlation_id' in data[ 0 ]
    assert data[ 0 ][ 'correlation_id' ] != 'call_a'


def test_005_model_dump_failure_surfaces( ) -> None:
    ''' Broken model_dump must not be swallowed into a lossy fallback. '''

    class _BrokenDump:
        id = 'call_bad'
        type = 'function'
        function = _SdkFunction( 'greet', '{}' )

        def model_dump( self ):
            raise RuntimeError( 'sdk serialization failed' )

    raised = False
    try:
        _openai._nativize_tool_call_mapping( _BrokenDump( ) )
    except RuntimeError as exc:
        raised = True
        assert 'sdk serialization failed' in str( exc )
    assert raised, 'expected RuntimeError from broken model_dump'


def test_006_stream_collect_path_still_builds_plain_dicts( ) -> None:
    ''' Streaming collector remains plain-dict (unchanged contract). '''
    from sources.aiwb.providers import core as _core
    indices = _core.create_response_indices( )
    indices.canisters[ 0 ] = SimpleNamespace(
        attributes = SimpleNamespace( model_context = { } ) )
    indices.references[ 0 ] = object( )
    delta_fn = SimpleNamespace( name = 'greet', arguments = '{"who":"s"}' )
    delta_call = SimpleNamespace(
        index = 0, id = 'call_s', function = delta_fn )
    delta = SimpleNamespace( tool_calls = [ delta_call ], content = None )

    def _noop( ref ): pass

    reactors = SimpleNamespace( updater = _noop )
    _openai._collect_response_as_invocations_v0(
        None, indices, 0, delta, reactors )
    calls = indices.records[ 0 ][ 'tool_calls' ]
    assert isinstance( calls[ 0 ], dict )
    assert calls[ 0 ][ 'id' ] == 'call_s'
    assert calls[ 0 ][ 'function' ][ 'name' ] == 'greet'
    assert calls[ 0 ][ 'function' ][ 'arguments' ] == '{"who":"s"}'
