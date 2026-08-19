---
name: Thread-Specific Storage
slug: thread-specific-storage
family: 09-concurrency
category: Concurrency
aliases: [Thread-Local Storage, TLS, TSS, Per-Thread Singleton]
first_described: "Schmidt, Harrison, Pryce 1997"
maturity: canonical
related: [singleton, proxy, double-checked-locking, active-object, monitor-object, half-sync-half-async]
incompatible_with: []
verified: 2026-08-02
---

# Thread-Specific Storage

## 1. Name, aliases, and lineage

The canonical name in the pattern literature is Thread-Specific Storage. Douglas
C. Schmidt, Timothy H. Harrison, and Nat Pryce described it in the paper
"Thread-Specific Storage for C/C++. An Object Behavioral Pattern for Accessing
per-Thread State Efficiently," presented at the 4th annual Pattern Languages of
Programs conference in Allerton Park, Illinois, in September 1997, and reprinted
in C++ Report, SIGS, Vol. 9, No. 10, November and December 1997. The attribution
and venue are confirmed on Schmidt's own patterns index page, which lists the
paper under the title "Thread-Specific Storage" and states it "Appeared in the
4th annual Pattern Languages of Programming conference in Allerton Park,
Illinois, September 2 to 5, 1997 and in the C++ Report, SIGS, Vol. 9, No. 10,
November/December, 1997 (with Tim Harrison and Nat Pryce)" ([Schmidt's patterns
index page](https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html), verified
2026-08-02). The paper itself was retrieved and read in full for this entry
([the PDF at
dre.vanderbilt.edu](https://www.dre.vanderbilt.edu/~schmidt/PDF/TSS-pattern.pdf),
verified 2026-08-02); its title page lists the three authors exactly as above,
with Schmidt and Harrison at the Department of Computer Science, Washington
University in St. Louis, and Pryce at the Department of Computing, Imperial
College, London.

The same author group, together with Michael Stal and Hans Rohnert, published
Pattern-Oriented Software Architecture Volume 2. Patterns for Concurrent and
Networked Objects, John Wiley and Sons, 2000, ISBN 978-0-471-60695-6 ([the
Wikipedia summary of the POSA series names Schmidt, Stal, Rohnert, and Buschmann
as the authors, the year, and the
ISBN](https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture),
verified 2026-08-02). That book is widely cited alongside Thread-Specific
Storage because it collects the concurrency patterns from the same ACE and TAO
research program at Washington University, the University of California at
Irvine, and Siemens AG that produced this pattern, Reactor, Proactor, Half-
Sync/Half-Async, and Leader/Followers. This research could not independently
confirm which chapter or page range of the 2000 book reprints Thread-Specific
Storage, so, following the same convention used elsewhere in this family for
the sibling ACE-program patterns, this entry treats the 1997 PLoP paper and C++
Report article as the primary citable source rather than asserting a POSA2
chapter number it could not verify.

The industry alias in far wider circulation than the pattern's own name is
Thread-Local Storage, abbreviated TLS, or the ambiguous shorthand TSS, which
this entry avoids using standalone because it collides with Transport Layer
Security in casual conversation. Thread-Local Storage is the name every major
language runtime and operating system vendor actually uses in its own API and
documentation, for the C11 `_Thread_local` keyword, the C++11 `thread_local`
keyword, Java's `ThreadLocal` class, and Windows' TLS API family
([Wikipedia's summary article on the mechanism uses "Thread-local storage" as
its own title and states "the functions `pthread_key_create` and
`pthread_key_delete` are used respectively to create and delete a key for
thread-specific data,"](https://en.wikipedia.org/wiki/Thread-local_storage)
verified 2026-08-02). The relationship between the two names is not a rename
over time. Thread-Local Storage is the older, lower-level operating-system and
compiler mechanism, present in production Unix and Windows threading libraries
well before 1997. Thread-Specific Storage is the higher-level object-oriented
design pattern that Schmidt, Harrison, and Pryce named around that mechanism,
adding the Proxy layer, the key indirection, and the collaboration structure
described in dimension 5. A codebase that says `thread_local` is invoking the
mechanism. A codebase that wraps that mechanism behind a typed accessor object
so calling code never sees a raw key is applying the pattern.

A third name, Per-Thread Singleton, appears in the pattern's own related-
patterns discussion rather than as an alternate title. The paper states
plainly that "Objects implemented with thread-specific storage are often used
as per-thread Singletons ... e.g., errno is a per-thread Singleton," while
also noting in the same sentence that this is not universal, because "a thread
can have multiple instances of a type allocated from thread-specific storage"
(TSS pattern PDF, section 11, Related Patterns, verified 2026-08-02). This
entry treats Per-Thread Singleton as a description of the pattern's most common
usage shape, not as an independent name, and expands the relationship in
dimension 13.

## 2. Problem and context

A piece of state is logically global, in the sense that every function in a
call chain wants to read or write it through one shared name, and yet the
state must physically differ for every thread that touches it, because two
threads writing the same location would corrupt each other's data. The paper's
own motivating example is the C library's `errno` variable. A blocking or
non-blocking system call sets `errno` on failure, and the calling code checks
it immediately afterward. The two steps, the set and the check, are not one
atomic operation. In a single-threaded program that gap never matters, because
nothing else runs between the call and the check. In a preemptively
multi-threaded program, a second thread can be scheduled between those two
steps and overwrite the shared `errno` before the first thread reads it, so
the first thread's check sees the second thread's error code (TSS pattern PDF,
section 2.2, Common Traps and Pitfalls, verified 2026-08-02, describing exactly
this race between two threads calling `recv` on a socket).

The naive fix, wrapping a mutex around the variable, does not work, and the
paper is explicit about why. "The 'obvious' solution of wrapping a mutex
around `errno` will not solve the race condition because the set/test
involves multiple operations, i.e., it is not atomic" (TSS pattern PDF,
section 2.3, verified 2026-08-02). A lock protects a single access, not a
sequence of two accesses separated by other work, and requiring the
application to hold the lock across that gap invites forgotten unlocks,
deadlock, and, on every call whether or not multiple threads are actually in
play, a locking cost paid for nothing.

The context in which Thread-Specific Storage is the right answer, stated
directly in the paper's applicability section and restated here in the
reader's own terms, has a specific shape. The state is accessed through
sequences of method calls within one thread, not shared across threads for
collaboration. The access point must stay globally visible in the source, so
existing code that was written assuming a single thread of control, or a
library whose public API predates threading, does not have to be rewritten to
pass the state as an explicit parameter through every intermediate call. And
the data really is private per thread, not merely private per request or per
task, which matters once asynchronous and cooperative concurrency models enter
the picture, covered in dimensions 4 and 13.

This is a genuinely different problem from the one Reactor, Proactor, and
Half-Sync/Half-Async solve elsewhere in this family. Those patterns organize
how work is dispatched to threads. Thread-Specific Storage organizes how a
piece of state travels alongside a thread once that thread is already running,
without being threaded explicitly through every function signature along the
way.

## 3. Forces

- **Locking overhead.** Favoured, decisively. The entire reason the pattern
  exists is to eliminate synchronization on the hot read and write path. Once
  a thread has located its own slot, no other thread can observe or race that
  access, so the operation needs no mutex, no atomic instruction, and no
  memory barrier beyond what the underlying platform's TLS implementation
  already provides.
- **API stability for existing callers.** Favoured. A function signature that
  reads `errno` or a thread-local logger needs no new parameter, so millions
  of lines of code written against a single-threaded assumption keep compiling
  and keep working once the underlying storage becomes thread-specific. This
  is judgement, not a claim the source paper makes about a specific migration,
  but it follows directly from the paper's own stated first applicability
  criterion, that the pattern suits code "originally written assuming a single
  thread of control and is being ported to a multi-threaded environment
  without changing existing APIs" (TSS pattern PDF, section 3, verified
  2026-08-02).
