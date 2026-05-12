# Change: Refactor Provider Model Interfaces

## Why

The provider model interfaces currently bind operations to model instances via
properties such as `controls_processor`, `messages_processor`,
`invocations_processor`, `serde_processor`, and `tokenizer`. Each processor
stores the model it serves, which couples model identity, model attributes,
provider client access, and provider-specific operation logic into a circular
object graph that is difficult to type, test, and evolve.

The recent Pyright cleanup exposed this pressure without changing the design.
The next provider-interface evolution should make model identity explicit and
move operations toward provider- or client-owned services that receive the model
explicitly.

## What Changes

- Add explicit model reference objects: `ModelAddress` for stable identity and
  `ModelDescriptor` for runtime model data needed by provider operations.
- Move provider-specific operations away from model-bound processor objects and
  toward client-owned, genus-oriented services.
- Replace direct dependence on `model.*_processor` properties in new code with
  explicit operations for controls, invocations, messages, serialization, and
  tokenization.
- **BREAKING** Remove model-bound processor access as part of the completed
  migration rather than keeping compatibility adapters as an end state.
- Preserve v0 conversation behavior while updating direct callers to the new
  operation services.
- Document the accepted architecture in `sources/aiwb/providers/README.md` as
  part of implementation.

## Impact

- Affected specs: `provider-model-operations`
- Affected code:
  - `sources/aiwb/providers/interfaces.py`
  - `sources/aiwb/providers/core.py`
  - `sources/aiwb/providers/clients/openai/conversers.py`
  - `sources/aiwb/providers/clients/anthropic/conversers.py`
  - `sources/aiwb/providers/utilities.py`
  - `sources/aiwb/controls/core.py`
  - `sources/aiwb/gui/actions.py`
  - `sources/aiwb/gui/invocables.py`
  - `sources/aiwb/gui/updaters.py`
  - `sources/aiwb/invocables/ensembles/summarization/operations.py`

## Resolved Design Direction

- `ModelAddress` contains only identity (`provider`, `client`, `genus`, and
  `name`).
- `ModelDescriptor` contains the runtime model reference: `address`, `client`,
  and `attributes`.
- Operations live on clients because clients own SDK access and can expose
  different services for different model genera.
- Operation services are grouped by genus or capability, such as
  `client.conversers`, rather than under a generic `operations` namespace.
- The completed implementation removes direct `model.*_processor`,
  `model.tokenizer`, `model.serde_processor`, and `model.converse_v0` access.
