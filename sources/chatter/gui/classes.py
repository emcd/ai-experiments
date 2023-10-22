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


''' Auxiliary classes for Holoviz Panel GUI. '''


from panel.layout import Row
from panel.reactive import ReactiveHTML
from param import Boolean, Event, Parameter, depends as param_depends

from . import base as __


@__.dataclass
class ConversationDescriptor:

    identity: str = (
        __.dataclass_declare( default_factory = lambda: __.uuid4( ).hex ) )
    timestamp: int = (
        __.dataclass_declare( default_factory = __.time_ns ) )
    title: __.typ.Optional[ str ] = None
    labels: __.AbstractMutableSequence[ str ] = (
        __.dataclass_declare( default_factory = list ) )
    gui: __.typ.Optional[ __.SimpleNamespace ] = None
    indicator: __.typ.Optional[ Row ] = None


# TODO: Reduce to simple wrapper for custom JS code.
#       Row initialization should be elsewhere.
class ConversationIndicator( ReactiveHTML ):

    clicked = Event( default = False )
    mouse_hover__ = Boolean( False )
    row__ = Parameter( )

    _scripts = {
        'my_mouseenter': '''
            if (event.target && event.target.matches(':hover')) {
                var timeout = setTimeout(
                    function() { data.mouse_hover__ = true; }, 400);
                event.target.onmouseleave = function() {
                    clearTimeout(timeout);
                    if (data.mouse_hover__) data.mouse_hover__ = false;
                };
            }''',
    }

    _template = '''
        <div id="ConversationIndicator"
            onclick="${_div_click}"
            onmouseenter="${script('my_mouseenter')}"
        >
            ${row__}
            <input id="ConversationIndicator_mouse_hover"
                type="hidden" value="${mouse_hover__}"/>
        </div>'''.strip( )

    # TODO: Should only need GUI namespace as argument.
    def __init__( self, title, identity, **params ):
        from .layouts import conversation_indicator_layout as layout
        row_gui = __.SimpleNamespace( )
        row = __.generate_component( row_gui, layout, 'column_indicator' )
        row_gui.rehtml_indicator = self
        row_gui.text_title.object = title
        self.gui__ = row_gui
        self.row__ = row
        self.identity__ = identity
        super( ).__init__( **params )

    def _div_click( self, event ):
        # TODO: Suppress event propagation from buttons contained in this.
        #       Especially for 'delete' button as this results in a
        #       'bokeh.core.serialization.DeserializationError' from
        #       an unresolved reference after deletion.
        # Cannot run callback directly. Trigger via Event parameter.
        self.clicked = True

    @param_depends( 'mouse_hover__', watch = True )
    def _handle_mouse_hover__( self ):
        self.gui__.row_actions.visible = self.mouse_hover__


# TODO: Reduce to simple wrapper for custom JS code.
#       Row initialization should be elsewhere.
class ConversationMessage( ReactiveHTML ):

    mouse_hover__ = Boolean( False )
    row__ = Parameter( )

    _scripts = {
        'my_mouseenter': '''
            if (event.target && event.target.matches(':hover')) {
                var timeout = setTimeout(
                    function() { data.mouse_hover__ = true; }, 400);
                event.target.onmouseleave = function() {
                    clearTimeout(timeout);
                    if (data.mouse_hover__) data.mouse_hover__ = false;
                };
            }''',
    }

    _template = '''
        <div id="ConversationMessage"
            onmouseenter="${script('my_mouseenter')}"
        >
            ${row__}
            <input id="ConversationMessage_mouse_hover"
                type="hidden" value="${mouse_hover__}"/>
        </div>'''.strip( )

    # TODO: Should only need GUI namespace as argument.
    def __init__( self, role, mime_type, actor_name = None, **params ):
        emoji = __.roles_emoji[ role ]
        styles = __.roles_styles[ role ]
        if 'text/plain' == mime_type:
            from .layouts import plain_conversation_message_layout as layout
        elif 'application/json' == mime_type:
            from .layouts import json_conversation_message_layout as layout
        else:
            from .layouts import rich_conversation_message_layout as layout
        row_gui = __.SimpleNamespace( )
        row = __.generate_component( row_gui, layout, 'row_message' )
        row.styles.update( styles )
        row_gui.rehtml_message = self
        row_gui.layout__ = layout
        self.auxdata__ = {
            'gui': row_gui,
            'mime-type': mime_type,
            'role': role,
        }
        if actor_name: self.auxdata__[ 'actor-name' ] = actor_name
        # TODO: Use user-supplied logos, when available.
        row_gui.toggle_active.name = emoji
        self.gui__ = row_gui
        self.row__ = row
        super( ).__init__( **params )

    @param_depends( 'mouse_hover__', watch = True )
    def _handle_mouse_hover__( self ):
        self.gui__.row_actions.visible = self.mouse_hover__


# TODO: Implement UserMessagePrompt with 'onkeyup' callback,
#       if https://github.com/holoviz/panel/pull/5592 is delayed.
#       https://developer.mozilla.org/en-US/docs/Web/API/HTMLTextAreaElement#autogrowing_textarea_example
