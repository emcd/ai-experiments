# Write Pieces Tool Development

## Current Implementation

We have implemented a context-based partial content update tool that allows LLMs to modify files by specifying before and after contexts for each operation. The implementation uses a two-pass approach:

1. First pass finds all operation ranges and validates them
2. Second pass applies the operations in order

The tool supports three operations:
- INSERT: Add new content at a position
- DELETE: Remove content between contexts
- REPLACE: Replace content between contexts with new content

## Challenges with Context-Based Approach

While implementing and testing the tool, we encountered several challenges:

1. **Context Matching**:
   - Difficult to match exact whitespace/indentation
   - Need large contexts to ensure unique matches
   - Easy to make mistakes with nested structures
   - Newline handling is tricky

2. **User Experience**:
   - LLMs must construct perfect context matches
   - Python's significant whitespace makes this especially challenging
   - Complex validation needed for overlapping operations

3. **Implementation Complexity**:
   - Two-pass approach with complex range finding
   - Need to handle BOF/EOF cases specially
   - Validation of context adjacency for inserts

## Proposed Direction: Line Numbers

We propose switching to a line number-based approach:

1. Add line numbering support to the read tool:
```python
# Read with line numbers
{
    'success': {
        'location': 'file.py',
        'content': {
            '1': 'def example():',
            '2': '    x = 1',
            '3': '    y = 2',
            '4': '    return x + y'
        },
        'mimetype': 'text/x-python',
        'charset': 'utf-8'
    }
}
```

2. Simplify write_pieces interface:
```python
{
    'location': 'file.py',
    'operations': [
        {
            'opcode': 'replace',
            'start': 2,          # line 2: "    x = 1"
            'length': 2,         # replace 2 lines
            'content': '    total = x + y\n    z = total * 2\n'
        },
        {
            'opcode': 'insert',
            'start': 1,          # after line 1
            'content': '    """Example function."""\n'
        },
        {
            'opcode': 'delete',
            'start': 4,          # line 4
            'length': 1          # delete 1 line
        }
    ]
}
```

### Advantages of Line Numbers

1. **Precision**:
   - Unambiguous positions
   - Easy to validate against file length
   - No whitespace/indentation issues
   - No context matching problems

2. **User Experience**:
   - LLMs can use numbered content from read tool
   - No need to construct perfect context matches
   - Clear operation boundaries

3. **Implementation**:
   - Simpler validation
   - No need for two passes
   - Easier to reason about operations
   - More robust error handling

### Next Steps

1. Add line numbering option to read tool
2. Update write_pieces schema for line numbers
3. Implement new line number-based logic
4. Update test suite
5. Consider adding validation for:
   - Line numbers in range
   - Non-overlapping operations
   - Valid content (newlines, etc.)

## Alternative Approaches Considered

We considered enhancing the context-based approach:

1. **Aho-Corasick Matching**:
   - Could help with partial matches
   - Would need line boundary expansion
   - Doesn't solve indentation issues

2. **Whitespace Normalization**:
   - Strip and re-indent contexts
   - Make whitespace matching optional
   - Add explicit indentation parameters

However, these would add complexity without providing the clarity and reliability of line numbers.

## Implementation Notes

The current implementation is in:
- `differences.py`: Core implementation
- `argschemata.py`: JSON Schema definitions
- `test_write_delta_2pass.py`: Test suite

The line number-based implementation will maintain the same file structure but with simplified logic and a more robust interface.