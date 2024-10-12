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

    honors_supervisor_instructions: bool = False
    invocations_support_level: InvocationsSupportLevel = (
        InvocationsSupportLevel.Single )

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        args = (
            super( Attributes, Attributes )
            .init_args_from_descriptor( descriptor ) )
        sdescriptor = descriptor.get( 'special', { } )
        for arg_name in ( 'honors-supervisor-instructions', ):
            arg = sdescriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        if 'invocations-support-level' in sdescriptor:
            args[ 'invocations_support_level' ] = (
                InvocationsSupportLevel(
                    sdescriptor[ 'invocations-support-level' ] ) )
        return selfclass( **args )


@__.standard_dataclass
class Model( __.ConverserModel ):

    @classmethod
    def from_descriptor(
        selfclass,
        client: __.Client,
        name: str,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        descriptor_ = dict( descriptor )
        attributes = Attributes.from_descriptor( descriptor_ )
        return selfclass(
            name = name, client = client, attributes = attributes )

    async def converse_v0(
        self,
        messages: __.AbstractSequence[ __.MessageCanister ],
        controls: __.AbstractDictionary[ str, __.Control ],
        specials,
        callbacks,
    ):
        # TODO: Implement.
        pass

    def deserialize_data( self, data: str ) -> __.a.Any:
        data_format = self.attributes.format_preferences.response_data
        match data_format:
            case __.DataFormatPreferences.JSON:
                from ....codecs.json import loads
                return loads( data )
        raise __.SupportError(
            f"Cannot deserialize data from {data_format.value} format." )

    def serialize_data( self, data: __.a.Any ) -> str:
        data_format = self.attributes.format_preferences.request_data
        match data_format:
            case __.DataFormatPreferences.JSON:
                from json import dumps
                return dumps( data )
        raise __.SupportError(
            f"Cannot serialize data to {data_format.value} format." )
