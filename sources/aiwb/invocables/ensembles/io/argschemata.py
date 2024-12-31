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

_update_content_context_description = '''
Context for locating where to apply a partial content update.

The before and after contexts help locate where the operation should be
applied:
* before: null means beginning of file, otherwise lines that must appear before
  operation
* after: null means end of file, otherwise lines that must appear after
  operation
* nth_match: Which occurrence to match (1-based, defaults to 1, only needed
  when identical contexts appear multiple times in the file)

Contexts can be multiline strings. Including more lines in a context will make
the match more specific. For example:
* "def example():" matches any function named example
* "def example():\\n    \"\"\"Example function.\"\"\"" matches only functions
  with that specific docstring

For INSERT operations:
* if after context is provided, it must immediately follow before context

For DELETE and REPLACE operations:
* gap between contexts defines what will be modified

Note: The tool preserves newlines exactly as provided in both contexts and
content. If you want a trailing newline in your content, you must include it
explicitly.
'''

_update_content_operation_description = '''
Type of partial content update operation.

Choices:
* insert: Insert new content at the specified position
* delete: Remove content between before and after contexts
* replace: Replace content between before and after contexts with new content
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

update_content_partial_argschema = {
    'type': 'object',
    'properties': {
        'location': {
            'type': 'string',
            'description': 'URL or local path of the file to be modified.'
        },
        'operations': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'opcode': {
                        'type': 'string',
                        'enum': ['insert', 'delete', 'replace'],
                        'description': _update_content_operation_description
                    },
                    'context': {
                        'type': 'object',
                        'properties': {
                            'before': {
                                'type': ['string', 'null'],
                                'description': (
'Context that must appear before operation point (null = beginning of file). '
'Can be multiline.' ),
                            },
                            'after': {
                                'type': ['string', 'null'],
                                'description': (
'Context that must appear after operation point (null = end of file). '
'Can be multiline.' ),
                            },
                            'nth_match': {
                                'type': 'integer',
                                'description': (
'Which occurrence to match (1-based, only needed for repeated contexts)' ),
                                'minimum': 1,
                                'default': 1
                            }
                        },
                        'required': ['before', 'after'],
                        'description': _update_content_context_description
                    },
                    'content': {
                        'type': 'string',
                        'description': (
'Content to insert or replace with (not used for delete operations). '
'Include explicit newlines where desired.' ),
                    }
                },
                'required': ['opcode', 'context']
            },
            'minItems': 1,
            'description': 'Sequence of modification operations to apply'
        }
    },
    'required': ['location', 'operations']
}
