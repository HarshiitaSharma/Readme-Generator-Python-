# readme-gen

A small CLI that scans a project directory — `package.json`, `pyproject.toml`, `requirements.txt`, the file tree, license, tests — and drafts a `README.md` from what it finds.

It won't write your project description for you, but it will save you from re-typing the same install instructions, folder tree, and license boilerplate for the tenth project this month.

## What it detects

- **Project type** — Node (`package.json`), Python (`pyproject.toml` / `requirements.txt` / `setup.py`), or mixed
- **Languages** — by scanning file extensions across the repo
- **Dependencies** — from `package.json`, `pyproject.toml` (PEP 621 or Poetry), or `requirements.txt`
- **Scripts / CLI commands** — npm `scripts`, or Python `[project.scripts]` console entry points
- **Folder structure** — a depth-limited tree, skipping `node_modules`, `.git`, `__pycache__`, build artifacts, etc.
- **Tests** — presence of a `tests/`, `test/`, `__tests__/`, or `spec/` directory
- **License** — presence and type (MIT, Apache, GPL, BSD, MPL) from a `LICENSE` file
- **`.env.example`** — flags whether one exists, so the README can mention it

## Installation

```bash
git clone https://github.com/yourusername/readme-gen.git
cd readme-gen
pip install -e .
```

This installs the `readme-gen` command on your PATH.

## Usage

```bash
# Generate README.md in the current directory
readme-gen

# Point it at another project
readme-gen path/to/project

# Preview without writing a file
readme-gen path/to/project --stdout

# Overwrite an existing README.md
readme-gen path/to/project --force

# Write somewhere other than <path>/README.md
readme-gen path/to/project -o docs/README.md
```

The generated file is a starting point, not a finished product — it fills in placeholders (marked `TODO` or in italics) for anything it can't infer, like a project description or a missing license.

## Project Structure

```
readme-gen/
├── src/
│   └── readme_generator/
│       ├── __init__.py
│       ├── cli.py          # argparse entry point
│       ├── scanner.py      # walks the repo, extracts ProjectInfo
│       └── render.py       # ProjectInfo -> README.md text
├── tests/
│   ├── fixtures/           # small fake Node & Python projects used in tests
│   └── test_scanner.py
├── .github/workflows/tests.yml
├── LICENSE
└── pyproject.toml
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

CI runs the same suite on Python 3.10–3.12 via GitHub Actions on every push and PR to `main`.

## Limitations / roadmap

- Dependency parsing for Poetry and PEP 621 covers the common cases, not every edge case (e.g., optional dependency groups, workspace monorepos).
- No AI-assisted description writing yet — descriptions are pulled verbatim from `package.json`/`pyproject.toml` metadata if present, otherwise left as a `TODO`.
- Doesn't yet detect Go, Rust, or Ruby project manifests (`go.mod`, `Cargo.toml`, `Gemfile`) — language *files* are detected for the tech-stack list, but not their dependency managers.

Contributions welcome — especially more manifest formats and language detectors.

## License

MIT — see [LICENSE](LICENSE) for details.
