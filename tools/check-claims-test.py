#!/usr/bin/env python3
"""Unit tests for check-claims.py."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("check_claims", ROOT / "tools" / "check-claims.py")
check_claims = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_claims)


class TestCheckClaims(unittest.TestCase):
    @patch("subprocess.run")
    def test_added_paths(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="A\tpatterns/01-gof/strategy.md\n"
                   "M\tpatterns/01-gof/observer.md\n"
                   "A\tdocs/README.md\n"
                   "A\tpatterns/02-code-smells/god-object.md\n"
        )
        paths = check_claims.added_paths()
        self.assertEqual(
            paths,
            ["patterns/01-gof/strategy.md", "patterns/02-code-smells/god-object.md"],
        )

    @patch("subprocess.run")
    def test_published_on_main_true(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(check_claims.published_on_main("patterns/01-gof/strategy.md"))

    @patch("subprocess.run")
    def test_published_on_main_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(check_claims.published_on_main("patterns/01-gof/new-pattern.md"))

    @patch("subprocess.run")
    def test_sibling_pr_paths(self, mock_run):
        gh_output = json.dumps([
            {
                "number": 10,
                "files": [
                    {"path": "patterns/01-gof/singleton.md"},
                    {"path": "README.md"},
                ],
            },
            {
                "number": 12,
                "files": [
                    {"path": "patterns/02-code-smells/feature-envy.md"},
                ],
            },
        ])
        mock_run.return_value = MagicMock(stdout=gh_output)
        siblings = check_claims.sibling_pr_paths(this_pr="10")
        self.assertNotIn("patterns/01-gof/singleton.md", siblings)
        self.assertEqual(siblings.get("patterns/02-code-smells/feature-envy.md"), 12)

    @patch("subprocess.run")
    def test_sibling_pr_paths_exception(self, mock_run):
        mock_run.side_effect = Exception("gh command failed")
        siblings = check_claims.sibling_pr_paths(this_pr="10")
        self.assertEqual(siblings, {})

    @patch.object(check_claims, "added_paths")
    def test_main_no_added_paths(self, mock_added):
        mock_added.return_value = []
        self.assertEqual(check_claims.main(), 0)

    @patch.object(check_claims, "sibling_pr_paths")
    @patch.object(check_claims, "published_on_main")
    @patch.object(check_claims, "added_paths")
    def test_main_with_collisions(self, mock_added, mock_pub, mock_siblings):
        mock_added.return_value = ["patterns/01-gof/strategy.md", "patterns/02-code-smells/god-object.md"]
        mock_pub.side_effect = lambda path: path == "patterns/01-gof/strategy.md"
        mock_siblings.return_value = {"patterns/02-code-smells/god-object.md": 42}

        rc = check_claims.main()
        self.assertEqual(rc, 1)

    @patch.object(check_claims, "sibling_pr_paths")
    @patch.object(check_claims, "published_on_main")
    @patch.object(check_claims, "added_paths")
    def test_main_clean(self, mock_added, mock_pub, mock_siblings):
        mock_added.return_value = ["patterns/01-gof/new-pattern.md"]
        mock_pub.return_value = False
        mock_siblings.return_value = {}

        rc = check_claims.main()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
