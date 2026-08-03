#!/usr/bin/env python3
"""Generates catalogue status from real state, never a hand-typed number.
Reads published entries plus docs/AUTHORING-QUEUE.json, writes
docs/PROGRESS.md, dist/catalogue-status.json/.csv, and the README table."""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"
QUEUE_PATH = ROOT / "docs" / "AUTHORING-QUEUE.json"
SCOPE_PATH = ROOT / "docs" / "SCOPE-TARGET.json"
README_PATH = ROOT / "README.md"
PROGRESS_PATH = ROOT / "docs" / "PROGRESS.md"
DIST_DIR = ROOT / "dist"

# An entry is stale past this many days since its last real edit (git log).
STALE_DAYS = 180

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
VALID_MATURITY = {"canonical", "established", "emerging", "contested", "deprecated"}

FAMILY_ORIGIN = {
    "01-gof": ("Design Patterns (GoF)", "Gamma, Helm, Johnson, Vlissides 1994"),
    "02-code-smells": ("Code Smells", "Fowler and Beck, Refactoring"),
    "03-refactoring": ("Refactoring Techniques", "Fowler, Refactoring 2nd ed"),
    "04-principles-and-laws": ("Principles and Laws", "Martin, Larman, Brewer, Conway"),
    "05-architectural": ("Architectural Patterns", "Buschmann POSA 1, Bass SEI"),
    "06-poeaa": ("Enterprise Application Architecture", "Fowler, PoEAA"),
    "07-integration": ("Enterprise Integration", "Hohpe and Woolf"),
    "08-cloud-distributed": ("Cloud and Distributed", "Azure Architecture Center"),
    "09-concurrency": ("Concurrency and Parallelism", "Schmidt POSA 2"),
    "10-microservices": ("Microservices", "Richardson"),
    "11-ddd": ("Domain-Driven Design", "Evans, Vernon"),
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
    "24-stream-processing": ("Stream Processing", "Dataflow model, Kafka docs"),
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


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER.match(text)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip().strip('"')
    return fm


def published_by_family() -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for f in sorted(PATTERNS.rglob("*.md")):
        if f.name == "README.md":
            continue
        family = f.parent.name
        text = f.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        maturity = fm.get("maturity", "")
        if maturity not in VALID_MATURITY:
            maturity = "unspecified"
        result.setdefault(family, []).append({"slug": f.stem, "maturity": maturity})
    return result


def stale_count(published_paths: set[str]) -> int:
    if not (ROOT / ".git").exists():
        return 0
    stale = 0
    for rel in published_paths:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            out = subprocess.run(
                ["git", "log", "-1", "--format=%ct", "--", rel],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
            ts = int(out.stdout.strip())
        except (ValueError, subprocess.SubprocessError):
            continue
        age_days = (datetime.now(timezone.utc).timestamp() - ts) / 86400
        if age_days > STALE_DAYS:
            stale += 1
    return stale


def planned_by_family(published_paths: set[str]) -> dict[str, int]:
    # Planned = queue entry not yet on disk, matching next-batch.py's filter.
    if not QUEUE_PATH.exists():
        return {}
    queue = json.loads(QUEUE_PATH.read_text())
    counts: dict[str, int] = {}
    for e in queue:
        if e["path"] in published_paths:
            continue
        family = Path(e["path"]).parts[1]
        counts[family] = counts.get(family, 0) + 1
    return counts


def build_rows() -> tuple[list[dict], int, int, int]:
    pub = published_by_family()
    published_paths = {
        f"patterns/{fam}/{e['slug']}.md"
        for fam, entries in pub.items()
        for e in entries
    }
    planned = planned_by_family(published_paths)
    stale = stale_count(published_paths)
    families = sorted(set(FAMILY_ORIGIN) | set(pub) | set(planned))
    rows = []
    total_pub = 0
    total_target = 0
    for fam in families:
        entries = pub.get(fam, [])
        n_pub = len(entries)
        n_planned = planned.get(fam, 0)
        target = n_pub + n_planned
        maturity_counts: dict[str, int] = {}
        for e in entries:
            maturity_counts[e["maturity"]] = maturity_counts.get(e["maturity"], 0) + 1
        origin = FAMILY_ORIGIN.get(fam, (fam, "unclassified"))
        rows.append(
            {
                "family": fam,
                "name": origin[0],
                "origin": origin[1],
                "published": n_pub,
                "planned": n_planned,
                "target": target,
                "percent": round(100 * n_pub / target, 1) if target else 0.0,
                "maturity": maturity_counts,
            }
        )
        total_pub += n_pub
        total_target += target
    return rows, total_pub, total_target, stale


def references_checked() -> int:
    cache_path = ROOT / ".ref-cache.json"
    if not cache_path.exists():
        return 0
    return len(json.loads(cache_path.read_text()))


def write_dist(rows: list[dict], total_pub: int, total_target: int, stale: int) -> None:
    DIST_DIR.mkdir(exist_ok=True)
    payload = {
        "generated_by": "tools/gen-catalogue-status.py",
        "published_total": total_pub,
        "target_total": total_target,
        "families_total": len(rows),
        "families_complete": sum(
            1 for r in rows if r["published"] == r["target"] and r["target"] > 0
        ),
        "stale_entries": stale,
        "references_checked": references_checked(),
        "rows": rows,
    }
    (DIST_DIR / "catalogue-status.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    with (DIST_DIR / "catalogue-status.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "name", "published", "planned", "target", "percent"])
        for r in rows:
            w.writerow(
                [
                    r["family"],
                    r["name"],
                    r["published"],
                    r["planned"],
                    r["target"],
                    r["percent"],
                ]
            )


def write_progress(
    rows: list[dict], total_pub: int, total_target: int, stale: int
) -> None:
    complete = sum(1 for r in rows if r["published"] == r["target"] and r["target"] > 0)
    lines = [
        "# Catalogue Progress",
        "",
        "Generated by `tools/gen-catalogue-status.py`. Never hand-edit; CI",
        "checks this file stays current with real repository state.",
        "",
        f"Published: {total_pub}",
        f"Target (published plus planned): {total_target}",
        f"Completion: {round(100 * total_pub / total_target, 1) if total_target else 0}%",
        f"Families: {len(rows)}",
        f"Families complete: {complete}",
        f"Stale entries (untouched past {STALE_DAYS} days): {stale}",
        f"References checked (live in .ref-cache.json): {references_checked()}",
        "",
        "| # | Family | Published | Planned | Target | Percent |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i:02d} | {r['name']} | {r['published']} | {r['planned']} | "
            f"{r['target']} | {r['percent']}% |"
        )
    PROGRESS_PATH.write_text("\n".join(lines) + "\n")


def rewrite_readme(
    rows: list[dict], total_pub: int, total_target: int, stale: int
) -> None:
    text = README_PATH.read_text()

    text = re.sub(
        r"!\[Families\]\(https://img\.shields\.io/badge/families-\d+-informational\)",
        f"![Families](https://img.shields.io/badge/families-{len(rows)}-informational)",
        text,
    )
    text = re.sub(
        r"!\[Entries\]\(https://img\.shields\.io/badge/entries-[^)]+\)",
        f"![Entries](https://img.shields.io/badge/entries-{total_pub}%20published%20%2F%20{total_target}%20planned-yellow)",
        text,
    )

    completion = round(100 * total_pub / total_target, 1) if total_target else 0.0
    refs = references_checked()
    dynamic_block = "\n".join(
        [
            "![CI](https://github.com/mjmirza/patterns/actions/workflows/ci.yml/badge.svg?branch=main)",
            "![Schema version](https://img.shields.io/badge/schema-v1.0-informational)",
            f"![Published entries](https://img.shields.io/badge/published-{total_pub}-brightgreen)",
            f"![Planned entries](https://img.shields.io/badge/planned-{total_target - total_pub}-lightgrey)",
            f"![Catalogue completion](https://img.shields.io/badge/completion-{completion}%25-yellow)",
            f"![References checked](https://img.shields.io/badge/references%20checked-{refs}-brightgreen)",
            f"![Stale entries](https://img.shields.io/badge/stale%20entries-{stale}-brightgreen)",
            "![Code examples tested](https://img.shields.io/badge/code%20examples-compiled%20in%20CI-brightgreen)",
        ]
    )
    text = re.sub(
        r"<!-- BADGES:AUTOGEN:START -->.*?<!-- BADGES:AUTOGEN:END -->",
        f"<!-- BADGES:AUTOGEN:START -->\n{dynamic_block}\n<!-- BADGES:AUTOGEN:END -->",
        text,
        flags=re.S,
    )

    table_lines = [
        "| # | Family | Origin | Published | Planned | Target |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        link = f"[{r['name']}](patterns/{r['family']}/)"
        table_lines.append(
            f"| {i:02d} | {link} | {r['origin']} | {r['published']} | "
            f"{r['planned']} | {r['target']} |"
        )
    new_table = "\n".join(table_lines)

    pattern = re.compile(
        r"(## The families\n\n)\| # \| Family \|.*?\n\n(?=Family 04)",
        re.S,
    )
    text = pattern.sub(lambda m: m.group(1) + new_table + "\n\n", text)

    README_PATH.write_text(text)


def main() -> int:
    rows, total_pub, total_target, stale = build_rows()
    write_dist(rows, total_pub, total_target, stale)
    write_progress(rows, total_pub, total_target, stale)
    rewrite_readme(rows, total_pub, total_target, stale)
    print(
        f"published={total_pub} target={total_target} families={len(rows)} stale={stale}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
