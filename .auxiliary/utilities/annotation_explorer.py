#!/usr/bin/env python3
"""
Simple script to find and display all type annotations in the GUI directory.
"""

import ast
import pathlib
from typing import List, Tuple

def extract_annotations(file_path: pathlib.Path) -> List[Tuple[int, str, str]]:
    """Extract all type annotations from a Python file."""
    annotations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.splitlines()
            
        tree = ast.parse(source, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Return type annotation
                if node.returns:
                    line_text = source_lines[node.lineno - 1] if node.lineno <= len(source_lines) else ""
                    annotations.append((node.lineno, 'return', line_text.strip()))
                
                # Parameter annotations
                for arg in node.args.args:
                    if arg.annotation:
                        line_text = source_lines[arg.lineno - 1] if arg.lineno <= len(source_lines) else ""
                        annotations.append((arg.lineno, 'parameter', line_text.strip()))
                        
            elif isinstance(node, ast.AsyncFunctionDef):
                # Same for async functions
                if node.returns:
                    line_text = source_lines[node.lineno - 1] if node.lineno <= len(source_lines) else ""
                    annotations.append((node.lineno, 'return', line_text.strip()))
                
                for arg in node.args.args:
                    if arg.annotation:
                        line_text = source_lines[arg.lineno - 1] if arg.lineno <= len(source_lines) else ""
                        annotations.append((arg.lineno, 'parameter', line_text.strip()))
                        
            elif isinstance(node, ast.AnnAssign):
                # Variable annotations
                line_text = source_lines[node.lineno - 1] if node.lineno <= len(source_lines) else ""
                annotations.append((node.lineno, 'variable', line_text.strip()))
                
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return annotations

def main():
    gui_dir = pathlib.Path("sources/aiwb/gui")
    
    if not gui_dir.exists():
        print(f"Directory {gui_dir} does not exist!")
        return 1
        
    python_files = list(gui_dir.glob("**/*.py"))
    
    print(f"Type annotations found in {len(python_files)} Python files:")
    print("=" * 80)
    
    total_annotations = 0
    
    for file_path in sorted(python_files):
        annotations = extract_annotations(file_path)
        if annotations:
            total_annotations += len(annotations)
            print(f"\n📁 {file_path} ({len(annotations)} annotations)")
            print("-" * 40)
            for line_num, ann_type, line_text in annotations:
                print(f"  Line {line_num:3d} ({ann_type:9s}): {line_text}")
                
    print(f"\n{'='*80}")
    print(f"Total annotations found: {total_annotations}")
    
    return 0

if __name__ == "__main__":
    exit(main())