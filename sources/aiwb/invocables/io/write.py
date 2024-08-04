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


''' AI functionality for writing files. '''


from . import __


@__.register_function( {
    'name': 'write_file',
    'description': '''
Writes provided contents to the given file. Returns the number of characters
written. ''',
    'parameters': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'Path to the file to be written.'
            },
            'contents': {
                'type': 'string',
            },
            'mode': {
                'type': 'string',
                'enum': [ 'append', 'truncate' ],
                'default': 'truncate',
            },
        },
        'required': [ 'path', 'contents' ],
    },
} )
def write_file( auxdata, /, path, contents, mode = 'truncate' ):
    with open( path, { 'append': 'a', 'truncate': 'w' }[ mode] ) as file:
        return file.write( contents )
