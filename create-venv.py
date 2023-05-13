#!/usr/bin/env python3

from pathlib import Path
from subprocess import run
from venv import create as create_venv

base_location = Path( __file__ ).parent.resolve( )
local_location = base_location / '.local'
for dirname in ( 'environments', 'installations', 'utilities' ):
    ( local_location / dirname ).mkdir( exist_ok = True, parents = True )

venv_location = local_location / 'environments/langchain'

if not venv_location.is_dir( ):
    create_venv( str( venv_location ), with_pip = True )

def activate_virtual_env( venv_location ):
    import os
    process_environment = os.environ.copy( )
    process_environment[ 'VIRTUAL_ENV' ] = str( venv_location )
    process_environment[ 'PATH' ] = os.pathsep.join(
        ( str( venv_location / 'bin' ), process_environment[ 'PATH' ] ) )
    process_environment.pop( 'PYTHONHOME', None )
    return process_environment

venv_variables = activate_virtual_env( venv_location )

run(
    ( 'python3', '-m', 'pip', 'install', '--upgrade', 'pip' ),
    env = venv_variables )
requirements_location = base_location / '.local/configuration/requirements.pip'
run(
    ( 'python3', '-m', 'pip', 'install',
      '--requirement', str( requirements_location ) ), env = venv_variables )
