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


''' Converser models for OpenAI AI provider. '''


from . import __


class InvocationsSupportLevel( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Degree to which invocations are supported. '''

    Single      = 'single'      # Mid-2023.
    Concurrent  = 'concurrent'  # Late 2023 and beyond.


@__.standard_dataclass
class Tokenizer( __.ConversationTokenizer ):

    extra_tokens_per_message: int = 3
    extra_tokens_for_name: int = 1
    model_name: str

    # TODO: count_conversation_tokens

    def count_text_tokens( self, auxdata: __.CoreGlobals, text: str ) -> int:
        from tiktoken import encoding_for_model, get_encoding
        try: encoding = encoding_for_model( self.model_name )
        # TODO: Warn about unknown model via callback.
        except KeyError: encoding = get_encoding( 'cl100k_base' )
        return len( encoding.encode( text ) )


@__.standard_dataclass
class Attributes( __.ConverserAttributes ):
    ''' Common attributes for OpenAI chat models. '''

    accepts_behavior_adjustment: bool = False # TODO: Via controls.
    honors_supervisor_instructions: bool = False
    invocations_support_level: InvocationsSupportLevel = (
        InvocationsSupportLevel.Single )
