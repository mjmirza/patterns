#!/usr/bin/env python3
"""Fail on broken internal links, drifted entry ids, or unresolved related refs."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import catalogue_model as model  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LINK_ROOTS = [
    ROOT / "patterns",
    ROOT / "docs",
    ROOT / ".github",
]
LINK_FILES = [
    ROOT / "README.md",
    ROOT / "ATTRIBUTION.md",
    ROOT / "GOVERNANCE.md",
    ROOT / "MAINTAINERS.md",
]


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for base in LINK_ROOTS:
        if base.exists():
            files.extend(sorted(base.rglob("*.md")))
    files.extend(path for path in LINK_FILES if path.exists())
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def main() -> int:
    index = model.build_index(ROOT)
    failed = 0
    for entry in index.entries:
        errors = model.identity_errors(entry, index)
        if errors:
            failed += 1
            print(f"FAIL {entry.rel}")
            for error in errors:
                print(f"     {error}")
    link_failed = 0
    files = markdown_files()
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        errors = model.markdown_link_errors(path, text, ROOT)
        if errors:
            link_failed += 1
            rel = path.relative_to(ROOT)
            print(f"FAIL {rel}")
            for error in errors:
                print(f"     {error}")
    entries = len(index.entries)
    print(
        f"\n{entries - failed}/{entries} entries pass identity and relationship checks"
    )
    print(f"{len(files) - link_failed}/{len(files)} files pass internal links")
    return 1 if failed or link_failed else 0


if __name__ == "__main__":
    sys.exit(main())
