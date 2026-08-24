---
name: Protected Variations
slug: protected-variations
family: 04-principles-and-laws
category: Principle
aliases: [PV, Open-Closed Principle, Information Hiding at Variation Points]
first_described: "Cockburn 1996, named and generalized by Larman 2001"
maturity: canonical
related: [strategy, factory-method, template-method, bridge, dependency-inversion-principle, open-closed-principle, information-hiding]
incompatible_with: []
verified: 2026-08-02
---

# Protected Variations

## 1. Name, aliases, and lineage

The canonical name in the object-oriented design literature is Protected
Variations, abbreviated PV. It is one of the nine patterns in Craig Larman's
GRASP catalog, General Responsibility Assignment Software Patterns, which
Larman published in *Applying UML and Patterns. An Introduction to
Object-Oriented Analysis and Design*, first edition, Prentice Hall, 1997,
and has kept in every later edition of that book.

The underlying idea predates the name. Alistair Cockburn described the same
principle without calling it Protected Variations in "Prioritizing Forces in
Software Design", published in *Pattern Languages of Program Design*, volume
2, Addison-Wesley, 1996. Cockburn did not yet know of the Open-Closed
Principle when he wrote it, a fact Larman states directly. Larman is the one
who coined the short label "protected variations" for general use and set out
its relationship to the older ideas, in "Protected Variation. The Importance
of Being Closed", *IEEE Software*, volume 18, number 3, May/June 2001, pages
89 to 91 (https://martinfowler.com/ieeeSoftware/protectedVariation.pdf,
verified 2026-08-02, hosted by Martin Fowler, who edited the Design column of
that issue).

Three older statements of essentially the same idea are treated in the
literature as expressions of one principle, not as three separate rules.

- **The Open-Closed Principle (OCP).** Bertrand Meyer, *Object-Oriented
  Software Construction*, IEEE Press, 1988. Meyer's statement, quoted in
  Larman's 2001 article, is that modules should be both open, for extension
  and adaptation, and closed, to avoid a modification that affects clients.
- **Information hiding.** David Parnas, "On the Criteria to Be Used in
  Decomposing Systems into Modules", *Communications of the ACM*, volume 15,
  number 12, December 1972. Parnas's own words, quoted in Larman's article,
  are that a designer begins with a list of difficult design decisions or
  decisions likely to change, and each module is then designed to hide such a
  decision from the others. Larman argues in the 2001 article that this is
  widely misread as a synonym for data encapsulation, when Parnas meant the
  hiding of a design DECISION, of which data encapsulation is one technique
  among several.
- **Protected Variations, Cockburn 1996 and Larman 2001.** Identify points of
  predicted variation or instability, and put a stable interface around them
  so the instability does not propagate to the rest of the system.

Larman's own framing in the 2001 article is precise on this point. OCP and PV
"formalize and generalize a common and fundamental design principle described
in many guises", and are "two expressions of the same principle, protection
against change to the existing code and design at variation and evolution
points, with minor differences in emphasis." The GRASP catalog entry in the
second and third editions of *Applying UML and Patterns* folds an earlier,
separately named GRASP pattern, Don't Talk to Strangers, the design guideline
usually associated with the Law of Demeter, into the discussion of Protected
Variations as one of its supporting techniques, because limiting an object's
acquaintance to its immediate collaborators is itself a way of not depending
on the internal shape of something that might change.

Protected Variations is therefore best understood as the ROOT PRINCIPLE, and
the Open-Closed Principle, information hiding, the Dependency Inversion
Principle, and a large share of the Gang of Four structural and behavioral
patterns are the mechanisms that carry it out in specific shapes. This entry
treats Protected Variations at the level of the principle itself, and treats
Factory Method, Strategy, Bridge, and the rest as instances rather than
synonyms.

## 2. Problem and context

A system is never finished changing. Requirements shift, a vendor is
replaced, a data format gains a field, a regulator adds a rule, a second
platform needs support, a team splits ownership of a module. The question
Protected Variations answers is not whether change will happen, but where a
given change will STOP once it starts.

Without any deliberate design effort, a change to one part of a system tends
to ripple outward through every place that concretely depends on the changed
part. A field renamed in a database table breaks every query that names it
literally. A vendor SDK swapped for a competitor's breaks every call site
that imported the vendor's types directly. A new tax rule for one country
forces a new branch into a function that was never meant to know about
countries at all. Each of these is a change whose blast radius was never
decided on purpose. It was decided by accident, by however the code happened
to be written the first time.

The context in which Protected Variations becomes the relevant question is
any point in a design where a decision is either already known to be
unstable, or is judged likely enough to become unstable that the cost of
guarding it now is worth paying. That judgment is the hard part, and
dimension 4 below and dimension 11's failure modes both return to it,
because guarding a point that never changes is its own failure mode, not a
safe default.

Parnas's 1972 paper frames this in terms of information the reader of one
module should not need to know about another module. Larman's 2001 framing
adds that the "interface" a stable point exposes need not be a formal
language construct such as a Java or C# `interface`. It can be a data
format, a wire protocol, a plugin contract, a naming service, or a rule
language, anything that draws a line a client depends on while the thing
behind the line is free to change.

## 3. Forces

- **Change containment versus indirection cost.** Favoured is that a change
  behind the stable point never reaches the client. Sacrificed is that every
  client call now passes through one more layer, one more virtual dispatch, or
  one more lookup, which a reader must trace through to see the real behavior.
- **Speed of the first version versus speed of the tenth change.** Sacrificed
  early. A protected point costs more to design and build the first time than
  a direct dependency would. Favoured later, because the tenth change to that
  point costs a fraction of what it would have cost against a direct
  dependency, and often costs zero for the client at all.
