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


''' Customization of Holoviz Panel GUI components. '''


from . import __


def register_transformers( auxdata ):
    ''' Registers component transformers. '''
    return __.AccretiveDictionary( {
        name: transformer for name, transformer
        in ( ( 'select-font-family', _transform_component_font_family ), ) } )


def _transform_component_font_family( auxdata, class_, arguments ):
    from panel.layout import Column, Row
    from panel.pane import Markdown
    from panel.reactive import ReactiveHTML
    styles = arguments.get( 'styles', { } )
    if 'font-family' in styles: pass # Respect explicit configuration.
    elif issubclass( class_, ( Column, Row ) ): pass
    # TODO: Analyze auxiliary attributes in component arguments.
    #       If 'use-special-fonts' absent, then apply sans serif fonts.
    elif not issubclass( class_, ( Markdown, ReactiveHTML ) ):
        styles[ 'font-family' ] = 'var(--sans-serif-fonts)'
        arguments[ 'styles' ] = styles
    return class_, arguments
