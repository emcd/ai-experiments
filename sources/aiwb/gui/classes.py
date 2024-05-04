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


import param

from panel.layout import Row
from panel.reactive import ReactiveHTML

from . import base as __


class AdaptiveTextArea( ReactiveHTML ):

    latent_value = param.String( default = '' )
    # TODO: 'max_length' breaks object serialization for some reason;
    #       need to find out why and fix.
    #max_length = param.Integer( default = 32767 )
    placeholder = param.String( default = '' )
    submission_behavior = param.String( default = 'slack-alt' )
    submission_value = param.String( default = '' )
    value = param.String( default = '' )
    _style_css__ = param.String( default = '' )

    _style_default__ = __.DictionaryProxy( {
        'resize': 'none',
    } )

    _child_config = {
        'value': 'template',
    }

    _scripts = {
        'my_keydown': '''
            if ('Enter' !== event.key) return true;
            if (!data.submission_behavior) return true;
            const modifiers = new Set();
            if (event.altKey) modifiers.add('alt');
            if (event.ctrlKey) modifiers.add('ctrl');
            if (event.metaKey) modifiers.add('meta');
            if (event.shiftKey) modifiers.add('shift');
            const onMac = (0 <= navigator.userAgent.indexOf("Mac"));
            var toSubmit = false;
            if ('chatgpt' == data.submission_behavior) {
                toSubmit = (0 === modifiers.size);
            }
            else if (1 === modifiers.size) {
                if ('slack-alt' == data.submission_behavior) {
                    toSubmit = modifiers.has(onMac ? 'meta' : 'ctrl');
                }
                else if ('jupyter' == data.submission_behavior) {
                    toSubmit = modifiers.has('shift');
                }
            }
            modifiers.clear();
            if (toSubmit) {
                event.preventDefault();
                data.submission_value = data.value;
                // XXX: Hack to trigger event.
                data.latent_value = data.value + '\\n';
                return false;
            }
            return true;''',
        'my_keyup': '''data.value = textarea.value;''',
        'value': '''
            textarea.value = data.value;
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
            if (!state.timer_active) {
                state.timer_active = true;
                setTimeout(
                    function() {
                        data.latent_value = textarea.value;
                        state.timer_active = false;
                    }, 400);
            }
            return true;''',
    }

    _template = '''
        <textarea id="textarea"
            class="my-no-scrollbar"
            maxlength="32767"
            onkeydown="${script('my_keydown')}"
            onkeyup="${script('my_keyup')}"
            placeholder="${placeholder}"
            style="${_style_css__}; height: ${model.height}px; width: ${model.width}px;"
        >
        ${value}
        </textarea>'''

    def __init__( self, **params ):
        super( ).__init__( **params )
        style = self._style_default__.copy( )
        style.update( params.get( 'style', { } ) )
        self._style_css__ = '; '.join( map( ': '.join, style.items( ) ) )


class CompactSelector( ReactiveHTML ):

    options = param.Dict( )
    value = param.String( )
    _style_css__ = param.String( )

    _style_default__ = __.DictionaryProxy( {
        'appearance': 'none',
        '-moz-appearance': 'none', '-webkit-appearance': 'none',
        'border-radius': '10%',
        # https://stackoverflow.com/a/60236111/14833542
        'text-align': 'center', 'text-align-last': 'center',
        '-moz-text-align-last': 'center',
    } )

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

    # TODO: Should only need GUI namespace as argument.
    def __init__( self, title, identity, **params ):
        super( ).__init__( **params )
        from .layouts import ( # pylint: disable=cyclic-import
            conversation_indicator_layout as layout,
        )
        row_gui = __.SimpleNamespace( )
        row = __.generate_component( row_gui, layout, 'column_indicator' )
        row_gui.rehtml_indicator = self
        row_gui.text_title.object = title
        self.gui__ = row_gui
        self.row__ = row
        self.identity__ = identity

    def _div_click( self, event ):
        # TODO: Suppress event propagation from buttons contained in this.
        #       Especially for 'delete' button as this results in a
        #       'bokeh.core.serialization.DeserializationError' from
        #       an unresolved reference after deletion.
        # Cannot run callback directly. Trigger via Event parameter.
        self.clicked = True

    @param.depends( 'mouse_hover__', watch = True )
    def _handle_mouse_hover__( self ):
        self.gui__.row_actions.visible = self.mouse_hover__



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
