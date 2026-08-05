---
name: Middle Man
slug: middle-man
family: 02-code-smells
category: Code Smell
aliases: [Excessive Delegation, Delegation Overload]
first_described: "Fowler, Beck 1999"
maturity: canonical
related: [feature-envy, facade, proxy, decorator, law-of-demeter, hide-delegate]
incompatible_with: []
verified: 2026-08-02
---

# Middle Man

## 1. Name, aliases, and lineage

The canonical name is Middle Man. It is catalogued as a code smell in Martin
Fowler, *Refactoring. Improving the Design of Existing Code*, Addison-Wesley,
1st edition 1999, in the smells chapter co-written with Kent Beck, and it
survives unchanged into the 2nd edition, Addison-Wesley, 2018. The book's own
online catalog, maintained by Fowler at refactoring.com, lists the cure for
this smell under the name Remove Middle Man, and states plainly that Remove
Middle Man is "the inverse of Hide Delegate"
(https://refactoring.com/catalog/removeMiddleMan.html, verified 2026-08-02).
That inverse relationship is the whole shape of the smell in one sentence. Hide
Delegate is the refactoring that introduces a forwarding method so a caller
does not have to reach through one object to get to another. Middle Man is what
you get when that forwarding is applied past the point where it earns its
keep, so that a class exists mostly to receive calls it does nothing with
except pass them along.

There is no second name for this smell in wide circulation the way there is
for, say, God Object or Shotgun Surgery. Practitioners sometimes say "pure
delegator," "pass-through class," or "delegation overload" in conversation,
but none of those is a term of art with its own catalog entry. This entry uses
Middle Man as the header and treats the others as descriptive synonyms rather
than aliases with independent lineage.

It is worth being precise about what Middle Man is not, because the pattern
literature has a structurally similar shape that is not a smell at all. The
Gang of Four Proxy pattern, described in Erich Gamma, Richard Helm, Ralph
Johnson, John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 4, Structural
Patterns, Proxy, is also a class whose job is largely to forward calls to
another object. The difference is intent and payload. A Proxy forwards because
forwarding is the entire point, controlling access, deferring construction,
or crossing a process boundary, and the class is explicit about carrying no
other responsibility. A Middle Man forwards because delegation was added
piecemeal to a class that was originally supposed to do something else, and
the forwarding crowded out the original job until nothing else was left. The
code can look identical. The diagnosis depends on why the class exists, not
on what its methods contain.

## 2. Problem and context

The smell shows up during evolution, almost never at the moment a class is
first written. A class starts with a narrow, legitimate reason to hold a
reference to a collaborator, an `Order` holds a `Customer`, a `Controller`
holds a `Service`, a `Repository` holds a database `Connection`. Early on the
holder exposes one or two of the collaborator's operations because callers
genuinely need them and reaching for the collaborator directly would leak an
implementation detail the holder is supposed to own. That first forwarding
method is Hide Delegate working exactly as intended, and it is good design.

The smell accretes one method at a time. A caller needs a third operation from
the collaborator. Rather than exposing the collaborator itself, which would
mean admitting the holder is not really encapsulating anything, a developer
adds another forwarding method with the same shape as the first two. This
repeats. Six months later the holder class has thirty public methods, and
twenty-two of them are one line long, `return this.collaborator.someMethod()`
possibly with argument reshuffling and nothing else. The holder still compiles
correctly, still passes its tests, and still looks, from the outside, like a
normal class with a normal API. The rot is invisible from the caller's side,
because every call succeeds. It is visible only when someone opens the holder
class and asks what it actually does, and finds the honest answer is nothing,
it hands the call to somebody else.

The context that produces this reliably is a layered architecture where a
team has been taught, correctly, that direct access to an inner layer from
an outer layer is bad, but has not been taught where that rule stops
applying. A Controller is told never to touch a Repository directly, so every
Repository method a Controller might conceivably need gets mirrored onto a
Service, even the read-only, side-effect-free ones that carry no business
rule and would be perfectly safe to call directly. A DTO gets extended, field
by field, until it duplicates its source entity's entire public surface. A
facade written for one bounded purpose is asked, feature by feature, to
front an entire subsystem, and each new front-door method is a forward with
nothing behind it but the call itself.

## 3. Forces

Encapsulation pulls toward hiding the collaborator, because exposing it lets
every caller couple directly to the collaborator's shape, and a later change
to that shape now breaks every caller instead of one holder class. This is
the force that legitimately justifies the first few forwarding methods.

Indirection cost pulls the opposite direction. Every layer of forwarding is a
frame the reader has to hold, a step the debugger has to step through, and a
place a stack trace gets longer without adding information. Indirection is
not free even when it is correct, and a reader who wants to understand one
behavior now has to open two files instead of one, then three, then four, as
delegation chains stack. Fowler and Beck's own smells chapter treats a class
delegating "more than half its work" as the informal threshold worth a second
look, engineering judgement rather than a fixed rule, and this entry follows
that same informal threshold in dimension 4 below.

Change amplification is the third force. When a collaborator's interface
grows by one method, and the holder's stated job is to hide the collaborator,
the holder's interface must grow by one method too, in lockstep, forever.
This is a maintenance tax that never shrinks, because the coupling the
forwarding was meant to avoid, a caller depending on the collaborator's
shape, has actually just been relocated one level up, to the holder now
depending on the collaborator's shape on the caller's behalf. The tax is paid
by whoever edits the holder class, and it grows with the size of the
collaborator's interface regardless of how many forwarding methods any given
caller actually uses.

Testability and mocking pull toward keeping the layer, in one specific
circumstance. When the collaborator is expensive to construct, crosses a
process boundary, or is a third-party dependency the codebase does not
control, a thin holder that owns nothing but a reference to it is exactly the
seam a test double replaces. This is the force that Proxy, Adapter, and Facade
lean on legitimately, and it is the reason Middle Man is diagnosed by
looking at why a class exists, never by counting its one-line methods in
isolation.

## 4. Applicability and non-applicability

Diagnose Middle Man when most of these hold at once.

- A large fraction of a class's public methods, as a rule of thumb more than
  half, do nothing but call a single collaborator's method with the same or
  near-identical arguments and return its result unmodified.
- The class holds exactly one, or a very small fixed number, of collaborator
  references, and adds a forwarding method every time a caller needs a new
  operation from that collaborator, rather than exposing the collaborator or
  reconsidering the boundary.
- Removing the class and letting callers hold the collaborator directly would
  not violate any invariant, because the class enforces no rule, aggregates
  no state, and performs no transformation of its own on the forwarded calls.
- Readers routinely have to open the collaborator's source to understand what
  a call to the holder actually does, because the holder's method body
  carries no information beyond the method name.
- The class was not designed from the outset as a boundary object, a Proxy,
  Adapter, or Facade with a stated architectural purpose, but grew into this
  shape incrementally as forwarding methods accumulated.

Do not diagnose Middle Man, and do not apply Remove Middle Man, when any of
these hold.

- The class is a Proxy by design, and the entire point of its existence is to
  intercept and forward calls, adding lazy loading, access control, caching,
  or a network hop transparently. Removing the proxy would remove the
  behavior it exists to provide, not merely an indirection. Gamma et al. 1994,
  chapter 4, Proxy, states the intent as controlling access to an object by
  providing a surrogate or placeholder for it.
- The class is a stable public API surface, a library entry point or a
  versioned interface, whose forwarding insulates external consumers from
  internal refactors. Removing the forward would break a contract the class
  exists specifically to keep stable, even though the internals behind it may
  change freely.
- The forwarding methods each add a small but real transformation, argument
  validation, unit conversion, error translation, or logging, even if that
  transformation is only a few lines. A method that is not a pure pass-through
  is not a Middle Man method, however thin it looks.
- The collaborator genuinely must stay hidden for encapsulation reasons that
  outweigh the indirection cost, for example because the collaborator's type
  is an internal implementation detail that would leak a persistence or
  vendor dependency into a public contract if exposed directly.
- The forwarding class is a deliberate anti-corruption layer or adapter at a
  bounded-context boundary, where the cost of indirection is intentionally
  paid to keep two models from bleeding into each other. See Eric Evans,
  *Domain-Driven Design. Tackling Complexity in the Heart of Software*,
  Addison-Wesley, 2003, chapter 14, on the Anticorruption Layer, which is
  structurally a forwarding layer whose entire justification is the
  translation it performs at the boundary.
- The class is small, stable, and rarely touched. The cost of a Middle Man is
  proportional to how often the class must be edited to keep up with its
  collaborator and how often a reader has to trace through it. A three-method
  forwarder that has not changed in two years is not worth the churn of a
  refactor whose only benefit is a shorter chain.

## 5. Structure

A Middle Man situation involves three participants.

- **The Client.** The code that wants a behavior. It calls the Middle Man
  because that is the object it was handed, not because it has any interest
  in the Middle Man's own state.
- **The Middle Man.** The class under suspicion. It holds a reference to the
  Real Object and exposes a set of methods, most of which have a body that
  does nothing but invoke the corresponding method on the Real Object and
  return the result, with little or no logic of its own.
- **The Real Object.** The collaborator that actually performs the work. It
  is the object the Middle Man was originally meant to hide, and it is the
  object the Client would call directly if the Middle Man did not exist.

The relationship is a delegation edge from Middle Man to Real Object, and a
dependency edge from Client to Middle Man. The smell is present when the
second edge carries no more information than the first, meaning the Client
gains nothing from routing through the Middle Man that it would not gain by
depending on the Real Object directly, apart from whatever the small residue
of genuinely non-trivial methods on the Middle Man still provides.

## 6. ASCII structure diagram

```
    BEFORE (Middle Man present)

    +----------+        +------------+        +-------------+
    |  Client  |------->| Middle Man |------->| Real Object  |
    +----------+        +------------+        +-------------+
                         | + opA()   |-------->| + opA()     |
                         | + opB()   |-------->| + opB()     |
                         | + opC()   |-------->| + opC()     |
                         | + opD()   |-------->| + opD()     |
                         +------------+        +-------------+
                         every method forwards, none transforms


    AFTER (Remove Middle Man applied)

    +----------+                                +-------------+
    |  Client  |------------------------------->| Real Object  |
    +----------+                                +-------------+
                                                  | + opA()     |
                                                  | + opB()     |
                                                  | + opC()     |
                                                  | + opD()     |
                                                  +-------------+
    Client now holds Real Object directly, Middle Man class deleted
```

## 7. Dynamics

The runtime call path is the same shape whether the design is healthy or
smelly, which is exactly why the smell is invisible from a stack trace alone
and must be diagnosed by reading the class, not by profiling it.

```
    Client.doWork()
        |
        v
    MiddleMan.opA(args)
        |  no branching, no state mutation, no transformation
        v
    RealObject.opA(args)
        |
        v
    result computed, invariants checked, side effects performed here
        |
        v
    return result  ---> back up through MiddleMan unchanged ---> Client
```

The dynamics that matter are not per-call, they are per-change. Trace what
happens when the Real Object's interface grows by one method that a Client
now needs.

```
    Time T0, RealObject.opE() added
        |
        v
    Time T1, a Client needs opE()
        |
        v
    Time T2, MiddleMan.opE() is added, forwarding to RealObject.opE()
        |     (this edit touches a file that adds zero new behavior)
        v
    Time T3, Client calls MiddleMan.opE()
        |
        v
    Time T4, MiddleMan.opE() calls RealObject.opE()
        |
        v
    result returns unchanged through two frames instead of one
```

Every iteration of this loop is a wasted edit, a wasted code review, and a
wasted stack frame, repeated for the lifetime of the collaboration. This is
the concrete mechanism behind the change amplification force from dimension
3, and it is why the smell is diagnosed longitudinally, by watching how a
class's edit history looks over months, as much as it is diagnosed by
reading a single snapshot of the code.

## 8. Implementation variants

**The accidental accumulator.** The most common shape, described in dimension
2. No one decided to build a Middle Man. A holder class gained one forwarding
method per caller need, over an extended period, until forwarding became its
majority behavior. Diagnosed by reading the class's git history one commit at
a time and noticing a long run of commits whose diff is a single new
one-line method with the same shape as the last one.

**The defensive wrapper that never earned its keep.** A team introduces a
thin wrapper around a third-party library up front, anticipating that the
library might be swapped later, and forwards every method the library
exposes that the codebase currently uses. If the swap never happens and the
wrapper never grows any translation logic, it sits as a permanent, unpaid-for
indirection. This variant differs from the accidental accumulator only in
timing, the forwarding was all added at once instead of incrementally, but
the diagnosis and cure are identical.

**The over-grown facade.** A Facade, Gamma et al. 1994, chapter 4, Facade, is
introduced correctly to simplify a complex subsystem's interface for one
specific use case. Over time, unrelated callers with different use cases are
told to route through the same facade rather than talk to the subsystem
directly, and the facade's interface is grown to match, method by method,
until it has become a full mirror of the subsystem with no simplification
left in it. The original Facade intent, presenting a narrower interface than
the subsystem, is gone, and what remains is a Middle Man that happens to be
named Facade in the codebase.

**The DTO that grew getters for its source entity.** A data transfer object,
built to cross a serialization boundary with a deliberately small, flat
shape, is extended field by field, and then method by method, to mirror an
entity's full public interface including behavior the entity exposes, not
just its data. The DTO stops being a data carrier and becomes a Middle Man
in front of the entity it was supposed to summarize.

**The generated stub with hand-added forwards.** Code generation tools, RPC
stub generators being the clearest example, deliberately produce
pass-through classes, and this is not a smell, it is the tool's stated job,
see dimension 9 for Java RMI. The variant to watch for is when a developer
opens a generated stub and hand-adds forwarding methods to it for
convenience, mixing generated Proxy code with hand-maintained Middle Man code
in the same file, which makes the next regeneration either overwrite the
hand-added methods or require a manual merge.

## 9. Known production uses

**Java RMI client stubs**, the classic and intentionally healthy instance of
this exact structural shape. The Java RMI tutorial documents that
`UnicastRemoteObject.exportObject` "exports the supplied remote object to
receive incoming remote method invocations on an anonymous TCP port and
returns the stub for the remote object to pass to clients," and that the
client-side stub serializes each call and opens a connection to the server
using the host and port information embedded in the stub
(https://docs.oracle.com/javase/8/docs/technotes/guides/rmi/hello/hello-world.html,
verified 2026-08-02). The stub's every method exists only to forward a call
across the network. It is not a smell, because the forwarding is the entire
declared job, the marshaling and network hop are the value, and no one
mistakes the stub for a class with independent business logic. This is
included precisely because it sits at the boundary the smell is defined
against, a pure forwarder that is correct because it is a Proxy, not an
accumulated Middle Man.

**Ruby's `Forwardable` module in the standard library**, which exists to make
delegation an explicit, single-line declaration rather than a manually
hand-written pass-through method, and by doing so documents the smell it is
designed to prevent from becoming invisible. The Ruby documentation states
that "the Forwardable module provides delegation of specified methods to a
designated object, using the methods `def_delegator` and `def_delegators`"
(https://docs.ruby-lang.org/en/3.3/Forwardable.html, verified 2026-08-02).
The module's own stated purpose is to serve "as an alternative to
inheritance" for selective method forwarding, which is a tacit acknowledgment
that hand-rolled forwarding classes are common enough in Ruby practice to
need a standard-library shortcut, and that the shortcut is meant for the
handful of deliberate delegations, not for growing an entire mirrored
interface.

**Enterprise JavaBeans remote and local business interfaces**, widely
criticized in the early 2000s Java community as an architecture that forced
every remote-callable method to be duplicated across a home interface, a
remote interface, and a bean implementation, with generated or hand-written
delegation gluing the layers together. Rod Johnson's *Expert One-on-One J2EE
Design and Development*, Wrox Press, 2002, chapters critiquing the EJB
component model, argues at length that the mandatory home and remote
interface layers of EJB 2.x forced boilerplate forwarding that added no value
for the large majority of local, same-JVM calls that never needed network
transparency, a critique that directly named this indirection tax and helped
drive the industry toward the lighter Spring and, later, EJB 3.x local
interface model that removed the mandatory forwarding layer for local calls.
This is a case where the industry itself diagnosed a widespread Middle Man
pattern at framework scale and refactored the standard to remove it.

**The `Object.assign` and spread-based flattening idiom in modern
JavaScript** is a direct, tooling-level response to the DTO variant of
Middle Man described in dimension 8. Rather than writing a wrapper class
with one getter per source field, the idiom `const dto = { ...entity }` or
`Object.assign({}, entity)` spreads an object's own enumerable properties
directly, which the MDN Web Docs reference for `Object.assign()` describes as
copying "the values of all enumerable own properties from one or more source
objects to a target object"
(https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/assign,
verified 2026-08-02). The idiom's popularity is evidence that the language
community treats a hand-written, per-field forwarding wrapper as
unnecessary overhead for the common case of copying data across a boundary,
which is the same judgement dimension 4's non-applicability list makes for
genuine transformation but the community makes by default for the pure copy
case.

## 10. Consequences

Positive.

- None, when the class is genuinely a diagnosed Middle Man rather than a
  Proxy, Adapter, or stable API. The smell catalog exists precisely because
  this shape offers no benefit once it has grown past the point that
  justified its first few methods.
- The class does provide a small, real benefit in the narrow window before it
  becomes a Middle Man, while it still hides a genuinely volatile
  collaborator shape from callers, per dimension 3's encapsulation force.
  That benefit is what makes the smell hard to see coming, the first ten
  forwarding methods were correct, and nothing marks the moment the eleventh
  crosses into waste.

Negative.

- Every new capability on the Real Object requires a matching, mechanical
  edit to the Middle Man before any Client can use it, doubling the number
  of files touched and code reviews needed for what is, in the Real Object,
  a single change.
- Stack traces grow one frame longer per hop for no diagnostic benefit,
  making debugging sessions slower and log correlation across the
  indirection harder, particularly in async or callback-heavy code where an
  extra frame can also mean an extra scheduling boundary.
- Readers new to the codebase spend real time opening the Middle Man,
  finding a one-line forward, then opening the Real Object to find the
  actual logic, a two-hop reading tax repeated for every unfamiliar method,
  which is a direct cost against onboarding time.
- Test doubles proliferate. A test that wants to stub the Real Object's
  behavior often has to stub it through the Middle Man's interface instead,
  and if the Middle Man's forwarding methods drift even slightly from the
  Real Object's signatures, the test double and the production forward can
  silently diverge.
- The Middle Man becomes a magnet for further degradation, because once a
  class is known to forward everything, the path of least resistance for the
  next developer who needs a new operation is to add one more forward rather
  than question whether the layer should exist, which is exactly the
  incremental mechanism from dimension 2.

## 11. Failure modes and misuse

Symptom. A code review repeatedly approves single-line pull requests that
add one method to a class, and the reviewer notices, only after the fact,
that this has happened dozens of times across many months to the same class.
Cause. No one owns the question of whether the forwarding class should
still exist, because each individual addition looks trivially correct in
isolation and the reviewer is evaluating the diff, not the class's
cumulative shape. Fix. Track the ratio of forwarding methods to total
methods on hot classes, per dimension 16, and flag a class for a design
review when that ratio crosses a threshold rather than reviewing each
addition alone.

Symptom. Removing the Middle Man class breaks compilation in far more
call sites than expected, revealing that Clients had been calling the
Middle Man with slightly different argument shapes than the Real Object
actually requires, because someone had, at some point, reordered or renamed
parameters on the forwarding method without updating every Client.
Cause. The Middle Man's interface had silently drifted from the Real
Object's interface, so "just forward" was no longer literally true, and the
forwarding methods had accumulated a small amount of genuine translation
logic mixed in with the pure forwards, without anyone noticing the class was
no longer a clean case for Remove Middle Man. Fix. Before applying Remove
Middle Man, diff every forwarding method's signature against its target
method's signature and separate the pure forwards, safe to remove, from the
methods that do real argument or return-value transformation, which should
be kept and possibly moved onto the Real Object as an overload or a small
adapter instead of deleted.

Symptom. After Remove Middle Man is applied, an unrelated part of the
system, previously insulated from the Real Object's type, starts failing to
compile or, in a dynamically typed language, starts throwing at runtime,
because it had been relying on the Middle Man's interface staying stable
while the Real Object's interface changed underneath it. Cause. The
Middle Man was not, in fact, a pure Middle Man for every caller, it was
serving a genuine stability role for a subset of callers even while it was
pure dead weight for the rest, and the refactor was applied uniformly
without checking every caller's actual dependency. Fix. Apply dimension
14's refactoring path caller by caller rather than deleting the Middle Man
wholesale, keeping the forwarding interface alive, even as a thin remaining
shim, for the callers that genuinely need the stability, while routing the
majority of callers directly to the Real Object.

Symptom. A team, having been taught to distrust delegation after a bad
experience with an over-grown Middle Man, starts flattening every layered
architecture into direct calls, and six months later discovers that a
genuine architectural boundary, an anti-corruption layer or a public API
surface, has been removed along with the accidental ones, and an internal
model change now breaks external consumers directly. Cause. Overcorrection.
Middle Man is diagnosed per dimension 4 by asking whether the forwarding
class does real work, not by counting how many of its methods are one line
long, and a blanket policy against thin classes destroys the legitimate
cases alongside the accidental ones. Fix. Keep dimension 4's
non-applicability list as an explicit checklist during any Middle Man
cleanup pass, and require a one-sentence justification for keeping each
forwarding class that survives the pass, so the decision is recorded rather
than defaulted.

## 12. Trade-off matrix

Compared against Facade, Proxy, and direct access with no intermediary at
all, across the forces from dimension 3.

| Force | Middle Man (uncured) | Facade (bounded, deliberate) | Proxy (bounded, deliberate) | Direct access, no layer |
|---|---|---|---|---|
| Encapsulation of collaborator shape | High, but not earning its keep | High, for its declared subsystem scope | High, and the point of the pattern | None |
| Indirection cost per call | One wasted frame, no added value | One frame, justified by the simplification it buys | One frame, justified by what the proxy adds | Zero |
| Change amplification when collaborator grows | Every new operation forces a matching edit | Only operations the facade's stated scope covers force an edit | Only operations the proxy's stated scope covers force an edit | None, callers see changes directly |
| Coupling if collaborator's shape changes | Every caller of the Middle Man is shielded, but the Middle Man itself must change in lockstep | Callers of the facade are shielded for the facade's declared scope | Callers of the proxy are shielded, by design | Every caller is directly coupled |
| Debuggability, stack depth | Worse, extra frame with no diagnostic content | Slightly worse, but the frame corresponds to a real simplification | Slightly worse, but the frame corresponds to the proxy's real work, caching, access control, network | Best, shortest trace |
| Onboarding cost for new readers | High, readers must open two files to learn nothing new | Low, the facade's name and scope explain why it exists | Low, the proxy's name and scope explain why it exists | Lowest |
| Test seam value | Low, the seam exists but nothing is actually swapped in most codebases that reach this state | High, the facade is a natural mock boundary | High, the proxy is often the exact seam a test double needs | None, must stub the Real Object directly |

## 13. Related and incompatible patterns

Feature Envy is the mirror-image smell. Feature Envy is a method that
reaches out to another object's data and behavior so much that it should
probably live on that other object instead. Middle Man is a class that has
been made to receive so much delegated behavior that it should probably not
exist at all. The two often appear together during a refactor, removing a
Middle Man frequently exposes a Client method that, once it talks to the Real
Object directly, is revealed to be envious of the Real Object's data in a way
the Middle Man had been masking.

Facade and Proxy, both Gamma et al. 1994, chapter 4, are the two
patterns Middle Man is most often confused with, because all three classes
can look identical in source form, a class whose methods forward to another
object. The distinguishing question, covered in dimensions 1 and 4, is
whether the forwarding is the class's declared, bounded purpose, Facade and
Proxy, or an accumulated byproduct of incremental additions with no bound,
Middle Man. A class can start as a legitimate Facade and become a Middle Man
over time without anyone renaming it, which is why the diagnosis is
periodic, not one-time.

Decorator, Gamma et al. 1994, chapter 4, is structurally a forwarder too,
every Decorator method calls the wrapped component's corresponding method,
but a Decorator adds behavior before or after the forwarded call by
contract, that is its entire reason to exist. A Decorator whose every method
forwards with genuinely nothing added, no behavior before or after any call,
has degenerated into a Middle Man wearing a Decorator's structure, and the
fix is either to add the missing behavior or to remove the layer.

Hide Delegate, the refactoring documented at
https://refactoring.com/catalog/hideDelegate.html (verified 2026-08-02) as
the inverse of Remove Middle Man, is the move that creates the first,
legitimate forwarding methods this smell later grows past. The two
refactorings sit at opposite ends of the same spectrum, and the practical
skill is knowing which direction a given class currently needs to move, not
treating either refactoring as universally correct.

Law of Demeter, described by Karl Lieberherr, Ian Holland and Arthur
Riel in "Object-Oriented Programming. An Objective Sense of Style," OOPSLA
1988 Proceedings, is frequently cited as the principle that motivates Hide
Delegate in the first place, an object should only talk to its immediate
collaborators, not reach through them to their collaborators' collaborators.
Middle Man is the pathological over-application of that same principle, the
Law of Demeter says do not reach through an object, it does not say wrap
every operation of every object you hold behind a forwarding method
regardless of cost, and conflating the two is a common misreading that
produces this smell.

Anticorruption Layer, Eric Evans 2003, chapter 14, is structurally
identical to a Middle Man that translates, and is listed in dimension 4's
non-applicability list because the translation it performs at a
bounded-context boundary is the entire justification for its existence, the
cost of the indirection is intentionally accepted in exchange for keeping two
domain models from corrupting each other.

## 14. Refactoring path in and out

Introducing the corresponding, legitimate structure, Hide Delegate, into code
that lacks it.

1. Identify a caller that reaches through an owned object to call a method on
   something that object holds, for example `order.getCustomer().getName()`
   from outside the `Order` class.
2. Add a forwarding method on the owning object, `Order.getCustomerName()`,
   whose body calls the inner collaborator's method and returns the result.
3. Update the caller to use the new forwarding method instead of reaching
   through.
4. Repeat only for operations callers actually need today, not for every
   operation the inner collaborator happens to expose, which is the step
   that, skipped, starts the drift toward Middle Man.

Removing an accumulated Middle Man once diagnosed, the Remove Middle Man
refactoring, https://refactoring.com/catalog/removeMiddleMan.html (verified
2026-08-02).

1. List every public method on the suspected Middle Man class and classify
   each as a pure forward, no transformation of arguments or return value, or
   a method with genuine logic, using the check from the failure-mode section
   above, diffing signatures against the Real Object's methods.
2. For every pure forward, find every call site and change it to call the
   Real Object directly instead, which requires the Client to hold a
   reference to the Real Object, obtained either from the same place the
   Middle Man originally obtained it, or by exposing a getter for the Real
   Object on the Middle Man as a transitional step.
3. Delete each pure forwarding method from the Middle Man once its call
   sites have been migrated and the compiler, or the test suite in a
   dynamically typed language, confirms nothing still calls it.
4. For methods with genuine logic, do not delete them, either leave them on
   the now-thinner Middle Man, which may still be worth keeping for those
   methods alone, or move them onto the Real Object directly as an
   Extract Method target if the logic more naturally belongs there, and move
   the Middle Man's remaining Clients to call the Real Object with the moved
   logic applied on that side instead.
5. If, after steps 1 through 4, the Middle Man class has zero remaining
   methods and zero remaining state of its own, delete the class entirely and
   update every Client's type reference to point at the Real Object.
6. If the Middle Man class retains a handful of methods with genuine logic,
   rename it if its original name implied it was still a full forwarding
   layer, so its new, smaller scope is honestly reflected in its name and
   the next developer does not resume adding forwards to it out of habit.

## 15. Testing and verification

A pure Middle Man is, ironically, trivial to unit test and that ease is
itself a diagnostic signal worth distrusting. A test that mocks the Real
Object, calls the Middle Man's forwarding method, and asserts the mock was
invoked with the same arguments and that the Middle Man returned the mock's
return value unchanged, is testing that a delegation happened, not that any
business behavior is correct. A codebase where a large fraction of unit
tests have this exact shape, call through, assert the mock was called, assert
the return value passed through unchanged, is itself evidence pointing at
Middle Man, because there is no other behavior for the tests to exercise.

Verification that the class genuinely qualifies as a Middle Man, before
refactoring it away, should be closer to static analysis than to writing new
tests. Count each public method's cyclomatic complexity, per Thomas
McCabe's original complexity measure, "A Complexity Measure," IEEE
Transactions on Software Engineering, SE-2(4), 1976, and flag methods whose
complexity is 1, meaning no branching at all, whose body is a single call
expression, and whose parameter list and return type match a corresponding
method on a held collaborator field. A method meeting all three conditions
is a candidate pure forward and does not need its own test beyond confirming
the call happens, which most test suites already implicitly cover through
integration tests that exercise the Client's actual behavior end to end.

After applying Remove Middle Man, the safety net is regression tests at the
Client's level of behavior, not at the level of individual forwarding calls.
If the Client-facing tests, the ones that assert real user-observable
outcomes rather than mock-call assertions, still pass once the Middle Man is
gone and Clients call the Real Object directly, the refactor preserved
behavior. If those Client-facing tests were themselves written as
mock-the-Middle-Man tests, they need to be rewritten first to assert against
the Real Object or against actual behavior, because otherwise the refactor
has no meaningful test coverage protecting it at all.

## 16. Observability signals

This is engineering judgement, not a sourced claim, drawn from the same
static and structural reasoning used in dimension 15.

A healthy signal is a stable, low ratio of pure-forward methods to total
methods on any given class, tracked over the class's git history rather than
as a single snapshot, since the smell is defined by accumulation over time.
A class whose forwarding-method count has grown monotonically across many
commits, with each commit adding one method and touching no other logic, is
the clearest structural indicator, and this is checkable mechanically by a
static analysis pass that walks a class's method list, flags each method
matching the single-call-expression shape from dimension 15, and reports the
ratio alongside a trend line derived from version control history.

A failing signal in a running system, distinct from the static code shape,
shows up as call-stack depth in production traces. If distributed tracing or
in-process profiling regularly shows three, four, or more stack frames of
pure forwarding between the frame a request enters at and the frame where
real work, a database call, a computation, an I/O operation, actually
happens, that depth is directly attributable to accumulated Middle Man
layers and is measurable the same way any other latency contributor is
measured, even though each individual forward contributes negligible wall
clock time on its own. The signal to watch is not latency, which a pure
forward barely affects, it is the count of no-op frames per request, tracked
as a code health metric alongside cyclomatic complexity and file churn,
because it correlates with the maintenance and onboarding costs from
dimension 10 even when it does not correlate with runtime performance.

## 17. Security and privacy implications

Largely silent as a direct attack surface, this dimension is analytical
judgement rather than a documented vulnerability class, and this entry says
so plainly rather than inventing a concern where the smell does not create
one on its own.

The one indirect implication worth naming concerns authorization checks. In
systems where an intermediary layer is expected to enforce an access-control
decision before forwarding a call, for example a service layer that is
supposed to check a caller's permissions before delegating to a repository,
a class that has degraded into a pure Middle Man is at risk of having lost
that check silently during the incremental accumulation described in
dimension 2, because a forwarding method added quickly to satisfy a new
caller's need is easy to write as a bare pass-through and easy to review as
trivial, precisely because it looks identical to the twenty other one-line
forwards already in the file. The fix is not specific to Middle Man, it is
the general practice of keeping authorization checks in one enforced,
tested location rather than scattered across forwarding methods where a
missing check is indistinguishable, on casual review, from a correct pure
forward.

The second implication is about credential and connection scope. A Middle
Man that forwards to a Real Object holding a database connection, an
authenticated HTTP client, or any resource with an ambient credential can
end up leaking that resource's authority further than intended, simply
because exposing a new forwarding method is cheap and does not visibly
change who now has access to the underlying resource. This is a
consequence of dimension 10's change amplification force intersecting with
access control rather than a property unique to Middle Man, but it is worth
naming because the smell's incremental, low-friction growth pattern is
exactly the condition under which this kind of scope creep goes unnoticed.

## 18. References

- Martin Fowler and Kent Beck, *Refactoring. Improving the Design of
  Existing Code*, Addison-Wesley, 1st edition, 1999, and 2nd edition, 2018,
  the smells chapter, Middle Man entry.
- Martin Fowler, "Remove Middle Man,"
  https://refactoring.com/catalog/removeMiddleMan.html, verified 2026-08-02,
  states the refactoring is the inverse of Hide Delegate.
- Martin Fowler, "Hide Delegate,"
  https://refactoring.com/catalog/hideDelegate.html, verified 2026-08-02.
- Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
  Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
  1994, chapter 4, Structural Patterns, Proxy, Facade, Decorator.
- Oracle, "A Simple Client/Server Example (The Java Tutorials, RMI),"
  https://docs.oracle.com/javase/8/docs/technotes/guides/rmi/hello/hello-world.html,
  verified 2026-08-02, on client-side stub generation and forwarding.
- Ruby core documentation, "module Forwardable,"
  https://docs.ruby-lang.org/en/3.3/Forwardable.html, verified 2026-08-02.
- MDN Web Docs, "Object.assign()," verified 2026-08-02,
  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/assign
- Rod Johnson, *Expert One-on-One J2EE Design and Development*, Wrox Press,
  2002, critique of the EJB 2.x home and remote interface delegation layer.
- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, chapter 14, Anticorruption Layer.
- Karl Lieberherr, Ian Holland, Arthur Riel, "Object-Oriented Programming.
  An Objective Sense of Style," OOPSLA 1988 Proceedings, on the Law of
  Demeter.
- Thomas J. McCabe, "A Complexity Measure," IEEE Transactions on Software
  Engineering, SE-2(4), 1976, on cyclomatic complexity as used in dimension
  15's verification method.

## Code examples

The pure-forwarding shape and its cure translate cleanly across languages
with static or duck-typed member access. Three languages are shown, each
compiled or run against the local toolchain, verification noted after each
block.

### TypeScript

```typescript
// middle-man.ts

interface OrderData {
  id: string;
  total: number;
  status: string;
}

class OrderRepository {
  private readonly rows: Map<string, OrderData> = new Map();

  save(order: OrderData): void {
    this.rows.set(order.id, order);
  }

  findById(id: string): OrderData | undefined {
    return this.rows.get(id);
  }

  markShipped(id: string): void {
    const row = this.rows.get(id);
    if (row) row.status = "shipped";
  }

  totalRevenue(): number {
    let sum = 0;
    for (const row of this.rows.values()) sum += row.total;
    return sum;
  }
}

class OrderServiceMiddleMan {
  constructor(private readonly repo: OrderRepository) {}
  save(order: OrderData): void { this.repo.save(order); }
  findById(id: string): OrderData | undefined { return this.repo.findById(id); }
  markShipped(id: string): void { this.repo.markShipped(id); }
  totalRevenue(): number { return this.repo.totalRevenue(); }
}

function processShipment(repo: OrderRepository, id: string): void {
  const order = repo.findById(id);
  if (!order) throw new Error(`no order ${id}`);
  repo.markShipped(id);
}

const repo = new OrderRepository();
repo.save({ id: "o1", total: 42.5, status: "pending" });
processShipment(repo, "o1");
const after = repo.findById("o1");
if (after?.status !== "shipped") throw new Error("shipment failed");
console.log("shipped", after.status, "revenue", repo.totalRevenue());
```

Compiled and run with `npx tsc --strict --outDir /tmp/mm-ts middle-man.ts`
followed by `node /tmp/mm-ts/middle-man.js`, output `shipped shipped
revenue 42.5`.

### Python

```python
# middle_man.py

class OrderRepository:
    def __init__(self):
        self._rows = {}

    def save(self, order_id, total):
        self._rows[order_id] = {"total": total, "status": "pending"}

    def find_by_id(self, order_id):
        return self._rows.get(order_id)

    def mark_shipped(self, order_id):
        if order_id in self._rows:
            self._rows[order_id]["status"] = "shipped"

    def total_revenue(self):
        return sum(row["total"] for row in self._rows.values())


class OrderServiceMiddleMan:
    def __init__(self, repo):
        self._repo = repo

    def save(self, order_id, total):
        return self._repo.save(order_id, total)

    def find_by_id(self, order_id):
        return self._repo.find_by_id(order_id)

    def mark_shipped(self, order_id):
        return self._repo.mark_shipped(order_id)

    def total_revenue(self):
        return self._repo.total_revenue()


def process_shipment(repo, order_id):
    order = repo.find_by_id(order_id)
    if order is None:
        raise ValueError(f"no order {order_id}")
    repo.mark_shipped(order_id)


if __name__ == "__main__":
    repo = OrderRepository()
    repo.save("o1", 42.5)
    process_shipment(repo, "o1")
    after = repo.find_by_id("o1")
    assert after["status"] == "shipped"
    print("shipped", after["status"], "revenue", repo.total_revenue())
```

Run with `python3 middle_man.py`, output `shipped shipped revenue 42.5`.

### Go

```go
// middle_man.go
package main

import "fmt"

type orderData struct {
	total  float64
	status string
}

type OrderRepository struct {
	rows map[string]*orderData
}

func NewOrderRepository() *OrderRepository {
	return &OrderRepository{rows: make(map[string]*orderData)}
}

func (r *OrderRepository) Save(id string, total float64) {
	r.rows[id] = &orderData{total: total, status: "pending"}
}

func (r *OrderRepository) FindByID(id string) (*orderData, bool) {
	row, ok := r.rows[id]
	return row, ok
}

func (r *OrderRepository) MarkShipped(id string) {
	if row, ok := r.rows[id]; ok {
		row.status = "shipped"
	}
}

func (r *OrderRepository) TotalRevenue() float64 {
	sum := 0.0
	for _, row := range r.rows {
		sum += row.total
	}
	return sum
}

type OrderServiceMiddleMan struct {
	repo *OrderRepository
}

func (s *OrderServiceMiddleMan) Save(id string, total float64) {
	s.repo.Save(id, total)
}

func (s *OrderServiceMiddleMan) FindByID(id string) (*orderData, bool) {
	return s.repo.FindByID(id)
}

func (s *OrderServiceMiddleMan) MarkShipped(id string) {
	s.repo.MarkShipped(id)
}

func processShipment(repo *OrderRepository, id string) error {
	if _, ok := repo.FindByID(id); !ok {
		return fmt.Errorf("no order %s", id)
	}
	repo.MarkShipped(id)
	return nil
}

func main() {
	repo := NewOrderRepository()
	repo.Save("o1", 42.5)
	if err := processShipment(repo, "o1"); err != nil {
		panic(err)
	}
	after, _ := repo.FindByID("o1")
	if after.status != "shipped" {
		panic("shipment failed")
	}
	fmt.Println("shipped", after.status, "revenue", repo.TotalRevenue())
}
```

Run with `go run middle_man.go`, output `shipped shipped revenue 42.5`.

Java and Rust were considered and omitted from this entry. The pattern
translates directly into both, a class holding a field of the collaborator's
type with one-line forwarding methods, but the three languages above already
cover a statically typed OOP language, a dynamically typed OOP language, and
a language without classes at all, which demonstrates that Middle Man is not
tied to any single type system or object model, and a fourth or fifth
language would add no further structural insight.