- **Discoverability and structural clarity.** Sacrificed. The paper names this
  cost itself under Liabilities. "It hides the structure of the system. The
  use of thread-specific storage hides the relationships between objects in an
  application, potentially making the application harder to understand" (TSS
  pattern PDF, section 6.2, verified 2026-08-02). A reader tracing where a
  value comes from cannot follow a parameter through the call stack. They must
  instead know that the accessor is thread-specific and reason about which
  thread is calling.
- **Memory footprint.** Sacrificed, proportionally to thread count. Every live
  thread that has ever touched a given key holds its own copy of the state,
  even threads that no longer need it, until the runtime frees the slot on
  thread exit or the collection is bounded some other way. A large thread
  pool multiplies a small per-slot cost into a real one.
- **Portability across threading libraries.** Judgement. The raw mechanism
  differs across POSIX pthreads, Win32, and every language runtime, so an
  application that talks to the raw API directly is coupled to whichever
  library it targets first. The pattern's Proxy participant, dimension 5,
  exists specifically to absorb that difference behind one stable interface,
  and the paper states the resulting benefit plainly for its own C++ wrapper,
  that "porting an application to another thread library ... only requires
  changing the TSS class, not any applications using the class" (TSS pattern
  PDF, section 9.2.4, verified 2026-08-02).
- **Correctness under thread-pool reuse.** Sacrificed unless actively managed.
  A worker thread in a pool that is used to service many unrelated units of
  work retains its thread-specific slot across those units. State set for one
  unit of work leaks forward into the next unless something explicitly resets
  or removes it. Dimension 11 covers this in detail.
- **Team topology and library boundary clarity.** Mildly sacrificed. Because
  the state is reached through a global access point rather than through
  constructor or method injection, the dependency on that state is implicit,
  which makes the contract between a library and its caller harder to audit
  than an explicit parameter would.

## 4. Applicability and non-applicability

Reach for Thread-Specific Storage when the following hold, closely following
the paper's own stated applicability list.

- The application "was originally written assuming a single thread of control
  and is being ported to a multi-threaded environment without changing
  existing APIs" (TSS pattern PDF, section 3, verified 2026-08-02).
- The application "contains multiple preemptive threads of control that can
  execute concurrently in an arbitrary scheduling order," and "each thread of
  control invokes sequences of methods that share data common only to that
  thread" (same source).
- The data must be reached "through a globally visible access point that is
  'logically' shared with other threads, but 'physically' unique for each
  thread," and the data "is passed implicitly between methods rather than
  being passed explicitly via parameters" (same source).
- A per-thread reusable resource, a scratch buffer, a database connection, a
  compiled regular expression cache, would otherwise be reconstructed on every
  call if it could not be cached somewhere private to the calling thread.

Do NOT reach for Thread-Specific Storage in these cases, and the reason is
what actually protects a codebase from the pattern's costs.

- **Multiple threads are collaborating on shared data.** The paper is explicit.
  "Multiple threads are collaborating on a single task that requires
  concurrent access to shared data... If thread-specific storage was used to
  store the database, the threads could not share the data" (TSS pattern PDF,
  section 3, verified 2026-08-02). If the whole point is that thread A must
  see what thread B wrote, thread-specific storage is the wrong tool by
  construction, because each thread's slot is invisible to every other
  thread. Use a monitor, a lock-protected shared structure, or a message
  queue instead.
- **Passing the value explicitly is more intuitive and no more expensive.**
  The paper's own second exclusion. "It is more intuitive and efficient to
  maintain both a physical and logical separation of data... it may be
  possible to have threads access data visible only within each thread by
  passing the data explicitly as parameters to all methods. In this case, the
  Thread-Specific Storage pattern may be unnecessary" (same source). A short
  call chain with two or three hops costs nothing extra to thread a parameter
  through, and doing so keeps the dependency visible in every signature.
- **The unit of concurrency is not an OS thread.** Node.js's own event loop
  runs application code on effectively one thread, and its documented answer
  to "how do I associate state with a request across an async chain" is
  `AsyncLocalStorage`, which the Node.js documentation itself describes as
  "similar to thread-local storage in other languages," used to "associate
  state and propagate it throughout callbacks and promise chains" ([Node.js
  API documentation, "Asynchronous context
  tracking"](https://nodejs.org/api/async_context.html), verified 2026-08-02).
  The state there follows a logical continuation, not an OS thread, and a
  literal thread-local variable would be either meaningless in a
  single-threaded event loop or actively wrong across an `await` that resumes
  on a different pooled worker. Reach for a continuation-local or task-local
  mechanism instead, see dimension 13.
