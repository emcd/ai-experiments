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


''' Base functionality to support AI workbench. '''


import enum

from abc import (
    ABCMeta as ABCFactory,
    abstractmethod as abstract_member_function,
)
from collections import namedtuple # TODO: Replace with dataclass.
from collections.abc import (
    Awaitable as AbstractAwaitable,
    Collection as AbstractCollection,
    Iterable as AbstractIterable,
    Mapping as AbstractDictionary,
    MutableMapping as AbstractMutableDictionary,
    MutableSequence as AbstractMutableSequence,
    Sequence as AbstractSequence,
)
from contextlib import (
    ExitStack as Contexts,
    contextmanager as produce_context_manager,
)
from dataclasses import (
    InitVar,
    dataclass,
    field as dataclass_declare,
)
from datetime import (
    datetime as DateTime,
    timedelta as TimeDelta,
    timezone as TimeZone,
)
from enum import Enum
from functools import (
    cache as memoize,
    partial as partial_function,
)
from logging import (
    Logger as Scribe,
    getLogger as acquire_scribe,
)
from os import PathLike
from pathlib import Path
from queue import SimpleQueue
from time import time_ns
from types import (
    MappingProxyType as DictionaryProxy,
    ModuleType as Module,
    SimpleNamespace,
)
from urllib.parse import (
    ParseResult as UrlParts,
    urlparse,
)
from uuid import uuid4

from accretive.qaliases import AccretiveDictionary, AccretiveNamespace
from platformdirs import PlatformDirs

from . import _annotations as a
from . import _generics as g


# TODO: Use accretive validator dictionary for URL accessor registry.
#    def register(
#        scheme: str,
#        accessor_factory: a.Callable[ [ UrlParts ], Location ]
#    ):
#        ''' Associates location accessor factory to URL scheme. '''
#        registry[ scheme ] = accessor_factory
url_accessors = AccretiveDictionary( )

def _convert_file_url_to_location( parts: UrlParts ) -> Path:
    if '.' == parts.netloc: return Path( ) / parts.path
    if parts.netloc:
        raise NotImplementedError(
            f"Shares not supported in file URLs. URL: {url}" )
    return Path( parts.path )

url_accessors[ '' ] = _convert_file_url_to_location
url_accessors[ 'file' ] = _convert_file_url_to_location


class Location( metaclass = ABCFactory ):
    ''' Dynamically-registered superclass for location types. '''
    # Note: Not a Protocol class because there is no common protocol.
    #       We just want issubclass support.

Location.register( Path )


async def gather_async(
    *operands: a.Any,
    return_exceptions: a.Annotation[
        bool,
        a.Doc( ''' Raw or wrapped results. Wrapped, if true. ''' )
    ] = False,
    error_message: str = 'Failure of async operations.',
    ignore_nonawaitables: a.Annotation[
        bool,
        a.Doc( ''' Ignore or error on non-awaitables. Ignore, if true. ''' )
    ] = False,
) -> AbstractSequence:
    ''' Gathers results from invocables concurrently and asynchronously. '''
    from exceptiongroup import ExceptionGroup # TODO: Python 3.11: builtin
    if ignore_nonawaitables:
        results = await _gather_async_permissive( operands )
    else:
        results = await _gather_async_strict( operands )
    if return_exceptions: return results
    errors = tuple( result.error for result in results if result.is_error( ) )
    if errors: raise ExceptionGroup( error_message, errors )
    return tuple( result.extract( ) for result in results )


async def intercept_error_async( awaitable: AbstractAwaitable ) -> g.Result:
    ''' Converts unwinding exceptions to error results.

        Exceptions, which are not instances of :py:exc:`Exception` or one of
        its subclasses, are allowed to propagate. In particular,
        :py:exc:`KeyboardInterrupt` and :py:exc:`SystemExit` must be allowed
        to propagate to be consistent with :py:class:`asyncio.TaskGroup`
        behavior.

        Helpful when working with :py:func:`asyncio.gather`, for example,
        because exceptions can be distinguished from computed values
        and collected together into an exception group.

        In general, it is a bad idea to swallow exceptions. In this case,
        the intent is to add them into an exception group for continued
        propagation.
    '''
    try: return g.Value( await awaitable )
    except Exception as exc: return g.Error( exc )


def parse_url( url: str ) -> Location:
    ''' Parses URL and creates an appropriate accessor for location. '''
    from urllib.parse import urlparse
    parts = urlparse( url )
    scheme = parts.scheme
    if scheme in url_accessors:
        location = url_accessors[ scheme ]( parts )
    else:
        raise NotImplementedError(
            f"URL scheme {scheme!r} not supported. URL: {url}" )
    # Cast because we do not have a common protocol.
    return a.cast( Location, location )


async def read_files_async(
    *files: PathLike,
    deserializer: a.Callable[ [ str ], a.Any ] = None,
    return_exceptions: bool = False
) -> AbstractSequence:
    ''' Reads files asynchronously. '''
    # TODO? Batch to prevent fd exhaustion over large file sets.
    from contextlib import AsyncExitStack
    from aiofiles import open as open_
    if return_exceptions:
        def extractor( result ):
            return result.extract( ).read( ) if result.is_value( ) else result
        def transformer( result ):
            return result.transform( deserializer )
    else:
        def extractor( stream ): return stream.read( )
        def transformer( datum ): return deserializer( datum )
    async with AsyncExitStack( ) as contexts:
        streams = await gather_async(
            *(  contexts.enter_async_context( open_( file ) )
                for file in files ),
            return_exceptions = return_exceptions )
        data = await gather_async(
            *( extractor( stream ) for stream in streams ),
            return_exceptions = return_exceptions,
            ignore_nonawaitables = return_exceptions )
    if deserializer: return tuple( transformer( datum ) for datum in data )
    return data


async def _gather_async_permissive(
    operands: a.Any
) -> AbstractSequence:
    from asyncio import gather # TODO? Python 3.11: TaskGroup
    awaitables = { }
    for i, operand in enumerate( operands ):
        if isinstance( operand, AbstractAwaitable ):
            awaitables[ i ] = intercept_error_async( operand )
    results_ = await gather( *awaitables.values( ) )
    results = list( operands )
    for i, result in zip( awaitables.keys( ), results_ ):
        results[ i ] = result
    return results


async def _gather_async_strict(
    operands: a.Any
) -> AbstractSequence:
    from asyncio import gather # TODO? Python 3.11: TaskGroup
    awaitables = [ ]
    for operand in operands:
        if not isinstance( operand, AbstractAwaitable ):
            raise ValueError( f"Operand {operand!r} must be awaitable." )
        awaitables.append( intercept_error_async( operand ) )
    return await gather( *awaitables )
