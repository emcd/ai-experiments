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


''' Exception classes for controls. '''


from . import __


class ControlArrayCapacityViolation( __.Omnierror, RuntimeError ):
    ''' Attempt to exceed control array capacity. '''

    def __init__(
        self, control_name, current_size, maximum, operation = 'add'
    ):
        super( ).__init__(
            f"Cannot {operation} to array '{control_name}': "
            f"current size {current_size}, maximum {maximum}." )


class ControlArrayDefinitionInvalidity( __.Omnierror, ValueError ):
    ''' Control array definition is invalid. '''

    def __init__( self, control_name, reason ):
        super( ).__init__(
            f"Array definition '{control_name}' is invalid: {reason}." )


class ControlArrayDimensionViolation( __.Omnierror, ValueError ):
    ''' Control array size exceeds limits. '''

    def __init__( self, control_name, size, maximum ):
        super( ).__init__(
            f"Array '{control_name}' has {size} elements, "
            f"exceeds maximum of {maximum}." )


class ControlElementMisclassification( __.Omnierror, TypeError ):
    ''' Control array element has invalid type. '''

    def __init__( self, control_name, expected_class, received_element ):
        received_class = type( received_element ).__qualname__
        super( ).__init__(
            f"Array '{control_name}' expects elements of type "
            f"'{expected_class}', received {received_class}: "
            f"{received_element!r}." )


class ControlOptionValueInvalidity( __.Omnierror, ValueError ):
    ''' Control value not in available options. '''

    def __init__( self, control_name, value, options ):
        options_str = ', '.join( repr( opt ) for opt in options )
        super( ).__init__(
            f"Value {value!r} for control '{control_name}' not in "
            f"available options: {options_str}." )


class ControlSpeciesIrrecognizability( __.Omnierror, ValueError ):
    ''' Unknown control species name. '''

    def __init__( self, species_name ):
        super( ).__init__( f"Unknown control species: {species_name!r}." )


class ControlValueConstraintViolation( __.Omnierror, ValueError ):
    ''' Control value outside acceptable range. '''

    def __init__( self, control_name, value, minimum, maximum ):
        super( ).__init__(
            f"Value {value} for control '{control_name}' outside "
            f"range [{minimum}, {maximum}]." )


class ControlValueMisclassification( __.Omnierror, TypeError ):
    ''' Control value has invalid type. '''

    def __init__( self, control_name, expected_type, received_value ):
        received_type = type( received_value ).__qualname__
        super( ).__init__(
            f"Control '{control_name}' expects {expected_type}, "
            f"received {received_type}: {received_value!r}." )
