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


''' Core interface to AI providers. '''


from . import __


class ChatCompletionError( Exception ): pass


@__.dataclass( frozen = True, kw_only = True, slots = True )
class ChatCallbacks:
    ''' Callbacks for AI provider to correspond with caller. '''

    allocator: __.a.Callable[ [ __.Canister ], __.a.Any ] = (
        lambda canister: canister )
    deallocator: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda handle: None )
    failure_notifier: __.a.Callable[ [ str ], None ] = (
        lambda status: None )
    progress_notifier: __.a.Callable[ [ int ], None ] = (
        lambda tokens_count: None )
    success_notifier: __.a.Callable[ [ __.a.Any ], None ] = (
        lambda status: None )
    updater: __.a.Callable[ [ __.a.Any, str ], None ] = (
        lambda handle: None )


class Provider:
    ''' Base for AI providers. '''


chat_callbacks_minimal = ChatCallbacks( )


async def prepare( auxdata ):
    ''' Prepare desired AI providers. '''
    from importlib import import_module
    scribe = __.acquire_scribe( __package__ )
    # TODO: Determine providers from configuration and only load those.
    names = ( 'openai', )
    registry = __.AccretiveDictionary( )
    # TODO: Build provider specs from configuration and load modules there.
    #       See vectorstores subpackage for example.
    modules = tuple(
        import_module( f".{name}", package = __package__ ) for name in names )
    results = await __.gather_async(
        *( module.prepare( auxdata ) for module in modules ),
        return_exceptions = True )
    for name, module, result in zip( names, modules, results ):
        match result:
            case __.g.Error( error ):
                summary = f"Could not prepare AI provider {name!r}."
                auxdata.notifications.enqueue_error(
                    error, summary, scribe = scribe )
            case __.g.Value( provider ):
                # TODO: Register provider future rather than module.
                registry[ provider.proper_name ] = module
    # TODO? Notify if empty registry.
    return registry


# TODO: Automatically populate with all classes and functions
#       where their __module__ attribute is __name__ of this module.
__all__ = (
    'ChatCallbacks', 'ChatCompletionError', 'Provider',
    'chat_callbacks_minimal', 'prepare',
)
