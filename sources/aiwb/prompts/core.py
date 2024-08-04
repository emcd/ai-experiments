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


''' Core functions for prompts. '''


from . import __


class Definition:

    @classmethod
    def instantiate_descriptor( class_, descriptor ):
        return class_( **descriptor )

    def __init__(
        self, name, species, templates,
        attributes = None, fragments = None, variables = ( )
    ):
        from ..controls.core import descriptor_to_definition
        self.name = name
        self.species = species # TODO: Validate. Dispatch to subclass?
        self.templates = templates # TODO: Validate.
        self.attributes = attributes or __.DictionaryProxy( { } )
        # TODO: Validate fragments. Bucket by MIME type?
        self.fragments = fragments or { }
        self.variables = __.DictionaryProxy( {
            variable[ 'name' ]: descriptor_to_definition( variable )
            for variable in variables } )

    def create_prompt( self, values = None ):
        return Instance( self, values = values )

    def deserialize( self, data ):
        return Instance( self, values = data )


class Instance:

    def __init__( self, definition, values = None ):
        self.definition = definition
        values = values or { }
        self.controls = __.DictionaryProxy( {
            name: (
                variable.create_control( values[ name ] ) if name in values
                else variable.create_control_default( ) )
            for name, variable in definition.variables.items( ) } )

    # TODO: Cache result.
    def render( self, auxdata ):
        # TODO: Immutable namespace for variables.
        variables = __.SimpleNamespace( **self.serialize( ) )
        templates = tuple(
            _acquire_template( auxdata, template_id )
            for template_id in self.definition.templates )
        fragments = __.SimpleNamespace( **{ # TODO: Immutable namespace.
            name: _acquire_fragment( auxdata, filename )
            for name, filename in self.definition.fragments.items( ) } )
        # TODO: Additional context, such as current model provider and name.
        text = '\n\n'.join( # TODO: Configurable delimiter.
            template.render( variables = variables, fragments = fragments )
            for template in templates )
        if not text: raise ValueError( 'Empty prompt rendered.' )
        return text

    def serialize( self ):
        from ..controls.core import serialize_dictionary
        return serialize_dictionary( self.controls )


async def prepare( auxdata ):
    ''' Load prompt definitions. '''
    descriptors = await _acquire_descriptors( auxdata )
    definitions = __.DictionaryProxy( {
        name: Definition.instantiate_descriptor( descriptor )
        for name, descriptor in descriptors.items( ) } )
    return definitions


async def _acquire_descriptors( auxdata ):
    # TODO: Support configurable prompt locations.
    from itertools import chain
    from tomli import loads
    scribe = __.acquire_scribe( __package__ )
    distribution_directory_base = (
        auxdata.distribution.provide_data_location( ) )
    suffix = 'prompts/descriptors'
    directories = tuple(
        directory for directory_base
        in ( distribution_directory_base, auxdata.directories.user_data_path )
        if ( directory := directory_base / suffix ).exists( ) )
    files = tuple( chain.from_iterable(
        directory.resolve( strict = True ).glob( '*.toml' )
        for directory in directories ) )
    results = await __.read_files_async(
        *files, deserializer = loads, return_exceptions = True )
    descriptors = { }
    for file, result in zip( files, results ):
        match result:
            case __.g.Error( error ):
                summary = f"Could not load prompt descriptor at: {file}"
                scribe.error( summary, exc_info = error )
                auxdata.notifications.put( error )
            case __.g.Value( record ):
                descriptors[ record[ 'name' ] ] = record
    return __.DictionaryProxy( descriptors )


def _acquire_fragment( auxdata, filename ):
    distribution_directory_base = (
        auxdata.distribution.provide_data_location( ) )
    suffix = 'prompts/fragments'
    for directory in (
        distribution_directory_base / suffix,
        auxdata.directories.user_data_path / suffix,
    ):
        if not directory.exists( ): continue
        path = directory / filename
        if not path.exists( ): continue
        # TODO: Use LRU cache.
        with path.open( ) as stream: return stream.read( )
    raise FileNotFoundError( filename ) # TODO: Improve.


def _acquire_template( auxdata, identifier ):
    from mako.template import Template
    distribution_directory_base = (
        auxdata.distribution.provide_data_location( ) )
    suffix = 'prompts/templates'
    for directory in (
        distribution_directory_base / suffix,
        auxdata.directories.user_data_path / suffix,
    ):
        if not directory.exists( ): continue
        path = directory / f"{identifier}.md.mako"
        if not path.exists( ): continue
        # TODO: Use 'module_directory' argument for caching.
        return Template(
            filename = str( path ),
            error_handler = _report_template_error,
        )
    raise FileNotFoundError( identifier ) # TODO: Improve.


def _extract_control_value( control ):
    from ..controls.core import FlexArray, InstanceBase
    if isinstance( control, FlexArray.Instance ):
        return tuple(
            _extract_control_value( element ) for element in control )
    if isinstance( control, InstanceBase ): return control.value
    raise ValueError # TODO: Fill out.


def _report_template_error( context, exc ):
    ic( context )
    ic( exc )
