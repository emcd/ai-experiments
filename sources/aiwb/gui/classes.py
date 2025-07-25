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


# References:
#   * https://blog.holoviz.org/posts/reactivehtml/index.html
#   * https://discourse.holoviz.org/t/how-to-trigger-re-render-of-template/5799/2


import param

from panel.custom import Children, ReactiveHTML
from panel.layout import Row
from panel.layout.base import ListLike

from . import __


# Applying stylesheets from native Panel widgets to custom widgets is not
# straightforward, because the Panel widgets are derived from Bokeh widgets,
# where the stylesheets are intrinsic on the HTML+CSS side and not exposed
# on the Python side.
#
# References:
# * https://github.com/holoviz/panel/issues/5586
# * https://panel.holoviz.org/how_to/styling/apply_css.html

# https://github.com/bokeh/bokeh/blob/4e546e5fa7a14caa9812e9ef392a0d70054b28ce/bokehjs/src/less/widgets/inputs.less
# AI-formatted CSS dump from browser.

_bokeh_button_stylesheets = '''
.bk-btn,::file-selector-button {
    height: 100%;
    display: inline-block;
    text-align: center;
    vertical-align: middle;
    white-space: nowrap;
    cursor: pointer;
    padding: var(--padding-vertical) var(--padding-horizontal);
    font-size: var(--font-size);
    border: 1px solid transparent;
    border-radius: var(--border-radius);
    outline: 0;
    outline-offset: -5px;
    user-select: none;
    -webkit-user-select: none;
}

.bk-btn:hover,::file-selector-button:hover,.bk-btn:focus,::file-selector-button:focus {
    text-decoration: none;
}

.bk-btn:active,::file-selector-button:active,.bk-active.bk-btn,.bk-active::file-selector-button {
    background-image: none;
    box-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
}

.bk-btn[disabled] {
    cursor: not-allowed;
    pointer-events: none;
    opacity: 0.65;
    box-shadow: none;
}

.bk-btn-default {
    color: #333;
    background-color: #fff;
    border-color: #ccc;
}

.bk-btn-default:hover {
    background-color: #f5f5f5;
    border-color: #b8b8b8;
}

.bk-active.bk-btn-default {
    background-color: #ebebeb;
    border-color: #adadad;
}

.bk-btn-default[disabled],.bk-btn-default[disabled]:hover,
.bk-btn-default[disabled]:focus,.bk-btn-default[disabled]:active,
.bk-active.bk-btn-default[disabled] {
    background-color: #e6e6e6;
    border-color: #ccc;
}

.bk-btn-default:focus,.bk-btn-default:active {
    outline: 1px dotted #ccc;
}
'''

_bokeh_font_stylesheets = '''
:host {
    --base-font: var(--bokeh-base-font, Helvetica, Arial, sans-serif);
    --mono-font: var(--bokeh-mono-font, monospace);
    --font-size: var(--bokeh-font-size, 12px);
    --line-height: calc(20 / 14);
    --line-height-computed: calc(var(--font-size) * var(--line-height));
    --border-radius: 4px;
    --padding-vertical: 6px;
    --padding-horizontal: 12px;
    --bokeh-top-level: 1000;
}

:host {
    box-sizing: border-box;
    font-family: var(--base-font);
    font-size: var(--font-size);
    line-height: var(--line-height);
}

*, *:before, *:after {
    box-sizing: inherit;
    font-family: inherit;
}

pre, code {
    font-family: var(--mono-font);
    margin: 0;
}
'''