- **Go's concurrency unit is the goroutine, and the language deliberately
  provides no goroutine-local storage.** Go's own FAQ, in the section "Why is
  there no goroutine ID," states the omission is intentional design, not an
  oversight. "The fundamental reason goroutines are anonymous is so that the
  full Go language is available when programming concurrent code," and warns
  that once a goroutine is named, "it becomes special, and one is tempted to
  associate all computation with that goroutine, ignoring the possibility of
  using multiple, possibly shared goroutines for the processing," citing
  `net/http` as the concrete case where per-request state tied to a goroutine
  would prevent a handler from farming work out to helper goroutines ([The Go
  Programming Language FAQ](https://go.dev/doc/faq), verified 2026-08-02). Go
  code that wants request-scoped state passes a `context.Context` explicitly
  through every call, which is Thread-Specific Storage's excluded case above,
  deliberately made mandatory at the language level. The Go example in
  dimension 8 demonstrates the idiomatic replacement rather than the pattern
  itself, because there is no idiomatic way to apply the pattern in Go as
  written.
- **The state must survive and be inspectable after the thread exits or is
  returned to a pool.** Thread-specific storage is bound to the thread's
  lifetime, or in a pooled thread's case, bound at most to how carefully the
  application resets it. Data with its own lifetime, an audit trail, a
  request log entry that must be queryable after the request finishes,
  belongs in an explicit, addressable object, not behind a thread key that
  becomes unreachable once the thread that owned it is gone.
- **The number of distinct keys is unbounded and driven by untrusted input.**
  If a key is derived from something outside the program's control, per-key
  slots multiply without limit, which is a resource-exhaustion vector covered
  in dimension 17.

## 5. Structure

Four participants, using the paper's own names, given here with the role each
plays.

- **Application Thread.** Any thread of control in the program. It never
  touches the underlying storage mechanism directly. It calls the TS Object
  Proxy's `getspecific` and `setspecific` operations exactly as it would call
  an ordinary method on an ordinary object.
- **TS Object Proxy.** The typed, per-key access point application code
  actually calls. It holds the key that identifies which slot in each
  thread's collection belongs to it, and it is "responsible for providing
  access to a unique object for each application thread via the
  `getspecific` and `setspecific` methods" (TSS pattern PDF, section 4,
  verified 2026-08-02). One Proxy instance mediates access for every thread
  that uses it, so it is shared, even though what it returns is not.
- **TS Object Collection.** A per-thread table mapping keys to that thread's
  TS Objects. Every thread that has ever touched thread-specific storage has
  exactly one collection, whether the runtime stores that collection inside
  the thread's own control block or in a global structure indexed by thread
  identifier, see dimension 8 for both implementation shapes.
- **TS Object.** A single thread's private instance of the data, reached only
  through its owning Proxy and located inside its owning thread's Collection.
  The paper's own example makes the errno TS Object "an object of type int"
  (TSS pattern PDF, section 4, verified 2026-08-02), but the type is arbitrary
  and is commonly a whole object graph, a connection, a buffer, or a logger.

The key detail that separates this pattern from a plain global variable is the
indirection through a key. The Proxy does not hold the data. It holds a key
that the currently running thread's Collection resolves to that thread's own
copy of the data. Two threads calling the same Proxy method reach the same
code path and the same key, and land in two different objects, because the
Collection each thread resolves the key against is private to that thread.

## 6. ASCII structure diagram

```
   +----------------------+
   |  Application Thread  |
   |----------------------|
   |  calls getspecific()  |
   |  calls setspecific()  |
   +-----------+----------+
               |
               v
   +----------------------+          key           +------------------------+
   |    TS Object Proxy    | --------------------->  |   TS Object Collection |
   |------------------------|                        |   (one per thread)      |
   | + getspecific(): TSObj |                        |-------------------------|
   | + setspecific(v: TSObj)|                        | + get_object(key): TSObj|
   | - key                  |                        | + set_object(key, v)    |
   +------------------------+                        +------------+------------+
                                                                    |
                                                                    v
                                                       +------------------------+
                                                       |        TS Object        |
                                                       |  (this thread's copy)   |
                                                       +------------------------+

   One Proxy instance is shared by every Application Thread.
   Each thread's Collection is private to that thread.
   The same key, resolved against a different Collection,
   reaches a different TS Object.
```

## 7. Dynamics

```
Thread A            TS Object Proxy      TS Object Collection A     TS Object A
   |                       |                        |                    |
   |-- getspecific() ----->|                        |                    |
   |                       |-- locate A's           |                    |
   |                       |   Collection --------->|                    |
   |                       |-- get_object(key) ---->|                    |
   |                       |                        |-- lookup(key) ---->|
   |                       |<---- returns A's TSObj -|                    |
   |<--- returns TSObj ----|                        |                    |
   |                       |                        |                    |
   |-- method() on TSObj ------------------------------------------------>|
   |<------------------- result, no lock taken ---------------------------|

Thread B            TS Object Proxy      TS Object Collection B     TS Object B
   |                       |                        |                    |
   |-- getspecific() ----->|                        |                    |
   |                       |-- locate B's           |                    |
   |                       |   Collection --------->|                    |
   |                       |-- get_object(key) ---->|                    |
   |                       |                        |-- lookup(key) ---->|
   |                       |<---- returns B's TSObj -|                    |
   |<--- returns TSObj ----|                        |                    |
```

The collaboration in words, following the paper's own three named steps (TSS
pattern PDF, section 5, Collaborations, verified 2026-08-02). First, "locate
the TS Object Collection," which each Application Thread reaches by calling
`getspecific` or `setspecific` on the Proxy, and which may itself require a
lock if collections are stored externally to threads, see dimension 8. Second,
"acquire the TS Object from thread-specific storage," where the Proxy uses its
key against the already-located Collection to find that thread's object.
Third, "set/get TS Object state," where the application operates on the
returned object with ordinary method calls, and, critically, "no locking is
necessary since the object is referenced by a pointer that is accessed only
within the calling thread" (same source, section 5). Two different threads
running the identical code path in parallel each traverse the diagram above
independently and never observe each other, because the second hop of each
traversal resolves against a different Collection.

## 8. Implementation variants

**Operating system or language runtime-provided keys.** The lowest-level,
most portable shape. POSIX defines `pthread_key_create`, which "shall create
a thread-specific data key visible to all threads in the process" ([The Open
Group Base Specifications Issue 7, `pthread_key_create`
description](https://pubs.opengroup.org/onlinepubs/9699919799/functions/pthread_key_create.html),
verified 2026-08-02), together with `pthread_setspecific` and
`pthread_getspecific` to bind and read a per-thread value under that key, and
`pthread_key_delete` to release it. The number of keys a process may hold is
bounded by `PTHREAD_KEYS_MAX`, which the same specification requires every
conforming implementation to support up to a minimum system-imposed value.
The paper's own worked implementation section discusses exactly this limit
under "Fixed- vs. variable-sized TS Object Collections," noting that "the
POSIX Pthread standard defines a minimum number of keys,
POSIX_THREAD_KEYS_MAX, that must be supported by conforming implementations"
(TSS pattern PDF, section 7.2, verified 2026-08-02). Win32 provides the
parallel `TlsAlloc`, `TlsSetValue`, `TlsGetValue`, and `TlsFree` family.

**External vs. internal Collection storage.** The paper names and evaluates
both shapes for where a thread's Collection physically lives. External storage
keeps "a global mapping of each thread's ID to its TS Object Collection
table," which "may require the use of a readers/writer lock to prevent race
conditions" at the moment of locating the Collection, though "once the
collection is located ... no additional locking is required since only one
thread can be active within a TS Object Collection" (TSS pattern PDF, section
7.2, verified 2026-08-02). Internal storage keeps each thread's Collection
inside the thread's own control block, so "this presents no problem for
internal implementations since the thread ID is implicitly associated with
the corresponding TS Object Collection contained in the thread's state" (same
source). Most production TLS implementations use the internal shape today,
because it avoids the lookup-time lock entirely; the paper's own diagram of
the internal shape shows the thread directly indexing its private table by
key with O(1) cost when the key range is fixed and small (same source,
Figure 5).

**Language-level keyword or attribute.** C11 introduces `_Thread_local` and
C++11 introduces the `thread_local` storage-duration specifier, described by
Microsoft's own MSVC documentation as "the recommended way to specify
thread-local storage for objects and class members," compiled to allocate a
separate copy of the marked variable for every thread rather than requiring an
explicit key ([Microsoft Learn, "Thread Local Storage
(TLS)"](https://learn.microsoft.com/en-us/cpp/parallel/thread-local-storage-tls?view=msvc-170),
verified 2026-08-02). C# provides the analogous `[ThreadStatic]` attribute on
a static field, whose own reference documentation warns that "don't specify
initial values for fields marked with ThreadStaticAttribute. Such
initialization occurs only once, when the class constructor executes, and
therefore affects only one thread" ([Microsoft Learn, "ThreadStaticAttribute
Class"](https://learn.microsoft.com/en-us/dotnet/api/system.threadstaticattribute),
verified 2026-08-02), which is a language-level surfacing of exactly the
lazily-initialized-per-thread concern the paper's own C++ template wrapper was
built to hide from application code.

**Boxed per-thread object accessed through a typed accessor, the TS Object
Proxy made concrete.** The pattern's own preferred production shape, and the
one every language example in dimension 9 below actually demonstrates in some
form. A single object owns a key or a `thread_local` slot and exposes a
typed `get`/`set` pair, or in C++'s smart-pointer form described in the
paper, overloads `operator->` so that "the C++ compiler replaces this call
with two method calls," a lookup that "returns a Logger instance residing in
thread-specific storage," followed by the ordinary method call on that
instance, so that "TSS behaves as a proxy that allows an application to
access and manipulate the thread-specific error value as if it were an
ordinary C++ object" (TSS pattern PDF, section 9.2, verified 2026-08-02).
Every access site reads as an ordinary field or method access, and the
key-based indirection disappears entirely from application code.

**Lazily-initialized class-attribute form (Python).** Python's
`threading.local` class is subclassed, and, per the language's own
documentation, "if you define an `__init__()` method, it will be called each
time the `local` object is used in a separate thread. This is necessary to
initialize each thread's dictionary" ([Python 3 documentation, `threading`,
"Thread-Local Data"](https://docs.python.org/3/library/threading.html#thread-local-data),
verified 2026-08-02). This is the same lazy-initialization idea as the
default creation method discussed in this family's Factory Method entry,
applied per thread instead of per call.

