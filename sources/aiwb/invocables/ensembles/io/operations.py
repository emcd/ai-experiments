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
    # TODO: Validate arguments.
    result = await _operate(
        opname = 'survey_entries', context = context, arguments = arguments )
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


async def read(
    context: __.Context, arguments: __.Arguments
) -> __.AbstractDictionary:
    ''' Reads file at URL or filesystem path.

        Metadata includes location and MIME type.
        If the content is text, then it will be presented as a string.
        Otherwise, the file size will be returned without the content.
    '''
    arguments_ = arguments.copy( )
    # TODO: Validate arguments.
    try: accessor = await _accessor_from_arguments( arguments_ )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    if not isinstance( accessor, __.FileAccessor ):
        return { 'error': 'Cannot acquire content of non-file.' }
    #as_bytes = arguments_.pop( 'as_bytes', False )
    #if as_bytes: return await _read_as_bytes( accessor, context, arguments_ )
    return await _read_as_string( accessor, context, arguments_ )


async def write_file(
    context: __.Context, arguments: __.Arguments
) -> __.AbstractDictionary:
    ''' Writes file at URL or filesystem path.

        Options can control update behavior.

        Result includes number of bytes written.
    '''
    arguments_ = arguments.copy( )
    if 'location' not in arguments:
        return { 'error': "Argument 'location' is required." }
    if 'content' not in arguments:
        return { 'error': "Argument 'content' is required." }
    options = arguments.get( 'options', ( ) )
    if not isinstance( options, __.AbstractSequence ):
        return { 'error': "Argument 'options' must be a list." }
    try:
        accessor = await _accessor_from_arguments(
            arguments_, species = __.LocationSpecies.File )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    if not isinstance( accessor, __.FileAccessor ):
        return { 'error': 'Cannot update content of non-file.' }
    #as_bytes = arguments_.pop( 'as_bytes', False )
    #if as_bytes: return await _write_as_bytes( accessor, context, arguments_ )
    return await _write_as_string( accessor, context, arguments_ )


async def _accessor_from_arguments(
    arguments: __.Arguments,
    species: __.Optional[ __.LocationSpecies ] = __.absent,
) -> __.SpecificLocationAccessor:
    url = __.Url.from_url( arguments.pop( 'location' ) )
    accessor = __.LocationAccessorSimple.from_url( url )
#    if url.scheme in ( '', 'file' ):
#        accessor = __.LocationAccessorSimple.from_url( url )
#    else:
#        accessor = __.LocationAccessorWithCache.from_url( url )
    return await accessor.as_specific( species = species )


async def _operate(
    opname: str, context: __.Context, arguments: __.Arguments,
) -> __.AbstractDictionary:
    arguments_ = arguments.copy( )
    # TODO? Move accessor creation to callers for better customization.
    try:
        accessor = (
            await __.LocationAccessorSimple.from_url(
                arguments_.pop( 'location' ) ).as_specific( ) )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    try: result = await getattr( accessor, opname )( **arguments_ )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    return { 'success': result }


async def _read_as_bytes(
    accessor: __.FileAccessor, context: __.Context, arguments: __.Arguments
) -> __.AbstractDictionary:
    try: result = await accessor.acquire_content_bytes( )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    from base64 import b64encode
    data = b64encode( result.content ).decode( 'ascii' )
    mimetype = result.mimetype
    data_url = f"data:{mimetype};base64,{data}"
    return {
        'location': str( accessor ),
        'mimetype': mimetype,
        'data_url': data_url,
    }


async def _read_as_string(
    accessor: __.FileAccessor, context: __.Context, arguments: __.Arguments
) -> __.AbstractDictionary:
    try: result = await accessor.acquire_content( charset = '#DETECT#' )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    return {
        'location': str( accessor ),
        'mimetype': result.mimetype,
        'charset': result.charset,
        'content': result.content,
    }


async def _write_as_string(
    accessor: __.FileAccessor, context: __.Context, arguments: __.Arguments
) -> __.AbstractDictionary:
    content = arguments[ 'content' ]
    options = arguments.get( 'options', ( ) )
    options_ = __.FileUpdateOptions.Defaults
    for option in options:
        if 'append' == option:
            options_ |= __.FileUpdateOptions.Append
        if 'error-if-exists' == option:
            options_ |= __.FileUpdateOptions.Absence
    try: result = await accessor.update_content( content, options = options_ )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    return {
        'location': str( accessor ),
        'mimetype': result.mimetype,
        'charset': result.charset,
        'count': result.count,
    }