_bokeh_input_stylesheets = '''
:host {
    --input-min-height: calc(var(--line-height-computed) + 2*var(--padding-vertical) + 2px);
}

.bk-input {
    position: relative;
    display: inline-block;
    width: 100%;
    flex-grow: 1;
    min-height: var(--input-min-height);
    padding: 0 var(--padding-horizontal);
    background-color: #fff;
    border: 1px solid #ccc;
    border-radius: var(--border-radius);
}

.bk-input:focus {
    border-color: #66afe9;
    outline: 0;
    box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.075), 0 0 8px rgba(102, 175, 233, 0.6);
}

.bk-input::placeholder,
.bk-input:-ms-input-placeholder,
.bk-input::-moz-placeholder,
.bk-input::-webkit-input-placeholder {
    color: #999;
    opacity: 1;
}

.bk-input[disabled],
.bk-input.bk-disabled {
    cursor: not-allowed;
    background-color: #eee;
    opacity: 1;
}

.bk-input-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
}

.bk-input-container .bk-input-prefix,
.bk-input-container .bk-input-suffix {
    display: flex;
    align-items: center;
    flex: 0 1 0;
    border: 1px solid #ccc;
    border-radius: var(--border-radius);
    padding: 0 var(--padding-horizontal);
    background-color: #e6e6e6;
}

.bk-input-container .bk-input-prefix {
    border-right: none;
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
}

.bk-input-container .bk-input-suffix {
    border-left: none;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}

.bk-input-container .bk-input {
    flex: 1 0 0;
}

.bk-input-container .bk-input:not(:first-child) {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}

.bk-input-container .bk-input:not(:last-child) {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
}

input[type=file].bk-input {
    padding-left: 0;
}

input[type=file]::file-selector-button {
    box-sizing: inherit;
    font-family: inherit;
    font-size: inherit;
    line-height: inherit;
}

select:not([multiple]).bk-input,
select:not([size]).bk-input {
    height: auto;
    appearance: none;
    -webkit-appearance: none;
    background-image: url('data:image/svg+xml;utf8,<svg version="1.1" viewBox="0 0 25 20" xmlns="http://www.w3.org/2000/svg"><path d="M 0,0 25,0 12.5,20 Z" fill="black" /></svg>');
    background-position: right 0.5em center;
    background-size: 8px 6px;
    background-repeat: no-repeat;
    padding-right: calc(var(--padding-horizontal) + 8px);
}

option {
    padding: 0;
}

select[multiple].bk-input,
select[size].bk-input,
textarea.bk-input {
    height: auto;
}

.bk-input-group {
    position: relative;
    width: 100%;
    height: 100%;
    display: inline-flex;
    flex-wrap: nowrap;
    align-items: start;
    flex-direction: column;
    white-space: nowrap;
}

.bk-input-group.bk-inline {
    flex-direction: row;
}

.bk-input-group.bk-inline > *:not(:first-child) {
    margin-left: 5px;
}

.bk-input-group > .bk-spin-wrapper {
    display: inherit;
    width: inherit;
    height: inherit;
    position: relative;
    overflow: hidden;
    padding: 0;
    vertical-align: middle;
}

.bk-input-group > .bk-spin-wrapper input {
    padding-right: 20px;
}

.bk-input-group > .bk-spin-wrapper > .bk-spin-btn {
    position: absolute;
    display: block;
    height: 50%;
    min-height: 0;
    min-width: 0;
    width: 30px;
    padding: 0;
    margin: 0;
    right: 0;
    border: none;
    background: none;
    cursor: pointer;
}

.bk-input-group > .bk-spin-wrapper > .bk-spin-btn:before {
    content: "";
    display: inline-block;
    transform: translateY(-50%);
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
}

.bk-input-group > .bk-spin-wrapper > .bk-spin-btn.bk-spin-btn-up {
    top: 0;
}

.bk-input-group > .bk-spin-wrapper > .bk-spin-btn.bk-spin-btn-up:before {
    border-bottom: 5px solid black;
}

.bk-input-group > .bk-spin-wrapper > .bk-spin-btn.bk-spin-btn-up:disabled:before {
    border-bottom-color: grey;
}

.bk-input-group > .bk-spin-wrapper > .bk-spin-btn.bk-spin-btn-down {
    bottom: 0;
}

.bk-input-group > .bk-spin-wrapper > .bk-spin-btn.bk-spin-btn-down:before {
    border-top: 5px solid black;
}

.bk-input-group > .bk-spin-wrapper > .bk-spin-btn.bk-spin-btn-down:disabled:before {
    border-top-color: grey;
}

.bk-description {
    position: relative;
    display: inline-block;
    margin-left: 0.25em;
    vertical-align: middle;
    margin-top: -2px;
    cursor: pointer;
}

.bk-description > .bk-icon {
    opacity: 0.5;
    width: 18px;
    height: 18px;
    background-color: gray;
    mask-image: var(--bokeh-icon-help);
    mask-size: contain;
    mask-repeat: no-repeat;
    -webkit-mask-image: var(--bokeh-icon-help);
    -webkit-mask-size: contain;
    -webkit-mask-repeat: no-repeat;
}

label:hover > .bk-description > .bk-icon,
.bk-icon.bk-opaque {
    opacity: 1;
}
'''

