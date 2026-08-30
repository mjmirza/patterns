#!/usr/bin/env python3
"""Unit tests for tools/validate-refs.py"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import importlib.util
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("validate_refs", TOOLS_DIR / "validate-refs.py")
validate_refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_refs)


class TestValidateRefs(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(validate_refs.clean("https://example.com/foo."), "https://example.com/foo")
        self.assertEqual(validate_refs.clean("https://example.com/foo,;:!?"), "https://example.com/foo")
        self.assertEqual(validate_refs.clean("https://example.com/foo)"), "https://example.com/foo")
        self.assertEqual(validate_refs.clean("https://example.com/foo(bar)"), "https://example.com/foo(bar)")

    def test_strip_fences(self):
        text = "line1\n```py\nhttps://example.com\n```\nline2"
        stripped = validate_refs.strip_fences(text)
        self.assertIn("line1", stripped)
        self.assertIn("line2", stripped)
        self.assertNotIn("https://example.com", stripped)

    def test_is_cached(self):
        cache = {
            "https://example.com/ok": 200,
            "https://example.com/accepted": 202,
            "https://example.com/moved": 301,
            "https://dev.mysql.com/doc/refman": "403 then HTTPError",
            "https://example.com/bad": 404,
        }
        self.assertTrue(validate_refs.is_cached("https://example.com/ok", cache))
        self.assertTrue(validate_refs.is_cached("https://example.com/accepted", cache))
        self.assertTrue(validate_refs.is_cached("https://example.com/moved", cache))
        self.assertTrue(validate_refs.is_cached("https://dev.mysql.com/doc/refman", cache))
        self.assertFalse(validate_refs.is_cached("https://example.com/bad", cache))
        self.assertFalse(validate_refs.is_cached("https://example.com/uncached", cache))

    def test_probe_success(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response):
            url, status = validate_refs.probe("https://example.com", timeout=5)
            self.assertEqual(url, "https://example.com")
            self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
