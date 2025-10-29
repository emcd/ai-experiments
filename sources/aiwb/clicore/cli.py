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


from . import __
from . import preparation as _preparation
from . import state as _state


class DisplayFormats( __.enum.Enum ): # TODO: Python 3.11: StrEnum
    ''' Format in which to display structured output. '''

    Json =      'json'
    Rich =      'rich'
    Toml =      'toml'


class DisplayStreams( __.enum.Enum ): # TODO: Python 3.11: StrEnum
    ''' Stream upon which to place output. '''

    Stderr =    'stderr'
    Stdout =    'stdout'


class ConsoleDisplay( __.immut.DataclassObject ):
    ''' Display of command results. '''

    silence: __.typx.Annotated[
        bool,
        __.tyro.conf.arg(
            aliases = ( '--quiet', '--silent', ), prefix_name = False ),
    ] = False
    colorize: __.typx.Annotated[
        __.typx.Optional[ bool ],
        __.tyro.conf.arg(
            name = 'console-colorization',
            aliases = ( '--colorize-console', ),
            prefix_name = False ),
    ] = None
    file: __.typx.Annotated[
        __.typx.Optional[ __.Path ],
        __.tyro.conf.arg(
            name = 'console-capture-file', prefix_name = False ),
    ] = None
    format: __.typx.Annotated[
        DisplayFormats,
        __.tyro.conf.arg( name = 'console-format', prefix_name = False ),
    ] = DisplayFormats.Rich
    stream: __.typx.Annotated[
        DisplayStreams,
        __.tyro.conf.arg( name = 'console-stream', prefix_name = False ),
    ] = DisplayStreams.Stderr

    def provide_format_serializer(
        self,
    ) -> __.typx.Callable[ [ __.typx.Any ], str ]:
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

    async def provide_printer(
        self,
    ) -> __.typx.Callable[ [ __.typx.Any ], None ]:
        ''' Providers printer for display format and stream.

            If silence, then returns null printer.
        '''
        # TODO: async printer
        # TODO: Multiplex to capture file, if desired.
        if self.silence: return lambda obj: None
        stream = await self.provide_stream( )
        serializer = self.provide_format_serializer( )
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

    async def provide_stream( self ) -> __.typx.TextIO:
        ''' Provides output stream for display. '''
        # TODO: async context manager for async file streams
        # TODO: return async stream - need async printers
        from sys import stdout, stderr
        match self.stream:
            case DisplayStreams.Stdout: return stdout
            case DisplayStreams.Stderr: return stderr

    async def render( self, obj: __.typx.Any ):
        ''' Renders object according to options. '''
        ( await self.provide_printer( ) )( obj )


class CliInscriptionControl( __.immut.DataclassObject ):
    ''' Logging configuration. '''

    mode: __.appcore.ScribePresentations = (
        __.appcore.ScribePresentations.Plain )
    level: __.typx.Literal[
        'debug', 'info', 'warn', 'error', 'critical'  # noqa: F821
    ] = 'info'
    target: str = 'stream://stderr'

    def as_control( self ) -> __.appcore.InscriptionControl:
        ''' Produces compatible inscription control. '''
        target_ = __.urlparse( self.target )
        target = __.sys.stderr
        match target_.scheme:
            case '' | 'file':
                target = (
                    __.appcore.InscriptionTargetDescriptor(
                        location = target_.path ) )
            case 'stream':
                match target_.netloc:
                    case 'stderr': target = __.sys.stderr
                    case 'stdout': target = __.sys.stdout
        return __.appcore.InscriptionControl(
            mode = self.mode, level = self.level, target = target )


class Inspectees( __.enum.Enum ): # TODO: Python 3.11: StrEnum
    ''' Facet of the application to inspect. '''

    Configuration =     'configuration'
    ''' Displays application configuration. '''
    # TODO: Directories.
    Environment =       'environment'
    ''' Displays application-relevant process environment. '''


class InspectCommand( metaclass = __.accret.Dataclass ):
    ''' Displays some facet of the application. '''

    inspectee: __.typx.Annotated[
        __.tyro.conf.Positional[ Inspectees ],
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


class LocationSurveyDirectoryCommand( metaclass = __.accret.Dataclass ):
    ''' Lists directory given by URL or filesystem path. '''

    # TODO: Cache options.

    filters: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg( prefix_name = False ),
    ] = ( '@gitignore', '+vcs' )
    recurse: __.typx.Annotated[
        bool,
        __.tyro.conf.arg( prefix_name = False ),
    ] = False
    url: __.typx.Annotated[
        __.tyro.conf.Positional[ str ],
        __.tyro.conf.arg( prefix_name = False ),
    ]

    async def __call__(
        self,
        auxdata: _state.Globals,
        display: ConsoleDisplay,
    ):
        accessor = __.locations.directory_adapter_from_url( self.url )
        dirents = await accessor.survey_entries(
            filters = self.filters, recurse = self.recurse )
        # TODO: Implement.
        await display.render( dirents )


class LocationAcquireContentCommand( metaclass = __.accret.Dataclass ):
    ''' Reads content from file at given URL or filesystem path. '''

    # TODO: Options
    url: __.locations.Url

    async def __call__(
        self,
        auxdata: _state.Globals,
        display: ConsoleDisplay,
    ):
        # TODO: Implement.
        pass


class LocationCommand( metaclass = __.accret.Dataclass ):
    ''' Accesses a location via URL or local filesystem path. '''

    command: __.typx.Union[
        __.typx.Annotated[
            LocationSurveyDirectoryCommand,
            __.tyro.conf.subcommand( 'list-folder', prefix_name = False ),
        ],
        __.typx.Annotated[
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


class Cli( __.immut.DataclassObject ):
    ''' Utility for inspection and tests of library core. '''

    configfile: __.typx.Optional[ str ] = None
    display: ConsoleDisplay
    inscription: CliInscriptionControl
    command: __.typx.Union[
        __.typx.Annotated[
            InspectCommand,
            __.tyro.conf.subcommand( 'inspect', prefix_name = False ),
        ],
        __.typx.Annotated[
            LocationCommand,
            __.tyro.conf.subcommand( 'location', prefix_name = False ),
        ],
    ]

    async def __call__( self ):
        ''' Invokes command after library preparation. '''
        nomargs = self.prepare_invocation_args( )
        async with __.ctxl.AsyncExitStack( ) as exits:
            auxdata = await _preparation.prepare( exits = exits, **nomargs )
            await self.command( auxdata = auxdata, display = self.display )

    def prepare_invocation_args(
        self,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        inscription = self.inscription.as_control( )
        args: __.NominativeArguments = dict(
            environment = True, inscription = inscription )
        if self.configfile: args[ 'configfile' ] = self.configfile
        return args


def execute_cli( ):
    config = (
        #__.tyro.conf.OmitSubcommandPrefixes,
        __.tyro.conf.EnumChoicesFromValues,
    )
    inscription = CliInscriptionControl(
        mode = __.appcore.ScribePresentations.Rich )
    default = Cli(
        display = ConsoleDisplay( ),
        inscription = inscription,
        command = InspectCommand( ) )
    __.asyncio.run( __.tyro.cli( Cli, config = config, default = default )( ) )
