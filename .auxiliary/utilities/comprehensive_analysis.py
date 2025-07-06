#!/usr/bin/env python3
"""
Comprehensive forward reference analysis for the sources/aiwb/gui directory.
"""

import ast
import pathlib
from typing import Dict, List, Set, Tuple, NamedTuple

class AnalysisResult(NamedTuple):
    """Result of forward reference analysis."""
    file_path: str
    total_classes: int
    total_annotations: int
    forward_references: List[str]
    self_references: List[str]
    class_names: List[str]
    
def analyze_file(file_path: pathlib.Path) -> AnalysisResult:
    """Perform comprehensive analysis of a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.splitlines()
            
        tree = ast.parse(source, filename=str(file_path))
        
        # Collect all class definitions
        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node.lineno
                
        # Collect all annotations and check for forward references
        annotations = []
        forward_refs = []
        self_refs = []
        
        current_class = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                current_class = node.name
                
                # Check for self-references in class methods
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check return type
                        if method.returns:
                            if isinstance(method.returns, ast.Name):
                                if method.returns.id == current_class:
                                    line_text = source_lines[method.lineno - 1] if method.lineno <= len(source_lines) else ""
                                    self_refs.append(f"Line {method.lineno}: {current_class} in return type")
                                elif method.returns.id in classes and classes[method.returns.id] > method.lineno:
                                    forward_refs.append(f"Line {method.lineno}: {method.returns.id} in return type")
                        
                        # Check parameter annotations
                        for arg in method.args.args:
                            if arg.annotation and isinstance(arg.annotation, ast.Name):
                                if arg.annotation.id == current_class:
                                    line_text = source_lines[arg.lineno - 1] if arg.lineno <= len(source_lines) else ""
                                    self_refs.append(f"Line {arg.lineno}: {current_class} in parameter")
                                elif arg.annotation.id in classes and classes[arg.annotation.id] > arg.lineno:
                                    forward_refs.append(f"Line {arg.lineno}: {arg.annotation.id} in parameter")
                                    
            elif isinstance(node, ast.FunctionDef):
                annotations.append(f"Function {node.name} at line {node.lineno}")
                
                # Check return type annotation
                if node.returns:
                    if isinstance(node.returns, ast.Name):
                        if node.returns.id in classes and classes[node.returns.id] > node.lineno:
                            forward_refs.append(f"Line {node.lineno}: {node.returns.id} in return type")
                
                # Check parameter annotations
                for arg in node.args.args:
                    if arg.annotation and isinstance(arg.annotation, ast.Name):
                        if arg.annotation.id in classes and classes[arg.annotation.id] > arg.lineno:
                            forward_refs.append(f"Line {arg.lineno}: {arg.annotation.id} in parameter")
                            
            elif isinstance(node, ast.AnnAssign):
                annotations.append(f"Variable annotation at line {node.lineno}")
                
                # Check variable annotation
                if isinstance(node.annotation, ast.Name):
                    if node.annotation.id in classes and classes[node.annotation.id] > node.lineno:
                        forward_refs.append(f"Line {node.lineno}: {node.annotation.id} in variable")
                        
        return AnalysisResult(
            file_path=str(file_path),
            total_classes=len(classes),
            total_annotations=len(annotations),
            forward_references=forward_refs,
            self_references=self_refs,
            class_names=list(classes.keys())
        )
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return AnalysisResult(
            file_path=str(file_path),
            total_classes=0,
            total_annotations=0,
            forward_references=[],
            self_references=[],
            class_names=[]
        )

def main():
    """Main entry point."""
    gui_dir = pathlib.Path("sources/aiwb/gui")
    
    if not gui_dir.exists():
        print(f"Directory {gui_dir} does not exist!")
        return 1
        
    python_files = list(gui_dir.glob("**/*.py"))
    
    print(f"Comprehensive Forward Reference Analysis")
    print(f"Analyzing {len(python_files)} Python files in {gui_dir}")
    print("=" * 80)
    
    results = []
    total_classes = 0
    total_annotations = 0
    total_forward_refs = 0
    total_self_refs = 0
    
    for file_path in sorted(python_files):
        result = analyze_file(file_path)
        results.append(result)
        
        total_classes += result.total_classes
        total_annotations += result.total_annotations
        total_forward_refs += len(result.forward_references)
        total_self_refs += len(result.self_references)
        
        if result.total_classes > 0 or result.total_annotations > 0:
            print(f"\n📁 {file_path}")
            print(f"   Classes: {result.total_classes} ({', '.join(result.class_names)})")
            print(f"   Annotations: {result.total_annotations}")
            
            if result.forward_references:
                print(f"   ⚠️  Forward references: {len(result.forward_references)}")
                for ref in result.forward_references:
                    print(f"      - {ref}")
                    
            if result.self_references:
                print(f"   ⚠️  Self references: {len(result.self_references)}")
                for ref in result.self_references:
                    print(f"      - {ref}")
                    
    print(f"\n{'='*80}")
    print(f"Summary:")
    print(f"  Total files analyzed: {len(python_files)}")
    print(f"  Total classes found: {total_classes}")
    print(f"  Total annotations found: {total_annotations}")
    print(f"  Forward reference issues: {total_forward_refs}")
    print(f"  Self reference issues: {total_self_refs}")
    
    if total_forward_refs == 0 and total_self_refs == 0:
        print(f"\n✅ No forward reference issues found!")
        print(f"   All type annotations appear to be properly handled.")
    else:
        print(f"\n⚠️  Issues found that may need attention:")
        print(f"   Consider using string literals for forward references.")
        
    return 0

if __name__ == "__main__":
    exit(main())