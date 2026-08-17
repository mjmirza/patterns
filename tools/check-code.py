#!/usr/bin/env python3
"""Compiles or syntax-checks every fenced code sample in every entry.
A sample that does not compile is a defect. Missing toolchains are skipped, never faked."""

from __future__ import annotations

import argparse
import json
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


def run(cmd: list[str], cwd: Path, timeout: int = 120, max_output: int = 1500) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        out = (p.stderr or p.stdout)
        if max_output and len(out) > max_output:
            out = out[:max_output]
        return p.returncode, out
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
    f.write_text(src, encoding="utf-8")
    return run([sys.executable, "-m", "py_compile", str(f)], d)


def check_java(src: str, d: Path) -> tuple[int, str]:
    javac = tool("javac")
    if not javac:
        return -1, "javac not available"
    name = public_class(src) or "Main"
    f = d / f"{name}.java"
    f.write_text(src, encoding="utf-8")
    return run([javac, "-nowarn", "-d", str(d), str(f)], d)


def check_rust(src: str, d: Path) -> tuple[int, str]:
    rustc = tool("rustc")
    if not rustc:
        return -1, "rustc not available"
    body = src if re.search(r"\bfn\s+main\s*\(", src) else src + "\nfn main() {}\n"
    f = d / "s.rs"
    f.write_text(body, encoding="utf-8")
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
    f.write_text(body, encoding="utf-8")
    return run([go, "vet", str(f)], d)


_TS_PROJECT: Path | None = None


def ts_project() -> Path | None:
    # A shared node_modules resolves @types/node; a fresh npx cache per file does not.
    global _TS_PROJECT
    if _TS_PROJECT is not None:
        checker = _TS_PROJECT / "checker.js"
        return _TS_PROJECT if checker.exists() else None
    npm = tool("npm")
    node = tool("node")
    if not npm or not node:
        _TS_PROJECT = Path("/nonexistent")
        return None
    proj = Path(tempfile.mkdtemp(prefix="patterns-ts-"))
    (proj / "package.json").write_text('{"name":"scratch","private":true}', encoding="utf-8")
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

    checker_script = proj / "checker.js"
    checker_script.write_text(
        """const fs = require("fs");
const path = require("path");
const ts = require("typescript");

const input = JSON.parse(fs.readFileSync(process.argv[2] || 0, "utf-8"));
const options = {
  noEmit: true,
  strict: true,
  target: ts.ScriptTarget.ES2022,
  moduleResolution: ts.ModuleResolutionKind.Bundler,
  module: ts.ModuleKind.ESNext,
  types: ["node"],
  lib: ["lib.es2022.d.ts"]
};

let currentFileName = "";
let currentFileContent = "";

const servicesHost = {
  getScriptFileNames: () => [currentFileName],
  getScriptVersion: (fileName) => "1",
  getScriptSnapshot: (fileName) => {
    if (fileName === currentFileName) {
      return ts.ScriptSnapshot.fromString(currentFileContent);
    }
    if (fs.existsSync(fileName)) {
      return ts.ScriptSnapshot.fromString(fs.readFileSync(fileName, "utf-8"));
    }
    return undefined;
  },
  getCurrentDirectory: () => __dirname,
  getCompilationSettings: () => options,
  getDefaultLibFileName: (opts) => ts.getDefaultLibFilePath(opts),
  fileExists: (fileName) => fileName === currentFileName || fs.existsSync(fileName),
  readFile: (fileName) => fileName === currentFileName ? currentFileContent : fs.readFileSync(fileName, "utf-8"),
  readDirectory: ts.sys.readDirectory,
  directoryExists: ts.sys.directoryExists,
  getDirectories: ts.sys.getDirectories,
};

const service = ts.createLanguageService(servicesHost, ts.createDocumentRegistry());

const results = {};

for (let idx = 0; idx < input.length; idx++) {
  const item = input[idx];
  currentFileName = path.join(__dirname, `virtual_${item.id}.ts`);
  currentFileContent = item.src;

  const diagnostics = service.getSyntacticDiagnostics(currentFileName)
    .concat(service.getSemanticDiagnostics(currentFileName));

  results[item.id] = [
    diagnostics.length === 0 ? 0 : 1,
    diagnostics.map(d => ts.flattenDiagnosticMessageText(d.messageText, "\\n")).join("\\n")
  ];
}

console.log(JSON.stringify(results));
""",
        encoding="utf-8",
    )

    _TS_PROJECT = proj
    return proj


