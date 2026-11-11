#!/usr/bin/env python3
"""Write dist/entries.json from published frontmatter. Never hand-edit the output."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import catalogue_model as model  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "entries.json"


def payload(index: model.Index) -> dict:
    rows: list[dict] = []
    for entry in index.entries:
        fields = entry.fields
        rows.append(
            {
                "id": fields.get("id", "").strip("'\""),
                "name": entry.name,
                "slug": entry.slug,
                "family": entry.family,
                "kind": fields.get("kind", "").strip("'\""),
                "maturity": fields.get("maturity", "").strip("'\""),
                "path": entry.rel,
                "related": model.parse_flow_list(fields.get("related", "[]")) or [],
                "related_concepts": model.parse_flow_list(
                    fields.get("related_concepts", "[]")
                )
                or [],
                "incompatible_with": model.parse_flow_list(
                    fields.get("incompatible_with", "[]")
                )
                or [],
                "incompatible_concepts": model.parse_flow_list(
                    fields.get("incompatible_concepts", "[]")
                )
                or [],
                "verified": fields.get("verified", "").strip("'\""),
                "last_reviewed": fields.get("last_reviewed", "").strip("'\""),
                "next_review_due": fields.get("next_review_due", "").strip("'\""),
                "applicability_excerpt": model.applicability_excerpt(entry.text),
            }
        )
    rows.sort(key=lambda row: row["id"])
    return {
        "generated_by": "tools/gen-entry-index.py",
        "excerpt_note": (
            "applicability_excerpt is copied from the Applicability section. "
            "It is not a separately authored decision summary."
        ),
        "entries": rows,
    }


def main() -> int:
    index = model.build_index(ROOT)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload(index), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(index.entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
