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


''' Qualified aliases to locations.

    Useful for avoiding namespace collisions from attribute imports.
'''

# ruff: noqa: F401,F403


from .core import (
    AccessImplement as      LocationAccessImplement,
    FileUpdateOptions,
    InodeAttributes,
    LocationSpecies,
    PossibleUrl,
    Url,
)
from .exceptions import *
from .interfaces import (
    DirectoryAccessor,
    FileAccessor,
    SpecificAccessor as     SpecificLocationAccessor,
)
from .registries import (
    adapter_from_url as             location_adapter_from_url,
    adapters_registry as            location_adapters_registry,
    cache_from_url as               location_cache_from_url,
    caches_registry as              location_caches_registry,
    directory_adapter_from_url,
    file_adapter_from_url,
    file_presenter_from_accessor,
    file_presenter_from_url,
    file_presenters_registry,
    text_file_presenter_from_accessor,
    text_file_presenter_from_url,
)
