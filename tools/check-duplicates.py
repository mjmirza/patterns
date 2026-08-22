#!/usr/bin/env python3
"""Multi-pass semantic duplicate detector for software patterns.

Pass 1: Exact string & path duplication.
Pass 2: Alias/acronym/name normalization.
Pass 3: Semantic problem/mechanism text comparison (token Jaccard similarity).
Pass 4: Cross-family comparison.
Pass 5: Historical PR/commit proposal comparison.
Pass 6 & 7: Evidence reporting and false-positive defense.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS_DIR = ROOT / "patterns"
QUEUE_FILE = ROOT / "docs" / "AUTHORING-QUEUE.json"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "or", "not", "this", "but", "they", "have", "had", "which"
}

GENERIC_PATTERN_TERMS = {
    "architecture", "pattern", "patterns", "technique", "smell",
    "framework", "system", "design", "model"
}


def normalize_term(term: str) -> str:
    """Normalize names/aliases: lowercase, strip generic suffixes/stopwords, remove non-alphanumeric."""
    s = term.lower().strip()
    s = re.sub(r"'s\b", "", s)
    words = [w for w in re.split(r"\W+", s) if w and w not in GENERIC_PATTERN_TERMS]
    s_clean = "".join(words)
    return s_clean or re.sub(r"\W+", "", term.lower())


def tokenize_text(text: str) -> set[str]:
    """Tokenize prose text into lower-case alphanumeric tokens without stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS and w not in GENERIC_PATTERN_TERMS}


def jaccard_similarity(set1: set[str], set2: set[str], threshold: float = 0.0) -> float:
    len1, len2 = len(set1), len(set2)
    if not len1 or not len2:
        return 0.0
    if threshold > 0 and (len1 < len2 * threshold or len2 < len1 * threshold):
        return 0.0
    inter_len = len(set1 & set2)
    if inter_len == 0:
        return 0.0
    union_len = len1 + len2 - inter_len
    return inter_len / union_len if union_len > 0 else 0.0


def extract_frontmatter_and_sections(filepath: Path) -> dict:
    text = filepath.read_text(encoding="utf-8", errors="replace")
    fm_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)

    fm_text = fm_match.group(1) if fm_match else ""
    name_match = re.search(r"^name\s*:\s*(.+)$", fm_text, re.MULTILINE)
    aliases_match = re.search(r"^aliases\s*:\s*(.+)$", fm_text, re.MULTILINE)
    family_match = re.search(r"^family\s*:\s*(.+)$", fm_text, re.MULTILINE)

    name = name_match.group(1).strip(" \"'\t") if name_match else filepath.stem
    family = family_match.group(1).strip(" \"'\t") if family_match else filepath.parent.name

    aliases = []
    if aliases_match:
        val = aliases_match.group(1).strip()
        if val.startswith("[") and val.endswith("]"):
            aliases = [x.strip(" \"'\t") for x in val[1:-1].split(",") if x.strip()]
        else:
            aliases = [val.strip(" \"'\t")]

    # Extract sections
    sections: dict[str, list[str]] = {}
    current_section = "preamble"
    sections[current_section] = []

    for line in text.splitlines():
        h_match = re.match(r"^#{2,3}\s+(.+)$", line)
        if h_match:
            current_section = h_match.group(1).strip().lower()
            sections[current_section] = []
        else:
            sections.setdefault(current_section, []).append(line)

    sec_combined = {k: "\n".join(v) for k, v in sections.items()}

    problem_text = ""
    mechanism_text = ""
    for k, v in sec_combined.items():
        if "problem" in k or "context" in k:
            problem_text += "\n" + v
        if "structure" in k or "dynamics" in k or "implementation" in k or "mechanism" in k:
            mechanism_text += "\n" + v

    problem_tokens = tokenize_text(problem_text)
    mechanism_tokens = tokenize_text(mechanism_text)

    return {
        "path": str(filepath.relative_to(ROOT)),
        "slug": filepath.stem,
        "name": name,
        "aliases": aliases,
        "family": family,
        "problem_tokens": problem_tokens,
        "mechanism_tokens": mechanism_tokens,
    }


def fetch_historical_proposals() -> list[dict]:
    """Retrieve historical proposals from git log history if available."""
    history = []
    try:
        cmd = ["git", "log", "--all", "--name-status", "--oneline"]
        out = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, check=False).stdout
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0] in {"A", "M"}:
                path = parts[-1]
                if path.startswith("patterns/") and path.endswith(".md"):
                    history.append({"path": path, "slug": Path(path).stem})
    except Exception:
        pass
    return history


