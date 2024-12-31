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

# ruff: noqa: F401,F403,F405
# pylint: disable=unused-import


from ....libcore.locations.qaliases import *
from ..__ import *


async def accessor_from_arguments(
    arguments: Arguments,
    species: Optional[ LocationSpecies ] = absent,
) -> SpecificLocationAccessor:
    url = Url.from_url( arguments.pop( 'location' ) )
    adapter = location_adapter_from_url( url )
    if adapter.is_cache_manager( ): accessor = adapter.produce_cache( )
    else: accessor = adapter
    if LocationSpecies.File is species: return accessor.as_file( )
    return await accessor.as_specific( species = species )
