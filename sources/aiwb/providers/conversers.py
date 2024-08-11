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


''' Base converser classes and functions for AI providers. '''


from __future__ import annotations

from . import __
from . import core as _core


@__.dataclass( frozen = True, kw_only = True, slots = True )
class ConverserModel( _core.Model ):
    ''' Represents an AI chat model. '''

    @__.abstract_member_function
    async def converse(
        messages: __.AbstractSequence[ __.MessageCanister ],
        controls: __.AbstractDictionary[ __.Control ],
        specials, # TODO: Annotate.
        callbacks, # TODO: Annotate.
    ): # TODO: Annotate return value.
        ''' Interacts with model to complete a round of conversation. '''
        raise NotImplementedError
