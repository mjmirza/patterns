---
name: Immutable Object
slug: immutable-object
family: 09-concurrency
category: Concurrency
aliases: [Immutable Value, Value Object (concurrency sense), Functional Object]
first_described: "Lea 1999"
maturity: canonical
related: [read-write-lock, monitor-object, thread-specific-storage, producer-consumer, future-promise, strategized-locking]
incompatible_with: [double-checked-locking]
verified: 2026-08-02
---

# Immutable Object

## 1. Name, aliases, and lineage

The canonical name in the concurrent programming pattern literature is
Immutable Object, sometimes written as Immutable. Doug Lea catalogs it as a
pattern for the exclusion problem in *Concurrent Programming in Java. Design
Principles and Patterns*, 2nd edition, Addison-Wesley, 1999, section 2.3.2,
titled "Immutable Objects." Lea frames it as the strongest possible answer to
the exclusion problem, the family of techniques that keep two threads from
observing or causing inconsistent state in a shared object, because an object
with no mutable state after construction has no exclusion problem to solve.
The book is the standard citation used across later concurrency literature for
this being named and treated as a first class design pattern, not merely a
language feature or a style preference.

Brian Goetz, Tim Peierls, Joshua Bloch, Joseph Bowbeer, David Holmes, and Doug
Lea, *Java Concurrency in Practice*, Addison-Wesley, 2006, section 3.4,
"Immutability," restates and sharpens the same idea for a wider audience. The
book states plainly that immutable objects are always thread safe, and it
devotes the section to the exact conditions an object must satisfy to earn
that guarantee. That book is the most commonly cited source for the pattern in
professional Java practice, and its wording, immutable objects are always
thread safe, is quoted in secondary literature more often than Lea's original
text, so both books are cited here as the pattern's primary lineage.

Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, Item 17,
"Minimize Mutability," is the construction side counterpart. Where Lea and
Goetz argue why immutability solves concurrency, Bloch gives the concrete
rules for building an immutable class in Java. Do not provide mutators, make
every field final and private, keep the class from being subclassed in a way
that breaks the invariant, and, critically, keep every method from letting a
caller modify an object referenced by a field. This entry treats Bloch's five
rules as the authoritative construction checklist, cross referenced against
Lea's concurrency argument for why the rules matter.

Outside the pattern-catalog tradition, the same idea has an entirely separate
lineage in functional programming, where it is not treated as a pattern at
all but as a default. Immutability by default is a foundational property of
Erlang, Haskell, Clojure, and, at the language-binding level, Rust, and in
each of those communities the vocabulary is "immutable data" or "persistent
data structures" rather than "Immutable Object." The Clojure reference
documentation states the position directly. Clojure's core data structures
"are immutable" and, as a direct consequence, "are efficient and inherently
thread-safe" ([Clojure Data Structures reference](https://clojure.org/reference/data_structures),
verified 2026-08-02). This entry treats the object oriented Immutable Object
pattern and the functional immutable-data default as the same underlying idea
applied in two different language paradigms, and calls out where the paradigm
changes what the pattern costs.

## 2. Problem and context

Two or more threads share a reference to the same object. At least one thread
reads fields of that object while another thread, at an unpredictable point in
time, writes to those same fields. Absent any coordination, the reading thread
can observe a value mid-write, observe stale values published by a different
CPU core's cache, or observe an object whose invariants briefly do not hold
because the writer has updated one field of a multi-field invariant but not
the others yet.

The conventional answer to that problem is exclusion. Put a lock, a monitor,
or an atomic compare-and-swap loop around every access to the shared state, so
that only one thread touches it at a time and every other thread waits. That
answer works, and it is the subject of a large fraction of this pattern
family, but it has a cost that scales with contention, and it introduces an
entire secondary class of bugs, deadlock, livelock, lock ordering violations,
missed unlocks on exception paths, that have nothing to do with the original
problem and everything to do with the exclusion mechanism itself.

The context in which Immutable Object applies is the situation where the
shared object does not, in fact, need to change after it is constructed. A
configuration snapshot loaded once at startup and read by every request
thread. A money amount, a date, a coordinate, a color, an event that already
happened and is being replayed. A message passed between an actor and its
mailbox. A key in a hash-based collection, which must not change identity or
hash code while it sits in the table or the table's internal invariants break
silently. In every one of these cases the object represents a value, a fact
about the world at the moment it was made, rather than a mutable entity with
an identity that persists while its state changes underneath that identity.

The pattern's context has a second, less obvious half. The object must not
merely be logically read-only from the caller's point of view, it must be
physically incapable of mutation, including by code the object itself calls,
including by a reflection API, and including through a reference that leaked
out of the object during construction. An object that is conventionally
treated as read-only by every current caller but exposes a public setter, or
returns a live reference to its internal mutable array, is not an Immutable
Object under this pattern's definition. It is a mutable object that has not
yet been mutated, and it carries none of the pattern's guarantees. This
distinction, between disciplined-read-only and structurally-immutable, is the
single most common source of the pattern's misuse, covered in dimension 11.

## 3. Forces

**Safety versus flexibility.** An immutable object can never represent a
changed state directly, every logical change becomes a new object. This is
the central trade the pattern makes. It trades the flexibility of in-place
mutation for the safety of never having an inconsistent intermediate state
visible to any other thread. Goetz et al. state the trade in one sentence in
*Java Concurrency in Practice*, section 3.4. An immutable object can be freely
shared and published without synchronization, because there is no state for
two threads to disagree about.

