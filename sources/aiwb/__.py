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
import                          sys
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
import                      appcore
import                      appcore.dictedits
import frigid as            immut
import typing_extensions as typx
import                      tyro

from absence import Absential, absent, is_absent
from appcore import asyncf, generics


ClassDecorators: typx.TypeAlias = (
    cabc.Iterable[ typx.Callable[ [ type ], type ] ] )
NominativeArguments: typx.TypeAlias = cabc.Mapping[ str, typx.Any ]
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
        streams = await asyncf.gather_async(
            *(  exits.enter_async_context( open_( file ) )
                for file in files ),
            return_exceptions = return_exceptions )
        data = await asyncf.gather_async(
            *( extractor( stream ) for stream in streams ),
            return_exceptions = return_exceptions,
            ignore_nonawaitables = return_exceptions )
    if deserializer: return tuple( transformer( datum ) for datum in data )
    return data
