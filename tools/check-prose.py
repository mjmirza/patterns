#!/usr/bin/env python3
"""Prose gate. Blocks AI slop vocabulary, banned punctuation, and emojis.
Code fences and ASCII diagrams are exempt because they are not prose."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [ROOT / "patterns", ROOT / "docs"]
EXTRA_FILES = [ROOT / "README.md", ROOT / "ATTRIBUTION.md"]

BANNED_CHARS = {
    "—": "em dash",
    "–": "en dash",
    "…": "ellipsis character, write three periods",
}

BANNED_WORDS = [
    "leverage",
    "leveraging",
    "delve",
    "delving",
    "robust",
    "seamless",
    "seamlessly",
    "comprehensive",
    "crucial",
    "vital",
    "unlock",
    "unlocking",
    "elevate",
    "elevating",
    "journey",
    "landscape",
    "realm",
    "harness",
    "harnessing",
    "empower",
    "empowering",
    "streamline",
    "streamlining",
    "cutting-edge",
    "game-changer",
    "game-changing",
    "ensure",
    "ensures",
    "ensuring",
    "furthermore",
    "moreover",
    "showcase",
    "showcases",
    "showcasing",
    "underscore",
    "underscores",
    "foster",
    "fostering",
    "nurture",
    "nurturing",
    "innovative",
    "meticulous",
    "meticulously",
    "intricate",
    "intricacies",
    "paradigm shift",
    "tapestry",
    "embark",
    "navigate the",
    "in today's",
    "it is important to note",
    "it is worth noting",
    "dive into",
    "deep dive",
    "at its core",
    "the real question is",
    "let us explore",
    "in conclusion",
]

EMOJI = re.compile(
    "["
    "\U0001f300-\U0001faff"
    "\U00002600-\U000027bf"
    "\U0001f000-\U0001f2ff"
    "\U0000fe00-\U0000fe0f"
    "]"
)

BANNED_PHRASES = [w for w in BANNED_WORDS if " " in w]
BANNED_SINGLE_WORDS = [w for w in BANNED_WORDS if " " not in w]

# A banned slop word can collide with a real proper noun (a cited surname).
# Skip the match only when capitalized exactly like the known name.
PROPER_NOUN_COLLISIONS = {
    "Foster",
}
BANNED_SINGLE_RE = re.compile(
    r"\b(?:" + "|".join(map(re.escape, BANNED_SINGLE_WORDS)) + r")\b"
)


def prose_lines(text: str) -> list[tuple[int, str]]:
    # Returns prose lines with 1-based numbers. Fences and frontmatter removed.
    out: list[tuple[int, str]] = []
    inside_fence = False
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    for i in range(start, len(lines)):
        line = lines[i]
        if line.lstrip().startswith("```"):
            inside_fence = not inside_fence
            continue
        if not inside_fence:
            out.append((i + 1, line))
    return out


def strip_inline_code(line: str) -> str:
    return re.sub(r"`[^`]*`", " ", line)


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []

    for lineno, raw in prose_lines(text):
        line = strip_inline_code(raw)
        low = line.lower()

        for ch, label in BANNED_CHARS.items():
            if ch in line:
                errors.append(f"line {lineno}: {label}")

        if EMOJI.search(line):
            errors.append(f"line {lineno}: emoji")

        for phrase in BANNED_PHRASES:
            if phrase in low:
                errors.append(f"line {lineno}: banned phrase '{phrase}'")

        for m in BANNED_SINGLE_RE.finditer(low):
            original = line[m.start() : m.end()]
            if original in PROPER_NOUN_COLLISIONS:
                continue
            errors.append(f"line {lineno}: banned word '{m.group(0)}'")

        if raw.strip() == "---":
            errors.append(f"line {lineno}: triple-dash used as separator")

    return errors


def collect() -> list[Path]:
    files: list[Path] = []
    for base in TARGETS:
        if base.exists():
            files.extend(sorted(base.rglob("*.md")))
    files.extend(f for f in EXTRA_FILES if f.exists())
    return files


def main() -> int:
    files = collect()
    failed = 0
    for f in files:
        errs = check(f)
        rel = f.relative_to(ROOT)
        if errs:
            failed += 1
            print(f"FAIL {rel}")
            for e in errs[:25]:
                print(f"     {e}")
            if len(errs) > 25:
                print(f"     and {len(errs) - 25} more")
    print(f"\n{len(files) - failed}/{len(files)} files pass the prose gate")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
