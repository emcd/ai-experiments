## 1. Design Approval

- [x] 1.1 Review and approve the `ModelAddress` and `ModelDescriptor` split.
- [x] 1.2 Confirm client-owned, genus-oriented operation services as the primary
  operation access path.
- [x] 1.3 Confirm that compatibility adapters are not part of the completed end
  state.

## 2. Interfaces

- [x] 2.1 Add immutable model reference types for `ModelAddress` identity and
  `ModelDescriptor` runtime model data.
- [x] 2.2 Add client-owned operation protocols grouped by model genus or
  capability, starting with converser operations for controls, messages,
  invocations, serialization, tokenization, and v0 conversations.
- [x] 2.3 Update model/client/provider protocols so operation ownership is
  explicit and broad model-bound processor requirements are no longer required
  for new code.

## 3. Provider Implementations

- [x] 3.1 Implement OpenAI client-owned converser services using existing
  behavior.
- [x] 3.2 Implement Anthropic client-owned converser services using existing
  behavior.
- [x] 3.3 Preserve provider-specific attribute typing inside provider modules.
- [x] 3.4 Preserve model integration and model discovery semantics.

## 4. Call-Site Migration

- [x] 4.1 Update provider helpers to call client-owned services instead of
  `model.*_processor` properties.
- [x] 4.2 Update GUI chat, invocation, title generation, and token-counting paths
  to call client-owned services.
- [x] 4.3 Update invocable ensembles that call `converse_v0`, `tokenizer`, or
  `serde_processor`.
- [x] 4.4 Remove obsolete model-bound processor classes and model properties from
  the completed end state.

## 5. Documentation

- [x] 5.1 Add `sources/aiwb/providers/README.md` describing provider model
  identity, model descriptors, operation ownership, and migration boundaries.
- [x] 5.2 Update any nearby README files if implementation touches other
  documented subtrees.

## 6. Validation

- [x] 6.1 Run `hatch --env develop run pyright`.
- [x] 6.2 Run targeted Ruff over changed Python files.
- [x] 6.3 Run `hatch run aiwb-application inspect`.
- [ ] 6.4 Smoke test GUI conversation selection and a new conversation.
- [ ] 6.5 Smoke test at least one provider conversation and invocation flow when
  API credentials and credits are available.

Note: Provider smoke testing is deferred until OpenAI model metadata is refreshed
and a live chat with tool calls can be exercised.
