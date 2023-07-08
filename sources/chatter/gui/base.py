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


''' Classes, constants, and utilities common to the GUI. '''


import dataclasses
import typing as typ

from collections import namedtuple
from collections.abc import (
    Mapping as AbstractDictionary,
    MutableSequence as AbstractMutableSequence,
    Sequence as AbstractSequence,
)
from dataclasses import dataclass
from datetime import (
    datetime as DateTime,
    timezone as TimeZone,
)
from functools import partial as partial_function
from pathlib import Path
from time import time_ns
from types import SimpleNamespace
from uuid import uuid4

import param

from panel.layout import Column, Row
from panel.reactive import ReactiveHTML


roles_emoji = {
    'AI': '🤖',
    'Document': '📄',
    'Function': '\N{Hammer and Wrench}\uFE0F',
    'Human': '🧑',
}

# TODO: Use style variables.
roles_styles = {
    'AI': {
        'background-color': 'WhiteSmoke',
    },
    'Document': {
        'background-color': 'White',
        'border-top': '2px dashed LightGray',
        'padding': '3px',
    },
    'Function': {
        'background-color': 'White',
        #'border-top': '2px dashed LightGray',
        #'padding': '3px',
    },
    'Human': {
        'background-color': 'White',
    },
}


def calculate_conversations_path( gui ):
    configuration = gui.auxdata__[ 'configuration' ]
    directories = gui.auxdata__[ 'directories' ]
    state_path = Path( configuration[ 'locations' ][ 'state' ].format(
        user_state_path = directories.user_state_path ) )
    return state_path / 'conversations'


def generate_component( components, layout, component_name ):
    entry = layout[ component_name ]
    elements = [ ]
    for element_name in entry.get( 'contains', ( ) ):
        elements.append( generate_component(
            components, layout, element_name ) )
    component_class = entry[ 'component_class' ]
    component_arguments = entry.get( 'component_arguments', { } )
    component = component_class( *elements, **component_arguments )
    components[ component_name ] = component
    return component
