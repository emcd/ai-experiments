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


async def acquire_models_integrators(
    auxdata: __.CoreGlobals, name: str
) -> __.AbstractDictionary[
    _core.ModelSpecies, __.AbstractSequence[ _core.ModelsIntegrator ]
]:
    ''' Returns models integrators, general to specific, by species. '''
    from collections import defaultdict
    from tomli import loads
    # TODO: Account for custom models, such as fine-tunes.
    #       Attributes integrators will come from application configuration
    #       rather than package data.
    cfile_name = 'attributes.toml'
    cfiles = [ ]
    integrators = defaultdict( list )
    directory = auxdata.distribution.provide_data_location( 'providers', name )
    # TODO: Raise error if provider data directory does not exist.
    cfiles.append( directory / cfile_name )
    # Longest model family names go last under the assumption that they are
    # more specific than shorter model family names with the same prefix and
    # thus should override them.
    cfiles.extend( sorted(
        directory.rglob( f"model-families/*/{cfile_name}" ),
        key = lambda f: len( f.parent.name ) ) )
    # Specific models (and their aliases) always go after model families.
    cfiles.extend( directory.rglob( f"models/*/{cfile_name}" ) )
    acquirers = tuple(
        __.text_file_presenter_from_url( cfile ).acquire_content( )
        for cfile in cfiles )
    configurations = tuple(
        loads( content ) for content in await __.gather_async( *acquirers ) )
    for cfile, configuration in zip( cfiles, configurations ):
        for species in _core.ModelSpecies:
            descriptor = configuration.get( species.value )
            if not descriptor: continue
            # TODO: Improve error handling.
            #       Catch regex errors and provide proper context.
            integrators[ species ].append(
                _core.ModelsIntegrator.from_descriptor( descriptor ) )
    return __.DictionaryProxy( {
        species: tuple( sequence ) for species, sequence
        in integrators.items( ) } )
