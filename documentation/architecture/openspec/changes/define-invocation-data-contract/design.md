# Design: Define Invocation Data Contract

## Context

The current invocation data layer mixes four concerns in the same data structures and channels: provider replay state, application invocable identity, GUI display payload, and positional result linkage. This mixing couples `sources/aiwb/{invocables,providers,gui,messages}/` directly to provider-specific tool-call protocol shapes and blocks the addition of MCP-sourced tools and provider-native/server-side tools. A first-pass leak-surface inventory is captured at `ai-experiments:artifacts/invocables/1` (R1 synthesis, closed); provider review audit trail at `ai-experiments:artifacts/invocables/2`.

The proposal affects cross-cutting architecture (multiple services, new data model, GUI display projection change) and is therefore cross-cutting work. Pre-R2 cleanup of OpenAI legacy `function_call` paths (per `todos/providers/2`) precedes the contract implementation; the contract does not preserve those paths.

## Goals

- **G1.** Normalize the application-side view of invocation requests and results so the application never reads provider-shaped envelopes to drive dedup, deactivation, elision, or display.
- **G2.** Mint provider-neutral correlation IDs at the harness boundary. IDs are stable across persistence and are the application-facing linkage primitive across dedup, deactivation, elision, and display.
- **G3.** Replace history-position result linkage (`result_index = i + j + 1` at `sources/aiwb/gui/actions.py:283`) with correlation-ID linkage.
- **G4.** Define persistence and rehydration semantics so normalized records survive conversation storage and replay cleanly across providers and across MCP server changes.
- **G5.** Preserve provider-native tool-use envelopes and provider-issued opaque IDs/state (response IDs, output item IDs, opaque session references for layer 3 native tools) as supplemental data attached to the application-layer correlation ID. Used only for same-provider replay or session continuation. Opaque to application-local invocation, dedup, and display correlation.
- **G6.** Define a GUI display projection boundary so raw provider replay envelopes do not leak into the user-visible invocation display unless the user explicitly opts into a "show details" view.
- **G7.** Reserve compatibility with local application tools, MCP-sourced tools, and provider-native/server-side tools. Each `InvocationRequest` carries its `InvocationProcessor` (Application or Provider) so downstream layers can render and persist differently per processor. Provenance distinctions within Application (local vs MCP) live at the registry/layer level.
- **G8.** Remove OpenAI legacy `function_call` paths before this contract lands, so the contract does not need to preserve `InvocationsSupportLevels.Single`.

## Non-Goals

- Full Pydantic migration (separately documented in `sources/aiwb/invocables/README.md`).
- Wholesale GUI redesign; the contract change is incremental.
- New ensemble / invocable discovery mechanisms.
- Controls package redesign (cross-cutting, owned by Coordinator/advisor per `coordination/controls/1`).
- OpenAI Responses API implementation (`todos/providers/3`, separate).
- MCP server-side implementation (separate work item).
- New persistence backends or storage format changes.

## Decisions

### D1. Invocation processor dichotomy

