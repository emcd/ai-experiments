## LLM Chatter

* Theme components with font families used in blog.

* Theme components with color scheme used in blog.

* Change message border on mouse enter/leave.

* Change conversation indicator background on mouse enter/leave.

* Find way for boxes of toggles or action buttons to float on top of other
  components.

* Add support for system/dark/light mode selection.

* Vim key bindings:

    - `dd` to delete selected message
    - `a` to append to user prompt
    - `i` to insert at beginning of user prompt
    - `G` to switch focus to user prompt
    - `:<n>` to select message `n`
    - `:e #<n>` to switch to conversation `n`

* Other key bindings:

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
