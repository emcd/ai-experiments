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

    name: str # application name
    configuration: __.AccretiveDictionary
    directories: __.PlatformDirs
    distribution: _distribution.Information
    # TODO? execution_id
    exits: __.Exits # TODO? Make accretive.
    notifications: _notifications.Queue

    @classmethod
    async def prepare(
        selfclass,
        exits: __.Exits,
        application_name: __.Optional[ str ] = __.absent,
        application_publisher: __.Optional[ str ] = __.absent,
        application_version: __.Optional[ str ] = __.absent,
    ) -> __.a.Self:
        ''' Acquires data to create DTO. '''
        package_name = __package__.split( '.', maxsplit = 1 )[ 0 ]
        if __.absent is application_name: application_name = package_name
        pdirs_arguments = __.AccretiveDictionary( dict(
            appname = application_name, ensure_exists = True ) )
        if __.absent is not application_publisher:
            pdirs_arguments[ 'appauthor' ] = application_publisher
        if __.absent is not application_version:
            pdirs_arguments[ 'version' ] = application_version
        directories = __.PlatformDirs( **pdirs_arguments )
        distribution = (
            await _distribution.Information.prepare(
                package = package_name, exits = exits ) )
        configuration = (
            await _configuration.acquire(
                application_name, distribution, directories ) )
        notifications = _notifications.Queue( )
        return selfclass(
            name = application_name,
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
                'application_name': self.name,
            }
            base = __.Path( spec.format( **args ) )
        if appendages: return base.joinpath( *appendages )
        return base
