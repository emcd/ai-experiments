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


''' Immutable global state for the application. '''


from . import __


class Globals( __.CoreGlobals ):
    ''' Immutable global data. Required by many application functions. '''

    # TODO: Use proper types.
    invocables: __.accret.Namespace
    prompts: __.DictionaryProxy
    providers: __.accret.Dictionary
    vectorstores: dict

    @classmethod
    def from_base(
        selfclass,
        base: __.CoreGlobals, *,
        invocables: __.accret.Namespace,
        prompts: __.DictionaryProxy,
        providers: __.accret.Dictionary,
        vectorstores: dict,
    ) -> __.a.Self:
        ''' Produces DTO from base DTO plus attribute injections. '''
        injections = __.DictionaryProxy( dict(
            invocables = invocables,
            prompts = prompts,
            providers = providers,
            vectorstores = vectorstores,
        ) )
        return selfclass( **base.as_dictionary( ), **injections )