- **Cognitive load.** Sacrificed. An abstraction the reader must learn adds a
  name, a contract, and a place to look, on top of the concrete thing it
  hides. Larman's 2001 article is explicit that PV is not free and that a
  designer "must pick your battles", applying protection only where the
  variation is judged real.
- **Coupling.** Favoured, and this is the central trade the whole principle
  exists to make. The client couples to a stable abstraction instead of to a
  volatile concretion, which is the Dependency Inversion Principle stated in
  coupling terms.
- **Team topology.** Favoured when the stable point sits at a genuine
  ownership boundary, for example between a platform team and product teams,
  or between an internal system and an external vendor. The interface becomes
  a contract two teams can develop against independently. Sacrificed when no
  such boundary exists, because the abstraction then serves nobody and only
  adds a layer between two parties who could simply talk to each other.
- **Correctness risk at the boundary itself.** A protected point is a place
  where two independently evolving things must still agree on a contract.
  Version skew, a client built against an old contract talking to a
  provider built against a new one, is a risk this principle introduces at
  exactly the point it was meant to reduce risk elsewhere. See dimension 11.
- **Latency and resource cost.** Close to neutral for pure indirection
  through a virtual call or an interface dispatch in a managed runtime.
  Meaningfully non-neutral for the heavier mechanisms, a network-facing
  service lookup, a rule engine, or an interpreter, each of which is itself
  named in Larman's 2001 article as a way of achieving PV and each of which
  carries its own real runtime cost that the article does not pretend away.

## 4. Applicability and non-applicability

Apply Protected Variations at a point where at least one of the following
holds, following Larman's own advice to identify points of PREDICTED
variation rather than to protect everything on principle.

- The decision is already known to have varied before, a second database
  vendor, a second payment provider, a second export format, and the team
  expects a third.
- The decision is owned by a different team, a different company, or a
  different release cycle than the code that consumes it, so the two sides
  cannot be changed in lockstep even if nothing about the underlying business
  logic changes.
- The decision encodes something a regulator, a market, or a partner
  organization controls externally, a tax rule, a currency, a compliance
  requirement, and history shows those rules change on a schedule the
  engineering team does not control.
- Two or more concrete implementations of the same decision are already known
  to be needed at once, not merely hypothesized, for example because two
  customer segments both need to be served today.
- The cost of guessing wrong and reworking the concrete dependency later is
  measured to be materially higher than the cost of adding one seam now, for
  instance because the concrete dependency is deeply embedded in generated
  code, a public API, or a database schema that is expensive to migrate.

Do NOT apply Protected Variations in these cases, and the reason in each case
is the same reason Larman gives directly in the 2001 article, that PV for
speculative future proofing carries a real and often larger cost than the
brittleness it is meant to avoid.

- **There is exactly one implementation and no credible second one planned.**
  This is the case Larman calls out by name with the Java `Color.red`
  example, a static final field whose likelihood of instability is so low
  that hiding it behind an accessor is what he calls "object purism". A
  speculative interface built for a variation that never arrives is YAGNI
  cost with no offsetting benefit. Cross reference the anti-pattern family
  entry on speculative generality.
- **The variation is imagined, not observed.** A design built to anticipate
  "maybe someday we will support a second cloud provider" when no second
  provider has ever been discussed by the business is the case Larman's
  pager-message anecdote in the 2001 article describes directly, a scripting
  interpreter added for flexibility that was later removed during rework
  because it was never needed.
- **The point of variation is chosen wrong.** Protecting the wrong seam, for
  example hiding the storage engine behind an interface while leaving the
  query language it exposes tightly coupled to every caller, gives the
  appearance of protection while the actual instability, the query language,
  ripples through the system unguarded. Larman's advice to "pick your
  battles" implies the corollary that picking the wrong battle wastes the
  same effort as fighting no battle at all.
- **The abstraction cannot actually be kept stable.** If the very shape of
  the interface is expected to change as often as the implementations behind
  it, the seam has not protected anything, it has merely moved the churn one
  level up and added a translation cost on top.
- **A simpler, already-adopted convention already achieves the protection.**
  If a team has standardized on dependency injection everywhere, adding a
  second, bespoke abstraction mechanism around one specific decision adds a
  second convention for readers to learn rather than reusing the one they
  already know.
- **The system is small, short-lived, or has one operator who is also the
  only future maintainer.** A one-off script or a prototype meant to be
  thrown away after a demonstration pays the coupling cost happily in
  exchange for skipping the indirection cost entirely, because there will be
  no tenth change to amortize the investment against.

## 5. Structure

Protected Variations is a principle rather than a fixed class diagram, so its
"participants" are roles a design plays rather than named classes with a
single canonical shape. Four roles recur across every mechanism the
principle motivates.

- **Client.** The code that needs a capability and must keep working when the
  concrete provider of that capability changes. The client's defining
  property is that it depends only on the next role, never on any concrete
  implementation directly.
