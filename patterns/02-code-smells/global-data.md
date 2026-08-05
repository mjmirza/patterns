---
name: Global Data
slug: global-data
family: 02-code-smells
category: Coupling
aliases: [Global Variables, Global State, Global Mutable State, Global Data Smell]
first_described: "Fowler 2018, Refactoring, second edition, with Kent Beck as contributor for the JavaScript examples"
maturity: canonical
related: [large-class, primitive-obsession, feature-envy, shotgun-surgery, singleton, dependency-injection, encapsulate-variable]
incompatible_with: []
verified: 2026-08-02
---

# Global Data

## 1. Name, aliases, and lineage

The canonical name used in this entry is Global Data, taken from Martin
Fowler, *Refactoring, Improving the Design of Existing Code*, second edition,
Addison-Wesley, 2018, Chapter 3, "Bad Smells in Code." A public summary of the
book's own section numbering, reproduced from a reader's chapter-by-chapter
notes and fetched live for this entry, lists Global Data as the fifth
numbered smell in that chapter, directly after Long Parameter List and
directly before Mutable Data, source
https://raw.githubusercontent.com/ittus/Refactoring-summary-2nd-javascript/master/README.md,
verified 2026-08-02. The book's own printed page range for this smell was not
independently confirmed by this research, so no page number is cited for it,
only the chapter and its section order.

The wider community usually calls the same shape Global Variables or Global
State, and both terms are used interchangeably with Global Data in code
review comments, static analysis tool output, and language specifications.
Global Mutable State is the phrase reached for when a writer wants to stress
that read-only global constants are not the concern, only shared state that
more than one part of a program can write. This entry follows that same
distinction throughout. a `const` exported from one module and imported by
many is not the smell described here, a mutable value reachable and writable
from more than one independent part of a program is.

Whether an entry with this exact name and this exact scope existed in the
1999 first edition of *Refactoring*, co-authored by Fowler with Kent Beck,
John Brant, William Opdyke, and Don Roberts, was not independently verified
for this entry, so no claim is made about the first edition's catalog one way
or the other. What is verified is the second edition's placement, and that is
the source cited here as the origin of the name as used in this entry.

A closely related but distinct piece of vocabulary is the Singleton pattern,
described in Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides,
*Design Patterns, Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994. Singleton is a structural technique for guaranteeing
one instance of a class exists. Global Data is a smell describing a
consequence some Singleton implementations produce, mutable state reachable
from anywhere, when the guaranteed single instance is also given writable
fields that many unrelated callers mutate. The two ideas are not synonyms.
many Singletons hold no mutable state at all, and Global Data can exist
without any Singleton in sight, for example as a bare module level variable
in Python or a package level `var` in Go. Dimension 13 below returns to this
relationship in more depth.

## 2. Problem and context

A program needs some piece of information in more than one place. A request
identifier for logging. A feature flag. A cache of expensive lookups. A
counter of how many items have been processed so far. The path of least
resistance, in almost every language that allows it, is to put that value
somewhere reachable without threading it through every function signature
that might need it, a module level variable in Python or JavaScript, a static
field in Java or C sharp, a package level `var` in Go, a file scope global in
C, a class variable on a Singleton, or an object attached to the language
runtime itself such as `window` in a browser or `process` in Node.js.

The problem does not appear on day one. A single global counter used by one
reporting function is not painful to read, to test, or to reason about. The
problem appears as the codebase grows around that variable. A second module
starts reading it. A third module starts writing it, for a reason that made
sense in isolation. A test suite runs the same process twice and the second
run inherits state left behind by the first, because nothing reset the
global between runs. A background job and an HTTP handler both mutate the
same in memory cache concurrently, and now the failure is not a wrong
answer, it is a race, present only under load, absent on the developer's own
machine.

The context in which Global Data becomes a genuine problem, rather than a
convenience, is any codebase with more than one independent reader or writer
of the same mutable value, especially once any of the following is true.
concurrent execution is possible, whether threads, async tasks, or separate
processes sharing memory. automated tests run the same code path more than
once in the same process. the codebase has more than one contributor who
cannot hold the full set of readers and writers of that variable in their
head at once. That last condition is the one that actually predicts pain in
practice. a global used by exactly one author, in exactly one function, is
functionally a local variable with worse scoping and rarely causes a
reported bug. a global reached from a dozen call sites written by a dozen
different people over several years is a liability regardless of language,
because no single person can any longer answer the question that matters
most about mutable state, who changed this, and in what order, relative to
who else read it.

## 3. Forces

**Convenience versus traceability.** A global variable removes the need to
thread a value through every intermediate function that does not itself use
the value but sits between the producer and the consumer. This is a real,
immediate win in code that would otherwise need three or four parameters
passed through layers that ignore them. The cost is paid later, when a
reader trying to answer where does this value come from has to search the
whole codebase rather than read the local function signature.

**Coupling versus independence.** Every reader and every writer of a shared
global becomes coupled to every other reader and writer, even when none of
them import or call each other directly. This is coupling through a shared
resource rather than through an explicit interface, and it is the hardest
kind to see in a dependency graph or an import list, because static analysis
tools that draw module dependency graphs from import statements will not
show a coupling edge between two modules that share a global, since neither
imports the other.

