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


# TODO: Use accretive validator dictionary for preparers registry.
preparers = __.AccretiveDictionary( )


async def prepare( auxdata ):
    ''' Prepares ensembles of invocables. '''
    scribe = __.acquire_scribe( __package__ )
    results = await __.gather_async(
        *preparers.values( ), return_exceptions = True )
    invocables = { }
    for name, result in zip( preparers.keys( ), results ):
        match result:
            case __.g.Error( error ):
                summary = "Could not prepare invocables ensemble {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( ensemble ):
                # TODO: Collect ensembles.
                invocables.update( ensemble )
    #return __.DictionaryProxy( invocables )
    return survey_functions( )


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
