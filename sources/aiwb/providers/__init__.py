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


''' Functionality for various AI providers. '''


from .__ import *


async def prepare( auxdata ):
    ''' Prepare desired AI providers. '''
    from asyncio import gather # TODO: Python 3.11: TaskGroup
    from importlib import import_module
    from accretive.qaliases import AccretiveDictionary
    # TODO: Determine providers from configuration and only load those.
    names = ( 'openai', )
    modules = [ ]
    auxdata.ai_providers = registry = AccretiveDictionary( )
    for name in names:
        modules.append( import_module( f".{name}", package = __package__ ) )
    providers = await gather(
        *( module.prepare( auxdata ) for module in modules ),
        return_exceptions = True )
    for provider, module in zip( providers, modules ):
        if isinstance( provider, BaseException ):
            # TODO: Log exception and also push onto warning stack.
            continue
        # TODO: Register provider object rather than module.
        registry[ provider.proper_name ] = module
    return registry
