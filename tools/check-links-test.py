#!/usr/bin/env python3
"""Tests for catalogue identity, relationship resolution, and internal links."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "catalogue_model", TOOLS / "catalogue_model.py"
)
model = importlib.util.module_from_spec(spec)
sys.modules["catalogue_model"] = model
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

    def test_apostrophe_in_an_unquoted_alias_is_part_of_the_name(self):
        parsed = model.parse_flow_list(
            "[Brewer's Theorem, Brewer's Conjecture, CAP Trade-off]"
        )
        self.assertEqual(
            parsed, ["Brewer's Theorem", "Brewer's Conjecture", "CAP Trade-off"]
        )
        parsed = model.parse_flow_list("[Tell Don't Ask, TDA]")
        self.assertEqual(parsed, ["Tell Don't Ask", "TDA"])

    def test_single_quoted_apostrophe_escape(self):
        parsed = model.parse_flow_list("['You''re Not Gonna Need It']")
        self.assertEqual(parsed, ["You're Not Gonna Need It"])

    def test_unclosed_alias_quote_does_not_parse(self):
        self.assertIsNone(model.parse_flow_list('["open]'))

    def test_unclosed_alias_quote_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_entry(root, "04-principles-and-laws", "cap-theorem", "", aliases='"open')
            index = model.build_index(root)
            errors = model.identity_errors(index.by_slug["cap-theorem"][0], index)
            self.assertTrue(
                any("aliases must be a single-line flow list" in error for error in errors),
                errors,
            )

    def test_missing_aliases_key_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "patterns" / "04-principles-and-laws" / "cap-theorem.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "\n".join(
                    [
                        "---",
                        "name: CAP Theorem",
                        "slug: cap-theorem",
                        "id: pat.04.cap-theorem",
                        "kind: law",
                        "family: 04-principles-and-laws",
                        "maturity: canonical",
                        "related: []",
                        "related_concepts: []",
                        "incompatible_with: []",
                        "incompatible_concepts: []",
                        "verified: 2026-08-02",
                        "last_reviewed: 2026-08-02",
                        "next_review_due: 2027-01-29",
                        "---",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            index = model.build_index(root)
            errors = model.identity_errors(index.by_slug["cap-theorem"][0], index)
            self.assertIn("frontmatter missing aliases", errors)

    def test_published_alias_lists_keep_apostrophes_and_quoted_commas(self):
        root = Path(__file__).resolve().parent.parent
        index = model.build_index(root)
        self.assertEqual(
            index.by_slug["cap-theorem"][0].aliases,
            ["Brewer's Theorem", "Brewer's Conjecture", "CAP Trade-off"],
        )
        self.assertIn(
            "Be Conservative In What You Do, Be Liberal In What You Accept",
            index.by_slug["postel-law"][0].aliases,
        )
        self.assertEqual(
            index.by_slug["tell-do-not-ask"][0].aliases[0], "Tell Don't Ask"
        )
        for entry in index.entries:
            parsed = model.parse_flow_list(entry.fields["aliases"])
            self.assertIsNotNone(parsed, entry.rel)
            self.assertEqual(entry.aliases, parsed, entry.rel)
        index_spec = importlib.util.spec_from_file_location(
            "gen_entry_index", TOOLS / "gen-entry-index.py"
        )
        gen_entry_index = importlib.util.module_from_spec(index_spec)
        index_spec.loader.exec_module(gen_entry_index)
        exported = {
            row["slug"]: row["aliases"]
            for row in gen_entry_index.payload(index)["entries"]
            if row["slug"] in {"cap-theorem", "postel-law", "tell-do-not-ask"}
        }
        self.assertEqual(
            exported["cap-theorem"],
            ["Brewer's Theorem", "Brewer's Conjecture", "CAP Trade-off"],
        )
        self.assertIn(
            "Be Conservative In What You Do, Be Liberal In What You Accept",
            exported["postel-law"],
        )
        self.assertEqual(exported["tell-do-not-ask"][0], "Tell Don't Ask")

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

    def test_related_key_does_not_overwrite_related_concepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "patterns" / "01-design-patterns-gof" / "command.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "\n".join(
                    [
                        "---",
                        "name: command",
                        "slug: command",
                        "family: 01-design-patterns-gof",
                        "maturity: canonical",
                        "related_concepts: [not-a-pattern]",
                        "related: [strategy]",
                        "incompatible_with: []",
                        "verified: 2026-08-02",
                        "---",
                        "",
                        "# command",
                        "",
                        "## 4. Applicability",
                        "",
                        "Use it when the case is real.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            write_entry(root, "01-design-patterns-gof", "strategy", "")
            index = model.build_index(root)
            updated = model.rewrite_text(index.by_slug["command"][0], index)
            self.assertIn("related: [strategy]", updated)
            self.assertIn("related_concepts: [not-a-pattern]", updated)

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
