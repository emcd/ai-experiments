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


''' Immutable global state for GUI. '''


from . import __
from . import server as _server
from . import updaters as _updaters


class Manager( __.immut.DataclassObject ):
    ''' Manager for GUI components and server. '''

    components: __.types.SimpleNamespace
    deduplicator: _updaters.UpdatesDeduplicator
    server: _server.Accessor
    transformers: __.accret.Dictionary


class Globals( __.ApiServerGlobals ):
    ''' Immutable global data for GUI. '''

    gui: Manager

    @classmethod
    def from_apiserver(
        selfclass,
        base: __.ApiServerGlobals, *,
        gui: Manager,
    ) -> __.typx.Self:
        ''' Produces DTO from base DTO plus attribute injections. '''
        return selfclass(
            application = base.application,
            configuration = base.configuration,
            directories = base.directories,
            distribution = base.distribution,
            exits = base.exits,
            notifications = base.notifications,
            invocables = base.invocables,
            prompts = base.prompts,
            providers = base.providers,
            vectorstores = base.vectorstores,
            apiserver = base.apiserver,
            gui = gui )
