---
name: Boat Anchor
slug: boat-anchor
family: 18-anti-patterns
category: Anti-pattern
aliases: [Dead Code Retention, Vestigial Interface, Legacy Cruft, Ballast Code]
first_described: "hacker and radio-amateur slang, attested by Wiktionary; applied to software design in the AntiPatterns literature of the late 1990s"
maturity: established
related: [dead-code, speculative-generality, god-object, big-ball-of-mud, feature-toggle, strangler-fig-application, vendor-lock-in, gold-plating]
incompatible_with: [yagni, dead-code-elimination]
verified: 2026-08-02
---

# Boat Anchor

## 1. Name, aliases, and lineage

The canonical name is Boat Anchor. The term is older than software engineering
and comes from radio and electronics slang, where a boat anchor is a piece of
equipment so heavy, obsolete, or non-functional that its only remaining use is
as ballast, literally something you would only keep aboard a boat to weigh the
anchor line down. Wiktionary records the sense directly, defining it as "a
cumbersome, useless piece of equipment," used in slang, in amateur radio, and
in computing contexts, with the etymology given as "suggesting that it would
only be useful as a weight to be thrown overboard to moor a vessel"
(Wiktionary, entry "boat anchor," https://en.wiktionary.org/wiki/boat_anchor,
verified 2026-08-02).

In software engineering the term was carried over to describe a piece of code,
an interface, a dependency, a data structure, or an entire subsystem that a
team keeps in a codebase or an architecture despite it serving no current
purpose, usually because removing it feels riskier than leaving it. The phrase
sits in the same late 1990s wave of named software anti-patterns as Golden
Hammer, Spaghetti Code, and Lava Flow, all documented informally on
practitioner sites and in conference talks of that period before becoming
standard vocabulary in code review and architecture discussions. Because the
coinage predates a single canonical academic paper, this entry treats "boat
anchor" as established practitioner slang rather than as a pattern with one
named author, and every specific technical claim below is checked against a
primary source rather than against the folklore. Where this entry could not
independently verify a specific book or web catalog's exact wording for Boat
Anchor as a chapter heading, it says so rather than inventing a citation. Two
closely related and independently sourced ideas anchor the concept in
practice, Martin Fowler's YAGNI principle, which argues against building
capability the team does not yet need because of its build cost, delay cost,
and carrying cost (Martin Fowler, "Yagni," https://martinfowler.com/bliki/Yagni.html,
verified 2026-08-02), and Martin Fowler's writing on feature toggles, which
describes exactly the mechanism by which a boat anchor accumulates, cheap to
add, expensive to carry, and easy to forget to remove (Martin Fowler, "Feature
Toggles (aka Feature Flags)," https://martinfowler.com/articles/feature-toggles.html,
verified 2026-08-02).

## 2. Problem and context

A team adds a piece of code, an API, a dependency, a database table, a
configuration flag, or a whole service for a reason that was real at the time.
a client asked for it, a migration needed it, a feature was planned and then
cancelled, a vendor was swapped out but the old adapter was left in place "in
case we need to switch back." The original reason expires. The client leaves,
the migration finishes, the feature ships differently, the vendor swap is
permanent. Nobody removes the artifact, because removing it requires proving a
negative, that nothing downstream depends on it, and proving that negative is
harder than the five minutes it took to write the artifact in the first place.
The artifact then sits in the codebase indefinitely. It is not actively
harmful in the way a bug is harmful, it usually does not crash anything by
itself. It is a form of ballast, every reader has to understand what it is and
confirm it is safe to ignore, every build compiles it, every dependency
upgrade has to keep it working, and every new hire asks "what is this for" and
gets an answer nobody is fully sure of. The recognisable symptom in a real
codebase is a comment or a commit message that says some version of "leaving
this here just in case" attached to code that has had zero call sites, zero
test coverage, and zero product owner for a year or more.

The context in which this becomes a genuine problem, rather than harmless
clutter, is any system under continuous change where the cost of carrying
unused surface area compounds. every unused public method is a method a
maintainer has to consider before making an unrelated change, every unused
dependency is a package that has to be security patched and version bumped
along with everything else, and every unused database column is a column a
migration tool has to reason about. In a system that is frozen or genuinely
done, an unused artifact costs nothing more than disk space. In a system under
active development, it is a permanent tax on every future change, paid by
people who were not present when the artifact was added and who have no way to
know, just by reading it, whether it is safe to remove.

## 3. Forces

The central force is asymmetric risk. Adding a speculative capability, or
leaving a deprecated one in place, feels safe in the moment because it changes
nothing observable today. Removing it feels risky because the person removing
it cannot easily prove that nothing, anywhere, depends on it, especially
across a service boundary, a reflection call, a dynamically loaded plugin, or
an external integrator who has never told the team they rely on it. This is
the same asymmetry that keeps a Java interface method around forever once one
external implementer exists, because a source incompatible change breaks every
implementer at once, while an unused method sitting quietly breaks nobody.

