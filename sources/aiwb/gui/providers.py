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


''' Management of AI providers for Holoviz Panel GUI. '''


from . import __


mutex_models = __.MutexAsync( )
mutex_providers = __.MutexAsync( )


async def access_provider_selection( components ):
    ''' Returns currently selected provider. '''
    # TODO: Replace with something that can honor multiple providers.
    async with mutex_providers:
        return (
            components.auxdata__.providers
            [ components.selector_provider.value ] )


async def access_model_selection( components ):
    ''' Returns currently selected model. '''
    # TODO: Replace with something that can honor multiple models.
    async with mutex_models:
        return (
            components.selector_model.auxdata__
            [ components.selector_model.value ] )


def package_controls( components ):
    ''' Assimilates from GUI control values for AI models. '''
    # TODO: Dynamic, depending on AI model.
    return dict(
        provider = components.selector_provider.value,
        model = components.selector_model.value,
        temperature = components.slider_temperature.value,
    )
