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


''' Functionality for various AI providers. '''


from .base import ChatCallbacks, ChatCompletionError, chat_callbacks_minimal


def prepare( configuration, directories ):
    from . import openai
    # TODO: Use accretive dictionary for providers registry.
    providers = { }
    # TODO: Prepare asynchronously.
    for provider in ( openai, ):
        try: provider_name = provider.prepare( configuration, directories )
        except Exception:
            #raise
            continue
        providers[ provider_name ] = provider
    return providers
