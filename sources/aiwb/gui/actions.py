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


def _update_conversation_status_on_error( actor ):
    from functools import wraps
    from .updaters import update_conversation_status

    @wraps( actor )
    async def report_on_action( components, *posargs, **nomargs ):
        update_conversation_status( components ) # Clear any extant status.
        try: return await actor( components, *posargs, **nomargs )
        except Exception as exc:
            update_conversation_status( components, content = exc )
            raise # TODO: Remove after traceback display is implemented.
        # Allow non-error exceptions (e.g., SystemExit) to blow through.

    return report_on_action


@_update_conversation_status_on_error
async def chat( components ):
    ''' Converses with AI model. '''
    from .updaters import (
        update_and_save_conversation,
        update_and_save_conversations_index,
        update_messages_post_summarization,
    )
    summarization = components.toggle_summarize.value
    match components.selector_user_prompt_class.value:
        case 'canned':
            prompt = components.text_canned_prompt.object
            components.selector_user_prompt_class.value = 'freeform'
        case _:
            prompt = components.text_freeform_prompt.value
            components.text_freeform_prompt.clear( )
    if prompt:
        canister = __.UserMessageCanister( ).add_content( prompt )
        _add_message( components, canister )
    while True: # TODO? Cutoff after N rounds.
        with _update_conversation_progress(
            components, 'Generating AI response...'
        ): message_components = await _chat( components )
        message_components.canister__.attributes.behaviors = [ 'active' ]
        _conversations.assimilate_canister_dto_to_gui( message_components )
        if not await _check_invocation_requests(
            components, message_components
        ): break
        await use_invocables( components, message_components.index__ )
        await _deactivate_duplicate_invocations( components )
    await _add_conversation_indicator_if_necessary( components )
    await update_and_save_conversations_index( components )
    if summarization:
        update_messages_post_summarization( components )
        components.toggle_summarize.value = False
    await update_and_save_conversation( components )


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
    model = await _providers.access_model_selection( components )
    requests = (
        await extract_invocation_requests(
            components,
            silent_extraction_failure = silent_extraction_failure ) )
    if not requests: return
    conversers = model.client.conversers
    invokers = tuple(
        conversers.execute_invocation( model, request )
        for request in requests )
    with _update_conversation_progress( components, 'Invoking tools...' ):
        canisters = await __.asyncf.gather_async( *invokers )
    for canister in canisters: _add_message( components, canister )
# TODO: Move invocation elision to chat postprocessing.
# TODO: Properly elide based on presence of invocation data.
# TODO: Add enablement boolean for invocation data.
#    # Elide invocation requests and results, if desired.
#    if components.checkbox_elide_function_history.value:
#        history = components.column_conversation_history
#        results_count = len( requests )
#        # TODO? Only elide results when function advises elision.
#        for i in range( -results_count - 2, -1 ):
#            history[ i ].gui__.toggle_active.value = (
#                history[ i ].gui__.toggle_pinned.value )


@_update_conversation_status_on_error
async def search( components ):
    ''' Performs search against vector databases. '''
    from .updaters import update_and_save_conversation
    prompt = components.text_freeform_prompt.value
    components.text_freeform_prompt.clear( )
    canister = __.UserMessageCanister( ).add_content( prompt )
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
        canister_d = (
            __.DocumentMessageCanister( )
            .add_content( document.page_content, mimetype = mimetype ) )
        _add_message( components, canister_d )
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
    title, labels = await generate_conversation_title( components )
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
    messages = _conversations.package_messages( components )
    controls = _providers.package_controls( components )
    special_data = await _invocables.package_invocables( components )
    callbacks = __.ConversationReactors(
        allocator = (
            lambda canister: _add_message( components, canister ) ),
        deallocator = (
            lambda canister_gui:
                components.column_conversation_history.pop( -1 ) ),
        updater = (
            lambda canister_components:
                _update_gui_on_chat( components, canister_components ) ),
    )
    model = await _providers.access_model_selection( components )
    return await model.client.conversers.converse_v0(
        model, messages, special_data, controls, callbacks )


def _detect_ai_completion( components, component = None ):
    component_ = (
        components.column_conversation_history[ -1 ]
        if component is None else component )
    if component_ is None: return False
    canister = component_.gui__.canister__
    match canister.role:
        case __.MessageRole.Assistant:
            return not hasattr( canister.attributes, 'invocation_data' )
        case _: return False


