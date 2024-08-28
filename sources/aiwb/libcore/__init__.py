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

# ruff: noqa: F401,F403
# pylint: disable=unused-import


from . import __
from . import configuration
from . import distribution
from . import environment
from . import inscription
from . import notifications
from . import preparation
from . import state

from .configuration import acquire as acquire_configuration
from .distribution import Information as DistributionInformation
from .environment import update as update_environment
from .inscription import (
    ScribeModes,
    prepare as prepare_scribes,
    prepare_scribe_icecream,
    prepare_scribe_logging,
)
from .notifications import Queue as NotificationsQueue
from .preparation import prepare
from .state import Globals, LocationSpecies


__.reclassify_modules( globals( ) )
