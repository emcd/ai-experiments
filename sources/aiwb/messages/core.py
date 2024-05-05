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


from . import base as __


@__.dataclass
class DirectoryManager:

    auxdata: __.SimpleNamespace

    _mkdir_nomargs_default = __.DictionaryProxy( dict(
        exist_ok = True, parents = True ) )

    def assert_content_directory( self, identity ):
        distributary = identity[ : 4 ]
        location = (
            self._provide_state_location( 'contents' )
            .joinpath( distributary, identity ) )
        if not location.exists( ): raise FileNotFoundError( location )
        return location

    def assert_conversation_directory( self, identity ):
        location = (
            self._provide_state_location( 'conversations' ) / identity )
        if not location.exists( ): raise FileNotFoundError( location )
        return location

    def create_content_directory( self, identity, mkdir_nomargs = None ):
        distributary = identity[ : 4 ]
        location = (
            self._provide_state_location( 'contents' )
            .joinpath( distributary, identity ) )
        mkdir_nomargs = mkdir_nomargs or self._mkdir_nomargs_default
        location.mkdir( **mkdir_nomargs )
        return location

    def create_conversation_directory( self, identity, mkdir_nomargs = None ):
        location = (
            self._provide_state_location( 'conversations' ) / identity )
        mkdir_nomargs = mkdir_nomargs or self._mkdir_nomargs_default
        location.mkdir( **mkdir_nomargs )
        return location

    def _provide_state_location( self, dirname = None ):
        configuration = self.auxdata.configuration
        directories = self.auxdata.directories
        location = __.Path( configuration[ 'locations' ][ 'state' ].format(
            user_state_path = directories.user_state_path ) )
        if dirname: return location / dirname
        return location


class Content: pass


@__.dataclass
class TextualContent( Content ):

    data: str
    identity: str = (
        __.dataclass_declare( default_factory = lambda: __.uuid4( ).hex ) )
    timestamp: int = (
        __.dataclass_declare( default_factory = __.time_ns ) )
    mimetype: str = 'text/markdown'

    def save( self, manager ):
        from tomli_w import dump
        # TODO: Async open and write.
        location = manager.create_content_directory( self.identity )
        # TODO? Handle URL for content source.
        descriptor = dict(
            mimetype = self.mimetype, timestamp = self.timestamp )
        descriptor[ 'format-version' ] = 1
        descriptor_location = location / 'descriptor.toml'
        with descriptor_location.open( 'wb' ) as descriptor_file:
            dump( descriptor, descriptor_file )
        data_location = location.joinpath(
            translate_mimetype_to_filename( 'data', self.mimetype ) )
        # TODO: Only write if timestamp newer than conversation timestamp.
        with data_location.open( 'w' ) as data_file:
            data_file.write( self.data )
        return self.identity


# TODO: PictureContent


@__.dataclass
class Canister:

    role: str
    attributes: __.SimpleNamespace = (
        __.dataclass_declare( default_factory = __.SimpleNamespace ) )
    contents: __.AbstractSequence[ Content ] = (
        __.dataclass_declare( default_factory = list ) )

    def add_content( self, data, /, **descriptor ):
        self.contents.append( create_content( data, **descriptor ) )
        return self

    def save( self, manager ):
        state = dict( role = self.role )
        # TODO: Async scatter contents.
        contents_identifiers = [ ]
        for content in self:
            contents_identifiers.append( content.save( manager ) )
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
    if mimetype in ( 'application/json', 'text/markdown', 'text/plain', ):
        return 'textual'
    # TODO: aural, motion-av, pictorial
    raise ValueError( f"Unrecognized MIME type: {mimetype}" )


def create_content( data, /, **descriptor ):
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


def restore_canister( manager, canister_state ):
    role = canister_state[ 'role' ]
    nomargs = { }
    attributes = canister_state.get( 'attributes' )
    if attributes:
        nomargs[ 'attributes' ] = __.SimpleNamespace( **attributes )
    canister = Canister( role, **nomargs )
    # TODO: Async gather contents.
    for content_identity in canister_state[ 'contents' ]:
        canister.contents.append(
            restore_content( manager, content_identity ) )
    return canister


def restore_content( manager, identity ):
    from tomli import load
    # TODO: Async open and read.
    # TODO: Maintain and check cache, since content may be shared
    #       across canisters and even conversations.
    location = manager.assert_content_directory( identity )
    descriptor_location = location / 'descriptor.toml'
    with descriptor_location.open( 'rb' ) as descriptor_file:
        descriptor = load( descriptor_file )
    version = descriptor.pop( 'format-version', 1 )
    mimetype = descriptor[ 'mimetype' ]
    # TODO? Handle URL for content source.
    data_location = location.joinpath(
        translate_mimetype_to_filename( 'data', mimetype ) )
    with data_location.open( 'rb' ) as data_file: data = data_file.read( )
    return create_content( data, **descriptor )


def translate_mimetype_to_filename( basename, mimetype ):
    # TODO? Python 3.10: match case
    if 'application/json' == mimetype: extension = 'json'
    elif 'text/markdown' == mimetype: extension = 'md'
    elif 'text/plain' == mimetype: extension = 'txt'
    else: raise ValueError( f"Unrecognized MIME type: {mimetype}" )
    return f"{basename}.{extension}"
