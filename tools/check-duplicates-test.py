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
fetch_historical_proposals = check_duplicates.fetch_historical_proposals


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

    def test_parenthetical_qualifiers_normalization(self):
        self.assertEqual(
            normalize_term("Producer-Consumer (Embedded)"), "producerconsumer"
        )
        self.assertEqual(
            normalize_term("Repository Pattern (Mobile Offline-First)"),
            "repository",
        )
        self.assertEqual(
            normalize_term("Model-View-Intent (MVI)"),
            normalize_term("Model-View-Intent"),
        )

    def test_distinct_near_neighbors(self):
        self.assertNotEqual(
            normalize_term("Rate Limiting"), normalize_term("Throttling")
        )
        self.assertNotEqual(
            normalize_term("Circuit Breaker"), normalize_term("Bulkhead")
        )
        self.assertNotEqual(
            normalize_term("Strangler Fig"), normalize_term("Branch by Abstraction")
        )

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
        self.assertAlmostEqual(jaccard_similarity({"a", "b"}, {"a", "c"}), 1.0 / 3.0)

    def test_jaccard_similarity_threshold_pruning(self):
        # 1 vs 10 elements cannot exceed 0.70 threshold (max 1/10 = 0.10)
        s1 = {"a"}
        s2 = {f"item_{i}" for i in range(10)}
        self.assertEqual(jaccard_similarity(s1, s2, threshold=0.70), 0.0)
        # Without threshold constraint, 1 vs 10 evaluates normally
        s1_with_overlap = {"item_0"}
        self.assertAlmostEqual(jaccard_similarity(s1_with_overlap, s2), 1.0 / 10.0)

    def test_analyze_repository(self):
        queue_file = ROOT / "docs" / "AUTHORING-QUEUE.json"
        results = analyze_repository(queue_file)
        self.assertGreater(results["published_count"], 0)
        self.assertGreaterEqual(results["queue_count"], 0)
        self.assertIsInstance(results["collisions"], list)

    def test_deferred_queue_filtering(self):
        import json
        import tempfile

        queue_data = [
            {
                "name": "Virtual List",
                "slug": "virtual-list",
                "path": "patterns/13-frontend-ui/virtual-list-deferred.md",
                "status": "deferred",
                "reason": "Deferred test item",
            },
            {
                "name": "Virtual List",
                "slug": "virtual-list",
                "path": "patterns/13-frontend-ui/virtual-list-active.md",
                "reason": "Active duplicate test item",
            },
        ]

        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tf:
            json.dump(queue_data, tf)
            tf.flush()
            temp_path = Path(tf.name)

        try:
            results = analyze_repository(temp_path)
            self.assertEqual(results["queue_count"], 1)
            collisions = results["collisions"]
            queue_paths = {c["queue_path"] for c in collisions}
            self.assertIn("patterns/13-frontend-ui/virtual-list-active.md", queue_paths)
            self.assertNotIn(
                "patterns/13-frontend-ui/virtual-list-deferred.md", queue_paths
            )
        finally:
            temp_path.unlink(missing_ok=True)

    def test_historical_proposal_detection(self):
        history = fetch_historical_proposals()
        self.assertIsInstance(history, list)
        queue_file = ROOT / "docs" / "AUTHORING-QUEUE.json"
        results = analyze_repository(queue_file)
        self.assertIsInstance(results["collisions"], list)

    def test_historical_proposal_collision_mock(self):
        fake_history = [
            {
                "path": "patterns/24-stream-processing/old-windowing-attempt.md",
                "slug": "windowing",
            }
        ]
        original_fetch = check_duplicates.fetch_historical_proposals
        check_duplicates.fetch_historical_proposals = lambda: fake_history
        import json
        import tempfile

        active_queue = [
            {
                "name": "Windowing",
                "slug": "windowing",
                "path": "patterns/24-stream-processing/windowing.md",
            }
        ]
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tf:
            json.dump(active_queue, tf)
            tf.flush()
            temp_path = Path(tf.name)

        try:
            results = analyze_repository(temp_path)
            historical_collisions = [
                c
                for c in results["collisions"]
                if c.get("type") == "HISTORICAL_PROPOSAL_COLLISION"
            ]
            self.assertGreater(len(historical_collisions), 0)
        finally:
            check_duplicates.fetch_historical_proposals = original_fetch
            temp_path.unlink(missing_ok=True)

    def test_collision_deduplication(self):
        queue_file = ROOT / "docs" / "AUTHORING-QUEUE.json"
        results = analyze_repository(queue_file)
        collisions = results["collisions"]
        seen_keys = set()
        for c in collisions:
            target = c.get("published_path", c.get("historical_path"))
            key = (c["type"], c["queue_path"], target, c["normalized_key"])
            self.assertNotIn(key, seen_keys, "Duplicate collision tuple found in results")
            seen_keys.add(key)

    def test_main_check_and_strict_exit_codes(self):
        import unittest.mock

        with unittest.mock.patch.object(
            sys, "argv", ["check-duplicates.py", "--check"]
        ):
            code_check = check_duplicates.main()
            self.assertEqual(code_check, 0)

        with unittest.mock.patch.object(
            sys, "argv", ["check-duplicates.py", "--strict"]
        ):
            code_strict = check_duplicates.main()
            self.assertEqual(code_strict, 0)

        fake_collisions = {
            "published_count": 1,
            "queue_count": 1,
            "historical_count": 0,
            "collisions": [
                {
                    "type": "QUEUE_VS_PUBLISHED",
                    "queue_path": "patterns/13-frontend-ui/test.md",
                    "published_path": "patterns/13-frontend-ui/virtual-list.md",
                    "matched_term": "virtual-list",
                    "normalized_key": "virtuallist",
                    "queue_name": "Virtual List",
                    "published_name": "Virtual List",
                }
            ],
            "semantic_collisions": [],
        }
        with unittest.mock.patch.object(
            check_duplicates, "analyze_repository", lambda _: fake_collisions
        ):
            with unittest.mock.patch.object(
                sys, "argv", ["check-duplicates.py", "--strict"]
            ):
                code_mock_strict = check_duplicates.main()
                self.assertEqual(code_mock_strict, 1)


if __name__ == "__main__":
    unittest.main()
