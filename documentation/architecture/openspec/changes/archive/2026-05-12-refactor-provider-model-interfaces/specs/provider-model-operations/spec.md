## ADDED Requirements

### Requirement: Explicit Model Reference

The system SHALL represent provider model identity separately from provider
operation implementations.

#### Scenario: Model identity is needed without operation behavior

- **WHEN** code needs to log, cache, compare, or persist a model reference
- **THEN** it can use a model identity value that includes provider, client,
  genus, and model name without constructing operation processors

#### Scenario: Provider operations need runtime model data

- **WHEN** provider operation code needs model attributes or SDK client access
- **THEN** it receives an explicit runtime model descriptor or model object as an
  argument

### Requirement: Provider-Owned Model Operations

The system SHALL expose provider model operations from client-owned services
grouped by model genus or capability rather than requiring new code to construct
model-bound processors.

#### Scenario: Native controls are prepared

- **WHEN** normalized controls are prepared for a selected model
- **THEN** a client-owned capability service receives the selected model and
  returns native provider arguments

#### Scenario: Native messages are prepared

- **WHEN** conversation message canisters are prepared for a selected model
- **THEN** a client-owned capability service receives the selected model,
  canisters, and supplements and returns native provider messages

#### Scenario: Invocations are prepared or extracted

- **WHEN** invocables are shared with a provider or invocation requests are
  extracted from a provider response
- **THEN** client-owned invocation operations receive the selected model
  explicitly and preserve provider-specific invocation metadata

#### Scenario: Serialization or tokenization is requested

- **WHEN** code serializes data, deserializes data, counts text tokens, or counts
  conversation tokens
- **THEN** the client-owned capability service receives the selected model
  explicitly and applies that model's format preferences and tokenization rules

### Requirement: v0 Conversation Compatibility

The system SHALL preserve existing v0 conversation behavior while removing
direct model-bound processor access from the completed implementation.

#### Scenario: GUI chat uses a selected model

- **WHEN** the GUI submits a v0 chat request with messages, supplements,
  controls, and reactors
- **THEN** the same provider request arguments and response canisters are
  produced as before the refactor

#### Scenario: Existing persisted invocation context is replayed

- **WHEN** a conversation contains provider-specific invocation metadata from
  OpenAI or Anthropic responses
- **THEN** migrated invocation operations preserve compatibility with that
  metadata or safely elide incompatible invocation history as before

### Requirement: Source-Tree Architecture Documentation

The system SHALL document the accepted provider model operation architecture in
the provider source subtree.

#### Scenario: A developer changes provider interfaces

- **WHEN** a developer reads `sources/aiwb/providers/README.md`
- **THEN** it explains model identity, model descriptors, client-owned operation
  services, migration boundaries, and validation expectations
