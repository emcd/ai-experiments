# AI Provider Architecture

This package separates model identity from provider operations.

## Model References

`ModelAddress` is stable identity. It contains provider name, client name, model
genus, and model name. Use it for logging, cache keys, comparisons, and persisted
references which do not need provider SDK access.

`ModelDescriptor` is runtime model data. It contains a `ModelAddress`, the
client which can operate on the model, and the model attributes. Use it when an
operation needs attributes or SDK access.

Concrete model objects still expose `client`, `name`, `attributes`, `address`,
and `descriptor`. They should not own provider behavior.

## Operation Ownership

Provider behavior lives on client-owned services grouped by model genus or
capability. Converser behavior is exposed through `client.conversers`.

Converser services receive the model explicitly for operations such as:

- native control preparation
- native message preparation
- invocation preparation, extraction, and execution
- data serialization and deserialization
- text and conversation token counting
- v0 conversation execution

This keeps SDK ownership with clients while keeping model identity and attributes
explicit at call sites.

## Migration Boundary

Do not add new model-bound processor properties such as `controls_processor`,
`messages_processor`, `invocations_processor`, `serde_processor`, or
`tokenizer`. Do not add new direct `model.converse_v0` calls.

Use the client-owned service instead:

```python
await model.client.conversers.converse_v0(
    model, messages, supplements, controls, reactors )
```

The v0 conversation API remains for behavior compatibility, but its ownership is
the converser service rather than the model.

## Validation

Provider interface changes should be validated with:

- `hatch --env develop run pyright`
- targeted Ruff checks over touched Python files
- `hatch run aiwb-application inspect`
- GUI conversation smoke checks when possible
- provider conversation and invocation smoke checks when API credentials and
  credits are available
