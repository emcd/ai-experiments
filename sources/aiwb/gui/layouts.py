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

    * Use constant sizes only for small elements. These serve as the basis for
      consistent sizing on a larger scale.

    * The 'max' height policy needs both 'height' and 'max_height' to be
      effective. Similarly for the 'max' width policy.

    * Prefer margins over padding for greater control. '''


from types import SimpleNamespace

from panel.layout import Card, Column, HSpacer, Row
from panel.pane import JSON, Markdown
from panel.widgets import (
    Button,
    Checkbox,
    FloatSlider,
    IntSlider,
    LoadingSpinner,
    MultiChoice,
    Select,
    StaticText,
    TextInput,
    Toggle,
)

from .classes import AdaptiveTextArea, CompactSelector, ConversationMessage


sizes = SimpleNamespace(
    action_button_height = 40,
    action_button_width = 120,
    element_margin = 2,
    icon_button_height = 40, # distortion if smaller, Bokeh/Panel limitation
    icon_size = '1em',
    message_width_max = 640,
    message_width_min = 480,
    sidebar_width_max = 336,
    standard_margin = 5,
)
sizes.icon_button_width = sizes.icon_button_height
sizes.actions_height = sizes.icon_button_height + 2 * sizes.element_margin
sizes.actions_width = (
      1 * sizes.icon_button_width
    + 2 * sizes.element_margin
    + 10 # border widths + extra fudge
)
sizes.prompt_width = sizes.message_width_max # - 2 * sizes.standard_margin


_css_code_overflow = '''
div[class="codehilite"] {
    overflow-x: auto;
}
'''


_action_button_attributes = dict(
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
            'interpolant_modal_area',
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
    'interpolant_modal_area': dict(
        component_class = Row,
        component_arguments = dict( width_policy = 'max' ),
        interpolant_id = 'modal',
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
            'button_upgrade_conversations',
            'button_remove_orphans',
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
    'button_upgrade_conversations': dict(
        component_class = Button,
        component_arguments = dict(
            name = '🔃 Upgrade Conversations',
            button_type = 'light',
            visible = False,
            **_action_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_upgrade_conversations' ),
    ),
    'button_remove_orphans': dict(
        component_class = Button,
        component_arguments = dict(
            name = '🔃 Remove Orphans',
            button_type = 'light',
            visible = False,
            **_action_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_remove_orphans' ),
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
        component_arguments = dict( visible = False ),
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
        contains = [ 'toggle_system_prompt_active', ],
    ),
    'toggle_system_prompt_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            # TODO: Set icon instead of name.
            name = '📏', value = True, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_system_prompt_active' ),
    ),
    'column_system_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            **_message_column_width_attributes,
        ),
        contains = [
            'row_system_prompt_selection',
            'row_system_prompt_variables',
            'text_system_prompt',
        ],
    ),
    'row_system_prompt_selection': dict(
        component_class = Row,
        contains = [
            'selector_system_prompt',
            'toggle_system_prompt_display',
        ],
    ),
    'selector_system_prompt': dict(
        component_class = Select,
        component_arguments = dict(
            options = [ 'General Conversation' ],
            value = 'General Conversation',
            align = 'center',
        ),
        event_functions = dict( value = 'on_select_system_prompt' ),
        populator_function = 'populate_supervisor_prompts_selector',
    ),
    'toggle_system_prompt_display': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Eye}\uFE0F', value = False, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_system_prompt_display' ),
    ),
    'row_system_prompt_variables': dict(
        component_class = Row,
        persistence_functions = dict(
            save = (
                'save_prompt_variables', dict( species = 'supervisor' ) ),
            restore = (
                'restore_prompt_variables', dict( species = 'supervisor' ) ),
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
        contains = [ 'toggle_functions_active', ],
    ),
    'toggle_functions_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            # TODO: Set icon instead of name.
            name = '🧰', value = True, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_functions_active' ),
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
            placeholder = 'Please click to select invocables.',
            delete_button = True,
            width_policy = 'max',
        ),
        event_functions = dict( value = 'on_select_invocables' ),
    ),
    'row_function_options': dict(
        component_class = Row,
        contains = [
            'toggle_functions_display',
            'checkbox_auto_functions',
            'checkbox_elide_function_history',
        ],
    ),
    'toggle_functions_display': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Eye}\uFE0F', value = False, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_functions_display' ),
    ),
    'checkbox_auto_functions': dict(
        component_class = Checkbox,
        component_arguments = dict(
            name = 'Automatic Function Execution',
            value = True,
            align = 'center',
        ),
    ),
    'checkbox_elide_function_history': dict(
        component_class = Checkbox,
        component_arguments = dict(
            name = 'Function History Elision',
            value = False,
            align = 'center',
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
        contains = [ 'row_conversation_status', 'row_user_prompts' ],
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
    'row_user_prompts': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'spacer_left_user_prompts',
            'row_user_prompts_header',
            'column_user_prompt',
            'spacer_right_user_prompts',
        ],
    ),
    'spacer_left_user_prompts': dict( component_class = HSpacer ),
    'row_user_prompts_header': dict(
        component_class = Row,
        component_arguments = dict( **_message_header_attributes ),
        contains = [ 'selector_user_prompt_class', ],
    ),
    'selector_user_prompt_class': dict(
        component_class = CompactSelector,
        component_arguments = dict(
            options = {
                'freeform': '\N{Lower Left Ballpoint Pen}\uFE0F',
                'canned': '🥫'
            },
            value = 'freeform',
            align = 'center',
            height = sizes.icon_button_height,
            width = sizes.icon_button_width,
            height_policy = 'fixed', width_policy = 'fixed',
        ),
        event_functions = dict( value = 'on_select_user_prompt_class' ),
    ),
    'column_user_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            **_message_column_width_attributes,
        ),
        contains = [
            'column_canned_prompt',
            'column_freeform_prompt',
            'row_actions',
        ],
    ),
    'column_canned_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            visible = False,
        ),
        contains = [
            'row_canned_prompt_selection',
            'row_canned_prompt_variables',
            'text_canned_prompt',
        ],
    ),
    'row_canned_prompt_selection': dict(
        component_class = Row,
        contains = [
            'selector_canned_prompt',
            'toggle_canned_prompt_display',
            'button_canned_prompt',
        ],
    ),
    'selector_canned_prompt': dict(
        component_class = Select,
        component_arguments = dict(
            options = [ 'Recap: General Conversation' ],
            value = 'Recap: General Conversation',
            align = 'center',
        ),
        event_functions = dict( value = 'on_select_canned_prompt' ),
        populator_function = 'populate_canned_prompts_selector',
    ),
    'toggle_canned_prompt_display': dict(
        component_class = Toggle,
        component_arguments = dict(
            name = '\N{Eye}\uFE0F', value = False, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_canned_prompt_display' ),
    ),
    'button_canned_prompt': dict(
        component_class = Button,
        component_arguments = dict(
            name = '\N{Lower Left Ballpoint Pen}\uFE0F',
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
    'column_freeform_prompt': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
        ),
        contains = [ 'text_freeform_prompt' ],
    ),
    'text_freeform_prompt': dict(
        component_class = AdaptiveTextArea,
        component_arguments = dict(
            placeholder = 'Enter message here...',
            height_policy = 'auto', width_policy = 'max',
            max_height = 240, height = 48,
            max_width = sizes.prompt_width, width = sizes.prompt_width,
        ),
        event_functions = dict(
            content_update_event = 'on_change_freeform_prompt',
            submission_event = 'on_submit_freeform_prompt',
        ),
    ),
    # TODO? Convert to column and place to right of prompts column.
    'row_actions': dict(
        component_class = Row,
        contains = [
            'button_chat',
            'toggle_summarize', # TODO: Rename to 'toggle_compactify'.
            'button_search',
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
    'spacer_right_user_prompts': dict( component_class = HSpacer ),
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
        # TODO: Dynamically-generated sections for each kind of model:
        #       chat completion, picture generation, text-to-speech, etc...
        contains = [
            'card_conversation',
            'card_vectorstore_textual',
            'text_autoscroll_status',
            'text_clipboard_export',
        ],
    ),
    'card_conversation': dict(
        component_class = Card,
        component_arguments = dict(
            title = 'Conversation Model',
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'selector_provider',
            'selector_model',
            'slider_temperature',
            'slider_responses_count',
            'text_tokens_total',
        ],
    ),
    'selector_provider': dict(
        # TODO: selector_provider_client
        component_class = Select,
        component_arguments = dict(
            name = 'Provider',
        ),
        event_functions = dict( value = 'on_select_provider' ),
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
    'slider_responses_count': dict(
        component_class = IntSlider,
        component_arguments = dict(
            name = 'Responses Count',
            start = 1, end = 3, step = 1, value = 1,
        ),
    ),
    'text_tokens_total': dict(
        component_class = StaticText,
        component_arguments = dict( name = 'Token Counter', value = '0', ),
        persist = False,
    ),
    'card_vectorstore_textual': dict(
        component_class = Card,
        component_arguments = dict(
            title = 'Textual Vector Database',
            collapsed = True,
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'selector_vectorstore',
            'slider_documents_count',
        ],
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
    'text_autoscroll_status': dict(
        component_class = TextInput,
        component_arguments = dict( value = 'automatic', visible = False ),
        javascript_cb_generator = 'generate_document_autoscroller',
        persist = False,
    ),
    # Hack because of how Panel and Javascript interact.
    'text_clipboard_export': dict(
        component_class = TextInput,
        component_arguments = dict( visible = False ),
        javascript_cb_generator = 'generate_message_copier',
        persist = False,
    ),
}

conversation_indicator_layout = {
    'column_indicator': dict(
        component_class = Column,
        # TODO: Add row for labels.
        contains = [ 'row_indicator' ],
    ),
    'row_indicator': dict(
        component_class = Row,
        contains = [ 'text_title', 'row_actions' ],
    ),
    'text_title': dict(
        component_class = Markdown,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = sizes.standard_margin,
            max_width = sizes.sidebar_width_max,
            width = sizes.sidebar_width_max,
        ),
    ),
    'row_actions': dict(
        component_class = Row,
        component_arguments = dict(
            styles = {
                # TODO: Use theme colors.
                'background-color': '#e8e8e8',
                'border-radius': '5%',
                'box-shadow': '-2px 2px 3px rgba(0, 0, 0, 0.2)',
                'padding': f"{sizes.element_margin}px",
                'position': 'absolute',
                'right': f"{sizes.standard_margin}px",
                'top': f"{sizes.standard_margin}px",
                'z-order': '25',
            },
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
    'row_canister': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        contains = [
            'spacer_left',
            'row_header',
            'rehtml_message',
            'spacer_right',
        ],
    ),
    'spacer_left': dict( component_class = HSpacer ),
    'row_header': dict(
        component_class = Row,
        component_arguments = dict( **_message_header_attributes ),
        contains = [ 'toggle_active', ],
    ),
    'toggle_active': dict(
        component_class = Toggle,
        component_arguments = dict(
            value = False, **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_message_active' ),
    ),
    'rehtml_message': dict(
        component_class = ConversationMessage,
        contains = [ 'row_content' ],
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            margin = 0,
            **_message_column_width_attributes,
        ),
    ),
    'row_content': dict(
        component_class = Row,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
        ),
        # TODO: Replace 'text_message' with 'pane_content'.
        contains = [ 'text_message', 'column_edit', 'row_actions' ],
    ),
    'column_edit': dict(
        component_class = Column,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            visible = False,
        ),
        contains = [
            'text_message_edit',
            'row_edit_actions',
        ],
    ),
    'text_message_edit': dict(
        component_class = AdaptiveTextArea,
        component_arguments = dict(
            height_policy = 'auto', width_policy = 'max',
            max_height = 240,
            margin = sizes.standard_margin,
            submission_behavior = 'slack-alt',
            **_message_column_width_attributes,
        ),
        event_functions = dict(
            content_update_event = 'on_change_message_edit',
            submission_event = 'on_submit_message_edit',
        ),
    ),
    'row_edit_actions': dict(
        component_class = Row,
        contains = [
            'button_edit_submit',
            'button_edit_cancel',
        ],
    ),
    'button_edit_submit': dict(
        component_class = Button,
        component_arguments = dict(
            name = 'Submit',
            button_type = 'primary',
            **_action_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_message_edit_submit' ),
    ),
    'button_edit_cancel': dict(
        component_class = Button,
        component_arguments = dict(
            name = 'Cancel',
            button_type = 'default',
            **_action_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_message_edit_cancel' ),
    ),
    'row_actions': dict(
        component_class = Row,
        component_arguments = dict(
            styles = {
                # TODO: Use theme colors.
                'background-color': '#e8e8e8',
                'border-radius': '5%',
                'box-shadow': '-2px 2px 3px rgba(0, 0, 0, 0.2)',
                'padding': f"{sizes.element_margin}px",
                'position': 'absolute',
                'right': f"{sizes.standard_margin}px",
                'top': f"{sizes.standard_margin}px",
                'z-order': '5',
            },
            visible = False,
        ),
        contains = [
            'toggle_pinned',
            # TODO: Vertical separator.
            'button_copy',
            'button_delete',
            'button_edit',
            'button_fork',
            'button_invoke',
            'button_regenerate',
        ],
    ),
    'toggle_pinned': dict(
        component_class = Toggle,
        component_arguments = dict(
            #name = '📌',
            icon = 'pin', # TODO: Alternate with 'pinned'.
            value = False,
            **_icon_button_attributes,
        ),
        event_functions = dict( value = 'on_toggle_message_pinned' ),
    ),
    'button_copy': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'copy',
            **_icon_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_copy_message' ),
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
        event_functions = dict( on_click = 'on_click_message_edit' ),
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
    'button_invoke': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'function',
            visible = False,
            **_icon_button_attributes,
        ),
        event_functions = dict( on_click = 'on_click_use_invocables' ),
    ),
    'button_regenerate': dict(
        component_class = Button,
        component_arguments = dict(
            icon = 'reload',
            visible = False,
            **_icon_button_attributes,
        ),
    ),
    'spacer_right': dict( component_class = HSpacer ),
}

json_conversation_message_layout = conversation_message_common_layout.copy( )
json_conversation_message_layout.update( {
    'text_message': dict(
        component_class = JSON,
        component_arguments = dict(
            depth = 0, theme = 'light',
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