**Testability versus realism of the running program.** Injected dependencies
can be swapped for a test double with a single line at the call site. A
global cannot be swapped that way without either a language feature for
monkeypatching the global itself, a build time flag, or a manual reset step
inserted into every test's setup and teardown. Tests that share a process
and share a global therefore either take on an ordering dependency, first
test to run sets the state the rest assume, or a maintenance burden, every
test file resets the global explicitly, and both of these costs are commonly
not visible until the test suite grows past a handful of files.

**Concurrency safety versus simplicity of a single shared value.** A single
shared mutable value read and written from one thread of control at a time
is simple and, for that access pattern, entirely safe. The same value
reached from two threads, two async tasks scheduled onto one event loop but
interleaved at an await point, or two processes sharing memory, needs
explicit synchronization, a mutex, an atomic operation, a channel, or
language level enforcement, or it produces a data race. The Rust standard
library's own documentation states this forces trade off directly for that
language's design. "If two threads are accessing the same mutable global
variable, it can cause a data race," and further states that guaranteeing
mutable, globally accessible data is free of data races is hard enough that
Rust treats a mutable static variable as unsafe by construction, source
https://doc.rust-lang.org/book/ch20-01-unsafe-rust.html, verified 2026-08-02.
That same page shows the concrete failure the language is designed to
prevent by construction. two threads incrementing a shared `static mut
COUNTER` "would likely result in data races, so it is undefined behavior."

**Cost of change versus locality of change.** A value with one reader and
one writer changes cheaply. changing its type, its meaning, or its
lifecycle touches exactly the code that owns it. A global with many readers
and writers turns every change to that value's shape or meaning into a
search across the whole codebase for every place that might be affected,
which is the same underlying cost that drives Shotgun Surgery and Divergent
Change, two other smells this pattern regularly produces as a side effect
rather than as its primary symptom.

## 4. Applicability and non-applicability

Apply the label Global Data, and reach for the refactorings in dimension 14,
when any of these hold.

- A mutable value is reachable from more than one function, class, or module
  without being passed as an argument, a constructor parameter, or an
  injected dependency, and more than one of those reachers writes to it.
- The value's lifecycle, when it is created, when it is reset, when it is
  safe to read, is implicit, known only by convention or by reading every
  call site, rather than made explicit by the type system or by an
  encapsulating owner.
- Tests of code that touches the value must run in a specific order, or must
  manually reset the value, to produce a repeatable result.
- Two or more independent features or subsystems need different values for
  what is currently one shared global, and are working around that by adding
  conditionals inside the code that reads the global rather than by giving
  each feature its own value.
- The value is mutated from more than one thread, coroutine, async task, or
  process without an explicit, auditable synchronization mechanism guarding
  every write.

Do not apply the label, and do not treat the surrounding code as smelling of
Global Data, when any of these hold. this is the non-applicability list the
template asks for, and it is the part most catalogs of this smell leave out.

- The value is a true constant, immutable after program start, such as a
  compiled regular expression, a lookup table built once, or a configuration
  value loaded at process startup and never written again during the
  process's lifetime. A read only global shared across a program is ordinary
  practice in every mainstream language and is not the smell this entry
  describes. the smell is in the writing, not in the sharing.
- The value is genuinely process wide by nature and the language or runtime
  already provides a controlled, well understood surface for it, for example
  a logging framework's global logger configuration, or a metrics library's
  process wide counter registry, where the library itself defines the
  contract for thread safe access and the alternative, threading a logger
  reference through every function in the call graph, would add far more
  coupling than it removes. The forces in dimension 3 still apply, and a
  library that gets this wrong still deserves the label, but a well designed
  library boundary around genuinely global concerns is not automatically a
  smell simply because the underlying storage happens to be global.
- The scope is a single function's local variables, or a single class's
  private instance fields accessed only through that class's own methods.
  neither of these is reachable without an explicit reference to that
  function's stack frame or that object, so neither is global in the sense
  this entry uses the word, regardless of how many lines of code the
  function or the class contains.
- The codebase is a single file script, run start to finish by one person, in
  one process, never under test automation, and never revisited by anyone
  else. this is a real and common context, ad hoc data analysis, a
  throwaway migration script, a one time report, and the cost this entry
  describes, coupling across independent readers and writers over time,
  simply does not accrue when there is only one reader, one writer, and one
  run.
- A dependency injection container, a service locator with a narrow,
  intentional surface, or a compile time constant table is being confused
  with Global Data because it is defined once, near the top of a file. the
  distinguishing question is always who can write to this, from how many
  independent places, not where in the file it is declared.

## 5. Structure

The pattern's structure is simple to draw and correspondingly easy to miss in
a large codebase, because the participants are rarely all visible in one file
at once.

**The global store.** A single storage location, a module level variable, a
static class field, an object attached to a runtime global such as
`globalThis` in JavaScript or `window` in a browser, a package level `var` in
Go, or a `static mut` in a systems language. It exists exactly once per
process, or per thread if the language provides thread local storage instead,
and it is reachable without an explicit reference passed to the code that
touches it.

