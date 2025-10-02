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


''' Package internal names. '''


from . import imports as __


ClassDecorators: __.typx.TypeAlias = (
    __.cabc.Iterable[ __.typx.Callable[ [ type ], type ] ] )
NominativeArguments: __.typx.TypeAlias = __.cabc.Mapping[ str, __.typx.Any ]
TextComparand: __.typx.TypeAlias = str | __.re.Pattern
TextComparands: __.typx.TypeAlias = __.cabc.Iterable[ TextComparand ]


_immutability_label = 'immutability'


PossiblePath: __.typx.TypeAlias = bytes | str | __.PathLike


package_name = __name__.split( '.', maxsplit = 1 )[ 0 ]


def calculate_class_fqname( class_: type ) -> str:
    ''' Calculates fully-qualified name for class. '''
    return f"{class_.__module__}.{class_.__qualname__}"


def exception_to_str( exception: BaseException ) -> str:
    ''' Produces string representation of exception with type. '''
    return "[{class_name}] {message}".format(
        class_name = calculate_class_fqname( type( exception ) ),
        message = str( exception ) )
