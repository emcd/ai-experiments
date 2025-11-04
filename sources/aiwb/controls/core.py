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


''' Core classes for controls. '''


from . import __
from . import exceptions as _exceptions


class DefinitionBase( metaclass = __.abc.ABCMeta ):
    # TODO: Protocol class.

    class Instance:
        # TODO: Protocol class.

        def __init__( self, definition, value ):
            self.definition = definition
            self.value = value

        @property
        def value( self ): return self._value

        @value.setter
        def value( self, value_ ):
            self._value = self.definition.validate_value( value_ )

        def serialize( self ): return self.value

    @classmethod
    def instantiate_descriptor( class_, descriptor ):
        nomargs = descriptor.copy( )
        nomargs[ 'attributes' ] = __.types.SimpleNamespace(
            **( nomargs.get( 'attributes', { } ) ) )
        if 'default' not in nomargs:
            nomargs[ 'default' ] = class_.produce_default( descriptor )
        return class_( **nomargs )

    @classmethod
    @__.abc.abstractmethod
    def produce_default( class_, descriptor ):
        raise NotImplementedError # TODO: Fill out error.

    def __init__( self, name, default, attributes ):
        self.name = name # TODO: Validate.
        self.default = self.validate_value( default )
        self.attributes = attributes # TODO: Validate.

    def create_control( self, value ):
        return self.Instance( self, value )

    def create_control_default( self ):
        return self.Instance( self, self.default )

    def deserialize( self, data ):
        return self.create_control( data )

    @__.abc.abstractmethod
    def validate_value( self, value ):
        raise NotImplementedError # TODO: Fill out error.


class Boolean( DefinitionBase ):

    class Instance( DefinitionBase.Instance ): pass

    @classmethod
    def produce_default( class_, descriptor ): return False

    def validate_value( self, value ):
        if not isinstance( value, bool ):
            raise _exceptions.ControlValueMisclassification(
                self.name, 'bool', value )
        return value


class DiscreteInterval( DefinitionBase ):

    class Instance( DefinitionBase.Instance ): pass

    @classmethod
    def produce_default( class_, descriptor ):
        default = descriptor.get( 'default' )
        return descriptor[ 'minimum' ] if None is default else default

    def __init__( self, name, minimum, maximum, grade, **nomargs ):
        self.minimum = minimum
        self.maximum = maximum
        self.grade = grade
        super( ).__init__( name, **nomargs )

    def validate_value( self, value ):
        # NOTE: Might be too strict, if GUI controls accept floating-points.
        from numbers import Rational
        if not isinstance( value, Rational ):
            raise _exceptions.ControlValueMisclassification(
                self.name, 'Rational', value )
        if not ( self.minimum <= value <= self.maximum ):
            raise _exceptions.ControlValueConstraintViolation(
                self.name, value, self.minimum, self.maximum )
        # TODO: Ensure exact placement on discrete spectrum.
        return value


