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


''' Interfaces for available I/O operations. '''


from . import __


@__.a.runtime_checkable
@__.standard_dataclass
class ArgumentsBase( __.a.Protocol ):
    ''' Base class for I/O arguments data transfer objects. '''

    location: __.LocationImplement

    @classmethod
    @__.abstract_member_function
    def from_dictionary( selfclass, arguments: __.Arguments ) -> __.a.Self:
        ''' Constructs data transfer object from dictionary. '''
        raise NotImplementedError


@__.standard_dataclass
class AcquireContentsArguments( ArgumentsBase ):

    @classmethod
    def from_dictionary( selfclass, arguments: __.Arguments ) -> __.a.Self:
        # TODO: Implement
        return selfclass( )


@__.standard_dataclass
class SurveyDirectoryArguments( ArgumentsBase ):
    ''' Valid arguments for the 'survey_directory' operation. '''

    #file_size_maximum: int
    filters: __.AbstractSequence[ str ]
    recursive: bool
    return_directories: bool
    return_special_entities: bool
    return_symlinks: bool

    @classmethod
    def from_dictionary( selfclass, arguments: __.Arguments ) -> __.a.Self:
        # TODO? Validate filters.
        # TODO: Use defaults from schema or class attributes.
        return selfclass(
            location = __.SimpleLocationAccessor.from_url(
                arguments[ 'location' ] ).expose_implement( ),
            #file_size_maximum = arguments.get( 'file_size_maximum', 40000 ),
            filters = arguments.get( 'filters', ( 'gitignore', 'vcs' ) ),
            recursive = arguments.get( 'recursive', True ),
            return_directories = arguments.get( 'return_directories', True ),
            return_special_entities = arguments.get(
                'return_special_entities', True ),
            return_symlinks = arguments.get( 'return_symlinks', True ) )


@__.standard_dataclass
class UpdateContentsArguments( ArgumentsBase ):

    @classmethod
    def from_dictionary( selfclass, arguments: __.Arguments ) -> __.a.Self:
        # TODO: Implement
        return selfclass( )


@__.a.runtime_checkable
@__.standard_dataclass
class Accessor( __.a.Protocol ):
    ''' Interface for standard I/O operations. '''

    @__.abstract_member_function
    async def acquire_contents(
        self, context: __.Context, arguments: AcquireContentsArguments
    ) -> __.AbstractDictionary:
        ''' Reads contents at URL or filesystem path. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def survey_directory(
        self, context: __.Context, arguments: SurveyDirectoryArguments
    ) -> __.AbstractDictionary:
        ''' Lists directory at URL or filesystem path. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def update_contents(
        self, context: __.Context, arguments: UpdateContentsArguments
    ) -> __.AbstractDictionary:
        ''' Writes contents at URL or filesystem path. '''
        raise NotImplementedError


# TODO: Use accretive dictionary with validators for argument classes registry.
accessors = __.AccretiveDictionary( )
arguments_classes = __.DictionaryProxy( {
    'acquire_contents': AcquireContentsArguments,
    'survey_directory': SurveyDirectoryArguments,
    'update_contents': UpdateContentsArguments,
} )


# TODO? grok
#   Probably move 'analyze' to separate summarization module.


async def list_folder(
    context: __.Context, arguments: __.Arguments,
) -> __.AbstractDictionary:
    ''' Lists directory at URL or filesystem path.

        May be recursive or single level.
        Optional filters, such as ignorefiles, may be applied.
    '''
    return await _operate(
        opname = 'survey_directory',
        context = context,
        arguments = arguments )


# TODO: read


# TODO: write


async def _operate(
    opname: str, context: __.Context, arguments: __.Arguments,
) -> __.AbstractDictionary:
    arguments_class = arguments_classes[ opname ]
    try: arguments_ = arguments_class.from_dictionary( arguments )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    try: accessor = _produce_accessor( arguments_.location )
    except Exception as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    return {
        'success': await getattr( accessor, opname )( context, arguments_ ) }


def _produce_accessor( location: __.LocationImplement ) -> Accessor:
    url = location.url
    scheme = location.url.scheme
    if scheme in accessors: return accessors[ scheme ]( )
    raise NotImplementedError(
        f"URL scheme {scheme!r} not supported. URL: {url}" )
