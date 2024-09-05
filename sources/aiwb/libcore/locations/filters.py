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


''' Location access adapter with aiofiles and pathlib. '''


from __future__ import annotations

from . import __
from . import core as _core
from . import exceptions as _exceptions


@__.a.runtime_checkable
@__.standard_dataclass
class Filter( __.a.Protocol ):
    ''' Determines if directory entry should be filtered. '''

    name: str

    @__.abstract_member_function
    async def __call__( self, dirent: _core.DirectoryEntry ) -> bool:
        raise NotImplementedError


# TODO: @gitignore
# TODO: +vcs
# TODO: -permissions:r
# TODO: -permissions:cud
# TODO: +permissions:cud
# TODO: +permissions:x
# TODO: -inode:file
# TODO: +inode:directory
# TODO: +inode:symlink
# TODO: +inode:SPECIALS
# TODO? +mimetype:image/*
# TODO? +mimetype:application/octet-stream


# TODO: Python 3.12: type statement for aliases
FiltersRegistry: __.a.TypeAlias = __.AbstractDictionary[ str, Filter ]
PossibleFilter: __.a.TypeAlias = bytes | str | Filter


# TODO: Use accretive validator dictionaries for registries.
filters_registry: FiltersRegistry = __.AccretiveDictionary( )


async def apply_filters(
    dirent: _core.DirectoryEntry,
    filters: __.AbstractSequence[ PossibleFilter ],
) -> bool:
    ''' Applies sequence of filters to directory entry. '''
    for filter in filters:
        if isinstance( filter, bytes ): filter = filter.decode( )
        if isinstance( filter, str ):
            # TODO? Parse arguments from name with ':'-splitting.
            #       E.g., '<mtime:1725421713'
            #       E.g., '<expiration:1725421713'
            if filter in filters_registry:
                filter = filters_registry[ filter ]
            else: raise _exceptions.AbsentFilterError( filter )
        if await filter( dirent ): return True
    return False
