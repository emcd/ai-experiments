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
    Pretty =    'pretty'
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
    display: DisplayOptions
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
        from sys import stdout, stderr
        from .preparation import prepare
        # TODO: Use argument to choose output stream.
        with __.Exits( ) as exits:
            auxdata = await prepare(
                application = self.application,
                environment = True,
                exits = exits,
                scribe_mode = self.scribe_mode )
            result = await self.command( auxdata = auxdata )
        match self.display.target:
            case DisplayTargets.Stdout: stream = stdout
            case DisplayTargets.Stderr: stream = stderr
        match self.display.format:
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
class DisplayOptions:
    ''' Options for the display of command results. '''

    format: __.a.Annotation[
        DisplayFormats,
        __.tyro.conf.SelectFromEnumValues,
    ] = DisplayFormats.Rich
    target: __.a.Annotation[
        DisplayTargets,
        __.tyro.conf.SelectFromEnumValues,
    ] = DisplayTargets.Stderr


@__.standard_dataclass
class InspectCommand:
    ''' Displays some facet of the application. '''

    inspectee: __.a.Annotation[
        __.tyro.conf.Positional[ Inspectees ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = Inspectees.Configuration

    async def __call__( self, auxdata: _state.Globals ):
        match self.inspectee:
            case Inspectees.Configuration:
                return dict( auxdata.configuration )
            case Inspectees.Environment:
                from os import environ
                prefix = "{}_".format( auxdata.application.name.upper( ) )
                return {
                    name: value for name, value in environ.items( )
                    if name.startswith( prefix ) }


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

    async def __call__( self, auxdata: _state.Globals ):
        return await self.command( auxdata = auxdata )


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

    async def __call__( self, auxdata: _state.Globals ):
        accessor = (
            await _locations.adapter_from_url( self.url )
            .as_specific( species = _locations.LocationSpecies.Directory ) )
        dirents = await accessor.survey_entries(
            filters = self.filters, recurse = self.recurse )
        # TODO: Implement.
        return dirents


@__.standard_dataclass
class LocationAcquireContentCommand:
    ''' Reads content from file at given URL. '''

    # TODO: Options
    url: _locations.Url

    async def __call__( self, auxdata: _state.Globals ):
        # TODO: Implement.
        pass


def execute_cli( ):
    from asyncio import run
    default = Cli(
        application = _application.Information( ),
        scribe_mode = _inscription.ScribeModes.Rich,
        display = DisplayOptions( ),
        command = InspectCommand( ),
    )
    run( __.tyro.cli( Cli, default = default )( ) )
