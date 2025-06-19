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

# TODO: Move immutability machinery to separate package.


import enum
import io
import re

from abc import (
    ABCMeta as ABCFactory,
    abstractmethod as abstract_member_function,
)
from asyncio import (
    Lock as MutexAsync,
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

from accretive import reclassify_modules # TODO: Replace with immutable.
from accretive.qaliases import (
    AccretiveClass,
    AccretiveDictionary,
    AccretiveModule,
    AccretiveNamespace,
    AccretiveObject,
    AccretiveProducerDictionary,
)

from . import _annotations as a
from . import _generics as g

# TODO: Python 3.12: Use type statement for aliases.
ClassDecorators: a.TypeAlias = AbstractIterable[ a.Callable[ [ type ], type ] ]
NominativeArgumentsDictionary: a.TypeAlias = AbstractDictionary[ str, a.Any ]
TextComparand: a.TypeAlias = str | re.Pattern
TextComparands: a.TypeAlias = AbstractIterable[ TextComparand ]


_immutability_label = 'immutability'


class ImmutableClass( type ):
    ''' Prevents mutation of class attributes. '''

    def __new__(
        factory, name, bases, namespace, *,
        class_decorators: ClassDecorators = ( ),
        **args
    ):
        class_ = super( ).__new__( factory, name, bases, namespace, **args )
        return _immutable_class__new__(
            class_, class_decorators = class_decorators )

    def __init__( selfclass, *posargs, **nomargs ):
        super( ).__init__( *posargs, **nomargs )
        _immutable_class__init__( selfclass )

    def __delattr__( selfclass, name: str ):
        if not _immutable_class__delattr__( selfclass, name ):
            super( ).__delattr__( name )

    def __setattr__( selfclass, name: str, value: a.Any ):
        if not _immutable_class__setattr__( selfclass, name ):
            super( ).__setattr__( name, value )


class ImmutableProtocolClass( a.Protocol.__class__ ):
    ''' Prevents mutation of protocol class attributes. '''

    def __new__(
        factory, name, bases, namespace, *,
        class_decorators: ClassDecorators = ( ),
        **args
    ):
        class_ = super( ).__new__( factory, name, bases, namespace, **args )
        return _immutable_class__new__(
            class_, class_decorators = class_decorators )

    def __init__( selfclass, *posargs, **nomargs ):
        super( ).__init__( *posargs, **nomargs )
        _immutable_class__init__( selfclass )

    def __delattr__( selfclass, name: str ):
        if not _immutable_class__delattr__( selfclass, name ):
            super( ).__delattr__( name )

    def __setattr__( selfclass, name: str, value: a.Any ):
        if not _immutable_class__setattr__( selfclass, name ):
            super( ).__setattr__( name, value )


def _immutable_class__new__(
    original: type,
    class_decorators: ClassDecorators = ( ),
    # TODO: mutable_class_attributes
) -> type:
    # Some decorators create new classes, which invokes this method again.
    # Short-circuit to prevent recursive decoration and other tangles.
    class_decorators_ = original.__dict__.get( '_class_decorators_', [ ] )
    if class_decorators_: return original
    setattr( original, '_class_decorators_', class_decorators_ )
    reproduction = original
    for decorator in class_decorators:
        class_decorators_.append( decorator )
        reproduction = decorator( original )
        if original is not reproduction:
            _repair_class_reproduction( original, reproduction )
        original = reproduction
    class_decorators_.clear( ) # Flag '__init__' to enable immutability.
    return reproduction


def _immutable_class__init__( class_: type ):
    if class_.__dict__.get( '_class_decorators_' ): return
    # Some metaclasses add class attributes in '__init__' method.
    # So, we wait until last possible moment to set immutability.
    del class_._class_decorators_
    if ( class_behaviors := class_.__dict__.get( '_class_behaviors_' ) ):
        class_behaviors.add( _immutability_label )
    # TODO: accretive set
    else: setattr( class_, '_class_behaviors_', { _immutability_label } )


def _immutable_class__delattr__( class_: type, name: str ) -> bool:
    # Consult class attributes dictionary to ignore immutable base classes.
    if _immutability_label not in class_.__dict__.get(
        '_class_behaviors_', ( )
    ): return False
    raise AttributeError(
        "Cannot delete attribute {name!r} "
        "on class {class_fqname!r}.".format(
            name = name,
            class_fqname = calculate_class_fqname( class_ ) ) )


def _immutable_class__setattr__( class_: type, name: str ) -> bool:
    # Consult class attributes dictionary to ignore immutable base classes.
    if _immutability_label not in class_.__dict__.get(
        '_class_behaviors_', ( )
    ): return False
    raise AttributeError(
        "Cannot assign attribute {name!r} "
        "on class {class_fqname!r}.".format(
            name = name,
            class_fqname = calculate_class_fqname( class_ ) ) )


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
#       Our 'Optional' indicates that a value binding may be *absent*.
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


def calculate_class_fqname( class_: type ) -> str:
    ''' Calculates fully-qualified name for class. '''
    return f"{class_.__module__}.{class_.__qualname__}"


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