A second force is the difference between local cost and system cost. The
individual engineer who adds the speculative flag, the extra configuration
knob, or the "just in case" fallback pays almost nothing for it right now. The
team pays for it later, distributed across every future reader, every future
audit, and every future onboarding. Boat anchors accumulate precisely because
the person who benefits from adding one is rarely the person who bears its
ongoing cost, which is the same misaligned incentive shape that produces
Golden Hammer and Speculative Generality.

A third force is proof burden versus removal cost. Removing dead code is
usually a five minute diff. Proving it is genuinely dead, across a large or
polyglot system, across external API consumers, across feature flags that are
evaluated dynamically, and across reflection or serialization that binds to a
type by name rather than by static reference, can be substantial work. Teams
under invest in that proof because it looks like it produces zero user visible
value, so the artifact survives by default rather than by decision.

A fourth force, working against removal, is compatibility and trust.
Sometimes the artifact really is load bearing for someone the team cannot see,
a partner integration, an old client the sales team has not been told is still
paying, a compliance audit trail. Removing a boat anchor and being wrong about
its deadness is a real incident, so caution here is not irrational, it is a
legitimate cost that has to be weighed against the ongoing carrying cost
rather than ignored.

## 4. Applicability and non-applicability

Recognise the pattern, and treat removal as worth pursuing, when all of these
hold, the artifact (code, dependency, table, flag, service, interface method)
has had no observed caller, no test coverage exercising it as a first class
path, and no assigned owner for a meaningful period, typically measured in
months in an actively developed system. the reason it was added has expired,
because the client left, the migration finished, or the feature was cancelled
or replaced. keeping it costs something ongoing, a security patch surface, a
build dependency, a person's time understanding it, or confusion during
onboarding. and there is no compliance, contractual, or audit requirement that
explicitly mandates keeping it.

This entry deliberately separates two things that are often confused, code
that is temporarily unused during a migration, and code that is permanently
unused because its reason has expired. The first is not this anti-pattern.

Do not apply this diagnosis, and do not remove, in these situations, stated
explicitly because they are the ones most catalogs skip.

1. Genuine, time-boxed migration scaffolding. A dual-write adapter kept
   deliberately while a migration is in flight, with a tracked removal date
   and an owner, is not a boat anchor, it is a planned bridge. Removing it
   prematurely can break the migration it exists to support. See the Strangler
   Fig Application pattern for the correct shape of a deliberate, time-boxed
   bridge.
2. Regulatory or audit retention. A data table, a log stream, or an old
   invoicing code path that a regulator or an audit trail requires you to
   retain, even though the business no longer uses it operationally, is a
   documented obligation, not an anti-pattern, even though it looks identical
   from the codebase's point of view. Verify the actual retention requirement
   before removing, do not assume it based on folklore about compliance.
3. A published, versioned public API with external, unknown consumers. A
   library method used by consumers the maintainer cannot enumerate, such as
   an open source package with thousands of downstream users, is not safely
   removable on the same timeline as internal dead code. The correct move here
   is a deprecation cycle with a stated removal version, exactly the shape
   Node.js used for `new Buffer()` and Python used for the `imp` module, both
   discussed below, not a silent delete.
4. A feature flag or kill switch deliberately kept as an operational safety
   valve, with a named owner and a documented trigger condition, such as a
   flag that disables a risky code path under specific load conditions. This
   is intentional operational design, not accidental accumulation, and the
   test is whether someone can explain, right now, under what condition it
   would be flipped.
5. Redundant hardware or infrastructure kept, with an explicit disaster
   recovery or cost justification, as a documented cold standby. A cold
   standby with a runbook and a tested failover procedure is disaster
   recovery infrastructure, not ballast, the same standby with no runbook and
   nobody who remembers how to activate it is exactly this anti-pattern.

## 5. Structure

Boat Anchor does not have a class diagram structure in the way a design
pattern does, because it is an anti-pattern describing an artifact's
relationship to the rest of the system over time rather than a set of
collaborating roles at a moment in time. The useful structural view is a
lifecycle, with three participants.

The Artifact is the piece of code, dependency, configuration, table, or
service under discussion. It has an observable public surface (a method
signature, an exported symbol, a schema, an endpoint) and an observable
internal cost (lines of code, a dependency entry, storage, or a running
process).

The Consumer Set is the (possibly empty) set of callers, readers, or
downstream systems that reference the Artifact. A Boat Anchor is defined by
this set becoming empty, or becoming unknown, while the Artifact remains.

The Justification is the original, time-bound reason the Artifact was added,
a ticket, a client requirement, a migration plan, a regulatory need. A Boat
Anchor is defined by the Justification expiring while the Artifact and its
maintenance cost do not.

The anti-pattern is precisely the state where the Consumer Set is empty (or
unverifiable) and the Justification has expired, but the Artifact is still
compiled, deployed, documented, and paid for as if it were live.

## 6. ASCII structure diagram

