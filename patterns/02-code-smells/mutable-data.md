---
name: Mutable Data
slug: mutable-data
family: 02-code-smells
category: Change Preventers
aliases: [Shared Mutable State, Aliasing Bug, Reference Mutation]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code, second edition renamed and expanded 2018"
maturity: canonical
related: [long-method, feature-envy, primitive-obsession, data-clumps, temporary-field, divergent-change, shotgun-surgery]
incompatible_with: []
verified: 2026-08-02
---

# Mutable Data

## 1. Name, aliases, and lineage

The canonical name is Mutable Data. It appears as a named entry in Martin
Fowler's refactoring catalog, together with Kent Beck writing the second
edition's foreword and case studies, *Refactoring, Improving the Design of
Existing Code*, second edition, Addison-Wesley, 2018, inside the "Bad Smells
in Code" chapter, and on the companion catalog site, which lists Mutable
Data under a set of change-preventer style smells alongside the
refactorings Encapsulate Variable, Remove Setting Method, and Separate
Query from Modifier as the cures most commonly paired with it, source
https://refactoring.com/catalog/, verified 2026-08-02. The first edition of
the book, 1999, describes the underlying diagnosis under the heading
"Temporary Field" and inside the general discussion of Data Class, without
yet using the standalone name Mutable Data. The second edition consolidates
that discussion into its own named smell, so a reader working from the 1999
printing will not find the term used exactly this way, and a reader who wants
the modern vocabulary should reach for the 2018 edition or the catalog site.

Outside the Fowler catalog, the same underlying problem is discussed under
several other names, and this entry treats them as describing the same
phenomenon from different angles rather than as distinct patterns. The
functional programming literature calls it Shared Mutable State, emphasising
that the danger appears only once a piece of data is both mutable and
reachable from more than one place at a time. Concurrency literature calls
the specific failure mode an Aliasing Bug, where two references believed to
point at independent copies actually point at the same underlying storage,
so a write through one reference is silently observed through the other.
Joshua Bloch, *Effective Java*, third edition, Addison-Wesley, 2018, Item 17,
"Minimize mutability", frames the same concern as a design principle rather
than a smell, arguing that a class should be made immutable unless there is a
good reason to make it mutable, and lists the five rules for doing so, source
https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/, the
canonical print reference for the item, checked against the book's public
table of contents 2026-08-02. This entry treats Bloch's design rule and
Fowler's smell as two views of one underlying problem, the design rule
describing the target state and the smell describing what code looks like
before that target is reached.

## 2. Problem and context

A piece of mutable data becomes a smell the moment two conditions hold at
once. First, the data can change after it is created, through a setter, a
field assignment, a mutating method call, or a mutation performed through a
container such as an array, a list, or a dictionary. Second, more than one
part of the program holds a reference to that same data, whether directly, by
being passed the same object, or indirectly, through a shared container, a
static field, a closure, a global, a cache, or a long-lived collection that
several call sites both read and write. Mutability alone is not a problem. A
loop counter that only the loop body ever touches is mutable and harmless.
The problem appears specifically at the intersection of mutability and
sharing, because a write performed at one call site can now be observed, and
sometimes silently misinterpreted, at a completely different call site that
has no textual proximity to the write and therefore no local signal that
anything changed.

The context in which this smell most commonly appears is a long-lived object
graph, a shared cache, a configuration object passed around and edited in
place, an in-memory collection accumulated across a request or a batch job,
or the state object at the centre of a UI framework or a distributed system.
It is not limited to object-oriented code. A Go function that receives a
slice header and appends past its current length, a Python function that
receives a list and calls `.append` on it, a JavaScript function that
receives an object and assigns a new property to it, and a Rust function
that receives a `&mut` reference and writes through it are all exercising
the exact same shape of risk, the language differences only change how
loudly, if at all, the compiler warns about it. Rust is the clearest
counterexample worth naming here, because the language makes exclusive
mutable access a compile-time property rather than a runtime convention. The
Rust Book states plainly that "by default, variables are immutable" and that
"you can make them mutable by adding `mut` in front of the variable name",
and the borrow checker separately enforces that a value may have either any
number of shared, read-only references or exactly one mutable reference at a
time, never both together, source
https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html,
verified 2026-08-02. That design choice exists precisely because the
aliased-mutation problem this entry describes is common and costly enough
in C and C++ codebases to justify moving the check into the type system.

## 3. Forces