@_update_conversation_status_on_error
async def generate_conversation_title( components ):
    ''' Generates conversation title from history. '''
    scribe = __.acquire_scribe( __package__ )
    model = await _providers.access_model_selection( components )
    controls = _providers.package_controls( components )
    format_name = model.attributes.format_preferences.response_data.value
    prompt = (
        components.auxdata__.prompts.definitions[ 'Title + Labels' ]
        .produce_prompt( values = { 'format': format_name } ) )
    canister = (
        __.UserMessageCanister( )
        .add_content( prompt.render( components.auxdata__ ) ) )
    messages = [
        *_conversations.package_messages( components )[ 1 : ], canister ]
    with _update_conversation_progress(
        components, 'Generating conversation title...'
    ):
        ai_canister = await model.client.conversers.converse_v0(
            model, messages, { }, controls, __.conversation_reactors_minimal )
    response = ai_canister[ 0 ].data
    scribe.info( f"New conversation title: {response}" )
    response = model.client.conversers.deserialize_data( model, response )
    return response[ 'title' ], response[ 'labels' ]


async def _check_invocation_requests( components, message_components ) -> bool:
    canister = message_components.canister__
    match canister.role:
        case __.MessageRole.Assistant:
            if hasattr( canister.attributes, 'invocation_data' ): pass
            else: return False
        case __.MessageRole.Invocation: pass
        case _: return False
    if not message_components.toggle_active.value: return False
    if not components.checkbox_auto_functions.value: return False # noqa: SIM103
    return True


async def _deactivate_duplicate_invocations( components ):
    if not components.checkbox_deduplicate_invocations.value: return
    deactivations = await _deduplicate_invocations( components )
    for index in deactivations:
        invocation_components = (
            components.column_conversation_history[ index ].gui__ )
        invocation_canister = invocation_components.canister__
        behaviors = getattr( invocation_canister.attributes, 'behaviors', [ ] )
        behaviors = [
            behavior for behavior in behaviors if 'active' != behavior ]
        invocation_canister.attributes.behaviors = behaviors
        _conversations.assimilate_canister_dto_to_gui( invocation_components )


async def _deduplicate_invocations(  # noqa: PLR0915
    components
) -> __.cabc.Sequence[ int ]:
    ''' Deduplicates invocations and their results.

        Per OpenSpec define-invocation-data-contract (Provider-Neutral
        Correlation IDs, scenarios "Correlation identifier drives
        dedup" and "Correlation identifier is the result-pairing
        key"): two invocation results with the same harness-minted
        correlation identifier are treated as duplicates and the
        older result is superseded by the newer one without inspecting
        provider-shaped envelopes. Request-to-result pairing is by the
        ``correlation_id`` on the normalized descriptor plus
        ``attributes.correlation_id`` on the result canister; the
        historical positional ``result_index = i + j + 1`` is no
        longer the primary surface. Iteration over the history column
        continues to use the positional index for unrelated
        operations (the "all duplicates, disable the canister
        itself" shortcut); only the result-pairing lookup replaces
        ``i + j + 1``. The whole-invocation deactivation behavior is
        preserved: an invocation canister whose every call has been
        superseded by a newer invocation is deactivated wholesale. The
        ``all_duplicates`` flag is cleared only when a call is NOT yet
        matched (and thus registers as a candidate deduper for older
        invocations), not when it is itself matched by a newer one. '''
    history = components.column_conversation_history
    correlation_id_to_index = _result_canister_index_by_id( history )
    deduplicators: __.accret.Dictionary[ str, list ] = (
        __.accret.Dictionary( ) )
    invokers = components.auxdata__.invocables.invokers
    deactivations = [ ]
    for i in range( len( history ) - 1, -1, -1 ): # Process in reverse order
        message_components = history[ i ].gui__
        canister = message_components.canister__
        if not hasattr( canister.attributes, 'invocation_data' ): continue
        if not message_components.toggle_active.value: continue
        invocation_data = canister.attributes.invocation_data
        all_duplicates = True
        for j, invocation in enumerate( invocation_data ):
            name = invocation[ 'name' ]
            if name not in invokers:
                all_duplicates = False
                continue
            invoker = invokers[ name ]
            if invoker.deduplicator_class is None:
                all_duplicates = False
                continue
            duplicate_target = _scan_newer_deduplicators(
                j, invocation, deduplicators,
                correlation_id_to_index, history, i )
            if duplicate_target is not None:
                if duplicate_target >= 0:
                    deactivations.append( duplicate_target )
                # Per the historical semantics, finding that this
                # call is itself a duplicate of a newer invocation
                # does NOT clear ``all_duplicates``. The flag is
                # cleared only when this call is NOT yet matched
                # (and thus registers as a candidate deduper for older
                # invocations), so the outer whole-invocation
                # deactivation shortcut still fires when every call
                # in the canister has been superseded.
                continue
            # Not duplicated, so this one might duplicate older ones.
            # Per scenario "Correlation identifier drives dedup": this
            # invocation is the OLDER relative to anything dedup-matched
            # later. Its durable correlation_id is recorded alongside
            # the dedup instance so a future older call's successor can
            # pair to this invocation's result via the index.
            _register_newer_dedup( invocation, invoker, deduplicators )
            all_duplicates = False
        # If all calls would be deduplicated, we can disable invocation.
        if (    all_duplicates
            and canister.role is __.MessageRole.Invocation
            and not message_components.toggle_pinned.value
        ): deactivations.append( i )
    return tuple( sorted( deactivations, reverse = True ) )


