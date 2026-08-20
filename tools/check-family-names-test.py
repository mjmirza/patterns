#!/usr/bin/env python3
"""Regression and unit tests for check-family-names.py.
Uses standard library unittest and temporary directories to verify table parsing and family directory validation."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

spec = importlib.util.spec_from_file_location(
    "check_family_names", TOOLS / "check-family-names.py"
)
check_family_names = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_family_names)


class TestCheckFamilyNames(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.tmp = Path(self.td.name)
        self.readme = self.tmp / "README.md"
        self.patterns = self.tmp / "patterns"
        self.patterns.mkdir()

    def tearDown(self):
        self.td.cleanup()

    def test_parse_table_slugs_valid(self):
        self.readme.write_text(
            "# Title\n\n"
            "## The families\n\n"
            "| # | Family |\n"
            "|---|---|\n"
            "| 01 | [Design Patterns (GoF)](patterns/01-gof/) |\n"
            "| 02 | [Code Smells](patterns/02-code-smells/) |\n\n"
            "## How to read it\n"
        )
        slugs, err = check_family_names.parse_table_slugs(self.readme)
        self.assertIsNone(err)
        self.assertEqual(
            slugs,
            {"01-gof": "Design Patterns (GoF)", "02-code-smells": "Code Smells"},
        )

    def test_parse_table_slugs_missing_header(self):
        self.readme.write_text("# Title\n\nNo table here\n")
        slugs, err = check_family_names.parse_table_slugs(self.readme)
        self.assertIn("section not found", err)
        self.assertEqual(slugs, {})

    def test_parse_table_slugs_empty_table(self):
        self.readme.write_text(
            "## The families\n\n| # | Family |\n|---|---|\n\n## Next\n"
        )
        slugs, err = check_family_names.parse_table_slugs(self.readme)
        self.assertIn("no family rows parsed", err)
        self.assertEqual(slugs, {})

    def test_parse_table_slugs_nonexistent_file(self):
        nonexistent = self.tmp / "NONEXISTENT.md"
        slugs, err = check_family_names.parse_table_slugs(nonexistent)
        self.assertIn("file not found", err)
        self.assertEqual(slugs, {})

    def test_verify_family_names_clean_run(self):
        self.readme.write_text(
            "## The families\n\n"
            "| # | Family |\n"
            "|---|---|\n"
            "| 01 | [GoF](patterns/01-gof/) |\n"
            "| 02 | [Smells](patterns/02-code-smells/) |\n\n"
            "## Next\n"
        )
        (self.patterns / "01-gof").mkdir()
        (self.patterns / "02-code-smells").mkdir()

        code, lines = check_family_names.verify_family_names(self.patterns, self.readme)
        self.assertEqual(code, 0)
        self.assertEqual(
            lines, ["2 family folder(s) on disk, all match README.md families table"]
        )

    def test_verify_family_names_unlisted_directory(self):
        self.readme.write_text(
            "## The families\n\n"
            "| # | Family |\n"
            "|---|---|\n"
            "| 01 | [GoF](patterns/01-gof/) |\n\n"
            "## Next\n"
        )
        (self.patterns / "01-gof").mkdir()
        (self.patterns / "99-unlisted").mkdir()

        code, lines = check_family_names.verify_family_names(self.patterns, self.readme)
        self.assertEqual(code, 1)
        output = "\n".join(lines)
        self.assertIn(
            "patterns/99-unlisted/ exists on disk but is NOT declared", output
        )

    def test_verify_family_names_missing_patterns_dir(self):
        self.readme.write_text(
            "## The families\n\n| 01 | [GoF](patterns/01-gof/) |\n\n## Next\n"
        )
        nonexistent_patterns = self.tmp / "nonexistent_patterns"

        code, lines = check_family_names.verify_family_names(
            nonexistent_patterns, self.readme
        )
        self.assertEqual(code, 1)
        self.assertIn("patterns directory not found", lines[0])


if __name__ == "__main__":
    unittest.main()
