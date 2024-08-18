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

write_file_model = {
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
}

@__.register_function( write_file_model )
async def write_file( auxdata, /, path, contents, mode = 'truncate' ):
    from aiofiles import open as open_
    mode_ = { 'append': 'a', 'truncate': 'w' }[ mode ]
    async with open_( path, mode_ ) as stream:
        return await stream.write( contents )
