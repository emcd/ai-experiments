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
    MutableSequence as AbstractMutableSequence,
    Sequence as AbstractSequence,
)
from dataclasses import dataclass
from datetime import (
    datetime as DateTime,
    timezone as TimeZone,
)
from pathlib import Path
from time import time_ns
from types import SimpleNamespace
from uuid import uuid4

import panel as pn
import param

from panel.layout import Column, GridBox, HSpacer, Row
from panel.reactive import ReactiveHTML
from panel.widgets import Button


def calculate_conversations_path( gui ):
    configuration = gui.auxiliary_data__[ 'configuration' ]
    directories = gui.auxiliary_data__[ 'directories' ]
    state_path = Path( configuration[ 'locations' ][ 'state' ].format(
        user_state_path = directories.user_state_path ) )
    return state_path / 'conversations'