The central force is the tension between convenience of mutation, which is
cheap to write and often reads as the most direct translation of "update
this thing", against the cost of reasoning about a value whose state at any
given line of code cannot be determined from that line alone. Mutation in
place avoids allocation, avoids copying, and in a tight loop it can matter
for real performance reasons, so the temptation to mutate is not irrational,
it is a genuine engineering trade rather than a beginner's mistake dressed
up as a smell.

A second force is aliasing against ownership. A design where every mutable
value has exactly one owner responsible for changing it removes almost all
of the risk this entry describes, but establishing and preserving that
single-owner discipline by convention, without language support, is fragile
work that erodes under time pressure and staff turnover. A third force is
testability. Code that receives an immutable value and returns a new value
is trivial to test in isolation, because the assertion is simply comparing
the output to the expected value, with no need to reconstruct a sequence of
prior mutations to understand the starting state. Mutated shared state
forces a test to either reset the shared object before every test, which is
extra ceremony, or to accept order-dependent tests, which is a well known
source of intermittent test failures. A fourth force is concurrency. A value
that is never mutated after construction can be shared freely across
threads with no synchronization, while a mutable value shared across threads
needs a lock, an atomic, or some other coordination primitive, and every one
of those primitives is itself a source of deadlocks, contention, and subtle
bugs if used incorrectly.

The pattern favours predictability, testability, and safe concurrent sharing.
It sacrifices some raw allocation and copying efficiency, and it sacrifices
the surface-level directness of a plain field assignment, replacing it with
the slightly more ceremonial construction of a new value with one field
changed.

## 4. Applicability and non-applicability

Reach for eliminating mutable data, or for containing it deliberately behind
a narrow interface, when any of the following hold.

- A value is shared across more than one thread, coroutine, or async task, and correctness depends on no other party observing a half-written state.
- A value is passed into a function or a method and the caller does not expect, and would be surprised by, that function changing the value's contents.
- A value is stored in a cache, a memoization table, or any other structure that is expected to represent a fixed snapshot, because a mutation reaching through the cache after the snapshot was taken silently invalidates the cache's whole purpose.
- A value participates in undo, redo, time-travel debugging, or any history mechanism, because keeping history of a mutable structure requires either deep copying at every step or a persistent data structure, while keeping history of immutable values only requires keeping the sequence of references.
- A bug report describes symptoms that only appear "sometimes" or "depending on order", which is the classic signature of an aliasing bug rather than a straightforward logic error.

Do NOT treat every mutable local variable as an instance of this smell, and
do not chase full immutability everywhere as a goal in itself.

- A loop accumulator, a builder object under active construction inside a single function, a mutable buffer used purely as scratch space that never escapes the function that created it, and any value whose lifetime and ownership are both provably confined to one call frame carry none of the risk this entry describes, because there is no second observer to be surprised by the mutation.
- Performance-critical inner loops, particularly in systems programming, game engines, and numerical code, routinely and correctly mutate large buffers in place rather than allocating a fresh copy on every iteration, and rewriting such code to be purely immutable can turn an O(1) amortized update into an O(n) copy, trading a real performance win for a theoretical purity gain that the surrounding code does not need.
- A single long-lived owner that mutates its own private state and never exposes a mutable reference to that state to any other party is also not this smell, because the two-condition test from dimension 2, mutability plus sharing, is only half satisfied.
- Do not apply the immutable-by-default discipline to a language or a runtime where doing so fights the idiom of that language's own community without a corresponding safety win, for example converting every small mutable struct in a hot path of a garbage-collected language into a fresh allocation per mutation purely for style, when no other part of the system ever observes the old value.

## 5. Structure

The participants in the general shape of this smell are not classes in a
diagram the way the Gang of Four patterns have participants, they are roles
that any piece of code can fall into.

The Shared Value is the mutable object, struct, array, map, or record that
more than one part of the program can reach a reference to.

An Owner, when the design is healthy, is the single component responsible
for deciding when and how the Shared Value changes, and every other
component treats what it receives from the Owner as read-only even when the
language does not enforce that at compile time.

A Mutator is any function, method, or code path that writes through a
reference to the Shared Value. In a well designed system there is exactly
one Mutator role, occupied only by the Owner. In a smelly system there are
several unrelated Mutators, each of which believes it is the only party
changing the value.

An Observer is any function, method, or code path that reads the Shared
Value and makes a decision based on its current contents. The smell
appears specifically when an Observer reads the value at a point in time
that is affected by a Mutator the Observer has no knowledge of.

