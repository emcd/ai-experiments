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


_supported_model_genera = frozenset( (
    __.ModelGenera.Converser,
) )


@__.standard_dataclass
class Client( __.Client ):

    async def access_model(
        self,
        auxdata: __.CoreGlobals,
        genus: __.ModelGenera,
        name: str,
    ) -> __.Model:
        # TODO? Cache nested dictionary of models for performance.
        try:
            return next(
                model for model
                in await self.survey_models( auxdata, genus = genus )
                if name == model.name )
        except StopIteration:
            # TODO: Raise appropriate type of error.
            raise LookupError(
                f"Could not access {genus.value} model {name!r} "
                f"on provider {self.name!r}." ) from None

    async def access_model_default(
        self,
        auxdata: __.CoreGlobals,
        genus: __.ModelGenera,
    ) -> __.Model:
        defaults = getattr( self.attributes.defaults, f"{genus.value}_model" )
        models = await self.survey_models( auxdata = auxdata, genus = genus )
        models_by_name = __.DictionaryProxy( {
            model.name: model for model in models } )
        try:
            return next(
                models_by_name[ default ] for default in defaults
                if default in models_by_name )
        except StopIteration:
            # TODO: Raise appropriate type of error.
            raise LookupError(
                f"Could not access default {genus.value} model "
                f"on provider {self.name!r}." ) from None

    async def survey_models(
        self,
        auxdata: __.CoreGlobals,
        genus: __.Optional[ __.ModelGenera ] = __.absent,
    ) -> __.AbstractSequence[ __.Model ]:
        integrators = await _cache_acquire_models_integrators( auxdata )
        # TODO: Use list of names rather than dictionary.
        names = await _cache_acquire_models( auxdata )
        models = [ ]
        supported_genera = (
            _supported_model_genera if __.absent is genus
            else _supported_model_genera & { genus } )
        for name in names:
            for genus_ in supported_genera:
                descriptor: __.AbstractDictionary[ str, __.a.Any ] = { }
                for integrator in integrators[ genus_ ]:
                    descriptor = integrator( name, descriptor )
                if not descriptor: continue
                #ic( name, descriptor )
                models.append( self._model_from_descriptor(
                    name = name,
                    genus = genus_,
                    descriptor = descriptor ) )
        return tuple( models )

    def _model_from_descriptor(
        self,
        name: str,
        genus: __.ModelGenera,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.Model:
        match genus:
            case __.ModelGenera.Converser:
                from . import conversers
                return conversers.Model.from_descriptor(
                    client = self, name = name, descriptor = descriptor )
        # TODO: Raise error on unmatched case.

    ## TEMP: Wrappers for Legacy Module-Level Interface
    # TODO: Transition to model-level methods.

    async def chat( self, messages, special_data, controls, callbacks ):
        return await _v0.chat( messages, special_data, controls, callbacks )


# TODO: AzureClient


@__.standard_dataclass
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
    async def from_descriptor(
        selfclass,
        auxdata: __.CoreGlobals,
        factory: __.Factory,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        await selfclass.assert_environment( auxdata )
        # TODO: Return future which acquires models in background.
        # TODO: Cache models on 'survey_models' operation.
        #       Remove dependency on legacy module-level cache.
        _v0.models_.update( await _cache_acquire_models( auxdata ) )
        return selfclass( **(
            super( OpenAIClient, OpenAIClient )
            .init_args_from_descriptor(
                auxdata = auxdata,
                factory = factory,
                descriptor = descriptor ) ) )


@__.standard_dataclass
class Factory( __.Factory ):

    async def produce_client(
        self,
        auxdata: __.CoreGlobals,
        descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ):
        #variant = descriptor.get( 'variant' )
        # TODO: Produce Azure variant, if requested.
        client_class = OpenAIClient
        # TODO: Return future.
        return await client_class.from_descriptor(
            auxdata = auxdata, factory = self, descriptor = descriptor )


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


# TODO? models integrators cache as cell variable of wrapper function
_models_integrators_cache = { }


async def _cache_acquire_models_integrators(
    auxdata: __.CoreGlobals, force: bool = False
):
    # TODO: Register watcher on package data directory to flag updates.
    #       Maybe 'watchfiles.awatch' as asyncio callback with this function.
    # TODO? async mutex in case of clear-update during access
    if force or not _models_integrators_cache:
        _models_integrators_cache.clear( )
        _models_integrators_cache.update(
            await __.acquire_models_integrators( auxdata, __.provider_name ) )
    return __.DictionaryProxy( _models_integrators_cache )


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
