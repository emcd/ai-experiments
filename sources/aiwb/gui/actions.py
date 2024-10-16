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


''' User actions in Holoviz Panel GUI. '''


from . import __
from . import conversations as _conversations
from . import invocables as _invocables
from . import providers as _providers


def _update_conversation_status_on_error( invocable ):
    from functools import wraps
    from .updaters import update_conversation_status

    @wraps( invocable )
    def invoker( gui, *posargs, **nomargs ):
        update_conversation_status( gui ) # Clear any extant status.
        try: return invocable( gui, *posargs, **nomargs )
        except BaseException as exc:
            update_conversation_status( gui, exc )
            raise # TODO: Remove after traceback display is implemented.

    return invoker


@_update_conversation_status_on_error
async def chat( components ):
    from ..messages.core import Canister
    from .updaters import (
        update_and_save_conversation,
        update_and_save_conversations_index,
        update_messages_post_summarization,
    )
    summarization = components.toggle_summarize.value
    if 'canned' == components.selector_user_prompt_class.value:
        prompt = components.text_canned_prompt.object
        components.selector_user_prompt_class.value = 'freeform'
    else:
        prompt = components.text_freeform_prompt.value
        components.text_freeform_prompt.value = ''
    if prompt:
        canister = Canister( role = 'Human' ).add_content( prompt )
        _add_message( components, canister )
    with _update_conversation_progress(
        components, 'Generating AI response...'
    ): canister_components = await _chat( components )
    canister_components.canister__.attributes.behaviors = [ 'active' ]
    _conversations.assimilate_canister_dto_to_gui( canister_components )
    await _add_conversation_indicator_if_necessary( components )
    await update_and_save_conversations_index( components )
    if summarization:
        update_messages_post_summarization( components )
        components.toggle_summarize.value = False
    await update_and_save_conversation( components )
    await _use_invocables_if_desirable( components, canister_components )


@_update_conversation_status_on_error
async def use_invocables(
    components,
    index,
    silent_extraction_failure = False,
):
    ''' Runs invocables via current AI provider for context. '''
    from .invocables import extract_invocation_requests
    from .updaters import truncate_conversation
    truncate_conversation( components, index )
    model = _providers.access_model_selection( components )
    processor = model.produce_invocations_processor( )
    requests = (
        extract_invocation_requests(
            components,
            silent_extraction_failure = silent_extraction_failure ) )
    if not requests: return
    invokers = tuple( processor( request ) for request in requests )
    with _update_conversation_progress( components, 'Invoking tools...' ):
        canisters = await __.gather_async( *invokers )
    for canister in canisters: _add_message( components, canister )
    await chat( components )
    # Elide invocation requests and results, if desired.
    if components.checkbox_elide_function_history.value:
        history = components.column_conversation_history
        results_count = len( requests )
        # TODO? Only elide results when function advises elision.
        for i in range( -results_count - 2, -1 ):
            history[ i ].gui__.toggle_active.value = (
                history[ i ].gui__.toggle_pinned.value )


@_update_conversation_status_on_error
async def search( components ):
    from ..messages.core import Canister
    from .updaters import update_and_save_conversation
    prompt = components.text_freeform_prompt.value
    components.text_freeform_prompt.value = ''
    canister = Canister( role = 'Human' ).add_content( prompt )
    _add_message( components, canister )
    documents_count = components.slider_documents_count.value
    vectorstore = components.auxdata__.vectorstores[
        components.selector_vectorstore.value ][ 'instance' ]
    # TODO: Error handling on vector database query failure.
    # TODO: Configurable query method.
    with _update_conversation_progress(
        components, 'Querying vector database...'
    ):
        documents = vectorstore.similarity_search(
            prompt, k = documents_count )
    for document in documents:
        mimetype = document.metadata.get( 'mime_type', 'text/plain' )
        canister = Canister( role = 'Document' ).add_content(
            document.page_content, mimetype = mimetype )
        _add_message( components, canister )
    await update_and_save_conversation( components )


async def _add_conversation_indicator_if_necessary( components ):
    from .updaters import (
        add_conversation_indicator,
        update_conversation_hilite,
    )
    conversations = components.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    if descriptor.identity in conversations.descriptors__: return
    # Do not proceed if we are in a function invocation. Wait for result.
    # Also, some models (e.g., GPT-4) are confused by the invocation.
    if not _detect_ai_completion( components ): return
    title, labels = await _generate_conversation_title( components )
    descriptor.title = title
    descriptor.labels = labels
    add_conversation_indicator( components, descriptor  )
    update_conversation_hilite( components, new_descriptor = descriptor )


def _add_message( gui, canister ):
    from .updaters import add_message, autoscroll_document
    message_gui = add_message( gui, canister )
    autoscroll_document( gui )
    return message_gui


async def _chat( components ):
    from ..providers import ChatCallbacks
    messages = _conversations.package_messages( components )
    controls = _providers.package_controls( components )
    special_data = _invocables.package_invocables( components )
    callbacks = ChatCallbacks(
        allocator = (
            lambda canister: _add_message( components, canister ) ),
        deallocator = (
            lambda canister_gui:
                components.column_conversation_history.pop( -1 ) ),
        updater = (
            lambda canister_components:
                _update_gui_on_chat( components, canister_components ) ),
    )
    model = _providers.access_model_selection( components )
    return await model.converse_v0(
        messages, special_data, controls, callbacks )


def _detect_ai_completion( gui, component = None ):
    if None is component: component = gui.column_conversation_history[ -1 ]
    canister = component.gui__.canister__
    if 'AI' != canister.role: return False
    attributes = canister.attributes
    return 'completion' == getattr(
        attributes, 'response_class', 'completion' )


async def _generate_conversation_title( components ):
    from ..messages.core import Canister
    from ..providers import chat_callbacks_minimal
    scribe = __.acquire_scribe( __package__ )
    model = _providers.access_model_selection( components )
    controls = _providers.package_controls( components )
    format_name = model.attendants.serde.preferences.response_data.value
    prompt = (
        components.auxdata__.prompts.definitions[ 'Title + Labels' ]
        .produce_prompt( values = { 'format': format_name } ) )
    canister = Canister( role = 'Human' ).add_content(
        prompt.render( components.auxdata__ ) )
    messages = [
        *_conversations.package_messages( components )[ 1 : ], canister ]
    with _update_conversation_progress(
        components, 'Generating conversation title...'
    ):
        ai_canister = await model.converse_v0(
            messages, { }, controls, chat_callbacks_minimal )
    response = ai_canister[ 0 ].data
    scribe.info( f"New conversation title: {response}" )
    response = model.attendants.serde.deserialize_data( response )
    return response[ 'title' ], response[ 'labels' ]


async def _use_invocables_if_desirable( components, message_components ):
    if 'AI' != message_components.canister__.role: return
    if not message_components.toggle_active.value: return
    if not components.checkbox_auto_functions.value: return
    await use_invocables(
        components, message_components.index__,
        silent_extraction_failure = True )


@__.exit_manager
def _update_conversation_progress( gui, message ):
    from .updaters import update_conversation_status
    yield update_conversation_status( gui, message, progress = True )
    update_conversation_status( gui )


def _update_gui_on_chat( gui, canister_gui ):
    from .updaters import autoscroll_document
    _conversations.assimilate_canister_dto_to_gui( canister_gui )
    #setattr(
    #    handle.text_message, 'object',
    #    getattr( handle.text_message, 'object' ) + content )
    autoscroll_document( gui )
