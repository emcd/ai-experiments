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


''' Available I/O operations. '''


from . import __


# TODO? grok
#   Probably move 'analyze' to separate summarization module.


async def list_folder(
    context: __.Context, arguments: __.Arguments,
) -> __.AbstractDictionary:
    ''' Lists directory at URL or filesystem path.

        May be recursive or single level.
        Optional filters, such as ignorefiles, may be applied.
    '''
    # TODO? file_size_maximum = arguments.get( 'file_size_maximum', 40000 )
    result = await _operate(
        opname = 'survey', context = context, arguments = arguments )
    if 'success' in result:
        result = result.copy( )
        dirents = [
            {
                'location': str( dirent.url ),
                'mimetype': dirent.inode.mimetype,
            }
            for dirent in result[ 'success' ]
        ]
        result[ 'success' ] = dirents
    return result


# TODO: read


# TODO: write


async def _operate(
    opname: str, context: __.Context, arguments: __.Arguments,
) -> __.AbstractDictionary:
    arguments_ = arguments.copy( )
    try:
        accessor = (
            await __.LocationAccessorSimple.from_url(
                arguments_.pop( 'location' ) ).as_specific( ) )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    return {
        'success':
            await getattr( accessor, opname )( **arguments_ ) }