_bokeh_menu_stylesheets = '''
:host {
    position: relative;
}

.bk-menu {
    position: absolute;
    left: 0;
    width: 100%;
    z-index: var(--bokeh-top-level);
    cursor: pointer;
    font-size: var(--font-size);
    background-color: #fff;
    border: 1px solid #ccc;
    border-radius: var(--border-radius);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.175);
}

.bk-menu.bk-above {
    bottom: 100%;
}

.bk-menu.bk-below {
    top: 100%;
}

.bk-menu > .bk-divider {
    height: 1px;
    margin: calc(var(--line-height-computed)/2 - 1px) 0;
    overflow: hidden;
    background-color: #e5e5e5;
}

.bk-menu > :not(.bk-divider) {
    padding: var(--padding-vertical) var(--padding-horizontal);
}

.bk-menu > :not(.bk-divider):hover,.bk-menu > :not(.bk-divider).bk-active {
    background-color: #e6e6e6;
}
'''


class AdaptiveTextArea( ReactiveHTML ):
    ''' Dynamically-sized text area which posts update and submit events. '''

    # TODO: 'max_length' breaks object serialization for some reason;
    #       need to find out why and fix.

    #max_length = param.Integer( default = 32767 )
    placeholder = param.String( default = '' )
    submission_behavior = param.String( default = 'slack-alt' )
    value = param.String( default = '' )
    value_to_ingest = param.String( default = '' )

    content_update_event = param.Event( )
    submission_event = param.Event( )

    _style_css__ = param.String( default = '' )

    _style_default__ = __.DictionaryProxy( {
        'font-size': '100%',
        'resize': 'none',
    } )

    _child_config = {
        'value': 'template',
    }

    _scripts = {
        'init': '''
            state.debounce_timer = null;
            textarea.value = data.value || '';
            self.auto_resize();''',
        'auto_resize': '''
            const taMinHeight = model.min_height || 0;
            const taMaxHeight = model.max_height || Infinity;
            // Account for border and padding.
            const taOffset = textarea.offsetHeight - textarea.clientHeight;
            // Reset scroll height on shrinkage; otherwise it sticks.
            // https://stackoverflow.com/a/18937018/14833542
            textarea.style.height = '0';
            model.height = taOffset + Math.min(
                Math.max(textarea.scrollHeight, taMinHeight), taMaxHeight);
            textarea.style.height = `${model.height}px`;
            if (!state.debounce_timer) {
                state.debouce_timer = setTimeout(
                    function() {
                        self._send_content_update_event();
                        state.debounce_timer = null;
                    }, 400);
            }''',
        'handle_keydown': '''
            if ('Enter' !== event.key) return true;
            if (!data.submission_behavior) return true;
            const modifiers = new Set();
            if (event.altKey) modifiers.add('alt');
            if (event.ctrlKey) modifiers.add('ctrl');
            if (event.metaKey) modifiers.add('meta');
            if (event.shiftKey) modifiers.add('shift');
            const isMac = 0 <= navigator.platform.toUpperCase().indexOf('MAC');
            let toSubmit = false;
            if ('chatgpt' == data.submission_behavior) {
                toSubmit = (0 === modifiers.size);
            }
            else if ('slack-alt' == data.submission_behavior) {
                toSubmit = modifiers.has(isMac ? 'meta' : 'ctrl');
            }
            else if ('jupyter' == data.submission_behavior) {
                toSubmit = modifiers.has('shift');
            }
            if (toSubmit) {
                event.preventDefault();
                self._send_submission_event();
                textarea.value = '';
                self.auto_resize();
                return false;
            }
            return true;''',
        'value_to_ingest': '''
            if (data.value_to_ingest !== textarea.value) {
                //textarea.focus();
                textarea.value = data.value_to_ingest || '';
                //void textarea.offsetHeight;
                self.auto_resize();
            }
        ''',
        '_send_content_update_event': '''
            console.log('Sending update event.');
            data.value = textarea.value;
            data.content_update_event = true;''',
        '_send_submission_event': '''
            console.log('Sending submission event.');
            data.value = textarea.value;
            data.submission_event = true;''',
    }

    _stylesheets = [ _bokeh_font_stylesheets, _bokeh_input_stylesheets ]

    _template = '''
        <textarea id="textarea"
            class="my-no-scrollbar bk-input"
            oninput="${script('auto_resize')}"
            onkeydown="${script('handle_keydown')}"
            placeholder="${placeholder}"
            style="${_style_css__}; height: ${model.height}px; width: ${model.width}px;"
        ></textarea>'''

    def __init__( self, **params ):
        super( ).__init__( **params )
        style = self._style_default__.copy( )
        style.update( params.get( 'style', { } ) )
        self._style_css__ = '; '.join( map( ': '.join, style.items( ) ) )

    def clear( self ):
        ''' Clears text area. '''
        value = self.value
        # Force change event to occur when necessary.
        # Otherwise, do not trigger change event to avoid flashing.
        if value != self.value_to_ingest: self.value_to_ingest = value
        if self.value_to_ingest: self.value_to_ingest = ''


