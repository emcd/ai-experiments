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


''' GUI layouts with Panel widgets. '''


import param

from panel.layout import Column, GridBox, HSpacer, Row
from panel.pane import Markdown
from panel.reactive import ReactiveHTML
from panel.widgets import (
    Button,
    FloatSlider,
    IntSlider,
    Select,
    StaticText,
    TextAreaInput,
    TextInput,
    Toggle,
)


#_sticky_css = '''
#div.sticky {
#    position: sticky;
#    top: 0;
#}
#'''
#class StickyContainer( ReactiveHTML ):
#
#    containee = param.Parameter( )
#
#    _template = (
#        '''<div id="StickyContainer" class="sticky">${containee}</div>''' )
#
#    def __init__( self, containee, **params ):
#        self.containee = containee
#        stylesheets = params.get( 'stylesheets', [ ] ).copy( )
#        stylesheets.append( _sticky_css )
#        params[ 'stylesheets' ] = stylesheets
#        super( ).__init__( **params )


_css_code_overflow = '''
div[class="codehilite"] {
    overflow-x: auto;
}
'''

_central_column_width_attributes = dict(
    max_width = 1024, min_width = 640,
    width = 1024,
)

_little_button_attributes = dict(
    align = 'center',
    button_style = 'outline', button_type = 'light',
    height_policy = 'min', width_policy = 'min',
    margin = 0,
    styles = { 'padding': '0' },
)

_message_header_attributes = dict(
    height_policy = 'auto', width_policy = 'max',
    margin = 5,
    max_width = 110, width = 110,
)


dashboard_layout = {
    'dashboard': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'max',
            min_width = 1024,
        ),
        contains = [
            'column_conversations_manager',
            'column_conversation',
            'column_conversation_control',
        ]
    ),
}

conversations_manager_layout = {
    'column_conversations_manager': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'fit',
            max_width = 480, min_width = 192,
            # TODO: Use style variable instead for theming.
            styles = { 'background': '#e8e8e8' },
            width = 480,
        ),
        contains = [
            'button_new_conversation',
            'column_conversations_indicators',
        ],
    ),
    'button_new_conversation': dict(
        component_class = Button,
        component_arguments = dict(
            name = 'New Conversation',
            width_policy = 'min',
        ),
    ),
    'column_conversations_indicators': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'max',
        )
    ),
}
dashboard_layout.update( conversations_manager_layout )

