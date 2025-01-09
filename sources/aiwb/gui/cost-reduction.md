# Cost Reduction Strategies

## Tool Use Deduplication

Status: Implemented

The workbench deduplicates tool results based on registered handlers. Key aspects:
- Opt-in via deduplicator registration
- Preserves pinned messages
- Handles supersession relationships (e.g., read superseding write)
- Runs after each tool use in the assistant-tool loop

## Cache Keepalive

Status: Proposed

Maintain Anthropic's server-side caching through periodic completions during user activity:

### Core Mechanism
- Monitor user activity via:
  - Text input widgets
  - Markdown editors
  - Clipboard operations
- Start/reset timer on activity
- Generate keepalive completion at ~80% of cache lifetime
- Store results in collapsible sidebar card

### Analytical Prompts
Rotate through prompts like:
- Summarize conversation thus far
- List unresolved questions
- Identify key decisions/conclusions
- Suggest next steps

### Initial Implementation
1. Add enable/disable checkbox near provider selection
2. Use Panel's existing input monitoring
3. Fixed percentage of cache lifetime
4. Basic collapsible results display
5. Simple prompt rotation

### Future Enhancements
1. Configurable activity thresholds
2. Separate cost tracking and display
3. Result categorization
4. Result promotion to main conversation
5. Adaptive prompt selection based on usage patterns
6. Cost control settings

## Improved Summarization

Status: Proposed Enhancement

Enhance existing summarization with deduplication awareness:

### Current Behavior
- User selects summarization prompt
- Toggle compresses previous conversation
- Deactivates messages before summary
- Preserves pinned messages

### Proposed Enhancements
1. Preserve tool results that existed before summary
2. Continue deduplication on new tool results
3. Track token usage and suggest summarization at configurable threshold (e.g., 40-50% of context window)

### Integration Points
- Use existing deduplication logic
- Maintain current pinning behavior
- Preserve complete tool result context for summary