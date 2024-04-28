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


''' Robust JSON handling. '''


def loads( string ):
    from json import JSONDecodeError, loads
    # LLMs can sometimes wrap JSON with code fences.
    if string.startswith( '```json' ) and string.endswith( '```' ):
        string = string[ 7 : -3 ]
    elif string.startswith( '```' ) and string.endswith( '```' ):
        string = string[ 3 : -3 ]
    try: return loads( string )
    except JSONDecodeError:
        # On failure, try to find JSON array or object at end of string,
        # since LLMs can sometimes be chatty even when asked not to be.
        # Also, handles case when LLM is front-loading function calls.
        # Not perfect, since bracket asymmetry may occur inside of strings.
        curly_counter = square_counter = 0
        start_index = end_index = len( string ) - 1
        for i in range( end_index, -1, -1 ):
            char = string[ i ]
            if '}' == char: curly_counter += 1
            elif '{' == char: curly_counter -= 1
            if ']' == char: square_counter += 1
            elif '[' == char: square_counter -= 1
            if 0 > curly_counter or 0 > square_counter: raise
            if 0 == curly_counter and 0 == square_counter:
                start_index = i
                break
        else: raise
        if start_index < end_index: return loads( string[ start_index : ] )
        raise
