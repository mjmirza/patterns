#!/usr/bin/env python3
"""Structural gate for pattern entries. See docs/ENTRY-TEMPLATE.md for the contract.
Exit 0 when every entry passes, 1 with a per file report otherwise."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"

REQUIRED_SECTIONS = [
    "Name, aliases, and lineage",
    "Problem and context",
    "Forces",
    "Applicability",
    "Structure",
    "Diagram",
    "Dynamics",
    "Implementation variants",
    "Known production uses",
    "Consequences",
    "Failure modes",
    "Trade-off",
    "Related",
    "Refactoring path",
    "Testing",
    "Observability",
    "Security",
    "References",
]

REQUIRED_FRONTMATTER = ["name", "slug", "family", "maturity", "verified"]

VALID_MATURITY = {"canonical", "established", "emerging", "contested", "deprecated"}

FENCE = re.compile(r"^```", re.M)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
CODE_LANG = re.compile(r"^```([a-zA-Z][a-zA-Z0-9+#]*)", re.M)
URL = re.compile(r"https?://[^\s<>)\]]+")

BANNED_CHARS = {"—": "em dash", "–": "en dash"}

KNOWN_LANGS = {
    "typescript",
    "ts",
    "python",
    "py",
    "java",
    "go",
    "rust",
    "rs",
    "csharp",
    "cs",
    "swift",
    "kotlin",
    "kt",
    "javascript",
    "js",
    "cpp",
    "c",
}

MIN_PROSE_WORDS = 1200


def strip_fences(text: str) -> str:
    # Prose checks must not fire inside code blocks or ASCII diagrams.
    out, inside = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []

    fm = FRONTMATTER.match(text)
    if not fm:
        errors.append("missing YAML frontmatter")
    else:
        block = fm.group(1)
        for key in REQUIRED_FRONTMATTER:
            if not re.search(rf"^{key}\s*:", block, re.M):
                errors.append(f"frontmatter missing key '{key}'")
        m = re.search(r"^maturity\s*:\s*(\S+)", block, re.M)
        if m and m.group(1).strip().strip("\"'") not in VALID_MATURITY:
            errors.append(f"invalid maturity '{m.group(1)}'")

    headings = re.findall(r"^#{2,3}\s+(.+)$", text, re.M)
    joined = " || ".join(headings).lower()
    for section in REQUIRED_SECTIONS:
        probe = section.split(",")[0].lower()
        if probe not in joined:
            errors.append(f"missing dimension '{section}'")

    body = text if not fm else text[fm.end() :]
    prose = strip_fences(body)

    for ch, label in BANNED_CHARS.items():
        if ch in prose:
            errors.append(f"banned character in prose: {label}")

    for line in prose.splitlines():
        if line.strip() == "---":
            errors.append("triple-dash used as section separator")
            break

    if len(FENCE.findall(body)) % 2 != 0:
        errors.append("unbalanced code fence")

    langs = {m.lower() for m in CODE_LANG.findall(body)} & KNOWN_LANGS
    if len(langs) < 3:
        errors.append(f"needs 3 code languages, found {len(langs)}: {sorted(langs)}")

    refs = URL.findall(body)
    if len(refs) < 3:
        errors.append(f"needs at least 3 cited URLs, found {len(refs)}")

    if not re.search(r"non-applicab", prose, re.I):
        errors.append("missing non-applicability list")

    words = len(prose.split())
    if words < MIN_PROSE_WORDS:
        errors.append(f"too short for master level: {words} prose words")

    return errors


def main() -> int:
    files = sorted(PATTERNS.rglob("*.md"))
    files = [f for f in files if f.name.lower() not in {"readme.md", "index.md"}]
    if not files:
        print("no pattern entries found")
        return 0

    failed = 0
    for f in files:
        errs = check_file(f)
        rel = f.relative_to(ROOT)
        if errs:
            failed += 1
            print(f"FAIL {rel}")
            for e in errs:
                print(f"     {e}")
        else:
            print(f"PASS {rel}")

    print(f"\n{len(files) - failed}/{len(files)} entries pass the structural gate")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
