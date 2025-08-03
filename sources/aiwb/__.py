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

# ruff: noqa: F401

import                          abc
import                          asyncio
import collections.abc as       cabc
import contextlib as            ctxl
import dataclasses as           dcls
import                          enum
import functools as             funct
import                          io
import itertools as             itert
import                          os
import                          re
import                          types

from asyncio import (
    Lock as MutexAsync,
)
from collections import namedtuple # TODO: Replace with dataclass.
from datetime import (
    datetime as DateTime,
    timedelta as TimeDelta,
    timezone as TimeZone,
)
from enum import Enum
from itertools import chain
from logging import (
    Logger as Scribe,
    getLogger as acquire_scribe,
)
from os import PathLike
from pathlib import Path
from queue import SimpleQueue
from threading import Thread
from time import time_ns
from urllib.parse import urlparse
from uuid import uuid4

import accretive as         accret
import frigid as            immut
import typing_extensions as typx
import                      tyro

from absence import Absential, absent, is_absent


from . import _generics as g

ClassDecorators: typx.TypeAlias = (
    cabc.Iterable[ typx.Callable[ [ type ], type ] ] )
NominativeArgumentsDictionary: typx.TypeAlias = cabc.Mapping[ str, typx.Any ]
TextComparand: typx.TypeAlias = str | re.Pattern
TextComparands: typx.TypeAlias = cabc.Iterable[ TextComparand ]


_immutability_label = 'immutability'


PossiblePath: typx.TypeAlias = bytes | str | PathLike


package_name = __name__.split( '.', maxsplit = 1 )[ 0 ]


def calculate_class_fqname( class_: type ) -> str:
    ''' Calculates fully-qualified name for class. '''
    return f"{class_.__module__}.{class_.__qualname__}"


async def chain_async( *iterables: cabc.Iterable | cabc.AsyncIterable ):
    ''' Chains items from iterables in sequence and asynchronously. '''
    for iterable in iterables:
        if isinstance( iterable, cabc.AsyncIterable ):
            async for item in iterable: yield item
        else:
            for item in iterable: yield item


def exception_to_str( exception: BaseException ) -> str:
    ''' Produces string representation of exception with type. '''
    return "[{class_name}] {message}".format(
        class_name = calculate_class_fqname( type( exception ) ),
        message = str( exception ) )


async def gather_async(
    *operands: typx.Any,
    return_exceptions: typx.Annotated[
        bool,
        typx.Doc( ''' Raw or wrapped results. Wrapped, if true. ''' )
    ] = False,
    error_message: str = 'Failure of async operations.',
    ignore_nonawaitables: typx.Annotated[
        bool,
        typx.Doc( ''' Ignore or error on non-awaitables. Ignore, if true. ''' )
    ] = False,
) -> cabc.Sequence:
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


async def intercept_error_async( awaitable: cabc.Awaitable ) -> g.Result:
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


async def read_files_async(
    *files: PathLike,
    deserializer: typx.Callable[ [ str ], typx.Any ] = None,
    return_exceptions: bool = False
) -> cabc.Sequence:
    ''' Reads files asynchronously. '''
    # TODO? Batch to prevent fd exhaustion over large file sets.
    from aiofiles import open as open_
    if return_exceptions:
        def extractor( result ):
            return result.extract( ).read( ) if result.is_value( ) else result
        def transformer( result ):
            return result.transform( deserializer )
    else:
        def extractor( stream ): return stream.read( )
        def transformer( datum ): return deserializer( datum )
    async with ctxl.AsyncExitStack( ) as exits:
        streams = await gather_async(
            *(  exits.enter_async_context( open_( file ) )
                for file in files ),
            return_exceptions = return_exceptions )
        data = await gather_async(
            *( extractor( stream ) for stream in streams ),
            return_exceptions = return_exceptions,
            ignore_nonawaitables = return_exceptions )
    if deserializer: return tuple( transformer( datum ) for datum in data )
    return data


async def _gather_async_permissive(
    operands: typx.Any
) -> cabc.Sequence:
    from asyncio import gather # TODO? Python 3.11: TaskGroup
    awaitables = { }
    for i, operand in enumerate( operands ):
        if isinstance( operand, cabc.Awaitable ):
            awaitables[ i ] = intercept_error_async( operand )
    results_ = await gather( *awaitables.values( ) )
    results = list( operands )
    for i, result in zip( awaitables.keys( ), results_ ):
        results[ i ] = result
    return results


async def _gather_async_strict(
    operands: typx.Any
) -> cabc.Sequence:
    from asyncio import gather # TODO? Python 3.11: TaskGroup
    awaitables = [ ]
    for operand in operands:
        if not isinstance( operand, cabc.Awaitable ):
            raise ValueError( f"Operand {operand!r} must be awaitable." )
        awaitables.append( intercept_error_async( operand ) )
    return await gather( *awaitables )


def _repair_class_reproduction( original, reproduction ):
    from platform import python_implementation
    match python_implementation( ):
        case 'CPython':
            _repair_cpython_class_closures( original, reproduction )


def _repair_cpython_class_closures( oldcls, newcls ):
    # https://github.com/python/cpython/issues/90562
    # https://github.com/python/cpython/pull/124455/files
    def try_repair_closure( function ):
        # If no class cell on function, then nothing to repair here.
        try: index = function.__code__.co_freevars.index( '__class__' )
        except ValueError: return False
        closure = function.__closure__[ index ]
        if oldcls is closure.cell_contents:
            closure.cell_contents = newcls
            return True
        return False

    from inspect import isfunction, unwrap
    # Iterate over all class attributes, seeking class closure to fix.
    # Fixing one is fixing all, since the closure cell is shared.
    for attribute in newcls.__dict__.values( ):
        attribute_ = unwrap( attribute )
        if isfunction( attribute_ ) and try_repair_closure( attribute_ ):
            return
        if isinstance( attribute_, property ):
            for aname in ( 'fget', 'fset', 'fdel' ):
                accessor = getattr( attribute_, aname )
                if None is accessor: continue
                if try_repair_closure( accessor ): return
