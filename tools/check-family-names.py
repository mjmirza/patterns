#!/usr/bin/env python3
"""Family folder naming gate. README.md '## The families' table is the
source of truth for every patterns/<slug>/ name. See docs/FAMILY-NAMING.md."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"
README = ROOT / "README.md"

TABLE_HEADER = "## The families"
LINK_RE = re.compile(r"\[([^\]]+)\]\(patterns/([^/)]+)/\)")


def parse_table_slugs(readme_path: Path = README) -> tuple[dict[str, str], str | None]:
    """Return ({slug: family_title}, error_message).
    If header missing or file unreadable, error_message is set."""
    if not readme_path.exists():
        return {}, f"file not found: {readme_path}"

    content = readme_path.read_text(encoding="utf-8", errors="replace")
    idx = content.find(TABLE_HEADER)
    if idx == -1:
        return {}, f"'{TABLE_HEADER}' section not found in {readme_path.name}"

    # Table runs until the next '##' heading or EOF.
    rest = content[idx:]
    end = rest.find("\n## ", 4)
    table_block = rest[:end] if end != -1 else rest

    slugs: dict[str, str] = {}
    for line in table_block.splitlines():
        line = line.strip()
        if (
            not line.startswith("|")
            or line.startswith("|---")
            or line.startswith("| # ")
        ):
            continue
        m = LINK_RE.search(line)
        if m:
            title, slug = m.group(1), m.group(2)
            slugs[slug] = title

    if not slugs:
        return {}, "no family rows parsed from README.md families table"

    return slugs, None


def verify_family_names(
    patterns_dir: Path = PATTERNS, readme_path: Path = README
) -> tuple[int, list[str]]:
    """Check family directory names against README table.
    Returns (status_code, output_lines).
    0 = pass, 1 = fail."""
    table_slugs, err = parse_table_slugs(readme_path)
    if err or not table_slugs:
        return 1, [f"ERROR: {err}"]

    if not patterns_dir.exists():
        return 1, [f"ERROR: patterns directory not found: {patterns_dir}"]

    actual_dirs = sorted(p.name for p in patterns_dir.iterdir() if p.is_dir())
    table_slug_set = set(table_slugs)

    problems: list[str] = []

    for d in actual_dirs:
        if d not in table_slug_set:
            problems.append(
                f"patterns/{d}/ exists on disk but is NOT declared in the "
                f"README '## The families' table. Either rename the folder "
                f"to match the table, or update the table if the family "
                f"was intentionally renamed."
            )

    if problems:
        lines = [
            "FAIL: family folder names do not match README.md families table\n"
        ]
        for p in problems:
            lines.append(f"  - {p}")
        lines.append(
            "\nThe README '## The families' table is the single source of "
            "truth for family folder naming in this repo. See "
            "docs/FAMILY-NAMING.md."
        )
        return 1, lines

    return 0, [
        f"{len(actual_dirs)} family folder(s) on disk, all match README.md families table"
    ]


def main() -> int:
    code, lines = verify_family_names()
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
