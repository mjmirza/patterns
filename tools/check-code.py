#!/usr/bin/env python3
"""Compiles or syntax-checks every fenced code sample in every entry.
A sample that does not compile is a defect. Missing toolchains are skipped, never faked."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"

FENCE = re.compile(r"^```([a-zA-Z][a-zA-Z0-9+#]*)\s*$(.*?)^```\s*$", re.M | re.S)

ALIASES = {
    "ts": "typescript",
    "js": "javascript",
    "py": "python",
    "rs": "rust",
    "kt": "kotlin",
    "cs": "csharp",
    "c++": "cpp",
}

JDK_BIN = "/opt/homebrew/opt/openjdk/bin"


def tool(name: str) -> str | None:
    # macOS ships /usr/bin/javac as a stub that errors when no JDK is present,
    # so a real toolchain directory must win over whatever is first on PATH.
    for prefix in (JDK_BIN, "/opt/homebrew/bin", "/usr/local/bin"):
        candidate = Path(prefix) / name
        if candidate.exists():
            return str(candidate)
    return shutil.which(name)


def run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, (p.stderr or p.stdout)[:1500]
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except Exception as e:
        return 125, f"{type(e).__name__}: {e}"


def public_class(src: str) -> str | None:
    m = re.search(
        r"public\s+(?:final\s+|abstract\s+)?(?:class|interface|enum|record)\s+(\w+)",
        src,
    )
    return m.group(1) if m else None


def check_python(src: str, d: Path) -> tuple[int, str]:
    f = d / "s.py"
    try:
        compile(src, str(f), "exec")
        return 0, ""
    except Exception as e:
        return 1, f"{type(e).__name__}: {e}"


def check_java(src: str, d: Path) -> tuple[int, str]:
    javac = tool("javac")
    if not javac:
        return -1, "javac not available"
    name = public_class(src) or "Main"
    f = d / f"{name}.java"
    f.write_text(src)
    return run([javac, "-nowarn", "-d", str(d), str(f)], d)


def check_rust(src: str, d: Path) -> tuple[int, str]:
    rustc = tool("rustc")
    if not rustc:
        return -1, "rustc not available"
    body = src if re.search(r"\bfn\s+main\s*\(", src) else src + "\nfn main() {}\n"
    f = d / "s.rs"
    f.write_text(body)
    return run(
        [
            rustc,
            "--edition",
            "2021",
            "--crate-type",
            "bin",
            "--emit",
            "metadata",
            "-o",
            str(d / "out"),
            str(f),
        ],
        d,
    )


def check_go(src: str, d: Path) -> tuple[int, str]:
    go = tool("go")
    if not go:
        return -1, "go not available"
    body = src if re.search(r"^package\s+\w+", src, re.M) else "package main\n" + src
    f = d / "s.go"
    f.write_text(body)
    return run([go, "vet", str(f)], d)


_TS_PROJECT: Path | None = None


def ts_project() -> Path | None:
    # A shared node_modules resolves @types/node; a fresh npx cache per file does not.
    global _TS_PROJECT
    if _TS_PROJECT is not None:
        return _TS_PROJECT if (_TS_PROJECT / "node_modules/.bin/tsc").exists() else None
    npm = tool("npm")
    if not npm:
        _TS_PROJECT = Path("/nonexistent")
        return None
    proj = Path(tempfile.mkdtemp(prefix="patterns-ts-"))
    (proj / "package.json").write_text('{"name":"scratch","private":true}')
    rc, out = run(
        [npm, "install", "--no-audit", "--no-fund", "typescript@5", "@types/node@22"],
        proj,
        timeout=180,
    )
    if rc != 0:
        _TS_PROJECT = Path("/nonexistent")
        print(
            f"warning: TypeScript scratch project failed: {out[:200]}", file=sys.stderr
        )
        return None
    _TS_PROJECT = proj
    return proj


def check_ts(src: str, d: Path) -> tuple[int, str]:
    proj = ts_project()
    if proj is None:
        return -1, "typescript scratch project unavailable"
    f = proj / f"s_{d.name}.ts"
    f.write_text(src)
    tsc = proj / "node_modules/.bin/tsc"
    return run(
        [
            str(tsc),
            "--noEmit",
            "--strict",
            "--target",
            "es2022",
            "--lib",
            "es2022",
            "--moduleResolution",
            "bundler",
            "--module",
            "esnext",
            "--types",
            "node",
            str(f),
        ],
        proj,
        timeout=60,
    )


def check_swift(src: str, d: Path) -> tuple[int, str]:
    sc = tool("swiftc")
    if not sc:
        return -1, "swiftc not available"
    f = d / "s.swift"
    f.write_text(src)
    return run([sc, "-parse", str(f)], d)


CHECKERS = {
    "python": check_python,
    "java": check_java,
    "rust": check_rust,
    "go": check_go,
    "typescript": check_ts,
    "swift": check_swift,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="restrict to one file path fragment")
    ap.add_argument("--lang", help="restrict to one language")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any failure")
    args = ap.parse_args()

    files = sorted(PATTERNS.rglob("*.md"))
    if args.only:
        files = [f for f in files if args.only in str(f)]

    total = passed = failed = skipped = 0
    failures: list[str] = []

    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        rel = f.relative_to(ROOT)
        seen_by_lang: dict[str, str] = {}
        for i, (lang_raw, src) in enumerate(FENCE.findall(text), 1):
            lang = ALIASES.get(lang_raw.lower(), lang_raw.lower())
            if lang not in CHECKERS:
                continue
            if args.lang and lang != args.lang:
                continue
            total += 1
            with tempfile.TemporaryDirectory() as td:
                code, out = CHECKERS[lang](src, Path(td))
            # A block using a symbol from an earlier same-language block (a
            # class shown, then a test double for it) is real docs, not broken.
            if code not in (0, -1) and lang in seen_by_lang:
                cumulative = seen_by_lang[lang] + "\n\n" + src
                with tempfile.TemporaryDirectory() as td2:
                    code2, out2 = CHECKERS[lang](cumulative, Path(td2))
                if code2 == 0:
                    code, out = code2, out2
            seen_by_lang[lang] = seen_by_lang.get(lang, "") + "\n\n" + src
            if code == -1:
                skipped += 1
            elif code == 0:
                passed += 1
            else:
                failed += 1
                failures.append(f"{rel} block {i} [{lang}]\n{out.strip()[:600]}")

    for fail in failures:
        print(f"FAIL {fail}\n")

    print(
        f"{passed} compiled, {failed} failed, {skipped} skipped (no toolchain), {total} total"
    )
    return 1 if (failed and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
