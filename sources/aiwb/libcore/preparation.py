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


""" Preparation of the library core. """


from . import __
from . import application as _application
from . import locations as _locations
from . import notifications as _notifications
from . import state as _state


async def prepare(
    exits: __.ctxl.AsyncExitStack,
    application: _application.Information = _application.Information(),
    configedits: __.appcore.dictedits.Edits = (),
    configfile: __.Absential[_locations.Url | __.Path | __.io.TextIOBase] = __.absent,
    environment: bool | __.NominativeArgumentsDictionary = False,
    inscription: __.Absential[ __.appcore.InscriptionControl ] = __.absent,
) -> _state.Globals:
    """Prepares globals DTO for use with library functions."""

    await _locations.register_defaults()
    if not __.is_absent( configfile ) and isinstance( configfile, _locations.Url ):
        configfile = __.Path( configfile.path )
    base = await __.appcore.prepare(
        exits = exits,
        application = application,
        configedits = configedits,
        configfile = configfile,
        environment = environment,
        inscription = inscription,
    )
    auxdata = _state.Globals(
        **base.as_dictionary(),
        notifications = _notifications.Queue(),
    )
    _inscribe_preparation_report( auxdata )
    return auxdata


def _inscribe_preparation_report( auxdata: _state.Globals ) -> None:
    scribe = __.acquire_scribe( __.package_name )
    scribe.info( f"Application Name: {auxdata.application.name}" )
    execution_id = getattr( auxdata.application, "execution_id", None )
    if execution_id is not None:
        scribe.info( f"Execution ID: {execution_id}" )
    scribe.info( "Application Cache Location: {}".format(
        auxdata.provide_cache_location() ) )
    scribe.info( "Application Data Location: {}".format(
        auxdata.provide_data_location() ) )
    scribe.info( "Application State Location: {}".format(
        auxdata.provide_state_location() ) )
    scribe.info( "Package Data Location: {}".format(
        auxdata.distribution.provide_data_location() ) )

