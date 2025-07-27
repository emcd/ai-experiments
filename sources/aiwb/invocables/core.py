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


from . import __


Arguments: __.a.TypeAlias = __.DictionaryProxy[ str, __.a.Any ]
#Arguments = __.a.TypeVar( 'Arguments', bound = __.pydantic.BaseModel )
ArgumentsModel: __.a.TypeAlias = __.DictionaryProxy[ str, __.a.Any ]
#ArgumentsModel: __.a.TypeAlias = type[ __.pydantic.BaseModel ]



class Deduplicator(
    __.immut.DataclassProtocol, __.a.Protocol,
    decorators = ( __.a.runtime_checkable, ),
):
    ''' Determines if tool invocations can be deduplicated. '''

    invocable_name: str
    arguments: __.AbstractDictionary[ str, __.a.Any ]

    @classmethod
    @__.abstract_member_function
    def provide_invocable_names( selfclass ) -> __.AbstractCollection[ str ]:
        raise NotImplementedError

    @__.abstract_member_function
    def is_duplicate(
        self,
        invocable_name: str,
        arguments: __.AbstractDictionary[ str, __.a.Any ],
    ) -> bool:
        raise NotImplementedError


class Context(
    __.immut.DataclassObject
):
    ''' Context data transfer object. '''

    auxdata: __.Globals
    invoker: 'Invoker'
    supplements: __.accret.Namespace


class Ensemble(
    __.immut.DataclassProtocol, __.a.Protocol,
    decorators = ( __.a.runtime_checkable, ),
):
    ''' Ensemble of invokers for related tools. '''

    name: str

    @__.abstract_member_function
    async def prepare_invokers(
        self, auxdata: __.Globals
    ) -> __.AbstractDictionary[ str, 'Invoker' ]:
        raise NotImplementedError

    def produce_invokers_from_registry(
        self, auxdata: __.Globals, registry
    ) -> __.AbstractDictionary[ str, 'Invoker' ]:
        # TODO: Handle pair-wise iterable or dictionary.
        # TODO: Use standard filter information.
        invokers = (
            Invoker.from_invocable(
                ensemble = self, invocable = invocable, argschema = argschema )
            for invocable, argschema in registry )
        return __.DictionaryProxy( {
            invoker.name: invoker for invoker in invokers } )


class Invoker(
    __.immut.DataclassObject
):
    ''' Calls tool registered to it. '''

    name: str
    ensemble: Ensemble
    invocable: 'Invocable'
    argschema: ArgumentsModel # TODO: Transform/validate on init.
    deduplicator_class: __.typx.Optional[ type[ Deduplicator ] ] = None

    @classmethod
    def from_invocable(
        selfclass,
        ensemble: Ensemble,
        invocable: 'Invocable',
        argschema: ArgumentsModel,
        deduplicator_class: __.typx.Optional[ type[ Deduplicator ] ] = None,
    ) -> __.a.Self:
        ''' Produces invoker from invocable and arguments model.

            The name of the invocable is used as the name of the invoker
            and the arguments model is validated. '''
        return selfclass(
            name = invocable.__name__,
            ensemble = ensemble,
            invocable = invocable,
            argschema = _validate_argschema( argschema ),
            deduplicator_class = deduplicator_class )

    async def __call__(
        self,
        auxdata: __.Globals,
        arguments: Arguments, *,
        supplements: __.accret.Dictionary = None,
    ) -> __.a.Any:
        context = Context(
            auxdata = auxdata, invoker = self, supplements = supplements )
        return await self.invocable( context, arguments )


Invocable: __.a.TypeAlias = (
    __.a.Callable[
        [ __.Globals, 'Invoker', Arguments, __.accret.Namespace ],
        #[ Context, Arguments ],
        __.AbstractCoroutine[ __.a.Any, __.a.Any, __.a.Any ] ] )


# TODO: Use accretive validator dictionary for preparers registry.
preparers = __.accret.Dictionary( )


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
    # TODO: Return accessor object instead of accretive namespace.
    return __.accret.Namespace( ensembles = ensembles, invokers = invokers )


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
    ensembles = __.accret.Dictionary( )
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
) -> __.AbstractDictionary[ str, 'Invoker' ]:
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
                summary = "Could not prepare invoker."
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
    'summarization':
        __.DictionaryProxy( { 'name': 'summarization', 'enable': True } ),
} )


def _trim_descriptions( schema ):
    from inspect import cleandoc
    for entry_name, entry in schema.items( ):
        if isinstance( entry, __.AbstractDictionary ):
            _trim_descriptions( entry )
        if 'description' != entry_name: continue
        if not isinstance( entry, str ): continue
        schema[ 'description' ] = cleandoc( entry )


def _validate_argschema( schema ):
    from jsonschema.validators import Draft202012Validator as Validator
    _trim_descriptions( schema )
    Validator.check_schema( schema )
    return schema