**Independent readers.** Any function, method, or module that reads the
value without having received it as a parameter or a constructor argument.
An independent reader has no way to know, from its own signature or its own
local code, which other parts of the program might change the value before
or after it reads.

**Independent writers.** Any function, method, or module that writes to the
value under the same condition, reachable without being passed a reference,
and with no coordination visible in either writer's own code that the other
writer exists.

**The implicit contract.** The shared, unwritten agreement about who is
allowed to write when, what a valid value looks like, and whether reads must
happen before or after a particular write. In well factored code this
contract would be enforced by a type, an interface, or an owning object's
public methods. In the Global Data shape, the contract exists only in the
heads of whoever last worked on each of the readers and writers, and in
whatever comments, if any, sit next to the declaration.

## 6. ASCII structure diagram

```
  BEFORE, the smell

  +------------------+
  | GLOBAL STORE      |   reachable from anywhere,
  | e.g. module-level |   no explicit reference required
  | mutable variable  |
  +---------+---------+
       ^  ^  ^     |  |
       |  |  |     |  |
    read  read read write  write
       |  |  |     |  |
  +----+  +--+  +--++  ++----------+
  | ModA|  |ModB|  |ModC|  |ModD    |
  | fn1 |  | fn2|  | fn3|  | fn4    |
  +-----+  +----+  +----+  +--------+
   no import relationship drawn between
   ModA..ModD, yet all four are coupled
   through the shared store above

  AFTER, ownership made explicit

  +------------------------+
  | Owner (class/module)    |
  | - holds the state       |
  | - exposes narrow methods|
  +-----------+-------------+
              |
      injected reference
              |
   +----------+----------+----------+
   |          |          |          |
  ModA       ModB       ModC       ModD
  (holds a reference to Owner, passed
   in explicitly at construction time)
```

## 7. Dynamics

```
  BEFORE, an interleaving that produces a stale read

  time -->

  ModA.fn1()        writes  GLOBAL.count = 10
  ModB.fn2()        reads   GLOBAL.count   -> sees 10, caches it locally
  ModC.fn3()        writes  GLOBAL.count = 11   (ModB never told)
  ModB.fn2() (later) uses its cached 10, now stale
  ModD.fn4()        writes  GLOBAL.count = 0    (a reset ModA did not expect)
  ModA.fn1() (later) reads  GLOBAL.count = 0, assumes its own write from
                     earlier is still in effect, it is not

  No message passes between ModA, ModB, ModC, ModD directly.
  Every dependency in this trace runs through the shared store,
  and none of it is visible by reading any single module's own code.

  AFTER, the owner serializes access and the caller sees an explicit call

  ModA -> owner.recordEvent()      owner updates its own private state
  ModB -> owner.currentCount()     owner returns a value, ModB does not cache
                                    it across calls without being told the
                                    owner does not guarantee it stays fresh
  ModC -> owner.recordEvent()      same explicit call, same owner, no
                                    hidden mutation from outside owner's API
  Every caller's dependency on shared state is now visible in that
  caller's own source, one reference to owner, passed in explicitly.
```

## 8. Implementation variants

**The bare module or package level variable.** The most common shape in
Python, JavaScript, Go, and C. no wrapping type, no accessor methods, direct
read and direct write from any importer. Cheapest to write, hardest to
retrofit safety onto later, because every call site already assumes direct
field access rather than a method call.

**The Singleton with mutable public fields.** A class guarantees exactly one
instance exists, following Gamma, Helm, Johnson, and Vlissides's Singleton
pattern, and then exposes public, writable fields or a public dictionary on
that one instance. The single instance guarantee solves a different problem,
preventing accidental duplicate construction, and does nothing by itself to
prevent the Global Data smell, because every caller with a reference to the
instance can still write to it from anywhere, with no coordination.

**The environment or process level global.** Values reached through a
runtime provided global surface rather than a variable the codebase itself
declared, `os.environ` in Python, `process.env` in Node.js, `System
getProperty` and `System setProperty` in Java. These are process wide by
construction, provided by the platform, and every one of the forces in
dimension 3 still applies to them, they are simply harder to eliminate
because removing them means replacing a language runtime feature rather than
application code the team itself wrote.

**The encapsulated singleton, sometimes called a monostate in informal team
usage.** Multiple instances of a class exist, but every instance's fields
point at or delegate to one shared piece of storage, so behavior is
identical to a true Singleton from the caller's point of view while looking,
syntactically, like ordinary object construction. This variant is
occasionally chosen deliberately to keep call sites looking uniform across a
codebase that mixes genuinely independent objects with genuinely global
ones, and it carries the same coupling cost as any other form of Global Data,
dressed in per instance syntax.

**The thread local or task local variable.** A value declared once but given
separate storage per thread or per async context, rather than one shared
storage location for the whole process. This removes the cross thread data
race concern entirely, because no two threads ever see the same storage
slot, but it does not remove the coupling concern within a single thread's
call graph, where every function on that thread can still read and write
the value without an explicit reference. The clearest documented example of
this variant is `errno` in POSIX systems, covered in full in dimension 9.

