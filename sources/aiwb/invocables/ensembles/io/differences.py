# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Partial content update operations. '''


from . import __


class DeltaType( str, __.Enum ):
    ''' Types of partial content update operations. '''
    INSERT = 'insert'
    DELETE = 'delete'
    REPLACE = 'replace'


class Operation( __.immut.DataclassObject ):
    ''' A single delta operation. '''
    opcode: DeltaType
    start: int
    end: int | None = None
    content: str | None = None


def produce_operation_error( op: Operation, file_length: int ) -> str:
    ''' Produces error message for invalid operation. '''
    if op.start < 0: return f"Start line {op.start} is negative"
    if op.start > file_length:
        return f"Start line {op.start} exceeds file length {file_length}"

    match op.opcode:
        case DeltaType.INSERT:
            if op.content is None: return "INSERT operation requires content"
            if not isinstance( op.content, str ):
                return "Content must be a string with \\n for line breaks"
            if op.end is not None:
                return "INSERT operation cannot specify end line"
        case DeltaType.DELETE | DeltaType.REPLACE:
            if op.end is None:
                return f"{op.opcode} operation requires end line"
            if op.end < op.start:
                return f"End line {op.end} is less than start line {op.start}"
            if op.end > file_length:
                return f"End line {op.end} exceeds file length {file_length}"
            if op.opcode == DeltaType.REPLACE:
                if op.content is None:
                    return "REPLACE operation requires content"
                if not isinstance( op.content, str ):
                    return "Content must be a string with \\n for line breaks"
            if op.opcode == DeltaType.DELETE and op.content is not None:
                return "DELETE operation cannot have content"
        case _:
            return f"Unknown operation type: {op.opcode}"
    return ''


def verify_operation( op: Operation, file_length: int ) -> bool:
    ''' Verifies that operation is valid for given file length. '''
    if op.start < 0: return False
    if op.start > file_length: return False
    match op.opcode:
        case DeltaType.INSERT:
            if op.content is None: return False
            if op.end is not None: return False
            return True
        case DeltaType.DELETE | DeltaType.REPLACE:
            if op.end is None: return False
            if op.end < op.start: return False
            if op.end > file_length: return False
            if op.opcode == DeltaType.REPLACE and op.content is None:
                return False
            if op.opcode == DeltaType.DELETE and op.content is not None:
                return False
            return True
    return False  # Unknown opcode


def assess_overlap( op1: Operation, op2: Operation ) -> bool:
    ''' Determines if two operations affect overlapping line ranges. '''
    if op1.opcode == DeltaType.INSERT:
        op1_range = ( op1.start + 1, op1.start + 1 )
    else:
        op1_range = ( op1.start, op1.end )
    if op2.opcode == DeltaType.INSERT:
        op2_range = ( op2.start + 1, op2.start + 1 )
    else:
        op2_range = ( op2.start, op2.end )
    return (
        op1_range[ 0 ] <= op2_range[ 1 ] and op2_range[ 0 ] <= op1_range[ 1 ] )


def verify_operations(
    operations: __.AbstractSequence[ Operation ], file_length: int
) -> list[ Operation ]:
    ''' Verifies all operations are valid and non-overlapping. '''
    if not operations: return [ ]
    sorted_ops = sorted( operations, key = lambda op: op.start )
    # Verify each operation
    for op in sorted_ops:
        if error := produce_operation_error( op, file_length ):
            raise ValueError( error )
    # Check for overlaps
    for i, op in enumerate( sorted_ops[ :-1 ] ):
        if assess_overlap( op, sorted_ops[ i + 1 ] ):
            raise ValueError(
                f"Operation at line {op.start} overlaps with "
                f"operation at line {sorted_ops[ i + 1 ].start}" )
    return sorted_ops


