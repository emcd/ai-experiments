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
from . import distribution as _distribution
from . import notifications as _notifications


class DirectorySpecies( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Possible species for locations. '''

    Cache = 'cache'
    Data = 'data'
    State = 'state'


class Globals(
    __.immut.DataclassObject
):
    ''' Immutable global data. Required by many library functions. '''

    application: _application.Information
    configuration: __.accret.Dictionary
    directories: __.PlatformDirs
    distribution: _distribution.Information
    exits: __.ExitsAsync # TODO? Make accretive.
    notifications: _notifications.Queue

    def as_dictionary( self ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        ''' Returns shallow copy of state. '''
        from dataclasses import fields
        return {
            field.name: getattr( self, field.name )
            for field in fields( self )
            if not field.name.startswith( '_' ) }

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