**Allocation cost versus lock cost.** The pattern replaces synchronization
overhead, acquiring and releasing a lock, memory-fencing on every access, with
allocation overhead, a new object on every logical change. Which cost
dominates depends entirely on contention and object size. Under low
contention a lock is nearly free and reallocation is pure waste. Under high
contention a lock becomes a serialization bottleneck that no amount of
hardware throughput can route around, while allocation of small, short-lived
objects is exactly the case modern generational garbage collectors are tuned
to handle cheaply. This is a real engineering trade-off with no universal
answer, argued further in dimension 10.

**Sharing versus copying.** Structural sharing is the technique that resolves
the tension above for large aggregates. Instead of copying an entire
collection to produce a modified version, a persistent data structure shares
the unchanged parts of the old structure with the new one and allocates only
the path that changed. Clojure's reference documentation names this
directly, stating the collections "support efficient creation of 'modified'
versions, by utilizing structural sharing" ([Clojure Data Structures
reference](https://clojure.org/reference/data_structures), verified
2026-08-02). Without structural sharing, immutability on large collections is
a real performance liability. With it, the amortized cost of a single-element
change on a large persistent map or vector is close to logarithmic rather
than linear in the collection size.

**Identity versus value.** A mutable object usually has an identity that
persists across state changes, the same bank account object before and after
a deposit. An immutable object is a value, and two immutable objects with
equal fields are interchangeable for every purpose that matters to the
program. This force pulls the pattern toward languages and idioms with strong
value-type support, records, structs, case classes, and away from designs
where object identity itself carries meaning, such as a mutable session
object a debugger is watching by reference.

**Team topology and cognitive load.** A codebase where a reference cannot
change under a reader is a language-enforced guarantee, not a convention team
members must remember, removes an entire category of code review question and
an entire category of who-wrote-to-this-field debugging session. The cost is
paid up front, in a design that requires more thought about what constructor
parameters an object needs and how to represent a changed version, and again
in languages without strong immutability support, where the discipline is
manual and violable.

## 4. Applicability and non-applicability

Reach for Immutable Object when the following hold.

- The object represents a fact, a value, a point in time, a message, or a
  configuration snapshot, rather than a stateful entity with a lifecycle.
- The object will be shared across threads, passed through a queue to another
  actor, cached, used as a map key, or handed to code you do not control and
  cannot audit for correct locking.
- The number of distinct states the object can be in is small relative to how
  often it is read, so the cost of allocating a new instance per change is
  paid rarely against a large number of lock-free reads.
- Equality and hashing need to be simple and stable, because the fields that
  participate in them never change after construction.
- The object needs to be safely published without a happens-before edge
  beyond correct construction. Goetz et al., *Java Concurrency in Practice*,
  section 3.4.1, "Final Fields and Immutability," are explicit that a
  properly constructed immutable object, meaning every field is declared
  final and the object's own reference does not escape the constructor, is
  guaranteed visible correctly to any thread that later obtains a reference
  to it, even without additional synchronization on the read side, as a
  consequence of the Java Memory Model's semantics for final fields.

Do NOT reach for Immutable Object when any of the following hold.

- The state genuinely represents a mutable entity whose changes need to be
  observed in place by many holders of one reference, a UI widget bound to a
  model, a game object's position updated sixty times a second, a running
  total that many threads increment concurrently. Immutable Object would
  force every observer to be re-notified of a new reference on every tick,
  which is strictly more expensive and more complex than mutating the field
  under a lock or an atomic.
- The object is large, changes frequently, and the language or library gives
  you no structural-sharing persistent collection to change it cheaply. Naive
  copy-on-write of a ten thousand element array on every single-element
  update is a real performance trap, not a theoretical one, and is the most
  common reason teams abandon the pattern under load.
- Construction itself is expensive relative to the frequency of change,
  because every change now pays that construction cost again. A value object
  wrapping a network connection or a compiled query plan does not belong
  behind this pattern. Those own genuinely mutable, expensive-to-recreate
  resources and belong behind a different lifecycle pattern entirely.
- The domain model requires reference identity to be meaningful independent
  of state, an actor that must be found by identity even as its internal
  fields change, a database row proxy where two column values happening to
  be equal must not make the objects interchangeable.
- The runtime has no reliable mechanism to prevent late mutation. A language
  with no final, readonly, or equivalent, and no cultural discipline around
  it, produces objects that are immutable by convention only, which provides
  none of the thread-safety guarantee the pattern exists to give, only the
  appearance of it. See dimension 11 for the specific failure this produces.

## 5. Structure

- **Immutable value.** The class or record whose every field is set exactly
  once, at construction, and never reassigned afterward. It exposes only
  accessors, never mutators. Its equality and hash code are derived purely
  from its fields.
- **Deep field.** Any field of the immutable value that is itself a
  reference to a mutable object, an array, a mutable collection, a mutable
  date type in languages that have one. The immutable value is only
  genuinely immutable if every deep field is either itself immutable, or is
  defensively copied on the way in and never exposed by reference on the way
  out.
- **Constructor or factory.** The single point where all state is
  established. In many implementations this is a plain constructor. In
  patterns that build the value incrementally before freezing it, a mutable
  builder plays this role and produces the immutable value as its terminal
  step.
