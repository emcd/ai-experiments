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


class FilterArgumentSupportError( __.SupportError ):
    ''' Attempt to use filter argument which has no implementation. '''

    def __init__( self, filter_name, argument_name ):
        super( ).__init__(
            f"Filter {filter_name!r} does not support "
            f"argument {argument_name!r}." )


class FilterAvailabilityError( __.SupportError ):
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


class LocationAccessorDerivationFailure( __.SupportError, AssertionError ):
    ''' Failure to derive specific location accessor. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not derive specific accessor for location '{url}'. "
            f"Reason: {reason}" )


class LocationAdapterDerivationFailure( __.SupportError, AssertionError ):
    ''' Failure to derive specific location access adapter. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not derive specific access adapter for location '{url}'. "
            f"Reason: {reason}" )


class LocationSpeciesAssertionFailure( __.Omniexception, AssertionError ):
    ''' Failure to provide acceptable location species. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Did not provide acceptable location species for '{url}'. "
            f"Reason: {reason}" )


class LocationOperateFailure( __.Omniexception, RuntimeError ):
    ''' Failure of attempt to operate on location. '''


class LocationAcquireContentFailure( LocationOperateFailure ):
    ''' Failure of attempt to acquire content from location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not acquire content from location '{url}'. "
            f"Reason: {reason}" )


class LocationCheckAccessFailure( LocationOperateFailure ):
    ''' Failure of attempt to check access to location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not check access to location '{url}'. "
            f"Reason: {reason}" )


class LocationCheckExistenceFailure( LocationOperateFailure ):
    ''' Failure of attempt to check existence of location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not check existence of location '{url}'. "
            f"Reason: {reason}" )


class LocationCreateFailure( LocationOperateFailure ):
    ''' Failure of attempt to create location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not create location '{url}'. "
            f"Reason: {reason}" )


class LocationDeleteFailure( LocationOperateFailure ):
    ''' Failure of attempt to delete location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not delete location '{url}'. "
            f"Reason: {reason}" )


class LocationExamineFailure( LocationOperateFailure ):
    ''' Failure of attempt to examine location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not examine location '{url}'. "
            f"Reason: {reason}" )


class LocationIsDirectoryFailure( LocationOperateFailure ):
    ''' Failure of attempt to determine if location is directory. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not determine if location '{url}' is directory. "
            f"Reason: {reason}" )


class LocationIsFileFailure( LocationOperateFailure ):
    ''' Failure of attempt to determine if location is file. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not determine if location '{url}' is file. "
            f"Reason: {reason}" )


class LocationIsIndirectionFailure( LocationOperateFailure ):
    ''' Failure of attempt to determine if location is indirection. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not determine if location '{url}' is indirection. "
            f"Reason: {reason}" )


class LocationUpdateContentFailure( LocationOperateFailure ):
    ''' Failure of attempt to update content at location. '''

    def __init__( self, url, reason ):
        super( ).__init__(
            f"Could not update content at location '{url}'. "
            f"Reason: {reason}" )


class LocationSpeciesSupportError( __.SupportError ):
    ''' Attempt to use location species which has no implementation. '''

    def __init__( self, entity_name, species ):
        super( ).__init__(
            f"Location species '{species}' not supported by {entity_name}." )


class RelativeLocatorClassValidityError(
    __.Omniexception, TypeError, ValueError
):
    ''' Attempt to supply invalid class of object as relative locator. '''

    def __init__( self, class_ ):
        fqname = __.calculate_class_fqname( class_ )
        super( ).__init__(
            f"Cannot use instances of class {fqname!r} as relative locators." )


class UrlClassValidityError( __.Omniexception, TypeError, ValueError ):
    ''' Attempt to supply invalid class of object as URL. '''

    def __init__( self, class_ ):
        fqname = __.calculate_class_fqname( class_ )
        super( ).__init__(
            f"Cannot use instances of class {fqname!r} as URLs." )


class UrlPartAssertionError( __.Omniexception, AssertionError, ValueError ):
    ''' Attempt to provide URL part which is not applicable. '''

    def __init__( self, entity_name, part_name, url ):
        super( ).__init__(
            f"URL {part_name} not applicable to {entity_name}. "
            f"URL: {url}" )


class UrlSchemeAssertionError( __.Omniexception, AssertionError, ValueError ):
    ''' Attempt to use URL scheme which is not applicable. '''

    def __init__( self, entity_name, url ):
        super( ).__init__(
            f"URL scheme {url.scheme!r} not applicable to {entity_name}. "
            f"URL: {url}" )


class UrlSchemeSupportError( __.SupportError ):
    ''' Attempt to use URL scheme which has no implementation. '''

    def __init__( self, url ):
        super( ).__init__(
            f"URL scheme {url.scheme!r} not supported. URL: {url}" )
