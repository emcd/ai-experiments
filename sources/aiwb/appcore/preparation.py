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


''' Preparation of the application core. '''


from . import __
from . import state as _state


async def prepare(
    exits: __.ExitsAsync, *,
    application: __.ApplicationInformation = __.ApplicationInformation( ),
    configedits: __.DictionaryEdits = ( ),
    configfile: __.Optional[ __.Url ] = __.absent,
    environment: bool = True,
    inscription: __.InscriptionControl = (
        __.InscriptionControl( mode = __.InscriptionModes.Rich ) ),
) -> _state.Globals:
    ''' Prepares AI-related functionality for applications. '''
    _configure_logging( application = application, inscription = inscription )
    # TODO: Configure metrics and traces emitters.
    auxdata_base = await __.prepare_core(
        application = application,
        configedits = configedits,
        configfile = configfile,
        environment = environment,
        exits = exits,
        inscription = inscription )
    from importlib import import_module
    names = ( 'invocables', 'prompts', 'providers', 'vectorstores' )
    modules = tuple(
        import_module( f".{name}", __.package_name ) for name in names )
    attributes = await __.gather_async( *(
        module.prepare( auxdata_base ) for module in modules ) )
    auxdata = _state.Globals.from_base(
        auxdata_base, **dict( zip( names, attributes ) ) )
    return auxdata


def _configure_logging(
    application: __.ApplicationInformation,
    inscription: __.InscriptionControl,
):
    ''' Configures standard Python logging for application. '''
    import logging
    from rich.console import Console
    from rich.logging import RichHandler
    if None is inscription.level:
        from os import environ
        envvar_name = (
            "{name}_LOG_LEVEL".format( name = application.name.upper( ) ) )
        level_name = environ.get( envvar_name, 'INFO' )
    else: level_name = inscription.level
    level = getattr( logging, level_name.upper( ) )
    handler = RichHandler(
        console = Console( stderr = True ),
        rich_tracebacks = True,
        show_time = False )
    logging.basicConfig(
        format = '%(name)s: %(message)s',
        level = level,
        handlers = [ handler ] )
    logging.captureWarnings( True )
