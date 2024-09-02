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


''' Exceptions pertaining to locations and location access. '''


from . import __


class InvalidUrlClassError( __.Omniexception, TypeError, ValueError ):
    ''' Attempt to supply an invalid class of object as a URL. '''

    def __init__( self, class_ ):
        # TODO: Interpolate fqname of class.
        super( ).__init__(
            f"Cannot use instances of class {class_!r} as URLs." )


class NoUrlSchemeSupportError( __.Omniexception, NotImplementedError ):
    ''' Attempt to use URL scheme which has no implementation. '''

    def __init__( self, url ):
        super( ).__init__(
            f"URL scheme {url.scheme!r} not supported. URL: {url}" )


class OperationFailure( __.Omniexception, RuntimeError ):
    ''' Failure of attempt to perform operation. '''


class CheckAccessOperationFailure( OperationFailure ):
    ''' Failure of attempt to check access. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not check access of location '{url}'. Reason: {reason}" )