**The controlled global behind an explicit accessor object.** A shared,
mutable value still lives in one process wide location, but every reader and
writer reaches it only through a small, named object with a defined
interface, rather than through direct field access. Django's `settings`
object, covered in dimension 9, is this variant, a genuinely global,
mutable at configuration load time piece of state, wrapped by
`django.conf.settings` so that every caller's dependency on it is at least
visible in that caller's own import list, even though the underlying storage
is still one shared location reachable from anywhere in the process.

## 9. Known production uses

**PHP superglobals.** The PHP manual documents nine built in arrays,
`$GLOBALS`, `$_SERVER`, `$_GET`, `$_POST`, `$_FILES`, `$_COOKIE`,
`$_SESSION`, `$_REQUEST`, and `$_ENV`, described in the manual's own words as
"built-in variables that are always available in all scopes," available
inside any function or method "with no need to do global $variable; to
access them," source
https://www.php.net/manual/en/language.variables.superglobals.php, verified
2026-08-02. Every PHP web application that reads request parameters or
session state touches one of these arrays, and every one of them is mutable,
process wide within a request, and reachable from any function without
being passed in, the shape this entry describes, applied at language design
scale rather than by an individual application team.

**POSIX `errno`.** The Linux manual page for `errno` states plainly that in
older code it was declared manually as a bare global, "extern int errno,"
and warns against that practice today, and separately states that in a
correctly built modern system "errno is thread-local, setting it in one
thread does not affect its value in any other thread," source
https://man7.org/linux/man-pages/man3/errno.3.html, verified 2026-08-02.
This is a documented, verifiable case of a language and its surrounding
tooling discovering, over decades, that a single process wide global
variable for error reporting was unsafe once multithreaded programs became
common, and moving the same conceptual variable to thread local storage
specifically to remove the cross thread data race the earlier design
permitted, without removing the coupling that exists within a single
thread's call graph, exactly the distinction drawn in dimension 8's thread
local variant.

**Django's settings module.** The Django documentation describes a settings
file as nothing more than an ordinary Python module carrying module level
variables, and states that application code is expected to reach it through
one shared object,
"in your Django apps, use settings by importing the object
django.conf.settings," rather than importing individual values, source
https://docs.djangoproject.com/en/5.2/topics/settings/, verified 2026-08-02.
This is a real, widely deployed web framework choosing the controlled
accessor variant from dimension 8 deliberately, one process wide,
effectively read mostly value, reached through a named object with a
documented contract, rather than through bare module level constants
imported piecemeal throughout an application, which the same documentation
states is unsupported, `from django.conf.settings import DEBUG` "won't
work."

**The Google C++ Style Guide's restrictions on static and global objects.**
Google's published style guide for its own C++ codebase states that
"objects with static storage duration are forbidden unless they are
trivially destructible," and explains the reason in terms of the exact
failure modes this entry's dimension 11 describes, "dynamic initialization
is not ordered across translation units, and neither is destruction," which
"can easily lead to hard-to-find bugs," and further notes that "when a
program starts threads that are not joined at exit, those threads may
attempt to access objects after their lifetime has ended," source
https://google.github.io/styleguide/cppguide.html, verified 2026-08-02. This
is a large, real, production codebase's own engineering standard, arrived at
from direct experience with the failure modes Global Data produces across a codebase of that size,
written as a rule the organization enforces on new code rather than as
advice offered without teeth.

## 10. Consequences

**Positive.** Global Data removes the need to thread a value through every
intermediate layer of a call graph that does not itself use the value,
which can make code that would otherwise carry three or four pass through
parameters noticeably easier to read at each of those intermediate layers.
It gives every part of a program access to genuinely process wide facts,
the process start time, a build identifier, a feature flag read once at
startup, without inventing a delivery mechanism for information that truly
has no single natural owner. For a value that is written exactly once, at
startup, and read many times afterward, the pattern's usual costs, coupling
across writers and non-deterministic test ordering, do not materialize,
because there is only one writer and its write happens before any reader
runs.

**Negative.** Every independent reader and writer of the shared value
becomes coupled to every other one, invisibly, in a way that standard
dependency analysis tools built from import statements will not surface,
because none of the readers or writers necessarily import each other. Tests
that exercise code touching the value either need explicit reset logic in
every test file, or become order dependent, passing or failing depending on
which other test ran first in the same process, which is a fragile,
maintenance heavy state to end up in as a test suite grows. Concurrent
readers and writers on the same mutable global, without an explicit
synchronization mechanism, produce a data race, a class of bug that is
frequently absent in local development, present only under production load,
and difficult to reproduce on demand, exactly the property that made it
worth Rust's language designers making unsynchronized mutable statics a
compile time error rather than a runtime risk, per the citation in dimension
3. Refactoring the type, shape, or meaning of the shared value requires
finding every reader and writer across the whole codebase rather than the
handful of call sites a properly encapsulated owner would have, which
raises the cost of otherwise ordinary changes as the number of readers and
writers grows.

