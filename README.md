# Patterns

A master level reference for software patterns. Every entry is written from
primary sources, carries eighteen mandatory dimensions, and cites every claim.

![License](https://img.shields.io/badge/license-CC%20BY%204.0-blue)
![Families](https://img.shields.io/badge/families-29-informational)
![Entries](https://img.shields.io/badge/entries-299%20published%20%2F%20887%20planned-yellow)
![Dimensions per entry](https://img.shields.io/badge/dimensions%20per%20entry-18-green)
![Citations](https://img.shields.io/badge/citations-verified%20in%20CI-brightgreen)
![Original prose](https://img.shields.io/badge/prose-100%25%20original-brightgreen)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-blueviolet)

<!-- BADGES:AUTOGEN:START -->
![CI](https://github.com/mjmirza/patterns/actions/workflows/ci.yml/badge.svg?branch=main)
![Schema version](https://img.shields.io/badge/schema-v1.0-informational)
![Published entries](https://img.shields.io/badge/published-299-brightgreen)
![Planned entries](https://img.shields.io/badge/planned-588-lightgrey)
![Catalogue completion](https://img.shields.io/badge/completion-33.7%25-yellow)
![References checked](https://img.shields.io/badge/references%20checked-1806-brightgreen)
![Stale entries](https://img.shields.io/badge/stale%20entries-0-brightgreen)
![Code examples tested](https://img.shields.io/badge/code%20examples-compiled%20in%20CI-brightgreen)
<!-- BADGES:AUTOGEN:END -->

There is no documentation site yet (no rendered docs build to badge). Tracked
as an open item in `docs/GOVERNANCE-AUDIT-2026-08-03.md`.

## What this is

A reference you can hand to a staff engineer and have them find something they
did not know. Not a tutorial. Not an overview. Not a set of one paragraph
summaries with a UML picture.

Most pattern catalogues answer one question. What is this pattern. This one
answers the eighteen questions an engineer actually has when they are
deciding whether to use it, how it will fail, what it costs, how to test it,
how to see it in production, and how to remove it later.

## What makes an entry master level

Every entry carries all eighteen dimensions. An entry missing one is not
merged. This is checked mechanically by `tools/check-structure.py` in CI, not
by good intentions.

| # | Dimension | The question it answers |
|---|---|---|
| 1 | Name, aliases, lineage | What is it called, by whom, since when |
| 2 | Problem and context | What situation creates the need |
| 3 | Forces | Which pressures it balances and which it sacrifices |
| 4 | Applicability and non-applicability | When to reach for it, and when NOT to |
| 5 | Structure | Participants, responsibilities, relationships |
| 6 | ASCII structure diagram | The shape, readable in a terminal |
| 7 | Dynamics | How the parts interact at runtime |
| 8 | Implementation variants | The real ways it gets built |
| 9 | Known production uses | Named systems, with sources |
| 10 | Consequences | The good and the cost, both listed |
| 11 | Failure modes and misuse | How it breaks, and how people get it wrong |
| 12 | Trade-off matrix | How it compares to named alternatives |
| 13 | Related and incompatible patterns | What composes, what conflicts |
| 14 | Refactoring path in and out | How to adopt it, and how to leave |
| 15 | Testing and verification | What got easier to test, what got harder |
| 16 | Observability signals | What to log, trace, and measure |
| 17 | Security and privacy | What surface it opens or closes |
| 18 | References | Every claim, independently checkable |

Dimension 4's second list and dimension 11 are the ones most catalogues skip.
They are the reason this repository exists.

## Terminology

The status words below mean exactly one thing each, and every count in this
README is generated from repository state by `tools/gen-catalogue-status.py`,
never hand-typed. See `docs/PROGRESS.md` and `dist/catalogue-status.json` for
the live, machine-readable numbers.

| Term | Meaning | Enforced by |
|---|---|---|
| Published | A file exists in `patterns/` and passes every CI gate | `tools/check-structure.py` |
| Planned | Named in `docs/AUTHORING-QUEUE.json`, not yet on disk | `tools/next-batch.py` |
| Total catalogue scope | Published plus planned, tracked in `docs/SCOPE-TARGET.json` | manual reconciliation, see that file |
| canonical / established / emerging / contested / deprecated | Per-entry epistemic maturity, declared in frontmatter | `tools/check-structure.py` |

Draft, in-review, and superseded are not yet modelled by the tooling. They
are open work, listed in `docs/GOVERNANCE-AUDIT-2026-08-03.md`, and this
README does not claim they are implemented.

## The families

| # | Family | Origin | Published | Planned | Target |
|---|---|---|---|---|---|
| 01 | [Design Patterns (GoF)](patterns/01-gof/) | Gamma, Helm, Johnson, Vlissides 1994 | 23 | 0 | 23 |
| 02 | [Code Smells](patterns/02-code-smells/) | Fowler and Beck, Refactoring | 28 | 0 | 28 |
| 03 | [Refactoring Techniques](patterns/03-refactoring/) | Fowler, Refactoring 2nd ed | 0 | 66 | 66 |
| 04 | [Principles and Laws](patterns/04-principles-and-laws/) | Martin, Larman, Brewer, Conway | 0 | 50 | 50 |
| 05 | [Architectural Patterns](patterns/05-architectural/) | Buschmann POSA 1, Bass SEI | 7 | 36 | 43 |
| 06 | [Enterprise Application Architecture](patterns/06-poeaa/) | Fowler, PoEAA | 0 | 50 | 50 |
| 07 | [Enterprise Integration](patterns/07-integration/) | Hohpe and Woolf | 0 | 57 | 57 |
| 08 | [Cloud and Distributed](patterns/08-cloud-distributed/) | Azure Architecture Center | 42 | 0 | 42 |
| 09 | [Concurrency and Parallelism](patterns/09-concurrency/) | Schmidt POSA 2 | 0 | 40 | 40 |
| 10 | [Microservices](patterns/10-microservices/) | Richardson | 44 | 6 | 50 |
| 11 | [Domain-Driven Design](patterns/11-ddd/) | Evans, Vernon | 29 | 8 | 37 |
| 12 | [Data and Storage](patterns/12-data-storage/) | Kleppmann | 0 | 43 | 43 |
| 13 | [Frontend and UI](patterns/13-frontend-ui/) | Framework documentation | 0 | 34 | 34 |
| 14 | [Testing](patterns/14-testing/) | Meszaros, xUnit Test Patterns | 30 | 0 | 30 |
| 15 | [Security](patterns/15-security/) | OWASP ASVS | 0 | 38 | 38 |
| 16 | [Functional Programming](patterns/16-functional/) | Category theory in practice | 0 | 40 | 40 |
| 17 | [AI and Agentic](patterns/17-ai-agentic/) | Papers and vendor engineering, 2023 to 2026 | 55 | 0 | 55 |
| 18 | [Anti-Patterns](patterns/18-anti-patterns/) | Brown et al, AntiPatterns | 41 | 12 | 53 |
| 19 | [API and Interface Design](patterns/19-api-design/) | REST, GraphQL, gRPC specifications | 0 | 10 | 10 |
| 20 | [Release and Deployment](patterns/20-release-deployment/) | Humble and Farley | 0 | 10 | 10 |
| 21 | [SRE and Operations](patterns/21-sre-operations/) | Google SRE, AWS Well-Architected | 0 | 12 | 12 |
| 22 | [Observability](patterns/22-observability/) | OpenTelemetry, RED and USE methods | 0 | 8 | 8 |
| 23 | [Workflow and Orchestration](patterns/23-workflow-orchestration/) | Durable execution literature | 0 | 6 | 6 |
| 24 | [Stream Processing](patterns/24-stream-processing/) | Dataflow model, Kafka docs | 0 | 8 | 8 |
| 25 | [MLOps](patterns/25-mlops/) | Google ML design patterns | 0 | 9 | 9 |
| 26 | [Interaction and HCI](patterns/26-interaction-hci/) | Tidwell, Designing Interfaces | 0 | 10 | 10 |
| 27 | [Mobile Architecture](patterns/27-mobile-architecture/) | Official Android/iOS architecture guidance | 0 | 12 | 12 |
| 28 | [Embedded and Hardware-Software](patterns/28-embedded-hardware/) | Embedded systems engineering literature | 0 | 14 | 14 |
| 29 | [Real-Time Simulation](patterns/29-realtime-simulation/) | Nystrom, Game Programming Patterns | 0 | 9 | 9 |

Family 04 is named Principles and Laws rather than patterns, because SOLID,
CAP, and Conway's Law are principles and laws, not patterns. They live here
because a reference without them has a hole, and they are marked as what they
are.

## How to read it

**By problem.** Start at [docs/BY-PROBLEM.md](docs/BY-PROBLEM.md). It maps
symptoms you can observe in a codebase to the patterns that address them.

**By family.** Pick a family above. Each family has an index with a one line
summary per entry.

**By language.** [docs/BY-LANGUAGE.md](docs/BY-LANGUAGE.md) lists which patterns
change shape in which language, and which ones a language makes unnecessary.

**By maturity.** Every entry declares `canonical`, `established`, `emerging`,
`contested`, or `deprecated` in its frontmatter. Emerging and contested entries
state plainly what is unsettled.

## Sourcing and legal position

Every word here is original. Patterns are ideas that belong to the people who
found and named them, and those people are credited in every entry and in
[ATTRIBUTION.md](ATTRIBUTION.md).

No text, diagram, or code sample is copied from any pattern catalogue. Where an
existing catalogue was consulted, it was consulted as a checklist of what a
reader would expect to find, never as a source of prose. This is stated in full
in [ATTRIBUTION.md](ATTRIBUTION.md) along with the licence terms of every
catalogue involved.

If you hold rights in anything here and believe it goes past fair citation,
open an issue titled `attribution` and it will be corrected or removed.

## Quality gates

Nothing merges without passing all of these.

| Gate | Tool | What it blocks |
|---|---|---|
| Structure | `tools/check-structure.py` | A missing dimension, bad frontmatter, fewer than three code languages, under 1200 prose words |
| Citations | `tools/validate-refs.py` | Any cited URL that does not resolve |
| Prose | `tools/check-prose.py` | Em dashes, en dashes, AI slop vocabulary, emojis, triple-dash separators |
| Markdown | `markdownlint-cli2` | Malformed markdown, emphasis used as a heading |
| Code | `tools/check-code.py` | Non-compiling examples (Python, TypeScript, Java, Go, Rust, Swift) |
| Catalogue status | `tools/gen-catalogue-status.py` | A README, `docs/PROGRESS.md`, or `dist/` export that has drifted from real repository state |

A per-file internal link checker does not exist yet. It is tracked in
`docs/GOVERNANCE-AUDIT-2026-08-03.md` as open work, not claimed as done.

Run the whole set locally.

```bash
make check
```

## Contributing

Read [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) first. The short
version.

1. One entry per pull request.
2. All eighteen dimensions, or it is sent back.
3. Original prose. If a sentence could be diffed against a source and match,
   rewrite it.
4. Every claim cited. Every cited URL verified on the day you submit.
5. Production usage names a real system with a real source.

Contributions are licensed under CC BY 4.0.

### Contributing with an AI coding agent

If you use Claude Code, Cursor, Codex, or a similar agent, paste this prompt
into it. It fetches the real rules from this repo rather than trusting a
stale copy of them, and it enforces the branch-first-then-PR workflow this
project requires.

```
You are contributing one entry to github.com/mjmirza/patterns, a master
level software pattern catalogue. Follow these steps exactly, in order.

1. Fork the repo (if you do not already have write access) and clone it.
   Do NOT work directly on main.
2. Read .github/CONTRIBUTING.md, docs/ENTRY-TEMPLATE.md, and one existing
   published entry under patterns/ end to end. These are the real, current
   rules. Do not assume you already know them.
3. Check docs/AUTHORING-PLAN.md for an unclaimed pattern, or pick a pattern
   the maintainer has not catalogued yet.
4. Create a branch named entry/<slug>, for example entry/circuit-breaker.
   Never commit to main.
5. Open a DRAFT pull request immediately, naming only the branch and the
   pattern you intend to write, before writing the entry. This draft PR is
   how you CLAIM the entry so nobody else duplicates your work. CI will
   reject a second PR that claims the same entry.
6. Write the entry to docs/ENTRY-TEMPLATE.md's exact eighteen-dimension
   shape. Original prose only, never paraphrased from a source close enough
   to diff-match it. Every factual claim gets a real, working citation you
   have actually checked, not one you assume exists.
7. Run this repo's own local checks before pushing (see the CI job names in
   .github/workflows/ci.yml for the exact commands: structure, prose, code
   samples, citations, markdown style).
8. Push, mark the PR ready for review, and fill in
   .github/PULL_REQUEST_TEMPLATE.md with real command output, not a claim
   that it passed.
9. Wait. The maintainer (mjmirza) reviews and merges every PR by hand. Do
   not merge your own PR, do not force-push over review feedback without
   discussion, and do not touch .github/workflows/ or any other
   CI-controlling file, those changes are blocked for anyone without the
   maintainer's 'security-reviewed' label.

If anything in this prompt conflicts with the actual .github/CONTRIBUTING.md
in the repo, the file in the repo wins, not this prompt.
```

### Authoring plan and progress

See [docs/AUTHORING-PLAN.md](docs/AUTHORING-PLAN.md) for the family by family
authoring order and the current state of each family.

## Credits

Built by [Mirza Iqbal](https://github.com/mjmirza).

The patterns catalogued here were discovered and named by the authors listed in
[ATTRIBUTION.md](ATTRIBUTION.md). This repository documents their work. It does
not claim it.

## License

Content is licensed under
[Creative Commons Attribution 4.0 International](LICENSE).

Use it, adapt it, sell work built on it. Give credit and link back.

```text
"Patterns" by Mirza Iqbal, CC BY 4.0
https://github.com/mjmirza/patterns
```
