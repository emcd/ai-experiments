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


''' Core implementations for Anthropic AI provider. '''


from . import __


@__.substandard_dataclass
class Client( __.Client ):

    async def access_model(
        self,
        auxdata: __.CoreGlobals,
        genus: __.ModelGenera,
        name: str,
    ) -> __.Model:
        # TODO: Implement.
        pass

    async def access_model_default(
        self,
        auxdata: __.CoreGlobals,
        genus: __.ModelGenera,
    ) -> __.Model:
        # TODO: Implement.
        pass

    async def survey_models(
        self,
        auxdata: __.CoreGlobals,
        genus: __.Optional[ __.ModelGenera ] = __.absent,
    ) -> __.AbstractSequence[ __.Model ]:
        # TODO: Implement.
        pass


@__.substandard_dataclass
class AnthropicClient( Client ):

    @classmethod
    async def assert_environment( selfclass, auxdata: __.CoreGlobals ):
        from os import environ
        api_key_name = 'ANTHROPIC_API_KEY'
        if api_key_name not in environ:
            # TODO: Raise appropriate error.
            raise LookupError( f"Missing {api_key_name!r}." )

    @classmethod
    async def from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        factory: __.Factory,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        await selfclass.assert_environment( auxdata )
        return selfclass( **(
            super( ).init_args_from_descriptor(
                auxdata = auxdata,
                factory = factory,
                descriptor = descriptor ) ) )


# TODO: AwsBedrockClient


# TODO: GoogleVertexClient


class Factory( __.Factory ):

    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        #variant = descriptor.get( 'variant' )
        # TODO: Produce AWS Bedrock or Google Vertex variant, if requested.
        client_class = AnthropicClient
        # TODO: Return future.
        return await client_class.from_descriptor(
            auxdata = auxdata, factory = self, descriptor = descriptor )
