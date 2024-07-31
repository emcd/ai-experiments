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


''' Base functionality to support AI workbench. '''


import enum

from dataclasses import dataclass
from enum import Enum
from logging import getLogger as acquire_scribe
from pathlib import Path
from types import MappingProxyType as DictionaryProxy

from aiofiles import open as open_async
from accretive.qaliases import AccretiveDictionary, AccretiveNamespace
from platformdirs import PlatformDirs

from . import _annotations as a


def provide_cache_location( auxdata, *appendages ):
    ''' Provides cache location from configuration. '''
    spec = auxdata.configuration.get( 'locations', { } ).get( 'cache' )
    if not spec: base = auxdata.directories.user_cache_path
    else:
        base = Path( spec.format(
            user_cache = auxdata.directories.user_cache_dir,
            application_name = auxdata.distribution.name ) )
    if appendages: return base.joinpath( *appendages )
    return base


def provide_data_location( auxdata, *appendages ):
    ''' Provides data location from configuration. '''
    spec = auxdata.configuration.get( 'locations', { } ).get( 'data' )
    if not spec: base = auxdata.directories.user_data_path
    else:
        base = Path( spec.format(
            user_data = auxdata.directories.user_data_dir,
            application_name = auxdata.distribution.name ) )
    if appendages: return base.joinpath( *appendages )
    return base


def provide_state_location( auxdata, *appendages ):
    ''' Provides state location from configuration. '''
    spec = auxdata.configuration.get( 'locations', { } ).get( 'state' )
    if not spec: base = auxdata.directories.user_state_path
    else:
        base = Path( spec.format(
            user_state = auxdata.directories.user_state_dir,
            application_name = auxdata.distribution.name ) )
    if appendages: return base.joinpath( *appendages )
    return base
