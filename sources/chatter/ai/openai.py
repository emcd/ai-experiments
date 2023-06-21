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


from . import base as __


name = 'OpenAI'


def provide_models( ):
    from collections import defaultdict
    from operator import itemgetter
    import openai
    # TODO: Only call API when explicitly desired. Should persist to disk.
    model_names = sorted( map(
        itemgetter( 'id' ),
        openai.Model.list( ).to_dict_recursive( )[ 'data' ] ) )
    sysprompt_honor = defaultdict( lambda: False )
    sysprompt_honor.update( {
        #'gpt-3.5-turbo-0613': True,
        #'gpt-3.5-turbo-16k-0613': True,
        'gpt-4': True,
        'gpt-4-32k': True,
        'gpt-4-0613': True,
        'gpt-4-32k-0613': True,
    } )
    tokens_limits = defaultdict( lambda: 4096 ) # Some are 4097... _shrug_.
    tokens_limits.update( {
        'code-davinci-002': 8000,
        'gpt-3.5-turbo-16k': 16384,
        'gpt-3.5-turbo-16k-0613': 16384,
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-4-0613': 8192,
        'gpt-4-32k-0613': 32768,
    } )
    return {
        model_name: {
            'honors-system-prompt': sysprompt_honor[ model_name ],
            'tokens-limit': tokens_limits[ model_name ],
        }
        for model_name in model_names
    }


def run_chat( model, messages, **controls ):
    from openai import ChatCompletion, OpenAIError
    try:
        response = ChatCompletion.create(
            messages = messages, model = model, **controls )
        return response.choices[ 0 ].message.content
    except OpenAIError as exc:
        raise __.ChatCompletionError( f"Error: {exc}" ) from exc


def run_streaming_chat( model, messages, **controls ):
    from openai import ChatCompletion, OpenAIError
    try:
        response = ChatCompletion.create(
            messages = messages, model = model, stream = True, **controls )
        initial_chunk = next( response )
        # TODO? Validate initial chunk.
        for chunk in response:
            delta = chunk.choices[ 0 ].delta
            if not delta: break
            yield delta[ 'content' ]
    except OpenAIError as exc:
        raise __.ChatCompletionError( f"Error: {exc}" ) from exc
