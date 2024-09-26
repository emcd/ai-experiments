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


''' Preparation of API server. '''


from . import __
from . import server as _server
from . import state as _state


async def prepare(
    exits: __.ExitsAsync, *,
    apiserver: _server.Control = _server.Control( ),
    application: __.ApplicationInformation = __.ApplicationInformation( ),
    configedits: __.DictionaryEdits = ( ),
    configfile: __.Optional[ __.Url ] = __.absent,
    environment: bool = True,
    inscription: __.InscriptionControl = (
        __.InscriptionControl( mode = __.InscriptionModes.Rich ) ),
) -> _state.Globals:
    ''' Prepares API server state. '''
    auxdata_base = await __.prepare_application(
        application = application,
        configedits = configedits,
        configfile = configfile,
        environment = environment,
        exits = exits,
        inscription = inscription )
    accessor = await _server.prepare( auxdata_base, control = apiserver )
    return _state.Globals.from_base( auxdata_base, apiserver = accessor )
