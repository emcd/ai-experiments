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


''' Arguments data transfer objects for operations on locations. '''


from __future__ import annotations

from . import __


class Permissions( __.enum.IntFlag ):
    ''' Permissions bits to report or test access. '''

    Abstain = 0
    Retrieve = __.produce_enumeration_value( )
    Create = __.produce_enumeration_value( )
    Update = __.produce_enumeration_value( )
    Delete = __.produce_enumeration_value( )
    Execute = __.produce_enumeration_value( )


@__.standard_dataclass
class CheckAccessArguments:
    ''' Arguments to access checker. '''
    # HTTP: pursue_indirection -> follow redirects
    #       permissions -> OPTIONS/GET/PUT/PATCH/DELETE/POST

    permissions: Permissions
    pursue_indirection: bool = True
