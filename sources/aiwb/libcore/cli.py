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
from . import locations as _locations
from . import state as _state


class DisplayFormats( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Format in which to display structured output. '''

    Json =      'json'
    Rich =      'rich'
    Toml =      'toml'


class DisplayTargets( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Target upon which to place output. '''

    # TODO? File
    Stderr =    'stderr'
    Stdout =    'stdout'


class Inspectees( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Facet of application to inspect. '''

    Configuration =     'configuration'
    ''' Displays application configuration. '''
    # TODO: Directories.
    Environment =       'environment'
    ''' Displays application-relevant process environment. '''


@__.standard_dataclass
class Cli:
    ''' Utility for inspection and tests of library core. '''

    application: _application.Information
    display: ConsoleDisplay
    scribe_mode: __.a.Annotation[
        _inscription.ScribeModes,
        __.tyro.conf.SelectFromEnumValues,
    ] = _inscription.ScribeModes.Rich
    command: __.a.Union[
        __.a.Annotation[
            InspectCommand,
            __.tyro.conf.subcommand( 'inspect', prefix_name = False ),
        ],
        __.a.Annotation[
            LocationCommand,
            __.tyro.conf.subcommand( 'location', prefix_name = False ),
        ],
    ]

    async def __call__( self ):
        ''' Invokes command after library preparation. '''
        from .preparation import prepare
        # TODO: Use argument to choose output stream.
        with __.Exits( ) as exits:
            auxdata = await prepare(
                application = self.application,
                environment = True,
                exits = exits,
                scribe_mode = self.scribe_mode )
            await self.command( auxdata = auxdata, display = self.display )


@__.standard_dataclass
class ConsoleDisplay:
    ''' Options and utilities for the display of command results. '''

    colorize: __.a.Nullable[ bool ] = None
    format: __.a.Annotation[
        DisplayFormats,
        __.tyro.conf.SelectFromEnumValues,
    ] = DisplayFormats.Rich
    target: __.a.Annotation[
        DisplayTargets,
        __.tyro.conf.SelectFromEnumValues,
    ] = DisplayTargets.Stderr

    async def provide_printer( self ) -> __.a.Any: # TODO: Callable
        ''' Providers printer for display format and target. '''
        # TODO: async printer
        stream = await self.stream_from_target( )
        serializer = self.serializer_from_format( )
        match self.format:
            case DisplayFormats.Rich:
                from rich.console import Console
                from rich.pretty import pprint
                if None is not self.colorize: no_color = not self.colorize
                else: no_color = self.colorize
                console = Console( file = stream, no_color = no_color )
                return lambda obj: pprint( obj, console = console )
            # TODO: Use pygments to colorize other formats.
            #       Determine colorization with isatty if colorize is None.
            case _:
                return lambda obj: print( serializer( obj ), file = stream )

    async def render( self, obj: __.a.Any ):
        ''' Renders object according to options. '''
        ( await self.provide_printer( ) )( obj )

    def serializer_from_format( self ) -> __.a.Any: # TODO: Callable
        ''' Provides serializer function for display format. '''
        match self.format:
            case DisplayFormats.Json:
                from json import dumps
                return lambda obj: dumps( obj, indent = 2 ) + '\n'
            case DisplayFormats.Rich:
                return lambda obj: obj
            case DisplayFormats.Toml:
                from tomli_w import dumps
                return lambda obj: dumps( obj ).strip( )

    async def stream_from_target( self ) -> __.a.Any: # TODO: io.writer
        ''' Provides stream for display target. '''
        # TODO: async context manager for async file streams
        # TODO: return async stream - need async printers
        from sys import stdout, stderr
        match self.target:
            case DisplayTargets.Stdout: return stdout
            case DisplayTargets.Stderr: return stderr
            # TODO: File?


@__.standard_dataclass
class InspectCommand:
    ''' Displays some facet of the application. '''

    inspectee: __.a.Annotation[
        __.tyro.conf.Positional[ Inspectees ],
        __.tyro.conf.SelectFromEnumValues,
        __.tyro.conf.arg( prefix_name = False ),
    ] = Inspectees.Configuration

    async def __call__(
        self,
        auxdata: _state.Globals,
        display: ConsoleDisplay,
    ):
        match self.inspectee:
            case Inspectees.Configuration:
                await display.render( dict( auxdata.configuration ) )
            case Inspectees.Environment:
                from os import environ
                prefix = "{}_".format( auxdata.application.name.upper( ) )
                await display.render( {
                    name: value for name, value in environ.items( )
                    if name.startswith( prefix ) } )


@__.standard_dataclass
class LocationCommand:
    ''' Accesses a location via URL or local filesystem path. '''

    command: __.a.Union[
        __.a.Annotation[
            LocationSurveyDirectoryCommand,
            __.tyro.conf.subcommand( 'list-folder', prefix_name = False ),
        ],
        __.a.Annotation[
            LocationAcquireContentCommand,
            __.tyro.conf.subcommand( 'read', prefix_name = False ),
        ],
        # TODO: LocationUpdateContentCommand (write)
    ]

    async def __call__(
        self,
        auxdata: _state.Globals,
        display: ConsoleDisplay,
    ): await self.command( auxdata = auxdata, display = display )


@__.standard_dataclass
class LocationSurveyDirectoryCommand:
    ''' Lists directory given by URL. '''

    # TODO: Cache options.
    filters: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = ( '@gitignore', '+vcs' )
    recurse: __.a.Annotation[
        bool,
        __.tyro.conf.arg( prefix_name = False ),
    ] = False
    url: __.a.Annotation[
        __.tyro.conf.Positional[ str ],
        __.tyro.conf.arg( prefix_name = False ),
    ]

    async def __call__(
        self,
        auxdata: _state.Globals,
        display: ConsoleDisplay,
    ):
        accessor = (
            await _locations.adapter_from_url( self.url )
            .as_specific( species = _locations.LocationSpecies.Directory ) )
        dirents = await accessor.survey_entries(
            filters = self.filters, recurse = self.recurse )
        # TODO: Implement.
        await display.render( dirents )


@__.standard_dataclass
class LocationAcquireContentCommand:
    ''' Reads content from file at given URL. '''

    # TODO: Options
    url: _locations.Url

    async def __call__(
        self,
        auxdata: _state.Globals,
        display: ConsoleDisplay,
    ):
        # TODO: Implement.
        pass


def execute_cli( ):
    from asyncio import run
    default = Cli(
        application = _application.Information( ),
        scribe_mode = _inscription.ScribeModes.Rich,
        display = ConsoleDisplay( ),
        command = InspectCommand( ),
    )
    run( __.tyro.cli( Cli, default = default )( ) )
