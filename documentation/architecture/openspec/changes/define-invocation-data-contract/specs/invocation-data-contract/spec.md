# invocation-data-contract Specification (delta)

## ADDED Requirements

### Requirement: Normalized Invocation Records

The system SHALL represent invocation requests, results, and supplements as normalized records that are provider-agnostic at the application layer. The normalized records SHALL expose only fields the application needs for invocation, dedup, deactivation, elision, display correlation, and persistence: identity (`name`), arguments (`arguments` mapping), correlation identifier, and a tool-source discriminator. Provider-shaped envelopes SHALL NOT be part of the normalized record body.

#### Scenario: Application reads only normalized fields for dedup

- **WHEN** the GUI deduplication logic inspects an invocation record
- **THEN** it reads only `name`, `arguments`, and the correlation identifier
- **AND** does not branch on provider-specific keys (e.g., `tool_calls`, `tool_use`, `function_call`)

#### Scenario: Invocable receives normalized arguments

- **WHEN** an `Invoker.__call__` invokes a registered invocable
- **THEN** the `arguments` parameter is the normalized mapping
- **AND** the invocable does not need to inspect provider-shaped data to do its work

#### Scenario: Endpoint output envelope adapts to normalized shape

- **WHEN** any provider endpoint (OpenAI Chat Completions, OpenAI Responses, Anthropic Messages, future endpoints) produces a tool-call or output-item shape that is not directly `(name, arguments)`
- **THEN** the converser for that endpoint adapts the tool-call or output-item shape to `(name, arguments)` and stores it as the normalized record fields
- **AND** the provider-originated envelope is attached separately as an opaque supplement under `model_context.supplement`
- **AND** the GUI dedup path at `sources/aiwb/gui/actions.py:256-304` and the `invocation_data` iteration in `sources/aiwb/gui/updaters.py:344-345, 382, 761` and `sources/aiwb/gui/conversations.py:64-66` consume only the normalized fields, not the supplement

### Requirement: Provider-Neutral Correlation IDs

The system SHALL mint a provider-neutral correlation identifier for every invocation request, regardless of tool source (Application or Provider). The harness SHALL always mint its own UUID4 correlation identifier and SHALL never re-use a provider-supplied identifier as the application-facing correlation ID. Provider-supplied tool-call IDs SHALL be recorded in the supplement as opaque data for same-provider replay/continuation. Correlation identifiers SHALL be stable across persistence and SHALL drive dedup, deactivation, elision, and display correlation.

#### Scenario: Harness mints correlation ID for local application tool

- **WHEN** an `InvocationRequest` is created for a local application invocable
- **THEN** the correlation identifier is minted by the harness
- **AND** is stored on the request and the corresponding result

#### Scenario: Harness always mints correlation IDs

- **WHEN** any invocation request is created, regardless of tool source
- **THEN** the harness mints its own UUID4 correlation identifier
- **AND** never re-uses a provider-supplied identifier as the application-facing correlation ID
- **AND** provider-supplied tool-call IDs (when present) are stored in the supplement, not exposed to application linkage

#### Scenario: Correlation identifier drives dedup

- **WHEN** two invocation results carry the same correlation identifier
- **THEN** the dedup logic treats them as duplicates
- **AND** the older result is superseded by the newer one without inspecting provider-shaped envelopes

#### Scenario: Correlation identifier is the result-pairing key

- **WHEN** the GUI pairs an invocation canister with its result canister
- **THEN** pairing uses the correlation identifier as the lookup key
- **AND** iteration over the history column continues to use positional index for unrelated operations

#### Scenario: Correlation identifier is the stable slot identifier

- **WHEN** the GUI or persistence layer needs to address a specific invocation record across turns, persistence, and dedup
- **THEN** the correlation identifier is the stable lookup key
- **AND** no separate `MessageCanister.identity` field is introduced

### Requirement: Three-Layer Tool-Source Model

The system SHALL distinguish two tool processors on every `InvocationRequest` via an `InvocationProcessor` enum with values `Application` and `Provider`. The processor discriminator SHALL be carried through persistence and SHALL be available to the GUI display projection boundary. The Application category covers both local application tools and MCP-sourced tools (both are client-provided; the harness supplies the JSON schema to the model). The Provider category covers provider-native/server-side tools whose schema is maintained server-side. Provenance distinctions (local vs MCP) within the Application category are tracked at the registry/layer level, not on every `InvocationRequest`.

#### Scenario: Application tool marked correctly

- **WHEN** an `InvocationRequest` originates from an `Invoker` registered in `sources/aiwb/invocables/core.py` or from an MCP server registration mediated by the harness
- **THEN** the `InvocationProcessor` discriminator is `Application`
- **AND** the harness emits the JSON schema to the model as part of the tool declaration
- **AND** the GUI display projection treats the result as client-provided output

#### Scenario: Provider tool marked correctly

- **WHEN** an `InvocationRequest` represents a provider-native/server-side tool such as `code_interpreter` or `file_search`
- **THEN** the `InvocationProcessor` discriminator is `Provider`
- **AND** the harness emits only the tool name to the model (the schema is server-side)
- **AND** the GUI display projection distinguishes provider-rendered output from application-rendered output

#### Scenario: Processor-aware rendering in the invocable selector

- **WHEN** the GUI renders the invocable selector
- **THEN** Application tools (including MCP-sourced) are selectable
- **AND** Provider tools are visible but disabled in the selector with a tooltip explaining server-side execution
- **AND** each processor carries a distinguishing visual badge (e.g., MCP badge for MCP-sourced Application tools, grayed state for Provider tools)

