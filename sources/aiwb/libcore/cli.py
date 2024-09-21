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


''' Utility CLI for inspecting and testing library core. '''


from __future__ import annotations

from . import __
from . import application as _application
from . import inscription as _inscription
from . import state as _state


class DisplayFormats( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Format in which to display structured output. '''

    Json =      'json'
    Pretty =    'pretty'
    Rich =      'rich'
    Toml =      'toml'


# TODO: Python 3.12: type statement for aliases
#DisplayFormats: __.a.TypeAlias = __.a.Literal[
#    'json', 'pretty', 'rich', 'toml',
#]


@__.standard_dataclass
class Cli:
    ''' Utility for inspection and tests of library core. '''

    application: _application.Information
    scribe_mode: _inscription.ScribeModes = _inscription.ScribeModes.Rich
    display_format: DisplayFormats = DisplayFormats.Rich
    command: __.a.Union[
        __.a.Annotation[
            ConfigurationCommand,
            __.tyro.conf.subcommand( 'configuration', prefix_name = False ),
        ],
        __.a.Annotation[
            EnvironmentCommand,
            __.tyro.conf.subcommand( 'environment', prefix_name = False ),
        ],
    ]

    def __call__( self ):
        ''' Invokes command after library preparation. '''
        from asyncio import run
        from sys import stdout
        from .preparation import prepare
        # TODO: Use argument to choose output stream.
        with __.Exits( ) as exits:
            auxdata = run( prepare(
                application = self.application,
                environment = True,
                exits = exits,
                scribe_mode = self.scribe_mode ) )
            result = self.command( auxdata = auxdata )
        stream = stdout
        match self.display_format:
            case DisplayFormats.Json:
                from json import dump
                dump( result, fp = stream, indent = 2 )
                print( file = stream ) # ensure final newline
            case DisplayFormats.Pretty:
                from pprint import pformat
                print( pformat( result ), file = stream )
            case DisplayFormats.Rich:
                from rich.console import Console
                from rich.pretty import pprint
                pprint( result, console = Console( file = stream ) )
            case DisplayFormats.Toml:
                from tomli_w import dumps
                print( dumps( result ).strip( ), file = stream )


@__.standard_dataclass
class ConfigurationCommand:
    ''' Displays application configuration. '''

    def __call__( self, auxdata: _state.Globals ):
        return dict( auxdata.configuration )


@__.standard_dataclass
class EnvironmentCommand:
    ''' Displays application-relevant process environment. '''

    def __call__( self, auxdata: _state.Globals ):
        from os import environ
        prefix = "{}_".format( auxdata.application.name.upper( ) )
        return {
            name: value for name, value in environ.items( )
            if name.startswith( prefix ) }
