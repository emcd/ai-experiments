# Custom Exception Design Analysis for TRY* Errors

## Overview

Analysis of 41 TRY* errors (1 TRY002, 34 TRY003, 6 TRY004) to design semantically meaningful custom exception classes following the patterns established in `locations/exceptions.py` and `providers/exceptions.py`.

**Project Exception Standard:**
- **NEVER raise bare stdlib exceptions** (`TypeError`, `ValueError`, `RuntimeError`, etc.)
- **ALWAYS define custom exception classes** that inherit from both:
  1. `__.Omnierror` (always first in inheritance chain)
  2. Appropriate stdlib exception type(s) (`TypeError`, `ValueError`, etc.)
- **Constructor takes semantic parameters**, not formatted message strings
- **Message formatting happens inside `__init__`**, not at raise site

## Current Exception Module Structure

- `locations/exceptions.py` - 23 custom exceptions for location/filesystem operations
- `providers/exceptions.py` - 3 custom exceptions for AI provider operations

**Pattern observed:**
- Exception classes take semantic parameters (not formatted messages)
- `__init__` methods construct descriptive messages from parameters
- Multi-inheritance from `__.Omnierror` + stdlib exceptions when appropriate
- Naming convention: `<Domain><Issue><ErrorType>` (e.g., `LocationAccessorDerivationFailure`)

## Proposed New Exception Modules

### 1. `controls/exceptions.py` (NEW)

**Errors to address: 12 (6 TRY004 + 5 TRY003 + 1 TRY002)**

#### Type Validation Errors (TRY004: 6 errors)

**Locations:**
- `controls/core.py:88` - Boolean.validate_value - expects `bool`
- `controls/core.py:111` - DiscreteInterval.validate_value - expects `Rational`
- `controls/core.py:221` - Options.__init__ - expects `Collection`
- `controls/core.py:240` - Text.validate_value - expects `str`
- `controls/core.py:196` - FlexArray.validate_value - expects `Sequence`
- `controls/core.py:202` - FlexArray.validate_value - expects specific element class

**Note:** TRY004 flags type validation errors that raise `ValueError` when they should raise `TypeError`. However, per project standards, we never raise bare stdlib exceptions - we define custom exceptions that inherit from both `__.Omnierror` and the appropriate stdlib exception type.

**Proposed exceptions:**

```python
class ControlValueMisclassification(__.Omnierror, TypeError):
    ''' Control value has invalid type. '''

    def __init__(self, control_name, expected_type, received_value):
        received_type = type(received_value).__qualname__
        super().__init__(
            f"Control '{control_name}' expects {expected_type}, "
            f"received {received_type}: {received_value!r}" )

class ControlElementMisclassification(__.Omnierror, TypeError):
    ''' Control array element has invalid type. '''

    def __init__(self, control_name, expected_class, received_element):
        received_class = type(received_element).__qualname__
        super().__init__(
            f"Array '{control_name}' expects elements of type "
            f"'{expected_class}', received {received_class}: "
            f"{received_element!r}" )
```

#### Value Validation Errors (TRY003: 5 errors)

**Locations:**
- `controls/core.py:113` - Value not in discrete interval range
- `controls/core.py:125` - FlexArray.Instance.__init__ exceeds maximum
- `controls/core.py:175` - FlexArray.__init__ minimum > maximum
- `controls/core.py:227` - Options.validate_value not in options
- `controls/core.py:274` - Unknown control species name

**Proposed exceptions:**

```python
class ControlValueConstraintViolation(__.Omnierror, ValueError):
    ''' Control value outside acceptable range. '''

    def __init__(self, control_name, value, minimum, maximum):
        super().__init__(
            f"Value {value} for control '{control_name}' outside "
            f"range [{minimum}, {maximum}]" )

class ControlArrayDimensionViolation(__.Omnierror, ValueError):
    ''' Control array size exceeds limits. '''

    def __init__(self, control_name, size, maximum):
        super().__init__(
            f"Array '{control_name}' has {size} elements, "
            f"exceeds maximum of {maximum}" )

class ControlArrayDefinitionInvalidity(__.Omnierror, ValueError):
    ''' Control array definition is invalid. '''

    def __init__(self, control_name, reason):
        super().__init__(
            f"Array definition '{control_name}' is invalid: {reason}" )

class ControlOptionValueInvalidity(__.Omnierror, ValueError):
    ''' Control value not in available options. '''

    def __init__(self, control_name, value, options):
        options_str = ', '.join(repr(opt) for opt in options)
        super().__init__(
            f"Value {value!r} for control '{control_name}' not in "
            f"available options: {options_str}" )

class ControlSpeciesIrrecognizability(__.Omnierror, ValueError):
    ''' Unknown control species name. '''

    def __init__(self, species_name):
        super().__init__(f"Unknown control species: {species_name!r}")
```

#### Capacity Errors (TRY002: 1 error + TRY003: 1 error)

