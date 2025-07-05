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


''' Factories, mass applicators, and registries. '''


from __future__ import annotations

from . import __
from . import interfaces as _interfaces


# TODO: Use accretive validator dictionaries for registries.
preparers_registry = __.accret.Dictionary( )


def access_client_default(
    auxdata: __.CoreGlobals, clients: _interfaces.ClientsByName
) -> _interfaces.Client:
    ''' Returns default client. '''
    defaults = auxdata.configuration.get( 'default-provider', ( ) )
    for default in defaults:
        if default in clients: return clients[ default ]
    return next( iter( clients.values( ) ) )
