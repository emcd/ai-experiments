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
from . import dictedits as _dictedits
from . import distribution as _distribution
from . import locations as _locations


async def acquire(
    application_name: str,
    directories: __.PlatformDirs,
    distribution: _distribution.Information,
    edits: _dictedits.Edits = ( ),
    file: __.Optional[ _locations.Url ] = __.absent,
) -> __.AccretiveDictionary:
    ''' Loads configuration as dictionary. '''
    if __.absent is file:
        from shutil import copyfile
        path = directories.user_config_path / 'general.toml'
        if not path.exists( ):
            copyfile(
                distribution.provide_data_location(
                    'configuration', 'general.toml' ), path )
        file = _locations.Url.from_url( path )
    accessor = _locations.text_file_presenter_from_url( file )
    # TODO: Assert scheme is '' or 'file'.
    from tomli import loads
    configuration = loads( await accessor.acquire_content( ) )
    includes = await _acquire_includes(
        application_name, directories, configuration.get( 'includes', ( ) ) )
    for include in includes: configuration.update( include )
    for edit in edits: edit( configuration )
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
