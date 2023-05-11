#!/usr/bin/env python3

from pathlib import Path
from subprocess import run
from venv import create as create_venv

base_path = Path( __file__ ).parent.resolve( )
local_path = base_path / '.local'
for dirname in ( 'environments', 'installations', 'utilities' ):
    ( local_path / dirname ).mkdir( exist_ok = True, parents = True )

venv_path = local_path / 'environments/langchain'

if not venv_path.is_dir( ): create_venv( str( venv_path ), with_pip = True )

def activate_virtual_env( venv_path ):
    from os import environ, pathsep
    new_env = environ.copy()
    new_env[ 'VIRTUAL_ENV' ] = str( venv_path )
    new_env[ 'PATH' ] = pathsep.join(
        ( str( venv_path / 'bin' ), new_env[ 'PATH' ] ) )
    new_env.pop( 'PYTHONHOME', None )
    return new_env

venv_env = activate_virtual_env( venv_path )

run(
    ( 'python3', '-m', 'pip', 'install', '--upgrade', 'pip' ),
    env = venv_env )
requirements_file = base_path / '.local/configuration/requirements.pip'
run(
    ( 'python3', '-m', 'pip', 'install', '-r', str( requirements_file ) ),
    env = venv_env )
