#!/usr/bin/env python3
"""Catalogue identity and relationship resolution. See docs/CITATION-POLICY.md and GOVERNANCE.md."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
REVIEW_WINDOW_DAYS = 180

KIND_BY_FAMILY = {
    "02-code-smells": "smell",
    "03-refactoring": "technique",
    "04-principles-and-laws": "principle",
    "18-anti-patterns": "anti-pattern",
}
LAW_SLUGS = {
    "acid",
    "base",
    "cap-theorem",
    "pacelc-theorem",
    "conway-law",
    "postel-law",
    "law-of-demeter",
}
VALID_KINDS = {"pattern", "smell", "technique", "principle", "law", "anti-pattern"}

# Well known renames of exactly one published entry. family/slug when the slug collides.
EXPLICIT_REFS: dict[str, list[str]] = {
    "extract-method": ["extract-function"],
    "inline-method": ["inline-function"],
    "move-method": ["move-function"],
    "rename-method": ["change-function-declaration"],
    "replace-inheritance-with-delegation": ["replace-subclass-with-delegate"],
    "replace-delegation-with-inheritance": ["replace-superclass-with-delegate"],
    "replace-data-value-with-object": ["replace-primitive-with-object"],
    "guard-clause": ["replace-nested-conditional-with-guard-clauses"],
    "guard-clauses": ["replace-nested-conditional-with-guard-clauses"],
    "pipes-and-filters": ["pipes-filters"],
    "publish-subscribe": ["publisher-subscriber"],
    "publish-subscribe-channel": ["publisher-subscriber"],
    "idempotent-receiver": ["idempotent-consumer"],
    "outbox": ["transactional-outbox"],
    "outbox-pattern": ["transactional-outbox"],
    "load-balancer": ["load-balancing"],
    "backend-for-frontend": ["backends-for-frontends"],
    "backends-for-frontend": ["backends-for-frontends"],
    "retry-with-backoff": ["retry"],
    "mock-object": ["mock"],
    "fake-object": ["fake"],
    "stub-object": ["stub"],
    "spy-object": ["spy"],
    "dummy-object": ["dummy"],
    "yagni": ["you-are-not-gonna-need-it"],
    "ycombinator-yagni": ["you-are-not-gonna-need-it"],
    "dry-principle": ["do-not-repeat-yourself"],
    "dont-repeat-yourself": ["do-not-repeat-yourself"],
    "microservices": ["microservices-architecture"],
    "blackboard": ["blackboard-architecture"],
    "quorum-consensus": ["quorum"],
    "service-per-container": ["service-instance-per-container"],
    "multiple-services-per-host": ["multiple-service-instances-per-host"],
    "golden-master-test": ["golden-master"],
    "contract-testing": ["contract-test"],
    "feature-flag": ["feature-toggle"],
    "feature-flags": ["feature-toggle"],
    "read-through": ["read-through-cache"],
    "write-through": ["write-through-cache"],
    "write-behind": ["write-behind-cache"],
    "multiversion-concurrency-control": ["mvcc"],
    "multi-version-concurrency-control": ["mvcc"],
    "vector-clocks": ["vector-clock"],
    "passkeys-webauthn": ["passkeys-and-webauthn"],
    "csrf-protection": ["csrf-token"],
    "saga-orchestration": ["saga"],
    "interpreter-gof": ["interpreter"],
    "distributed-two-phase-commit": ["two-phase-commit"],
    "strict-two-phase-commit": ["two-phase-commit"],
    "distributed-transaction-2pc": ["two-phase-commit"],
    "react-pattern": ["react"],
    "react-agent-loop": ["react"],
    "tool-use": ["function-calling"],
    "tool-use-function-calling": ["function-calling"],
    "reranker-pattern": ["reranking"],
    "context-window-auto-compaction": ["memory-compaction"],
    "react": ["react-prompting"],
    "domain-events": [
        "10-microservices/domain-event",
        "11-domain-driven-design/domain-event",
    ],
    "strangler-fig-application": ["strangler-fig", "strangler-application"],
    "bounded-buffer": ["09-concurrency/producer-consumer"],
    "client-side-discovery": ["client-side-service-discovery"],
    "command-query-separation": ["separate-query-from-modifier"],
    "conflict-free-replicated-data-type": ["crdt"],
    "context-mapping": ["context-map"],
    "dead-letter-queue": ["dead-letter-channel", "dead-letter-topic"],
    "dry": ["do-not-repeat-yourself"],
    "duplicated-code": ["duplicate-code"],
    "either": ["result-either"],
    "global-mutable-state": ["global-data"],
    "global-state": ["global-data"],
    "gold-plating": ["speculative-generality"],
    "golden-master-testing": ["golden-master"],
    "introduce-explaining-variable": ["extract-variable"],
    "kiss": ["keep-it-simple"],
    "lamport-timestamp": ["lamport-clock"],
    "least-to-most-prompting": ["least-to-most"],
    "log-structured-merge-tree": ["lsm-tree"],
    "mutation-testing": ["mutation-test"],
    "mvc": ["model-view-controller"],
    "option": ["option-maybe"],
    "optional": ["option-maybe"],
    "orchestrator-workers": ["orchestrator-worker"],
    "pipe-and-filter": ["pipes-filters"],
    "plan-and-execute": ["plan-execute"],
    "replace-exception-with-test": ["replace-exception-with-precheck"],
    "result": ["result-either"],
    "rich-domain-model": ["domain-model"],
    "robustness-principle": ["postel-law"],
    "role-based-access-control": ["rbac"],
    "service-per-vm": ["service-instance-per-vm"],
    "shared-mutable-state": ["mutable-data"],
    "strict-two-phase-locking": ["two-phase-locking"],
    "sum-type": ["algebraic-data-type"],
    "whole-value": [
        "06-enterprise-application-architecture/value-object",
        "11-domain-driven-design/value-object",
    ],
    "worker-pool": ["thread-pool"],
    "zero-trust-architecture": ["zero-trust"],
}

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SUFFIXES = ("-pattern", "-architecture", "-principle", "-antipattern")


def norm(value: str) -> str:
    value = value.lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def expected_kind(family: str, slug: str) -> str:
    if family == "04-principles-and-laws" and slug in LAW_SLUGS:
        return "law"
    return KIND_BY_FAMILY.get(family, "pattern")


def entry_id(family: str, slug: str) -> str:
    return f"pat.{family[:2]}.{slug}"


def add_days(iso: str, days: int) -> str:
    start = datetime.strptime(iso, "%Y-%m-%d").date()
    return (start + timedelta(days=days)).isoformat()


def parse_flow_list(raw: str) -> list[str] | None:
    """Parse one YAML flow list. Returns None when the value is not one."""
    text = raw.strip()
    if not (text.startswith("[") and text.endswith("]")):
        return None
    inner = text[1:-1].strip()
    if not inner:
        return []
    parts: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for ch in inner:
        if quote:
            if ch == quote:
                quote = None
            else:
                buf.append(ch)
            continue
        if ch in ("'", '"'):
            quote = ch
            continue
        if ch == ",":
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if quote:
        return None
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return [part for part in parts if part]


def format_flow(items: list[str]) -> str:
    return "[" + ", ".join(items) + "]"


def field_map(block: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        key, _, value = line.partition(":")
        found[key.strip()] = value.strip()
    return found


@dataclass
class Entry:
    path: Path
    rel: str
    family: str
    slug: str
    name: str
    text: str
    fields: dict[str, str] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)

    @property
    def ref_qualified(self) -> str:
        return f"{self.family}/{self.slug}"


@dataclass
class Index:
    root: Path
    entries: list[Entry]
    by_slug: dict[str, list[Entry]]
    by_norm: dict[str, list[Entry]]
    by_rel: dict[str, Entry]


def load_entries(root: Path) -> list[Entry]:
    patterns = root / "patterns"
    found: list[Entry] = []
    if not patterns.exists():
        return found
    for path in sorted(patterns.rglob("*.md")):
        if path.name.lower() in {"readme.md", "index.md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        match = FRONTMATTER.match(text)
        if not match:
            continue
        fields = field_map(match.group(1))
        slug = fields.get("slug", "").strip("'\"")
        family = path.parent.name
        aliases = parse_flow_list(fields.get("aliases", "[]")) or []
        rel = path.relative_to(root).as_posix()
        found.append(
            Entry(
                path=path,
                rel=rel,
                family=family,
                slug=slug,
                name=fields.get("name", "").strip("'\""),
                text=text,
                fields=fields,
                aliases=aliases,
            )
        )
    return found


def build_index(root: Path, entries: list[Entry] | None = None) -> Index:
    rows = entries if entries is not None else load_entries(root)
    by_slug: dict[str, list[Entry]] = {}
    by_norm: dict[str, list[Entry]] = {}
    by_rel: dict[str, Entry] = {}
    for entry in rows:
        by_slug.setdefault(entry.slug, []).append(entry)
        by_rel[entry.rel] = entry
        keys = {norm(entry.slug), norm(entry.name)}
        keys.update(norm(alias) for alias in entry.aliases)
        for key in keys:
            if not key:
                continue
            bucket = by_norm.setdefault(key, [])
            if entry not in bucket:
                bucket.append(entry)
    return Index(
        root=root, entries=rows, by_slug=by_slug, by_norm=by_norm, by_rel=by_rel
    )


def qualify(entry: Entry, index: Index) -> str:
    if len(index.by_slug.get(entry.slug, [])) == 1:
        return entry.slug
    return entry.ref_qualified


def _lookup_slug(index: Index, slug: str) -> list[Entry]:
    return list(index.by_slug.get(slug, []))


def _lookup_qualified(index: Index, ref: str) -> list[Entry]:
    if "/" not in ref:
        return []
    family, _, slug = ref.partition("/")
    return [entry for entry in index.by_slug.get(slug, []) if entry.family == family]


def resolve_token(token: str, source: Entry, index: Index) -> tuple[list[str], str]:
    """Return catalogue refs and the rule that produced them. Empty means a concept."""
    token = token.strip()
    if not token:
        return [], "empty"

    def pack(entries: list[Entry], how: str) -> tuple[list[str], str]:
        kept = [entry for entry in entries if entry.rel != source.rel]
        if not kept:
            return [], "self"
        refs: list[str] = []
        seen: set[str] = set()
        for entry in kept:
            ref = qualify(entry, index)
            if ref not in seen:
                seen.add(ref)
                refs.append(ref)
        return refs, how

    if token in EXPLICIT_REFS:
        found: list[Entry] = []
        for ref in EXPLICIT_REFS[token]:
            found.extend(_lookup_qualified(index, ref) or _lookup_slug(index, ref))
        if found:
            return pack(found, "explicit")

    qualified = _lookup_qualified(index, token)
    if qualified:
        return pack(qualified, "qualified")

    exact = _lookup_slug(index, token)
    if exact:
        return pack(exact, "slug")

    # Do not follow aliases. Short aliases such as pipeline and windowing
    # name a broader idea than the one entry that claimed the word.
    if "-and-" in token:
        folded = token.replace("-and-", "-")
        folded_hits = _lookup_slug(index, folded)
        if len(folded_hits) == 1:
            return pack(folded_hits, "and-fold")

    for suffix in SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            stem = token[: -len(suffix)]
            stem_hits = _lookup_slug(index, stem)
            if len(stem_hits) == 1:
                return pack(stem_hits, "suffix")

    if len(token) >= 8:
        prefixed = [
            entry
            for entry in index.entries
            if entry.family == source.family
            and entry.rel != source.rel
            and (entry.slug == token or entry.slug.startswith(token + "-"))
        ]
        if len(prefixed) == 1:
            return pack(prefixed, "family-prefix")

    return [], "concept"


def split_refs(
    tokens: list[str], source: Entry, index: Index
) -> tuple[list[str], list[str]]:
    refs: list[str] = []
    concepts: list[str] = []
    seen_refs: set[str] = set()
    seen_concepts: set[str] = set()
    for token in tokens:
        found, how = resolve_token(token, source, index)
        if not found:
            if how == "self" or not token or token in seen_concepts:
                continue
            seen_concepts.add(token)
            concepts.append(token)
            continue
        for ref in found:
            if ref not in seen_refs:
                seen_refs.add(ref)
                refs.append(ref)
    return refs, concepts


def git_commit_date(root: Path, rel: str) -> str | None:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", rel],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if ISO_DATE.fullmatch(value):
        return value
    return None


def reviewed_dates(fields: dict[str, str], rel: str, root: Path) -> tuple[str, str]:
    verified = fields.get("verified", "").strip("'\"")
    if not ISO_DATE.fullmatch(verified):
        verified = git_commit_date(root, rel) or ""
    last = fields.get("last_reviewed", "").strip("'\"")
    if not ISO_DATE.fullmatch(last):
        last = verified
    due = fields.get("next_review_due", "").strip("'\"")
    if not ISO_DATE.fullmatch(due) and ISO_DATE.fullmatch(last):
        due = add_days(last, REVIEW_WINDOW_DAYS)
    return last, due


def _set_line(lines: list[str], key: str, value: str, after: tuple[str, ...]) -> None:
    rendered = f"{key}: {value}"
    for index, line in enumerate(lines):
        # Exact key. startswith("related:") also matches related_concepts.
        if line.split(":", 1)[0] == key:
            lines[index] = rendered
            return
    insert_at = len(lines)
    for index, line in enumerate(lines):
        name = line.split(":", 1)[0]
        if name in after:
            insert_at = index + 1
    lines.insert(insert_at, rendered)


def rewrite_text(entry: Entry, index: Index) -> str:
    match = FRONTMATTER.match(entry.text)
    if not match:
        return entry.text
    lines = match.group(1).splitlines()
    related = parse_flow_list(entry.fields.get("related", "[]")) or []
    incompatible = parse_flow_list(entry.fields.get("incompatible_with", "[]")) or []
    old_related_concepts = (
        parse_flow_list(entry.fields.get("related_concepts", "[]")) or []
    )
    old_incompatible_concepts = (
        parse_flow_list(entry.fields.get("incompatible_concepts", "[]")) or []
    )
    related_refs, related_concepts = split_refs(
        related + old_related_concepts, entry, index
    )
    incompatible_refs, incompatible_concepts = split_refs(
        incompatible + old_incompatible_concepts, entry, index
    )
    verified = entry.fields.get("verified", "").strip("'\"")
    repaired = (
        verified
        if ISO_DATE.fullmatch(verified)
        else (git_commit_date(index.root, entry.rel) or "")
    )
    if repaired and repaired != verified:
        _set_line(lines, "verified", repaired, ("maturity", "family", "slug"))
    last, due = reviewed_dates(
        {**entry.fields, "verified": repaired}, entry.rel, index.root
    )
    _set_line(lines, "id", entry_id(entry.family, entry.slug), ("slug",))
    _set_line(lines, "kind", expected_kind(entry.family, entry.slug), ("id", "slug"))
    _set_line(
        lines, "related", format_flow(related_refs), ("maturity", "aliases", "family")
    )
    _set_line(lines, "related_concepts", format_flow(related_concepts), ("related",))
    _set_line(
        lines,
        "incompatible_with",
        format_flow(incompatible_refs),
        ("related_concepts", "related"),
    )
    _set_line(
        lines,
        "incompatible_concepts",
        format_flow(incompatible_concepts),
        ("incompatible_with",),
    )
    if last:
        _set_line(lines, "last_reviewed", last, ("verified",))
    if due:
        _set_line(lines, "next_review_due", due, ("last_reviewed", "verified"))
    body = entry.text[match.end() :]
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def ref_exists(token: str, index: Index) -> bool:
    if "/" in token:
        return bool(_lookup_qualified(index, token))
    return len(index.by_slug.get(token, [])) == 1


def identity_errors(entry: Entry, index: Index) -> list[str]:
    errors: list[str] = []
    fields = entry.fields
    if entry.slug != entry.path.stem:
        errors.append(
            f"slug '{entry.slug}' does not match filename '{entry.path.stem}'"
        )
    family_field = fields.get("family", "").strip("'\"")
    if family_field != entry.family:
        errors.append(
            f"frontmatter family '{family_field}' does not match directory '{entry.family}'"
        )
    wanted_id = entry_id(entry.family, entry.slug)
    if fields.get("id", "").strip("'\"") != wanted_id:
        errors.append(f"id must be {wanted_id}")
    wanted_kind = expected_kind(entry.family, entry.slug)
    kind = fields.get("kind", "").strip("'\"")
    if kind != wanted_kind:
        errors.append(f"kind must be {wanted_kind} for this family")
    if kind and kind not in VALID_KINDS:
        errors.append(f"invalid kind '{kind}'")
    for key in ("verified", "last_reviewed", "next_review_due"):
        value = fields.get(key, "").strip("'\"")
        if not ISO_DATE.fullmatch(value):
            errors.append(f"{key} must be a YYYY-MM-DD date, found '{value}'")
    last = fields.get("last_reviewed", "").strip("'\"")
    due = fields.get("next_review_due", "").strip("'\"")
    verified = fields.get("verified", "").strip("'\"")
    if ISO_DATE.fullmatch(last) and ISO_DATE.fullmatch(due) and due < last:
        errors.append("next_review_due is earlier than last_reviewed")
    if ISO_DATE.fullmatch(verified) and ISO_DATE.fullmatch(last) and last < verified:
        errors.append("last_reviewed is earlier than verified")
    for key in ("related", "incompatible_with"):
        raw = fields.get(key)
        if raw is None:
            errors.append(f"frontmatter missing {key}")
            continue
        items = parse_flow_list(raw)
        if items is None:
            errors.append(f"{key} must be a single-line flow list")
            continue
        for item in items:
            if not ref_exists(item, index):
                errors.append(f"{key} ref does not resolve to one entry: {item}")
    for key in ("related_concepts", "incompatible_concepts"):
        raw = fields.get(key, "[]")
        items = parse_flow_list(raw)
        if items is None:
            errors.append(f"{key} must be a single-line flow list")
            continue
        for item in items:
            refs, how = resolve_token(item, entry, index)
            if refs and how != "self":
                errors.append(
                    f"{key} names '{item}', which resolves to {refs}. "
                    "Move it into the matching ref list."
                )
    return errors


def markdown_link_errors(path: Path, text: str, root: Path) -> list[str]:
    errors: list[str] = []
    inside = False
    kept: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            kept.append(line)
    body = re.sub(r"`[^`\n]+`", "", "\n".join(kept))
    root_resolved = root.resolve()
    for target in LINK_RE.findall(body):
        target = target.strip()
        if target.startswith(("<", "http://", "https://", "mailto:", "#")):
            continue
        path_part = target.split("#", 1)[0].strip()
        if not path_part:
            continue
        dest = (path.parent / path_part).resolve()
        try:
            dest.relative_to(root_resolved)
        except ValueError:
            errors.append(f"link escapes the repository: {target}")
            continue
        if not dest.exists():
            errors.append(f"broken internal link: {target}")
    return errors


def applicability_excerpt(text: str, limit: int = 320) -> str:
    """First slice of the Applicability section, for the machine-readable export."""
    collecting = False
    fence = False
    buf: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if line.startswith("## ") and "applicab" in line.lower():
            collecting = True
            continue
        if collecting and line.startswith("## "):
            break
        if collecting:
            buf.append(line.strip())
    prose = re.sub(r"\s+", " ", " ".join(part for part in buf if part)).strip()
    if len(prose) <= limit:
        return prose
    cut = prose[:limit]
    dot = cut.rfind(". ")
    if dot >= 80:
        return cut[: dot + 1]
    space = cut.rfind(" ")
    if space >= 80:
        return cut[:space]
    return cut
