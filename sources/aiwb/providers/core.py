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


from . import __


ClientImplement = __.typx.TypeVar( 'ClientImplement', covariant = True )
NativeControls = __.typx.TypeVar( 'NativeControls', covariant = True )
NativeMessages = __.typx.TypeVar( 'NativeMessages', covariant = True )
ProviderVariants = __.typx.TypeVar( 'ProviderVariants', covariant = True )

InvocationDescriptor: __.typx.TypeAlias = (
    __.AbstractDictionary[ str, __.typx.Any ] )


class ClientDefaults( __.immut.DataclassObject ):
    ''' Collection of default values for AI provider. '''

    converser_model: __.AbstractSequence[ str ] = ( )

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.typx.Any ],
    ) -> __.typx.Self:
        ''' Produces client defaults instance from descriptor. '''
        args = __.accret.Dictionary( )
        for arg_name in ( 'converser-model', ):
            arg = descriptor.get( arg_name )
            if None is arg: continue
            if isinstance( arg, str ): arg = ( arg, )
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        return selfclass( **args )


class ClientAttributes( __.immut.DataclassObject ):
    ''' Common attributes for AI provider clients. '''

    defaults: ClientDefaults = ClientDefaults( )

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.typx.Any ],
    ) -> __.typx.Self:
        ''' Produces client attributes instance from descriptor. '''
        return selfclass(
            **selfclass.init_args_from_descriptor( descriptor ) )

    @classmethod
    def init_args_from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.typx.Any ],
    ) -> __.AbstractDictionary[ str, __.typx.Any ]:
        ''' Extracts dictionary of initializer arguments from descriptor. '''
        args = __.accret.Dictionary( )
        args[ 'defaults' ] = (
            ClientDefaults.from_descriptor(
                descriptor.get( 'defaults', { } ) ) )
        return args


class ConversationReactors( __.immut.DataclassObject ):
    ''' Callbacks for AI provider to correspond with caller. '''

    allocator: __.typx.Callable[ [ __.MessageCanister ], __.typx.Any ] = (
        lambda canister: canister )
    deallocator: __.typx.Callable[ [ __.typx.Any ], None ] = (
        lambda handle: None )
    failure_notifier: __.typx.Callable[ [ str ], None ] = (
        lambda status: None )
    progress_notifier: __.typx.Callable[ [ int ], None ] = (
        lambda tokens_count: None )
    success_notifier: __.typx.Callable[ [ __.typx.Any ], None ] = (
        lambda status: None )
    updater: __.typx.Callable[ [ __.typx.Any ], None ] = (
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
    __.immut.DataclassObject
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
        descriptor: __.AbstractDictionary[ str, __.typx.Any ],
    ) -> __.typx.Self:
        args = __.accret.Dictionary( )
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
    __.immut.DataclassObject
):
    ''' Various limits on number of tokens in chat completion. '''

    # TODO? per_prompt
    per_response: int = 0
    total: int = 0

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: __.AbstractDictionary[ str, __.typx.Any ],
    ) -> __.typx.Self:
        args = __.accret.Dictionary( )
        for arg_name in ( 'per-response', 'total' ):
            arg = descriptor.get( arg_name )
            if None is arg: continue
            arg_name_ = arg_name.replace( '-', '_' )
            args[ arg_name_ ] = arg
        return selfclass( **args )


class InvocationRequest(
    __.immut.DataclassObject
):
    ''' Provider-neutral invocation (tool use) request. '''

    name: str
    arguments: __.AbstractDictionary[ str, __.typx.Any ]
    invocation: __.typx.Callable # TODO: Full signature.
    specifics: __.accret.Dictionary = ( # TODO: Full signature.
        __.dataclass_declare( default_factory = __.accret.Dictionary ) )

    @classmethod
    def from_descriptor(
        selfclass,
        descriptor: InvocationDescriptor,
        context, # TODO: Signature.
    ) -> __.typx.Self:
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
    __.immut.DataclassObject
):
    ''' Integrates attributes from configuration for matching models. '''
    # TODO: Immutable class attributes.

    attributes: __.AbstractDictionary[ str, __.typx.Any ]
    behaviors: ModelIntegrationBehaviors
    regex: __.re.Pattern

    @classmethod
    def from_descriptor(
        selfclass, descriptor: __.AbstractDictionary[ str, __.typx.Any ]
    ) -> __.typx.Self:
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
        self, name: str, attributes: __.AbstractDictionary[ str, __.typx.Any ]
    ) -> __.AbstractDictionary[ str, __.typx.Any ]:
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
InvocationsRequests: __.typx.TypeAlias = (
    __.AbstractSequence[ InvocationRequest ] )
ModelsIntegrators: __.typx.TypeAlias = __.AbstractSequence[ ModelsIntegrator ]
ModelsIntegratorsMutable: __.typx.TypeAlias = (
    __.AbstractMutableSequence[ ModelsIntegrator ] )
ModelsIntegratorsByGenus: __.typx.TypeAlias = (
    __.AbstractDictionary[ ModelGenera, ModelsIntegrators ] )
ModelsIntegratorsByGenusMutable: __.typx.TypeAlias = (
    __.AbstractMutableDictionary[ ModelGenera, ModelsIntegratorsMutable ] )


conversation_reactors_minimal = ConversationReactors( )


def _merge_dictionaries_recursive(
    theirs: __.AbstractMutableDictionary[ str, __.typx.Any ],
    ours: __.AbstractDictionary[ str, __.typx.Any ],
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
