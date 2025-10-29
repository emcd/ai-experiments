# Ruff Linter Cleanup Plan

## Overview

The project currently has 175 Ruff linter errors to address before achieving linter-clean status, which is a prerequisite for aligning with the standard Copier template for Python projects.

**Total Issues:** 175 errors
**Auto-fixable:** 44 errors (with 14 more via `--unsafe-fixes`)

## Error Distribution

```
36  RUF100  [*] unused-noqa
34  TRY003  [ ] raise-vanilla-args
21  E501    [ ] line-too-long
 9  RUF012  [ ] mutable-class-default
 7  PLR0911 [ ] too-many-return-statements
 6  SIM103  [ ] needless-bool
 6  TRY004  [ ] type-check-without-type-error
 5  PERF401 [ ] manual-list-comprehension
 4  PLR0912 [ ] too-many-branches
 4  PLR0915 [ ] too-many-statements
 4  SIM114  [*] if-with-same-arms
 3  C901    [ ] complex-structure
 3  PLR0913 [ ] too-many-arguments
 3  PLR2004 [ ] magic-value-comparison
 3  RET502  [*] implicit-return-value
 3  SLF001  [ ] private-member-access
 2  B008    [ ] function-call-in-default-argument
 2  PLW2901 [ ] redefined-loop-name
 2  RET503  [ ] implicit-return
 2  RET504  [ ] unnecessary-assign
 2  S101    [ ] assert
 2  S112    [ ] try-except-continue
 2  SIM102  [ ] collapsible-if
 2  SIM108  [ ] if-else-block-instead-of-if-exp
 2  SIM118  [ ] in-dict-keys
 1  PERF203 [ ] try-except-in-loop
 1  PLR1704 [ ] redefined-argument-from-local
 1  RET505  [*] superfluous-else-return
 1  S311    [ ] suspicious-non-cryptographic-random-usage
 1  S702    [ ] mako-templates
 1  TRY002  [ ] raise-vanilla-class
```

## Phased Cleanup Strategy

### Phase 1: Quick Wins (Auto-fixable) ⚡

These are safe, mechanical fixes that Ruff can handle automatically.

**Command:** `ruff check --fix sources/aiwb`

#### 1.1 RUF100 - Unused `noqa` directives (36 errors) ✓
**Priority:** HIGH - Completely safe, good cleanup
**Effort:** Minimal
**Risk:** None
**Status:** Ready to auto-fix

These are leftover lint suppressions that are no longer needed. Safe to remove.

#### 1.2 SIM114 - If with same arms (4 errors)
**Priority:** HIGH
**Effort:** Minimal
**Risk:** Low (requires review)
**Status:** Review auto-fixes carefully

Detects conditional branches with identical code that can be simplified.

#### 1.3 RET502/505 - Implicit/superfluous returns (4 errors)
**Priority:** HIGH
**Effort:** Minimal
**Risk:** Low (requires review)
**Status:** Review auto-fixes carefully

- RET502: Functions with explicit return in some paths but not others
- RET505: Unnecessary `else` after `return`

**Action Items:**
- [ ] Run `ruff check --fix sources/aiwb`
- [ ] Review the diff carefully, especially SIM114 and RET502/505
- [ ] Test: `python -m aiwb.application inspect configuration`
- [ ] Test: `python -m aiwb.clicore`
- [ ] Commit with message: "Apply Ruff auto-fixes (Phase 1: RUF100, SIM114, RET502/505)"

**Expected Impact:** ~44 errors fixed (25% reduction)

---

### Phase 2: Moderate Cleanup 🔧

Mechanical fixes that require human judgment and review.

#### 2.1 E501 - Line too long (21 errors)
**Priority:** MEDIUM
**Effort:** Moderate
**Risk:** Low
**Note:** Cannot use `ruff format` - project follows different style than Black

Manual fixes required:
- Split long lines at logical boundaries
- Respect existing code style (not Black-style)
- May require restructuring some expressions

#### 2.2 TRY003 - Raise vanilla args (34 errors)
**Priority:** MEDIUM
**Effort:** High
**Risk:** Low

Add descriptive error messages to exception raises:
```python
# Before
raise ValueError

# After
raise ValueError("Invalid configuration: expected bool, got {type(value)}")
```

#### 2.3 RUF012 - Mutable class defaults (9 errors)
**Priority:** HIGH
**Effort:** Low
**Risk:** Medium (behavioral change)

Replace mutable defaults with `field(default_factory=...)`:
```python
# Before
class Foo:
    items: list = []

# After
from dataclasses import field
class Foo:
    items: list = field(default_factory=list)
```

#### 2.4 PERF401 - Manual list comprehension (5 errors)
**Priority:** LOW
**Effort:** Low
**Risk:** Low

