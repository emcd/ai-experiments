% if 'directory-entries' in variables.mime_type:
* Ignore files in a cache directory, such as `__pycache__`.
* Ignore temporary files, such as Vim swaps (`.swp`, `.swo`, etc...).
* Ignore behavior control files, like `.dockerignore`, `.editorconfig`,
  `.gitignore`, etc.
* Ignore version control metadata (e.g., files under `.git`).
* Ignore files which have been simply classified as data or which are composed
  of non-textual data, such as compiled executables, compressed data, graphical
  images, and binary serializations (Protobuf data, Python pickles, etc...).
* Ignore special entities, if reading from them would likely result in
  non-textual data (block device nodes) or an infinite stream of data (e.g.,
  `/dev/zero`).
* Ignore core dumps, log files, crash reports, and anything which is likely
  generated data (Sphinx HTML output, code coverage reports, etc...).
* Ignore environment files (e.g., `.env`), private keys, and any other file
  which could contain sensitive data.
* Ignore package management lock files (`Pipfile.lock`, `package-lock.json`,
  `.terraform.lock.hcl`, etc...).
* If a filename is unconventional, yet legal, for its corresponding type and
  the file would not be ignored for another reason, then allow it. (E.g.,
  `__.py`)
* If a MIME type is invalid or does not match file extension, but a file would
  not be ignored for another reason, then allow it.
% elif 'text/x-python' in variables.mime_type:
* Analyze the purpose of the module, accounting for explanatory comments and
  the names of entities.
* Make note of imports.
* Create a bullet list of all classes and function definitions and module
  attribute assignments. Use nested lists to reflect nested class and function
  definitions.
* For each listed entity, describe its purpose as part of its list entry.
* For each listed function, describe its mechanics as part of its list entry.
  Additionally, make note of any potential bugs, dangerous practices, or uncaught
  error conditions within the function. Provide code snippets if they are
  instructive in support of your analysis and are dissimilar from other snippets
  provided in earlier analysis.
* If a class or function definition or compound literal appears unterminated at
  end of chunk, then make a note of this, including the fully-qualified name of
  the unterminated entity.
* Note any contradictions between documentations (docstrings, inline comments)
  and the actual mechanics of their corresponding entities.
% elif variables.mime_type.startswith('text/x-script'):
* Analyze the purpose of the file/module, accounting for explanatory comments
  and the names of entities.
* Make note of imports or includes.
* Create a bullet list of file/module-level entities, including syntactic
  constructs, functions, and global variables. Do likewise for the members of
  constructs, using nested lists.
* For each listed entity, describe its purpose as part of its list entry. Also,
  note any todo, hack, or fixme comments.
* For each listed function, note any potential bugs, dangerous practices, or
  insufficient error handling as part of its list entry. Provide code snippets if
  they are instructive in support of your analysis and are dissimilar from other
  snippets provided in earlier analysis.
* If an entity is unterminated at end of chunk, then make a note of this,
  including the fully-qualified name of the unterminated entity.
* Note any contradictions between comments and the actual mechanics of their
  corresponding entities.
% else:
* Analyze the purpose of the file, accounting for introductory remarks,
  metadata, and the names of headings.
* If a table of contents exists, then recapitulate it if you have not already
  done so.
* If a table of contents does not exist, then build one from headings, nesting
  subordinate or weaker headings as appropriate. Keep in mind that this table may
  need to be built across multiple chunks.
* List each topic, title, or heading and describe its content in a level of
  detail which sufficiently captures any arguments, nuances, or points explored
  within it.
* If an entity is unterminated at end of chunk, then make a note of
  fully-qualified heading to which it probably belongs.
* Note any content which may be counterfactual within the context of the
  discourse or which may contradict other content.
* State any clarifications that would be useful.
% endif
% if variables.instructions:
% for instruction in variables.instructions:
* ${instruction}
% endfor
% endif

Please ensure that the analysis is thorough and accounts for any specific
details mentioned in the instructions.
