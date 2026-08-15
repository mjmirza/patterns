#!/usr/bin/env python3
"""Regression tests for tools/check-code.py. Stdlib only, no dependency.
Verifies Python code block syntax checking works correctly in-process."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("check_code", TOOLS / "check-code.py")
check_code = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_code)


class CheckPythonTests(unittest.TestCase):
    def test_valid_python_syntax_passes(self):
        valid_src = "def add(a: int, b: int) -> int:\n    return a + b\n"
        with tempfile.TemporaryDirectory() as td:
            code, msg = check_code.check_python(valid_src, Path(td))
            self.assertEqual(code, 0)
            self.assertEqual(msg, "")

    def test_invalid_python_syntax_fails(self):
        invalid_src = "def bad_syntax(a, b\n    return a + b\n"
        with tempfile.TemporaryDirectory() as td:
            code, msg = check_code.check_python(invalid_src, Path(td))
            self.assertEqual(code, 1)
            self.assertIn("SyntaxError", msg)

    def test_complex_valid_python_features(self):
        async_src = (
            "import asyncio\n\n"
            "async def fetch_data(url: str) -> dict:\n"
            "    await asyncio.sleep(0.1)\n"
            "    return {'status': 200}\n"
        )
        with tempfile.TemporaryDirectory() as td:
            code, msg = check_code.check_python(async_src, Path(td))
            self.assertEqual(code, 0)
            self.assertEqual(msg, "")


if __name__ == "__main__":
    unittest.main()