- **Stable Point (the "interface" in Larman's broad sense).** The seam a
  client is written against. This can be a formal language interface, an
  abstract class, a data format, a wire protocol, a plugin contract, a
  configuration schema, or a naming or lookup service. Larman is explicit
  that PV's use of the word interface is broader than a Java or COM interface
  construct, and the concrete mechanism chosen for the Stable Point is what
  dimension 8 catalogs.
- **Variant.** A concrete realization of the capability the Stable Point
  describes. Multiple Variants can coexist, and a Variant can be added,
  removed, or replaced without touching the Client, provided it honors the
  Stable Point's contract.
- **Binder (sometimes present, sometimes implicit).** The mechanism that
  connects a particular Client to a particular Variant at a particular time.
  In the simplest case the Binder is a constructor call or a dependency
  injection container's wiring. In the heavier mechanisms it is a naming
  service, a plugin loader reading a configuration file, or a rules engine
  reading external rules, all of which Larman names explicitly as data-driven
  and service-lookup expressions of PV in the 2001 article.

What varies in shape between mechanisms is only how the Stable Point is
expressed and how the Binder connects Client to Variant. The relationship the
diagram must show, in every mechanism, is that the Client's dependency arrow
terminates at the Stable Point and never at a Variant.

## 6. ASCII structure diagram

```
Before protection (unprotected variation point)

+--------+
| Client |
+--------+
           | direct dependency
           v
+-----------------+
| ConcreteVendorX |
+-----------------+

A change inside ConcreteVendorX's contract reaches
Client directly. Replacing the vendor means editing
Client.


After protection (Protected Variations applied)

+--------+
| Client |
+--------+
           | depends on
           v
+----------------------+
| Stable Point         |
| (interface, format,  |
| protocol, or lookup) |
| operation()          |
+----------------------+
           ^
           | implemented by
     +-----+-----+
     |           |
+--------------------+ +--------------------+
| ConcreteVendorX    | | ConcreteVendorY    |
| operation()        | | operation()        |
+--------------------+ +--------------------+

Client's only dependency arrow terminates at Stable
Point. A Binder (a constructor call, DI container, or
lookup service, not drawn) decides which Variant
answers a given call at runtime. Adding
ConcreteVendorZ later touches neither Client nor
Stable Point.
```

## 7. Dynamics

The behavior worth showing is not one method call, it is what happens on
two separate timelines, the ordinary runtime call, and the change event that
the whole principle exists to contain.

```
Runtime call, ordinary operation

  Client            Stable Point           Variant (current Binder choice)
    |                     |                            |
    |-- operation() ----->|                            |
    |                     |-- forwards / dispatches --->|
    |                     |                            |-- does the work
    |                     |<-- result ------------------|
    |<-- result ----------|                            |


Change event, the moment PV is meant to absorb

  (a new Variant, ConcreteVendorZ, must replace ConcreteVendorX)

  Operator / Binder configuration        Stable Point         Client
          |                                   |                  |
          |-- register / wire ConcreteVendorZ |                  |
          |   as the active Variant --------->|                  |
          |                                   |  (no change to   |
          |                                   |   Client code    |
          |                                   |   or to the      |
          |                                   |   Stable Point   |
          |                                   |   contract)      |
          |                                   |                  |
          |                        Client -- operation() ------->|
          |                                   |-- dispatches --->| ConcreteVendorZ
          |                                   |<-- result -------|
          |<---------------------------------------------------- result

  The blast radius of the vendor swap is the Binder configuration only.
  Client's source and the Stable Point's contract are both untouched.
```

Two honest limits belong here, not hidden until dimension 11. First, the
diagram assumes ConcreteVendorZ genuinely satisfies the Stable Point's
contract with the same semantics as ConcreteVendorX. If it does not, for
example it returns results in a different rounding mode or a different unit,
the protection is only syntactic and the change still reaches the client
behaviorally, without a compile error to announce it. Second, the
Binder step itself is a real deployment event, a configuration change, a
container restart, a registry update, and it carries its own operational
risk, which dimension 16 covers.

## 8. Implementation variants

Larman's 2001 article names these mechanisms directly as expressions of the
one principle, ordered here from lightest to heaviest.

**Data encapsulation.** The lightest form. A field is hidden behind an
accessor so its internal representation can change without the caller
knowing. Larman's own caution against over-applying this, the `Color.red`
example, belongs to this variant specifically.

**Interfaces and polymorphism.** The Stable Point is a formal language
interface or abstract base, and the Variant is a concrete implementing or
subclassing type. This is the shape behind Strategy, Bridge, and the
subclass-overriding form of Factory Method described in the sibling entry on
that pattern.

**Indirection.** A layer sits between Client and Variant purely to avoid a
direct reference, without necessarily adding polymorphism of its own. A
message queue between a producer and a consumer, or a facade over a chatty
subsystem, are indirection used as PV. Larman names brokers and virtual
machines as complex real examples of this category.

**Uniform access.** A language feature, not a design pattern, that lets a
client write `object.member` without knowing whether `member` resolves to a
field read or a method call. Larman cites Ada, Eiffel, and C# property
syntax as examples. Where a language supports this directly, converting a
public field to a computed property later requires no client-side edit at
all, collapsing data encapsulation's usual migration cost to zero.

**Standards.** An externally defined, versioned specification, a file
format, a wire protocol, an API shape, plays the role of Stable Point across
organizational boundaries that no single team controls. HTTP, SQL, and a
published OpenAPI contract are all standards used this way.

**Data-driven design.** Behavior is parameterized by data read from outside
the code, a configuration value, a class name resolved at startup, a style
sheet, object-relational mapping metadata. Larman is explicit that this is a
"broad family of techniques" and that the system is protected from the
impact of the data changing by externalizing the variant and reading it in
rather than compiling it in.

**Service lookup.** A special case of data-driven design in Larman's own
taxonomy, where a naming service or trader, his examples are JNDI and Jini,
supplies the concrete provider at runtime by name, so the client's only fixed
dependency is on the lookup service's stable interface.

**Interpreter-driven design.** A rules engine, a scripting or language
interpreter, a constraint logic engine, or a neural network execution engine
reads externally supplied logic and executes it, protecting the system from
variation in that logic without a code change or redeploy. Larman's own
worked example in the 2001 article is exactly this, an airline's logistics
support system whose frequently changing business rules were moved into a
rules engine with an external rule editor precisely because the rate of
change was measured to be high enough to justify the mechanism's real cost.

**Reflective or metalevel design.** Introspection and reflection, Larman's
own example is `java.beans.Introspector` resolving a getter method by
property name at runtime, protect a caller from needing to know a concrete
type's shape at compile time. This is the heaviest and most dynamically
typed-feeling mechanism in the list, and it trades the strongest possible
compile-time safety for the strongest possible runtime flexibility.

## 9. Known production uses

**The POSIX filesystem system call interface.** `open`, `read`, `write`, and
`close` form a Stable Point that every userspace program depends on, while
the Variant behind it, ext4, XFS, Btrfs, NFS, or a FUSE-mounted virtual
filesystem, is swapped without recompiling the calling program. The Linux
kernel's own internal mechanism for this is the Virtual Filesystem Switch,
documented in the kernel's own documentation tree, "Overview of the Linux
Virtual File System", The Linux Kernel documentation,
https://www.kernel.org/doc/html/latest/filesystems/vfs.html, verified
2026-08-02, which states directly that the VFS "allows different filesystem
implementations to coexist" behind one uniform system call interface.

**JDBC, the Java Database Connectivity API.** `java.sql.Driver`,
`java.sql.Connection`, and `java.sql.Statement` form the Stable Point every
JDBC-consuming application is written against, while the Variant is a
vendor-supplied driver JAR for PostgreSQL, Oracle, or any other database.
Oracle's own Java SE 21 API documentation for `java.sql.DriverManager`
describes the class as managing a list of database drivers and states that
"when the method `getConnection` is called, the `DriverManager` will attempt
to locate a suitable driver from amongst those loaded", Oracle, Java SE 21 API
Specification, `java.sql.DriverManager`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/DriverManager.html,
verified 2026-08-02, which is the service-lookup mechanism from dimension 8
operating exactly as Larman describes it.

**The OCI runtime specification for containers.** Docker, containerd, and
Podman each implement the Open Container Initiative's runtime specification
as their Variant, and any tool built against the `runc`-compatible interface
can swap the underlying container runtime without the calling orchestrator,
for example Kubernetes's kubelet, being rewritten. The specification itself
states its purpose as defining "a standard, community-driven specification"
so that consumers do not depend on any one implementation, Open Container
Initiative, `runtime-spec`, README,
https://github.com/opencontainers/runtime-spec/blob/main/README.md, verified
2026-08-02.

**The W3C Document Object Model as a browser-rendering Stable Point.**
Web page authors write JavaScript against the DOM specification's stable
interface, `document.getElementById`, `Node.appendChild`, and so forth, and
the underlying rendering engine, Blink in Chromium, Gecko in Firefox,
WebKit in Safari, is a Variant that differs completely in implementation
while presenting the same contract. The W3C's own DOM specification states
it defines "a platform- and language-neutral interface that allows programs
and scripts to dynamically access and update the content, structure, and
style of a document", World Wide Web Consortium, "DOM Standard" (maintained
jointly with WHATWG), https://dom.spec.whatwg.org/, verified 2026-08-02.

