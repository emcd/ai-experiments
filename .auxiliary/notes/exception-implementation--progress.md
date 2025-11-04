# Exception Implementation Progress

## Context and References

- **Implementation Title**: Custom Exception Infrastructure for TRY* Error Resolution
- **Start Date**: 2025-11-03
- **Reference Files**:
  - `.auxiliary/notes/exception-design-analysis.md` - Complete design specifications for 21 exception classes
  - `.auxiliary/notes/ruff-cleanup-plan.md` - Overall Ruff cleanup strategy and progress tracking
  - `sources/aiwb/locations/exceptions.py` - Existing exception pattern reference
  - `sources/aiwb/providers/exceptions.py` - Existing exception pattern reference
  - `.auxiliary/instructions/practices-python.rst` - Python development practices
  - `.auxiliary/instructions/nomenclature.rst` - Naming conventions
- **Design Documents**: exception-design-analysis.md
- **Session Notes**: TodoWrite tracking for current session tasks

## Design and Style Conformance Checklist

- [ ] Module organization follows practices guidelines
- [ ] Function signatures use wide parameter, narrow return patterns
- [ ] Type annotations comprehensive with TypeAlias patterns
- [ ] Exception handling follows Omniexception → Omnierror hierarchy
- [ ] Naming follows nomenclature conventions
- [ ] Immutability preferences applied
- [ ] Code style follows formatting guidelines (spaces inside delimiters, etc.)

## Implementation Progress Checklist

### Phase 1: Controls Module (12 errors)
- [ ] `controls/exceptions.py` - Create module with 8 exception classes
- [ ] `controls/core.py` - Update to use new exceptions
- [ ] `gui/controls.py` - Update to use new exceptions
- [ ] Phase 1 testing: `hatch run aiwb-application inspect configuration`

### Phase 2: Smaller Modules (9 errors)
- [ ] `invocables/exceptions.py` - Create module with 2 exception classes
- [ ] `invocables/ensembles/probability/calculations.py` - Update to use new exceptions
- [ ] `invocables/ensembles/io/differences.py` - Update to use new exceptions
- [ ] `messages/exceptions.py` - Create module with 1 exception class
- [ ] `messages/core.py` - Update to use new exceptions
- [ ] `prompts/exceptions.py` - Create module with 2 exception classes
- [ ] `prompts/flavors/native.py` - Update to use new exceptions
- [ ] `gui/exceptions.py` - Create module with 1 exception class
- [ ] `gui/utilities.py` - Update to use new exceptions
- [ ] Phase 2 testing: `hatch run aiwb-application inspect configuration`

### Phase 3: Provider and Location Extensions (19 errors)
- [ ] `providers/exceptions.py` - Extend with 6 exception classes
- [ ] `providers/interfaces.py` - Update to use new exceptions
- [ ] `providers/clients/anthropic/conversers.py` - Update to use new exceptions
- [ ] `providers/clients/anthropic/clients.py` - Update to use new exceptions
- [ ] `providers/clients/openai/conversers.py` - Update to use new exceptions
- [ ] `providers/clients/openai/clients.py` - Update to use new exceptions
- [ ] `providers/utilities.py` - Update to use new exceptions
- [ ] `locations/exceptions.py` - Extend with 1 exception class
- [ ] `locations/adapters/aiofiles.py` - Update to use new exception
- [ ] Phase 3 testing: `hatch run aiwb-application inspect configuration`

## Quality Gates Checklist

- [ ] Linters pass (`hatch --env develop run linters`)
- [ ] Type checker passes
- [ ] Tests pass (`hatch --env develop run testers`)
- [ ] Code review ready

## Decision Log

- 2025-11-03: Phased implementation approach - Implementing in 3 phases (controls, smaller modules, providers/locations) with testing between phases to catch breakage early

## Handoff Notes

**Current State**: Phases 1 and 2 COMPLETE - 15 exception classes implemented across 6 modules, all tested successfully

**Completed Work**:
- Phase 1: controls module (8 exceptions) + gui/controls.py update - TESTED ✓
- Phase 2: invocables (2), messages (1), prompts (2), gui (1) modules - TESTED ✓
- Fixed `aiwb/__/__init__.py` to export `Omnierror`, `Omniexception`, `SupportError`
- All TRY002, TRY003, TRY004 errors for Phase 1 & 2 modules resolved

**Next Steps**:
1. Phase 3: Extend providers/exceptions.py (6 new exception classes)
2. Update 6 provider source files to use new exceptions
3. Extend locations/exceptions.py (1 new exception class)
4. Update locations/adapters/aiofiles.py
5. Final testing and linter validation

**Known Issues**: None - all tests passing

**Context Dependencies**:
- All exception classes inherit from both `__.Omnierror` and appropriate stdlib exception
- Constructor parameters are semantic (domain objects, values, constraints), not formatted messages
- Exception names use descriptive nouns without "Error" suffix
- Project spacing conventions followed (spaces inside delimiters)
- Import pattern: `from . import exceptions as _exceptions` or `from .exceptions import SomeException as _SomeException`
