#!/usr/bin/env python3

"""Tests for two-pass implementation of write_delta operations."""

import asyncio

from write_delta_2pass import Operation, Context, DeltaType, write_delta


async def run_test(
    name: str,
    content: str,
    operations: list[Operation],
    expected: str | None = None
) -> None:
    """Run a single test case."""
    print(f"\nTest: {name}")
    print("Input:")
    print("```")
    print(content, end='')
    print("```")

    try:
        result = await write_delta(content, operations)
        print("\nOutput:")
        print("```")
        print(result, end='')
        print("```")

        if expected is not None:
            if result == expected:
                print("\nResult: ✅ Matches expected output")
            else:
                print("\nResult: ❌ Does not match expected output")
                print("\nExpected:")
                print("```")
                print(expected, end='')
                print("```")
                print("\nDifference analysis:")
                if len(result) != len(expected):
                    print(f"Length mismatch: result={len(result)}, expected={len(expected)}")
                for i, (r, e) in enumerate(zip(result, expected)):
                    if r != e:
                        print(f"First difference at position {i}:")
                        print(f"Result: {repr(result[i:i+10])}")
                        print(f"Expected: {repr(expected[i:i+10])}")
                        break
    except Exception as e:
        print(f"\nError: {e}")


async def main():
    """Run test cases."""
    # Test 1: Simple insertion
    await run_test(
        "Simple insertion",
        content="""\
def example():
    return True""",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(
                    before="""\
def example():""",
                    after="""\
    return True"""
                ),
                content="    \"\"\"Example function.\"\"\""
            )
        ],
        expected="""\
def example():
    \"\"\"Example function.\"\"\"
    return True"""
    )

    # Test 2: Multiple operations
    await run_test(
        "Multiple operations",
        content="""\
class Example:
    def method1(self):
        return True

    def method2(self):
        return False""",
        operations=[
            Operation(
                type=DeltaType.DELETE,
                context=Context(
                    before="""\
class Example:
    def method1(self):
        return True
""",
                    after=None  # EOF
                )
            ),
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="class Example:",
                    after=""  # Empty line after the method
                ),
                content="    def method1(self):\n        return 42"
            )
        ],
        expected="""\
class Example:
    def method1(self):
        return 42
"""
    )

    # Test 3: Start of file insertion
    await run_test(
        "Start of file insertion",
        content="""\
def example():
    return True""",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(
                    before=None,  # BOF
                    after="""\
def example():
    return True"""
                ),
                content="\"\"\"Module docstring.\"\"\"\n"
            )
        ],
        expected="""\
\"\"\"Module docstring.\"\"\"

def example():
    return True"""
    )

    # Test 4: End of file insertion
    await run_test(
        "End of file insertion",
        content="""\
def example():
    return True""",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(
                    before="""\
def example():
    return True""",
                    after=None  # EOF
                ),
                content="\ndef another():\n    return False"
            )
        ],
        expected="""\
def example():
    return True

def another():
    return False"""
    )

    # Test 5: Multiple matches
    await run_test(
        "Multiple matches - second occurrence",
        content="""\
def repeat():
    return True

def repeat():
    return True

def something_else():
    pass""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="def repeat():",
                    after="",  # Empty line after function
                    match_occurrence=2
                ),
                content="    return False"
            )
        ],
        expected="""\
def repeat():
    return True

def repeat():
    return False

def something_else():
    pass"""
    )

    # Test 6: Empty file operations
    await run_test(
        "Empty file operations",
        content="",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(
                    before=None,  # BOF
                    after=None
                ),
                content="#!/usr/bin/env python3\n\n\"\"\"Empty module.\"\"\""
            )
        ],
        expected="""\
#!/usr/bin/env python3

\"\"\"Empty module.\"\"\""""
    )

    # Test 7: Operations with empty lines in context
    await run_test(
        "Operations with empty lines in context",
        content="""\
def example():
    \"\"\"Example function.\"\"\"

    # Some comment
    return True

def another():
    pass""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="""\
def example():
    \"\"\"Example function.\"\"\"""",
                    after="def another():"
                ),
                content="    return False\n"
            )
        ],
        expected="""\
def example():
    \"\"\"Example function.\"\"\"
    return False

def another():
    pass"""
    )

    # Test 8: Operations near file boundaries
    await run_test(
        "Operations near file boundaries",
        content="""\
#!/usr/bin/env python3

\"\"\"Module docstring.\"\"\"

def example():
    pass""",
        operations=[
            Operation(
                type=DeltaType.DELETE,
                context=Context(
                    before=None,  # BOF
                    after="\"\"\"Module docstring.\"\"\""
                )
            ),
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="\"\"\"Module docstring.\"\"\"",
                    after=None   # EOF
                ),
                content="\ndef example():\n    return True"
            )
        ],
        expected="""\
\"\"\"Module docstring.\"\"\"

def example():
    return True"""
    )

    # Test 9: Invalid operations
    await run_test(
        "Invalid operations - delete beyond file end",
        content="""\
def example():
    pass""",
        operations=[
            Operation(
                type=DeltaType.DELETE,
                context=Context(
                    before=None,  # BOF
                    after=None   # EOF
                )
            )
        ],
        expected="""\
"""
    )

    # Test 10: Multiple empty lines in content
    await run_test(
        "Multiple empty lines in content",
        content="""\
def first():
    pass


def second():
    pass


def third():
    pass""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="""\
def first():
    pass""",
                    after="def third():"
                ),
                content="\ndef second():\n    return True\n"
            )
        ],
        expected="""\
def first():
    pass

def second():
    return True

def third():
    pass"""
    )

    # Test 11: Overlapping contexts
    await run_test(
        "Overlapping contexts",
        content="""\
def example():
    value = 1
    value += 1
    return value""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="def example():",
                    after="    return value"
                ),
                content="    value = 42"
            )
        ],
        expected="""\
def example():
    value = 42
    return value"""
    )

    # Test 12: Replace at beginning of file
    await run_test(
        "Replace at beginning of file",
        content="""\
old_line1
old_line2
keep_this
last_line""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before=None,  # BOF
                    after="keep_this"
                ),
                content="new_line1\nnew_line2"
            )
        ],
        expected="""\
new_line1
new_line2
keep_this
last_line"""
    )

    # Test 13: Delete at beginning of file
    await run_test(
        "Delete at beginning of file",
        content="""\
remove_this1
remove_this2
keep_this
last_line""",
        operations=[
            Operation(
                type=DeltaType.DELETE,
                context=Context(
                    before=None,  # BOF
                    after="keep_this"
                )
            )
        ],
        expected="""\
keep_this
last_line"""
    )

    # Test 14: Insert with after context
    await run_test(
        "Insert with after context",
        content="""\
def example():
    x = 1
    return x""",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(
                    before="    x = 1",
                    after="    return x"
                ),
                content="    y = 2"
            )
        ],
        expected="""\
def example():
    x = 1
    y = 2
    return x"""
    )


    # Test 15: Unicode content
    await run_test(
        "Unicode content",
        content="""\
def greet(name):
    return f'Hello, {name}! 👋'""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="def greet(name):",
                    after=""
                ),
                content="    print('¡Hola! 🌎')"
            )
        ],
        expected="""\
def greet(name):
    print('¡Hola! 🌎')"""
    )


    # Test 16: Windows line endings
    await run_test(
        "Windows line endings",
        content="line1\r\nline2\r\nline3",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="line1\r",
                    after="line3"
                ),
                content="modified\r"
            )
        ],
        expected="line1\r\nmodified\r\nline3"
    )

    # Test 17: Overlapping operations (should fail)
    await run_test(
        "Overlapping operations",
        content="""\
def example():
    x = 1
    y = 2
    z = 3
    return x + y + z""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="    x = 1\n    y = 2",
                    after="    z = 3"
                ),
                content="    total = 0"
            ),
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before="    y = 2\n    z = 3",
                    after="    return"
                ),
                content="    result = 42"
            )
        ],
        expected="Error: Operation at line 1 has after context that overlaps with operation at line 2"
    )


if __name__ == '__main__':
    asyncio.run(main())
