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

file_update_argschema = {
    'type': 'object',
    'properties': {
        'location': {
            'type': 'string',
            'description': 'Location of the file to be written.'
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
    # TODO? Require 'mode' for OpenAI strict schema.
    'required': [ 'location', 'contents' ],
}


async def write_file(
    auxdata: __.Globals,
    invoker: __.Invoker,
    arguments: __.Arguments,
    context: __.AccretiveNamespace,
) -> int:
    ''' Writes contents to file location.

        Returns number of characters written. '''
    from aiofiles import open as open_
    mode = { 'append': 'a', 'truncate': 'w' }[
        arguments.get( 'mode', 'truncate' ) ]
    location = __.Path( arguments[ 'location' ] )
    async with open_( location, mode ) as stream:
        return await stream.write( arguments[ 'contents' ] )
