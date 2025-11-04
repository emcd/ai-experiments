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


''' Exception classes for GUI components. '''


from . import __


class ComponentAttributeAbsence( __.Omnierror, AttributeError ):
    ''' Component missing required attribute. '''

    def __init__( self, component_class, attribute_name, operation ):
        super( ).__init__(
            f"Cannot {operation}: component of type {component_class!r} "
            f"has no {attribute_name!r} attribute." )