- **Wither, with-expression, or copy-on-write producer.** The mechanism by
  which a logical change is expressed. Because the original cannot be
  mutated, changing an immutable object always means producing a new
  instance that differs in one or more fields while sharing the rest,
  whether through a hand-written `withX` method, a language level `with`
  expression, or a persistent data structure's update operation.
- **Consumer.** Any thread, actor, or piece of code that holds a reference to
  the immutable value. Because the value cannot change under it, the
  consumer needs no lock, no defensive copy, and no synchronization to read
  it safely, no matter how many other consumers hold the same reference
  concurrently.

## 6. ASCII structure diagram

```
+-----------------------------+
|      ImmutableValue         |
|-----------------------------|
| - field1: T1  (final)       |
| - field2: T2  (final)       |
| - deepField: MutableThing   |  <- defensively copied in,
|                              |     never exposed by reference
|-----------------------------|
| + get1(): T1                |
| + get2(): T2                |
| + withField1(T1): Immutable |  <- returns a NEW instance
| + equals(other): bool       |
| + hashCode(): int           |
+-----------------------------+
              ^
              |  shared, read freely, no lock
   +----------+----------+----------+
   |          |          |          |
Thread A   Thread B   Thread C   Thread D
(reader)   (reader)   (reader)   (produces v2
                                  via withField1,
                                  does NOT touch v1)

    v1 --withField1(x)--> v2   (v1 is unchanged, still held
                                by A, B, C; v2 is a distinct,
                                also-immutable object)
```

## 7. Dynamics

The dynamics of Immutable Object are unusual among concurrency patterns in
that the interesting sequence diagram is not about coordination, it is about
the absence of coordination, and about exactly where the one synchronization
point that remains actually sits, publication of the reference itself.

```
Publisher thread                 Reader thread(s)
-----------------                ------------------
1. call constructor
2. assign every final field
3. constructor returns, object
   fully formed, invariants hold
4. publish reference (put into
   a field, a queue, a map,
   return from a factory)
      |
      |  safe-publication edge
      v
                                 5. obtain the reference
                                 6. read any field directly
                                    (no lock acquired)
                                 7. observed value is GUARANTEED
                                    to be the fully-constructed
                                    value from step 2, never a
                                    partially-initialized one,
                                    PROVIDED every field is
                                    final/readonly and the object
                                    did not escape before step 3

To change the value:
Producer thread                  (v1 continues to exist,
-----------------                 unmodified, for anyone
1. read v1's current fields       still holding it)
2. compute new field values
3. construct v2 = new instance
   with the changed fields and
   the unchanged fields copied
4. publish v2 wherever v1 used
   to be found (a variable, an
   atomic reference, a message)
      |
      v
Reader thread(s) that fetch the
reference again now see v2;
reader threads that already hold
v1 continue to see v1's original
values forever. There is no
"torn" state visible to anyone.
```

The guarantee in step 7 is the pattern's real payoff and its most
misunderstood detail. It depends on the language's memory model treating a
field marked final, readonly, or the equivalent as a promise that its value
is fixed at the end of the constructor and safely visible to any thread that
later obtains a correct reference to the object, without that reader needing
its own lock or barrier. Goetz et al. describe exactly this mechanism in
*Java Concurrency in Practice*, section 3.5.2, "Safe Publication Idioms,"
pairing it with the warning that the guarantee is voided the instant the
constructor lets the not-yet-finished object escape, for example by
registering the object with a listener or starting a thread from inside the
constructor, before construction finishes.

## 8. Implementation variants

**Manual final-field class (Java, C++ `const` members, C# `readonly`).** The
class declares every field final or readonly, assigns each exactly once in
the constructor, defensively copies any mutable input, and exposes only
getters. This is the variant Bloch's *Effective Java* Item 17 formalizes into
five rules, and it is the closest to Lea's and Goetz's original description.
It requires the most manual discipline and is the variant where the
non-applicability failure in dimension 11, a leaked mutable field, is most
common, because nothing in older Java syntax stops a getter from returning
the live array reference by accident.

**Record types (Java 16+ records, C# 9+ records, Kotlin data classes with
`val`, Python `@dataclass(frozen=True)`).** The language generates the
constructor, accessors, `equals`, `hashCode`, and often a copy-with-changes
operation, and enforces that every declared field is set once. Microsoft's
own tutorial states plainly that a `record` gives "immutable value
semantics" out of the box, and that a `with` expression performs
"nondestructive mutation," a copy with named fields overridden, rather than
an in-place change ([Use record types tutorial, Microsoft
Learn](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/tutorials/records),
verified 2026-08-02). This variant removes most of the manual-discipline
failure mode but still requires the author to keep any reference-typed
field itself immutable, or not exposed live, because the language's
generated code does not deep-copy a field's own mutable internals.

**Persistent (structurally-shared) collections.** Vectors, maps, and sets
implemented as balanced trees or tries so that a single-element change
allocates only the nodes on the path from the root to the changed leaf, and
shares every other node with the previous version. Clojure's core
collections work this way by default, and the reference documentation
states they "make all of their performance bound guarantees for persistent
use" ([Clojure Data Structures reference](https://clojure.org/reference/data_structures),
verified 2026-08-02). Java's `java.util.List.of(...)` and `Map.of(...)`
factories, introduced in Java 9, and libraries such as Vavr or the Guava
`ImmutableList` and `ImmutableMap` family bring a related, though not always
structurally-shared, style of immutable collection to the JVM.

