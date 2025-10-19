import ast
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set
import difflib
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze as raw_analyze
import json
from collections import defaultdict


class SingleFileModularityAnalyzer:
    """

    Analyzes a single Python file's internal modularity.

    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not self.file_path.suffix == '.py':
            raise ValueError(f"File must be a Python file: {file_path}")
        
        self.module_data = {
            'path': str(self.file_path),
            'ast_tree': None,
            'functions': [],
            'classes': [],
            'imports': [],
            'metrics': {},
            'source': ''
        }
        self.function_relationships = {}
        self.duplication_map = {}
        self.complexity_scores = {}
        
    def analyze_file(self) -> List[Dict[str, Any]]:
        """Main analysis pipeline for single file."""
        print(f"Analyzing file: {self.file_path}\n")
        
        #Load and parse file
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.module_data['source'] = f.read()
        
        # Step 2: AST Analysis
        print("Running AST analysis...")
        self._ast_analyze()
        
        # Step 3: Radon Metrics
        print("Running Radon analysis...")
        self._radon_analyze()
        
        # Step 4: Difflib Comparison (within file)
        print("Running difflib analysis...")
        self._difflib_analyze()
        
        # Step 5: Identify issues
        print("Identifying modularity issues...")
        issues = self._identify_modularity_issues()
        
        # Step 6: Generate suggestions
        print("Generating refactoring suggestions...")
        suggestions = self._generate_refactoring_plan(issues)
        
        return suggestions
    
    # TODO remove
    # def _load_file(self):
    #     """Load the Python file."""
    #     with open(self.file_path, 'r', encoding='utf-8') as f:
    #         self.module_data['source'] = f.read()
    
    def _ast_analyze(self):
        """Perform AST analysis on the file."""
        try:
            source_code = self.module_data['source']
            self.module_data['ast_tree'] = ast.parse(source_code, filename=str(self.file_path))
            
            # Extract structural information
            self._extract_ast_info(source_code)
            
            # Build internal function relationships
            self._build_function_relationships()
            
        except Exception as e:
            print(f"Error parsing file: {e}")
            raise
    
    def _extract_ast_info(self, source_code: str):
        """Extract functions, classes, and imports from AST."""
        for node in ast.walk(self.module_data['ast_tree']):
            if isinstance(node, ast.FunctionDef):
                function_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'end_lineno': node.end_lineno,
                    'args': self._extract_arguments(node),
                    'calls': self._extract_calls(node),
                    'returns': self._has_return(node),
                    'is_private': node.name.startswith('_'),
                    'source': ast.get_source_segment(source_code, node) or '',
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list]
                }
                self.module_data['functions'].append(function_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'lineno': node.lineno,
                    'end_lineno': node.end_lineno,
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                    'bases': [self._get_name(base) for base in node.bases],
                    'source': ast.get_source_segment(source_code, node) or '',
                    'is_private': node.name.startswith('_')
                }
                self.module_data['classes'].append(class_info)
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._extract_import_info(node)
                self.module_data['imports'].append(import_info)
    
    def _extract_arguments(self, node: ast.FunctionDef) -> List[str]:
        """Extract function arguments."""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return args
    
    def _extract_calls(self, node: ast.FunctionDef) -> List[str]:
        """Extract function calls within a function."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child)
                if call_name:
                    calls.append(call_name)
        return calls
    
    def _has_return(self, node: ast.FunctionDef) -> bool:
        """Check if function has return statement."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Get the name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ''
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from various AST node types."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return ''
    
    def _get_decorator_name(self, node: ast.AST) -> str:
        """Get decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return ''
    
    def _extract_import_info(self, node: ast.AST) -> Dict[str, Any]:
        """Extract import information."""
        if isinstance(node, ast.Import):
            return {
                'type': 'import',
                'module': None,
                'names': [alias.name for alias in node.names],
                'lineno': node.lineno
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                'type': 'import_from',
                'module': node.module,
                'names': [alias.name for alias in node.names],
                'lineno': node.lineno
            }
        return {}
    
    def _build_function_relationships(self):
        """Build relationships between functions in the file."""
        functions = self.module_data['functions']
        
        for func in functions:
            self.function_relationships[func['name']] = {
                'calls': func['calls'],
                'called_by': [],
                'related_functions': []
            }
        
        # Find which functions call each other
        for func in functions:
            for call in func['calls']:
                if call in self.function_relationships:
                    self.function_relationships[call]['called_by'].append(func['name'])
        
        # Find related functions (share common calls or data)
        for i, func1 in enumerate(functions):
            for func2 in functions[i+1:]:
                shared_calls = set(func1['calls']) & set(func2['calls'])
                if len(shared_calls) >= 2:  # Share at least 2 common calls
                    self.function_relationships[func1['name']]['related_functions'].append(func2['name'])
                    self.function_relationships[func2['name']]['related_functions'].append(func1['name'])
    
    def _radon_analyze(self):
        """Perform Radon complexity analysis."""
        try:
            source_code = self.module_data['source']
            
            # Cyclomatic Complexity
            cc_results = cc_visit(source_code)
            
            # Maintainability Index
            mi_score = mi_visit(source_code, multi=True)
            
            # Raw metrics
            raw = raw_analyze(source_code)
            
            self.module_data['metrics'] = {
                'complexity': cc_results,
                'maintainability': mi_score,
                'loc': raw.loc,
                'sloc': raw.sloc,
                'comments': raw.comments,
                'multi': raw.multi,
                'blank': raw.blank
            }
            
            # Add complexity to individual functions
            for func in self.module_data['functions']:
                func['complexity'] = self._find_complexity_for_function(cc_results, func['name'])
            
            # Store file-level scores
            self.complexity_scores = {
                'average_complexity': self._calculate_average_complexity(cc_results),
                'max_complexity': max([cc.complexity for cc in cc_results], default=0),
                'maintainability': mi_score,
                'size': raw.sloc,
                'function_count': len(self.module_data['functions']),
                'class_count': len(self.module_data['classes'])
            }
            
        except Exception as e:
            print(f"Error analyzing with Radon: {e}")
    
    def _find_complexity_for_function(self, cc_results: List, func_name: str) -> int:
        """Find complexity score for a specific function."""
        for cc in cc_results:
            if cc.name == func_name:
                return cc.complexity
        return 0
    
    def _calculate_average_complexity(self, cc_results: List) -> float:
        """Calculate average complexity."""
        if not cc_results:
            return 0.0
        return sum(cc.complexity for cc in cc_results) / len(cc_results)
    
    def _difflib_analyze(self):
        """Perform difflib similarity analysis within the file."""
        functions = self.module_data['functions']
        
        # Compare all functions against each other within the same file
        for i, func1 in enumerate(functions):
            for func2 in functions[i+1:]:
                # Normalize and compare
                norm1 = self._normalize_code(func1['source'])
                norm2 = self._normalize_code(func2['source'])
                
                similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
                
                if similarity > 0.7:  # 70% similar threshold for same file
                    key = (func1['name'], func2['name'])
                    
                    self.duplication_map[key] = {
                        'func1': func1['name'],
                        'func2': func2['name'],
                        'similarity': similarity,
                        'source1': func1['source'],
                        'source2': func2['source'],
                        'line1': func1['lineno'],
                        'line2': func2['lineno'],
                        'complexity1': func1.get('complexity', 0),
                        'complexity2': func2.get('complexity', 0)
                    }
    
    def _normalize_code(self, source: str) -> str:
        """Normalize code for comparison."""
        if not source:
            return ''
        
        lines = source.split('\n')
        normalized = []
        
        for line in lines:
            stripped = line.strip()
            # Remove comments and empty lines
            if stripped and not stripped.startswith('#'):
                # Remove string literals for better structural comparison
                normalized.append(stripped)
        
        return '\n'.join(normalized)
    
    def _identify_modularity_issues(self) -> List[Dict[str, Any]]:
        """Identify modularity issues within the file."""
        issues = []
        
        # Issue 1: File is too large
        if self.complexity_scores['size'] > 500:
            issues.append({
                'type': 'large_file',
                'severity': 'high',
                'metrics': self.complexity_scores,
                'description': f"File is too large ({self.complexity_scores['size']} SLOC). Consider splitting."
            })
        
        # Issue 2: Too many functions (low cohesion indicator)
        if self.complexity_scores['function_count'] > 20:
            issues.append({
                'type': 'too_many_functions',
                'severity': 'medium',
                'count': self.complexity_scores['function_count'],
                'description': f"File has {self.complexity_scores['function_count']} functions. Consider organizing into classes or modules."
            })
        
        # Issue 3: Complex functions
        complex_functions = [
            f for f in self.module_data['functions']
            if f.get('complexity', 0) > 10
        ]
        if complex_functions:
            issues.append({
                'type': 'complex_functions',
                'severity': 'high',
                'functions': [{'name': f['name'], 'complexity': f['complexity'], 'line': f['lineno']} for f in complex_functions],
                'description': f"{len(complex_functions)} functions have high complexity (>10)"
            })
        
        # Issue 4: Duplicate code within file
        if self.duplication_map:
            high_similarity = [d for d in self.duplication_map.values() if d['similarity'] > 0.85]
            if high_similarity:
                issues.append({
                    'type': 'internal_duplication',
                    'severity': 'high' if len(high_similarity) > 3 else 'medium',
                    'duplicates': list(self.duplication_map.values()),
                    'count': len(self.duplication_map),
                    'description': f"{len(self.duplication_map)} pairs of similar functions found"
                })
        
        # Issue 5: Orphan functions (not called by anything)
        orphan_functions = [
            f for f in self.module_data['functions']
            if not f['is_private'] 
            and len(self.function_relationships.get(f['name'], {}).get('called_by', [])) == 0
            and f['name'] not in ['main', '__init__']
            and 'test_' not in f['name']
        ]
        if len(orphan_functions) > 5:
            issues.append({
                'type': 'orphan_functions',
                'severity': 'low',
                'functions': [f['name'] for f in orphan_functions],
                'count': len(orphan_functions),
                'description': f"{len(orphan_functions)} functions are never called internally"
            })
        
        # Issue 6: God functions (too long)
        god_functions = [
            f for f in self.module_data['functions']
            if len(f['source'].split('\n')) > 50
        ]
        if god_functions:
            issues.append({
                'type': 'god_functions',
                'severity': 'medium',
                'functions': [{'name': f['name'], 'lines': len(f['source'].split('\n')), 'line': f['lineno']} for f in god_functions],
                'description': f"{len(god_functions)} functions are too long (>50 lines)"
            })
        
        # Issue 7: Low maintainability
        if self.complexity_scores['maintainability'] < 65:
            issues.append({
                'type': 'low_maintainability',
                'severity': 'high',
                'score': self.complexity_scores['maintainability'],
                'description': f"Low maintainability index: {self.complexity_scores['maintainability']:.2f}"
            })
        
        # Issue 8: Mixed responsibilities (many unrelated functions)
        cohesion = self._calculate_file_cohesion()
        if cohesion < 0.3 and self.complexity_scores['function_count'] > 10:
            issues.append({
                'type': 'mixed_responsibilities',
                'severity': 'medium',
                'cohesion': cohesion,
                'description': f"Low cohesion ({cohesion:.2f}): File likely has mixed responsibilities"
            })
        
        # Issue 9: No classes (procedural style with many functions)
        if self.complexity_scores['class_count'] == 0 and self.complexity_scores['function_count'] > 15:
            issues.append({
                'type': 'procedural_style',
                'severity': 'low',
                'function_count': self.complexity_scores['function_count'],
                'description': "Consider using classes to organize related functions"
            })
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        issues.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return issues
    
    def _calculate_file_cohesion(self) -> float:
        """Calculate cohesion of functions in the file."""
        functions = self.module_data['functions']
        
        if len(functions) < 2:
            return 1.0
        
        # Count how many functions are related to each other
        total_relationships = 0
        possible_relationships = len(functions) * (len(functions) - 1) / 2
        
        for func_name, relationships in self.function_relationships.items():
            total_relationships += len(relationships['called_by'])
            total_relationships += len(relationships['related_functions'])
        
        # Divide by 2 since we count each relationship twice
        total_relationships = total_relationships / 2
        
        if possible_relationships == 0:
            return 1.0
        
        return min(1.0, total_relationships / possible_relationships)
    
    def _generate_refactoring_plan(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate refactoring suggestions for identified issues."""
        suggestions = []
        
        for issue in issues:
            if issue['type'] == 'internal_duplication':
                suggestion = self._handle_internal_duplication(issue)
                suggestions.append(suggestion)
            
            elif issue['type'] == 'large_file':
                suggestion = self._handle_large_file(issue)
                suggestions.append(suggestion)
            
            elif issue['type'] == 'complex_functions':
                suggestion = self._handle_complex_functions(issue)
                suggestions.append(suggestion)
            
            elif issue['type'] == 'god_functions':
                suggestion = self._handle_god_functions(issue)
                suggestions.append(suggestion)
            
            elif issue['type'] == 'mixed_responsibilities':
                suggestion = self._handle_mixed_responsibilities(issue)
                suggestions.append(suggestion)
            
            elif issue['type'] == 'too_many_functions':
                suggestion = self._handle_too_many_functions(issue)
                suggestions.append(suggestion)
            
            elif issue['type'] == 'procedural_style':
                suggestion = self._handle_procedural_style(issue)
                suggestions.append(suggestion)
            
            elif issue['type'] == 'low_maintainability':
                suggestion = self._handle_low_maintainability(issue)
                suggestions.append(suggestion)
            
            elif issue['type'] == 'orphan_functions':
                suggestion = self._handle_orphan_functions(issue)
                suggestions.append(suggestion)
        
        return suggestions
    
    def _handle_internal_duplication(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle internal code duplication."""
        duplicates = issue['duplicates']
        
        return {
            'action': 'extract_common_function',
            'issue': issue,
            'steps': [
                {
                    'type': 'identify_common_code',
                    'description': 'Extract common logic into a helper function',
                    'duplicate_pairs': [(d['func1'], d['func2']) for d in duplicates]
                },
                {
                    'type': 'refactor_duplicates',
                    'description': 'Replace duplicate code with calls to helper function',
                    'count': len(duplicates)
                }
            ],
            'estimated_impact': {
                'lines_saved': sum(len(d['source1'].split('\n')) for d in duplicates) // 2,
                'duplicate_count': len(duplicates)
            }
        }
    
    def _handle_large_file(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle large file issue."""
        # Cluster functions by relationships
        clusters = self._cluster_functions()
        
        return {
            'action': 'split_file',
            'issue': issue,
            'steps': [
                {
                    'type': 'create_module',
                    'name': f"module_{i+1}.py",
                    'functions': cluster,
                    'description': f'Extract {len(cluster)} related functions'
                }
                for i, cluster in enumerate(clusters)
            ],
            'estimated_impact': {
                'new_files': len(clusters),
                'current_size': issue['metrics']['size'],
                'estimated_new_sizes': [len(c) * 20 for c in clusters]  # Rough estimate
            }
        }
    
    def _handle_complex_functions(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex functions."""
        return {
            'action': 'simplify_functions',
            'issue': issue,
            'steps': [
                {
                    'type': 'break_down_function',
                    'function': func['name'],
                    'line': func['line'],
                    'complexity': func['complexity'],
                    'description': f"Break down {func['name']} (complexity: {func['complexity']})"
                }
                for func in issue['functions']
            ],
            'estimated_impact': {
                'functions_affected': len(issue['functions']),
                'average_complexity_reduction': '50-70%'
            }
        }
    
    def _handle_god_functions(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle god functions."""
        return {
            'action': 'split_long_functions',
            'issue': issue,
            'steps': [
                {
                    'type': 'extract_methods',
                    'function': func['name'],
                    'line': func['line'],
                    'lines': func['lines'],
                    'description': f"Split {func['name']} ({func['lines']} lines) into smaller functions"
                }
                for func in issue['functions']
            ],
            'estimated_impact': {
                'functions_affected': len(issue['functions']),
                'estimated_new_functions': len(issue['functions']) * 3
            }
        }
    
    def _handle_mixed_responsibilities(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mixed responsibilities."""
        clusters = self._cluster_functions()
        
        return {
            'action': 'separate_concerns',
            'issue': issue,
            'steps': [
                {
                    'type': 'create_focused_module',
                    'description': 'Group related functions into separate modules or classes',
                    'clusters': len(clusters)
                }
            ],
            'estimated_impact': {
                'cohesion_improvement': '2-3x',
                'suggested_modules': len(clusters)
            }
        }
    
    def _handle_too_many_functions(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle too many functions."""
        return {
            'action': 'organize_functions',
            'issue': issue,
            'steps': [
                {
                    'type': 'group_into_classes',
                    'description': 'Organize related functions into classes',
                    'function_count': issue['count']
                }
            ],
            'estimated_impact': {
                'current_functions': issue['count'],
                'estimated_classes': issue['count'] // 5
            }
        }
    
    def _handle_procedural_style(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle procedural style."""
        return {
            'action': 'introduce_classes',
            'issue': issue,
            'steps': [
                {
                    'type': 'convert_to_oop',
                    'description': 'Convert related functions into class methods',
                    'function_count': issue['function_count']
                }
            ],
            'estimated_impact': {
                'style_improvement': 'Better encapsulation and organization'
            }
        }
    
    def _handle_low_maintainability(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle low maintainability."""
        return {
            'action': 'improve_maintainability',
            'issue': issue,
            'steps': [
                {
                    'type': 'reduce_complexity',
                    'description': 'Simplify complex functions and improve code structure'
                },
                {
                    'type': 'add_documentation',
                    'description': 'Add docstrings and comments'
                },
                {
                    'type': 'improve_naming',
                    'description': 'Use more descriptive variable and function names'
                }
            ],
            'estimated_impact': {
                'current_score': issue['score'],
                'target_score': 75
            }
        }
    
    def _handle_orphan_functions(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Handle orphan functions."""
        return {
            'action': 'review_unused_code',
            'issue': issue,
            'steps': [
                {
                    'type': 'verify_usage',
                    'description': 'Verify if these functions are part of public API',
                    'functions': issue['functions'][:5]  # Show first 5
                },
                {
                    'type': 'consider_removal',
                    'description': 'Consider removing or documenting as utility functions'
                }
            ],
            'estimated_impact': {
                'functions_to_review': issue['count']
            }
        }
    
    def _cluster_functions(self) -> List[List[str]]:
        """Cluster functions by relationships."""
        functions = self.module_data['functions']
        clusters = []
        assigned = set()
        
        for func in functions:
            if func['name'] in assigned:
                continue
            
            # Start new cluster
            cluster = [func['name']]
            assigned.add(func['name'])
            
            # Add related functions
            relationships = self.function_relationships.get(func['name'], {})
            for related in relationships.get('related_functions', []):
                if related not in assigned:
                    cluster.append(related)
                    assigned.add(related)
            
            if cluster:
                clusters.append(cluster)
        
        # Add unassigned functions to smallest cluster or create new
        unassigned = [f['name'] for f in functions if f['name'] not in assigned]
        if unassigned:
            if clusters:
                clusters[0].extend(unassigned)
            else:
                clusters.append(unassigned)
        
        return clusters
    
    # def export_results(self, suggestions: List[Dict[str, Any]], output_file: str = None):
    #     """Export analysis results to JSON."""
    #     if output_file is None:
    #         output_file = self.file_path.stem + '_modularity_report.json'
        
    #     report = {
    #         'file_path': str(self.file_path),
    #         'file_name': self.file_path.name,
    #         'total_issues': len(suggestions),
    #         'suggestions': suggestions,
    #         'summary': {
    #             'total_functions': len(self.module_data['functions']),
    #             'total_classes': len(self.module_data['classes']),
    #             'total_lines': self.module_data['metrics'].get('loc', 0),
    #             'sloc': self.module_data['metrics'].get('sloc', 0),
    #             'average_complexity': self.complexity_scores.get('average_complexity', 0),
    #             'max_complexity': self.complexity_scores.get('max_complexity', 0),
    #             'maintainability': self.complexity_scores.get('maintainability', 0),
    #             'cohesion': self._calculate_file_cohesion()
    #         },
    #         'functions': [
    #             {
    #                 'name': f['name'],
    #                 'line': f['lineno'],
    #                 'complexity': f.get('complexity', 0),
    #                 'lines': len(f['source'].split('\n')),
    #                 'is_private': f['is_private']
    #             }
    #             for f in self.module_data['functions']
    #         ]
    #     }
        
    #     with open(output_file, 'w', encoding='utf-8') as f:
    #         json.dump(report, f, indent=2, default=str)
        
    #     print(f"\nReport exported to {output_file}")
    #     return report
    
#     def print_summary(self, suggestions: List[Dict[str, Any]]):
#         """Print a human-readable summary."""
#         print("\n" + "="*80)
#         print("FILE MODULARITY ANALYSIS SUMMARY")
#         print("="*80)
        
#         print(f"\nFile: {self.file_path.name}")
#         print(f"Path: {self.file_path}")
#         print(f"\nFile Metrics:")
#         print(f"  Lines of Code: {self.module_data['metrics'].get('loc', 0)}")
#         print(f"  Source Lines: {self.complexity_scores.get('size', 0)}")
#         print(f"  Functions: {self.complexity_scores.get('function_count', 0)}")
#         print(f"  Classes: {self.complexity_scores.get('class_count', 0)}")
#         print(f"  Average Complexity: {self.complexity_scores.get('average_complexity', 0):.2f}")
#         print(f"  Max Complexity: {self.complexity_scores.get('max_complexity', 0)}")
#         print(f"  Maintainability Index: {self.complexity_scores.get('maintainability', 0):.2f}")
#         print(f"  Cohesion Score: {self._calculate_file_cohesion():.2f}")
        
#         print(f"\nTotal issues found: {len(suggestions)}")
        
#         # Count by severity
#         severity_counts = defaultdict(int)
#         for suggestion in suggestions:
#             severity_counts[suggestion['issue']['severity']] += 1
        
#         print("\nIssues by severity:")
#         for severity in ['critical', 'high', 'medium', 'low']:
#             count = severity_counts.get(severity, 0)
#             if count > 0:
#                 print(f"  {severity.upper()}: {count}")
        
#         # Count by type
#         type_counts = defaultdict(int)
#         for suggestion in suggestions:
#             type_counts[suggestion['issue']['type']] += 1
        
#         print("\nIssues by type:")
#         for issue_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
#             print(f"  {issue_type.replace('_', ' ').title()}: {count}")
        
#         print("\n" + "="*80)
#         print("TOP ISSUES")
#         print("="*80)
        
#         for i, suggestion in enumerate(suggestions[:5], 1):
#             issue = suggestion['issue']
#             print(f"\n{i}. [{issue['severity'].upper()}] {issue['type'].replace('_', ' ').title()}")
#             print(f"   {issue['description']}")
#             print(f"   Action: {suggestion['action'].replace('_', ' ').title()}")
#             print(f"   Steps: {len(suggestion.get('steps', []))}")
            
#             # Show specific details based on issue type
#             if issue['type'] == 'complex_functions' and 'functions' in issue:
#                 print(f"   Complex functions:")
#                 for func in issue['functions'][:3]:
#                     print(f"     - {func['name']} (line {func['line']}, complexity: {func['complexity']})")
            
#             elif issue['type'] == 'internal_duplication' and 'duplicates' in issue:
#                 print(f"   Duplicate pairs:")
#                 for dup in issue['duplicates'][:3]:
#                     print(f"     - {dup['func1']} <-> {dup['func2']} ({dup['similarity']:.1%} similar)")
            
#             elif issue['type'] == 'god_functions' and 'functions' in issue:
#                 print(f"   Long functions:")
#                 for func in issue['functions'][:3]:
#                     print(f"     - {func['name']} (line {func['line']}, {func['lines']} lines)")
        
#         # Print most complex functions
#         print("\n" + "="*80)
#         print("MOST COMPLEX FUNCTIONS")
#         print("="*80)
        
#         complex_funcs = sorted(
#             self.module_data['functions'],
#             key=lambda f: f.get('complexity', 0),
#             reverse=True
#         )[:5]
        
#         for i, func in enumerate(complex_funcs, 1):
#             complexity = func.get('complexity', 0)
#             if complexity > 0:
#                 print(f"{i}. {func['name']} - Complexity: {complexity} (line {func['lineno']})")
        
#         # Print function relationships
#         print("\n" + "="*80)
#         print("FUNCTION CALL GRAPH (Top 5 Most Called)")
#         print("="*80)
        
#         most_called = sorted(
#             self.function_relationships.items(),
#             key=lambda x: len(x[1].get('called_by', [])),
#             reverse=True
#         )[:5]
        
#         for func_name, relationships in most_called:
#             called_by_count = len(relationships.get('called_by', []))
#             if called_by_count > 0:
#                 print(f"\n{func_name}:")
#                 print(f"  Called by {called_by_count} function(s): {', '.join(relationships['called_by'][:3])}")
#                 if len(relationships['called_by']) > 3:
#                     print(f"  ... and {len(relationships['called_by']) - 3} more")


# def generate_diff_preview(suggestion: Dict[str, Any]) -> List[Dict[str, str]]:
#     """Generate diff preview for a refactoring suggestion."""
#     diffs = []
    
#     for step in suggestion.get('steps', []):
#         if step['type'] == 'break_down_function':
#             diff_text = f"=== {step['function']} (line {step['line']}) ===\n"
#             diff_text += f"Complexity: {step['complexity']}\n"
#             diff_text += f"Suggestion: {step['description']}\n"
#             diff_text += "\n# Example refactoring:\n"
#             diff_text += f"- def {step['function']}(...):\n"
#             diff_text += "-     # Long complex function\n"
#             diff_text += "+     \n"
#             diff_text += "+ def {step['function']}_part1(...):\n"
#             diff_text += "+     # First responsibility\n"
#             diff_text += "+     \n"
#             diff_text += "+ def {step['function']}_part2(...):\n"
#             diff_text += "+     # Second responsibility\n"
            
#             diffs.append({
#                 'type': 'function_split',
#                 'diff': diff_text
#             })
        
#         elif step['type'] == 'extract_methods':
#             diff_text = f"=== {step['function']} (line {step['line']}) ===\n"
#             diff_text += f"Current: {step['lines']} lines\n"
#             diff_text += f"Suggestion: {step['description']}\n"
            
#             diffs.append({
#                 'type': 'extract_method',
#                 'diff': diff_text
#             })
        
#         elif step['type'] == 'identify_common_code':
#             diff_text = "=== Code Duplication ===\n"
#             for pair in step['duplicate_pairs'][:3]:
#                 diff_text += f"Similar: {pair[0]} <-> {pair[1]}\n"
#             diff_text += "\nSuggestion: Extract common logic into helper function\n"
            
#             diffs.append({
#                 'type': 'duplication',
#                 'diff': diff_text
#             })
        
#         elif step['type'] == 'create_module':
#             diff_text = f"=== New file: {step['name']} ===\n"
#             diff_text += f"Move {len(step['functions'])} functions:\n"
#             for func in step['functions'][:5]:
#                 diff_text += f"  - {func}\n"
#             if len(step['functions']) > 5:
#                 diff_text += f"  ... and {len(step['functions']) - 5} more\n"
            
#             diffs.append({
#                 'type': 'file_split',
#                 'diff': diff_text
#             })
    
#     return diffs


# Main execution
# if __name__ == "__main__":
#     import sys
    
#     # Get file path from command line
#     if len(sys.argv) > 1:
#         file_path = sys.argv[1]
#     else:
#         print("Usage: python single_file_analyzer.py <path_to_python_file>")
#         print("Example: python single_file_analyzer.py my_script.py")
#         sys.exit(1)
    
#     print(f"Starting modularity analysis...\n")
    
#     # Create analyzer
#     try:
#         analyzer = SingleFileModularityAnalyzer(file_path)
#     except (FileNotFoundError, ValueError) as e:
#         print(f"Error: {e}")
#         sys.exit(1)
    
#     # Run analysis
#     try:
#         suggestions = analyzer.analyze_file()
        
#         # Print summary
#         analyzer.print_summary(suggestions)
        
#         # Export detailed report
#         analyzer.export_results(suggestions)
        
#         # Generate previews for top suggestions
#         if suggestions:
#             print("\n" + "="*80)
#             print("REFACTORING PREVIEWS")
#             print("="*80)
            
#             for i, suggestion in enumerate(suggestions[:3], 1):
#                 print(f"\n--- Preview {i}: {suggestion['action'].replace('_', ' ').title()} ---")
#                 previews = generate_diff_preview(suggestion)
#                 for preview in previews:
#                     print(preview['diff'])
#                     print()
        
#         print("\n" + "="*80)
#         print("Analysis complete!")
#         print(f"Full report saved to: {analyzer.file_path.stem}_modularity_report.json")
#         print("="*80)
        
#     except Exception as e:
#         print(f"Error during analysis: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)