## 6. ASCII structure diagram

```
  Healthy shape, single owner

  +-----------+        owns, mutates       +---------------+
  |  Owner    | -------------------------->|  Shared Value |
  +-----------+                            +---------------+
        |                                          ^
        | hands out read-only view                 |
        v                                          |
  +-----------+          reads only                |
  | Observer  | ------------------------------------
  +-----------+


  Smelly shape, multiple mutators aliasing one value

  +-----------+     writes      +---------------+     reads
  | Mutator A | --------------->|  Shared Value |<------------+
  +-----------+                 +---------------+              |
                                        ^                       |
                                        | writes          +-----------+
                                  +-----------+            | Observer  |
                                  | Mutator B |            +-----------+
                                  +-----------+
                    Observer cannot tell whether A or B, or both,
                    wrote last, and in what order, from local code alone.
```

## 7. Dynamics

The runtime sequence that exposes the smell always has the same shape. A
Shared Value is created and a reference to it is distributed to two or more
parties, either by being passed as an argument, stored in a field several
objects can reach, or captured in more than one closure. Time passes, and
during that time one party mutates the value through its reference, without
notifying or coordinating with any other party holding a reference to the
same value. A second party then reads the value through its own reference,
under the assumption that the value still reflects what it looked like when
that party first received it, or under the assumption that nothing else in
the system has touched it since. The read now silently returns the mutated
state, and the second party's subsequent logic runs against data it did not
expect, producing either a wrong answer, a crash further downstream when an
invariant the second party relied on turns out to have been violated, or, in
the specific case of a for-loop iterating over a collection while another
party removes elements from that same collection, a runtime exception such
as a concurrent modification exception in Java, or silently skipped elements
in a language that does not detect the conflict at all.

```
   Party A                Shared Value            Party B
      |                        |                      |
      | receive reference -----|--- receive reference -|
      |                        |                      |
      | mutate() ------------->| (state changes)      |
      |                        |                      |
      |                        |<---------- read() ---|
      |                        |                      |
      |                        |--- returns mutated -->|
      |                        |     state, silently   |
      |                        |                      |
      |                        |         B now acts on data it never
      |                        |         asked to be changed, with no
      |                        |         local signal that it changed.
```

In a concurrent context, the same diagram gains a race, because the mutate
and the read can interleave at the level of individual instructions rather
than at the level of whole method calls, and the observable outcome can then
depend on scheduling, meaning the bug reproduces intermittently and is far
harder to diagnose than the single-threaded version of the same defect.

## 8. Implementation variants

The remedy is not one technique, it is a family of techniques chosen to fit
the language and the concurrency model in use.

Defensive copying is the simplest variant and works in any language. A
component that must hand out a reference to internal mutable state instead
hands out a copy, so the caller can mutate the copy freely without affecting
the internal state. This is cheap to add and easy to understand, but it
costs an allocation on every hand-out, and it does not help if the internal
component itself is mutated concurrently from two directions.

Encapsulation via accessor methods, called Encapsulate Variable or
Encapsulate Field in the Fowler catalog, replaces direct field access with a
getter and, if truly needed, a narrowly scoped setter, so that every read
and write passes through one place where invariants can be checked and, if
the design later needs it, logging or synchronization can be added without
touching every call site, source https://refactoring.com/catalog/, verified
2026-08-02.

True immutable value objects go further and remove the setter entirely.
Java's `record` keyword, introduced as a preview feature in Java 14 and
finalized in Java 16, is the language-native version of this variant. The
official language documentation states that a record's fields are declared
`final` "because the class is intended to serve as a simple 'data carrier'"
and that a record class provides only accessor methods, source
https://docs.oracle.com/en/java/javase/17/language/records.html, verified
2026-08-02, meaning the compiler, not a convention, guarantees a `Rectangle`
record's `length` and `width` can never change after construction. Rust's
default immutability, described in dimension 2, is the same variant enforced
at the language level rather than by a keyword layered on top of an
otherwise mutable-by-default object model.

Persistent data structures are the variant used when a system needs to keep
old versions of a value cheaply, rather than only preventing mutation of the
current version. A persistent collection returns a new logical version on
every "modification" while sharing most of its internal storage with the
previous version through structural sharing, so the cost of a change is
close to the cost of the change itself rather than the cost of copying the
whole structure. Clojure's built-in collections are the reference example of
this variant in a mainstream language, the language reference stating that
all of the Clojure collections are immutable and persistent, and that the
Clojure collections support efficient creation of modified versions by
utilizing structural sharing, source
https://clojure.org/reference/data_structures, verified 2026-08-02.

