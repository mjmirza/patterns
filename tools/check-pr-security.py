#!/usr/bin/env python3
"""Blocks a malicious PR. Secrets fail closed; a CI-controlling path
change needs a maintainer-applied label, never the PR author's own diff."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SENSITIVE_PREFIXES = (
    ".github/workflows/",
    "tools/check-structure.py",
    "tools/check-prose.py",
    "tools/check-code.py",
    "tools/validate-refs.py",
    "tools/check-claims.py",
    "tools/check-pr-security.py",
    "tools/gen-catalogue-status.py",
    "tools/gen-indexes.py",
    ".github/CODEOWNERS",
    ".gitignore",
)

OVERRIDE_LABEL = "security-reviewed"

ADVISORY_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"you\s+are\s+now\s+(in\s+)?(developer|admin|jailbreak|dan)\s*mode",
    r"</?\s*(system|assistant)\s*>",
    r"\[INST\]|\[/INST\]",
]

ZERO_WIDTH = set("​‌‍‎‏‪‫‬‭‮⁠⁡⁢⁣⁤﻿")


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, cwd=ROOT, timeout=timeout, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return 127, "", str(e)
    return r.returncode, r.stdout, r.stderr


def base_sha() -> str:
    return os.environ.get("BASE_SHA") or "origin/main"


def changed_paths() -> list[str] | None:
    code, out, err = run(["git", "diff", "--name-only", f"{base_sha()}...HEAD"])
    if code != 0:
        print(
            f"git diff failed, cannot verify this PR is clean: {err}", file=sys.stderr
        )
        return None
    return [p for p in out.splitlines() if p.strip()]


def diff_added_lines(paths: list[str]) -> dict[str, list[str]] | None:
    by_file: dict[str, list[str]] = {}
    for path in paths:
        code, out, err = run(["git", "diff", f"{base_sha()}...HEAD", "--", path])
        if code != 0:
            print(f"git diff failed on {path}: {err}", file=sys.stderr)
            return None
        added = [
            line[1:]
            for line in out.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        if added:
            by_file[path] = added
    return by_file


def sensitive_paths(paths: list[str]) -> list[str]:
    return [
        p for p in paths if any(p == s or p.startswith(s) for s in SENSITIVE_PREFIXES)
    ]


def has_override_label() -> bool:
    pr = os.environ.get("PR_NUMBER", "")
    if not pr:
        return False
    code, out, _ = run(["gh", "pr", "view", pr, "--json", "labels"], timeout=20)
    if code != 0:
        return False
    try:
        labels = json.loads(out).get("labels", [])
    except json.JSONDecodeError:
        return False
    return any(lbl.get("name") == OVERRIDE_LABEL for lbl in labels)


def advisory_injection_scan(by_file: dict[str, list[str]]) -> list[str]:
    notes = []
    compiled = [re.compile(p, re.IGNORECASE) for p in ADVISORY_PATTERNS]
    for path, lines in by_file.items():
        for line in lines:
            norm = unicodedata.normalize("NFKC", line)
            for rx in compiled:
                if rx.search(norm):
                    notes.append(
                        f"{path}: contains instruction-override phrasing (reviewer note)"
                    )
                    break
            if any(ch in ZERO_WIDTH for ch in line):
                notes.append(
                    f"{path}: contains a zero-width/bidi unicode character (reviewer note)"
                )
    return notes


def gitleaks_scan() -> tuple[bool, str]:
    code, out, err = run(
        [
            "gitleaks",
            "detect",
            "--source",
            str(ROOT),
            "--log-opts",
            f"{base_sha()}..HEAD",
            "--no-banner",
        ],
        timeout=60,
    )
    if code == 0:
        return True, ""
    if code == 1:
        return (
            False,
            "gitleaks found a potential secret in this PR's diff, see the job log above",
        )
    return False, f"gitleaks did not run cleanly (exit {code}): {err.strip()[:300]}"


def main() -> int:
    paths = changed_paths()
    if paths is None:
        print("BLOCKED: could not compute this PR's changed files, failing closed")
        return 1
    if not paths:
        print("no changed files, nothing to check")
        return 0

    blocking: list[str] = []

    sensitive = sensitive_paths(paths)
    if sensitive:
        if has_override_label():
            print(
                f"sensitive path(s) touched but '{OVERRIDE_LABEL}' label present, allowed:"
            )
            for p in sensitive:
                print(f"  {p}")
        else:
            blocking.append(
                f"touches CI-controlling path(s) without the '{OVERRIDE_LABEL}' label: "
                + ", ".join(sensitive)
            )

    leaks_clean, leaks_msg = gitleaks_scan()
    if not leaks_clean:
        blocking.append(leaks_msg)

    if blocking:
        print("PR SECURITY CHECK FAILED.")
        for b in blocking:
            print(f"  {b}")
        print("")
        print(
            f"A CI-controlling path change is only allowed after a maintainer "
            f"reads the diff and applies the '{OVERRIDE_LABEL}' label. A fork "
            f"PR author cannot label their own PR."
        )
        return 1

    by_file = diff_added_lines(paths)
    if by_file is None:
        print("BLOCKED: could not read this PR's diff content, failing closed")
        return 1

    notes = advisory_injection_scan(by_file)
    if notes:
        print("Advisory notes for the human reviewer (not blocking):")
        for n in notes:
            print(f"  {n}")

    print(
        f"security check clean: {len(paths)} file(s) changed, no secrets, no unreviewed infra changes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
