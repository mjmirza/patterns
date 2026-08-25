#!/usr/bin/env python3
"""Unit tests for tools/gen-indexes.py family README index generator."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

spec = importlib.util.spec_from_file_location(
    "gen_indexes", TOOLS / "gen-indexes.py"
)
gen_indexes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_indexes)


class TestGenIndexes(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.tmp = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_field_parsing(self):
        block = 'name: "Strategy Pattern"\ncategory: Behavioral\nmaturity: canonical'
        self.assertEqual(gen_indexes.field(block, "name"), "Strategy Pattern")
        self.assertEqual(gen_indexes.field(block, "category"), "Behavioral")
        self.assertEqual(gen_indexes.field(block, "maturity"), "canonical")
        self.assertEqual(gen_indexes.field(block, "missing", "default_val"), "default_val")

    def test_first_intent_extraction_and_truncation(self):
        sample_entry = (
            "---\nname: Test Pattern\n---\n"
            "## 1. Name, aliases, and lineage\n"
            "Lineage text here.\n\n"
            "## 2. Problem and context\n"
            "This is the core problem statement that needs to be extracted as intent. "
            "It explains why the pattern exists and when to use it in practice. "
            "Additional sentence to make this summary long enough for truncation testing when exceeding max length limit.\n\n"
            "## 3. Forces\n"
            "Forces text.\n"
        )
        intent = gen_indexes.first_intent(sample_entry)
        self.assertTrue(intent.startswith("This is the core problem statement"))
        self.assertLessEqual(len(intent), 183)  # 180 chars + " ..."

    def test_first_intent_missing_section_2(self):
        sample_entry = "---\nname: Test Pattern\n---\n## 1. Name\nNo section 2 here.\n"
        intent = gen_indexes.first_intent(sample_entry)
        self.assertEqual(intent, "")

    def test_load_planned(self):
        queue_file = self.tmp / "AUTHORING-QUEUE.json"
        queue_data = [
            {"path": "patterns/01-design-patterns-gof/nonexistent-queued-test-pattern.md", "name": "Test Pattern", "reason": "Test reason"},
            {"path": "patterns/01-design-patterns-gof/deferred-item.md", "name": "Deferred", "status": "deferred"},
            {"path": "invalid-path/item.md", "name": "Invalid"},
        ]
        queue_file.write_text(json.dumps(queue_data), encoding="utf-8")

        original_queue = gen_indexes.QUEUE
        gen_indexes.QUEUE = queue_file
        try:
            planned = gen_indexes.load_planned()
            self.assertIn("01-design-patterns-gof", planned)
            self.assertEqual(planned["01-design-patterns-gof"], [("Test Pattern", "Test reason")])
        finally:
            gen_indexes.QUEUE = original_queue

    def test_build_index(self):
        family_dir = self.tmp / "patterns" / "01-design-patterns-gof"
        family_dir.mkdir(parents=True)

        entry1 = family_dir / "strategy.md"
        entry1.write_text(
            "---\n"
            "name: Strategy\n"
            "category: Behavioral\n"
            "maturity: canonical\n"
            "---\n"
            "## 1. Name\nStrategy.\n\n"
            "## 2. Problem and context\nDefine a family of algorithms.\n\n"
            "## 3. Forces\nFlexibility.\n",
            encoding="utf-8",
        )

        planned_items = [("Visitor", "Classic pattern")]
        count = gen_indexes.build(family_dir, planned_items)
        self.assertEqual(count, 1)

        readme = family_dir / "README.md"
        self.assertTrue(readme.exists())
        content = readme.read_text(encoding="utf-8")
        self.assertIn("# Family 01. Design Patterns", content)
        self.assertIn("## Behavioral", content)
        self.assertIn("| [Strategy](strategy.md) | canonical |", content)
        self.assertIn("## Planned", content)
        self.assertIn("- Visitor. Classic pattern", content)

    def test_build_empty_family(self):
        family_dir = self.tmp / "patterns" / "99-empty"
        family_dir.mkdir(parents=True)
        count = gen_indexes.build(family_dir, [])
        self.assertEqual(count, 0)
        self.assertFalse((family_dir / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