**Continuation-local or task-local storage, the async-native cousin.**
Where the unit of concurrency is a logical continuation rather than an OS
thread, the equivalent access point follows the continuation instead of a
thread identifier. Node.js's `AsyncLocalStorage` is the concrete example,
established once per request with `run()` and read anywhere downstream with
`getStore()`, and the runtime itself frames the relationship as an analogy
to, not an instance of, the classical pattern (Node.js API documentation,
"Asynchronous context tracking," verified 2026-08-02, quoted in full in
dimension 4). This variant is discussed further, and distinguished more
sharply, in dimension 13.

## 9. Known production uses

**The POSIX and Win32 `errno` mechanism.** The pattern's own headline example
and, per the paper itself, its most widely deployed instance. "The `errno`
mechanism implemented on OS platforms that support the POSIX and Solaris
threading APIs are widely-used examples of the Thread-Specific Storage
pattern. In addition, the C runtime library provided with Win32 supports
thread-specific `errno`. The Win32 `GetLastError`/`SetLastError` functions
also implement the Thread-Specific Storage pattern" (TSS pattern PDF, section
10, Known Uses, verified 2026-08-02).

**Win32 per-thread window message queues.** "In the Win32 operating system,
windows are owned by threads. Each thread that owns a window has a private
message queue where the OS enqueues user-interface events. API calls that
retrieve the next message waiting to be processed dequeue the next message on
the calling thread's message queue, which resides in thread-specific storage"
(same source, section 10).

**OpenGL rendering state on Win32.** "OpenGL is a C API for rendering
three-dimensional graphics... State variables set before the vertices are
passed to the library determine precisely what OpenGL draws as it receives
the vertices. This state is stored as encapsulated global variables within
the OpenGL library or on the graphics card itself. On the Win32 platform, the
OpenGL library maintains a unique set of state variables in thread-specific
storage for each thread using the library" (same source, section 10).

**The ACE network programming toolkit.** The paper's own authors' toolkit.
"Thread-specific storage is used within the ACE network programming toolkit
to implement its error handling scheme, which is similar to the Logger
approach described in Section 9.2.3. In addition, ACE implements the
type-safe thread-specific storage template wrappers described in Section 9"
(same source, section 10).

**Apache Log4j 2's ThreadContext, formerly the Mapped Diagnostic Context.**
A modern, independently documented and independently sourced instance beyond
the paper's own list. The Log4j 2 manual states that ThreadContext "facilitates
associating information with the executing thread and making this information
accessible to the rest of the logging system," describing the mechanism as
comparable to Java's ThreadLocal, and offers both a map-structured store, the Mapped
Diagnostic Context or MDC, and a stack-structured store, the Nested Diagnostic
Context or NDC ([Apache Log4j 2 manual, "Thread
Context"](https://logging.apache.org/log4j/2.x/manual/thread-context.html),
verified 2026-08-02). Application code sets a request identifier, a session
identifier, or a tenant identifier once at the top of a request handler, and
every log statement anywhere downstream on that same thread picks it up
implicitly, without the identifier being threaded through every intervening
function signature, which is the pattern's own governing forces from
dimension 3 playing out directly in a widely deployed logging framework.

## 10. Consequences

Positive.

- Eliminates locking on the hot read and write path entirely, because each
  thread's data is unreachable from any other thread. The paper's own summary
  is direct. "The Thread-Specific Storage pattern can be implemented so that
  no locking is needed to thread-specific data... This eliminates locking
  overhead for data shared within a thread, which is faster than acquiring
  and releasing a mutex" (TSS pattern PDF, section 6.1, verified 2026-08-02).
- Preserves existing, single-threaded-shaped APIs while a codebase moves to a
  multi-threaded environment, avoiding a rewrite of every call site to pass
  an extra parameter.
- Concentrates the low-level, error-prone key management inside one Proxy
  type, so, per the paper, "porting an application to another thread library
  ... only requires changing the TSS class, not any applications using the
  class" (TSS pattern PDF, section 9.2.4, verified 2026-08-02).
- Makes construction and destruction of the per-thread state a single
  decision expressed once in the class definition, described in the paper as
  "greater flexibility and transparency," where "changing a class to/from a
  thread-specific class simply requires changing how an object of the class
  is defined" (same source, section 9.2.4).
- Provides a natural home for caching an expensive-to-construct, non-shareable
  resource, a compiled pattern, a scratch buffer, a per-connection handle, so
  it is built once per thread rather than once per call.

Negative.

- Hides the structure of the application. The paper names this cost directly.
  "It hides the structure of the system. The use of thread-specific storage
  hides the relationships between objects in an application, potentially
  making the application harder to understand" (TSS pattern PDF, section 6.2,
  verified 2026-08-02).
- Encourages reaching for a thread-safe global variable in cases that did not
  need one. "It encourages the use of (thread-safe) global variables. Many
  applications do not require multiple threads to access thread-specific data
  via a common access point... A simpler approach, however, would represent
  each worker thread as an Active Object with an instance of the Logger stored
  internally" (same source, section 6.2).
- Grows memory linearly with the number of distinct threads that have ever
  touched a given key, which matters for a large or long-lived thread pool
  and is judgement drawn directly from the shape the pattern itself
  describes, not a claim the source paper makes as a numbered liability.
- Ties correctness to the thread that happens to be running, which reads
  correctly for a fixed one-thread-per-unit-of-work model and reads
  incorrectly the moment the runtime hands a continuation to a different
  thread mid-flight, covered further in dimension 4 and dimension 11.
- Makes the dependency on the state implicit rather than visible in a
  function's signature, which weakens the contract a reader or a test can
  read directly off the code.

## 11. Failure modes and misuse

**Stale value leaking across pooled-thread reuse.** Symptom. A worker in a
thread pool occasionally logs, or acts on, a request identifier, a tenant
identifier, or a security context that belongs to a completely different,
earlier request handled by the same physical thread. Cause. The
thread-specific slot is set once and never cleared or overwritten at the
start of the next unit of work assigned to that same thread, because
"physically unique for each thread" is not the same guarantee as "unique for
each unit of work," and a pooled thread outlives any single unit of work it
services. Fix. Set the slot explicitly at the start of
every unit of work handled by a pooled thread, always, regardless of whether
it was cleared by the previous consumer, and clear or overwrite it again when
the unit of work finishes if the runtime does not already reset
thread-local state at task boundaries.

**Memory retained past the point the value is needed.** Symptom. Heap usage
in a long-running server process grows in rough proportion to the total
number of worker threads that have ever run, not the number currently
active, and never comes back down. Cause. A large or heavyweight object was
placed into a thread-specific slot and nothing ever released it, while its
owning thread stays alive in a long-lived pool. Java's own `ThreadLocal`
documentation states the underlying garbage-collection contract precisely.
"Each thread holds an implicit reference to its copy of a thread-local
variable as long as the thread is alive and the `ThreadLocal` instance is
accessible; after a thread goes away, all of its copies of thread-local
instances are subject to garbage collection" ([Oracle Java SE 21 API
Specification, `java.lang.ThreadLocal`
class description](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/ThreadLocal.html),
verified 2026-08-02); the failure mode arises exactly because a pooled
thread does NOT go away between units of work. Fix. Call the runtime's
explicit removal operation, `remove()` in Java's `ThreadLocal`, when a unit
of work finishes and the slot's value is no longer needed, rather than
relying on the thread itself eventually exiting.

