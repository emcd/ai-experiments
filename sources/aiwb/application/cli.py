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


''' CLI for configuring, inspecting, and testing application. '''


from . import __
from . import state as _state


class EnablementTristate( __.enum.Enum ): # TODO: Python 3.11: StrEnum
    ''' Disable, enable, or retain the natural state? '''

    Disable = 'disable'
    Retain = 'retain'
    Enable = 'enable'

    def __bool__( self ) -> bool:
        if self.Disable is self: return False
        if self.Enable is self: return True
        # TODO: Raise proper error.
        raise RuntimeError

    def is_retain( self ) -> bool:
        ''' Does enum indicate a retain state? '''
        return self.Retain is self


class ConfigurationModifiers( __.immut.DataclassObject ):
    ''' Configuration injectors/modifiers. '''

    maintenance: __.typx.Annotated[
        __.typx.Optional[ bool ],
        __.tyro.conf.arg( name = 'maintenance-mode', prefix_name = False ),
    ] = None
    all_promptstores: __.typx.Annotated[
        EnablementTristate,
        __.tyro.conf.arg( prefix_name = False ),
    ] = EnablementTristate.Retain
    all_providers: __.typx.Annotated[
        EnablementTristate,
        __.tyro.conf.arg( prefix_name = False ),
    ] = EnablementTristate.Retain
    all_vectorizers: __.typx.Annotated[
        EnablementTristate,
        __.tyro.conf.arg( prefix_name = False ),
    ] = EnablementTristate.Retain
    all_vectorstores: __.typx.Annotated[
        EnablementTristate,
        __.tyro.conf.arg( prefix_name = False ),
    ] = EnablementTristate.Retain
    disable_promptstores: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg(
            name = 'disable-promptstore', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    enable_promptstores: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg(
            name = 'enable-promptstore', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    disable_providers: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg(
            name = 'disable-provider', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    enable_providers: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg(
            name = 'enable-provider', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    disable_vectorizers: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg(
            name = 'disable-vectorizer', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    enable_vectorizers: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg(
            name = 'enable-vectorizer', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    disable_vectorstores: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg(
            name = 'disable-vectorstore', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    enable_vectorstores: __.typx.Annotated[
        __.cabc.Sequence[ str ],
        __.tyro.conf.arg(
            name = 'enable-vectorstore', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )

    def as_edits( self ) -> __.appcore.dictedits.Edits:
        ''' Returns modifications as sequence of configuration edits. '''
        edits = [ ]
        if None is not self.maintenance:
            edits.append( __.appcore.dictedits.SimpleEdit(
                address = ( 'maintenance-mode', ),
                value = self.maintenance ) )
        for collection_name in (
            'promptstores', 'providers', 'vectorizers', 'vectorstores',
        ):
            collection = getattr( self, f"all_{collection_name}" )
            if not collection.is_retain( ):
                edits.append( __.appcore.dictedits.ElementsEntryEdit(
                    address = ( collection_name, ),
                    editee = ( 'enable', bool( collection ) ) ) )
            disables = frozenset(
                getattr( self, f"enable_{collection_name}" ) )
            enables = frozenset(
                getattr( self, f"enable_{collection_name}" ) )
            # TODO: Raise error if intersection of sets is not empty.
            edits.extend(
                __.appcore.dictedits.ElementsEntryEdit(
                    address = ( collection_name, ),
                    identifier = ( 'name', disable ),
                    editee = ( 'enable', False ) )
                for disable in disables )
            edits.extend(
                __.appcore.dictedits.ElementsEntryEdit(
                    address = ( collection_name, ),
                    identifier = ( 'name', enable ),
                    editee = ( 'enable', True ) )
                for enable in enables )
        return tuple( edits )


class Cli( __.CoreCli ):
    ''' Utility for configuration, inspection, and tests of application. '''

    # TODO: Add commands for prompts, providers, and vectorstores.
    configuration: ConfigurationModifiers

    async def __call__( self ):
        ''' Invokes command after application preparation. '''
        nomargs = self.prepare_invocation_args( )
        from .preparation import prepare
        async with __.ctxl.AsyncExitStack( ) as exits:
            auxdata = await prepare( exits = exits, **nomargs )
            await self.command( auxdata = auxdata, display = self.display )

    def prepare_invocation_args(
        self,
    ) -> __.cabc.Mapping[ str, __.typx.Any ]:
        args = __.CoreCli.prepare_invocation_args( self )
        args[ 'configedits' ] = self.configuration.as_edits( )
        return args


class ExecuteServerCommand( metaclass = __.immut.ProtocolClass ):
    ''' Runs API server until signal. '''

    @__.abc.abstractmethod
    async def __call__(
        self,
        auxdata: _state.Globals,
        display: __.CliConsoleDisplay,
    ): raise NotImplementedError

    async def execute_until_signal(
        self,
        auxdata: _state.Globals,
        display: __.CliConsoleDisplay,
        scribe: __.Scribe,
    ):
        from asyncio import Future, get_running_loop
        from signal import SIGINT, SIGTERM
        signal_future = Future( )

        def react_to_signal( signum ):
            scribe.info( f"Received signal {signum.name} ({signum.value})." )
            signal_future.set_result( signum )

        loop = get_running_loop( )
        for signum in ( SIGINT, SIGTERM, ):
            loop.add_signal_handler( signum, react_to_signal, signum )
        await signal_future


def execute_cli( ):
    config = (
        #__.tyro.conf.OmitSubcommandPrefixes,
        __.tyro.conf.EnumChoicesFromValues,
    )
    default = Cli(
        configuration = ConfigurationModifiers( ),
        display = __.CliConsoleDisplay( ),
        inscription = (
            __.CliInscriptionControl(
                mode = __.appcore.ScribePresentations.Rich ) ),
        command = __.CoreCliInspectCommand( ) )
    __.asyncio.run( __.tyro.cli( Cli, config = config, default = default )( ) )
