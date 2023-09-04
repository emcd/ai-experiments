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


''' Message processing utilities. '''


def prepare_prompt_templates( configuration, directories ):
    templates = { }
    for template_class in ( 'canned', 'system', ):
        templates[ template_class ] = { }
        templates[ template_class ].update( _acquire_prompt_templates(
            configuration[ 'main-path' ].joinpath(
                f".local/data/{template_class}-prompts" ) ) )
        user_directory = directories.user_data_path.joinpath(
            f"{template_class}-prompts" )
        if user_directory.exists( ):
            templates[ template_class ].update( _acquire_prompt_templates(
                user_directory ) )
    from types import SimpleNamespace
    return SimpleNamespace( **templates )


def render_prompt_template( template, controls, variables = None ):
    from collections.abc import Mapping as AbstractDictionary
    from types import SimpleNamespace # TODO: Make immutable.
    if isinstance( controls, AbstractDictionary ):
        controls = SimpleNamespace( **controls )
    variables = variables or { }
    if isinstance( variables, AbstractDictionary ):
        variables = SimpleNamespace( **variables )
    from mako.template import Template
    return Template( template ).render(
        controls = controls, variables = variables )


def _acquire_prompt_templates( directory ):
    from yaml import safe_load
    templates = { }
    for path in directory.resolve( strict = True ).glob( '*.yaml' ):
        with path.open( ) as stream: contents = safe_load( stream )
        name = contents[ 'id' ]
        templates[ name ] = contents
    return templates