def check_ts_batch(tasks: list[tuple[int, str]]) -> dict[int, tuple[int, str]]:
    """Runs batch TypeScript checks via Node LanguageService runner."""
    if not tasks:
        return {}
    proj = ts_project()
    if proj is None:
        return {tid: (-1, "typescript scratch project unavailable") for tid, _ in tasks}

    node = tool("node")
    if not node:
        return {tid: (-1, "node not available") for tid, _ in tasks}

    checker_script = proj / "checker.js"
    tasks_file = proj / "tasks.json"
    tasks_file.write_text(json.dumps([{"id": tid, "src": src} for tid, src in tasks]), encoding="utf-8")
    rc, out = run([node, str(checker_script), str(tasks_file)], proj, timeout=180, max_output=0)
    if rc != 0 or not out.strip():
        return {tid: (1, f"TypeScript runner failed: {out}") for tid, _ in tasks}

    try:
        raw_res = json.loads(out)
        res = {}
        for tid_str, (code, msg) in raw_res.items():
            res[int(tid_str)] = (code, msg)
        return res
    except Exception as e:
        return {tid: (1, f"Failed to parse TS runner output: {e}\n{out[:500]}") for tid, _ in tasks}


def check_ts(src: str, d: Path) -> tuple[int, str]:
    res = check_ts_batch([(0, src)])
    return res.get(0, (-1, "typescript check failed"))


def check_swift(src: str, d: Path) -> tuple[int, str]:
    sc = tool("swiftc")
    if not sc:
        return -1, "swiftc not available"
    f = d / "s.swift"
    f.write_text(src, encoding="utf-8")
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

    ts_tasks: list[tuple[int, str]] = []
    task_counter = 0

    # First pass: map blocks and collect TypeScript batch tasks with explicit task IDs
    parsed_files: list[tuple[Path, list[tuple[int, str, str, int | None, int | None]]]] = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        blocks: list[tuple[int, str, str, int | None, int | None]] = []
        seen_ts = ""
        for i, (lang_raw, src) in enumerate(FENCE.findall(text), 1):
            lang = ALIASES.get(lang_raw.lower(), lang_raw.lower())
            if lang not in CHECKERS:
                continue
            if args.lang and lang != args.lang:
                continue

            st_id: int | None = None
            cum_id: int | None = None
            if lang == "typescript":
                st_id = task_counter
                ts_tasks.append((st_id, src))
                task_counter += 1

                if seen_ts:
                    cum_src = seen_ts + "\n\n" + src
                    cum_id = task_counter
                    ts_tasks.append((cum_id, cum_src))
                    task_counter += 1
                seen_ts = (seen_ts + "\n\n" + src) if seen_ts else src

            blocks.append((i, lang, src, st_id, cum_id))
        parsed_files.append((f, blocks))

    # Run TypeScript tasks in batch
    ts_results = check_ts_batch(ts_tasks) if ts_tasks else {}

    total = passed = failed = skipped = 0
    failures: list[str] = []

    # Second pass: evaluate all results using explicit task IDs
    for f, blocks in parsed_files:
        rel = f.relative_to(ROOT)
        seen_by_lang: dict[str, str] = {}
        for i, lang, src, st_id, cum_id in blocks:
            total += 1
            if lang == "typescript" and st_id is not None:
                code, out = ts_results.get(st_id, (-1, "no result"))
                if code not in (0, -1) and cum_id is not None:
                    code2, out2 = ts_results.get(cum_id, (-1, "no result"))
                    if code2 == 0:
                        code, out = code2, out2
                seen_by_lang[lang] = seen_by_lang.get(lang, "") + "\n\n" + src
            else:
                with tempfile.TemporaryDirectory() as td:
                    code, out = CHECKERS[lang](src, Path(td))
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
