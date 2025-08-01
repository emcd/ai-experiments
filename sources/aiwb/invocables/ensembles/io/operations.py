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


async def list_folder(
    context: __.Context, arguments: __.Arguments,
) -> __.cabc.Mapping:
    ''' Lists directory at URL or filesystem path.

        May be recursive or single level.
        Optional filters, such as ignorefiles, may be applied.
    '''
    # TODO? file_size_maximum = arguments.get( 'file_size_maximum', 40000 )
    arguments_ = arguments.copy( )
    # TODO: Validate arguments.
    try: accessor = await __.accessor_from_arguments( arguments_ )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    if not isinstance( accessor, __.DirectoryAccessor ):
        return { 'error': 'Cannot list entries of non-directory.' }
    arguments_[ 'attributes' ] = __.InodeAttributes.Mimetype
    if 'filters' not in arguments_:
        arguments_[ 'filters' ] = ( '@gitignore', '+vcs', )
    try: result = await accessor.survey_entries( **arguments_ )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    dirents = [
        {
            'location': str( dirent.url ),
            'mimetype': dirent.inode.mimetype,
        }
        for dirent in result
    ]
    return { 'success': dirents }


async def read(
    context: __.Context, arguments: __.Arguments
) -> __.cabc.Mapping:
    ''' Reads file at URL or filesystem path.

        Metadata includes location and MIME type.
        If the content is text, then it will be presented as a string, by
        defualt, or else a dictionary, mapping line numbers to content lines,
        if the line numbering option is enabled. Otherwise, the file size will
        be returned without the content.
    '''
    arguments_ = arguments.copy( )
    # TODO: Validate arguments.
    try: accessor = await __.accessor_from_arguments( arguments_ )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    if not isinstance( accessor, __.FileAccessor ):
        return { 'error': 'Cannot acquire content of non-file.' }
    arguments_[ 'attributes' ] = (
        __.InodeAttributes.Mimetype | __.InodeAttributes.Charset )
    #as_bytes = arguments_.pop( 'as_bytes', False )
    #if as_bytes: return await _read_as_bytes( accessor, context, arguments_ )
    return await _read_as_string( accessor, context, arguments_ )


async def write_file(
    context: __.Context, arguments: __.Arguments
) -> __.cabc.Mapping:
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
    if not isinstance( options, __.cabc.Sequence ):
        return { 'error': "Argument 'options' must be a list." }
    try:
        accessor = await __.accessor_from_arguments(
            arguments_, species = __.LocationSpecies.File )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    if not isinstance( accessor, __.FileAccessor ):
        return { 'error': 'Cannot update content of non-file.' }
    arguments_[ 'attributes' ] = (
        __.InodeAttributes.Mimetype | __.InodeAttributes.Charset )
    #as_bytes = arguments_.pop( 'as_bytes', False )
    #if as_bytes: return await _write_as_bytes( accessor, context, arguments_ )
    return await _write_as_string( accessor, context, arguments_ )


async def _read_as_bytes(
    accessor: __.FileAccessor, context: __.Context, arguments: __.Arguments
) -> __.cabc.Mapping:
    try: result = await accessor.acquire_content_result( )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    from base64 import b64encode
    data = b64encode( result.content ).decode( 'ascii' )
    mimetype = result.inode.mimetype
    data_url = f"data:{mimetype};base64,{data}"
    return {
        'location': str( accessor ),
        'mimetype': mimetype,
        'data_url': data_url,
    }


async def _read_as_string(
    accessor: __.FileAccessor, context: __.Context, arguments: __.Arguments
) -> __.cabc.Mapping:
    presenter = __.text_file_presenter_from_accessor(
        accessor = accessor, charset = '#DETECT#' )
    try: result = await presenter.acquire_content_result( )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    if arguments.get( 'number-lines', False ):
        lines = result.content.split( '\n' ) if result.content else [ ]
        content_ = { i + 1: line for i, line in enumerate( lines ) }
    else: content_ = result.content
    return {
        'location': str( accessor ),
        'mimetype': result.inode.mimetype,
        'charset': result.inode.charset,
        'content': content_,
    }


async def _write_as_string(
    accessor: __.FileAccessor, context: __.Context, arguments: __.Arguments
) -> __.cabc.Mapping:
    presenter = __.text_file_presenter_from_accessor( accessor = accessor )
    content = arguments[ 'content' ]
    options = arguments.get( 'options', ( ) )
    options_ = __.FileUpdateOptions.Defaults
    for option in options:
        if 'append' == option:
            options_ |= __.FileUpdateOptions.Append
        if 'error-if-exists' == option:
            options_ |= __.FileUpdateOptions.Absence
    try: result = await presenter.update_content( content, options = options_ )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    return {
        'location': str( accessor ),
        'mimetype': result.mimetype,
        'charset': result.charset,
        'bytes_count': result.bytes_count,
    }
