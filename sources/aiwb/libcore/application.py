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


''' Information about application. '''


from . import __


@__.standard_dataclass
class Information:
    ''' Information about an application. '''

    name: str
    publisher: __.a.Nullable[ str ] = None
    version: __.a.Nullable[ str ] = None
    execution_id: __.a.Annotation[
        __.a.Nullable[ str ], __.a.Doc( "For telemetry, etc..." )
    ] = None

    def produce_platform_directories( self ) -> __.PlatformDirs:
        arguments = __.AccretiveDictionary( dict(
            appname = self.name, ensure_exists = True ) )
        if self.publisher: arguments[ 'appauthor' ] = self.publisher
        if self.version: arguments[ 'version' ] = self.version
        return __.PlatformDirs( **arguments )