conversation_layout = {
    'column_conversation': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'row_system_prompt',
            'column_conversation_history',
            'column_user_prompts',
        ],
    ),
    'row_system_prompt': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            # TODO: Use style variable instead for theming.
            styles = { 'background': 'WhiteSmoke' },
        ),
        contains = [
            'spacer_left_system_prompt',
            'row_system_prompt_header',
            'column_system_prompt',
            'spacer_right_system_prompt',
        ],
    ),
    'spacer_left_system_prompt': dict( component_class = HSpacer ),
    'row_system_prompt_header': dict(
        component_class = Row,
        component_arguments = dict( **_message_header_attributes ),
        contains = [
            'label_system',
            'spacer_label_system',
            'toggle_system_prompt_active',
            'toggle_system_prompt_display',
        ],
    ),
    'label_system': dict(
        component_class = StaticText,
        component_arguments = dict( value = '📏' ),
        persist = False,
    ),
    'spacer_label_system': dict( component_class = HSpacer ),
    'toggle_system_prompt_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', value = True, **_little_button_attributes,
        ),
    ),
    'toggle_system_prompt_display': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Eye}\uFE0F', value = False, **_little_button_attributes,
        ),
    ),
    'column_system_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            **_central_column_width_attributes,
        ),
        contains = [
            'selector_system_prompt',
            'row_system_prompt_variables',
            'text_system_prompt',
        ],
    ),
    'selector_system_prompt': dict(
        component_class = Select,
        component_arguments = dict(
            options = [ 'General Conversation' ],
            value = 'General Conversation',
        ),
    ),
    'row_system_prompt_variables': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        persistence_functions = dict(
            save = 'save_prompt_variables',
            restore = 'restore_prompt_variables',
        ),
    ),
    'text_system_prompt': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'fit',
            width_policy = 'max',
            visible = False,
        ),
    ),
    'spacer_right_system_prompt': dict( component_class = HSpacer ),
    'column_conversation_history': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        persistence_functions = dict(
            save = 'save_conversation_messages',
            restore = 'restore_conversation_messages',
        ),
    ),
    'column_user_prompts': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            # TODO: Use style variable instead for theming.
            styles = { 'background': 'White' },
        ),
        contains = [
            'row_canned_prompt',
            'row_user_prompt',
        ]
    ),
    'row_canned_prompt': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'spacer_left_canned_prompt',
            'row_canned_prompt_header',
            'column_canned_prompt',
            'spacer_right_canned_prompt',
        ],
    ),
    'spacer_left_canned_prompt': dict( component_class = HSpacer ),
    'row_canned_prompt_header': dict(
        component_class = Row,
        component_arguments = dict( **_message_header_attributes ),
        contains = [
            'label_canned',
            'spacer_label_canned',
            'toggle_canned_prompt_active',
            'toggle_canned_prompt_display',
        ],
    ),
    'label_canned': dict(
        component_class = StaticText,
        component_arguments = dict( value = '🥫' ),
        persist = False,
    ),
    'spacer_label_canned': dict( component_class = HSpacer ),
    'toggle_canned_prompt_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', value = False, **_little_button_attributes,
        ),
    ),
    'toggle_canned_prompt_display': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Eye}\uFE0F', value = False, **_little_button_attributes,
        ),
    ),
    'column_canned_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            **_central_column_width_attributes,
        ),
        contains = [
            'row_canned_prompt_selection',
            'row_canned_prompt_variables',
            'text_canned_prompt',
        ],
    ),
    'row_canned_prompt_selection': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'selector_canned_prompt', 'button_refine_canned_prompt',
        ],
    ),
    'selector_canned_prompt': dict(
        component_class = Select,
        component_arguments = dict(
            options = [ 'Recap: General Conversation' ],
            value = 'Recap: General Conversation',
        ),
    ),
    'button_refine_canned_prompt': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'arrow-big-down', icon_size = '16px',
        ),
    ),
    'row_canned_prompt_variables': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
    ),
    'text_canned_prompt': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'fit',
            width_policy = 'max',
            visible = False,
        ),
    ),
    'spacer_right_canned_prompt': dict( component_class = HSpacer ),
    'row_user_prompt': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'spacer_left_user_prompt',
            'row_user_prompt_header',
            'column_user_prompt',
            'spacer_right_user_prompt',
        ],
    ),
    'spacer_left_user_prompt': dict( component_class = HSpacer ),
    'row_user_prompt_header': dict(
        component_class = Row,
        component_arguments = dict( **_message_header_attributes ),
        contains = [
            'label_user',
            'spacer_label_user',
            'toggle_user_prompt_active',
            'toggle_user_prompt_dork',
        ],
    ),
    'label_user': dict(
        component_class = StaticText,
        component_arguments = dict( value = '🧑' ),
        persist = False,
    ),
    'spacer_label_user': dict( component_class = HSpacer ),
    'toggle_user_prompt_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', value = True, **_little_button_attributes,
        ),
    ),
    'toggle_user_prompt_dork': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💍', value = False, **_little_button_attributes,
        ),
    ),
    'column_user_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            **_central_column_width_attributes,
        ),
        contains = [ 'text_input_user', 'row_actions', ],
    ),
    'text_input_user': dict(
        component_class = TextAreaInput,
        component_arguments = dict(
            value = '',
            placeholder = 'Enter user message here...',
            height_policy = 'auto', width_policy = 'max',
            max_height = 480, # min_height = 240,
        ),
    ),
    'row_actions': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [ 'button_chat', 'button_query', ],
    ),
    'button_chat': dict(
        component_class = Button,
        component_arguments = dict( name = '💬 Chat AI' ),
    ),
    'button_query': dict(
        component_class = Button,
        component_arguments = dict( name = '🔍 Query Documents' ),
    ),
    'spacer_right_user_prompt': dict( component_class = HSpacer ),
}
dashboard_layout.update( conversation_layout )

