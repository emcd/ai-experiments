# OpenAI Responses API Models

## Current Limitation

This configuration does **not** currently support models that are **only available through the OpenAI Responses API**. These models require a different API endpoint (`v1/responses`) and have different request/response formats compared to the standard Chat Completions API (`v1/chat/completions`).

## Affected Models

The following models are only available through the Responses API and are therefore **not included** in our model family configurations:

1. **GPT-5.1 Codex** (`gpt-5.1-codex`)
2. **GPT-5.1 Codex Max** (`gpt-5.1-codex-max`)
3. **GPT-5 Codex** (`gpt-5-codex`)
4. **GPT-5.1 Codex mini** (`gpt-5.1-codex-mini`)
5. **codex-mini-latest** (deprecated)

## Example Configuration (If Supported)

If the Responses API were supported, the model family configurations would look similar to other GPT-5 models. Here are example TOML configurations for reference:

### GPT-5.1 Codex Family

```toml
format-version = 1

[converser]
name-regex = '^gpt-5\.1-codex(-.*)?$'
modalities = [ 'text', 'pictures' ]

[converser.special]
invocations-support-level = 'concurrent'

[converser.tokens-limits]
per-response = 128_000
total = 400_000
```

### GPT-5.1 Codex Max Family

```toml
format-version = 1

[converser]
name-regex = '^gpt-5\.1-codex-max(-.*)?$'
modalities = [ 'text', 'pictures' ]

[converser.special]
invocations-support-level = 'concurrent'

[converser.tokens-limits]
per-response = 128_000
total = 400_000
```

### GPT-5 Codex Family

```toml
format-version = 1

[converser]
name-regex = '^gpt-5-codex(-.*)?$'
modalities = [ 'text', 'pictures' ]

[converser.special]
invocations-support-level = 'concurrent'

[converser.tokens-limits]
per-response = 128_000
total = 400_000
```

## Technical Details

### Responses API vs Chat Completions API

| Aspect | Responses API | Chat Completions API |
|--------|---------------|---------------------|
| Endpoint | `v1/responses` | `v1/chat/completions` |
| Request format | Different structure | Standard messages array |
| Tool calling | Built-in | Separate function calling |
| Streaming | Supported | Supported |
| Cost | Same token pricing | Same token pricing |

### Implementation Requirements

To support Responses API models, the following would be needed:

1. **New API client implementation** for the `v1/responses` endpoint
2. **Request/response adapters** to convert between our internal format and Responses API format
3. **Tool handling integration** for the Responses API's built-in tool calling
4. **Error handling** for API-specific errors and rate limits

## Future Considerations

If Responses API support is added in the future, these model families should be created with the following considerations:

1. **API endpoint selection** - Automatically use `v1/responses` for these models
2. **Request formatting** - Convert our standard request format to Responses API format
3. **Response parsing** - Extract content and tool calls from Responses API format
4. **Error mapping** - Map Responses API errors to our internal error types

## References

- [OpenAI Responses API Documentation](https://platform.openai.com/docs/api-reference/responses)
- [OpenAI Models Page](https://platform.openai.com/docs/models)
- [Migrating to Responses API Guide](https://platform.openai.com/docs/guides/migrate-to-responses)