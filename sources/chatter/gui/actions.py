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


from . import base as __


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
def chat( gui ):
    from ..messages import AuxiliaryData
    from .updaters import (
        update_and_save_conversation,
        update_and_save_conversations_index,
        update_message,
        update_messages_post_summarization,
    )
    summarization = gui.toggle_summarize.value
    if 'canned' == gui.selector_user_prompt_class.value:
        prompt = gui.text_canned_prompt.object
        gui.selector_user_prompt_class.value = 'freeform'
    else:
        prompt = gui.text_freeform_prompt.value
        gui.text_freeform_prompt.value = ''
    if prompt:
        auxdata = AuxiliaryData( role = 'Human' )
        _add_message( gui, auxdata, content = prompt )
    with _update_conversation_progress( gui, 'Generating AI response...' ):
        message_gui = _chat( gui )
    update_message( message_gui )
    _add_conversation_indicator_if_necessary( gui )
    update_and_save_conversations_index( gui )
    if summarization:
        update_messages_post_summarization( gui )
        gui.toggle_summarize.value = False
    update_and_save_conversation( gui )
    _invoke_functions_if_desirable( gui, message_gui )


@_update_conversation_status_on_error
def invoke_functions( gui, index ):
    from ..messages import AuxiliaryData
    from .updaters import truncate_conversation
    truncate_conversation( gui, index )
    provider = __.access_ai_provider_current( gui )
    controls = __.package_controls( gui )
    # TODO: Async parallel fanout.
    requests = __.extract_invocation_requests( gui )
    for request in requests:
        with _update_conversation_progress( gui, 'Executing AI function...' ):
            control, message = provider.invoke_function( request, controls )
        auxdata = AuxiliaryData(
            context = control.context,
            mime_type = control.mime_type,
            role = 'Function' )
        _add_message( gui, auxdata, content = message )
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
def search( gui ):
    from ..messages import AuxiliaryData
    from .updaters import update_and_save_conversation
    prompt = gui.text_freeform_prompt.value
    gui.text_freeform_prompt.value = ''
    _add_message( gui, AuxiliaryData( role = 'Human' ), content = prompt )
    documents_count = gui.slider_documents_count.value
    vectorstore = gui.auxdata__.vectorstores[
        gui.selector_vectorstore.value ][ 'instance' ]
    # TODO: Error handling on vector database query failure.
    # TODO: Configurable query method.
    with _update_conversation_progress( gui, 'Querying vector database...' ):
        documents = vectorstore.similarity_search(
            prompt, k = documents_count )
    for document in documents:
        mime_type = document.metadata.get( 'mime_type', 'text/plain' )
        auxdata = AuxiliaryData( role = 'Document', mime_type = mime_type )
        _add_message( gui, auxdata, content = document.page_content )
    update_and_save_conversation( gui )


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
    try: __.extract_invocation_requests( gui )
    except: pass
    else: return
    try: title, labels = _generate_conversation_title( gui )
    except Exception as exc: return
    descriptor.title = title
    descriptor.labels = labels
    add_conversation_indicator( gui, descriptor  )
    update_conversation_hilite( gui, new_descriptor = descriptor )


def _add_message( gui, auxdata, content = None ):
    from .updaters import add_message, autoscroll_document
    message_gui = add_message( gui, auxdata, content = content )
    autoscroll_document( gui )
    return message_gui


def _chat( gui ):
    from ..ai.providers import ChatCallbacks
    messages = __.package_messages( gui )
    controls = __.package_controls( gui )
    special_data = __.package_special_data( gui )
    callbacks = ChatCallbacks(
        allocator = (
            lambda auxdata_: _add_message( gui, auxdata_, content = '' ) ),
        deallocator = (
            lambda handle: gui.column_conversation_history.pop( -1 ) ),
        updater = (
            lambda handle, content:
            _update_gui_on_chat( gui, handle, content ) ),
    )
    provider = gui.selector_provider.auxdata__[ gui.selector_provider.value ]
    return provider.chat( messages, special_data, controls, callbacks )


def _generate_conversation_title( gui ):
    # TODO: Use model-preferred serialization format for title and labels.
    from ..ai.providers import ChatCallbacks, ChatCompletionError
    from ..codecs.json import loads
    from ..messages.templates import render_prompt_template
    template = gui.selector_canned_prompt.auxdata__[
        'JSON: Title + Labels' ][ 'template' ]
    controls = __.package_controls( gui )
    prompt = render_prompt_template( template, controls )
    messages = [
        *__.package_messages( gui )[ 1 : ],
        { 'role': 'Human', 'content': prompt }
    ]
    provider = gui.selector_provider.auxdata__[
        gui.selector_provider.value ]
    # TODO: Use standard set of text capture callbacks.
    callbacks = ChatCallbacks(
        allocator = ( lambda auxdata_: [ ] ),
        updater = ( lambda handle, content: handle.append( content ) ),
    )
    with _update_conversation_progress(
        gui, 'Generating conversation title...'
    ): handle = provider.chat( messages, { }, controls, callbacks )
    response = ''.join( handle )
    __.scribe.info( f"New conversation title: {response}" )
    response = loads( response )
    return response[ 'title' ], response[ 'labels' ]


def _invoke_functions_if_desirable( gui, message_gui ):
    if 'AI' != message_gui.auxdata__.role: return
    if not message_gui.toggle_active.value: return
    if not gui.checkbox_auto_functions.value: return
    try: __.extract_invocation_requests( gui )
    except: return
    invoke_functions( gui, message_gui.index__ )


@__.produce_context_manager
def _update_conversation_progress( gui, message ):
    from .updaters import update_conversation_status
    yield update_conversation_status( gui, message, progress = True )
    update_conversation_status( gui )


def _update_gui_on_chat( gui, handle, content ):
    from .updaters import autoscroll_document
    setattr(
        handle.text_message, 'object',
        getattr( handle.text_message, 'object' ) + content )
    autoscroll_document( gui )
