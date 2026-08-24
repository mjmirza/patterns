---
name: Do Not Repeat Yourself
slug: do-not-repeat-yourself
family: 04-principles-and-laws
category: Principle
aliases: [DRY, Single Source of Truth, Once and Only Once]
first_described: "Hunt, Thomas 1999"
maturity: canonical
related: [single-responsibility-principle, high-cohesion, low-coupling, template-method, pure-fabrication]
incompatible_with: []
verified: 2026-08-02
---

# Do Not Repeat Yourself

## 1. Name, aliases, and lineage

The canonical name is Don't Repeat Yourself, almost universally abbreviated
DRY. It was coined by Andy Hunt and Dave Thomas and formulated as, "every
piece of knowledge must have a single, unambiguous, authoritative
representation within a system" (Andrew Hunt and David Thomas, *The Pragmatic
Programmer. From Journeyman to Master*, Addison-Wesley, 1999, chapter 2,
section "The Evils of Duplication"). Thomas is later credited with coining
both "DRY" and the unrelated term "Code Kata"
([Wikipedia, Dave Thomas (programmer)](https://en.wikipedia.org/wiki/Dave_Thomas_(programmer)),
verified 2026-08-02).

Kent Beck's earlier Extreme Programming value of "once and only once" for a
piece of logic is a close precursor with the same intent, applied narrower, to
code rather than to knowledge in general. Ward Cunningham and the
Smalltalk community used similar language before Hunt and Thomas gave it a
name, but the named, citable formulation is theirs
([Wikipedia, Don't repeat yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself),
verified 2026-08-02).

Two names are used loosely as synonyms and are worth separating. Single Source
of Truth describes the same idea applied to data and configuration, one place
that is authoritative and every other place reads from it, rather than to
logic or code. Once and Only Once is Beck's phrasing, narrower, and predates
the DRY name.

A deliberately contrasting term, WET, exists as the folk-etymology opposite.
Community usage backronyms it as "write everything twice", "write every
time", or "we enjoy typing", used to describe code that violates DRY
([Wikipedia, Don't repeat yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself),
verified 2026-08-02). WET is not itself a named pattern with a canonical
source, it is a joke label for the absence of DRY.

The single sentence from Hunt and Thomas is the load-bearing part of the whole
principle, and it is worth reading twice. The unit of concern is a piece of
KNOWLEDGE, not a piece of TEXT. Two blocks of code that happen to look
identical but express two independent facts are not a DRY violation. Two
blocks of code that look completely different but express the same fact in
two encodings are a DRY violation. This is the single most common
misunderstanding of the principle, covered fully in dimension 11.

## 2. Problem and context

A single fact about the system, a tax rate, a validation rule, a URL, a unit
conversion, a business rule about who is allowed to approve a refund, gets
written down in more than one place in the codebase. The fact is correct when
it is first written in both places. Time passes. The fact changes, because
requirements change, a bug is found, or the business rule is updated. One of
the two places gets updated. The other does not, either because the author
did not know it existed, could not find it, or found it and decided updating
it was somebody else's file.

The system now silently disagrees with itself. There is no compile error, no
test failure necessarily, because both copies are individually valid code,
they just encode different, contradictory versions of the same fact. The bug
this produces is not a crash. It is a quiet divergence that surfaces much
later as "why does the receipt say a different total than the checkout
screen" or "why did staging pass and production reject the same input", and
by then nobody remembers there were ever two copies to keep in sync.

The context in which this problem arises is any codebase past its first
working version, because a single unduplicated fact never causes this
problem, only a fact that has been copied does. It gets worse in direct
proportion to two things, team size, because more people means more chances
that the second location is unknown to whoever edits the first, and change
frequency, because a fact that never changes again is never a maintenance
problem regardless of how many copies exist.

## 3. Forces

**Change cost versus indirection cost.** Centralizing a fact into one place
lowers the cost of a future change to a single edit, at the cost of adding a
layer of indirection, a function call, an import, a lookup, that a reader must
follow to see the fact's current value. The more often a fact changes, the
more the centralization pays for itself. The more rarely it changes, the more
the indirection is pure overhead with no future payoff.

**Coupling versus consistency.** Extracting a shared fact into one location
couples every consumer of that fact to that location. If the consumers
genuinely need the same fact, this coupling is desirable, because it is the
mechanism that keeps them consistent. If two consumers only coincidentally
have the same value today, and are conceptually independent, this coupling is
a false dependency that will bite when one consumer needs to diverge and
cannot without touching the shared location and reasoning about every other
consumer of it.

**Discoverability versus locality.** A duplicated fact is trivially readable
in place, a reader sees the whole logic without searching anywhere. A
centralized fact is readable exactly once and consistent everywhere, but a
reader unfamiliar with the codebase has to go find it, and an editor with an
imperfect mental model of the codebase can miss that a shared function they
are calling is shared, and change its behavior for every caller by accident.

**Premature abstraction risk.** The pressure to eliminate duplication as soon
as it is noticed collides with the reality that the correct shared
abstraction is often not yet knowable from two data points. Centralizing too
early, on the strength of a single instance of duplicated-looking code,
tends to produce a shared function with parameters and conditionals bolted on
to handle every caller's slightly different need, which is a worse outcome
than the duplication it replaced. This tension is named directly and is
covered as its own dimension of judgement in section 11.

**Cognitive load.** A codebase with a single well-known location for each
important fact is easier to hold in a reader's head once they know the map.
A codebase with the same fact scattered across many files is harder to
verify correct, because correctness now requires checking that N copies
agree, and N grows the load linearly.

DRY openly favors change cost and long-run consistency over locality and
short-run readability, and it explicitly sacrifices the ability to read one
piece of code in total isolation, on the bet that most non-trivial facts in a
system change more than once.

## 4. Applicability and non-applicability

Apply DRY when the following hold together, not individually.

- The duplicated thing is a single piece of KNOWLEDGE, a business rule, a
  formula, a schema, a constant, a contract, not merely similar-looking text.
- The duplicates are semantically coupled, meaning a correct change to one of
  them is, by the nature of the domain, always also a correct change to the
  others. If updating one copy and not the other could ever be intentional and
  correct, the copies are not the same knowledge.
- The fact is expected to change again, or its correctness matters enough
  that a silent divergence would be a real defect, not a cosmetic annoyance.
- There is already a real, not hypothetical, second occurrence. DRY is a
  response to an observed duplication, not a design-time prediction of one.

Do NOT apply DRY, and prefer leaving the duplication in place, when any of
these hold.

- The two pieces of code look alike by coincidence but represent independent
  domain concepts that happen to share a shape today. Merging them creates a
  false coupling that will need to be un-merged the moment the concepts
  diverge, which Sandi Metz documents as the wrong-abstraction failure mode
  (see dimension 9 and 11).
- Only one instance exists so far. The Rule of Three, popularized by Martin
  Fowler and attributed to Don Roberts, "the first time you do something, you
  just do it. The second time you do something similar, you wince at the
  duplication, but you do the duplicate thing anyway. The third time you do
  something similar, you refactor" ([Wikipedia, Rule of three (computer
  programming)](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)),
  verified 2026-08-02), is the standard heuristic against abstracting on the
  first sighting of a duplicate.
