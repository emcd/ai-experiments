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


''' Prompts to support AI agents for I/O. '''


common_code_instructions = [ ]

dirents_instructions = [
    '''
Ignore files in a cache directory, such as `__pycache__`.''',
    '''
Ignore temporary files, such as Vim swaps (`.swp`, `.swo`, etc...).''',
    '''
Ignore behavior control files, like `.dockerignore`, `.editorconfig`,
`.gitignore`, etc....''',
    '''
Ignore version control metadata (e.g., files under `.git`).''',
    '''
Ignore files which have been simply classified as data or which are composed of
non-textual data, such as compiled executables, compressed data, graphical
images, and binary serializations (Protobuf data, Python pickles, etc...).''',
    '''
Ignore special entities, if reading from them would likely result in
non-textual data (block device nodes) or an infinite stream of data (e.g.,
`/dev/zero`).''',
    '''
Ignore core dumps, log files, crash reports, and anything which is likely
generated data (Sphinx HTML output, code coverage reports, etc...).''',
    '''
Ignore environment files (e.g., `.env`), private keys, and any other file which
could contain sensitive data.''',
    '''
Ignore package management lock files (`Pipfile.lock`, `package-lock.json`,
`.terraform.lock.hcl`, etc...).''',
    '''
If a MIME type is invalid or does not match file extension, but a file would
not be ignored for another reason, then allow it.''',
]

generic_code_instructions = [
    '''
Analyze the purpose of the file/module, accounting for explanatory comments and
the names of entities.''',
    '''
Make note of imports or includes.''',
    '''
Create a bullet list of file/module-level entities, including syntactic
constructs, functions, and global variables. Do likewise for the members of
constructs, using nested lists.''',
    '''
For each listed entity, describe its purpose as part of its list entry. Also,
note any todo, hack, or fixme comments.''',
    '''
For each listed function, note any potential bugs, dangerous practices, or
insufficient error handling as part of its list entry. Provide code snippets if
they are instructive in support of your analysis and are dissimilar from other
snippets provided in earlier analysis.''',
    '''
If an entity is unterminated at end of chunk, then make a note of this,
including the fully-qualified name of the unterminated entity.''',
    '''
Note any contradictions between comments and the actual mechanics of their
corresponding entities.''',
    *common_code_instructions,
]

generic_instructions = [
    '''
Analyze the purpose of the file, accounting for introductory remarks, metadata,
and the names of headings.''',
    '''
If a table of contents exists, then recapitulate it if you have not already
done so.''',
    '''
If a table of contents does not exist, then build one from headings, nesting
subordinate or weaker headings as appropriate. Keep in mind that this table may
need to built across multiple chunks.'''
    '''
List each topic, title, or heading and describe its content in a level of
detail which sufficiently captures any arguments, nuances, or points explored
within it.''',
    '''
If an entity is unterminated at end of chunk, then make a note of
fully-qualified heading to which it probably belongs.''',
    '''
Note any content which may be counterfactual within the context of the
discourse or which may contradict other content.''',
    '''
State any clarifications that would be useful.''',
]

python_code_instructions = [
    '''
Analyze the purpose of the module, accounting for explanatory comments and the
names of entities.''',
    '''
Make note of imports.''',
    '''
Create a bullet list of all classes and function definitions and module
attribute assignments. Use nested lists to reflect nested class and function
definitions.''',
    '''
For each listed entity, describe its purpose as part of its list entry.''',
    '''
For each listed function, describe its mechanics as part of its list entry.
Additionally, make note of any potential bugs, dangerous practices, or uncaught
error conditions within the function. Provide code snippets if they are
instructive in support of your analysis and are dissimilar from other snippets
provided in earlier analysis.''',
    '''
If a class or function definition or compound literal appears unterminated at
end of chunk, then make a note of this, including the fully-qualified name of
the unterminated entity.''',
    '''
Note any contradictions between documentations (docstrings, inline comments)
and the actual mechanics of their corresponding entities.''',
    *common_code_instructions,
]


def select_default_instructions( mime_type ):
    if 'directory-entries' in mime_type:
        instructions = dirents_instructions
    elif mime_type in ( 'text/x-python', 'text/x-script.python', ):
        instructions = python_code_instructions
    elif mime_type.startswith( 'text/x-script' ):
        instructions = generic_code_instructions
    else: instructions = generic_instructions
    # TODO: Consider model-specific instruction list formats to maximize
    #       prompt adherence.
    return ' '.join( map( str.strip, instructions ) )
