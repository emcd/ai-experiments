# Pyright Complex Fixes - Deferred Items

This document tracks Pyright errors that cannot be fixed with simple type annotations using built-in types or types available via `_` imports. These fixes are deferred as they would require:
- Additional imports that would pollute the public namespace
- Logic refactoring
- Architectural changes
- More complex type definitions

## Format

For each deferred fix, we document:
- **Package/Module**: The affected module
- **Error Type**: The Pyright error code
- **Issue**: Description of the problem
- **Reason for Deferral**: Why it can't be fixed simply
- **Potential Solution**: Suggestions for future fix (optional)

---

## Deferred Fixes

### aiwb.apiserver.cli - Method Override Incompatibilities
**Error Type**: `reportIncompatibleMethodOverride`, `reportIncompatibleVariableOverride`

**Issues**:
1. `ExecuteServerCommand.__call__` method has parameter type mismatch with base class
2. `Cli.command` attribute overrides base class with incompatible union type

**Reason for Deferral**: These require understanding the class hierarchy and potentially refactoring the inheritance structure or using protocol types.

**Potential Solution**:
- May need to use `@typing.override` with proper generic types
- Could require adjusting the base class definitions
- May need Protocol definitions for proper structural typing

### aiwb.apiserver.state - Complex kwargs Unpacking
**Error Type**: `reportArgumentType`

**Issue**:
The `Globals.from_base` method uses `**base.as_dictionary()` unpacking at line 42, but Pyright cannot properly type-check the unpacked dictionary against the `__init__` parameters.

**Reason for Deferral**:
- Pyright has limited ability to type-check dictionary unpacking with `**kwargs`
- Would require either TypedDict definitions or refactoring the unpacking logic
- The `.as_dictionary()` method would need to return a more precisely typed dictionary

**Potential Solution**:
- Create a TypedDict that matches the `__init__` signature
- Use explicit parameter passing instead of dictionary unpacking
- Add type: ignore comments if the runtime behavior is correct

### aiwb.apiserver.state - Method Override Parameter Mismatch
**Error Type**: `reportIncompatibleMethodOverride`

**Issue**:
The `from_base` classmethod has parameter type mismatches and missing parameters compared to the base class.

**Reason for Deferral**: Requires understanding the base class signature and potentially using generics or Protocol types properly.

**Potential Solution**: Review base class definition and ensure parameter compatibility.

### aiwb.codecs.json - Non-exhaustive Match Statement
**Error Type**: `reportMatchNotExhaustive`

**Issue**:
The match statement in the `loads` function (around line 41) only handles 4 specific characters: `{`, `}`, `[`, `]`. Pyright reports that it doesn't exhaustively handle all possible string values.

**Reason for Deferral**:
- Requires code modification beyond type annotations (adding `case _: pass`)
- While this wouldn't change the logic (unmatched cases already implicitly pass), it's a code change rather than a pure type annotation

**Potential Solution**:
- Add `case _: pass` as the last case in the match statement
- This makes the match exhaustive without changing behavior

### aiwb.vectorstores - Multiple Complex Type Issues
**Error Types**: `reportUnknownVariableType`, `reportUnknownMemberType`, `reportUnknownParameterType`, `reportMatchNotExhaustive`

**Issues**:
1. Abstract method `Factory.client_from_descriptor` missing return type (requires understanding return type pattern)
2. Module-level `preparers` Dictionary has Unknown type arguments
3. Lists and tuples with Unknown element types due to type inference limitations
4. Non-exhaustive match statements for GenericResult (would require adding `case _: pass`)
5. Container types with Unknown type arguments that propagate through function returns

**Reason for Deferral**:
- Most errors stem from incomplete type information in container types and generic results
- Would require extensive TypeVar usage or more precise type annotations throughout
- Match statement exhaustiveness requires code modifications beyond type annotations
- The `preparers` dictionary would need proper type arguments but contains heterogeneous values

**Potential Solution**:
- Add proper return type to abstract method (possibly a generic result type)
- Add type arguments to module-level `preparers` dictionary
- Consider using TypedDict or more specific container types
- Add `case _: pass` to match statements

### aiwb.application - Complex Class Hierarchy and kwargs Issues
**Error Types**: `reportUnknownParameterType`, `reportUnknownVariableType`, `reportIndexIssue`, `reportArgumentType`

**Issues**:
1. Signal handler parameter types require importing from signal module
2. Multiple issues with abstract class instantiation
3. Container types with Unknown type arguments
4. Complex kwargs unpacking in state.py (similar to apiserver.state)
5. Mapping vs dict type compatibility issues

**Reason for Deferral**:
- Signal handler would require importing signal types (Signals enum or int)
- Abstract class instantiation errors suggest design issues beyond type annotations
- State class has same complex kwargs unpacking issues as apiserver
- Many errors cascade from upstream type inference issues

**Potential Solution**:
- Add signal module imports for proper signal handler typing
- Review abstract class usage and ensure proper implementation
- Fix kwargs unpacking with explicit parameter passing or TypedDict
- Add type arguments to container types

---

## Common Patterns Requiring Complex Fixes

### Pattern 1: Generic Type Arguments
**Error Type**: `reportMissingTypeArgument`

Many generic types (list, dict, set, etc.) are used without type arguments. Fixing these often requires:
- Understanding the actual runtime types being used
- Potentially adding type parameters that reference types from external modules
- May require refactoring to make types more explicit

### Pattern 2: Unknown Parameter Types
**Error Type**: `reportUnknownParameterType`

Functions that receive parameters from external libraries or dynamic sources. Fixing these may require:
- Type stubs for third-party libraries
- Protocol definitions
- TypeVar or Generic usage

### Pattern 3: Unknown Member/Variable Types
**Error Types**: `reportUnknownMemberType`, `reportUnknownVariableType`

Variables whose types can't be inferred from context. Common in:
- Dynamic attribute access
- Complex factory patterns
- Callback functions with unclear signatures

---

## Statistics

- **Total Complex Fixes Deferred**: 0
- **By Error Type**: (To be updated)
- **By Package**: (To be updated)

---

## Review Process

When marking a fix as "complex" and deferring it:
1. Document it in this file with clear description
2. Add a `# TODO: Pyright - <brief description>` comment in the code
3. Continue with other fixable errors in the module
4. Revisit complex fixes in a later phase after simpler fixes are complete