- Deduplicating would require an abstraction across a module or service
  boundary that is intentionally decoupled, for example two independently
  deployed microservices that both happen to validate an email address the
  same way today. Sharing that validator via a network call or a tightly
  version-pinned library trades an acceptable duplication for an unacceptable
  runtime or release coupling. See the trade-off with the microservice
  database-per-service pattern in dimension 12.
- The duplication is in TEST code that exists to pin an example independently
  of the implementation, where consolidating test setup can hide the fact
  that two tests are checking genuinely different scenarios that happen to
  share fixture text today. See dimension 15.
- Performance requires an inlined, denormalized copy of data, for example a
  read-optimized cache or a materialized view that intentionally duplicates
  data already stored authoritatively elsewhere, with an explicit
  invalidation strategy. This is deliberate, tracked duplication for a named
  reason, not the accidental kind DRY targets.
- The two occurrences are DRY in knowledge but live in different bounded
  contexts in the Domain-Driven Design sense, where a "Customer" in the
  billing context and a "Customer" in the shipping context are legitimately
  different models even though today's fields overlap, and sharing one model
  couples two contexts that the domain intends to evolve independently.

## 5. Structure

DRY has no fixed participant structure of its own, because it is a principle
that other patterns implement, not an implementation pattern with named
roles. It is useful nonetheless to name the structural elements that any DRY
refactor produces, because the same shape recurs regardless of which
mechanism carries it out.

- **The knowledge.** The fact, rule, formula, or schema being deduplicated.
  It has an owner, meaning exactly one place in the running system where a
  change to it is made.
- **The single representation.** The one location, a function, a class, a
  constant, a configuration file, a database table, a code generator input,
  that holds the authoritative form of the knowledge.
- **The consumers.** Every call site, template, module, or service that needs
  the knowledge and, after the refactor, obtains it by referring to the single
  representation rather than by encoding it again.
