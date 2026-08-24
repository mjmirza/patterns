#!/usr/bin/env python3
"""Generates a README index per family from entry frontmatter.
Regenerated on every run so an index can never drift from the entries."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"
QUEUE = ROOT / "docs" / "AUTHORING-QUEUE.json"


def load_planned() -> dict[str, list[tuple[str, str]]]:
    """Groups queued (name, reason) pairs by family folder name.
    reason is optional and renders only when a queue entry sets it."""
    if not QUEUE.exists():
        return {}
    try:
        data = json.loads(QUEUE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    planned: dict[str, list[tuple[str, str]]] = {}
    for entry in data:
        path = entry.get("path", "")
        name = entry.get("name", "")
        reason = entry.get("reason", "")
        parts = path.split("/")
        if len(parts) < 3 or parts[0] != "patterns" or not name:
            continue
        if (ROOT / path).exists():
            continue
        planned.setdefault(parts[1], []).append((name, reason))
    return planned


FAMILY_TITLES = {
    "01-design-patterns-gof": (
        "Design Patterns",
        "Gamma, Helm, Johnson, Vlissides 1994",
    ),
    "02-code-smells": ("Code Smells", "Fowler and Beck, Refactoring"),
    "03-refactoring": ("Refactoring Techniques", "Fowler, Refactoring 2nd edition"),
    "04-principles-and-laws": ("Principles and Laws", "Martin, Larman, Brewer, Conway"),
    "05-architectural": ("Architectural Patterns", "Buschmann POSA 1, Bass SEI"),
    "06-enterprise-application-architecture": (
        "Enterprise Application Architecture",
        "Fowler, PoEAA",
    ),
    "07-integration": ("Enterprise Integration", "Hohpe and Woolf"),
    "08-cloud-distributed": (
        "Cloud and Distributed",
        "Azure Architecture Center, Nygard",
    ),
    "09-concurrency": ("Concurrency and Parallelism", "Schmidt POSA 2"),
    "10-microservices": ("Microservices", "Richardson"),
    "11-domain-driven-design": ("Domain-Driven Design", "Evans, Vernon"),
    "12-data-storage": ("Data and Storage", "Kleppmann"),
    "13-frontend-ui": ("Frontend and UI", "Framework documentation"),
    "14-testing": ("Testing", "Meszaros, xUnit Test Patterns"),
    "15-security": ("Security", "OWASP ASVS"),
    "16-functional": ("Functional Programming", "Category theory in practice"),
    "17-ai-agentic": ("AI and Agentic", "Papers and vendor engineering, 2023 to 2026"),
    "18-anti-patterns": ("Anti-Patterns", "Brown et al, AntiPatterns"),
    "19-api-design": ("API and Interface Design", "REST, GraphQL, gRPC specifications"),
    "20-release-deployment": ("Release and Deployment", "Humble and Farley"),
    "21-sre-operations": ("SRE and Operations", "Google SRE, AWS Well-Architected"),
    "22-observability": ("Observability", "OpenTelemetry, RED and USE methods"),
    "23-workflow-orchestration": (
        "Workflow and Orchestration",
        "Durable execution literature",
    ),
    "24-stream-processing": (
        "Stream Processing",
        "Dataflow model, Kafka documentation",
    ),
    "25-mlops": ("MLOps", "Google ML design patterns"),
    "26-interaction-hci": ("Interaction and HCI", "Tidwell, Designing Interfaces"),
    "27-mobile-architecture": (
        "Mobile Architecture",
        "Official Android/iOS architecture guidance",
    ),
    "28-embedded-hardware": (
        "Embedded and Hardware-Software",
        "Embedded systems engineering literature",
    ),
    "29-realtime-simulation": (
        "Real-Time Simulation",
        "Nystrom, Game Programming Patterns",
    ),
}

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def field(block: str, key: str, default: str = "") -> str:
    m = re.search(rf"^{key}\s*:\s*(.+)$", block, re.M)
    return m.group(1).strip().strip("\"'") if m else default


def first_intent(text: str) -> str:
    # Dimension 2 opens on the problem, which is the useful one-line summary.
    # Dimension 1 opens on the canonical name, which says nothing.
    m = re.search(r"^##\s*2\.[^\n]*\n(.*?)(?=^##\s)", text, re.M | re.S)
    if not m:
        return ""
    body = "\n".join(
        ln
        for ln in m.group(1).splitlines()
        if ln.strip() and not ln.lstrip().startswith(("```", "|", ">", "#"))
    )
    flat = re.sub(r"\s+", " ", re.sub(r"[*_`\[\]]", "", body)).strip()
    sentences = re.split(r"(?<=\.)\s+", flat)
    out = sentences[0] if sentences else flat
    if len(out) < 40 and len(sentences) > 1:
        out = f"{out} {sentences[1]}"
    if len(out) <= 180:
        return out
    return out[:180].rsplit(" ", 1)[0].rstrip(" ,;") + " ..."


def build(family: Path, planned_names: list[tuple[str, str]]) -> int:
    entries = sorted(p for p in family.glob("*.md") if p.name.lower() != "readme.md")
    if not entries and not planned_names:
        return 0

    key = family.name
    title, origin = FAMILY_TITLES.get(key, (key, ""))
    rows, groups = [], {}

    for f in entries:
        text = f.read_text(encoding="utf-8", errors="replace")
        m = FRONTMATTER.match(text)
        block = m.group(1) if m else ""
        name = field(block, "name", f.stem)
        cat = field(block, "category", "Uncategorised")
        mat = field(block, "maturity", "unknown")
        words = len(text.split())
        groups.setdefault(cat, []).append(
            (name, f.name, mat, words, first_intent(text))
        )
        rows.append(words)

    planned_names = sorted(planned_names)
    total = len(entries) + len(planned_names)
    published_line = f"{len(entries)} entries, {sum(rows):,} words"
    if planned_names:
        published_line += (
            f", {len(planned_names)} more planned, {total} total when the "
            "family is complete"
        )
    published_line += ". Every entry carries all 18"

    lines = [
        f"# Family {key.split('-')[0]}. {title}",
        "",
        f"Origin. {origin}" if origin else "",
        "",
        published_line,
        "dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).",
        "",
    ]

    for cat in sorted(groups):
        lines += [f"## {cat}", ""]
        lines += ["| Pattern | Maturity | Words | Intent |", "|---|---|---|---|"]
        for name, fn, mat, words, intent in sorted(groups[cat]):
            lines.append(f"| [{name}]({fn}) | {mat} | {words:,} | {intent} |")
        lines.append("")

    if planned_names:
        lines.append("## Planned")
        lines.append("")
        lines.append(
            "Named, not yet authored. Queued in "
            "[docs/AUTHORING-QUEUE.json](../../docs/AUTHORING-QUEUE.json), "
            "each one to be built to the same 18-dimension standard as "
            "the entries above before it is published."
        )
        lines.append("")
        for name, reason in planned_names:
            lines.append(f"- {name}. {reason}" if reason else f"- {name}")
        lines.append("")

    lines += [
        "## Reading order",
        "",
        "Entries are independent. Each one names the patterns it composes with and",
        "the patterns it conflicts with in dimension 13, so following those links",
        "gives a better path than reading top to bottom.",
        "",
        "Generated by `tools/gen-indexes.py`. Do not edit by hand.",
    ]

    (family / "README.md").write_text("\n".join(lines) + "\n")
    return len(entries)


def main() -> int:
    total = 0
    planned = load_planned()
    for family in sorted(PATTERNS.iterdir()):
        if family.is_dir():
            n = build(family, planned.get(family.name, []))
            if n:
                print(f"{family.name}: {n} entries indexed")
                total += n
    print(f"\n{total} entries across all family indexes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
