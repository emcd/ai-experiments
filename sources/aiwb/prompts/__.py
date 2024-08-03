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


''' Common declarations and utilities for prompts. '''

# pylint: disable=unused-import


import typing as typ # TODO: Replace with _annotations.

from abc import ABCMeta as ABCFactory, abstractmethod as abstract_function
from collections.abc import (
    MutableMapping as AbstractMutableDictionary,
    MutableSequence as AbstractMutableSequence,
    Sequence as AbstractSequence,
)
from dataclasses import dataclass, field as dataclass_declare
from pathlib import Path
from types import MappingProxyType as DictionaryProxy, SimpleNamespace

from .. import _annotations as a
from .. import _generics as g
from ..__ import acquire_scribe, read_files_async
