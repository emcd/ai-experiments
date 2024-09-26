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


''' Immutable global state. '''


from . import __


@__.standard_dataclass
class Globals( __.CoreGlobals ):
    ''' Immutable global data. Required by many application functions. '''

    invocables: __.AccretiveNamespace
    prompts: __.DictionaryProxy
    providers: __.AccretiveDictionary
    vectorstores: dict

    @classmethod
    async def prepare( selfclass, base: __.CoreGlobals ) -> __.a.Self:
        ''' Acquires data to create DTO. '''
        # TODO: Use __.gather_async
        from asyncio import gather # TODO: Python 3.11: TaskGroup
        from dataclasses import fields
        from importlib import import_module
        slots = ( 'invocables', 'prompts', 'providers', 'vectorstores' )
        modules = tuple(
            import_module( f".{slot}", __.package_name ) for slot in slots )
        attributes = await gather( *(
            module.prepare( base ) for module in modules ) )
        return selfclass(
            **{ field.name: getattr( base, field.name )
                for field in fields( base ) },
            **dict( zip( slots, attributes ) ) )