## 11. Failure modes and misuse

**Symptom, cause, fix. Test order dependence.** Symptom, a test suite passes
when run as a whole file but fails, or passes differently, when a single
test is run in isolation, or when tests are reordered or run in parallel.
Cause, two or more tests read or write the same global, and one test's
leftover state becomes another test's starting assumption, whether or not
that assumption was ever written down anywhere. Fix, give the value an
explicit owner with a constructor, so each test can create a fresh instance,
and pass that instance into the code under test rather than letting the
code under test reach the global directly, following the refactoring path
in dimension 14.

**Symptom, cause, fix. A production only race condition.** Symptom, a bug
report describing occasionally wrong counts, occasionally missing entries,
or an occasional crash under load, that the reporting team cannot reproduce
on a single request in a staging environment. Cause, two threads, two async
tasks scheduled onto one event loop but interleaved at an await point, or
two worker processes with shared memory, write to the same global without a
synchronization mechanism guarding every write, so the final value depends
on the exact, non-deterministic order the operating system's scheduler
happened to interleave the operations in. Fix, either introduce an explicit
lock, mutex, or atomic operation around every write, or, preferably, remove
the shared mutable global entirely in favor of message passing or an owner
object with its own internal, private synchronization, so callers never
directly touch the shared storage.

**Symptom, cause, fix. A change to one feature silently breaking an
unrelated one.** Symptom, a developer changes the shape or the meaning of a
global variable to support a new feature, ships it, and an entirely
unrelated feature, in a module the developer never opened, starts behaving
incorrectly. Cause, the unrelated feature was also reading, or writing, the
same global, and neither the original developer nor the code review had any
way to discover that from the diff alone, because the coupling is invisible
in the import graph, exactly the negative consequence named in dimension
10. Fix, before changing a global's shape, search the whole codebase for
every reader and writer, not only the ones the change was written for, and
treat that search as a required, not optional, step of the change, and
longer term, move the value behind an owning object whose public interface
makes every caller's dependency visible in that caller's own source.

**Symptom, cause, fix. Configuration drift between environments.** Symptom,
code behaves correctly in a developer's own environment and incorrectly in
staging or production, and the difference cannot be reproduced by reading
the application's own source code. Cause, the application reads mutable
process wide state, an environment variable, a runtime flag, that is set
differently, or set at a different time relative to when the application
reads it, in each environment, and nothing in the application's source
makes that dependency, or its timing, explicit. Fix, read environment
provided global state once, at a single, well defined point during startup,
convert it into an explicit, typed configuration object at that point, and
pass that object to everything that needs it from then on, rather than
letting arbitrary code reach `os.environ`, `process.env`, or an equivalent
at any point during the program's execution.

## 12. Trade-off matrix

| Force | Global Data | Dependency Injection | Singleton (state free) | Service Locator |
|---|---|---|---|---|
| Call site verbosity | lowest, no parameter needed | higher, constructor or method parameters grow | low, one accessor call, no parameters | low, one lookup call, no parameters |
| Coupling visibility in imports | invisible, no import edge drawn | visible, an explicit constructor argument or import | visible, an explicit import of the singleton | invisible, the locator itself is imported but what it resolves to is not |
| Testability, swap for a test double | hard, requires monkeypatching or a manual reset | easy, pass a different instance at construction | easy if the class is state free, no state to isolate | hard, must reconfigure the shared locator's registry between tests |
| Concurrency safety by default | none, needs manual synchronization | inherits whatever the injected instance provides | none by itself, same as any object with mutable state | none by itself, same as Global Data once resolved |
| Cost of changing the value's shape | high, search the whole codebase for every reader and writer | low, change the type at the one owning class and let the compiler or type checker find every call site | low if state free, otherwise same cost as Global Data | medium, every resolution call site is affected but at least all pass through one registry |
| Best fit | a true, write once at startup, read many constant | a value with more than one independent reader or writer during the program's normal operation | a genuinely single instance concern with no shared mutable state, for example a stateless formatter | a plugin style architecture where the concrete implementation is chosen at runtime and the number of distinct services is large |

## 13. Related and incompatible patterns

**Large Class.** A class that accumulates a large, mutable public surface
often becomes the de facto global store for a codebase, every unrelated
module reaches into the same overgrown class's fields rather than into a
bare module level variable, but the underlying coupling problem, many
independent readers and writers of shared mutable state, is identical to
Global Data, only wearing a class shaped costume.

**Primitive Obsession.** Global Data frequently carries primitive types,
plain strings, integers, and dictionaries, rather than a small type with
its own invariants, because a bare global variable rarely gets the same
design attention a proper owning class would receive. The two smells
compound each other. a global holding a raw dictionary is both harder to
trace, because it is global, and harder to validate, because nothing
enforces what a valid entry in that dictionary looks like.

**Feature Envy and Shotgun Surgery.** Feature Envy describes a method that
reaches into another object's data more than its own. code that reaches
into a shared global instead of its own local state or its own
constructor injected collaborators is the same underlying habit, reaching
outward for data rather than being handed it, aimed at a global rather than
at a specific object. Shotgun Surgery, one small conceptual change forcing
edits across many files, is the most common downstream consequence of
Global Data once a codebase has enough independent readers and writers that
changing the shared value's shape can no longer be done in one place.