def apply_operations(
    lines: list[ str ], operations: __.AbstractSequence[ Operation ]
) -> list[ str ]:
    ''' Applies sequence of operations to content lines. '''
    if not operations: return lines
    sorted_ops = sorted(
        operations, key = lambda op: op.start, reverse = True )
    result = lines.copy( )
    # Apply each operation
    for op in sorted_ops:
        match op.opcode:
            case DeltaType.INSERT:
                new_lines = (
                    [ ] if op.content is None else op.content.split( '\n' ) )
                # Insert after start line (or at beginning for start=0)
                # TODO: Hoist start case out of loop.
                if op.start == 0:
                    # TODO: result = new_lines + result
                    result[ 0 : 0 ] = new_lines
                else:
                    result[ op.start : op.start ] = new_lines
            case DeltaType.DELETE:
                del result[ op.start - 1 : op.end ]
            case DeltaType.REPLACE:
                new_lines = (
                    [ ] if op.content is None else op.content.split( '\n' ) )
                # Replace lines from start through end
                result[ op.start - 1 : op.end ] = new_lines
    return result


async def acquire_content( accessor: __.FileAccessor ) -> tuple[ str, int ]:
    ''' Acquires content and line count from file. '''
    if not await accessor.check_existence( ): return '', 0
    presenter = __.text_file_presenter_from_accessor( accessor = accessor )
    result = await presenter.acquire_content_result( )
    content = result.content
    lines = content.split( '\n' ) if content else [ ]
    return content, len( lines )


async def update_content(
    accessor: __.FileAccessor, content: str
) -> __.AbstractDictionary:
    ''' Updates file with modified content. '''
    presenter = __.text_file_presenter_from_accessor( accessor = accessor )
    result = await presenter.update_content(
        content, options = __.FileUpdateOptions.Defaults )
    return {
        'success': {
            'location': str( accessor ),
            'bytes_written': result.bytes_count
        }
    }


async def write_pieces(
    context: __.Context, arguments: __.Arguments
) -> __.AbstractDictionary:
    ''' Modifies file at URL or filesystem path with partial content updates.

        Operations can insert, delete, or replace content at specific line
        numbers. Each operation specifies the lines to modify and, for insert
        and replace operations, the new content to use.

        Do *not* use this tool on files for which you do not have line numbers.
        Attempting to guess line numbers is very error-prone and dangerous.

        Do *not* use this tool for more than three consecutive conversation
        turns. Ask user approval to continue after three consecutive turns of
        using this tool.

        Think through changes before using this tool.
    '''
    # Validate arguments
    if 'location' not in arguments:
        return { 'error': "Argument 'location' is required." }
    if 'operations' not in arguments:
        return { 'error': "Argument 'operations' is required." }
    arguments_ = arguments.copy( )
    try:
        accessor = await __.accessor_from_arguments(
            arguments_, species = __.LocationSpecies.File )
    except Exception as exc: return { 'error': str( exc ) }
    try: content, file_length = await acquire_content( accessor )
    except Exception as exc: return { 'error': str( exc ) }
    try:
        # Convert and validate operations
        operations = [
            Operation(
                opcode = DeltaType( op[ 'opcode' ] ),
                start = op[ 'start' ],
                end = op.get( 'end' ),
                content = op.get( 'content' )
            )
            for op in arguments_[ 'operations' ]
        ]
        validated_ops = verify_operations( operations, file_length )
    except Exception as exc: return { 'error': str( exc ) }
    lines = content.split( '\n' ) if content else [ ]
    try: modified_lines = apply_operations( lines, validated_ops )
    except Exception as exc: return { 'error': str( exc ) }
    modified_content = '\n'.join( modified_lines )
    try: result = await update_content( accessor, modified_content )
    except Exception as exc: return { 'error': str( exc ) }
    if arguments_.get( 'return-content', True ):
        content_lines = (
            modified_content.split( '\n' ) if modified_content else [ ] )
        result[ 'success' ][ 'content' ] = {
            i + 1: line for i, line in enumerate( content_lines ) }
    return result
