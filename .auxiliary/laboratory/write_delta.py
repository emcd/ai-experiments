#!/usr/bin/env python3

"""Core implementation of write_delta operations."""

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class DeltaType(str, Enum):
    """Types of delta operations."""
    INSERT = 'insert'
    DELETE = 'delete'
    REPLACE = 'replace'


@dataclass
class Context:
    """Context for locating where to apply a delta."""
    before: list[str] | None
    after: list[str] | None = None
    match_occurrence: int = 1


@dataclass
class Operation:
    """A single delta operation."""
    type: DeltaType
    context: Context
    length: int = 1
    content: str | None = None


def normalize_content(content: str) -> str:
    """Ensure content ends with a newline."""
    return content if not content or content.endswith('\n') else content + '\n'


def find_line_positions(content: str, start_pos: int, length: int) -> tuple[int, int]:
    """Find the start and end positions of a range of lines.
    
    Args:
        content: The string to search in
        start_pos: Starting position
        length: Number of lines to include
        
    Returns:
        (start_pos, end_pos) tuple where:
        - start_pos is the start of the first line
        - end_pos is after the last newline of the last line
    """
    # Count lines from the start position
    pos = start_pos
    lines_found = 0
    while lines_found < length:
        next_pos = content.find('\n', pos)
        if next_pos == -1:
            return start_pos, len(content)
        pos = next_pos + 1
        lines_found += 1
    return start_pos, pos


async def find_string_position(
    content: str,
    before: list[str] | None,
    after: list[str] | None = None,
    occurrence: int = 1
) -> tuple[int, int]:
    """Find start and end positions in content string.
    
    Args:
        content: The string to search in
        before: Lines that should appear before the operation point
        after: Lines that should appear after the operation point
        occurrence: Which occurrence to match (1-based)
    
    Returns:
        (start_pos, end_pos) tuple where:
        - start_pos is the position where the match begins
        - end_pos is the position after the match
    
    Raises:
        ValueError: If context cannot be found or occurrence is invalid
    """
    # Handle file boundary cases
    if before is None:
        return (0, 0)  # Start of file
    if after is None and not before:
        return (len(content), len(content))  # End of file
    
    # Convert context to strings for matching
    before_text = ''.join(line + '\n' for line in before)
    after_text = ''.join(line + '\n' for line in after) if after else None
    
    # Find all occurrences of the before context
    pos = 0
    count = 0
    while True:
        pos = content.find(before_text, pos)
        if pos == -1:
            break
        
        # Check if after context matches (if provided)
        match_start = pos
        match_end = pos + len(before_text)
        if after_text:
            if not content.startswith(after_text, match_end):
                pos += 1
                continue
            match_end += len(after_text)
        
        count += 1
        if count == occurrence:
            return (match_start, match_end)
        
        pos += 1
    
    if count == 0:
        raise ValueError("Could not find matching context")
    raise ValueError(
        f"Requested match {occurrence} but only found {count} matches"
    )


def prepare_content(content: str | None, preserve_trailing: bool = False) -> str:
    """Prepare content for insertion/replacement.
    
    Args:
        content: The content to prepare
        preserve_trailing: Whether to preserve trailing newlines
        
    Returns:
        Prepared content with appropriate line endings
    """
    if content is None:
        return ''
    
    # Split into lines and add newlines
    lines = content.splitlines()
    if not lines:
        return content if preserve_trailing else ''
    
    # Add newlines to all lines except possibly the last
    result = '\n'.join(line for line in lines[:-1])
    if lines[:-1]:
        result += '\n'
    
    # Handle last line
    if preserve_trailing and content.endswith('\n'):
        result += lines[-1] + '\n'
    else:
        result += lines[-1]
    
    return result


async def apply_delta_operations(
    content: str,
    operations: Sequence[Operation]
) -> str:
    """Apply sequence of delta operations to content.
    
    Args:
        content: The content to modify
        operations: Sequence of operations to apply
        
    Returns:
        Modified content with all operations applied
        
    Raises:
        ValueError: If an operation is invalid
    """
    # Ensure content ends with newline for consistent handling
    result = normalize_content(content)
    had_trailing_newline = bool(content and content.endswith('\n'))
    
    # Process operations in order
    for op in operations:
        # Find position for this operation
        start_pos, context_end = await find_string_position(
            result,
            op.context.before,
            op.context.after,
            op.context.match_occurrence
        )
        
        if op.type == DeltaType.DELETE:
            # Find the range of lines to delete
            _, end_pos = find_line_positions(result, start_pos, op.length)
            result = result[:start_pos] + result[end_pos:]
            
        elif op.type == DeltaType.REPLACE:
            if op.content is None:
                raise ValueError("Replace operation requires content")
            # Find the range of lines to replace
            _, end_pos = find_line_positions(result, start_pos, op.length)
            # Prepare new content
            new_content = prepare_content(op.content, preserve_trailing=True)
            result = result[:start_pos] + new_content + result[end_pos:]
            
        elif op.type == DeltaType.INSERT:
            if op.content is None:
                raise ValueError("Insert operation requires content")
            # For insert, we want to insert after the before context
            insert_pos = context_end if op.context.before is not None else start_pos
            # Prepare new content
            new_content = prepare_content(op.content, preserve_trailing=True)
            result = result[:insert_pos] + new_content + result[insert_pos:]
    
    # Handle final line ending
    if not had_trailing_newline:
        result = result.rstrip('\n')
    elif not result.endswith('\n'):
        result += '\n'
    
    return result