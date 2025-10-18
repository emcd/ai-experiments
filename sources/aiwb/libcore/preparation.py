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


''' Preparation of the library core. '''


from . import __
from . import state as _state


async def prepare(
    exits: __.ctxl.AsyncExitStack,
    configedits: __.appcore.dictedits.Edits = ( ),
    configfile: __.Absential[ __.Url ] = __.absent,
    environment: bool = False,
    inscription: __.Absential[ __.appcore.InscriptionControl ] = __.absent,
) -> _state.Globals:
    ''' Prepares globals DTO for use with library functions.

        Also:
        * Configures logging for library package (not application).
        * Optionally, loads process environment from files.

        Note that asynchronous preparation allows for applications to
        concurrently initialize other entities outside of the library, even
        though the library initialization, itself, is inherently sequential.
    '''
    await __.locations.register_defaults( )
    auxdata_base = await __.appcore.prepare(
        configedits = configedits,
        environment = environment,
        exits = exits,
        inscription = inscription )
    notifications = __.NotificationsQueue( )
    auxdata = _state.Globals(
        application = auxdata_base.application,
        configuration = auxdata_base.configuration,
        directories = auxdata_base.directories,
        distribution = auxdata_base.distribution,
        exits = auxdata_base.exits,
        notifications = notifications )
    _prepare_scribe_icecream( inscription )
    _inscribe_preparation_report( auxdata )
    return auxdata


def _prepare_scribe_icecream(
    control: __.Absential[ __.appcore.InscriptionControl ]
):
    ''' Prepares Icecream debug printing. '''
    if __.is_absent( control ):
        control = __.appcore.InscriptionControl( )
    from icecream import ic, install
    nomargs = dict( includeContext = True, prefix = 'DEBUG    ' )
    match control.mode:
        case __.appcore.ScribePresentations.Null:
            ic.configureOutput( **nomargs )
            ic.disable( )
        case __.appcore.ScribePresentations.Plain:
            ic.configureOutput( **nomargs )
        case __.appcore.ScribePresentations.Rich:
            from rich.pretty import pretty_repr
            ic.configureOutput( argToStringFunction = pretty_repr, **nomargs )
    install( )


def _inscribe_preparation_report( auxdata: _state.Globals ):
    scribe = __.acquire_scribe( __.package_name )
    scribe.info( f"Application Name: {auxdata.application.name}" )
    scribe.info( "Application Cache Location: {}".format(
        auxdata.provide_cache_location( ) ) )
    scribe.info( "Application Data Location: {}".format(
        auxdata.provide_data_location( ) ) )
    scribe.info( "Application State Location: {}".format(
        auxdata.provide_state_location( ) ) )
    scribe.info( "Package Data Location: {}".format(
        auxdata.distribution.provide_data_location( ) ) )
