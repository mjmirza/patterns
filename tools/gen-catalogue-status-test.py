#!/usr/bin/env python3
"""Regression tests for gen-catalogue-status.py. Stdlib only, no dependency.
Proves the double-count bug (queue entries already published still counted
as planned) stays fixed."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent

SPEC = importlib.util.spec_from_file_location(
    "gen_catalogue_status", TOOLS / "gen-catalogue-status.py"
)
gen_catalogue_status = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen_catalogue_status)


def run_generator(repo: Path) -> dict:
    p = subprocess.run(
        [sys.executable, str(repo / "tools" / "gen-catalogue-status.py")],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    return json.loads((repo / "dist" / "catalogue-status.json").read_text())


def make_fixture(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "patterns" / "01-fake").mkdir(parents=True)
    (repo / "docs").mkdir()
    shutil.copy(TOOLS / "gen-catalogue-status.py", repo / "tools")
    (repo / "patterns" / "01-fake" / "alpha.md").write_text(
        "---\nname: Alpha\nmaturity: canonical\n---\n\n# Alpha\n"
    )
    queue = [
        {"name": "Alpha", "slug": "alpha", "path": "patterns/01-fake/alpha.md"},
        {"name": "Beta", "slug": "beta", "path": "patterns/01-fake/beta.md"},
    ]
    (repo / "docs" / "AUTHORING-QUEUE.json").write_text(json.dumps(queue))
    (repo / "README.md").write_text(
        "![Families](https://img.shields.io/badge/families-1-informational)\n"
        "![Entries](https://img.shields.io/badge/entries-x-yellow)\n\n"
        "## The families\n\n| # | Family |\n|---|---|\n\nFamily 04 filler\n"
    )
    return repo


class DoubleCountRegression(unittest.TestCase):
    def test_published_entry_not_double_counted_as_planned(self):
        with tempfile.TemporaryDirectory() as td:
            repo = make_fixture(Path(td))
            status = run_generator(repo)
            row = next(r for r in status["rows"] if r["family"] == "01-fake")
            self.assertEqual(row["published"], 1)
            self.assertEqual(row["planned"], 1)
            self.assertEqual(row["target"], 2)

    def test_target_never_double_counts_published_total(self):
        with tempfile.TemporaryDirectory() as td:
            repo = make_fixture(Path(td))
            status = run_generator(repo)
            self.assertEqual(status["published_total"], 1)
            self.assertEqual(status["target_total"], 2)


class StaleCountTests(unittest.TestCase):
    def test_stale_count_empty_paths(self):
        self.assertEqual(gen_catalogue_status.stale_count(set()), 0)

    @patch("subprocess.run")
    def test_stale_count_git_log_parsing(self, mock_run):
        now = datetime.now(timezone.utc).timestamp()
        old_ts = int(now - (200 * 86400))
        recent_ts = int(now - (10 * 86400))

        mock_output = (
            f"COMMIT {recent_ts}\n"
            f"patterns/01-fake/recent.md\n"
            f"COMMIT {old_ts}\n"
            f"patterns/01-fake/old.md\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)

        with patch.object(gen_catalogue_status, "ROOT", Path("/tmp")):
            with patch.object(Path, "exists", return_value=True):
                paths = {"patterns/01-fake/recent.md", "patterns/01-fake/old.md"}
                stale = gen_catalogue_status.stale_count(paths)
                self.assertEqual(stale, 1)


if __name__ == "__main__":
    unittest.main()