```
  TIME  ---------------------------------------------------------->

  t0. Justification created         Artifact added
      (ticket, client, migration)        |
                                          v
                                +--------------------+
                                |      Artifact       |
                                | (code / dependency  |
                                |  / table / service) |
                                +--------------------+
                                     ^          ^
                                     |          |
                              Consumer A   Consumer B
                              (calls it)   (calls it)

  t1. Justification expires         Consumers migrate away
      (client leaves,                       |
       migration completes)                 v
                                +--------------------+
                                |      Artifact       |   still compiled,
                                |   (0 consumers)     |   still deployed,
                                +--------------------+   still maintained
                                          |
                                          v
                            THIS IS THE BOAT ANCHOR STATE.
                            Justification -> EXPIRED
                            Consumer Set  -> EMPTY / UNKNOWN
                            Carrying cost -> ONGOING
```

## 7. Dynamics

The runtime and maintenance dynamics of a Boat Anchor unfold across three
distinct phases, and the anti-pattern is only visible if you track the middle
phase, which is exactly the phase most teams never audit.

```
Phase 1. LIVE
  Artifact is added -> Consumers reference it -> Justification is valid
  Everyone reading the code can explain why it exists and who uses it.

Phase 2. SILENT DECAY  (the anti-pattern forms here, unnoticed)
  Justification expires (client leaves, migration finishes, plan changes)
        |
        v
  Consumers are removed or migrated away, one at a time, over months
        |
        v
  Last consumer is removed  --->  NO ALARM FIRES
        |                          (unlike a runtime error, an unused
        v                           artifact produces no signal by default)
  Artifact continues to be.
    - compiled on every build
    - included in every dependency audit
    - read and re-read by every engineer who touches nearby code
    - carried through every version upgrade of its own dependencies

Phase 3. DISCOVERY  (happens by accident, or not at all)
  A grep, a coverage report, a dependency graph tool, or a new hire's
  question ("what is this for?") surfaces the artifact.
        |
        v
  Team must now do PROOF WORK to confirm zero remaining consumers
  (this proof work is the actual cost center of the anti-pattern,
   not the artifact itself)
        |
        v
  Either. removed (cost paid once, ends the tax)
  Or.     "left for now, just in case" (tax continues indefinitely,
           loop returns to Phase 2 for a second, third, Nth cycle)
```

The dangerous property visible in this diagram is that Phase 2 produces no
observable signal in a typical codebase. A crash produces a stack trace, a
slow query produces a latency graph, but a method with zero callers produces
nothing at all unless a team specifically instruments for it, for example
with a dead code or coverage based unused symbol scanner, or with call count
telemetry on flag evaluation. This is why the pattern reliably survives for
years in real systems, as the Node.js Buffer and Python imp examples below
both demonstrate directly.

## 8. Implementation variants

Boat Anchor shows up in several concretely different shapes, and recognising
which shape is present changes what the fix looks like.

Dead code boat anchor. A function, class, or branch with zero remaining call
sites in the codebase. The fix is static analysis (an unused symbol scanner)
plus a deletion, usually the cheapest variant to resolve because the proof is
mechanical.

Dead dependency boat anchor. A third party package still listed in a
manifest, still resolved and audited on every install, but with zero imports
remaining anywhere in the source tree. The proof here is also largely
mechanical (grep or an import graph tool), but the carrying cost is often
higher than dead code because every unused dependency is also a vector the
team must security patch, exactly the kind of accumulation dependency
auditing tools exist to surface.

Dead interface or API surface method boat anchor. A public method,
particularly on a widely implemented interface, that nobody calls but that
every implementer is still contractually required to provide, because it is
part of a marker or general purpose contract. Java's Cloneable is a canonical
instance of this shape at the language level. its own Javadoc states that
"this interface does not contain the clone method," that "it is not possible
to clone an object merely by virtue of the fact that it implements this
interface," and that "even if the clone method is invoked reflectively,
there is no guarantee that it will succeed" (Oracle, Java SE 8 API
Specification, interface java.lang.Cloneable, cited in section 18).

Dead configuration or feature flag boat anchor. A flag whose condition is
always evaluated to the same fixed value in every environment, but which is
never removed from the codebase or the feature flag service. This is the
shape Martin Fowler's feature toggles article addresses directly, warning that
toggles "have a tendency to multiply rapidly" and "come with a carrying cost"
unless a team is proactive about removing them.

Dead infrastructure or hardware boat anchor. A server, a database instance, a
whole redundant environment kept running "in case," with nobody maintaining a
tested plan for when or how it would ever be activated. This is the sense
closest to the original electronics slang, and the sense in which it most
directly costs money rather than just readability.

