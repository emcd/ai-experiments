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
    ): canister_components = _chat( components )
    canister_components.canister__.attributes.behaviors = [ 'active' ]
    __.assimilate_canister_dto_to_gui( canister_components )
    _add_conversation_indicator_if_necessary( components )
    await update_and_save_conversations_index( components )
    if summarization:
        update_messages_post_summarization( components )
        components.toggle_summarize.value = False
    await update_and_save_conversation( components )
    _invoke_functions_if_desirable( components, canister_components )


@_update_conversation_status_on_error
def invoke_functions( gui, index ):
    from .updaters import truncate_conversation
    truncate_conversation( gui, index )
    provider = __.access_ai_provider_current( gui )
    controls = __.package_controls( gui )
    # TODO: Async parallel fanout.
    requests = __.extract_invocation_requests( gui )
    for request in requests:
        with _update_conversation_progress( gui, 'Executing AI function...' ):
            canister = provider.invoke_function( request, controls )
        _add_message( gui, canister )
    chat( gui )
    # Elide invocation requests and results, if desired.
    if gui.checkbox_elide_function_history.value:
        history = gui.column_conversation_history
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


def _add_conversation_indicator_if_necessary( gui ):
    from .updaters import (
        add_conversation_indicator,
        update_conversation_hilite,
    )
    conversations = gui.column_conversations_indicators
    descriptor = conversations.current_descriptor__
    if descriptor.identity in conversations.descriptors__: return
    # Do not proceed if we are in a function invocation. Wait for result.
    # Also, some models (e.g., GPT-4) are confused by the invocation.
    if not _detect_ai_completion( gui ): return
    title, labels = _generate_conversation_title( gui )
    descriptor.title = title
    descriptor.labels = labels
    add_conversation_indicator( gui, descriptor  )
    update_conversation_hilite( gui, new_descriptor = descriptor )


def _add_message( gui, canister ):
    from .updaters import add_message, autoscroll_document
    message_gui = add_message( gui, canister )
    autoscroll_document( gui )
    return message_gui


def _chat( gui ):
    from ..providers import ChatCallbacks
    from .__ import access_ai_provider_current
    messages = __.package_messages( gui )
    controls = __.package_controls( gui )
    special_data = __.package_special_data( gui )
    callbacks = ChatCallbacks(
        allocator = (
            lambda canister: _add_message( gui, canister ) ),
        deallocator = (
            lambda canister_gui: gui.column_conversation_history.pop( -1 ) ),
        updater = (
            lambda canister_gui: _update_gui_on_chat( gui, canister_gui ) ),
    )
    provider = access_ai_provider_current( gui )
    return provider.chat( messages, special_data, controls, callbacks )


def _detect_ai_completion( gui, component = None ):
    if None is component: component = gui.column_conversation_history[ -1 ]
    canister = component.gui__.canister__
    if 'AI' != canister.role: return False
    attributes = canister.attributes
    return 'completion' == getattr(
        attributes, 'response_class', 'completion' )


def _generate_conversation_title( gui ):
    from ..codecs.json import loads
    from ..messages.core import Canister
    from ..providers import chat_callbacks_minimal
    from .__ import access_ai_provider_current
    provider = access_ai_provider_current( gui )
    controls = __.package_controls( gui )
    provider_format_name = provider.provide_format_name( controls )
    prompt = (
        gui.auxdata__.prompts.definitions[ 'Title + Labels' ]
        .produce_prompt( values = { 'format': provider_format_name } ) )
    canister = Canister( role = 'Human' ).add_content(
        prompt.render( gui.auxdata__ ) )
    messages = [ *__.package_messages( gui )[ 1 : ], canister ]
    with _update_conversation_progress(
        gui, 'Generating conversation title...'
    ):
        ai_canister = provider.chat(
            messages, { }, controls, chat_callbacks_minimal )
    response = ai_canister[ 0 ].data
    __.scribe.info( f"New conversation title: {response}" )
    response = provider.parse_data( response, controls )
    return response[ 'title' ], response[ 'labels' ]


def _invoke_functions_if_desirable( gui, message_gui ):
    if 'AI' != message_gui.canister__.role: return
    if not message_gui.toggle_active.value: return
    if not gui.checkbox_auto_functions.value: return
    try: __.extract_invocation_requests( gui )
    except Exception as exc:
        ic( exc )
        return
    invoke_functions( gui, message_gui.index__ )


@__.produce_context_manager
def _update_conversation_progress( gui, message ):
    from .updaters import update_conversation_status
    yield update_conversation_status( gui, message, progress = True )
    update_conversation_status( gui )


def _update_gui_on_chat( gui, canister_gui ):
    from .__ import assimilate_canister_dto_to_gui
    from .updaters import autoscroll_document
    assimilate_canister_dto_to_gui( canister_gui )
    #setattr(
    #    handle.text_message, 'object',
    #    getattr( handle.text_message, 'object' ) + content )
    autoscroll_document( gui )
