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
from . import application as _application


# TODO: Types for commands, then union of types for program.
#       Will give back instance of type to pass to common dispatcher.
#       Can place 'execute' method on command types.
#       More composable and reusable.

# TODO: Standard set of output options: pretty, json, toml


def configuration(
    application: _application.Information,
):
    from asyncio import run
    from pprint import pprint
    from .preparation import prepare
    with __.Exits( ) as exits:
        auxdata = run( prepare(
            application = application,
            environment = True,
            exits = exits ) )
        pprint( dict( auxdata.configuration ) )


def environment(
    application: _application.Information,
):
    from asyncio import run
    from os import environ
    from .preparation import prepare
    with __.Exits( ) as exits:
        run( prepare(
            application = application,
            environment = True,
            exits = exits ) )
        prefix = "{}_".format( application.name.upper( ) )
        for name, value in environ.items( ):
            if name.startswith( prefix ): print( f"{name} = {value}" )


def main( ):
    ''' Prepares and executes CLI. '''
    #__.tyro.cli( configuration )
    __.tyro.extras.subcommand_cli_from_dict( {
        'configuration': configuration,
        'environment': environment,
    } )


if '__main__' == __name__: main( )
