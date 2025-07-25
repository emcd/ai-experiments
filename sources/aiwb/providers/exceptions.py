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


''' Exception classes for AI providers. '''


from __future__ import annotations

from . import __


class InvocationFormatError( __.Omnierror, ValueError ):
    ''' Invalid format for invocation request. '''


class ModelOperateFailure( __.Omnierror ):
    ''' Failure of attempt to operate AI model. '''

    def __init__(
        self,
        model,
        operation: str,
        cause: __.Absential[ str | Exception ] = __.absent,
    ):
        if isinstance( cause, Exception ):
            cause_message = "Cause: {}".format( __.exception_to_str( cause ) )
        elif isinstance( cause, str ): cause_message = f"Cause: {cause}"
        else: cause_message = ''
        message = ' '.join( filter(
            None,
            ( (
                f"Could not perform {operation} with {model}.",
                cause_message ) ) ) )
        super( ).__init__( message )


class ProviderIncompatibilityError( __.SupportError ):
    ''' Provider is not compatible with object. '''

    def __init__( self, provider, entity_name ):
        message = (
            f"AI provider {provider.name!r} is not compatible "
            f"with {entity_name}." )
        super( ).__init__( message )
