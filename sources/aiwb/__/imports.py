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

# ruff: noqa: F401

import                          abc
import                          asyncio
import collections.abc as       cabc
import contextlib as            ctxl
import dataclasses as           dcls
import                          enum
import functools as             funct
import                          io
import itertools as             itert
import                          os
import                          re
import                          sys
import                          types

from asyncio import (
    Lock as MutexAsync,
)
from collections import namedtuple # TODO: Replace with dataclass.
from datetime import (
    datetime as DateTime,
    timedelta as TimeDelta,
    timezone as TimeZone,
)
from itertools import chain
from logging import (
    Logger as Scribe,
    getLogger as acquire_scribe,
)
from os import PathLike
from pathlib import Path
from queue import SimpleQueue
from threading import Thread
from time import time_ns
from urllib.parse import urlparse
from uuid import uuid4

import accretive as         accret
import                      appcore
import                      appcore.dictedits
import frigid as            immut
import typing_extensions as typx
import                      tyro

from absence import Absential, absent, is_absent
from appcore import asyncf, generics