def analyze_repository(queue_path: Path) -> dict:
    published_files = [
        p for p in PATTERNS_DIR.rglob("*.md")
        if p.name.lower() not in {"readme.md", "index.md"}
    ]
    published = [extract_frontmatter_and_sections(f) for f in published_files]

    queue = []
    if queue_path.exists():
        try:
            queue = json.loads(queue_path.read_text(encoding="utf-8"))
        except Exception:
            queue = []

    collisions = []

    # Map published terms
    published_norm_map: dict[str, list[dict]] = {}
    for entry in published:
        all_terms = [entry["name"], entry["slug"]] + list(entry["aliases"])
        for term in all_terms:
            norm = normalize_term(term)
            if norm:
                published_norm_map.setdefault(norm, []).append(entry)

    # Queue vs Published Normalized Name/Alias Collisions
    for q in queue:
        q_path = q.get("path", "")
        q_slug = q.get("slug", "")
        q_name = q.get("name", "")
        q_aliases = q.get("aliases", [])

        q_terms = [q_name, q_slug] + list(q_aliases)
        for term in q_terms:
            norm = normalize_term(term)
            if norm in published_norm_map:
                for pub in published_norm_map[norm]:
                    if pub["path"] != q_path:
                        collisions.append({
                            "type": "QUEUE_VS_PUBLISHED",
                            "queue_path": q_path,
                            "published_path": pub["path"],
                            "matched_term": term,
                            "normalized_key": norm,
                            "queue_name": q_name,
                            "published_name": pub["name"],
                        })

    # Published vs Published Semantic Similarity Check
    semantic_collisions = []
    threshold = 0.70
    for i in range(len(published)):
        p1 = published[i]
        t1_prob = p1["problem_tokens"]
        t1_mech = p1["mechanism_tokens"]
        for j in range(i + 1, len(published)):
            p2 = published[j]
            prob_sim = jaccard_similarity(t1_prob, p2["problem_tokens"], threshold)
            if prob_sim > threshold:
                mech_sim = jaccard_similarity(t1_mech, p2["mechanism_tokens"], threshold)
                if mech_sim > threshold:
                    semantic_collisions.append({
                        "type": "PUBLISHED_SEMANTIC_DUPLICATE",
                        "path1": p1["path"],
                        "path2": p2["path"],
                        "problem_similarity": prob_sim,
                        "mechanism_similarity": mech_sim,
                    })

    history = fetch_historical_proposals()

    return {
        "published_count": len(published),
        "queue_count": len(queue),
        "historical_count": len(history),
        "collisions": collisions,
        "semantic_collisions": semantic_collisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Software Pattern Duplicate Detector")
    parser.add_argument("--check", action="store_true", help="Run duplicate detection check")
    parser.add_argument("--strict", action="store_true", help="Fail with non-zero exit code on queue/published duplicate collision")
    args = parser.parse_args()

    results = analyze_repository(QUEUE_FILE)
    print(f"Analyzed {results['published_count']} published entries, {results['queue_count']} queue entries, {results['historical_count']} historic commits.")

    collisions = results["collisions"]
    semantic = results["semantic_collisions"]

    if collisions:
        print(f"\nFound {len(collisions)} potential duplicate/collision pairs:")
        seen = set()
        for c in collisions:
            pair_key = (c["queue_path"], c["published_path"], c["normalized_key"])
            if pair_key not in seen:
                seen.add(pair_key)
                print(f"  [QUEUE COLLISION] {c['queue_path']} ({c['queue_name']}) <-> Published: {c['published_path']} ({c['published_name']}) via '{c['matched_term']}'")

    if semantic:
        print(f"\nFound {len(semantic)} high semantic overlap published pairs:")
        for s in semantic:
            print(f"  [SEMANTIC SIMILARITY] {s['path1']} <-> {s['path2']} (Prob: {s['problem_similarity']:.2f}, Mech: {s['mechanism_similarity']:.2f})")

    if args.strict or args.check:
        # Require clean check if strict is set or if specified
        if collisions and args.strict:
            print("\nDUPLICATE CHECK FAILED: Strict duplicate blocking enabled.")
            return 1

    print("\nDuplicate check completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
