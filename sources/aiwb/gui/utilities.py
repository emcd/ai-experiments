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


''' Convenience fucntions for Holoviz Panel GUI. '''


def access_text_component_value( component ) -> str:
    ''' Returns text value from appropriate component attribute. '''
    if hasattr( component, 'value' ): return component.value
    if hasattr( component, 'object' ): return str( component.object )
    # TODO: Appropriate error.
    raise AssertionError( "Component has no text attribute." )


def assign_text_component_value( component, text: str ):
    ''' Assigns text value to appropriate component attribute. '''
    if hasattr( component, 'value' ): component.value = text
    elif hasattr( component, 'object' ): component.object = text
    # TODO: Appropriate error.
    else: raise AssertionError( "Component has no text attribute." )
