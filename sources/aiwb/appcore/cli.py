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


from __future__ import annotations

from ..libcore.cli import (
    # Direct imports as public symbols for intentional re-export.
    ConsoleDisplay,
    InspectCommand,
)
from . import __


@__.standard_dataclass
class Cli( __.Cli ):
    ''' Utility for configuration, inspection, and tests of application. '''

    configuration: ConfigurationModifiers

    async def __call__( self ):
        ''' Invokes command after application preparation. '''
        from .preparation import prepare
        with __.Exits( ) as exits:
            auxdata = await prepare(
                application = self.application,
                configedits = self.configuration.as_edits( ),
                exits = exits,
                inscription = self.inscription )
            await self.command( auxdata = auxdata, display = self.display )

    # TODO: Add commands for prompts, providers, and vectorstores.


class EnablementTristate( __.Enum ): # TODO: Python 3.11: StrEnum
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


@__.standard_dataclass
class ConfigurationModifiers:
    ''' Configuration injectors/modifiers. '''

    maintenance: __.a.Annotation[
        EnablementTristate,
        __.tyro.conf.arg( name = 'maintenance-mode', prefix_name = False ),
    ] = EnablementTristate.Retain
    all_promptstores: __.a.Annotation[
        EnablementTristate,
        __.tyro.conf.arg( prefix_name = False ),
    ] = EnablementTristate.Retain
    all_providers: __.a.Annotation[
        EnablementTristate,
        __.tyro.conf.arg( prefix_name = False ),
    ] = EnablementTristate.Retain
    all_vectorizers: __.a.Annotation[
        EnablementTristate,
        __.tyro.conf.arg( prefix_name = False ),
    ] = EnablementTristate.Retain
    all_vectorstores: __.a.Annotation[
        EnablementTristate,
        __.tyro.conf.arg( prefix_name = False ),
    ] = EnablementTristate.Retain
    disable_promptstores: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg(
            name = 'disable-promptstore', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    enable_promptstores: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg(
            name = 'enable-promptstore', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    disable_providers: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg(
            name = 'disable-provider', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    enable_providers: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg(
            name = 'enable-provider', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    disable_vectorizers: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg(
            name = 'disable-vectorizer', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    enable_vectorizers: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg(
            name = 'enable-vectorizer', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    disable_vectorstores: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg(
            name = 'disable-vectorstore', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )
    enable_vectorstores: __.a.Annotation[
        __.AbstractSequence[ str ],
        __.tyro.conf.arg(
            name = 'enable-vectorstore', prefix_name = False ),
        __.tyro.conf.UseAppendAction,
    ] = ( )

    def as_edits( self ) -> __.AbstractSequence[ __.ConfigurationEdit ]:
        ''' Returns modifications as sequence of configuration edits. '''
        edits = [ ]
        if not self.maintenance.is_retain( ):
            edits.append( __.SimpleConfigurationEdit(
                address = ( 'maintenance-mode', ),
                value = bool( self.maintenance ) ) )
        for collection_name in (
            'promptstores', 'providers', 'vectorizers', 'vectorstores',
        ):
            collection = getattr( self, f"all_{collection_name}" )
            if not collection.is_retain( ):
                edits.append( __.ArrayMembersEntryConfigurationEdit(
                    address = ( collection_name, ),
                    editee = ( 'enable', bool( collection ) ) ) )
            disables = frozenset(
                getattr( self, f"enable_{collection_name}" ) )
            enables = frozenset(
                getattr( self, f"enable_{collection_name}" ) )
            # TODO: Raise error if intersection of sets is not empty.
            for disable in disables:
                edits.append( __.ArrayMembersEntryConfigurationEdit(
                    address = ( collection_name, ),
                    identifier = ( 'name', disable ),
                    editee = ( 'enable', False ) ) )
            for enable in enables:
                edits.append( __.ArrayMembersEntryConfigurationEdit(
                    address = ( collection_name, ),
                    identifier = ( 'name', enable ),
                    editee = ( 'enable', True ) ) )
        return tuple( edits )


def execute_cli( ):
    from asyncio import run
    config = (
        #__.tyro.conf.OmitSubcommandPrefixes,
        __.tyro.conf.SelectFromEnumValues,
    )
    default = Cli(
        application = __.ApplicationInformation( ),
        configuration = ConfigurationModifiers( ),
        display = ConsoleDisplay( ),
        inscription = __.InscriptionControl( mode = __.InscriptionModes.Rich ),
        command = InspectCommand( ),
    )
    run( __.tyro.cli( Cli, config = config, default = default )( ) )
