#!/usr/bin/env python3
"""Emits the next N unfinished entries from the queue as workflow args.
State lives on disk, so a compacted or fresh session resumes with zero context."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "docs" / "AUTHORING-QUEUE.json"


def passing() -> set[str]:
    # An entry is finished when the structural gate says PASS. Nothing else counts.
    try:
        out = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check-structure.py")],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=300,
        ).stdout
    except Exception:
        return set()
    return {
        line.split(None, 1)[1].strip()
        for line in out.splitlines()
        if line.startswith("PASS ")
    }


def claimed_paths() -> dict[str, int]:
    # A path with an open PR is claimed. Fail open on any gh/network error.
    try:
        prs = json.loads(
            subprocess.run(
                ["gh", "pr", "list", "--state", "open", "--json", "number,files"],
                capture_output=True,
                text=True,
                cwd=ROOT,
                timeout=20,
            ).stdout
            or "[]"
        )
    except Exception:
        return {}
    claims: dict[str, int] = {}
    for pr in prs:
        num = pr.get("number")
        if num is None:
            continue
        for f in pr.get("files", []):
            path = f.get("path", "")
            if path.startswith("patterns/") and path.endswith(".md"):
                claims[path] = num
    return claims


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=8)
    ap.add_argument("--family", help="restrict to one family directory prefix")
    ap.add_argument("--status", action="store_true", help="counts only")
    args = ap.parse_args()

    if not QUEUE.exists():
        print(f"queue missing at {QUEUE}", file=sys.stderr)
        return 1

    entries = json.loads(QUEUE.read_text())
    done = passing()
    claims = claimed_paths()
    todo = [e for e in entries if e["path"] not in done and e["path"] not in claims]
    if args.family:
        todo = [e for e in todo if e["path"].startswith(f"patterns/{args.family}")]

    if claims and not args.status:
        skipped = ", ".join(f"{p} (PR #{n})" for p, n in list(claims.items())[:5])
        print(
            f"skipping {len(claims)} claimed by an open PR: {skipped}", file=sys.stderr
        )

    if args.status:
        by_family: dict[str, list[int]] = {}
        for e in entries:
            fam = e["path"].split("/")[1]
            slot = by_family.setdefault(fam, [0, 0])
            slot[1] += 1
            if e["path"] in done:
                slot[0] += 1
        for fam in sorted(by_family):
            d, t = by_family[fam]
            bar = "#" * round(20 * d / t) if t else ""
            print(f"{fam:<26} {d:>3}/{t:<3} {bar}")
        print(f"\n{len(done)} done, {len(todo)} remaining, {len(entries)} total")
        return 0

    print(json.dumps(todo[: args.size], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