Copy-on-write is a hybrid, used when most operations are reads and mutation
is rare, where a value behaves as if it were mutated in place from the
caller's point of view, but the underlying implementation transparently
allocates a fresh copy only on the first write after a value has been
shared, and shares storage freely otherwise, giving read-heavy workloads
close to zero copying cost while still protecting against aliased mutation.

Immutable update through a reducer function is the variant used at the level
of an entire application's state rather than a single object, and is the
shape enforced by Redux, discussed with a named citation in dimension 9.

## 9. Known production uses

Redux, the state management library originating in the React community and
now used well beyond it, enforces this remedy as a hard rule rather than a
suggestion. The official Redux fundamentals tutorial states, in the
project's own bold emphasis, that in Redux reducers are never allowed to
mutate the original or current state values, shows a direct field
assignment on the state object as an explicitly illegal example, and shows
the correct replacement, spreading the prior state into a new object with
the changed field, source
https://redux.js.org/tutorials/fundamentals/part-3-state-actions-reducers,
verified 2026-08-02. The same page lists the reasons the project gives for
the rule, including that mutation causes bugs such as the UI not updating
properly to show the latest values, and that it breaks the ability to use
time-travel debugging correctly, which is a direct, named instance of the
history and observability forces described in dimensions 3 and 16 of this
entry.

Clojure's core data structures, list, vector, map, and set, are immutable
and persistent by default across the entire language, as cited in dimension
8, meaning the remedy is not an opt-in library feature in Clojure, it is the
baseline behaviour every Clojure program is written against.

The Java platform's record construct, part of the standard library and
compiler toolchain since Java 16, is a named, first-party language feature
whose explicit design goal, per the Oracle language documentation cited in
dimension 8, is to make it straightforward to declare a data-carrying type
with fields the compiler guarantees are final and with no generated setter
methods, giving ordinary application code an immutable value type without
hand-writing a defensive-copy or builder pattern for every case.

The Rust language's ownership and borrowing system, cited in dimensions 2
and 8, is a fourth named production use, distinguished from the other three
by operating at the level of the language's type system and borrow checker
rather than at the level of a library convention, so that an attempt to
hold two mutable references to the same value, or a mutable reference
alongside a shared reference, is rejected at compile time rather than
merely discouraged by documentation.

## 10. Consequences

Positive.

- Code that avoids sharing mutable data is much easier to reason about locally, because the value of a variable at a given line can be determined by reading backward through that one function rather than by searching the whole codebase for every place that might have touched a shared reference.
- It becomes safe to share values across threads without synchronization, because there is nothing left to race over.
- Undo, redo, and time-travel debugging become close to free, because keeping history is simply keeping a list of past values rather than deep-copying a mutable structure at every step.
- Equality comparison becomes simpler and more reliable, because a value that never changes can be compared, hashed, and used as a map key or a set member without the risk that it will be mutated after insertion, which would silently corrupt the hash-based container that holds it.
- Testing becomes substantially simpler, because a pure function that receives an immutable value and returns a new value needs no setup or teardown of shared state between tests.

Negative.

- Every logical change that would have been an in-place mutation now allocates a new value, and in a language without structural sharing that means a full copy, which costs both memory and CPU relative to mutation and can matter in hot paths, tight loops, or large in-memory datasets.
- Passing changes through the system now requires threading the new value back to every place that needs it, which in a deeply nested call chain can turn into its own code smell, either a long parameter list carrying the updated value down through layers that do not otherwise need it, or a return-value plumbing problem where every intermediate function must remember to pass the new value back up.
- Some algorithms, particularly graph algorithms and certain numerical methods, are naturally expressed with in-place mutation and become noticeably harder to read, and sometimes asymptotically slower, when forced into a purely immutable style.
- Retrofitting immutability onto an existing mutable codebase is itself a nontrivial and risky refactor, because every call site that currently relies on the old mutate-in-place behaviour must be found and updated, and a missed call site produces a bug that is, by the nature of this smell, difficult to detect through casual testing.

## 11. Failure modes and misuse

