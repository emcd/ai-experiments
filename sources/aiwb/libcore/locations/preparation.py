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


''' Registration of default location access adapters, etc.... '''


from . import __


async def register_defaults( ):
    ''' Registers default location access adapters, etc.... '''
    from importlib import import_module
    from inspect import ismodule
    genera_modules = (
        import_module( f".{name}", __package__ )
        for name in ( 'adapters', 'presenters' ) )
    species_modules = (
        import_module( f".{name}", genus_module.__package__ )
        for genus_module in genera_modules
        for name, attribute in vars( genus_module ).items( )
        if not name.startswith( '_' ) and not name.startswith( '@' ) and ismodule( attribute ) )
    registrators = tuple(
        species_module.register_defaults( )
        for species_module in species_modules
        if hasattr( species_module, 'register_defaults' ) )
    await __.gather_async( *registrators )
