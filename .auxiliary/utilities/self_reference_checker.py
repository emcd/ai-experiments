#!/usr/bin/env python3
"""
Check for self-references in class methods that might need quoting.
"""

import ast
import pathlib
from typing import List, Tuple

def check_self_references(file_path: pathlib.Path) -> List[Tuple[int, str, str, str]]:
    """Find self-references in class methods."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.splitlines()
            
        tree = ast.parse(source, filename=str(file_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                
                # Check methods within this class
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check return type annotation
                        if method.returns:
                            if isinstance(method.returns, ast.Name) and method.returns.id == class_name:
                                line_text = source_lines[method.lineno - 1] if method.lineno <= len(source_lines) else ""
                                issues.append((method.lineno, class_name, 'return', line_text.strip()))
                        
                        # Check parameter annotations
                        for arg in method.args.args:
                            if arg.annotation:
                                if isinstance(arg.annotation, ast.Name) and arg.annotation.id == class_name:
                                    line_text = source_lines[arg.lineno - 1] if arg.lineno <= len(source_lines) else ""
                                    issues.append((arg.lineno, class_name, 'parameter', line_text.strip()))
                                    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return issues

def main():
    gui_dir = pathlib.Path("sources/aiwb/gui")
    
    if not gui_dir.exists():
        print(f"Directory {gui_dir} does not exist!")
        return 1
        
    python_files = list(gui_dir.glob("**/*.py"))
    
    print(f"Checking for self-references in {len(python_files)} Python files:")
    print("=" * 80)
    
    total_issues = 0
    
    for file_path in sorted(python_files):
        issues = check_self_references(file_path)
        if issues:
            total_issues += len(issues)
            print(f"\n📁 {file_path} ({len(issues)} self-references)")
            print("-" * 40)
            for line_num, class_name, ref_type, line_text in issues:
                print(f"  Line {line_num:3d} ({ref_type:9s}): {class_name} -> {line_text}")
                
    print(f"\n{'='*80}")
    if total_issues > 0:
        print(f"Total self-references found: {total_issues}")
        print("These may need to be quoted as string literals to avoid NameError.")
    else:
        print("✅ No self-references found!")
    
    return 0

if __name__ == "__main__":
    exit(main())