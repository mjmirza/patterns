#!/usr/bin/env python3
"""Unit tests for tools/check-structure.py.
Verifies structural validation rules for pattern entries."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

# Dynamically import check-structure.py from tools/
spec = importlib.util.spec_from_file_location(
    "check_structure", TOOLS / "check-structure.py"
)
check_structure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_structure)


def generate_valid_pattern() -> str:
    frontmatter = (
        "---\n"
        "name: Test Pattern\n"
        "slug: test-pattern\n"
        "family: 01-design-patterns-gof\n"
        "maturity: canonical\n"
        "verified: true\n"
        "---\n\n"
    )

    sections = [
        "## 1. Name, aliases, and lineage\nTest pattern lineage.",
        "## 2. Problem and context\nProblem context.",
        "## 3. Forces\nForces description.",
        "## 4. Applicability\nWhen to use and non-applicability scenarios.",
        "## 5. Structure\nStructure description.",
        "## 6. Diagram\n```\n+---+ -> +---+\n```",
        "## 7. Dynamics\nDynamics description.",
        "## 8. Implementation variants\nVariants.",
        "## 9. Known production uses\nProduction uses.",
        "## 10. Consequences\nConsequences.",
        "## 11. Failure modes\nFailure modes.",
        "## 12. Trade-off\nTrade-offs.",
        "## 13. Related\nRelated patterns.",
        "## 14. Refactoring path\nRefactoring path.",
        "## 15. Testing\nTesting strategies.",
        "## 16. Observability\nObservability notes.",
        "## 17. Security\nSecurity considerations.",
        "## 18. References\n"
        "1. https://example.com/ref1\n"
        "2. https://example.com/ref2\n"
        "3. https://example.com/ref3\n",
    ]

    code_samples = (
        "```python\ndef py_example():\n    pass\n```\n\n"
        "```typescript\nfunction tsExample(): void {}\n```\n\n"
        "```java\npublic class JavaExample {}\n```\n\n"
    )

    # Add prose body to satisfy min prose words (1200 words)
    prose_filler = "Word " * 1200 + "\n\n"

    return frontmatter + "\n\n".join(sections) + "\n\n" + code_samples + prose_filler


class TestCheckStructure(unittest.TestCase):
    def test_strip_fences(self):
        text = "Prose before\n```python\ncode_line = 1\n```\nProse after"
        stripped = check_structure.strip_fences(text)
        self.assertIn("Prose before", stripped)
        self.assertIn("Prose after", stripped)
        self.assertNotIn("code_line = 1", stripped)

    def test_check_file_valid(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "test-pattern.md"
            file_path.write_text(generate_valid_pattern(), encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertEqual(errors, [])

    def test_check_file_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern().replace("---\n", "", 2)
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(any("missing YAML frontmatter" in e for e in errors))

    def test_check_file_missing_frontmatter_key(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern().replace("verified: true\n", "")
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(
                any("frontmatter missing key 'verified'" in e for e in errors)
            )

    def test_check_file_invalid_maturity(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern().replace(
                "maturity: canonical", "maturity: fake_maturity"
            )
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(any("invalid maturity 'fake_maturity'" in e for e in errors))

    def test_check_file_missing_required_section(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern().replace(
                "## 17. Security", "## 17. Governance"
            )
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(any("missing dimension 'Security'" in e for e in errors))

    def test_check_file_banned_characters(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern() + "\nThis contains an em dash — here."
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(
                any("banned character in prose: em dash" in e for e in errors)
            )

    def test_check_file_triple_dash_separator(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern() + "\n---\nSome prose after triple dash."
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(
                any("triple-dash used as section separator" in e for e in errors)
            )

    def test_check_file_unbalanced_code_fence(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern() + "\n```python\nunclosed code fence"
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(any("unbalanced code fence" in e for e in errors))

    def test_check_file_insufficient_languages(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern().replace("```typescript", "```python")
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(
                any("needs 3 code languages, found" in e for e in errors)
            )

    def test_check_file_insufficient_urls(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern().replace(
                "https://example.com/ref2", "no_url_2"
            ).replace("https://example.com/ref3", "no_url_3")
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(any("needs at least 3 cited URLs" in e for e in errors))

    def test_check_file_missing_non_applicability(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern().replace("non-applicability", "scenarios")
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(any("missing non-applicability list" in e for e in errors))

    def test_check_file_too_short(self):
        with tempfile.TemporaryDirectory() as td:
            file_path = Path(td) / "invalid.md"
            content = generate_valid_pattern().replace("Word " * 1200, "Short prose.")
            file_path.write_text(content, encoding="utf-8")
            errors = check_structure.check_file(file_path)
            self.assertTrue(
                any("too short for master level" in e for e in errors)
            )


if __name__ == "__main__":
    unittest.main()
