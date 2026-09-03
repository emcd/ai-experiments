# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-


''' GUI server local WebSocket origin configuration. '''


from types import SimpleNamespace
from unittest.mock import Mock

from sources.aiwb.gui import server as _server


def test_001_fixed_port_allows_local_hostname_aliases( ) -> None:
    ''' Fixed-port GUI server accepts localhost and loopback origins. '''
    template = Mock( )
    components = SimpleNamespace( template__ = template )
    control = _server.Control(
        address = '127.0.0.1', open_browser = False, port = 5006 )
    _server._start_gui( components, control )
    assert template.show.call_args.kwargs[ 'websocket_origin' ] == [
        'localhost:5006', '127.0.0.1:5006' ]


def test_002_dynamic_port_uses_matching_localhost_default( ) -> None:
    ''' Dynamic-port GUI server opens its default authorized hostname. '''
    template = Mock( )
    components = SimpleNamespace( template__ = template )
    _server._start_gui( components, _server.Control( open_browser = False ) )
    assert template.show.call_args.kwargs[ 'address' ] == 'localhost'
    assert template.show.call_args.kwargs[ 'websocket_origin' ] is None