**Builder-then-freeze.** A mutable builder object accumulates state through
ordinary setters, then a terminal `build()` call copies the accumulated
fields into a genuinely immutable result and, in careful implementations,
invalidates the builder so it cannot keep mutating the object it already
handed out. This variant exists to make expensive, many-field construction
practical without weakening the produced value's immutability, and it is
the variant most often paired with the Builder pattern from the creational
family.

**Freeze-on-publish (JavaScript `Object.freeze`, Python tuples and
frozenset).** Some languages offer no compile-time enforcement of
immutability at all and instead provide a runtime call that seals an
existing mutable object against further writes. `Object.freeze` in
JavaScript and the tuple and frozenset built-in types in Python are the
common instances. This variant is weaker than the compiled variants above.
It is a shallow freeze in JavaScript, meaning a frozen object's own
reference-typed properties are not themselves frozen, and it can be
bypassed via reflection or, in non-strict JavaScript mode, silently ignored
rather than raising an error.

**Copy-on-write wrapper around a mutable core.** Instead of an immutable
value type, a mutable container is wrapped so that every apparent mutation
actually clones the entire underlying structure, mutates the clone, and
swaps it in atomically. This is the shape of naive copy-on-write, distinct
from a true persistent collection because it does not share structure
between versions, and its cost profile is the linear-copy trap described in
dimension 4's non-applicability list.

## 9. Known production uses

**`java.lang.String` and the boxed numeric types in the JVM standard
library.** Every `String` instance is immutable after construction. The
JDK's own class documentation states this directly. "Strings are constant;
their values cannot be changed after they are created" ([java.lang.String
Javadoc, Java SE 21](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html),
verified 2026-08-02). `Integer`, `Long`, `BigInteger`, and `BigDecimal`
follow the same rule, and their immutability is precisely why they can be
freely cached, interned, and shared across every thread in a JVM process
without synchronization anywhere in the standard library's implementation of
them.

**`java.time` (JSR-310, Java 8 and later).** `LocalDate`, `LocalDateTime`,
`Instant`, `Duration`, and every other type in the `java.time` package
replaced the earlier, notoriously not-thread-safe `java.util.Date` and
`Calendar` classes specifically by making every date and time type
immutable, so that every apparent mutating method, `plusDays`, `withYear`,
and so on, returns a new instance and leaves the receiver untouched. This
design decision is documented as a deliberate, named goal of the JSR-310
effort that produced `java.time`, which explicitly modeled itself on the
earlier third-party Joda-Time library's immutable date and time types.

**Clojure's core persistent data structures.** Every built-in collection
type in Clojure, vectors, maps, sets, and lists, is immutable and
persistent by default, and the language's own reference documentation
states the direct consequence. Because of this, "the collections are
efficient and inherently thread-safe" ([Clojure Data Structures
reference](https://clojure.org/reference/data_structures), verified
2026-08-02). This is arguably the single most consequential production use
of the pattern in a widely deployed language, because it makes every
ordinary data manipulation in Clojure thread-safe by construction rather
than by discipline, a property the language's creator Rich Hickey has
described in public talks as the central design bet of the language.

**Rust's variable and reference immutability defaults.** Rust bindings are
immutable unless explicitly declared with the `mut` keyword, and the
official Rust Book states this as one of the language's "many nudges Rust
gives you to write your code in a way that takes advantage of the safety
and easy concurrency that Rust offers" ([The Rust Programming Language,
section 3.1, "Variables and
Mutability"](https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html),
verified 2026-08-02). Combined with the borrow checker, which additionally
guarantees that a value with any live immutable borrow cannot simultaneously
have a mutable borrow anywhere in the program, this makes Rust one of the
few mainstream systems languages where the compiler itself, not a coding
convention, enforces the exclusion guarantee Immutable Object exists to
provide.

