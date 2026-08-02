# Entry Template. The Master Level Contract

Every pattern entry in this repository carries all 18 dimensions below. An entry
missing a dimension is not finished. This is the single difference between a
master reference and a getting started overview, and it is enforced by
`tools/check-structure.py` in CI.

## Hard rules for every entry

1. **Original prose only.** Never copy or closely paraphrase a source. Read the
   source, understand the pattern, write the explanation yourself. If a sentence
   could be diffed against a source and match, rewrite it.
2. **Every factual claim carries a citation.** Book claims cite author, title,
   edition, and page or chapter. Web claims cite the full URL plus the date the
   page was verified. No citation means the claim does not ship.
3. **ASCII diagrams live inside fenced code blocks only.** Never in prose.
4. **No em dashes, no en dashes, no decorative colons.** Periods and commas.
5. **Real production usage must name a real system**, with a source. "Used in
   many web frameworks" is not acceptable. "Used by the Java Servlet filter
   chain, see the Jakarta Servlet 6.0 specification section 6.2" is.
6. **Trade-off tables compare against named alternatives**, never against a
   generic "the naive approach".

## Required frontmatter

````markdown
---
name: Chain of Responsibility
slug: chain-of-responsibility
family: 01-gof
category: Behavioral
aliases: [Chain of Command, Responsibility Chain]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [command, composite, decorator, mediator]
incompatible_with: []
verified: 2026-08-02
---
````

`maturity` is one of `canonical`, `established`, `emerging`, `contested`,
`deprecated`. Emerging and contested entries must say plainly in the body what
is not yet settled.

## The 18 dimensions, in order

### 1. Name, aliases, and lineage
Canonical name. Every alias in real use. Who first described it, in which
publication, in which year, with the citation. If the name is contested or the
pattern is known by a different name in another community, say so here.

### 2. Problem and context
The concrete situation that creates the need. Written so a reader who has never
heard the pattern name can recognise the problem in their own codebase. State
the context in which the problem arises, because a pattern outside its context
is an anti-pattern.

### 3. Forces
The competing pressures the pattern balances. At minimum consider latency,
coupling, consistency, operability, cost, team topology, and cognitive load.
Say which forces the pattern favours and which it sacrifices. A pattern that
sacrifices nothing is described wrongly.

### 4. Applicability and non-applicability
Two lists. When to reach for it. When NOT to, with the reason. The second list
is the more valuable one and is the one most catalogs omit.

### 5. Structure
Participants with their responsibilities, and the relationships between them.
Name each participant with the role it plays, not with a generic class name.

### 6. ASCII structure diagram
Inside a fenced code block. Boxes and arrows showing the participants and their
relationships. Must be readable in a plain terminal at 80 columns.

### 7. Dynamics
How the participants interact at runtime. A sequence flow, a state transition,
or an event flow, whichever fits. Also inside a fenced code block when drawn.

### 8. Implementation variants
The real ways this pattern is built in practice, with the trade-off of each.
Include the language-idiomatic variants where a language changes the shape,
for example a closure replacing a Strategy class.

### 9. Known production uses
Named systems, libraries, frameworks, or standards, each with a source. At least
two. This is the dimension that proves the pattern is real and not academic.

### 10. Consequences
Positive and negative, as two explicit lists. Every pattern has a cost. Name it.

### 11. Failure modes and misuse
How this pattern breaks in production, and how people misuse it. Include the
symptom a reader would actually observe, not the abstract mistake alone.

### 12. Trade-off matrix
A table comparing this pattern against its named alternatives across the forces
from dimension 3. The alternatives must be named patterns, not strawmen.

### 13. Related and incompatible patterns
Which patterns compose with this one, which ones replace it, and which ones
actively conflict with it. Explain the relationship, never a bare list of names.

### 14. Refactoring path in and out
How to introduce this pattern into code that does not have it, step by step.
And how to remove it when it stops earning its place. Cross reference the
refactoring family where a named refactoring applies.

### 15. Testing and verification
How to test code that uses this pattern. What is easy to test because of it,
and what became harder. Name the test doubles or techniques that apply.

### 16. Observability signals
What to log, trace, or measure so this pattern is visible in production. What a
healthy instance looks like on a dashboard, and what a failing one looks like.

### 17. Security and privacy implications
The attack surface the pattern opens or closes. Data handling implications.
Where it is silent, say so plainly rather than inventing a concern.

### 18. References
Every source used, with author, title, edition or version, page or section, URL
where one exists, and the date the URL was verified. Sources must be
independently checkable by a reader.

## Code examples

Every entry carries working code in at least three languages from this set.
TypeScript, Python, Java, Go, Rust, C#, Swift, Kotlin. Choose the languages
where the pattern is genuinely idiomatic, and say why a language is omitted when
the pattern does not translate.

Code is original, minimal, and runnable. No framework scaffolding. No comment
longer than two lines, per the repository comment policy.

## What a reviewer rejects

An entry is sent back when any of these is true.

1. A dimension is missing or is a single filler sentence.
2. A claim has no citation, or a citation does not resolve.
3. Production usage is unnamed or unsourced.
4. The trade-off table compares against a strawman.
5. The prose reads as a paraphrase of a single source.
6. The ASCII diagram sits outside a fenced code block.
7. The entry omits the non-applicability list.

## Scope decision, recorded 2026-08-02

Every entry in this repository is authored at full depth. All eighteen
dimensions, every entry, no exceptions and no lighter class of entry.

A tiered model was considered and rejected by the repository owner. The trade
was roughly 200 deep entries plus 700 lighter ones against 900 deep entries.
The owner chose 900 deep entries with the cost visible. This note exists so the
decision is not silently re-litigated later by a contributor who finds the
authoring effort large.

## Judgement versus sourced claim

Not every sentence in an entry can carry a citation, and pretending otherwise
produces fake citations. The rule is honest labelling, not universal sourcing.

**Must be sourced.** Anything a reader could check and find wrong.

1. Who named the pattern, when, and in which publication.
2. Any statement about what a named library, language, or specification does.
3. Any named production use.
4. Any claim about a language feature, a memory model, or an API contract.
5. Any historical or attribution claim, including "X called this an anti-pattern".

**May be engineering judgement.** State it as reasoning, never dress it as fact.

1. Dimension 3, forces, where you weigh which pressure dominates.
2. Dimension 10, consequences, where the cost is a matter of degree.
3. Dimension 11, failure modes, where the symptom is drawn from experience.
4. Dimension 15, testing, and dimension 16, observability, which are practice.
5. Dimension 17, security, where the implication is analytical.

An entry that presents judgement as a sourced fact is worse than an entry with
fewer citations. When a dimension is largely judgement, say so in one line at
the top of that dimension so the reader can weigh it accordingly.

## Available toolchains

Compile or run every sample you can, and state plainly which you could not.

| Language | Availability |
|---|---|
| Python | `python3`, present |
| Go | `go`, present |
| TypeScript | via `npx tsc`, present |
| JavaScript | `node`, present |
| Swift | `swiftc`, present |
| Java | `javac`, being installed, check before assuming |
| Rust | `rustc`, being installed, check before assuming |
| C#, Kotlin | not installed, hand-check and say so |

A sample you could not compile is still acceptable. Silently implying you did
compile it is not.
