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
from . import application as _application
from . import configuration as _configuration
from . import distribution as _distribution
from . import notifications as _notifications


class DirectorySpecies( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Possible species for locations. '''

    Cache = 'cache'
    Data = 'data'
    State = 'state'


@__.standard_dataclass
class Globals:
    ''' Immutable global data. Required by many library functions. '''

    application: _application.Information
    configuration: __.AccretiveDictionary
    directories: __.PlatformDirs
    distribution: _distribution.Information
    exits: __.Exits # TODO? Make accretive.
    notifications: _notifications.Queue

    @classmethod
    async def prepare(
        selfclass,
        exits: __.Exits, *,
        application: __.Optional[ _application.Information ] = __.absent,
        configedits: __.AbstractSequence[ _configuration.Edit ] = ( ),
    ) -> __.a.Self:
        ''' Acquires data to create DTO. '''
        if __.absent is application: application = _application.Information( )
        directories = application.produce_platform_directories( )
        distribution = (
            await _distribution.Information.prepare(
                package = __.package_name, exits = exits ) )
        configuration = (
            await _configuration.acquire(
                application_name = application.name,
                directories = directories,
                distribution = distribution,
                edits = configedits ) )
        notifications = _notifications.Queue( )
        return selfclass(
            application = application,
            configuration = configuration,
            directories = directories,
            distribution = distribution,
            exits = exits,
            notifications = notifications )

    def provide_cache_location( self, *appendages: str ) -> __.Path:
        ''' Provides cache location from configuration. '''
        return self.provide_location( DirectorySpecies.Cache, *appendages )

    def provide_data_location( self, *appendages: str ) -> __.Path:
        ''' Provides data location from configuration. '''
        return self.provide_location( DirectorySpecies.Data, *appendages )

    def provide_state_location( self, *appendages: str ) -> __.Path:
        ''' Provides state location from configuration. '''
        return self.provide_location( DirectorySpecies.State, *appendages )

    def provide_location(
        self, species: DirectorySpecies, *appendages: str
    ) -> __.Path:
        ''' Provides particular species of location from configuration. '''
        species = species.value
        base = getattr( self.directories, f"user_{species}_path" )
        if spec := self.configuration.get( 'locations', { } ).get( species ):
            args = {
                f"user_{species}": base,
                'user_home': __.Path.home( ),
                'application_name': self.application.name,
            }
            base = __.Path( spec.format( **args ) )
        if appendages: return base.joinpath( *appendages )
        return base
