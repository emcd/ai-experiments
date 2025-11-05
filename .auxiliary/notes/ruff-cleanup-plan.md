# Ruff Linter Cleanup Plan

## Current Status

**Errors:** 7 of 175 (96% reduction)
**Progress:** 168 fixed/suppressed
**Auto-fixable:** 0 errors (8 with `--unsafe-fixes`)

**Remaining (7 in sources/):**
```
 2  B008     function-call-in-default-argument
 2  SIM102   collapsible-if
 2  SIM118   in-dict-keys
 1  SLF001   private-member-access
```

---

## Completed Work

### Phase 1: Auto-fixes ✓ (39 errors)
- RUF100 (36): Unused noqa directives
- RET502/505 (3): Implicit/superfluous returns
- SIM114 (5): Excluded - violates project style

### Phase 2: Moderate Cleanup ✓ (84 errors)
- **E501 (23):** Line too long - wrapped at logical boundaries
- **TRY* (52):** Exception handling
  - Created custom exception infrastructure
  - Fixed import spaghetti via `__` re-export modules
  - See `.auxiliary/notes/cascades.md` for pattern
- **RUF012 (9):** Mutable class defaults - added `_ClassVar` annotations
- **PERF401:** Manual list comprehension - fixed/suppressed for readability
- **SIM103:** Needless bool - fixed/suppressed for readability

### Phase 3.1: Complexity Metrics ✓ (22 errors)
All suppressed with `# noqa` and appropriate documentation:
- **PLR0911/912/915 (18):** Too many returns/branches/statements - 12 functions
- **PLR0913 (3):** Too many arguments - 3 functions
- **C901:** Complex structure - covered above
- **E501 (1):** Line too long from TODO comment - rewrapped

**Refactoring candidates (2 with TODO comments):**
- `VcsIgnoreFilter.__call__` - HIGH priority (data-driven refactoring)
- `honor_inode_attributes` - MEDIUM priority (extract helpers)

### Phase 3.2: PLR Refactor Issues ✓ (4 errors)
All PLR issues resolved by defining named constants and renaming variables:
- **PLR1704 (1):** Redefined argument - renamed `exc` to `exception` in `gui/updaters.py:101`
- **PLR2004 (3):** Magic value comparisons - defined module-level constants:
  - `TOKEN_USAGE_WARNING_THRESHOLD = 0.75` in `gui/updaters.py`
  - `DICE_SIDES_MINIMUM = 4` in `invocables/ensembles/probability/calculations.py`
  - `FILE_SIZE_MAXIMUM = 40000` in `invocables/ensembles/summarization/operations.py`

### Phase 3.3: RET Return Statement Issues ✓ (4 errors)
All RET issues resolved by suppressing or adding explicit returns:
- **RET504 (2):** Unnecessary assignment - suppressed with `# noqa: RET504`:
  - `gui/invocables.py:49` - `requests` variable aids debugging
  - `providers/preparation.py:55` - `clients` variable aids debugging
- **RET503 (2):** Missing explicit return - added `return None  # TODO: Raise error.`:
  - `vectorstores/clients/chroma.py:67` - Non-Path locations not yet implemented
  - `vectorstores/clients/faiss.py:61` - Non-Path locations not yet implemented

### Phase 3.4: B905 Zip Strict Parameter ✓ (13 errors)
All B905 issues resolved by adding explicit `strict=True` parameter:
- `application/preparation.py:55` - zip names with module attributes
- `gui/components.py:102` - zip icon filenames with content
- `invocables/core.py:191` - zip ensemble names with results
- `prompts/core.py:165` - zip store names, descriptors with results
- `prompts/flavors/native.py:110` - zip definition files with results
- `providers/preparation.py:71,75,77` - zip client names/descriptors with providers/results (3 instances)
- `providers/preparation.py:105` - zip provider names with results
- `providers/utilities.py:226` - zip subdirectories with configurations
- `vectorstores/core.py:100,102` - zip client factories/names/descriptors with results (2 instances)
- `vectorstores/core.py:129` - zip factory names with results

### Phase 3.5: Deferred ⊘ (7 errors)
Code quality issues deferred as intentional design choices:
- **B008 (2):** Function call in argument defaults - MappingProxyType for immutability
- **SIM102 (2):** Collapsible if statements - readability preference
- **SIM118 (2):** Unnecessary .keys() call - explicit iteration style
- **SLF001 (1):** Private member access - intentional for testing/introspection

**Recommendation:** Address opportunistically during refactoring work.

---

## Notes

- **Code Style:** Project does NOT use Black/Ruff formatting. Manual line breaks respect 79-character limit.
- **Namespace Hygiene:** Use underscore-prefixed imports (`_Symbol`) for type-only imports.
- **Testing:** Verify application functionality after changes.
- **Incremental Progress:** Commit after each phase for easy rollback.
