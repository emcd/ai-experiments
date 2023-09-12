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


''' Default chatter template. '''


# TODO: Cleanup imports.

import pathlib

from typing import ClassVar, Dict

import param

from panel.config import config
from panel.template.base import Template
from panel.theme import Design
from panel.theme.base import THEMES
from panel.theme.native import Native


class DefaultTemplate( Template ):
    ''' Template for standard chatter layout. '''

    design = param.ClassSelector(
        class_ = Design,
        default = Native,
        is_instance = False,
        instantiate = False,
        doc = '''A Design applies a specific design system to a template.'''
    )

    _css = pathlib.Path( __file__ ).parent / 'default.css'

    _resources: ClassVar[Dict[str, Dict[str, str]]] = {
        'css': {
            'lato': "https://fonts.googleapis.com/css?family=Lato&subset=latin,latin-ext"
        }
    }

    _template = pathlib.Path( __file__ ).parent / 'default.html'

    def __init__(self, **params):
        template = self._template.read_text( encoding = 'utf-8' )
        super().__init__( template = template, **params )
        self._render_variables['theme'] = self._design.theme
