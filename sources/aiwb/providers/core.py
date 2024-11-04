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


ClientImplement = __.a.TypeVar( 'ClientImplement', covariant = True )
NativeControls = __.a.TypeVar( 'NativeControls', covariant = True )
NativeMessages = __.a.TypeVar( 'NativeMessages', covariant = True )
ProviderVariants = __.a.TypeVar( 'ProviderVariants', covariant = True )


class ClientDefaults(
    metaclass = __.ImmutableClass,
    class_decorators = ( __.standard_dataclass, ),
):
    ''' Collection of default values for AI provider. '''

    converser_model: __.AbstractSequence[ str ] = ( )

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces client defaults instance from descriptor. '''
        args = __.AccretiveDictionary( )
        for arg_name in ( 'converser-model', ):
            arg = descriptor.get( arg_name )
            if None is arg: continue
            if isinstance( arg, str ): arg = ( arg, )
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        return selfclass( **args )


class ClientAttributes(
    metaclass = __.ImmutableClass,
    class_decorators = ( __.standard_dataclass, ),
):
    ''' Common attributes for AI provider clients. '''

    defaults: ClientDefaults = ClientDefaults( )

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        ''' Produces client attributes instance from descriptor. '''
        return selfclass(
            **selfclass.init_args_from_descriptor( descriptor ) )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.AbstractDictionary[ str, __.a.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.AccretiveDictionary( )
        args[ 'defaults' ] = (
            ClientDefaults.from_descriptor(
                descriptor.get( 'defaults', { } ) ) )
        return args


class ConversationReactors(
    metaclass = __.ImmutableClass,
    class_decorators = ( __.standard_dataclass, ),
):
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


class DataFormatPreferences( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Preferred data formats for AI model input or output. '''

    Indefinite =    '#indefinite#'
    JSON =          'JSON'
    XML =           'XML'


class MathFormatPreferences( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Preferred math expression formats for AI model input or output. '''

    Indefinite =    '#indefinite#'
    MathJax =       'MathJax' # $$ .. $$, \[ .. \], \( .. \)


class TextFormatPreferences( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Preferred text prose formats for AI model input or output. '''

    Indefinite =    '#indefinite#'
    Markdown =      'Markdown'


class ConverserModalities( __.Enum ): # TODO: Python 3.11: StrEnum
    ''' Supportable input modalities for AI chat models. '''

    Audio       = 'audio'
    Pictures    = 'pictures'
    Text        = 'text'


class ConverserFormatPreferences(
    metaclass = __.ImmutableClass,
    class_decorators = ( __.standard_dataclass, )
):
    ''' Preferred formats for converser model requests and responses. '''

    request_data: DataFormatPreferences = DataFormatPreferences.Indefinite
    request_math: MathFormatPreferences = MathFormatPreferences.Indefinite
    request_text: TextFormatPreferences = TextFormatPreferences.Indefinite
    response_data: DataFormatPreferences = DataFormatPreferences.Indefinite
    response_math: MathFormatPreferences = MathFormatPreferences.Indefinite
    response_text: TextFormatPreferences = TextFormatPreferences.Indefinite

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.a.Any ],
    ) -> __.a.Self:
        args = __.AccretiveDictionary( )
        for arg_species in ( 'data', 'math', 'text' ):
            match arg_species:
                case 'data': preferences_class = DataFormatPreferences
                case 'math': preferences_class = MathFormatPreferences
                case 'text': preferences_class = TextFormatPreferences
            for arg_genus in ( 'request', 'response' ):
                arg_name = f"{arg_genus}-{arg_species}"
                arg = descriptor.get( arg_name )
                if None is arg: continue
                arg_name_ = arg_name.replace( '-', '_' )
                args[ arg_name_ ] = preferences_class( arg )
        return selfclass( **args )


class ConverserTokensLimits(
    metaclass = __.ImmutableClass,
    class_decorators = ( __.standard_dataclass, )
):
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


class InvocationRequest(
    metaclass = __.ImmutableClass,
    class_decorators = ( __.standard_dataclass, )
):
    ''' Provider-neutral invocation (tool use) request. '''

    name: str
    arguments: __.AbstractDictionary[ str, __.a.Any ]
    invocation: __.a.Callable # TODO: Full signature.
    specifics: __.AccretiveDictionary = ( # TODO: Full signature.
        __.dataclass_declare( default_factory = __.AccretiveDictionary ) )

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: InvocationDescriptor,
        context, # TODO: Signature.
    ) -> __.a.Self:
        ''' Produces instance from descriptor dictionary. '''
        from .exceptions import InvocationFormatError as Error
        if not isinstance( descriptor, __.AbstractDictionary ):
            raise Error( "Invocation descriptor is not dictionary." )
        if 'name' not in descriptor:
            raise Error( "Invocation descriptor without name." )
        name = descriptor[ 'name' ]
        if name not in context.invokers:
            raise Error( f"Invocable {name!r} is not available." )
        arguments = descriptor.get( 'arguments', { } )
        # TODO: Provide supplements based on specification from invocable.
        invocation = __.partial_function(
            context.invokers[ name ],
            auxdata = context.auxdata,
            arguments = arguments,
            supplements = context.supplements )
        return selfclass(
            name = name, arguments = arguments, invocation = invocation )


class ModelIntegrationBehaviors( __.enum.IntFlag ):
    ''' How to fold attributes from model integrators together. '''
    # TODO: Immutable class attributes.

    Default             = 0
    ReplaceControls     = __.produce_enumeration_value( )


class ModelsIntegrator(
    metaclass = __.ImmutableClass,
    class_decorators = ( __.standard_dataclass, )
):
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


# TODO: Python 3.12: Use type statement for aliases.
InvocationDescriptor: __.a.TypeAlias = (
    __.AbstractDictionary[ str, __.a.Any ] )
InvocationsRequests: __.a.TypeAlias = (
    __.AbstractSequence[ InvocationRequest ] )
ModelsIntegrators: __.a.TypeAlias = __.AbstractSequence[ ModelsIntegrator ]
ModelsIntegratorsMutable: __.a.TypeAlias = (
    __.AbstractMutableSequence[ ModelsIntegrator ] )
ModelsIntegratorsByGenus: __.a.TypeAlias = (
    __.AbstractDictionary[ ModelGenera, ModelsIntegrators ] )
ModelsIntegratorsByGenusMutable: __.a.TypeAlias = (
    __.AbstractMutableDictionary[ ModelGenera, ModelsIntegratorsMutable ] )


conversation_reactors_minimal = ConversationReactors( )


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
