## LLM Chatter

* AI: Functions

    - Environment, executables, and libraries detection for supported
      functionality.
    - Improve callbacks to record intermediate AI assistant outputs.
    - Use `ctags` to help with code navigation.
    - Use Beautiful Soup to help with web page analysis.
      Replace large JS data blobs, canvas elements, etc... with comments.
    - Role-playing Game Agents: orchestrator, master, player, character

* AI: Models and Providers

    - Standardized set of text capture callbacks.
    - Environment and executables detection for supported providers.
    - Support Llama 2 models via Llama.cpp, Ollama, or Vllm.

* General

    - Support async loading of vector databases, prompt templates, etc....
    - Support hosting conversation-related resources as relative URLs.
      Allows abstraction from local file system.
    - Rewrite in Vue.js and Python FastAPI?
    - Support for image generation chats with OpenAI Dall-E and Leonardo.ai.
    - Option to record conversations to vector databases.
    - Import conversations from OpenAI shares.

* GUI: Key Bindings

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
    - `<UP ARROW>` and `<DOWN ARROW>` to navigate messages
    - `{` and `}` to navigate code blocks in message

* GUI: Miscellaneous

    - Store icons as SVG files. Make custom `IconButton` and
      `IconToggle` classes, which use these.
      https://discourse.holoviz.org/t/how-to-trigger-re-render-of-template/5799/5
    - Create `ConversationHistory` class to manage history column and status
      row. For reuse in main dashboard and for AI agent trackers.
    - Persist prompt variables.
    - Persist warnings and errors with timestamps.
    - Collapsible messages (eye icon). Automatically collapse on message
      deactivation.
    - Ensure central column content always fits on screen. Hide side panels
      to save space, if necessary.
    - Scroll-to-top and scroll-to-bottom button.
    - Export conversations to static HTML.
    - Implement modal dialog for vector store addition, etc....
    - Toggle for conversation indicator labels display.
    - Search for conversations by title or label.
    - Mathematica/Jupyter-style In/Out cell groups?
      Maybe does not lend itself to selective message activation.
    - Fade transition for conversation indicators?
      See: https://stackoverflow.com/questions/32269019/text-overflow-fade-css?rq=3
    - Custom logo for human user in chat history.
    - Gravatar integration for human user logo in chat history?

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

    - Font families from blog.
    - Color scheme from blog.
    - Support for system/dark/light mode selection.
    - Probably use template themes, but also see:
      https://discourse.holoviz.org/t/how-do-i-use-css-to-modify-panel-widgets-style-like-fontsize-and-color/1534

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
