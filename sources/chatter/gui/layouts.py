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


''' GUI layouts with Panel widgets.

    Based on experience with Bokeh/Panel and GUI layout, in general, the
    following guidance should be considered:

    * Do not use height and width policies except where necessary. Excessive
      policy use can lead to hard-to-debug display behaviors.

    * Used fixed sizes only for small elements. These serve as the basis for
      consistent sizing on a larger scale.

    * The 'max' height policy needs both 'height' and 'max_height' to be
      effective. Similarly for the 'max' width policy.

    * Prefer margins over padding for greater control. '''


from types import SimpleNamespace

import param

from panel.layout import Column, HSpacer, Row
from panel.pane import JSON, Markdown
from panel.reactive import ReactiveHTML
from panel.widgets import (
    Button,
    Checkbox,
    FloatSlider,
    IntSlider,
    LoadingSpinner,
    MultiChoice,
    Select,
    StaticText,
    TextAreaInput,
    TextInput,
    Toggle,
)


sizes = SimpleNamespace(
    action_button_height = 40,
    action_button_width = 120,
    element_margin = 2,
    icon_button_height = 40, # distortion if smaller, Bokeh/Panel limitation
    icon_size = '1em',
    message_width_max = 1024,
    message_width_min = 480,
    sidebar_width_max = 336,
    standard_margin = 5,
)
sizes.icon_button_width = sizes.icon_button_height
sizes.actions_height = sizes.icon_button_height + 2 * sizes.element_margin
sizes.actions_width = (
      3 * sizes.icon_button_width
    + 6 * sizes.element_margin
    + 10 # border widths + extra fudge
)


_css_code_overflow = '''
div[class="codehilite"] {
    overflow-x: auto;
}
'''


_action_button_attributes = dict(
    #align = 'center',
    button_style = 'solid', # button_type = 'light',
    height = sizes.action_button_height, height_policy = 'fixed',
    width = sizes.action_button_width, width_policy = 'fixed',
)

_icon_button_attributes = dict(
    align = 'center',
    button_style = 'outline', button_type = 'light',
    height = sizes.icon_button_height, width = sizes.icon_button_width,
    height_policy = 'fixed', width_policy = 'fixed',
    margin = sizes.element_margin,
)

_message_column_width_attributes = dict(
    max_width = sizes.message_width_max, min_width = sizes.message_width_min,
    width = sizes.message_width_max,
)

_message_header_attributes = dict(
    height_policy = 'auto', width_policy = 'max',
    margin = sizes.standard_margin,
    max_width = sizes.actions_width, width = sizes.actions_width,
)


conversation_container_names = (
    'conversation_control',
    'conversation_history',
    'system_prompts',
    'user_prompts',
)


dashboard_layout = {
    'dashboard': dict(
        component_class = Row,
        contains = [
            'column_conversations_manager',
            'interpolant_conversation_control',
            'interpolant_conversation_history',
            'interpolant_system_prompts',
            'interpolant_user_prompts',
        ],
        virtual = True,
    ),
    # Need indirection to assign containers rather than copy component arrays
    # to prevent shared ownership visibility issues.
    'interpolant_conversation_control': dict(
        component_class = Row,
        component_arguments = dict( width_policy = 'max' ),
        interpolant_id = 'right',
    ),
    'interpolant_conversation_history': dict(
        component_class = Row,
        component_arguments = dict( width_policy = 'max' ),
        interpolant_id = 'main',
    ),
    'interpolant_system_prompts': dict(
        component_class = Row,
        component_arguments = dict( width_policy = 'max' ),
        interpolant_id = 'top',
    ),
    'interpolant_user_prompts': dict(
        component_class = Row,
        component_arguments = dict( width_policy = 'max' ),
        interpolant_id = 'bottom',
    ),
}

conversations_manager_layout = {
    'column_conversations_manager': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'max',
            # TODO: Use width of container.
            max_width = sizes.sidebar_width_max,
            width = sizes.sidebar_width_max,
        ),
        contains = [
            'button_create_conversation',
            'column_conversations_indicators',
        ],
        interpolant_id = 'left',
    ),
    'button_create_conversation': dict(
        component_class = Button,
        component_arguments = dict(
            name = '🆕 New Conversation',
            button_type = 'light',
            **_action_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_create_conversation' ),
    ),
    'column_conversations_indicators': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'min', width_policy = 'max',
        )
    ),
}
dashboard_layout.update( conversations_manager_layout )

