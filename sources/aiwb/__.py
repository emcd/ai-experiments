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
# pylint: disable=unused-import


import enum
import io
import re

from abc import (
    ABCMeta as ABCFactory,
    abstractmethod as abstract_member_function,
)
from collections import namedtuple # TODO: Replace with dataclass.
from collections.abc import (
    Awaitable as        AbstractAwaitable,
    Collection as       AbstractCollection,
    Coroutine as        AbstractCoroutine,
    Mapping as          AbstractDictionary,
    Iterable as         AbstractIterable,
    AsyncIterable as    AbstractIterableAsync,
    MutableMapping as   AbstractMutableDictionary,
    MutableSequence as  AbstractMutableSequence,
    Sequence as         AbstractSequence,
)
from contextlib import (
    ExitStack as            Exits,
    AsyncExitStack as       ExitsAsync,
    contextmanager as       exit_manager,
    asynccontextmanager as  exit_manager_async,
)
from dataclasses import (
    dataclass,
    field as dataclass_declare,
)
from datetime import (
    datetime as DateTime,
    timedelta as TimeDelta,
    timezone as TimeZone,
)
from enum import Enum, auto as produce_enumeration_value
from functools import (
    cache as memoize,
    partial as partial_function,
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
from types import (
    MappingProxyType as DictionaryProxy,
    ModuleType as Module,
    SimpleNamespace,
)
from urllib.parse import urlparse
from uuid import uuid4

import tyro

from accretive import reclassify_modules
from accretive.qaliases import (
    AccretiveClass,
    AccretiveDictionary,
    AccretiveModule,
    AccretiveNamespace,
    AccretiveObject,
)

from . import _annotations as a
from . import _generics as g


def calculate_class_fqname( class_: type ) -> str:
    ''' Calculates fully-qualified name for class. '''
    return f"{class_.__module__}.{class_.__qualname__}"


_dataclass_mutable_attributes = frozenset( (
    '__dataclass_fields__', '__dataclass_params__',
    '__delattr__', '__setattr__',
    '__doc__',
    '__eq__',
    '__getstate__', '__setstate__',
    '__hash__',
    '__init__',
    '__match_args__',
    '__qualname__',
    '__repr__',
    '__slots__',
) )
_protocol_class_mutable_attributes = frozenset( (
    '__abstractmethods__',
    '__init__',
    '__non_callable_proto_members__',
    '__parameters__',
    '__protocol_attrs__',
    '__subclasshook__',
    '_abc_impl',
    '_is_protocol',
    '_is_runtime_protocol',
) )
_protocol_dataclass_mutable_attributes = (
    _dataclass_mutable_attributes | _protocol_class_mutable_attributes )


class ImmutableClass( type ):
    ''' Prevents mutation of class attributes. '''

    def __delattr__( selfclass, name: str ):
        raise AttributeError(
            "Cannot delete attribute {name!r} "
            "on class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( selfclass ) ) )

    def __setattr__( selfclass, name: str, value: a.Any ):
        raise AttributeError(
            "Cannot assign attribute {name!r} "
            "on class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( selfclass ) ) )


class ImmutableDataclass( type ):
    ''' Prevents mutation of dataclass attributes. '''

    def __delattr__( selfclass, name: str ):
        raise AttributeError(
            "Cannot delete attribute {name!r} "
            "on class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( selfclass ) ) )

    def __setattr__( selfclass, name: str, value: a.Any ):
        # Note: Unfortunately, there are no good indicators for when dataclass
        #       preparation is complete. Therefore, we must allow certain
        #       mutations throughout class lifetime.
        if name not in _dataclass_mutable_attributes:
            raise AttributeError(
                "Cannot assign attribute {name!r} "
                "on class {class_fqname!r}.".format(
                    name = name,
                    class_fqname = calculate_class_fqname( selfclass ) ) )
        super( ).__setattr__( name, value )


class ImmutableProtocolClass( a.Protocol.__class__ ):
    ''' Prevents mutation of protocol class factory attributes. '''

    def __delattr__( selfclass, name: str ):
        raise AttributeError(
            "Cannot delete attribute {name!r} "
            "on class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( selfclass ) ) )

    def __setattr__( selfclass, name: str, value: a.Any ):
        # Note: Unfortunately, there are no good indicators for when protocol
        #       class preparation is complete. Therefore, we must allow certain
        #       mutations throughout class lifetime.
        if name not in _protocol_class_mutable_attributes:
            raise AttributeError(
                "Cannot assign attribute {name!r} "
                "on class {class_fqname!r}.".format(
                    name = name,
                    class_fqname = calculate_class_fqname( selfclass ) ) )
        super( ).__setattr__( name, value )


class ImmutableProtocolDataclass( a.Protocol.__class__ ):
    ''' Prevents mutation of protocol dataclass attributes. '''

    def __delattr__( selfclass, name: str ):
        raise AttributeError(
            "Cannot delete attribute {name!r} "
            "on class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( selfclass ) ) )

    def __setattr__( selfclass, name: str, value: a.Any ):
        # Note: Unfortunately, there are no good indicators for when dataclass
        #       or protocol class preparation is complete. Therefore, we must
        #       allow certain mutations throughout class lifetime.
        if name not in _protocol_dataclass_mutable_attributes:
            raise AttributeError(
                "Cannot assign attribute {name!r} "
                "on class {class_fqname!r}.".format(
                    name = name,
                    class_fqname = calculate_class_fqname( selfclass ) ) )
        super( ).__setattr__( name, value )


class ImmutableObject( metaclass = ImmutableClass ):
    ''' Prevents mutation of object attributes. '''

    def __delattr__( self, name ):
        raise AttributeError(
            "Cannot delete attribute {name!r} on instance "
            "of class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( type( self ) ) ) )

    def __setattr__( self, name, value ):
        raise AttributeError(
            "Cannot assign attribute {name!r} on instance "
            "of class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( type( self ) ) ) )


class ImmutableProtocol( a.Protocol, metaclass = ImmutableProtocolClass ):
    ''' Prevents mutation of protocol object attributes. '''

    def __delattr__( self, name ):
        raise AttributeError(
            "Cannot delete attribute {name!r} on instance "
            "of class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( type( self ) ) ) )

    def __setattr__( self, name, value ):
        raise AttributeError(
            "Cannot assign attribute {name!r} on instance "
            "of class {class_fqname!r}.".format(
                name = name,
                class_fqname = calculate_class_fqname( type( self ) ) ) )


class Falsifier( metaclass = ImmutableClass ): # pylint: disable=eq-without-hash
    ''' Produces falsey objects.

        :py:class:`object` produces truthy objects.
        :py:class:`types.NoneType` "produces" falsey ``None`` singleton.
        :py:class:`typing.NoDefault` is truthy singleton.
    '''

    def __bool__( self ): return False

    def __eq__( self, other ): return self is other

    def __ne__( self, other ): return self is not other


class Absent( Falsifier, ImmutableObject ):
    ''' Type of the sentinel for option without default value. '''

    def __new__( selfclass ):
        ''' Singleton. '''
        absent_ = globals( ).get( 'absent' )
        if isinstance( absent_, selfclass ): return absent_
        return super( ).__new__( selfclass )


# TODO: Python 3.12: Use type statement for aliases.
# NOTE: Nullability and optionality are NOT the same thing.
#       We have aliased 'typing.Optional' to 'Nullable'.
#       The 'Optional' defined below is NOT the same as 'typing.Optional'!
#       Our 'Optional' indicates that a value binding may be ABSENT.
#       Similar in spirit to the 'typing.NoDefault' sentinel, we have an
#       'absent' sentinel which is a singleton instance of 'Absent'. This is
#       useful when 'None' may be a legitimate value for an argument and we
#       need another way to indicate that no value is being passed instead.
#       Undoubtedly, this name is confusing, but it seems to best describe the
#       semantics that we are trying to convey. Assuming that the "<type> |
#       None" idiom becomes more popular with adoption of Python 3.10+, the
#       nomenclatural confusion will hopefully lessen over time as
#       'typing.Optional' disappears from common Python use.
Optional: a.TypeAlias = g.T | Absent
PossiblePath: a.TypeAlias = bytes | str | PathLike


absent: a.Annotation[
    Absent, a.Doc( ''' Sentinel for option with no default value. ''' )
] = Absent( )
package_name = __package__.split( '.', maxsplit = 1 )[ 0 ]
standard_dataclass = dataclass( frozen = True, kw_only = True, slots = True )
# Note: @dataclass decorator replaces classes when slots = True
#       In CPython, this breaks association with the class cell variable
#       used by super( ), etc... and messes with inheritance if you make super
#       calls that have explicit arguments. So, we have to settle for something
#       substandard when inheriting data classes with super call methods.
# TODO: Python 3.14: Replace substandard dataclass with standard dataclass.
#       https://github.com/python/cpython/issues/90562
#       https://github.com/python/cpython/pull/124455/files
substandard_dataclass = dataclass( frozen = True, kw_only = True )


async def chain_async( *iterables: AbstractIterable | AbstractIterableAsync ):
    ''' Chains items from iterables in sequence and asynchronously. '''
    for iterable in iterables:
        if isinstance( iterable, AbstractIterableAsync ):
            async for item in iterable: yield item
        else:
            for item in iterable: yield item


def exception_to_str( exception: BaseException ) -> str:
    ''' Produces string representation of exception with type. '''
    return "[{class_name}] {message}".format(
        class_name = calculate_class_fqname( type( exception ) ),
        message = str( exception ) )


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


async def read_files_async(
    *files: PathLike,
    deserializer: a.Callable[ [ str ], a.Any ] = None,
    return_exceptions: bool = False
) -> AbstractSequence:
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
    async with ExitsAsync( ) as exits:
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
