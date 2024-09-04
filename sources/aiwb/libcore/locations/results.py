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


''' Results data transfer objects for operations on location. '''


from __future__ import annotations

from . import __
from . import core as _core


@__.standard_dataclass
class DirectoryEntry:
    ''' Location plus infromation about it. '''

    inode: Inode
    url: _core.Url


@__.standard_dataclass
class Inode:
    ''' Information about location. '''

    mimetype: str
    permissions: _core.Permissions
    species: _core.LocationSpecies
    supplement: _core.AdapterInode
