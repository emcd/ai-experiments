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


''' Generic types. '''


from . import _annotations as _a


T = _a.TypeVar( 'T' ) # generic
U = _a.TypeVar( 'U' ) # generic
E = _a.TypeVar( 'E', bound = Exception ) # error


class Result( _a.Generic[ T ] ):
    ''' Either a value or an error. '''
    # TODO: Enforce class and instance immutability.

    def is_error( self ) -> bool:
        ''' Returns ``True`` if error result. Else ``False``. '''
        return isinstance( self, Error )

    def is_value( self ) -> bool:
        ''' Returns ``True`` if value result. Else ``False``. '''
        return isinstance( self, Value )

    def extract( self ) -> T:
        ''' Extracts value from result. Else, raises error from result. '''
        # Like Result.unwrap in Rust.
        if isinstance( self, Value ): return self.value
        raise self.error

    def transform(
        self, function: _a.Callable[ [ T ], U ]
    ) -> _a.Self | "Result[ U ]":
        ''' Transforms value in value result. Ignores error result. '''
        # Like Result.map in Rust.
        if isinstance( self, Value ): return Value( function( self.value ) )
        return self


class Value( Result[ T ] ):
    ''' Result of successful computation. '''

    __match_args__ = ( 'value', )
    __slots__ = ( 'value', )

    value: T

    def __init__( self, value: T ):
        self.value = value


class Error( Result[ T ] ):
    ''' Result of failed computation. '''

    __match_args__ = ( 'error', )
    __slots__ = ( 'error', )

    error: Exception

    def __init__( self, error: Exception ):
        self.error = error
