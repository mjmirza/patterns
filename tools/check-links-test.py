#!/usr/bin/env python3
"""Unit tests for check-links.py link validator tool."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

# Load check-links.py module dynamically since file contains a hyphen
TOOLS_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "check_links", TOOLS_DIR / "check-links.py"
)
check_links_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_links_mod)


class TestCheckLinks(unittest.TestCase):
    def test_extract_links_from_file_prose_and_code_blocks(self):
        content = """# Test Document

Here is a valid link to [README](../README.md).
Here is an external link to [Google](https://google.com).
Here is an anchor link to [#section](#section).

```python
# In code block
a = [1](2)
x = func(arg1, arg2)
```

And another link to [Progress](../../docs/PROGRESS.md#summary).
"""
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            links = check_links_mod.extract_links_from_file(tmp_path)
            targets = [link[2] for link in links]
            self.assertIn("../README.md", targets)
            self.assertIn("../../docs/PROGRESS.md#summary", targets)
            self.assertNotIn("https://google.com", targets)
            self.assertNotIn("#section", targets)
            self.assertNotIn("2", targets)
        finally:
            tmp_path.unlink()

    def test_check_links_detects_broken(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            valid_file = root / "exists.md"
            valid_file.write_text("# Exists", encoding="utf-8")

            source_file = root / "source.md"
            source_file.write_text(
                "Link 1: [Valid](exists.md)\nLink 2: [Broken](missing.md)\n",
                encoding="utf-8",
            )

            broken = check_links_mod.check_links(root)
            self.assertEqual(len(broken), 1)
            self.assertEqual(broken[0]["target"], "missing.md")
            self.assertEqual(broken[0]["source"], "source.md")


if __name__ == "__main__":
    unittest.main()
