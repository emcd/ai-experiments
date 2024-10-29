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


# We do not want to import 'anthropic' package on module initialization,
# as it is not guaranteed to be available then. However, we can appease
# typecheckers by pretending as though it is available.
if __.a.TYPE_CHECKING:
    from anthropic import AsyncAnthropic as _AsyncAnthropic  # type: ignore
else:
    _AsyncAnthropic: __.a.TypeAlias = __.a.Any


class ClientVariants( __.Enum ):
    ''' Anthropic client variants. '''

    Anthropic =     'anthropic'
    AwsBedrock =    'aws-bedrock'
    GoogleVertex =  'google-vertex'


# TODO: Move lists of models to providers data.
_model_names = __.DictionaryProxy( {
    ClientVariants.Anthropic: (
        'claude-3-haiku-20240307',
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3.5-sonnet-20241022',
    ),
    ClientVariants.AwsBedrock: (
        'anthropic.claude-3-haiku-20240307-v1:0',
        'anthropic.claude-3-opus-20240229-v1:0',
        'anthropic.claude-3-sonnet-20240229-v1:0',
        'anthropic.claude-3.5-sonnet-20241022-v2:0',
    ),
    ClientVariants.GoogleVertex: (
        'claude-3-haiku@20240307',
        'claude-3-opus@20240229',
        'claude-3-sonnet@20240229',
        'claude-3.5-sonnet-v20241022',
    ),
} )
_supported_model_genera = frozenset( (
    __.ModelGenera.Converser,
) )


class Client( __.Client, class_decorators = ( __.standard_dataclass, ) ):

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
#        supported_genera = __.select_model_genera(
#            _supported_model_genera, genus )
#        in_cache, models = _consult_models_cache( self, supported_genera )
#        if in_cache: return models
        models = [ ]
#        integrators = (
#            await __.memcache_acquire_models_integrators(
#                auxdata, provider = self.provider ) )
#        names = await _acquire_models( auxdata, self )
        # TODO: Implement.
        return tuple( models )


class AnthropicClient( Client, class_decorators = ( __.standard_dataclass, ) ):

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
        provider: __.Provider,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        await selfclass.assert_environment( auxdata )
        # TODO: Return future which acquires models in background.
        return selfclass( **(
            super( ).init_args_from_descriptor(
                auxdata = auxdata,
                provider = provider,
                descriptor = descriptor ) ) )

    def produce_implement( self ) -> _AsyncAnthropic:
        from anthropic import AsyncAnthropic
        return AsyncAnthropic( )


# TODO: AwsBedrockClient


# TODO: GoogleVertexClient


_client_classes = __.DictionaryProxy( {
    ClientVariants.Anthropic: AnthropicClient,
    # TODO: Other variants.
} )
class Provider( __.Provider, class_decorators = ( __.standard_dataclass, ) ):

    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        variant = descriptor.get( 'variant', ClientVariants.Anthropic.value )
        client_class = _client_classes[ ClientVariants( variant ) ]
        # TODO: Return future.
        return await client_class.from_descriptor(
            auxdata = auxdata, provider = self, descriptor = descriptor )