**Field initializer silently runs on only one thread.** Symptom. A
`[ThreadStatic]` field in C#, or an equivalent static-initializer-based
mechanism in another language, has the correct starting value on the thread
that first loaded the class, and an unexpected default, zero, empty string,
or null, on every other thread. Cause. Static field initializers execute
exactly once, at class construction time, on whichever thread happens to
trigger that construction, and a per-thread attribute does not make the
initializer re-run per thread. Microsoft's own reference documentation states
this directly as a warning. "Don't specify initial values for fields marked
with ThreadStaticAttribute. Such initialization occurs only once, when the
class constructor executes, and therefore affects only one thread. If you
don't specify an initial value, the field will be initialized to its default
value" ([Microsoft Learn, "ThreadStaticAttribute
Class," Remarks](https://learn.microsoft.com/en-us/dotnet/api/system.threadstaticattribute),
verified 2026-08-02). Fix. Initialize the value explicitly and lazily inside
the accessor, checking for the runtime's default and constructing the real
initial value on first access per thread, rather than in a field initializer
or a class constructor.

**Global state reached through the pattern breaks unit test isolation.**
Symptom. A test passes in isolation and fails, or intermittently fails, when
run as part of a larger suite, particularly a suite that reuses a fixed pool
of test-runner threads across test cases. Cause. A value one test set into
thread-specific storage was never cleared and is still present when the next
test case runs on the same pooled thread. This is a special case of the
first failure mode above, made worse because test frameworks routinely reuse
worker threads across unrelated test cases for speed. Fix. Reset every
thread-specific slot the code under test could have touched in a test
teardown step, or run the affected tests on a freshly created thread rather
than a pooled one.

**Async and continuation-based frameworks silently losing the value across a
hop.** Symptom. Code that correctly reads a request-scoped value earlier in
a handler reads the wrong value, or an unset default, after an `await`, a
callback, or a scheduled continuation resumes, in an environment where the
runtime is free to resume that continuation on a different OS thread than the
one that started it. Cause. Thread-specific storage is keyed to the thread,
and the continuation is not guaranteed to keep running on the thread it
started on once it crosses a genuine asynchronous boundary. Fix. Use the
runtime's continuation-aware equivalent instead of the raw thread-local
mechanism, `AsyncLocalStorage` in Node.js or an equivalent flowed context in
another async runtime, both discussed in dimension 13, rather than reaching
for a literal thread-local variable in code that is not guaranteed to stay on
one OS thread for its whole logical lifetime.

**Unreachable key after the owning module is unloaded.** Symptom. A native
extension or plugin that created a thread-specific key is unloaded from the
process, and a subsequent access to that key from an unrelated thread crashes
or returns garbage rather than a clean error. Cause. The key was never
released with the platform's deletion call before the code that defined its
destructor callback left memory. Fix. Release every created key with the
matching deletion call, `pthread_key_delete` on POSIX or `TlsFree` on Win32,
during the owning module's own teardown, before that module's code becomes
unreachable.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Thread-Specific Storage | Explicit parameter passing | Shared state plus a lock (Monitor Object) | Continuation-local storage (AsyncLocalStorage / task-local) | Active Object with private instance state |
|---|---|---|---|---|---|
| Locking cost on access | None. Each thread's slot is unreachable from other threads | None. No shared mutable state exists | Present on every access | None on the fast path. Propagation cost is paid once at continuation creation | None. State lives inside the Active Object's own instance, one per servant |
| API stability for existing callers | High. No new parameter needed | Low. Every intermediate signature in the call chain changes | High for the shared object, but callers must still acquire the lock correctly | High. No new parameter needed | Low. Callers address the Active Object explicitly, not a global name |
| Discoverability of the dependency | Low. Hidden behind a global access point | High. Visible in every signature | Medium. The shared object is visible, the locking discipline is not | Low. Hidden behind a global access point, same cost as thread-specific storage | Medium. The dependency is on a specific object instance, addressed explicitly |
| Correct under thread pool reuse without extra effort | No. Requires explicit reset per unit of work | Yes. Nothing is retained implicitly | Yes for the shared data, contention aside | Yes, by construction, since scope follows the continuation, not the thread | Yes. State belongs to the servant object, not the calling thread |
| Correct across an async hop to a different OS thread | No. The value is bound to the thread that set it | Yes, the value travels with the explicit parameter regardless of which thread resumes the work | Not applicable to this axis | Yes. This is exactly the case it was built for | Yes. The message queue, not the OS thread, carries the request |
| Memory cost | Grows with the number of distinct threads that have used a key | None beyond the value itself | One shared copy regardless of thread count | Grows with the number of live continuations, not threads | One copy per servant instance |
| Suits collaborative shared data between threads | No. Explicitly excluded by the pattern's own applicability list | No, unless the shared object itself is passed | Yes. This is the case it exists for | No | Possible, via messages to the shared servant |

Reading of the table. Thread-Specific Storage wins decisively on locking cost
and on leaving an existing single-threaded API untouched, and it loses
decisively the moment either the concurrency unit is not a genuine OS thread
or the state must be shared rather than merely made globally reachable.
Explicit parameter passing is strictly more correct in every row except
locking cost, at the price of touching every intermediate signature, which is
exactly the cost the pattern's applicability section says to accept when the
call chain is short. Continuation-local storage occupies almost the same cell
as Thread-Specific Storage on discoverability and API stability while fixing
the one row that actually breaks in modern async servers, correctness across a
resumed continuation, which is why it has displaced the classical pattern in
async-native runtimes, discussed further in dimension 13.

## 13. Related and incompatible patterns

- **Singleton.** The paper's own related-patterns section states the
  relationship directly. "Objects implemented with thread-specific storage
  are often used as per-thread Singletons... e.g., errno is a per-thread
  Singleton. Not all uses of thread-specific storage are Singletons, however,
  since a thread can have multiple instances of a type allocated from
  thread-specific storage" (TSS pattern PDF, section 11, verified 2026-08-02).
  Thread-Specific Storage is best understood as Singleton's scope relaxed from
  "one instance per process" to "one instance per thread per process," using
  the same intent, one logically global access point, with the uniqueness
  constraint narrowed.
- **Proxy.** The paper names its own TSS wrapper class as playing this role
  directly. "The TSS template class shown in Section 8 serves as a Proxy
  which shields the libraries, frameworks, and applications from the
  implementation of thread-specific storage provided by OS thread libraries"
  (same source, section 11). The TS Object Proxy participant in dimension 5
  is a literal instance of the Proxy pattern applied to the raw key-based API.
- **Double-Checked Locking Optimization.** A frequent companion at
  initialization time. The paper states that "the Double-Checked Locking
  Optimization pattern is commonly used by applications that utilize the
  Thread-Specific Storage pattern to avoid constraining the order of
  initialization for thread-specific storage keys" (same source, section 11).
  Creating a key is itself a one-time, process-wide operation that competing
  threads must not perform redundantly or race on, which is exactly the
  problem Double-Checked Locking addresses.
- **Active Object and Monitor Object.** Substitutes rather than companions
  for the specific liability the paper itself calls out. Where a value is
  reached via a global access point purely to avoid passing it as a
  parameter, but does not actually need to be visible to unrelated code, the
  paper's own Liabilities discussion recommends representing the owning
  worker as an Active Object holding the state internally instead (TSS
  pattern PDF, section 6.2, verified 2026-08-02, quoted in full in dimension
  10). Monitor Object plays a comparable role when the state genuinely must
  be shared, at which point Thread-Specific Storage's applicability is
  excluded entirely, per dimension 4.
