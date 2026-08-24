---
name: Dead Code
slug: dead-code
family: 02-code-smells
category: Code Smell
aliases: [Unreachable Code, Unused Code, Vestigial Code, Zombie Code]
first_described: "Beck, Fowler 1999"
maturity: canonical
related: [comments, speculative-generality, lazy-class, duplicate-code, feature-flags]
incompatible_with: []
verified: 2026-08-02
---

# Dead Code

## 1. Name, aliases, and lineage

The canonical name in the literature this repository draws from is Dead Code.
The refactoring that removes it, Remove Dead Code, is one of the named entries
in Martin Fowler's refactoring catalog, described in Martin Fowler, Kent Beck,
John Brant, William Opdyke and Don Roberts, *Refactoring. Improving the Design
of Existing Code*, Addison-Wesley, 1999, and carried forward unchanged in the
second edition, 2018. The catalog page for the refactoring itself, maintained
by Fowler on his own site, opens with the mechanism `if (false) {
doSomethingThatUsedToMatter(); }` as the shape of code that has stopped
mattering but has not been deleted
([refactoring.com/catalog/removeDeadCode.html](https://refactoring.com/catalog/removeDeadCode.html),
verified 2026-08-02). One honest caveat belongs here rather than being
smoothed over. some editions of the catalog present Dead Code primarily as the
target of a refactoring rather than as a separately numbered smell alongside
entries such as Long Method or Feature Envy, and this entry treats it as both,
because the industry usage that grew up around the catalog, in static analysis
tooling, in code review vocabulary, and in linting rule names, has settled on
Dead Code as the name of the smell itself, independent of which page of which
edition first used the words.

The idea is older than the catalog name. Compiler construction calls the same
phenomenon dead code and has run automated dead code elimination as an
optimization pass since early optimizing compilers, a subject covered at
length in the standard compiler-theory reference Alfred V. Aho, Monica S. Lam,
Ravi Sethi and Jeffrey D. Ullman, *Compilers. Principles, Techniques, and
Tools*, 2nd edition, Addison-Wesley, 2006, in the chapters on code
optimization, where dead code elimination sits alongside constant folding and
common subexpression elimination as a data flow analysis over a control flow
graph. That usage predates Fowler's catalog by decades and refers to a
narrower, purely mechanical fact, an instruction whose result is never used
along any path. The refactoring-catalog usage this entry centers on is wider,
and covers a function, a class, a configuration flag, or an entire code path
that a human reader can determine, by reasoning about the system rather than
by running a dataflow algorithm, will never execute or never be read again.

**Unreachable Code** is the term compilers and linters reach for when the
claim is purely syntactic and provable, code that sits after an unconditional
return, break, continue, or raise, where no control flow path can reach it.
**Unused Code** is the broader umbrella covering a declaration, whether a
variable, a parameter, a private method, or an entire class, that nothing in
the reachable call graph refers to. **Vestigial Code** and **Zombie Code** are
informal terms used in code review and in blog writing for code that still
runs but no longer serves the business purpose it was written for, the
classic Knight Capital shape examined in dimension 11 below, where the code
is not unreachable at all, it executes fine, it is simply doing something
nobody wants it to do anymore. Keeping these three registers distinct matters
for this entry because the tooling that finds each one is different, and
conflating them is a common source of false confidence, a team that has
wired up a linter for unreachable code has covered none of the surface that a
call-graph tool like Go's `deadcode` command covers, and neither tool covers
the Knight Capital shape at all, because that code was neither unreachable
nor unused, it was merely unintended.

## 2. Problem and context

Dead code accumulates as an ordinary, unavoidable byproduct of change. A
feature ships, then a later feature makes it redundant, and the branch that
implemented the first feature stops being called, but nobody deletes it,
because deleting it is not the task at hand, the task at hand is building the
new feature. A migration completes and the old code path that fed the old
system is left in place, either because someone was not confident the
migration would hold, or because removing it felt riskier than leaving it.
An experiment ships behind a flag, the experiment concludes, the flag's
default is flipped, and the losing branch of the flag stays in the source
tree because nobody owns the task of flipping the flag away and deleting the
branch. A parameter is added to a function signature for a caller that later
gets refactored away, and the parameter itself, and the branch it
conditioned, outlive the caller. In every one of these cases the code was
written correctly, for a reason that was real at the time, and the smell
appears only in retrospect, once the reason has expired and nobody has told
the code.

The context in which this becomes a problem, rather than a harmless historical
artifact, is any codebase read by more than one person over more than one
sitting, which is to say almost every codebase that survives past a personal
prototype. A reader encountering a function has no way to distinguish, from
the text alone, a function that is load-bearing from one that is a fossil.
Both read the same. Both look intentional. Both invite the same care during a
refactor, the same question in a code review, the same hesitation before
deletion, and the same defensive copy-paste when a new feature looks similar
to what the dead function used to do. The cost of dead code is not that it
runs, in the unreachable case it explicitly does not run, the cost is that it
must be read, understood, and reasoned about by every person who touches the
surrounding code, forever, until someone finally proves it is safe to delete.
That proof gets harder to construct the longer the code sits there, because
the person who wrote it, and the reason it was written, both fade from
institutional memory while the code itself sits unchanged, looking exactly as
confident and intentional as it did on the day it still mattered.

A second, sharper version of the problem is the Knight Capital shape,
examined in full in dimension 11. code that is not unreachable and not
provably unused by any static tool, because some caller somewhere still
invokes it, but which the team believes, incorrectly, to be retired. This is
the more dangerous half of the smell, because it evades every automated
detector that this entry's tooling section describes, and it is the half that
turns a purely cosmetic annoyance into an operational incident.

## 3. Forces

Three forces pull against each other whenever a team decides whether a piece
of code is safe to remove.

**Confidence versus cost of verification.** Deleting a function that turns
out to be load-bearing is expensive to discover and expensive to reverse
under pressure, so the safe default is caution, and caution has a cost. every
hour spent proving a function is truly unreachable is an hour not spent on
new work. Static analysis narrows this cost for the purely unreachable case,
where the proof is mechanical, but for the wider unused case, where the proof
depends on runtime behavior, reflection, dynamic dispatch, or an external
caller outside the analyzed codebase, no tool can offer certainty, only
evidence.

**Reading cost versus deletion risk.** Every line of dead code left in place
is read by every future contributor who encounters the file, and that
per-reading cost compounds across the number of readers and the number of
years the code survives. Against that stands the one-time risk of deleting
something that mattered. The reading cost is diffuse, borne quietly by many
people over a long time, and the deletion risk is concentrated, borne loudly
by whoever pushes the delete and has to explain the outage. Diffuse costs
lose to concentrated risks in most human decision-making, which is exactly
why dead code accumulates rather than getting cleaned as it appears, this
force alone explains most of the smell's prevalence far better than
carelessness does.

**Version control as a safety net versus version control as an excuse.**
The strongest argument for deleting rather than commenting out or flagging
off aggressively is that the code is never actually gone, it is one `git log -p path/to/file`
or one revert away, recoverable at the exact commit where
it was removed, with full history intact. This force is real and should push
teams toward deletion. It also gets used, dishonestly, as an excuse to leave
dead code in place, "we'll just delete it later, it's all in git anyway,"
where the safety net becomes a reason not to act rather than a reason to act
with confidence, and the deletion never happens because there is no forcing
function that makes it happen.

**Static provability versus dynamic reachability.** A statically typed,
ahead-of-time compiled language with no reflection and no dynamic dispatch
lets a tool prove a function unreachable with total certainty, because the
call graph is fixed at compile time. A dynamically typed language, a
plugin architecture, a dependency-injection container that wires
implementations by string name, or a reflection-based framework that invokes
methods it discovers by annotation, all break that certainty, because the
call site the tool needs to see does not exist in source form anywhere the
tool can find it. This is the force that explains why the same smell needs
entirely different tooling per language, covered in dimension 8.

## 4. Applicability and non-applicability

Apply Remove Dead Code, and treat a surviving piece of unused code as a smell
needing action, when the following hold.

- A function, method, class, module, or file has zero call sites in the
  reachable call graph of every entry point the codebase ships, verified by
  a whole-program reachability tool where the language permits one.
- A conditional branch is provably unreachable, guarded by a condition that
  cannot evaluate true, commonly a feature flag whose rollout finished
  months ago and whose value is now hardcoded, or a version check against a
  platform version the product no longer supports.
- A configuration key, environment variable, or database column has no
  remaining reader anywhere in the codebase, confirmed by the same
  reachability discipline this entry's dimension 8 covers for code, cross
  referenced against the equivalent full-stack orphan check for schema and
  configuration.
- Commented-out code blocks sit in the source tree as a substitute for
  deletion. version control already retains this history, so the comment
  form adds reading cost with zero corresponding benefit over deleting it
  outright.
- A parameter, generic type argument, or interface method exists but every
  caller passes the same constant value, or every implementer provides the
  identical body, which is evidence the abstraction the parameter was built
  for never materialized.

Do not remove code, and do not treat the following as the Dead Code smell,
which is the list most catalogs skip and the one that causes the most real
damage when ignored.

- **Code reachable only through reflection, dependency injection by name,
  serialization, or a plugin registry the analysis tool cannot see into.**
  A static reachability tool reports zero call sites for a class that Spring,
  a service locator, or a JSON deserializer instantiates by class name at
  runtime, and deleting it breaks the running system while every automated
  check stayed green. This is the single most common false positive class
  across every tool in dimension 8, and it is the reason none of those tools
  should run in an unattended, auto-delete mode.
- **Public API surface of a published library.** A library's exported
  function may have zero callers inside the library's own repository while
  having many callers in every downstream consumer the library author has
  never seen. Reachability analysis is sound only within the boundary of what
  it can see, and a library's boundary is porous by design.
- **Code behind a feature flag that is mid-rollout, not finished.** The
  losing branch of an active experiment or an in-progress staged rollout is
  not dead, it is temporarily unreached in the current environment and fully
  live in others, or scheduled to become live once the rollout percentage
  increases. Confusing an active flag with a retired one is exactly the
  mistake dimension 11 examines in the Knight Capital incident, in reverse,
  there the retired flag was mistaken for something still safe to leave in
  place, here the mistake is the opposite, treating an active flag's
  currently-losing branch as dead.
- **Debug, diagnostic, or admin-only code paths exercised only outside the
  normal request path.** A route mounted only when an environment variable is
  set, an admin panel gated behind an internal-only header, or a debug dump
  triggered by a signal handler, all look unreachable to a tool that only
  traces the default request path from `main`, and all matter.
- **Code required to satisfy a contract, an interface, or a regulatory
  retention obligation, even when currently unexercised.** An unimplemented
  branch of a state machine required for a compliance audit trail, or a
  fallback handler mandated by a service level agreement for an error class
  that has not occurred yet, is not dead, it is insurance, and insurance
  looking unused is the entire point of insurance.
- **A single commented-out line left deliberately as a note about an approach
  that was tried and rejected, paired with a comment explaining why**, is a
  judgement call rather than a hard rule, and many teams choose to keep a very
  small number of these as institutional memory rather than committing the
  same rejected approach to git history where nobody will ever look at it
  again. This is a narrow exception and should not be read as license for the
  wholesale commented-out blocks the applicability list above targets.

## 5. Structure

Dead code is a smell, not a design pattern, so it has no participants that
collaborate toward a goal. What it has instead is a shape, a location in the
call graph and the reachability graph, and this entry treats that location as
its structure. Four positions describe every instance of the smell.

**The declaration.** The function, method, class, variable, import,
configuration key, or database column whose text still exists in the source
tree or schema.

**The call graph, or reachability graph.** The set of edges from every entry
point the program ships, a `main` function, an HTTP route table, a message
queue consumer, a cron job registration, a test runner's discovered test
list, out through every reachable declaration. A declaration is dead
precisely when no path in this graph reaches it, and live precisely when at
least one path does, however rare that path's execution is at runtime.

**The guard, for the reachable-but-unreachable-in-practice case.** A
conditional expression, a feature flag check, a platform version comparison,
or a configuration switch, whose value determines whether a branch that is
syntactically present and structurally reachable ever actually executes. When
the guard's value is now fixed, because the flag has been fully rolled out,
or the platform version can no longer be less than the check, the branch it
protects is dead even though the call graph, drawn without evaluating the
guard's value, would still show it as reachable.

**The verification evidence.** Whatever record, whether a whole-program
static analysis report, a production code-coverage trace collected over a
representative time window, a grep across the codebase and its known
consumers, or an explicit acknowledgment from the person who owns the
declaration, establishes that no live path reaches the declaration. This
fourth element is the one most catalogs omit and the one this entry treats as
load bearing, because a claim of dead code with no evidence behind it is
indistinguishable, to the next reader, from a claim that happens to be wrong.

## 6. ASCII structure diagram

```
REACHABILITY GRAPH

Entry points: main(), httpRoute /orders, cronJob nightly

main() and httpRoute /orders both call dispatch(), which
calls:
  handleOrder()
  applyTax()
  validate()

cronJob nightly calls reconcile(), which calls:
  readLedger()
  writeLedger()

This is the live subgraph, every function above has a path
back to an entry point.

Dead subgraph: applyLegacyDiscount(). No incoming edge from
any entry point above, zero paths back to any entry point.


GUARD-GATED BRANCH

process(order)
     |
     v
if legacyFlag.isEnabled():
    doLegacyPath(order)
else:
    doCurrentPath(order)

legacyFlag is hardcoded false in every environment since the
rollout finished.

doLegacyPath: dead, guard never true.
doCurrentPath: live, the only path actually taken.

doLegacyPath is structurally reachable but practically dead,
needs the guard's known value as evidence, not the call
graph alone.
```

## 7. Dynamics

Dead code has no runtime dynamics of its own, by definition nothing runs
along the paths that matter to this entry, so what belongs here instead is
the lifecycle a piece of code moves through as it becomes dead, and the
sequence a team follows to verify and remove it.

```
LIFECYCLE OF A DECLARATION

  written, called by >=1 live path
        |
        v
  a change removes the last caller
  (a migration completes, an experiment
   concludes, a caller is refactored)
        |
        v
  declaration becomes UNREACHABLE
  but the source text is unchanged
        |
        v
  time passes; institutional memory
  of "why this exists" decays
        |
        v
  a static tool, a coverage gap, or a
  human reviewer flags it as dead
        |
        v
  VERIFICATION SEQUENCE (dimension 15)
        |
        +--> confirm zero static call sites
        |         |
        |         v
        +--> confirm zero production coverage
        |    over a representative window
        |         |
        |         v
        +--> confirm no reflective, DI, or
        |    plugin-registry reference
        |         |
        |         v
        +--> confirm no external/public API
        |    consumer outside the repo
        |         |
        v         v
    all four pass?  -- no --> treat as false positive,
        |                     annotate the guard instead
       yes
        |
        v
  DELETE, in one commit, referencing
  the verification evidence in the
  commit message (dimension 14)
```

## 8. Implementation variants

The mechanism that finds and removes dead code differs by how much the
language commits its structure to compile time versus how much it defers to
runtime, and this section walks the variants in that order, most static
first.

**Compile-time hard errors for unused locals and imports.** Go's compiler
refuses to compile a source file that imports a package it never references,
"imported and not used" is a build-blocking error rather than a lint warning,
and a compiler may also make it an error to declare an unused local variable
inside a function body, a restriction the language specification names
explicitly ([go.dev/ref/spec](https://go.dev/ref/spec), section on variable
declarations, verified 2026-08-04). This variant gives the strongest possible
guarantee for the two narrowest categories it covers, an unused import and an
unused local variable can never survive to production in a Go binary, but it
is silent about an unused top-level function or method, which the compiler
happily builds, verified directly against `go build` on a sample file in
dimension "code examples" below.

**Compile-time warnings for unused declarations, opt-in to errors.**
TypeScript's `noUnusedLocals` and `noUnusedParameters` compiler flags turn an
unused private class member or an unused local into a build failure when
enabled, verified directly by compiling a sample file with `tsc --strict
--noUnusedLocals --noUnusedParameters`, which reported `error TS6133:
'applyLegacyDiscount' is declared but its value is never read` for a genuinely
uncalled private method. Rust's `dead_code` lint is on by default at the
`warn` level and reports "function is never used" for any unexported item
with no caller found within the crate being compiled, again verified directly
by compiling a sample with `rustc -W dead-code`
([doc.rust-lang.org/rustc/lints](https://doc.rust-lang.org/rustc/lints/listing/warn-by-default.html),
verified 2026-08-04). Swift's compiler warns on an unused local binding,
"initialization of immutable value was never used," verified directly with
`swiftc`, but does not warn, by default, on an unused private method the way
Rust and TypeScript's opt-in flag do, which is a real and useful difference to
know before assuming Swift's diagnostics cover the same ground.

**Whole-program static reachability analysis.** For languages or situations
where the compiler's own unused-declaration diagnostics stop at the file or
package boundary, a separate whole-program tool walks the call graph starting
from declared entry points. Go's own `golang.org/x/tools/cmd/deadcode`
command builds a call graph using rapid type analysis from a program's `main`
function and reports every function unreachable from it, explicitly
supporting a `-whylive` flag to explain why a function that looked dead is
actually reachable through an indirect path, which is the tool's own built-in
defense against the false-positive risk this entry keeps returning to
([pkg.go.dev/golang.org/x/tools/cmd/deadcode](https://pkg.go.dev/golang.org/x/tools/cmd/deadcode),
verified 2026-08-04). Knip performs the equivalent analysis for TypeScript
and JavaScript projects, finding unused files, unused exports, unused
dependencies, and unused types across an entire repository rather than one
file at a time, and is adopted widely enough to name specific outcomes, one
integration reports deleting roughly 300,000 lines of unused code at Vercel
([knip.dev](https://knip.dev/), verified 2026-08-04, dimension 9 below has the
fuller adopter list).

**Confidence-scored heuristic detection for dynamic languages.** Python has
no compile step and no static call graph a tool can fully trust, because
`getattr`, string-based dispatch, and framework conventions such as Django's
URL routing or a plugin's entry-point discovery all create call sites no
parser can see. Vulture, a Python static analyzer, resolves this by assigning
a confidence percentage to every finding rather than a flat yes-or-no verdict,
100 percent for unreachable code following a `return`, `break`, `continue`,
or `raise`, 90 percent for an unused import, and 60 percent for an unused
attribute, class, function, method, or variable, and it recommends generating
a whitelist file to suppress code that is only ever called implicitly
([vulture, github.com/jendrikseipp/vulture](https://github.com/jendrikseipp/vulture),
verified 2026-08-04). This variant is a direct engineering response to the
non-applicability forces in dimension 4, rather than pretending certainty it
cannot have, the tool reports its own uncertainty as a number and leaves the
judgement call to the reader, which this entry considers the correct default
posture for any dynamically dispatched language.

**Coverage-driven detection.** Rather than reasoning about the call graph at
all, this variant instruments a running program, typically in a staging or
production environment over a representative time window spanning at least
one full business cycle, and flags any function or branch that recorded zero
executions. This catches the categories static analysis structurally cannot,
reflective calls, dynamically dispatched handlers, and rarely exercised
integration code, at the cost of only ever proving "unused during this
window," never "unused, period," which is why dimension 15 treats coverage
evidence as necessary but not sufficient on its own.

**Bundler-level dead code elimination, known as tree shaking.** JavaScript
bundlers including webpack perform an automated, build-time variant of this
same idea for the specific case of ES module exports, relying on the static
`import` and `export` syntax of ES2015 modules to prove which exported
bindings a given entry point actually uses, and stripping the rest from the
production bundle. Webpack's own documentation states plainly that "tree
shaking is a term commonly used in the JavaScript context for dead-code
elimination"
([webpack.js.org/guides/tree-shaking](https://webpack.js.org/guides/tree-shaking/),
verified 2026-08-04). This variant differs from every other one in this list
by removing dead code automatically as part of every production build rather
than surfacing it for a human to review and delete from source, and it works
only because the ES module system was designed with enough static structure
to make the reachability proof sound at build time, the same static-versus-
dynamic force from dimension 3 in its purest bundler-level form.

## 9. Known production uses

Knip is adopted across an unusually well-documented set of named production
codebases for a tool in this category, its own site lists Adobe, Anthropic,
Astro, AWS, Cloudflare, Datadog, ESLint, Google, Microsoft, Shopify, Svelte,
TanStack, and Vercel as users, and quotes a specific outcome, one adopter
reporting that Knip "helped us delete ~300k lines of unused code at Vercel"
([knip.dev](https://knip.dev/), verified 2026-08-04). This is the strongest
available evidence in this entry that the smell, and the discipline of
actively hunting for it with a whole-program tool rather than relying on
manual review, is a live, ongoing practice inside large, well-resourced
engineering organizations rather than a purely academic concern.

Webpack's tree-shaking pass is a dead-code-elimination mechanism running
inside one of the most widely deployed JavaScript build tools in production
use, applied automatically to every production bundle a project builds with
webpack's default configuration once ES module syntax is used throughout the
dependency graph, per webpack's own guide describing the mechanism
([webpack.js.org/guides/tree-shaking](https://webpack.js.org/guides/tree-shaking/),
verified 2026-08-04). Every website shipping a webpack-built JavaScript bundle
with unused exports stripped from it is, in this narrow but very real sense,
a production instance of automated dead code removal running on every deploy.

Go's official toolchain ships `golang.org/x/tools/cmd/deadcode` as a
maintained command distributed alongside the language's other developer
tools, built specifically to report functions unreachable from a program's
`main` entry point using rapid type analysis over the full program, including
sound handling of interface dispatch and reflection where it can be proven
safe
([pkg.go.dev/golang.org/x/tools/cmd/deadcode](https://pkg.go.dev/golang.org/x/tools/cmd/deadcode),
verified 2026-08-04). Its existence as an officially maintained tool, rather
than a third-party experiment, is itself evidence that dead code detection at
whole-program scale is a problem the Go team judged common enough across its
own production user base to justify first-party tooling.

## 10. Consequences

Positive, from removing dead code and keeping it removed as a discipline.

- Every remaining line in the codebase is a candidate for actually mattering,
  which lowers the cognitive tax a reader pays on every file they open,
  because they no longer have to separately ask "is this real" before asking
  "what does this do."
- The reachable surface a refactor has to reason about shrinks, which lowers
  the risk of an unrelated regression, a function that cannot be called
  cannot be broken by a change to its neighbors, but a function that looks
  callable invites a defensive touch during refactors that a genuinely dead
  function does not deserve.
- Build artifacts, whether a compiled binary, a JavaScript bundle, or a
  container image, shrink when dead code is removed before it is ever
  shipped, directly through mechanisms such as tree shaking, and indirectly
  through smaller source trees compiling faster.
- A smaller reachable call graph is a smaller attack surface, examined fully
  in dimension 17, an endpoint, a deserialization path, or a debug hook that
  cannot be reached cannot be exploited, no matter what vulnerability it
  contains.
- Removing dead code forces the exact verification discipline in dimension 15
  onto the team as a habit, which as a side effect improves the team's actual
  understanding of its own reachability graph, an understanding that pays off
  again the next time an incident requires tracing what can and cannot be
  called from where.

Negative, or the genuine cost this smell's removal carries.

- Deletion is irreversible in the moment it happens, and the verification
  evidence dimension 5 requires is only ever probabilistic outside of a
  fully static, fully compiled, reflection-free language, so every deletion
  carries some residual risk that the code was live through a path the
  verification missed. This is the central tension of the whole smell and
  this entry does not pretend it away.
- Aggressive automated deletion, run without a human review step, is
  qualitatively more dangerous than leaving dead code in place, because a
  false positive that deletes live code fails loudly and immediately in
  production, while a false negative that leaves genuinely dead code in
  place merely costs reading time, an asymmetric risk profile that argues
  for keeping a human in the loop even when tooling is excellent.
- Whole-program reachability tooling has real setup and maintenance cost of
  its own, correctly configuring entry points, excluding generated code,
  and maintaining a whitelist for reflectively-called code is ongoing work,
  not a one-time install, and a team that treats the tool's first report as
  ground truth without tuning it will chase false positives.
- A codebase mid-migration, or one that deliberately retains legacy paths for
  regulatory or rollback reasons, has a legitimately larger amount of
  code that LOOKS dead under naive analysis than a codebase not in that
  state, and applying this smell's removal discipline too eagerly during such
  a period can delete the exact rollback path the migration needs if it
  fails, which is precisely the non-applicability case in dimension 4.

## 11. Failure modes and misuse

**Symptom.** A tool reports zero call sites for a class, the team deletes it,
and the production system starts throwing a class-not-found or similar
runtime error under a specific request shape that the automated test suite
never exercised.
**Cause.** The class was instantiated by a dependency-injection container, a
service locator, or a deserialization framework using its fully qualified
name as a string or an annotation, none of which appear as a textual call
site any static analyzer can see, exactly the non-applicability case named
first in dimension 4.
**Fix.** Before treating a static reachability report as sufficient evidence
in any language with a reflection or dependency-injection ecosystem in wide
use, cross-check the report against a full-text search for the class or
method's bare name as a string literal anywhere in the codebase and its
configuration files, and treat a hit there as a reason to investigate rather
than to delete.

**Symptom.** A team runs a code coverage report over a two-week window,
finds a function with zero hits, deletes it, and three months later a
quarterly batch job or an annual billing-cycle handler fails because the
function it called no longer exists.
**Cause.** Coverage evidence is only ever a statement about the window it was
collected over, and a function that legitimately runs on a cadence longer
than the window will always show zero coverage during that window, no matter
how live it actually is.
**Fix.** Treat a coverage window shorter than one full business cycle,
typically at minimum a month and ideally a full quarter or year for anything
touching billing, reporting, or compliance, as insufficient evidence on its
own, and require it to be combined with a static reachability check and, for
anything financially or legally significant, an explicit sign-off from the
function's domain owner before deletion.

**Symptom.** A specific, narrow, and genuinely serious version of the
symptom above. code that everyone believed was retired executes anyway,
under conditions nobody expects, and does real financial or operational
damage before anyone notices. This is the Knight Capital shape named in
dimension 1. In August 2012, Knight Capital deployed new code implementing a
Retail Liquidity Program feature to seven of eight production servers,
repurposing a flag that had previously activated an old, retired function
called Power Peg. The eighth server never received the update. When live
order flow arrived carrying the repurposed flag, that eighth server routed
orders into the old Power Peg code path, which was still fully present in
the deployed binary, and which, because the code responsible for reporting
order fulfillment back had been altered when Power Peg was deprecated, sent
out orders indefinitely without ever recording them as filled. Over roughly
45 minutes this generated 4 million executions across 154 stocks totaling
more than 397 million shares, disrupted prices in 148 New York Stock Exchange
listed companies, and cost Knight Capital a pre-tax loss reported at $440
million, wiping out roughly three-quarters of the firm's equity value within
a day
([Knight Capital Group, en.wikipedia.org](https://en.wikipedia.org/wiki/Knight_Capital_Group),
verified 2026-08-04).
**Cause.** The Power Peg code was not unreachable by any static analysis,
its call site existed and was reachable through the very flag the new
feature repurposed, so no dead code tool of any kind would ever have flagged
it. It was retired only in the sense that the team's operational understanding
said it was retired, and that understanding was never encoded anywhere the
system itself could check, and it was never actually deleted from the eight
production servers, seven of which happened not to route flow into it, purely
by chance of how the specific update happened to interact with each server's
prior state.
**Fix.** The lesson this entry draws is not that dead code tooling should
have caught this, no tool in dimension 8 claims to catch it, because the code
was not dead by any of those tools' definitions. The lesson is that "we don't
use this anymore" is a claim about intent and operational practice, not a
property a static or coverage tool can verify, and that a flag or code path
believed retired must be either fully deleted from every deployed artifact,
with the deletion itself verified across every server the deployment reaches,
or explicitly and permanently disabled at the point of use in a way that
survives an unrelated code change reusing an adjacent identifier, never left
present-but-believed-inert as an assumption living only in the team's memory.

**Symptom.** A team enables a whole-program dead code tool for the first
time, runs it, and gets a report of hundreds of findings, most of which turn
out on inspection to be exported public API used only by a separate,
downstream repository the tool cannot see.
**Cause.** Running whole-program reachability analysis against a library or
a monorepo package boundary without first configuring the tool's entry
points to include every externally consumed export, which is exactly the
public-API non-applicability case from dimension 4.
**Fix.** Configure the tool's entry-point list explicitly to include every
publicly exported symbol before trusting its first report, and for a
genuinely public library, treat its exported surface as permanently live
from the tool's perspective regardless of internal call count, reserving
whole-program deletion analysis for the library's private internals only.

## 12. Trade-off matrix

| Force | Comment it out, keep it in the source | Delete and rely on version control | Feature-flag it off permanently | Whole-program automated deletion, unattended |
|---|---|---|---|---|
| Reading cost for future contributors | Highest. every reader pays the cost of parsing and dismissing it, forever, with no compiler or reachability tool ever removing the burden | Lowest. gone from the file entirely, history remains one `git log` away for the rare case someone needs it | Low to moderate. the branch is gone from the active path but the flag machinery and dead branch text often linger, which is exactly how the Knight Capital shape starts | Lowest in the short run, but see the recoverability row, an unattended false positive turns a reading-cost problem into an incident |
| Recoverability if the deletion turns out to be wrong | Perfect, nothing was removed, at the cost of paying the reading cost the whole time it sits there | Very good in a well-hooked repository, restorable from history in minutes, but requires someone to notice quickly | Poor, a permanently-off flag whose branch is later fully deleted is as recoverable as any delete, but the intermediate flagged-off state is often mistaken for done when it is not | Worst, because there is no human review step at the moment of deletion to catch a false positive before it ships |
| Confidence required before acting | None, this is the do-nothing option, which is exactly its problem | Requires the full verification sequence in dimension 15 | Requires confirming the flag's rollout is genuinely complete and permanent, a narrower but still real confidence bar | Requires near-total confidence in the tool's soundness for the specific language and framework, rarely achievable given the non-applicability cases in dimension 4 |
| Appropriate default posture | Never the right long-term choice per dimension 4's explicit guidance, acceptable only for a single, deliberately annotated rejected-approach note | The right default for anything static analysis and coverage evidence together can confirm dead | The right intermediate step for anything mid-rollout, converted to full deletion once the rollout is confirmed permanent | Appropriate only as report generation feeding a human review step, never as an unattended production action |

## 13. Related and incompatible patterns

**Comments**, covered elsewhere in this repository's code smell family,
shares a root cause with Dead Code in the specific case of a comment that
describes behavior the code beside it no longer implements, a comment left
behind by the same kind of change that leaves code behind, an explanation
whose subject has moved on without it. The two smells often travel together,
a commented-out block is simultaneously an instance of Dead Code and a
comment that has stopped being true the moment execution passed it by.

**Speculative Generality** is Dead Code's forward-looking sibling rather than
its backward-looking cousin. where Dead Code is capability that used to be
needed and no longer is, Speculative Generality is capability built in
anticipation of a need that never arrived, an abstract base class with one
subclass, a configuration parameter no caller ever varies, a strategy
interface with a single strategy. Both smells produce structurally similar
evidence, low or zero real usage, but the fix differs in tone, Dead Code is
removed because its job is finished, Speculative Generality is removed, or
its unneeded flexibility is collapsed, because its job never started.

**Lazy Class** overlaps with Dead Code at the extreme, a class reduced by
successive removals of dead methods down to a single trivial remaining
responsibility is a Lazy Class candidate, and the refactoring path in
dimension 14 explicitly checks for this outcome, deleting a dead method can
leave its containing class newly eligible for a separate Inline Class
refactoring.

**Duplicate Code** relates to Dead Code through a specific failure pattern,
a team unsure whether an old implementation is safe to delete sometimes
writes a new implementation alongside it rather than replacing it in place,
intending to delete the old one "once we're sure," and the old one then
becomes simultaneously duplicate and, once the new path is fully adopted,
dead, compounding both smells until someone finally removes it.

**Feature Flags**, as an operational practice rather than a named pattern in
this repository yet, is the mechanism most directly responsible for
turning what would otherwise be an ordinary Dead Code cleanup into the
Knight Capital failure mode. a flag that gates a code path is, by
construction, a place where "this branch is currently dead" and "this
branch will become live again if the flag's value changes" are both true
statements about the same code at the same time, and confusing which one
applies is the single most consequential misuse this entry documents. This
entry treats feature flags as related rather than incompatible, because the
practice of flagging is not itself wrong, the failure is in never following
through to full deletion once a flag's rollout is permanently decided.

No pattern in this repository is incompatible with removing genuinely dead
code in the strict sense of one precluding the other, the empty
`incompatible_with` list in this entry's frontmatter reflects that
correctly, but dimension 4's non-applicability list functions as the
practical incompatibility this entry actually needs, several legitimate
design choices, a public library boundary, a compliance retention
requirement, a mid-rollout flag, produce code that resembles Dead Code
closely enough that applying the removal discipline without checking that
list first is the real risk, not any conflict with another named pattern.

## 14. Refactoring path in and out

There is no path "into" this smell in the sense of a deliberate design
decision, nobody sets out to write dead code, it arrives as the residue of
an earlier, legitimate decision once that decision's context expires, which
is exactly dimension 2's account of the problem. The path this dimension
covers, then, is entirely the path out, from suspected-dead to confidently
removed.

1. **Identify a candidate.** A candidate surfaces from one of several
   sources, a whole-program static tool's report, a coverage report showing
   zero hits over a representative window, a code review comment noticing a
   function with no visible callers, or direct knowledge that a feature
   shipped and its predecessor was meant to be retired.

2. **Run the full verification sequence from dimension 15 before touching
   anything.** Static zero-call-sites, coverage zero-hits over a full
   business cycle where relevant, a full-text search for the symbol's bare
   name to catch reflective and DI-based references, and a check against
   the non-applicability list in dimension 4, particularly whether the
   candidate is public API, is mid-rollout, or is a compliance requirement.

3. **If the candidate fails any check in step 2, stop, and instead annotate
   rather than delete.** Where the code is genuinely reachable but the team
   wants to record that it should be revisited, mark it explicitly, a
   `// TODO: remove once rollout X reaches 100%, tracked in ISSUE-123` comment
   or equivalent, rather than treating "probably dead" as equivalent to
   "confirmed dead."

4. **If the candidate passes every check, delete it in a single, focused
   commit** whose message states the verification evidence explicitly,
   which static tool run and which coverage window were consulted, so a
   future reader who finds the deletion in `git blame` can see why it was
   judged safe rather than having to re-derive the confidence from scratch.
   This composes directly with a codebase's committed history as the safety
   net referenced throughout dimension 3, the commit message is the
   documentation of the proof, not merely of the change.

5. **Where the deletion is of a function or class that used to guard against
   a Lazy Class or a now-pointless abstraction**, per dimension 13, check
   whether the containing class or module has become trivial as a result and
   is itself now a candidate for a separate Inline Class or Collapse
   Hierarchy refactoring, rather than treating the dead-code deletion as
   fully finished the moment the immediate candidate is gone.

6. **Where the deletion removes the last caller of some other declaration**,
   re-run the reachability check on that newly-orphaned declaration too,
   dead code removal is often iterative, deleting one function frequently
   makes a second, previously-live function newly dead, and stopping after
   one pass leaves that second function for someone else to rediscover
   later.

## 15. Testing and verification

Verifying that a piece of code is genuinely dead, rather than merely rare, is
the load-bearing activity this entire smell revolves around, and it is
strictly harder than testing that a piece of code works, because a positive
claim, "this code does X," can be demonstrated by a single passing test,
while the claim this entry cares about, "no path anywhere reaches this
code," is a universal negative that no single test can ever fully establish.
The practical response, consistent across every serious tool this entry has
examined, is to combine several independent, partial forms of evidence
rather than trusting any one of them alone.

**Static reachability, where the language supports it soundly.** Run the
whole-program tool appropriate to the language, Go's `deadcode` command, or
Knip for a TypeScript or JavaScript repository, and treat its report of zero
call sites as the strongest single piece of evidence available, while
remembering that its soundness stops exactly at the boundary the tool cannot
see into, reflection, dependency-injection-by-name, and any consumer outside
the analyzed repository, as dimension 4 lays out.

**Coverage over a representative production window.** Where feasible,
instrument the running system rather than only the test suite, because unit
and integration tests exercise the paths their authors thought to test, which
is frequently a smaller set than the paths production traffic actually
exercises. A coverage report from real traffic over a full business cycle is
stronger evidence of true reachability than a green test suite is, and the
Knight Capital incident is a sharp reminder that a code path can be entirely
untested and entirely unmentioned in documentation while still being live in
production, which is precisely why coverage evidence and static evidence
need to be gathered together rather than either one alone.

**A full-text search for the bare symbol name.** This is the cheapest check
in the sequence and the one most teams skip, and it is the single check that
would have caught the false-positive failure mode named first in dimension
11, a class instantiated by fully-qualified name from a configuration file
or an annotation will surface in a plain grep even when it surfaces nowhere
in a call-graph analysis, because the reference exists as a string rather
than as syntax the parser recognizes as a call.

**Deletion as its own test.** Once a candidate passes the checks above, the
strongest remaining verification step is often simply deleting it and
running the full build, the full test suite, and, for anything
production-facing, a staged rollout with monitoring, because a compiler
error, a failing test, or a production alert triggered by the deletion is
conclusive evidence that a caller existed that the earlier evidence missed.
This step only works safely when version control makes the deletion cheaply
reversible, tying directly back to the version-control force in dimension 3.

**What becomes easier and what becomes harder because of this discipline.**
A codebase with a mature dead-code-detection habit makes the next
verification cycle easier, because the reachability graph stays close to
accurate over time rather than accumulating years of drift, and a
well-maintained whitelist of reflectively-called symbols, built up
incrementally as false positives are found and confirmed live, becomes
institutional documentation of exactly where the static analysis boundary
sits. What becomes harder is trusting a single tool's report in isolation,
once a team has been burned once by a false positive, the discipline
correctly shifts toward requiring the combined evidence this dimension
describes rather than a single green check mark.

## 16. Observability signals

A healthy instance of this discipline shows up in a few concrete,
measurable signals, and an unhealthy one, whether from neglect or from
overcorrection into unattended automated deletion, shows up in the
corresponding failures of those same signals.

- **Trend of the whole-program dead-code tool's finding count over time.** A
  team actively practicing this discipline shows this count oscillating
  around a low, roughly stable baseline, rising modestly after a feature
  ships and its predecessor is retired, then falling back down as the
  refactoring path in dimension 14 runs its course within a sprint or two. A
  monotonically rising count, with no corresponding deletions, is the signal
  that the discipline has stalled and dead code is accumulating unchecked.
- **Ratio of deletion commits that reference verification evidence in their
  message, per step 4 of dimension 14, against deletion commits that do
  not.** A high ratio indicates the team is following the discipline rather
  than deleting on a hunch, and gives future incident responders a paper
  trail to follow when a deletion turns out, rarely, to have been wrong.
- **Post-deletion incident count, specifically incidents whose root cause
  traces to a deletion previously judged safe by this entry's verification
  sequence.** This should trend toward, and stay near, zero, and any nonzero
  count deserves a retrospective specifically asking which of the four
  verification steps in dimension 15 was skipped or gave a false pass,
  because that is the concrete, correctable gap rather than a vague call to
  "be more careful."
- **Production coverage gaps that persist across multiple consecutive
  measurement windows without either a deletion or an explicit
  keep-alive annotation being added.** This is the queue of unresolved
  candidates from step 1 of dimension 14, and a growing, aging queue with no
  throughput is the clearest possible dashboard signal that the team has
  identified dead code faster than it is willing, or able, to remove it.
- **Age and staleness of the reflective-reference whitelist a tool like
  Vulture accumulates.** A whitelist entry that is itself unreferenced by
  any current framework configuration is worth periodically re-auditing, an
  entry added years ago to suppress a false positive for a plugin the system
  no longer loads has quietly become dead code about dead code, and belongs
  back in the review queue.

## 17. Security and privacy implications

Dead code that is genuinely unreachable poses no runtime attack surface by
the strict definition, code nothing can call cannot be exploited through
that call path, and this is one of the real security benefits removing it
provides, reflected already in dimension 10's consequences. The security
implications this dimension actually needs to cover, then, are the two
places where the smell's boundary cases turn a maintenance annoyance into a
genuine exposure.

First, an administrative, debug, or diagnostic endpoint that a shallow
reachability analysis judges dead because the main application's normal
request flow never reaches it, while it remains fully live and reachable
through a separate, less-traveled entry point, an internal-only route, a
signal handler, or a management port, is exactly the non-applicability case
named in dimension 4, and it is a genuine security liability precisely
because the team's mental model, having been told the tool found it
unreachable, treats it as gone rather than as an active, unmonitored attack
surface that still needs the same access control, input validation, and
patching discipline as any other live endpoint.

Second, and more seriously, code believed retired but never actually
deleted or permanently disabled is a latent activation risk whether or not
the trigger that reactivates it is malicious. The Knight Capital incident in
dimension 11 was not a security breach in the adversarial sense, nobody
attacked the system, but its mechanism, an old, believed-dead code path
reactivated by an unrelated change reusing an adjacent flag, is structurally
identical to how a genuine attacker would want to trigger unmaintained,
unmonitored, believed-dormant functionality on purpose, a code path nobody
is watching, patching, or testing is a code path whose behavior under
adversarial input is unknown, precisely because everyone stopped paying
attention to it. This is engineering judgement rather than a sourced claim
about a specific attack, the structural parallel is the point, code left
present-but-believed-inert should be treated, from a security review
perspective, with the same suspicion as code known to be actively exposed,
because "we think nobody can trigger this" and "we have verified nobody can
trigger this" are different claims with very different risk profiles, and
this entry's dimension 15 exists precisely to convert the first into the
second before anyone relies on it.

On the data-handling side specifically, a dead code path that still holds a
reference to, logs, or forwards personal or sensitive data, even while
unreachable from the current production entry points, remains a liability
under most data-protection regimes if it is ever reactivated by exactly the
mechanism Knight Capital's incident demonstrated, and removing dead code
that touches sensitive data is correspondingly higher priority, not lower
priority, than removing dead code that does not, because the blast radius of
an accidental reactivation is measured in exposed records rather than only
in engineering time.

## 18. References

- Martin Fowler, Kent Beck, John Brant, William Opdyke, Don Roberts,
  *Refactoring. Improving the Design of Existing Code*, Addison-Wesley,
  1999, and the second edition, Martin Fowler with Kent Beck, 2018, the
  origin catalog for the smell and refactoring vocabulary this entry
  builds on. The web edition of the specific refactoring is at
  [refactoring.com/catalog/removeDeadCode.html](https://refactoring.com/catalog/removeDeadCode.html),
  verified 2026-08-02.
- Alfred V. Aho, Monica S. Lam, Ravi Sethi, Jeffrey D. Ullman, *Compilers.
  Principles, Techniques, and Tools*, 2nd edition, Addison-Wesley, 2006, the
  compiler-theory account of dead code elimination as a data flow
  optimization, referenced in dimension 1 for the narrower, purely mechanical
  sense of the term.
- The Go Programming Language Specification, variable declarations section,
  on the implementation restriction permitting a compiler to reject an
  unused local variable, [go.dev/ref/spec](https://go.dev/ref/spec), verified
  2026-08-04.
- The `dead_code` lint, part of Rust's warn-by-default lint group,
  [doc.rust-lang.org/rustc/lints/listing/warn-by-default.html](https://doc.rust-lang.org/rustc/lints/listing/warn-by-default.html),
  verified 2026-08-04.
- The `no-unused-vars` rule, ESLint, stating its purpose that "variables that
  are declared and not used anywhere in the code are most likely an error
  due to incomplete refactoring,"
  [eslint.org/docs/latest/rules/no-unused-vars](https://eslint.org/docs/latest/rules/no-unused-vars),
  verified 2026-08-02.
- Vulture, a Python dead code static analyzer, its confidence-scoring
  mechanism and whitelist approach for reflectively-called code,
  [github.com/jendrikseipp/vulture](https://github.com/jendrikseipp/vulture),
  verified 2026-08-04.
- Knip, a whole-project unused-code, unused-export, and unused-dependency
  finder for TypeScript and JavaScript, with named production adopters
  including Vercel, Anthropic, Google, and Microsoft,
  [knip.dev](https://knip.dev/), verified 2026-08-04.
- The `deadcode` command, part of the official `golang.org/x/tools`
  distribution, reporting functions unreachable from a Go program's `main`
  using rapid type analysis,
  [pkg.go.dev/golang.org/x/tools/cmd/deadcode](https://pkg.go.dev/golang.org/x/tools/cmd/deadcode),
  verified 2026-08-04.
- "Tree shaking," webpack's own guide describing dead-code elimination for
  ES modules at bundle time,
  [webpack.js.org/guides/tree-shaking](https://webpack.js.org/guides/tree-shaking/),
  verified 2026-08-04.
- "Knight Capital Group," the 2012 trading incident used in dimension 11 as
  the primary account of dead, believed-retired code being reactivated in
  production with severe financial consequences,
  [en.wikipedia.org/wiki/Knight_Capital_Group](https://en.wikipedia.org/wiki/Knight_Capital_Group),
  verified 2026-08-04.

## Code examples

All five samples below were compiled or run directly against the toolchains
installed in the authoring environment, and the diagnostic output quoted next
to each one is the real, observed output of that run, not a reconstruction.

### TypeScript

```typescript
interface Order {
  id: string;
  total: number;
}

class OrderProcessor {
  private taxRate = 0.19;

  process(order: Order): number {
    if (order.total < 0) {
      throw new Error("negative total");
    }
    return this.applyTax(order.total);
  }

  private applyTax(amount: number): number {
    return amount * (1 + this.taxRate);
  }

  // Dead: no call site anywhere in this file or any importer.
  private applyLegacyDiscount(amount: number): number {
    return amount * 0.95;
  }
}

const p = new OrderProcessor();
console.log(p.process({ id: "o1", total: 100 }));
```

Compiled with `tsc --strict --noUnusedLocals --noUnusedParameters --noEmit`
against TypeScript 5.9, producing exactly one diagnostic, exit code 2.

```
sample.ts(21,11): error TS6133: 'applyLegacyDiscount' is declared but its value is never read.
```

### Python

```python
class OrderProcessor:
    TAX_RATE = 0.19

    def process(self, total: float) -> float:
        if total < 0:
            raise ValueError("negative total")
        return self._apply_tax(total)

    def _apply_tax(self, amount: float) -> float:
        return amount * (1 + self.TAX_RATE)

    def _apply_legacy_discount(self, amount: float) -> float:
        # Dead: nothing in this module or its test suite calls this.
        return amount * 0.95


processor = OrderProcessor()
print(processor.process(100.0))
```

Run directly with `python3`, output `119.0`, no diagnostic, because CPython
performs no unused-declaration analysis at all, this is the exact absence of
a compile-time signal that motivates a separate tool. Running Vulture 2.14
against the same file surfaces the dead method at its documented 60 percent
confidence tier for an unused method.

```
sample.py:15: unused method '_apply_legacy_discount' (60% confidence)
```

### Go

```go
package main

import "fmt"

const taxRate = 0.19

func applyTax(amount float64) float64 {
	return amount * (1 + taxRate)
}

func applyLegacyDiscount(amount float64) float64 {
	return amount * 0.95
}

func process(total float64) float64 {
	if total < 0 {
		panic("negative total")
	}
	return applyTax(total)
}

func main() {
	fmt.Println(process(100.0))
}
```

`go build .` succeeds and `go run .` prints `119`, because Go's compiler does
not flag an unused top-level function, only unused imports and unused local
variables are build errors and `go vet .` stays clean on this file too, it
has no unreachable statement to find. Adding a statement after the early
`return` inside `process`, shown below as illustrative text rather than as a
second checked block because its entire purpose is to fail the check it
demonstrates, produces a real diagnostic `go vet` does catch.

```text
func process(total float64) float64 {
	if total < 0 {
		panic("negative total")
	}
	return applyTax(total)
	fmt.Println("unreachable")
}
```

```text
main.go:20:2: unreachable code
```

A second, separate file demonstrates the hard compile error Go does enforce,
an unused import, shown the same illustrative way because a file that fails
to build cannot be a passing checked sample.

```text
package main

import (
	"fmt"
	"strings"
)

func main() {
	fmt.Println("hi")
}
```

```text
./main.go:5:2: "strings" imported and not used
```

`golang.org/x/tools/cmd/deadcode` is the whole-program tool that would catch
`applyLegacyDiscount` in the checked example above, which neither `go build`
nor `go vet` reports, because it is unreachable from `main` through the call
graph even though it compiles and vets cleanly on its own.

### Rust

```rust
struct OrderProcessor {
    tax_rate: f64,
}

impl OrderProcessor {
    fn new() -> Self {
        OrderProcessor { tax_rate: 0.19 }
    }

    fn process(&self, total: f64) -> f64 {
        if total < 0.0 {
            panic!("negative total");
        }
        self.apply_tax(total)
    }

    fn apply_tax(&self, amount: f64) -> f64 {
        amount * (1.0 + self.tax_rate)
    }

    fn apply_legacy_discount(&self, amount: f64) -> f64 {
        amount * 0.95
    }
}

fn main() {
    let p = OrderProcessor::new();
    println!("{}", p.process(100.0));
}
```

Compiled with `rustc --edition 2021 -W dead-code`, printing `119` on run,
with the compiler's `dead_code` lint reporting the unused method by name.

```
warning: method `apply_legacy_discount` is never used
```

### Swift

```swift
struct OrderProcessor {
    let taxRate: Double = 0.19

    func process(_ total: Double) -> Double {
        if total < 0 {
            fatalError("negative total")
        }
        let unusedFlag = true
        return applyTax(total)
    }

    func applyTax(_ amount: Double) -> Double {
        return amount * (1 + taxRate)
    }

    func applyLegacyDiscount(_ amount: Double) -> Double {
        return amount * 0.95
    }
}

let p = OrderProcessor()
print(p.process(100.0))
```

Compiled with `swiftc`, output `119.0`. Swift's compiler warns on the unused
local `unusedFlag` but, unlike Rust and unlike TypeScript's opt-in flag, does
not by default warn on the unused `applyLegacyDiscount` method, an
instructive real difference between the languages' default diagnostic
coverage rather than an assumption.

```
main.swift:8:13: warning: initialization of immutable value 'unusedFlag' was never used; consider replacing with assignment to '_' or removing it [#no-usage]
```

No Java or C# sample is included. `javac` is not installed in the authoring
environment (`java -version` reports no Java runtime located), and Kotlin and
C# are marked as not installed in this repository's toolchain table, so
neither could be compiled or run rather than merely typed and asserted to
work.
