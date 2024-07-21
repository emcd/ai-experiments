Please summarize this conversation in five or fewer words, such that the
summary could be used a title or short blurb. You are encouraged, but not
required, to use emoji in place of one or two words, provided that the
spelled-out words can sufficiently summarize the conversation by themselves.
For example, if the conversation is about rolling a High Elf Wizard character
in Dungeons and Dragons, then you might generate
`D&D: High Elf Wizard 🧙‍♂️🎲` as the title. Or, if the conversation is
about developing a pantheon for a LitRPG world, then you might generate
`🌌 LitRPG: World-Building: Deities ⚡🌟` as the title. Or, if the conversation
is about updating the documentation for an AI workbench software project,
then you might generate `🤖 Workbench: Docs Update 📄` as the title.

Pay attention to the entire conversation and do not assume that the initial
user message reflects the true nature of the conversation. Also, if a user
message within the conversation history contains a request for review or
recapitulation of a topic or collection of contents, then please focus on any
additional action requested by the user rather than the request for review or
recapitulation itself. Avoid using "overview", "recap", "summary", or similar
words in the generated title, unless the singular nature of the conversation is
a review of some topic or collection of contents and contains no additional
request for specific analysis or creative output. For example, if the initial
user message asks for the contents of a directory to be read and summarized,
then asks for a representation of the directory layout, and a subsequent
AI-driven tool call reveals that the directory contains source code for a
Python data structures library, then you might generate
`Python Library: Directory Layout 📂` as the title.

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