- **Continuation-local and task-local storage (a modern sibling, not from the
  same paper).** Node.js `AsyncLocalStorage` and equivalent task-local
  mechanisms in other async runtimes solve the identical shaped problem, a
  logically global access point for state that is physically private to one
  execution context, using an execution context that is a continuation or a
  structured-concurrency task rather than an OS thread. Node's own
  documentation frames the relationship as an analogy, describing
  `AsyncLocalStorage` as "similar to thread-local storage in other languages"
  (Node.js API documentation, "Asynchronous context tracking," verified
  2026-08-02). The two are not interchangeable implementations of one
  pattern, because their scoping rules differ in exactly the case that
  matters, an execution resuming on a different OS thread, see dimension 4
  and dimension 12.
- **Half-Sync/Half-Async and Leader/Followers, the sibling ACE-program
  patterns in this family.** Both organize which thread runs a given piece of
  work. Thread-Specific Storage is orthogonal to that decision. It governs
  what happens to state once a thread is already running, and composes
  cleanly with either dispatch pattern as long as the dispatch pattern
  guarantees a stable one-thread-per-unit-of-work assignment for the duration
  the state must remain valid, which Leader/Followers does and a
  work-stealing or continuation-hopping scheduler does not.

## 14. Refactoring path in and out

Introducing the pattern into code that currently threads a value explicitly
through every call, or currently uses an unsynchronized global variable that
happens to work only because the application is still single-threaded.

1. Confirm the value genuinely fits the pattern's applicability list from
   dimension 4. Logically one access point, physically one copy per thread,
   accessed only within sequences of calls made by the owning thread, never
   shared for collaboration between threads.
2. Wrap the raw platform mechanism, `pthread_key_create` and its pair, the
   language's `thread_local` keyword, or the runtime's `ThreadLocal`-shaped
   class, behind one small typed accessor type. Do this even for a single
   call site. The wrapping is what makes the eventual portability and testing
   benefits from dimensions 10 and 15 available at all.
3. Replace the single-threaded global variable, or the explicit parameter at
   the shallowest call sites, with a call through the new accessor. Run the
   existing tests after each call site is converted, one at a time, rather
   than converting the whole call graph in one change.
4. Decide the initialization discipline explicitly. Either the accessor lazily
   constructs a default value on first access per thread, following Python's
   own `__init__`-per-thread convention described in dimension 8, or the
   accessor requires an explicit `set` before any `get`, following the
   errno-style discipline where the operating system itself always sets the
   slot before application code ever reads it. Do not leave this to a
   language-level field initializer, per the failure mode in dimension 11.
5. Add explicit reset or removal at the boundary of whichever unit of work
   owns the value's lifetime, before this code ever runs on a pooled thread,
   per the stale-value failure mode in dimension 11, even if the current
   deployment does not yet use a thread pool.
6. Add the type-per-thread assertion test described in dimension 15 so a
   missing reset, or a value that leaked from one unit of work into the next,
   fails a test rather than surfacing as a production incident.

Removing the pattern once the reasons that motivated it no longer apply,
which most commonly happens when a codebase migrates from a
thread-per-request model to an async or task-based concurrency model.

1. Confirm the trigger. Either the state is now provably only ever touched
   inside one short call chain, so an explicit parameter costs nothing extra,
   or the runtime's unit of concurrency is no longer a stable OS thread for
   the duration the state must remain valid, which makes the pattern
   incorrect rather than merely unneeded, per dimension 4.
2. If the call chain is short, thread the value through as an explicit
   parameter one call site at a time, starting from the deepest caller and
   working outward, running tests after each conversion, then delete the
   thread-specific accessor once nothing calls it.
3. If the concurrency unit changed, replace the thread-local accessor with the
   equivalent continuation-scoped or task-scoped primitive for the runtime in
   use, `AsyncLocalStorage` in Node.js or the equivalent in another async
   runtime, keeping the same public accessor shape so call sites change
   minimally, then delete the old thread-local implementation once the new
   one is verified against the failure mode it exists to fix, a value read
   correctly across a resumed continuation on a different OS thread.
4. Delete the now-unused key creation and deletion calls, and confirm with the
   platform's own tooling, or a heap profiler, that the per-thread memory
   growth described in dimension 10 has actually gone away.

## 15. Testing and verification

Easier because of the pattern.

- A test can construct a fresh per-thread accessor instance, bypassing the
  process-wide global, and assert the isolation property directly by reading
  and writing from two spawned threads and confirming neither observes the
  other's write. This exercises the pattern's own core guarantee as a direct,
  fast, deterministic unit test rather than requiring a real concurrent
  production scenario to reproduce a bug.
- Because the underlying storage is opaque behind the Proxy from dimension 5,
  a test-only implementation of the same accessor interface can substitute a
  plain, non-thread-local field for single-threaded test code that does not
  need real thread isolation, keeping the test fast and free of any real
  threading.

Harder because of the pattern.

- A stale value bug, the leading failure mode from dimension 11, is
  by nature a cross-test-case, cross-invocation bug. It does not show up in
  a test that creates one fresh thread, exercises the accessor, and tears the
  thread down, because that is exactly the case where the pattern behaves
  correctly. It shows up only when a pooled thread is reused across two units
  of work, which many single-scenario unit tests never model.
- Assertions inside a spawned worker thread do not automatically fail the
  test that spawned it in most unit test frameworks, so an assertion failure
  raised on the wrong thread can be silently swallowed unless the test
  explicitly captures it and re-raises or records it on the main thread after
  joining.

Techniques that apply.

- **Cross-invocation reuse test.** Simulate a pooled thread by running two
  unrelated units of work on the identical, deliberately reused thread, and
  assert the second unit of work sees only its own state, never a residue
  from the first. This is the single most valuable test for this pattern
  because it targets the leading production failure mode directly rather than
  the easy, already-correct single-use case.
- **Explicit removal assertion.** After a unit of work completes and calls
  whatever teardown or removal step it is supposed to call, assert the
  accessor's slot for that thread is back to its documented default rather
  than merely assuming the removal call succeeded.
- **Cross-thread isolation assertion.** Spawn N threads, have each set a
  distinct value and then read it back after a synchronization barrier that
  forces all N threads to have written before any of them reads, and assert
  every thread reads back only the value it itself wrote.
- **Async-hop regression test, where a continuation-based mechanism replaced
  a literal thread-local.** Force the runtime's scheduler to resume a
  continuation on a different worker thread than the one that started it,
  commonly reliable to trigger under a runtime with a small worker pool and
  an explicit yield, and assert the propagated value survives the hop. This
  is the test that would have caught the failure mode from dimension 11 if a
  team accidentally reached for a thread-local primitive where a
  continuation-local one was required.

## 16. Observability signals

What to record.

- A gauge of the number of distinct threads currently holding a live slot for
  a given key, so an operator can see the memory-growth risk from dimension
  10 before it becomes an incident, rather than discovering it from a heap
  dump after the fact.
- A counter, incremented on every explicit removal call, alongside a counter
  of every set call for the same key, so the two counters staying close
  together over a long-running window is direct evidence that units of work
  are actually cleaning up after themselves on pooled threads, and a growing
  gap between them is direct evidence they are not.
- For any accessor that lazily initializes on first access per thread, a
  counter of initializations, labelled by thread pool name where the
  application uses more than one pool, so an unexpectedly high
  initialization rate on a supposedly stable pool flags threads being
  recycled or replaced more often than expected.
