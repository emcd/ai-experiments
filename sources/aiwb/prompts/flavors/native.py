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


''' Native prompt definitions, instances, and managers. '''


from .. import core as _core
from . import __


class Definition( _core.Definition ):


    @__.dataclass( kw_only = True, slots = True )
    #@__.dataclass( frozen = True, kw_only = True, slots = True )
    class Instance( _core.Definition.Instance ):

        values: __.InitVar[ __.AbstractDictionary[ str, __.a.Any ] ] = None
        controls: __.a.Any = __.dataclass_declare( init = False )

        def __post_init__( self, values ):
            values = values or { }
            self.controls = __.DictionaryProxy( {
                name: (
                    variable.create_control( values[ name ] )
                    if name in values else variable.create_control_default( ) )
                for name, variable in self.definition.variables.items( ) } )

        def render( self, auxdata: __.Globals ) -> str:
            # TODO: Async execution.
            # TODO: Cache result.
            # TODO: Immutable namespaces for fragments and variables.
            definition = self.definition
            variables = __.AccretiveNamespace( **self.serialize( ) )
            templates = tuple(
                _acquire_template( auxdata, definition.manager, template_id )
                for template_id in self.definition.templates )
            fragments = __.AccretiveNamespace( **{
                name: _acquire_fragment(
                    auxdata, definition.manager, filename )
                for name, filename in definition.fragments.items( ) } )
            # TODO: Additional context, such as current provider and model.
            text = '\n\n'.join( # TODO: Configurable delimiter.
                template.render( variables = variables, fragments = fragments )
                for template in templates )
            if not text: raise ValueError( 'Empty prompt rendered.' )
            return text

        def serialize( self ) -> dict:
            from ...controls.core import serialize_dictionary
            return serialize_dictionary( self.controls )

    def __init__(
        self, manager, location, name, species, templates,
        attributes = None, fragments = None, variables = ( )
    ):
        from ...controls.core import descriptor_to_definition
        super( ).__init__( manager, location, name )
        self.species = species
        self.templates = templates # TODO: Validate.
        self.attributes = attributes or __.DictionaryProxy( { } )
        # TODO: Validate fragments. Bucket by MIME type?
        self.fragments = fragments or { }
        self.variables = __.DictionaryProxy( {
            variable[ 'name' ]: descriptor_to_definition( variable )
            for variable in variables } )


class Manager( _core.Manager ):

    @classmethod
    async def prepare( selfclass, auxdata: __.Globals ) -> __.a.Self:
        return selfclass( )

    async def acquire_definitions(
        self,
        auxdata: __.Globals,
        location: __.Location,
    ) -> __.AbstractDictionary[ str, Definition ]:
        match location:
            case __.Path( ): pass
            case _: raise NotImplementedError
        location_ = location / 'descriptors' # TODO: Rename to 'definitions'.
        files = tuple( location_.resolve( strict = True ).glob( '*.toml' ) )
        deserializer = __.partial_function(
            _deserialize_definition_data, manager = self, location = location )
        results = await __.read_files_async(
            *files, deserializer = deserializer, return_exceptions = True )
        definitions = { }
        for file, result in zip( files, results ):
            match result:
                case __.g.Error( error ):
                    summary = f"Could not load prompt definition at '{file}'."
                    auxdata.notifications.enqueue_error(
                        error, summary, scribe = scribe )
                case __.g.Value( definition ):
                    definitions[ definition.name ] = definition
        return __.DictionaryProxy( definitions )


async def prepare( auxdata: __.Globals ) -> Manager:
    return await Manager.prepare( auxdata )


def _acquire_fragment(
    auxdata: __.Globals, manager: Manager, filename: str
) -> str:
    # TODO: Async execution.
    locations = tuple(
        store.location / 'fragments'
        for store in auxdata.prompts.stores.values( )
        if manager is store.manager )
    # Last match wins.
    files = tuple( location / filename for location in reversed( locations ) )
    for file in files:
        if not file.exists( ): continue
        break
    else: raise FileNotFoundError( filename ) # TODO: Improve.
    # TODO: Use LRU cache.
    with file.open( ) as stream: return stream.read( )


def _acquire_template(
    auxdata: __.Globals, manager: Manager, identifier: str
):
    # TODO: Async execution.
    from mako.template import Template
    filename = f"{identifier}.md.mako"
    locations = tuple(
        store.location / 'templates'
        for store in auxdata.prompts.stores.values( )
        if manager is store.manager )
    # Last match wins.
    files = tuple( location / filename for location in reversed( locations ) )
    for file in files:
        if not file.exists( ): continue
        break
    else: raise FileNotFoundError( filename ) # TODO: Improve.
    # TODO: Use 'module_directory' argument for caching.
    return Template(
        filename = str( file ),
        error_handler = _report_template_error,
    )


def _deserialize_definition_data(
    data: str, manager: Manager, location: __.Location
) -> Definition:
    ''' Converts definition data into definition. '''
    from tomli import loads
    return Definition.instantiate_descriptor(
        manager, location, loads( data ) )


def _report_template_error( context, exc ):
    ic( context )
    ic( exc )
