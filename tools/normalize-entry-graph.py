#!/usr/bin/env python3
"""Write stable ids, kinds, review dates, and catalogue-only relationship lists."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import catalogue_model as model  # noqa: E402


def report(index: model.Index) -> None:
    how = Counter()
    samples: dict[str, str] = {}
    for entry in index.entries:
        for key in ("related", "incompatible_with"):
            raw = entry.fields.get(key, "[]")
            tokens = model.parse_flow_list(raw) or []
            for token in tokens:
                refs, rule = model.resolve_token(token, entry, index)
                how[rule] += 1
                if rule not in {"slug", "self", "empty"}:
                    samples.setdefault(f"{rule}: {token} -> {refs}", entry.rel)
    print("resolution counts:")
    for rule, count in how.most_common():
        print(f"  {count:4} {rule}")
    print("non-exact resolutions:")
    for label in sorted(samples):
        print(f"  {label}  eg {samples[label]}")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    index = model.build_index(root)
    if "--dry-run" in sys.argv:
        report(index)
        return 0
    changed = 0
    for entry in index.entries:
        updated = model.rewrite_text(entry, index)
        if updated != entry.text:
            entry.path.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"rewrote {changed} of {len(index.entries)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
