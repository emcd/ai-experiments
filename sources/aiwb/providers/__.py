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


''' Common classes and functions for AI providers. '''

# pylint: disable=unused-import


from ..__ import *
from ..messages.core import Canister


class ChatCompletionError( Exception ): pass


@dataclass
class ChatCallbacks:
    ''' Callbacks for AI provider to correspond with caller. '''

    allocator: a.Callable[ [ Canister ], a.Any ] = (
        lambda canister: canister )
    deallocator: a.Callable[ [ a.Any ], None ] = (
        lambda handle: None )
    failure_notifier: a.Callable[ [ str ], None ] = (
        lambda status: None )
    progress_notifier: a.Callable[ [ int ], None ] = (
        lambda tokens_count: None )
    success_notifier: a.Callable[ [ a.Any ], None ] = (
        lambda status: None )
    updater: a.Callable[ [ a.Any, str ], None ] = (
        lambda handle: None )


class Provider:
    ''' Base for AI providers. '''


chat_callbacks_minimal = ChatCallbacks( )


# TODO: Automatically populate with all classes and functions
#       where their __module__ attribute is __name__ of this module.
__all__ = (
    'ChatCallbacks', 'ChatCompletionError', 'Provider',
    'chat_callbacks_minimal',
)