Symptom, a bug that only reproduces "sometimes", especially under load or
under a specific ordering of operations, and disappears when a debugger or
extra logging is attached. Cause, two threads or two asynchronous tasks hold
references to the same mutable object and race to read and write it, so the
observable outcome depends on scheduling rather than on program logic alone.
Fix, either make the shared value immutable so there is nothing left to race
over, or introduce an explicit synchronization primitive around every access
to the shared mutable value, and prefer the former whenever the value's
access pattern allows it, because a missing lock reproduces the exact same
symptom while a removed mutation path cannot.

Symptom, an entity that was retrieved from a cache and appeared correct at
lookup time is later found to have unexpected field values, without any
code path that appears to write to it directly. Cause, the cache stores a
reference to the live object rather than a defensively copied snapshot, and
some other part of the system that was handed the same object by an
unrelated code path mutates it, silently corrupting the cached entry for
every future reader of that cache key. Fix, either store an immutable
snapshot in the cache at insertion time, so subsequent mutation of the
original object cannot reach the cached copy, or hand out a defensive copy
from the cache on every read, so a consumer's mutation of what it received
cannot reach the cache's stored value.

Symptom, an iterator, or a similar iteration construct, throws a
concurrent-modification style exception, or in a language without that
runtime check, silently skips or duplicates elements. Cause, a collection is
being mutated, an element added or removed, while a loop is iterating over
that same collection, so the iterator's internal position becomes
inconsistent with the collection's actual current contents. Fix, iterate
over a defensive copy of the collection when the loop body needs to mutate
the original, or collect the set of changes to apply and apply them after
the iteration completes rather than during it.

Symptom, adding a defensive copy in one place, or converting one value type
to immutable, appears to fix a bug locally but a related bug then appears
somewhere else in the same feature. Cause, this is the misuse case rather
than the smell case, treating immutability as a local patch applied wherever
a specific symptom was noticed, instead of tracing the value's full set of
Mutators and Observers as described in dimension 5 and deciding on a
consistent ownership model for the value across all of them. A partial fix
that removes one Mutator while leaving a second Mutator undiscovered simply
moves the bug to whichever call path was not covered by the patch.

Symptom, code that has been converted wholesale to a purely immutable style
becomes noticeably slower or measurably more verbose than the original, and
the team begins reverting the change under time pressure. Cause, the
applicability boundary in dimension 4 was crossed, immutability was applied
to a hot loop or a locally scoped, unshared buffer where the two-condition
test for this smell, mutability plus sharing, was never actually satisfied
in the first place. Fix, restrict the immutable-by-default discipline to
values that genuinely cross an ownership boundary, and permit mutation
freely within a single function's private, unshared working state.

## 12. Trade-off matrix

| Force | Mutable data, shared freely | Defensive copying | Encapsulation with narrow setter | Immutable value objects | Persistent data structures |
|---|---|---|---|---|---|
| Local reasoning | Low, value can change from anywhere | Medium, copy is safe once handed out | Medium to high, one controlled write path | High, value never changes after construction | High, same as immutable, plus history is cheap |
| Concurrency safety | None, needs external locking | Good after the copy point | Good if the setter itself is synchronized | Excellent, nothing to synchronize | Excellent, and old versions remain valid under concurrent readers |
| Allocation and copy cost | Lowest, no extra allocation | One copy per hand-out | Low, no copy unless the setter chooses to copy | One allocation per logical change | Close to the size of the change, via structural sharing |
| History, undo, time travel | Hard, requires manual snapshotting | Hard, still requires manual snapshotting | Hard, same limitation | Easy, keep the sequence of references | Easy and cheap, this is the variant's core strength |
| Ease of retrofitting onto existing code | Not applicable, this is the starting point | Easy, add copies at boundaries | Moderate, requires finding and routing through the setter | Hard, every mutation call site must change | Hard, and usually requires a library or language feature |
| Fit for a hot, single-owner loop | Best fit, no overhead | Wasteful, unnecessary copy | Unnecessary indirection | Can be the wrong tool, see dimension 4 | Can be the wrong tool for pure scratch buffers |

## 13. Related and incompatible patterns

Long Method and Feature Envy often co-occur with Mutable Data, because a
method that reaches into another object's mutable fields to both read and
write them is exhibiting Feature Envy toward that object's state, and the
method that performs many such reaches across a large body of code is
frequently also a Long Method, since the logic for safely sequencing several
mutations tends to accumulate into one large function rather than being
decomposed. Primitive Obsession compounds this smell specifically, because a
raw mutable array, list, or dictionary passed around in place of a proper
value type gives every recipient an implicit, unguarded mutation capability
that a narrow, purpose-built type would not expose. Data Clumps and Temporary
Field frequently share the same root cause as Mutable Data, an object whose
responsibilities have not been separated cleanly enough that its state can
be given a single, clear owner. Divergent Change and Shotgun Surgery are
downstream symptoms rather than causes, because a Shared Value with many
uncoordinated Mutators tends to force a change in one business rule to touch
every one of those Mutators, which is the definition of Shotgun Surgery, and
tends to make the containing class responsible for reacting to unrelated
kinds of change, which is the definition of Divergent Change.

