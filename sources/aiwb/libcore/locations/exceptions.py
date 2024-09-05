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


class FilterArgumentSupportError( __.Omniexception, NotImplementedError ):
    ''' Attempt to use filter argument which has no implementation. '''

    def __init__( self, filter_name, argument_name ):
        super( ).__init__(
            f"Filter {filter_name!r} does not support "
            f"argument {argument_name!r}." )


class FilterAvailabilityError( __.Omniexception, NotImplementedError ):
    ''' Attempt to use filter which is not available. '''

    def __init__( self, filter_name ):
        super( ).__init__( f"Filter unavailable: {filter_name!r}" )


class FilterClassValidityError( __.Omniexception, TypeError, ValueError ):
    ''' Attempt to supply invalid class of object as filter. '''

    def __init__( self, class_ ):
        fqname = __.calculate_class_fqname( class_ )
        super( ).__init__(
            f"Cannot use instances of class {fqname!r} as filters." )


class FilterSpecifierValidityError( __.Omniexception, ValueError ):
    ''' Attempt to produce filter from invalid specifier. '''

    def __init__( self, specifier, reason ):
        super( ).__init__(
            f"Filter specifier {specifier!r} is invalid. Reason: {reason}" )


class UrlClassValidityError( __.Omniexception, TypeError, ValueError ):
    ''' Attempt to supply invalid class of object as URL. '''

    def __init__( self, class_ ):
        fqname = __.calculate_class_fqname( class_ )
        super( ).__init__(
            f"Cannot use instances of class {fqname!r} as URLs." )


class UrlSchemeSupportError( __.Omniexception, NotImplementedError ):
    ''' Attempt to use URL scheme which has no implementation. '''

    def __init__( self, url ):
        super( ).__init__(
            f"URL scheme {url.scheme!r} not supported. URL: {url}" )


class LocationOperateFailure( __.Omniexception, RuntimeError ):
    ''' Failure of attempt to operate on location. '''


class LocationCheckAccessFailure( LocationOperateFailure ):
    ''' Failure of attempt to check access to location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not check access of location '{url}'. Reason: {reason}" )


class LocationExamineFailure( LocationOperateFailure ):
    ''' Failure of attempt to examine location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not examine location '{url}'. Reason: {reason}" )
