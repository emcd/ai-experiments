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


from panel.layout import Column, GridBox, HSpacer, Row
from panel.pane import Markdown
from panel.widgets import (
    Button,
    Checkbox,
    CheckButtonGroup,
    FloatSlider,
    IntSlider,
    Select,
    StaticText,
    TextAreaInput,
    TextInput,
)

dashboard_layout = {
    'dashboard': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'max',
            min_width = 1024,
            width_policy = 'max',
        ),
        contains = [
            'column_conversations_manager',
            'left_spacer',
            'column_conversation',
            'right_spacer',
            'column_conversation_control',
        ]
    ),
}

conversations_manager_layout = {
    'column_conversations_manager': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'max',
            max_width = 480, min_width = 192,
            styles = { 'background': 'LightGray' },
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
    'left_spacer': dict( component_class = HSpacer ),
}
dashboard_layout.update( conversations_manager_layout )

conversation_layout = {
    'column_conversation': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'max',
            max_width = 1280, min_width = 640,
        ),
        contains = [
            'row_system_prompt',
            'column_conversation_history',
            'row_summarization_prompt',
            'row_user_prompt',
        ],
    ),
    'row_system_prompt': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'max',
            # TODO: Use style variable instead for theming.
            styles = { 'background': 'WhiteSmoke' },
        ),
        contains = [ 'label_system', 'column_system_prompt', ],
    ),
    'label_system': dict(
        component_class = StaticText,
        component_arguments = dict( value = '💬📏', width = 40, ),
        persist = False,
    ),
    'column_system_prompt': dict(
        component_class = Column,
        contains = [
            'row_system_prompt_selector',
            'row_system_prompt_variables',
            'text_system_prompt',
        ],
    ),
    'row_system_prompt_selector': dict(
        component_class = Row,
        contains = [
            'selector_system_prompt',
            'checkbox_display_system_prompt',
        ],
    ),
    'selector_system_prompt': dict(
        component_class = Select,
        component_arguments = dict(
            options = [ 'None', ],
            value = 'None',
        ),
    ),
    'checkbox_display_system_prompt': dict(
        component_class = Checkbox,
        component_arguments = dict(
            align = 'center',
            name = 'Display',
            value = False,
        ),
    ),
    'row_system_prompt_variables': dict(component_class = Row, ),
    'text_system_prompt': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'fit',
            width_policy = 'max',
            visible = False,
        ),
    ),
    'column_conversation_history': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'max',
        ),
        persistence_functions = dict(
            save = 'save_conversation_messages',
            restore = 'restore_conversation_messages',
        ),
    ),
    'row_summarization_prompt': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'max',
        ),
        contains = [
            'label_summarization',
            'column_summarization_prompt',
        ],
    ),
    'label_summarization': dict(
        component_class = StaticText,
        component_arguments = dict( value = '💬∑', width = 40, ),
        persist = False,
    ),
    'column_summarization_prompt': dict(
        component_class = Column,
        contains = [
            'row_summarizer_selection',
            'row_summarization_prompt_variables',
            'text_summarization_prompt',
        ],
    ),
    'row_summarizer_selection': dict(
        component_class = Row,
        contains = [
            'selector_summarization_prompt',
            'checkbox_summarize',
        ],
    ),
    'selector_summarization_prompt': dict(
        component_class = Select,
        component_arguments = dict(
            options = [ 'None' ],
            value = 'None',
        ),
    ),
    'checkbox_summarize': dict(
        component_class = Checkbox,
        component_arguments = dict(
            align = 'center',
            name = 'Display and Activate',
            value = False,
        ),
    ),
    'row_summarization_prompt_variables': dict( component_class = Row, ),
    'text_summarization_prompt': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'fit',
            width_policy = 'max',
            visible = False,
        ),
    ),
    'row_user_prompt': dict(
        component_class = Row,
        component_arguments = dict(
            align = ( 'end', 'start' ),
            width_policy = 'max',
        ),
        contains = [ 'label_user', 'column_user_prompt' ],
    ),
    'label_user': dict(
        component_class = StaticText,
        component_arguments = dict( value = '💬🧑', width = 40, ),
        persist = False,
    ),
    'column_user_prompt': dict(
        component_class = Column,
        component_arguments = dict( width_policy = 'max' ),
        contains = [ 'text_input_user', 'row_actions', ],
    ),
    'text_input_user': dict(
        component_class = TextAreaInput,
        component_arguments = dict(
            value = '',
            placeholder = 'Enter user message here...',
            height_policy = 'fit', width_policy = 'max',
            max_height = 480, # min_height = 240,
        ),
    ),
    'row_actions': dict(
        component_class = Row,
        contains = [ 'button_chat', 'button_query', ],
    ),
    'button_chat': dict(
        component_class = Button,
        component_arguments = dict( name = 'Chat' ),
    ),
    'button_query': dict(
        component_class = Button,
        component_arguments = dict( name = 'Query' ),
    ),
}
dashboard_layout.update( conversation_layout )