class CompactSelector( ReactiveHTML ):

    options = param.Dict( )
    value = param.String( )
    _style_css__ = param.String( )

    _style_default__ = __.DictionaryProxy( {
        'appearance': 'none',
        '-moz-appearance': 'none', '-webkit-appearance': 'none',
        'border-radius': '10%',
        'padding': '0',
        # https://stackoverflow.com/a/60236111/14833542
        'text-align': 'center', 'text-align-last': 'center',
        '-moz-text-align-last': 'center',
    } )

    _stylesheets = [ _bokeh_font_stylesheets, _bokeh_input_stylesheets ]

    _template = '''
        <div class="bk-input-group">
        <select id="CompactSelector"
            class="bk-input"
            onchange="${_select_change}"
            style="${_style_css__}; height: ${model.height}px; width: ${model.width}px;",
            value="${value}"
        >
            {% for option_name, option_value in options.items( ) %}
            <option value="{{option_name}}">{{option_value}}</option>
            {% endfor %}
        </select>
        </div>'''

    def __init__( self, **params ):
        super( ).__init__( **params )
        style = self._style_default__.copy( )
        style.update( params.get( 'style', { } ) )
        self._style_css__ = '; '.join( map( ': '.join, style.items( ) ) )

    def _select_change( self, event ):
        self.value = event.data[ 'target' ][ 'value' ]


class ConversationDescriptor(
    __.immut.DataclassObjectMutable
):

    identity: str = (
        __.dataclass_declare( default_factory = lambda: __.uuid4( ).hex ) )
    timestamp: int = (
        __.dataclass_declare( default_factory = __.time_ns ) )
    title: __.typx.Optional[ str ] = None
    labels: __.AbstractMutableSequence[ str ] = (
        __.dataclass_declare( default_factory = list ) )
    gui: __.typx.Optional[ __.SimpleNamespace ] = None
    indicator: __.typx.Optional[ Row ] = None


