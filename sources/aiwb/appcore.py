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


''' Core entities for use with workbench applications. '''


from . import __
from . import libcore as _libcore


@__.standard_dataclass
class Globals( _libcore.Globals ):
    ''' Immutable global data. Required by many application functions. '''

    invocables: __.AccretiveNamespace
    prompts: __.DictionaryProxy
    providers: __.AccretiveDictionary
    vectorstores: dict

    @classmethod
    async def prepare( selfclass, base: _libcore.Globals ) -> __.a.Self:
        ''' Acquires data to create DTO. '''
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


async def prepare(
    exits: __.Exits, *,
    application: __.Optional[ _libcore.ApplicationInformation ] = __.absent,
) -> Globals:
    ''' Prepares AI-related functionality for applications. '''
    _configure_logging( application = application )
    # TODO: Configure metrics and traces emitters.
    auxdata_base = await _libcore.prepare(
        application = application,
        environment = True,
        exits = exits,
        scribe_mode = _libcore.ScribeModes.Rich )
    auxdata = await Globals.prepare( auxdata_base )
    return auxdata


def _configure_logging(
    application: __.Optional[ _libcore.ApplicationInformation ] = __.absent
):
    ''' Configures standard Python logging for application. '''
    import logging
    from os import environ
    from rich.console import Console
    from rich.logging import RichHandler
    if __.absent is application:
        application_name = __package__.split( '.', maxsplit = 1 )[ 0 ]
    else: application_name = application.name
    envvar_name = "{name}_LOG_LEVEL".format( name = application_name.upper( ) )
    level = getattr( logging, environ.get( envvar_name, 'INFO' ) )
    handler = RichHandler(
        console = Console( stderr = True ),
        rich_tracebacks = True,
        show_time = False )
    logging.basicConfig(
        format = '%(name)s: %(message)s',
        level = level,
        handlers = [ handler ] )
    logging.captureWarnings( True )
