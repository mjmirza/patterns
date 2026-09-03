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


class StaleCountTest(unittest.TestCase):
    def test_stale_count_no_git_directory(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            orig_root = gen_catalogue_status.ROOT
            try:
                gen_catalogue_status.ROOT = tmp_path
                count = gen_catalogue_status.stale_count({"patterns/01-fake/alpha.md"})
                self.assertEqual(count, 0)
            finally:
                gen_catalogue_status.ROOT = orig_root

    @patch("subprocess.run")
    def test_stale_count_calculation(self, mock_run):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).timestamp()
        fresh_ts = int(now - (10 * 86400))
        stale_ts = int(now - (200 * 86400))

        mock_stdout = (
            f"TS:{fresh_ts}\npatterns/01-fake/fresh.md\n"
            f"TS:{stale_ts}\npatterns/01-fake/stale.md\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_stdout)

        published = {"patterns/01-fake/fresh.md", "patterns/01-fake/stale.md"}
        count = gen_catalogue_status.stale_count(published)
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
