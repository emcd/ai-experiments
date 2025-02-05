* AI: Agents
    - Programming Agents: orchestrator, designer, programmer, reviewer
    - Role-playing Game Agents: orchestrator, master, player, character

* AI: Invocables (aka. "functions" or "tools")

    - Detection of environment, executables, and libraries for functions.
    - Improve callbacks to record intermediate AI assistant outputs.
    - Tool to interact with PR comments.
    - Tool to interact with vector databases for documentation search.
    - Tool to perform documentation searchs against web sites.
    - Tool to generate gists.
    - Tool to submit and update PRs.
    - Use `ctags` to help with code navigation.
    - Use Beautiful Soup to help with web page analysis.
      Replace large JS data blobs, canvas elements, etc... with comments.

* AI: Models and Providers

    - Environment and executables detection for supported providers.
    - Support local models via Llama.cpp, Ollama, or Vllm.
    - OpenAI: Add usage reporting:
      https://cookbook.openai.com/examples/how_to_stream_completions#4-how-to-get-token-usage-data-for-streamed-chat-completion-response

* Architecture and Design

    - Refactor AI providers `interfaces` module into subpackage.
    - `ConversationsIndex` and `Conversation` classes.
    - Rework GUI to pass immutable conversation object through functions
      instead of components namespace. Cannot pass GUI globals object, since
      each conversation has a mutated copy of the conversation-related
      components.
    - Finish decoupling widgets from data in conversation save/restore.
    - Use `absent` object instead of `None` for optional arguments
      with no default.
    - Use immutable dataclasses and protocol classes wherever possible.

* Documentation

    - Architecture diagrams: overall, invocables, providers.
    - Conventions and standards.
    - Add missing docstrings to classes and functions.

* General

    - Support hosting conversation-related resources as relative URLs.
      Allows abstraction from local file system.
      (FastAPI server implemented. Still need to implement routes.)
    - Support for image generation chats with OpenAI Dall-E and Leonardo.ai.
    - Option to record conversations to vector databases.
    - Import conversations from OpenAI shares or account data exports.

* GUI: Key Bindings

    - https://github.com/holoviz/panel/issues/3193
    - `dd` to delete selected message
    - `a` to append to user prompt
    - `i` to insert at beginning of user prompt
    - `G` to switch focus to user prompt
    - `:<n>` to select message `n`
    - `:e #<n>` to switch to conversation `n`
    - `<SPACE>` to activate/deactivate current message
    - `<SHIFT>`+`<SPACE>` to pin/unpin current message
    - Customizable chat completion activation:
      ChatGPT mode: `<ENTER>`
      Mathematica/Jupyter mode: `<SHIFT>`+`<ENTER>`
      Slack alternative mode: `<CONTROL>`+`<ENTER>`
      (support implemented; needs settings page)
    - `<UP ARROW>` and `<DOWN ARROW>` to navigate messages
    - `{` and `}` to navigate code blocks in message

* GUI: Miscellaneous

    - Refactor 'classes' module into 'widgets', 'messages', and
      'conversations'.
    - Create `ConversationHistory` class to manage history column and status
      row. For reuse in main dashboard and for AI agent trackers.
    - Persist prompt variables.
    - Persist warnings and errors with timestamps.
    - Collapsible messages (eye icon). Automatically collapse on message
      deactivation.
    - Ensure central column content always fits on screen. Hide side panels
      to save space, if necessary.
    - Scroll-to-bottom button.
    - Export conversations to static HTML.
    - Implement modal dialog for vector store addition, etc....
    - Toggle for conversation indicator labels display.
    - Search for conversations by title or label.
    - Mathematica/Jupyter-style In/Out cell groups.
      Message clusters: user prompt, tool calls, and AI response.
    - Custom logo for human user in chat history.
    - Gravatar integration for human user logo in chat history?
    - Thin hover-over menu under each message instead of floating menu for
      message actions.
    - Model information in thin bar under each message cohort.

* GUI: Page Header

    - Hamburgers/rotated arrows to collapse left and right sidebars.
    - Activity indicator with dropdown list of all current activities.
    - Warning indicator with dropdown list of all current warnings.
    - Error indicator with dropdown list of all current errors.
    - Token count versus limit?
    - Selector for system/dark/light mode.
    - Selector for main theme.
    - Selector for code theme.

* GUI: Theme components.

    - Support for system/dark/light mode selection.
    - Color scheme from blog + Material Solarized.
      https://github.com/emcd/emcd.github.io/blob/source/themes/mine/assets/css/theme.css
      https://material-theme.com/docs/reference/color-palette/
    - Button titles in sans serif font of sufficient weight.

* Messages

    - Cohorts: Parallel responses from one or more AIs.
    - Clusters: Rounds of conversations.

* Prompts

    - Ensure Markdown constructs are used to structure human-facing output.
    - Ensure lists and tables from AI agents are recapitulated.
