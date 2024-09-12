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
* @gitignore: Removes entries ignored by relevant '.gitignore' files.
* +vcs: Removes entries related to VCS configuration and state,
        like the '.git' directory. Can take an optional argument, after a
        colon, which is a comma-separated list of matchers. The defualt,
        '+vcs', is equivalent to '+vcs:git,hg,svn'.
'''

_directory_recursion_description = '''
Recursively list subdirectories?

If this flag is set, then it is recommended to also enable filters like
'@gitignore' and '+vcs' to prevent unnecessary results from being returned.
'''

_update_content_option_description = '''
File update behavior option.

Default behavior is to create file if it does not exist and to truncate file
for content replacement.

Choices:
* append: Append to file rather than truncate.
* error-if-exists: Do not update file if it already exists.
'''

acquire_content_argschema = {
    'type': 'object',
    'properties': {
        'location': {
            'type': 'string',
            'description': 'URL or local filesystem path to be read.'
        },
    },
    'required': [ 'location' ],
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
                'description': _directory_filter_description
            },
            'default': [ '@gitignore', '+vcs' ],
        },
        'recurse': {
            'type': 'boolean',
            'description': _directory_recursion_description,
            'default': True
        }
#        },
#        'file_size_maximum': {
#            'type': 'integer',
#            'description':
#                'Do not list regular files larger than this many bytes.',
#            'default': 40000
#        }
    },
    'required': [ 'location' ],
}

update_content_argschema = {
    'type': 'object',
    'properties': {
        'location': {
            'type': 'string',
            'description': 'URL or local path of the file to be written.'
        },
        'content': {
            'type': 'string',
        },
        'options': {
            'type': 'array',
            'items': {
                'type': 'string',
                'enum': [ 'append', 'error-if-exists' ],
                'description': _update_content_option_description,
            },
            'default': [ ],
        },
    },
    # TODO? Require 'options' for OpenAI strict schema.
    'required': [ 'location', 'contents' ],
}