## 10. Consequences

Positive.

- A change confined to a Variant, a vendor swap, a bug fix inside one
  implementation, a new provider added alongside an old one, never touches the
  Client or the Stable Point's contract, which is the entire economic
  argument for the principle.
- Two teams, or a team and an external vendor, can develop independently
  against a shared contract without a synchronized release, because the
  contract is the only thing either side must hold fixed.
- Multiple Variants can be tested against the same Stable Point using the
  same contract test suite, which is the mechanism dimension 15 names
  directly.
- Larman's own strongest claim in the 2001 article, that PV underlies the
  motivation and advice of most other patterns and principles, is a
  consequence in itself, learning to recognize the principle lets a designer
  see the common structure behind a large share of the GoF catalog rather
  than memorizing each pattern as an unrelated recipe.

Negative.

- Every Stable Point is a permanent maintenance liability of its own. It has
  to be versioned, documented, and kept honest against every Variant that
  implements it, and that cost is paid whether or not the anticipated
  variation ever actually arrives.
- The indirection a reader must trace through grows with every layer added,
  and Larman's own warning is that novice designers under-protect while
  intermediate designers systematically over-protect, adding flexibility "in
  ways that never get used".
- A Stable Point drawn around the wrong decision protects the wrong thing and
  leaves the real instability unguarded while still paying the full cost of
  the abstraction.
- Contract drift between Client expectations and Variant behavior is a new
  failure class the principle itself introduces, covered fully in dimension
  11.
- The heaviest mechanisms, interpreter-driven and reflective design, trade a
  large amount of compile-time safety for their flexibility, and defects that
  a type system would have caught at build time surface instead as runtime
  failures, sometimes in production.

## 11. Failure modes and misuse

**Speculative protection with no observed variation.** Symptom. A codebase
carries an interface with exactly one implementation, `PaymentProcessor`
with only `StripeProcessor`, and every change to Stripe's integration still
requires editing both the interface and the implementation in lockstep.
Cause. The Stable Point was drawn for an imagined future vendor that has
never actually been discussed by the business, so the abstraction earns
nothing while still costing a file, a name, and a reader's attention on every
pass through the code. Fix. Delete the interface, per Larman's own
`Color.red` reasoning, and reintroduce it later if a second Variant is
genuinely committed to, not merely imagined.

**Leaky Stable Point.** Symptom. Client code contains a cast back to a
concrete Variant type, or an `instanceof` or `is` check that branches on which
concrete provider is active. Cause. The Stable Point's contract is narrower
than what the Client actually needs, so the Client reaches around the
abstraction to get the missing capability. Fix. Push the missing operation
into the Stable Point's contract for every Variant to implement, or accept
that the Client genuinely needs Variant-specific behavior and the seam was
drawn in the wrong place.

**Contract drift, the version-skew failure.** Symptom. A Client built
against version N of a Stable Point receives a response from a Variant built
against version N+1, and the failure is a subtly wrong value rather than a
crash, for example an added enum member the Client's switch statement does
not handle and silently falls through on. Cause. The Stable Point's contract
changed in a way that was not additive-only, or the Client was not rebuilt
against the new contract before the Variant shipped. Fix. Treat every
Stable Point as a versioned artifact with an explicit compatibility policy,
additive-only changes for a minor version, a documented migration for a
breaking one, and add a contract test, per dimension 15, that runs against
every Variant on every change.

