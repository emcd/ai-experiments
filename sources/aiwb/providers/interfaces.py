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


''' Abstract base classes and interfaces. '''


from __future__ import annotations

from . import __


@__.a.runtime_checkable
@__.standard_dataclass
class Client( __.a.Protocol ):
    ''' Interacts with AI provider. '''
    # TODO: Immutable class attributes.

    name: str

    @classmethod
    @__.abstract_member_function
    async def assert_environment(
        selfclass,
        auxdata: __.CoreGlobals,
    ):
        ''' Asserts necessary environment for client. '''
        raise NotImplementedError

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        return __.AccretiveDictionary( name = descriptor[ 'name' ] )

    @classmethod
    @__.abstract_member_function
    async def prepare(
        selfclass,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def survey_models(
        self, auxdata: __.CoreGlobals
    ) -> __.AbstractSequence[ Model ]:
        ''' Returns models available from provider. '''
        raise NotImplementedError


@__.a.runtime_checkable
class ConversationTokenizer( __.a.Protocol ):
    ''' Tokenizes conversation for counting. '''
    # TODO: Immutable class attributes.

    # TODO: count_conversation_tokens

    @__.abstract_member_function
    def count_text_tokens( self, auxdata: __.CoreGlobals, text: str ) -> int:
        ''' Counts tokens in plain text. '''
        raise NotImplementedError


@__.a.runtime_checkable
class Factory( __.a.Protocol ):
    ''' Produces clients. '''
    # TODO: Immutable class attributes.

    @__.abstract_member_function
    async def client_from_descriptor(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ) -> Client:
        ''' Produces client from descriptor dictionary. '''
        raise NotImplementedError


@__.a.runtime_checkable
@__.standard_dataclass
class Model( __.a.Protocol ):
    ''' Represents an AI model. '''
    # TODO: Immutable class attributes.

    name: str
    provider: Client


@__.a.runtime_checkable
@__.standard_dataclass
class ConverserModel( Model, __.a.Protocol ):
    ''' Represents an AI chat model. '''

    tokenizer: ConversationTokenizer

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