conversation_control_layout = {
    'right_spacer': dict( component_class = HSpacer ),
    'column_conversation_control': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'max',
            max_width = 480, min_width = 192,
            styles = { 'background': 'LightGray' },
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
    'row_indicator': dict(
        component_class = Row,
        component_arguments = dict( width_policy = 'max' ),
        contains = [ 'gridbox_actions', 'text_title' ],
    ),
    'gridbox_actions': dict(
        component_class = GridBox,
        component_arguments = dict(
            ncols = 3,
            align = 'center',
            height_policy = 'min', width_policy = 'min',
            margin = 5,
            styles = { 'padding': '2px' },
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
            align = 'center',
            button_style = 'outline', button_type = 'light',
            height_policy = 'min', width_policy = 'min',
            icon = 'trash', icon_size = '1em',
            margin = 1,
            styles = { 'border': '0', 'padding': '0' },
        ),
    ),
    'button_edit_title': dict(
        component_class = Button,
        component_arguments = dict(
            align = 'center',
            button_style = 'outline', button_type = 'light',
            height_policy = 'min', width_policy = 'min',
            icon = 'edit', icon_size = '1em',
            margin = 1,
            styles = { 'border': '0', 'padding': '0' },
        ),
    ),
    'button_edit_labels': dict(
        component_class = Button,
        component_arguments = dict(
            align = 'center',
            button_style = 'outline', button_type = 'light',
            height_policy = 'min', width_policy = 'min',
            icon = 'bookmark-edit', icon_size = '1em',
            margin = 1,
            styles = { 'border': '0', 'padding': '0' },
        ),
    ),
    'text_title': dict(
        component_class = Markdown,
        component_arguments = dict(
            align = 'center',
            height_policy = 'min', width_policy = 'max',
        ),
    ),
}

conversation_message_common_layout = {
    'row_message': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'max',
        ),
        contains = [ 'column_header', 'text_message' ],
    ),
    'column_header': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'min',
        ),
        contains = [ 'row_behaviors', 'gridbox_actions' ],
    ),
    'row_behaviors': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'min',
        ),
        contains = [ 'label_role', 'checkbuttons_behaviors' ]
    ),
    'label_role': dict(
        component_class = StaticText,
        component_arguments = dict(
            align = 'center',
            height_policy = 'min', width_policy = 'min',
            margin = 5,
        ),
    ),
    'checkbuttons_behaviors': dict(
        component_class = CheckButtonGroup,
        component_arguments = dict(
            options = [ '💬', '📌' ],
            value = [ '💬' ],
            align = 'center',
            button_style = 'outline', button_type = 'light',
            height_policy = 'min', width_policy = 'min',
            margin = 5,
            styles = { 'padding': '2px' },
        ),
    ),
    'gridbox_actions': dict(
        component_class = GridBox,
        component_arguments = dict(
            ncols = 3,
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
            align = 'center',
            button_style = 'outline', button_type = 'light',
            height_policy = 'min', width_policy = 'min',
            icon = 'trash',
            margin = 0,
            styles = { 'padding': '0' },
        ),
    ),
    'button_edit': dict(
        component_class = Button,
        component_arguments = dict(
            align = 'center',
            button_style = 'outline', button_type = 'light',
            height_policy = 'min', width_policy = 'min',
            icon = 'edit',
            margin = 0,
            styles = { 'padding': '0' },
        ),
    ),
    'button_copy': dict(
        component_class = Button,
        component_arguments = dict(
            align = 'center',
            button_style = 'outline', button_type = 'light',
            height_policy = 'min', width_policy = 'min',
            icon = 'copy',
            margin = 0,
            styles = { 'padding': '0' },
        ),
    ),
}

plain_conversation_message_layout = conversation_message_common_layout.copy( )
plain_conversation_message_layout.update( {
    'text_message': dict(
        component_class = StaticText,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'max',
        ),
    ),
} )

rich_conversation_message_layout = conversation_message_common_layout.copy( )
rich_conversation_message_layout.update( {
    'text_message': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'max',
        ),
    ),
} )
