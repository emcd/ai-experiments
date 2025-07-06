#!/usr/bin/env python3
''' Forward reference analyzer for finding NameError issues in type annotations. '''

import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import re


class ForwardReferenceAnalyzer(ast.NodeVisitor):
    ''' AST visitor to analyze forward reference issues. '''
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.class_definitions: Dict[str, int] = {}  # class_name -> line_number
        self.issues: List[Dict[str, Any]] = []
        self.current_class = None
        self.in_class_scope = False
        self.tree = None
        
    def analyze(self, tree: ast.AST) -> List[Dict[str, Any]]:
        ''' Analyze the AST in two passes: collect classes, then check references. '''
        self.tree = tree
        
        # First pass: collect all class definitions
        self._collect_class_definitions(tree)
        
        # Second pass: check for forward references
        self.visit(tree)
        
        return self.issues
        
    def _collect_class_definitions(self, node: ast.AST) -> None:
        ''' First pass: collect all class definitions in the file. '''
        for child in ast.walk(node):
            if isinstance(child, ast.ClassDef):
                self.class_definitions[child.name] = child.lineno
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        ''' Visit class definition and check for forward references. '''
        # Check if this class is used in type annotations before it's defined
        self._check_forward_references_in_class(node)
        
        # Enter class scope
        old_class = self.current_class
        old_in_class = self.in_class_scope
        self.current_class = node.name
        self.in_class_scope = True
        
        self.generic_visit(node)
        
        # Exit class scope
        self.current_class = old_class
        self.in_class_scope = old_in_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        ''' Visit function definition and check annotations. '''
        self._check_annotations_in_function(node)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        ''' Visit async function definition and check annotations. '''
        self._check_annotations_in_function(node)
        self.generic_visit(node)
        
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        ''' Visit annotated assignment (variable annotations). '''
        self._check_annotation_node(node.annotation, node.lineno, "variable annotation")
        self.generic_visit(node)
        
    def _check_forward_references_in_class(self, class_node: ast.ClassDef) -> None:
        ''' Check for forward references within a class definition. '''
        for stmt in class_node.body:
            if isinstance(stmt, ast.AnnAssign):
                self._check_annotation_node(stmt.annotation, stmt.lineno, f"attribute in class {class_node.name}")
                
    def _check_annotations_in_function(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        ''' Check annotations in function parameters and return type. '''
        # Check parameter annotations
        for arg in func_node.args.args:
            if arg.annotation:
                self._check_annotation_node(arg.annotation, func_node.lineno, f"parameter '{arg.arg}' in function {func_node.name}")
                
        # Check return type annotation
        if func_node.returns:
            self._check_annotation_node(func_node.returns, func_node.lineno, f"return type of function {func_node.name}")
            
    def _check_annotation_node(self, annotation: ast.AST, lineno: int, context: str) -> None:
        ''' Check a single annotation node for forward references. '''
        referenced_names = self._extract_names_from_annotation(annotation)
        
        for name in referenced_names:
            if name in self.class_definitions:
                class_def_line = self.class_definitions[name]
                if lineno < class_def_line:
                    # Forward reference detected
                    self.issues.append({
                        'type': 'forward_reference',
                        'line': lineno,
                        'class_name': name,
                        'class_defined_at': class_def_line,
                        'context': context,
                        'annotation': ast.unparse(annotation)
                    })
                    
    def _extract_names_from_annotation(self, annotation: ast.AST) -> Set[str]:
        ''' Extract all identifiers from an annotation. '''
        names = set()
        
        if isinstance(annotation, ast.Name):
            names.add(annotation.id)
        elif isinstance(annotation, ast.Attribute):
            # For things like typing.List, we want the base name
            names.update(self._extract_names_from_annotation(annotation.value))
        elif isinstance(annotation, ast.Subscript):
            # For things like List[Something], check both the base and the subscript
            names.update(self._extract_names_from_annotation(annotation.value))
            names.update(self._extract_names_from_annotation(annotation.slice))
        elif isinstance(annotation, ast.BinOp):
            # For union types like int | str
            names.update(self._extract_names_from_annotation(annotation.left))
            names.update(self._extract_names_from_annotation(annotation.right))
        elif isinstance(annotation, ast.Tuple):
            # For tuple annotations
            for elt in annotation.elts:
                names.update(self._extract_names_from_annotation(elt))
        elif isinstance(annotation, ast.List):
            # For list annotations
            for elt in annotation.elts:
                names.update(self._extract_names_from_annotation(elt))
        elif hasattr(annotation, 'elts'):
            # Generic handling for other collection types
            for elt in annotation.elts:
                names.update(self._extract_names_from_annotation(elt))
                
        return names


def analyze_file(filepath: Path) -> List[Dict[str, Any]]:
    ''' Analyze a single Python file for forward reference issues. '''
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content, filename=str(filepath))
        analyzer = ForwardReferenceAnalyzer(str(filepath))
        return analyzer.analyze(tree)
        
    except SyntaxError as e:
        return [{
            'type': 'syntax_error',
            'line': e.lineno,
            'message': str(e),
            'context': 'file parsing'
        }]
    except Exception as e:
        return [{
            'type': 'analysis_error',
            'line': 0,
            'message': str(e),
            'context': 'file analysis'
        }]


def analyze_directory(directory: Path) -> Dict[str, List[Dict[str, Any]]]:
    ''' Analyze all Python files in a directory for forward reference issues. '''
    results = {}
    
    for py_file in directory.glob('**/*.py'):
        if py_file.is_file():
            issues = analyze_file(py_file)
            if issues:
                results[str(py_file)] = issues
                
    return results


def generate_report(results: Dict[str, List[Dict[str, Any]]]) -> str:
    ''' Generate a human-readable report of forward reference issues. '''
    if not results:
        return "No forward reference issues found."
        
    report = []
    report.append("Forward Reference Analysis Report")
    report.append("=" * 40)
    report.append("")
    
    total_issues = sum(len(issues) for issues in results.values())
    total_files = len(results)
    
    report.append(f"Summary: {total_issues} issues found across {total_files} files")
    report.append("")
    
    for filepath, issues in results.items():
        report.append(f"File: {filepath}")
        report.append("-" * len(f"File: {filepath}"))
        
        for issue in issues:
            if issue['type'] == 'forward_reference':
                report.append(f"  Line {issue['line']}: Forward reference to '{issue['class_name']}'")
                report.append(f"    Context: {issue['context']}")
                report.append(f"    Annotation: {issue['annotation']}")
                report.append(f"    Class '{issue['class_name']}' defined at line {issue['class_defined_at']}")
                report.append(f"    Fix: Add quotes around '{issue['class_name']}' or use string literal")
            elif issue['type'] == 'syntax_error':
                report.append(f"  Line {issue['line']}: Syntax error - {issue['message']}")
            elif issue['type'] == 'analysis_error':
                report.append(f"  Analysis error: {issue['message']}")
            report.append("")
            
    return "\n".join(report)


def main():
    ''' Main entry point for the forward reference analyzer. '''
    import sys
    
    # Allow specifying directory as command line argument
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path("sources/aiwb/apiserver")
    
    if not target_dir.exists():
        print(f"Directory {target_dir} does not exist.")
        return
        
    print(f"Analyzing Python files in {target_dir}...")
    results = analyze_directory(target_dir)
    
    report = generate_report(results)
    print()
    print(report)
    
    # Also save to a file
    with open("forward_reference_report.md", "w") as f:
        f.write(report)
    print(f"\nReport saved to forward_reference_report.md")


if __name__ == "__main__":
    main()