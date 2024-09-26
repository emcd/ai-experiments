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


''' Immutable global state for API server. '''


from . import __
from . import server as _server


@__.standard_dataclass
class Globals( __.ApplicationGlobals ):
    ''' Immutable global data for API server. '''

    apiserver: _server.Accessor

    @__.a.override
    @classmethod
    def from_base(
        selfclass,
        base: __.ApplicationGlobals, *,
        apiserver: _server.Accessor,
    ) -> __.a.Self:
        ''' Produces DTO from base DTO plus attribute injections. '''
        injections = __.DictionaryProxy( dict( apiserver = apiserver ) )
        from dataclasses import fields
        return selfclass(
            **{ field.name: getattr( base, field.name )
                for field in fields( base ) },
            **injections )
