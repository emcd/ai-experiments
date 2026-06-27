# provider-model-operations Specification (delta)

## MODIFIED Requirements

### Requirement: Provider-Owned Model Operations

The system SHALL expose provider model operations from client-owned services
grouped by model genus or capability rather than requiring new code to construct
model-bound processors. Client-owned invocation operations SHALL read from
normalized invocation records (per `invocation-data-contract`) and SHALL attach
provider-originated supplements (per `invocation-data-contract`) rather than
returning provider-shaped envelopes to the application layer.

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
  explicitly and preserve provider-specific invocation metadata as opaque
  supplements attached to normalized records (per `invocation-data-contract`)

#### Scenario: Serialization or tokenization is requested

- **WHEN** code serializes data, deserializes data, counts text tokens, or counts
  conversation tokens
- **THEN** the client-owned capability service receives the selected model
  explicitly and applies that model's format preferences and tokenization rules
