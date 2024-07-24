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


def prepare( auxdata ):
    ''' Prepares support for GUI components. '''
    _prepare_icons_cache( auxdata )
    _register_transformers( auxdata )


_icons_cache = __.AccretiveDictionary( )
# TODO? Execute with async gather.
def _prepare_icons_cache( auxdata ):
    directory = auxdata.distribution.location / 'data/icons'
    for file in directory.glob( '*.svg' ):
        with file.open( ) as stream:
            _icons_cache[ file.stem ] = stream.read( )


def _register_transformers( auxdata ):
    auxdata.gui.transformers = __.AccretiveDictionary( {
        name: transformer for name, transformer
        in (
            ( 'use-local-icon', _use_local_icon ),
            #( 'transform-font', _transform_font ),
        )
    } )


def _transform_font( auxdata, class_, arguments ):
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


def _use_local_icon( auxdata, class_, arguments ):
    icon = arguments.get( 'icon' )
    if None is icon: pass
    elif icon.startswith( '<svg' ) and icon.endswith( '</svg>' ): pass
    elif icon in _icons_cache: arguments[ 'icon' ] = _icons_cache[ icon ]
    return class_, arguments