system_prompts_layout = {
    'column_system_prompts': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            # TODO: Use style variable instead for theming.
            styles = { 'background': 'WhiteSmoke' },
        ),
        contains = [
            'row_system_prompt',
            'row_functions_prompt',
        ],
    ),
    'row_system_prompt': dict(
        component_class = Row,
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
            'toggle_system_prompt_active',
            'toggle_system_prompt_display',
        ],
    ),
    'label_system': dict(
        component_class = StaticText,
        component_arguments = dict(
            value = '📏', align = 'center', width = sizes.icon_button_width,
        ),
        persist = False,
    ),
    'toggle_system_prompt_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', value = True, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_system_prompt_active' ),
    ),
    'toggle_system_prompt_display': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Eye}\uFE0F', value = False, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_system_prompt_display' ),
    ),
    'column_system_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            **_message_column_width_attributes,
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
        event_functions = dict( value = 'on_select_system_prompt' ),
        populator_function = 'populate_system_prompts_selector',
    ),
    'row_system_prompt_variables': dict(
        component_class = Row,
        persistence_functions = dict(
            save = 'save_prompt_variables',
            restore = 'restore_prompt_variables',
        ),
    ),
    'text_system_prompt': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            visible = False,
        ),
    ),
    'spacer_right_system_prompt': dict( component_class = HSpacer ),
    'row_functions_prompt': dict(
        component_class = Row,
        component_arguments = dict( visible = False ),
        contains = [
            'spacer_left_functions_prompt',
            'row_functions_prompt_header',
            'column_functions_prompt',
            'spacer_right_functions_prompt',
        ],
    ),
    'spacer_left_functions_prompt': dict( component_class = HSpacer ),
    'row_functions_prompt_header': dict(
        component_class = Row,
        component_arguments = dict( **_message_header_attributes ),
        contains = [
            'label_functions',
            'toggle_functions_active',
            'toggle_functions_display',
        ],
    ),
    'label_functions': dict(
        component_class = StaticText,
        component_arguments = dict(
            value = '🧰', align = 'center', width = sizes.icon_button_width,
        ),
        persist = False,
    ),
    'toggle_functions_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', value = True, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_functions_active' ),
    ),
    'toggle_functions_display': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Eye}\uFE0F', value = False, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_functions_display' ),
    ),
    'column_functions_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            **_message_column_width_attributes,
        ),
        contains = [
            'multichoice_functions',
            'row_function_options',
            'column_functions_json',
        ],
    ),
    'multichoice_functions': dict(
        component_class = MultiChoice,
        component_arguments = dict(
            placeholder = 'Please click to select functions.',
            delete_button = True,
            width_policy = 'max',
        ),
        event_functions = dict( value = 'on_select_functions' ),
    ),
    'row_function_options': dict(
        component_class = Row,
        contains = [
            'checkbox_auto_functions',
            'checkbox_elide_function_history',
        ],
    ),
    'checkbox_auto_functions': dict(
        component_class = Checkbox,
        component_arguments = dict(
            name = 'Automatic Function Execution',
            value = True,
        ),
    ),
    'checkbox_elide_function_history': dict(
        component_class = Checkbox,
        component_arguments = dict(
            name = 'Function History Elision',
            value = True,
        ),
    ),
    'column_functions_json': dict(
        component_class = Column,
        component_arguments = dict( visible = False ),
    ),
    'spacer_right_functions_prompt': dict( component_class = HSpacer ),
}

conversation_history_layout = {
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
}

