% if 'python-custom' == variables.style:
Please reformat the above Python code according to the following guidelines.
Note that _whitespace is extremely important_ in this format and you *must*
pay careful attention to it.

* One space after each opening delimiter. `(`, `[`, and `{`.
  One space before each closing delimiter. `)`, `]`, and `}`.

* Empty tuple is `( )`. Empty list is `[ ]` and not `[]`.
  Empty dict is `{ }` and not `{}`.

* Use `"` around f-strings and string literals that use the `format`
  method. Use `'` around all other string literals.

* One space before and one space after `=` for assignments and keyword
  argument defaults.

* Prefer a single line for simple conditionals and exception handler
  branches.

<%text>
## Example

Convert this:
```
def fibonacci(n, memo={}):
  if n in memo:
      return memo[n]
  if n <= 2:
      return 1
  memo[n] = fibonacci(n - 1, memo) + fibonacci(n - 2, memo)
  return memo[n]
```

into this:
```
def fibonacci( n, memo = { } ):
    if n in memo: return memo[ n ]
    if n <= 2: return 1
    memo[ n ] = fibonacci( n - 1, memo ) + fibonacci( n - 2, memo )
    return memo[ n ]
```
</%text>

List how the formatting rules apply to each piece of code _before_ generating
the reformatted code. I.e., do not display the reformatted code until after
you have displayed an understanding of what needs to change.
% endif
