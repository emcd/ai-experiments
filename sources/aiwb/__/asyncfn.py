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


async def chain_async(
    *iterables: (
        __.cabc.Iterable[ __.typx.Any ]
        | __.cabc.AsyncIterable[ __.typx.Any ] )
) -> __.cabc.AsyncIterator[ __.typx.Any ]:
    ''' Chains items from iterables in sequence and asynchronously. '''
    for iterable in iterables:
        if isinstance( iterable, __.cabc.AsyncIterable ):
            async for item in iterable: yield item
        else:
            for item in iterable: yield item


def _make_processors_with_exceptions(
    deserializer: __.typx.Optional[
        __.typx.Callable[ [ str ], __.typx.Any ] ]
) -> tuple[
    __.typx.Callable[ [ __.typx.Any ], __.typx.Any ],
    __.typx.Callable[ [ __.typx.Any ], __.typx.Any ],
]:
    ''' Creates extractor and transformer for exception-wrapped results. '''
    def extractor( result: __.typx.Any ) -> __.typx.Any:
        return (
            result.extract( ).read( )
            if result.is_value( ) else result )
    def transformer( result: __.typx.Any ) -> __.typx.Any:
        return result.transform( deserializer )
    return extractor, transformer


def _make_processors_normal(
    deserializer: __.typx.Optional[
        __.typx.Callable[ [ str ], __.typx.Any ] ]
) -> tuple[
    __.typx.Callable[
        [ __.typx.Any ], __.cabc.Coroutine[ __.typx.Any, __.typx.Any, str ]
    ],
    __.typx.Callable[ [ __.typx.Any ], __.typx.Any ],
]:
    ''' Creates extractor and transformer for normal results. '''
    def extractor(
        stream: __.typx.Any
    ) -> __.cabc.Coroutine[ __.typx.Any, __.typx.Any, str ]:
        return stream.read( )
    def transformer( datum: __.typx.Any ) -> __.typx.Any:
        # Transformer only called when deserializer is not None.
        return __.typx.cast(
            __.typx.Callable[ [ str ], __.typx.Any ], deserializer
        )( datum )
    return extractor, transformer


async def read_files_async(
    *files: __.PathLike[ str ],
    deserializer: __.typx.Optional[
        __.typx.Callable[ [ str ], __.typx.Any ] ] = None,
    return_exceptions: bool = False
) -> __.cabc.Sequence[ __.typx.Any ]:
    ''' Reads files asynchronously. '''
    # TODO? Batch to prevent fd exhaustion over large file sets.
    from aiofiles import open as open_
    extractor, transformer = (
        _make_processors_with_exceptions( deserializer )
        if return_exceptions
        else _make_processors_normal( deserializer ) )
    async with __.ctxl.AsyncExitStack( ) as exits:
        streams = await __.asyncf.gather_async(
            *(  exits.enter_async_context( open_( file ) )
                for file in files ),
            return_exceptions = return_exceptions )
        data = await __.asyncf.gather_async(
            *( extractor( stream ) for stream in streams ),
            return_exceptions = return_exceptions,
            ignore_nonawaitables = return_exceptions )
    if deserializer:
        return tuple( transformer( datum ) for datum in data )
    return data
