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
# pylint: disable=unused-import


from . import __
from . import application
from . import base
from . import cli
from . import configuration
from . import dictedits
from . import distribution
from . import environment
from . import exceptions
from . import inscription
from . import locations
from . import notifications
from . import preparation
from . import state

from .application import Information as ApplicationInformation
from .base import *
from .cli import (
    Cli,
    ConsoleDisplay as CliConsoleDisplay,
    InspectCommand as CliInspectCommand,
    LocationCommand as CliLocationCommand,
    execute_cli,
)
from .configuration import (
    acquire as acquire_configuration,
)
from .dictedits import (
    Edit as                 DictionaryEdit,
    Edits as                DictionaryEdits,
    ElementsEntryEdit as    ElementsEntryDictionaryEdit,
    SimpleEdit as           SimpleDictionaryEdit,
)
from .distribution import Information as DistributionInformation
from .environment import update as update_environment
from .exceptions import *
from .inscription import (
    Control as InscriptionControl,
    Modes as InscriptionModes,
    prepare as prepare_scribes,
    prepare_scribe_icecream,
    prepare_scribe_logging,
)
from .locations.qaliases import *
from .notifications import Queue as NotificationsQueue
from .preparation import prepare
from .state import DirectorySpecies, Globals


def main( ):
    ''' Entrypoint for utility to inspect and test library core. '''
    execute_cli( )


__.reclassify_modules( globals( ) )
