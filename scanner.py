"""Scans a project directory and extracts facts a README needs."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".pytest_cache", ".mypy_cache",
    "egg-info", ".idea", ".vscode",
}

# Extension -> human label, used to guess the tech stack from the tree.
EXT_LABELS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "React (JSX)",
    ".ts": "TypeScript", ".tsx": "React (TSX)", ".java": "Java",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".c": "C", ".cpp": "C++", ".cs": "C#", ".html": "HTML",
    ".css": "CSS", ".ipynb": "Jupyter Notebook",
}


@dataclass
class ProjectInfo:
    name: str
    description: str = ""
    project_type: str = "unknown"          # "node", "python", "mixed", "unknown"
    languages: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)
    scripts: dict[str, str] = field(default_factory=dict)         # npm scripts (package.json "scripts")
    cli_commands: dict[str, str] = field(default_factory=dict)    # python console entry points ([project.scripts])
    entry_points: list[str] = field(default_factory=list)   # likely "main" files
    has_tests: bool = False
    has_license: bool = False
    license_name: str = ""
    has_env_example: bool = False
    tree: list[str] = field(default_factory=list)


def _walk_tree(root: Path, max_entries: int = 200) -> list[str]:
    """Build a shallow, readable file tree (depth-limited, dirs first)."""
    lines: list[str] = []

    def add(path: Path, prefix: str, depth: int):
        if len(lines) >= max_entries or depth > 3:
            return
        try:
            entries = sorted(
                [p for p in path.iterdir()
                 if p.name not in IGNORE_DIRS
                 and not p.name.startswith(".")
                 and not p.name.endswith((".egg-info", ".dist-info"))],
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except PermissionError:
            return
        for i, entry in enumerate(entries):
            if len(lines) >= max_entries:
                lines.append(prefix + "└── ...")
                return
            connector = "└── " if i == len(entries) - 1 else "├── "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{connector}{entry.name}{suffix}")
            if entry.is_dir():
                extension = "    " if i == len(entries) - 1 else "│   "
                add(entry, prefix + extension, depth + 1)

    add(root, "", 0)
    return lines


def _detect_languages(root: Path) -> list[str]:
    counts: dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")
                       and not d.endswith((".egg-info", ".dist-info"))]
        for f in filenames:
            ext = Path(f).suffix
            if ext in EXT_LABELS:
                counts[EXT_LABELS[ext]] = counts.get(EXT_LABELS[ext], 0) + 1
    return [lang for lang, _ in sorted(counts.items(), key=lambda kv: -kv[1])]


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _parse_requirements_txt(path: Path) -> list[str]:
    deps = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        deps.append(re.split(r"[=<>!~\[]", line)[0].strip())
    return deps


def _parse_pyproject_deps(data: dict) -> list[str]:
    deps = []
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    deps += [k for k in poetry_deps if k.lower() != "python"]
    project_deps = data.get("project", {}).get("dependencies", [])
    deps += [re.split(r"[=<>!~\[]", d)[0].strip() for d in project_deps]
    return deps


def _find_license(root: Path) -> tuple[bool, str]:
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
        p = root / name
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")[:200].upper()
            for lic in ("MIT", "APACHE", "GPL", "BSD", "MPL"):
                if lic in text:
                    return True, lic.title() if lic != "MIT" else "MIT"
            return True, "Custom"
    return False, ""


def scan_project(path: str) -> ProjectInfo:
    root = Path(path).resolve()
    name = root.name
    info = ProjectInfo(name=name)

    pkg_json = root / "package.json"
    pyproject = root / "pyproject.toml"
    requirements = root / "requirements.txt"
    setup_py = root / "setup.py"

    is_node = pkg_json.exists()
    is_python = pyproject.exists() or requirements.exists() or setup_py.exists()

    if is_node and is_python:
        info.project_type = "mixed"
    elif is_node:
        info.project_type = "node"
    elif is_python:
        info.project_type = "python"

    if is_node:
        data = _read_json(pkg_json)
        info.name = data.get("name", info.name)
        info.description = data.get("description", "")
        info.dependencies = sorted((data.get("dependencies") or {}).keys())
        info.dev_dependencies = sorted((data.get("devDependencies") or {}).keys())
        info.scripts = data.get("scripts") or {}
        if "main" in data:
            info.entry_points.append(data["main"])

    if pyproject.exists():
        try:
            import tomllib  # py3.11+
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except ImportError:
            data = {}
        proj = data.get("project", {})
        info.name = proj.get("name", info.name)
        info.description = proj.get("description", info.description)
        info.dependencies += _parse_pyproject_deps(data)
        info.cli_commands.update(proj.get("scripts") or {})
    elif requirements.exists():
        info.dependencies += _parse_requirements_txt(requirements)

    info.languages = _detect_languages(root)

    # Guess entry points if none declared yet.
    if not info.entry_points:
        for candidate in ("main.py", "app.py", "src/main.jsx", "src/main.tsx", "src/index.js", "index.js"):
            if (root / candidate).exists():
                info.entry_points.append(candidate)

    info.has_tests = any((root / d).exists() for d in ("tests", "test", "__tests__", "spec"))
    info.has_env_example = any((root / f).exists() for f in (".env.example", ".env.sample"))
    info.has_license, info.license_name = _find_license(root)
    info.tree = _walk_tree(root)

    return info