conversation_control_layout = {
    'column_conversation_control': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'fit',
            max_width = 480, min_width = 192,
            styles = { 'background': '#e8e8e8' },
            width = 480,
        ),
        contains = [
            'selector_provider',
            'selector_model',
            'slider_temperature',
            'selector_vectorstore',
            'slider_documents_count',
            'text_tokens_total',
            'text_status',
        ],
    ),
    'selector_provider': dict(
        component_class = Select,
        component_arguments = dict(
            name = 'Provider',
            options = [ 'OpenAI' ],
            value = 'OpenAI',
        ),
    ),
    'selector_model': dict(
        component_class = Select,
        component_arguments = dict(
            name = 'Model',
            options = [ 'gpt-3.5-turbo' ],
            value = 'gpt-3.5-turbo',
        ),
    ),
    'slider_temperature': dict(
        component_class = FloatSlider,
        component_arguments = dict(
            name = 'Temperature',
            start = 0, end = 2, step = 0.1, value = 0,
        ),
    ),
    'selector_vectorstore': dict(
        component_class = Select,
        component_arguments = dict(
            name = 'Vector Store',
        ),
    ),
    'slider_documents_count': dict(
        component_class = IntSlider,
        component_arguments = dict(
            name = 'Number of Documents',
            start = 0, end = 5, step = 1, value = 3,
        ),
    ),
    'text_tokens_total': dict(
        component_class = StaticText,
        component_arguments = dict( name = 'Token Counter', value = '0', ),
        persist = False,
    ),
    'text_status': dict(
        component_class = StaticText,
        component_arguments = dict( name = 'Status', value = 'OK', ),
        persist = False,
    ),
}
dashboard_layout.update( conversation_control_layout )

conversation_indicator_layout = {
    'column_indicator': dict(
        component_class = Column,
        component_arguments = dict( width_policy = 'max' ),
        contains = [ 'text_title', 'row_actions_structure' ],
    ),
    'text_title': dict(
        component_class = Markdown,
        component_arguments = dict(
            align = 'center',
            height_policy = 'min', width_policy = 'max',
        ),
    ),
    'row_actions_structure': dict(
        component_class = Row,
        component_arguments = dict(
            height = 40, min_height = 40,
            height_policy = 'min', width_policy = 'max',
        ),
        contains = [ 'row_actions' ]
    ),
    'row_actions': dict(
        component_class = Row,
        component_arguments = dict(
            align = ( 'center', 'end' ),
            height_policy = 'min', width_policy = 'min',
            #margin = 5,
            #styles = { 'padding': '2px' },
            visible = False,
        ),
        contains = [
            'button_delete',
            'button_edit_title',
            'button_edit_labels',
        ],
    ),
    'button_delete': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'trash', # icon_size = '1em',
            **_little_button_attributes,
        ),
    ),
    'button_edit_title': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'edit', # icon_size = '1em',
            **_little_button_attributes,
        ),
    ),
    'button_edit_labels': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'bookmark-edit', # icon_size = '1em',
            **_little_button_attributes,
        ),
    ),
}

conversation_message_common_layout = {
    'row_message': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'spacer_left',
            'column_header',
            'text_message',
            'spacer_right',
        ],
    ),
    'spacer_left': dict( component_class = HSpacer ),
    'column_header': dict(
        component_class = Column,
        component_arguments = dict( **_message_header_attributes ),
        contains = [ 'row_behaviors', 'row_actions' ],
    ),
    'row_behaviors': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'label_role',
            'spacer_role',
            'toggle_active',
            'toggle_pinned',
        ],
    ),
    'label_role': dict(
        component_class = StaticText,
        component_arguments = dict(
            align = 'center',
            height_policy = 'min', width_policy = 'min',
            margin = 0,
        ),
    ),
    'spacer_role': dict( component_class = HSpacer ),
    'toggle_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', #icon = 'message-dots',
            value = False,
            **_little_button_attributes,
        ),
    ),
    'toggle_pinned': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '📌', #icon = 'pin',
            value = False,
            **_little_button_attributes,
        ),
    ),
    'row_actions': dict(
        component_class = Row,
        component_arguments = dict(
            align = ( 'start', 'end' ),
            height_policy = 'min', width_policy = 'min',
            margin = 5,
            styles = { 'padding': '2px' },
            visible = False,
        ),
        contains = [ 'button_delete', 'button_edit', 'button_copy' ],
    ),
    'button_delete': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'trash',
            **_little_button_attributes,
        ),
    ),
    'button_edit': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'edit',
            **_little_button_attributes,
        ),
    ),
    'button_copy': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'copy',
            **_little_button_attributes,
        ),
    ),
    'spacer_right': dict( component_class = HSpacer ),
}

plain_conversation_message_layout = conversation_message_common_layout.copy( )
plain_conversation_message_layout.update( {
    'text_message': dict(
        component_class = StaticText,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            styles = { 'overflow': 'auto' },
            **_central_column_width_attributes,
        ),
    ),
} )

rich_conversation_message_layout = conversation_message_common_layout.copy( )
rich_conversation_message_layout.update( {
    'text_message': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            styles = { 'overflow': 'auto' },
            stylesheets = [ _css_code_overflow ],
            **_central_column_width_attributes,
        ),
    ),
} )
