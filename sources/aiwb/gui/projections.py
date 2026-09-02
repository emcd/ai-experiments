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
#  distributed under the License is distributed on an "AS IS" BASIS,        #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and        #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Normalized display projection for invocation canisters.

    Per OpenSpec define-invocation-data-contract (GUI Display Projection
    Boundary, requirement at ``specs/invocation-data-contract/spec.md``):
    the user-visible invocation display projects only the normalized record
    ``(name, arguments, correlation_id, processor)``; raw provider replay
    envelopes are surfaced only when the user explicitly opts into per-
    canister details.

    Renderer-owned by the GUI layer, not by backend modules. Field
    presence is optional so the projection remains stable across the v0
    to v1 round-trip gap (descriptor-side ``correlation_id`` and
    ``processor`` are filled in once the cross-lane commits from tasks 1.4
    / 1.5 / 1.7 land; the projection function tolerates either shape). '''


from . import __


def display_payload( record ):
    ''' Returns normalized projection from a record, dict, or canister.

        Accepts an ``InvocationRequest`` object, an ``invocation_data``
        entry dict, or ``None``; returns a mapping with the four canonical
        keys ``name``, ``arguments``, ``correlation_id``, ``processor``.
        Missing fields surface as ``None`` so the projection stays stable
        across the v0-to-v1 round-trip gap. '''
    if record is None:
        return dict(
            name = None, arguments = None,
            correlation_id = None, processor = None )
    # InvocationRequest or similar object exposes attributes directly.
    if hasattr( record, 'correlation_id' ) and not isinstance( record, dict ):
        name = getattr( record, 'name', None )
        arguments = getattr( record, 'arguments', None )
        correlation_id = getattr( record, 'correlation_id', None )
        processor = getattr( record, 'processor', None )
    else:
        try: record_dict = dict( record )
        except ( TypeError, ValueError ): record_dict = { }
        name = record_dict.get( 'name' )
        arguments = record_dict.get( 'arguments' )
        correlation_id = record_dict.get( 'correlation_id' )
        processor = record_dict.get( 'processor' )
    if isinstance( arguments, __.cabc.Mapping ):
        arguments = dict( arguments )
    processor_value = getattr( processor, 'value', processor )
    return dict(
        name = name,
        arguments = arguments,
        correlation_id = correlation_id,
        processor = processor_value )


def normalize_processor( processor ):
    ''' Returns the string value of a processor label.

        Accepts an ``InvocationProcessor`` enum member, its ``.value``
        string, ``None``, or any other label; returns a lowercase string or
        ``None`` so the renderer can switch on it without comparing against
        enum identity. '''
    if processor is None: return None
    raw = getattr( processor, 'value', processor )
    if raw is None: return None
    rendered = str( raw ).lower( )
    return rendered or None


def render_projection( record ):
    ''' Markdown rendering of the default normalized projection.

        The default user-visible invocation display. Does not include the
        provider envelope or supplement; those are reachable via the opt-in
        ``toggle_details`` affordance on the per-message ``row_actions``
        bar (see ``invocation_conversation_message_layout``). '''
    from json import dumps
    payload = display_payload( record )
    name = payload[ 'name' ] or '<unnamed>'
    arguments = payload[ 'arguments' ]
    arguments_rendered = (
        dumps( arguments, indent = 2 ) if arguments is not None else '' )
    correlation_id = payload[ 'correlation_id' ] or 'pending'
    processor = normalize_processor( payload[ 'processor' ] ) or 'application'
    lines = [
        f"**Invocation**: `{name}`",
        f"**Arguments**:\n\n```json\n{arguments_rendered}\n```",
        f"**Correlation ID**: `{correlation_id}`",
        f"**Processor**: `{processor}`",
    ]
    return '\n\n'.join( lines )


def render_raw_envelope( canister ):
    ''' Raw provider envelope rendered as JSON for opt-in details view.

        Per opt-in-only contract: supplement and per-invocation raw
        provider envelope are surfaced here only when the user has
        explicitly enabled details on the message canister. The
        application never inspects this for pairing, dedup, or default
        display correlation. '''
    from json import dumps
    attributes = getattr( canister, 'attributes', None )
    model_context = getattr( attributes, 'model_context', { } ) if (
        attributes is not None ) else { }
    return dumps( model_context, indent = 2, default = str )


def render_invocation_data_projection( invocation_data ):
    ''' Renders the projection for each item in an ``invocation_data`` list.

        Parallel invocations appear as discrete blocks under the canister
        header; per spec, the bloc renderer is owned by the GUI layer
        rather than a backend module. '''
    if not invocation_data: return ''
    blocks = [ render_projection( record ) for record in invocation_data ]
    separator = '\n\n---\n\n'
    return separator.join( blocks )