The refactoring most directly paired with this smell in the Fowler catalog
is Encapsulate Variable, together with Remove Setting Method for the case
where a field should never have been settable after construction at all,
and Separate Query from Modifier for the case where a single method both
reads and mutates state and needs to be split so that reading a value never
has the side effect of changing it, source
https://refactoring.com/catalog/, verified 2026-08-02.

This entry is not incompatible with any named pattern in this repository in
the sense of two ideas that can never be applied together. It is, however,
in direct design tension with any pattern whose classic implementation
relies on in-place mutation of shared state as its mechanism, in particular
the Observer pattern's subject, which is commonly a mutable object that
notifies observers precisely because its state changed, and the Singleton
pattern, whose single shared instance is a natural home for exactly the kind
of many-Mutator, many-Observer aliasing this entry warns against if that
instance's fields are left publicly mutable. Neither Observer nor Singleton
is wrong to use alongside this entry, but both deserve the encapsulation and
ownership discipline described in dimensions 8 and 5 applied specifically to
their shared state.

## 14. Refactoring path in and out

Introducing the discipline into code that currently mutates shared data
freely follows a repeatable sequence. First, identify the Shared Value and
enumerate every Mutator and every Observer that touches it, which usually
means searching for every assignment to the relevant field or every call to
a method known to mutate it. Second, apply Encapsulate Variable so that every
one of those reads and writes passes through a single getter and setter
pair, even before deciding what the long-term ownership model should be,
because this step alone makes every future change local to one place rather
than scattered across the codebase. Third, decide on an ownership model,
either a single component becomes the sole Mutator and every other party is
converted to read-only access through the getter, or the value is converted
into an immutable type and every former Mutator is rewritten to construct
and return a new value instead of writing through a reference. Fourth, where
the value is passed into functions that only need to read it, change the
function signature to accept the narrowest read-only view the language
offers, a readonly field, a const reference, a shared, non-mutable
reference, or simply documentation and code review discipline in a language
that offers no such construct, so the boundary is visible even if it is not
enforced by the compiler. Fifth, add the failure-mode symptoms from
dimension 11 as regression tests before performing the conversion, so a
partial fix that leaves an undiscovered Mutator produces a failing test
rather than a production incident.

Removing the discipline, that is, deliberately reintroducing controlled
mutation, is the less common direction but is a legitimate refactor when
profiling shows the allocation cost from dimension 11 is the actual
bottleneck in a hot path. The safe path is to first confirm, using the
Mutator and Observer inventory from the introduction path above, that the
value in question genuinely has exactly one owner and no other Observer
depends on the value remaining stable across the call in question, then
narrow the scope of the reintroduced mutation to the smallest possible
region, typically a single function's local scratch buffer, rather than
reopening the value to mutation from every former call site at once.

## 15. Testing and verification

Code built around immutable values is easier to unit test because a test
only needs to construct an input value, call the function under test, and
assert on the returned output value, with no setup step to reset a shared
object's state between tests and no risk that test order affects the
outcome. This is a large part of why the Redux community, cited in
dimension 9, treats the immutable-update rule as central rather than
optional, reducers built this way are trivially pure functions to test.

Code that still has a Shared Value with more than one Mutator needs a
different testing strategy focused specifically on catching the aliasing
failure. A test double that wraps the Shared Value and records every call
that mutates it, sometimes called a mutation spy, can assert that only the
expected component ever calls the mutating operation during a given test
scenario, surfacing an unexpected second Mutator that manual code review
missed. For the concurrency variant of this smell, deterministic reproduction
in a unit test is difficult by nature, since the bug depends on scheduling,
so the more reliable verification technique is a stress test that runs many
concurrent operations against the shared value in a loop under a race
detector, such as the Go race detector invoked with the `-race` flag on
`go test`, or a similar tool in the target language, rather than relying on
a hand-written assertion to catch the race directly.

