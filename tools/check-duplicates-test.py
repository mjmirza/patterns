#!/usr/bin/env python3
"""Unit tests for tools/check-duplicates.py duplicate detection engine."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("check_duplicates", ROOT / "tools" / "check-duplicates.py")
check_duplicates = importlib.util.module_from_spec(spec)
sys.modules["check_duplicates"] = check_duplicates
spec.loader.exec_module(check_duplicates)

normalize_term = check_duplicates.normalize_term
tokenize_text = check_duplicates.tokenize_text
analyze_repository = check_duplicates.analyze_repository


class TestCheckDuplicates(unittest.TestCase):

    def test_normalize_term(self):
        self.assertEqual(normalize_term("Strangler Fig"), "stranglerfig")
        self.assertEqual(normalize_term("Strangler Application"), "stranglerapplication")
        self.assertEqual(normalize_term("Pipeline Architecture"), "pipeline")
        self.assertEqual(normalize_term("Pipes and Filters"), "pipesandfilters")
        self.assertEqual(normalize_term("Rate Limiting"), "ratelimiting")
        self.assertEqual(normalize_term("Throttling"), "throttling")

    def test_tokenize_text(self):
        tokens = tokenize_text("The circuit breaker pattern prevents cascading failures in distributed architecture.")
        self.assertIn("circuit", tokens)
        self.assertIn("breaker", tokens)
        self.assertIn("prevents", tokens)
        self.assertIn("cascading", tokens)
        self.assertNotIn("the", tokens)
        self.assertNotIn("in", tokens)
        self.assertNotIn("architecture", tokens)

    def test_analyze_repository(self):
        queue_file = ROOT / "docs" / "AUTHORING-QUEUE.json"
        results = analyze_repository(queue_file)
        self.assertGreater(results["published_count"], 0)
        self.assertGreater(results["queue_count"], 0)
        self.assertIsInstance(results["collisions"], list)


if __name__ == "__main__":
    unittest.main()
