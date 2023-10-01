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


''' Prompts to support AI agents for I/O. '''


common_code_instructions = [
    '''
As part of each summary, note any potential bugs, missing cases, or
insufficient error handling. Likewise, note todo, hack, and fixme comments.''',
]


generic_code_instructions = [
    '''
Summarize file/module-level entities, including constructs, functions, and
global variables. Do likewise for the members of constructs.''',
    '''
Note any contradictions between comments and the actual mechanics of their
corresponding entities.''',
    *common_code_instructions,
]


generic_instructions = [
    '''
List each topic, chapter title, or heading and summarize its content.''',
    '''
Note any content which may be counterfactual within the context of the
discourse or which may contradict other content.''',
]


python_code_instructions = [
    '''
Summarize classes, functions, and module attributes.''',
    '''
Note any contradictions between documentations (docstrings,
inline comments) and the actual mechanics of their corresponding
entities.''',
    *common_code_instructions,
]


def select_default_instructions( mime_type ):
    if mime_type in ( 'text/x-python', 'text/x-script.python', ):
        instructions = python_code_instructions
    elif mime_type.startswith( 'text/x-script' ):
        instructions = generic_code_instructions
    else: instructions = generic_instructions
    # TODO: Consider model-specific instruction list formats to maximize
    #       prompt adherence.
    return ' '.join( map( str.strip, instructions ) )
