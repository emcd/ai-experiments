## LLM Chatter

* AI: Agents and Functions

    - Environment, executables, and libraries detection for supported
      functionality.
    - Improve callbacks to record intermediate AI assistant outputs.
    - Use `ctags` to help with code navigation.
    - Use Beautiful Soup to help with web page analysis.
      Replace large JS data blobs, canvas elements, etc... with comments.
    - Role-playing Game Agents: orchestrator, master, player, character

* AI: Models and Providers

    - Environment and executables detection for supported providers.
    - Support local models via Llama.cpp, Ollama, or Vllm.

* Architecture and Design

    - Separate library core and application core.
      Optional logging configuration for library core.
      Optional environment variables processing for library core.
      Configrable application name for library core.
    - Global immutable state DTOs instead of accretive namespaces.
      GUI global state inherits from application global state.
      Dataclasses implementations should be frozen and kw-only
      with async classmethod to prepare fully-initialized DTOs.
    - Async loading of prompt definitions.
    - Async loading of vectorstores. Drop Langchain dependency.
    - Regnerative dictionary, which is immutable except for invocation
      of registered async regeneration function.
      Useful for AI models registries.
    - Visibility functions for wildcard exports of modules.
      (Borrow from 'accretive' package.)

* General

    - Decouple widgets from data in conversation save/restore.
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
    - Fade transition for conversation indicators?
      See: https://stackoverflow.com/questions/32269019/text-overflow-fade-css?rq=3
    - Custom logo for human user in chat history.
    - Gravatar integration for human user logo in chat history?
    - Dropdown menu instead of floating menu for conversation actions.
    - Thin hover-over menu under each message instead of floating menu for
      message actions.
    - Model information in thin bar under each message cohort.
    - Copy button for code blocks embedded in message pane.
      https://github.com/holoviz/panel/issues/6209
      https://github.com/executablebooks/markdown-it-py/issues/324
      https://github.com/ReAlign/markdown-it-copy/blob/master/index.js
      https://github.com/DCsunset/markdown-it-code-copy/blob/master/index.js
      https://github.com/executablebooks/sphinx-copybutton/blob/master/sphinx_copybutton/_static/copybutton.js_t

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

* Prompts

    - Ensure Markdown constructs are used to structure human-facing output.
    - Ensure lists and tables from AI agents are recapitulated.


## Github Actions Workflows

* Define tool to interact with PR comments.

* Define tool to interact with vector databases for documentation search.

* Define tool to perform documentation searchs against web sites.

* Define tool to generate gists.

* Define tool to submit and update PRs.

* Define agent to use these tools and a command supplied via argument to a
  workflow.
