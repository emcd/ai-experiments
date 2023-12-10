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


from . import base as __


class Definition:

    @classmethod
    def instantiate_descriptor( class_, descriptor ):
        return class_( **descriptor )

    def __init__(
        self, name, species, templates,
        attributes = None, fragments = ( ), variables = ( )
    ):
        from ..controls.core import descriptor_to_definition
        self.name = name
        self.species = species # TODO: Validate. Dispatch to subclass?
        self.templates = templates # TODO: Validate.
        self.attributes = attributes or __.DictionaryProxy( { } )
        # TODO: Validate fragments. Bucket by MIME type?
        self.fragments = fragments
        self.variables = __.DictionaryProxy( {
            variable[ 'name' ]: descriptor_to_definition( variable )
            for variable in variables } )

    def create_manager( self ): return Manager( self )


class Manager:

    def __init__( self, definition ):
        self.definition = definition

    def render( self, values = __.DictionaryProxy( { } ) ):
        # TODO: Validate values against variable definitions.
        # TODO: Acquire templates.
        # TODO: Acquire fragments.
        # TODO: Render prompt.
        pass


# TODO: Support async loading.
def prepare( auxdata ):
    return __.DictionaryProxy( {
        name: Definition.instantiate_descriptor( descriptor )
        for name, descriptor in _acquire_descriptors( auxdata ).items( ) } )


# TODO: Support async loading.
def _acquire_descriptors( auxdata ):
    from tomli import load
    distribution_directory_base = auxdata.configuration[ 'main-path' ] / 'data'
    suffix = 'prompts/descriptors'
    descriptors = { }
    for directory in (
        distribution_directory_base / suffix,
        auxdata.directories.user_data_path / suffix,
    ):
        if not directory.exists( ): continue
        for path in directory.resolve( strict = True ).glob( '*.toml' ):
            with path.open( 'rb' ) as stream:
                # TODO? Prefix with species.
                descriptors[ path.stem ] = load( stream )
    return __.DictionaryProxy( descriptors )


def _acquire_fragment( auxdata, filename ):
    distribution_directory_base = auxdata.configuration[ 'main-path' ] / 'data'
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
    distribution_directory_base = auxdata.configuration[ 'main-path' ] / 'data'
    suffix = 'prompts/templates'
    for directory in (
        distribution_directory_base / suffix,
        auxdata.directories.user_data_path / suffix,
    ):
        if not directory.exists( ): continue
        path = directory / f"{identifier}.md.mako"
        if not path.exists( ): continue
        # TODO: Use 'module_directory' argument for caching.
        return Template( filename = str( path ) )
    raise FileNotFoundError( identifier ) # TODO: Improve.
