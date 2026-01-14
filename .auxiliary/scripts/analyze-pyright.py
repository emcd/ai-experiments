#!/usr/bin/env python3
"""Analyze Pyright output to understand error distribution."""

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple


class PyrightError(NamedTuple):
    """Represents a Pyright error."""
    file_path: str
    line_number: int
    error_type: str
    message: str


def parse_pyright_output(output_file: Path) -> list[PyrightError]:
    """Parse Pyright output file and extract errors."""
    errors = []
    error_pattern = re.compile(
        r'^  (/[^:]+):(\d+):\d+ - error: (.+?) \((\w+)\)$'
    )

    with output_file.open() as f:
        for line in f:
            match = error_pattern.match(line)
            if match:
                file_path, line_num, message, error_type = match.groups()
                errors.append(PyrightError(
                    file_path=file_path,
                    line_number=int(line_num),
                    error_type=error_type,
                    message=message
                ))

    return errors


def get_package_from_path(file_path: str) -> str:
    """Extract package name from file path."""
    # Example: /home/user/ai-experiments/sources/aiwb/messages/core.py
    # Extract: aiwb.messages
    parts = Path(file_path).parts
    try:
        sources_idx = parts.index('sources')
        package_parts = parts[sources_idx + 1:sources_idx + 3]
        return '.'.join(package_parts) if len(package_parts) > 1 else package_parts[0]
    except (ValueError, IndexError):
        return 'unknown'


def analyze_errors(errors: list[PyrightError]) -> None:
    """Analyze and print error statistics."""

    # Count errors by type
    error_types = Counter(e.error_type for e in errors)

    # Count errors by package
    package_errors = defaultdict(list)
    for error in errors:
        package = get_package_from_path(error.file_path)
        package_errors[package].append(error)

    # Count errors by file
    file_errors = Counter(e.file_path for e in errors)

    print(f"Total errors: {len(errors)}")
    print("\n" + "="*80)
    print("TOP 20 ERROR TYPES:")
    print("="*80)
    for error_type, count in error_types.most_common(20):
        print(f"  {error_type:40s} {count:5d}")

    print("\n" + "="*80)
    print("TOP 20 PACKAGES BY ERROR COUNT:")
    print("="*80)
    sorted_packages = sorted(
        package_errors.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    for package, pkg_errors in sorted_packages[:20]:
        print(f"  {package:40s} {len(pkg_errors):5d}")

    print("\n" + "="*80)
    print("TOP 20 FILES BY ERROR COUNT:")
    print("="*80)
    for file_path, count in file_errors.most_common(20):
        # Show relative path
        rel_path = Path(file_path).relative_to('/home/user/ai-experiments')
        print(f"  {str(rel_path):60s} {count:5d}")

    # Find packages with fewest errors (good starting points)
    print("\n" + "="*80)
    print("PACKAGES WITH FEWEST ERRORS (potential starting points):")
    print("="*80)
    sorted_packages_asc = sorted(
        package_errors.items(),
        key=lambda x: len(x[1])
    )
    for package, pkg_errors in sorted_packages_asc[:15]:
        if package != 'unknown':
            print(f"  {package:40s} {len(pkg_errors):5d}")

    # Error type distribution by package
    print("\n" + "="*80)
    print("ERROR TYPE DISTRIBUTION FOR TOP 10 PACKAGES:")
    print("="*80)
    for package, pkg_errors in sorted_packages[:10]:
        print(f"\n{package}:")
        pkg_error_types = Counter(e.error_type for e in pkg_errors)
        for error_type, count in pkg_error_types.most_common(5):
            print(f"  {error_type:40s} {count:5d}")


def main():
    """Main function."""
    output_file = Path('.auxiliary/notes/pyright-output.txt')

    if not output_file.exists():
        print(f"Error: {output_file} not found")
        return 1

    errors = parse_pyright_output(output_file)
    analyze_errors(errors)

    return 0


if __name__ == '__main__':
    exit(main())
