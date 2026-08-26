#!/usr/bin/env python3
"""Unit tests for tools/validate-refs.py."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "validate_refs", ROOT / "tools" / "validate-refs.py"
)
validate_refs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_refs)


class TestValidateRefs(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(validate_refs.clean("https://example.com/page."), "https://example.com/page")
        self.assertEqual(validate_refs.clean("https://example.com/page,"), "https://example.com/page")
        self.assertEqual(validate_refs.clean("https://example.com/page;"), "https://example.com/page")
        self.assertEqual(
            validate_refs.clean("https://en.wikipedia.org/wiki/Foo_(bar)"),
            "https://en.wikipedia.org/wiki/Foo_(bar)",
        )
        self.assertEqual(
            validate_refs.clean("https://example.com/page)"),
            "https://example.com/page",
        )

    def test_strip_fences(self):
        text = "Prose before\n```python\nhttps://example.com/code\n```\nProse after"
        stripped = validate_refs.strip_fences(text)
        self.assertIn("Prose before", stripped)
        self.assertIn("Prose after", stripped)
        self.assertNotIn("https://example.com/code", stripped)

    def test_is_cached(self):
        cache = {
            "https://example.com/ok": 200,
            "https://example.com/redirect": 301,
            "https://example.com/accepted": 202,
            "https://dl.acm.org/citation.cfm?id=12345": 403,
            "https://example.com/fail": 404,
        }

        self.assertTrue(validate_refs.is_cached("https://example.com/ok", cache))
        self.assertTrue(validate_refs.is_cached("https://example.com/redirect", cache))
        self.assertTrue(validate_refs.is_cached("https://example.com/accepted", cache))
        self.assertTrue(validate_refs.is_cached("https://dl.acm.org/citation.cfm?id=12345", cache))
        self.assertFalse(validate_refs.is_cached("https://example.com/fail", cache))
        self.assertFalse(validate_refs.is_cached("https://example.com/uncached", cache))

    @patch("urllib.request.urlopen")
    def test_probe_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        url, status = validate_refs.probe("https://example.com", timeout=5)
        self.assertEqual(url, "https://example.com")
        self.assertEqual(status, 200)

    @patch("urllib.request.urlopen")
    def test_probe_http_error_retry_get(self, mock_urlopen):
        import urllib.error

        req_err = urllib.error.HTTPError(
            "https://example.com", 403, "Forbidden", {}, None
        )
        mock_response = MagicMock()
        mock_response.status = 200

        mock_urlopen.side_effect = [req_err, MagicMock(__enter__=MagicMock(return_value=mock_response))]

        url, status = validate_refs.probe("https://example.com", timeout=5)
        self.assertEqual(url, "https://example.com")
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
