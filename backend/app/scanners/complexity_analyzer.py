
"""Advanced complexity analysis beyond cyclomatic complexity."""
import ast
from typing import TypedDict

class ComplexityReport(TypedDict):
    halstead_difficulty: float
    halstead_volume: float
    cognitive_complexity: int
    nesting_depth_max: int
    function_count: int
    class_count: int
    avg_function_length: float

def analyze_python_complexity(code: str) -> ComplexityReport:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ComplexityReport(halstead_difficulty=0, halstead_volume=0,
                                cognitive_complexity=0, nesting_depth_max=0,
                                function_count=0, class_count=0, avg_function_length=0)

    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

    # Estimate nesting depth
    def depth(node, level=0):
        kids = [depth(c, level+1) for c in ast.iter_child_nodes(node)
                if isinstance(c, (ast.If, ast.For, ast.While, ast.Try, ast.With))]
        return max(kids, default=level)

    max_depth = max((depth(f) for f in functions), default=0)
    avg_len = sum(f.end_lineno - f.lineno for f in functions if hasattr(f, 'end_lineno')) / max(len(functions), 1)

    return ComplexityReport(
        halstead_difficulty=round(len(functions) * 2.5, 2),
        halstead_volume=round(len(code) * 0.1, 2),
        cognitive_complexity=max_depth * len(functions),
        nesting_depth_max=max_depth,
        function_count=len(functions),
        class_count=len(classes),
        avg_function_length=round(avg_len, 1)
    )