**The wrong decision protected.** Symptom. A storage layer is hidden behind
a clean repository interface, yet the query language it exposes to callers,
raw SQL fragments passed as parameters, is not, so a database migration
still touches every call site. Cause. PV was applied to the storage
mechanism, which was not actually the unstable part, while the query
language, which was, was left unprotected. Fix. Re-identify the actual axis
of variation, here the query surface rather than the storage engine, and draw
the Stable Point there instead or in addition.

**Binder misconfiguration at deploy time.** Symptom. A production incident
where the wrong Variant is active, the staging payment provider answering
live traffic, or an outdated plugin version loaded after a rollback. Cause.
The Binder step, dimension 5's connecting mechanism, is itself a piece of
configuration that can be wrong, and PV's diagrams tend to omit it as an
implementation detail rather than treating it as a first-class deployable
artifact with its own review and rollback process. Fix. Version and review
Binder configuration with the same rigor as code, and log which Variant
answered which call, per dimension 16.

**Over-generalized reflective or interpreter-driven protection.** Symptom.
A team ships a rules engine or a scripting layer for a decision that turns
out to change perhaps once a year, and every subsequent maintainer must learn
a bespoke rule syntax to make a one-line change that a direct code edit and a
deploy would have handled in less time than learning the syntax took. Cause.
The heaviest mechanism in dimension 8 was chosen against the lightest actual
rate of change. This is precisely Larman's own pager-message-system
counterexample from the 2001 article, where the scripting layer was removed
during rework because it was never needed. Fix. Match the mechanism's weight
to the measured, not assumed, frequency and blast radius of the variation.

## 12. Trade-off matrix

Compared against named alternatives that address the same underlying
concern, across the forces named in dimension 3.

| Force | Protected Variations (general principle) | Hard-coded direct dependency | Speculative generality (interface, one implementation) | Configuration flag with an if/else | Dependency injection container |
|---|---|---|---|---|---|
| Change containment when a real second Variant arrives | Strong. Only the Binder and the new Variant change | None. Every call site is edited | Nominal. The interface exists but nothing has exercised a real swap | Weak. The branch itself must be edited and grows with every option | Strong. Wiring changes, code does not |
| Cost paid before the variation is ever needed | Real, but scoped to the identified point only | None | Real, paid everywhere an interface was speculatively added | Low upfront, grows with every added branch | Moderate, a container and its configuration |
| Readability for a first-time reader | Lower. An extra name and contract to learn | Highest. The concrete thing is named right where it is used | Lower, for no offsetting benefit if no second Variant ever appears | Moderate. The branch is visible in one place | Lower. Wiring lives outside the call site |
| Team or vendor boundary support | Strong, this is its primary strength per Larman's team-topology framing | None, both sides must move in lockstep | Weak, an interface alone does not enforce a real contract boundary | Weak, both branches usually live in one codebase and one team | Strong, similar to a hand-built Stable Point |
| Risk of contract drift between sides | Present, and must be actively managed, see dimension 11 | Not applicable, there is only one side | Present but usually undetected, since there is no second Variant to drift from | Low, both branches are visible and reviewed together | Present, same as a hand-built Stable Point |
| Suitability for a short-lived or single-maintainer system | Poor. The tenth change that amortizes the cost may never come | Best. Lowest cost, no wasted indirection | Poor. Pure cost with no benefit | Acceptable for a small, bounded option set | Poor. The container's own learning cost outweighs the benefit |

Reading of the table. Protected Variations, applied through whichever
mechanism from dimension 8 fits the case, wins decisively at a real
organizational or vendor boundary and where a second Variant is a near
certainty. A hard-coded direct dependency wins for anything genuinely
single-shot. Speculative generality is the trap the whole principle warns
against, it pays PV's full readability and maintenance cost while returning
none of its change-containment benefit, because there is no second Variant to
protect against in the first place.

## 13. Related and incompatible patterns

- **Open-Closed Principle.** Not a related pattern so much as the same
  principle under a different name and a slightly different emphasis, per
  Larman's own 2001 statement quoted in dimension 1. OCP frames the goal in
  terms of a module's openness to extension and closedness to modification.
  PV frames the same goal in terms of identifying the variation point first
  and building the stable interface around it. Treat them as one idea with
  two vocabularies rather than as two ideas to reconcile.
- **Information hiding (Parnas).** The older ancestor. Parnas's 1972 formula
  of hiding a difficult or likely-to-change design DECISION, not merely
  hiding data, is the same act PV performs, and Larman's 2001 article argues
  the term has been widely misread as a synonym for data encapsulation alone,
  which is only one of PV's mechanisms from dimension 8.
- **Dependency Inversion Principle.** A structural corollary. Once a Client
  depends on a Stable Point rather than on a concrete Variant, the dependency
  arrow between the abstract and the concrete has been inverted, which is
  exactly what the Dependency Inversion Principle names as its own goal. PV
  answers WHERE to draw the seam. DIP describes the SHAPE of the dependency
  arrow once the seam exists.
- **Factory Method, Strategy, Bridge, Template Method, Abstract Factory.**
  Each of these GoF patterns is a concrete, named mechanism for achieving
  Protected Variations at a specific kind of decision, respectively which
  class to instantiate, which algorithm to run, which implementation
  hierarchy to vary independently of an abstraction hierarchy, which steps of
  an algorithm to override, and which family of related products to create
  together. See the sibling Factory Method entry in this family for how one
  of these mechanisms plays out in full detail. Treating any one of these
  patterns as a synonym for PV rather than as one instance of it is a common
  confusion this entry exists to correct.
