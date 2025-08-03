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


''' Standard ensemble for I/O. '''


from . import __
from .deduplicators import IoContentDeduplicator, SurveyDirectoryDeduplicator

from .argschemata import (
    acquire_content_argschema,
    survey_directory_argschema,
    update_content_argschema,
    update_content_partial_argschema,
)
from .differences import write_pieces
from .operations import list_folder, read, write_file


_name = __package__.rsplit( '.', maxsplit = 1 )[ -1 ]


async def prepare(
    auxdata: __.Globals,
    descriptor: __.cabc.Mapping[ str, __.typx.Any ],
) -> 'Ensemble':
    ''' Installs dependencies and returns ensemble. '''
    # TODO: Install dependencies: github, etc....
    return Ensemble( name = _name )


__.preparers[ _name ] = prepare


class Ensemble( __.Ensemble ):

    async def prepare_invokers(
        self, auxdata: __.Globals
    ) -> __.cabc.Mapping[ str, __.Invoker ]:
        registry = [
            (   invocable,
                argschema,
                IoContentDeduplicator
                if invocable.__name__
                in IoContentDeduplicator.provide_invocable_names( )
                else SurveyDirectoryDeduplicator
                if invocable.__name__
                in SurveyDirectoryDeduplicator.provide_invocable_names( )
                else None )
            for invocable, argschema in _invocables ]
        return __.types.MappingProxyType( {
            invoker.name: invoker for invoker in (
                __.Invoker.from_invocable(
                    ensemble = self,
                    invocable = invocable,
                    argschema = argschema,
                    deduplicator_class = deduplicator_class )
                for invocable, argschema, deduplicator_class in registry
            )
        } )

_invocables = (
    ( read, acquire_content_argschema ),
    ( list_folder, survey_directory_argschema ),
    ( write_file, update_content_argschema ),
    ( write_pieces, update_content_partial_argschema ),
)


