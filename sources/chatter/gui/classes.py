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


from . import base as __


@__.dataclass
class ConversationDescriptor:

    identity: str = (
        __.dataclasses.field( default_factory = lambda: __.uuid4( ).hex ) )
    timestamp: int = (
        __.dataclasses.field( default_factory = __.time_ns ) )
    title: __.typ.Optional[ str ] = None
    labels: __.AbstractMutableSequence[ str ] = (
        __.dataclasses.field( default_factory = list ) )
    gui: __.typ.Optional[ __.SimpleNamespace ] = None
    indicator: __.typ.Optional[ __.Row ] = None


class ConversationIndicator( __.ReactiveHTML ):

    clicked = __.param.Event( default = False )
    row__ = __.param.Parameter( )

    _template = (
        '''<div id="ConversationIndicator" '''
        '''onclick="${_div_click}" '''
        '''onmouseenter="${_div_mouseenter}" '''
        '''onmouseleave="${_div_mouseleave}" '''
        '''>${row__}</div>''' )

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

    def _div_mouseenter( self, event ):
        self.gui__.row_actions.visible = True

    def _div_mouseleave( self, event ):
        self.gui__.row_actions.visible = False


class ConversationMessage( __.ReactiveHTML ):

    row__ = __.param.Parameter( )

    _template = (
        '''<div id="ConversationMessage" '''
        '''onmouseenter="${_div_mouseenter}" '''
        '''onmouseleave="${_div_mouseleave}" '''
        '''>${row__}</div>''' )

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
        row_gui.label_role.value = emoji
        self.gui__ = row_gui
        self.row__ = row
        super( ).__init__( **params )

    def _div_mouseenter( self, event ):
        self.gui__.row_actions.visible = True

    def _div_mouseleave( self, event ):
        self.gui__.row_actions.visible = False
