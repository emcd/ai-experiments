## LLM Chatter

* Theme components.

    - Font families from blog.
    - Color scheme from blog.
    - Support for system/dark/light mode selection.
    - Probably use template themes, but also see:
      https://discourse.holoviz.org/t/how-do-i-use-css-to-modify-panel-widgets-style-like-fontsize-and-color/1534

* GUI Enhancements

    - Change message border on mouse enter/leave.
    - Change conversation indicator background on mouse enter/leave.
    - Float boxes of toggles and action buttons on top of other components.
    - Implement modal dialog for vector store addition, etc....
    - Fade transition for conversation indicators.
      See: https://stackoverflow.com/questions/32269019/text-overflow-fade-css?rq=3
    - Set application title and favicon.
    - Mathematica/Jupyter-style In/Out cell groups.

* Key Bindings

    - `dd` to delete selected message
    - `a` to append to user prompt
    - `i` to insert at beginning of user prompt
    - `G` to switch focus to user prompt
    - `:<n>` to select message `n`
    - `:e #<n>` to switch to conversation `n`
    - `<SPACE>` to activate/deactivate current message
    - `<SHIFT>`+`<SPACE>` to pin/unpin current message
    - `<SHIFT>`+`<ENTER>` to chat
    - `<UP ARROW>` and `<DOWN ARROW>` to navigate messages

* Rewrite in Vue.js and Python FastAPI?

* Support for image generation chats with OpenAI Dall-E and Leonardo.ai API.


## Github Actions Workflows

* Define tool to interact with PR comments.

* Define tool to interact with vector databases for documentation search.

* Define tool to perform documentation searchs against web sites.

* Define tool to generate gists.

* Define tool to submit and update PRs.

* Define agent to use these tools and a command supplied via argument to a
  workflow.

* Start small: generate code locally first. Can use tool to interact with local
  files and respond to comments in chat.
