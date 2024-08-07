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


''' Core entities for use with the workbench library. '''


from . import __


@__.dataclass( frozen = True, kw_only = True, slots = True )
class DistributionInformation:
    ''' Information about a package distribution. '''

    name: str
    location: __.Path
    editable: bool
    publisher: str

    @classmethod
    async def prepare(
        selfclass, package: str, publisher: str, contexts: __.Contexts
    ) -> __.a.Self:
        ''' Acquires information about our package distribution. '''
        from importlib.metadata import packages_distributions
        from aiofiles import open as open_
        # TODO: Python 3.12: importlib.resources
        from importlib_resources import files, as_file
        from tomli import loads
        # https://github.com/pypa/packaging-problems/issues/609
        name = packages_distributions( ).get( package )
        if None is name: # Development sources rather than distribution.
            editable = True # Implies no use of importlib.resources.
            location = (
                __.Path( __file__ ).parents[ 2 ].resolve( strict = True ) )
            async with open_( location / 'pyproject.toml' ) as file:
                pyproject = loads( await file.read( ) )
            name = pyproject[ 'project' ][ 'name' ]
        else:
            editable = False
            # Extract package contents to temporary directory, if necessary.
            location = contexts.enter_context( as_file( files( package ) ) )
        return selfclass(
            editable = editable,
            location = location,
            name = name,
            publisher = publisher )

    def provide_data_location( self, *appendages: str ) -> __.Path:
        ''' Provides location of distribution data. '''
        base = self.location / 'data'
        if appendages: return base.joinpath( *appendages )
        return base


