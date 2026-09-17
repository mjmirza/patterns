#!/usr/bin/env python3
"""Internal Markdown Relative Link Checker.

Validates that all relative internal links within Markdown files (.md)
point to existing files or directories within the repository.

Ignores:
- External URLs (http://, https://, mailto:, etc.)
- In-page anchors (#anchor)
- Code blocks (fenced ``` or indented code fences)
- Formatting artifacts / false positives in code snippets
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Regex to match Markdown links: [text](link)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def is_code_block_delimiter(line: str) -> bool:
    s = line.strip()
    return s.startswith("```") or s.startswith("~~~")


def find_md_files(root_dir: Path) -> list[Path]:
    md_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip .git and dist directories
        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir == ".git" or rel_dir.startswith(".git" + os.sep):
            continue
        if rel_dir == "dist" or rel_dir.startswith("dist" + os.sep):
            continue
        for filename in filenames:
            if filename.endswith(".md"):
                md_files.append(Path(dirpath) / filename)
    return sorted(md_files)


def extract_links_from_file(filepath: Path) -> list[tuple[int, str, str]]:
    """Returns a list of tuples: (line_number, link_text, link_target) from non-code prose."""
    links = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return links

    in_code_block = False

    for line_idx, line in enumerate(content.splitlines(), start=1):
        if is_code_block_delimiter(line):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        for m in LINK_RE.finditer(line):
            text, target = m.group(1), m.group(2).strip()

            # Ignore external links
            if (
                target.startswith("http://")
                or target.startswith("https://")
                or target.startswith("mailto:")
                or target.startswith("ftp://")
            ):
                continue

            # Ignore pure anchors
            if target.startswith("#"):
                continue

            # Ignore false positives with space, asterisks, or commas (typically code snippet artifacts)
            if " " in target or "*" in target or "," in target:
                continue

            links.append((line_idx, text, target))

    return links


def check_links(root_dir: Path) -> list[dict]:
    broken = []
    md_files = find_md_files(root_dir)

    for filepath in md_files:
        links = extract_links_from_file(filepath)
        for line_num, text, target in links:
            # Strip anchor fragment if present
            path_part = target.split("#")[0]
            if not path_part:
                continue

            # Resolve relative path against file directory
            target_path = (filepath.parent / path_part).resolve()

            # Check if target exists on disk
            if not target_path.exists():
                broken.append(
                    {
                        "source": str(filepath.relative_to(root_dir)),
                        "line": line_num,
                        "text": text,
                        "target": target,
                        "resolved_path": str(target_path),
                    }
                )

    return broken


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check relative internal links in Markdown files."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code if broken internal links are found.",
    )
    args = parser.parse_args()

    broken = check_links(ROOT)

    if broken:
        print(f"Found {len(broken)} broken internal relative link(s):")
        for b in broken:
            print(f"  {b['source']}:{b['line']} -> [{b['text']}]({b['target']})")
        if args.strict:
            return 1
    else:
        print("All internal relative Markdown links resolve correctly.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
