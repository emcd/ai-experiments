#!/usr/bin/env python3

"""Two-pass implementation of write_delta operations."""

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
    """Context for locating where to apply a delta.

    Args:
        before: Context that must appear before operation point
               None = Beginning of file
               str = Lines that must match
        after: Context that must appear after operation point
               None = End of file (required for DELETE/REPLACE)
               str = Lines that must match
        match_occurrence: Which occurrence to match (1-based)
    """
    before: str | None  # None means BOF
    after: str | None   # None means EOF
    match_occurrence: int = 1


@dataclass
class Operation:
    """A single delta operation."""
    type: DeltaType
    context: Context
    content: str | None = None  # Required for INSERT/REPLACE


@dataclass
class LineRange:
    """Range of lines affected by an operation."""
    before_start: int    # -1 for BOF
    before_end: int     # Last line of before context
    after_start: int    # First line of after context
    operation: Operation


def split_lines(content: str) -> list[str]:
    """Split content into lines, handling empty string case.

    Args:
        content: String to split

    Returns:
        List of lines (empty list for empty content)
    """
    return [] if not content else content.split('\n')


def validate_operation(op: Operation) -> None:
    """Validate operation type and context requirements.

    Raises:
        ValueError: If operation is invalid
    """
    match op.type:
        case DeltaType.INSERT:
            if op.content is None:
                raise ValueError("INSERT operation requires content")

        case DeltaType.DELETE | DeltaType.REPLACE:
            if op.type == DeltaType.REPLACE and op.content is None:
                raise ValueError("REPLACE operation requires content")
            if op.type == DeltaType.DELETE and op.content is not None:
                raise ValueError("DELETE operation cannot have content")
            # Must have after context (string or None for EOF)
            #if op.context.after is None and op.context.before is None:
            #    raise ValueError(
            #        f"{op.type} operation cannot match both BOF and EOF"
            #    )


def find_context_match(
    lines: list[str],
    context: list[str],
    start_from: int = 0,
    occurrence: int = 1
) -> int:
    """Find the line number where a context matches.

    Args:
        lines: List of lines to search
        context: Lines to match
        start_from: Line number to start searching from
        occurrence: Which occurrence to match (1-based)

    Returns:
        Line number where the match begins

    Raises:
        ValueError: If context cannot be found or occurrence is invalid
    """
    matches = []
    for i in range(start_from, len(lines) - len(context) + 1):
        if all(lines[i + j] == context[j] for j in range(len(context))):
            matches.append(i)
            if len(matches) == occurrence:
                return i

    if not matches:
        raise ValueError(f"Could not find context {context}")
    raise ValueError(
        f"Requested match {occurrence} but only found {len(matches)} matches"
    )


def find_operation_ranges(
    lines: list[str],
    operations: Sequence[Operation]
) -> list[LineRange]:
    """First pass: Find all operation ranges and validate.

    Args:
        lines: Original content split into lines
        operations: Sequence of operations to apply

    Returns:
        List of line ranges for each operation

    Raises:
        ValueError: If any operation is invalid or contexts cannot be found
    """
    ranges = []

    for op in operations:
        # Validate operation
        validate_operation(op)

        # Convert contexts to lines
        before_lines = (
            None if None is op.context.before
            else op.context.before.split('\n') )
        after_lines = (
            None if None is op.context.after
            else op.context.after.split('\n') )

        # Handle beginning of file
        if op.context.before is None:  # BOF
            before_start = -1
            before_end = -1
            if not after_lines:  # EOF
                after_start = len(lines)
            else:
                after_start = find_context_match(
                    lines,
                    after_lines,
                    start_from=0,
                    occurrence=op.context.match_occurrence
                )

        # Handle all other cases
        else:
            # Find before context
            before_start = find_context_match(
                lines,
                before_lines,
                occurrence=op.context.match_occurrence
            )
            before_end = before_start + len(before_lines) - 1

            # Find after context
            if op.context.after is None:  # EOF
                after_start = len(lines)
            else:
                after_start = find_context_match(
                    lines,
                    after_lines,
                    start_from=before_end + 1
                )
                # For INSERT, after context must immediately follow before context
                if op.type == DeltaType.INSERT and after_start != before_end + 1:
                    raise ValueError(
                        f"Gap between before and after contexts at line {before_end + 1}"
                    )

        ranges.append(LineRange(
            before_start=before_start,
            before_end=before_end,
            after_start=after_start,
            operation=op
        ))

    return ranges


