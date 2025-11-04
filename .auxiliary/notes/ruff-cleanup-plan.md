# Ruff Linter Cleanup Plan

## Current Status

**Errors:** 28 of 175 (84% reduction)
**Progress:** 147 fixed/suppressed
**Auto-fixable:** 0 errors (8 with `--unsafe-fixes`)

**Remaining (28):**
```
 3  PLR2004  magic-value-comparison
 3  SLF001   private-member-access
 2  B008     function-call-in-default-argument
 2  PLW2901  redefined-loop-name
 2  RET503   implicit-return
 2  RET504   unnecessary-assign
 2  S101     assert
 2  S112     try-except-continue
 2  SIM102   collapsible-if
 2  SIM108   if-else-block-instead-of-if-exp
 2  SIM118   in-dict-keys
 1  PERF203  try-except-in-loop
 1  PLR1704  redefined-argument-from-local
 1  S311     suspicious-non-cryptographic-random-usage
 1  S702     mako-templates
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

### Phase 3.2: Deferred ⊘ (28 errors)
Code quality and security issues deferred as intentional design choices:
- **Code Quality (21):** PLR2004, SLF001, B008, PLW2901, RET503/504, SIM102/108/118, PERF203, PLR1704
- **Security (4):** S101, S112, S311, S702
- **Style (3):** All E501 resolved

**Recommendation:** Address opportunistically during refactoring work.

---

## Notes

- **Code Style:** Project does NOT use Black/Ruff formatting. Manual line breaks respect 79-character limit.
- **Namespace Hygiene:** Use underscore-prefixed imports (`_Symbol`) for type-only imports.
- **Testing:** Verify application functionality after changes.
- **Incremental Progress:** Commit after each phase for easy rollback.