Tools presented to language models originate from two processors:
- **Application processor** — covers both local application tools (`Invoker`/`Invocable` registered in `sources/aiwb/invocables/core.py`) and MCP-sourced tools (MCP servers presenting tools to the harness, which then presents them to the model via the model provider's standard tool-call mechanism). MCP is not a provider-side tool-call protocol. For Application tools, the harness supplies the JSON schema in the tool declaration.
- **Provider processor** — covers provider-native/server-side tools (`code_interpreter`, `file_search`, `web_search` and equivalents). The provider maintains the schema server-side; the harness emits only the tool name in the tool declaration.

Provenance distinctions within the Application category (local application vs MCP-sourced) live at the registry/layer level, not on every `InvocationRequest`. The processor discriminator is the per-invocation data-model concern.

Per-processor implications:
- For Application, the application owns invocation; correlation IDs are minted by the harness.
- For Provider, the application does not run the tool; the harness emits the tool name and the provider runs it. Correlation IDs are still minted by the harness; provider-issued IDs live in the supplement.
- The GUI display projection boundary distinguishes the two processors.

### D2. Two-layer application/provider contract split

The contract separates two data layers:
- **Provider-neutral correlation IDs** — opaque string IDs minted by the harness (layers 1, 2) or accepted from the provider (layer 3). Drive dedup, deactivation, elision, and display correlation. Stable across persistence.
- **Provider-originated supplements** — opaque payload carried alongside each correlation ID. Provider-shaped. Used by the originating provider's converser for same-provider replay or session continuation. Application does not interpret supplements.

This split lets the application stay provider-agnostic while preserving provider-specific fidelity.

### D3. Correlation ID minting

Default: the harness always mints its own UUID4 correlation identifier for every invocation request, regardless of processor (Application or Provider). The harness never re-uses a provider-supplied identifier as the application-facing correlation ID. Provider-supplied tool-call IDs (e.g., OpenAI `tool_call_id`, Anthropic `tool_use_id`, OpenAI Responses `response_id` / `output_item_id`, or any opaque session reference) are recorded in the supplement for same-provider replay/continuation.

MCP-supplied primitives (if present and shaped compatibly) are recorded in the supplement as opaque data to aid with MCP call tracing; they do not become the application-facing correlation ID.

Extension point: the harness exposes a hook for MCP-specific adapter logic, but the default behavior is always harness-minted.

### D4. GUI display projection boundary

The user-visible invocation display projects only normalized fields: `(name, arguments, correlation_id)`. Raw provider replay envelopes are not part of the default projection. A separate "show details" or "debug" affordance exposes the supplement and the per-invocation raw provider envelope when explicitly selected.

This addresses the leak-surface finding at `sources/aiwb/gui/updaters.py:344-345, 382, 761` and `sources/aiwb/gui/layouts.py:1051-1063` (raw JSON dump of `invocation_data`).

### D5. Pre-R2 cleanup of OpenAI legacy `function_call`

**Completed** as dispatch commit `a31afb5` on `providers` branch (`Remove OpenAI legacy function_call and retire deprecated model families`), per `todos/providers/2`. The dispatch covers the legacy code paths in the OpenAI converser, the `Attributes` field cleanup, the `InvocationsSupportLevels` enum collapse, and regex updates for retired model families. Follow-on commit `32694f5` (`gpt-4o* family deletes`) completes the cleanup; together these commits remove the legacy `function_call` and retired-model surface that the contract must not depend on. The contract does not preserve `InvocationsSupportLevels.Single` as a contract requirement; the OpenAI provider implementation can be assumed to emit only modern `tool_calls` for tool-call replay.

#### D5a. Legacy persistence rewrite/drop policy (deployment decision)

Persisted conversations with legacy `function_call` records in `model_context.supplement` will not replay tool-call history after the dispatch commit. The policy decision (rewrite old records to the new shape, drop them, or accept that they won't replay) is a deployment concern, not a contract concern. Tracked at `todos/providers/8`. GUI-side legacy paths (`gui/persistence.py:366-388` save normalization, `messages/core.py:279-290` very-old restore) require coordinated FE Web follow-on (suggested as a new `todos/web/<n>`).

The contract requires the persistence layer to **support** a one-shot upgrade path (see `specs/invocation-data-contract/spec.md` Scenario "Legacy upgrade path is bounded"). The actual rewrite/drop policy is configured at deployment time within that upgrade path's implementation.

### D6. Persistence and rehydration

Each persisted invocation record carries:
- The normalized request fields.
- The correlation ID.
- The provider-originated supplement (opaque payload).
- The `ToolSource` discriminator.

Rehydration reads the persisted record and reconstructs the same normalized in-memory shape. Supplements round-trip exactly so same-provider replay fidelity is preserved. The legacy restore path in `sources/aiwb/messages/core.py:279-290` (handling conversations persisted before this contract) becomes a one-shot upgrade path, removable once all in-tree persisted conversations have been migrated.

### D7. Three-layer compat with MCP and provider-native tools

The contract reserves the shape for MCP-sourced tools (harness-mediated, layer 2) and provider-native/server-side tools (layer 3) without implementing either. Each `InvocationRequest` carries a `ToolSource` so downstream layers can distinguish, and the GUI display projection boundary handles each layer distinctly. Default values for the four open questions are documented in §Risks below.

## Risks / Trade-offs

- **R1. Migration churn.** Existing persisted conversations predate the contract. Mitigation: the rehydration path in `sources/aiwb/messages/core.py:279-290` provides a one-shot upgrade; once conversations are migrated, the path can be deleted.
- **R2. Provider-specific supplement round-trip.** Opaque supplements must round-trip exactly for same-provider replay fidelity. Mitigation: supplements are serialized as opaque blobs (e.g., base64-encoded JSON or a tagged union); no interpretation by the application layer.
- **R3. Correlation ID uniqueness.** The harness must guarantee correlation ID uniqueness across all live and persisted invocations in a conversation, regardless of processor. Mitigation: UUID4 minting (see D3). Provider-issued IDs do not contribute to harness uniqueness guarantees and are not exposed as application-facing correlation IDs.
- **R4. Cross-lane coupling risk.** The contract is intentionally cross-cutting; without strict sequencing of pre-R2 cleanup (`todos/providers/2`), legacy `function_call` paths could leak into the contract design. Mitigation: pre-R2 cleanup is gated as a precondition in `tasks.md` §2.2.
- **R5. GUI display projection risk.** The "show details" affordance is an explicit user opt-in; without it, debuggability suffers. Mitigation: the affordance is exposed at least at the developer/debug console level even if not surfaced in the default user UI.
- **R6. MCP correlation ID open question.** Default is harness-minted; if an MCP server supplies a correlation primitive and we do not honor it, debugging MCP-mediated failures is harder. Mitigation: extension point in D3; revisited if real MCP integration surfaces this need.
- **R7. Legacy persisted `function_call` records.** After the dispatch commit `a31afb5` removes the OpenAI legacy path, persisted conversations carrying `function_call` records in `model_context.supplement` cannot replay tool-call history. The contract requires the persistence layer to support a one-shot upgrade path (Scenario "Legacy upgrade path is bounded"), but the rewrite/drop policy decision is a deployment concern tracked at `todos/providers/8`. GUI-side legacy paths require coordinated FE Web follow-on. Mitigation: cross-link `todos/providers/8` and the suggested `todos/web/<n>` from this proposal; the policy is decided before R2 implementation begins so the upgrade path is configurable rather than hard-coded.

## Migration Plan

Phased:
1. **Pre-R2 cleanup**: Remove OpenAI legacy `function_call` paths per `todos/providers/2`. Gated as a precondition in `tasks.md` §2.2.
2. **Mock smoke first**: Build mock multi-tool invocation smoke (`todos/invocables/3`) covering parallel tool calls, dedup supersession, correlation-ID-based linkage, and display projection. Gating the contract change with mock coverage prevents regressions during scaffolding.
3. **Contract scaffolding**: Add the `InvocationRequest`, `InvocationResult`, `InvocationSupplement`, and correlation ID types. Wire through `Invoker`, `Context`, and conversers in mock-friendly mode.
4. **Provider adaptation**: OpenAI and Anthropic conversers read from and write to normalized records; supplements attached as opaque payloads.
5. **GUI adaptation**: Display projection boundary; replace positional result linkage; `_deactivate_duplicate_invocations` uses correlation IDs.
6. **Persistence/rehydration**: Update `gui/persistence.py` and `messages/core.py`.
7. **Live smoke (BE Providers lane)**: OpenAI Chat Completions tool calls and OpenAI Responses API smokes (per `todos/providers/3`).

Rollback: each phase can be reverted independently. The pre-R2 cleanup is irreversible on its own (legacy paths deleted) but that is by design.

## Open Questions

Four open questions, surfaced for human decision. Recorded here with a default that will hold unless Coordinator/human overrides:

| # | Question | Default | Surface |
|---|----------|---------|---------|
| OQ1 | Provider-native (Provider processor) tool opt-in granularity: per-tool, per-model, per-conversation, or global? Existence is determined by the provider/model/API; opt-in is a policy decision (per-conversation or global). | Per-conversation policy at the conversation level, with a global default at the configuration level. | Coordinator/human via this proposal. |
| OQ2 | MCP correlation ID minting: harness-minted always, or adapt MCP-supplied primitives? | Always harness-minted. MCP-supplied primitives are recorded in the supplement as opaque data to aid with MCP call tracing. | Coordinator/human via this proposal. |
| OQ3 | Does `silent_extraction_failure` belong in a broad error-policy contract, or remain a follow-on? The contract requires conversers to hand well-formed invocations to the invocables engine. UI surfacing of extraction failures is a separate contract between converser and UI. | Follow-on (small-scope per R1 synthesis section 8). R2 only requires conversers to hand well-formed invocations to the invocables engine. | Coordinator/human via this proposal; tracked at `todos/web/5`. |
| OQ4 | Is a typed `Context.supplements` accessor included in R2 or deferred? The accessor can have typed methods for known keys (`model`, `controls`) plus a nested dictionary for provider-defined shapes. | Included in R2 as a small precursor inside the proposal scope. Typed shell with nested-dictionary escape for provider-defined shapes. | Coordinator/human via this proposal. |

The defaults above are tentative. If a default is contested during review, the proposal is updated and re-validated before the human approval gate.
