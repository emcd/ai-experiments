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


''' Foundation for AI functions for I/O. '''

# pylint: disable=unused-import


from ..__ import *


def render_prompt( auxdata, control, content, mime_type ):
    from .prompts import select_default_instructions
    control = control or { }
    provider = auxdata.providers[ auxdata.controls[ 'provider' ] ]
    instructions = control.get( 'instructions', '' )
    if control.get( 'mode', 'supplement' ):
        instructions = ' '.join( filter( None, (
            select_default_instructions( mime_type ), instructions ) ) )
    return provider.render_data(
        dict( content = content, instructions = instructions ),
        auxdata.controls )
