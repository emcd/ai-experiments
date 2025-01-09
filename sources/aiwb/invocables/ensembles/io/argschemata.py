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

_acquire_content_number_lines_description = '''
Return dictionary, mapping line number to line content?

When true, content is returned as a dictionary where keys are
line numbers (1-based) and values are the lines without their
trailing newlines. This format is designed to aid partial
content updates.

When false, content is returned as a string, preserving all
newlines.
'''

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

_update_content_partial_content_description = '''
Content to insert or replace with.

For INSERT and REPLACE operations:
* Required
* Must be a string (not a list or other type)
* Use \\n to separate multiple lines
* No trailing newline needed unless you want to:
  - Add a newline at the end of the file
  - Add extra blank lines after the content
* Examples:
  - '    x = 42'         # Inserts/replaces single line
  - '    x = 42\\n    y = 84'  # Inserts/replaces two lines
  - '    x = 42\\n'      # Inserts/replaces and adds newline
* For multiple contiguous insertions, combine into single operation
* Empty string creates empty line

For DELETE operations:
* Not used (will be ignored)
'''

_update_content_partial_end_description = '''
Last line number of the operation.

For INSERT operations:
* Not used (will be ignored)

For DELETE and REPLACE operations:
* Last line to be modified (inclusive)
* Must be greater than or equal to start line
* Must be a valid line number (1 through last line)
* Example: start=1, end=1 affects single line
'''

_update_content_partial_return_description = '''
Return entire content after successful update?

When true, includes complete content of file with line numbers after the
update as part of the success response. This makes it easy to verify the
changes or use the result in subsequent operations.

When false, only returns basic operation information in success response.
'''

_update_content_partial_start_description = '''
First line number of the operation.

For INSERT operations:
* Specifies the line after which content will be inserted
* Use 0 to insert at the beginning of the file
* Content will appear on new lines after the specified line
* For multiple insertions at same position, combine into single operation

For DELETE and REPLACE operations:
* First line to be modified
* Must be a valid line number (1 through last line)
* When used with end, forms an inclusive range
'''

_update_content_operation_description = '''
Type of partial content update operation.

Choices:
* insert: Insert new content at the specified position
* delete: Remove content between start and end lines
* replace: Replace content between start and end lines with new content

Notes:
* Operations are applied in order of increasing line numbers
* Multiple operations must not affect overlapping lines
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
        'number-lines': {
            'type': 'boolean',
            'description': _acquire_content_number_lines_description,
            'default': False,
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
                        'description': _update_content_operation_description,
                    },
                    'start': {
                        'type': 'integer',
                        'minimum': 0,
                        'description':
                            _update_content_partial_start_description,
                    },
                    'end': {
                        'type': 'integer',
                        'minimum': 1,
                        'description':
                            _update_content_partial_end_description,
                    },
                    'content': {
                        'type': 'string',
                        'description':
                            _update_content_partial_content_description,
                    },
                    'return-content': {
                        'type': 'boolean',
                        'description':
                            _update_content_partial_return_description,
                        'default': True
                    },
                },
                'required': ['opcode', 'start'],
                'allOf': [
                    {
                        'if': {
                            'properties': {
                                'opcode': {'enum': ['insert', 'replace']}
                            }
                        },
                        'then': {
                            'required': ['content']
                        }
                    },
                    {
                        'if': {
                            'properties': {
                                'opcode': {'enum': ['delete', 'replace']}
                            }
                        },
                        'then': {
                            'required': ['start', 'end']
                        }
                    }
                ]
            },
            'minItems': 1,
            'description': 'Sequence of modification operations to apply'
        }
    },
    'required': ['location', 'operations']
}
