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


from . import base as __


class DefinitionBase( metaclass = __.ABCFactory ):

    @classmethod
    def instantiate_descriptor( class_, descriptor ):
        nomargs = descriptor.copy( )
        nomargs[ 'attributes' ] = __.SimpleNamespace(
            **( nomargs.get( 'attributes', { } ) ) )
        return class_( **nomargs )

    def __init__( self, name, attributes = None ):
        self.name = name
        self.attributes = attributes or __.SimpleNamespace( )

    def create_control( self, value ):
        return self.Instance( self, value )

    @__.abstract_function
    def validate_value( self, value ):
        raise NotImplementedError # TODO: Fill out error.


class InstanceBase:

    def __init__( self, definition, value ):
        self.definition = definition
        self.value = definition.validate_value( value )


class Boolean( DefinitionBase ):

    class Instance( InstanceBase ): pass

    def __init__( self, name, default = False, **nomargs ):
        self.default = self.validate_value( default )
        super( ).__init__( name, **nomargs )

    def validate_value( self, value ):
        if not isinstance( value, bool ):
            raise ValueError # TODO: Fill out error.
        return value


class DiscreteInterval( DefinitionBase ):

    class Instance( InstanceBase ): pass

    def __init__(
        self, name, minimum, maximum, grade, default = None, **nomargs
    ):
        self.minimum = minimum
        self.maximum = maximum
        self.grade = grade
        self.default = self.validate_value(
            self.minimum if None is default else default )
        super( ).__init__( name, **nomargs )

    def validate_value( self, value ):
        # NOTE: Might be too strict, if GUI controls accept floating-points.
        from numbers import Rational
        if not isinstance( value, Rational ):
            raise ValueError # TODO: Fill out error.
        if not ( self.minimum <= value <= self.maximum ):
            raise ValueError # TODO: Fill out error.
        # TODO: Ensure exact placement on discrete spectrum.
        return value


class FlexArray( DefinitionBase ):

    # TODO: Implement mutable sequence protocol.
    class Instance( InstanceBase ):

        def __init__( self, definition, value ):
            from itertools import chain
            initial_values = value
            super( ).__init__( definition, initial_values )
            if definition.maximum:
                initial_values = initial_values[ 0 : definition.maximum ]
            default_values_count = definition.minimum - len( initial_values )
            if 0 < default_values_count:
                initial_values = chain(
                    initial_values,
                    ( definition.default
                      for _ in range( default_values_count ) ) )
            self.elements = [
                definition.element_definition.create_control( value_ )
                for value_ in initial_values ]

        def append( self, value ):
            definition = self.definition
            element_definition = self.value
            elements_count = len( self.elements )
            if definition.maximum and definition.maximum <= elements_count:
                raise Exception # TODO: Fill out error.
            self.elements.append( element_definition.create_control( value ) )
            return self

        def remove( self, index = None ):
            if None is index: self.elements.pop( )
            elif isinstance( index, int ): self.elements.pop( index )
            else: self.elements.remove( index )
            return self

    @classmethod
    def instantiate_descriptor( class_, descriptor ):
        descriptor_ = descriptor.copy( )
        element_descriptor = descriptor_.pop( 'element' ).copy( )
        if 'name' not in element_descriptor:
            element_descriptor[ 'name' ] = descriptor[ 'name' ]
        element_class = _species_to_class(
            element_descriptor.pop( 'species' ) )
        descriptor_[ 'element_definition' ] = (
            element_class( **element_descriptor ) )
        return super( ).instantiate_descriptor( descriptor_ )

    def __init__(
        self, name, element_definition,
        minimum = 1, maximum = None, default = ( ), **nomargs
    ):
        self.element_definition = element_definition
        self.minimum = minimum
        if maximum and minimum > maximum:
            raise ValueError # TODO: Fill out error.
        self.maximum = maximum
        self.default = self.validate_value( default )
        super( ).__init__( name, **nomargs )

    def validate_value( self, value ):
        values = value
        if not isinstance( values, __.AbstractSequence ):
            raise ValueError # TODO: Fill out error.
        return tuple(
            self.element_definition.validate_value( value_ )
            for value_ in values )


class Options( DefinitionBase ):

    class Instance( InstanceBase ): pass

    def __init__( self, name, options, default = None, **nomargs ):
        if not isinstance( options, __.AbstractCollection ):
            raise ValueError # TODO: Fill out error.
        self.options = options
        self.default = self.validate_value(
            next( iter( options ) ) if None is default else default )
        super( ).__init__( name, **nomargs )

    def validate_value( self, value ):
        if value not in self.options:
            raise ValueError # TODO: Fill out error.
        return value


class Text( DefinitionBase ):

    class Instance( InstanceBase ): pass

    def __init__( self, name, default = '', **nomargs ):
        self.default = self.validate_value( default )
        super( ).__init__( name, **nomargs )

    def validate_value( self, value ):
        if not isinstance( value, str ):
            raise ValueError # TODO: Fill out error.


def descriptor_to_definition( descriptor ):
    descriptor_ = descriptor.copy( )
    class_ = _species_to_class( descriptor_.pop( 'species' ) )
    return class_.instantiate_descriptor( descriptor_ )


def _species_to_class( name ):
    # TODO: Python 3.10: match statement
    # Could compute class programmatically, but explicit is safer.
    if 'boolean' == name: return Boolean
    if 'discrete-interval' == name: return DiscreteInterval
    if 'flex-array' == name: return FlexArray
    if 'options' == name: return Options
    if 'text' == name: return Text
    raise ValueError( f"Unknown class name '{name}'." )