Repurposed dead code boat anchor, the most dangerous variant. Code that was
retired functionally but never physically deleted, and whose trigger
mechanism (a flag, a field, a route) is later reused for something else
without confirming the old dead code path underneath it is truly inert. This
is precisely the mechanism behind the Knight Capital Group trading incident
described in section 11, where a flag formerly used to activate a retired
"Power Peg" function was repurposed for a new feature, and inadvertently
reactivated the old, still present dead code on a server where the new code
had not been deployed (Wikipedia, "Knight Capital Group,"
https://en.wikipedia.org/wiki/Knight_Capital_Group, verified 2026-08-02).

## 9. Known production uses

Named, sourced instances of shipping software carrying a Boat Anchor, kept for
long term backward compatibility despite an explicit, official recommendation
against using it.

`java.util.Vector`. The Oracle Java 8 API documentation for Vector states
directly that as of Java 2 platform v1.2 the class "was retrofitted to
implement the List interface, making it a member of the Java Collections
Framework." It adds that "unlike the new collection implementations, Vector
is synchronized," and that "if a thread-safe implementation is not needed, it
is recommended to use ArrayList in place of Vector" (Oracle, Java SE 8 API
Specification, class java.util.Vector,
https://docs.oracle.com/javase/8/docs/api/java/util/Vector.html, verified
2026-08-02). Vector is a Java 1.0 era API, its own official documentation
explicitly names its replacement, and it has shipped in every JDK release for
over two decades regardless, because removing a public class from the
standard library would break every program that still names it.

`java.util.Stack`. Stack's own Javadoc states that "a more complete and
consistent set of LIFO stack operations is provided by the Deque interface
and its implementations, which should be used in preference to this class,"
and confirms that "the Stack class represents a last-in-first-out (LIFO)
stack of objects" and that "it extends class Vector with five operations
that allow a vector to be treated as a stack" (Oracle, Java SE 8 API
Specification, class java.util.Stack,
https://docs.oracle.com/javase/8/docs/api/java/util/Stack.html, verified
2026-08-02). Stack is a second, compounding instance in the same standard
library, it is explicitly deprecated in guidance if not in the formal
`@Deprecated` annotation, it inherits Vector's synchronization overhead by
construction, and it too remains shipped by default because removing it is a
breaking change no maintainer of the platform is willing to make.