class LocationSpecies( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Possible species for locations. '''

    Cache = 'cache'
    Data = 'data'
    State = 'state'


@__.dataclass( frozen = True, kw_only = True, slots = True )
class _NotificationBase:
    ''' Common base for notifications. '''

    summary: str


@__.dataclass( frozen = True, kw_only = True, slots = True )
class ErrorNotification( _NotificationBase ):
    ''' Summary and exception associated with error. '''

    error: Exception


@__.dataclass( frozen = True, kw_only = True, slots = True )
class NotificationsQueue:
    ''' Queue for notifications to be consumed by application. '''

    # TODO: Hide queue attribute.
    queue: __.SimpleQueue = __.dataclass_declare(
        default_factory = __.SimpleQueue )

    # TODO: enqueue_admonition

    def enqueue_error(
        self,
        error: Exception,
        summary: str,
        append_reason: bool = True,
        scribe: __.Scribe = None
    ) -> __.a.Self:
        ''' Enqueues error notification, optionally logging it. '''
        if append_reason: summary = f"{summary} Reason: {error}"
        if scribe: scribe.error( summary, exc_info = error )
        return self._enqueue(
            ErrorNotification( error = error, summary = summary ) )

    # TODO: enqueue_future

    @__.produce_context_manager
    def enqueue_on_error(
        self,
        summary: str,
        append_reason: bool = True,
        scribe: __.Scribe = None
    ):
        ''' Produces context manager which enqueues errors. '''
        try: yield
        except Exception as exc:
            self.enqueue_error(
                exc, summary, append_reason = append_reason, scribe = scribe )

    def _enqueue( self, notification: _NotificationBase ) -> __.a.Self:
        self.queue.put( notification )
        return self


class ScribeModes( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Possible modes for logging output. '''

    Null = __.enum.auto( )
    Rich = __.enum.auto( )


@__.dataclass( frozen = True, kw_only = True, slots = True )
class Globals:
    ''' Immutable global data. Required by many library functions. '''

    contexts: __.Contexts # TODO? Make accretive.
    configuration: __.AccretiveDictionary
    directories: __.PlatformDirs
    distribution: DistributionInformation
    notifications: NotificationsQueue

    @classmethod
    async def prepare(
        selfclass,
        contexts: __.Contexts,
        distribution: DistributionInformation = None,
    ) -> __.a.Self:
        ''' Acquires data to create DTO. '''
        if None is distribution:
            distribution = (
                await DistributionInformation.prepare(
                    package = __package__, publisher = 'emcd',
                    contexts = contexts ) )
        directories = __.PlatformDirs(
            distribution.name, distribution.publisher, ensure_exists = True )
        configuration = (
            await acquire_configuration( distribution, directories ) )
        notifications = NotificationsQueue( )
        return selfclass(
            configuration = configuration,
            contexts = contexts,
            directories = directories,
            distribution = distribution,
            notifications = notifications )

    def provide_cache_location( self, *appendages: str ) -> __.Path:
        ''' Provides cache location from configuration. '''
        return self.provide_location( LocationSpecies.Cache, *appendages )

    def provide_data_location( self, *appendages: str ) -> __.Path:
        ''' Provides data location from configuration. '''
        return self.provide_location( LocationSpecies.Data, *appendages )

    def provide_state_location( self, *appendages: str ) -> __.Path:
        ''' Provides state location from configuration. '''
        return self.provide_location( LocationSpecies.State, *appendages )

    def provide_location(
        self, species: LocationSpecies, *appendages: str
    ) -> __.Path:
        ''' Provides particular species of location from configuration. '''
        species = species.value
        base = getattr( self.directories, f"user_{species}_path" )
        if spec := self.configuration.get( 'locations', { } ).get( species ):
            args = {
                f"user_{species}": base,
                'user_home': __.Path.home( ),
                'application_name': self.distribution.name,
            }
            base = __.Path( spec.format( **args ) )
        if appendages: return base.joinpath( *appendages )
        return base


async def acquire_configuration(
    distribution: DistributionInformation, directories: __.PlatformDirs
) -> __.AccretiveDictionary:
    ''' Loads configuration as dictionary. '''
    from shutil import copyfile
    from aiofiles import open as open_
    from tomli import loads
    location = directories.user_config_path / 'general.toml'
    if not location.exists( ):
        copyfile(
            distribution.provide_data_location(
                'configuration', 'general.toml' ), location )
    # TODO: Raise error if location is not file.
    async with open_( location ) as file:
        configuration = loads( await( file.read( ) ) )
    includes = await _acquire_configuration_includes(
        distribution, directories, configuration.get( 'includes', ( ) ) )
    for include in includes: configuration.update( include )
    return __.AccretiveDictionary( configuration )


async def _acquire_configuration_includes(
    distribution: DistributionInformation,
    directories: __.PlatformDirs,
    specs: tuple[ str ]
) -> __.AbstractSequence[ dict ]:
    from itertools import chain
    from tomli import loads
    locations = tuple(
        __.Path( spec.format(
            user_configuration = directories.user_config_path,
            user_home = __.Path.home( ),
            application_name = distribution.name ) )
        for spec in specs )
    iterables = tuple(
        ( location.glob( '*.toml' ) if location.is_dir( ) else ( location, ) )
        for location in locations )
    includes = await __.read_files_async(
        *( file for file in chain.from_iterable( iterables ) ),
        deserializer = loads )
    return includes


def configure_icecream( mode: ScribeModes ):
    ''' Configures Icecream debug printing. '''
    from icecream import ic, install
    nomargs = dict( includeContext = True, prefix = 'DEBUG    ' )
    match mode:
        case ScribeModes.Null:
            ic.configureOutput( **nomargs )
            ic.disable( )
        case ScribeModes.Rich:
            from rich.pretty import pretty_repr
            ic.configureOutput( argToStringFunction = pretty_repr, **nomargs )
    install( )


def configure_logging( auxdata: Globals, mode: ScribeModes ):
    ''' Configures standard Python logging. '''
    # https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
    import logging
    from os import environ
    envvar_name = "{name}_LOG_LEVEL".format(
        name = auxdata.distribution.name.upper( ) )
    level = getattr( logging, environ.get( envvar_name, 'INFO' ) )
    scribe = __.acquire_scribe( __package__ )
    scribe.setLevel( level )
    match mode:
        case ScribeModes.Null:
            scribe.addHandler( logging.NullHandler( ) )
        case ScribeModes.Rich:
            from rich.console import Console
            from rich.logging import RichHandler
            handler = RichHandler(
                console = Console( stderr = True ),
                rich_tracebacks = True,
                show_time = False )
            scribe.addHandler( handler )
    scribe.debug( 'Logging initialized.' )


async def prepare(
    contexts: __.Contexts,
    environment: bool = False,
    scribe_mode: ScribeModes = ScribeModes.Null,
) -> Globals:
    ''' Prepares globals DTO for use with library functions.

        Also:
        * Configures logging for application or library mode.
        * Optionally, updates the process environment.

        Note that asynchronous preparation allows for applications to
        concurrently initialize other entities outside of the library, even
        though the library initialization, itself, is inherently sequential.
    '''
    auxdata = await Globals.prepare( contexts = contexts )
    if environment: await update_environment( auxdata )
    configure_icecream( mode = scribe_mode )
    configure_logging( auxdata, mode = scribe_mode )
    return auxdata


async def update_environment( auxdata: Globals ):
    ''' Updates process environment from dot files. '''
    locations = auxdata.configuration.get( 'locations', { } )
    location = __.Path( ) / '.env'
    if not location.exists( ) and auxdata.distribution.editable:
        location = __.Path( auxdata.distribution.location ) / '.env'
    if not location.exists( ) and 'environment' in locations:
        location = __.Path( locations[ 'environment' ].format(
            user_configuration = auxdata.directories.user_config_path,
            user_home = __.Path.home( ) ) )
    if not location.exists( ): return
    files = (
        location.glob( '*.env' ) if location.is_dir( ) else ( location, ) )
    await __.read_files_async(
        *( file for file in files ), deserializer = _inject_dotenv_data )


def _inject_dotenv_data( data: str ) -> dict:
    from io import StringIO
    from dotenv import load_dotenv
    return load_dotenv( stream = StringIO( data ) )
