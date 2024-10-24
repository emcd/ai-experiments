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


''' Utilities for AI providers. '''


from . import __
from . import core as _core
from . import exceptions as _exceptions
from . import interfaces as _interfaces


async def acquire_provider_configuration(
    auxdata: __.CoreGlobals, name: str
) -> __.AbstractDictionary[ str, __.a.Any ]:
    ''' Returns configuration dictionary for AI provider. '''
    directory = auxdata.distribution.provide_data_location( 'providers', name )
    # TODO: Raise error if provider data directory does not exist.
    configuration = { }
    for configuration_ in await __.gather_async(
        _acquire_configuration( auxdata, directory ),
        _acquire_configurations( auxdata, directory, 'model-families' ),
        _acquire_configurations( auxdata, directory, 'models' )
    ): configuration.update( configuration_ )
    # Extend from custom configuration.
    for index_name in ( 'model-families', 'models', ):
        configurations_ = _copy_custom_provider_configurations(
            auxdata, provider_name = name, index_name = index_name )
        # TODO: Raise error if no name in an entry.
        configuration[ index_name ] = tuple( sorted(
            configuration[ index_name ] + configurations_,
            key = lambda cfg: cfg[ 'name' ] ) )
    return __.DictionaryProxy( configuration )


async def acquire_models_integrators(
    auxdata: __.CoreGlobals, name: str
) -> __.AbstractDictionary[
    _core.ModelGenera, __.AbstractSequence[ _core.ModelsIntegrator ]
]:
    ''' Returns models integrators, general to specific, by genus. '''
    # TODO: Use provider configuration directly rather than loading.
    p_configuration = await acquire_provider_configuration( auxdata, name )
    # Longest model family names go last under the assumption that they are
    # more specific than shorter model family names with the same prefix and
    # thus should override them.
    mf_configurations = sorted(
        p_configuration.get( 'model-families', ( ) ),
        key = lambda mfc: len( mfc[ 'name' ] ) )
    m_configurations = p_configuration.get( 'models', ( ) )
    # Model families always go after the provider.
    # Specific models (and their aliases) always go after model families.
    configurations = ( p_configuration, *mf_configurations, *m_configurations )
    from collections import defaultdict
    integrators = defaultdict( list )
    for configuration in configurations:
        for genus in _core.ModelGenera:
            descriptor = configuration.get( genus.value )
            if not descriptor: continue
            # TODO: Improve error handling.
            #       Catch regex errors and provide proper context.
            integrators[ genus ].append(
                _core.ModelsIntegrator.from_descriptor( descriptor ) )
    return __.DictionaryProxy( {
        genus: tuple( sequence ) for genus, sequence
        in integrators.items( ) } )


def invocation_requests_from_canister(
    processor: _interfaces.InvocationsProcessor,
    auxdata: __.CoreGlobals,
    supplements: __.AccretiveDictionary,
    canister: __.MessageCanister,
    invocables: __.AccretiveNamespace,
    ignore_invalid_canister: bool = False,
) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
    # TODO: Provide supplements based on specification from invocable.
    Error = _exceptions.InvocationFormatError
    try: requests = _validate_invocation_requests_canister( canister )
    except Error:
        if ignore_invalid_canister: return [ ]
        raise
    supplements[ 'model' ] = processor.model
    invokers = invocables.invokers
    model_context = getattr( canister.attributes, 'model_context', { } )
    # TODO: Model-specific... move to correct provider.
    tool_calls = model_context.get( 'tool_calls' )
    requests_ = [ ]
    for i, request in enumerate( requests ):
        if not isinstance( request, __.AbstractDictionary ):
            raise Error( 'Tool use request is not dictionary.' )
        if 'name' not in request:
            raise Error( 'Name is missing from tool use request.' )
        if ( name := request[ 'name' ] ) not in invokers:
            raise Error( f"Tool {name!r} is not available." )
        arguments = request.get( 'arguments', { } )
        request_ = dict( request )
        request_[ 'invocable__' ] = __.partial_function(
            invokers[ name ],
            auxdata = auxdata,
            arguments = arguments,
            supplements = supplements )
        if tool_calls:
            request_[ 'context__' ] = (
                processor.validate_request( tool_calls[ i ] ) )
        requests_.append( request_ )
    return requests_


async def _acquire_configuration(
    auxdata: __.CoreGlobals, directory: __.Path
) -> __.AbstractDictionary[ str, __.a.Any ]:
    from tomli import loads
    files = directory.glob( '*.toml' )
    acquirers = tuple(
        __.text_file_presenter_from_url( file ).acquire_content( )
        for file in files )
    configuration = { }
    for content in await __.gather_async( *acquirers ):
        configuration.update( loads( content ) )
    return configuration


async def _acquire_configurations(
    auxdata: __.CoreGlobals, directory: __.Path, index_name: str
) -> __.AbstractDictionary[ str, __.a.Any ]:
    subdirectories = tuple(
        entity for entity in directory.rglob( f"{index_name}/*" )
        if entity.is_dir( ) )
    acquirers = tuple(
        _acquire_configuration( auxdata, subdirectory )
        for subdirectory in subdirectories )
    configurations = await __.gather_async( *acquirers )
    configurations_ = [ ]
    for subdirectory, configuration in zip( subdirectories, configurations ):
        configuration_ = { 'name': subdirectory.name }
        configuration_.update( configuration )
        configurations_.append( __.DictionaryProxy( configuration_ ) )
    return __.DictionaryProxy( { index_name: tuple( configurations_ ) } )


def _copy_custom_provider_configurations(
    auxdata: __.CoreGlobals, provider_name: str, index_name: str
) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
    factory_descriptors = (
        auxdata.configuration.get( 'provider-factories', ( ) ) )
    try:
        configurations = next(
            descriptor for descriptor in factory_descriptors
            if provider_name == descriptor[ 'name' ] )
    except StopIteration: configurations = { }
    return tuple( configurations.get( index_name, ( ) ) )


def _validate_invocation_requests_canister(
    canister: __.MessageCanister
) -> __.AbstractSequence[ __.AbstractDictionary[ str, __.a.Any ] ]:
    Error = _exceptions.InvocationFormatError
    from ..codecs.json import loads
    try: requests = loads( canister[ 0 ].data )
    except Exception as exc: raise Error( str( exc ) ) from exc
    if not isinstance( requests, __.AbstractSequence ):
        raise Error( 'Tool use requests is not sequence.' )
    return requests
