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


''' Preparation for Anthropic AI provider. '''


from . import __
from . import clients as _clients


async def prepare( auxdata: __.CoreGlobals ):
    ''' Installs dependencies and returns factory. '''
    # TODO: Install dependencies in isolated environment, if necessary.
    #       Packages: anthropic
    return _clients.Factory( )

_package_name = __package__.rsplit( '.', maxsplit = 1 )[ -1 ]
__.preparers_registry[ _package_name ] = prepare
