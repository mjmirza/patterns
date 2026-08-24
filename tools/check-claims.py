#!/usr/bin/env python3
"""Blocks a PR that adds a patterns/*.md path another open PR already
touches, or a path already published on main. Runs in CI on pull_request."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def added_paths() -> list[str]:
    base = os.environ.get("BASE_SHA", "origin/main")
    out = subprocess.run(
        ["git", "diff", "--name-status", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    ).stdout
    added = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == "A":
            path = parts[-1]
            if path.startswith("patterns/") and path.endswith(".md"):
                added.append(path)
    return added


def published_on_main(path: str) -> bool:
    base = os.environ.get("BASE_SHA", "origin/main")
    r = subprocess.run(
        ["git", "cat-file", "-e", f"{base}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return r.returncode == 0


def sibling_pr_paths(this_pr: str) -> dict[str, int]:
    prs = json.loads(
        subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--json", "number,files"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=False,
        ).stdout
        or "[]"
    )
    claims: dict[str, int] = {}
    for pr in prs:
        num = pr.get("number")
        if num is None or str(num) == str(this_pr):
            continue
        for f in pr.get("files", []):
            p = f.get("path", "") if isinstance(f, dict) else ""
            if p.startswith("patterns/") and p.endswith(".md"):
                claims[p] = num
    return claims


def main() -> int:
    this_pr = os.environ.get("PR_NUMBER", "")
    added = added_paths()
    if not added:
        print("no new patterns/*.md files added, nothing to check")
        return 0

    problems = []
    for path in added:
        if published_on_main(path):
            problems.append(f"{path}: already published on main")

    siblings = sibling_pr_paths(this_pr)
    for path in added:
        if path in siblings:
            problems.append(f"{path}: already claimed by open PR #{siblings[path]}")

    if problems:
        print("CLAIM CHECK FAILED. Two contributors are working on the same entry.")
        for p in problems:
            print(f"  {p}")
        print("")
        print("Rebase off the entry that already exists, or pick a different")
        print("entry from docs/AUTHORING-QUEUE.json. See .github/CONTRIBUTING.md.")
        return 1

    print(f"claim check clean: {len(added)} new entr(y/ies), no collisions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
