"""Command-line entry point: readme-gen <path>"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .render import render_readme
from .scanner import scan_project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="readme-gen",
        description="Scan a project directory and draft a README.md from what it finds.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Path to the project (default: current directory)")
    parser.add_argument("-o", "--output", default=None,
                         help="Where to write the README (default: <path>/README.md)")
    parser.add_argument("--stdout", action="store_true",
                         help="Print to stdout instead of writing a file")
    parser.add_argument("--force", action="store_true",
                         help="Overwrite README.md if it already exists")
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"error: path does not exist: {root}", file=sys.stderr)
        return 1

    info = scan_project(str(root))
    readme_text = render_readme(info)

    if args.stdout:
        print(readme_text)
        return 0

    out_path = Path(args.output) if args.output else root / "README.md"
    if out_path.exists() and not args.force:
        print(f"error: {out_path} already exists. Use --force to overwrite, or --stdout to preview.",
              file=sys.stderr)
        return 1

    out_path.write_text(readme_text, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
