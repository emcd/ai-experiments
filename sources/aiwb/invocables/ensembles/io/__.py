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


''' Internal imports and utilities for I/O invocables. '''

# ruff: noqa: F403,F405


from ....locations.qaliases import *
from ..__ import *


async def accessor_from_arguments(
    arguments: cabc.MutableMapping[ str, typx.Any ],
    species: Absential[ LocationSpecies ] = absent,
) -> SpecificLocationAccessor:
    url = Url.from_url( arguments.pop( 'location' ) )
    adapter = location_adapter_from_url( url )
    if adapter.is_cache_manager( ): accessor = location_cache_from_url( url )
    else: accessor = adapter
    if LocationSpecies.File is species: return accessor.as_file( )
    return await accessor.as_specific( species = species )


def is_directory_accessor(
    accessor: typx.Any,
) -> typx.TypeGuard[ DirectoryAccessor ]:
    ''' Determines if object can survey directory entries. '''
    return hasattr( accessor, 'survey_entries' )


def is_file_accessor( accessor: typx.Any ) -> typx.TypeGuard[ FileAccessor ]:
    ''' Determines if object can acquire and update file content. '''
    return (
        hasattr( accessor, 'acquire_content_result' )
        and hasattr( accessor, 'update_content' ) )
