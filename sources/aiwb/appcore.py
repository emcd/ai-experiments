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


@__.dataclass( frozen = True, kw_only = True, slots = True )
class Globals( _libcore.Globals ):
    ''' Immutable global data. Required by many application functions. '''

    invocables: __.DictionaryProxy
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
            import_module( f".{slot}", __package__ ) for slot in slots )
        attributes = await gather( *(
            module.prepare( base ) for module in modules ) )
        return selfclass(
            **{ field.name: getattr( base, field.name )
                for field in fields( base ) },
            **dict( zip( slots, attributes ) ) )


async def prepare( ) -> __.AccretiveNamespace:
    ''' Prepares AI-related functionality for applications. '''
    _configure_logging_pre( )
    auxdata_base = await _libcore.prepare(
        environment = True, scribe_mode = _libcore.ScribeModes.Rich )
    _configure_logging_post( auxdata_base )
    auxdata = await Globals.prepare( auxdata_base )
    # TODO: Configure metrics and traces emitters.
    return auxdata


def _configure_logging_pre( ):
    ''' Configures standard Python logging during early initialization. '''
    import logging
    from rich.console import Console
    from rich.logging import RichHandler
    handler = RichHandler(
        console = Console( stderr = True ),
        rich_tracebacks = True,
        show_time = False )
    logging.basicConfig(
        format = '%(name)s: %(message)s',
        handlers = [ handler ] )
    logging.captureWarnings( True )


def _configure_logging_post( auxdata: _libcore.Globals ):
    ''' Configures standard Python logging after context available. '''
    import logging
    from os import environ
    envvar_name = "{name}_LOG_LEVEL".format(
        name = auxdata.distribution.name.upper( ) )
    level = getattr( logging, environ.get( envvar_name, 'INFO' ) )
    root_scribe = __.acquire_scribe( )
    root_scribe.setLevel( level )
    library_scribe = __.acquire_scribe( __package__ )
    library_scribe.propagate = False # Prevent double-logging.