**Singleton, and why it is related but not the same thing.** As established
in dimension 1, Singleton is a structural guarantee, exactly one instance,
and Global Data is a description of a consequence, mutable state reachable
from anywhere. The two combine badly precisely because Singleton makes it
effortless to reach the one instance from anywhere in a codebase, so a
Singleton with mutable, publicly writable fields inherits every cost this
entry describes while looking, on the surface, like a disciplined design
choice because it followed a named pattern from a respected catalog. A
Singleton whose fields are immutable after construction, or private and
mutated only through methods that maintain its own internal invariants,
does not inherit those costs, because it is no longer Global Data even
though it is still a Singleton.

**Dependency Injection, the usual replacement.** Passing the value, or an
object that owns the value, explicitly into whatever needs it, through a
constructor or a function parameter, is the standard technique for
removing Global Data's invisible coupling, because it turns every reader
and writer's dependency into something visible in that reader or writer's
own signature. Dimension 14 walks through this refactoring step by step.

**Encapsulate Variable, the refactoring, not the smell.** Named in Fowler's
catalog of refactorings as the first mechanical step toward controlling
access to a piece of data that started life as a bare, directly accessed
variable, by wrapping every read and every write behind a getter and a
setter method before deciding what, if anything, those methods should do
differently from a bare field. This is usually the first concrete step
taken against an instance of Global Data, described fully in dimension 14.

No pattern in this catalog is truly incompatible with Global Data in the
sense of being impossible to combine with it. the relationship is always
one of a smell and its likely cause or its likely cure, never a hard
technical conflict.

## 14. Refactoring path in and out

**How Global Data is introduced, almost always by accident.** A single
value is needed in one place, and a developer, reasonably, reaches for the
cheapest available storage, a module level variable, a static field, an
entry in an existing configuration object. A second need for the same value
appears later, in different code, written by a different person or by the
same person on a different day, and the cheapest path is to read the
existing global rather than to design a delivery mechanism for a two
consumer value. Each individual step is locally reasonable. the smell
accumulates from the sum of many locally reasonable steps, not from one bad
decision, which is exactly why it is rarely caught by a single code review
and instead needs to be looked for on purpose.

**Refactoring out, step by step.**

1. Identify every reader and every writer of the value across the whole
   codebase, not a sample, the complete list, using a text search for the
   variable's name plus, where the language allows it, a search for any
   alias or re export of the same value under a different name.
2. Apply Encapsulate Variable first, wrap every direct read and every direct
   write behind an accessor method or property, even before deciding to
   change anything about where the storage lives. This step alone makes
   every access point visible and testable independently, and it is
   reversible on its own if the rest of the refactoring is paused partway.
3. Introduce an owning type, a class or a module, whose constructor or
   initializer creates the storage, rather than the storage existing at
   import time or at class load time before any code has asked for it.
4. Change each caller, one at a time, starting with whichever caller has
   the fewest other callers depending on it, to receive a reference to the
   owning type through its own constructor or function parameter, rather
   than reaching the global directly. Compile or type check, and run the
   test suite, after each individual caller is migrated, rather than
   migrating every caller in one large, unreviewable change.
5. Once every caller has been migrated to receive an explicit reference,
   delete the original global declaration. if the language or a linter can
   flag any remaining direct reference to the old name, use that check as
   the final confirmation that no caller was missed.
6. Where the value truly needs to be reachable from a very large or very
   deep call graph, and passing an explicit parameter through every layer
   would add more noise than it removes, consider a narrow, explicit
   accessor object rather than a bare variable, following the controlled
   global variant in dimension 8, so that every caller's dependency on the
   shared value is at least declared in that caller's own imports, even
   though the underlying storage remains one shared instance.

**Refactoring in, when it is a deliberate, informed choice.** A true,
process wide, write once constant, computed or loaded once at startup and
never written again, is a legitimate case for a plain global, and the
refactoring in this direction is simply, load it once, in one clearly named
location, close to the process's entry point, and treat any later write to
that same storage, anywhere else in the codebase, as a defect to be found
and removed rather than as a second legitimate writer to be accommodated.

## 15. Testing and verification

Code coupled to Global Data is difficult to test in isolation precisely
because isolation is what the smell removes. a unit test for a function
that reads a global must either accept whatever value the global currently
holds, which makes the test's outcome depend on execution order and on
whatever earlier code ran in the same process, or must reach into the
global directly and overwrite it before calling the function under test,
which makes the test coupled to the global's exact internal representation
and requires careful, symmetric teardown to avoid leaking state into the
next test.

Once the value has been moved behind an explicit owner, following the
refactoring path in dimension 14, testing becomes ordinary. a fresh
instance of the owning type is constructed at the start of each test, with
whatever starting state that particular test needs, passed into the code
under test through the same constructor or function parameter real callers
use, and no reset step is needed between tests because each test's owner
instance is independent of every other test's.

