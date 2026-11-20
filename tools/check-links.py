#!/usr/bin/env python3
"""Fail on broken internal links, drifted entry ids, unresolved related refs,
or a Wayback replay URL that does not name one capture."""

from __future__ import annotations

import re
import sys
from datetime import datetime
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

# A Wayback replay URL is /web/<capture id>/<original>. The capture id is
# YYYYMMDDhhmmss, optionally followed by a rewrite flag such as id_.
# A shorter id, including a bare 2, is a prefix search. The archive answers
# HTTP 200 and redirects to whichever capture is currently closest.
URL = re.compile(r"https?://[^\s<>\]\"']+")
TRAILING = ".,;:!?"
WAYBACK_REPLAY = re.compile(
    r"^https?://web\.archive\.org/web/([^/]+)(?:/.*)?$",
    re.IGNORECASE,
)
WAYBACK_FLAGS = ("id_", "js_", "cs_", "im_", "if_", "fw_", "mp_", "oe_")


def clean_url(url: str) -> str:
    while url and url[-1] in TRAILING:
        url = url[:-1]
    while url.endswith(")") and url.count("(") < url.count(")"):
        url = url[:-1]
    return url


def prose_without_fences(text: str) -> str:
    out: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return re.sub(r"`[^`]*`", " ", "\n".join(out))


def wayback_timestamp_error(url: str) -> str | None:
    match = WAYBACK_REPLAY.match(url)
    if not match:
        return None
    token = match.group(1)
    digits = token
    for flag in WAYBACK_FLAGS:
        if token.endswith(flag):
            digits = token[: -len(flag)]
            break
    if not re.fullmatch(r"\d{14}", digits):
        return f"wayback capture id must be 14 digits, found '{token}'"
    try:
        datetime.strptime(digits, "%Y%m%d%H%M%S")
    except ValueError:
        return f"wayback capture id is not a calendar time, found '{digits}'"
    return None


def wayback_replay_errors(text: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for raw in URL.findall(prose_without_fences(text)):
        url = clean_url(raw)
        if url in seen:
            continue
        seen.add(url)
        error = wayback_timestamp_error(url)
        if error:
            errors.append(f"{error}: {url}")
    return errors


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
    wayback_failed = 0
    files = markdown_files()
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        errors = model.markdown_link_errors(path, text, ROOT)
        wayback = wayback_replay_errors(text)
        if errors or wayback:
            if errors:
                link_failed += 1
            if wayback:
                wayback_failed += 1
            rel = path.relative_to(ROOT)
            print(f"FAIL {rel}")
            for error in errors:
                print(f"     {error}")
            for error in wayback:
                print(f"     {error}")
    entries = len(index.entries)
    print(
        f"\n{entries - failed}/{entries} entries pass identity and relationship checks"
    )
    print(f"{len(files) - link_failed}/{len(files)} files pass internal links")
    print(
        f"{len(files) - wayback_failed}/{len(files)} files pin every Wayback capture"
    )
    return 1 if failed or link_failed or wayback_failed else 0


if __name__ == "__main__":
    sys.exit(main())