- **Don't Talk to Strangers, the Law of Demeter.** Folded into the GRASP
  discussion of Protected Variations in later editions of Larman's book as a
  supporting technique, because limiting an object's collaborators to its
  immediate acquaintances reduces the surface area a change in a distant
  object can reach, which is a narrower, more local expression of the same
  containment goal.
- **Speculative generality (anti-pattern).** The direct incompatibility.
  Where PV protects a real, identified variation point, speculative
  generality builds the same mechanical shape, an interface, an abstract
  base, a plugin hook, around a variation nobody has actually observed or
  committed to. The two share the same mechanical shape and can only be told apart
  by whether the variation being protected against is real, which is
  precisely dimension 4's non-applicability list.
- **Big Ball of Mud (anti-pattern).** The failure state PV exists to prevent
  as a codebase grows large. A system with no protected variation points at
  all accumulates direct, concrete dependencies everywhere, so that every
  change has an unpredictable and often system-wide blast radius.

## 14. Refactoring path in and out

Introducing protection into code that has none. The relevant named
refactoring is Extract Interface, paired with Introduce Polymorphic Creation
with Factory Method or a comparable mechanism, both covered in the
refactoring family entries; the steps below sequence them for the PV case
specifically.

1. Confirm the variation is real before touching anything, per dimension 4.
   Point at the concrete evidence, a second vendor already under contract, a
   regulator's published upcoming rule, a second customer segment already
   committed for the next release, not a hypothetical.
2. Find every concrete call site that depends on the volatile decision
   directly. Grep for the concrete type or the concrete branch, not for a
   keyword, so the list is complete before any code moves.
3. Extract the minimal contract those call sites actually use into a Stable
   Point, starting with only the operations genuinely called, not the
   provider's full surface area. Over-extracting here reintroduces the
   speculative-generality trap from dimension 4 one level down.
4. Make the existing concrete implementation satisfy the new Stable Point
   as its first Variant. Run the full test suite. Nothing about runtime
   behavior should change at this step.
5. Route every call site found in step 2 through the Stable Point instead of
   the concrete type. Run the tests after each site, not once at the end, so
   a regression is caught at the exact site that introduced it.
6. Introduce the Binder, the smallest mechanism from dimension 8 that fits
   the identified boundary, a constructor parameter for a simple case, a
   configuration-driven lookup for a boundary that genuinely needs runtime
   selection. Resist reaching for the heaviest mechanism, an interpreter or a
   rules engine, unless the measured rate of change specifically justifies
   its cost.
7. Add the second, real Variant, and add the contract test from dimension 15
   before the second Variant is trusted in production.

Removing protection once it stops earning its place. The signal is a Stable
Point with exactly one Variant that has never had a second one added, for a
duration long enough that the team has concluded, in Larman's own terms, the
speculative future proofing was not needed.

1. Confirm no second Variant has been added and none is genuinely planned,
   distinguishing "we might someday" from an actual committed second Variant.
2. Inline the single Variant's implementation back through the Stable Point
   at every call site. This is Inline Class from the refactoring family
   applied to the Variant.
3. Delete the Stable Point's contract and the Binder configuration that
   selected the single Variant.
4. Run the full test suite and confirm the contract test from dimension 15
   is also deleted, since there is no longer a contract to test against.

## 15. Testing and verification

Easier because of the pattern.

- A test-only Variant, a fake or an in-memory implementation of the Stable
  Point's contract, lets Client behavior be tested with no dependency on the
  real Variant's cost or availability, a real database, a real payment
  network, a real external service.
- Each Variant can be exercised against the same test suite, written once
  against the Stable Point's contract, which is the standard contract-test or
  abstract-test-case technique, the same technique named in the sibling
  Factory Method entry for exactly the same structural reason.

Harder because of the pattern.

- A defect that only manifests when two specific Variant implementations
  disagree on an edge case, for example one rounds half-to-even and another
  rounds half-up, is invisible to a test suite that only ever exercises one
  Variant, and is exactly the contract-drift failure from dimension 11.
- The Binder's own correctness, that the right Variant is actually wired to
  the right Client in the right environment, is a configuration-level
  concern that unit tests against the Stable Point's contract do not cover at
  all, and needs its own, separate verification.

Techniques that apply.

- **Contract test suite, run against every Variant.** One shared test suite,
  written entirely against the Stable Point's public contract, executed once
  per Variant. A Variant that fails the shared suite has drifted from the
  contract regardless of how its own implementation-specific tests read.
- **Consumer-driven contract testing.** Where the Stable Point crosses a real
  team or organizational boundary, per dimension 4's applicability list, the
  Client team publishes the exact interactions it depends on and the Variant
  team's build verifies against that published expectation before shipping,
  catching the version-skew failure from dimension 11 before it reaches
  production rather than after.
- **Property-based testing on the Stable Point's invariants.** Where the
  contract states an invariant that must hold for every Variant, for example
  that a parsed-then-serialized value round-trips unchanged, a property test
  written once against the contract and run against every Variant catches a
  violation any single example-based test would miss.
- **Binder configuration as a tested artifact.** Treat the wiring that
  selects which Variant answers in which environment as code with its own
  test, asserting that the production configuration resolves to the intended
  Variant, which is the direct answer to the Binder-misconfiguration failure
  mode in dimension 11.

## 16. Observability signals

The whole point of the principle is that the Client no longer names the
concrete Variant in its source, which means the concrete Variant has to
appear somewhere in telemetry or an operator has no way to know which one is
actually running.

What to record.

- On every dispatch through the Stable Point, a log field or trace attribute
  naming which concrete Variant answered, and the Binder configuration
  version that selected it, so an incident can be traced back to a specific
  wiring change.
- A counter of calls through the Stable Point, labelled by Variant, so a
  dashboard shows the real distribution of which Variant is actually in use
  in production, which frequently differs from what an engineer assumes from
  reading the Binder configuration alone.
