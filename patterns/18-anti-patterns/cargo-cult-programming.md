---
name: Cargo Cult Programming
slug: cargo-cult-programming
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Cargo Cult Software Engineering, Ritual Programming, Copy-Paste-Without-Understanding]
first_described: "Term appears in the Jargon File version 2.5.1, January 1991, per the term's own etymology on Wikipedia; the underlying metaphor is Richard Feynman's 1974 Caltech commencement address 'Cargo Cult Science'"
maturity: canonical
related: [copy-paste-programming, golden-hammer, boat-anchor, template-method, code-review, dead-code]
incompatible_with: [code-review, test-driven-development]
verified: 2026-08-02
---

# Cargo Cult Programming

## 1. Name, aliases, and lineage

The canonical name is Cargo Cult Programming. According to the term's own
Wikipedia entry, the phrase "cargo-cult programming" first appeared in
version 2.5.1 of the Jargon File, released in January 1991
([Wikipedia, Cargo cult programming](https://en.wikipedia.org/wiki/Cargo_cult_programming),
verified 2026-08-02). The Jargon File is the long-running glossary of hacker
slang later published in print as Eric S. Raymond's *The New Hacker's
Dictionary* (MIT Press, 1996). The same Wikipedia article gives the lead
definition, restated here nearly word for word, as a style of computer programming
characterized by the ritual inclusion of code or program structures that
serve no real purpose, occurring when a programmer copies some existing
code structure or programming style without understanding why the original
code was designed that way. That is the definition this entry uses
throughout.

The word cargo cult is not a software coinage at all. It names a real
category of religious and social movements documented across Melanesia,
most visibly on islands used as staging bases during the Second World War,
where some communities that had observed Allied forces receiving enormous
shipments of manufactured goods by air and sea built airstrips, control
towers, and radio-shaped objects out of local materials after the war
ended, hoping the ritual reenactment would summon the cargo again. Software
engineering did not borrow that anthropological term directly. It borrowed
it through an intermediate, better documented step, the physicist Richard
Feynman's 1974 commencement address at the California Institute of
Technology, later published as the essay "Cargo Cult Science" in the June
1974 issue of *Engineering and Science*, volume 37, number 7, pages 10
through 13, and reprinted as the closing chapter of *Surely You're Joking,
Mr. Feynman. Adventures of a Curious Character* by Richard P. Feynman and
Ralph Leighton, W. W. Norton and Company, 1985, pages 338 through 346
(publication details verified via
[Wikipedia, Cargo cult science](https://en.wikipedia.org/wiki/Cargo_cult_science),
verified 2026-08-02). Feynman used the South Pacific cargo cults as a
metaphor for research that reproduces the outward form of science, the
procedures, the write-ups, the presentations, without the inward discipline
of testing a hypothesis against reality. His summary line, paraphrased
across many secondary sources as the islanders build everything to look
exactly right yet the airplanes still do not land, is the exact shape
software engineers reached for a decade and a half later to describe code
that looks like the source it was copied from but does not do what that
source did, because the copier never understood which parts of the original
mattered.

A second, distinct but closely related coinage belongs to Steve McConnell,
who wrote a short opinion column titled "Cargo Cult Software Engineering" in
*IEEE Software*, volume 17, issue 2, March and April 2000, pages 11 through
13, and later folded the same argument into his book *Professional Software
Development*, Addison-Wesley, 2003, pages 23 through 26 (bibliographic
details verified via
[Wikipedia, Cargo cult programming](https://en.wikipedia.org/wiki/Cargo_cult_programming),
verified 2026-08-02). McConnell's version targets the organizational level
rather than a single function or file, a company that adopts a practice it
saw at a successful competitor, such as mandatory unpaid overtime, without
the underlying condition that made the practice work there, such as a
genuinely motivated team solving a problem it cares about. This entry
treats McConnell's usage as the same anti-pattern at a different scale.
Individual cargo cult programming is one function copied without its
reasoning; organizational cargo cult software engineering is one practice
adopted without its precondition. The mechanism, ritual imitation of form
absent the understanding that made the form correct, is identical at both
scales, which is why both are grouped under one alias set here rather than
split into two entries.

## 2. Problem and context

A developer under time pressure needs code that solves a problem they do
not fully understand, in a domain they have not fully learned, often on a
deadline that leaves no room to read the relevant specification, the
relevant algorithm, or the relevant library documentation from first
principles. A working example exists nearby, a Stack Overflow answer, a
tutorial blog post, a neighboring function in the same file, a snippet a
teammate pasted in a chat, or a pattern the developer half-remembers from a
previous job. The example compiles, it passes the one test the developer
runs by hand, and the deadline is met. The problem this anti-pattern names
is what happens next. the developer never goes back to learn why the
example was shaped the way it was, so the borrowed code becomes a black
box that is reproduced again in the next file, and the next, entirely by
visual imitation rather than by reasoning about the forces that shaped the
original.

The context in which this becomes damaging, rather than merely inelegant,
is any context where the borrowed code's correctness depended on a
condition that is not present at the new call site. A retry loop with
exponential backoff is correct around a flaky network call and actively
harmful around a call that always fails deterministically, because it
converts a fast, clear failure into a slow, confusing one. A memoization
decorator is correct around a pure function and silently wrong around a
function whose result changes between calls, because it converts a live
value into a frozen one without raising any error at all. A broad
exception handler that swallows every failure is defensible in a
best-effort logging path and dangerous around a payment authorization
call, because it converts a failed charge into what looks, from the
caller's perspective, like a successful one. In every one of these cases
the borrowed code is not wrong in isolation. it was correct in its
original context. What is missing is the developer's understanding of
which features of that context made it correct, so the code is
transplanted into a new context where those features do not hold, and
nothing in the code itself signals the mismatch.

Cargo cult programming is distinguished from ordinary code reuse by exactly
one property. the copier cannot explain, in their own words, why each part
of the copied structure exists. A developer who copies a retry-with-backoff
implementation and can explain why the base delay is 100 milliseconds, why
the multiplier is 2, why there is a maximum retry count, and why the jitter
term exists, has reused code responsibly, even if every line is
byte-for-byte identical to the source. A developer who copies the same
implementation and cannot answer any of those four questions has cargo
culted it, even if they then go on to tune the numbers by trial and error
until the tests pass. The observable code is often indistinguishable
between the two cases. what differs, and what this pattern's failure modes
in dimension 11 are built to surface, is whether the code's structure
tracks the actual forces of the new problem or merely the visual memory of
an old one.

## 3. Forces

- **Deadline pressure against comprehension cost.** Understanding an
  unfamiliar algorithm, library, or subsystem well enough to derive a
  correct solution from first principles almost always costs more wall
  clock time than finding and adapting an example that already looks
  correct. Cargo cult programming is the anti-pattern's answer to this
  force taken to its extreme, where the developer stops paying any of the
  comprehension cost and pays only the copying cost.
- **Perceived authority of the source.** A snippet that appears in an
  official framework's own documentation, in a highly upvoted answer, or in
  a senior colleague's code carries implicit social proof that discourages
  questioning it. The more authoritative the source looks, the less likely
  a developer under pressure is to interrogate whether every part of it
  transfers to the new context, which is precisely backward, since an
  authoritative source is more likely to contain context-specific
  reasoning that a less careful source would have omitted entirely.
- **Visual similarity against semantic equivalence.** Code that looks the
  same as a working example is easy to produce by pattern matching, but
  looking the same and being semantically appropriate for the new context
  are unrelated properties. This is the same force Feynman named directly.
  the outward form is trivially reproducible; the inward reasoning that
  made the form correct is not.
- **Short-term green build against long-term maintainability.** Cargo
  culted code frequently passes the tests that exist at the moment it is
  written, because those tests were often written by the same developer
  under the same lack of understanding, or because the tests exercise only
  the happy path the borrowed example was designed for. The force here
  favors whatever makes the build green today over whatever will still be
  correct when the untested edge case eventually occurs.
- **Fear of breaking something that already works.** Once cargo culted code
  ships and survives in production for a while, later developers are
  reluctant to remove parts of it that look purposeful but are not,
  because nobody can be certain a given line is dead weight rather than a
  fix for a subtle bug someone else already hit once. This force is a
  direct cause of the boat anchor and dead code that this anti-pattern
  tends to leave behind, and it compounds over time because each layer of
  cargo culted code makes the next developer even less willing to remove
  the layer beneath it.

## 4. Applicability and non-applicability

This is an anti-pattern. It has no case in which reaching for it on
purpose is correct. The applicability section below instead names the
situations where a developer is genuinely at risk of falling into it, so
those moments can be recognized and handled deliberately, and the
non-applicability section names the situations that resemble it but are
not the same failure at all.

### Genuinely at risk of it

- Copying an example from documentation, a tutorial, or an AI coding
  assistant's suggestion into a new file without reading the surrounding
  prose that explains the example's assumptions.
- Adapting boilerplate from a similar but not identical existing module in
  the same codebase, where the new module's requirements diverge from the
  old one's in ways the copier has not enumerated.
- Adding a defensive pattern, such as a retry loop, a lock, a cache, or a
  broad exception handler, because that is what the team always does,
  without a specific failure mode in mind that the pattern is meant to
  prevent.
- Configuring infrastructure as code, a build pipeline, or a linter ruleset
  by copying an existing team's configuration wholesale and never revisiting
  which settings apply to the new project's actual constraints.

### Not this anti-pattern

- **Deliberate, understood code reuse.** Extracting a function, adopting a
  library, or applying a named design pattern because the developer has
  verified the new context matches the conditions the reused code assumes
  is ordinary engineering, not cargo culting, however visually similar the
  result is to a copied snippet.
- **Following a documented team convention.** A house style enforced by a
  linter or a style guide, where the reasoning is written down and
  available even if the individual developer has not personally derived
  it, is a governance mechanism, not a ritual, provided the convention's
  rationale is discoverable rather than lost.
- **Test-driven development's red, green, refactor cycle producing code
  that looks like a known pattern.** Arriving at a Strategy or Template
  Method shape because tests forced that shape out through refactoring is
  the opposite of cargo culting. the structure follows from verified
  requirements rather than from visual imitation.
- **Boilerplate mandated by a language, framework, or protocol**, such as a
  constructor a language requires for every class or a health check
  endpoint a platform requires for every service. Reproducing required
  scaffolding is not ritual imitation, because the scaffolding has a real,
  checkable purpose even when a given developer has not personally traced
  why the platform requires it.
- **Copy-Paste Programming**, the closely related anti-pattern documented
  separately in this repository. that entry concerns duplicating code the
  developer *does* understand, to avoid the design work of a shared
  abstraction; this entry concerns reproducing code the developer does
  *not* understand, to avoid the comprehension work of learning why it is
  shaped the way it is. The two frequently occur together but are distinct
  failures with distinct fixes, see dimension 13.

## 5. Structure

Cargo cult programming has no static structure of participants in the way
a design pattern does, because it is a process failure rather than an
architectural shape. The entry describes its participants as the roles
present whenever the anti-pattern occurs.

- **The Source Artifact.** The original code, configuration, or practice
  that worked correctly in its own context. It carries implicit
  preconditions that made it correct there. these preconditions are almost
  never written down alongside the artifact itself.
- **The Copier.** The developer who reproduces the Source Artifact's visible
  form into a New Context without first extracting and checking its
  preconditions against that New Context.
- **The New Context.** The call site, module, or organization the copied
  form is placed into. It may or may not satisfy the Source Artifact's
  original preconditions; the Copier has not verified which.
- **The Ritual Form.** What actually gets reproduced, the syntactic shape,
  the variable names, the surrounding comments, the sequence of API calls.
  This is the only part of the Source Artifact that visual copying can
  transfer, because it is the only part that is visible in the source text.
- **The Missing Rationale.** The reasoning that connected the Source
  Artifact's preconditions to its Ritual Form. It exists, if it exists at
  all, only in the mind of whoever wrote the Source Artifact, or in
  documentation the Copier did not read. Its absence from the New Context
  is the defining property of this anti-pattern.

## 6. ASCII structure diagram

```
   Source Artifact                         New Context
  (worked HERE, because                  (Copier assumes it
   of preconditions P)                    will work here too)
  +------------------------+             +------------------------+
  |  Ritual Form            |   copied   |  Ritual Form           |
  |  (syntax, names,        | =========> |  (identical syntax)    |
  |   call sequence)        |  visually  |                        |
  +------------------------+             +------------------------+
  |  Missing Rationale      |    NOT     |  Missing Rationale     |
  |  (why P made this       |  copied    |  (never reconstructed) |
  |   correct)              |  --X-->    |                        |
  +------------------------+             +------------------------+
  |  Preconditions P        |    NOT     |  Preconditions ?       |
  |  (e.g. call is network  |  checked   |  (unknown whether P    |
  |   I/O and can           |  --X-->    |   holds here at all)   |
  |   transiently fail)     |            |                        |
  +------------------------+             +------------------------+

  Result. Ritual Form is present in both places.
          Whether Preconditions P hold in the New Context is unverified.
          Correctness in the New Context is therefore a coincidence,
          not a property the Copier established.
```

## 7. Dynamics

```
1. DEADLINE PRESSURE arrives. a feature or fix is due, and the
   developer does not already know how to build the relevant piece.

2. SEARCH. the developer finds a Source Artifact that appears to
   solve a similar-looking problem (documentation example, a forum
   answer, a sibling module, an AI suggestion, a past project).

3. VISUAL MATCH. the developer confirms the Source Artifact's
   surface shape resembles what they believe they need, WITHOUT
   deriving from the New Context's actual requirements what shape
   is needed.

4. TRANSPLANT. the Ritual Form is copied into the New Context,
   usually with surface-level renaming (variables, endpoints,
   identifiers) but without re-deriving each structural choice.

5. LOCAL VERIFICATION. the developer runs the one test scenario at
   hand. If it passes, the transplant is treated as validated.
   -- The test scenario is frequently the ONLY path that happens
      to satisfy the Source Artifact's original preconditions,
      because it is the path the developer had in mind when they
      went looking for an example in the first place.

6. SHIP. the code merges. It now exists as a new Source Artifact
   in the codebase, available for the NEXT developer to copy from,
   with the Missing Rationale one generation further removed.

7. LATENT MISMATCH. some later input, load pattern, or code path
   exercises a case where the New Context's actual preconditions
   diverge from the original Preconditions P. Because the Ritual
   Form gives no signal that it depends on P, nothing in the code
   itself indicates a mismatch is occurring.

8. FAILURE SURFACES, often far from the transplant site and far
   in time from step 4, as one of the failure modes in dimension
   11 (a masked bug, a swallowed error, a false sense of resilience,
   a performance cliff). Root-causing it requires reconstructing the
   Missing Rationale from scratch, which is strictly harder than
   deriving it would have been at step 3, because the investigator
   must first discover THAT a rationale is missing before they can
   look for it.
```

## 8. Implementation variants

Cargo cult programming shows up differently depending on where in the
software lifecycle the ritual imitation happens.

- **Snippet-level cargo culting.** The most common variant. a function, a
  regex, an algorithm implementation, or a small utility is copied from a
  search result or a neighboring file. This is the variant illustrated in
  dimension 9's code example.
- **Configuration cargo culting.** Infrastructure-as-code files, CI
  pipeline files, linter rulesets, and dependency manifests are copied
  wholesale from a previous project. Because configuration is declarative
  and rarely executed step by step by a human, it is especially easy to
  carry forward settings whose purpose nobody in the new project can state,
  and especially hard to notice when one of those settings is actively
  wrong for the new project.
- **API usage cargo culting.** A library's API is used in a pattern copied
  from an example, including calls that were only necessary for that
  example's specific setup, such as an explicit database connection
  teardown call that the new context's connection pooling library already
  handles automatically, producing redundant or conflicting behavior.
- **Security control cargo culting.** A cryptographic routine, an
  authentication check, or an input sanitization step is copied from a
  tutorial without understanding its threat model, which is one of the
  most consequential variants because a security control that looks right
  but is subtly wrong, for example a signature verification that accepts
  the wrong algorithm, provides a false sense of protection that is worse
  than providing none, since it removes the incentive to add a real
  control later.
- **Organizational cargo culting, per McConnell.** A team adopts a process,
  a ceremony, a tool, or a management practice observed at a successful
  organization, such as daily standups, a specific branching strategy, or
  mandatory code review thresholds, without the precondition that made the
  practice effective there, such as a small enough team for a standup to
  stay useful or a codebase stable enough for the branching strategy's
  assumptions to hold.
- **AI-assisted cargo culting.** A large language model produces plausible,
  well-formatted code for a prompt, and the developer accepts it because it
  compiles and looks idiomatic, without independently verifying the
  reasoning behind each structural choice the model made. This is
  the same shape as copying from a human-authored tutorial. the
  Source Artifact's apparent fluency and confidence substitute for actual
  verification, and the risk scales with how convincingly the output is
  formatted rather than with how correct it is.

## 9. Known production uses

Cargo cult programming, like copy-paste programming, is rarely named by an
organization about its own code, since it is a diagnosis applied after the
fact rather than a practice anyone advertises. The evidence for its
prevalence and its consequences comes from three independently verifiable
sources, the term's own sustained use in the software engineering
literature since 1991, the empirical security research that has measured
its downstream effect across many real codebases, and the static analysis tooling built to
catch the specific symptom, unused or unexplained code, that it commonly
leaves behind.

- **The 1991 Jargon File entry itself as a marker of prevalence.** A term
  is added to a live glossary of working practitioner slang only once the
  behavior it names is common enough that practitioners need a shared word
  for it. The Jargon File's inclusion of cargo-cult programming starting
  in version 2.5.1, January 1991, and its continued presence through later
  editions culminating in Eric S. Raymond's *The New Hacker's Dictionary*,
  MIT Press, 1996, is itself the earliest verifiable evidence that this was
  a recognized, named, recurring failure mode in real development shops by
  the early 1990s, well before the World Wide Web made copy-pasted code
  from search results the dominant vector it is today
  ([Wikipedia, Cargo cult programming](https://en.wikipedia.org/wiki/Cargo_cult_programming),
  verified 2026-08-02).
- **Acar, Backes, Fahl, Kim, Mazurek, and Stransky's controlled developer
  study.** "You Get Where You're Looking For. The Impact of Information
  Sources on Code Security," presented at the 2016 IEEE Symposium on
  Security and Privacy, San Jose, California, pages 289 through 305,
  assigned Android developers the same security-relevant coding tasks and
  varied only which information source they were permitted to use. The
  paper is confirmed to resolve as a genuine PDF document at
  <https://www.cs.umd.edu/class/fall2017/cmsc818O/papers/get-where-look.pdf>
  (verified 2026-08-02). Wikipedia's own citation of this paper, cross-checked
  in the same verification pass, reports that developers who relied on a
  general web search engine as their information source tended to write
  less secure code than developers who relied on the official Android
  documentation, even though the search-engine group's code was, by the
  paper's own framing, frequently more functional in the narrow sense of
  appearing to work
  ([Wikipedia, Cargo cult programming, citing Acar et al. 2016](https://en.wikipedia.org/wiki/Cargo_cult_programming),
  verified 2026-08-02). This is a direct, measured instance of the
  mechanism this entry describes at production scale. code copied from an
  authoritative-looking source passed the developers' own local checks
  while carrying security weaknesses the copiers had not verified were
  absent, which is precisely the difference between the Ritual Form and the Missing
  Rationale drawn in dimension 6.
- **ESLint's no-unused-vars rule as evidence of the tooling built around
  the pattern's residue.** ESLint's own documentation for the rule states
  that variables that are declared and not used anywhere in the code are
  most likely an error due to incomplete refactoring, and that such
  variables take up space in the code and can lead to confusion by readers
  ([ESLint documentation, no-unused-vars](https://eslint.org/docs/latest/rules/no-unused-vars),
  verified 2026-08-02). The rule ships enabled by default in ESLint's
  recommended configuration and runs on effectively every JavaScript and
  TypeScript project that adopts ESLint's baseline settings. While
  unused-variable detection targets the broader family of leftover code
  rather than cargo culting specifically, it is the direct, industry-scale
  mechanism by which the Ritual Form left behind by cargo culted code,
  imports, parameters, and local variables copied along with a snippet but
  never actually exercised by the New Context, gets caught in continuous
  integration across a very large fraction of JavaScript and TypeScript
  codebases.
- **Steve McConnell's naming of the organizational variant.** McConnell's
  "Cargo Cult Software Engineering," *IEEE Software*, volume 17, issue 2,
  March and April 2000, pages 11 through 13, and its expansion in
  *Professional Software Development*, Addison-Wesley, 2003, pages 23
  through 26 (bibliographic details verified via
  [Wikipedia, Cargo cult programming](https://en.wikipedia.org/wiki/Cargo_cult_programming),
  verified 2026-08-02), documents this pattern being applied by named
  practicing organizations to their own process choices, in a
  peer-reviewed industry publication rather than an anonymous forum,
  which is independent evidence that the failure mode generalizes beyond
  individual snippets to entire adopted methodologies.

## 10. Consequences

### Positive

There are no positive consequences of the anti-pattern itself. Any benefit
observed is a benefit of the underlying practice of code reuse, which is
sound engineering when the Missing Rationale is actually recovered, and
which this entry is careful not to condemn, see dimension 4's
non-applicability list. What follows is the closest thing to a positive
case, stated honestly as a short-term, situational benefit rather than a
recommendation.

- Immediate velocity under deadline pressure, because visual copying is
  much faster than deriving a solution from the New Context's
  actual requirements, and this speed is real even though the resulting
  correctness is coincidental rather than established.
- A working example to react to. even flawed cargo culted code sometimes
  gives a team something concrete to critique in code review, which can be
  faster than reviewing a blank design, provided the review actually
  interrogates the code's rationale rather than merely confirming it looks
  familiar.

### Negative

- **Correctness by coincidence rather than by design.** The code works only
  to the extent that the New Context happens to share the Source
  Artifact's unstated preconditions, and nothing in the code signals when
  that stops being true, which is the structural root of every failure
  mode in dimension 11.
- **Compounding loss of institutional knowledge.** Every generation of
  copying removes the Missing Rationale one step further from anyone who
  could reconstruct it, since the second copier is working from the first
  copier's already-rationale-free version rather than from the true Source
  Artifact.
- **False confidence from a green build.** A test suite written by the same
  developer under the same lack of understanding tends to exercise only
  the paths the developer already had in mind, which is precisely the set
  of paths where the cargo culted code is most likely to happen to work.
- **Accumulation of dead or misleading structure.** Ritual Form elements
  that served the Source Artifact's original context but not the New
  Context, an unused parameter, an unnecessary lock, a superfluous null
  check, become boat anchor debris. nobody feels safe removing them
  because nobody can be certain they are not silently load-bearing.
- **Security regressions that pass local verification.** As the Acar et al.
  study in dimension 9 documents across many real codebases, copied security-relevant code
  can be functionally convincing while remaining substantively insecure,
  and the very fact that it appears to work removes the pressure to review
  it more closely.
- **Erosion of the organization's ability to change the code later.** A
  codebase where a large fraction of the logic is Ritual Form without
  Rationale is one where every refactor carries more risk, because the
  people doing the refactor cannot reliably distinguish load-bearing
  structure from vestigial structure without expensive investigation.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| A cache or memoization layer returns a value that is stale relative to the underlying data, and the bug reproduces intermittently, correlated with how recently the value changed rather than with any obvious input. | A caching pattern was copied onto a function whose output is not a pure function of its input, because the copier reproduced the caching mechanism without checking the purity precondition that made caching correct in the source. | Remove the cache and re-derive whether one is warranted from the New Context's actual read frequency and staleness tolerance; if warranted, add an explicit invalidation or expiry policy the team can name a reason for. |
| A retry loop makes a permanently failing operation take several seconds or minutes to report failure instead of failing immediately, and the delay is reproduced across many unrelated call sites in the codebase. | A retry-with-backoff pattern was copied from code that wrapped a transiently failing network call and applied to an operation whose failures are deterministic, such as invalid input or a missing resource, where retrying cannot change the outcome. | Classify the failure as transient or deterministic before adding retry logic; retry only transient failures, and fail fast, with a clear error, on deterministic ones. |
| A broad catch block is present around a critical operation, and when that operation fails in production, the caller proceeds as if it had succeeded, with no error surfaced anywhere. | An exception-swallowing pattern was copied from a best-effort logging or telemetry path, where swallowing failures is an accepted trade-off, and applied to a critical path such as a payment charge or a data write, where it hides a real failure. | Narrow the caught exception type to only the specific, expected failure, and for critical paths, propagate or explicitly handle every other failure rather than silently continuing. |
| A configuration file, pipeline definition, or infrastructure template carries settings that nobody on the current team can explain, and removing any one of them is treated as too risky to attempt. | The configuration was copied wholesale from a previous project's working configuration, transplanting settings whose purpose was specific to that project's constraints, which no longer hold. | Audit the configuration line by line against the current project's actual requirements, remove or re-justify each setting individually, and document the reason for each surviving line. |
| A security check, such as a signature verification or an input sanitizer, is present, appears to function in every test the team runs, and is later found by an external audit to accept input it should reject. | The check was copied from a tutorial or forum answer that solved a narrower or different threat model than the one the New Context actually faces, and the copier verified only that legitimate input passes, never that the specific illegitimate input the real threat model cares about is rejected. | Re-derive the check from the actual threat model, write a failing test for the specific attack the check must reject before writing or keeping the implementation, and prefer a maintained, audited library over a hand-copied routine wherever one exists. |
| A team adopts a process, such as daily standups or a specific branching model, that visibly worked at another organization, and morale or throughput does not improve, sometimes worsening, but the team keeps the process because that is how it is supposed to be done. | The organizational-level variant of the anti-pattern, per McConnell. the practice's form was adopted without the precondition, such as team size, codebase maturity, or genuine shared motivation, that made it effective at the source organization. | Identify the specific outcome the practice was meant to produce, verify whether the team's actual constraints support that outcome, and either adapt or drop the practice based on that verification rather than on its resemblance to a successful example. |

## 12. Trade-off matrix

| Force | Cargo Cult Programming | Copy-Paste Programming (understood duplication) | Deliberate abstraction via a named pattern (e.g. Strategy, Template Method) | Writing from first principles with no reference |
|---|---|---|---|---|
| Time to first working version | Fastest, since no comprehension work is done before copying. | Fast, comparable to cargo culting, but the developer can explain each line. | Slower, since the abstraction's shape must be designed or extracted deliberately. | Slowest, since every design decision is derived rather than borrowed. |
| Correctness confidence | Low and unverifiable by the developer who wrote it, since the rationale is unknown to them. | Moderate. correctness for the copied case is understood, but duplication risk (dimension 13) remains. | High, when the abstraction genuinely matches the problem's variability. | High, provided the developer's own reasoning is sound and reviewed. |
| Coupling to the source of the borrowed idea | None mechanically, but semantic coupling to unstated preconditions is total and invisible. | None mechanically; each copy is independent, per Copy-Paste Programming dimension 10. | Structural coupling to the chosen pattern's shape, which is visible and reviewable. | None, by construction. |
| Maintainability over time | Degrades, since later developers inherit code they also cannot fully explain, compounding dimension 10's institutional knowledge loss. | Stable but scales poorly with the number of copies needing the same future fix. | Improves, since the abstraction concentrates the logic that needs future changes. | Depends entirely on the quality of the original design, but at least the reasoning exists somewhere. |
| Risk under a changing requirement | Highest. nobody can predict which parts of the Ritual Form the new requirement will break, since the dependency between form and precondition was never mapped. | Moderate. each copy must be found and updated individually, but the impact of each is locally understood. | Lowest for changes the abstraction anticipated; can be high for changes it did not, per Golden Hammer. | Depends on the original design's foresight. |

## 13. Related and incompatible patterns

- **Copy-Paste Programming.** The two anti-patterns are frequently confused
  and frequently co-occur, but they are distinct along exactly one axis.
  Copy-Paste Programming duplicates code the developer understands, to
  avoid the design cost of extracting a shared abstraction; Cargo Cult
  Programming reproduces code the developer does not understand, to avoid
  the comprehension cost of learning why it works. A single instance of
  copied code can be both at once, duplicated and unexplained. The fix for
  each differs. Copy-Paste Programming is fixed by extracting a shared
  abstraction once the duplication's cost exceeds its benefit; Cargo Cult
  Programming is fixed by recovering the rationale before the code is kept
  at all, regardless of how many copies exist.
- **Golden Hammer.** Golden Hammer is the anti-pattern of applying a tool or
  pattern the developer *does* understand to every problem regardless of
  fit. Cargo Cult Programming can produce a Golden Hammer indirectly. once
  a cargo culted snippet ships successfully enough times, later developers
  may come to trust its Ritual Form as a general-purpose solution and start
  reaching for it deliberately, at which point the anti-pattern has
  transitioned from unexplained imitation into an equally unexamined but
  now-habitual tool choice.
- **Boat Anchor.** Cargo culted code that nobody dares remove because its
  purpose is unknown is a direct production mechanism for Boat Anchor
  debris, see dimension 10's discussion of dead-code accumulation.
- **Template Method.** The design pattern this anti-pattern is most often
  mistaken for at the syntactic level, since both can present as a fixed
  sequence of steps with some steps varying. The distinguishing question is
  whether the fixed steps were chosen because the domain genuinely requires
  that sequence, which is Template Method used correctly, or because that
  is what the copied example happened to contain, which is Cargo Cult
  Programming wearing Template Method's clothing.
- **Code Review.** A rigorous code review practice is the primary
  structural incompatibility with this anti-pattern, listed in the
  frontmatter, because a reviewer who asks why a given line exists and
  requires an answer directly forces the Missing Rationale to either be
  supplied or exposed as absent, which is the single most effective
  interruption point in the dynamics described in dimension 7.
- **Test-Driven Development.** Also listed as incompatible in the
  frontmatter, because writing a failing test before writing the
  implementation forces the developer to state, in the test itself, what
  the code is actually required to do in the New Context, which is a
  concrete, checkable substitute for the Missing Rationale that a copied
  snippet does not otherwise provide.

## 14. Refactoring path in and out

There is no path into this anti-pattern that any competent engineering
process should deliberately take; it is entered by omission, when the step
of verifying a borrowed idea against the New Context's actual requirements
is skipped under pressure. The refactoring path described here is
therefore entirely a path out, applicable once cargo culted code is
suspected or found in an existing codebase.

1. **Identify candidate Ritual Form.** Look for code whose author, when
   asked directly, cannot explain a specific structural choice, such as a
   particular timeout value, a particular lock, a particular exception
   type being caught, or a particular configuration setting. Version
   control history and an honest conversation with the original author,
   when available, are the fastest way to locate this.
2. **Recover or reconstruct the preconditions.** For each structural
   element in question, determine what condition of the environment would
   need to be true for that element to be necessary and correct. This may
   require reading the original source the code was copied from, if it can
   still be found, or reasoning from the element's observable behavior
   backward to the condition it implies.
3. **Check the preconditions against the current context.** For each
   precondition identified in step 2, verify explicitly whether it holds
   in the code's actual current call sites. This step is where most of the
   value of the whole refactor is realized, because it is the step the
   original cargo culting skipped.
4. **Remove elements whose precondition does not hold**, replacing them
   with either nothing, if the element served no purpose here, or with an
   element genuinely derived from the current context's actual
   requirements, if some handling is still needed but the borrowed shape
   was wrong for it.
5. **Add a test that encodes the now-understood rationale**, so the
   requirement the code satisfies is captured somewhere checkable rather
   than left implicit in the code's shape, closing the loop that
   Test-Driven Development, per dimension 13, would have closed from the
   start.
6. **Document the surviving rationale briefly at the point of use**, so the
   next reader inherits an explanation rather than only a shape, preventing
   the same recovery effort from being needed again.

## 15. Testing and verification

The single most effective test against this anti-pattern is not a test of
the code's output but a test of the developer's understanding, and it
belongs in code review rather than in an automated suite. for any
non-obvious structural choice, requiring the author to state, in their own
words, the specific condition that choice is protecting against. Code that
survives this question with a clear, falsifiable answer is not cargo
culted, regardless of its origin; code whose author cannot answer it is a
strong candidate regardless of how well it currently passes automated
tests.

Automated verification helps in a narrower, complementary way. property
based and mutation testing, described elsewhere in this repository, are
particularly well suited to exposing cargo culted code, because both
techniques probe behavior the developer did not explicitly have in mind
when they copied the Source Artifact. A mutation testing run that deletes
a line of defensive code and finds that no test fails is strong evidence
that either the line is genuinely unnecessary or that its necessity has
never been demonstrated, either of which is exactly the situation this
anti-pattern produces. Similarly, a property based test that generates
inputs the developer did not anticipate, such as a non-pure function fed
through a memoization layer under a property that checks the cached and
uncached results agree over many random inputs and random delays, will
surface the specific failure this entry's code examples demonstrate,
without requiring the tester to already suspect the specific bug.

Static analysis is the third layer, catching the Ritual Form's residue
rather than the reasoning gap itself. unused-variable and unused-import
linters, as documented for ESLint's no-unused-vars rule in dimension 9,
routinely surface leftover elements of a copied snippet that never became
relevant in the New Context, which is a useful, cheap signal that
something was transplanted without full adaptation, even though passing
such a linter is not evidence the surviving code is actually understood.

## 16. Observability signals

Cargo cult programming, being a defect in the developer's understanding
rather than in the running system's behavior per se, is not directly
observable through production metrics the way a resource leak or a race
condition is. What is observable is its downstream consequences, and a
team that watches for the following signals will catch instances of this
anti-pattern before they become expensive.

- **A defensive code path, such as a retry or a broad exception handler,
  that never actually triggers in production telemetry over a long
  observation window.** This suggests the path was copied for a condition
  that does not occur in this system, and its continued presence obscures
  what would otherwise be a clear, fast failure.
- **A cluster of near-identical configuration blocks across services, none
  of which any current team member can attribute a specific setting
  within to a specific requirement.** A configuration drift audit, or a
  simple diff across services' pipeline definitions, surfaces this
  directly.
- **Code review comments repeatedly asking why a given block is present on
  the same block across multiple pull requests without the question ever
  being answered and the block ever being resolved.** A review tool or
  search across historical pull request comments for unresolved questions
  is a cheap, high-signal query for this.
- **A mutation testing report, per dimension 15, that shows a stable set of
  surviving mutants concentrated in code that was recently added by
  copying from another source.** Correlating mutation survival with commit
  provenance, specifically commits whose message or diff pattern suggests
  a large snippet was pasted in as a single change, is a direct,
  measurable proxy for this anti-pattern's presence.
- **Postmortems that repeatedly trace a root cause back to nobody knowing
  why a check was there, or the check having been copied from another
  service.** Tracking this specific root-cause category across incident
  postmortems over time turns an anecdotal impression into a trend line a
  team can act on.

## 17. Security and privacy implications

This anti-pattern's security implications are among the best documented in
the empirical literature, as dimension 9's discussion of Acar et al.'s 2016
IEEE Symposium on Security and Privacy study shows directly. developers who
relied on an information source without independently verifying its
security properties produced code that was more likely to be functionally
convincing and simultaneously more likely to be insecure than code written
against an authoritative reference, because functional convincingness and
security correctness are different properties that a purely visual copy
cannot be expected to preserve together.

The mechanism generalizes beyond that study's specific Android context to
any security-relevant code, cryptographic primitive usage, authentication
and authorization checks, input validation and sanitization, and
access-control configuration. In each of these domains, a cargo culted
implementation is uniquely dangerous compared to an ordinary functional
bug, because it usually passes every functional test the team runs, and
its presence actively discourages further scrutiny. a reviewer who sees an
authentication check already present is less likely to ask whether that
check is the right one than a reviewer who sees no check at all. The
correct discipline, restated from dimension 15, is to require that
security-relevant code be justified by a stated threat model and, where
possible, sourced from a maintained, audited library rather than a
transplanted example, precisely because the cost of an unverified security
control failing silently is far higher than the cost of an unverified
caching layer failing silently.

Privacy implications follow the same shape for data-handling code. a
data-retention, anonymization, or consent-check routine copied from another
jurisdiction's or another product's compliance code carries that source's
specific regulatory preconditions, and a New Context under a different
regulatory regime, a different data classification, or a different user
population can silently violate its own obligations while running code
that looks, and was, entirely correct somewhere else.

## 18. References

- Wikipedia. ["Cargo cult programming"](https://en.wikipedia.org/wiki/Cargo_cult_programming). Verified 2026-08-02. Used for the lead definition, the Jargon File version 2.5.1, January 1991 attribution, the Acar et al. citation, and the McConnell citation details.
- Wikipedia. ["Cargo cult science"](https://en.wikipedia.org/wiki/Cargo_cult_science). Verified 2026-08-02. Used for Feynman's 1974 Caltech commencement address, its publication as "Cargo Cult Science" in *Engineering and Science*, volume 37, number 7, June 1974, pages 10 through 13, and its reprinting in *Surely You're Joking, Mr. Feynman*, W. W. Norton, 1985, pages 338 through 346.
- Feynman, Richard P., and Ralph Leighton. *Surely You're Joking, Mr. Feynman. Adventures of a Curious Character*. W. W. Norton and Company, 1985. Chapter "Cargo Cult Science," pages 338 through 346, per Wikipedia's bibliographic entry, verified 2026-08-02.
- McConnell, Steve. "Cargo Cult Software Engineering." *IEEE Software*, volume 17, issue 2, March and April 2000, pages 11 through 13, per Wikipedia's bibliographic entry, verified 2026-08-02.
- McConnell, Steve. *Professional Software Development*. Addison-Wesley, 2003, pages 23 through 26, per Wikipedia's bibliographic entry, verified 2026-08-02.
- Acar, Yasemin, Michael Backes, Sascha Fahl, Doowon Kim, Michelle L. Mazurek, and Christian Stransky. "You Get Where You're Looking For. The Impact of Information Sources on Code Security." 2016 IEEE Symposium on Security and Privacy, San Jose, California, 2016, pages 289 through 305. PDF confirmed reachable at https://www.cs.umd.edu/class/fall2017/cmsc818O/papers/get-where-look.pdf, verified 2026-08-02. Bibliographic detail and findings summary cross-checked against Wikipedia's citation of the same paper, verified 2026-08-02.
- ESLint. ["no-unused-vars" rule documentation](https://eslint.org/docs/latest/rules/no-unused-vars). Verified 2026-08-02. Used for the rule's stated purpose regarding leftover code from incomplete refactoring.
- Raymond, Eric S., editor. *The New Hacker's Dictionary*. 3rd edition, MIT Press, 1996. Print publication of the Jargon File, referenced for the term's lineage per Wikipedia's citation, verified 2026-08-02.

## Code examples

The failure shown next is a common, real shape of snippet-level
cargo culting, dimension 8's first variant. a memoization wrapper, a
pattern genuinely correct around a pure function, is copied onto a status
report function whose entire purpose is to report the current time. The
Missing Rationale is the purity precondition. memoization is safe exactly
when the wrapped function's result depends only on its arguments, and
unsafe exactly when it does not. The cargo culted version below passes an
obvious first check, calling it once produces a plausible-looking
timestamped string, and only breaks visibly when the same input is
requested twice with time elapsed in between, which is precisely the kind
of check a developer under deadline pressure is least likely to run before
shipping.

### Python

The cargo culted version. This is presented first to make the bug
concrete and runnable, not as a template to copy.

```python
from functools import lru_cache
import time


@lru_cache(maxsize=None)
def get_status_report(server_id: str) -> str:
    # Copied from a config-loading module where lru_cache was correct,
    # because that module's inputs really did map to fixed outputs.
    return f"{server_id}: {time.time()}"


if __name__ == "__main__":
    r1 = get_status_report("db-1")
    time.sleep(1.0)
    r2 = get_status_report("db-1")
    assert r1 == r2, "unexpected. cache should be masking the second call"
    print("BAD  ", r1, "==", r2, "(second call never actually ran)")
```

Running this script prints `BAD` and the two identical strings, because
`lru_cache` recognizes the argument `"db-1"` on the second call and returns
the first call's cached result without invoking the function body again.
The status report silently freezes at whatever moment it was first
requested.

```
$ python3 bad.py
BAD   db-1: 1785854479.955989 == db-1: 1785854479.955989 (second call never actually ran)
```

The fix, once the purity precondition is checked and found absent, is to
remove the copied caching layer entirely rather than tune it.

```python
import time


def get_status_report(server_id: str) -> str:
    return f"{server_id}: {time.time()}"


if __name__ == "__main__":
    r1 = get_status_report("db-1")
    time.sleep(1.0)
    r2 = get_status_report("db-1")
    assert r1 != r2, "expected two distinct timestamps"
    print("GOOD ", r1, "!=", r2)
```

```
$ python3 good.py
GOOD  db-1: 1785854485.746669 != db-1: 1785854486.956764
```

### TypeScript

The same mistake, reproduced in a generic memoize helper, the shape most
often seen when the memoize helper itself is the copied Source Artifact
rather than a single decorator call.

```typescript
function memoize<A extends unknown[], R>(fn: (...args: A) => R) {
  const cache = new Map<string, R>();
  return (...args: A): R => {
    const key = JSON.stringify(args);
    if (!cache.has(key)) {
      cache.set(key, fn(...args));
    }
    return cache.get(key) as R;
  };
}

function getStatusReport(serverId: string): string {
  return `${serverId}: ${Date.now()}`;
}

const cachedReport = memoize(getStatusReport);

const r1 = cachedReport("db-1");
const start = Date.now();
while (Date.now() - start < 50) {
  // busy wait past clock resolution
}
const r2 = cachedReport("db-1");

if (r1 !== r2) {
  throw new Error("expected the cargo culted cache to return a stale value");
}
console.log("BAD ", r1, r2, "(second call never actually ran)");
```

```
$ npx tsc --target es2020 --module commonjs bad.ts && node bad.js
BAD  db-1: 1785854494274 db-1: 1785854494274 (second call never actually ran)
```

```typescript
function getStatusReport(serverId: string): string {
  return `${serverId}: ${Date.now()}`;
}

const r1 = getStatusReport("db-1");
const start = Date.now();
while (Date.now() - start < 50) {
  // busy wait past clock resolution
}
const r2 = getStatusReport("db-1");

if (r1 === r2) {
  throw new Error("expected two distinct timestamps");
}
console.log("GOOD", r1, "!=", r2);
```

```
$ npx tsc --target es2020 --module commonjs good.ts && node good.js
GOOD db-1: 1785854499042 != db-1: 1785854499092
```

### Go

A concurrency-safe variant, showing that the mistake is unrelated to
whether the copied wrapper is naive or carefully engineered with a mutex.
A well-built cache is still a cache, and a well-built cache around a
non-pure function is still wrong.

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type memoizedReporter struct {
	mu    sync.Mutex
	cache map[string]string
	fn    func(string) string
}

func newMemoizedReporter(fn func(string) string) *memoizedReporter {
	return &memoizedReporter{cache: make(map[string]string), fn: fn}
}

func (m *memoizedReporter) Report(serverID string) string {
	m.mu.Lock()
	defer m.mu.Unlock()
	if v, ok := m.cache[serverID]; ok {
		return v
	}
	v := m.fn(serverID)
	m.cache[serverID] = v
	return v
}

func statusReport(serverID string) string {
	return fmt.Sprintf("%s: %d", serverID, time.Now().UnixNano())
}

func main() {
	cached := newMemoizedReporter(statusReport)
	r1 := cached.Report("db-1")
	time.Sleep(50 * time.Millisecond)
	r2 := cached.Report("db-1")
	if r1 != r2 {
		panic("expected the cargo culted cache to return a stale value")
	}
	fmt.Println("BAD ", r1, r2, "(second call never actually ran)")
}
```

```
$ go run bad.go
BAD  db-1: 1785854506390357000 db-1: 1785854506390357000 (second call never actually ran)
```

```go
package main

import (
	"fmt"
	"time"
)

func statusReport(serverID string) string {
	return fmt.Sprintf("%s: %d", serverID, time.Now().UnixNano())
}

func main() {
	r1 := statusReport("db-1")
	time.Sleep(50 * time.Millisecond)
	r2 := statusReport("db-1")
	if r1 == r2 {
		panic("expected two distinct timestamps")
	}
	fmt.Println("GOOD", r1, "!=", r2)
}
```

```
$ go run good.go
GOOD db-1: 1785854511934156000 != db-1: 1785854511986205000
```

All six samples above (three languages, bad and good, each) were executed
during authoring. `python3` ran both Python scripts directly. `npx tsc`
compiled both TypeScript files to CommonJS and `node` ran the output.
`go run` compiled and ran both Go files. Every run reproduced the output
shown.