For code that cannot yet be fully refactored, for example while a large
migration is in progress, dependency injection frameworks and testing
libraries in most languages provide a monkeypatching or mocking facility
specifically for temporarily substituting a module level or class level
attribute for the duration of one test, and restoring the original value
afterward automatically. This is a legitimate stopgap during a migration,
and it is also a reliable signal, if a codebase's test suite leans on this
facility heavily and repeatedly for the same value, that the value is a
strong candidate for the refactoring path in dimension 14 rather than a
permanent testing pattern to build further tests around.

Concurrent code touching shared mutable state additionally needs
concurrency specific verification beyond ordinary unit tests, because a
data race can pass every sequential test and still fail intermittently
under real, interleaved execution. Language provided race detectors, where
available, such as running a test suite under a race detecting build, are
the appropriate tool for this category of failure. an ordinary assertion
based test, run once, sequentially, will not reliably reproduce a race
condition even when one genuinely exists in the code under test.

## 16. Observability signals

A healthy instance of shared, genuinely process wide state, the kind that
survives the non-applicability list in dimension 4, is boring to observe.
it is set once, near process startup, and every later read returns the
same value for the lifetime of the process, which is exactly the pattern a
startup time log line recording the loaded configuration, once, is meant to
confirm.

A failing instance of Global Data tends to show up first as an
inconsistency between two parts of a running system that should, by the
application's own logic, agree, but do not, a feature flag that reads true
in one request's logs and false in another concurrent request's logs with
no code path that should have changed it in between, or a counter whose
final logged value is lower than the sum of every individual increment a
trace shows really happened, the direct, observable fingerprint of a lost
update under a data race. Structured logs that include, alongside the value
itself, a request identifier, a thread or task identifier, and a timestamp,
turn this class of bug from theoretical to diagnosable, because they let a
reader reconstruct the actual interleaving of reads and writes after the
fact, which is otherwise invisible once the process has moved on.

Where a language or platform provides a race detector, wiring it into a
regularly scheduled test or staging run, rather than only running it
manually when a bug is already suspected, converts a data race from a
production incident waiting to happen into a build time signal, and is the
single most useful observability investment available for this specific
smell, because it detects the underlying cause directly rather than waiting
for one of its downstream symptoms to reach a user.

## 17. Security and privacy implications

Global Data can widen an attack surface in a specific, concrete way. any
code with access to the process's memory space can reach and, if the
storage is not further protected, mutate the shared value, which means a
vulnerability in one, entirely unrelated part of a program, an injection
flaw in a request parsing library, for example, can be used to corrupt or
read state that a different, security sensitive part of the same process
relies on, because there is no interface boundary between them to enforce.
An explicitly injected dependency at least confines the set of code that
can be handed a reference to sensitive state to whatever the constructor
graph actually wires together, which is a smaller, more auditable surface
than every function in a process being able to reach a bare global by name.

Global, process wide caches deserve particular attention in multi tenant
systems, a cache keyed loosely, or not keyed by tenant at all, that is
written by one tenant's request and read by another tenant's request within
the same process, is a realistic mechanism for cross tenant data leakage,
and the underlying cause is exactly the shape this entry describes, shared
mutable state reachable by more than one independent caller with no
enforced isolation between them. Where a cache, a session store, or any
other piece of process wide mutable state can hold data belonging to more
than one security principal, the storage's key space, and any code path
that can read across keys, is the first thing to audit.

Where global state exists as an artifact of the platform rather than the
application's own design, `os.environ` or `process.env` are the clearest
example, secrets accidentally placed into that shared, readable surface
become reachable from any library loaded into the same process, including
third party dependencies that were never intended to have access to them,
which is a distinct, additional reason, beyond the coupling and testability
costs already described, to convert environment provided global state into
an explicit, narrowly passed configuration object as early as possible in a
process's startup, following the fix described for configuration drift in
dimension 11.

## 18. References

1. Martin Fowler, *Refactoring, Improving the Design of Existing Code*,
   second edition, Addison-Wesley, 2018, Chapter 3, "Bad Smells in Code,"
   the Global Data entry, cited via a live-verified reproduction of the
   book's own chapter section order,
   https://raw.githubusercontent.com/ittus/Refactoring-summary-2nd-javascript/master/README.md,
   verified 2026-08-02.
2. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
   Patterns, Elements of Reusable Object-Oriented Software*,
   Addison-Wesley, 1994, the Singleton pattern chapter, cited for the
   distinction drawn in dimensions 1 and 13 between a single instance
   guarantee and shared mutable state.
3. PHP Manual, "Superglobals,"
   https://www.php.net/manual/en/language.variables.superglobals.php,
   verified 2026-08-02.
4. Linux manual page, `errno(3)`,
   https://man7.org/linux/man-pages/man3/errno.3.html, verified 2026-08-02.
5. Django Project documentation, "Settings,"
   https://docs.djangoproject.com/en/5.2/topics/settings/, verified
   2026-08-02.
6. Google, "Google C++ Style Guide," section "Static and Global Variables,"
   https://google.github.io/styleguide/cppguide.html, verified 2026-08-02.
