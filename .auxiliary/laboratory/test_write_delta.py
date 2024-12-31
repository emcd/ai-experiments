#!/usr/bin/env python3

"""Test program for write_delta operations."""

import asyncio

from write_delta import Operation, Context, DeltaType, apply_delta_operations


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
        result = await apply_delta_operations(content, operations)
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
    return True
""",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(before=["def example():"]),
                content="    \"\"\"Example function.\"\"\"\n"
            )
        ],
        expected="""\
def example():
    \"\"\"Example function.\"\"\"
    return True
"""
    )
    
    # Test 2: Multiple operations
    await run_test(
        "Multiple operations",
        content="""\
class Example:
    def method1(self):
        return True
    
    def method2(self):
        return False
""",
        operations=[
            Operation(
                type=DeltaType.DELETE,
                context=Context(
                    before=[
                        "    def method2(self):",
                        "        return False"
                    ]
                ),
                length=2
            ),
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before=[
                        "    def method1(self):",
                        "        return True"
                    ]
                ),
                length=2,
                content="    def method1(self):\n        return 42\n"
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
    return True
""",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(before=None),
                content="\"\"\"Module docstring.\"\"\"\n\n"
            )
        ],
        expected="""\
\"\"\"Module docstring.\"\"\"

def example():
    return True
"""
    )
    
    # Test 4: End of file insertion
    await run_test(
        "End of file insertion",
        content="""\
def example():
    return True
""",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(
                    before=[
                        "def example():",
                        "    return True"
                    ],
                    after=None
                ),
                content="\ndef another():\n    return False\n"
            )
        ],
        expected="""\
def example():
    return True

def another():
    return False
"""
    )
    
    # Test 5: Multiple matches
    await run_test(
        "Multiple matches - second occurrence",
        content="""\
def repeat():
    return True

def also_repeat():
    return True

def something_else():
    pass
""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before=["    return True"],
                    match_occurrence=2
                ),
                length=1,
                content="    return False\n"
            )
        ],
        expected="""\
def repeat():
    return True

def also_repeat():
    return False

def something_else():
    pass
"""
    )
    
    # Test 6: Empty file operations
    await run_test(
        "Empty file operations",
        content="",
        operations=[
            Operation(
                type=DeltaType.INSERT,
                context=Context(before=None),
                content="#!/usr/bin/env python3\n\n\"\"\"Empty module.\"\"\"\n"
            )
        ],
        expected="""\
#!/usr/bin/env python3

\"\"\"Empty module.\"\"\"
"""
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
    pass
""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before=[
                        "def example():",
                        "    \"\"\"Example function.\"\"\"",
                        "",
                        "    # Some comment"
                    ]
                ),
                length=4,
                content="def example():\n    \"\"\"Example function.\"\"\"\n\n    return False\n"
            )
        ],
        expected="""\
def example():
    \"\"\"Example function.\"\"\"

    return False
def another():
    pass
"""
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
                context=Context(before=["#!/usr/bin/env python3"]),
                length=1
            ),
            Operation(
                type=DeltaType.REPLACE,
                context=Context(before=["    pass"]),
                length=1,
                content="    return True\n"
            )
        ],
        expected="""\

\"\"\"Module docstring.\"\"\"

def example():
    return True
"""
    )
    
    # Test 9: Invalid operations
    await run_test(
        "Invalid operations - delete beyond file end",
        content="""\
def example():
    pass
""",
        operations=[
            Operation(
                type=DeltaType.DELETE,
                context=Context(before=["def example():"]),
                length=5  # File only has 2 lines
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
                    before=[
                        "def second():",
                        "    pass",
                        "",
                        ""
                    ]
                ),
                length=4,
                content="def second():\n    return True\n"
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
    return value
""",
        operations=[
            Operation(
                type=DeltaType.REPLACE,
                context=Context(
                    before=[
                        "    value = 1",
                        "    value += 1"
                    ]
                ),
                length=2,
                content="    value = 42\n"
            )
        ],
        expected="""\
def example():
    value = 42
    return value
"""
    )


if __name__ == '__main__':
    asyncio.run(main())