- **The binding mechanism.** How a consumer obtains the knowledge at the
  point of use, a function call, an import, dependency injection, a build-time
  code generation step, a runtime configuration read, or an inherited method.
  The choice of binding mechanism is what differentiates a Template Method
  implementation of DRY from a shared-constants-module implementation of DRY.

## 6. ASCII structure diagram

```
Before

+---------------+
| Checkout code |
| tax = p * r   |
+---------------+
+--------------+
| Receipt code |
| tax = p * r  |
+--------------+

Two independent copies of the formula. A tax-law
change means finding and editing both, and nothing
enforces they still match.

After

+------------------+
| Checkout code    |
| orderTotal(p, r) |
+------------------+
+------------------+
| Receipt code     |
| orderTotal(p, r) |
+------------------+
     | both call
     v
+------------------------------------------------+
| orderTotal(p, r), single, owned, authoritative |
+------------------------------------------------+

One representation, two consumers bound to it. A
tax-law change means editing one function. Both
callers agree by construction, not by care.
```

## 7. Dynamics

The dynamics of DRY are a compile-time or design-time property, not a runtime
event sequence, which is why this dimension is drawn as a change-propagation
flow rather than a message sequence.

```
  Requirement changes (e.g. tax law update)
          |
          v
  Change made ONCE, at the single representation
          |
          v
  Every consumer picks up the new value
   automatically, at their next call/build/load,
   with no per-consumer edit required
          |
          v
  All consumers are consistent by construction

  Compare to the duplicated case:

  Requirement changes
          |
          +----> Copy A updated (visible, someone remembered)
          |
          +----> Copy B NOT updated (invisible, someone forgot)
                          |
                          v
                 System silently disagrees with itself
                 until a person notices the symptom,
                 not the cause
```

The binding mechanism decides WHEN the consumer picks up the change. A
runtime function call picks it up on the next invocation. A build-time code
generator, such as a `.proto` compile step, picks it up on the next build. A
database foreign key or a normalized schema picks it up on the next query. A
copy-pasted constant never picks it up, which is precisely the failure mode
DRY exists to close.

## 8. Implementation variants

DRY has no single implementation, it is realized through whichever mechanism
a language or system offers for one-to-many delegation. The variants below
are ordered from cheapest and most local to most structural.

- **Extract function or method.** The most common variant. A duplicated
  calculation, validation, or formatting routine is pulled into a named
  function that every call site invokes. This is the mechanism demonstrated
  in the code examples for this entry.
- **Extract constant.** A duplicated literal value, a magic number, a URL, a
  configuration default, is given one named location. Trivial to apply,
  frequently skipped, and one of the highest-value-per-effort DRY moves in
  practice because a literal has no behavior to accidentally couple.
- **Template Method or Strategy.** When the duplication is a shared algorithm
  SHAPE with varying steps, rather than an identical calculation, Template
  Method (see the `template-method` entry in this catalog) or Strategy names
  the invariant part once and varies only the differing steps, which is DRY
  applied to control flow rather than to a formula.
- **Inheritance or mixin/trait sharing.** A shared method or field is placed
  on a common base class, abstract class, mixin, or trait, and every subtype
  inherits it rather than reimplementing it. Carries the well-documented risk
  of coupling unrelated types through a shared parent purely to reuse a
  method, which is a known anti-pattern the `composition-over-inheritance`
  guidance addresses.
- **Data-driven or table-driven design.** Instead of duplicating a branch of
  logic per case, the varying facts are moved into a data structure, a
  lookup table, an enum-to-value map, a rules table in a database, and the
  logic that reads it is written once. This is DRY applied to CONTROL FLOW
  duplication rather than to formula duplication, and it is the mechanism
  behind rules engines and configuration-driven feature flags.
- **Code generation from a single schema.** A `.proto` file, an OpenAPI
  specification, a database schema, or a GraphQL schema is the one
  authoritative representation, and client code, server stubs, and
  documentation are generated FROM it at build time, rather than hand-written
  separately in each consuming language. This variant explicitly trades
  build-time complexity for runtime and cross-language consistency, and is
  covered further in dimension 9.
- **Shared library or module.** The knowledge is packaged as an importable
  unit, a shared internal package, an npm workspace package, a Cargo crate,
  used by multiple parts of a monorepo or, more riskily, by multiple
  independently deployed services. The cross-service case reintroduces the
  coupling-versus-consistency tension from dimension 3 at organizational
  scale, discussed in dimension 4's non-applicability list.
- **Convention over configuration.** Instead of repeating a mapping, a file
  naming scheme, a directory layout, a naming convention itself becomes the
  single source of truth, and the framework infers behavior from it rather
  than reading it from a repeated declaration. Ruby on Rails is the
  best-documented instance of this variant, discussed with a source in
  dimension 9.