A useful static verification technique, where the language supports it, is
to make illegal mutation a compile error rather than a runtime concern at
all, which is exactly what Rust's borrow checker does, described in
dimensions 2 and 8, and what a final field in Java or a readonly field in
C# does at a narrower scope. Where the language offers no such enforcement,
a static analysis or lint rule that flags a mutating call on a value
received as a function parameter is the closest available substitute, and
should be treated as advisory rather than a substitute for the design work
of establishing clear ownership.

## 16. Observability signals

A healthy instance of the pattern shows almost no observability signal at
all, because there is nothing surprising happening, values do not change
underneath their observers, so there is nothing that needs to be logged or
traced specifically to explain a mutation. A struggling instance shows up in
a few characteristic ways. In application logs, watch for a value being
logged with one set of contents at one point in a request's processing and a
different set of contents when logged again later in the same request,
without an explicit, named operation in between that explains the change. In
a debugger or a tracing tool, watch for two stack frames that both hold a
reference to what turns out to be the identical object, which most languages
let a developer confirm directly by comparing reference identity rather than
value equality. In metrics, an unusually high allocation rate or garbage
collection pressure after converting a system to an immutable style is the
expected cost described in dimension 10, and should be checked against a
before-and-after benchmark rather than assumed to be a problem, since it is
the known, accepted trade rather than a defect. In incident postmortems, a
bug whose root cause traces back to one component mutating an object that a
second component was still holding a reference to is the clearest
retrospective signal that this smell was present, and is worth searching for
explicitly when triaging a class of "intermittent" or "cannot reproduce
locally" bugs.

## 17. Security and privacy implications

Shared mutable state is a real security surface in two specific
situations. The first is a shared cache or session object that holds
per-user or per-tenant data, where a defect that allows one request's
handler to mutate a cached object in place, rather than replacing it with a
new value, can leak one user's data into a response served to a different
user who subsequently reads the same cached entry, which is a data
isolation failure rather than a mere correctness bug. The second is any
value that participates in an authorization decision, such as a permissions
object or a role list attached to a request context, where an unrelated
component mutating that value after the authorization check has already
passed can produce a time-of-check to time-of-use gap, the general class of
vulnerability where a security decision is made against one state of the
data and then acted on against a later, different state of the same data.
Neither of these implications is unique to this smell, both are instances of
well known vulnerability classes, cross-tenant data leakage and
time-of-check-to-time-of-use races, but Mutable Data is specifically the
structural precondition that makes both of them possible, so eliminating
aliased mutation around session, cache, and authorization state is a direct
mitigation for both. This entry is silent on any implication specific to
encryption, key handling, or input validation, none of which are affected
by whether a given value happens to be mutable.

## 18. References

1. Martin Fowler, with Kent Beck, John Brant, William Opdyke, and Don
   Roberts, *Refactoring, Improving the Design of Existing Code*, second
   edition, Addison-Wesley, 2018.
2. Refactoring.com online catalog, entries for Mutable Data, Encapsulate
   Variable, Remove Setting Method, and Separate Query from Modifier,
   https://refactoring.com/catalog/, verified 2026-08-02.
3. Joshua Bloch, *Effective Java*, third edition, Addison-Wesley, 2018,
   Item 17, "Minimize mutability",
   https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/,
   checked against the publisher's public table of contents 2026-08-02.
4. The Rust Programming Language book, "Variables and Mutability",
   https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html,
   verified 2026-08-02.
5. Oracle, Java SE 17 Language Specification companion documentation,
   "Records", https://docs.oracle.com/en/java/javase/17/language/records.html,
   verified 2026-08-02.
6. Clojure Reference, "Data Structures",
   https://clojure.org/reference/data_structures, verified 2026-08-02.
7. Redux documentation, "Fundamentals, Part 3, State, Actions, and
   Reducers",
   https://redux.js.org/tutorials/fundamentals/part-3-state-actions-reducers,
   verified 2026-08-02.

## Code examples

Three languages are shown, each demonstrating the same alias, a `Report`
value handed to two call sites, mutated in place by one and left untouched
by the immutable variant. TypeScript and Python were picked because their
default object and list semantics make the aliasing hazard from dimension 2
easy to see with no special syntax, and Go was picked because its explicit
pointer receiver versus value receiver makes the mutable-versus-immutable
choice visible directly in the function signature rather than hidden inside
the call. Every sample below was compiled or run against a real toolchain
before being included, and the exact commands are given after each block.

### TypeScript, before and after

