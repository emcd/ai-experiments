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


def create_control( descriptor ):
    from panel.widgets import Checkbox, Select, TextInput
    identity = descriptor[ 'identity' ]
    species = descriptor.get( 'species', 'text' )
    label = descriptor[ 'label' ]
    if 'array' == species:
        # TODO: count-initial, count-maximum, element-descriptor, compact
        raise NotImplementedError
    elif 'boolean' == species:
        default = descriptor.get( 'default', False )
        component = Checkbox( name = label, value = default )
    elif 'discrete-range' == species:
        # TODO: domain, default, minimum, maximum, grade
        raise NotImplementedError
    elif 'options' == species:
        options = descriptor[ 'options' ] # TODO: name of populator function
        default = options[ 0 ]
        component = Select( name = label, options = options, value = default )
    elif 'text' == species:
        default = variable.get( 'default', '' )
        component = TextInput( name = label, value = default )
        else:
            raise ValueError(
                f"Invalid component species, '{species}', for '{identity}'." )
    return component
