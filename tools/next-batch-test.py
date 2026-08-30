#!/usr/bin/env python3
"""Unit tests for next-batch.py."""

from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "next_batch", ROOT / "tools" / "next-batch.py"
)
next_batch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(next_batch)


class TestNextBatch(unittest.TestCase):
    def setUp(self):
        self.sample_queue = [
            {
                "name": "Active Pattern 1",
                "slug": "active-pattern-1",
                "category": "testing",
                "path": "patterns/14-testing/active-pattern-1.md",
            },
            {
                "name": "Active Pattern 2",
                "slug": "active-pattern-2",
                "category": "testing",
                "path": "patterns/14-testing/active-pattern-2.md",
            },
            {
                "name": "Deferred Pattern",
                "slug": "deferred-pattern",
                "category": "observability",
                "path": "patterns/22-observability/deferred-pattern.md",
                "status": "deferred",
                "reason": "Permanently deferred.",
            },
        ]

    @patch.object(next_batch, "claimed_paths")
    @patch.object(next_batch, "passing")
    @patch.object(next_batch, "QUEUE")
    def test_main_default_filters_deferred(
        self, mock_queue, mock_passing, mock_claims
    ):
        mock_queue.exists.return_value = True
        mock_queue.read_text.return_value = json.dumps(self.sample_queue)
        mock_passing.return_value = set()
        mock_claims.return_value = {}

        with patch("sys.argv", ["next-batch.py", "--size", "5"]):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                rc = next_batch.main()
                self.assertEqual(rc, 0)
                output = json.loads(mock_stdout.getvalue())
                self.assertEqual(len(output), 2)
                paths = [e["path"] for e in output]
                self.assertIn("patterns/14-testing/active-pattern-1.md", paths)
                self.assertIn("patterns/14-testing/active-pattern-2.md", paths)
                self.assertNotIn("patterns/22-observability/deferred-pattern.md", paths)

    @patch.object(next_batch, "claimed_paths")
    @patch.object(next_batch, "passing")
    @patch.object(next_batch, "QUEUE")
    def test_main_status_filters_deferred(
        self, mock_queue, mock_passing, mock_claims
    ):
        mock_queue.exists.return_value = True
        mock_queue.read_text.return_value = json.dumps(self.sample_queue)
        mock_passing.return_value = {"patterns/14-testing/active-pattern-1.md"}
        mock_claims.return_value = {}

        with patch("sys.argv", ["next-batch.py", "--status"]):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                rc = next_batch.main()
                self.assertEqual(rc, 0)
                stdout_text = mock_stdout.getvalue()
                self.assertIn("14-testing", stdout_text)
                self.assertNotIn("22-observability", stdout_text)
                self.assertIn("1 done, 1 remaining, 2 total", stdout_text)

    @patch.object(next_batch, "claimed_paths")
    @patch.object(next_batch, "passing")
    @patch.object(next_batch, "QUEUE")
    def test_main_claimed_filtering(
        self, mock_queue, mock_passing, mock_claims
    ):
        mock_queue.exists.return_value = True
        mock_queue.read_text.return_value = json.dumps(self.sample_queue)
        mock_passing.return_value = set()
        mock_claims.return_value = {"patterns/14-testing/active-pattern-1.md": 99}

        with patch("sys.argv", ["next-batch.py", "--size", "5"]):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                    rc = next_batch.main()
                    self.assertEqual(rc, 0)
                    output = json.loads(mock_stdout.getvalue())
                    self.assertEqual(len(output), 1)
                    self.assertEqual(
                        output[0]["path"], "patterns/14-testing/active-pattern-2.md"
                    )
                    self.assertIn(
                        "skipping 1 claimed by an open PR", mock_stderr.getvalue()
                    )

    @patch.object(next_batch, "QUEUE")
    def test_main_queue_missing(self, mock_queue):
        mock_queue.exists.return_value = False
        with patch("sys.argv", ["next-batch.py"]):
            with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                rc = next_batch.main()
                self.assertEqual(rc, 1)
                self.assertIn("queue missing", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