**Locations:**
- `controls/core.py:142` - FlexArray.Instance.append exceeds maximum (TRY002 - bare Exception)
- `gui/controls.py:116` - Flexible array in GUI exceeds maximum (TRY003)

**Proposed exceptions:**

```python
class ControlArrayCapacityViolation(__.Omnierror, RuntimeError):
    ''' Attempt to exceed control array capacity. '''

    def __init__(self, control_name, current_size, maximum, operation='add'):
        super().__init__(
            f"Cannot {operation} to array '{control_name}': "
            f"current size {current_size}, maximum {maximum}" )
```

---

### 2. `invocables/exceptions.py` (NEW)

**Errors to address: 3 TRY003**

**Locations:**
- `invocables/ensembles/probability/calculations.py:42` - Invalid dice spec (regex)
- `invocables/ensembles/probability/calculations.py:48` - Invalid dice spec (constraints)
- `invocables/ensembles/io/differences.py:122` - Overlapping edit operations

**Proposed exceptions:**

```python
class DiceSpecificationInvalidity(__.Omnierror, ValueError):
    ''' Invalid dice specification format or constraints. '''

    def __init__(self, dice_spec, reason):
        super().__init__(
            f"Invalid dice specification '{dice_spec}': {reason}" )

class EditContention(__.Omnierror, ValueError):
    ''' Edit operations overlap in file. '''

    def __init__(self, operation1_line, operation2_line):
        super().__init__(
            f"Operation at line {operation1_line} overlaps with "
            f"operation at line {operation2_line}" )
```

---

### 3. `messages/exceptions.py` (NEW)

**Errors to address: 2 TRY003**

**Locations:**
- `messages/core.py:239` - Unrecognized MIME type for classification
- `messages/core.py:319` - Derive extension from MIME type (unrecognized)

**Proposed exceptions:**

```python
class MimetypeInvalidity(__.Omnierror, ValueError):
    ''' MIME type is unrecognized or unsupported. '''

    def __init__(self, mimetype, operation):
        super().__init__(
            f"Cannot {operation}: unrecognized MIME type {mimetype!r}" )
```

---

### 4. `prompts/exceptions.py` (NEW)

**Errors to address: 2 TRY003**

**Locations:**
- `prompts/flavors/native.py:66` - Empty prompt rendered
- `prompts/flavors/native.py:156` - Could not find prompt by name

**Proposed exceptions:**

```python
class PromptRenderFailure(__.Omnierror, ValueError):
    ''' Prompt rendering produced invalid result. '''

    def __init__(self, reason):
        super().__init__(f"Prompt rendering failed: {reason}")

class PromptTemplateAbsence(__.Omnierror, FileNotFoundError):
    ''' Prompt template not found. '''

    def __init__(self, prompt_name):
        super().__init__(f"Could not find prompt {prompt_name!r}")
```

---

### 5. `gui/exceptions.py` (NEW)

**Errors to address: 2 TRY003**

**Locations:**
- `gui/utilities.py:29` - Component has no text attribute (set)
- `gui/utilities.py:37` - Component has no text attribute (get)

**Note:** Already covered by `gui/controls.py:116` under controls/exceptions.py

**Proposed exceptions:**

```python
class ComponentAttributeAbsence(__.Omnierror, AttributeError):
    ''' Component missing required attribute. '''

    def __init__(self, component_class, attribute_name, operation):
        super().__init__(
            f"Cannot {operation}: component of type {component_class!r} "
            f"has no {attribute_name!r} attribute" )
```

---

### 6. Extend `providers/exceptions.py`

**Errors to address: 18 TRY003**

#### Model Access Errors (4 errors)

**Locations:**
- `providers/interfaces.py:120` - Could not access named model
- `providers/interfaces.py:142` - Could not access default model
- `providers/core.py:206` - Invocation descriptor not dictionary
- `providers/core.py:208` - Invocation descriptor without name
- `providers/core.py:211` - Invocable not available

**Note:** Lines 206, 208, 211 already use `InvocationFormatError` - these are properly handled!

**Proposed additions:**

```python
class ModelInaccessibility(__.Omnierror, LookupError):
    ''' Failed to access model from provider. '''

    def __init__(self, provider_name, genus, model_name=None):
        if model_name:
            super().__init__(
                f"Could not access {genus.value} model {model_name!r} "
                f"on provider {provider_name!r}" )
        else:
            super().__init__(
                f"Could not access default {genus.value} model "
                f"on provider {provider_name!r}" )
```

#### Message Refinement Errors (11 errors)

**Locations:**
- `providers/clients/anthropic/conversers.py:158` - Cannot refine messages (no function)
- `providers/clients/anthropic/conversers.py:242` - Adjacent function results
- `providers/clients/anthropic/conversers.py:251` - Mixed function/tool call results
- `providers/clients/anthropic/conversers.py:375` - Unknown anchor role
- `providers/clients/openai/conversers.py:191` - Invocation requests count mismatch
- `providers/clients/openai/conversers.py:197` - Invocation requests count mismatch (tool_calls)
- `providers/clients/openai/conversers.py:336` - Can only have one invocation with legacy
- `providers/clients/openai/conversers.py:345` - Invocation requests is not sequence
- `providers/clients/openai/conversers.py:410` - Cannot create canister from unknown species
- `providers/clients/openai/conversers.py:792,795` - Unknown refiner action
- `providers/clients/openai/conversers.py:817` - Unknown anchor role
- `providers/clients/openai/conversers.py:845` - Mixed function/tool call results

