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


''' Native prompt definitions, instances, and stores. '''


from .. import core as _core
from . import __
from ..exceptions import (
    PromptRenderFailure as _PromptRenderFailure,
    PromptTemplateAbsence as _PromptTemplateAbsence,
)


class Definition( _core.Definition ):

    class Instance( _core.Definition.Instance ):
        # TODO: Immutability of class and instances.

        __slots__ = ( 'controls', )

        controls: __.typx.Any # TODO: Correct type for controls.

        def __init__(
            self,
            definition: 'Definition',
            values: __.cabc.Mapping[ str, __.typx.Any ] = None
        ):
            super( ).__init__( definition )
            values = values or { }
            self.controls = __.types.MappingProxyType( {
                name: (
                    variable.create_control( values[ name ] )
                    if name in values else variable.create_control_default( ) )
                for name, variable in self.definition.variables.items( ) } )

        def render( self, auxdata: __.Globals ) -> str:
            # TODO: Async execution.
            # TODO: Cache result.
            # TODO: Immutable namespaces for fragments and variables.
            definition = self.definition
            variables = __.accret.Namespace( **self.serialize( ) )
            templates = tuple(
                acquire_template( auxdata, template_id )
                for template_id in self.definition.templates )
            fragments = __.accret.Namespace( **{
                name: acquire_fragment( auxdata, filename )
                for name, filename in definition.fragments.items( ) } )
            # TODO: Additional context, such as current provider and model.
            text = '\n\n'.join( # TODO: Configurable delimiter.
                template.render( variables = variables, fragments = fragments )
                for template in templates )
            if not text: raise _PromptRenderFailure( "empty text produced" )
            return text

        def serialize( self ) -> dict:
            from ...controls.core import serialize_dictionary
            return serialize_dictionary( self.controls )

    def __init__(
        self, location, name, species, templates,
        attributes = None, fragments = None, variables = ( )
    ):
        from ...controls.core import descriptor_to_definition
        super( ).__init__( location, name )
        self.species = species
        self.templates = templates # TODO: Validate.
        self.attributes = attributes or __.types.MappingProxyType( { } )
        # TODO: Validate fragments. Bucket by MIME type?
        self.fragments = fragments or { }
        self.variables = __.types.MappingProxyType( {
            variable[ 'name' ]: descriptor_to_definition( variable )
            for variable in variables } )


class Store( _core.Store ):

    async def acquire_definitions(
        self,
        auxdata: __.Globals,
    ) -> __.cabc.Mapping[ str, 'Definition' ]:
        scribe = __.acquire_scribe( __package__ )
        location = self.location
        match location:
            case __.Path( ): pass
            case _: raise NotImplementedError
        # TODO: Rename 'descriptors' to 'definitions'.
        location = location / 'descriptors'
        files = tuple( location.resolve( strict = True ).glob( '*.toml' ) )
        deserializer = __.funct.partial(
            _deserialize_definition_data, store = self )
        results = await __.read_files_async(
            *files, deserializer = deserializer, return_exceptions = True )
        definitions = { }
        for file, result in zip( files, results ):
            match result:
                case __.generics.Error( error ):
                    summary = f"Could not load prompt definition at '{file}'."
                    auxdata.notifications.enqueue_error(
                        error, summary, scribe = scribe )
                case __.generics.Value( definition ):
                    definitions[ definition.name ] = definition
        return __.types.MappingProxyType( definitions )

_core.flavors[ 'native' ] = Store


def acquire_fragment( auxdata: __.Globals, filename: str ) -> str:
    # TODO: Async execution.
    file = discover_file_from_stores( auxdata, f"fragments/{filename}" )
    # TODO: Use LRU cache.
    with file.open( ) as stream: return stream.read( )


def acquire_template( auxdata: __.Globals, identifier: str ):
    ''' Returns template object if identifier located in relevant store. '''
    # TODO: Return type.
    # TODO: Async execution.
    from mako.template import Template
    file = discover_file_from_stores(
        auxdata, f"templates/{identifier}.md.mako" )
    # TODO: Use 'module_directory' argument for caching.
    return Template(
        filename = str( file ),
        error_handler = _report_template_error,
    )


def discover_file_from_stores( auxdata: __.Globals, name: str ) -> __.Path:
    ''' Returns path to file if it exists in any store.

        Stores are searched in reverse order, under the assumption that
        custom prompt stores come later than default prompt stores and should
        override them.
    '''
    files = tuple(
        ( store.location / name ).resolve( strict = True )
        for store in reversed( auxdata.prompts.stores.values( ) )
        if isinstance( store, Store ) )
    for file in files:
        if not file.exists( ): continue
        return file
    raise _PromptTemplateAbsence( name )


def _deserialize_definition_data( data: str, store: 'Store' ) -> 'Definition':
    ''' Converts definition data into definition. '''
    from tomli import loads
    return Definition.instantiate_descriptor( store, loads( data ) )


def _report_template_error( context, exc ):
    ic( context )
    ic( __.exception_to_str( exc ) )
