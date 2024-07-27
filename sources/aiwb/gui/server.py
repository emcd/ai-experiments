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


''' FastAPI server for GUI support. '''

# https://bugfactory.io/articles/starting-and-stopping-uvicorn-in-the-background/


from . import __


async def prepare( auxdata ):
    ''' Prepares and executes FastAPI server. '''
    from socket import socket
    from threading import Thread
    from fastapi import FastAPI
    from uvicorn import Config, Server
    app = FastAPI( )
    app.get( '/' )( _http_get_root )
    config = Config( app = app, reload = True )
    server = Server( config = config )
    ( sock := socket( ) ).bind( ( '127.0.0.1', 0 ) )
    # TODO? Use async thread pool executor.
    thread = Thread( target = server.run, kwargs = { "sockets": [ sock ] } )
    address, port = sock.getsockname( )
    ic( address, port )
    auxdata.gui.server_context = __.AccretiveNamespace(
        server = server, thread = thread, address = address, port = port )


async def _http_get_root( ):
    return { 'message': 'Hello World' }