**Proposed additions:**

```python
class MessageRefinementFailure(__.Omnierror, AssertionError):
    ''' Message refinement encountered invalid state. '''

    def __init__(self, reason):
        super().__init__(f"Cannot refine messages: {reason}")

class MessageRoleInvalidity(__.Omnierror, AssertionError, ValueError):
    ''' Invalid or unknown message role. '''

    def __init__(self, role, context):
        super().__init__(
            f"Unknown or invalid message role {role!r} in {context}")
```

#### Client Errors (3 errors)

**Locations:**
- `providers/clients/anthropic/clients.py:113` - Missing API key
- `providers/clients/openai/clients.py:115` - Missing API key
- `providers/utilities.py:133,137` - Incompatible provider genus/model configuration

**Proposed additions:**

```python
class ProviderCredentialsInavailability(__.Omnierror, LookupError):
    ''' Provider credentials not available. '''

    def __init__(self, provider_name, credential_name):
        super().__init__(
            f"Missing {credential_name!r} for provider {provider_name!r}" )

class ProviderConfigurationInvalidity(__.Omnierror, ValueError):
    ''' Provider configuration is invalid or incompatible. '''

    def __init__(self, reason):
        super().__init__(f"Invalid provider configuration: {reason}")
```

---

### 7. Extend `locations/exceptions.py`

**Errors to address: 1 TRY003**

**Location:**
- `locations/adapters/aiofiles.py:527` - Inode type not supported

**Proposed addition:**

```python
class InodeSpeciesNoSupport(__.SupportError):
    ''' Inode type not supported by entity. '''

    def __init__(self, inode_type, entity_name):
        super().__init__(
            f"Inode type {inode_type!r} not supported by {entity_name}" )
```

---

## Summary Statistics

### By Error Type
- **TRY002** (bare exception): 1 error → 1 custom exception class (inherits from `__.Omnierror`, `RuntimeError`)
- **TRY003** (long message): 34 errors → ~17 custom exception classes with semantic constructors
- **TRY004** (wrong exception type): 6 errors → 2 custom exception classes (inherit from `__.Omnierror`, `TypeError`)

**Important:** All 41 errors will be resolved with custom exception classes, not bare stdlib exceptions.

### By Module
- **controls/** (NEW): 8 exception classes for 12 errors
  - `ControlValueMisclassification`, `ControlElementMisclassification`
  - `ControlValueConstraintViolation`, `ControlArrayDimensionViolation`
  - `ControlArrayDefinitionInvalidity`, `ControlOptionValueInvalidity`
  - `ControlSpeciesIrrecognizability`, `ControlArrayCapacityViolation`
- **invocables/** (NEW): 2 exception classes for 3 errors
  - `DiceSpecificationInvalidity`, `EditContention`
- **messages/** (NEW): 1 exception class for 2 errors
  - `MimetypeInvalidity`
- **prompts/** (NEW): 2 exception classes for 2 errors
  - `PromptRenderFailure`, `PromptTemplateAbsence`
- **gui/** (NEW): 1 exception class for 2 errors
  - `ComponentAttributeAbsence`
- **providers/** (extend): 6 exception classes for 18 errors
  - `ModelInaccessibility`, `MessageRefinementFailure`
  - `MessageRoleInvalidity`, `ProviderCredentialsInavailability`
  - `ProviderConfigurationInvalidity`
- **locations/** (extend): 1 exception class for 1 error
  - `InodeSpeciesNoSupport`

**Total: 7 exception modules (5 new, 2 extended) with 21 new exception classes**

---

## Implementation Strategy

1. **Create exception modules** in order of dependency:
   - `controls/exceptions.py`
   - `invocables/exceptions.py`
   - `messages/exceptions.py`
   - `prompts/exceptions.py`
   - `gui/exceptions.py`

2. **Extend existing modules**:
   - `providers/exceptions.py` - Add 6 classes
   - `locations/exceptions.py` - Add 1 class

3. **Replace error raises** systematically by module

4. **Test coverage** - Ensure existing tests still pass with new exception types

---

## Notes

- Many errors already have semantic context in their messages - extraction into `__init__` parameters is straightforward
- Some errors marked with `# TODO: Fill out error` or `# TODO: Appropriate error classes` - these were anticipated
- Several errors in providers/core.py already properly use `InvocationFormatError`
- Pattern follows established conventions: inherit from `__.Omnierror` + relevant stdlib exception
- Some exceptions can be consolidated (e.g., multiple "adjacent function results" → single MessageRefinementError)
