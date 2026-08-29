"""
Walks a Python repo, parses every function with `ast`, and returns a list of
FunctionRecord objects: source code, docstring, and the names of functions it calls.

This is intentionally simple (single-file, no cross-import resolution) — good enough
to build a real dependency graph and real embeddings without turning into a full
static-analysis engine.
"""
import ast
import os
from dataclasses import dataclass, field


@dataclass
class FunctionRecord:
    qualified_name: str      # "path/to/file.py::function_name"
    name: str
    source: str
    docstring: str
    calls: list[str] = field(default_factory=list)  # names of functions called inside


def _extract_calls(node: ast.AST) -> list[str]:
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
            calls.append(child.func.id)
    return calls


def index_repo(repo_path: str) -> list[FunctionRecord]:
    records: list[FunctionRecord] = []

    for root, _, files in os.walk(repo_path):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, repo_path)

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_source = ast.get_source_segment(source, node) or ""
                    docstring = ast.get_docstring(node) or ""
                    records.append(
                        FunctionRecord(
                            qualified_name=f"{rel_path}::{node.name}",
                            name=node.name,
                            source=func_source,
                            docstring=docstring,
                            calls=_extract_calls(node),
                        )
                    )
    return records
