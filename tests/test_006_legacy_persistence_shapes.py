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


''' Legacy invocation persistence upgrade fixtures (todos/providers/8). '''


from __future__ import annotations

from json import dumps, loads

from sources.aiwb.gui.persistence import _standardize_invocation_requests_v0
from sources.aiwb.messages import core as _messages


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
    ''' tool_calls with mapping arguments become descriptor list. '''
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
    assert extra[ 'tool_calls' ][ 0 ][ 'id' ] == 'call_a'
    assert 'correlation_id' not in loads( content )[ 0 ]


def test_003_tool_calls_with_json_string_arguments_normalizes( ) -> None:
    ''' OpenAI-wire JSON-string arguments coerce to mappings. '''
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
    content, extra = _standardize_invocation_requests_v0( _state( payload ) )
    assert loads( content ) == [
        { 'name': 'greet', 'arguments': { 'who': 'a' } },
    ]
    assert extra[ 'tool_calls' ][ 0 ][ 'id' ] == 'call_a'


def test_004_single_name_arguments_dict_normalizes( ) -> None:
    ''' Single top-level name+arguments mapping normalizes. '''
    payload = { 'name': 'greet', 'arguments': { 'who': 'b' } }
    content, extra = _standardize_invocation_requests_v0( _state( payload ) )
    assert loads( content ) == [
        { 'name': 'greet', 'arguments': { 'who': 'b' } },
    ]
    assert extra[ 'name' ] == 'greet'


def test_005_single_name_arguments_json_string_normalizes( ) -> None:
    ''' Single-record JSON-string arguments coerce to mappings. '''
    payload = { 'name': 'greet', 'arguments': '{"who":"b"}' }
    content, extra = _standardize_invocation_requests_v0( _state( payload ) )
    assert extra[ 'name' ] == 'greet'
    assert loads( content ) == [
        { 'name': 'greet', 'arguments': { 'who': 'b' } },
    ]


def test_006_function_call_key_is_elided( ) -> None:
    ''' Literal function_call envelope elides to empty descriptors. '''
    payload = {
        'function_call': {
            'name': 'greet',
            'arguments': '{"who":"c"}',
        },
    }
    content, extra = _standardize_invocation_requests_v0( _state( payload ) )
    assert loads( content ) == [ ]
    assert 'function_call' in extra


def test_007_upgrade_never_copies_provider_id_as_correlation( ) -> None:
    ''' Provider call ids must not become correlation_id. '''
    raw = {
        'tool_calls': [ {
            'id': 'call_provider',
            'type': 'function',
            'function': {
                'name': 'greet',
                'arguments': '{"x":1}',
            },
        } ],
    }
    descriptors = _messages.upgrade_invocation_data( raw )
    assert len( descriptors ) == 1
    assert 'correlation_id' not in descriptors[ 0 ]
    assert descriptors[ 0 ][ 'name' ] == 'greet'
    assert descriptors[ 0 ][ 'arguments' ] == { 'x': 1 }


def test_008_malformed_json_arguments_elide_single_record( ) -> None:
    ''' Unparseable single-record arguments yield no descriptor. '''
    assert _messages.coerce_invocation_arguments( '{not-json' ) is None
    assert _messages.coerce_invocation_arguments( '[1,2]' ) is None
    assert _messages.coerce_invocation_arguments( 'null' ) is None
    assert _messages.upgrade_invocation_data( {
        'name': 'greet',
        'arguments': '{not-json',
    } ) == [ ]
    content, extra = _standardize_invocation_requests_v0( _state( {
        'name': 'greet',
        'arguments': '{not-json',
    } ) )
    assert loads( content ) == [ ]
    assert extra[ 'name' ] == 'greet'


def test_009_malformed_json_arguments_omit_tool_call_item( ) -> None:
    ''' Bad tool_calls item is omitted; valid siblings retained. '''
    raw = {
        'tool_calls': [
            {
                'id': 'call_bad',
                'type': 'function',
                'function': {
                    'name': 'greet',
                    'arguments': '{not-json',
                },
            },
            {
                'id': 'call_good',
                'type': 'function',
                'function': {
                    'name': 'read',
                    'arguments': '{"location":"x"}',
                },
            },
        ],
    }
    descriptors = _messages.upgrade_invocation_data( raw )
    assert descriptors == [
        { 'name': 'read', 'arguments': { 'location': 'x' } },
    ]


def test_010_malformed_descriptor_list_item_omitted( ) -> None:
    ''' Bad arguments on one list descriptor omit only that item. '''
    raw = [
        { 'name': 'bad', 'arguments': '{nope' },
        { 'name': 'good', 'arguments': { 'ok': True } },
    ]
    assert _messages.upgrade_invocation_data( raw ) == [
        { 'name': 'good', 'arguments': { 'ok': True } },
    ]
