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


''' Filter which honors Git ignore files (``.gitignore``). '''


from gitignorefile import Cache as _Cache

from . import __


class Filter( __.Filter ):
    ''' Filters directory entry according to relevant .gitignore files. '''
    # TODO: Immutable class and instance attributes.

    cache: _Cache

    def __init__( self ): self.cache = _Cache( )

    async def __call__( self, dirent: __.DirectoryEntry ) -> bool:
        # TODO: Replace with async implementation.
        # TODO: Handle exceptions.
        return self.cache( dirent.url.path )

__.filters_registry[ '@gitignore' ] = Filter
