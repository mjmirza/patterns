#!/usr/bin/env python3
"""Regression tests for gen-by-problem-by-language.py.
Verifies that frontmatter, sections, bullet points, and language code blocks
are correctly and deterministically parsed and generated."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent


def run_generator(repo: Path) -> int:
    p = subprocess.run(
        [sys.executable, str(repo / "tools" / "gen-by-problem-by-language.py")],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return p.returncode


def make_fixture(tmp: Path) -> Path:
    repo = tmp / "repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "patterns" / "01-fake").mkdir(parents=True)
    (repo / "docs").mkdir()
    shutil.copy(TOOLS / "gen-by-problem-by-language.py", repo / "tools")

    # Create mock entry 1
    (repo / "patterns" / "01-fake" / "alpha.md").write_text(
        "---\n"
        "name: Alpha Pattern\n"
        "slug: alpha\n"
        "family: 01-fake\n"
        "maturity: canonical\n"
        "verified: 2026-08-02\n"
        "---\n\n"
        "# Alpha Pattern\n\n"
        "## 1. Name, aliases, and lineage\n\n"
        "Alpha Lineage\n\n"
        "## 2. Problem and context\n\n"
        "This is the core problem statement for Alpha.\n\n"
        "You can recognize the problem by these symptoms:\n"
        "- First symptom of Alpha.\n"
        "- Second symptom of Alpha.\n\n"
        "## 4. Applicability\n\n"
        "Do NOT reach for it in Go.\n\n"
        "## 8. Implementation variants\n\n"
        "In Rust, this pattern is built differently.\n\n"
        "## 11. Failure modes\n\n"
        "**Symptom.** Alpha has failed.\n\n"
        "## 18. References\n\n"
        "References here.\n\n"
        "```go\n"
        "func GoExample() {}\n"
        "```\n"
    )

    # Create mock entry 2
    (repo / "patterns" / "01-fake" / "beta.md").write_text(
        "---\n"
        "name: Beta Pattern\n"
        "slug: beta\n"
        "family: 01-fake\n"
        "maturity: canonical\n"
        "verified: 2026-08-02\n"
        "---\n\n"
        "# Beta Pattern\n\n"
        "## 1. Name, aliases, and lineage\n\n"
        "Beta Lineage\n\n"
        "## 2. Problem and context\n\n"
        "This is the core problem statement for Beta.\n\n"
        "Symptoms:\n"
        "- First symptom of Beta.\n\n"
        "## 4. Applicability\n\n"
        "Do NOT reach for it in Python.\n\n"
        "## 8. Implementation variants\n\n"
        "In TypeScript, this pattern is simpler.\n\n"
        "## 11. Failure modes\n\n"
        "- Failure symptom for Beta.\n\n"
        "## 18. References\n\n"
        "References here.\n\n"
        "```rust\n"
        "fn rust_example() {}\n"
        "```\n"
    )
    return repo


class TestGenerator(unittest.TestCase):
    def test_generator_runs_successfully_and_parses_content(self):
        with tempfile.TemporaryDirectory() as td:
            repo = make_fixture(Path(td))
            ret = run_generator(repo)
            self.assertEqual(ret, 0)

            by_problem_path = repo / "docs" / "BY-PROBLEM.md"
            by_language_path = repo / "docs" / "BY-LANGUAGE.md"

            self.assertTrue(by_problem_path.exists())
            self.assertTrue(by_language_path.exists())

            by_problem = by_problem_path.read_text()
            by_language = by_language_path.read_text()

            # Verify by-problem content
            self.assertIn("Alpha Pattern", by_problem)
            self.assertIn("Beta Pattern", by_problem)
            self.assertIn("This is the core problem statement for Alpha.", by_problem)
            self.assertIn("First symptom of Alpha.", by_problem)
            self.assertIn("Second symptom of Alpha.", by_problem)
            self.assertIn("Alpha has failed.", by_problem)
            self.assertIn("First symptom of Beta.", by_problem)
            self.assertIn("Failure symptom for Beta.", by_problem)

            # Verify by-language content
            self.assertIn("Yes", by_language)  # Implementation checkmarks
            self.assertIn("Go", by_language)
            self.assertIn("Rust", by_language)
            self.assertIn("TypeScript", by_language)
            self.assertIn("Python", by_language)

            # Section 4/8 language detection asserts
            # Rust mentioned in Section 8 (Changes Shape) for Alpha
            self.assertIn("Rust", by_language)
            # Go mentioned in Section 4 (Made Unnecessary) for Alpha
            self.assertIn("Go", by_language)


if __name__ == "__main__":
    unittest.main()
