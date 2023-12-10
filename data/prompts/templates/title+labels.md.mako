Please summarize this conversation in five or fewer words, such that the
summary could be used a title or short blurb to identify the conversation if it
is presented as a selectable option in a GUI. You may use emoji in the blurb as
you deem appropriate.

Please also generate up to five labels for this conversation, which denote the
primary semantic elements of it and could be used for searching the
conversation by topic. For example, if you are helping to construct the
grammatical rules for a conlang, you might generate `conlang` and `grammar` as
labels. Or, if you have been asked to write some C++ code, then you might
generate `programming` and `C++` as labels. Or, if you are helping explore
political systems and forms of goverment, then you might generate `political
system` and `government` as labels. Or, if you are being asked to create
prompts for creating natural landscapes with the Midjourney AI art generator,
then you might generate `AI art`, `Midjourney`, `nature`, and `landscape` as
labels. Etc....

The summary and labels must be presented as valid ${variables.format}. Present
only the raw ${variables.format}. Do not wrap it in any formatting directives,
such as Markdown code fences, or include other text with it. Your output is
intended for consumption by a ${variables.format} parser and must therefore be
valid ${variables.format}.

% if fragments and variables.format in { 'JSON', }:
Below is an example.

  % if 'JSON' == variables.format:
${fragments.json}
  % endif
% endif
