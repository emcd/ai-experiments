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


''' Regression coverage for Context.model and Context.controls accessors. '''


from __future__ import annotations

from types import SimpleNamespace

from sources.aiwb.invocables.core import (
    Context,
    ContextSupplements,
    Invoker,
)


class _Ensemble:
    name = 'test'


async def _noop( context, arguments ):
    return arguments


def _make_invoker( ) -> Invoker:
    return Invoker(
        name = '_noop',
        ensemble = _Ensemble( ),  # type: ignore[arg-type]
        invocable = _noop,
        argschema = {
            'type': 'object',
            'properties': { },
        },
    )


def test_001_context_controls_empty_when_absent( ) -> None:
    ''' Missing controls injects as empty mapping (not error). '''
    context = Context(
        auxdata = None,  # type: ignore[arg-type]
        invoker = _make_invoker( ),
        supplements = ContextSupplements.from_mapping( { } ),
        correlation_id = 'a' * 32,
    )
    assert dict( context.controls ) == { }
    assert context.supplements[ 'controls' ] is context.controls


def test_002_context_controls_and_model_from_mapping( ) -> None:
    ''' Accessors expose injected model and controls. '''
    model = SimpleNamespace( name = 'm' )
    controls = { 'temperature': SimpleNamespace( value = 0.2 ) }
    context = Context(
        auxdata = None,  # type: ignore[arg-type]
        invoker = _make_invoker( ),
        supplements = ContextSupplements.from_mapping( {
            'model': model,
            'controls': controls,
            'invokers': ( ),
        } ),
        correlation_id = 'b' * 32,
    )
    assert context.model is model
    assert context.controls[ 'temperature' ].value == 0.2
    assert context.supplements[ 'model' ] is model
    assert 'invokers' in context.supplements.extras


def test_003_context_model_missing_raises( ) -> None:
    ''' Missing model raises KeyError like supplements['model']. '''
    context = Context(
        auxdata = None,  # type: ignore[arg-type]
        invoker = _make_invoker( ),
        supplements = ContextSupplements.from_mapping( { } ),
        correlation_id = 'c' * 32,
    )
    try:
        _ = context.model
    except KeyError as exc:
        assert 'model' in str( exc )
        return
    raise AssertionError( 'Expected KeyError for missing model.' )


def test_004_mapping_compatibility_preserved( ) -> None:
    ''' Legacy supplements['model'] still works when model present. '''
    model = SimpleNamespace( name = 'legacy' )
    supplements = ContextSupplements.from_mapping( { 'model': model } )
    assert supplements[ 'model' ] is model
    assert supplements.get( 'model' ) is model
    assert supplements.get( 'missing' ) is None
    assert 'model' in supplements
    assert 'controls' in supplements
