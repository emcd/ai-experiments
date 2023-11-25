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

    _mkdir_nomargs_default = __.DictionaryProxy(
        dict( exist_ok = True, parents = True ) )

    def assert_content_directory( self, identity ):
        location = self._provide_state_location( 'contents' ) / identity
        if not location.exists( ): raise FileNotFoundError( location )
        return location

    def assert_conversation_directory( self, identity ):
        location = (
            self._provide_state_location( 'conversations' ) / identity )
        if not location.exists( ): raise FileNotFoundError( location )
        return location

    def create_content_directory( self, identity, mkdir_nomargs = None ):
        location = self._provide_state_location( 'contents' ) / identity
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
    contents: __.AbstractSequence[ Content ]
    attributes: __.SimpleNamespace = (
        __.dataclass_declare( default_factory = __.SimpleNamespace ) )
    context: __.AbstractMutableDictionary[ __.typ.Any ] = (
        __.dataclass_declare( default_factory = dict ) )

    def save( self, manager ):
        canister_state = dict( role = self.role )
        # TODO: Async scatter contents.
        contents_state = [ ]
        for content in self.contents:
            contents_state.append( content.save( manager ) )
        canister_state[ 'contents' ] = contents_state
        attributes = self.attributes.__dict__
        if attributes: canister_state[ 'attributes' ] = attributes
        if self.context: canister_state[ 'context' ] = self.context
        return canister_state


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
        else: return TextualContent( data.decode( ), **descriptor )
    # TODO: aural, motion-av, pictorial
    else: raise NotImplementedError( f"MIME type not implemented: {mimetype}" )


def restore_canister( manager, canister_state ):
    role = canister_state[ 'role' ]
    # TODO: Async gather contents.
    contents = [ ]
    for content_identity in canister_state[ 'contents' ]:
        contents.append( restore_content( manager, content_identity ) )
    nomargs = { }
    attributes = canister_state.get( 'attributes' )
    if attributes:
        nomargs[ 'attributes' ] = __.SimpleNamespace( **attributes )
    context = canister_state.get( 'context' )
    if context: nomargs[ 'context' ] = context
    return Canister( role, contents, **nomargs )


def restore_content( manager, identity ):
    from tomli import load
    # TODO: Async open and read.
    # TODO: Maintain and check cache, since content may be shared
    #       across canisters and even conversations.
    location = manager.assert_content_directory( identity )
    descriptor_location = location / 'descriptor.toml'
    with descriptor_location.open( 'rb' ) as descriptor_file:
        descriptor = load( descriptor_file )
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
