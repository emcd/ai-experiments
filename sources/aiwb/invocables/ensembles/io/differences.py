# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.         #
#  You may obtain a copy of the License at                                  #
#                                                                           #
#      http://www.apache.org/licenses/LICENSE-2.0                           #
#                                                                           #
#  Unless required by applicable law or agreed to in writing, software      #
#  distributed under the License is distributed on an "AS IS" BASIS,        #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and      #
#  limitations under the License.                                           #
#                                                                           #
#============================================================================#


''' Partial content update operations. '''


from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from . import __


class DeltaType(str, Enum):
    ''' Types of partial content update operations. '''
    INSERT = 'insert'
    DELETE = 'delete'
    REPLACE = 'replace'


@dataclass
class Context:
    ''' Context for locating where to apply a delta. '''
    before: str | None  # None means BOF
    after: str | None   # None means EOF
    nth_match: int = 1


@dataclass
class Operation:
    ''' A single delta operation. '''
    opcode: DeltaType
    context: Context
    content: str | None = None  # Required for INSERT/REPLACE


@dataclass
class LineRange:
    ''' Range of lines affected by an operation. '''
    before_start: int    # -1 for BOF
    before_end: int     # Last line of before context
    after_start: int    # First line of after context
    operation: Operation


def split_lines(content: str) -> list[str]:
    ''' Split content into lines, handling empty string case. '''
    return [] if not content else content.split('\n')


def validate_operation(op: Operation) -> None:
    ''' Validate operation type and context requirements. '''
    match op.opcode:
        case DeltaType.INSERT:
            if op.content is None:
                raise ValueError("INSERT operation requires content")

        case DeltaType.DELETE | DeltaType.REPLACE:
            if op.opcode == DeltaType.REPLACE and op.content is None:
                raise ValueError("REPLACE operation requires content")
            if op.opcode == DeltaType.DELETE and op.content is not None:
                raise ValueError("DELETE operation cannot have content")


def find_context_match(
    lines: list[str],
    context: list[str],
    start_from: int = 0,
    occurrence: int = 1
) -> int:
    ''' Find the line number where a context matches. '''
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
    ''' First pass: Find all operation ranges and validate. '''
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
                    occurrence=op.context.nth_match
                )

        # Handle all other cases
        else:
            # Find before context
            before_start = find_context_match(
                lines,
                before_lines,
                occurrence=op.context.nth_match
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
                if op.opcode == DeltaType.INSERT and after_start != before_end + 1:
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
    ''' Check for overlaps and other invalid conditions. '''
    if not ranges:
        return

    # Sort ranges by where their change regions start
    sorted_ranges = sorted(ranges, key=lambda r: r.before_end)

    # Check for overlaps
    for i in range(len(sorted_ranges) - 1):
        current = sorted_ranges[i]
        next_range = sorted_ranges[i + 1]

        # Skip BOF inserts (they can't overlap)
        if current.before_start == -1 and current.operation.opcode == DeltaType.INSERT:
            continue

        # For DELETE/REPLACE, after context must not extend into next operation's change region
        if current.operation.opcode in (DeltaType.DELETE, DeltaType.REPLACE):
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
    ''' Second pass: Apply operations in order. '''
    if not ranges:
        return lines

    # Sort ranges by where their change regions start
    sorted_ranges = sorted(ranges, key=lambda r: r.before_end)

    result = []
    current_line = 0

    for range_ in sorted_ranges:
        # Handle BOF operations
        if range_.before_start == -1:
            if range_.operation.opcode == DeltaType.INSERT:
                if range_.operation.content:
                    result.extend(split_lines(range_.operation.content))
            else:  # DELETE/REPLACE
                if range_.operation.opcode == DeltaType.REPLACE:
                    result.extend(split_lines(range_.operation.content))
                current_line = range_.after_start
            continue

        # Copy lines up to this operation
        result.extend(lines[current_line:range_.before_end + 1])

        # Apply the operation
        if range_.operation.content:  # INSERT/REPLACE
            result.extend(split_lines(range_.operation.content))

        # Move past the changed region
        if range_.operation.opcode == DeltaType.INSERT:
            current_line = range_.before_end + 1
        else:  # DELETE/REPLACE
            current_line = range_.after_start

    # Add any remaining lines
    if current_line < len(lines):
        result.extend(lines[current_line:])

    return result


async def write_pieces(
    context: __.Context, arguments: __.Arguments
) -> __.AbstractDictionary:
    ''' Modifies file at URL or filesystem path with partial content updates.

        Operations can insert, delete, or replace content at specific positions.
        Each operation uses before and after contexts to locate where it should
        be applied.

        Result includes number of bytes written.
    '''
    arguments_ = arguments.copy()
    if 'location' not in arguments:
        return { 'error': "Argument 'location' is required." }
    if 'operations' not in arguments:
        return { 'error': "Argument 'operations' is required." }

    try:
        accessor = await __.accessor_from_arguments(
            arguments_, species=__.LocationSpecies.File)
    except Exception as exc:
        return { 'error': str(exc) }

#    if not isinstance(accessor, __.FileAccessor):
#        return { 'error': 'Cannot modify content of non-file.' }

    try:
        # Get current content
        presenter = __.text_file_presenter_from_accessor(accessor=accessor)
        result = await presenter.acquire_content_result()
        content = result.content

        # Convert operations from JSON
        operations = [
            Operation(
                opcode=DeltaType(op['opcode']),
                context=Context(
                    before=op['context']['before'],
                    after=op['context']['after'],
                    nth_match=op['context'].get('nth_match', 1)
                ),
                content=op.get('content')
            )
            for op in arguments['operations']
        ]

        # Apply operations
        lines = split_lines(content)
        ranges = find_operation_ranges(lines, operations)
        validate_ranges(ranges)
        modified_lines = apply_operations(lines, ranges)
        modified_content = '\n'.join(modified_lines)

        # Write back
        result = await presenter.update_content(
            modified_content,
            options=__.FileUpdateOptions.Defaults
        )

        return {
            'success': {
                'location': str(accessor),
                'bytes_written': result.bytes_count
            }
        }

    except Exception as exc:
        return { 'error': str(exc) }
