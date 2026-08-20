#!/usr/bin/env python3
"""Unit tests for check-code.py."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("check_code", ROOT / "tools" / "check-code.py")
check_code = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_code)


class TestCheckCode(unittest.TestCase):
    def test_check_python_valid(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out = check_code.check_python("x = 1 + 2\n", Path(td))
            self.assertEqual(rc, 0)

    def test_check_python_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out = check_code.check_python("def invalid_syntax(\n", Path(td))
            self.assertNotEqual(rc, 0)

    def test_check_ts_valid(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out = check_code.check_ts("const x: number = 42;\n", Path(td))
            self.assertEqual(rc, 0)

    def test_check_ts_type_error(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out = check_code.check_ts("const x: number = 'hello';\n", Path(td))
            self.assertNotEqual(rc, 0)
            self.assertIn("Type 'string' is not assignable to type 'number'", out)

    def test_check_ts_batch_cumulative(self):
        tasks = [
            (0, "interface Person { name: string; }"),
            (1, "const p: Person = { name: 'Alice' };"),  # Fails standalone due to missing Person
            (2, "interface Person { name: string; }\n\nconst p: Person = { name: 'Alice' };"),  # Cumulative succeeds
        ]
        res = check_code.check_ts_batch(tasks)
        self.assertEqual(res[0][0], 0)
        self.assertNotEqual(res[1][0], 0)
        self.assertEqual(res[2][0], 0)

    def test_main_multi_file_multi_snippet_ts(self):
        """Regression test for multi-file multi-snippet task ID mapping."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            patterns_dir = td_path / "patterns"
            patterns_dir.mkdir()

            f1 = patterns_dir / "01_test.md"
            f1.write_text(
                "```ts\ninterface A { a: number; }\n```\n"
                "```ts\nconst obj: A = { a: 1 };\n```\n",
                encoding="utf-8",
            )

            f2 = patterns_dir / "02_test.md"
            f2.write_text(
                "```ts\nconst x: string = 'hello';\n```\n"
                "```ts\nconst y: number = 123;\n```\n",
                encoding="utf-8",
            )

            old_patterns = check_code.PATTERNS
            old_root = check_code.ROOT
            try:
                check_code.PATTERNS = patterns_dir
                check_code.ROOT = td_path
                sys_argv_backup = list(sys.argv)
                sys.argv = ["check-code.py", "--strict"]
                rc = check_code.main()
                self.assertEqual(rc, 0)
            finally:
                check_code.PATTERNS = old_patterns
                check_code.ROOT = old_root
                sys.argv = sys_argv_backup


if __name__ == "__main__":
    unittest.main()