def validate_ranges(ranges: list[LineRange]) -> None:
    """Check for overlaps and other invalid conditions.

    Args:
        ranges: List of line ranges to validate

    Raises:
        ValueError: If ranges overlap or are otherwise invalid
    """
    if not ranges:
        return

    # Sort ranges by where their change regions start
    sorted_ranges = sorted(ranges, key=lambda r: r.before_end)

    # Check for overlaps
    for i in range(len(sorted_ranges) - 1):
        current = sorted_ranges[i]
        next_range = sorted_ranges[i + 1]

        # Skip BOF inserts (they can't overlap)
        if current.before_start == -1 and current.operation.type == DeltaType.INSERT:
            continue

        # For DELETE/REPLACE, after context must not extend into next operation's change region
        if current.operation.type in (DeltaType.DELETE, DeltaType.REPLACE):
            if current.after_start > next_range.before_end:
                raise ValueError(
                    f"Operation at line {current.before_start} has after context "
                    f"that overlaps with operation at line {next_range.before_start}"
                )

        # Check if current operation's change space overlaps with next operation's change space
        if current.after_start > next_range.before_end:
            raise ValueError(
                f"Operation at line {current.before_start} overlaps with "
                f"operation at line {next_range.before_start}"
            )


def apply_operations(
    lines: list[str],
    ranges: list[LineRange]
) -> list[str]:
    """Second pass: Apply operations in order.

    Args:
        lines: Original content split into lines
        ranges: Sorted list of line ranges

    Returns:
        List of modified lines
    """
    if not ranges:
        return lines

    # Sort ranges by where their change regions start
    sorted_ranges = sorted(ranges, key=lambda r: r.before_end)

    result = []
    current_line = 0

    for range_ in sorted_ranges:
        # Handle BOF operations
        if range_.before_start == -1:
            if range_.operation.type == DeltaType.INSERT:
                if range_.operation.content:
                    result.extend(split_lines(range_.operation.content))
            else:  # DELETE/REPLACE
                if range_.operation.type == DeltaType.REPLACE:
                    result.extend(split_lines(range_.operation.content))
                current_line = range_.after_start
            continue

        # Copy lines up to this operation
        result.extend(lines[current_line:range_.before_end + 1])

        # Apply the operation
        if range_.operation.content:  # INSERT/REPLACE
            result.extend(split_lines(range_.operation.content))

        # Move past the changed region
        if range_.operation.type == DeltaType.INSERT:
            current_line = range_.before_end + 1
        else:  # DELETE/REPLACE
            current_line = range_.after_start

    # Add any remaining lines
    if current_line < len(lines):
        result.extend(lines[current_line:])

    return result


async def write_delta(
    content: str,
    operations: Sequence[Operation]
) -> str:
    """Apply a sequence of delta operations to content.

    Args:
        content: The content to modify
        operations: Sequence of operations to apply

    Returns:
        Modified content

    Raises:
        ValueError: If operations are invalid or cannot be applied
    """
    # Split content into lines
    lines = split_lines(content)

    # Find ranges for all operations
    ranges = find_operation_ranges(lines, operations)

    # Validate ranges
    validate_ranges(ranges)

    # Apply operations
    result = apply_operations(lines, ranges)

    # Join lines back together
    return '\n'.join(result)
