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


''' Core classes and functions for AI applications. '''


from . import __


def prepare( ) -> __.AccretiveNamespace:
    ''' Prepares AI-related functionality for applications. '''
    # TODO: Support async loading.
    from . import vectorstores
    from .ai import functions as ai_functions # TODO: invocables
    from .ai import providers as ai_providers # TODO: providers
    from .prompts import core as prompts
    auxdata = __.prepare( )
    # TODO: Pass auxdata to all preparers.
    configuration = auxdata.configuration
    directories = auxdata.directories
    auxdata.ai_functions = ai_functions.prepare( configuration, directories )
    auxdata.ai_providers = ai_providers.prepare( configuration, directories )
    auxdata.prompt_definitions = prompts.prepare( auxdata )
    auxdata.vectorstores = vectorstores.prepare( configuration, directories )
    return auxdata