class FlexArray( DefinitionBase ):

    class Instance( DefinitionBase.Instance ):

        def __init__( self, definition, value ):
            subvalues = value
            if definition.maximum and definition.maximum < len( subvalues ):
                raise _exceptions.ControlArrayDimensionViolation(
                    definition.name, len( subvalues ), definition.maximum )
            element_definition = definition.element_definition
            elements = [
                element_definition.create_control( subvalue )
                for subvalue in subvalues ]
            super( ).__init__( definition, elements )

        def __iter__( self ): return iter( self.value )

        def __len__( self ): return len( self.value )

        def append( self, value ):
            definition = self.definition
            elements = self.value
            element_definition = definition.element_definition
            elements_count = len( elements )
            if definition.maximum and definition.maximum <= elements_count:
                raise _exceptions.ControlArrayCapacityViolation(
                    definition.name, elements_count, definition.maximum )
            elements.append( element_definition.create_control( value ) )
            return self

        def pop( self, index = -1 ):
            elements = self.value
            return elements.pop( index = index )

        def serialize( self ):
            elements = self.value
            return tuple( element.serialize( ) for element in elements )

    @classmethod
    def instantiate_descriptor( class_, descriptor ):
        descriptor_ = descriptor.copy( )
        element_descriptor = descriptor_.pop( 'element' ).copy( )
        if 'name' not in element_descriptor:
            element_descriptor[ 'name' ] = descriptor[ 'name' ]
        element_class = _species_to_class(
            element_descriptor.pop( 'species' ) )
        descriptor_[ 'element_definition' ] = (
            element_class.instantiate_descriptor( element_descriptor ) )
        return super( ).instantiate_descriptor( descriptor_ )

    @classmethod
    def produce_default( class_, descriptor ): return ( )

    def __init__(
        self, name, element_definition, minimum = 1, maximum = None, **nomargs
    ):
        self.element_definition = element_definition
        self.minimum = minimum
        if maximum and minimum > maximum:
            raise _exceptions.ControlArrayDefinitionInvalidity(
                name, f"minimum ({minimum}) > maximum ({maximum})" )
        self.maximum = maximum
        nomargs[ 'default' ] = [
            element_definition.create_control( value )
            for value in nomargs.pop( 'default' ) ]
        super( ).__init__( name, **nomargs )

    def create_control_default( self ):
        subvalues = tuple(
            element.serialize( ) for element in self.default )
        return self.Instance( self, subvalues )

    def deserialize( self, data ):
        return [
            self.element_definition.deserialize( subdata )
            for subdata in data ]

    def validate_value( self, value ):
        elements = value
        element_class = self.element_definition.Instance
        if not isinstance( elements, __.cabc.Sequence ):
            raise _exceptions.ControlValueMisclassification(
                self.name, 'Sequence', elements )
        for element in elements:
            if not isinstance( element, element_class ):
                raise _exceptions.ControlElementMisclassification(
                    self.name, element_class.__qualname__, element )
        return elements


class Options( DefinitionBase ):

    class Instance( DefinitionBase.Instance ): pass

    @classmethod
    def produce_default( class_, descriptor ):
        if 'default' in descriptor: return descriptor[ 'default' ]
        return next( iter( descriptor[ 'options' ] ) )

    def __init__( self, name, options, **nomargs ):
        if not isinstance( options, __.cabc.Collection ):
            raise _exceptions.ControlValueMisclassification(
                name, 'Collection', options )
        self.options = options
        super( ).__init__( name, **nomargs )

    def validate_value( self, value ):
        if value not in self.options:
            raise _exceptions.ControlOptionValueInvalidity(
                self.name, value, self.options )
        return value


class Text( DefinitionBase ):

    class Instance( DefinitionBase.Instance ): pass

    @classmethod
    def produce_default( class_, descriptor ): return ''

    def validate_value( self, value ):
        if not isinstance( value, str ):
            raise _exceptions.ControlValueMisclassification(
                self.name, 'str', value )
        return value


# TODO: Python 3.12: Use type statement for aliases.
ControlsInstancesByName: __.typx.TypeAlias = (
    __.cabc.Mapping[ str, DefinitionBase.Instance ] )


def descriptor_to_definition( descriptor ):
    descriptor_ = descriptor.copy( )
    class_ = _species_to_class( descriptor_.pop( 'species' ) )
    return class_.instantiate_descriptor( descriptor_ )


def deserialize_dictionary( definitions, dictionary ):
    return __.types.MappingProxyType( {
        name: definitions[ name ].deserialize( data )
        for name, data in dictionary.items( ) } )


def serialize_dictionary( controls ):
    return {
        name: control.serialize( ) for name, control in controls.items( ) }


def _species_to_class( name ):
    # TODO: Python 3.10: match statement
    # Could compute class programmatically, but explicit is safer.
    if 'boolean' == name: return Boolean
    if 'discrete-interval' == name: return DiscreteInterval
    if 'flex-array' == name: return FlexArray
    if 'options' == name: return Options
    if 'text' == name: return Text
    raise _exceptions.ControlSpeciesIrrecognizability( name )
