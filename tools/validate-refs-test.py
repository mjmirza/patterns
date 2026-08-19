#!/usr/bin/env python3
"""Regression tests for validate-refs.py. Stdlib only, no external dependencies.
Verifies URL cleaning, fence stripping, cache lookup filtering, and citation collection."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent

# Dynamically import validate-refs.py
spec = importlib.util.spec_from_file_location("validate_refs", TOOLS / "validate-refs.py")
validate_refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_refs)


class TestClean(unittest.TestCase):
    def test_strip_trailing_punctuation(self):
        self.assertEqual(validate_refs.clean("https://example.com/foo."), "https://example.com/foo")
        self.assertEqual(validate_refs.clean("https://example.com/bar,"), "https://example.com/bar")
        self.assertEqual(validate_refs.clean("https://example.com/baz;"), "https://example.com/baz")
        self.assertEqual(validate_refs.clean("https://example.com/qux!"), "https://example.com/qux")

    def test_unmatched_closing_parenthesis(self):
        # Markdown link format: [text](https://example.com/path)
        self.assertEqual(validate_refs.clean("https://example.com/path)"), "https://example.com/path")
        # Valid URL containing balanced parenthesis
        self.assertEqual(
            validate_refs.clean("https://en.wikipedia.org/wiki/Pattern_(architecture)"),
            "https://en.wikipedia.org/wiki/Pattern_(architecture)",
        )


class TestStripFences(unittest.TestCase):
    def test_fenced_code_blocks_removed(self):
        text = (
            "Here is prose with https://example.com/prose\n"
            "```python\n"
            "print('https://example.com/code')\n"
            "```\n"
            "More prose with https://example.com/prose2\n"
        )
        stripped = validate_refs.strip_fences(text)
        self.assertIn("https://example.com/prose", stripped)
        self.assertIn("https://example.com/prose2", stripped)
        self.assertNotIn("https://example.com/code", stripped)


class TestIsCached(unittest.TestCase):
    def test_standard_http_statuses(self):
        cache = {
            "https://example.com/200": 200,
            "https://example.com/301": 301,
            "https://example.com/302": 302,
        }
        self.assertTrue(validate_refs.is_cached("https://example.com/200", cache))
        self.assertTrue(validate_refs.is_cached("https://example.com/301", cache))
        self.assertTrue(validate_refs.is_cached("https://example.com/302", cache))

    def test_valid_nonstandard_statuses(self):
        cache = {
            "https://example.com/202": 202,
            "https://example.com/204": 204,
            "https://example.com/303": 303,
            "https://example.com/307": 307,
            "https://example.com/308": 308,
        }
        for url in cache:
            self.assertTrue(validate_refs.is_cached(url, cache))

    def test_allow_unreachable_hosts(self):
        cache = {
            "https://ieeexplore.ieee.org/document/12345": "403 then HTTPError",
            "https://martinfowler.com/articles/enterprise.html": "403 then HTTPError",
        }
        self.assertTrue(
            validate_refs.is_cached("https://ieeexplore.ieee.org/document/12345", cache)
        )
        self.assertTrue(
            validate_refs.is_cached("https://martinfowler.com/articles/enterprise.html", cache)
        )

    def test_uncached_and_failed_urls(self):
        cache = {
            "https://example.com/404": 404,
            "https://example.com/500": 500,
        }
        self.assertFalse(validate_refs.is_cached("https://example.com/404", cache))
        self.assertFalse(validate_refs.is_cached("https://example.com/500", cache))
        self.assertFalse(validate_refs.is_cached("https://example.com/missing", cache))


class TestCollect(unittest.TestCase):
    def test_collect_finds_prose_urls_only(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            patterns_dir = tmp / "patterns" / "01-test"
            patterns_dir.mkdir(parents=True)

            sample = (
                "# Sample Pattern\n\n"
                "See https://example.com/doc1 for details.\n\n"
                "```python\n"
                "# Ignore https://example.com/code_url\n"
                "```\n\n"
                "Further reading: [Link](https://example.com/doc2).\n"
            )
            (patterns_dir / "sample.md").write_text(sample, encoding="utf-8")

            # Patch ROOT and PATTERNS in validate_refs module
            orig_root, orig_patterns = validate_refs.ROOT, validate_refs.PATTERNS
            try:
                validate_refs.ROOT = tmp
                validate_refs.PATTERNS = tmp / "patterns"
                collected = validate_refs.collect()

                self.assertIn("https://example.com/doc1", collected)
                self.assertIn("https://example.com/doc2", collected)
                self.assertNotIn("https://example.com/code_url", collected)
            finally:
                validate_refs.ROOT = orig_root
                validate_refs.PATTERNS = orig_patterns


if __name__ == "__main__":
    unittest.main()