- Where the pattern backs a diagnostic context such as Log4j's ThreadContext
  from dimension 9, confirmation, sampled periodically in a health check, that
  a value set at the top of a request handler is actually still present and
  correct by the time a downstream log statement fires, which catches the
  stale-context and lost-context failure modes from dimension 11 as a
  continuous production signal rather than only as a test.

A healthy instance on a dashboard. The live-slot gauge tracks the size of the
active thread pool and does not climb independently of it. The set and
removal counters for a given key stay within a small, stable delta of each
other over any sustained window. The lazy-initialization counter is flat once
a thread pool has warmed up, since every thread in a stable pool should
initialize its slot at most once.

A failing instance. The live-slot gauge climbs steadily while the actual
thread pool size stays flat, which is the unbounded-retention failure mode
from dimension 11 made visible before it becomes an out-of-memory incident.
The set and removal counters diverge over time, which is the stale-value
failure mode made visible as a number rather than discovered from a
misattributed log line or a customer report. The lazy-initialization counter
keeps climbing on a supposedly stable pool, which points at threads being
torn down and recreated more often than the deployment assumes, silently
paying the initialization cost on every replacement.

## 17. Security and privacy implications

**Cross-tenant or cross-request data leakage on a pooled thread.** This is
the pattern's single most serious security implication, and it is a direct
extension of the stale-value correctness failure mode from dimension 11 into
a confidentiality failure. If a pooled worker thread that has recently finished
serving tenant A's request is handed tenant B's request next, and the
handling code trusts the thread-specific slot without explicitly resetting
it, tenant B's request can read state, an authorization token, a partially
constructed response, a piece of tenant A's data, that was never meant for
it. Where the accessor backs a diagnostic or logging context, the same
failure mode can also cause tenant B's log lines to be mislabelled with
tenant A's identifier, corrupting an audit trail rather than merely leaking
data forward. The fix is the same as the correctness fix in dimension 11,
a mandatory reset at the start of every unit of work on a pooled thread,
but the stakes here are confidentiality and auditability rather than merely
a wrong log line, so this deserves to be treated as a security control, not
only a correctness nicety, on any pooled-thread server handling more than
one tenant or more than one authenticated principal.

**Sensitive data retained in memory past its useful lifetime.** Because the
underlying storage is bound to the thread rather than to an explicit,
garbage-collectable object with a clear owner, a credential, a decrypted
token, or personal data placed into a thread-specific slot can remain
resident in the process's memory for the entire lifetime of a long-lived
pooled thread, long after the request that needed it has finished, unless
the application explicitly clears the slot. This extends the ordinary
attack surface of a heap or core dump, or a memory-disclosure vulnerability
elsewhere in the same process, to cover data whose retention the application
never intended.

**Resource exhaustion through an unbounded key space.** Where a key, or the
identity used to select a per-thread slot, is derived even indirectly from
untrusted input rather than fixed at compile time or bounded by a fixed
thread pool size, an attacker who can cause the process to spawn threads, or
who can influence which keys get created, can drive the number of live
per-thread allocations up without a natural bound, which is a resource
exhaustion vector distinct from an ordinary memory leak because it scales
with attacker-controlled input rather than only with organic load. Bound the
set of keys to a fixed, application-controlled set decided at compile time
or at startup, never derived from a request.

On broader privacy the pattern is otherwise close to neutral in its classical,
process-internal form, in the same way this family's Factory Method entry
notes for its own pattern. Where the observability advice in dimension 16
recommends logging a thread identifier or a key name alongside slot metrics,
that identifier is not itself personal data, and the caution above about
retained sensitive data concerns the VALUE stored in the slot, not the
mechanism's own instrumentation.

## Code examples

Four languages, chosen to show the pattern's real range, from the raw
mechanism to a deliberate absence.

Python shows the language's own idiomatic, lazily-per-thread-initialized
form, closest in spirit to the paper's own C++ smart-pointer wrapper. Rust
shows the compiler-checked, macro-declared `thread_local!` form, the closest
modern analogue to C++11's `thread_local` keyword. Swift has no first-class
standard-library thread-local API, so the example below calls the same
POSIX `pthread_key_create`, `pthread_setspecific`, and `pthread_getspecific`
functions the pattern's own primary source describes, through Swift's
Darwin and Glibc interop, which demonstrates the raw mechanism from
dimension 8 directly rather than a language-level convenience wrapping it.
Go is included deliberately to show the pattern's own excluded case from
dimension 4 made concrete. Go provides no goroutine-local storage by design,
and idiomatic Go code threads the equivalent state through an explicit
`context.Context` parameter instead, which is the pattern's own
non-applicability case, not the pattern itself. All four programs implement
the same scenario, a request handler that sets a per-thread or per-goroutine
request identifier once, then calls two helper functions that log a message
tagged with that identifier without the identifier being passed to them as a
parameter, mirroring the shape of the paper's own `errno` and `Logger`
examples. All four were run and produced the expected per-thread or
per-goroutine tagged output, interleaved because the underlying threads or
goroutines run concurrently; the exact interleaving order is nondeterministic
and expected to vary between runs.

### Python

```python
import threading

_ctx = threading.local()


def current_request_id() -> str:
    return getattr(_ctx, "request_id", "-")


def log(message: str) -> None:
    print(f"[{current_request_id()}] {message}")


def handle_request(request_id: str) -> None:
    _ctx.request_id = request_id
    validate()
    process()


def validate() -> None:
    log("validating")


def process() -> None:
    log("processing")


def worker(n: int) -> None:
    handle_request(f"req-{n}")


threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

Run with `python3 tss.py`. Output observed on this machine, one interleaving
of three possible orderings.

```
[req-0] validating
[req-0] processing
[req-1] validating
[req-1] processing
[req-2] validating
[req-2] processing
```

`_ctx` is one shared `threading.local` instance, playing the TS Object Proxy
role from dimension 5. `getattr(_ctx, "request_id", "-")` supplies the lazy
default the errno-style discipline from dimension 14 calls for, without a
field initializer that would run on only one thread, the failure mode from
dimension 11.

### Rust

```rust
use std::cell::RefCell;
use std::thread;

thread_local! {
    static REQUEST_ID: RefCell<String> = RefCell::new(String::from("-"));
}

fn set_request_id(id: &str) {
    REQUEST_ID.with(|cell| *cell.borrow_mut() = id.to_string());
}

fn log(msg: &str) {
    REQUEST_ID.with(|cell| println!("[{}] {}", cell.borrow(), msg));
}

fn validate() {
    log("validating");
}

fn process() {
    log("processing");
}

fn handle_request(id: &str) {
    set_request_id(id);
    validate();
    process();
}

fn main() {
    let handles: Vec<_> = (0..3)
        .map(|n| thread::spawn(move || handle_request(&format!("req-{}", n))))
        .collect();
    for h in handles {
        h.join().unwrap();
    }
}
```

Compiled with `rustc -O tss.rs -o tss_rs` and run as `./tss_rs`. Output
observed on this machine.

```
[req-2] validating
[req-2] processing
[req-1] validating
[req-1] processing
[req-0] validating
[req-0] processing
```

`thread_local!` declares `REQUEST_ID` as a `LocalKey`, the Rust standard
library's own name for the TS Object Proxy role, and `.with()` is the
`getspecific`/`setspecific` access point from dimension 5, given only a
shared reference into a closure, which is why the value is wrapped in a
`RefCell` to allow mutation through that shared reference.

### Swift

```swift
#if canImport(Glibc)
import Glibc
#else
import Darwin
#endif
import Foundation

final class RequestBox {
    var id: String = "-"
}

var requestKey = pthread_key_t()
pthread_key_create(&requestKey) { rawPtr in
    Unmanaged<RequestBox>.fromOpaque(rawPtr).release()
}

