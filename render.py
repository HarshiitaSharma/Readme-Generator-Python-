"""Turns a ProjectInfo into README.md text."""

from __future__ import annotations

from .scanner import ProjectInfo

RUNTIME_HINT = {
    "node": ("Node.js (includes npm)",),
    "python": ("Python 3.9+",),
    "mixed": ("Node.js (includes npm)", "Python 3.9+"),
    "unknown": (),
}


def _title_case(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").strip().title()


def _install_and_run(info: ProjectInfo) -> str:
    lines = ["## Getting Started", "", "### Prerequisites", ""]
    prereqs = RUNTIME_HINT.get(info.project_type, ())
    if prereqs:
        for p in prereqs:
            lines.append(f"- {p}")
    else:
        lines.append("- _(Could not detect a runtime — add prerequisites here.)_")
    lines += ["", "### Installation", "", "```bash",
              f"git clone https://github.com/yourusername/{info.name}.git",
              f"cd {info.name}"]

    if info.project_type in ("node", "mixed"):
        lines.append("npm install")
    if info.project_type in ("python", "mixed"):
        lines.append("pip install -r requirements.txt  # or: pip install -e .")
    if info.has_env_example:
        lines.append("cp .env.example .env  # then fill in your values")
    lines.append("```")

    if info.scripts:
        lines += ["", "### Available scripts", ""]
        for name, cmd in info.scripts.items():
            lines.append(f"- `npm run {name}` — `{cmd}`")

    if info.cli_commands:
        lines += ["", "### CLI commands", "",
                   "Installed as console scripts, so after installation you can run:", ""]
        for name in info.cli_commands:
            lines.append(f"- `{name}`")

    if not info.scripts and not info.cli_commands and info.entry_points:
        lines += ["", "### Run it", "", "```bash"]
        for ep in info.entry_points:
            if ep.endswith(".py"):
                lines.append(f"python {ep}")
            elif ep.endswith((".js", ".jsx", ".ts", ".tsx")):
                lines.append("npm run dev")
        lines.append("```")

    return "\n".join(lines)


def _tech_stack(info: ProjectInfo) -> str:
    lines = ["## Tech Stack", ""]
    if info.languages:
        lines.append("**Languages:** " + ", ".join(info.languages))
    key_deps = [d for d in info.dependencies if d][:12]
    if key_deps:
        lines.append("")
        lines.append("**Key dependencies:** " + ", ".join(f"`{d}`" for d in key_deps))
    if not info.languages and not key_deps:
        lines.append("_(No dependency manifest detected — list your stack here.)_")
    return "\n".join(lines)


def _folder_structure(info: ProjectInfo) -> str:
    if not info.tree:
        return ""
    body = "\n".join(info.tree)
    return "## Project Structure\n\n```\n" + f"{info.name}/\n{body}\n" + "```"


def render_readme(info: ProjectInfo) -> str:
    title = _title_case(info.name)
    desc = info.description or "_TODO: one or two sentences describing what this project does and why it exists._"

    parts = [f"# {title}", "", desc, ""]

    parts.append(_tech_stack(info))
    parts.append("")

    structure = _folder_structure(info)
    if structure:
        parts.append(structure)
        parts.append("")

    parts.append(_install_and_run(info))
    parts.append("")

    if info.has_tests:
        parts.append("## Testing")
        parts.append("")
        if info.project_type in ("python", "mixed"):
            parts.append("```bash\npytest\n```")
        else:
            parts.append("```bash\nnpm test\n```")
        parts.append("")

    parts.append("## Contributing")
    parts.append("")
    parts.append("Issues and pull requests are welcome. For larger changes, please open an "
                 "issue first to discuss what you'd like to change.")
    parts.append("")

    parts.append("## License")
    parts.append("")
    if info.has_license:
        parts.append(f"{info.license_name} — see [LICENSE](LICENSE) for details.")
    else:
        parts.append("_No license file detected. Consider adding one — "
                      "[choosealicense.com](https://choosealicense.com/) can help you pick._")

    return "\n".join(parts).rstrip() + "\n"
