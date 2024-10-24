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


''' Core classes for messages. '''


from . import __


class DirectoryManager(
    metaclass = __.ImmutableDataclass,
    dataclass_arguments = __.standard_dataclass_arguments,
):
    ''' Manages conversation and message content directories. '''

    auxdata: __.AccretiveNamespace

    _mkdir_nomargs_default = __.DictionaryProxy( dict(
        exist_ok = True, parents = True ) )

    def assert_content_directory( self, identity ):
        ''' Errors if particular content directory does not exist. '''
        distributary = identity[ : 4 ]
        location = self.auxdata.provide_state_location(
            'contents', distributary, identity )
        if not location.exists( ): raise FileNotFoundError( location )
        return location

    def assert_conversation_directory( self, identity ):
        ''' Errors if particular conversation directory does not exist. '''
        location = self.auxdata.provide_state_location(
            'conversations', identity )
        if not location.exists( ): raise FileNotFoundError( location )
        return location

    def create_content_directory( self, identity, mkdir_nomargs = None ):
        ''' Creates content directory if it does not exist. '''
        distributary = identity[ : 4 ]
        location = self.auxdata.provide_state_location(
            'contents', distributary, identity )
        mkdir_nomargs = mkdir_nomargs or self._mkdir_nomargs_default
        location.mkdir( **mkdir_nomargs )
        return location

    def create_conversation_directory( self, identity, mkdir_nomargs = None ):
        ''' Creates conversation directory if it does not exist. '''
        location = self.auxdata.provide_state_location(
            'conversations', identity )
        mkdir_nomargs = mkdir_nomargs or self._mkdir_nomargs_default
        location.mkdir( **mkdir_nomargs )
        return location


@__.a.runtime_checkable
class Content( __.a.Protocol ):
    ''' Base for various content types. '''

    @__.abstract_member_function
    async def save( self, manager: DirectoryManager ):
        ''' Persists content to durable storage. '''
        raise NotImplementedError


@__.dataclass
class TextualContent( Content ):
    ''' Descriptor and data for textual content. '''

    data: str
    identity: str = (
        __.dataclass_declare( default_factory = lambda: __.uuid4( ).hex ) )
    timestamp: int = (
        __.dataclass_declare( default_factory = __.time_ns ) )
    mimetype: str = 'text/markdown'

    async def save( self, manager: DirectoryManager ):
        # TODO: Use locations subpackage for I/O.
        from aiofiles import open as open_
        from tomli_w import dumps
        location = manager.create_content_directory( self.identity )
        # TODO? Handle URL for content source.
        descriptor = dict(
            mimetype = self.mimetype, timestamp = self.timestamp )
        descriptor[ 'format-version' ] = 1
        descriptor_location = location / 'descriptor.toml'
        async with open_( descriptor_location, 'w' ) as descriptor_stream:
            await descriptor_stream.write( dumps( descriptor ) )
        data_location = location.joinpath(
            translate_mimetype_to_filename( 'data', self.mimetype ) )
        # TODO: Only write if timestamp newer than conversation timestamp.
        async with open_( data_location, 'w' ) as data_stream:
            await data_stream.write( self.data )
        return self.identity


# TODO: PictureContent


@__.dataclass
class Canister:
    ''' Message canister which can have multiple contents. '''

    role: str
    attributes: __.SimpleNamespace = (
        __.dataclass_declare( default_factory = __.SimpleNamespace ) )
    contents: __.AbstractMutableSequence[ Content ] = (
        __.dataclass_declare( default_factory = list ) )

    def add_content( self, data, /, **descriptor ):
        ''' Adds content of appropriate type to canister. '''
        self.contents.append( create_content( data, **descriptor ) )
        return self

    async def save( self, manager: DirectoryManager ):
        ''' Persists canister to durable storage. '''
        state = dict( role = self.role )
        savers = tuple( content.save( manager ) for content in self )
        contents_identifiers = await __.gather_async( *savers )
        state[ 'contents' ] = contents_identifiers
        attributes = self.attributes.__dict__
        if attributes: state[ 'attributes' ] = attributes
        return state

    def __getitem__( self, index ): return self.contents[ index ]

    def __iter__( self ): return iter( self.contents )

    def __len__( self ): return len( self.contents )


# TODO: Cohort: Bundle of related canisters.
#       * Image prompt and generations.
#       * Chat user prompt, AI function invocation request, AI function
#         invocations, and final AI response.
#       * Chat user prompt, semantic search documents, and AI response.


def classify_mimetype( mimetype ):
    ''' Determines content type from MIME type. '''
    if mimetype in ( 'application/json', 'text/markdown', 'text/plain', ):
        return 'textual'
    # TODO: aural, motion-av, pictorial
    raise ValueError( f"Unrecognized MIME type: {mimetype}" )


def create_content( data, /, **descriptor ):
    ''' Creates content object based on data and descriptor. '''
    mimetype = descriptor.get( 'mimetype' )
    if not mimetype:
        # TODO: Detect specific text format, such as Markdown or JSON.
        #       Standard MIME type detection will show 'text/plain'.
        if isinstance( data, str ): mimetype = 'text/markdown'
        else:
            from magic import from_buffer
            mimetype = from_buffer( data, mime = True )
    mimetype_class = classify_mimetype( mimetype )
    if 'textual' == mimetype_class:
        if isinstance( data, str ): return TextualContent( data, **descriptor )
        return TextualContent( data.decode( ), **descriptor )
    # TODO: aural, motion-av, pictorial
    raise NotImplementedError( f"MIME type not implemented: {mimetype}" )


async def restore_canister( manager, canister_state ):
    ''' Restores canister into memory from persistent storage. '''
    # TODO: Intercept 'response_class' attribute and patch role accordingly.
    role = canister_state[ 'role' ]
    nomargs = { }
    attributes = canister_state.get( 'attributes' )
    if attributes:
        nomargs[ 'attributes' ] = __.SimpleNamespace( **attributes )
    canister = Canister( role, **nomargs )
    restorers = tuple(
        restore_content( manager, content_identity )
        for content_identity in canister_state.get( 'contents', ( ) ) )
    contents = await __.gather_async( *restorers )
    for content in contents:
        canister.contents.append( content )
    return canister


async def restore_content( manager, identity ):
    ''' Restores content into memory from persistent storage. '''
    # TODO: Use locations subpackage for I/O.
    from aiofiles import open as open_
    from tomli import loads
    # TODO: Maintain and check cache, since content may be shared
    #       across canisters and even conversations.
    location = manager.assert_content_directory( identity )
    descriptor_file = location / 'descriptor.toml'
    async with open_( descriptor_file ) as descriptor_stream:
        descriptor = loads( await descriptor_stream.read( ) )
    descriptor.pop( 'format-version', 1 )
    descriptor[ 'identity' ] = identity
    mimetype = descriptor[ 'mimetype' ]
    # TODO? Handle URL for content source.
    data_file = location.joinpath(
        translate_mimetype_to_filename( 'data', mimetype ) )
    async with open_( data_file ) as data_stream:
        data = await data_stream.read( )
    return create_content( data, **descriptor )


def translate_mimetype_to_filename( basename, mimetype ):
    ''' Translates MIME type to filename with appropriate extension. '''
    # TODO: Appropriate error class.
    match mimetype:
        case 'application/json': extension = 'json'
        case 'text/markdown': extension = 'md'
        case 'text/plain': extension = 'text'
        case _: raise ValueError( f"Unrecognized MIME type: {mimetype}" )
    return f"{basename}.{extension}"
