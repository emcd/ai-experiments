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
from . import application as _application
from . import configuration as _configuration
from . import dictedits as _dictedits
from . import distribution as _distribution
from . import environment as _environment
from . import inscription as _inscription
from . import locations as _locations
from . import notifications as _notifications
from . import state as _state


async def prepare(
    exits: __.ExitsAsync,
    application: _application.Information = _application.Information( ),
    configedits: _dictedits.Edits = ( ),
    configfile: __.Optional[ _locations.Url ] = __.absent,
    environment: bool = False,
    inscription: __.Optional[ _inscription.Control ] = __.absent,
) -> _state.Globals:
    ''' Prepares globals DTO for use with library functions.

        Also:
        * Configures logging for library package (not application).
        * Optionally, updates the process environment.

        Note that asynchronous preparation allows for applications to
        concurrently initialize other entities outside of the library, even
        though the library initialization, itself, is inherently sequential.
    '''
    directories = application.produce_platform_directories( )
    distribution = (
        await _distribution.Information.prepare(
            package = __.package_name, exits = exits ) )
    configuration = (
        await _configuration.acquire(
            application_name = application.name,
            directories = directories,
            distribution = distribution,
            edits = configedits,
            file = configfile ) )
    notifications = _notifications.Queue( )
    auxdata = _state.Globals(
        application = application,
        configuration = configuration,
        directories = directories,
        distribution = distribution,
        exits = exits,
        notifications = notifications )
    if environment: await _environment.update( auxdata )
    _inscription.prepare( auxdata, control = inscription )
    _inscribe_preparation_report( auxdata )
    return auxdata


def _inscribe_preparation_report( auxdata: _state.Globals ):
    scribe = __.acquire_scribe( __.package_name )
    scribe.info( f"Application Name: {auxdata.application.name}" )
    scribe.info( f"Execution ID: {auxdata.application.execution_id}" )
    scribe.info( "Application Cache Location: {}".format(
        auxdata.provide_cache_location( ) ) )
    scribe.info( "Application Data Location: {}".format(
        auxdata.provide_data_location( ) ) )
    scribe.info( "Application State Location: {}".format(
        auxdata.provide_state_location( ) ) )
    scribe.info( "Package Data Location: {}".format(
        auxdata.distribution.provide_data_location( ) ) )
