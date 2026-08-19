#!/usr/bin/env python3
"""Regression tests for next-batch.py. Stdlib only, no external dependencies.
Verifies passing entry extraction, open PR claim detection, and queue batching."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent

# Dynamically import next-batch.py
spec = importlib.util.spec_from_file_location("next_batch", TOOLS / "next-batch.py")
next_batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(next_batch)


class TestPassing(unittest.TestCase):
    @patch("subprocess.run")
    def test_passing_extracts_pass_lines(self, mock_run):
        mock_run.return_value.stdout = (
            "PASS patterns/01-gof/factory-method.md\n"
            "FAIL patterns/01-gof/singleton.md\n"
            "PASS patterns/02-code-smells/long-method.md\n"
        )
        passed = next_batch.passing()
        self.assertEqual(
            passed,
            {
                "patterns/01-gof/factory-method.md",
                "patterns/02-code-smells/long-method.md",
            },
        )

    @patch("subprocess.run", side_effect=Exception("error"))
    def test_passing_handles_subprocess_error(self, mock_run):
        self.assertEqual(next_batch.passing(), set())


class TestClaimedPaths(unittest.TestCase):
    @patch("subprocess.run")
    def test_claimed_paths_single_query_parse(self, mock_run):
        mock_payload = [
            {
                "number": 101,
                "files": [
                    {"path": "patterns/01-gof/builder.md"},
                    {"path": "docs/README.md"},
                ],
            },
            {
                "number": 102,
                "files": [
                    {"path": "patterns/02-code-smells/god-class.md"},
                ],
            },
        ]
        mock_run.return_value.stdout = json.dumps(mock_payload)
        claims = next_batch.claimed_paths()
        self.assertEqual(claims["patterns/01-gof/builder.md"], 101)
        self.assertEqual(claims["patterns/02-code-smells/god-class.md"], 102)
        self.assertNotIn("docs/README.md", claims)

    @patch("subprocess.run", side_effect=Exception("gh not found"))
    def test_claimed_paths_handles_failure(self, mock_run):
        self.assertEqual(next_batch.claimed_paths(), {})


class TestMain(unittest.TestCase):
    def test_queue_filtering(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            docs_dir = tmp / "docs"
            docs_dir.mkdir()

            queue = [
                {"name": "Done Item", "path": "patterns/01-gof/done.md"},
                {"name": "Claimed Item", "path": "patterns/01-gof/claimed.md"},
                {"name": "Todo Item 1", "path": "patterns/01-gof/todo1.md"},
                {"name": "Todo Item 2", "path": "patterns/02-smell/todo2.md"},
            ]
            (docs_dir / "AUTHORING-QUEUE.json").write_text(json.dumps(queue))

            orig_queue = next_batch.QUEUE
            try:
                next_batch.QUEUE = docs_dir / "AUTHORING-QUEUE.json"
                with patch.object(
                    next_batch, "passing", return_value={"patterns/01-gof/done.md"}
                ), patch.object(
                    next_batch,
                    "claimed_paths",
                    return_value={"patterns/01-gof/claimed.md": 42},
                ):
                    # Filter for size=2
                    with patch("argparse.ArgumentParser.parse_args") as mock_args:
                        mock_args.return_value = MagicMock(
                            size=2, family=None, status=False
                        )
                        with patch("sys.stdout.write") as mock_write:
                            ret = next_batch.main()
                            self.assertEqual(ret, 0)
            finally:
                next_batch.QUEUE = orig_queue


if __name__ == "__main__":
    unittest.main()
