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


''' Inventory fixtures for legacy invocation persistence shapes.

    Documents current behavior of
    ``gui.persistence._standardize_invocation_requests_v0`` for
    ``todos/providers/8`` policy work. Does **not** change production
    migration policy; locks observed shapes so a human decision can
    choose support / one-shot migrate / drop with reproducible facts.
'''


from __future__ import annotations

from json import dumps, loads

from sources.aiwb.gui.persistence import _standardize_invocation_requests_v0


def _state( payload: object ) -> dict[ str, str ]:
    return { 'content': dumps( payload ) }


def test_001_post_r2_descriptor_list_passes_through( ) -> None:
    ''' Post-R2 list of name+arguments descriptors is unchanged. '''
    payload = [ {
        'name': 'greet',
        'arguments': { 'who': 'world' },
        'correlation_id': 'a' * 32,
        'processor': 'application',
    } ]
    content, extra = _standardize_invocation_requests_v0( _state( payload ) )
    assert loads( content ) == payload
    assert extra == { }


def test_002_tool_calls_with_dict_arguments_normalizes( ) -> None:
    ''' Pre-R2 tool_calls with mapping arguments become descriptor list. '''
    payload = {
        'tool_calls': [ {
            'id': 'call_a',
            'type': 'function',
            'function': {
                'name': 'greet',
                'arguments': { 'who': 'a' },
            },
        } ],
    }
    content, extra = _standardize_invocation_requests_v0( _state( payload ) )
    assert loads( content ) == [
        { 'name': 'greet', 'arguments': { 'who': 'a' } },
    ]
    # Helper rewrites envelope arguments to OpenAI wire JSON strings.
    assert extra[ 'tool_calls' ][ 0 ][ 'function' ][ 'arguments' ] == (
        '{"who": "a"}' )


def test_003_tool_calls_with_json_string_arguments_raises( ) -> None:
    ''' OpenAI-wire JSON-string arguments are not handled today.

        Current implementation calls ``.copy()`` on arguments and
        AttributeError on ``str``. Any support/migrate policy must
        accept string-or-mapping arguments before re-enabling this
        helper on a live restore path.
    '''
    payload = {
        'tool_calls': [ {
            'id': 'call_a',
            'type': 'function',
            'function': {
                'name': 'greet',
                'arguments': '{"who":"a"}',
            },
        } ],
    }
    raised = False
    try:
        _standardize_invocation_requests_v0( _state( payload ) )
    except AttributeError as exc:
        raised = True
        assert 'copy' in str( exc )
    assert raised, 'expected AttributeError for JSON-string arguments'


def test_004_single_name_arguments_dict_normalizes( ) -> None:
    ''' Single top-level name+arguments mapping (function_call-era). '''
    payload = { 'name': 'greet', 'arguments': { 'who': 'b' } }
    content, extra = _standardize_invocation_requests_v0( _state( payload ) )
    assert loads( content ) == [
        { 'name': 'greet', 'arguments': { 'who': 'b' } },
    ]
    assert extra[ 'arguments' ] == '{"who": "b"}'


def test_005_single_name_arguments_json_string_raises( ) -> None:
    ''' Single-record JSON-string arguments also fail on .copy(). '''
    payload = { 'name': 'greet', 'arguments': '{"who":"b"}' }
    raised = False
    try:
        _standardize_invocation_requests_v0( _state( payload ) )
    except AttributeError:
        raised = True
    assert raised


def test_006_function_call_key_is_not_upgraded( ) -> None:
    ''' Literal function_call envelope key is not recognized.

        Returns original content unchanged and empty extra_context.
        Replay cannot be reconstructed from this branch today.
    '''
    payload = {
        'function_call': {
            'name': 'greet',
            'arguments': '{"who":"c"}',
        },
    }
    raw = dumps( payload )
    content, extra = _standardize_invocation_requests_v0(
        { 'content': raw } )
    assert content == raw
    assert extra == { }
