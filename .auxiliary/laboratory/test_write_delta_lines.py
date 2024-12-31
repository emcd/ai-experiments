#!/usr/bin/env python3

"""Tests for line number-based implementation of write_delta operations."""

import asyncio

from write_delta_lines import Operation, DeltaType, write_delta


async def run_test(
    name: str,
    content: str,
    operations: list[Operation],
    expected: str
) -> None:
    """Run a single test case.
    
    Args:
        name: Name of the test case
        content: Input content to modify
        operations: List of operations to apply
        expected: Expected output content or error message
                 (error messages should start with "Error: ")
    """
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
        
        if expected.startswith("Error: "):
            print("\nResult: ❌ Expected error but got success")
            print(f"Expected: {expected}")
            return
            
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
        error_msg = f"Error: {str(e)}"
        print(f"\n{error_msg}")
        if expected.startswith("Error: "):
            if error_msg == expected:
                print("Result: ✅ Matches expected error")
            else:
                print("Result: ❌ Error message mismatch")
                print(f"Expected: {expected}")
        else:
            print("Result: ❌ Unexpected error")


async def main():
    """Run test cases."""

    # Test 1: Simple insertion at specific line
    await run_test(
        "Simple insertion at line",
        content="""\
def example():
    return True""",
        operations=[
            Operation(
                opcode=DeltaType.INSERT,
                start=1,  # After line 1
                content='    """Example function."""'
            )
        ],
        expected='''\
def example():
    """Example function."""
    return True'''
    )

    # Test 2: Multiple operations with line numbers
    await run_test(
        "Multiple operations with line numbers",
        content="""\
class Example:
    def method1(self):
        return True

    def method2(self):
        return False""",
        operations=[
            Operation(
                opcode=DeltaType.DELETE,
                start=5,  # "def method2"
                end=6     # "return False"
            ),
            Operation(
                opcode=DeltaType.REPLACE,
                start=2,  # "def method1"
                end=3,    # "return True"
                content='    def method1(self):\n        return 42'
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
                opcode=DeltaType.INSERT,
                start=0,  # Beginning of file
                content='"""Module docstring."""\n'
            )
        ],
        expected='''\
"""Module docstring."""

def example():
    return True'''
    )

    # Test 4: End of file insertion
    await run_test(
        "End of file insertion",
        content="""\
def example():
    return True""",
        operations=[
            Operation(
                opcode=DeltaType.INSERT,
                start=2,  # After last line
                content='\ndef another():\n    return False'
            )
        ],
        expected="""\
def example():
    return True

def another():
    return False"""
    )

    # Test 5: Empty file operations
    await run_test(
        "Empty file operations",
        content="",
        operations=[
            Operation(
                opcode=DeltaType.INSERT,
                start=0,
                content='#!/usr/bin/env python3\n\n"""Empty module."""'
            )
        ],
        expected='''\
#!/usr/bin/env python3

"""Empty module."""'''
    )

    # Test 6: Invalid line numbers
    await run_test(
        "Invalid line numbers - beyond file end",
        content="""\
def example():
    pass""",
        operations=[
            Operation(
                opcode=DeltaType.DELETE,
                start=5,    # Beyond end of file
                end=10
            )
        ],
        expected="Error: Start line 5 exceeds file length 2"
    )

    # Test 7: Overlapping operations
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
                opcode=DeltaType.REPLACE,
                start=2,  # "x = 1"
                end=3,    # "y = 2"
                content='    total = 0\n'
            ),
            Operation(
                opcode=DeltaType.REPLACE,
                start=3,  # "y = 2"
                end=4,    # "z = 3"
                content='    result = 42\n'
            )
        ],
        expected="Error: Operation at line 2 overlaps with operation at line 3"
    )

    # Test 8: Insert between specific lines
    await run_test(
        "Insert between specific lines",
        content="""\
def example():
    x = 1
    return x""",
        operations=[
            Operation(
                opcode=DeltaType.INSERT,
                start=2,  # After "x = 1"
                content='    y = 2'
            )
        ],
        expected="""\
def example():
    x = 1
    y = 2
    return x"""
    )

    # Test 9: Multiple inserts at same position
    await run_test(
        "Multiple inserts at same position",
        content="""\
def example():
    return True""",
        operations=[
            Operation(
                opcode=DeltaType.INSERT,
                start=1,  # After "def example():"
                content='    """First docstring."""\n'
            ),
            Operation(
                opcode=DeltaType.INSERT,
                start=1,  # After "def example():"
                content='    """Second docstring."""\n'
            )
        ],
        expected="Error: Operation at line 1 overlaps with operation at line 1"
    )

    # Test 10: Replace entire file
    await run_test(
        "Replace entire file",
        content="""\
old_content_1
old_content_2
old_content_3""",
        operations=[
            Operation(
                opcode=DeltaType.REPLACE,
                start=1,
                end=3,
                content='new_content_1\nnew_content_2'
            )
        ],
        expected="""\
new_content_1
new_content_2"""
    )

    # Test 11: Invalid operation combinations
    await run_test(
        "Invalid operation - insert with end",
        content="""\
def example():
    pass""",
        operations=[
            Operation(
                opcode=DeltaType.INSERT,
                start=1,
                end=2,
                content='    """Invalid."""\n'
            )
        ],
        expected="Error: INSERT operation cannot specify end line"
    )

    # Test 12: Delete with invalid range
    await run_test(
        "Delete with invalid range",
        content="""\
def example():
    x = 1
    y = 2
    return x + y""",
        operations=[
            Operation(
                opcode=DeltaType.DELETE,
                start=3,
                end=2  # Less than start
            )
        ],
        expected="Error: End line 2 is less than start line 3"
    )

    # Test 13: Complex multi-operation sequence
    await run_test(
        "Complex multi-operation sequence",
        content="""\
def example():
    x = 1
    y = 2
    z = 3
    return x + y + z""",
        operations=[
            Operation(
                opcode=DeltaType.INSERT,
                start=0,
                content='"""Example module."""\n'
            ),
            Operation(
                opcode=DeltaType.REPLACE,
                start=4,  # "z = 3"
                end=4,
                content='    z = 42'
            ),
            Operation(
                opcode=DeltaType.INSERT,
                start=5,  # After "return" line
                content='\ndef another():\n    return None'
            )
        ],
        expected='''\
"""Example module."""

def example():
    x = 1
    y = 2
    z = 42
    return x + y + z

def another():
    return None'''
    )

    # Test 14: Operations with empty lines
    await run_test(
        "Operations with empty lines",
        content="""\
def first():
    pass

def second():
    pass

def third():
    pass""",
        operations=[
            Operation(
                opcode=DeltaType.REPLACE,
                start=3,  # Empty line
                end=5,    # "pass" after second()
                content='\ndef new_second():\n    return True'
            )
        ],
        expected="""\
def first():
    pass

def new_second():
    return True

def third():
    pass"""
    )

    # Test 15: Delete at start of file
    await run_test(
        "Delete at start of file",
        content='''\
"""Old docstring."""

def example():
    pass''',
        operations=[
            Operation(
                opcode=DeltaType.DELETE,
                start=1,
                end=2
            )
        ],
        expected="""\
def example():
    pass"""
    )


if __name__ == '__main__':
    asyncio.run(main())