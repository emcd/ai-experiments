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


''' Common functionality and utilities for vectorstores. '''

# pylint: disable=unused-import


from collections.abc import (
    Mapping as AbstractDictionary,
)
from dataclasses import dataclass
from pathlib import Path
from types import (
    MappingProxyType as DictionaryProxy,
    ModuleType as Module,
)
from urllib.parse import urlparse

from accretive.qaliases import AccretiveDictionary

from .. import _annotations as a
from .. import _generics as g
from ..__ import acquire_scribe, gather_async


def derive_standard_file_paths( auxdata ):
    # TODO: Use auxdata.locations.provide_user_data.
    configuration = auxdata.configuration
    directories = auxdata.directories
    return dict(
        data_path = Path(
            configuration[ 'locations' ][ 'data' ].format(
                user_data = directories.user_data_path ) ) / 'vectorstores',
    )