class ConversationIndicator( ReactiveHTML ):

    clicked = param.Event( default = False )
    mouse_hover__ = param.Boolean( False )
    row__ = param.Parameter( )

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

    def __init__( self, container_gui, **params ):
        super( ).__init__( **params )
        # TODO: Remove non-GUI component attributes.
        self.gui__ = container_gui
        self.row__ = container_gui.column_indicator # TODO: Rename.
        self.identity__ = container_gui.identity__

    def _div_click( self, event ):
        # TODO: Suppress event propagation from buttons contained in this.
        #       Especially for 'delete' button as this results in a
        #       'bokeh.core.serialization.DeserializationError' from
        #       an unresolved reference after deletion.
        self.clicked = True

    @param.depends( 'mouse_hover__', watch = True )
    def _handle_mouse_hover__( self ):
        is_current = (
            self.gui__.parent__.column_conversations_indicators
            .current_descriptor__.identity
            == self.identity__ )
        self.gui__.interceptor_actions.visible = (
            not self.gui__.column_title_edit.visible and self.mouse_hover__ )
        self.gui__.button_title_regenerate.visible = is_current


class ConversationMessage( ReactiveHTML ):

    mouse_hover__ = param.Boolean( False )
    row__ = param.Parameter( )

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

    def __init__( self, row, **params ):
        super( ).__init__( **params )
        self.row__ = row

    @param.depends( 'mouse_hover__', watch = True )
    def _handle_mouse_hover__( self ):
        self.row__.gui__.row_actions.visible = self.mouse_hover__


class EventsInterceptor( ListLike, ReactiveHTML ):
    ''' Container which intercepts and posts DOM events. '''

    clicked = param.Boolean( )
    key_pressed = param.String( )
    objects = Children( )

    _scripts = {
        'handle_click': '''
            data.clicked = true;
            event.stopPropagation();
        ''',

        'handle_keydown': '''
            data.key_pressed = event.key;
            event.stopPropagation();
        ''',
    }

    _template = '''
        <div id="EventsInterceptor" class="pn-container"
            onclick="${script('handle_click')}"
            onkeydown="${script('handle_keydown')}"
        >
            {% for obj in objects %}
                <div id="object">${obj}</div>
            {% endfor %}
        </div>
    '''.strip( )

_menu_objects_stylesheets = '''
        .menu-objects-container {
            position: relative;
        }

        .menu-objects-menu {
            box-sizing: border-box;
            max-width: 336px;
            overflow: visible;
            position: fixed;
            width: max-content;
        }

        .menu-objects-item {
            cursor: default;
        }

        .bk-menu > .menu-objects-item:hover {
            background-color: transparent;
        }
'''
class MenuObjects( ListLike, ReactiveHTML ):
    ''' Dropdown menu which can contain arbitrary widgets. '''

    objects = Children( )

    _stylesheets = [
        _bokeh_font_stylesheets,
        _bokeh_button_stylesheets,
        _bokeh_menu_stylesheets,
        _menu_objects_stylesheets,
    ]

    _scripts = {
        'handle_mouseleave': '''
            state.menuVisible = false;
            menu.style.display = 'none';
        ''',

        'init': '''
            state.menuVisible = false;
        ''',

        'toggle_menu': '''
            state.menuVisible = !state.menuVisible;
            if (state.menuVisible) {
                // Position menu relative to toggle button
                const toggleRect = toggle.getBoundingClientRect();
                menu.style.top = `${toggleRect.bottom}px`;
                menu.style.left = `${toggleRect.left}px`;
                menu.style.display = 'block';
            } else {
                menu.style.display = 'none';
            }
        ''',
    }

    _template = '''
        <div id="MenuObjects"
            class="bk-Dropdpwn solid menu-objects-container"
            onmouseleave="${script('handle_mouseleave')}"
        >
            <div class="bk-button-group">
                <button id="toggle"
                    class="bk-btn bk-btn-default"
                    onclick="${script('toggle_menu')}"
                >⋯</button>
            </div>
            <div id="menu"
                class="bk-menu menu-objects-menu"
                style="display: none;"
            >
                {% for obj in objects %}
                    <div id="object" class="menu-objects-item">${obj}</div>
                {% endfor %}
            </div>
        </div>
    '''.strip( )