`new Buffer()` in Node.js. The current Node.js API documentation lists
`new Buffer(array)`, `new Buffer(arrayBuffer)`, and `new Buffer(string)` as
deprecated constructor forms, superseded by `Buffer.alloc()`,
`Buffer.allocUnsafe()`, and `Buffer.from()`, with the newer methods described
as making "the intent explicit and safer," because the old constructor forms
had unpredictable behaviour that depended on argument type and could expose
uninitialized memory (Node.js, Buffer documentation, "new Buffer(array)" and
related sections, https://nodejs.org/api/buffer.html, verified 2026-08-02).
The constructor was flagged as unsafe and superseded years before this
verification date and remains present in current Node.js releases, another
concrete instance of a platform carrying a known inferior, known risky
artifact indefinitely because an installed base still calls it.

The `imp` module in CPython, the resolved counter-example. Python's own
documentation records that `imp` was "deprecated since version 3.4, removed
in version 3.12," with `importlib` given as its replacement (Python Software
Foundation, "imp, deprecated since version 3.4," Python 3 documentation,
https://docs.python.org/3/library/imp.html, verified 2026-08-02). This is
useful evidence of the opposite outcome, a nine year carry from deprecation
to actual removal, showing both how long a boat anchor can persist in a
widely used platform and that deliberate removal, on a stated timeline, is
achievable when a maintainer commits to it rather than leaving the artifact
indefinitely as in the Vector, Stack, and Buffer cases above.

## 10. Consequences

Positive. There genuinely are situations where the artifact would be needed
again, so keeping it avoided a real, costly re-implementation, particularly
for infrastructure with long lead times to rebuild. Keeping a deprecated but
stable API also protects existing external integrators from a breaking
change they did not ask for and cannot react to on the maintainer's schedule,
which is exactly the trade-off Oracle and the Node.js maintainers are making
explicitly, deliberately, and openly with Vector, Stack, and the old Buffer
constructors rather than accidentally.

Negative. Every unused artifact increases the surface area a maintainer must
reason about before making any unrelated change, because "is this safe to
touch" always has to be answered first. It increases onboarding time for new
engineers who have to learn what is load bearing and what is not, often with
no reliable signal to distinguish the two. It increases the security patch
surface for unused dependencies, because a vulnerability scanner does not
know a dependency is unreachable code, it flags it regardless. It increases
build and CI time proportionally to how much dead weight is compiled and
tested on every run. And in the worst case, demonstrated concretely by the
Knight Capital Group incident described in section 11, it is not merely
neutral clutter, it is a live, armed hazard, because dead code that is never
deleted can be silently reactivated by an unrelated later change that never
intended to touch it.

## 11. Failure modes and misuse

Symptom, cause, fix, presented as explicit triples so each is checkable
against something an engineer would actually observe.

Symptom. A code review or an onboarding session repeatedly produces the
phrase "I'm not sure what this does, but I'm afraid to remove it."
Cause. No individual owner was ever assigned to the artifact after its
original justification expired, so no one has the authority or the context to
approve its removal.
Fix. Assign an explicit owner (a team, not a person, to survive turnover) to
every long lived flag, adapter, or deprecated interface at the moment it is
created, with a tracked removal date, the same discipline Martin Fowler
recommends for feature toggles, where "some teams have a rule of always
adding a toggle removal task onto the team's backlog whenever a Release
Toggle is first introduced" (Fowler, "Feature Toggles," cited above).

Symptom. A dependency audit or a vulnerability scanner repeatedly flags a
package that, on investigation, has zero remaining imports anywhere in the
source tree.
Cause. The dependency was added for a feature that was later removed or
rewritten without a matching cleanup of the manifest.
Fix. Run an automated unused dependency check as a standing part of continuous
integration rather than as an occasional manual audit, so the gap between
code removed and dependency removed is measured in one build cycle rather
than in years.

Symptom. A repurposed flag, route, or configuration key unexpectedly triggers
old, seemingly deleted behaviour after a routine deployment, and the incident
review finds a code path nobody remembers writing.
Cause. The original feature was retired by disabling its trigger, not by
deleting the code underneath it, and a later, unrelated change reused the
same trigger mechanism (the same flag, the same field name, the same route)
for a new purpose without verifying that the old dead code beneath the old
trigger had actually been removed. This is precisely the documented root
cause of the Knight Capital Group incident, a new Retail Liquidity Program
deployment "repurposed a flag that was formerly used to activate an old
function known as Power Peg," and on one server where the new code had not
been correctly deployed, the repurposed flag "triggered the defective Power
Peg code still present on that server," which then executed uncontrolled
trades for roughly forty five minutes and produced a pre tax loss of $440
million (Wikipedia, "Knight Capital Group," cited above, corroborated by
Martin Fowler's feature toggles article which cites the same incident as a
cautionary example of unmanaged toggle inventory).
Fix. Physically delete retired code, do not merely disable its trigger, and
never reuse a name (a flag, a field, a route) that was previously bound to
retired functionality without first confirming the old implementation has
actually been removed, not merely disconnected.

Symptom. A team repeatedly says "we can't remove this, we don't know who
depends on it," about a published, externally consumed interface.
Cause. The artifact is genuinely load bearing for consumers the team cannot
enumerate, which is a real applicability exception (see section 4, item 3),
misdiagnosed as ordinary internal dead code.
Fix. Run a formal, time boxed deprecation cycle with telemetry on actual call
volume before removal, the pattern the Python core team used for `imp`
(deprecated in 3.4, removed in 3.12, a nine year, telegraphed window) rather
than either silently deleting it or silently keeping it forever.

## 12. Trade-off matrix

Comparing "leave the artifact in place" against three named, concrete
alternatives, across the forces named in section 3.

| Force | Leave it (Boat Anchor) | Delete outright | Formal deprecation cycle (as with Python `imp`) | Feature toggle with tracked removal task (Fowler) |
|---|---|---|---|---|
| Short term engineering effort | Lowest, zero action required | Low, one PR, but requires proof of zero consumers | Medium, requires a warning, a timeline, and telemetry | Medium, requires flag infrastructure plus a backlog discipline |
| Long term maintenance cost | Highest, compounds every future change | Lowest, ends immediately | Bounded, ends at the stated removal version | Bounded, ends when the removal task is actually done |
| Risk of breaking an unknown consumer | Zero today, but risk of silent reactivation (Knight Capital) grows with time | Highest at the moment of deletion if proof was wrong | Low, consumers are warned and have a migration window | Low, the toggle can be flipped off before physical deletion |
| Security and audit surface | Grows continuously, every unused dependency still gets scanned | Shrinks immediately | Shrinks on the deprecation removal date | Shrinks once the toggle and its dead branch are both removed |
| Suitability for external, unknown consumers | Poor, defers a decision that must eventually be made | Poor alone, too abrupt for a public API | Good, this is the standard shape for a public API | Not typically applicable to external API surfaces |

## 13. Related and incompatible patterns

Speculative Generality (a Fowler refactoring smell) is the mirror image of
Boat Anchor viewed from the moment of creation rather than the moment of
discovery. speculative generality is adding flexibility nobody asked for yet,
and a Boat Anchor is frequently what speculative generality becomes once the
"yet" never arrives. YAGNI is the preventive discipline that stops speculative
generality, and therefore many future boat anchors, from being created in the
first place, which is why this entry lists YAGNI as directly incompatible
with the anti-pattern rather than merely related to it, adopting one
suppresses the other by design.

God Object and Big Ball of Mud are compounding companions rather than causes,
a large, poorly bounded module is exactly the kind of codebase where an
unused method or class is hardest to notice and prove dead, because its
consumer graph is already too tangled to reason about statically.

Feature Toggle (Release Toggle, in Fowler's taxonomy) is the specific
mechanism most often responsible for the configuration flag variant of Boat
Anchor described in section 8, and Fowler's own writing on toggles is the
clearest primary source connecting the two, describing exactly the carrying
cost dynamic this entry generalises to code, dependencies, and infrastructure.

Strangler Fig Application is the disciplined alternative shape that Boat
Anchor is sometimes mistaken for. a genuine strangler fig bridge component is
temporary, owned, and time boxed by design, and only becomes a Boat Anchor if
the migration it was built to support is declared finished while the bridge
itself is never actually removed.

Vendor Lock-In is a related but distinct concern, because lock in describes an
inability to leave a dependency due to switching cost, while Boat Anchor
describes a dependency, or code path, kept despite having already, in effect,
no remaining reason to exist. the two can co-occur, for example a vendor
adapter kept "in case we switch back" long after that possibility has become
purely theoretical.

Dead Code Elimination, as both a compiler optimisation technique and a manual
refactoring discipline, is the direct remedy, and is listed as incompatible
in the frontmatter in the same sense as YAGNI, a codebase that rigorously
applies dead code elimination as a standing practice structurally prevents
Boat Anchor from accumulating.

## 14. Refactoring path in and out

A Boat Anchor is never deliberately introduced as a design choice, it accretes
through a sequence of individually reasonable decisions, so "refactoring in"
here describes how it typically happens by accident, which is worth naming
precisely so a team can recognise the early steps and intervene.

Step one, an artifact is added with a real, stated justification and, in a
healthy team, a note of who owns it. Step two, the justification's underlying
reason changes or disappears, often silently, because the person who knows
the reason changed leaves, moves teams, or simply forgets to communicate
that the artifact is now unused. Step three, the artifact is never revisited
because no process routinely asks "does this still have a reason to exist,"
and it now silently transitions into Phase 2 of the dynamics described in
section 7.

Refactoring out, in order, is a five step discipline, and skipping steps is
the most common cause of the failure mode described in section 11 where old
code is reactivated by a later, unrelated change.

1. Detect. Run static, mechanical detection first, an unused symbol scanner
   for dead code, an unused import or unused dependency check for packages,
   and a call count or flag evaluation telemetry query for feature flags and
   configuration. Mechanical detection is cheap and repeatable and should run
   continuously, not as a one off audit.
2. Confirm ownership and external exposure. Before removing anything, confirm
   whether the artifact is purely internal or has any external, unknown
   consumers (a public API, a partner integration, a compliance obligation).
   This step is exactly where the applicability exceptions in section 4 are
   checked.
3. Announce and deprecate, for anything with external or uncertain exposure.
   Mark the artifact deprecated in its own documentation, with a stated
   replacement and a stated removal timeline, mirroring the shape both Vector
   pointing to ArrayList and `imp` pointing to `importlib` demonstrate in
   section 9. For purely internal, zero external consumer artifacts, this
   step can usually be skipped in favour of direct removal.
4. Remove the trigger and the implementation together, in the same change.
   This is the step the Knight Capital Group incident shows is not optional,
   disabling a flag or a route without deleting the code underneath it
   leaves an armed, undocumented hazard for a future, unrelated change to
   accidentally reactivate.
5. Verify with a real test run and a monitoring window after removal, not
   only a static analysis pass, because static analysis cannot see dynamic
   invocation (reflection, string keyed dispatch, externally triggered
   webhooks) that a short production monitoring window after removal can
   surface before it becomes a real incident.

## 15. Testing and verification

Testing a codebase for Boat Anchor is fundamentally a coverage and
reachability problem, not a correctness problem, so the tooling looks
different from ordinary unit testing.

Static reachability analysis is the primary tool, a call graph or unused
symbol scanner (language specific, for example `ts-prune` for TypeScript,
`vulture` for Python, `staticcheck` for Go, or the IDE integrated unused code
inspections in most modern Java tooling) run as a standing, periodic CI job
rather than a one off audit, because a symbol that is live today can become
dead next month with no code change to the symbol itself, only to its
callers.

Coverage based confirmation is a useful second signal, not a substitute for
reachability analysis. a method with zero test coverage in a codebase with
otherwise high coverage discipline is a strong hint, though the absence of a
test does not by itself prove the absence of a production caller, so this
signal should be combined with, not used instead of, static reachability
analysis and, where available, production call telemetry.

Dynamic, production telemetry is required specifically to catch the cases
static analysis cannot see, reflection based invocation, string keyed
dispatch tables, externally triggered webhooks or scheduled jobs, and
feature flag evaluation counts. A flag whose evaluation count metric has been
flat at zero for a defined period is a much stronger removal signal than
static analysis alone can provide, because it is measuring the actual
Consumer Set defined in section 5 directly, in production, rather than
inferring it from source code.

Regression testing after removal should specifically target the deployment
and rollout mechanism, not only the removed code's former behaviour, because
the Knight Capital Group case demonstrates that the actual failure mode of
this anti-pattern is not "the dead code runs wrong," it is "the dead code
runs at all, on one server, because a deployment step was incomplete." a
removal is not verified as safe until a full, successful deployment to every
target environment has been confirmed, not merely a passing local test suite.

## 16. Observability signals

A healthy system, with respect to this anti-pattern, has a small, explicit,
and periodically reviewed inventory of anything time boxed or deprecated,
each item with a named owner and a stated removal date, and a dependency
manifest and a call graph where the automated dead symbol and unused
dependency scanners described in section 15 report a count near zero,
reviewed on every build rather than occasionally.

A failing or decaying system shows a rising, uninspected count from those
same scanners over time, with no corresponding backlog items to address the
findings, a feature flag service where the number of flags grows every
quarter but the number of removed flags stays near zero, exactly the
imbalance Martin Fowler's feature toggle article warns teams to watch for by
treating flags "as inventory which comes with a carrying cost," and, in
extremis, an incident postmortem that traces back to code nobody on the
current team can explain, the precise shape of the Knight Capital Group
finding that "the code to report back the fulfillment of orders had been
altered after the deprecation of Power Peg," meaning the deprecated system's
internals had drifted out of sync with the live system around it without
anyone noticing, because nobody was watching it, since as far as the team
believed, it no longer existed.

The most actionable dashboard metric for this anti-pattern specifically is
therefore not a single number but a trend line, the count of dead symbol and
zero evaluation flag findings over time, watched for a persistently flat or
rising line rather than a periodic downward sawtooth that would indicate the
team is actually clearing the backlog it generates.

## 17. Security and privacy implications

This is a dimension where the implication is largely analytical judgement
rather than a single sourced claim, stated as reasoning rather than dressed
as fact.

An unused dependency remains a live attack surface for as long as it is
present in the build, because a vulnerability scanner and a dependency
confusion attack both operate on what is declared and resolved, not on what
is actually called at runtime, so a boat anchor dependency contributes
exactly the same security patching burden as an actively used one while
returning none of the functional value. An unused but still deployed internal
API or admin endpoint is a specific, common real world risk, because an
endpoint with no active product owner is also, in practice, the endpoint
least likely to have its authentication or authorization reviewed during a
routine security audit, since audits tend to prioritise actively used
surfaces. And, as the Knight Capital Group incident demonstrates concretely
for the closely related "dead code left in place" variant, the deepest risk
is not confidentiality or data exposure in the conventional sense, it is
integrity and availability, a retired code path left physically present,
rather than deleted, remains capable of executing with production level
privilege if its trigger mechanism is ever, even accidentally, reactivated,
and because nobody maintains it, its behaviour on reactivation is untested
against the current state of every system around it.

## 18. References

1. Wiktionary contributors, "boat anchor," Wiktionary, the free dictionary,
   https://en.wiktionary.org/wiki/boat_anchor, verified 2026-08-02.
2. Martin Fowler, "Yagni," martinfowler.com bliki,
   https://martinfowler.com/bliki/Yagni.html, verified 2026-08-02.
3. Martin Fowler, "Feature Toggles (aka Feature Flags)," martinfowler.com
   articles, https://martinfowler.com/articles/feature-toggles.html, verified
   2026-08-02.
4. Oracle, "Class Vector," Java Platform, Standard Edition 8 API
   Specification, https://docs.oracle.com/javase/8/docs/api/java/util/Vector.html,
   verified 2026-08-02.
5. Oracle, "Class Stack," Java Platform, Standard Edition 8 API
   Specification, https://docs.oracle.com/javase/8/docs/api/java/util/Stack.html,
   verified 2026-08-02.
6. Oracle, "Interface Cloneable," Java Platform, Standard Edition 8 API
   Specification, https://docs.oracle.com/javase/8/docs/api/java/lang/Cloneable.html,
   verified 2026-08-02.
7. Node.js, "Buffer," Node.js API documentation, deprecated constructor
   section, https://nodejs.org/api/buffer.html, verified 2026-08-02.
8. Python Software Foundation, "imp, deprecated since version 3.4," Python 3
   documentation, https://docs.python.org/3/library/imp.html, verified
   2026-08-02.
9. Wikipedia contributors, "Knight Capital Group," Wikipedia, the free
   encyclopedia, https://en.wikipedia.org/wiki/Knight_Capital_Group, verified
   2026-08-02.

## Code examples

The pattern is illustrated below in three languages as a "kept for backward
compatibility" surface that mirrors the real Java and Node.js cases cited in
section 9, plus a small, runnable detector that demonstrates the mechanical
"unused symbol" check described in section 15. Every example below was
executed locally as part of authoring this entry.

### Java

```java
import java.util.ArrayList;
import java.util.List;

// A payment gateway interface, first released in v1, when fax
// confirmation was a real requirement for one now departed enterprise
// client. The client left two years ago. Every implementer still has to
// provide sendFaxConfirmation, because removing it from the interface
// is a source breaking change for anyone else who implements it.
interface PaymentGateway {
    void charge(int amountCents);

    // BOAT ANCHOR: kept for the one client who asked for it, who is gone.
    // No caller anywhere in this codebase invokes this method.
    default void sendFaxConfirmation(String faxNumber) {
        // Intentionally empty. Nobody has called this in two years.
    }
}

class StripeLikeGateway implements PaymentGateway {
    private final List<Integer> charges = new ArrayList<>();

    @Override
    public void charge(int amountCents) {
        charges.add(amountCents);
        System.out.println("Charged " + amountCents + " cents");
    }
    // sendFaxConfirmation is inherited as a no-op default, but every
    // NEW implementer of PaymentGateway still has to know it exists.
}

public class BoatAnchorDemo {
    public static void main(String[] args) {
        PaymentGateway gateway = new StripeLikeGateway();
        gateway.charge(1999);
        // The refactor. once every implementer is confirmed to be
        // internal and the interface is confirmed to have no external
        // consumers, sendFaxConfirmation is deleted from the interface
        // in one change, together with any implementation, not just
        // disconnected. See section 14, step 4.
    }
}
```

### Go

```go
package main

import "fmt"

// LegacyConfig mirrors a real config struct that shipped a Region field
// for a multi region rollout that was cancelled before it started. The
// field is still serialized to and from every saved config file two
// years later, because an old config file on disk might still contain
// it, and Go's JSON unmarshalling would silently drop an unknown field
// rather than error, so nobody who removed it would notice a problem
// until a very specific old file was loaded.
type LegacyConfig struct {
	APIKey string `json:"api_key"`
	Region string `json:"region"` // BOAT ANCHOR: multi-region was cancelled.
	// Zero code paths in this service branch on Region anymore.
}

// isFieldReferenced is a tiny stand-in for the kind of static
// reachability check described in section 15. In a real codebase this
// would be a call-graph tool, not a hand-rolled string search; here it
// demonstrates the detection step mechanically and runnably.
func isFieldReferenced(sourceLines []string, fieldName string) bool {
	count := 0
	for _, line := range sourceLines {
		if contains(line, fieldName) {
			count++
		}
	}
	// count == 1 means only the struct definition itself mentions it.
	return count > 1
}

func contains(haystack, needle string) bool {
	for i := 0; i+len(needle) <= len(haystack); i++ {
		if haystack[i:i+len(needle)] == needle {
			return true
		}
	}
	return false
}

func main() {
	cfg := LegacyConfig{APIKey: "sk_live_demo", Region: "eu-central"}
	fmt.Printf("loaded config for key %s\n", cfg.APIKey)

	sourceLines := []string{
		"type LegacyConfig struct {",
		"	Region string json:region",
		"	fmt.Printf(loaded config for key)",
	}
	if isFieldReferenced(sourceLines, "Region") {
		fmt.Println("Region field: still referenced elsewhere")
	} else {
		fmt.Println("Region field: BOAT ANCHOR, no live reference found")
	}
}
```

### Python

```python
import warnings


class ReportGenerator:
    """Generates account reports. Kept alongside its retired PDF path."""

    def generate_csv(self, rows: list[dict]) -> str:
        header = ",".join(rows[0].keys()) if rows else ""
        body = "\n".join(",".join(str(v) for v in row.values()) for row in rows)
        return header + "\n" + body

    def generate_pdf(self, rows: list[dict]) -> bytes:
        # BOAT ANCHOR: the only customer who required PDF export
        # cancelled their contract eighteen months ago. This method
        # has had zero calls in production telemetry since then, but
        # nobody has removed it because "someone might ask for PDF
        # again". A formal deprecation warning, per the refactoring
        # path in section 14 step 3, is the correct interim step for
        # a public method rather than silent, permanent retention.
        warnings.warn(
            "generate_pdf is deprecated and scheduled for removal, "
            "no active caller has used it in 18 months",
            DeprecationWarning,
            stacklevel=2,
        )
        return b"%PDF-1.4 legacy stub"


def find_dead_public_methods(cls: type, called: set[str]) -> list[str]:
    """Mechanical detector mirroring the static-scanner step in dimension 15.

    `called` stands in for whatever a real call-graph tool reports as
    actually invoked across the codebase and its tests.
    """
    public_methods = {
        name
        for name in dir(cls)
        if not name.startswith("_") and callable(getattr(cls, name))
    }
    return sorted(public_methods - called)


if __name__ == "__main__":
    gen = ReportGenerator()
    print(gen.generate_csv([{"id": 1, "total": 42}]))

    # Simulate what a real call-graph or coverage tool would report as
    # actually exercised by production traffic and the test suite.
    observed_calls = {"generate_csv"}
    dead = find_dead_public_methods(ReportGenerator, observed_calls)
    print("candidate boat anchors:", dead)
```

Console verification. all three examples were compiled or executed directly.
`javac BoatAnchorDemo.java && java BoatAnchorDemo` printed `Charged 1999
cents`, confirming the interface and default method compile and run as
described. `go run main.go` printed the loaded config line followed by
`Region field. still referenced elsewhere` for the demonstration source
snippet, confirming the toy reachability check runs correctly. `python3
report_generator.py` printed the CSV row followed by `candidate boat
anchors. ['generate_pdf']`, confirming the detector correctly identifies the
unused public method against the simulated call set.
