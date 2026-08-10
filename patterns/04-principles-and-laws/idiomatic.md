---
name: Idiomatic
slug: idiomatic
family: 04-principles-and-laws
category: Principle
aliases: [Idiomatic Code, Pythonic, Go-like, Rustic, Idiom Compliance]
first_described: "Kernighan and Plauger 1974, formalized per-language from the 1990s onward"
maturity: canonical
related: [convention-over-configuration, principle-of-least-astonishment, kiss, yagni]
incompatible_with: []
verified: 2026-08-02
---

# Idiomatic

## 1. Name, aliases, and lineage

The principle carries no single canonical citation the way a Gang of Four
pattern does, because it predates and outlives any one publication. It is a
property, not a pattern. Code is idiomatic when it is written the way
experienced practitioners of a given language and community actually write
that language, using the constructs, naming conventions, and structural habits
that language's own standard library, tooling, and influential authors have
converged on, rather than a construction that merely compiles and produces the
correct output.

The earliest widely cited articulation of the underlying idea is Brian
Kernighan and P. J. Plauger, *The Elements of Programming Style*, 2nd edition,
McGraw-Hill, 1978, which catalogued recurring bad habits translated wholesale
from one language's habits into another and argued that code should be written
in the natural grain of the language it is written in, not in a dialect of
whatever language the author learned first. The book predates the word
"idiomatic" being applied to source code in the sense used here, but its
central argument, that a construct correct in FORTRAN is often wrong in PL/I
because it fights the second language's natural expression, is the same
argument every later per-language style guide restates.

