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


''' Core classes and functions for AI providers. '''


from __future__ import annotations

from . import __


class ChatCompletionError( Exception ): pass


@__.dataclass( frozen = True, kw_only = True, slots = True )
class ChatCallbacks:
    ''' Callbacks for AI provider to correspond with caller. '''

    allocator: __.a.Callable[ [ __.MessageCanister ], __.a.Any ] = (
        lambda canister: canister )
    deallocator: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda handle: None )
    failure_notifier: __.a.Callable[ [ str ], None ] = (
        lambda status: None )
    progress_notifier: __.a.Callable[ [ int ], None ] = (
        lambda tokens_count: None )
    success_notifier: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda status: None )
    updater: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda handle: None )


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


@__.standard_dataclass
class ConverserAttributes:
    ''' Common attributes for AI chat models. '''

    accepts_response_multiplicity: bool = False # TODO: Via controls.
    accepts_supervisor_instructions: bool = False
    modalities: __.AbstractSequence[ ConverserModalities ] = (
        ConverserModalities.Text, )
    supports_continuous_response: bool = False
    supports_invocations: bool = False
    tokens_limits: ConverserTokensLimits = ConverserTokensLimits( )


chat_callbacks_minimal = ChatCallbacks( )
# TODO: Use accretive validator dictionary for preparers registry.