- A counter of contract-shape mismatches, a field the Client expected but did
  not receive, an enum value the Client's handling code did not anticipate,
  logged as a distinct, logged event rather than silently defaulted or
  swallowed.
- For any Binder that performs a runtime lookup, a service-lookup failure
  counter and the latency of that lookup, since a lookup-based Binder adds a
  real runtime dependency that a compile-time wiring choice does not carry.
- A version identifier for the Stable Point's own contract, surfaced
  alongside every dispatch, so a fleet running mixed contract versions during
  a rollout is visible rather than assumed to be uniform.

A healthy instance on a dashboard. The per-Variant call distribution matches
what the Binder configuration says it should be, and it only moves when a
deliberate configuration change explains the move. Contract-shape mismatches
sit at zero. Lookup latency, where a lookup-based Binder is in play, is flat
and small relative to the surrounding operation.

A failing instance. A Variant appears in the distribution that the current
Binder configuration should not be selecting at all, which is the
misconfiguration failure from dimension 11 made visible. Or contract-shape
mismatches climb on one Variant only, which localizes a version-skew problem
to a specific Variant's rollout without reading its source. Or lookup latency
develops a long tail on a service-lookup Binder, which points at the lookup
service itself rather than at any Client or Variant code.

## 17. Security and privacy implications

Protected Variations is neutral on security in its narrowest sense, drawing
a seam around a decision says nothing by itself about what data crosses that
seam. Three genuine implications follow once the mechanism is examined
concretely, and stating them plainly here is preferable to inventing a
broader claim the principle does not actually support.

**A Stable Point that crosses a trust boundary is a new attack surface by
definition.** When the Variant behind a Stable Point is supplied by a third
party, a plugin, a vendor's driver, a downloaded rule set for an
interpreter-driven design, the Client's algorithm now executes code or
interprets data it did not author, at whatever privilege level the Client
itself runs at. This is the same untrusted-implementor concern the sibling
Factory Method entry describes for its published extension point, and it
applies with equal force to every mechanism in dimension 8 that admits an
externally supplied Variant. Treat the Variant as untrusted input, validate
what it returns against the contract rather than trusting the declared type,
and run third-party Variants under the least privilege the runtime
environment allows.

**Data-driven and interpreter-driven mechanisms widen the input surface that
must be validated.** A rules engine reading external rules, or a
configuration-driven Binder reading a plugin path or a class name from a
file, turns what used to be a compile-time, reviewed decision into a runtime
input. An attacker who can influence that input, a malicious rule, a path
traversal in a plugin loader, a poisoned configuration value, can steer the
Client's behavior without ever touching the Client's own source code. Bound
what an interpreted rule or a loaded plugin is permitted to do, and validate
any externally supplied path or identifier before it is used to select a
Variant.

**The Binder's own audit trail matters for both security and privacy
incident response.** Because the concrete Variant that handled a given
request is no longer visible in the calling code, reconstructing which
concrete implementation processed a specific piece of data during an
incident depends entirely on the observability signals named in dimension
16. Where the data crossing the Stable Point is personal or regulated data,
the Variant-identifying log field from dimension 16 is not merely an
operational convenience, it is frequently the only record that lets an
organization answer which specific system, and therefore whose data
processing agreement or jurisdiction, actually handled a given record.

## Code examples

Three languages chosen for genuinely different idiomatic shapes. TypeScript
shows the classical interface-plus-implementations form. Python shows the
same shape using duck typing and, separately, the data-driven registry
mechanism named directly in dimension 8. Go shows the mechanism Go's lack of
inheritance naturally produces, a small interface satisfied implicitly, with
the Binder expressed as a constructor function held in a struct field, the
same parameter-passing idiom the sibling Factory Method entry documents for
Go-shaped languages generally.

### TypeScript

```typescript
// The Stable Point every Client depends on. Note the interface's shape
// stays fixed while ConcreteVendorX/Y are free to change internally.
interface TaxCalculator {
  calculate(amountCents: number, countryCode: string): number;
}

class GermanVatCalculator implements TaxCalculator {
  calculate(amountCents: number, countryCode: string): number {
    if (countryCode !== "DE") throw new Error("wrong region");
    return Math.round(amountCents * 0.19);
  }
}

class UsSalesTaxCalculator implements TaxCalculator {
  calculate(amountCents: number, countryCode: string): number {
    if (countryCode !== "US") throw new Error("wrong region");
    return Math.round(amountCents * 0.0725);
  }
}

// Client depends only on the Stable Point. It never names a concrete
// calculator, so adding a third country never requires editing this class.
class Invoice {
  constructor(
    private readonly amountCents: number,
    private readonly countryCode: string,
    private readonly calculator: TaxCalculator, // the Binder supplied this
  ) {}

  totalWithTax(): number {
    return this.amountCents + this.calculator.calculate(this.amountCents, this.countryCode);
  }
}

// The Binder, here a plain lookup map, decides which Variant a given
// country resolves to. Adding a third country touches only this map.
const calculators: Record<string, TaxCalculator> = {
  DE: new GermanVatCalculator(),
  US: new UsSalesTaxCalculator(),
};

const invoice = new Invoice(10000, "DE", calculators["DE"]);
console.log(invoice.totalWithTax());
```

### Python

Classical form first, then the data-driven registry variant Larman names
directly in dimension 8.