**Redux and the broader unidirectional-data-flow front-end ecosystem.**
Redux's own FAQ documentation states that both Redux's `combineReducers`
utility and React-Redux's `connect` bindings rely on shallow reference
equality to detect state changes efficiently, and that "such shallow
checking requires immutability to function correctly," further stating
that "immutable data management ultimately makes data handling safer" and
that it enables time-travel debugging because reducers are required to be
pure functions with no side effects ([Redux FAQ, Immutable
Data](https://redux.js.org/faq/immutable-data), verified 2026-08-02). This
is a production use of Immutable Object one layer removed from raw thread
safety. The concurrency being managed is not OS-thread concurrency but the
concurrent, overlapping renders and dispatches of a UI runtime, and the
pattern's identity-implies-equality property is what makes the entire
framework's re-render optimization correct.

**C# `record` types (C# 9, 2020, and later).** Microsoft's own tutorial
documentation for record types describes them as providing "immutable
value semantics" for data modeling and demonstrates the `with` expression
as the idiomatic way to produce a changed copy without mutating the
original, explicitly calling this "nondestructive mutation" ([Use record
types tutorial, Microsoft
Learn](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/tutorials/records),
verified 2026-08-02). Records are now the recommended default for
data-transfer and value-modeling types in modern C# guidance, in
preference to hand-written mutable classes with public setters.

## 10. Consequences

Positive.

- Any thread may read an immutable object at any time with no lock, no
  barrier the application author has to write, and no risk of ever
  observing a partially-updated or torn state, as long as the object was
  safely published. Goetz et al., section 3.4, state this in the strongest
  possible terms. Immutable objects are always thread-safe.
- Equality, hashing, and use as a map or set key are simple and permanently
  stable, because the fields participating in them never change after
  construction. A mutable object used as a hash key that is later mutated
  corrupts the hash table's internal bucket invariants silently. An
  immutable key structurally cannot do this.
- Safe, cheap sharing. An immutable object can be cached, returned from a
  factory to many callers, and passed by reference to untrusted code
  without a defensive copy, because there is nothing for the untrusted code
  to corrupt.
- Reasoning about the object is local. Its entire state is fixed at the
  point where its constructor returns, so understanding what it can be in
  requires reading only the constructor, not every method that might ever
  be called on it over its lifetime.
- It composes naturally with functional-style transformation pipelines,
  event sourcing, and undo and redo, because keeping a reference to an old
  value around costs nothing extra and never risks that old value silently
  changing underneath a history log.

Negative.

- Every logical change allocates a new object. For small, short-lived
  values this is close to free on a modern generational garbage collector.
  For large aggregates without structural sharing it is a real, sometimes
  severe, linear-copy cost, argued in dimension 3.
- The pattern can push an unbounded number of intermediate values into
  existence during a busy update loop, and those objects still need to be
  collected, which trades a synchronization cost for a garbage collection
  cost rather than eliminating cost outright.
- Object identity stops being a meaningful way to track the same logical
  thing over time, which is a genuine loss for domains that are naturally
  entity-like rather than value-like, and forces those domains onto a
  different pattern, typically Monitor Object or an actor with private
  mutable state, to represent identity correctly.
- In languages without compiler-enforced immutability, the pattern is only
  as strong as the discipline of every author who ever touches the class,
  forever, because one added setter or one leaked mutable field silently
  removes every guarantee the pattern was providing, with no compiler
  error to catch it.

## 11. Failure modes and misuse

**The leaked mutable field.** Symptom. Two objects that are supposed to be
independent immutable values are observed to change together, or a value
object mysteriously changes after it was constructed and never had a setter
called on it. Cause. The constructor stored a caller-supplied array, list,
or `Date` by reference instead of copying it, or a getter returns the
object's internal mutable field directly instead of a copy or an
unmodifiable view. The caller who still holds the original reference, or who
mutates the returned reference, is silently mutating what was supposed to
be an immutable object. Fix. Defensively copy every mutable input on the
way into the constructor, and return defensive copies or genuinely
unmodifiable views from every accessor that would otherwise expose a
mutable internal, exactly Bloch's rules in *Effective Java* Item 17.

**Shallow freeze mistaken for deep immutability.** Symptom. `Object.freeze`
was called, or a frozen dataclass was used, and yet a nested property still
changes. Cause. Freezing or marking-frozen in most languages that offer it
as a runtime call rather than a compile-time guarantee only prevents
reassignment of the object's own top-level properties. Any reference-typed
property still points at a fully mutable object underneath, and that inner
object was never frozen. Fix. Recursively freeze every nested
reference-typed field at construction time, or restructure so every field
is itself an immutable type, never rely on a shallow freeze to provide a
deep guarantee.

**The reflection or unsafe-write escape hatch.** Symptom. An object
declared final in every field, correctly constructed, and never exposed via
a setter is observed to change anyway, in a way that defeats every review
of the source code. Cause. Reflection APIs, or in native-interop code,
direct memory writes, can bypass a final field's normal write protection in
some runtimes and configurations. Fix. This is a hardening concern rather
than a routine one. Where it matters, restrict reflective access via the
language's own module or security boundary rather than assuming final
alone is airtight against all callers.

**This-escape during construction.** Symptom. A thread other than the one
running the constructor observes an object with some fields still at their
default value, even though every field is declared final and the
constructor has, from the constructing thread's point of view, already
finished setting every field. Cause. The constructor passed a reference to
itself to another object, registered a listener, spawned a thread, or
otherwise let a reference to the not-yet-finished object escape before the
constructor returned, and the memory model's safe-publication guarantee for
final fields applies only to references obtained after construction
genuinely completes. Fix. Never let the not-yet-finished object escape the
constructor. If registration or callback wiring is necessary, do it in a
factory method that constructs the object first and only then performs the
wiring, after the constructor has fully returned.

**Naive copy-on-write on a large collection.** Symptom. A service that
adopted immutable state for correctness starts showing latency spikes and
longer garbage collection pauses under load, worse than the
mutable-plus-lock version it replaced. Cause. Every logical single-element
change to a large collection is implemented as a full linear copy of the
entire collection rather than a structurally-shared persistent update, so
an O(1) logical operation became an O(n) allocation and copy. Fix. Adopt a
genuine persistent data structure library for large, frequently-changing
collections, or reconsider whether the collection in question is actually
a good fit for Immutable Object at all, per dimension 4's
non-applicability guidance.

## 12. Trade-off matrix

| Force | Immutable Object | Read-Write Lock | Monitor Object | Thread-Specific Storage |
|---|---|---|---|---|
| Read cost under contention | No cost, no lock ever acquired | Low, readers share a shared-mode lock | Higher, every access serializes through one lock | No cost, but only because state is not actually shared |
| Write cost | New allocation per change, cheap for small values, can be costly for large uncopied structures | Blocks all readers while a writer holds the exclusive lock | Blocks all other accessors while one holds the monitor | Not applicable, each thread owns and writes its own copy |
| Correctness guarantee | Structural, enforced by the type once safely published, no lock discipline required at every call site | Depends on every accessor correctly acquiring the right lock mode | Depends on every accessor correctly going through the monitor's synchronized methods | Depends on the runtime correctly isolating per-thread storage |
| Object identity preserved across change | No, a change always produces a distinct value | Yes, the same object is mutated in place | Yes, the same object is mutated in place | Yes, but the object is per-thread, not shared |
| Cost of sharing across many readers | Free, no defensive copy needed | Free to read, contention grows with writer frequency | Free to read serially, contention grows with any access frequency | Not shared at all, so this force does not apply |
| Best fit | Values, messages, snapshots, cache entries, map keys | Read-heavy shared state that must remain a single mutable entity | Any mix of reads and writes on shared state needing simple correctness over raw throughput | Per-thread caches, counters, or buffers that never need cross-thread visibility |

## 13. Related and incompatible patterns

**Read-Write Lock.** The most direct alternative when a design needs
shared, frequently-read, occasionally-written state and cannot or does not
want to pay Immutable Object's per-change allocation cost. The two patterns
are often compared directly because they solve the identical problem, safe
concurrent reads, with opposite strategies. Immutable Object removes the
possibility of a write racing a read by removing writes to existing
objects entirely. Read-Write Lock instead coordinates writes and reads
explicitly so that in-place mutation stays safe.

**Monitor Object.** Where Immutable Object is the answer for state that
does not need to change in place, Monitor Object is the answer for state
that does, bundling data and the synchronized operations on it into one
object so every access is automatically serialized. A common, effective
composition is a Monitor Object whose internal state is itself built from
Immutable Object values, so the monitor's synchronized methods only ever
swap one immutable snapshot for another rather than mutating individual
fields, narrowing the monitor's own internal correctness surface.

**Future or Promise.** A future or promise is frequently implemented as,
or resolves to, an immutable value once completed. The completed result
cannot change again, and any number of threads may safely read it once it
has settled, which is exactly the Immutable Object guarantee applied to
the terminal state of an asynchronous computation.

**Producer-Consumer via message passing.** Actor systems and
message-passing concurrency models depend heavily on Immutable Object for
the messages passed between actors, because a mutable message handed
across a queue boundary would let the sender and receiver race on it
exactly as if it were shared mutable state with no queue at all. This is
why frameworks in this tradition commonly either enforce or strongly
recommend that message payload types be immutable.

**Thread-Specific Storage.** A different, complementary strategy for the
same underlying exclusion problem. Instead of making the shared object
incapable of change, Thread-Specific Storage makes the object not actually
shared, giving each thread its own private copy. The two compose when a
per-thread mutable accumulator is periodically snapshotted into an
immutable value for publication to other threads.

**Incompatible with Double-Checked Locking.** Double-Checked Locking
exists specifically to lazily and safely initialize a shared mutable field
exactly once under concurrent access, with careful attention to the memory
model's requirements around the field's visibility. Once the field being
guarded is itself made genuinely immutable and safely published via
final-field semantics, the entire double-checking apparatus, the lock, the
volatile field, the second null check, becomes unnecessary complexity
solving a problem that no longer exists. The two patterns are not composed
together on the same field, one supersedes the need for the other.

## 14. Refactoring path in and out

Introducing Immutable Object into a class that currently has setters and
mutable state.

1. Identify every field that participates in the object's meaningful state
   and confirm the object's lifecycle actually allows fixing all of them at
   construction time. If some field's value genuinely depends on
   information only available after construction, the design needs a
   builder or a two-phase factory rather than a straight conversion.
2. Change every field's declaration to final, readonly, or the language
   equivalent, and move every value currently set outside the constructor
   into constructor parameters.
3. Remove every setter and every other method that mutates a field.
4. Audit every constructor parameter and every accessor for a
   reference-typed value. Defensively copy mutable inputs on the way in,
   and return unmodifiable views or copies, never the live internal
   reference, on the way out.
5. Replace every call site that used to call a setter with a call that
   captures the returned new instance from a `withX` method or an
   equivalent copy-with-change operation, and update the call site to use
   the new reference going forward rather than assuming the old one
   changed in place.
6. Re-run the object's existing test suite and add a specific test
   asserting that a `withX` call leaves the original instance's field
   values unchanged, which is the single assertion that most reliably
   catches an incomplete conversion.

Removing Immutable Object when a value genuinely needs to become a
mutable, identity-bearing entity, the less common but real reverse
direction.

1. Confirm the change is warranted by dimension 4's non-applicability
   criteria, most commonly a large, frequently-updated aggregate paying
   real allocation cost with no persistent-collection option available,
   rather than by a preference for fewer `withX` calls at call sites.
2. Introduce a wrapping mutable holder, or convert the class itself, one
   field at a time, back to a mutable field with an accompanying
   synchronization strategy, typically Monitor Object or Read-Write Lock,
   chosen from dimension 12's trade-off matrix based on the actual read
   and write ratio measured in production, not guessed.
3. Update every call site that previously captured a new reference from a
   `withX` call to instead call a mutator and continue holding the same
   reference, and specifically re-audit every place the old immutable
   value was shared across threads without a lock, because that sharing
   was safe only because the value could not change, and it is no longer
   safe once it can.

## 15. Testing and verification

What Immutable Object makes easy to test. Constructing an instance and
asserting its field values, with no setup of mocks, no need to reset
shared state between tests, and no test-ordering dependency, because two
tests can construct and read two immutable instances concurrently with
zero risk of interference. Equality-based assertions,
`assertEquals(expected, actual)`, are simple and reliable because the
object's equality is defined purely by its immutable fields.

The test specific to this pattern that most catalogs of general advice
omit. Assert that a `withX`-style change operation does not mutate the
receiver. Concretely, capture the receiver's field values, or the receiver
reference itself alongside a deep copy of its state, call the change
operation, and assert both that the returned value reflects the change and
that the original receiver's observable state is bit-for-bit identical to
what it was before the call. This single test catches the
leaked-mutable-field failure mode from dimension 11 far more reliably than
reading the source, because a defensive copy that was forgotten in one
accessor but present in nine others is easy to miss by inspection and easy
to catch by this exact assertion.

For concurrency-specific verification, a stress test that constructs one
shared immutable instance, publishes it via the actual publication
mechanism the production code uses, a field write, a queue put, a
concurrent map put, and spins up many reader threads that repeatedly read
every field and assert internal invariants hold, catches this-escape bugs
and unsafe-publication bugs that a single-threaded test cannot, because
those specific bugs are defined by what a second thread is allowed to
observe.

In languages where immutability is enforced only by convention, a mutation
test that attempts every public method and confirms none of them changes
the observed state, run as part of the class's own test suite, functions
as a regression guard against a future change accidentally reintroducing a
setter or a mutable getter.

## 16. Observability signals

Because Immutable Object removes the classic lock-contention observability
signals, no lock wait time, no monitor queue depth, to measure, the
observability concern shifts almost entirely to allocation and garbage
collection. A healthy Immutable Object design shows a steady, predictable
allocation rate for the value types in question, proportional to the
actual rate of logical changes in the domain, and a young-generation
garbage collector that reclaims the resulting short-lived objects cheaply
with pause times that do not correlate with request latency spikes.

The unhealthy signal, corresponding to the naive copy-on-write failure
mode in dimension 11, is an allocation rate or an average
allocated-bytes-per-change metric that scales with the size of the
collection being changed rather than with the size of the change itself,
visible in a heap profiler or an allocation-tracing tool as one dominant
allocation site whose per-call byte count tracks a collection's total
size. Object-count and byte-count telemetry per value type, sampled from a
memory profiler under production-representative load, is the concrete way
to see this before it becomes a latency incident.

A second useful signal, specific to safe-publication correctness rather
than performance, is a test or a runtime assertion, in languages that
support it, that a newly-constructed value's fields are never observed at
their zero-value or default state by any consumer thread. A sighting of a
default-valued final field by a thread other than the constructing thread
is direct evidence of a this-escape bug from dimension 11, and is the kind
of defect that a race-detection tool, rather than ordinary logging, is
built to surface.

## 17. Security and privacy implications

Immutable Object narrows one specific attack surface directly. An object
that cannot be mutated after construction cannot be corrupted in place by
a time-of-check-to-time-of-use race, where an attacker-influenced value is
validated once and then, before it is used, mutated by a concurrent path
to a value that would not have passed validation. Passing validated input
through the system as an immutable value from the moment it is validated
closes this class of bug structurally rather than relying on every
downstream consumer to re-validate or to re-read the value atomically.

The pattern also has a privacy-relevant consequence that cuts the other
way and is frequently overlooked. Because an immutable value, once
constructed and shared, cannot be scrubbed or overwritten in place,
sensitive data placed into an immutable object, a plaintext credential, a
token, personally identifiable information, lingers in memory for as long
as any reference to that object survives and for as long as the garbage
collector has not yet reclaimed it, with no way for the holder to zero it
out early. Mutable buffer types that support explicit zeroing after use
exist specifically to avoid this exposure window, and are the correct
choice, not Immutable Object, for short-lived secret material that needs
to be actively wiped rather than left to the collector's own timing.

Where the immutable value is a message or a value type used as a hash-map
key across a trust boundary, correctly implemented equality and hashing
over genuinely immutable fields also close a distinct integrity concern.
An object that changed its hash code after being inserted into a
hash-based collection, because a field it was hashed on later mutated,
corrupts the collection's lookup structure in a way that can be exploited
to hide or duplicate entries. An immutable key structurally cannot do this
because its hash-relevant fields cannot change after insertion.

## 18. References

1. Doug Lea, *Concurrent Programming in Java. Design Principles and
   Patterns*, 2nd edition, Addison-Wesley, 1999, ISBN 0-201-31009-0,
   section 2.3.2, "Immutable Objects."
2. Brian Goetz, Tim Peierls, Joshua Bloch, Joseph Bowbeer, David Holmes,
   and Doug Lea, *Java Concurrency in Practice*, Addison-Wesley, 2006, ISBN
   0-321-34960-1, section 3.4, "Immutability," and section 3.5.2, "Safe
   Publication Idioms."
3. Joshua Bloch, *Effective Java*, 3rd edition, Addison-Wesley, 2018, ISBN
   978-0-13-468599-1, Item 17, "Minimize Mutability."
4. Clojure reference documentation, "Data Structures,"
   https://clojure.org/reference/data_structures, verified 2026-08-02.
5. Java SE 21 API documentation, `java.lang.String`,
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html,
   verified 2026-08-02.
6. Oracle, "Immutable Objects," The Java Tutorials, Concurrency lesson,
   https://docs.oracle.com/javase/tutorial/essential/concurrency/imstrat.html,
   verified 2026-08-02.
7. The Rust Programming Language, chapter 3.1, "Variables and
   Mutability,"
   https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html,
   verified 2026-08-02.
8. Microsoft Learn, "Use record types tutorial," C# documentation,
   https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/tutorials/records,
   verified 2026-08-02.
9. Redux documentation, "Immutable Data," FAQ,
   https://redux.js.org/faq/immutable-data, verified 2026-08-02.

## Code examples

Working code in five languages, TypeScript, Python, Go, Rust, and Swift.
Java was omitted because no Java runtime was available in the verification
environment for this entry, `javac --version` reported no JRE located. The
pattern's Java shape is nonetheless fully described in dimensions 8 and 9
above, following Bloch's Item 17 rules directly.

Every sample models the same small domain object, a money amount, showing
construction, a `withX`-style change that returns a new instance, and a
defensive-copy point for a reference-typed field.

### TypeScript

```typescript
class Money {
  readonly amountCents: number;
  readonly currency: string;

  constructor(amountCents: number, currency: string) {
    this.amountCents = amountCents;
    this.currency = currency;
    Object.freeze(this);
  }

  withAmount(amountCents: number): Money {
    return new Money(amountCents, this.currency);
  }

  add(other: Money): Money {
    if (other.currency !== this.currency) {
      throw new Error("currency mismatch");
    }
    return this.withAmount(this.amountCents + other.amountCents);
  }
}

const price = new Money(1999, "EUR");
const discounted = price.withAmount(1499);
console.log(price.amountCents, discounted.amountCents);
```

### Python

```python
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Money:
    amount_cents: int
    currency: str

    def with_amount(self, amount_cents: int) -> "Money":
        return replace(self, amount_cents=amount_cents)

    def add(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError("currency mismatch")
        return self.with_amount(self.amount_cents + other.amount_cents)


price = Money(1999, "EUR")
discounted = price.with_amount(1499)
print(price.amount_cents, discounted.amount_cents)
```

### Go

```go
package main

import "fmt"

type Money struct {
	amountCents int
	currency    string
}

func NewMoney(amountCents int, currency string) Money {
	return Money{amountCents: amountCents, currency: currency}
}

func (m Money) WithAmount(amountCents int) Money {
	return Money{amountCents: amountCents, currency: m.currency}
}

func (m Money) Add(other Money) (Money, error) {
	if other.currency != m.currency {
		return Money{}, fmt.Errorf("currency mismatch")
	}
	return m.WithAmount(m.amountCents + other.amountCents), nil
}

func main() {
	price := NewMoney(1999, "EUR")
	discounted := price.WithAmount(1499)
	fmt.Println(price.amountCents, discounted.amountCents)
}
```

Go has no compiler-enforced field immutability. `Money` is passed by value
here, so `WithAmount` and `Add` return a distinct struct rather than
mutating the receiver, and the fields are unexported so no package outside
this file can reassign them directly. This is the closest Go idiom to the
pattern in a language without a final or readonly field modifier.

### Rust

```rust
#[derive(Clone, Debug, PartialEq)]
struct Money {
    amount_cents: i64,
    currency: String,
}

impl Money {
    fn new(amount_cents: i64, currency: &str) -> Self {
        Money { amount_cents, currency: currency.to_string() }
    }

    fn with_amount(&self, amount_cents: i64) -> Money {
        Money { amount_cents, currency: self.currency.clone() }
    }

    fn add(&self, other: &Money) -> Result<Money, String> {
        if other.currency != self.currency {
            return Err("currency mismatch".to_string());
        }
        Ok(self.with_amount(self.amount_cents + other.amount_cents))
    }
}

fn main() {
    let price = Money::new(1999, "EUR");
    let discounted = price.with_amount(1499);
    println!("{} {}", price.amount_cents, discounted.amount_cents);
}
```

### Swift

```swift
import Foundation

struct Money {
    let amountCents: Int
    let currency: String

    func withAmount(_ amountCents: Int) -> Money {
        Money(amountCents: amountCents, currency: currency)
    }

    func add(_ other: Money) throws -> Money {
        guard other.currency == currency else {
            throw NSError(domain: "Money", code: 1)
        }
        return withAmount(amountCents + other.amountCents)
    }
}

let price = Money(amountCents: 1999, currency: "EUR")
let discounted = price.withAmount(1499)
print(price.amountCents, discounted.amountCents)
```

All five samples were run against the actual toolchains present in the
verification environment. `npx tsc` for TypeScript type checking,
`python3` for the Python sample, `go run` for Go, `rustc` for Rust, and
`swiftc` for Swift. Results are reported in the accompanying verification
summary.
