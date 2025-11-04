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


from . import __


class InvocationFieldAbsence( __.Omnierror, ValueError ):
    ''' Required field missing from invocation request. '''

    def __init__( self, field: str ):
        super( ).__init__( f"Missing required field {field!r}." )


class InvocationFieldTypeMismatch( __.Omnierror, TypeError ):
    ''' Field in invocation request has incorrect type. '''

    def __init__(
        self,
        field: str,
        expected_type: str,
        received_type: __.Absential[ str ] = __.absent,
    ):
        if __.is_absent( received_type ):
            message = f"Field {field!r} expected {expected_type}."
        else:
            message = (
                f"Field {field!r} expected {expected_type}, "
                f"received {received_type}." )
        super( ).__init__( message )


class InvocationRequestCountMismatch( __.Omnierror, ValueError ):
    ''' Number of invocation requests does not match expectation. '''

    def __init__(
        self,
        expected_count: int,
        received_count: int,
        invocation_type: __.Absential[ str ] = __.absent,
    ):
        counts = f"{received_count}/{expected_count}"
        if __.is_absent( invocation_type ):
            message = f"Request count mismatch: {counts}."
        else:
            message = (
                f"Request count mismatch for {invocation_type}: {counts}." )
        super( ).__init__( message )


class InvocableInaccessibility( __.Omnierror, ValueError ):
    ''' Requested invocable not available in current context. '''

    def __init__( self, name: str ):
        super( ).__init__( f"Invocable {name!r} not available." )


class MessageRefinementFailure( __.Omnierror, AssertionError ):
    ''' Message refinement encountered invalid state. '''

    def __init__(
        self,
        issue_type: str,
        detected_role: __.Absential[ str ] = __.absent,
        anchor_role: __.Absential[ str ] = __.absent,
    ):
        if 'adjacent' == issue_type:
            message = f"Adjacent {detected_role} results detected."
        elif 'mixed' == issue_type:
            if __.is_absent( anchor_role ):
                message = "Mixed function and tool call results detected."
            else:
                message = (
                    f"Mixed function and tool call results detected "
                    f"(anchor: {anchor_role}, cursor: {detected_role})." )
        else:
            message = f"Message refinement failure: {issue_type}."
        super( ).__init__( message )


class MessageRoleInvalidity( __.Omnierror, AssertionError, ValueError ):
    ''' Invalid or unknown message role. '''

    def __init__( self, role, context ):
        super( ).__init__(
            f"Unknown or invalid message role {role!r} in {context}." )


class ModelInaccessibility( __.Omnierror, LookupError ):
    ''' Failed to access model from provider. '''

    def __init__( self, provider_name, genus, model_name = None ):
        if model_name:
            super( ).__init__(
                f"Could not access {genus.value} model {model_name!r} "
                f"on provider {provider_name!r}." )
        else:
            super( ).__init__(
                f"Could not access default {genus.value} model "
                f"on provider {provider_name!r}." )


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


class ProviderConfigurationInvalidity( __.Omnierror, ValueError ):
    ''' Provider configuration is invalid or incompatible. '''

    def __init__( self, reason ):
        super( ).__init__( f"Invalid provider configuration: {reason}." )


class ProviderCredentialsInavailability( __.Omnierror, LookupError ):
    ''' Provider credentials not available. '''

    def __init__( self, provider_name, credential_name ):
        super( ).__init__(
            f"Missing {credential_name!r} for provider {provider_name!r}." )


class ProviderDataFormatNoSupport( __.SupportError ):
    ''' Data format not supported by provider. '''

    def __init__( self, data_format, operation ):
        super( ).__init__(
            f"Cannot {operation} data in {data_format} format." )


class ProviderIncompatibilityError( __.SupportError ):
    ''' Provider is not compatible with object. '''

    def __init__( self, provider, entity_name ):
        message = (
            f"AI provider {provider.name!r} is not compatible "
            f"with {entity_name}." )
        super( ).__init__( message )
