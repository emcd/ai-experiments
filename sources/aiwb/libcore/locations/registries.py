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


''' Factories, mass applicators, and registries. '''

# ruff: noqa: F401


from __future__ import annotations

from . import __
from . import core as _core
from . import exceptions as _exceptions
from . import interfaces as _interfaces


# TODO: Python 3.12: type statement for aliases
AdaptersRegistry: __.a.TypeAlias = (
    __.AbstractDictionary[ str, type[ '_interfaces.GeneralAdapter' ] ] )
CachesRegistry: __.a.TypeAlias = (
    __.AbstractDictionary[ str, type[ '_interfaces.CacheManager' ] ] )
FilePresentersRegistry: __.a.TypeAlias = (
    __.AbstractDictionary[ str, type[ '_interfaces.FilePresenter' ] ] )
# TODO: Content filters versus dirent filters.
FiltersRegistry: __.a.TypeAlias = (
    __.AbstractDictionary[ str, type[ '_interfaces.Filter' ] ] )


# TODO: Use accretive validator dictionaries for registries.
adapters_registry: AdaptersRegistry = __.accret.Dictionary( )
caches_registry: CachesRegistry = __.accret.Dictionary( )
file_presenters_registry: FilePresentersRegistry = __.accret.Dictionary( )
filters_registry: FiltersRegistry = __.accret.Dictionary( )


def adapter_from_url( url: _core.PossibleUrl ) -> '_interfaces.GeneralAdapter':
    ''' Produces location access adapter from URL. '''
    url = _core.Url.from_url( url )
    scheme = url.scheme
    if scheme in adapters_registry:
        return adapters_registry[ scheme ].from_url( url )
    from .exceptions import UrlSchemeSupportError
    raise UrlSchemeSupportError( url )


async def apply_filters(
    dirent: _core.DirectoryEntry,
    filters: __.AbstractIterable[ '_interfaces.Filter' ],
) -> bool:
    ''' Applies iterable of filters to directory entry. '''
    for filter_ in filters:
        if await filter_( dirent ): return True
    return False


def cache_from_url(
    url: _core.PossibleUrl,
    manager: __.Optional[ '_interfaces.CacheManager' ] = __.absent,
) -> '_interfaces.GeneralCache':
    ''' Produces cache from URL and cache manager. '''
    adapter = adapter_from_url( url = url )
    if adapter.is_cache_manager( ):
        if __.absent is not manager:
            # TODO: raise error
            pass
        manager = adapter
    elif __.absent is manager:
        # TODO: raise error
        pass
    # TODO: assert manager type
    return manager.produce_cache( adapter )


def directory_adapter_from_url(
    url: _core.PossibleUrl
) -> '_interfaces.DirectoryAdapter':
    ''' Produces directory access adapter from URL. '''
    return adapter_from_url( url ).as_directory( )


def file_adapter_from_url(
    url: _core.PossibleUrl
) -> '_interfaces.FileAdapter':
    ''' Produces file access adapter from URL. '''
    return adapter_from_url( url ).as_file( )


async def file_presenter_from_accessor(
    accessor: '_interfaces.FileAccessor',
    mimetype: __.Optional[ str ] = __.absent,
) -> '_interfaces.FileAccessor' | '_interfaces.FilePresenter':
    ''' Produces file content presenter from accessor, if possible.

        If no registered MIME type, then returns bare file accessor.
    '''
    if __.absent is mimetype:
        inode = await accessor.examine(
            attributes = _core.InodeAttributes.Mimetype )
        mimetype = inode.mimetype
    if mimetype in file_presenters_registry:
        return file_presenters_registry[ mimetype ]( accessor = accessor )
    mimetype = '/'.join( ( mimetype.split( '/', maxsplit = 1 )[ 0 ], '*' ) )
    if mimetype in file_presenters_registry:
        return file_presenters_registry[ mimetype ]( accessor = accessor )
    return accessor


async def file_presenter_from_url(
    url: _core.PossibleUrl,
    mimetype: __.Optional[ str ] = __.absent,
) -> '_interfaces.FileAccessor' | '_interfaces.FilePresenter':
    ''' Produces file content presenter from URL, if possible.

        If no registered MIME type, then returns bare file accessor.
    '''
    adapter = adapter_from_url( url ).as_file( )
    return await file_presenter_from_accessor( accessor = adapter )


def text_file_presenter_from_accessor(
    accessor: '_interfaces.FileAccessor',
    charset: __.Optional[ str ] = __.absent,
    charset_errors: str = 'strict',
    newline: __.Optional[ str ] = __.absent,
) -> '_interfaces.FilePresenter':
    ''' Produces text file content presenter from accessor. '''
    charset_ = None if __.absent is charset else charset
    newline_ = None if __.absent is newline else newline
    return file_presenters_registry[ 'text/*' ](
        accessor = accessor,
        charset = charset_,
        charset_errors = charset_errors,
        newline = newline_ )


def text_file_presenter_from_url(
    url: _core.PossibleUrl,
    charset: __.Optional[ str ] = __.absent,
    charset_errors: str = 'strict',
    newline: __.Optional[ str ] = __.absent,
) -> '_interfaces.FilePresenter':
    ''' Produces text file content presenter from URL. '''
    adapter = adapter_from_url( url ).as_file( )
    return text_file_presenter_from_accessor(
        accessor = adapter,
        charset = charset,
        charset_errors = charset_errors,
        newline = newline )


def filters_from_specifiers(
    filters: __.AbstractIterable[ '_interfaces.PossibleFilter' ]
) -> __.AbstractSequence[ '_interfaces.Filter' ]:
    ''' Converts iterable of possible filters into filters. '''
    filters_ = [ ]
    for filter_ in filters:
        if isinstance( filter_, bytes ): filter_ = filter_.decode( )
        if isinstance( filter_, str ):
            name, arguments = _parse_filter_specifier( filter_ )
            if name in filters_registry:
                filter_ = filters_registry[ name ]( *arguments )
            # TODO? Collect errors into exception group.
            else: raise _exceptions.FilterAvailabilityError( name )
        if isinstance( filter_, _interfaces.Filter ):
            filters_.append( filter_ )
        else: raise _exceptions.FilterClassValidityError( filter_ )
    return tuple( filters_ )


def _parse_filter_specifier(
    specifier: str
) -> ( str, __.AbstractSequence[ __.a.Any ] ):
    for index, delim in enumerate( specifier ):
        if ':' == delim: break
        if delim in ( '<', '>' ): break
    else: return specifier, ( )
    match delim:
        case ':': name, *arguments = specifier.split( delim )
        case '<' | '>':
            index1 = index + 1
            if index1 < len( specifier ) and '=' == specifier[ index1 ]:
                splitter = f"{delim}="
            else: splitter = delim
            name, *arguments = specifier.split( splitter, maxsplit = 1 )
            arguments = ( splitter, *arguments )
    return name, tuple( arguments )