```typescript
// Before: a shared config object that two callers mutate in place.
interface Report { title: string; totals: number[]; }

function addTaxLine(report: Report, tax: number): void {
  report.totals.push(tax);
}

function printSubtotal(report: Report): number {
  return report.totals.reduce((a, b) => a + b, 0);
}

// After: an immutable update, each caller returns a new Report.
function addTaxLineImmutable(report: Report, tax: number): Report {
  return { title: report.title, totals: [...report.totals, tax] };
}

const original: Report = { title: "Q1", totals: [100, 50] };
const mutated = original;
addTaxLine(mutated, 15);
console.log("after mutation, original.totals also changed:", original.totals);

const originalTwo: Report = { title: "Q2", totals: [100, 50] };
const updated = addTaxLineImmutable(originalTwo, 15);
console.log("originalTwo untouched:", originalTwo.totals);
console.log("updated has the new line:", updated.totals);
console.log("subtotal of updated:", printSubtotal(updated));
```

Compiled with `npx tsc --noEmit mutable-data.ts` for type checking, then
`npx tsc mutable-data.ts --outDir /tmp/out && node /tmp/out/mutable-data.js`.
The output shows `original.totals` gaining the pushed value even though only
`mutated`, an alias of the same object, was passed to `addTaxLine`, and
shows `originalTwo` staying untouched when the immutable variant is used
instead.

### Python, before and after

```python
from dataclasses import dataclass, replace


@dataclass
class Report:
    title: str
    totals: list


def add_tax_line(report, tax):
    report.totals.append(tax)


def add_tax_line_immutable(report, tax):
    return replace(report, totals=report.totals + [tax])


def print_subtotal(report):
    return sum(report.totals)


original = Report(title="Q1", totals=[100, 50])
mutated_alias = original
add_tax_line(mutated_alias, 15)
print("after mutation, original.totals also changed:", original.totals)

original_two = Report(title="Q2", totals=[100, 50])
updated = add_tax_line_immutable(original_two, 15)
print("original_two untouched:", original_two.totals)
print("updated has the new line:", updated.totals)
print("subtotal of updated:", print_subtotal(updated))
```

Run with `python3 mutable_data.py`. `dataclasses.replace` is the standard
library's built-in support for constructing a modified copy of a dataclass
instance without mutating the original, the closest Python equivalent to
the Encapsulate Variable plus immutable-construction pattern from
dimension 8.

### Go, before and after

```go
package main

import "fmt"

type Report struct {
	Title  string
	Totals []int
}

func addTaxLine(r *Report, tax int) {
	r.Totals = append(r.Totals, tax)
}

func addTaxLineImmutable(r Report, tax int) Report {
	newTotals := make([]int, len(r.Totals), len(r.Totals)+1)
	copy(newTotals, r.Totals)
	newTotals = append(newTotals, tax)
	return Report{Title: r.Title, Totals: newTotals}
}

func printSubtotal(r Report) int {
	sum := 0
	for _, v := range r.Totals {
		sum += v
	}
	return sum
}

func main() {
	original := Report{Title: "Q1", Totals: []int{100, 50}}
	mutatedAlias := &original
	addTaxLine(mutatedAlias, 15)
	fmt.Println("after mutation, original.Totals also changed:", original.Totals)

	originalTwo := Report{Title: "Q2", Totals: []int{100, 50}}
	updated := addTaxLineImmutable(originalTwo, 15)
	fmt.Println("originalTwo untouched:", originalTwo.Totals)
	fmt.Println("updated has the new line:", updated.Totals)
	fmt.Println("subtotal of updated:", printSubtotal(updated))
}
```

Run with `go run main.go`. The pointer receiver on `addTaxLine` is the
explicit, compiler-checked signal that the function mutates its argument,
which is the closest Go comes to the compile-time exclusivity guarantee
that Rust's borrow checker enforces, described in dimensions 2 and 8. The
value receiver on `addTaxLineImmutable`, combined with copying the backing
slice before appending, is what keeps `originalTwo` untouched, since a Go
slice header shares its backing array across copies unless a fresh array is
explicitly allocated, which is exactly the aliasing hazard named in
dimension 2's discussion of `append` past a slice's current length.

Java, Rust, and Swift are not shown as separate samples because the same
alias-versus-immutable contrast is already the entire subject of the Java
`record` and Rust ownership citations in dimensions 8 and 9, and repeating
the identical `Report` example a fourth and fifth time in those languages
would not demonstrate anything the three samples above and the two cited,
verified language features do not already cover.