## 9. Known production uses

- **Ruby on Rails and ActiveRecord.** DRY is listed among the Rails Guides'
  stated guiding principles, alongside Convention over Configuration, and the
  framework's migrations-generate-schema mechanism is a direct implementation,
  the database schema is derived from one ordered set of migration files
  rather than hand-maintained separately from the code that queries it
  ([Ruby on Rails Discussions, "What is the official position on the DRY
  concept in Rails?"](https://discuss.rubyonrails.org/t/what-is-the-official-position-on-the-dry-concept-in-rails/82798),
  verified 2026-08-02).
- **Protocol Buffers (gRPC ecosystem).** A single `.proto` interface
  definition file is the authoritative schema, and the `protoc` compiler
  generates the corresponding data-access code in each target language at
  build time, so a change to a message's shape is made once and propagates to
  every language binding on the next compile, rather than requiring a
  hand-synchronized struct or class in each language
  ([Protocol Buffers overview, protobuf.dev](https://protobuf.dev/overview/),
  verified 2026-08-02, quoting "You define how you want your data to be
  structured once, then you can use special generated source code to easily
  write and read your structured data to and from a variety of data streams
  and using a variety of languages").
- **Terraform modules (HashiCorp).** HashiCorp's own module-development
  documentation frames a module as a reusable container of resource
  definitions so that infrastructure described once can be instantiated
  multiple times, rather than the same set of cloud resources being copied
  into every environment's configuration by hand, while explicitly cautioning
  against over-modularizing purely to avoid a small amount of repetition
  ([HashiCorp Developer, "Module Creation - Recommended Pattern"](https://developer.hashicorp.com/terraform/language/modules/develop),
  verified 2026-08-02).
- **OpenAPI code generation (openapi-generator project).** An OpenAPI YAML or
  JSON specification is treated as the single source of truth for an HTTP
  API's shape, and the openapi-generator project produces client SDKs and
  server stubs in dozens of target languages from that one document, so the
  request and response contract is defined once rather than reimplemented
  per language client.
- **Database normalization (relational schema design).** Codd's normal
  forms are the data-modeling instance of the same idea, applied decades
  before the DRY name existed, a normalized relational schema stores each
  fact in exactly one row of one table, and every other table that needs it
  references it by foreign key rather than copying the value, which is why
  normalization theory and DRY are frequently cited alongside each other as
  the data and code halves of one idea.

## 10. Consequences

Positive.

- A single edit propagates correctly to every consumer, eliminating the
  entire class of "we fixed it in one place and not the other" defects.
- Business rules, formulas, and schemas become independently testable in one
  location, rather than requiring the same test to be written and maintained
  against every duplicate.
- Onboarding improves for a fact that changes often, because a new team
  member learns one location to check rather than needing to know every
  place a rule was copied.
- Code volume shrinks, which reduces the total surface area that has to be
  read, reviewed, and kept correct.

Negative.

- Every consumer becomes coupled to the shared representation, so a change
  intended for one consumer can silently affect every other consumer that was
  not meant to be touched, which is the reverse of the failure mode DRY fixes
  and is exactly as damaging when the shared abstraction was wrong.
- Indirection cost is paid by every future reader, who must now trace a
  function call, an import, or a generated-code step to see the current value
  of a fact that used to be visible in place.
- A poorly chosen abstraction, forced to serve two or three call sites that
  turn out not to share the same underlying concept, accretes conditional
  parameters over time until it is harder to understand and change than the
  duplication it replaced, a failure mode named directly in dimension 11.
- Applied prematurely, on a single occurrence rather than an observed
  pattern, DRY produces speculative generality, an abstraction built for a
  future variation that may never arrive, at a cost paid immediately.

## 11. Failure modes and misuse

**The wrong abstraction.** Two pieces of code look similar and are merged
into one shared function, but they represent different knowledge that only
coincidentally has the same shape today. Sandi Metz documents this directly,
"duplication is far cheaper than the wrong abstraction", and describes the
symptom as a shared method that grows conditional branches and boolean flag
parameters over successive changes, each new caller's slightly different need
bolted onto the same function rather than given its own
([Sandi Metz, "The Wrong Abstraction"](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
verified 2026-08-02).

Symptom. A shared function accumulates parameters named `isSpecialCase`,
`mode`, or `variant`, and its body contains `if` branches that are only ever
taken by one caller.

Cause. Two call sites were merged on the strength of looking alike, before it
was verified that they represent the same domain knowledge that must always
change together.

Fix. Un-merge. Give each caller its own small function again, even if the
bodies are momentarily identical text, and only re-merge once a third caller
confirms the duplication is knowledge, not coincidence, per the Rule of Three
in dimension 4.

**DRY applied across bounded contexts.** A "Customer" or "Order" concept is
modeled once and shared across two parts of the system that domain-driven
design would treat as separate bounded contexts, for example billing and
fulfillment, because both currently need a name and an address.

Symptom. An innocuous field addition needed by one context, for example a
billing-only tax identifier, requires a migration that touches a shared model
consumed by an unrelated context, and every team that touches that model has
to coordinate.

Cause. Treating "the data looks the same" as evidence the concept is the
same, when the two contexts may have entirely different lifecycle and
consistency requirements for what only appears to be one entity.

Fix. Give each context its own local representation, and translate at the
boundary, accepting the duplication of the shared FIELDS as the cost of
correctly separating the DIFFERENT KNOWLEDGE that governs each.

**Speculative generality.** A shared abstraction is introduced for two call
sites that do not yet exist, or from a single call site anticipating a second
one that never arrives, to preempt a future duplication.

Symptom. A function or class with configuration options, hooks, or
parameters that no current caller uses, added "in case" a second consumer
needs them.

Cause. Applying DRY as a design-time prediction rather than a response to an
observed, real duplication, inverting the Rule of Three.

Fix. Delete the unused generality, and re-add it only when a real second
caller exists and the shared knowledge is confirmed.

**Cross-service DRY via a shared library.** Two independently deployable
services import the same internal library to avoid duplicating a validation
rule or a data model.

Symptom. Deploying a fix to one service requires bumping and redeploying the
shared library in every other service that depends on it, turning what
should be an independent deployment into a coordinated one, or the two
services silently drift because one upgraded the shared library and the
other did not.

Cause. Treating build-time code sharing as free, when it reintroduces the
release-coupling that the services' independent-deployment boundary was
built to remove.

Fix. Either accept the duplication as the price of the deployment boundary,
per dimension 4's non-applicability list, or move the shared knowledge
behind a network call to a small owning service, trading library coupling
for a runtime dependency, which is a different, explicit trade.

**Copy-paste that looks like knowledge but is not.** Two blocks of test
fixture data, or two UI components, are textually identical today and get
merged into a shared constant or component out of a reflexive dislike of
seeing repeated text.

Symptom. A later, legitimate change to one of the two locations is blocked
or complicated because the shared constant or component now has to serve
two diverging needs.

Cause. Treating textual similarity as proof of shared knowledge, the exact
misreading of DRY the Hunt and Thomas definition warns against by scoping
the principle to "knowledge", not to text.

Fix. Judge duplication by asking whether the two things must always change
together as a matter of domain fact, not by whether they currently read the
same.

## 12. Trade-off matrix

| Force | DRY (single representation) | Duplication tolerated (WET) | AHA, delayed abstraction |
|---|---|---|---|
| Consistency on change | High, one edit propagates everywhere | Low, each copy edited by hand, drift risk | Medium, consistency deferred until abstraction is confirmed correct |
| Coupling introduced | High, every consumer depends on the shared point | None between consumers | Low until the third occurrence forces a choice |
| Risk of wrong abstraction | Present if merged too early | Absent, no abstraction exists to be wrong | Reduced, waits for evidence before committing |
| Reader locality | Lower, must follow indirection | Higher, logic is visible in place | Higher early, lower after eventual extraction |
| Best suited to | A fact confirmed to recur and to matter if it drifts | A single occurrence, or two coincidentally similar but conceptually independent pieces | A team without confidence yet that two similar blocks share real knowledge |

AHA programming, "Avoid Hasty Abstractions", coined by Kent C. Dodds, is the
named middle position between strict DRY and tolerating full duplication, it
agrees with WET's caution against premature merging and with DRY's eventual
goal of one representation once the knowledge is confirmed shared
([Kent C. Dodds, "AHA Programming"](https://kentcdodds.com/blog/aha-programming),
verified 2026-08-02).

## 13. Related and incompatible patterns

- **Single Responsibility Principle.** A class or function with one reason to
  change is a natural home for one piece of knowledge, so applying SRP tends
  to produce the correctly-scoped extraction point DRY needs, and a class that
  already violates SRP is a common place to find a duplicated fact hiding
  inside two of its unrelated responsibilities.
- **High Cohesion and Low Coupling.** DRY's single representation is only a
  net improvement when it is placed somewhere cohesive, a module whose other
  contents are related to the extracted fact. Placing a shared formula in an
  unrelated "Utils" class produces low cohesion even while nominally
  satisfying DRY, which is why the placement of the single representation
  matters as much as its existence.
- **Template Method.** One of the most common structural implementations of
  DRY for algorithm shape rather than for pure data, the invariant steps are
  written once in the base class and only the varying steps are supplied per
  subtype.
- **Pure Fabrication.** When no existing domain class is the natural home for
  a shared piece of knowledge, a Pure Fabrication, a class invented purely for
  design reasons rather than to model a domain concept, is the standard place
  to put the single representation without distorting an existing domain
  class.
- **Composition over inheritance guidance.** Sits in tension with the
  inheritance-based DRY variant from dimension 8, warning that sharing code by
  putting it on a common ancestor purely to avoid duplication, rather than
  because the types have a genuine is-a relationship, produces a fragile,
  overly coupled hierarchy, favoring composition-based sharing instead.
- **Incompatible in the strict sense with nothing in this catalog**, because
  DRY is a principle rather than a competing structural pattern, but it is in
  direct creative tension with any deliberate, tracked duplication strategy,
  a read-optimized cache, a materialized view, an event-sourced projection,
  where the duplication is intentional and the consistency is handled by an
  explicit synchronization mechanism rather than by having only one copy.

## 14. Refactoring path in and out

**Introducing DRY into code that lacks it.**

1. Confirm the duplication is KNOWLEDGE, not merely similar text, by asking
   whether the two locations must always change together as a domain fact.
   If unsure, stop, and wait for a third occurrence per the Rule of Three.
2. Write a characterization test against each existing call site if one does
   not already exist, capturing today's observable behavior before touching
   anything, per the systematic-debugging and test-first guidance elsewhere
   in this catalog.
3. Extract the shared logic into a new, named function, constant, or module,
   placed in a cohesive location, not a generic utility grab-bag.
4. Redirect the FIRST call site to the extraction, run its test, confirm
   behavior is unchanged.
5. Redirect the SECOND call site to the same extraction, run its test,
   confirm behavior is unchanged, and confirm both call sites now produce
   identical output for identical input, which the code examples in this
   entry assert directly.
6. Delete the original duplicated code once every call site is redirected
   and every test is green.
7. Watch the extraction over its next two or three real changes. If it stays
   simple, it was correctly identified as shared knowledge. If it starts
   growing conditional parameters serving only one caller, proceed to the
   removal path below.

**Removing DRY that has become the wrong abstraction.**

1. Identify which callers of the shared function or class are exercising
   which conditional branch or parameter combination.
2. For each caller, inline the shared logic back into a caller-local copy,
   keeping only the behavior that caller actually needs, and delete the
   parameters and branches that existed solely for a different caller.
3. Run each caller's test suite after its inlining, independently, to confirm
   the un-merge did not change that caller's behavior.
4. Once every caller has its own copy again, delete the original shared
   function.
5. Accept the resulting duplication as correct until a future, GENUINE third
   occurrence of the SAME underlying knowledge reappears, at which point
   restart the introduction path above with the benefit of now having real
   evidence the abstraction should exist.

## 15. Testing and verification

DRY changes what is easy and what is hard to test, in both directions.

What becomes easier. A shared formula or rule extracted into one function can
be tested exhaustively in ISOLATION, with unit tests covering its edge cases
once, and every consumer inherits that correctness without needing to
duplicate the edge-case tests per call site. The Go and Rust examples in this
entry demonstrate the direct consequence, an assertion that two independent
call sites produce identical output for identical input, which is trivially
true once both delegate to the same function and would require a manual
cross-check if they did not.

What becomes harder. A test suite that itself duplicates fixture setup across
many test files is a common and legitimate target for extraction, but
over-sharing test fixtures via a single shared setup function risks the same
wrong-abstraction failure from dimension 11 applied to tests, where two tests
that are meant to check independent scenarios end up sharing a fixture that
subtly couples them, so that fixing one test's data requirements silently
breaks another test that happened to rely on the old shared values. The
standard guard is to keep shared test HELPERS narrow and explicit about what
they set up, and to prefer a builder or factory function with clear defaults
over a single monolithic shared fixture object.

A useful verification technique specific to this principle is a
"knowledge audit" test, an automated check, sometimes as simple as a shared
integration test that calls every known consumer of a fact with the same
input and asserts they agree, which is exactly what the assertion in the
Rust and Go examples for this entry demonstrates in miniature, and which
scales in real systems to a contract test run against every service that
consumes a shared schema.

## 16. Observability signals

DRY itself is a design-time property and has no direct runtime signal, but
its ABSENCE produces observable symptoms worth instrumenting for.

- **Divergence alerts.** Where a fact is intentionally duplicated for
  performance, a cache or a materialized view, log or metric the gap between
  the cached copy and the authoritative source, and alert if that gap exceeds
  an expected staleness window, turning an accidental-looking silent
  divergence into a monitored, deliberate one.
- **Schema drift checks in CI.** For code-generation-based DRY, protobuf,
  OpenAPI, GraphQL, a healthy pipeline regenerates the derived code from the
  schema on every build and fails if the generated output differs from what
  is checked in, which is the mechanical way to detect that someone
  hand-edited a generated file, silently reintroducing a duplicate.
- **Static duplication metrics.** Tools that measure code-clone percentage
  across a codebase are a lagging but useful signal, a rising clone
  percentage over time in a codebase whose team believes it practices DRY is
  worth investigating for whether real knowledge is going unshared or whether
  the metric is catching coincidental, non-knowledge duplication that is
  correctly left alone per dimension 4.
- **A high fan-in count on a shared function**, meaning many callers, is a
  positive signal that a real, validated single source of truth exists, while
  a shared function whose fan-in is exactly one is a candidate to inline back
  per the removal path in dimension 14, since a single caller gains nothing
  from the indirection.

## 17. Security and privacy implications

DRY has a direct, positive security implication when applied to
authentication, authorization, and input-validation logic specifically. A
duplicated authorization check, for example the same "is this user allowed to
view this record" rule reimplemented in two API endpoints, is a well
documented source of real vulnerabilities, because the two copies can drift,
and an attacker only needs to find the endpoint where the check was not
updated to match a new access rule. Centralizing authorization logic into one
checked, tested location, and requiring every endpoint to call it rather than
reimplement it, is one of the highest-value applications of this principle
for security.

The negative implication runs the other way for secrets and credentials
specifically. DRY should NOT be read as license to store a single
credential, API key, or encryption key and reference it from many services
with no additional control, because centralizing a secret's STORAGE without
also centralizing its ACCESS CONTROL and rotation turns a single compromised
consumer into a compromise of every consumer that shares the credential. The
correct application of DRY to secrets is centralizing the SOURCE OF ISSUANCE,
a secrets manager or vault, not eliminating per-consumer scoped credentials
in favor of one shared value everywhere.

There is no privacy-specific implication distinct from the security point
above, beyond the general observation that a single, well-audited location
for a data-access rule is easier to review for compliance with a privacy
policy than the same rule scattered and possibly drifted across many call
sites.

## 18. References

- Andrew Hunt and David Thomas, *The Pragmatic Programmer. From Journeyman to
  Master*, Addison-Wesley, 1999, chapter 2, "The Evils of Duplication". The
  originating source of the DRY name and its definition.
- [Wikipedia, "Don't repeat yourself"](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself),
  verified 2026-08-02. Summary of the principle, the WET backronym, and
  implementation approaches Hunt and Thomas describe across system layers.
- [Wikipedia, "Dave Thomas (programmer)"](https://en.wikipedia.org/wiki/Dave_Thomas_(programmer)),
  verified 2026-08-02. Attribution of the DRY coinage to Thomas.
- [Wikipedia, "Rule of three (computer programming)"](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)),
  verified 2026-08-02. The Don Roberts guideline as popularized by Martin
  Fowler, used here as the standard non-applicability heuristic in dimension
  4.
- [Sandi Metz, "The Wrong Abstraction"](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
  published 2016-01-20, verified 2026-08-02. Source of "duplication is far
  cheaper than the wrong abstraction" and the described symptom of a shared
  method accumulating caller-specific conditionals.
- [Kent C. Dodds, "AHA Programming"](https://kentcdodds.com/blog/aha-programming),
  verified 2026-08-02. Source of the AHA, "Avoid Hasty Abstractions", middle
  position referenced in the trade-off matrix.
- [Ruby on Rails Discussions, "What is the official position on the DRY
  concept in Rails?"](https://discuss.rubyonrails.org/t/what-is-the-official-position-on-the-dry-concept-in-rails/82798),
  verified 2026-08-02. Confirms DRY as a stated Rails Guides principle.
- [Protocol Buffers, "Protocol Buffers Overview"](https://protobuf.dev/overview/),
  verified 2026-08-02. Source for the single-schema, multi-language code
  generation production use.
- [HashiCorp Developer, "Module Development - Recommended Pattern"](https://developer.hashicorp.com/terraform/language/modules/develop),
  verified 2026-08-02. Source for the Terraform module reuse production use
  and its caution against over-modularizing.

## Code examples

Four languages, each pulling the identical shared calculation out of two
otherwise independent call sites, then asserting the two call sites agree by
construction rather than by manual cross-check. Java is omitted because no
Java toolchain was available on this machine to compile and run it, and
compiling an unrun sample would misrepresent it as verified.

### Go

```go
package main

import "fmt"

// orderTotal is the single authoritative source for the price-plus-tax formula.
func orderTotal(subtotalCents int64, taxRateBps int64) int64 {
	tax := subtotalCents * taxRateBps / 10000
	return subtotalCents + tax
}

// Two independent call sites, both delegating instead of re-deriving the formula.
func checkoutSummary(subtotalCents, taxRateBps int64) string {
	return fmt.Sprintf("Checkout total: %d cents", orderTotal(subtotalCents, taxRateBps))
}

func receiptSummary(subtotalCents, taxRateBps int64) string {
	return fmt.Sprintf("Receipt total: %d cents", orderTotal(subtotalCents, taxRateBps))
}

func main() {
	subtotal := int64(19999)
	taxRateBps := int64(875)

	fmt.Println(checkoutSummary(subtotal, taxRateBps))
	fmt.Println(receiptSummary(subtotal, taxRateBps))
	fmt.Println("both call sites derive the tax knowledge from one function")
}
```

Ran with `go run dry.go`, output.

```
Checkout total: 21748 cents
Receipt total: 21748 cents
both call sites derive the tax knowledge from one function
```

### Rust

```rust
// Single authoritative source for the shipping-cost formula.
fn shipping_cost_cents(weight_grams: u32, zone: &str) -> u32 {
    let per_gram_rate = match zone {
        "domestic" => 2,
        "international" => 5,
        _ => 8,
    };
    let base_fee = 350;
    base_fee + weight_grams * per_gram_rate
}

// Two call sites that would otherwise duplicate the rate table.
fn cart_estimate(weight_grams: u32, zone: &str) -> u32 {
    shipping_cost_cents(weight_grams, zone)
}

fn invoice_line_item(weight_grams: u32, zone: &str) -> u32 {
    shipping_cost_cents(weight_grams, zone)
}

fn main() {
    let weight = 1200;
    let zone = "international";

    let estimate = cart_estimate(weight, zone);
    let invoiced = invoice_line_item(weight, zone);

    println!("Cart estimate: {} cents", estimate);
    println!("Invoice line: {} cents", invoiced);
    assert_eq!(estimate, invoiced, "the two call sites must agree by construction");
    println!("agreement is structural, not coincidental");
}
```

Compiled with `rustc -O -o dry_rs dry.rs` and run, output.

```
Cart estimate: 6350 cents
Invoice line: 6350 cents
agreement is structural, not coincidental
```

### TypeScript

```typescript
// Single authoritative source for what counts as a valid email address.
function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

interface SignupForm {
  email: string;
}

interface NewsletterForm {
  email: string;
}

// Two independent forms, both delegating to the one predicate.
function validateSignup(form: SignupForm): string[] {
  const errors: string[] = [];
  if (!isValidEmail(form.email)) errors.push("invalid email");
  return errors;
}

function validateNewsletter(form: NewsletterForm): string[] {
  const errors: string[] = [];
  if (!isValidEmail(form.email)) errors.push("invalid email");
  return errors;
}

const bad = validateSignup({ email: "not-an-email" });
const good = validateNewsletter({ email: "user@example.com" });

console.log("signup errors:", bad);
console.log("newsletter errors:", good);
console.log("both forms share one definition of a valid email");
```

Compiled with `tsc --strict --target es2020 --module commonjs`, run with
`node`, output.

```
signup errors: [ 'invalid email' ]
newsletter errors: []
both forms share one definition of a valid email
```

### Python

```python
from decimal import Decimal


def late_fee(balance: Decimal, days_overdue: int) -> Decimal:
    """Single authoritative source for the late-fee formula."""
    if days_overdue <= 0:
        return Decimal("0")
    rate = Decimal("0.015")
    return (balance * rate * days_overdue).quantize(Decimal("0.01"))


def dunning_email_amount(balance: Decimal, days_overdue: int) -> Decimal:
    return balance + late_fee(balance, days_overdue)


def statement_line_amount(balance: Decimal, days_overdue: int) -> Decimal:
    return balance + late_fee(balance, days_overdue)


if __name__ == "__main__":
    balance = Decimal("500.00")
    days = 10

    email_total = dunning_email_amount(balance, days)
    statement_total = statement_line_amount(balance, days)

    print(f"Dunning email total: {email_total}")
    print(f"Statement total: {statement_total}")
    assert email_total == statement_total
    print("one fee formula, two consumers, structurally in sync")
```

Ran with `python3 dry.py`, output.

```
Dunning email total: 575.00
Statement total: 575.00
one fee formula, two consumers, structurally in sync
```
