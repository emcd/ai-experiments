## Context

Provider conversation models currently implement behavior by returning fresh,
model-bound processor objects. The shared interface in
`sources/aiwb/providers/interfaces.py` defines `ControlsProcessor`,
`InvocationsProcessor`, `MessagesProcessor`, `ConverserSerdeProcessor`, and
`ConversationTokenizer` as protocols with a `model` property and constructors
that accept `model`. Concrete OpenAI and Anthropic models instantiate these
processors from model properties.

The concrete providers then call back through those properties inside their own
operation paths. For example, `_prepare_client_arguments` nativizes controls via
`model.controls_processor.nativize_controls`, nativizes messages via
`model.messages_processor.nativize_messages_v0`, and nativizes invocables via
`model.invocations_processor.nativize_invocables`. GUI and invocable code also
calls `model.converse_v0`, `model.tokenizer`, `model.serde_processor`, and
`model.invocations_processor` directly.

This design works at runtime, but it makes every operation appear to belong to
the model object. In practice, the operation logic is provider/client behavior
parameterized by a model. That mismatch creates type pressure, encourages broad
model protocols, and makes it harder to introduce model families or provider
capabilities that differ by operation.

## Goals

- Separate model identity from provider operation implementations.
- Make the model passed to provider operations explicit at call sites.
- Preserve immutable or effectively immutable model descriptors and attributes.
- Reduce circular typing between model protocols and operation protocols.
- Preserve existing v0 conversation behavior throughout migration.
- Keep the implementation incremental and reviewable.

## Non-Goals

- Redesign controls definitions or GUI widgets.
- Replace provider configuration files or model metadata format.
- Remove v0 conversation compatibility in the same change.
- Add new provider capabilities beyond reorganizing how existing capabilities are
  addressed.
- Preserve model-bound processor properties as a compatibility layer after the
  migration is complete.

## Current Pain Points

- Processor objects are bound to one model but are usually stateless apart from
  that reference.
- Models know about every operation category, even when provider/client services
  are the real behavior owners.
- Provider-specific attributes such as OpenAI invocation support levels and
  Anthropic computer-use support require concrete model narrowing in several
  places.
- Tokenization and serialization are exposed as model properties, which makes
  ordinary utility calls depend on model-owned processor construction.
- Conversation code composes controls, messages, supplements, invocations, and
  reactors through model methods instead of an explicit operation service.

## Proposed Architecture

Introduce an explicit model reference layer and provider operation services.

`ModelAddress` should represent stable identity:

- provider name
- client name
- model genus
- model name

`ModelDescriptor` should represent a runtime model reference:

- `address`
- `client`
- `attributes`

The two objects are intentionally separate. `ModelAddress` is cheap identity for
logs, cache keys, persisted references, and comparisons. `ModelDescriptor` is
the value passed to runtime operations that need attributes or SDK access. A
single object would be simpler at first, but would tend to mix persistence and
runtime concerns as capabilities grow.

Provider operations should be owned by client services rather than by the model.
Clients are the right owner because they already own SDK access and can expose
different operation services for different model genera. The preferred shape is
a genus-oriented service reachable from the client, for example:

```python
await client.conversers.converse_v0(
    model = model,
    messages = messages,
    supplements = supplements,
    controls = controls,
    reactors = reactors,
)
```

Avoid a generic `operations` nesting level unless implementation proves that it
solves a concrete naming or discoverability problem. A shallow service such as
`client.conversers` is easier to read than
`client.operations.conversations`, and it leaves room for other model genera
such as `client.vectorizers`, `client.picture_generators`,
`client.audio_transcribers`, and `client.audio_tts`.

The converser service should cover the existing responsibilities currently split
across model-bound processors:

- `controls`: nativize normalized controls for a model.
- `messages`: nativize and refine message canisters for a model.
- `invocations`: nativize invocables, extract invocation requests, and execute
  invocation requests with model context.
- `serde`: serialize and deserialize data according to model preferences.
- `tokens`: count text and conversation tokens for a model.
- `conversations`: perform v0 conversation orchestration for a model.

Operations should receive `model` explicitly and may still use provider-specific
concrete model/attribute types internally. This allows narrow provider modules to
keep precise types without forcing broad common protocols to expose every
provider-specific detail.

## Migration Strategy

This is alpha software, so the migration should be a sharp break. The completed
change should remove direct model-bound processor access rather than preserving a
parallel adapter architecture.

The implementation may use short-lived local delegations inside a branch if they
help preserve behavior while moving code, but they are not part of the accepted
end state. By the end of this change, internal callers should use client-owned
services instead of:

- `model.controls_processor`
- `model.messages_processor`
- `model.invocations_processor`
- `model.serde_processor`
- `model.tokenizer`
- `model.converse_v0`

## Considered Options

### Keep Bound Processors

This preserves the current runtime pattern but leaves the type and architecture
pressure in place. It does not clarify ownership of provider behavior.

### Provider Strategy Functions

Plain functions such as `nativize_controls( model, controls )` minimize object
ceremony. They are simple inside provider modules, but they do not provide an
obvious common access path for GUI and invocable callers.

### Client-Owned Operation Services

Client-owned services make runtime ownership explicit and provide a stable
access path from selected models. This is the preferred direction because the
client already owns provider SDK access and model discovery. Services should be
grouped by model genus or capability, for example `client.conversers`, so that
TTS, audio transcription, picture generation, vectorization, and conversation
models can evolve independently.

### Model-Owned Capability Bundle

A bundle such as `model.operations.messages.nativize_v0( model, ... )` improves
organization but still makes model objects responsible for locating behavior. It
also adds nesting without clarifying SDK ownership. This should not be the
primary model.

## Migration Plan

1. Add model reference types and provider operation protocols without changing
   behavior.
2. Implement client-owned genus services for OpenAI and Anthropic by moving
   existing processor method bodies into services such as `client.conversers`.
3. Update internal provider helpers to call operations directly instead of
   constructing model-bound processors.
4. Update GUI and invocable callers to use explicit operations.
5. Remove model-bound processor properties and direct `model.converse_v0`,
   `model.tokenizer`, and `model.serde_processor` access from the end state.
6. Add `sources/aiwb/providers/README.md` documenting the accepted architecture,
   ownership boundaries, and migration rules.

## Validation

- Run `hatch --env develop run pyright`.
- Run targeted Ruff over changed Python files.
- Run `hatch run aiwb-application inspect`.
- Smoke test GUI conversation selection and a new conversation.
- When credentials and credits are available, smoke test at least one OpenAI or
  Anthropic conversation and one invocation flow.