### Requirement: Provider-Originated Supplements as Opaque Data

The system SHALL attach a provider-originated supplement to each invocation record. The supplement SHALL be opaque to the application layer; only the converser for the originating provider SHALL interpret it. The supplement SHALL be used by the originating provider's converser for same-provider replay or session continuation. The application SHALL NOT inspect the supplement for local invocation, dedup, or display correlation.

#### Scenario: Application does not interpret supplement

- **WHEN** the GUI processes an invocation record
- **THEN** it reads the correlation identifier, the normalized fields, and the tool-source discriminator
- **AND** does not read fields inside the supplement

#### Scenario: Provider converser reads supplement for replay

- **WHEN** the same provider is asked to replay or continue a turn for a conversation
- **THEN** the converser for that provider reads its own supplement
- **AND** emits the provider-shaped envelope derived from the supplement
- **AND** does not require the application to have inspected the supplement

#### Scenario: Provider-issued tool-call IDs are preserved in the supplement

- **WHEN** any provider (Application or Provider processor) returns tool-call IDs (e.g., OpenAI `tool_call_id`, Anthropic `tool_use_id`, OpenAI Responses `response_id` / `output_item_id`, or any opaque session reference)
- **THEN** those IDs are stored in the supplement for the originating provider
- **AND** are available to the originating provider's converser for same-provider replay/continuation
- **AND** are never used as the application-facing correlation ID

### Requirement: GUI Display Projection Boundary

The system SHALL project the user-visible invocation display from the normalized record, not from the supplement. Raw provider replay envelopes SHALL NOT appear in the default user-visible invocation display. A separate "show details" or debug affordance MAY expose the supplement and the per-invocation raw provider envelope when the user explicitly opts in.

#### Scenario: Default user display shows normalized fields only

- **WHEN** the GUI renders an invocation in the conversation history
- **THEN** the visible content is derived from the normalized record
- **AND** does not include provider-shaped envelopes

#### Scenario: Debug affordance exposes raw envelope on demand

- **WHEN** the user explicitly invokes a debug or "show details" affordance on an invocation record
- **THEN** the supplement and the per-invocation raw provider envelope are available for inspection
- **AND** are not displayed in the default view
- **AND** the affordance is disabled by default
- **AND** the affordance lives on the message canister (e.g., the per-message `row_actions` bar) rather than in a separate debug console

#### Scenario: Existing message-role iconography is preserved

- **WHEN** the GUI renders a normalized invocation canister
- **THEN** the existing message-role iconography (e.g., the hammer-and-wrench glyph for `MessageRole.Invocation` in the `_roles_emoji` mapping at `sources/aiwb/gui/updaters.py:228-234`) is preserved on the canister header
- **AND** the change from raw JSON body to normalized rendering does not alter the visual scan anchor

#### Scenario: Parallel invocations render as discrete blocks

- **WHEN** an assistant canister contains multiple invocations from a single parallel tool call
- **THEN** each invocation renders as a discrete block inside the canister
- **AND** each block carries its own `(name, arguments, correlation_id, tool_source)` projection
- **AND** the renderer is owned by the GUI layer (e.g., `sources/aiwb/gui/updaters` or a new `sources/aiwb/gui/projections` module), not by a backend module

### Requirement: Persistence and Rehydration Semantics

The system SHALL persist normalized invocation records, correlation identifiers, tool-source discriminators, and provider-originated supplements together. Rehydration SHALL reconstruct the same normalized in-memory shape. The supplement SHALL round-trip exactly so same-provider replay fidelity is preserved.

#### Scenario: Persisted record round-trips through rehydration

- **WHEN** a conversation is saved and later loaded
- **THEN** each invocation record rehydrates with the same normalized fields, correlation identifier, tool-source discriminator, and supplement
- **AND** the resulting in-memory shape is indistinguishable from a freshly created record

#### Scenario: Supplement is opaque to persistence

- **WHEN** a record is persisted
- **THEN** the supplement is stored as an opaque blob
- **AND** is not interpreted or transformed by the persistence layer

#### Scenario: Supplement is byte-stable across persistence

- **WHEN** a record is persisted and later rehydrated
- **THEN** the supplement deserialized from the persistence layer is byte-equal to the supplement written
- **AND** any same-provider converser that re-emits a request from the supplement produces the same wire-shape request as the original

#### Scenario: Legacy upgrade path is bounded

- **WHEN** a conversation was persisted before this contract landed
- **THEN** a one-shot upgrade path reconstructs the normalized shape from the legacy shape
- **AND** once all in-tree conversations are migrated the upgrade path is removable

### Requirement: Pre-R2 OpenAI Legacy function_call Removal

The system SHALL remove OpenAI legacy `function_call` paths before this contract lands. The contract SHALL NOT preserve `InvocationsSupportLevels.Single` as a contract requirement.

#### Scenario: Legacy function_call paths are absent at contract landing

- **WHEN** the contract implementation begins
- **THEN** the OpenAI converser no longer branches on `InvocationsSupportLevels.Single`
- **AND** no code path emits `functions` or `function_call` request arguments
- **AND** no code path parses `function_call` from responses

#### Scenario: Contract does not depend on legacy path

- **WHEN** the contract spec is read
- **THEN** no requirement depends on the existence of legacy `function_call` paths
- **AND** all scenarios are satisfied by `tools`/`tool_calls`-shaped or Responses-API-shaped invocations only
