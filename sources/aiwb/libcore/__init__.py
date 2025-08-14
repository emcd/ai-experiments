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


''' Core entities for use across broader library. '''

# ruff: noqa: F401,F403,F405


from . import __
from . import application
from . import base
from . import locations
from . import notifications
from . import preparation
from . import state

from .application import Information as ApplicationInformation
from .base import *
from appcore import (
    InscriptionControl,
    ScribePresentations as InscriptionModes,
)
from appcore.dictedits import (
    Edit as                 DictionaryEdit,
    Edits as                DictionaryEdits,
    ElementsEntryEdit as    ElementsEntryDictionaryEdit,
    SimpleEdit as           SimpleDictionaryEdit,
)
from .locations.qaliases import *
from .notifications import Queue as NotificationsQueue
from .preparation import prepare
from .state import DirectorySpecies, Globals


