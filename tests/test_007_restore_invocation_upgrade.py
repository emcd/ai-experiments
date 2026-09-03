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


''' restore_canister one-shot invocation_data upgrade (todos/providers/8). '''


from __future__ import annotations

import asyncio
from copy import deepcopy
from json import dumps

from sources.aiwb.messages import core as _messages
from sources.aiwb.messages.core import Role


def _restore( state: dict ) -> object:
    return asyncio.get_event_loop( ).run_until_complete(
        _messages.restore_canister( None, state ) )


def test_001_restore_post_r2_descriptors_unchanged( ) -> None:
    ''' Post-R2 descriptors round-trip; caller state not mutated. '''
    cid = 'b' * 32
    descriptors = [ {
        'name': 'greet',
        'arguments': { 'who': 'world' },
        'correlation_id': cid,
        'processor': 'application',
    } ]
    original = {
        'role': Role.Invocation.value,
        'attributes': {
            'invocation_data': deepcopy( descriptors ),
            'model_context': {
                'provider': 'openai',
                'supplement': { 'tool_calls': [ { 'id': 'call_x' } ] },
            },
        },
        'contents': [ ],
    }
    before = deepcopy( original )
    canister = _restore( original )
    assert original == before
    assert canister.attributes.invocation_data == descriptors
    assert (
        canister.attributes.model_context[ 'supplement' ][ 'tool_calls' ][ 0 ]
        [ 'id' ] == 'call_x' )


def test_002_restore_tool_calls_string_args_and_supplement( ) -> None:
    ''' Envelope as invocation_data migrates; fills empty supplement. '''
    envelope = {
        'tool_calls': [ {
            'id': 'call_a',
            'type': 'function',
            'function': {
                'name': 'greet',
                'arguments': '{"who":"a"}',
            },
        } ],
    }
    state = {
        'role': Role.Invocation.value,
        'attributes': {
            'invocation_data': deepcopy( envelope ),
            'model_context': { 'provider': 'openai' },
        },
        'contents': [ ],
    }
    canister = _restore( state )
    data = canister.attributes.invocation_data
    assert data == [ { 'name': 'greet', 'arguments': { 'who': 'a' } } ]
    assert 'correlation_id' not in data[ 0 ]
    assert data[ 0 ].get( 'id' ) is None
    supplement = canister.attributes.model_context[ 'supplement' ]
    assert supplement[ 'tool_calls' ][ 0 ][ 'id' ] == 'call_a'


def test_003_restore_function_call_elides_without_crash( ) -> None:
    ''' Literal function_call elides to empty descriptors. '''
    state = {
        'role': Role.Invocation.value,
        'attributes': {
            'invocation_data': {
                'function_call': {
                    'name': 'greet',
                    'arguments': '{"who":"c"}',
                },
            },
        },
        'contents': [ ],
    }
    canister = _restore( state )
    assert canister.attributes.invocation_data == [ ]


def test_004_apply_upgrade_fills_supplement_from_envelope( ) -> None:
    ''' Envelope-only attributes get supplement for same-provider replay. '''
    envelope = {
        'tool_calls': [ {
            'id': 'call_b',
            'type': 'function',
            'function': {
                'name': 'read',
                'arguments': { 'location': 'x' },
            },
        } ],
    }
    attributes: dict = { 'invocation_data': envelope }
    _messages.apply_invocation_data_upgrade( attributes )
    assert attributes[ 'invocation_data' ] == [
        { 'name': 'read', 'arguments': { 'location': 'x' } },
    ]
    assert attributes[ 'model_context' ][ 'supplement' ][ 'tool_calls' ][ 0 ][
        'id' ] == 'call_b'


def test_005_restore_malformed_json_content_elides( ) -> None:
    ''' Unparseable TEMP content becomes empty invocation_data. '''
    # Simulate TEMP path outcome: loads failure → []
    attributes = { 'invocation_data': 'not-json' }
    # upgrade_invocation_data on non-mapping non-sequence list-elide
    # string is not Sequence of descriptors
    assert _messages.upgrade_invocation_data( 'not-json' ) == [ ]
    # After failed loads, restore sets []
    attributes[ 'invocation_data' ] = [ ]
    _messages.apply_invocation_data_upgrade( attributes )
    assert attributes[ 'invocation_data' ] == [ ]


def test_006_oneshot_save_shape_is_post_r2_descriptors( ) -> None:
    ''' After restore, invocation_data is save-ready descriptors. '''
    state = {
        'role': Role.Invocation.value,
        'attributes': {
            'invocation_data': {
                'name': 'greet',
                'arguments': '{"who":"z"}',
            },
        },
        'contents': [ ],
    }
    canister = _restore( state )
    # Canister.save dumps attributes.__dict__; ensure descriptor list.
    saved_attrs = dict( canister.attributes.__dict__ )
    assert isinstance( saved_attrs[ 'invocation_data' ], list )
    assert saved_attrs[ 'invocation_data' ][ 0 ][ 'arguments' ] == {
        'who': 'z',
    }
    # dumps must succeed for persistence JSON.
    dumps( saved_attrs[ 'invocation_data' ] )