```python
from abc import ABC, abstractmethod


class TaxCalculator(ABC):
    @abstractmethod
    def calculate(self, amount_cents: int, country_code: str) -> int: ...


class GermanVatCalculator(TaxCalculator):
    def calculate(self, amount_cents: int, country_code: str) -> int:
        assert country_code == "DE"
        return round(amount_cents * 0.19)


class UsSalesTaxCalculator(TaxCalculator):
    def calculate(self, amount_cents: int, country_code: str) -> int:
        assert country_code == "US"
        return round(amount_cents * 0.0725)


class Invoice:
    def __init__(self, amount_cents: int, country_code: str, calculator: TaxCalculator):
        self.amount_cents = amount_cents
        self.country_code = country_code
        self.calculator = calculator  # supplied by the Binder, never named here

    def total_with_tax(self) -> int:
        return self.amount_cents + self.calculator.calculate(self.amount_cents, self.country_code)


if __name__ == "__main__":
    invoice = Invoice(10_000, "DE", GermanVatCalculator())
    print(invoice.total_with_tax())
```

Data-driven form. The Binder reads a country code from external input and
resolves the Variant through a registry rather than through code that names
every calculator directly.

```python
_REGISTRY: dict[str, type[TaxCalculator]] = {
    "DE": GermanVatCalculator,
    "US": UsSalesTaxCalculator,
}


def resolve_calculator(country_code: str) -> TaxCalculator:
    calculator_class = _REGISTRY.get(country_code)
    if calculator_class is None:
        raise KeyError(f"no calculator registered for {country_code}")
    return calculator_class()


invoice = Invoice(10_000, "US", resolve_calculator("US"))
print(invoice.total_with_tax())
```

### Go

Go has no inheritance, so the classical subclass-based shape does not apply.
The idiomatic form is a small interface implicitly satisfied by any type
with the matching method, with the Binder expressed as a constructor-time
field, the same shape the sibling Factory Method entry documents as Go's
natural expression of the pattern family.

```go
package main

import "fmt"

// The Stable Point. Any type with this method satisfies it implicitly,
// no "implements" declaration required.
type TaxCalculator interface {
	Calculate(amountCents int, countryCode string) int
}

type GermanVatCalculator struct{}

func (GermanVatCalculator) Calculate(amountCents int, countryCode string) int {
	if countryCode != "DE" {
		panic("wrong region")
	}
	return int(float64(amountCents) * 0.19)
}

type UsSalesTaxCalculator struct{}

func (UsSalesTaxCalculator) Calculate(amountCents int, countryCode string) int {
	if countryCode != "US" {
		panic("wrong region")
	}
	return int(float64(amountCents) * 0.0725)
}

// Invoice, the Client, depends only on the TaxCalculator interface field.
// Swapping the concrete calculator never touches this type.
type Invoice struct {
	AmountCents int
	CountryCode string
	Calculator  TaxCalculator // supplied by the Binder at construction time
}

func (i Invoice) TotalWithTax() int {
	return i.AmountCents + i.Calculator.Calculate(i.AmountCents, i.CountryCode)
}

func main() {
	invoice := Invoice{
		AmountCents: 10000,
		CountryCode: "DE",
		Calculator:  GermanVatCalculator{},
	}
	fmt.Println(invoice.TotalWithTax())
}
```

## 18. References

1. Craig Larman. *Applying UML and Patterns. An Introduction to
   Object-Oriented Analysis and Design*. Prentice Hall, first edition 1997,
   with the GRASP catalog, including Protected Variations, present in every
   subsequent edition. Source of the GRASP pattern name and its formal
   definition as one of the nine General Responsibility Assignment Software
   Patterns.
2. Alistair Cockburn. "Prioritizing Forces in Software Design". In *Pattern
   Languages of Program Design*, volume 2, Addison-Wesley, 1996. Source of
   the earliest description of the underlying idea, published before the
   Protected Variations name existed and before Cockburn knew of the
   Open-Closed Principle, per Larman's own account.
3. Craig Larman. "Protected Variation. The Importance of Being Closed".
   *IEEE Software*, volume 18, number 3, May/June 2001, pages 89 to 91.
   https://martinfowler.com/ieeeSoftware/protectedVariation.pdf
   Verified 2026-08-02. The primary source for this entry. Naming of the term
   for general use, the relationship to OCP and information hiding, the full
   list of mechanisms in dimension 8, the Color.red and pager-scripting
   anecdotes in dimensions 4 and 11, and the "pick your battles" framing in
   dimension 3.
4. Bertrand Meyer. *Object-Oriented Software Construction*. IEEE Press
   Prentice Hall, 1988. Source of the Open-Closed Principle statement quoted
   in dimension 1, as reproduced and cited in Larman's 2001 article.
5. David Parnas. "On the Criteria to Be Used in Decomposing Systems into
   Modules". *Communications of the ACM*, volume 15, number 12, December
   1972, pages 1053 to 1058. Source of information hiding, quoted directly in
   dimension 1 via Larman's 2001 article's reproduction of Parnas's own
   words.
6. The Linux Kernel documentation project. "Overview of the Linux Virtual
   File System". https://www.kernel.org/doc/html/latest/filesystems/vfs.html
   Verified 2026-08-02. Source for the POSIX filesystem production use in
   dimension 9.
7. Oracle. *Java SE 21 API Specification*, `java.sql.DriverManager`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/DriverManager.html
   Verified 2026-08-02. Source for the JDBC production use in dimension 9.
8. Open Container Initiative. `runtime-spec` project README.
   https://github.com/opencontainers/runtime-spec/blob/main/README.md
   Verified 2026-08-02. Source for the container runtime specification
   production use in dimension 9.
9. World Wide Web Consortium and WHATWG. "DOM Standard".
   https://dom.spec.whatwg.org/
   Verified 2026-08-02. Source for the Document Object Model production use
   in dimension 9.
10. GRASP (object-oriented design). Wikipedia.
    https://en.wikipedia.org/wiki/GRASP_(object-oriented_design)
    Verified 2026-08-02. Used only to cross-check the naming and grouping of
    Protected Variations among the other eight GRASP patterns, not as a
    source of explanation for the principle itself.
