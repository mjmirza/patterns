---
name: Keep It Simple
slug: keep-it-simple
family: 04-principles-and-laws
category: Principle
aliases: [KISS, Keep It Simple Stupid, Simplicity Principle]
first_described: "Kelly Johnson, Lockheed Skunk Works, c. 1960s (popularized); Hoare 1980 Turing Award lecture (software-specific framing)"
maturity: canonical
related: [yagni, dry, separation-of-concerns, single-responsibility-principle]
incompatible_with: []
verified: 2026-08-02
---

# Keep It Simple

## 1. Name, aliases, and lineage

The canonical name in software engineering is Keep It Simple, almost always
referenced by its acronym KISS. The acronym is popularly expanded as "Keep It
Simple, Stupid," though many teams soften the last word to "Simple" or
"Straightforward" to keep the phrase usable in professional settings without
the insult reading as directed at a colleague.

The acronym is widely attributed to Kelly Johnson, the lead engineer at
Lockheed's Skunk Works, the advanced development program that produced
aircraft such as the U-2 and the SR-71 Blackbird. The attributed origin story
is that Johnson handed a team of design engineers a basic set of tools and
challenged them to build an aircraft repairable by an average mechanic in the
field, under combat conditions, using only those tools. The Wikipedia article
on the KISS principle records this account and further notes the U.S. Navy
first documented the phrase in 1960, with the acronym form popularized by the
1970s (Wikipedia, "KISS principle," verified 2026-08-02,
https://en.wikipedia.org/wiki/KISS_principle). The precise phrase, and whether
Johnson himself ever wrote "stupid," is not independently confirmed by a
primary Lockheed document. The attribution should be read as the standard
engineering-folklore account, not as a citation to a dated, signed memo.

Software engineering did not need Lockheed to independently discover the same
idea. Tony Hoare's 1980 Turing Award lecture, "The Emperor's Old Clothes,"
delivered the same principle in a form specific to programming, and it is the
citation software engineers reach for when they want a founding text rather
than an aerospace anecdote. Hoare put it this way. "There are two ways of
constructing a software design. One way is to make it so simple that there are
obviously no deficiencies. And the other way is to make it so complicated that
there are no obvious deficiencies. The first method is far more difficult"
(C.A.R. Hoare, "The Emperor's Old Clothes," 1980 ACM Turing Award Lecture,
Communications of the ACM, vol. 24, no. 2, February 1981, p. 76). This is the
sentence most commonly quoted as software's own KISS statement, independent of
the Lockheed story, and it is arguably the more rigorous of the two because it
names the actual failure mode. complexity hides deficiencies rather than
eliminating them.

A second, related lineage runs through Fred Brooks, who in 1986 drew the
distinction between essential and accidental complexity that gives KISS its
modern technical vocabulary. Brooks argued that the difficulty inherent in a
problem cannot be simplified away, but the difficulty a team adds on top of
that through its own tools, process, and architecture can be, and it is this
second kind, the accidental kind, that KISS targets (Frederick P. Brooks Jr.,
"No Silver Bullet. Essence and Accidents of Software Engineering," IEEE
Computer, vol. 20, no. 4, April 1987, reprinted from a 1986 IFIP conference
paper; summarized in Wikipedia, "No Silver Bullet," verified 2026-08-02,
https://en.wikipedia.org/wiki/No_Silver_Bullet). KISS, in this lineage, is not
a call to make problems smaller than they are. It is a call to stop
manufacturing difficulty that was never in the problem to begin with.

A third and more recent contribution reframes the whole principle around a
distinction the earlier authors gestured at but never named cleanly. Rich
Hickey's 2011 talk "Simple Made Easy" argues that "simple" and "easy" are
different axes entirely, not synonyms, and that most teams optimize for the
wrong one. Hickey traces "simple" to the Latin roots "sim" and "plex," one
fold, meaning a thing is not intertwined with other things, and traces "easy"
to a root meaning adjacent or nearby, meaning a thing is familiar or close at
hand (Rich Hickey, "Simple Made Easy," Strange Loop conference, 20 October
2011, InfoQ recording, verified 2026-08-02,
https://www.infoq.com/presentations/Simple-Made-Easy/). A global variable is
easy to reach for and objectively complex, because it is entangled with every
piece of code that touches it. A pure function passed explicit arguments is
simple, because it is not entangled with anything, even if writing one takes
more thought than reaching for a shared mutable field. This distinction is
load-bearing for how the rest of this entry treats KISS. Simplicity is a
property of the artifact, its structural entanglement. Easiness is a property
of the developer's familiarity in the moment. KISS argues for the former, and
most violations of KISS in real codebases are committed in the name of the
latter.

## 2. Problem and context

Every non-trivial piece of software accretes complexity over its lifetime, and
that accretion happens in two very different ways that are easy to conflate.
The first is essential complexity, the complexity genuinely required by the
problem the software solves. Tax law has edge cases because tax law has edge
cases, not because the code is badly written. The second is accidental
complexity, complexity the team introduced through choices that were not
demanded by the problem. an extra layer of indirection nobody uses, a
configuration system for options that never vary, a message queue introduced
for a workload that never exceeded ten requests a minute, an abstract base
class with one implementation. KISS is the discipline of continuously refusing
the second kind while accepting the first as the actual cost of doing the job.

The problem KISS addresses arises specifically in situations where a
developer has more than one way to solve something and the more elaborate way
is available, familiar, or feels more professional. This happens constantly
because software engineering culture rewards the appearance of foresight. A
developer who builds a generic plugin architecture "in case we need to swap
providers later" looks like they are thinking ahead. A developer who writes
the direct call and a two-line comment explaining why a plugin architecture
was not warranted looks, at a glance, like they did less work. KISS exists
because the second developer usually did the harder job, correctly judging
that the plugin architecture is complexity paid up front against a need that
may never arrive, and the first developer's foresight is, more often than
not, waste that the whole team pays interest on for years.

The context in which KISS bites hardest is any codebase with more than one
maintainer and any expected lifetime past the current sprint, because
complexity's cost is not paid by the person who writes it, it is paid by
every person who reads it afterward, including that same person six months
later with the context gone. A one-off script run once and discarded has
almost no KISS pressure on it. nobody will ever read it again, so entanglement
costs nothing. A library used by forty other teams has enormous KISS
pressure, because every unit of accidental complexity in it is multiplied by
every reader who has to hold it in their head before they can safely change
anything near it.

## 3. Forces

KISS is not free. It trades against several real forces, and treating it as a
principle with no cost is how it gets waved around as a slogan rather than
applied as an engineering discipline.

- **Simplicity versus flexibility.** The simplest version of a piece of code
  usually handles today's requirement and nothing else. Flexibility, the
  ability to handle tomorrow's unknown requirement, is purchased with
  indirection, parameters, and abstraction, all of which are structural
  complexity by Hickey's definition. KISS says pay for flexibility only when
  the second concrete use case actually shows up, not when it is merely
  imaginable, but this means KISS-driven code sometimes needs real rework
  later, and that rework is a genuine, non-hypothetical cost.
- **Simplicity versus performance.** Some of the fastest known algorithms and
  data structures are more complex than their naive counterparts, precisely
  because the complexity buys speed the simple version cannot reach. A KISS
  team defaults to the simple version and complicates only where profiling
  proves the cost is real, but a team that never revisits that default under
  a performance regime that has changed will ship something that is simple
  and too slow.
- **Simplicity versus completeness.** A complete solution to a general
  problem is almost always more complex than a partial solution to the
  specific problem actually in front of the team. KISS favors the specific,
  partial solution, which means it deliberately under-serves cases that are
  not yet real. This is a productive trade until the day one of those cases
  becomes real and the team discovers the specific solution does not
  generalize cleanly.
- **Simplicity versus correctness under edge cases.** Handling every edge
  case correctly frequently multiplies branches and states. KISS pressure
  pushes toward handling the common case cleanly and either rejecting or
  explicitly punting on rare cases, which is the right trade when the rare
  cases are genuinely rare and wrong when "rare" was a guess that turns out
  to be false.
- **Simple versus easy, restated as a force.** The force that makes KISS hard
  to apply in practice is that the easy choice, copy the pattern the team
  already knows, add a config flag, wrap it in a framework abstraction that
  ships with the stack, is very often the complex choice by Hickey's
  definition, and the simple choice, a direct function, an explicit
  argument, one fewer moving part, can require more upfront thought and
  therefore feels harder to reach for under deadline pressure. KISS is, in
  this framing, a discipline of resisting the locally easy option in favor of
  the structurally simple one.
- **Simplicity versus team scale.** A small team with tight communication can
  hold more implicit context in their heads, which lowers the practical cost
  of a mildly complex design because everyone already knows the shape of it.
  A large or distributed team cannot rely on that shared context, which raises
  the practical cost of the same design. KISS pressure is therefore not
  constant. It rises with team size and with contributor turnover.

## 4. Applicability and non-applicability

Reach for KISS deliberately when:

- The requirement in front of you is concrete and the requirements you are
  tempted to design for are speculative, imagined, or explicitly labeled
  "someday."
- You are choosing between two designs that solve the actual, current problem
  equally well, and one has fewer moving parts, fewer entangled pieces of
  state, or a shorter path from input to output.
- The code will be read by people other than you, especially people who join
  the project later with no access to the reasoning you have in your head
  right now.
- You are early in a project's life and do not yet have enough real usage
  data to know which axes of flexibility will actually matter.
- The alternative to the simple design is a general-purpose framework,
  plugin system, or configuration layer built for a single concrete
  consumer, which is complexity purchased for a flexibility nobody has asked
  for yet.
- You are debugging. The simplest hypothesis and the simplest reproduction
  case that still exhibits the bug should always be tried before a more
  elaborate one, independent of whether the eventual fix turns out to be
  simple.

Do NOT apply KISS, or recognize where it does not license the choice being
made, when:

- The problem itself is irreducibly complex and a simpler-looking solution
  is actually an incorrect or incomplete one. A tax engine that ignores
  filing-status interactions to "keep it simple" is not simple, it is wrong,
  and KISS never licenses dropping essential complexity to make the code
  read more nicely. This is the single most common misapplication of the
  principle. using it as cover for an incomplete implementation rather than
  as a filter against unnecessary machinery.
- You already have two or more real, current consumers with genuinely
  different needs. At that point the "simple" single-purpose version is the
  one entangled with two callers' assumptions, and a small, deliberate
  abstraction is very often the structurally simpler choice by Hickey's
  definition, even though it has more code.
- The team has already paid for infrastructure, conventions, or a framework
  that the codebase is built on, and bypassing it for a "simpler" one-off
  shortcut in a single module creates an inconsistency that every future
  reader now has to reconcile. Local simplicity that increases global
  entanglement is not KISS.
- Security or correctness-critical code benefits from an established,
  audited, and slightly heavier implementation over a hand-rolled simpler
  one. A homegrown authentication scheme is simpler to read than an
  integration with an established identity provider, and it is also far more
  dangerous. KISS is subordinate to correctness and security, never a
  justification to override them.
- The domain genuinely requires precision that a simplified model cannot
  express, such as financial rounding rules, time zone and calendar
  arithmetic, or concurrency correctness. Simplifying these to reduce line
  count routinely reintroduces the exact bug classes the more careful
  handling exists to prevent.
- You are tempted to invoke KISS as a rhetorical stop sign in a design
  discussion without engaging the actual trade-off. "Let's keep it simple"
  used to shut down a legitimate discussion about a real, current
  requirement is not the principle, it is the principle's name borrowed to
  win an argument, and it should be recognized and named as such when it
  happens.

## 5. Structure

KISS is a principle, not a structural design pattern, so it has no
participants, classes, or roles in the sense the Gang of Four catalog uses.
What it has instead is a decision procedure, a small, repeatable evaluation a
developer or a reviewer runs when facing a choice between two or more designs
that all satisfy the current, real requirement.

- **The candidate designs.** Two or more ways to solve the concrete problem
  actually in front of the team, each of which is functionally adequate for
  the requirement as it exists today.
- **The entanglement count.** For each candidate, how many other pieces of
  the system does this design touch, depend on, or require the reader to
  hold in mind simultaneously to reason about correctness. This is Hickey's
  simplicity axis, and it is the one KISS should actually be evaluated
  against, not line count and not development effort.
- **The familiarity discount.** For each candidate, how much of its apparent
  complexity is genuinely structural versus how much is simply unfamiliar to
  the person judging it right now. A design should not be rejected as
  "complex" purely because the reviewer has not seen the pattern before, and
  a design should not be accepted as "simple" purely because it is the
  pattern the team always reaches for.
- **The speculative-requirement filter.** For each piece of flexibility a
  candidate design buys, is there a second, real, current consumer that
  needs it, or is the flexibility justified only by an imagined future
  consumer. Flexibility justified by an imagined consumer is charged fully
  against the design's complexity score and gets no credit for
  "forward-thinking."
- **The verdict.** The candidate with the lowest entanglement count, after
  the familiarity discount is applied and after essential requirements are
  confirmed to still be met in full, is the one KISS selects. When two
  candidates tie on entanglement, the tie is broken by whichever reads more
  directly as the statement of the actual requirement, because that is the
  version a future reader will most quickly trust as correct.

## 6. ASCII structure diagram

```text
                  A requirement in front of the team
                              |
                              v
             +--------------------------------+
             |   Enumerate candidate designs   |
             |   that fully satisfy it today   |
             +--------------------------------+
                     |                |
                     v                v
        +----------------+   +----------------+
        | Candidate A     |   | Candidate B     |
        | (direct)        |   | (abstracted)    |
        +----------------+   +----------------+
                |                     |
                v                     v
     +------------------+   +------------------+
     | Entanglement.     |   | Entanglement.    |
     | how many other    |   | how many other   |
     | parts of the      |   | parts of the     |
     | system does this  |   | system does this |
     | design touch?     |   | design touch?    |
     +------------------+   +------------------+
                |                     |
                +----------+----------+
                           v
             +--------------------------------+
             |   Is any extra flexibility here |
             |   justified by a SECOND, REAL,  |
             |   CURRENT consumer?              |
             +--------------------------------+
                     |               |
                    yes              no
                     |               |
                     v               v
          keep the abstraction   discard the abstraction,
          (a real force,          adopt the lower-
           not speculation)       entanglement candidate
                     \               /
                      \             /
                       v           v
              +---------------------------+
              |  Chosen design. the one   |
              |  with least structural    |
              |  entanglement that still  |
              |  fully meets the ESSENTIAL|
              |  requirement, not a       |
              |  shortened one            |
              +---------------------------+
```

## 7. Dynamics

The KISS evaluation is not a one-time gate at design time, it is a recurring
loop that runs at three different moments in a code's life, and the dynamics
differ at each.

```text
   ---- at design time ----

   requirement arrives
        |
        v
   sketch simplest design that meets it fully
        |
        v
   walk the applicability checklist (dimension 4)
        |
        v
   is a speculative future need pulling the design
   toward more machinery than the current requirement needs?
        |
      yes -> strip it back to the current requirement, note
             the future need in a comment or ticket, move on
        |
       no -> proceed with the design as sketched


   ---- at review time ----

   reviewer reads the diff
        |
        v
   for every added abstraction, layer, flag, or parameter,
   ask. which CURRENT caller needs this?
        |
        v
   no current caller needs it -> flag it, ask author to justify
   or remove
        |
        v
   a real, current caller needs it -> accept, and note it as
   the concrete justification in the review thread so the next
   reader does not have to re-derive it


   ---- at the moment requirements actually change ----

   a genuinely new, concrete requirement lands
        |
        v
   does the existing simple design still satisfy it directly?
        |
      yes -> no change needed, KISS held, nothing to do
        |
       no -> now, and only now, introduce the abstraction,
             indirection, or generalization the new requirement
             actually demands, sized to the requirement that
             exists, not to every requirement that might follow it
```

The important dynamic to notice is that KISS is deliberately reactive to real
requirements rather than proactive against imagined ones. This is the same
dynamic that separates it from over-engineering. the loop only adds structure
in response to a requirement that has actually arrived, never in anticipation
of one that has not.

## 8. Implementation variants

KISS is not implemented as code, it is implemented as a set of habits and
review practices that shape what code looks like. The variants below are the
concrete forms teams use to operationalize the principle.

- **Inline until duplicated, extract on the second occurrence.** A concrete
  rule some teams adopt from the "Rule of Three" heuristic. write the code
  directly the first time, and only pull out a shared function, class, or
  abstraction the second or third time the same logic is needed, once the
  actual shape of the reuse is known rather than guessed. This directly
  operationalizes the speculative-requirement filter from dimension 5.
- **Function-first, class-later.** In languages that support both free
  functions and classes, defaulting to a plain function until state or
  polymorphism is genuinely required avoids paying for object-oriented
  machinery, constructors, and instance lifecycle, that a stateless
  transformation never needed.
- **Composition over configuration.** Rather than building a generic,
  parameterized system that reads behavior from a config file or flags,
  write the specific behavior directly and, if a second variant is later
  needed, compose it explicitly (a second function, a second call site)
  rather than encoding both behaviors as branches inside one configurable
  system. A config-driven system is often chosen because it looks flexible,
  but it is frequently more entangled than two short, separate, honest
  functions.
- **Feature-flag deletion discipline.** Feature flags are a legitimate and
  sometimes necessary form of complexity, but KISS-disciplined teams treat
  every flag as debt with an expiration date and delete the flag, and the
  dead branch it guarded, once the decision it existed to support has been
  made. A codebase littered with permanently-on flags is a codebase that
  never paid down its complexity debt.
- **The "delete first" refactor.** Before adding new code to solve a
  problem, check whether the problem can instead be solved by deleting
  existing code, an unused parameter, a redundant layer, an abstraction with
  one implementation. Deletion, when it is correct, is strictly more
  KISS-aligned than any addition, because it reduces entanglement rather
  than merely avoiding an increase in it.
- **Boring technology by default.** SQLite's own design documentation is
  explicit that the C language was chosen in part because it is "old and
  boring," a well-understood language with a small, well-known dependency
  surface, in contrast to "modern" languages that "often require
  multi-megabyte runtimes loaded with thousands and thousands of interfaces"
  (SQLite Consortium, "Why SQLite Uses C," verified 2026-08-02,
  https://www.sqlite.org/whyc.html). Choosing the well-understood tool over
  the newer, more capable one is a direct implementation of KISS at the
  technology-selection level, not only at the code level.
- **Small dependency surface as a hard constraint.** Some teams operationalize
  KISS as a literal budget, a cap on the number of third-party dependencies a
  module may pull in, forcing the "write it yourself, briefly" option to be
  seriously considered against "pull in a library for this." Rob Pike's Go
  proverb "A little copying is better than a little dependency" captures this
  variant directly (Rob Pike, Gopherfest, 2015, collected at Go Proverbs,
  verified 2026-08-02, https://go-proverbs.github.io/). A small amount of
  duplicated code that stays local and entangles with nothing is judged
  simpler, in Hickey's structural sense, than a dependency edge to an
  external package, even a well-maintained one, because the dependency edge
  is itself a form of entanglement with something outside the team's control.

## 9. Known production uses

- **SQLite.** SQLite's own project documentation states its design goal of
  minimizing the standard-library and runtime surface it depends on, listing
  in its minimum configuration only a handful of C standard library
  functions (`memcmp`, `memcpy`, `memmove`, `memset`, `strcmp`, `strlen`,
  `strncmp`), and explicitly contrasts this with "modern" language runtimes
  that carry "multi-megabyte runtimes loaded with thousands and thousands of
  interfaces" (SQLite Consortium, "Why SQLite Uses C," verified 2026-08-02,
  https://www.sqlite.org/whyc.html). The choice of a single, dependency-light
  C library that compiles into a host application rather than a networked
  server process is a direct, named, first-party consequence of prioritizing
  a small dependency surface and a small number of moving parts.
- **The Go programming language.** Go's own designers have repeatedly framed
  the language's feature set as a deliberate KISS trade-off. fewer language
  features than comparable statically typed languages of its era, in
  exchange for code that is easier to read across a large, unfamiliar
  codebase. This is captured in the collected "Go Proverbs," attributed to
  Rob Pike's 2015 Gopherfest talk, including "Clear is better than clever"
  and "A little copying is better than a little dependency" (Go Proverbs,
  verified 2026-08-02, https://go-proverbs.github.io/). The deliberate
  omission of generics from Go for its first thirteen years, added only in
  Go 1.18, 2022, is a widely discussed, named instance of a language design
  team choosing to withhold a feature specifically to avoid the added
  cognitive and implementation complexity, until real, widespread use
  demonstrated the need.
- **Unix and the Unix philosophy of small, composable tools.** Doug McIlroy's
  frequently quoted formulation, "Write programs that do one thing and do it
  well. Write programs to work together. Write programs to handle text
  streams, because that is a universal interface," is the founding statement
  of a design tradition, still visible in the standard Unix toolset
  (`grep`, `sort`, `wc`, `cut`, piped together rather than reimplemented as
  one monolithic tool) that is one of the most cited real-world instances of
  simplicity through minimal, single-purpose components rather than
  general-purpose, do-everything programs (Wikipedia, "Unix philosophy,"
  attributing the formulation to Doug McIlroy, verified 2026-08-02,
  https://en.wikipedia.org/wiki/Unix_philosophy).
- **Basecamp and the "majestic monolith."** The Basecamp engineering team has
  publicly and repeatedly argued against splitting a small team's
  application into microservices before the team's scale actually demands
  it, favoring a single, well-organized Ruby on Rails application, a
  position they have described in public talks and blog posts as choosing a
  simpler operational and mental model over a distributed architecture whose
  complexity is not yet justified by real load or team size. This is a
  named, public instance of the applicability boundary in dimension 4. the
  flexibility a distributed architecture buys is deferred until a second,
  real operational need, independent scaling, independent deployment
  cadence for a genuinely separate team, actually appears.

## 10. Consequences

Positive:

- **Lower cognitive load for every future reader.** A design with fewer
  entangled parts requires holding less state in mind to reason about
  correctness, which directly reduces the time and error rate of every
  future change, not only the current one.
- **Fewer places for bugs to hide.** Hoare's framing is precise here.
  complexity does not remove deficiencies, it hides them behind machinery
  that makes them harder to see. A simpler implementation surfaces its own
  bugs more readily during both review and testing.
- **Faster onboarding.** New team members can become productive contributors
  sooner in a codebase with fewer unnecessary abstractions to learn before
  they can safely make a change.
- **Cheaper, more confident refactoring.** Code with less structural
  entanglement can be changed with a smaller blast radius, because fewer
  other pieces of the system depend on its internal shape.
- **Reduced surface area for accidental complexity to compound.** Complexity
  tends to breed complexity. an unnecessary abstraction invites a second
  developer to build on top of it, entrenching a design decision that was
  never justified in the first place. Refusing the first unnecessary layer
  prevents this compounding.

Negative:

- **Real rework when a speculative need turns out to be real after all.**
  Because KISS deliberately declines to build for needs that have not yet
  arrived, some fraction of the time those needs do arrive, and the team
  pays a real, sometimes substantial, refactoring cost that a more general
  design from the start would have avoided. This cost is genuine and should
  not be minimized. it is the actual price paid for the far larger and more
  common savings from not over-building for needs that never arrive.
- **Risk of under-engineering being mistaken for KISS.** Because KISS carries
  social approval ("keeping it simple" sounds like good engineering
  judgment), it is sometimes invoked to justify skipping essential
  correctness handling, error handling, or edge-case coverage that the
  problem genuinely requires. This is a misuse of the principle, but the
  fact that it is a common misuse is itself a real, practical cost of having
  a principle whose name is so easy to invoke without engaging its
  substance.
- **Judgment-dependent, not mechanically checkable.** Unlike a rule such as
  "no function longer than fifty lines," KISS requires a human judgment call
  about what counts as essential versus accidental complexity for the
  specific problem at hand, which means it is applied inconsistently across
  a team unless the team explicitly discusses and calibrates its
  application, for example during code review.
- **Local simplicity can create global inconsistency.** A "simple" one-off
  choice that ignores the conventions and infrastructure the rest of the
  codebase already uses can be simple in isolation and complex in context,
  because it forces every future reader to learn and reconcile a second way
  of doing the same thing.

## 11. Failure modes and misuse

- **Symptom.** A feature ships with an obvious edge case unhandled, and when
  asked about it the author says "I kept it simple." **Cause.** KISS was
  invoked to justify dropping essential complexity, the complexity actually
  demanded by the problem, rather than accidental complexity, the complexity
  the implementation added on its own. **Fix.** Separate the two explicitly
  before invoking the principle. list the requirements the problem actually
  imposes, and confirm they are all still met, before evaluating design
  options for unnecessary machinery. If dropping the edge case is a
  legitimate scoping decision, it should be stated and agreed as a scoping
  decision, not smuggled in under the KISS label.

- **Symptom.** Code review pushback of "this is too simple, what about
  future requirement X" recurs on every pull request, and the codebase
  slowly fills with parameters, flags, and abstraction layers that no
  current caller uses. **Cause.** The team is treating imagined future
  requirements as though they were current ones, which is the opposite
  failure from the first. over-engineering disguised as prudence, sometimes
  called "speculative generality." **Fix.** Apply the speculative-requirement
  filter from dimension 5 explicitly in review. ask for the name of the
  concrete, current caller that needs the flexibility being requested. If
  none exists, the flexibility is deferred, not built, and the future
  requirement is captured as a comment or ticket instead of code.

- **Symptom.** A "simple" rewrite of a subsystem ships, passes its own
  tests, and then a wave of production incidents follows over the next few
  weeks as callers that depended on the previous system's less obvious
  behaviors break one by one. **Cause.** The rewrite was judged simple by
  looking only at the new code in isolation, without accounting for its
  entanglement with existing callers, configuration, and downstream
  consumers, which is exactly the entanglement axis Hickey's definition of
  simplicity is meant to measure. **Fix.** Before judging a redesign simple,
  enumerate its actual callers and integration points, not only its internal
  structure, and verify the entanglement count against the system as it
  exists, not against an idealized version of it.

- **Symptom.** Two engineers disagree sharply about whether a design is
  "simple," each confident the other is wrong, and the disagreement does not
  resolve with more discussion. **Cause.** One or both engineers are
  conflating simplicity with familiarity, per Hickey's simple-versus-easy
  distinction. the design that feels simple to the engineer who has used the
  pattern before may be objectively more entangled than the alternative, and
  vice versa. **Fix.** Reframe the disagreement explicitly around
  entanglement, not familiarity. ask each engineer to name what the design
  depends on and is coupled to, not how comfortable they are writing it.

- **Symptom.** A hand-rolled implementation of a well-known, hard-to-get-right
  piece of logic (a date/time library, a cryptographic routine, a parser for
  a standard format) ships because "the standard library or the established
  package felt heavier than we needed." **Cause.** KISS was applied to line
  count or dependency count without weighing correctness risk, treating
  "fewer lines" as equivalent to "simpler" even in a domain where the
  well-tested, heavier option is structurally simpler in the sense that
  matters, because it entangles the team with fewer unverified edge cases.
  **Fix.** In domains with known, well-documented correctness hazards, weigh
  the entanglement with unverified behavior of the homegrown option against
  the entanglement with an external dependency, and default to the
  established option unless there is a concrete, demonstrated reason the
  hand-rolled version is actually simpler by the entanglement measure, not
  merely by line count.

## 12. Trade-off matrix

| Force | Keep It Simple (KISS) | YAGNI | DRY | Design Patterns / GoF abstraction |
|---|---|---|---|---|
| Primary target | Removing structural entanglement, not just code volume | Removing speculative features not yet needed | Removing duplicated knowledge | Providing a proven, named shape for a recurring structural problem |
| When flexibility is added | Only when a second, real, current caller demands it | Only when a real feature request demands it | Not directly about flexibility, about single source of truth | Often added preemptively to model an anticipated variation point |
| Risk of misuse | Under-serving essential complexity, or being invoked as a rhetorical stop sign | Being invoked to justify skipping known near-term requirements | Over-abstracting two coincidentally similar pieces of code into one, entangling them wrongly | Adding a pattern's machinery before the variation it models is real |
| Relationship to the others | The umbrella principle, YAGNI and disciplined DRY are specific tactics that serve it | A specific application of KISS to feature scope and timing | Can conflict with KISS when the "single source of truth" adds indirection two callers do not yet need | Can conflict with KISS when applied before a second real implementation exists, complements KISS once one does |
| Failure signature when absent | Codebase accretes unnecessary layers, flags, and generality | Team builds capabilities nobody asked for, delaying real, needed work | Same logic duplicated in multiple places drifts out of sync over time | Ad hoc, inconsistent solutions to a recurring structural problem, reinvented differently each time it appears |

## 13. Related and incompatible patterns

- **YAGNI (You Aren't Gonna Need It).** YAGNI is best understood as KISS
  applied specifically to feature and capability scope over time. do not
  build the capability now, on the speculation it will be needed later.
  Where KISS is the general discipline of minimizing structural
  entanglement in any design decision, YAGNI is its most direct and
  well-known corollary, focused on the timing of when work gets done at
  all. The two compose without tension in the overwhelming majority of
  cases, a YAGNI-scoped feature set, implemented, is very often also the
  KISS-simplest implementation of that feature set.
- **DRY (Don't Repeat Yourself).** DRY and KISS are frequently in genuine
  tension, not merely apparent tension. Removing a duplication by extracting
  a shared abstraction adds an indirection and a new point of entanglement
  between the two previously-independent call sites. if that duplication
  was coincidental rather than a genuine single source of truth, DRY has
  made the design less simple by Hickey's definition even though it has
  fewer total lines. The Rule of Three heuristic in dimension 8 exists
  specifically to mediate this tension. wait for a third real occurrence
  before trusting that a duplication is genuine rather than coincidental,
  which keeps DRY subordinate to, and in service of, KISS rather than
  opposed to it.
- **Separation of Concerns.** Separation of Concerns and KISS are usually
  allies. separating unrelated responsibilities into distinct units reduces
  the entanglement within each unit, which is exactly what KISS asks for.
  The tension appears only when separation is taken further than the
  problem's actual seams warrant, producing many small, individually simple
  units whose interactions are more complex to reason about than a single,
  slightly larger unit would have been. KISS asks the designer to evaluate
  entanglement at the level of the whole design, not only within each
  individual piece.
- **Single Responsibility Principle.** SRP is a structural rule that, applied
  well, tends to produce KISS-aligned designs, because a unit with one
  responsibility has fewer reasons to change and therefore fewer entangled
  dependents. Applied over-zealously, splitting responsibilities finer than
  the domain's natural seams, it produces the same over-fragmentation risk
  described above for Separation of Concerns.
- **Incompatible or in tension with speculative generality and premature
  abstraction.** KISS is directly opposed to the practice, sometimes called
  speculative generality, of designing an abstraction to cover variation
  that has not yet been observed in real usage. This is not a named pattern
  in the sense the rest of this catalog uses, but it is the most common
  concrete thing KISS argues against, and it is worth naming explicitly
  because it frequently arrives disguised as another legitimate pattern (a
  Strategy interface with one strategy, a plugin system with one plugin, a
  configuration layer for a value that has never varied).

## 14. Refactoring path in and out

Introducing more discipline around KISS into an existing codebase, in order.

1. **Establish an entanglement vocabulary in code review**, before touching
   any code. Agree as a team on the specific question to ask about a new
   abstraction. "which current caller needs this," not "might we need this
   someday." Naming the question explicitly is what turns KISS from a vague
   slogan into an actionable review practice.
2. **Audit existing unused flexibility.** Search for abstract base classes
   with a single implementation, interfaces with a single implementer,
   configuration options that have never been set to a non-default value,
   and feature flags that have been permanently on or off for months. These
   are the concrete, low-risk targets for the "delete first" refactor from
   dimension 8.
3. **Delete or inline the unused flexibility, one piece at a time, each with
   its own small change.** Removing an unused abstraction is usually a
   mechanical, low-risk refactor (inline the single implementation, remove
   the interface, remove the unused parameter), and doing it as small,
   isolated changes rather than one large sweep keeps each change reviewable
   and reversible.
4. **Re-run the test suite and observe production behavior after each
   deletion**, not only at the end of the sweep, since the goal is confidence
   that removed flexibility was genuinely unused, not merely untested.
5. **Capture the pattern for future decisions.** Where the audit repeatedly
   finds the same category of unnecessary complexity (a config system nobody
   configures, a plugin architecture with one plugin), record that pattern
   explicitly as a team convention to watch for, so the same accidental
   complexity does not simply grow back.

Removing KISS discipline, or recognizing when a KISS-simple design must give
way to real complexity, in order.

1. **Confirm a second, real, current consumer with a genuinely different
   need has actually arrived.** Not a hypothetical one, a concrete pull
   request, ticket, or production requirement.
2. **Introduce the minimal abstraction that serves both current consumers**,
   not a general one sized for consumers that do not yet exist. This is the
   moment, and the only moment, at which the Rule of Three or an equivalent
   heuristic licenses extraction.
3. **Update the design's documentation or comments to record why the
   abstraction now exists**, naming the two concrete callers that justify
   it, so a future reader auditing for unused flexibility (step 2 of the
   introduction path above) can quickly confirm the abstraction is earning
   its keep rather than re-deriving the justification from scratch.
4. **Re-evaluate periodically as usage evolves.** An abstraction that was
   genuinely justified by two real callers can become unjustified again if
   one of those callers is later removed or the two converge on identical
   behavior, the audit step from the introduction path applies continuously,
   not only once.

## 15. Testing and verification

KISS-aligned code is, almost definitionally, easier to test, because lower
structural entanglement means fewer collaborators to mock, stub, or set up
before a unit's behavior can be exercised in isolation. A function that takes
explicit arguments and returns a value, with no hidden dependency on shared
mutable state, a global, or a framework lifecycle, can be tested directly with
example-based tests and requires no test double at all. This is a direct,
practical consequence of the simplicity Hickey describes. an untangled unit is
also an independently testable unit.

Verifying that KISS is actually being applied, as opposed to merely believed
to be applied, is harder than verifying most structural patterns, because
there is no compiler check for "unnecessary abstraction." The closest
practical techniques are these.

- **Coverage of the abstraction's call sites, not only its internals.** If a
  test suite exercises an interface's single implementation but never
  exercises a second implementation or a second call pattern, that is a
  strong, checkable signal the abstraction may be unjustified speculative
  generality rather than an earned abstraction.
- **Mutation testing on the "flexibility" surface.** Deliberately break a
  configuration option, a strategy branch, or a plugin hook and observe
  whether any test fails. If nothing fails, nothing is exercising that
  flexibility, which is direct evidence it is unused complexity rather than
  a genuinely load-bearing design choice.
- **Cyclomatic complexity as a quantitative proxy.** Thomas McCabe's
  cyclomatic complexity metric, the count of linearly independent paths
  through a unit of code derived from its control-flow graph, is a widely
  used, mechanically computable proxy for one dimension of KISS. a unit
  with an unusually high path count relative to its peers in the same
  codebase is a concrete, checkable candidate for simplification (Thomas J.
  McCabe, "A Complexity Measure," IEEE Transactions on Software Engineering,
  vol. SE-2, no. 4, December 1976). It is a proxy, not a proof. a function
  can have low cyclomatic complexity and still be structurally entangled
  through hidden shared state that the metric cannot see, and a function
  with legitimately high branch count from essential complexity should not
  be flagged as a KISS violation merely because the number is high.
- **Review checklist adherence, tracked over time.** Since the strongest
  verification tool for KISS is the human question "which current caller
  needs this," teams that want to verify the discipline is holding can track,
  informally, how often that question is asked and answered with a concrete
  name in review threads, versus how often new flexibility ships
  unquestioned.

## 16. Observability signals

KISS itself is a design-time and review-time discipline, not a runtime
behavior, so it has no direct runtime telemetry the way a caching layer or a
retry policy does. The signals that indicate whether KISS is holding in a
codebase are structural and process signals rather than production metrics.

- **Rising cyclomatic complexity or a rising count of configuration options
  and feature flags over time**, tracked per module via static analysis in
  CI, is a leading indicator that accidental complexity is accumulating
  faster than it is being removed.
- **Dependency count and dependency graph depth**, tracked at build time, is
  a direct, checkable measure of one concrete form of complexity KISS
  targets. each additional third-party dependency, and each additional
  transitive dependency it drags in, is a unit of entanglement with code the
  team does not control.
- **Time-to-first-productive-change for new contributors**, tracked
  informally through onboarding retrospectives, is a strong, if lagging,
  human signal. a codebase where new engineers consistently take a long time
  to feel safe making their first change is a codebase carrying more
  cognitive entanglement than its actual requirements justify.
- **The ratio of abstraction points to their real implementations**,
  spot-checked periodically (how many interfaces have exactly one
  implementer, how many strategy classes have exactly one strategy in
  production use), is the most direct structural check against speculative
  generality specifically, and can be automated as a lightweight static
  analysis pass over the codebase.
- **Incident postmortems that cite "we didn't understand how this
  interacted with X."** A recurring root cause in incident reviews that
  points to unexpected interaction between components, rather than to a
  straightforward logic error in one component, is a strong qualitative
  signal that entanglement in the system exceeds what the team can reliably
  reason about, and is exactly the failure mode KISS aims to prevent.

## 17. Security and privacy implications

KISS has a genuine, well-documented positive relationship with security, and
a genuine, equally real risk of misapplication in the opposite direction, and
both deserve to be stated plainly rather than treated as a single uniform
claim.

On the positive side, a smaller, less entangled attack surface is easier to
reason about correctly, and this is a widely accepted principle in security
engineering independent of its software-design framing. fewer code paths mean
fewer places an attacker-controlled input can reach an unintended state, fewer
external dependencies mean a smaller supply chain to audit, and a design with
explicit, direct data flow is easier for a reviewer to trace for an injection
or an authorization bypass than a design where the same data passes through
several layers of generic, configuration-driven indirection before reaching
its use. Removing unused code paths, unused configuration options, and unused
feature flags per the audit in dimension 14 also removes attack surface, not
only cognitive load, since an unused branch can still be reachable by a
sufficiently unexpected input and is by definition untested against
adversarial conditions.

On the negative side, KISS should never be invoked to justify a hand-rolled,
"simpler" implementation of a security-sensitive primitive, cryptographic
routines, authentication and session handling, input parsing for a format
with a well-known history of parser vulnerabilities, in preference to an
established, audited library. This is the specific instance of the
non-applicability boundary from dimension 4 and the failure mode from
dimension 11 that matters most in a security context. a homegrown routine is
frequently simpler by a superficial line-count measure and dramatically more
complex, and more dangerous, by the structural entanglement measure that
actually counts, because it entangles the system with every edge case the
established library has already found and fixed and the homegrown version has
not yet encountered.

On privacy specifically, minimizing the amount of personal data a system
collects, stores, or passes between components is itself a direct application
of KISS. each additional field of personal data collected, stored, or
transmitted is an additional point of entanglement, an additional thing every
future reader must reason about correctly, an additional item that must be
protected, and an additional item that must be accounted for in a data
subject access request or a breach notification. Data minimization and KISS
point in the same direction for exactly the reason Hickey's definition
predicts. unnecessary data is unnecessary entanglement, no different in kind
from unnecessary code.

## 18. References

- Wikipedia, "KISS principle," verified 2026-08-02, https://en.wikipedia.org/wiki/KISS_principle
- C.A.R. Hoare, "The Emperor's Old Clothes," 1980 ACM Turing Award Lecture, published in Communications of the ACM, vol. 24, no. 2, February 1981, p. 76.
- Frederick P. Brooks Jr., "No Silver Bullet. Essence and Accidents of Software Engineering," IEEE Computer, vol. 20, no. 4, April 1987; summarized in Wikipedia, "No Silver Bullet," verified 2026-08-02, https://en.wikipedia.org/wiki/No_Silver_Bullet
- Rich Hickey, "Simple Made Easy," Strange Loop conference, 20 October 2011, InfoQ recording, verified 2026-08-02, https://www.infoq.com/presentations/Simple-Made-Easy/
- Martin Fowler, "Yagni," bliki, verified 2026-08-02, https://martinfowler.com/bliki/Yagni.html
- Wikipedia, "Unix philosophy," Doug McIlroy formulation, verified 2026-08-02, https://en.wikipedia.org/wiki/Unix_philosophy
- SQLite Consortium, "Why SQLite Uses C," verified 2026-08-02, https://www.sqlite.org/whyc.html
- Go Proverbs, collected from Rob Pike's 2015 Gopherfest talk, verified 2026-08-02, https://go-proverbs.github.io/
- Thomas J. McCabe, "A Complexity Measure," IEEE Transactions on Software Engineering, vol. SE-2, no. 4, December 1976 (the source of cyclomatic complexity, cited in dimension 15 as a testing proxy; formula and definition drawn from established software engineering knowledge of this widely taught metric, cross-referenced against Wikipedia, "Cyclomatic complexity," not independently re-fetched as a live URL for this entry).

## Code examples

The pattern here is a discipline applied to design decisions, not a
structural shape with a canonical implementation, so the code below
illustrates the same requirement solved two ways. a KISS-violating version
that adds unjustified flexibility for a single, current, concrete need, and
the KISS-aligned version that meets the identical requirement with less
entanglement. All three were run against the installed toolchains on this
machine.

### TypeScript

```typescript
// over-engineered. a generic "discount strategy" system built for one
// concrete discount rule that has never varied.
interface DiscountStrategy {
  apply(total: number): number;
}
class PercentageDiscount implements DiscountStrategy {
  constructor(private readonly percent: number) {}
  apply(total: number): number {
    return total - total * (this.percent / 100);
  }
}
class DiscountEngine {
  constructor(private readonly strategy: DiscountStrategy) {}
  checkout(total: number): number {
    return this.strategy.apply(total);
  }
}

// KISS. the same requirement, one real caller, no interface, no engine.
function applyTenPercentDiscount(total: number): number {
  return total - total * 0.1;
}

const overEngineered = new DiscountEngine(new PercentageDiscount(10));
console.log("over-engineered", overEngineered.checkout(200));
console.log("kiss", applyTenPercentDiscount(200));
```

```text
$ npx tsc --strict --target es2020 keep-it-simple.ts && node keep-it-simple.js
over-engineered 180
kiss 180
```

### Python

```python
# over-engineered. a plugin registry built for a single, fixed validator.
from typing import Callable, Dict

VALIDATORS: Dict[str, Callable[[str], bool]] = {}


def register_validator(name: str):
    def decorator(fn: Callable[[str], bool]):
        VALIDATORS[name] = fn
        return fn
    return decorator


@register_validator("email")
def _validate_email(value: str) -> bool:
    return "@" in value and "." in value


def validate(name: str, value: str) -> bool:
    return VALIDATORS[name](value)


# KISS. the same requirement, one real caller, no registry.
def is_valid_email(value: str) -> bool:
    return "@" in value and "." in value


if __name__ == "__main__":
    print("over-engineered", validate("email", "a@b.com"))
    print("kiss", is_valid_email("a@b.com"))
```

```text
$ python3 keep_it_simple.py
over-engineered True
kiss True
```

### Go

```go
package main

import "fmt"

// over-engineered. an interface and constructor for a single, fixed
// tax rate that has never had a second implementation.
type TaxCalculator interface {
	Calculate(amount float64) float64
}

type flatRateTax struct {
	rate float64
}

func (f flatRateTax) Calculate(amount float64) float64 {
	return amount * f.rate
}

func newTaxCalculator(rate float64) TaxCalculator {
	return flatRateTax{rate: rate}
}

// KISS. the same requirement, one real caller, no interface.
func calculateTax(amount float64) float64 {
	return amount * 0.19
}

func main() {
	calc := newTaxCalculator(0.19)
	fmt.Println("over-engineered", calc.Calculate(100))
	fmt.Println("kiss", calculateTax(100))
}
```

```text
$ go run keep_it_simple.go
over-engineered 19
kiss 19
```

Java and Rust were not run for this entry. The same demonstration, a small,
single-purpose function versus an unjustified interface or trait built for a
single implementer, translates directly into either language without a
language-specific twist worth showing separately, so a fourth and fifth copy
of the identical illustration was judged to add length without adding
information.