Use `list.extend()` instead of loops with `append()`:
```python
# Before
for item in items:
    result.append(transform(item))

# After
result.extend(transform(item) for item in items)
```

#### 2.5 SIM103 - Needless bool (6 errors)
**Priority:** LOW
**Effort:** Low
**Risk:** Low

Simplify boolean expressions:
```python
# Before
return True if condition else False

# After
return condition
```

#### 2.6 TRY004 - Type check without TypeError (6 errors)
**Priority:** MEDIUM
**Effort:** Low
**Risk:** Low

Use `TypeError` for type validation:
```python
# Before
if not isinstance(value, bool):
    raise ValueError

# After
if not isinstance(value, bool):
    raise TypeError(f"Expected bool, got {type(value)}")
```

**Action Items:**
- [ ] 2.1: Fix line-too-long errors manually
- [ ] 2.2: Add descriptive error messages (can be done incrementally)
- [ ] 2.3: Fix mutable class defaults (test carefully)
- [ ] 2.4: Use list.extend() pattern
- [ ] 2.5: Simplify boolean expressions
- [ ] 2.6: Use TypeError for type checks

---

### Phase 3: Architectural (Optional/Later) 🏗️

These may indicate design issues and can be deferred or left as-is if they reflect intentional design choices.

#### 3.1 Code Complexity (15 errors)
- PLR0911: Too many return statements (7 errors)
- PLR0912: Too many branches (4 errors)
- PLR0915: Too many statements (4 errors)

**Recommendation:** Consider for refactoring but not critical. May indicate complex business logic that's inherently complicated.

#### 3.2 C901 - Complex structure (3 errors)
**Recommendation:** Review for potential simplification, but may be acceptable complexity.

#### 3.3 PLR0913 - Too many arguments (3 errors)
**Recommendation:** Consider parameter objects or builder patterns, but not urgent.

#### 3.4 Other Low-Priority Issues
- PLR2004: Magic value comparison (3)
- SLF001: Private member access (3)
- B008: Function call in default argument (2)
- PLW2901: Redefined loop name (2)
- RET503/504: Implicit return / unnecessary assign (4)
- S101/S112: Assert / try-except-continue (4)
- SIM102/108/118: Various simplifications (6)
- Others: Single occurrences (5)

**Recommendation:** Address opportunistically during other refactoring work.

---

## Execution Plan

### Immediate (This Session)
1. Execute Phase 1 auto-fixes
2. Review and commit

### Near-term (Next 1-2 Sessions)
1. Phase 2.1: Fix line-too-long errors
2. Phase 2.3: Fix mutable class defaults
3. Phase 2.6: Use TypeError for type checks
4. Phase 2.4: Apply list.extend() pattern
5. Phase 2.5: Simplify boolean expressions

### Medium-term (As Time Permits)
1. Phase 2.2: Add descriptive error messages (34 errors - can be done incrementally)

### Long-term (Future Consideration)
1. Phase 3: Review architectural issues during larger refactoring efforts

---

## Success Criteria

- [ ] All Phase 1 issues resolved (44 errors)
- [ ] All Phase 2 issues resolved (81 errors)
- [ ] `ruff check sources/aiwb` returns only Phase 3 issues (50 errors) or clean
- [ ] All tests pass
- [ ] Application runs correctly (`aiwb-application` and `aiwb-clicore` commands work)

---

## Notes

- **Code Style:** This project does NOT use Black/Ruff formatting. Manual line breaks must respect existing style.
- **Testing:** After each phase, verify:
  - `python -m aiwb.application inspect configuration`
  - `python -m aiwb.clicore`
  - Full test suite (when available)
- **Incremental Progress:** Commit after each phase or sub-phase for easy rollback if needed.
- **Documentation:** Update this file as phases are completed.

---

## Status Tracking

- [x] Phase 1.1: RUF100 - Unused noqa directives (36 errors fixed)
- [x] Phase 1.2: SIM114 - If with same arms (EXCLUDED - violates project style)
- [x] Phase 1.3: RET502/505 - Implicit/superfluous returns (3 errors fixed)
- **Phase 1 Complete: 39 errors fixed, 131 remaining (excluding 5 SIM114)**
- **Note:** SIM114 added to pyproject.toml ignore list
- [ ] Phase 2.1: E501 - Line too long
- [ ] Phase 2.2: TRY003 - Raise vanilla args
- [ ] Phase 2.3: RUF012 - Mutable class defaults
- [ ] Phase 2.4: PERF401 - Manual list comprehension
- [ ] Phase 2.5: SIM103 - Needless bool
- [ ] Phase 2.6: TRY004 - Type check without TypeError
- [ ] Phase 3: Architectural issues (deferred)
