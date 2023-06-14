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


''' State management for Panel GUI. '''


from panel.layout import Column, HSpacer, Row
from panel.pane import Markdown
from panel.widgets import (
    Button,
    Checkbox,
    FloatSlider,
    IntSlider,
    Select,
    StaticText,
    TextAreaInput,
    TextInput,
)


def populate( gui, vectorstores ):
    populate_providers_selector( gui )
    populate_models_selector( gui )
    populate_system_prompts_selector( gui )
    populate_summarization_prompts_selector( gui )
    populate_vectorstores_selector( gui, vectorstores )


def populate_models_selector( gui ):
    provider = gui.selector_provider.metadata__[
        gui.selector_provider.value ][ 'model-provider' ]
    models = provider( )
    gui.selector_model.options = list( models.keys( ) )
    gui.selector_model.metadata__ = models


def populate_providers_selector( gui ):
    gui.selector_provider.options = [
        'OpenAI',
    ]
    gui.selector_provider.metadata__ = {
        'OpenAI': { 'model-provider': _provide_openai_models },
    }


def populate_system_prompts_selector( gui ):
    from pathlib import Path
    from .callbacks import update_system_prompt_variables
    _populate_prompts_selector(
        gui.selector_system_prompt,
        Path( '.local/data/system-prompts' ) )
    update_system_prompt_variables( gui )


def populate_summarization_prompts_selector( gui ):
    from pathlib import Path
    from .callbacks import update_summarization_prompt_variables
    _populate_prompts_selector(
        gui.selector_summarization_prompt,
        Path( '.local/data/summarization-prompts' ) )
    update_summarization_prompt_variables( gui )


def populate_vectorstores_selector( gui, vectorstores ):
    gui.selector_vectorstore.metadata__ = vectorstores
    gui.selector_vectorstore.options = list( vectorstores.keys( ) )


def save_conversation( gui, registry, path ):
    from .layouts import layout
    state = { }
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        component_class = data[ 'component_class' ]
        if component_class in ( Button, HSpacer, ): continue
        component = getattr( gui, name )
        if component_class in ( Column, Row, ):
            if 'persistence_functions' not in data: continue
            saver_name = data[ 'persistence_functions' ][ 'save' ]
            saver = registry[ saver_name ]
            state.update( saver( component ) )
        elif component_class in (
            Checkbox, FloatSlider, IntSlider, Select, TextAreaInput, TextInput,
        ): state[ name ] = dict( value = component.value )
        elif component_class in ( Markdown, StaticText, ):
            state[ name ] = dict( value = component.object )
        else:
            raise ValueError(
                f"Unrecognized component class '{component_class}' "
                f"for component '{name}'." )
    from json import dump
    with path.open( 'w' ) as file: dump( state, file, indent = 2 )


def restore_conversation( gui, registry, path ):
    from json import load
    from .layouts import layout
    with path.open( ) as file: state = load( file )
    for name, data in layout.items( ):
        if not data.get( 'persist', True ): continue
        component_class = data[ 'component_class' ]
        if component_class in ( Button, HSpacer, ): continue
        component = getattr( gui, name )
        if component_class in ( Column, Row, ):
            if 'persistence_functions' not in data: continue
            restorer_name = data[ 'persistence_functions' ][ 'restore' ]
            restorer = registry[ restorer_name ]
            restorer( component, state )
        elif component_class in (
            Checkbox, FloatSlider, IntSlider, Select, TextAreaInput, TextInput,
        ): component.value = state[ name ][ 'value' ]
        elif component_class in ( Markdown, StaticText, ):
            component.object = state[ name ][ 'value' ]
        else:
            raise ValueError(
                f"Unrecognized component class '{component_class}' "
                f"for component '{name}'." )


def _populate_prompts_selector( gui_selector, prompts_directory ):
    from yaml import safe_load
    metadata = { }; prompt_names = [ ]
    for prompt_path in (
        prompts_directory.resolve( strict = True ).glob( '*.yaml' )
    ):
        with prompt_path.open( ) as file:
            contents = safe_load( file )
            id_ = contents[ 'id' ]
            metadata[ id_ ] = contents
            prompt_names.append( id_ )
    gui_selector.metadata__ = metadata
    gui_selector.options = prompt_names


def _provide_openai_models( ):
    from collections import defaultdict
    from operator import itemgetter
    import openai
    # TODO: Only call API when explicitly desired. Should persist to disk.
    model_names = sorted( map(
        itemgetter( 'id' ),
        openai.Model.list( ).to_dict_recursive( )[ 'data' ] ) )
    sysprompt_honor = defaultdict( lambda: False )
    sysprompt_honor.update( {
        'gpt-3.5-turbo-0613': True,
        'gpt-3.5-turbo-16k-0613': True,
        'gpt-4': True,
        'gpt-4-32k': True,
        'gpt-4-0613': True,
        'gpt-4-32k-0613': True,
    } )
    tokens_limits = defaultdict( lambda: 4096 ) # Some are 4097... _shrug_.
    tokens_limits.update( {
        'code-davinci-002': 8000,
        'gpt-3.5-turbo-16k': 16384,
        'gpt-3.5-turbo-16k-0613': 16384,
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-4-0613': 8192,
        'gpt-4-32k-0613': 32768,
    } )
    return {
        model_name: {
            'honors-system-prompt': sysprompt_honor[ model_name ],
            'tokens-limit': tokens_limits[ model_name ],
        }
        for model_name in model_names
    }
