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


''' Fundamental configuration. '''


from . import __
from . import distribution as _distribution


async def acquire(
    application_name: str,
    distribution: _distribution.Information,
    directories: __.PlatformDirs
) -> __.AccretiveDictionary:
    ''' Loads configuration as dictionary. '''
    from shutil import copyfile
    from aiofiles import open as open_
    from tomli import loads
    location = directories.user_config_path / 'general.toml'
    if not location.exists( ):
        copyfile(
            distribution.provide_data_location(
                'configuration', 'general.toml' ), location )
    # TODO: Raise error if location is not file.
    async with open_( location ) as file:
        configuration = loads( await( file.read( ) ) )
    includes = await _acquire_includes(
        application_name, directories, configuration.get( 'includes', ( ) ) )
    for include in includes: configuration.update( include )
    return __.AccretiveDictionary( configuration )


async def _acquire_includes(
    application_name: str,
    directories: __.PlatformDirs,
    specs: tuple[ str ]
) -> __.AbstractSequence[ dict ]:
    from itertools import chain
    from tomli import loads
    locations = tuple(
        __.Path( spec.format(
            user_configuration = directories.user_config_path,
            user_home = __.Path.home( ),
            application_name = application_name ) )
        for spec in specs )
    iterables = tuple(
        ( location.glob( '*.toml' ) if location.is_dir( ) else ( location, ) )
        for location in locations )
    includes = await __.read_files_async(
        *( file for file in chain.from_iterable( iterables ) ),
        deserializer = loads )
    return includes
