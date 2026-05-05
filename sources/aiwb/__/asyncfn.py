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


''' Async helpers. '''


from . import imports as __


async def chain_async( *iterables: __.cabc.Iterable | __.cabc.AsyncIterable ):
    ''' Chains items from iterables in sequence and asynchronously. '''
    for iterable in iterables:
        if isinstance( iterable, __.cabc.AsyncIterable ):
            async for item in iterable: yield item
        else:
            for item in iterable: yield item


async def read_files_async(
    *files: __.PathLike,
    deserializer: __.typx.Optional[
        __.typx.Callable[ [ str ], __.typx.Any ] ] = None,
    return_exceptions: bool = False
) -> __.cabc.Sequence:
    ''' Reads files asynchronously. '''
    # TODO? Batch to prevent fd exhaustion over large file sets.
    from aiofiles import open as open_
    if return_exceptions:
        extractor = _extract_result_stream
        transformer = _transform_result
    else:
        extractor = _extract_stream
        transformer = _transform_datum
    async with __.ctxl.AsyncExitStack( ) as exits:
        streams = await __.asyncf.gather_async(
            *(  exits.enter_async_context( open_( file ) )
                for file in files ),
            return_exceptions = return_exceptions )
        data = await __.asyncf.gather_async(
            *( extractor( stream ) for stream in streams ),
            return_exceptions = return_exceptions,
            ignore_nonawaitables = return_exceptions )
    if deserializer is not None:
        return _transform_data(
            data, transformer = transformer, deserializer = deserializer )
    return data


def _extract_result_stream( result: __.typx.Any ) -> __.typx.Any:
    ''' Extracts stream read coroutine from result wrapper. '''
    return result.extract( ).read( ) if result.is_value( ) else result


def _extract_stream( stream: __.typx.Any ) -> __.typx.Any:
    ''' Extracts stream read coroutine. '''
    return stream.read( )


def _transform_datum(
    datum: __.typx.Any, *,
    deserializer: __.typx.Callable[ [ str ], __.typx.Any ],
) -> __.typx.Any:
    ''' Transforms datum with deserializer. '''
    return deserializer( datum )


def _transform_data(
    data: __.cabc.Iterable[ __.typx.Any ], *,
    transformer: __.cabc.Callable[ ..., __.typx.Any ],
    deserializer: __.typx.Callable[ [ str ], __.typx.Any ],
) -> tuple[ __.typx.Any, ... ]:
    ''' Transforms data with deserializer. '''
    return tuple(
        transformer( datum, deserializer = deserializer ) for datum in data )


def _transform_result(
    result: __.typx.Any, *,
    deserializer: __.typx.Callable[ [ str ], __.typx.Any ],
) -> __.typx.Any:
    ''' Transforms result wrapper with deserializer. '''
    return result.transform( deserializer )