func currentBox() -> RequestBox {
    if let raw = pthread_getspecific(requestKey) {
        return Unmanaged<RequestBox>.fromOpaque(raw).takeUnretainedValue()
    }
    let box = RequestBox()
    pthread_setspecific(requestKey, Unmanaged.passRetained(box).toOpaque())
    return box
}

func setRequestID(_ id: String) {
    currentBox().id = id
}

func log(_ message: String) {
    print("[\(currentBox().id)] \(message)")
}

func validate() { log("validating") }
func process() { log("processing") }

func handleRequest(_ id: String) {
    setRequestID(id)
    validate()
    process()
}

let group = DispatchGroup()
for n in 0..<3 {
    group.enter()
    Thread.detachNewThread {
        handleRequest("req-\(n)")
        group.leave()
    }
}
group.wait()
```

Compiled with `swiftc tss.swift -o tss_swift` and run as `./tss_swift`.
Output observed on this machine.

```
[req-0] validating
[req-0] processing
[req-1] validating
[req-1] processing
[req-2] validating
[req-2] processing
```

`pthread_key_create` takes an optional destructor, called by the runtime
when an owning thread exits, into which this example releases the retained
`RequestBox`, avoiding the unbounded-retention failure mode from dimension
11 for threads that exit cleanly. `currentBox()` plays the combined role of
the TS Object Proxy's `getspecific` path and the lazy-default discipline
from the Python example, constructing and retaining a fresh `RequestBox` on
first access per thread and returning the existing one on every later
access from that same thread. This is the raw mechanism from dimension 8,
written by hand rather than through a language keyword, because Swift's
standard library, unlike C++11, C11, or Rust, has no built-in `thread_local`
storage-duration specifier.

### Go, showing the excluded case rather than the pattern

```go
package main

import (
	"context"
	"fmt"
	"sync"
)

type reqIDKey struct{}

func withRequestID(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, reqIDKey{}, id)
}

func requestID(ctx context.Context) string {
	if v, ok := ctx.Value(reqIDKey{}).(string); ok {
		return v
	}
	return "-"
}

func logMsg(ctx context.Context, msg string) {
	fmt.Printf("[%s] %s\n", requestID(ctx), msg)
}

func validate(ctx context.Context) {
	logMsg(ctx, "validating")
}

func process(ctx context.Context) {
	logMsg(ctx, "processing")
}

func handleRequest(ctx context.Context, id string) {
	ctx = withRequestID(ctx, id)
	validate(ctx)
	process(ctx)
}

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			handleRequest(context.Background(), fmt.Sprintf("req-%d", n))
		}(i)
	}
	wg.Wait()
}
```

Run with `go run tss.go`. Output observed on this machine.

```
[req-2] validating
[req-2] processing
[req-1] validating
[req-1] processing
[req-0] validating
[req-0] processing
```

There is no goroutine-local key anywhere in this program, and that absence
is the point. `requestID` is carried through `context.Context`, passed as an
ordinary parameter to `validate` and `process` rather than reached through a
global access point, which is exactly the excluded case from dimension 4.
The Go FAQ's own stated reason, that a `net/http` handler must remain free
to fan work out to helper goroutines without those goroutines losing access
to the request's state, is precisely why this example threads `ctx`
explicitly rather than attempting a goroutine-keyed workaround.

## 18. References

1. Douglas C. Schmidt, Timothy H. Harrison, Nat Pryce. "Thread-Specific
   Storage for C/C++. An Object Behavioral Pattern for Accessing per-Thread
   State Efficiently." Proceedings of the 4th Pattern Languages of Programs
   Conference, Allerton Park, Illinois, September 1997. Also published in
   C++ Report, SIGS, Vol. 9, No. 10, November/December 1997.
   https://www.dre.vanderbilt.edu/~schmidt/PDF/TSS-pattern.pdf
   Verified 2026-08-02. Primary source for the problem, forces, structure,
   participants, collaborations, implementation variants, consequences,
   liabilities, known uses, and related patterns throughout this entry.
2. Douglas C. Schmidt. Patterns index page listing "Thread-Specific Storage"
   with its title, venue, and co-author attribution.
   https://www.dre.vanderbilt.edu/~schmidt/patterns-ace.html
   Verified 2026-08-02. Source for the paper's exact venue, date, and
   co-authorship confirmation in dimension 1.
3. Douglas C. Schmidt, Michael Stal, Hans Rohnert, Frank Buschmann.
   Pattern-Oriented Software Architecture Volume 2. Patterns for Concurrent
   and Networked Objects. John Wiley and Sons, 2000. ISBN 978-0-471-60695-6.
   Cited via the Wikipedia summary of the POSA series for author list, year,
   and ISBN, https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture
   Verified 2026-08-02. Named as the book most closely associated with the
   same ACE-program research group in dimension 1, with the chapter
   attribution explicitly left unconfirmed rather than asserted.
4. Wikipedia contributors. "Thread-local storage."
   https://en.wikipedia.org/wiki/Thread-local_storage
   Verified 2026-08-02. Source for the industry-standard "Thread-Local
   Storage" naming and the `pthread_key_create`/`pthread_key_delete`
   summary quoted in dimension 1.
5. Oracle. Java SE 21 API Specification, `java.lang.ThreadLocal`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/ThreadLocal.html
   Verified 2026-08-02. Source for the garbage-collection contract quoted in
   dimension 11.
6. Microsoft. "Thread Local Storage (TLS)," Visual C++ documentation.
   https://learn.microsoft.com/en-us/cpp/parallel/thread-local-storage-tls?view=msvc-170
   Verified 2026-08-02. Source for the C++11 `thread_local` description in
   dimension 8.
7. The Open Group. The Open Group Base Specifications Issue 7,
   `pthread_key_create`.
   https://pubs.opengroup.org/onlinepubs/9699919799/functions/pthread_key_create.html
   Verified 2026-08-02. Source for the POSIX key-creation contract quoted in
   dimension 8.
8. Python Software Foundation. Python 3 documentation, `threading` module,
   "Thread-Local Data."
   https://docs.python.org/3/library/threading.html#thread-local-data
   Verified 2026-08-02. Source for the per-thread `__init__` behaviour of
   `threading.local` quoted in dimension 8.
9. The Rust Project Developers. Rust standard library documentation,
   `std::thread_local` macro.
   https://doc.rust-lang.org/std/macro.thread_local.html
   Verified 2026-08-02. Source for the `LocalKey` and `.with()` description
   underlying the Rust code example.
10. The Go Authors. "Frequently Asked Questions (FAQ)," section "Why is
    there no goroutine ID?"
    https://go.dev/doc/faq
    Verified 2026-08-02. Source for Go's deliberate omission of
    goroutine-local storage, quoted in dimension 4.
11. Microsoft. "ThreadStaticAttribute Class," .NET API documentation.
    https://learn.microsoft.com/en-us/dotnet/api/system.threadstaticattribute
    Verified 2026-08-02. Source for the field-initializer warning quoted in
    dimension 11.
12. The Apache Software Foundation. Apache Log4j 2 manual, "Thread Context."
    https://logging.apache.org/log4j/2.x/manual/thread-context.html
    Verified 2026-08-02. Source for the ThreadContext/MDC production use in
    dimension 9.
13. OpenJS Foundation. Node.js API documentation, "Asynchronous context
    tracking."
    https://nodejs.org/api/async_context.html
    Verified 2026-08-02. Source for the `AsyncLocalStorage` description and
    its own self-comparison to thread-local storage, quoted in dimensions 4
    and 13.
