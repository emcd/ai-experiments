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


''' Data structures and utilities for API server. '''


from __future__ import annotations

from . import __


class Accessor(
    __.immut.DataclassObject
):
    ''' Accessor for server properties and thread. '''

    application: __.FastAPI
    control: 'Control'
    server: __.UvicornServer
    thread: __.Thread


class Control(
    __.immut.DataclassObject
):
    ''' Binding address and port, etc... for server. '''

    address: str = '127.0.0.1'
    port: int = 0
    reload: bool = True

    def with_address_and_port( self, address: str, port: int ) -> __.a.Self:
        ''' Returns new instance with mutated address and port. '''
        # TODO: Generic 'with_attributes' method.
        return type( self )(
            address = address, port = port, reload = self.reload )


async def prepare(
    auxdata: __.ApplicationGlobals, control: Control
) -> Accessor:
    ''' Prepares server accessor from control information. '''
    # https://bugfactory.io/articles/starting-and-stopping-uvicorn-in-the-background/
    scribe = __.acquire_scribe( __package__ )
    from socket import socket
    app = __.FastAPI( )
    app.get( '/' )( _http_get_root )
    config = __.UvicornConfig( app = app, reload = control.reload )
    server = __.UvicornServer( config = config )
    ( sock := socket( ) ).bind( ( control.address, control.port ) )
    address, port = sock.getsockname( )
    control_ = control.with_address_and_port( address = address, port = port )
    thread = await auxdata.exits.enter_async_context(
        _execute_server_thread( server, nomargs = { "sockets": [ sock ] } ) )
    scribe.info( f"API server listening on {address}:{port}." )
    return Accessor(
        application = app,
        control = control_,
        server = server,
        thread = thread )


@__.exit_manager_async
async def _execute_server_thread(
    server: __.UvicornServer, nomargs: __.AbstractDictionary[ str, __.a.Any ]
) -> __.AbstractGenerator:
    scribe = __.acquire_scribe( __package__ )
    from asyncio import sleep
    from threading import Thread
    thread = Thread( target = server.run, kwargs = nomargs )
    thread.start( )
    scribe.info( "Waiting for API server to start." )
    try:
        while not server.started: await sleep( 0.001 )
        yield thread
    finally:
        scribe.info( "Waiting for API server to stop." )
        server.should_exit = True
        thread.join( )


async def _http_get_root( ):
    return { 'message': 'Hello World' }
