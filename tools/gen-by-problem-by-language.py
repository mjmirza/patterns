#!/usr/bin/env python3
"""Generates docs/BY-PROBLEM.md and docs/BY-LANGUAGE.md from pattern entries.
Ensures discovery pathways are up-to-date with repository content."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS_DIR = ROOT / "patterns"
DOCS_DIR = ROOT / "docs"

# Languages we want to index
TARGET_LANGS = {
    "go": "Go",
    "rust": "Rust",
    "python": "Python",
    "typescript": "TypeScript",
    "java": "Java",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "csharp": "C#",
    "cpp": "C++",
}

FAMILY_NAMES = {
    "01-gof": "Design Patterns (GoF)",
    "02-code-smells": "Code Smells",
    "03-refactoring": "Refactoring Techniques",
    "04-principles-and-laws": "Principles and Laws",
    "05-architectural": "Architectural Patterns",
    "06-enterprise-application-architecture": "Enterprise Application Architecture",
    "07-integration": "Enterprise Integration",
    "08-cloud-distributed": "Cloud and Distributed",
    "09-concurrency": "Concurrency and Parallelism",
    "10-microservices": "Microservices",
    "11-domain-driven-design": "Domain-Driven Design",
    "12-data-storage": "Data and Storage",
    "13-frontend-ui": "Frontend and UI",
    "14-testing": "Testing",
    "15-security": "Security",
    "16-functional": "Functional Programming",
    "17-ai-agentic": "AI and Agentic",
    "18-anti-patterns": "Anti-Patterns",
    "19-api-design": "API and Interface Design",
    "20-release-deployment": "Release and Deployment",
    "21-sre-operations": "SRE and Operations",
    "22-observability": "Observability",
    "23-workflow-orchestration": "Workflow and Orchestration",
    "24-stream-processing": "Stream Processing",
    "25-mlops": "MLOps",
    "26-interaction-hci": "Interaction and HCI",
    "27-mobile-architecture": "Mobile Architecture",
    "28-embedded-hardware": "Embedded and Hardware-Software",
    "29-realtime-simulation": "Real-Time Simulation",
}

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
CODE_BLOCK_RE = re.compile(r"^```([a-zA-Z0-9+#]+)", re.M)


def clean_text(text: str) -> str:
    # Removes simple markdown formatting and table pipe delimiters
    t = text.replace("|", "/")
    t = re.sub(r"[*_`#\[\]]", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def extract_section(text: str, num: int) -> str:
    # Find Section "num." up to next main section heading "num+1." or any ## heading
    # Handles "## X." where X is the number, or "### X."
    pattern = rf"^##[#]?\s+{num}\.[^\n]*\n(.*?)(?=^##[#]?\s+\d+\.|\Z)"
    m = re.search(pattern, text, re.M | re.S)
    return m.group(1).strip() if m else ""


def extract_problem_statement(sec2: str) -> str:
    # Extracts the first paragraph that is not a list, blockquote, or code block
    for block in sec2.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith(("-", "*", ">", "```", "1.", "|")):
            continue
        return clean_text(block)
    return ""


def clean_symptom_prefix(text: str) -> str:
    # Strips leading numbers, bullets, bold Symptom headers, etc.
    t = text.strip()
    t = re.sub(r"^\d+\.\s*", "", t)
    if t.startswith(("-", "*")):
        t = t[1:].strip()
    t = re.sub(r"^\*\*symptom\.?\*\*\s*", "", t, flags=re.I)
    t = re.sub(r"^symptom\.?\s*", "", t, flags=re.I)
    return clean_text(t)


def extract_symptoms_sec2(sec2: str) -> list[str]:
    # Extracts bullet points/symptoms from Section 2
    symptoms = []
    lines = sec2.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith(("-", "*")) and len(line) > 2:
            cleaned = clean_symptom_prefix(line)
            if cleaned:
                symptoms.append(cleaned)
    return symptoms


def extract_symptoms_sec11(sec11: str) -> list[str]:
    # Extracts symptoms/failure modes from Section 11 while filtering out Cause, Fix, Triple lines
    symptoms = []
    for line in sec11.splitlines():
        line_str = line.strip()
        low = line_str.lower()
        if not line_str:
            continue
        # Filter out lines that are Cause, Fix, or Triple lines
        if low.startswith(("cause.", "fix.", "triple")) or "cause." in low[:10] or "fix." in low[:10]:
            continue

        if "symptom" in low or line_str.startswith(("-", "*")):
            cleaned = clean_symptom_prefix(line_str)
            # Make sure it didn't turn into a Cause or Fix
            if cleaned and not cleaned.lower().startswith(("cause.", "fix.", "triple")):
                symptoms.append(cleaned)
    return symptoms


def parse_languages(text: str) -> set[str]:
    # Extracts code languages used in the code blocks
    langs = {m.lower() for m in CODE_BLOCK_RE.findall(text)}
    # Map synonyms/variants
    mapped_langs = set()
    for lang in langs:
        if lang in {"ts", "typescript"}:
            mapped_langs.add("typescript")
        elif lang in {"py", "python"}:
            mapped_langs.add("python")
        elif lang in {"rs", "rust"}:
            mapped_langs.add("rust")
        elif lang in {"go"}:
            mapped_langs.add("go")
        elif lang in {"java"}:
            mapped_langs.add("java")
        elif lang in {"swift"}:
            mapped_langs.add("swift")
        elif lang in {"kt", "kotlin"}:
            mapped_langs.add("kotlin")
        elif lang in {"cs", "csharp"}:
            mapped_langs.add("csharp")
        elif lang in {"cpp", "c"}:
            mapped_langs.add("cpp")
    return mapped_langs


def detect_mentions(section_text: str, lang_key: str) -> bool:
    # Checks if a section mentions a language specifically
    text_lower = section_text.lower()

    # Define search terms for each language
    terms = {
        "go": [r"\bgo\b", r"\bgolang\b"],
        "rust": [r"\brust\b"],
        "python": [r"\bpython\b"],
        "typescript": [r"\btypescript\b", r"\bts\b"],
        "java": [r"\bjava\b"],
        "swift": [r"\bswift\b"],
        "kotlin": [r"\bkotlin\b"],
        "csharp": [r"\bcsharp\b", r"c#"],
        "cpp": [r"\bcpp\b", r"\bc\+\+\b"],
    }

    for pattern in terms.get(lang_key, []):
        if re.search(pattern, text_lower):
            return True
    return False


def build_problem_doc(patterns: list[dict]) -> str:
    lines = [
        "# Patterns by Problem and Symptom",
        "",
        "This document maps observable symptoms you can detect in a codebase to the patterns that address them.",
        "Instead of searching by pattern names you might not know, look for the symptoms your system is exhibiting.",
        "",
        "## Symptoms Index",
        "",
        "A scannable index of codebase symptoms and the matching patterns to explore:",
        "",
        "| Observed Symptom | Applicable Pattern | Family |",
        "|---|---|---|",
    ]

    # Gather all symptoms with pattern mappings for the quick-lookup table
    table_rows = []
    for p in patterns:
        all_symptoms = p["symptoms_sec2"] + p["symptoms_sec11"]
        for sym in all_symptoms:
            # Truncate extremely long symptoms for table readability
            short_sym = sym if len(sym) <= 120 else sym[:117] + "..."
            table_rows.append((short_sym, p["name"], f"../patterns/{p['family_dir']}/{p['file_name']}", p["family_name"]))

    # Sort table alphabetically by symptom for easy scanning
    for sym, name, link, fam in sorted(table_rows, key=lambda x: x[0].lower()):
        lines.append(f"| {sym} | [{name}]({link}) | {fam} |")

    lines.append("")
    lines.append("## Detailed Problem Profiles by Family")
    lines.append("")

    # Group patterns by family
    families = {}
    for p in patterns:
        families.setdefault(p["family_dir"], []).append(p)

    for fam_dir in sorted(families.keys()):
        fam_name = FAMILY_NAMES.get(fam_dir, fam_dir)
        lines.append(f"### {fam_name}")
        lines.append("")

        for p in sorted(families[fam_dir], key=lambda x: x["name"]):
            link = f"../patterns/{p['family_dir']}/{p['file_name']}"
            lines.append(f"#### [{p['name']}]({link})")
            lines.append("")
            if p["problem_statement"]:
                lines.append(f"**Core Problem:** {p['problem_statement']}")
                lines.append("")
            if p["symptoms_sec2"]:
                lines.append("**Observable Symptoms:**")
                lines.append("")  # MD032: blank line before list
                for sym in p["symptoms_sec2"]:
                    lines.append(f"- {sym}")
                lines.append("")  # MD032: blank line after list
            if p["symptoms_sec11"]:
                lines.append("**Failure Mode Symptoms:**")
                lines.append("")  # MD032: blank line before list
                for sym in p["symptoms_sec11"]:
                    lines.append(f"- {sym}")
                lines.append("")  # MD032: blank line after list

    lines.append("Generated by `tools/gen-by-problem-by-language.py`. Do not edit by hand.")
    return "\n".join(lines) + "\n"


def build_language_doc(patterns: list[dict]) -> str:
    lines = [
        "# Patterns by Language",
        "",
        "This reference lists which patterns change shape in which programming language, and which ones a language makes unnecessary.",
        "",
        "## Language Implementation Matrix",
        "",
        "This matrix tracks which patterns provide runnable code examples in each language. Yes indicates the language is natively supported with a fully compiled or runnable implementation.",
        "",
    ]

    # Build matrix table headers
    langs_sorted = sorted(TARGET_LANGS.keys())
    headers = ["Pattern", "Family"] + [TARGET_LANGS[l] for l in langs_sorted]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    # Add rows to matrix
    for p in sorted(patterns, key=lambda x: (x["family_dir"], x["name"])):
        link = f"../patterns/{p['family_dir']}/{p['file_name']}"
        row = [f"[{p['name']}]({link})", p["family_name"]]
        for l in langs_sorted:
            row.append("Yes" if l in p["impl_langs"] else "")
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append("## Language Reference Guides")
    lines.append("")

    for lang_key in langs_sorted:
        lang_name = TARGET_LANGS[lang_key]
        lines.append(f"### {lang_name}")
        lines.append("")

        # 1. Implemented in
        impls = []
        for p in patterns:
            if lang_key in p["impl_langs"]:
                link = f"../patterns/{p['family_dir']}/{p['file_name']}"
                impls.append(f"- [{p['name']}]({link}) ({p['family_name']})")

        lines.append(f"#### Implemented in {lang_name}")
        lines.append("")
        lines.append(f"These patterns contain runnable code examples written in {lang_name}:")
        lines.append("")
        if impls:
            lines.extend(sorted(impls))
        else:
            lines.append("No direct implementations recorded yet.")
        lines.append("")

        # 2. Changes shape in
        shapes = []
        for p in patterns:
            if detect_mentions(p["sec8_text"], lang_key):
                link = f"../patterns/{p['family_dir']}/{p['file_name']}"
                shapes.append(f"- [{p['name']}]({link}) ({p['family_name']})")

        lines.append(f"#### Changes Shape in {lang_name}")
        lines.append("")
        lines.append(f"These patterns have unique implementation variants or change their design structure specifically when built using {lang_name} features (documented in Dimension 8):")
        lines.append("")
        if shapes:
            lines.extend(sorted(shapes))
        else:
            lines.append("No language-specific design mutations recorded.")
        lines.append("")

        # 3. Made unnecessary or alternative in
        unnecessaries = []
        for p in patterns:
            if detect_mentions(p["sec4_text"], lang_key):
                link = f"../patterns/{p['family_dir']}/{p['file_name']}"
                unnecessaries.append(f"- [{p['name']}]({link}) ({p['family_name']})")

        lines.append(f"#### Made Unnecessary or Alternative in {lang_name}")
        lines.append("")
        lines.append(f"These patterns have native features in {lang_name} that make the pattern unnecessary, or require an alternative design approach (documented in Dimension 4):")
        lines.append("")
        if unnecessaries:
            lines.extend(sorted(unnecessaries))
        else:
            lines.append("No language-level redundancies recorded.")
        lines.append("")

    lines.append("Generated by `tools/gen-by-problem-by-language.py`. Do not edit by hand.")
    return "\n".join(lines) + "\n"


def main() -> int:
    pattern_files = sorted(PATTERNS_DIR.rglob("*.md"))
    pattern_files = [f for f in pattern_files if f.name.lower() not in {"readme.md", "index.md"}]

    if not pattern_files:
        print("Error: No pattern entries found on disk.")
        return 1

    patterns_data = []

    for f in pattern_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        fm_match = FRONTMATTER_RE.match(text)
        block = fm_match.group(1) if fm_match else ""

        def fm_field(key: str, default: str = "") -> str:
            m = re.search(rf"^{key}\s*:\s*(.+)$", block, re.M)
            return m.group(1).strip().strip("\"'") if m else default

        name = fm_field("name", f.stem)
        family_dir = f.parent.name
        family_name = FAMILY_NAMES.get(family_dir, family_dir)

        sec2_text = extract_section(text, 2)
        sec4_text = extract_section(text, 4)
        sec8_text = extract_section(text, 8)
        sec11_text = extract_section(text, 11)

        problem_statement = extract_problem_statement(sec2_text)
        symptoms_sec2 = extract_symptoms_sec2(sec2_text)
        symptoms_sec11 = extract_symptoms_sec11(sec11_text)
        impl_langs = parse_languages(text)

        patterns_data.append({
            "name": name,
            "file_name": f.name,
            "family_dir": family_dir,
            "family_name": family_name,
            "problem_statement": problem_statement,
            "symptoms_sec2": symptoms_sec2,
            "symptoms_sec11": symptoms_sec11,
            "impl_langs": impl_langs,
            "sec4_text": sec4_text,
            "sec8_text": sec8_text,
        })

    # Ensure docs directory exists
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate documents
    by_problem_content = build_problem_doc(patterns_data)
    by_language_content = build_language_doc(patterns_data)

    (DOCS_DIR / "BY-PROBLEM.md").write_text(by_problem_content, encoding="utf-8")
    (DOCS_DIR / "BY-LANGUAGE.md").write_text(by_language_content, encoding="utf-8")

    print("Success: Generated docs/BY-PROBLEM.md and docs/BY-LANGUAGE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
