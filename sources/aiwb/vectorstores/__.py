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


''' Common functionality and utilities for vectorstores. '''

# pylint: disable=unused-import


from urllib.parse import ParseResult as UrlParseResult, urlparse

from .. import libcore as _libcore
from ..__ import *


def derive_vectorstores_location(
    auxdata: _libcore.Globals, location_info: UrlParseResult
) -> Path:
    ''' Derives vectorstore location from configuration and URL. '''
    return Path( location_info.path.format(
        user_data = auxdata.provide_data_location( 'vectorstores' ) ) )
