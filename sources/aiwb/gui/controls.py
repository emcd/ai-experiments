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


''' Management of control widgets for Holoviz Panel GUI. '''


from . import __
from ..controls import exceptions as _control_exceptions


class ComponentManager( metaclass = __.abc.ABCMeta ):

    def __init__( self, control, callback ):
        self.control = control
        self.callback = callback
        self.component = component = self._materialize( control, callback )
        component.auxdata__ = getattr(
            component, 'auxdata__', __.types.SimpleNamespace( ) )
        component.auxdata__.manager = self

    def assimilate( self ):
        self.control.value = self.component.value
        return self

    @__.abc.abstractmethod
    def _materialize( self, control, callback ):
        raise NotImplementedError


class ContainerManager:

    def __init__( self, container, controls, callback ):
        self.container = container
        container.objects = [
            _materialize_instance( control, callback )
            for control in controls ]
        container.auxdata__ = getattr(
            container, 'auxdata__', __.types.SimpleNamespace( ) )
        container.auxdata__.manager = self

    def assimilate( self ):
        for component in self.container:
            component.auxdata__.manager.assimilate( )


class Boolean( ComponentManager ):

    def _materialize( self, control, callback ):
        from panel import widgets
        definition = control.definition
        attributes = definition.attributes
        component = widgets.Checkbox(
            name = attributes.label, value = control.value )
        component.param.watch( callback, 'value' )
        return component


class DiscreteInterval( ComponentManager ):

    def _materialize( self, control, callback ):
        from numbers import Integral, Rational
        from panel import widgets
        definition = control.definition
        attributes = definition.attributes
        if isinstance( definition.grade, Integral ):
            component_class = widgets.IntSlider
            converter = int
        elif isinstance( definition.grade, Rational ):
            component_class = widgets.FloatSlider
            converter = float
        component = component_class(
            name = attributes.label,
            start = converter( definition.minimum ),
            end = converter( definition.maximum ),
            step = converter( definition.grade ),
            value = control.value )
        component.param.watch( callback, 'value' )
        return component


class FlexArray( ComponentManager ):

    def _materialize( self, control, callback ):
        from panel import layout
        elements = control.value
        # TODO: Create '+' button.
        #       Ensure that it creates components with corresponding managers.
        # TODO: Select appropriate container from attributes.
        # TODO: Set container properties according to attributes.
        container_class = layout.Row
        return container_class( *(
            _materialize_instance( element, callback )
            for element in elements ) )

    def assimilate( self ):
        array = self.control
        container = self.component
        definition = array.definition
        if definition.maximum and definition.maximum < len( container ):
            raise _control_exceptions.ControlArrayCapacityViolation(
                array.name, len( container ), definition.maximum )
        elements = [ ]
        for component in container:
            manager = component.auxdata__.manager
            manager.assimilate( )
            element = manager.control
            elements.append( element )
        array.value.clear( )
        array.value.extend( elements )
        return self


class Options( ComponentManager ):

    def _materialize( self, control, callback ):
        from panel import widgets
        definition = control.definition
        attributes = definition.attributes
        options = definition.options
        options = {
            attributes[ 'label' ]: name
            for name, attributes in options.items( ) }
        # TODO: Choose GUI component according to attributes.
        component = widgets.Select(
            name = attributes.label,
            options = options,
            value = control.value )
        component.param.watch( callback, 'value' )
        return component


class Text( ComponentManager ):

    def _materialize( self, control, callback ):
        from panel import widgets
        definition = control.definition
        attributes = definition.attributes
        component = widgets.TextInput(
            name = attributes.label, value = control.value )
        component.param.watch( callback, 'value' )
        return component


def _materialize_instance( control, callback ):
    from ..controls import core as controls
    if isinstance( control, controls.Boolean.Instance ):
        return Boolean( control, callback ).component
    if isinstance( control, controls.DiscreteInterval.Instance ):
        return DiscreteInterval( control, callback ).component
    if isinstance( control, controls.FlexArray.Instance ):
        return FlexArray( control, callback ).component
    if isinstance( control, controls.Options.Instance ):
        return Options( control, callback ).component
    if isinstance( control, controls.Text.Instance ):
        return Text( control, callback ).component
    raise ValueError( "Invalid control class '{class_name}'.".format(
        class_name = type( control ).__qualname__ ) )
