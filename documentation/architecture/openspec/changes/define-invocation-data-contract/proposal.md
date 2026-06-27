# Change: Define Invocation Data Contract

## Why

The current invocation data layer mixes four concerns in the same data structures and channels: provider replay state, application invocable identity, GUI display payload, and positional result linkage. This mixing is the root cause of a documented leak surface across `sources/aiwb/{invocables,providers,gui,messages}/` and a hard blocker for three-layer tool-source support (local application tools, MCP-sourced tools, provider-native/server-side tools) and OpenAI Responses API work.

The application currently reads provider-shaped envelopes directly to drive dedup, deactivation, elision, and display. Adding MCP-sourced tools (MCP is **not** a provider-side tool-call protocol; MCP servers present tools to the harness, which then presents them via the model provider's standard tool-call mechanism) and provider-native/server-side tools (`code_interpreter`, `file_search`, `web_search`, equivalents) to the harness requires a normalized, provider-neutral contract on the application side.

## What Changes

- **ADDED** `invocation-data-contract` capability spec: normalized `InvocationRequest`, `InvocationResult`, and `InvocationSupplement` records; provider-neutral correlation IDs minted by the harness; persistence and rehydration semantics; GUI display projection boundary.
- **MODIFIED** `provider-model-operations` capability spec: the "Invocations are prepared or extracted" requirement is updated so client-owned converser services read from and emit to normalized records rather than driving application behavior from provider-shaped envelopes.
- **Pre-R2 cleanup (referenced, not a contract requirement)**: OpenAI legacy `function_call` paths are removed before this contract lands. Completed on `providers` branch as dispatch commits `a31afb5` (`Remove OpenAI legacy function_call and retire deprecated model families`) and `32694f5` (`gpt-4o* family deletes`), per `todos/providers/2`. The contract does **not** preserve `InvocationsSupportLevels.Single` paths; the OpenAI provider implementation can be assumed to emit only modern `tool_calls` for tool-call replay.
- **Legacy persistence policy (deployment decision, not a contract requirement)**: persisted conversations with legacy `function_call` records in `model_context.supplement` will not replay tool-call history after the provider cleanup. The rewrite/drop policy for those records is tracked at `todos/providers/8` and remains a separate pre/post-R2 follow-on. GUI-side legacy paths (`gui/persistence.py:366-388` save normalization, `messages/core.py:279-290` very-old restore) are not provider-layer and require coordinated FE Web follow-on (suggested as a new `todos/web/<n>`).

## Impact

- Affected specs:
  - `invocation-data-contract` (new).
  - `provider-model-operations` (modified: invocations-prepared-or-extracted requirement).
- Affected code (anticipated implementation touch points, listed for review only — no code changes in this proposal):
  - `sources/aiwb/invocables/core.py` — `Invoker`, `Context`, `Deduplicator`.
  - `sources/aiwb/providers/core.py` — `InvocationRequest` reshaped; new `InvocationResult`, `InvocationSupplement` types.
  - `sources/aiwb/providers/interfaces.py` — `ConverserOperations.execute_invocation` and `requests_from_canister` signatures adjusted to read from normalized records.
  - `sources/aiwb/providers/clients/openai/conversers.py` — `execute_invocation`, `requests_from_canister`, `_reconstitute_invocations` rewritten against normalized records; legacy `InvocationsSupportLevels.Single` paths deleted.
  - `sources/aiwb/providers/clients/anthropic/conversers.py` — same shape of changes.
  - `sources/aiwb/providers/utilities.py` — `invocation_requests_from_canister` reads from normalized records.
  - `sources/aiwb/gui/actions.py` — `_deactivate_duplicate_invocations` uses correlation IDs; positional `result_index = i + j + 1` replaced.
  - `sources/aiwb/gui/invocables.py`, `sources/aiwb/gui/updaters.py`, `sources/aiwb/gui/persistence.py` — display projection boundary.
  - `sources/aiwb/messages/core.py` — `restore_canister` rehydration updated.
- Cross-lane coordination:
  - `providers@ai-experiments` co-author on the proposal per earlier confirmation; review request for provider replay/supplement semantics and OpenAI Responses API reservations before calling ready.
  - `web@ai-experiments` review request for GUI display projection, invocation/result linkage, and browser/display implications before calling ready.
- Open questions (surfaced in `design.md`, not resolved in this proposal unless an obvious default exists):
  - Provider-native tool opt-in granularity (per-tool / per-model / global).
  - MCP correlation ID minting (harness-minted always vs adapting MCP-supplied correlation primitives if present).
  - `silent_extraction_failure` scope (broad error-policy contract vs follow-on).
  - Typed `Context.supplements` accessor (include in R2 vs defer).
- Migration plan (in `design.md`): phased, with the pre-R2 OpenAI legacy `function_call` removal preceding contract scaffolding, and a mock multi-tool invocation smoke (per `todos/invocables/3`) gating the contract change.

## Out of scope

- Full Pydantic migration (covered separately in `sources/aiwb/invocables/README.md`).
- New ensemble / invocable discovery mechanisms.
- Controls package redesign (separate coordination under `coordination/controls/1`).
- OpenAI Responses API implementation (separate work item under `todos/providers/3`).
- MCP server-side implementation (separate work item).
- Code refactors unrelated to the contract (e.g., wholesale GUI reorg).
