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


''' CLI for configuring and executing GUI application. '''


from __future__ import annotations

#from ..libcore.cli import (
#    # Direct imports as public symbols for intentional re-export.
#    ConsoleDisplay,
#    InspectCommand,
#)
from . import __


#@__.standard_dataclass
#class Cli( __.ApplicationCli ):
#    ''' Configuration and execution of GUI application. '''
#
#    # TODO: Implement __call__
#    # TODO: Implement prepare_invocation_args


@__.standard_dataclass
class GuiCommand:
    ''' Initializes and executes GUI engine. '''

    # TODO: Implement.
