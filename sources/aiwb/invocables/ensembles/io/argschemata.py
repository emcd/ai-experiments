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


''' Argument schemata for I/O operations. '''


_directory_filter_description = '''
Filter to apply on directory listing.

Choices:
* gitignore: Removes entries not allowed by relevant '.gitignore' files.
* vcs: Removes entries related to VCS configuration, like the '.git' directory.
'''

_directory_recursion_description = '''
Recursively list subdirectories?

If this flag is set, then it is recommended to also enable filters like
'gitignore' and 'vcs' to prevent unnecessary results from being returned.
'''

instructions_mode_argschema = {
    'type': 'string',
    'description': '''
Replace or supplement default instructions of AI agent with given
instructions? ''',
    'enum': [ 'replace', 'supplement' ],
    'default': 'supplement',
}

instructions_argschema = {
    'type': 'object',
    'description': '''
Special instructions to AI agent to replace or supplement its default
instructions. If not supplied, the agent will use only its default
instructions. ''',
    'properties': {
        'mode': instructions_mode_argschema,
        'instructions': {
            'type': 'string',
            'description': '''
Analysis instructions for AI. Should not be empty in replace mode. '''
        },
    },
}

acquire_contents_argschema = {
    'type': 'object',
    'properties': {
        'source': {
            'type': 'string',
            'description': 'URL or local filesystem path to be read.'
        },
        'control': instructions_argschema,
    },
    'required': [ 'source' ],
}

survey_directory_argschema = {
    'type': 'object',
    'properties': {
        'location': {
            'type': 'string',
            'description': 'URL or local path of directory to be listed.'
        },
        'filters': {
            'type': 'array',
            'items': {
                'type': 'string',
                'description': _directory_filter_description,
                'enum': [ 'gitignore', 'vcs' ]
            },
            'default': [ 'gitignore', 'vcs' ],
        },
        'recursive': {
            'type': 'boolean',
            'description': _directory_recursion_description,
            'default': True
        },
#        'file_size_maximum': {
#            'type': 'integer',
#            'description':
#                'Do not list regular files larger than this many bytes.',
#            'default': 40000
#        },
        'return_directories': {
            'type': 'boolean',
            'description': 'Include directories in results?',
            'default': True
        },
        'return_special_entities': {
            'type': 'boolean',
            'description':
                'Include device nodes, named pipes, etc... in results?',
            'default': True
        },
        'return_symlinks': {
            'type': 'boolean',
            'description': 'Include symlinks in results?',
            'default': True
        }
    },
    'required': [ 'location' ],
}

update_contents_argschema = {
    'type': 'object',
    'properties': {
        'location': {
            'type': 'string',
            'description': 'Location of the file to be written.'
        },
        'contents': {
            'type': 'string',
        },
        'mode': {
            'type': 'string',
            'enum': [ 'append', 'truncate' ],
            'default': 'truncate',
        },
    },
    # TODO? Require 'mode' for OpenAI strict schema.
    'required': [ 'location', 'contents' ],
}
