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


def parse_table_slugs() -> dict[str, str]:
    # Return {slug: family_title} for every row in the families table.
    content = README.read_text()
    idx = content.find(TABLE_HEADER)
    if idx == -1:
        print(f"ERROR: '{TABLE_HEADER}' section not found in README.md")
        sys.exit(1)
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
    return slugs


def main() -> int:
    table_slugs = parse_table_slugs()
    if not table_slugs:
        print("ERROR: no family rows parsed from README.md families table")
        return 1

    actual_dirs = sorted(p.name for p in PATTERNS.iterdir() if p.is_dir())
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
        print("FAIL: family folder names do not match README.md families table\n")
        for p in problems:
            print(f"  - {p}")
        print(
            "\nThe README '## The families' table is the single source of "
            "truth for family folder naming in this repo. See "
            "docs/FAMILY-NAMING.md."
        )
        return 1

    print(
        f"{len(actual_dirs)} family folder(s) on disk, all match README.md families table"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