user_prompts_layout = {
    'column_user_prompts': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            # TODO: Use style variable instead for theming.
            styles = { 'background': 'White' },
        ),
        contains = [
            'row_conversation_status',
            'row_canned_prompt',
            'row_user_prompt',
        ],
    ),
    'row_conversation_status': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'spacer_left_conversation_status',
            'spinner_ai_progress',
            'text_conversation_status',
            'spacer_right_conversation_status',
        ],
    ),
    'spacer_left_conversation_status': dict( component_class = HSpacer ),
    'spinner_ai_progress': dict(
        component_class = LoadingSpinner,
        component_arguments = dict(
            size = 40,
            value = False,
            visible = False,
        ),
        persist = False,
    ),
    'text_conversation_status': dict(
        component_class = StaticText,
        component_arguments = dict( name = 'Status', visible = False ),
        persist = False,
    ),
    'spacer_right_conversation_status': dict( component_class = HSpacer ),
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
            'toggle_canned_prompt_active',
            'toggle_canned_prompt_display',
        ],
    ),
    'label_canned': dict(
        component_class = StaticText,
        component_arguments = dict(
            value = '🥫', align = 'center', width = sizes.icon_button_width,
        ),
        persist = False,
    ),
    'toggle_canned_prompt_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', value = False, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_canned_prompt_active' ),
    ),
    'toggle_canned_prompt_display': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Eye}\uFE0F', value = False, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_canned_prompt_display' ),
    ),
    'column_canned_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            **_message_column_width_attributes,
        ),
        contains = [
            'row_canned_prompt_selection',
            'row_canned_prompt_variables',
            'text_canned_prompt',
        ],
    ),
    'row_canned_prompt_selection': dict(
        component_class = Row,
        contains = [ 'selector_canned_prompt', 'button_canned_prompt' ],
    ),
    'selector_canned_prompt': dict(
        component_class = Select,
        component_arguments = dict(
            options = [ 'Recap: General Conversation' ],
            value = 'Recap: General Conversation',
        ),
        event_functions = dict( value = 'on_select_canned_prompt' ),
        populator_function = 'populate_canned_prompts_selector',
    ),
    'button_canned_prompt': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'arrow-big-down', icon_size = sizes.icon_size,
            **_icon_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_uncan_prompt' ),
    ),
    'row_canned_prompt_variables': dict(
        component_class = Row,
    ),
    'text_canned_prompt': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
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
            'toggle_user_prompt_active',
            'label_user_blank',
        ],
    ),
    'label_user': dict(
        component_class = StaticText,
        component_arguments = dict(
            value = '🧑', align = 'center', width = sizes.icon_button_width,
        ),
        persist = False,
    ),
    'toggle_user_prompt_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', value = True, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_user_prompt_active' ),
    ),
    'label_user_blank': dict(
        component_class = StaticText,
        component_arguments = dict(
            value = ' ', align = 'center', width = sizes.icon_button_width,
        ),
        persist = False,
    ),
    'column_user_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            **_message_column_width_attributes,
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
            max_length = 32767,
        ),
        event_functions = dict(
            value = 'on_input_finish_user_prompt',
            value_input = 'on_input_user_prompt',
        ),
    ),
    'row_actions': dict(
        component_class = Row,
        contains = [
            'button_chat',
            'toggle_summarize',
            'button_search',
            'button_run_tool',
        ],
    ),
    'button_chat': dict(
        component_class = Button,
        component_arguments = dict(
            name = '💬 Chat',
            disabled = True,
            button_type = 'primary',
            **_action_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_chat' ),
    ),
    'toggle_summarize': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Compression}\uFE0F', value = False,
            **_icon_button_attributes,
        ),
    ),
    'button_search': dict(
        component_class = Button,
        component_arguments = dict(
            name = '🔍 Search',
            disabled = True,
            **_action_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_search' ),
    ),
    'button_run_tool': dict(
        component_class = Button,
        component_arguments = dict(
            name = '\N{Hammer and Wrench}\uFE0F Run',
            disabled = True,
            **_action_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_run_tool' ),
    ),
    'spacer_right_user_prompt': dict( component_class = HSpacer ),
}

conversation_control_layout = {
    'column_conversation_control': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'max', width_policy = 'max',
            styles = { 'padding': f"{sizes.standard_margin}px" },
            # TODO: Use width of container.
            max_width = sizes.sidebar_width_max, # min_width = 192,
            width = sizes.sidebar_width_max,
        ),
        contains = [
            'selector_provider',
            'selector_model',
            'slider_temperature',
            'selector_vectorstore',
            'slider_documents_count',
            'text_tokens_total',
        ],
    ),
    'selector_provider': dict(
        component_class = Select,
        component_arguments = dict(
            name = 'Provider',
            options = [ 'OpenAI' ],
            value = 'OpenAI',
        ),
        populator_function = 'populate_providers_selector',
    ),
    'selector_model': dict(
        component_class = Select,
        component_arguments = dict( name = 'Model' ),
        event_functions = dict( value = 'on_select_model' ),
        populator_function = 'populate_models_selector',
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
        populator_function = 'populate_vectorstores_selector',
    ),
    'slider_documents_count': dict(
        component_class = IntSlider,
        component_arguments = dict(
            name = 'Number of Documents',
            start = 0, end = 5, step = 1, value = 3,
        ),
        event_functions = dict( value = 'on_adjust_documents_count' ),
    ),
    'text_tokens_total': dict(
        component_class = StaticText,
        component_arguments = dict( name = 'Token Counter', value = '0', ),
        persist = False,
    ),
}

