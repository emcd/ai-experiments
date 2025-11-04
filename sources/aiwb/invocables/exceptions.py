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


''' Exception classes for invocables. '''


from . import __


class DiceSpecificationInvalidity( __.Omnierror, ValueError ):
    ''' Invalid dice specification format or constraints. '''

    def __init__( self, dice_spec, reason ):
        super( ).__init__(
            f"Invalid dice specification '{dice_spec}': {reason}." )


class EditContention( __.Omnierror, ValueError ):
    ''' Edit operations overlap in file. '''

    def __init__( self, operation1_line, operation2_line ):
        super( ).__init__(
            f"Operation at line {operation1_line} overlaps with "
            f"operation at line {operation2_line}." )
