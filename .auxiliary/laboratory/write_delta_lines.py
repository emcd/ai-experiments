#!/usr/bin/env python3

"""Line number-based implementation of write_delta operations."""

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class DeltaType(str, Enum):
    """Types of delta operations."""
    INSERT = 'insert'
    DELETE = 'delete'
    REPLACE = 'replace'


@dataclass
class Operation:
    """A single delta operation."""
    opcode: DeltaType
    start: int
    end: int | None = None
    content: str | None = None


def validate_operation(op: Operation, file_length: int) -> None:
    """Validate a single operation.

    Args:
        op: Operation to validate
        file_length: Number of lines in file

    Raises:
        ValueError: If operation is invalid
    """
    # Validate start bounds
    if op.start < 0:
        raise ValueError(f"Start line {op.start} is negative")
    if op.start > file_length:
        raise ValueError(
            f"Start line {op.start} exceeds file length {file_length}"
        )

    # Validate operation-specific requirements
    match op.opcode:
        case DeltaType.INSERT:
            if op.content is None:
                raise ValueError("INSERT operation requires content")
            if op.end is not None:
                raise ValueError("INSERT operation cannot specify end line")

        case DeltaType.DELETE | DeltaType.REPLACE:
            if op.end is None:
                raise ValueError(f"{op.opcode} operation requires end line")
            if op.end < op.start:
                raise ValueError(
                    f"End line {op.end} is less than start line {op.start}"
                )
            if op.end > file_length:
                raise ValueError(
                    f"End line {op.end} exceeds file length {file_length}"
                )
            if op.opcode == DeltaType.REPLACE and op.content is None:
                raise ValueError("REPLACE operation requires content")
            if op.opcode == DeltaType.DELETE and op.content is not None:
                raise ValueError("DELETE operation cannot have content")


def regions_overlap(op1: Operation, op2: Operation) -> bool:
    """Check if two operations overlap.

    Args:
        op1: First operation
        op2: Second operation

    Returns:
        True if operations overlap, False otherwise
    """
    # Convert operations to ranges
    if op1.opcode == DeltaType.INSERT:
        op1_start = op1.start + 1
        op1_end = op1.start + 1
    else:
        op1_start = op1.start
        op1_end = op1.end

    if op2.opcode == DeltaType.INSERT:
        op2_start = op2.start + 1
        op2_end = op2.start + 1
    else:
        op2_start = op2.start
        op2_end = op2.end

    return op1_start <= op2_end and op2_start <= op1_end


def validate_operations(
    operations: Sequence[Operation],
    file_length: int
) -> list[Operation]:
    """First pass: Validate all operations.

    Args:
        operations: Sequence of operations to validate
        file_length: Number of lines in file

    Returns:
        List of validated operations

    Raises:
        ValueError: If any operation is invalid
    """
    if not operations:
        return []

    # Sort operations by start line
    sorted_ops = sorted(operations, key=lambda op: op.start)

    # Validate each operation
    for i, op in enumerate(sorted_ops):
        # Validate operation itself
        validate_operation(op, file_length)

        # Check for overlaps with subsequent operations
        for other in sorted_ops[i + 1:]:
            if regions_overlap(op, other):
                raise ValueError(
                    f"Operation at line {op.start} overlaps with "
                    f"operation at line {other.start}"
                )

    return sorted_ops


def apply_operations(
    lines: list[str],
    operations: Sequence[Operation]
) -> list[str]:
    """Second pass: Apply operations to content.

    Args:
        lines: Original content as list of lines
        operations: Sequence of validated operations

    Returns:
        Modified content as list of lines
    """
    if not operations:
        return lines

    # Sort operations in reverse order by start line
    sorted_ops = sorted(operations, key=lambda op: op.start, reverse=True)
    result = lines.copy()

    # Apply each operation
    for op in sorted_ops:
        match op.opcode:
            case DeltaType.INSERT:
                # Split content into lines
                new_lines = [] if op.content is None else op.content.split('\n')
                # Insert after start line (or at beginning for start=0)
                if op.start == 0:
                    result[0:0] = new_lines
                else:
                    result[op.start:op.start] = new_lines

            case DeltaType.DELETE:
                # Remove lines from start through end
                del result[op.start - 1:op.end]

            case DeltaType.REPLACE:
                # Split content into lines
                new_lines = [] if op.content is None else op.content.split('\n')
                # Replace lines from start through end
                result[op.start - 1:op.end] = new_lines

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
    lines = content.split('\n') if content else []
    file_length = len(lines)

    # Validate operations
    validated_ops = validate_operations(operations, file_length)

    # Apply operations
    result = apply_operations(lines, validated_ops)

    # Join lines back together
    return '\n'.join(result)
