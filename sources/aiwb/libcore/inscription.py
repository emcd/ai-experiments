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


class Modes( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Possible modes for logging output. '''

    Null = 'null' # suppress library logs
    Pass = 'pass' # pass library logs to root logger
    Rich = 'rich' # print rich library logs to stderr


@__.standard_dataclass
class Control:
    ''' Logging and debug printing behavior. '''

    mode: Modes = Modes.Null
    level: __.a.Nullable[ __.a.Literal[
        'debug', 'info', 'warn', 'error', 'critical' # noqa: F821
    ] ] = None

    # TODO? Support capture file and stream choice.


def prepare( auxdata: _state.Globals, control: Control ):
    ''' Prepares various scribes in a sensible manner. '''
    prepare_scribe_icecream( control = control )
    prepare_scribe_logging( control = control )


def prepare_scribe_icecream( control: Control ):
    ''' Prepares Icecream debug printing. '''
    from icecream import ic, install
    nomargs = dict( includeContext = True, prefix = 'DEBUG    ' )
    match control.mode:
        case Modes.Null:
            ic.configureOutput( **nomargs )
            ic.disable( )
        case Modes.Pass:
            ic.configureOutput( **nomargs )
        case Modes.Rich:
            from rich.pretty import pretty_repr
            ic.configureOutput( argToStringFunction = pretty_repr, **nomargs )
    install( )


def prepare_scribe_logging( control: Control ):
    ''' Prepares standard Python logging. '''
    # https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
    import logging
    if None is control.level:
        from os import environ
        envvar_name = (
            "{name}_LOG_LEVEL".format( name = __.package_name.upper( ) ) )
        level_name = environ.get( envvar_name, 'INFO' )
    else: level_name = control.level
    level = getattr( logging, level_name.upper( ) )
    scribe = __.acquire_scribe( __.package_name )
    scribe.propagate = False # prevent double-logging
    scribe.setLevel( level )
    match control.mode:
        case Modes.Null:
            scribe.addHandler( logging.NullHandler( ) )
        case Modes.Pass:
            scribe.propagate = True
        case Modes.Rich:
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
