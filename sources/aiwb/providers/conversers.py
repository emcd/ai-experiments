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


class ConverserModalities( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Supportable input modalities for AI chat models. '''

    Audio       = 'audio'
    Pictures    = 'pictures'
    Text        = 'text'
    # TODO: Video


@__.standard_dataclass
class ConverserTokensLimits:
    ''' Various limits on number of tokens in chat completion. '''

    # TODO? per_prompt
    per_response: int = 0
    total: int = 0


@__.a.runtime_checkable
class ConversationTokenizer( __.a.Protocol ):
    ''' Tokenizes conversation for counting. '''

    # TODO: count_conversation_tokens

    @__.abstract_member_function
    def count_text_tokens( self, auxdata: __.CoreGlobals, text: str ) -> int:
        ''' Counts tokens in plain text. '''
        raise NotImplementedError


@__.standard_dataclass
class ConverserAttributes:
    ''' Common attributes for AI chat models. '''

    accepts_response_multiplicity: bool = False # TODO: Via controls.
    accepts_supervisor_instructions: bool = False
    modalities: __.AbstractSequence[ ConverserModalities ] = (
        ConverserModalities.Text, )
    supports_continuous_response: bool = False
    supports_invocations: bool = False
    tokenizer: ConversationTokenizer
    tokens_limits: ConverserTokensLimits = ConverserTokensLimits( )


@__.standard_dataclass
class ConverserModel( _core.Model ):
    ''' Represents an AI chat model. '''

    @__.abstract_member_function
    async def converse(
        self,
        messages: __.AbstractSequence[ __.MessageCanister ],
        controls: __.AbstractDictionary[ str, __.Control ],
        specials, # TODO: Annotate.
        callbacks, # TODO: Annotate.
    ): # TODO: Annotate return value.
        ''' Interacts with model to complete a round of conversation. '''
        raise NotImplementedError
