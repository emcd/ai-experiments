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


''' Clients for OpenAI AI provider. '''


from . import __
from . import v0 as _v0


_supported_model_species = frozenset( (
    __.ModelSpecies.Converser,
) )


class Client( __.Client ):

    async def survey_models(
        self, auxdata: __.CoreGlobals
    ) -> __.AbstractSequence[ __.Model ]:
        integrators = (
            await __.acquire_models_integrators( auxdata, __.provider_name ) )
        # TODO: Use list of names rather than dictionary.
        names = await _cache_acquire_models( auxdata )
        models = [ ]
        for name in names:
            for species in _supported_model_species:
                descriptor: __.AbstractDictionary[ str, __.a.Any ] = { }
                for integrator in integrators[ species ]:
                    descriptor = integrator( name, descriptor )
                if not descriptor: continue
                #ic( name, descriptor )
                models.append( self._model_from_descriptor(
                    name = name, species = species, descriptor = descriptor ) )
        return tuple( models )

    def _model_from_descriptor(
        self,
        name: str,
        species: __.ModelSpecies,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.Model:
        match species:
            case __.ModelSpecies.Converser:
                from . import conversers
                return conversers.Model.from_descriptor(
                    client = self, name = name, descriptor = descriptor )
        # TODO: Raise error on unmatched case.

    ## TEMP: Wrappers for Legacy Module-Level Interface
    # TODO: Transition to model-level methods.

    def access_model_data( self, model_name, data_name ):
        return _v0.access_model_data( model_name, data_name )

    async def chat( self, messages, special_data, controls, callbacks ):
        return await _v0.chat( messages, special_data, controls, callbacks )

    def count_conversation_tokens( self, messages, special_data, controls ):
        return _v0.count_conversation_tokens(
            messages, special_data, controls )

    def count_text_tokens( self, text, model_name ):
        return _v0.count_text_tokens( text, model_name )

    def extract_invocation_requests( self, canister, auxdata, invocables ):
        return _v0.extract_invocation_requests(
            canister, auxdata, invocables )

    async def invoke_function( self, request, controls ):
        return await _v0.invoke_function( request, controls )

    def parse_data( self, content, controls ):
        return _v0.parse_data( content, controls )

    def provide_chat_models( self ):
        return _v0.provide_chat_models( )

    def provide_format_name( self, controls ):
        return _v0.provide_format_name( controls )

    def render_data( self, content, controls ):
        return _v0.render_data( content, controls )

    def select_default_model( self, models, auxdata ):
        return _v0.select_default_model( models, auxdata )


# TODO: AzureClient


class OpenAIClient( Client ):

    @classmethod
    async def assert_environment( selfclass, auxdata: __.CoreGlobals ):
        from os import environ
        api_key_name = 'OPENAI_API_KEY'
        if api_key_name not in environ:
            # TODO: Raise appropriate error.
            raise LookupError( f"Missing {api_key_name!r}." )
        # TODO: Warn on missing 'OPENAI_ORG_ID' and 'OPENAI_PROJECT_ID'.

    @classmethod
    async def prepare(
        selfclass,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        await selfclass.assert_environment( auxdata )
        # TODO: Return future which acquires models in background.
        # TODO: Cache models on 'survey_models' operation.
        #       Remove dependency on legacy module-level cache.
        _v0.models_.update( await _cache_acquire_models( auxdata ) )
        return selfclass(
            **super( ).init_args_from_descriptor( auxdata, descriptor ) )


class Factory( __.Factory ):

    async def client_from_descriptor(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        #variant = descriptor.get( 'variant' )
        # TODO: Produce Azure variant, if requested.
        # TODO: Return future.
        return await OpenAIClient.prepare( auxdata, descriptor )


async def _cache_acquire_models( auxdata ):
    # TODO: Add provider client as argument.
    # TODO? Use cache accessor from libcore.locations.
    from json import dumps, loads
    from aiofiles import open as open_
    from openai import APIError
    scribe = __.acquire_scribe( __package__ )
    file = auxdata.provide_cache_location(
        'providers', 'openai', 'models.json' )
    if file.is_file( ):
        # TODO: Get cache expiration interval from configuration.
        interval = __.TimeDelta( seconds = 4 * 60 * 60 ) # 4 hours
        then = ( __.DateTime.now( __.TimeZone.utc ) - interval ).timestamp( )
        if file.stat( ).st_mtime > then:
            async with open_( file ) as stream:
                return loads( await stream.read( ) )
    try: models = await _discover_models_from_api( )
    except APIError as exc:
        if file.is_file( ):
            auxdata.notifications.enqueue_apprisal(
                summary = "Connection error. Loading stale models cache.",
                exception = exc,
                scribe = scribe )
            async with open_( file ) as stream:
                return loads( await stream.read( ) )
        raise
    file.parent.mkdir( exist_ok = True, parents = True )
    async with open_( file, 'w' ) as stream:
        await stream.write( dumps( models, indent = 4 ) )
    return models


# https://platform.openai.com/docs/guides/function-calling/supported-models
_function_support_models = frozenset( (
    # TODO: Confirm legacy function call support in gpt-4o.
    'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
    'gpt-4', 'gpt-4-32k', 'gpt-4-turbo',
    'gpt-4o-mini', 'gpt-4o', 'chatgpt-4o-latest',
    #'o1-mini', 'o1-preview',
    'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0125',
    'gpt-3.5-turbo-16k-0613',
    'gpt-4-0613', 'gpt-4-1106-preview', 'gpt-4-0125-preview',
    'gpt-4-32k-0613',
    'gpt-4-vision-preview', 'gpt-4-1106-vision-preview',
    'gpt-4-turbo-2024-04-09', 'gpt-4-turbo-preview',
    'gpt-4o-mini-2024-07-18',
    'gpt-4o-2024-05-13', 'gpt-4o-2024-08-06',
) )
_multifunction_support_models = frozenset( (
    'gpt-3.5-turbo', 'gpt-4-turbo',
    'gpt-4o-mini', 'gpt-4o', 'chatgpt-4o-latest',
    #'o1-mini', 'o1-preview',
    'gpt-3.5-turbo-1106', 'gpt-3.5-turbo-0125',
    'gpt-4-1106-preview', 'gpt-4-0125-preview',
    'gpt-4-vision-preview', 'gpt-4-1106-vision-preview',
    'gpt-4-turbo-2024-04-09', 'gpt-4-turbo-preview',
    'gpt-4o-mini-2024-07-18',
    'gpt-4o-2024-05-13', 'gpt-4o-2024-08-06',
) )
# TODO: Multifunction support by model family.
# https://platform.openai.com/docs/models
_model_family_context_window_sizes = __.DictionaryProxy( {
    'gpt-3.5-turbo': 16_385,
    'gpt-4-32k': 32_768,
    'gpt-4-0125': 128_000,
    'gpt-4-1106': 128_000,
    'gpt-4-turbo': 128_000,
    'gpt-4-vision': 128_000,
    'gpt-4o-mini': 128_000,
    'gpt-4o': 128_000,
    'o1-mini': 128_000,
    'o1-preview': 128_000,
} )
_model_context_window_sizes = {
    'gpt-3.5-turbo-0301': 4_096,
    'gpt-3.5-turbo-0613': 4_096,
    'chatgpt-4o-latest': 128_000,
}
# TODO: Track support for JSON output and StructuredOutput.
async def _discover_models_from_api( ):
    # TODO: Replace with model attribute integrators and model objects.
    from operator import attrgetter
    from accretive import ProducerDictionary
    from openai import AsyncOpenAI
    model_names = sorted( map(
        attrgetter( 'id' ), ( await AsyncOpenAI( ).models.list( ) ).data ) )
    sysprompt_honor = ProducerDictionary( lambda: False )
    sysprompt_honor.update( {
        #'gpt-3.5-turbo-0613': True,
        #'gpt-3.5-turbo-16k-0613': True,
        model_name: True for model_name in model_names
        if model_name.startswith( (
            'chatgpt-4o-', 'gpt-4', # 'o1-',
        ) ) } )
    function_support = ProducerDictionary( lambda: False )
    function_support.update( {
        model_name: True for model_name in model_names
        if model_name in _function_support_models } )
    multifunction_support = ProducerDictionary( lambda: False )
    multifunction_support.update( {
        model_name: True for model_name in model_names
        if model_name in _multifunction_support_models } )
    # Legacy 'gpt-3.5-turbo' has a 4096 tokens limit.
    tokens_limits = ProducerDictionary( lambda: 4096 )
    for model_name in model_names:
        if model_name in _model_context_window_sizes:
            tokens_limits[ model_name ] = (
                _model_context_window_sizes[ model_name ] )
            continue
        for model_family_name, tokens_limit \
        in _model_family_context_window_sizes.items( ):
            if model_name.startswith( model_family_name ):
                tokens_limits[ model_name ] = tokens_limit
                break
    return {
        model_name: {
            'honors-system-prompt': sysprompt_honor[ model_name ],
            'supports-functions': function_support[ model_name ],
            'supports-multifunctions': multifunction_support[ model_name ],
            'tokens-limit': tokens_limits[ model_name ],
        }
        for model_name in model_names
    }
