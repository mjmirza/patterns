#!/usr/bin/env python3
"""Tests for catalogue identity, relationship resolution, and internal links."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "catalogue_model", TOOLS / "catalogue_model.py"
)
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def write_entry(
    root: Path, family: str, slug: str, related: str, aliases: str = ""
) -> None:
    path = root / "patterns" / family / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"name: {slug}",
                f"slug: {slug}",
                f"family: {family}",
                "maturity: canonical",
                f"aliases: [{aliases}]",
                f"related: [{related}]",
                "incompatible_with: []",
                "verified: 2026-08-02",
                "---",
                "",
                f"# {slug}",
                "",
                "## 4. Applicability",
                "",
                "Use it when the case is real. Do not use it for a one-off script.",
                "",
            ]
        ),
        encoding="utf-8",
    )


class CatalogueModelTest(unittest.TestCase):
    def test_review_window_is_180_days(self):
        self.assertEqual(model.add_days("2026-08-02", 180), "2027-01-29")

    def test_flow_list_keeps_commas_inside_quotes(self):
        parsed = model.parse_flow_list('["Gamma, Helm", singleton]')
        self.assertEqual(parsed, ["Gamma, Helm", "singleton"])

    def test_windowing_alias_does_not_become_virtual_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_entry(root, "13-frontend-ui", "virtual-list", "", aliases="Windowing")
            write_entry(root, "24-stream-processing", "event-time", "windowing")
            index = model.build_index(root)
            source = index.by_slug["event-time"][0]
            refs, how = model.resolve_token("windowing", source, index)
            self.assertEqual(refs, [])
            self.assertEqual(how, "concept")

    def test_duplicate_slug_is_qualified_and_self_is_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_entry(
                root, "11-domain-driven-design", "value-object", "value-object, money"
            )
            write_entry(
                root, "06-enterprise-application-architecture", "value-object", ""
            )
            write_entry(root, "06-enterprise-application-architecture", "money", "")
            index = model.build_index(root)
            source = next(
                entry
                for entry in index.by_slug["value-object"]
                if "11-" in entry.family
            )
            refs, how = model.resolve_token("value-object", source, index)
            self.assertEqual(how, "slug")
            self.assertEqual(
                refs, ["06-enterprise-application-architecture/value-object"]
            )

    def test_rewrite_is_idempotent_and_sets_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_entry(
                root, "01-design-patterns-gof", "command", "missing-idea, strategy"
            )
            write_entry(root, "01-design-patterns-gof", "strategy", "")
            index = model.build_index(root)
            source = index.by_slug["command"][0]
            once = model.rewrite_text(source, index)
            source.path.write_text(once, encoding="utf-8")
            again_index = model.build_index(root)
            twice = model.rewrite_text(again_index.by_slug["command"][0], again_index)
            self.assertEqual(once, twice)
            self.assertIn("id: pat.01.command", once)
            self.assertIn("kind: pattern", once)
            self.assertIn("related: [strategy]", once)
            self.assertIn("related_concepts: [missing-idea]", once)
            self.assertIn("next_review_due: 2027-01-29", once)
            errors = model.identity_errors(
                again_index.by_slug["command"][0], again_index
            )
            self.assertEqual(errors, [])

    def test_broken_internal_link_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "docs" / "note.md"
            page.parent.mkdir()
            page.write_text(
                "See [missing](missing.md) and [home](../README.md).\n",
                encoding="utf-8",
            )
            (root / "README.md").write_text("# Home\n", encoding="utf-8")
            errors = model.markdown_link_errors(page, page.read_text(), root)
            self.assertEqual(errors, ["broken internal link: missing.md"])

    def test_inline_code_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "note.md"
            page.write_text(
                "Call `map[A, B](fa: F[A])` then see [home](README.md).\n",
                encoding="utf-8",
            )
            (root / "README.md").write_text("# Home\n", encoding="utf-8")
            errors = model.markdown_link_errors(page, page.read_text(), root)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
