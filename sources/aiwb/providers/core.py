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


''' Core classes and functions for AI providers. '''


from __future__ import annotations

from . import __


class ChatCompletionError( Exception ): pass


@__.dataclass( frozen = True, kw_only = True, slots = True )
class ChatCallbacks:
    ''' Callbacks for AI provider to correspond with caller. '''

    allocator: __.a.Callable[ [ __.MessageCanister ], __.a.Any ] = (
        lambda canister: canister )
    deallocator: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda handle: None )
    failure_notifier: __.a.Callable[ [ str ], None ] = (
        lambda status: None )
    progress_notifier: __.a.Callable[ [ int ], None ] = (
        lambda tokens_count: None )
    success_notifier: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda status: None )
    updater: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda handle: None )


class ConverserModalities( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Supportable input modalities for AI chat models. '''

    Audio       = 'audio'
    Pictures    = 'pictures'
    Text        = 'text'


@__.standard_dataclass
class ConverserTokensLimits:
    ''' Various limits on number of tokens in chat completion. '''

    # TODO? per_prompt
    per_response: int = 0
    total: int = 0

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        args = __.AccretiveDictionary( )
        for arg_name in ( 'per-response', 'total' ):
            arg = descriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        return selfclass( **args )


@__.standard_dataclass
class ConverserAttributes:
    ''' Common attributes for AI chat models. '''

    accepts_supervisor_instructions: bool = False
    modalities: __.AbstractSequence[ ConverserModalities ] = (
        ConverserModalities.Text, )
    supports_continuous_response: bool = False
    supports_invocations: bool = False
    tokens_limits: ConverserTokensLimits = ConverserTokensLimits( )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.AccretiveDictionary( )
        for arg_name in (
            'accepts-supervisor-instructions',
            'supports-continuous-response',
            'supports-invocations',
        ):
            arg = descriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        modalities = [ ]
        for modality_name in descriptor.get( 'modalities', ( ) ):
            modalities.append( ConverserModalities( modality_name ) )
        args[ 'modalities' ] = tuple( modalities )
        tokens_limits = ConverserTokensLimits.from_descriptor(
            descriptor.get( 'tokens-limits', { } ) )
        args[ 'tokens_limits' ] = tokens_limits
        return args


class ModelIntegrationBehaviors( __.enum.IntFlag ):

    Default             = 0
    ReplaceControls     = __.produce_enumeration_value( )


@__.standard_dataclass
class ModelsIntegrator:
    ''' Integrates attributes from configuration for matching models. '''
    # TODO: Immutable class attributes.

    attributes: __.AbstractDictionary[ str, __.a.Any ]
    behaviors: ModelIntegrationBehaviors
    regex: __.re.Pattern

    @classmethod
    def from_descriptor(
        selfclass, descriptor: __.AbstractDictionary[ str, __.a.Any ]
    ) -> __.a.Self:
        ''' Instance from configuration. '''
        desc = dict( descriptor )
        # TODO: Error if 'name-regex' is missing.
        regex = __.re.compile( desc.pop( 'name-regex' ) )
        behaviors = ModelIntegrationBehaviors.Default
        if desc.pop( 'replaces-controls', False ):
            behaviors |= ModelIntegrationBehaviors.ReplaceControls
        attributes = __.DictionaryProxy( desc )
        return selfclass(
            attributes = attributes, behaviors = behaviors, regex = regex )

    def __call__(
        self, name: str, attributes: __.AbstractDictionary[ str, __.a.Any ]
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Returns integrated copy of model attributes. '''
        if not self.regex.match( name ): return attributes
        ours = dict( self.attributes )
        theirs = dict( attributes )
        controls = ours.pop( 'controls', [ ] )
        if (    'controls' not in theirs
            or  self.behaviors & ModelIntegrationBehaviors.ReplaceControls
        ): theirs[ 'controls' ] = controls
        else: theirs[ 'controls' ].extend( controls )
        _merge_dictionaries_recursive( theirs, ours )
        return __.DictionaryProxy( theirs )


class ModelGenera( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Available genera for models. '''

    # Note: Not including domain-specific classifiers or text completers
    #       unless there is a compelling reason.
    AudioGenerator =    'audiogenerator'
    AudioTts =          'audiotts'
    Converser =         'converser'
    PictureGenerator =  'picturegenerator'
    Vectorizer =        'vectorizer'
    VideoGenerator =    'videogenerator'


chat_callbacks_minimal = ChatCallbacks( )
# TODO: Use accretive validator dictionary for preparers registry.


def _merge_dictionaries_recursive(
    theirs: __.AbstractMutableDictionary[ str, __.a.Any ],
    ours: __.AbstractDictionary[ str, __.a.Any ],
):
    for name, our_value in ours.items( ):
        if name not in theirs:
            theirs[ name ] = our_value
            continue
        their_value = theirs[ name ]
        if (    not isinstance( their_value, __.AbstractDictionary )
            or  not isinstance( our_value, __.AbstractDictionary )
        ):
            theirs[ name ] = our_value
            continue
        _merge_dictionaries_recursive( their_value, our_value )
