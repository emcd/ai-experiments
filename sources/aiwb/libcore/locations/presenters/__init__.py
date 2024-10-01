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


''' Location content presenters.

    A presenter builds on top of a location accessor and uses its underlying
    methods to access content at a location. This content is then transformed
    into a different format or type by the presenter.
'''

# ruff: noqa: F401
# pylint: disable=unused-import


from . import __
from . import text

from .text import FilePresenter as TextFilePresenter


__.reclassify_modules( globals( ) )
