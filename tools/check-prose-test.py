#!/usr/bin/env python3
"""Unit tests for tools/check-prose.py prose validator."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

spec = importlib.util.spec_from_file_location(
    "check_prose", TOOLS / "check-prose.py"
)
check_prose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_prose)


class TestCheckProse(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.tmp = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_prose_lines_frontmatter_and_fences(self):
        content = (
            "---\n"
            "name: test-pattern\n"
            "---\n"
            "Line 4: This is prose.\n"
            "```python\n"
            "def foo():\n"
            "    return 'leverage'\n"
            "```\n"
            "Line 9: More prose.\n"
        )
        lines = check_prose.prose_lines(content)
        self.assertEqual(
            lines,
            [
                (4, "Line 4: This is prose."),
                (9, "Line 9: More prose."),
            ],
        )

    def test_strip_inline_code(self):
        line = "Use `leverage` in code, but leverage in prose."
        stripped = check_prose.strip_inline_code(line)
        self.assertEqual(stripped, "Use   in code, but leverage in prose.")

    def test_check_clean_file(self):
        test_file = self.tmp / "clean.md"
        test_file.write_text(
            "---\n"
            "name: clean\n"
            "---\n"
            "## 1. Context\n"
            "This pattern provides a straight forward solution to a clear problem.\n"
        )
        errs = check_prose.check(test_file)
        self.assertEqual(errs, [])

    def test_check_banned_words_and_phrases(self):
        test_file = self.tmp / "slop.md"
        test_file.write_text(
            "We leverage this robust tool to dive into the problem.\n"
        )
        errs = check_prose.check(test_file)
        self.assertTrue(any("banned word 'leverage'" in e for e in errs))
        self.assertTrue(any("banned word 'robust'" in e for e in errs))
        self.assertTrue(any("banned phrase 'dive into'" in e for e in errs))

    def test_check_proper_noun_collision(self):
        test_file = self.tmp / "proper_noun.md"
        test_file.write_text(
            "According to Foster, we should foster clean architecture.\n"
        )
        errs = check_prose.check(test_file)
        # Capitalized 'Foster' is exempt, but lowercase 'foster' triggers an error.
        foster_errs = [e for e in errs if "banned word 'foster'" in e]
        self.assertEqual(len(foster_errs), 1)

    def test_check_banned_characters_and_emojis(self):
        test_file = self.tmp / "chars.md"
        test_file.write_text(
            "Here is an em dash—and an en dash–and ellipsis… 😀\n"
        )
        errs = check_prose.check(test_file)
        self.assertTrue(any("em dash" in e for e in errs))
        self.assertTrue(any("en dash" in e for e in errs))
        self.assertTrue(any("ellipsis character" in e for e in errs))
        self.assertTrue(any("emoji" in e for e in errs))

    def test_check_triple_dash_separator(self):
        test_file = self.tmp / "separator.md"
        test_file.write_text(
            "Section 1\n\n---\n\nSection 2\n"
        )
        errs = check_prose.check(test_file)
        self.assertTrue(any("triple-dash used as separator" in e for e in errs))

    def test_collect(self):
        files = check_prose.collect()
        self.assertIsInstance(files, list)
        self.assertGreater(len(files), 0)
        self.assertTrue(all(f.suffix == ".md" for f in files))


if __name__ == "__main__":
    unittest.main()
