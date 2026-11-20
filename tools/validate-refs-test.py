#!/usr/bin/env python3
"""Unit tests for tools/validate-refs.py"""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

    def test_wayback_prefix_timestamp_is_rejected(self):
        short = "https://web.archive.org/web/2/https://example.com/page"
        self.assertIn("14 digits", validate_refs.wayback_timestamp_error(short))
        wildcard = "https://web.archive.org/web/*/https://example.com/page"
        self.assertIn("14 digits", validate_refs.wayback_timestamp_error(wildcard))

    def test_wayback_pinned_capture_is_accepted(self):
        pinned = (
            "https://web.archive.org/web/20221101064556/"
            "https://karandhillon95.medium.com/the-morning-after-syndrome-4e49096156ed"
        )
        self.assertIsNone(validate_refs.wayback_timestamp_error(pinned))
        flagged = "https://web.archive.org/web/20221101064556id_/https://example.com/a"
        self.assertIsNone(validate_refs.wayback_timestamp_error(flagged))

    def test_wayback_impossible_calendar_time_is_rejected(self):
        bad = "https://web.archive.org/web/20221131064556/https://example.com/a"
        self.assertIn("calendar time", validate_refs.wayback_timestamp_error(bad))

    def test_archive_catalogue_record_is_not_a_replay_url(self):
        record = "https://archive.org/details/refactoringimpro0000fowl"
        self.assertIsNone(validate_refs.wayback_timestamp_error(record))

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