7. The Rust Programming Language, Chapter 20, "Unsafe Rust," the section on
   mutable static variables, https://doc.rust-lang.org/book/ch20-01-unsafe-rust.html,
   verified 2026-08-02.

## Code examples

### Python, a global cache dictionary refactored into an owned collaborator

```python
# BEFORE. a bare module-level dict, written and read from anywhere.
_price_cache = {}


def fetch_price(sku: str) -> float:
    if sku not in _price_cache:
        _price_cache[sku] = _lookup_price_from_supplier(sku)
    return _price_cache[sku]


def clear_cache_for_test() -> None:
    _price_cache.clear()


def _lookup_price_from_supplier(sku: str) -> float:
    return 19.99 if sku == "SKU-1" else 0.0


if __name__ == "__main__":
    print(fetch_price("SKU-1"))
    clear_cache_for_test()
    print(fetch_price("SKU-1"))
```

```python
# AFTER. an owning class, constructed once per caller that needs one,
# with no module-level mutable state left for an unrelated reader to reach.
from typing import Callable, Dict


class PriceCache:
    def __init__(self, lookup: Callable[[str], float]) -> None:
        self._lookup = lookup
        self._entries: Dict[str, float] = {}

    def price_for(self, sku: str) -> float:
        if sku not in self._entries:
            self._entries[sku] = self._lookup(sku)
        return self._entries[sku]


def _lookup_price_from_supplier(sku: str) -> float:
    return 19.99 if sku == "SKU-1" else 0.0


if __name__ == "__main__":
    cache = PriceCache(_lookup_price_from_supplier)
    print(cache.price_for("SKU-1"))
    fresh_cache = PriceCache(_lookup_price_from_supplier)
    print(fresh_cache.price_for("SKU-1"))
```

### TypeScript, a global mutable config object refactored into constructor injection

```typescript
// BEFORE. a shared, mutable module export, written from more than one place.
export const appConfig: { retries: number; baseUrl: string } = {
  retries: 3,
  baseUrl: "https://api.example.com",
};

export function setRetriesFromFlag(flagValue: number): void {
  appConfig.retries = flagValue;
}

export function callWithRetry(path: string): string {
  return `GET ${appConfig.baseUrl}${path} up to ${appConfig.retries} times`;
}
```

```typescript
// AFTER. config is a plain, immutable value, handed to the collaborator
// that needs it, instead of being read from a shared mutable export.
interface AppConfig {
  readonly retries: number;
  readonly baseUrl: string;
}

class ApiClient {
  constructor(private readonly config: AppConfig) {}

  callWithRetry(path: string): string {
    return `GET ${this.config.baseUrl}${path} up to ${this.config.retries} times`;
  }
}

function loadConfig(flagValue: number): AppConfig {
  return { retries: flagValue, baseUrl: "https://api.example.com" };
}

const client = new ApiClient(loadConfig(5));
console.log(client.callWithRetry("/orders"));
```

### Go, an unsynchronized package-level counter refactored into an owned, guarded struct

```go
package main

import "fmt"

// BEFORE. a package-level mutable map, reachable and writable from any
// function in the package with no synchronization at all.
var visitCounts = map[string]int{}

func recordVisit(page string) {
	visitCounts[page] = visitCounts[page] + 1
}

func totalVisits() int {
	total := 0
	for _, count := range visitCounts {
		total = total + count
	}
	return total
}

func main() {
	recordVisit("/home")
	recordVisit("/home")
	recordVisit("/pricing")
	fmt.Println(totalVisits())
}
```

```go
package main

import (
	"fmt"
	"sync"
)

// AFTER. an owning type with its own private map and its own mutex, so
// every caller must be handed a reference before it can touch the state,
// and every write is explicitly guarded rather than relying on convention.
type VisitCounter struct {
	mu     sync.Mutex
	counts map[string]int
}

func NewVisitCounter() *VisitCounter {
	return &VisitCounter{counts: map[string]int{}}
}

func (v *VisitCounter) RecordVisit(page string) {
	v.mu.Lock()
	defer v.mu.Unlock()
	v.counts[page] = v.counts[page] + 1
}

func (v *VisitCounter) Total() int {
	v.mu.Lock()
	defer v.mu.Unlock()
	total := 0
	for _, count := range v.counts {
		total = total + count
	}
	return total
}

func main() {
	counter := NewVisitCounter()
	counter.RecordVisit("/home")
	counter.RecordVisit("/home")
	counter.RecordVisit("/pricing")
	fmt.Println(counter.Total())
}
```

A note on language coverage. Rust was not given a full runnable code sample
in this entry because its own standard library documentation, cited in
dimensions 3, 8, and 10, already makes the pattern's central concurrency
force explicit at the language level, a mutable global in Rust requires an
`unsafe` block to declare and to touch at all, which is itself one of the
clearest pieces of evidence in any mainstream language that Global Data's
concurrency cost is treated as a first class design concern rather than an
afterthought, and repeating that same demonstration in a fourth code sample
would not add a distinct failure mode beyond what the Go sample above
already shows for an unsynchronized shared map.
