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


@__.standard_dataclass
class Context:
    ''' Context data transfer object. '''
    # TODO? Hoist into invocables core.

    auxdata: __.Globals
    invoker: __.Invoker
    extras: __.AccretiveNamespace


@__.a.runtime_checkable
@__.standard_dataclass
class ArgumentsBase( __.a.Protocol ):
    ''' Base class for I/O arguments data transfer objects. '''

    @classmethod
    @__.abstract_member_function
    def from_dictionary( selfclass, arguments: __.Arguments ) -> __.a.Self:
        ''' Constructs data transfer object from dictionary. '''
        raise NotImplementedError


@__.standard_dataclass
class AcquireContentArguments( ArgumentsBase ):

    @classmethod
    def from_dictionary( selfclass, arguments: __.Arguments ) -> __.a.Self:
        # TODO: Implement
        return selfclass( )


@__.standard_dataclass
class SurveyDirectoryArguments( ArgumentsBase ):

    recursive: bool
    filters: __.AbstractSequence[ str ]

    @classmethod
    def from_dictionary( selfclass, arguments: __.Arguments ) -> __.a.Self:
        # TODO? Validate filters.
        return selfclass(
            recursive = arguments.get( 'recursive', False ),
            filters = arguments.get( 'filters', ( ) ) )


@__.standard_dataclass
class UpdateContentArguments( ArgumentsBase ):

    @classmethod
    def from_dictionary( selfclass, arguments: __.Arguments ) -> __.a.Self:
        # TODO: Implement
        return selfclass( )


@__.a.runtime_checkable
@__.standard_dataclass
class Accessor( __.a.Protocol ):
    ''' Interface for standard I/O operations. '''

    @classmethod
    @__.abstract_member_function
    def from_url_parts( selfclass, parts: __.UrlParts ) -> __.a.Self:
        ''' Constructs instance from result of URL parse. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def list_folder(
        self, context: Context, arguments: SurveyDirectoryArguments,
    ) -> __.AbstractDictionary:
        ''' Lists directory at URL or filesystem path. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def read(
        self, context: Context, arguments: AcquireContentArguments,
    ) -> __.AbstractDictionary:
        ''' Reads contents at URL or filesystem path. '''
        raise NotImplementedError

    @__.abstract_member_function
    async def write(
        self, context: Context, arguments: UpdateContentArguments,
    ) -> __.AbstractDictionary:
        ''' Writes contents at URL or filesystem path. '''
        raise NotImplementedError


# TODO: Use accretive dictionary with validators for validators registry.
accessors = __.AccretiveDictionary( )
arguments_classes = __.DictionaryProxy( {
    'list_folder': SurveyDirectoryArguments,
    'read': AcquireContentArguments,
    'write': UpdateContentArguments,
} )


# TODO? grok
#   Probably move 'analyze' to separate summarization module.


async def list_folder(
    auxdata: __.Globals,
    invoker: __.Invoker,
    arguments: __.Arguments,
    extras: __.AccretiveNamespace,
) -> __.AbstractDictionary:
    ''' Lists directory at URL or filesystem path.

        May be recursive or single level.
        Optional filters, such as ignorefiles, may be applied.
    '''
    return await _operate(
        opname = 'list_folder',
        auxdata = auxdata,
        invoker = invoker,
        arguments = arguments,
        extras = extras )


# TODO: read


# TODO: write


async def _operate(
    opname: str,
    auxdata: __.Globals,
    invoker: __.Invoker,
    arguments: __.Arguments,
    extras: __.AccretiveNamespace,
) -> __.AbstractDictionary:
    try: accessor = _produce_accessor( arguments[ 'location' ] )
    except NotImplementedError as exc:
        # TODO? Generate apprisal notification.
        return { 'error': str( exc ) }
    context = Context( auxdata = auxdata, invoker = invoker, extras = extras )
    arguments_class = arguments_classes[ opname ]
    arguments_ = arguments_class.from_dictionary( arguments )
    return {
        'success': await getattr( accessor, opname )( context, arguments_ ) }


def _produce_accessor( url: str ) -> Accessor:
    # TODO? Unify with URL scheme parser in package base.
    parts = __.urlparse( url )
    scheme = parts.scheme
    if scheme in accessors:
        return accessors[ scheme ].from_url_parts( parts )
    else:
        raise NotImplementedError(
            f"URL scheme {scheme!r} not supported. URL: {url}" )