conversation_indicator_layout = {
    'column_indicator': dict(
        component_class = Column,
        #contains = [ 'row_indicator', 'flexbox_labels' ],
        contains = [ 'row_indicator' ],
    ),
    'row_indicator': dict(
        component_class = Row,
        contains = [ 'text_title', 'row_actions_structure' ],
    ),
    'text_title': dict(
        component_class = Markdown,
        component_arguments = dict(
            align = ( 'center', 'start' ),
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            max_width = (
                sizes.sidebar_width_max
                - sizes.actions_width
                - sizes.standard_margin * 2 ),
            width = (
                sizes.sidebar_width_max
                - sizes.actions_width
                - sizes.standard_margin * 2 ),
        ),
    ),
    'row_actions_structure': dict(
        component_class = Row,
        component_arguments = dict(
            height = sizes.actions_height, width = sizes.actions_width,
            height_policy = 'fixed', width_policy = 'fixed',
            margin = sizes.standard_margin,
        ),
        contains = [ 'row_actions' ]
    ),
    'row_actions': dict(
        component_class = Row,
        component_arguments = dict(
            align = ( 'center', 'end' ),
            visible = False,
        ),
        contains = [
            'button_edit_title',
            'button_edit_labels',
            'button_delete',
        ],
    ),
    'button_edit_title': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'edit', icon_size = sizes.icon_size,
            **_icon_button_attributes,
        ),
    ),
    'button_edit_labels': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'bookmark-edit', icon_size = sizes.icon_size,
            **_icon_button_attributes,
        ),
    ),
    'button_delete': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'trash', icon_size = sizes.icon_size,
            **_icon_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_delete_conversation' ),
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
        contains = [
            'row_behaviors',
            'row_actions_structure',
        ],
    ),
    'row_behaviors': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'label_role',
            'toggle_active',
            'toggle_pinned',
        ],
    ),
    'label_role': dict(
        component_class = StaticText,
        component_arguments = dict(
            align = 'center', width = sizes.icon_button_width,
        ),
    ),
    'toggle_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '💬', #icon = 'message-dots',
            value = False,
            **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_message_active' ),
    ),
    'toggle_pinned': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '📌', #icon = 'pin',
            value = False,
            **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_message_pinned' ),
    ),
    'row_actions_structure': dict(
        component_class = Row,
        component_arguments = dict(
            height = sizes.actions_height, width = sizes.actions_width,
            height_policy = 'fixed', width_policy = 'fixed',
        ),
        contains = [ 'row_actions' ]
    ),
    'row_actions': dict(
        component_class = Row,
        component_arguments = dict(
            align = ( 'center', 'end' ),
            visible = False,
        ),
        contains = [
            'button_copy',
            'button_delete',
            'button_edit',
            'button_fork',
            # TODO: button_regenerate
        ],
    ),
    'button_copy': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'copy',
            **_icon_button_attributes,
        ),
    ),
    'button_delete': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'trash',
            visible = False,
            **_icon_button_attributes,
        ),
    ),
    'button_edit': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'edit',
            visible = False,
            **_icon_button_attributes,
        ),
    ),
    'button_fork': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'git-fork',
            visible = False,
            **_icon_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_fork_conversation' ),
    ),
    'spacer_right': dict( component_class = HSpacer ),
}

json_conversation_message_layout = conversation_message_common_layout.copy( )
json_conversation_message_layout.update( {
    'text_message': dict(
        component_class = JSON,
        component_arguments = dict(
            depth = 1, theme = 'light',
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            styles = { 'overflow': 'auto' },
            **_message_column_width_attributes,
        ),
    ),
} )

plain_conversation_message_layout = conversation_message_common_layout.copy( )
plain_conversation_message_layout.update( {
    'text_message': dict(
        component_class = StaticText,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            styles = { 'overflow': 'auto' },
            **_message_column_width_attributes,
        ),
    ),
} )

rich_conversation_message_layout = conversation_message_common_layout.copy( )
rich_conversation_message_layout.update( {
    'text_message': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            styles = { 'overflow': 'auto' },
            stylesheets = [ _css_code_overflow ],
            **_message_column_width_attributes,
        ),
    ),
} )
