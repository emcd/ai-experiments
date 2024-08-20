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


''' Core classes and functions for invocables. '''


from __future__ import annotations

from . import __


#ModelClass: __.a.TypeAlias = type[ __.pydantic.BaseModel ]
#Model = __.a.TypeVar( 'Model', bound = __.pydantic.BaseModel )


@__.a.runtime_checkable
@__.standard_dataclass
class Ensemble( __.a.Protocol ):
    ''' Ensemble of invokers for related tools. '''

    name: str

    @__.abstract_member_function
    async def prepare_invokers(
        self, auxdata: __.Globals
    ) -> __.AbstractDictionary[ str, Invoker ]:
        raise NotImplementedError


@__.standard_dataclass
class Invoker:
    ''' Calls tool registered to it. '''

    name: str
    ensemble: Ensemble
    invocable: __.a.Callable # TODO: Proper signature for async coroutine.
    specification: str

    @classmethod
    def from_invocable(
        selfclass, /,
        ensemble: Ensemble,
        invocable: __.a.Callable, # TODO: Proper signature for async coroutine.
        specification: str,
    ) -> __.a.Self:
        name = invocable.__name__ # TODO? Get name from model.
        return selfclass(
            name = name,
            ensemble = ensemble,
            invocable = invocable,
            specification = specification )

    async def __call__(
        self,
        auxdata: __.Globals,
        arguments: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Any:
        return await self.invocable( auxdata, arguments )


# TODO: Use accretive validator dictionary for preparers registry.
preparers = __.AccretiveDictionary( )


def descriptors_from_configuration(
    auxdata: __.Globals,
    defaults: __.AbstractDictionary[ str, __.a.Any ] = None,
) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
    ''' Validates and returns descriptors from configuration. '''
    scribe = __.acquire_scribe( __package__ )
    defaults_ = dict( defaults or { } )
    descriptors = [ ]
    for descriptor in auxdata.configuration.get( 'invocables', ( ) ):
        if 'name' not in descriptor:
            auxdata.notifications.enqueue_error(
                ValueError( "Descriptor missing name." ),
                "Could not load ensemble of invocables from configuration.",
                details = descriptor,
                scribe = scribe )
            continue
        if not descriptor.get( 'enable', True ): continue
        descriptors.append( descriptor )
        name = descriptor[ 'name' ]
        if name in defaults_: defaults_.pop( name )
    return tuple( list( defaults_.values( ) ) + descriptors )


async def prepare( auxdata ):
    ''' Prepares invokers from defaults and configuration. '''
    ensembles = await prepare_ensembles( auxdata )
    invokers = await prepare_invokers( auxdata, ensembles )
    return survey_functions( ) # TODO: Accretive namespace.


async def prepare_ensembles( auxdata ):
    ''' Prepares ensembles of invokers from defaults and configuration. '''
    scribe = __.acquire_scribe( __package__ )
    descriptors = __.DictionaryProxy( {
        descriptor[ 'name' ]: descriptor
        for descriptor in descriptors_from_configuration(
            auxdata, defaults = _default_ensemble_descriptors ) } )
    preparers_ = __.DictionaryProxy( {
        name: preparers[ name ]( auxdata, descriptor )
        for name, descriptor in descriptors.items( ) } )
    results = await __.gather_async(
        *preparers_.values( ), return_exceptions = True )
    ensembles = __.AccretiveDictionary( )
    for name, result in zip( preparers_.keys( ), results ):
        match result:
            case __.g.Error( error ):
                summary = "Could not prepare invokers ensemble {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( ensemble ):
                ensembles[ name ] = ensemble
    return ensembles


async def prepare_invokers(
    auxdata: __.Globals,
    ensembles: __.AbstractDictionary[ str, Ensemble ],
) -> __.AbstractDictionary[ str, Invoker ]:
    ''' Prepares invokers from ensembles. '''
    scribe = __.acquire_scribe( __package__ )
    results = await __.gather_async(
        *(  ensemble.prepare_invokers( auxdata )
            for ensemble in ensembles.values( ) ),
        return_exceptions = True )
    invokers = { }
    for result in results:
        match result:
            case __.g.Error( error ):
                summary = f"Could not prepare invoker."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( invokers_ ):
                invokers.update( invokers_ )
    return __.DictionaryProxy( invokers )


_default_ensemble_descriptors = __.DictionaryProxy( {
    'io':
        __.DictionaryProxy( { 'name': 'io', 'enable': True } ),
    'probability':
        __.DictionaryProxy( { 'name': 'probability', 'enable': True } ),
} )


# TODO: Produce registrations from ensembles.
_registry = __.AccretiveDictionary( )


def register_function( schema ):
    from json import dumps
    from jsonschema.validators import Draft202012Validator as Validator
    _trim_descriptions( schema )
    Validator.check_schema( schema )
    def register( function ):
        function.__doc__ = dumps( schema, indent = 2 )
        _registry[ schema[ 'name' ] ] = function
        return function
    return register


def survey_functions( ): return __.DictionaryProxy( _registry )


def _trim_descriptions( schema ):
    from inspect import cleandoc
    for entry_name, entry in schema.items( ):
        if isinstance( entry, __.AbstractDictionary ):
            _trim_descriptions( entry )
        if 'description' != entry_name: continue
        if not isinstance( entry, str ): continue
        schema[ 'description' ] = cleandoc( entry )
