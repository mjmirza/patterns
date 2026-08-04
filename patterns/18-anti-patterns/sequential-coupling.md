---
name: Sequential Coupling
slug: sequential-coupling
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Temporal Coupling, Connascence of Execution, Order-Dependent API]
first_described: "Page-Jones 1988 (as Connascence of Execution, within the connascence taxonomy); Seemann 2011 (named and defined as a design smell, Temporal Coupling)"
maturity: canonical
related: [state, builder, iterator, template-method, boat-anchor]
incompatible_with: []
verified: 2026-08-02
---

# Sequential Coupling

## 1. Name, aliases, and lineage

The name used in this entry is Sequential Coupling, treated here as a full
synonym of the more common term Temporal Coupling. Both names describe the
same defect, an object exposes two or more public members that must be
invoked in a specific order for the object to behave correctly, and nothing
in the type signature of those members states that requirement. The two
names compete in practitioner usage with no clean split between them, so
this entry does not invent a distinction that the literature does not carry.

The clearest, most citable statement of the defect as a named design smell
comes from Mark Seemann, writing on his ploeh blog in a post titled "Design
Smell. Temporal Coupling", 24 May 2011. Seemann defines it plainly, quoting
his own wording, as "an implicit relationship between two, or more, members
of a class requiring clients to invoke one member before the other"
([Seemann, Design Smell. Temporal Coupling](https://blog.ploeh.dk/2011/05/24/DesignSmellTemporalCoupling/),
verified 2026-08-02). His worked example is a class with an `Initialize`
method and a `Spread` method, where calling `Spread` before `Initialize`
compiles without complaint and fails only at run time. That example, an
initialize-then-act pair with no compile-time enforcement between them, is
the canonical shape this entire entry is built around, and the reader
should hold it in mind through every dimension below.

The identical defect was already named a decade earlier under a different
taxonomy. Meilir Page-Jones classified software coupling by what two
components must share to remain correct together, a scheme he called
connascence, first published in his book *Practical Guide to Structured
Systems Design*, second edition, Dorset House, 1988, ISBN 978-0136907695
([Wikipedia, Connascent software components, citing Page-Jones](https://en.wikipedia.org/wiki/Connascent_software_components),
verified 2026-08-02). Within that taxonomy, the case where "the order of
execution of multiple components is important" is named Connascence of
Execution, defined in exactly those words on the reference site that
carries the taxonomy forward for practitioners today, with a worked
example of an `Email` object whose `setSubject` call has no effect once it
arrives after `send`, a near duplicate of Seemann's later example built
from a different vocabulary
([connascence.io, Connascence of Execution](https://connascence.io/execution.html),
verified 2026-08-02). Page-Jones therefore has the earlier, book-published
description of the same mechanism, and Seemann has the more widely quoted,
directly named articulation of it as a design smell for object-oriented
APIs specifically. This entry cites both rather than picking a single
inventor, because the honest record is two independent namings of one
defect from two different traditions, structured systems analysis and
object-oriented design smells, that only later recognized each other.

One disambiguation matters enough to state before anything else. The word
"sequential" already has a long-established, unrelated, and favorable
meaning in software design literature, sequential cohesion. Larry
Constantine originated the cohesion and coupling metrics in the late 1960s
as part of Structured Design, published with Edward Yourdon in *Structured
Design. Fundamentals of a Discipline of Computer Program and Systems
Design*, Yourdon Press, 1979, building on an earlier 1974 article by
Stevens, Myers, and Constantine
([Wikipedia, Cohesion (computer science)](https://en.wikipedia.org/wiki/Cohesion_(computer_science)),
verified 2026-08-02). In that taxonomy, sequential cohesion describes a
module whose internal steps run in order because the output of one step is
literally the input to the next, a parsing pipeline or a data transform
chain, and it is rated one of the two best cohesion types alongside
functional cohesion. That is a statement about how well a single module's
internal parts belong together. Sequential Coupling, the subject of this
entry, is a statement about an external contract between an object and its
callers. A well-written pipeline function with excellent sequential
cohesion inside it can still expose terrible sequential coupling to its
callers if it is split into separately callable steps with no enforcement
between them. The two ideas share a word and nothing else, and conflating
them in conversation is a common and avoidable confusion this entry
refuses to repeat.

A related, informal alias appears in some object-oriented design writing
as Order-Dependent API, used descriptively rather than as a formally
sourced term, and this entry lists it as an alias on that basis rather
than attributing it to a specific author.

## 2. Problem and context

An object accumulates behavior across its public surface the way most
long-lived classes do, one method added at a time as new requirements
arrive. At some point in that growth, a later method's correctness starts
to depend on an earlier method having already run. The dependency is
rarely planned. It is usually the accidental result of moving what used to
be one large method's internal steps into several smaller public methods,
without also asking what happens if a caller invokes only the second half.

The situation is recognizable in a codebase by a specific shape. A class
holds a field that starts empty or in a sentinel state. One public method
populates that field. A different public method reads it, and either
assumes it is already populated, or checks and reacts if it is not,
usually by throwing, sometimes by silently doing nothing. Nothing about
the second method's signature communicates that the first method must
have already run. A reader has to open the source, read the body, and
reconstruct the protocol by inference, or consult documentation that may
or may not exist and may or may not still be accurate.

The context that produces this defect has three recurring shapes, and
naming them precisely helps a reader recognize which one they are looking
at.

- **Setup before use.** A resource, a connection, a parser, a session,
  needs some expensive or external step, opening a socket, allocating a
  buffer, authenticating, before its main operation can run. The setup
  step and the main operation end up as two separate public calls, `Open`
  then `Send`, `Connect` then `Query`, `Parse` then `GetResult`.
- **Teardown after use.** The mirror image. A resource must be released,
  closed, committed, or rolled back after use, and the release step is a
  separate public call that a caller can forget, `Close`, `Commit`,
  `Dispose`.
- **State machine in disguise.** The object has more than two valid states
  and different methods are valid in different states, an order form that
  can be modified before checkout but not after, a socket that can send
  before it is closed but not after. The object never declares this
  explicitly as a state machine, so every method carries its own ad hoc
  state check, if it checks at all.

All three shapes share the same root context. Something inside the object
is stateful across calls, that state is not represented in the type of the
object as seen by the caller, and the object's own methods are the only
place where the rule about valid call order is enforced, if it is enforced
anywhere. The problem is not that the object has state. Almost every
useful object does. The problem is that the state's constraints on call
order are invisible until violated.

## 3. Forces

- **Encapsulation versus visible protocol.** Hiding a multi-step process
  behind a small set of methods is normally what encapsulation is for, but
  when the hidden process has an order requirement the object does not
  also enforce, encapsulation has hidden the wrong thing. The information
  that should be visible, the valid call sequence, has been hidden along
  with the implementation detail that legitimately should be.
- **Deferred, expensive work versus safety.** A real reason drives the
  setup before use shape, opening a network connection or authenticating
  a session is costly, and doing it only when needed, rather than in a
  constructor that might be called speculatively, is often the right
  performance decision. That same deferral is exactly what creates the
  window in which a caller can call the wrong method first. The pattern
  favors laziness and pays for it in safety.
- **Reusability versus atomic construction.** An object built through a
  sequence of calls can be paused mid-sequence, inspected, reconfigured,
  or pooled and reused, none of which a fully atomic, single-call
  constructor supports as naturally. Every one of those flexibility
  benefits is also the surface area on which a caller can go wrong.
- **Compile-time safety versus implementation and type-count cost.** The
  strongest known fixes, discussed in dimension 8, move the ordering
  constraint into the type system so an invalid sequence fails to
  compile. That safety is bought with more types, one per valid state,
  and with extra ceremony for every legitimate caller, even the ones who
  would never have made the mistake.
- **Testability.** A method with no order dependency can be tested in
  isolation with an arrange step of one line. A method with sequential
  coupling requires its test to first replay the entire valid history
  that leads to the state under test, which couples every test to the
  object's internal protocol as tightly as production callers are
  coupled to it.
- **Discoverability for a new caller.** A method's own name and parameter
  list are the primary thing a new caller reads. When the true
  precondition lives only in a doc comment, a wiki page, or nowhere, a
  new caller has no reliable way to discover it before hitting the
  failure. IDE autocomplete actively works against safety here, because
  it lists the out-of-order method as just as callable as the correct
  next one.

No design in this space escapes every one of these forces at once. A
resource that is expensive to acquire genuinely benefits from a two-step
acquire-then-use shape, and the honest engineering question is never
whether an order dependency should exist, it is whether the dependency is
made visible and enforced, or left as an unstated assumption for callers
to discover on their own.

## 4. Applicability and non-applicability

Sequential Coupling as described in this entry is a defect to fix, not a
design to choose. The applicability list below is therefore phrased as
recognition criteria, when a piece of code genuinely has this defect and
is worth the cost of a fix, rather than as reasons to introduce it.

Treat an order dependency as the anti-pattern, worth fixing, when the
following hold together.

- The order requirement is not expressed anywhere in the object's public
  type, so a compiler, a type checker, or even a careful reader glancing
  at a method signature cannot detect the mistake before it happens.
- Violating the order produces a poor outcome, a confusing exception far
  from its cause, a silent no-op, or corrupted output, rather than a
  clear, immediate, well-localized failure.
- A caller outside the object's own module is expected to hold the
  correct call sequence in memory, from documentation, from an example
  they copied, or from having been burned by it once already.
- A realistic, not-excessively-costly redesign exists, an atomic
  constructor, a resource-scope wrapper, or a staged type, that would
  remove the defect without removing any capability callers genuinely
  need.

Do NOT treat the following as instances of this anti-pattern, and building
a staged type or a fluent protocol to fix any of them is very often a
worse outcome than leaving the code as it is.

- **Iteration protocols.** `hasNext` and `next` on an iterator, or `Scan`
  followed by `Text` on a scanner, carry an order requirement, but the
  requirement is the entire, universally understood contract of iteration
  in the host language, documented once at the language or
  standard-library level rather than once per class, and violated rarely
  because the idiom is taught before any specific class using it is read.
  See dimension 9 for a sourced example and dimension 13 for why this
  repository draws the line here rather than flagging every iterator as
  an anti-pattern.
- **Resource lifecycles already wrapped by a language construct.** A file
  handle used inside Python's `with`, a database transaction used inside
  Go's `defer`, or a stream used inside Java's try-with-resources still
  has an underlying open-then-close order requirement, but the language
  construct has already turned that requirement into something the
  compiler or runtime enforces structurally. The residual risk here is a
  caller who bypasses the wrapper and calls the raw open and close
  methods directly, which is a real, lower-severity instance of the
  defect, not an argument that the wrapped form is itself the
  anti-pattern.
- **Builders that end in an explicit terminal call.** A fluent builder
  that requires `.build()` as its last call is deliberately sequentially
  coupled to everything before it, and that is the accepted,
  well-understood contract of the Builder pattern, not a smell, provided
  the builder's earlier steps do not also carry undocumented order
  requirements among themselves. See dimension 13.
- **Genuine, small, explicit state machines.** A traffic light, an order
  workflow with three or four named states, or a wizard-style form is
  correctly modeled as a state machine, and different operations are
  correctly valid only in certain states. This is not the anti-pattern
  provided the states are named and the transitions are checked
  consistently, ideally through the GoF State pattern described in
  dimension 13 rather than through ad hoc flags scattered across methods.
- **A collapse into one giant constructor when steps are genuinely
  independent.** The instinct to fix any order dependency by cramming
  every step into one constructor call is itself a mistake when some of
  those steps are legitimately optional, independently reusable, or
  expensive enough that eager execution would waste effort for callers
  who do not need every step. Forcing atomic construction onto a case
  that needed staged, optional configuration trades one defect,
  undocumented ordering, for another, an inflexible, eager, hard-to-test
  constructor. See dimension 11 for a named failure mode of
  over-correcting in this direction.

## 5. Structure

The anti-pattern has four participants, named by the role each plays.

- **StatefulComponent.** The object exposing the defect. It has a public
  surface of two or more members whose correct behavior depends on prior
  calls to other members of the same object.
- **ImplicitState.** A field or set of fields inside StatefulComponent
  that records what has already happened, a boolean flag, an enum, a
  nullable reference that starts null, a cursor position. This state is
  private, or at least not exposed in a form the type system can
  reason about, so it cannot participate in compile-time checking.
- **OrderedMember.** Any one of the public methods whose precondition or
  postcondition touches ImplicitState. Some OrderedMembers write
  ImplicitState, transition members, and some read it, dependent members,
  and a member can do both.
- **Client.** The caller of StatefulComponent, who must independently
  discover, remember, and honor the valid sequence of OrderedMember
  calls. The Client's only sources of truth are documentation, examples,
  and, absent both, the failure itself.

A fifth, optional participant is worth naming because its presence
changes the anti-pattern's severity more than any other factor, the
FailureBehavior, what happens when a Client calls an OrderedMember out of
turn. An explicit, immediate, well-labeled exception is the least harmful
outcome available once the defect exists at all. A silent no-op or a
corrupted result is the worst, because the Client receives no signal that
anything went wrong until much later, if ever. Dimension 11 treats the
choice of FailureBehavior as its own axis of misuse.

## 6. ASCII structure diagram

```
   +----------------------------------------------+
   |               StatefulComponent               |
   |------------------------------------------------|
   |  - implicitState: bool / enum / cursor  <---.  |  (never exposed
   |                                              |  |   in the type)
   |  + transitionMember()   writes implicitState-'  |
   |  + dependentMember()    reads  implicitState    |
   |  + otherDependentMember() reads implicitState   |
   +----------------------------------------------+
                 ^                    ^
                 |  calls, any order  |  calls, any order
                 |  the type allows   |  the type allows
   +----------------------------------------------+
   |                    Client                      |
   |------------------------------------------------|
   |  must independently know                        |
   |    transitionMember() before dependentMember()  |
   |  the type signature enforces nothing here        |
   +----------------------------------------------+

   Both member calls above have the identical signature shape as far as
   the type system is concerned. Only implicitState, invisible to the
   Client, distinguishes a valid call from an invalid one.
```

## 7. Dynamics

The runtime behavior worth tracing is not the single happy path, it is the
divergence between the correct sequence and the two common mistakes, a
skipped step and a repeated step. The failure, when there is one, happens
inside `dependentMember`, at a point in time and a location in the call
stack that has nothing to do with where the actual mistake, the missing or
misordered call, was made.

```
Correct sequence

  Client                         StatefulComponent
    |                                    |
    |-- transitionMember() ------------->|
    |                                    |-- implicitState := true
    |<-- returns -------------------------|
    |                                    |
    |-- dependentMember() --------------->|
    |                                    |-- reads implicitState (true)
    |                                    |-- proceeds normally
    |<-- correct result ------------------|


Skipped-step failure, the common shape when the failure is guarded

  Client                         StatefulComponent
    |                                    |
    |-- dependentMember() --------------->|   (transitionMember was
    |                                    |     never called)
    |                                    |-- reads implicitState (false)
    |                                    |-- throws InvalidOperationException
    |<-- exception, far from the ---------|   or equivalent
    |     Client's actual mistake         |


Skipped-step failure, the shape when the failure is unguarded

  Client                         StatefulComponent
    |                                    |
    |-- dependentMember() --------------->|
    |                                    |-- reads implicitState (false)
    |                                    |-- silently no-ops, or reads a
    |                                    |    default/null value
    |<-- looks like success ---------------|
    |                                    |
    (the wrong result surfaces later, somewhere else entirely, with no
     stack trace pointing back to this call)
```

Two timing details matter beyond the diagram. First, when the failure is
guarded by an exception, the exception's throw site is inside
StatefulComponent, at `dependentMember`, while the actual mistake was made
by the Client, at the call to `dependentMember` itself rather than at a
missing call to `transitionMember` that is nowhere on the stack. A reader
of the stack trace sees only the effect, never the cause, unless the
exception message is written carefully enough to name the missing prior
call by name. Second, repeated calls to `transitionMember` are a separate
failure shape from skipped ones and deserve their own check, since some
implementations correctly reject a second `Open` but many silently allow
it, leaking whatever resource the first call acquired.

## 8. Implementation variants

**Unguarded implicit state.** The most common starting shape, and the most
dangerous. `implicitState` exists, is written by transition members and
read by dependent members, and no member checks it before acting. A
dependent member called too early reads a default, empty, or null value
and proceeds anyway, producing FailureBehavior in the silent, worst-case
form from dimension 7.

**Exception-guarded implicit state.** Each dependent member checks
`implicitState` first and throws an exception, `InvalidOperationException`,
`IllegalStateException`, or a language-specific equivalent, when the check
fails. This is strictly better than the unguarded form, because the
failure is at least immediate and loud, but the check is still enforced
only at run time, only in the members someone remembered to guard, and
only for callers who happen to exercise the failing path in a test.

**Explicit finite-state-machine field.** Instead of one or two boolean
flags, the object holds a single enum field naming its current state, and
every member consults a small, centralized table of which states permit
which calls. This does not add compile-time safety, but it consolidates
the protocol into one place a reader can audit, replacing scattered ad hoc
checks with one authoritative source, and it is the natural bridge toward
the GoF State pattern described in dimension 13.

**Resource-scope wrapper, RAII and its descendants.** C++'s Resource
Acquisition Is Initialization idiom, Python's `with` statement and
context manager protocol, Java's try-with-resources, C#'s `using`, and
Go's `defer` all address the specific setup-then-teardown half of this
anti-pattern by binding the release step to the lifetime of a scope, so a
caller cannot forget to call the closing member as long as they enter the
scope at all. This fixes the teardown half completely and reliably. It
does not, by itself, fix ordering problems among calls made inside the
scope, a `Send` called before `Open` completes inside a `using` block is
still possible unless the scope's entry point is also the only place
`Open` can be triggered.

**Staged, fluent builder types.** Instead of one class with hidden state,
the protocol is split into two or more classes, one per valid state, and
each transition member returns an instance of the next class rather than
`this`. A method that would be invalid in the current state simply does
not exist on the current type, so calling it is a compile error rather
than a run time one. This is the strongest general-purpose fix available
in statically typed languages, sometimes called a typestate, discussed
further in the code examples, and its cost is one class or interface per
state plus the loss of the ability to hold a single stable reference
across the whole protocol, since the reference's type itself changes at
each step.

**Atomic construction, the immutable value object.** Where every step in
the sequence is in fact mandatory and none of it is genuinely expensive to
run eagerly, the cheapest fix available is often to remove the
multi-step protocol entirely and perform the whole sequence inside a
single constructor or static factory call, returning an object that is
fully valid from the moment it exists and exposes no further transition
members at all. This sacrifices the ability to defer expensive work or to
reuse the object across multiple protocol runs, and it is the right
trade whenever that flexibility was never actually used.

## 9. Known production uses

**`java.lang.Thread.start()`.** A `Thread` object may be started at most
once. The Java SE 21 API specification states this directly, "A thread
can be started at most once. In particular, a thread can not be restarted
after it has terminated," and documents that calling `start()` a second
time throws `IllegalThreadStateException`
([Oracle, Java SE 21 API Specification, Thread](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html),
verified 2026-08-02). This is the exception-guarded variant from
dimension 8, applied to the repeated-call failure shape rather than the
skipped-call shape, one of the oldest and most heavily used classes in
the platform carrying a documented, enforced order constraint on itself.

**`java.sql.ResultSet`.** A `ResultSet` begins with its cursor positioned
before the first row, and a caller must call `next()` to advance to a row
before reading any column value, or the call throws. The specification
states, "A `ResultSet` object maintains a cursor pointing to its current
row of data. Initially the cursor is positioned before the first row,"
and separately, "Any invocation of a `ResultSet` method which requires a
current row will result in a `SQLException` being thrown"
([Oracle, Java SE 21 API Specification, ResultSet](https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/ResultSet.html),
verified 2026-08-02). This is the setup-before-use shape from dimension
2, guarded, and it is one of the most-called stateful APIs in enterprise
software, present in essentially every JDBC-based data access layer
written since the mid-1990s.

**`SqlConnection.Open()`, ADO.NET.** Microsoft's .NET data access API
requires a connection to be opened before commands can execute against
it, and documents that calling `Open()` on an already-open connection
throws `InvalidOperationException` with the message "The connection is
already open"
([Microsoft, .NET API documentation, SqlConnection.Open](https://learn.microsoft.com/en-us/dotnet/api/system.data.sqlclient.sqlconnection.open),
verified 2026-08-02). This is the same defect as `Thread.start()`, a
guarded, repeated-call violation of an order constraint, in a different
platform's most heavily used data access primitive, which shows the
pattern recurring independently across language communities that share no
common codebase.

**Go's `bufio.Scanner`.** The Go standard library's line and token
scanner requires `Scan()` to be called before `Text()` or `Bytes()`
return a meaningful value. The package documentation states that `Scan`
"advances the Scanner to the next token, which will then be available
through the `Scanner.Bytes` or `Scanner.Text` method," and separately
that `Bytes` "returns the most recent token generated by a call to
`Scanner.Scan`"
([Go project, package bufio, Scanner](https://pkg.go.dev/bufio#Scanner),
verified 2026-08-02). Go's own documentation and idiom classify this as
the accepted iteration-protocol shape excluded from applicability in
dimension 4 rather than as a defect, and it is included here for exactly
that reason, as a real, named, sourced instance of the same underlying
mechanical dependency deployed deliberately and safely, the boundary case
this entry needs to be honest about the difference between the
anti-pattern and a sanctioned convention.

## 10. Consequences

Positive, present only because a real design trade-off produced them,
never because the defect itself is desirable.

- Expensive or external setup, opening a socket, authenticating,
  allocating a large buffer, can be deferred until a caller genuinely
  needs it, rather than paid eagerly by every caller including those who
  never proceed further.
- An object can be paused mid-protocol, inspected, or reconfigured
  between steps in ways a single atomic constructor call does not allow.
- The shape mirrors genuinely stateful real-world processes one to one, a
  connection really is either open or not, which can make the code read
  naturally to a domain expert who already thinks in those terms, at the
  cost of that same person being exactly the kind of caller most likely
  to assume the object enforces the rule they already know informally.

Negative.

- The valid call sequence is a contract the type system cannot see, so
  static analysis, refactoring tools, and code review all lose their
  ability to catch violations before they run.
- Failures, when they are caught at all, surface at the site of the
  dependent call, not at the site of the actual mistake, which is the
  missing or misordered transition call, forcing every debugging session
  to work backward from effect to cause.
- Every unit test that exercises a dependent member must first
  reconstruct the entire valid history leading up to it, coupling the
  test suite as tightly to the internal protocol as production code is.
- Concurrent or re-entrant use is unusually dangerous, because two
  callers racing through the same protocol on a shared instance can
  interleave their calls and leave `implicitState` in a combination
  neither caller intended, a failure mode invisible in any
  single-threaded test.
- The entire burden of documenting the protocol correctly, and keeping
  that documentation current as the class evolves, falls on prose that
  has no mechanical link to the code it describes and can silently go
  stale.

## 11. Failure modes and misuse

**A late exception with no connection to its cause.** Symptom. A test or
a production log shows a `NullPointerException`, a nil pointer
dereference, or an equivalent, several frames deep inside a method whose
job has nothing to do with initialization. Cause. A dependent member
reads a field that a transition member was supposed to set, and no guard
exists, so the failure happens at the first place the missing value is
actually dereferenced rather than at the missing call itself. Fix. Add an
explicit, named guard at the entry of every dependent member, per the
exception-guarded variant in dimension 8, or remove the gap entirely with
atomic construction.

**Intermittent failures that reproduce only under concurrency.** Symptom.
A test suite is flaky specifically when run in parallel or under load,
and passes reliably in isolation. Cause. Two callers share one instance
of StatefulComponent and race through its transition and dependent
members, interleaving in a way neither caller's own code path
anticipated. Fix. Make the object either fully immutable after
construction, so there is no shared mutable protocol state to race on, or
give each caller its own instance rather than sharing one across
concurrent callers.

**A slow resource leak that grows over the process lifetime.** Symptom.
Open file descriptors, open sockets, or database connections accumulate
over the life of a long-running process and eventually exhaust an
operating system limit. Cause. The teardown half of a setup-then-teardown
protocol, `Close`, `Dispose`, `Release`, is easy to forget precisely
because forgetting it produces no immediate symptom. Fix. Bind the
release call to a scope using the host language's resource-scope
construct described in dimension 8, so entering the scope at all
guarantees the release runs.

**A wrong answer with no exception at all.** Symptom. A report shows zero
rows, a cache never populates, or a computed value is silently the
default rather than the intended one, discovered by a person noticing
incorrect output rather than by any automated signal. Cause. The class
implements the unguarded variant from dimension 8, where a dependent
member called too early quietly returns a default rather than failing.
Fix. Change the unguarded implementation to the guarded one first,
converting the silent failure into a loud one, then pursue a structural
fix if the cost is justified.

**Boilerplate call sequences copied across every call site.** Symptom.
The same three or four lines, `open()`, `authenticate()`, `configure()`,
in that exact order, appear verbatim at dozens of call sites across a
codebase, and one of the copies is eventually found to have the steps in
a subtly wrong order or missing a step. Cause. No single entry point
exists that performs the whole valid sequence on the caller's behalf, so
every caller reimplements the protocol from memory or from a copied
example. Fix. Add one method or factory function that performs the
entire sequence correctly, and either deprecate direct access to the
individual steps or document plainly that the combined entry point is
the intended one.

**Over-correction into an inflexible mega-constructor.** Symptom. A class
that legitimately needed staged, optional configuration is rewritten
into a single constructor that requires every parameter up front, and
callers who only needed a subset of the original steps now pay for all of
them, or resort to passing sentinel values for parameters they do not
use. Cause. A well-intentioned fix for sequential coupling applied
without checking whether the steps were genuinely mandatory and
genuinely cheap enough to run eagerly, the exact non-applicability case
named in dimension 4. Fix. Restore optional, staged configuration through
a builder, ideally the staged, type-safe form from dimension 8 rather
than the original unguarded form, rather than forcing atomic construction
onto a case that needed flexibility.

## 12. Trade-off matrix

Compared against the named alternatives introduced across dimensions 8
and 13, across the forces from dimension 3.

| Force | Raw sequential coupling, unguarded | Raw sequential coupling, exception-guarded | RAII / resource-scope wrapper | Staged, fluent typestate | Atomic immutable construction | GoF State (explicit state machine) |
|---|---|---|---|---|---|---|
| Visibility of the order requirement | None | None in the type, only in the thrown message | Partial, the scope boundary is visible, internal order is not | Full, encoded in the type of each returned object | Full, there is no order left to violate | Partial, centralized in one table, still runtime-checked |
| When a violation is caught | Never, wrong result silently returned | At run time, at the point of misuse | At run time, only for calls made outside the scope | At compile time | Not applicable, no invalid state is representable | At run time, at the point of misuse |
| Deferred, expensive setup | Supported | Supported | Supported, tied to scope entry | Supported, deferred until the transition call | Not supported, everything runs at construction | Supported |
| Object reuse across multiple protocol runs | Possible, unsafely | Possible, safely if reset logic is correct | Limited to the wrapped scope's lifetime | Requires constructing a new value per state, no in-place reuse | Not applicable, a new instance is required per run | Possible, if the transition table permits returning to an earlier state |
| Test setup cost per dependent member | High, must replay full history, and may not even fail | High, must replay full history | Moderate, the wrapper often provides a convenient test double | Low, the state itself is the type, harder to construct an invalid one at all | Lowest, valid construction is the only path | Moderate, must drive the state machine to the target state |
| Concurrency safety | Worst, races corrupt shared implicit state silently | Poor, races still corrupt shared state, at least loudly | Good within one scope's lifetime, poor if the wrapped object is shared across scopes | Good, a moved-from or consumed value cannot be reused by a second caller in languages with ownership | Best, immutable objects share safely with no coordination | Poor unless the transition table itself is synchronized |
| Implementation and type-count cost | Lowest | Low, one guard per member | Low to moderate, one wrapper type | Highest, one type per state | Low, but callers lose flexibility | Moderate, one enum plus one table |

Reading of the table. Nothing in this comparison is free. The unguarded
and guarded forms of the raw defect cost the least to write and the most
to use correctly. RAII fixes exactly the teardown half of the problem at
low cost and is the right default wherever the host language provides it.
The staged typestate buys the strongest guarantee, compile-time rejection
of invalid sequences, at the highest cost in class or interface count,
and earns that cost mainly in libraries with many external callers where
the number of mistakes prevented across all callers outweighs the
ceremony paid by each. Atomic construction is the cheapest complete fix
whenever the deferred flexibility it removes was never actually used.
The GoF State pattern does not add compile-time safety by itself, its
value is making an already necessary state machine explicit and
centrally auditable rather than scattered.

## 13. Related and incompatible patterns

- **State (GoF).** The most direct structural relative. Where Sequential
  Coupling leaves the valid-call-sequence rule implicit and scattered
  across ad hoc checks in each method, the State pattern, described in
  Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides, *Design
  Patterns. Elements of Reusable Object-Oriented Software*,
  Addison-Wesley, 1994, in the Behavioral Patterns chapter under State,
  makes the current state a first-class object and delegates each
  request to it, so which operations are valid is determined by which
  State object is currently installed rather than by a field a reader
  has to trace through every method. This does not add compile-time
  enforcement by itself, since a caller in most languages can still hold
  a reference to the context and call a method the current state object
  does not support, triggering a runtime error inside the State object
  instead of inside a raw boolean check, but it consolidates the
  protocol into one auditable place, which is a real and worthwhile
  improvement even without static guarantees.
- **Builder.** A substitute and, in its staged form, a fix. An ordinary,
  unstaged builder where every setter returns `this` still allows a
  caller to omit a mandatory field and call `.build()` anyway, which is
  Sequential Coupling wearing a fluent syntax. A staged builder, where
  each step returns a distinct interface exposing only the next legal
  step, removes that gap entirely and is the general pattern
  instantiated concretely in the typestate code example in this entry.
- **Iterator.** A legitimate, accepted instance of the identical
  mechanical shape, `hasNext` and `next`, or `Scan` and `Text`, that this
  repository deliberately does not classify as an anti-pattern, for the
  reasons given in dimension 4 and demonstrated with a sourced example
  in dimension 9. Understanding why Iterator is acceptable and a bespoke,
  undocumented, two-method protocol on an unrelated class is not, is the
  single most useful distinction a reader of this entry should take
  away.
- **Template Method.** A related but distinct concern. Template Method
  fixes the order of a sequence of steps by having the base class itself
  call each hook in the correct order from one final, non-overridable
  method, so the caller never gets a chance to call the hooks directly,
  let alone out of order. Sequential Coupling is precisely what remains
  when a class exposes what should have been private, ordered hook
  methods as independently callable public methods instead, leaving the
  caller to supply the ordering that Template Method would otherwise
  supply itself. A Template Method whose protected hooks are mistakenly
  declared public degrades directly into this anti-pattern.
- **Immutable value object.** The strongest available fix and, taken to
  its logical end, structurally incompatible with the defect. An object
  with no mutators exposed after construction has no intermediate,
  partially valid state for a caller to observe or act on out of order,
  because construction either succeeds completely and atomically or does
  not produce an object at all. Wherever the flexibility that staged
  mutation provided was never actually exercised, converting to an
  immutable value object removes the anti-pattern rather than merely
  mitigating it.
- **Boat Anchor.** A loosely related, commonly co-occurring anti-pattern
  documented elsewhere in this family. A half-finished migration away
  from a raw sequential-coupling protocol, toward a staged builder or an
  atomic constructor, frequently leaves the old transition methods in
  place, unused but not removed, which is exactly the accretion pattern
  the Boat Anchor entry describes. The two are not the same defect, but
  fixing one without cleaning up after itself tends to create the other.

## 14. Refactoring path in and out

Sequential Coupling is not deliberately introduced as a design choice in
the way a genuine pattern is. It accretes, one incremental change at a
time, from code that did not originally have it, which makes
"refactoring in" here a description of how the defect typically arrives
rather than a recommendation.

The typical arrival looks like this. A class starts with one method that
does everything, including some setup work at the top of its body. Later,
a second caller needs the same setup but a different main operation, so
the setup code is extracted into its own public method and the original
method's setup call is simply removed, leaving the caller of the original
method to call the new setup method first by convention. Nobody adds a
guard to the main operation, because at the time of the change every
known caller was updated correctly. A third caller arrives later, does
not know the convention, and calls only the main operation, and the
defect is now live.

Refactoring the defect out is an ordered discipline, and skipping steps
tends to reproduce a milder version of the same problem under a
different name, per the over-correction failure mode in dimension 11.

1. **Name the states.** Before writing any new code, list every distinct
   state the object can be in and which of its public members are valid
   in each one. If this list cannot be written down in a few lines, the
   class likely has more going on than a simple order dependency and may
   need a larger redesign than this refactoring covers.
2. **Add guards before changing structure.** For every dependent member,
   add an explicit check against the implicit state and throw a clearly
   worded exception naming both the member that was called and the
   member that should have been called first. This alone converts the
   worst FailureBehavior, silent wrong results, into the least bad one,
   an immediate and diagnosable exception, and can ship on its own as a
   complete, low-risk first step.
3. **Decide between atomic construction and a staged type.** Using the
   applicability criteria in dimension 4, determine whether every step
   in the sequence is genuinely mandatory and cheap enough to run
   eagerly. If so, collapse the sequence into a single constructor or
   factory call and remove the individual transition members from the
   public surface entirely. If some steps are genuinely optional or
   expensive to defer, proceed to the staged typestate design shown in
   the code examples, splitting the class into one type per state.
4. **Migrate callers gradually behind the old surface.** Keep the
   original, guarded members in place, but change their implementation
   to delegate to the new atomic or staged form internally, so existing
   callers keep compiling while new call sites are written against the
   safer surface. This is the same additive, non-breaking migration
   shape used whenever a public contract needs to change under active
   callers.
5. **Retire the old surface deliberately.** Once telemetry, a
   deprecation window, or a code search confirms no caller still depends
   on the raw, individually callable transition members, remove them in
   the same change that removes the internal delegation, rather than
   leaving unused, deprecated methods behind indefinitely, which is
   exactly how a half-finished version of this refactoring produces a
   Boat Anchor.

## 15. Testing and verification

Sequential Coupling makes some things about testing measurably harder and
a smaller number of things measurably easier, and naming both honestly is
more useful than treating the pattern as purely a testing liability.

Harder because of the defect.

- Every test that exercises a dependent member must first arrange the
  object into the correct prior state by calling the transition members
  in order, which couples the test suite to the same undocumented
  protocol that production callers are exposed to, so a change to the
  protocol breaks tests in the same silent way it breaks production
  code.
- A test written against the unguarded variant from dimension 8 cannot
  distinguish a correct result from an accidentally-correct result
  produced by reading a default value, because nothing in the object's
  behavior signals the difference.
- Concurrency-related corruption, described in dimension 11, is
  characteristically invisible to a single-threaded test suite, so its
  absence from the test suite says nothing about its absence in
  production.

Easier, or at least directly testable, once the defect is guarded or
fixed.

- Once every dependent member carries an explicit guard, the guard
  itself becomes a trivially testable unit, one test per member
  asserting that calling it before its precondition throws the expected,
  specifically worded exception.
- Once the object is converted to a staged typestate, whether a given
  call sequence is even expressible becomes a compile-time property, so
  an entire category of tests that previously existed to catch
  out-of-order calls becomes unnecessary, replaced by the type checker
  running on every build.

Techniques that apply specifically to this defect.

- **Precondition test per dependent member.** For every method
  identified as a dependent member in the object's participant list from
  dimension 5, write one test that calls it before the required
  transition member and asserts the specific, named exception, not
  merely that some exception was thrown.
- **State-transition table test.** Where an explicit
  finite-state-machine field or a State pattern implementation exists,
  per dimension 8 and dimension 13, write a single parameterized test
  driven by the transition table itself, asserting for every state and
  every member whether the call is expected to succeed or fail, rather
  than one bespoke test per combination written by hand.
- **Constructor-only test for the atomic form.** Once a class has been
  converted to atomic, immutable construction, the corresponding test
  suite shrinks to asserting that construction with valid inputs
  produces a fully correct object and that construction with invalid
  inputs fails at the constructor, with no further tests needed for
  order, because no further order exists.
- **Compile-fail test for the typestate form.** Where the host language
  and test tooling support it, a dedicated compile-fail test, asserting
  that a specific invalid sequence does not type-check, documents the
  intended protection directly and catches a future refactor that
  accidentally reintroduces a shared type across two states that were
  meant to stay distinct.

## 16. Observability signals

The defect itself produces very little to observe when things go well,
which is part of the danger, so the signals worth collecting are almost
entirely about the failure paths and the near-misses that precede them.

What to record.

- A counter of guard-triggered exceptions, labeled by the specific
  dependent member and, where feasible, by the calling code path or
  service, so a spike in one label localizes both which precondition is
  being violated and by whom.
- For the unguarded variant, if it cannot be converted to the guarded
  form immediately, an explicit log line or metric recorded at the point
  where a dependent member reads its implicit state, noting whether the
  state was present or was a default, since this is the only way to
  make a silent failure visible in production without changing its
  behavior.
- For the resource-scope wrapper variant, a gauge of currently-open
  scopes and a counter of scopes entered versus scopes exited cleanly,
  which together reveal a resource leak, the failure mode from
  dimension 11, well before the underlying operating system limit is
  hit.
- For any object shared across more than one caller, a counter of
  transition-member calls per instance, since an instance whose
  transition member is called more times than expected is the earliest
  observable sign of the concurrency race described in dimension 11,
  before any corrupted result has surfaced.

A healthy instance on a dashboard shows guard-triggered exceptions at or
near zero, and any nonzero baseline explained by a known, accepted caller
rather than growing silently over time. Scope-entered and scope-exited
counters track each other closely with a small, bounded, explainable gap
rather than diverging.

A failing instance shows one of two shapes. Either the guard-exception
counter for one specific dependent member climbs after a deployment,
which usually means a new caller was written against the raw protocol
without discovering the required order, or the open-scope gauge climbs
without a matching rise in the exited counter, which is the resource
leak in progress, both localizable from telemetry alone before a person
reads any application code.

## 17. Security and privacy implications

The defect is not itself a primary security mechanism failure, but it
opens one concrete attack path and touches one operational risk worth
stating precisely rather than inventing a broader concern that is not
actually there.

**Denial of service through forced re-initialization or repeated setup.**
Where the transition member performs real, costly work, opening a
connection, allocating memory, performing a cryptographic handshake, and
the class does not guard against it being called repeatedly, an attacker
or a buggy client who can trigger the transition call in a loop can
force the server to repeat that expensive work far more often than a
correct protocol would ever require, turning a normal request into a
resource-exhaustion vector. This is the same mechanism as the
repeated-call failure mode in dimension 7, with an adversarial actor in
place of an accidental one. The fix from dimension 8, guarding
transition members against a second call in addition to guarding
dependent members against an early one, closes this specific path.

**Security-relevant state left partially applied.** Where the sequence
being coordinated includes a security-relevant step, authentication
before authorization, or input validation before use, an object that
allows a dependent member to be called before its transition member has
run risks letting a caller reach the sensitive operation with the
security check silently skipped rather than explicitly bypassed, which
is more dangerous than an outright missing check because it looks, from
the caller's perspective, like the check ran. This is a strong argument,
independent of the general design forces in dimension 3, for guarding
rather than leaving unguarded any sequential coupling where one of the
steps is security-relevant, and for preferring the atomic construction
fix from dimension 8 wherever the security-relevant step can be made
mandatory at construction rather than left as a separately callable step
at all.

The pattern has no direct privacy implication of its own. Where the
implicit state being tracked happens to include personal data, a session
token, a user identifier captured during the setup step, the privacy
obligations that apply are the ordinary ones that apply to any field
holding that kind of data, and this entry does not add anything specific
to sequential coupling on top of them.

## Code examples

Three languages, chosen to show three distinct points on the path from
the raw defect to its strongest available fix, rather than three
restatements of the same idea. TypeScript shows the raw, unguarded and
guarded defect directly, including the fact that it type-checks cleanly
despite being wrong, which is the entire point of the anti-pattern. Go
shows the resource-scope callback fix, idiomatic to the language's
`defer` mechanism and to its wider preference for functions that take a
callback over methods that must be called in a fixed order by the
caller. Rust shows the strongest fix, a typestate built from ownership,
where an invalid sequence is rejected by the compiler rather than by a
runtime check. Java is deliberately omitted from the code examples
despite supplying two of the sourced production uses in dimension 9,
because no local Java toolchain was available in the session that wrote
this entry, a fact recorded here rather than silently assumed, and
because the classical Java shape, a boolean flag guarded by a thrown
exception, is already fully described in plain language in dimension 8
and directly evidenced by the cited Thread and ResultSet sources.

### TypeScript

The defect first. This compiles without error even though the last line
is wrong at run time, which is the anti-pattern's entire mechanism.

```typescript
class RawConnection {
  private open = false;

  constructor(private readonly addr: string) {}

  connect(): void {
    this.open = true;
  }

  send(message: string): void {
    if (!this.open) {
      throw new Error(
        `send called before connect on ${this.addr}, sequential coupling violated`
      );
    }
    console.log(`sent ${message} to ${this.addr}`);
  }

  close(): void {
    this.open = false;
  }
}

// This entire block type-checks. The mistake is only visible at run time.
const raw = new RawConnection("localhost:9000");
raw.send("too early");
```

Now the staged, typestate fix. Each state is its own class, so a method
that would be invalid in the current state does not exist on the current
type at all, and calling it is a compile error rather than a thrown
exception.

```typescript
class DisconnectedConnection {
  constructor(private readonly addr: string) {}

  connect(): ConnectedConnection {
    return new ConnectedConnection(this.addr);
  }
}

class ConnectedConnection {
  constructor(private readonly addr: string) {}

  send(message: string): void {
    console.log(`sent ${message} to ${this.addr}`);
  }

  close(): DisconnectedConnection {
    return new DisconnectedConnection(this.addr);
  }
}

const staged = new DisconnectedConnection("localhost:9000");
const connected = staged.connect();
connected.send("hello");
// staged.send("too early");
// TypeScript rejects this line at compile time, "Property 'send' does
// not exist on type 'DisconnectedConnection'."
```

### Go

The resource-scope fix, idiomatic to Go. `WithConnection` owns the
entire lifecycle and uses `defer` to guarantee the close step runs, so
the raw transition members are never called directly by application
code at all.

```go
package main

import (
	"errors"
	"fmt"
)

// RawConnection still exposes the raw, individually callable protocol,
// guarded so a violation fails loudly rather than silently.
type RawConnection struct {
	addr string
	open bool
}

func NewRawConnection(addr string) *RawConnection {
	return &RawConnection{addr: addr}
}

func (c *RawConnection) Open() error {
	if c.open {
		return errors.New("open called twice, sequential coupling violated")
	}
	c.open = true
	return nil
}

func (c *RawConnection) Send(message string) error {
	if !c.open {
		return errors.New("send called before open, sequential coupling violated")
	}
	fmt.Printf("sent %q to %s\n", message, c.addr)
	return nil
}

func (c *RawConnection) Close() error {
	c.open = false
	return nil
}

// WithConnection is the fix. It owns Open and Close so a caller never
// gets the chance to call Send out of order.
func WithConnection(addr string, use func(*RawConnection) error) error {
	c := NewRawConnection(addr)
	if err := c.Open(); err != nil {
		return err
	}
	defer c.Close()
	return use(c)
}

func main() {
	err := WithConnection("localhost:9000", func(c *RawConnection) error {
		return c.Send("hello")
	})
	if err != nil {
		fmt.Println("error", err)
	}
}
```

### Rust

The strongest fix. A phantom-typed state parameter, combined with
methods that consume `self` by value, means the compiler rejects an
invalid call sequence rather than the runtime detecting one. Once
`close` runs, the value it consumed no longer exists, so a later call to
`send` on it is a compile error, not a bug that surfaces later.

```rust
use std::marker::PhantomData;

struct Unopened;
struct Opened;

struct Connection<State> {
    addr: String,
    _state: PhantomData<State>,
}

impl Connection<Unopened> {
    fn new(addr: &str) -> Self {
        Connection {
            addr: addr.to_string(),
            _state: PhantomData,
        }
    }

    fn open(self) -> Connection<Opened> {
        println!("opening {}", self.addr);
        Connection {
            addr: self.addr,
            _state: PhantomData,
        }
    }
}

impl Connection<Opened> {
    fn send(&self, message: &str) {
        println!("sent {:?} to {}", message, self.addr);
    }

    fn close(self) {
        println!("closing {}", self.addr);
    }
}

fn main() {
    let conn = Connection::<Unopened>::new("localhost:9000");
    let conn = conn.open();
    conn.send("hello");
    conn.close();
    // conn.send("too late");
    // Rust rejects this line at compile time, `conn` was moved by the
    // preceding call to close(), so it can no longer be used.
}
```

## 18. References

1. Mark Seemann. "Design Smell. Temporal Coupling". ploeh blog, 24 May
   2011. https://blog.ploeh.dk/2011/05/24/DesignSmellTemporalCoupling/
   Verified 2026-08-02. Source of the definition quoted in dimension 1
   and the `Initialize`/`Spread` example referenced throughout.
2. connascence.io. "Connascence of Execution".
   https://connascence.io/execution.html Verified 2026-08-02. Source of
   the Page-Jones connascence classification of the same defect, and of
   the `Email`/`setSubject`/`send` example cited in dimension 1.
3. Wikipedia contributors. "Connascent software components".
   https://en.wikipedia.org/wiki/Connascent_software_components Verified
   2026-08-02. Source for Meilir Page-Jones as the originator of the
   connascence taxonomy and the citation to *Practical Guide to
   Structured Systems Design*, second edition, 1988.
4. Wikipedia contributors. "Cohesion (computer science)".
   https://en.wikipedia.org/wiki/Cohesion_(computer_science) Verified
   2026-08-02. Source for the Constantine and Yourdon origin of the
   cohesion taxonomy and for the definition of sequential cohesion used
   in the disambiguation in dimension 1.
5. Wikipedia contributors. "Coupling (computer programming)".
   https://en.wikipedia.org/wiki/Coupling_(computer_programming) Verified
   2026-08-02. Source for the classic, distinct definition of temporal
   coupling as bundling unrelated actions that happen to occur at the
   same time, cited in dimension 1 to show the name is separately
   overloaded.
6. Martin Fowler, with Eric Evans. "FluentInterface". martinfowler.com
   bliki, updated 2008. https://www.martinfowler.com/bliki/FluentInterface.html
   Verified 2026-08-02. Background source on fluent, chained method
   interfaces informing the staged-builder discussion in dimensions 8
   and 13.
7. Oracle. *Java SE 21 API Specification*, `java.lang.Thread`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html
   Verified 2026-08-02. Source for the `Thread.start()` production use
   in dimension 9.
8. Oracle. *Java SE 21 API Specification*, `java.sql.ResultSet`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.sql/java/sql/ResultSet.html
   Verified 2026-08-02. Source for the `ResultSet` cursor and `next()`
   production use in dimension 9.
9. Microsoft. *.NET API documentation*,
   `SqlConnection.Open` (`System.Data.SqlClient`).
   https://learn.microsoft.com/en-us/dotnet/api/system.data.sqlclient.sqlconnection.open
   Verified 2026-08-02. Source for the ADO.NET production use in
   dimension 9.
10. The Go Authors. *Go package documentation*, `bufio`, `Scanner`.
    https://pkg.go.dev/bufio#Scanner Verified 2026-08-02. Source for the
    `bufio.Scanner` production use in dimension 9, presented as an
    accepted convention rather than an instance of the defect, per
    dimension 4.
11. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design
    Patterns. Elements of Reusable Object-Oriented Software*.
    Addison-Wesley, 1994. ISBN 0-201-63361-2. Behavioral Patterns
    chapter, State. Source for the State pattern relationship discussed
    in dimension 13.