The word itself entered common software usage through per-language style
literature in the 1990s and 2000s, each community independently choosing to
name the same property. Effective Go, the language team's own guide, states
plainly that a straightforward translation of a C++ or Java program into Go
is unlikely to produce a satisfactory result, because Java programs are
written in Java, not Go, and that writing Go well requires understanding
"its properties and idioms" (The Go Authors, *Effective Go*,
<https://go.dev/doc/effective_go>, verified 2026-08-02). Python's community
uses the adjective "Pythonic" for the same property, and Tim Peters codified
the value system behind it as *The Zen of Python*, later ratified as PEP 20
(Tim Peters, "PEP 20, The Zen of Python", 2004,
<https://peps.python.org/pep-0020/>, verified 2026-08-02), which opens with
"Beautiful is better than ugly. Explicit is better than implicit. Simple is
better than complex" and states "There should be one, and preferably only
one, obvious way to do it." Joshua Bloch's *Effective Java* (3rd edition,
Addison-Wesley, 2018) is the equivalent canon for Java, and the Rust API
Guidelines (Rust language team, <https://rust-lang.github.io/api-guidelines/>,
verified 2026-08-02) are the equivalent formal specification for Rust,
distinguished from the others by being partly machine-checked rather than
purely advisory prose.

There is no single alias in universal use across languages. "Pythonic" and
"Go-like" or "idiomatic Go" are the terms practitioners actually say aloud,
while "idiomatic" is the umbrella word used when speaking about the property
in general, language-agnostic terms, which is the sense this entry documents.

## 2. Problem and context

A person who learns to program in one language carries that language's mental
model into every language learned afterward. The habits are not wrong in
themselves, they were correct in the first language, but they become friction
in the second. A Java or C# programmer moving to Go tends to write getters and
setters for every field, wrap collection iteration in verbose index loops out
of habit, and reach for interface hierarchies before they are needed. A C or
C++ programmer moving to Python tends to write explicit loop-and-index code
where a comprehension or a built-in like `enumerate` would say the same thing
in a fifth of the tokens and in a shape every other Python reader recognises
on sight. Kernighan and Plauger's 1978 examples are drawn from exactly this
failure, FORTRAN habits producing bad PL/I, and the same failure recurs every
time a language changes but the author's habits do not.

The context in which idiom compliance matters is any codebase read and
modified by more than one person, or by the same person after enough time has
passed that they are effectively a stranger to their own code. In that
context a reader's comprehension speed depends heavily on pattern matching
against constructs they have seen thousands of times in the standard library,
in open source dependencies, and in other code at the same company. A
correct but non-idiomatic construct forces the reader to parse it from first
principles instead of recognising it, which is measurably slower and a
documented source of code review friction and onboarding cost, discussed
further in dimension 3.

Idiom compliance is not a claim that all idioms are objectively superior in
every dimension. A hand-rolled loop is sometimes faster than the idiomatic
higher-order function it replaces, and an idiomatic getter-free Go struct is
sometimes less convenient for a specific serialization library than a getter
would be. The principle is that the default choice, absent a measured reason
to deviate, should be the construction the language's own community has
converged on, because that convergence carries information. Thousands of
practitioners have already weighed the trade-off for the common case and
settled on an answer, and re-litigating that answer inside one codebase costs
more than it returns unless the specific case genuinely differs from the
common one.

## 3. Forces

**Readability for the community versus readability for the individual.** The
author of a piece of code may find their own non-idiomatic construction
perfectly readable, because they wrote it and hold its shape in working
memory. A reader encountering it cold does not have that advantage and must
reconstruct the author's reasoning from the code alone. Idiom compliance
optimizes for the population of future readers, most of whom the author will
never meet, at some cost to the author's momentary comfort with their own
preferred style.

**Familiarity transfer versus local optimization.** A construct that matches
the language's idiom transfers a reader's existing knowledge from every other
idiomatic codebase they have read, including the standard library and the
language's own documentation. A locally optimized, non-idiomatic construct
might genuinely be faster or more compact for this one call site, but that
gain does not transfer, the reader has to relearn it here and only here.

**Onboarding cost versus individual choice.** New team members onboard by
pattern-matching against what they already know from wider practice. Every
place a codebase diverges from that shared idiom is a place a newcomer must
be explicitly taught rather than being able to infer from prior experience.
The cost compounds with team size and turnover. Weighed against this is a
team's legitimate desire to establish a house style that expresses genuine
local priorities, discussed as its own related principle in dimension 13.

**Tooling automation versus manual judgement.** Some languages, most visibly
Go with `gofmt` and Rust with `rustfmt` and `clippy::style`, have made large
portions of idiom compliance a mechanical, non-negotiable property of the
toolchain rather than a matter of taste. `gofmt`'s documentation states that
all Go code in the standard packages has been formatted with `gofmt` (The Go
Authors, *Effective Go*, <https://go.dev/doc/effective_go>, verified
2026-08-02), removing formatting idiom from human judgement entirely. Other
languages, notably JavaScript and to a lesser degree Python before Black's
wide adoption, historically left far more of idiom to manual judgement and
convention documents, which increases the force of enforcement cost, since
someone has to notice and flag the deviation by hand.

**Cost of the deviation versus cost of the migration.** Once a codebase has
accumulated a large amount of non-idiomatic code in a consistent
non-idiomatic style of its own, converting it to the wider community's idiom
is a real cost with real regression risk, and the argument for leaving it
alone grows every year the codebase survives. Idiom compliance is cheapest
when enforced from the first commit and grows more expensive the longer a
divergent local style is allowed to compound.

This entry weighs judgement, the balance of these forces in a given team, as
practitioner reasoning rather than sourced fact, except where a specific
document is quoted directly.

## 4. Applicability and non-applicability

Reach for idiom compliance as the default when the following hold.

- The code will be read or modified by more than one person, now or in the
  foreseeable future, including the author's own future self.
- The team hires or expects to hire from the wider language community and
  therefore benefits from shared, transferable pattern recognition.
- A language-official or community-canonical style guide and formatter
  exist and are actively maintained, for example Go's `gofmt`, Rust's
  `rustfmt` plus `clippy`, Python's PEP 8 plus Black, or Java's Google Java
  Format.
- The team is porting or translating code from one language to another and
  needs a check against carrying the source language's idiom into the
  target language, which is exactly the failure Kernighan and Plauger
  documented.
- Code review time and onboarding time are scarce resources the team wants
  to protect, since idiomatic code reduces both.

Do NOT chase idiom compliance, or apply it only with restraint, in these
cases.

- The idiom itself is contested or actively shifting inside the language
  community. Forcing premature convergence on an unsettled idiom locks a
  codebase into a style the community may later abandon. Python's own
  history with percent-style string formatting versus `.format()` versus
  f-strings is an example of an idiom that genuinely changed across
  language versions, and code written idiomatically for Python 2 read as
  dated, not idiomatic, in Python 3.6 and later.
- The non-idiomatic construction is a deliberate, measured performance or
  correctness trade-off documented at the call site, for example an
  index-based loop chosen over an idiomatic iterator because a profiler
  showed the iterator's bounds-check overhead mattered in a hot path. The
  idiom is a strong default, not an absolute rule, and dimension 10 records
  the corresponding cost of blind adherence.
- The codebase is a small, single-author script never intended to be read
  by anyone else and never intended to outlive the task, where the cost of
  idiom compliance exceeds any benefit it would return.
- Following the target language's idiom would require abandoning a
  cross-language internal library or code-generation pipeline the team
  depends on for reasons unrelated to this one language, for example a
  generated client whose shape is dictated by a schema compiler rather than
  by hand-authored idiom.
- The "idiomatic" construction being proposed is in fact a cargo-culted
  pattern borrowed from a different language and merely dressed in the
  target language's syntax, which is discussed further as a failure mode in
  dimension 11 and is the opposite of genuine idiom compliance even though
  it is frequently defended using the same vocabulary.

## 5. Structure

Idiom compliance is not a single participant acting on a single object, it is
a relationship among four elements that must all be present for the property
to be reliably enforceable rather than aspirational.

- **The idiom itself.** The specific construct, naming convention, or
  structural pattern the language community has converged on for a given
  problem, for example returning an optional value rather than a sentinel,
  using a comprehension rather than a manual accumulator loop for a simple
  map or filter, or naming a getter without a `get_` prefix in Rust.
- **The canonical source.** The document, tool, or body of code the
  community treats as authoritative for what counts as idiomatic, which may
  be an official style guide (Effective Go, PEP 8), an authoritative book
  (Effective Java), a machine-checked ruleset (Rust API Guidelines,
  `clippy::style`), or, absent any of those, the observed convention of the
  language's own standard library and most-starred open source projects.
- **The enforcement mechanism.** The thing that actually catches a deviation
  and surfaces it to a human, whether an automatic formatter that rewrites
  the code (`gofmt`, `rustfmt`, Black), a linter that warns without
  rewriting (`clippy`, `golangci-lint`, `pylint`, ESLint with a
  style-focused configuration such as the Airbnb JavaScript style guide's
  shareable config), or a human code reviewer applying the canonical
  source from memory.
- **The deviation and its context.** The specific piece of code under
  review, and the local reason, if any, that it diverges from the idiom.
  Idiom compliance is a judgement made against this specific context, not a
  context-free grep for a forbidden token.

The relationship among these four is what distinguishes idiom compliance from
a simple lint rule. A lint rule is one narrow instantiation of the
enforcement mechanism, applied against one narrow instantiation of the idiom,
and idiom compliance as a whole is the sum of every such instantiation a
community has agreed on, plus the human judgement that fills the gaps no
automated tool covers.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                     LANGUAGE COMMUNITY                      |
|  (converges on shared conventions over years of practice)   |
+-------------------------------------------------------------+
                 |
                 |  distills into
                 v
+-------------------------+     +---------------------------+
|   CANONICAL SOURCE      |     |   STANDARD LIBRARY /       |
|   (Effective Go, PEP 8, | <-->|   INFLUENTIAL OPEN SOURCE   |
|   Rust API Guidelines,  |     |   (the idiom made concrete) |
|   Effective Java)       |     +---------------------------+
+-------------------------+
                 |
                 |  operationalized by
                 v
+-------------------------+     +---------------------------+
|  ENFORCEMENT MECHANISM  |     |   HUMAN CODE REVIEWER      |
|  (gofmt, rustfmt,       | <-->|   (applies canonical source |
|  clippy::style, Black,  |     |   to cases tools cannot     |
|  golangci-lint)         |     |   see, e.g. naming intent)   |
+-------------------------+     +---------------------------+
                 |
                 |  is checked against
                 v
+---------------------------------------------------------+
|                CANDIDATE CODE UNDER REVIEW               |
|  Idiomatic  <-------- deviation --------> Non-idiomatic  |
|  (matches shape reader already                            |
|   recognises from wide practice)     (correct but foreign  |
|                                        shape, forces the    |
|                                        reader to parse from |
|                                        first principles)    |
+---------------------------------------------------------+
```

## 7. Dynamics

The runtime dynamic of idiom compliance is really a review-time dynamic, since
the property is evaluated by readers rather than by the running program. The
typical flow, in a team that has automated as much of it as their language
allows, moves through five stages.

```
Author writes code
        |
        v
Save-time / pre-commit formatter runs (gofmt, rustfmt, Black)
        |
        +--> Formatter rewrites whitespace, import order,
        |    brace placement mechanically. No human judgement
        |    needed for this layer. Author cannot deviate
        |    even if they want to.
        v
CI lint step runs (clippy, golangci-lint, pylint, ESLint)
        |
        +--> Flags idiom deviations the formatter cannot fix,
        |    such as preferring an iterator adapter to a manual
        |    loop, or preferring an optional value to a null
        |    check. Author fixes or justifies with an explicit
        |    suppression plus a comment.
        v
Human code review
        |
        +--> Reviewer applies canonical source from memory for
        |    the residual cases no tool catches, whether this is
        |    the conventional name for the concept, the
        |    conventional error-handling shape, or whether it
        |    reads the way a reader who knows the language's
        |    conventions expects.
        v
Merge, or request changes citing the canonical source
```

Where a language has strong automated tooling (Go, Rust), the human-judgement
layer at the bottom shrinks to genuinely subjective residue such as naming
choices and API shape. Where a language has weak or optional tooling
(historically JavaScript before ESLint configs matured, C++ across its many
competing style guides), the human-judgement layer carries almost the entire
weight, and idiom compliance becomes far more dependent on reviewer knowledge
and team discipline than on the toolchain.

## 8. Implementation variants

Idiom compliance takes a materially different shape in each language,
because each language's idiom is different and each language's tooling
support for enforcing it is at a different level of maturity.

- **Go.** The strongest case of mechanical enforcement in mainstream use.
  `gofmt` fixes all whitespace, brace, and import-order idiom automatically
  and is treated as non-optional by the community, since deviating from
  `gofmt` output is itself considered non-idiomatic. `go vet` and
  `golangci-lint` catch a further layer, for example unchecked error
  returns and non-idiomatic naming of one-method interfaces (the "-er"
  suffix convention documented in Effective Go). What remains to human
  judgement is mostly API shape, whether to return an error as the second
  value (idiomatic) versus a boolean ok-flag (idiomatic only in a narrower
  set of cases, such as map lookups) versus a panic (rarely idiomatic
  outside programmer-error conditions).
- **Rust.** Idiom compliance is partly codified as a machine-checked
  document, the Rust API Guidelines, with individual guideline codes such
  as C-CASE for casing and C-CONV for conversion-method prefixes
  (`as_`, `to_`, `into_`), each with a rationale (Rust language team, Rust
  API Guidelines, <https://rust-lang.github.io/api-guidelines/naming.html>,
  verified 2026-08-02). `rustfmt` handles formatting the way `gofmt` does
  for Go. `clippy::style`, described in Clippy's own documentation as being
  mostly about writing idiomatic code and the most opinionated
  warn-by-default group (Rust language team, Clippy lint documentation,
  <https://doc.rust-lang.org/clippy/lints.html>, verified 2026-08-02), is
  the single clearest instance in any mainstream language of idiom
  compliance being shipped as a first-class, warn-by-default compiler
  lint rather than left to a separate opt-in linter.
- **Python.** PEP 8 is the canonical style document, and Black is the
  now-dominant automatic formatter, adopted by CPython's own tooling
  chain. "Pythonic" idiom extends beyond formatting into constructs,
  favoring comprehensions over manual accumulator loops for simple
  transformations, context managers over manual try or finally resource
  cleanup, truthiness checks over explicit length checks, and duck typing
  over explicit type checks where practical. Google's own Python style
  guide advises using default iterators and operators for types that
  support them, and treats comprehensions as clearer than manual
  construction for the simple case (Google, Google Python Style Guide,
  <https://google.github.io/styleguide/pyguide.html>, verified 2026-08-02),
  both textbook instances of the same idiom.
- **TypeScript and JavaScript.** The weakest single canonical source among
  the four languages covered in this entry's code examples, because no
  language-official style guide exists the way Effective Go or PEP 8 do.
  The community instead converges around widely adopted shareable
  configurations, most visibly the Airbnb JavaScript Style Guide's ESLint
  config, alongside TypeScript-specific idiom such as preferring `unknown`
  over `any` for values of genuinely unknown shape, discriminated unions
  over class hierarchies for closed sets of variants, and optional
  chaining plus nullish coalescing over manual truthiness checks for
  reading a possibly-absent nested value, both language features added
  specifically to give idiomatic expression to a pattern the community was
  already writing verbosely by hand.
- **Java.** Idiom in Java shifted with each major language version, most
  sharply at Java 8's introduction of lambdas and streams. Code that was
  idiomatic Java in 2010, an explicit `for` loop with an anonymous
  `Comparator` inner class, reads as dated rather than idiomatic in a
  modern Java codebase, where a lambda or method reference is now expected
  for the same job. Effective Java (Bloch, 3rd edition, Addison-Wesley,
  2018) is the most influential single canonical source, and its
  item-by-item structure, for example Item 1's guidance on static factory
  methods over public constructors, is itself an idiom-compliance
  document.

## 9. Known production uses

- **The Go standard library, formatted and reviewed against `gofmt` and
  Effective Go as policy.** The Go Authors state in Effective Go that all
  Go code in the standard packages has been formatted with `gofmt`, making
  the standard library itself both an enforcement artifact and the primary
  worked example new Go programmers study to learn the language's idiom
  (The Go Authors, *Effective Go*, <https://go.dev/doc/effective_go>,
  verified 2026-08-02).
- **The Rust compiler and standard library toolchain shipping
  `clippy::style` as a warn-by-default lint group.** Every crate built with
  a standard `cargo clippy` invocation receives idiom warnings without any
  separate opt-in configuration, which the Clippy documentation itself
  frames explicitly as the purpose of that lint group (Rust language team,
  Clippy lint documentation, <https://doc.rust-lang.org/clippy/lints.html>,
  verified 2026-08-02).
- **CPython's own codebase and the wider Python community's adoption of
  Black as a shared, near-universal formatter**, removing formatting idiom
  from case-by-case human judgement across a very large fraction of public
  Python packages on PyPI, a scale of adoption that made "Pythonic" idiom
  compliance for whitespace and layout effectively non-negotiable in a way
  it was not before Black's release.
- **Google's internal monorepo and public style guides for C++, Java,
  Python, and Go**, each independently maintained and each enforced through
  a combination of static analysis and mandatory code review, documented
  publicly at Google's style guide site, of which the Python guide is one
  instance cited directly above (Google, Google Python Style Guide,
  <https://google.github.io/styleguide/pyguide.html>, verified 2026-08-02).
  This is a named example of idiom compliance enforced at organizational
  scale across a multi-million-line codebase spanning several languages
  simultaneously.

## 10. Consequences

Positive consequences follow from the property.

- Faster code review, because a reviewer who recognises the idiom does not
  need to reconstruct the author's reasoning from first principles, they
  recognise the shape and can focus review attention on logic rather than
  form.
- Lower onboarding cost, because new team members transfer pattern
  recognition from wider practice instead of having to learn a local
  dialect from scratch.
- Access to tooling built around the idiom. Language servers, linters,
  automated refactoring tools, and even large language model code
  assistants are trained overwhelmingly on idiomatic corpus code, and
  non-idiomatic constructions receive materially worse suggestions and
  worse automated refactoring support from all of these tools.
- A smaller surface for a specific class of bug. Some idioms exist
  specifically because the non-idiomatic alternative is a known footgun,
  for example Go's idiom of checking an error immediately after the call
  that can produce it, rather than deferring the check, which reduces the
  chance an error is silently dropped.

Negative consequences accompany it as well.

- Idiom compliance pursued as an end in itself, rather than as a means to
  readability, produces code optimized for looking like other code rather
  than for being clear about what it actually does. A comprehension nested
  three levels deep because comprehensions are Pythonic is a worse
  outcome than an explicit loop that a reader can trace line by line.
- Idioms genuinely change across language versions, and code idiomatic for
  an older version of a language can read as dated rather than idiomatic
  once the community has moved on, which is a real maintenance cost.
  Keeping a codebase's idiom current requires periodic, deliberate
  revisiting, not a one-time compliance pass.
- Automated formatters remove bikeshedding over whitespace but do nothing
  for the deeper layer of idiom, naming, structure, error handling shape.
  Teams in languages with weaker canonical sources (this entry's Java and
  JavaScript examples relative to its Go and Rust examples) can mistake a
  formatter passing for the code being idiomatic and stop there.
- Chasing idiom across a language boundary in a polyglot codebase can
  itself become a source of inconsistency, if a shared internal library
  ends up idiomatic in one language and foreign-shaped in every other
  language that consumes it, trading one kind of unfamiliarity for
  another.

## 11. Failure modes and misuse

Cargo-culted idiom is a construct copied from a blog post, a book, or a
different language and applied without understanding the reason it exists,
producing something that has the surface shape of an idiom without its
actual benefit. The observable symptom is a reviewer asking why a piece of
code is written this way and the author being unable to answer beyond
having seen it done this way. The cause is idiom compliance treated as a
checklist of surface patterns rather than as an understanding of the forces
in dimension 3. The fix is to require the author, in review, to state the
concrete benefit the construction is buying at this call site, not merely
that it matches a pattern seen elsewhere.

Idiom worship over clarity happens when a team decides the idiomatic
construct is always the correct one and applies it even where it hurts
readability, for example collapsing a genuinely multi-step transformation
into a single dense method-chain because method chains are idiomatic in the
language. The observable symptom is code review comments repeatedly asking
what a line actually does, for lines that are individually idiomatic but
collectively opaque. The cause is idiom compliance conflated with terseness,
when the actual goal, per dimension 2, is recognisability rather than
brevity. The fix is to split the chain into named intermediate steps when
the composed form stops being faster to read than the expanded form, and to
treat that as a legitimate, non-idiom-violating choice rather than a
failure to be idiomatic.

Stale idiom is code written idiomatically for an earlier version of the
language, or an earlier era of the community's practice, left unrevisited
as the convention moves on, so it reads as dated to a new hire even though
nothing about it is incorrect. The observable symptom is new hires flagging
the same pattern repeatedly across code review, asking why a codebase is
not using a newer idiom. The cause is idiom compliance treated as a
one-time property established at authoring time rather than an ongoing
property that needs periodic revisiting as the language evolves. The fix is
to track idiom currency the same way dependency currency is tracked, with
periodic sweeps, rather than only at the moment code is first written.

Cross-language transliteration is the precise failure Kernighan and
Plauger documented in 1978, where a programmer fluent in language A writes
language B using A's habits, because B happens to permit the same
construction even though B's own community does not use it that way. The
observable symptom is getters and setters on every field in idiomatic Go,
or manual index-based loops in idiomatic Python, or class hierarchies
standing in for what would idiomatically be a discriminated union in
TypeScript. The cause is that the author's mental model has not yet
updated to the new language's own idiom, often because the code compiles
and runs correctly, so nothing forces the update. The fix is to pair the
author, early, with a reviewer fluent in the target language's specific
idiom, and to lean on the language's automated tooling from dimension 8
wherever it exists, since a correct-but-foreign construction that a
formatter cannot fix is exactly the case that most needs a human to catch
it.

Local house style presented as wider idiom happens when a team's internal
convention, adopted for genuine local reasons, gets defended in review as
the idiomatic way when in fact it diverges from what the wider community
does. The observable symptom is a new hire familiar with the wider
community pushing back on a pattern the team insists is standard, with
neither side able to point to a canonical source. The cause is conflating
dimension 13's related principle, Convention over Configuration at the
team level, with idiom compliance at the language-community level, which
are related but distinct properties. The fix is to be explicit in team
documentation about which patterns are wider idiom, cited against a
canonical source, and which are deliberate local convention chosen for a
stated local reason, so the two are never silently conflated.

## 12. Trade-off matrix

The named alternatives compared here are the other principles a team might
lean on instead of, or alongside, idiom compliance when deciding how a
piece of code should be shaped.

| Force | Idiomatic (this entry) | Convention over Configuration | Principle of Least Astonishment | House Style / Local Convention |
|---|---|---|---|---|
| Source of authority | The wider language community, standard library, and canonical style documents | The specific framework's own established defaults | The specific reader's or team's prior expectation | The specific team, chosen deliberately |
| Transfers across projects | High, a reader who knows the language recognises it anywhere | Medium, transfers only across projects using the same framework | Low, depends entirely on who the reader is | Low, transfers only within the team that set it |
| Enforcement maturity | High in Go and Rust (automated), lower in Java and JavaScript | Framework-dependent, often documentation-only | Almost never automated, purely a review-time judgement | Depends entirely on whether the team writes it down and lints it |
| Cost to establish | Low, already exists, cost is in learning it | Medium, must learn the specific framework's defaults | Zero to establish, but expensive to apply consistently since it is subjective per reader | Medium to high, the team must author and maintain its own guide |
| Risk of staleness | Real, idiom shifts with language versions (dimension 11) | Real, framework defaults change across major versions | Low, human expectations shift slowly | Real, and worse, because there is no external community to signal the shift |
| Best combined with | Convention over Configuration inside a framework, and House Style for genuinely local decisions the wider community has no opinion on | Idiomatic compliance for anything the framework itself is silent on | Any of the others, since it is the underlying human-factors reason all of them exist | Idiomatic compliance as the default, with House Style documenting only genuine deviations and the reason for each |

## 13. Related and incompatible patterns

Convention over Configuration is the framework-scoped sibling of idiom
compliance. Where idiom compliance is a property of a whole language
community, Convention over Configuration is the same idea narrowed to a
single framework's own established defaults, for example Rails' file
naming and directory layout conventions. The two compose cleanly, since a
piece of code inside a Rails application should be both idiomatic Ruby and
conventional Rails at the same time, and a violation of either is a
separate, distinguishable kind of deviation.

Principle of Least Astonishment is the underlying human-factors
justification idiom compliance rests on. A reader is least astonished by
code that matches the shape they already expect from wider practice, so
idiom compliance is one concrete, checkable instantiation of the broader
Principle of Least Astonishment rather than a competing idea.

KISS, keep it simple, and idiom compliance can pull in opposite directions
when the idiomatic construction for a given language happens to be denser
or more abstract than the simplest possible expression of the same logic,
which is exactly the idiom-worship failure mode in dimension 11. The
resolution is not to abandon idiom compliance but to recognise that the
idiomatic form and the simplest form are usually, but not always, the same
thing, and to prefer simplicity when the two genuinely diverge.

YAGNI, you aren't gonna need it, is compatible and largely orthogonal.
Idiom compliance concerns how a given piece of functionality is expressed,
while YAGNI concerns whether a given piece of functionality should exist
at all. An idiomatically written unnecessary abstraction is still an
unnecessary abstraction.

No pattern in this repository is flagged as strictly incompatible with
idiom compliance, since idiom compliance is a property of expression rather
than a structural pattern that competes for the same responsibility as
another pattern. The closest thing to an incompatibility is the tension
already described against KISS, and it is a tension of degree, not a
structural conflict.

## 14. Refactoring path in and out

Introducing idiom compliance into an existing codebase that has drifted from
it, or was never written with it in mind, proceeds in a specific order to
avoid a single enormous, unreviewable diff.

1. Establish the canonical source for the language in question, in writing,
   linked from the team's contribution documentation, so there is a single
   agreed reference rather than each reviewer's private opinion.
2. Turn on the language's automatic formatter first, and run it once across
   the whole codebase as a single, mechanical, git-blame-preserving commit.
   Most formatters, including `gofmt`, `rustfmt`, and Black, support a
   suppression file style option so the reformatting commit specifically
   does not obscure history. This layer carries zero risk of behaviour
   change, since it touches only whitespace and layout.
3. Enable the language's idiom-focused linter (`clippy::style`,
   `golangci-lint`'s idiom-focused analyzers, `pylint`, an ESLint config
   with a style-focused rule set) in warn-only mode against the existing
   codebase, and triage the resulting warning count. Do not attempt to fix
   every warning in one pass, since a large legacy codebase can easily
   surface thousands.
4. Set the linter to fail CI only on newly introduced violations,
   suppressing the existing backlog with an explicit baseline file most
   linters support, so the codebase stops getting worse immediately while
   the existing backlog is paid down opportunistically as files are
   touched for other reasons.
5. Pay down the backlog file by file, ideally as part of otherwise-planned
   work on that file rather than as a dedicated large refactor. A pure
   idiom-compliance change with no behaviour change is the highest-risk,
   lowest-value kind of change to review in isolation, all cost, with the
   benefit only accruing gradually as future readers encounter it.

The reverse direction, removing idiom compliance, is rare and almost always
undesirable on its own terms. It typically happens as a side effect of a
team choosing to diverge deliberately for a stated local reason, per
dimension 4's non-applicability list, in which case the correct action is
not to refactor idiom compliance out but to document the specific, narrow
deviation and the reason for it at the point of deviation, leaving the
rest of the codebase's idiom compliance untouched.

## 15. Testing and verification

Idiom compliance is unusual among the properties in this repository in that
it is largely verified by tooling rather than by runtime tests, because it
is a static property of the source text rather than a property of program
behaviour.

Running the formatter in check-only mode in CI is the cheapest and
highest-confidence layer and should always run before any slower check,
failing the build if any file would be rewritten. A linter run in CI,
configured to the team's agreed canonical source and, per the refactoring
path above, gated against a baseline so it fails only on new violations in
a legacy codebase, is the second layer. Code review checklist items cover
the residual cases no tool covers, most commonly naming choices and API
shape decisions such as return type or error-handling shape, which are
judgement rather than sourced or machine-checkable facts and should be
recorded as such in review comments rather than asserted as objective
rules.

Idiom compliance makes some things easier to test. Idiomatic error-handling
shapes, Go's explicit paired value and error return, Rust's `Result` type,
or Python's exceptions caught at the idiomatic boundary, tend to be more
consistently and predictably testable than ad hoc, non-idiomatic error
signalling, because test authors can rely on the same shape appearing
everywhere rather than having to discover a bespoke convention per
function.

It makes some things harder to test as well. A highly idiomatic, densely
composed construction, several chained higher-order function calls in one
expression for example, can be harder to unit-test at a granular level than
the same logic expanded into named intermediate steps, since there is no
intermediate value to assert against without decomposing the expression
first. This is the same tension described in dimension 11's idiom-worship
failure mode, expressed as a testing cost rather than a readability cost.

## 16. Observability signals

Idiom compliance is not something a running production system exposes at
runtime, since it is a property of source code rather than of program
state, but it has clear, trackable signals at the development-process
level.

Linter warning count over time, tracked per commit or per release, is a
leading indicator of whether the codebase is converging on or diverging
from its stated idiom. A steadily falling count after the baseline is
established indicates the backlog is being paid down, while a rising
count indicates new code is being written faster than it is being brought
into compliance.

The category of code review comments matters too, specifically the
fraction of review comments that are pure style or idiom nits versus
comments about logic or correctness. A healthy, well-tooled repository
pushes idiom comments almost entirely into automated formatter and linter
output, leaving human review comments concentrated on logic. A repository
where most of the human review threads are idiom-related comments signals
that automation is under-deployed relative to what the language's
toolchain actually supports.

Onboarding time to a new hire's first accepted pull request is an indirect
but practically useful signal, since idiom-compliant code is easier to
learn from and pattern-match against. A lengthening trend in this metric,
holding team size and hiring pipeline constant, is worth correlating
against idiom drift.

Formatter and linter version currency is a further signal, since a
canonical source that is itself several major versions behind current
practice is silently teaching new authors an outdated idiom. Tracking the
age of the pinned linter or formatter version alongside the language's own
release cadence surfaces this before it accumulates into a large
migration.

## 17. Security and privacy implications

Idiom compliance is, in the general case, a readability and maintainability
property rather than a security control, and this entry states that
plainly rather than inventing a security narrative where the connection is
weak. The one place a genuine, analytical connection exists is that
several languages' idioms specifically exist to close a known correctness
or security footgun, and deviating from the idiom reopens that footgun.

Go's idiom of checking an error return immediately after the call that can
produce it exists specifically to prevent the class of bug where a failed
operation's result is used as though it had succeeded. Skipping the
idiomatic check, even though the language permits it, silently
reintroduces the exact defect the idiom exists to close.

Rust's idiom of using `Result` and `Option` rather than sentinel values or
nulls is enforced by the type system itself for the null case, but the
`Result`-handling idiom, propagating with the question-mark operator or
explicitly matching rather than calling an unwrap method in non-prototype
code, is a convention rather than a compiler-enforced rule. An author who
reaches for an unwrap call out of habit from a language without a
`Result` type reintroduces an unhandled-failure panic path that the idiom
exists specifically to avoid.

Idiomatic use of a language's context-manager or ownership-based resource
cleanup construct, Python's `with` statement or Rust's ownership-based
drop mechanism, closes resource-leak classes of bug that a manual,
non-idiomatic acquire-and-forget-to-release construction reopens.

Beyond these specific, language-idiom-tied correctness cases, this entry
records no further security or privacy implication, and states that
explicitly rather than manufacturing one.

## 18. References

1. Brian W. Kernighan and P. J. Plauger, *The Elements of Programming
   Style*, 2nd edition, McGraw-Hill, 1978. Foundational source for the idea
   that a construction correct in one language can be wrong when carried
   unchanged into another.
2. The Go Authors, *Effective Go*, <https://go.dev/doc/effective_go>,
   verified 2026-08-02.
3. Tim Peters, "PEP 20, The Zen of Python", 2004,
   <https://peps.python.org/pep-0020/>, verified 2026-08-02.
4. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item
   1, "Consider static factory methods instead of constructors."
5. Rust language team, Rust API Guidelines,
   <https://rust-lang.github.io/api-guidelines/naming.html>, verified
   2026-08-02.
6. Rust language team, Clippy lint documentation, `clippy::style` group
   description, <https://doc.rust-lang.org/clippy/lints.html>, verified
   2026-08-02.
7. Google, Google Python Style Guide,
   <https://google.github.io/styleguide/pyguide.html>, verified
   2026-08-02.
8. Guido van Rossum, Barry Warsaw, and Nick Coghlan, "PEP 8, Style Guide
   for Python Code", <https://peps.python.org/pep-0008/>, verified
   2026-08-02.

## Code examples

The same task, reading a value that may be absent from a lookup and falling
back to a default, is shown in its idiomatic form and its foreign,
transliterated form in four languages, to make the difference concrete
rather than abstract.

### TypeScript

```typescript
// Idiomatic. Optional chaining and nullish coalescing express
// "read if present, otherwise default" directly.
function idiomaticGreeting(user: { nickname?: string } | null): string {
  return `Hello, ${user?.nickname ?? "friend"}`;
}

// Foreign. Transliterated from a language without these operators,
// correct but forces the reader to trace two branches by hand.
function foreignGreeting(user: { nickname?: string } | null): string {
  let name: string;
  if (user !== null && user !== undefined) {
    if (user.nickname !== undefined && user.nickname !== null) {
      name = user.nickname;
    } else {
      name = "friend";
    }
  } else {
    name = "friend";
  }
  return "Hello, " + name;
}

console.log(idiomaticGreeting({ nickname: "Mirza" }));
console.log(idiomaticGreeting(null));
console.log(foreignGreeting({ nickname: "Mirza" }));
console.log(foreignGreeting(null));
```

### Python

```python
"""Same task. Read a possibly-absent value, fall back to a default."""


def idiomatic_greeting(user: dict | None) -> str:
    nickname = (user or {}).get("nickname", "friend")
    return f"Hello, {nickname}"


def foreign_greeting(user: dict | None) -> str:
    # Transliterated from a language with explicit null checks and no
    # dict.get default argument. Correct, but fights the language.
    if user is not None:
        if "nickname" in user and user["nickname"] is not None:
            name = user["nickname"]
        else:
            name = "friend"
    else:
        name = "friend"
    return "Hello, " + name


if __name__ == "__main__":
    print(idiomatic_greeting({"nickname": "Mirza"}))
    print(idiomatic_greeting(None))
    print(foreign_greeting({"nickname": "Mirza"}))
    print(foreign_greeting(None))
```

### Go

```go
package main

import "fmt"

// Idiomatic. The two-value map lookup ("comma ok") is Go's own idiom
// for "read if present, otherwise default", and needs no helper type.
func idiomaticGreeting(users map[string]string, id string) string {
	if nickname, ok := users[id]; ok && nickname != "" {
		return fmt.Sprintf("Hello, %s", nickname)
	}
	return "Hello, friend"
}

// Foreign. Reaching for an explicit two-step existence check plus a
// scan, the shape a Java or C# background carries over.
func foreignGreeting(users map[string]string, id string) string {
	var name string
	exists := false
	for k, v := range users {
		if k == id {
			exists = true
			name = v
			break
		}
	}
	if exists && name != "" {
		return "Hello, " + name
	}
	return "Hello, friend"
}

func main() {
	users := map[string]string{"m1": "Mirza"}
	fmt.Println(idiomaticGreeting(users, "m1"))
	fmt.Println(idiomaticGreeting(users, "missing"))
	fmt.Println(foreignGreeting(users, "m1"))
	fmt.Println(foreignGreeting(users, "missing"))
}
```

### Rust

```rust
use std::collections::HashMap;

// Idiomatic. Option::unwrap_or, plus C-CONV-style borrowed access via
// get(), is the Rust API Guidelines' own recommended shape for this.
fn idiomatic_greeting(users: &HashMap<String, String>, id: &str) -> String {
    let nickname = users.get(id).map(|s| s.as_str()).unwrap_or("friend");
    format!("Hello, {}", nickname)
}

// Foreign. Reaching for .unwrap() and a manual contains_key check,
// the shape a language without Option carries over. Panics on a
// missing key instead of expressing absence through the type system.
fn foreign_greeting(users: &HashMap<String, String>, id: &str) -> String {
    if users.contains_key(id) {
        let nickname = users.get(id).unwrap();
        format!("Hello, {}", nickname)
    } else {
        "Hello, friend".to_string()
    }
}

fn main() {
    let mut users: HashMap<String, String> = HashMap::new();
    users.insert("m1".to_string(), "Mirza".to_string());

    println!("{}", idiomatic_greeting(&users, "m1"));
    println!("{}", idiomatic_greeting(&users, "missing"));
    println!("{}", foreign_greeting(&users, "m1"));
    println!("{}", foreign_greeting(&users, "missing"));
}
```

All four samples were run against their respective toolchains during
authoring. `npx tsc` type-checked the TypeScript sample with no errors,
`python3` executed the Python sample and printed the four expected
greetings, `go run` executed the Go sample and printed the four expected
greetings, and `rustc` compiled and ran the Rust sample, printing the four
expected greetings. Java and C# are omitted from the runnable examples for
this entry. Both languages' idiomatic shape for this task, `Optional` with
`orElse` in Java and the null-conditional plus null-coalescing operators
in C#, is close enough to the TypeScript and Rust forms shown above that a
fifth and sixth near-duplicate example would not add a materially new
idiom to demonstrate.
