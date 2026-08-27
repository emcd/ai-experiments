## 1. Implementation

- [x] 1.1 Add `InvocationRequest`, `InvocationResult`, `InvocationSupplement` dataclasses to `sources/aiwb/providers/core.py` with `immut.DataclassObject` semantics. The supplement is opaque to the application layer; only the converser for the originating provider interprets it.
- [x] 1.2 Define a provider-neutral correlation ID type (`InvocationCorrelationId`, opaque string) in the same module. Stable across persistence.
- [x] 1.3 Update `Invoker.__call__` and `Context` so the correlation ID is available to the invocable implementation without ad-hoc dict reads on `Context.supplements`. Note: this task also covers the OQ4 typed `Context.supplements` accessor; intended to land first in the work order as the OQ4 precursor even though the surrounding task numbers reflect the type-definition order.
- [ ] 1.4 Replace `result_index = i + j + 1` in `sources/aiwb/gui/actions.py:283` with correlation-ID-based result pairing; positional indexing of the history column is preserved for unrelated operations.
- [ ] 1.5 Update `_deactivate_duplicate_invocations` in `sources/aiwb/gui/actions.py:256-304` to use correlation IDs.
- [ ] 1.6 Add a GUI display projection boundary: a `display_payload` projection that exposes only normalized `(name, arguments, correlation_id)` for the user-visible invocation display; raw provider-originated envelopes remain available behind an explicit "show details" affordance.
- [ ] 1.7 Update persistence (`sources/aiwb/gui/persistence.py:_standardize_invocation_requests_v0:366`) and rehydration (`sources/aiwb/messages/core.py:restore_canister:270`) to serialize/deserialize normalized records with correlation IDs and opaque supplements.
- [x] 1.8 Reserve the processor dichotomy in the contract: `InvocationProcessor` enum or equivalent with values `Application` and `Provider`. Each `InvocationRequest` carries its processor discriminator so the GUI and persistence can distinguish. Provenance distinctions within `Application` (local vs MCP) live at the registry/layer level, not on every `InvocationRequest`.

## 2. Provider adaptation

- [ ] 2.1 OpenAI converser: rewrite `requests_from_canister` (pre-dispatch `sources/aiwb/providers/clients/openai/conversers.py:182`; cross-link to `master` post-dispatch for current location) to consume normalized records (no OpenAI-shaped `tool_calls` reads at this layer); rewrite `execute_invocation` (pre-dispatch `:130`) to write normalized results, attaching the OpenAI-specific supplement (response IDs, output item IDs, opaque session references for layer 3 native tools).
- [ ] 2.2 OpenAI converser: legacy `function_call` removal **completed** as dispatch commit `a31afb5` on `providers` branch (`Remove OpenAI legacy function_call and retire deprecated model families`), per `todos/providers/2`. Follow-on commit `32694f5` (`gpt-4o*` family deletes) completes the cleanup; together these commits remove the legacy `function_call` and retired-model surface that the contract must not depend on. Contract implementation does not need to repeat removal; the dispatch commits are the authoritative reference. GUI save normalization (`gui/persistence.py:366-388`) and very-old restore path (`messages/core.py:279-290`) are not provider-layer; the legacy persistence rewrite/drop policy is tracked at `todos/providers/8` (BE Providers) and a corresponding `todos/web/<n>` (FE Web) as a pre/post-R2 follow-on.
- [ ] 2.3 OpenAI converser: rewrite `nativize_invocables` and `_nativize_invocation_message`, `_nativize_result_message`, `_reconstitute_invocations` to read from and write to normalized records. Note: pre-dispatch line numbers from earlier drafts; cross-link to `master` post-dispatch for current locations. `_reconstitute_legacy_invocation` is removed by dispatch (per §2.2) and is not in scope for R2.
- [ ] 2.4 Anthropic converser: same shape of changes as 2.1 and 2.3 against `sources/aiwb/providers/clients/anthropic/conversers.py`.
- [ ] 2.5 Update `requests_from_canister` consumers (`sources/aiwb/providers/utilities.py:123`, `sources/aiwb/gui/invocables.py:extract_invocation_requests:28`) to pass normalized records end-to-end.
- [ ] 2.6 Update `_nativize_messages_v0` in both conversers (pre-dispatch `openai/conversers.py:223`, `anthropic/conversers.py:184`; cross-link to `master` post-dispatch for current locations) to round-trip the supplement as opaque payload.
- [ ] 2.7 Attach the correlation identifier to `ResultMessageCanister.attributes.model_context` (or a new normalized `correlation_id` attribute) so the result-pairing consumer (`requests_from_canister`) can match it. Correlation ID mapping is at the request/result level, not the message level; slot identification refers to the result canister being matched back to its originating request.

## 3. Three-layer tool-source support

- [x] 3.1 Define the `InvocationProcessor` taxonomy (`Application`, `Provider`) and ensure each `Invoker` and `InvocationRequest` carries its processor discriminator.
- [ ] 3.2 Reserve the configuration and presentation seam for provider-native/server-side tools so a future provider can opt in to including them without the harness running code on its side. Do not implement an actual provider-native tool in R2. Opt-in policy is per-conversation with a global configuration default.
- [x] 3.3 Reserve MCP-sourced tool representation as application-layer invocables. Do not implement MCP transport or discovery in R2. The harness always mints the application correlation ID; any MCP-supplied primitive remains opaque supplemental tracing data.

## 4. Tests and validation

- [ ] 4.1 Mock multi-tool invocation smoke (per `todos/invocables/3`): mock converser + mock invokers through `extract_invocation_requests` → `gather_async` → `_deactivate_duplicate_invocations`. Coverage: parallel tool calls, dedup supersession via `IoContentDeduplicator`, correlation-ID-based linkage, display projection boundary.
- [ ] 4.2 Run `hatch --env develop run pyright` and Ruff over touched files (per `pyproject.toml` linters).
- [ ] 4.3 Run `hatch run aiwb-application inspect` (non-GUI; do **not** use `hatch run aiwb inspect`, which launches GUI/browser per the standing note in `coordination/general/1`).
- [ ] 4.4 Live smoke for OpenAI Chat Completions tool calls (BE Providers lane per coordination/general/2 lane ownership). OpenAI Responses API smoke is deferred to `todos/providers/3` because Responses API implementation is out of scope for R2.

## 5. Documentation

- [x] 5.1 Update `sources/aiwb/invocables/README.md` to add an architecture-level overview of the invocable stack (currently JSON-Schema/Pydantic-only per R1 finding 6).
- [ ] 5.2 Cross-link from `todos/providers/2` (OpenAI legacy function_call removal) and `todos/providers/3` (OpenAI Responses API) once this proposal lands.
