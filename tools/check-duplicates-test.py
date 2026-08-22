#!/usr/bin/env python3
"""Unit tests for tools/check-duplicates.py duplicate detection engine."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "check_duplicates", ROOT / "tools" / "check-duplicates.py"
)
check_duplicates = importlib.util.module_from_spec(spec)
sys.modules["check_duplicates"] = check_duplicates
spec.loader.exec_module(check_duplicates)

normalize_term = check_duplicates.normalize_term
tokenize_text = check_duplicates.tokenize_text
jaccard_similarity = check_duplicates.jaccard_similarity
analyze_repository = check_duplicates.analyze_repository


class TestCheckDuplicates(unittest.TestCase):
    def test_normalize_term(self):
        self.assertEqual(normalize_term("Strangler Fig"), "stranglerfig")
        self.assertEqual(
            normalize_term("Strangler Application"), "stranglerapplication"
        )
        self.assertEqual(normalize_term("Pipeline Architecture"), "pipeline")
        self.assertEqual(normalize_term("Pipes and Filters"), "pipesandfilters")
        self.assertEqual(normalize_term("Rate Limiting"), "ratelimiting")
        self.assertEqual(normalize_term("Throttling"), "throttling")

    def test_tokenize_text(self):
        tokens = tokenize_text(
            "The circuit breaker pattern prevents cascading failures in distributed architecture."
        )
        self.assertIn("circuit", tokens)
        self.assertIn("breaker", tokens)
        self.assertIn("prevents", tokens)
        self.assertIn("cascading", tokens)
        self.assertNotIn("the", tokens)
        self.assertNotIn("in", tokens)
        self.assertNotIn("architecture", tokens)

    def test_jaccard_similarity(self):
        self.assertEqual(jaccard_similarity(set(), set()), 0.0)
        self.assertEqual(jaccard_similarity({"a"}, set()), 0.0)
        self.assertEqual(jaccard_similarity(set(), {"b"}), 0.0)
        self.assertEqual(jaccard_similarity({"a", "b"}, {"a", "b"}), 1.0)
        self.assertEqual(jaccard_similarity({"a", "b"}, {"c", "d"}), 0.0)
        self.assertAlmostEqual(
            jaccard_similarity({"a", "b"}, {"a", "c"}), 1.0 / 3.0
        )

    def test_jaccard_similarity_threshold_pruning(self):
        # 1 vs 10 elements cannot exceed 0.70 threshold (max 1/10 = 0.10)
        s1 = {"a"}
        s2 = {f"item_{i}" for i in range(10)}
        self.assertEqual(jaccard_similarity(s1, s2, threshold=0.70), 0.0)
        # Without threshold constraint, 1 vs 10 evaluates normally
        s1_with_overlap = {"item_0"}
        self.assertAlmostEqual(
            jaccard_similarity(s1_with_overlap, s2), 1.0 / 10.0
        )

    def test_analyze_repository(self):
        queue_file = ROOT / "docs" / "AUTHORING-QUEUE.json"
        results = analyze_repository(queue_file)
        self.assertGreater(results["published_count"], 0)
        self.assertGreater(results["queue_count"], 0)
        self.assertIsInstance(results["collisions"], list)


if __name__ == "__main__":
    unittest.main()
