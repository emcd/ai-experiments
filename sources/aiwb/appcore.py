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


async def prepare( ) -> __.AccretiveNamespace:
    ''' Prepares AI-related functionality for applications. '''
    from asyncio import gather # TODO: Python 3.11: TaskGroup
    from . import invocables
    from . import prompts
    from . import providers
    from . import vectorstores
    from .libcore import ( ScribeModes, prepare as prepare_ )
    _configure_logging_pre( )
    auxdata = await prepare_(
        environment = True, scribe_mode = ScribeModes.Rich )
    # TEMP: Convert accretive namespace.
    auxdata = __.AccretiveNamespace(
        configuration = auxdata.configuration,
        directories = auxdata.directories,
        distribution = auxdata.distribution )
    _configure_logging_post( auxdata )
    # TODO: Configure metrics and traces emitters.
    await gather( *(
        module.prepare( auxdata ) for module in (
            invocables, prompts, providers, vectorstores ) ) )
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


def _configure_logging_post( auxdata: __.AccretiveNamespace ):
    ''' Configures standard Python logging after context available. '''
    # TODO: auxdata should be Globals
    import logging
    from os import environ
    envvar_name = "{name}_LOG_LEVEL".format(
        name = auxdata.distribution.name.upper( ) )
    level = getattr( logging, environ.get( envvar_name, 'INFO' ) )
    scribe = __.acquire_scribe( )
    scribe.setLevel( level )
