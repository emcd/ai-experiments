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


''' Core entities for use with workbench applications. '''

# ruff: noqa: F401,F403,F405
# pylint: disable=unused-import


from . import __
from . import cli
from . import preparation
from . import state

from .cli import Cli, execute_cli
from .preparation import prepare
from .state import Globals


def main( ):
    ''' Entrypoint for utility to inspect and test library core. '''
    execute_cli( )


__.reclassify_modules( globals( ) )
