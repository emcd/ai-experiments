# Tool Calls

Currently, we use Python dictionaries as a source of truth for tool input
parameters. This is a deliberate design decision, based on limitations
encountered while researching and experimenting with Pydantic. These
dictionaries are structured to be serializable into JSON Schema strings by
merely using `json.dumps` from the Python standard library. The JSON Schema in
the strings is currently compatible with both Anthropic and OpenAI model
tool-calling input specifications.

## References

* https://docs.anthropic.com/en/docs/build-with-claude/tool-use
* https://github.com/anthropics/courses/tree/master/ToolUse
* https://cookbook.openai.com/examples/structured_outputs_intro
* https://cookbook.openai.com/examples/structured_outputs_multi_agent

## Why not use Pydantic?

Although Pydantic is very popular for validating inputs and generating JSON
Schema, the JSON Schema that it generates is unnecessarily verbose and contains
constructs that might not be supported by upstream validators/converters for
some language models. In particular:

* Pydantic has no way to generate a JSON Schema without the optional `title`
  fields. This is wasteful in terms of tokens and may be invalid or confusing
  to upstream[^1].

* Although the structured outputs (`strict = True`) feature on newer OpenAI
  models does support JSON Schema definitions and `$ref` references, it is not
  clear that all models (Anthropic, older OpenAI models, etc...) do.[^2]
  Pydantic, however, does not seem to have a way to nest definitions in
  generated output and, instead, makes use of `$ref` references.[^3] In
  principle, this is what we would want, if we had clearer guarantees of
  upstream support. Which we do not.

* Pydantic V2 is inconsistent in the way JSON Schema `minItems` and `maxItems`
  are specfied. Although many of the JSON Schema "extra" keyword arguments to
  Pydantic fields reflect JSON Schema options, these do not.[^4] They could
  have been easily aliased to avoid this confusion (and maintain compatibility
  with V1 expectations).

### Pydantic References

* https://docs.pydantic.dev/latest/concepts/models/#basic-model-usage
* https://docs.pydantic.dev/latest/api/config/
* https://docs.pydantic.dev/latest/concepts/fields/#default-values
* https://docs.pydantic.dev/latest/concepts/json_schema/#field-level-customization

### Pydantic Example

```python
class NamedDiceSpec( __.pydantic.BaseModel ):

    model_config = __.pydantic.ConfigDict( frozen = True )

    name: __.typx.Annotated[
        str, __.pydantic.Field( description = _dice_name_description ) ]
    # TODO? Split dice field into number, sides, and offset fields.
    dice: __.typx.Annotated[
        str, __.pydantic.Field( description = _dice_spec_description ) ]


class NamedDiceSpecs( __.pydantic.BaseModel ):

    model_config = __.pydantic.ConfigDict( frozen = True )

    specs: __.typx.Annotated[
        tuple[ NamedDiceSpec, ... ], __.pydantic.Field( min_length = 1 ) ]
```

```json
{
  '$defs': {
      'NamedDiceSpec': {
          'properties': {
              'name': {
                  'description': '\nName of the dice roll. Note that this may be duplicate across list items. This\nallows for scenarios, like D&D ability scores, where more than one independent\nroll may be used to determine the same score.\n',
                  'title': 'Name',
                  'type': 'string'
              },
              'dice': {
                  'description': "\nA dice specification, such as '1d10' or '3d6+2'. The pattern comprises the\nnumber of dice, the type of dice (i.e., the number of sides, which must be even\nand greater than 3), and an optional offset which can be positive or negative.\nThe offset is added to the total roll of the dice and does not have an upper\nlimit, but a negative offset must not reduce the total roll to less than 1. For\ninstance, '1d4-1' is illegal because a roll of 1 would result in a total value\nof 0.\n",
                  'title': 'Dice',
                  'type': 'string'
              }
          },
          'required': ['name', 'dice'],
          'title': 'NamedDiceSpec',
          'type': 'object'
      }
  },
  'properties': {
      'specs': {
          'items': {'$ref': '#/$defs/NamedDiceSpec'},
          'minItems': 1,
          'title': 'Specs',
          'type': 'array'
      }
  },
  'required': ['specs'],
  'title': 'NamedDiceSpecs',
  'type': 'object'
}
```

### Future Conversion to Pydantic

That said, if it becomes clear that we need stronger input validation or need
to serialize to more formats, then Pydantic or a something similar could be
considered in the future. Tools, such as
(datamodel-code-generator)[https://github.com/koxudaxi/datamodel-code-generator]
can be used to create Pydantic models or even standard Python data classes in
the future.

# Footnotes

[^1]: More context on Pydantic and `title` fields:
    * https://github.com/pydantic/pydantic/discussions/8504
    * https://zzbbyy.substack.com/p/schemas-for-openai-functions-parameters

[^2]: OpenAI structured output schema support information:
    * https://platform.openai.com/docs/guides/structured-outputs/supported-schemas
    * https://cookbook.openai.com/examples/structured_outputs_intro#using-the-sdk-parse-helper

[^3]: No way to suppress definitions and `$ref` references in Pydantic:
    * https://github.com/pydantic/pydantic/issues/889

[^4]: More context on Pydantic inconsistencies with JSON Schema:
    * https://github.com/pydantic/pydantic/issues/5405
