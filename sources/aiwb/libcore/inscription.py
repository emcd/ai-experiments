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


''' Scribes for debugging and logging. '''


from . import __
from . import state as _state


class ScribeModes( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Possible modes for logging output. '''

    Null = __.produce_enumeration_value( ) # suppress library logs
    Pass = __.produce_enumeration_value( ) # pass library logs to root logger
    Rich = __.produce_enumeration_value( ) # print rich library logs to stderr


def prepare( auxdata: _state.Globals, mode: ScribeModes ):
    ''' Prepares various scribes in a sensible manner. '''
    prepare_scribe_icecream( mode = mode )
    prepare_scribe_logging( auxdata, mode = mode )


def prepare_scribe_icecream( mode: ScribeModes ):
    ''' Prepares Icecream debug printing. '''
    from icecream import ic, install
    nomargs = dict( includeContext = True, prefix = 'DEBUG    ' )
    match mode:
        case ScribeModes.Null:
            ic.configureOutput( **nomargs )
            ic.disable( )
        case ScribeModes.Pass:
            ic.configureOutput( **nomargs )
        case ScribeModes.Rich:
            from rich.pretty import pretty_repr
            ic.configureOutput( argToStringFunction = pretty_repr, **nomargs )
    install( )


def prepare_scribe_logging( auxdata: _state.Globals, mode: ScribeModes ):
    ''' Prepares standard Python logging. '''
    # https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
    import logging
    from os import environ
    envvar_name = "{name}_LOG_LEVEL".format( name = __.package_name.upper( ) )
    level = getattr( logging, environ.get( envvar_name, 'INFO' ).upper( ) )
    scribe = __.acquire_scribe( __.package_name )
    scribe.propagate = False # prevent double-logging
    scribe.setLevel( level )
    match mode:
        case ScribeModes.Null:
            scribe.addHandler( logging.NullHandler( ) )
        case ScribeModes.Pass:
            scribe.propagate = True
        case ScribeModes.Rich:
            from rich.console import Console
            from rich.logging import RichHandler
            formatter = logging.Formatter( '%(name)s: %(message)s' )
            handler = RichHandler(
                console = Console( stderr = True ),
                rich_tracebacks = True,
                show_time = False )
            handler.setFormatter( formatter )
            scribe.addHandler( handler )
    scribe.debug( 'Logging initialized.' )