def _scan_newer_deduplicators(  # noqa: PLR0913, PLR0917
    j, invocation, deduplicators,
    correlation_id_to_index, history, index_of_invocation_canister,
):
    ''' Returns this invocation's result index if a newer invocation
        registered in ``deduplicators`` matches this invocation's args.
        Iteration is newest-first, so by the time this is called the
        dictionaries contain entries for every invocation the current
        one is older than. Returns ``-1`` if a newer duplicate exists
        but its result is already deactivated or pinned, and ``None``
        when no newer duplicate exists.

        Per scenario "Correlation identifier is the result-pairing
        key": the lookup prefers this invocation's own
        ``correlation_id`` (the older one) so the result can be found
        by durable id. The positional fallback ``i + j + 1`` is
        preserved for pre-R2 / un-hydrated descriptors whose
        correlation_id is None. '''
    name = invocation[ 'name' ]
    for _, dedup in deduplicators.get( name, [ ] ):
        if not dedup.is_duplicate( name, invocation[ 'arguments' ] ):
            continue
        current_correlation_id = invocation.get( 'correlation_id' )
        if current_correlation_id is None:
            result_index = index_of_invocation_canister + j + 1
        else:
            result_index = (
                correlation_id_to_index.get( current_correlation_id ) )
        if (    result_index is not None
            and result_index < len( history )
            and history[ result_index ].gui__.toggle_active.value
            and not history[ result_index ].gui__.toggle_pinned.value
        ): return result_index
        return -1
    return None


def _result_canister_index_by_id( history ):
    ''' Builds ``correlation_id -> history index`` for canisters whose
        ``attributes.correlation_id`` is set. Used to locate an older
        invocation's result canister by durable id (rather than by
        ``i + j + 1``). First occurrence wins; well-formed conversations
        have one correlation_id per result canister. '''
    index: __.accret.Dictionary[ str, int ] = __.accret.Dictionary( )
    for index_, message in enumerate( history ):
        attributes = getattr( message.gui__.canister__, 'attributes', None )
        cid = getattr( attributes, 'correlation_id', None ) if (
            attributes is not None ) else None
        if cid and cid not in index: index[ cid ] = index_
    return index


def _register_newer_dedup( invocation, invoker, deduplicators ):
    ''' Registers this invocation as a candidate deduper for any
        older invocation processed later. Per scenario "Correlation
        identifier drives dedup", the durable ``correlation_id`` from
        the descriptor is recorded alongside the dedup instance so a
        future older call can pair to this invocation's result via
        the correlation_id index. '''
    dedup = invoker.deduplicator_class(
        invocable_name = invocation[ 'name' ],
        arguments = invocation[ 'arguments' ] )
    stored_correlation_id = invocation.get( 'correlation_id' )
    for name_ in invoker.deduplicator_class.provide_invocable_names( ):
        deduplicators.setdefault( name_, [ ] ).append(
            ( stored_correlation_id, dedup ) )


@__.ctxl.contextmanager
def _update_conversation_progress( components, message ):
    from .updaters import update_conversation_status
    yield update_conversation_status(
        components, content = message, progress = True )
    update_conversation_status( components )


def _update_gui_on_chat( gui, canister_gui ):
    from .updaters import autoscroll_document
    _conversations.assimilate_canister_dto_to_gui( canister_gui )
    autoscroll_document( gui )
