import re
from collections import defaultdict
from typing import Dict, List, Set


_PYTHON_IMPORT = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.MULTILINE)
_JS_IMPORT = re.compile(r"""(?:import|require)\s*\(?['"](\.{1,2}/[^'"]+)['"]\)?""", re.MULTILINE)
_JAVA_IMPORT = re.compile(r"^\s*import\s+([\w.]+);", re.MULTILINE)


def _extract_imports(filename: str, content: str) -> List[str]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "py":
        return _PYTHON_IMPORT.findall(content)
    if ext in ("js", "ts", "jsx", "tsx", "mjs"):
        return _JS_IMPORT.findall(content)
    if ext == "java":
        return _JAVA_IMPORT.findall(content)
    return []


def build_dependency_graph(diff: str) -> Dict[str, List[str]]:
    """
    Parse a unified diff and return {filename: [imported_modules]}.
    Only added lines (+) are scanned so we reflect the new state of the code.
    """
    graph: Dict[str, List[str]] = defaultdict(list)
    current_file: str | None = None
    current_lines: List[str] = []

    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            if current_file and current_lines:
                graph[current_file] = _extract_imports(current_file, "\n".join(current_lines))
            current_file = line[6:].strip()
            current_lines = []
        elif line.startswith("+") and not line.startswith("+++"):
            current_lines.append(line[1:])

    if current_file and current_lines:
        graph[current_file] = _extract_imports(current_file, "\n".join(current_lines))

    return dict(graph)


def format_dependency_graph(graph: Dict[str, List[str]]) -> str:
    if not graph:
        return ""
    lines = []
    for filename, imports in graph.items():
        if imports:
            lines.append(f"  {filename} imports: {', '.join(imports[:8])}")
    return "\n".join(lines) if lines else ""


def parse_diff_files(diff: str) -> List[str]:
    """Return list of filenames present in the diff."""
    files = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:].strip())
    return files
