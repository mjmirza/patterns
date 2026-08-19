---
name: Double-Checked Locking
slug: double-checked-locking
family: 09-concurrency
category: Concurrency
aliases: [DCL, Double-Checked Locking Optimization, Lock Hint Pattern]
first_described: "Schmidt, Harrison 1996 (Pattern Languages of Program Design 3); further formalized by Schmidt, Stal, Rohnert, Buschmann 2000 in Pattern-Oriented Software Architecture Volume 2"
maturity: contested
related: [monitor-object, scoped-locking, thread-specific-storage, leader-followers, half-sync-half-async]
incompatible_with: []
verified: 2026-08-14
---

## 1. Name, aliases, and lineage

Double-Checked Locking, usually abbreviated DCL, was first written up as a
pattern by Douglas C. Schmidt and Tim Harrison in "Double-Checked Locking, An
Optimization Pattern for Efficiently Initializing and Accessing Thread-safe
Objects," published in Pattern Languages of Program Design 3 in 1996. The
pattern was later included in a more formal, cross-language form as the
Double-Checked Locking Optimization pattern in Pattern-Oriented Software
Architecture, Volume 2, Patterns for Concurrent and Networked Objects, by
Douglas Schmidt, Michael Stal, Hans Rohnert, and Frank Buschmann in 2000. It is
sometimes called the Lock Hint pattern because the unsynchronized first check
acts as a hint that the guarded resource is probably already initialized,
letting the caller skip the more expensive locked path.

The pattern occupies an unusual place in this catalog. Its structure, checking
a condition, taking a lock only when the condition looks unmet, and checking
the condition again inside the lock, is sound and is reused constantly inside
concurrency libraries. Its most famous historical instance, the naive C++ and
pre-2004 Java "lazy singleton with a raw pointer or reference field," is
broken under real compiler and processor behavior, and the C++ and Java
communities each spent years documenting exactly why. That history is why this
entry marks the pattern `contested`. the shape is trustworthy, the classic
handwritten singleton implementation of it usually is not, and readers arrive
at this page carrying the second belief about the first thing.

Bill Pugh, a professor who worked on the Java Memory Model revision that
eventually fixed the pattern in Java, and Douglas Schmidt himself, one of the
pattern's original authors, both published widely read explanations of why the
naive form fails. Pugh's page, hosted at the University of Maryland, remains
the most cited technical explanation of the Java case and is linked in
dimension 18 below (Pugh, "The 'Double-Checked Locking is Broken' Declaration,"
https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html,
verified 2026-08-14). Scott Meyers and Andrei Alexandrescu wrote the equivalent
analysis for C++ in "C++ and the Perils of Double-Checked Locking," Dr. Dobb's
Journal, 2004, which pushed the C++ standards committee toward the
`std::call_once` facility that C++11 eventually shipped as the safe
replacement.

## 2. Problem and context

A piece of expensive, shared state, a database connection pool, a parsed
configuration object, a cache of compiled regular expressions, a singleton
service object, needs to be created exactly once and then read by many
threads for the remaining lifetime of the process. Creating it is costly
enough, in time, memory, or side effects such as opening a socket, that
creating it eagerly at program startup is wasteful when the feature it backs
is rarely used, and creating it more than once is a correctness bug, not just
a performance loss, when the object owns a resource like a file handle or has
identity semantics that callers compare with equality.

The straightforward safe answer is to wrap the whole read-and-maybe-create
sequence in a lock. That is correct, but every subsequent read pays the cost
of acquiring a lock even after the object exists and will never change again.
On a system where this accessor is called millions of times a second, a
still-contended lock on the hot read path is a measurable throughput problem
even when the lock is almost never actually contended by a concurrent writer,
because acquiring an uncontended lock still costs a memory fence and, on some
runtimes, a kernel round trip if the lock has to arbitrate.

Double-checked locking exists to answer a narrower question. once the object
is built, can readers avoid the lock entirely while still being correct on
the rare occasion two threads race to build it for the first time. The
pattern's promise is that the lock is paid at most once per process, or a
bounded, small number of times under contention, rather than on every access
forever.

## 3. Forces

- **Latency versus safety.** The whole point of the pattern is shaving lock
  acquisition cost off the read path. Every version of the pattern trades some
  amount of implementation subtlety for that latency win, and the classic
  broken form traded away correctness it did not know it was giving up.
- **Memory visibility versus mutual exclusion.** A lock provides two things at
  once, one thread's exclusion of others, and a happens-before edge that makes
  writes made inside the lock visible to a later thread that later acquires
  the same lock. The naive first check reads the shared field with neither
  property, so it can observe a write that is not yet fully visible unless the
  language's memory model, and the field's declaration, specifically promise
  otherwise.
- **Compiler and processor freedom versus programmer intuition.** Both
  compilers and CPUs are permitted to reorder independent memory operations as
  long as the reordering is invisible to a single thread of execution. A
  constructor call followed by a store into a shared field looks like two
  sequential steps to the programmer and is, to the compiler and the
  processor, two independent operations with no ordering requirement between
  them unless a memory barrier is inserted. This is the force that actually
  breaks the naive pattern, and it is invisible in source code.
- **Portability versus platform-specific correctness.** A hand-rolled DCL
  implementation that happens to work on x86, whose strong memory model
  forgives a lot of missing barriers, can fail on ARM or POWER, whose weaker
  memory models permit more reordering. A pattern whose correctness depends on
  the target processor is a portability liability that is easy to miss in
  testing on a single architecture.
- **Reinventing versus reusing a language-provided primitive.** Nearly every
  modern language now ships a built-in "run this exactly once, safely" utility
  (`std::call_once` in C++, `sync.Once` in Go, `std::sync::Once` and
  `std::sync::OnceLock` in Rust, the volatile-holder-field idiom or
  `ConcurrentHashMap.computeIfAbsent` in Java, `Lazy<T>` in .NET). The force
  here is whether to trust a heavily reviewed standard-library primitive or to
  hand-write the check-lock-check sequence again, and get it subtly wrong.

## 4. Applicability and non-applicability

Reach for double-checked locking, or more precisely for the language's
correctly fenced version of it, when all of the following hold.

- The guarded value is created once and never mutated again after
  construction completes, so a reader that observes a fully constructed value
  never needs to re-synchronize with future writes.
- The uncontended read path is called often enough that a lock on every call
  is a measured bottleneck, not a guessed one. Profile first.
- The target language and runtime give you a real, documented way to publish
  the reference safely, a `volatile` field in Java, a fenced pointer store in
  C++ or Rust, an atomic with acquire and release ordering, or, better, a
  built-in once-primitive.
- Constructing the guarded value is expensive or has an observable side
  effect (opening a connection, allocating a large buffer) that must not
  happen more than once, so an unsynchronized "just build it every time and
  let the last write win" strategy is unacceptable.

Do not reach for it, and this list matters more than the first one, when any
of these hold.

- The language or runtime does not give you a memory-model-safe way to
  publish the reference. Writing DCL in a language whose specification says
  nothing about ordering, or where you are not certain the ordering
  guarantee applies to the exact construct you used, reproduces the classic
  bug.
- A ready-made once-primitive exists in the standard library. `sync.Once`,
  `std::call_once`, `std::sync::OnceLock`, or an equivalent almost always
  outperforms, and is far easier to review than, a hand-rolled version, and
  the "known production uses" in dimension 9 show that even expert teams
  prefer to build the primitive once and reuse it rather than reimplement DCL
  at every call site.
- The guarded object needs to be re-created or invalidated later, for example
  a cache entry with a TTL. DCL is shaped for exactly-once initialization; a
  value with a lifecycle wants a different pattern such as
  Monitor Object, a read-write lock over a mutable reference, or an atomic
  swap of an immutable snapshot.
- The construction cost is small. If building the object is cheap, a plain
  lock around the whole accessor, or eager initialization at startup, is
  simpler and the double-checked structure adds cognitive load for a latency
  win nobody will notice.
- You are working in a language with a global interpreter lock that already
  serializes bytecode execution, such as CPython. The naive form of DCL is
  usually harmless there because the GIL supplies the missing happens-before
  edge as a side effect, but relying on that is relying on an implementation
  detail of one interpreter, not a language guarantee, and it silently breaks
  on a free-threaded build or a different Python implementation. See
  dimension 8 for the fully corrected treatment.
- Correctness is more valuable than the saved lock acquisition and the team
  cannot commit to keeping the memory-ordering annotations correct through
  future refactors. A plain synchronized accessor that is obviously correct
  beats a fast accessor that is subtly wrong.

## 5. Structure

- **Guard field.** The reference or value being lazily constructed, stored in
  a location the language's memory model allows to be published safely
  across threads, a `volatile` field in Java, an atomic pointer or atomic
  wrapper in C++ and Rust, or a variable published only through a
  once-primitive.
- **Fast path check.** An unsynchronized read of the guard field. Taken by
  every caller after the value exists, and it is this read that must observe
  a fully constructed object, never a partially constructed one and never a
  stale null.
- **Lock.** A mutual-exclusion primitive, a mutex, a monitor, or a
  synchronized block, acquired only when the fast path check suggests the
  value is not yet built.
- **Slow path check.** A second read of the guard field, performed after the
  lock is held. This is the check that actually prevents two threads from
  both constructing the object, because only one thread can hold the lock at
  a time, and the second thread to arrive will see the first thread's
  finished write.
- **Construction and publication.** The expensive object is built, fully
  initialized, and only then assigned to the guard field, in that exact
  order, with a memory barrier or an equivalent language guarantee that keeps
  the assignment invisible to another thread until construction has
  completed.

## 6. ASCII structure diagram

```
                +-------------------------------+
                |           Accessor            |
                |  getInstance() / Value getter |
                +-------------------------------+
                              |
                              v
                +-------------------------------+
                |  Guard field (published via    |
                |  volatile / atomic / Once)     |
                +-------------------------------+
                   ^          ^              ^
       fast read   |          |  lock/unlock |   slow read + write
   (no lock, most  |          |              |   (locked, first
     calls land    |    +-----+-----+        |   builder only)
        here)      |    |    Lock    |       |
                    |    | (mutex or |       |
                    |    | monitor)  |       |
                    |    +-----+-----+        |
                    |          |              |
                    +----------+--------------+
                              |
                              v
                +-------------------------------+
                |     Guarded expensive object    |
                |  (connection pool, cache, ...)  |
                +-------------------------------+
```

## 7. Dynamics

The two interesting timelines are the uncontended steady state, which is the
whole reason the pattern exists, and the first-race timeline, which is the
part that is easy to get wrong.

```
Steady state, object already built, N callers, no lock ever taken.

Thread A  --read guard--> [non-null] --return-->
Thread B  --read guard--> [non-null] --return-->
Thread C  --read guard--> [non-null] --return-->
(no lock acquired by anyone; this is the fast path DCL exists to provide)


First race, two threads arrive before construction.

Thread A                          Thread B
  |                                  |
  | read guard -> null               | read guard -> null
  | acquire lock (wins race)         | try acquire lock (blocks)
  | read guard again -> still null   |    ... blocked ...
  | construct object                 |    ... blocked ...
  | publish: guard = object          |    ... blocked ...
  |   (write must be ordered after   |
  |    construction completes)       |
  | release lock                     |
  |                                  | acquire lock (now free)
  |                                  | read guard again -> object
  |                                  |   (sees A's fully built object,
  |                                  |    skips construction)
  |                                  | release lock
  |                                  | return object
  v                                  v
return object                    return object


Broken variant, no memory barrier between construction and publication.

Thread A                          Thread B
  | allocate memory for object       |
  | write guard = <raw address>      |  <- reordered ahead of the
  |   (compiler/CPU may reorder      |     constructor's field writes
  |    this store earlier than       |     on this thread's view
  |    the constructor body)         |
  | run constructor body,            | read guard -> non-null (fast path!)
  |   writing object's fields        | read object's fields
  |                                  |   -> sees zeroed / partial state
  |                                  |   (the constructor has not
  |                                  |    finished from B's perspective)
```

The broken variant is not a hypothetical. It is exactly the bug that Pugh's
page and the Meyers and Alexandrescu article each document for Java and C++
respectively, and it is why dimension 8 spends so much space on the specific
fix for each ecosystem rather than presenting one pseudocode block and calling
the pattern solved.

## 8. Implementation variants

### Java, pre-5.0 (broken) and 5.0-and-later (fixed with volatile)

Before Java 5.0, the language specification did not guarantee that a write to
a plain field inside a constructor happened-before a later unsynchronized
read of a reference to that object from another thread, so the naive pattern
below could publish a partially constructed object.

```java
// BROKEN before Java 5.0, and broken today if instance is not volatile.
class BrokenSingleton {
    static class Config { final int value = 42; }
    private static Config instance; // no volatile, no ordering guarantee
    static Config getInstance() {
        if (instance == null) {
            synchronized (BrokenSingleton.class) {
                if (instance == null) {
                    instance = new Config(); // may publish before ctor finishes
                }
            }
        }
        return instance;
    }
}
```

The 2004 Java Memory Model revision, JSR 133, strengthened the semantics of
the `volatile` keyword so that a write to a volatile field happens-before
every later read of that same field by another thread, and it made that
guarantee interact correctly with the object's constructor writes as well.
Declaring the guard field `volatile` is the entire fix, and it is the
canonical, working, memory-model-legal form of the pattern in Java today.

```java
import java.util.concurrent.atomic.AtomicInteger;

public class DCL {
    private static volatile Config instance;
    private static final AtomicInteger constructions = new AtomicInteger(0);

    static class Config {
        final int value;
        Config() {
            constructions.incrementAndGet();
            this.value = 42;
        }
    }

    static Config getInstance() {
        Config result = instance;              // one volatile read, fast path
        if (result == null) {
            synchronized (DCL.class) {
                result = instance;              // re-check under the lock
                if (result == null) {
                    instance = result = new Config();
                }
            }
        }
        return result;
    }

    public static void main(String[] args) throws InterruptedException {
        int threadCount = 64;
        Thread[] threads = new Thread[threadCount];
        for (int i = 0; i < threadCount; i++) {
            threads[i] = new Thread(DCL::getInstance);
        }
        for (Thread t : threads) t.start();
        for (Thread t : threads) t.join();
        if (constructions.get() != 1) {
            throw new AssertionError("expected exactly one construction");
        }
        System.out.println("constructions=" + constructions.get()
            + " value=" + getInstance().value);
    }
}
```

Bloch's community and the wider Java literature generally still prefer the
initialization-on-demand holder idiom over a hand-written volatile DCL for a
plain lazy singleton, because it delegates the once-only guarantee to the
class loader instead of to a hand-checked memory-ordering argument. that
idiom, however, is a different pattern from DCL, not a variant of it, and the
choice between the two is engineering judgement rather than a sourced
mandate.

### Go, hand-rolled with atomics versus the standard sync.Once

Go's memory model, formalized in the Go specification, provides a
happens-before guarantee for the `sync/atomic` package's operations, so a
hand-rolled DCL can be written correctly using an atomic pointer for the
guard field. The Go team's own standard library, however, already ships the
primitive most code should use.

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type Config struct{ Value int }

var (
	instance     atomic.Pointer[Config]
	mu           sync.Mutex
	constructCnt atomic.Int32
)

func getInstance() *Config {
	if p := instance.Load(); p != nil {
		return p // fast path, no lock
	}
	mu.Lock()
	defer mu.Unlock()
	if p := instance.Load(); p != nil {
		return p // slow-path re-check
	}
	c := &Config{Value: 42}
	constructCnt.Add(1)
	instance.Store(c)
	return c
}

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 64; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); getInstance() }()
	}
	wg.Wait()
	if constructCnt.Load() != 1 {
		panic("expected exactly one construction")
	}
	fmt.Println("hand-rolled constructions=", constructCnt.Load())

	// The idiomatic replacement: sync.Once does the same check-lock-check
	// internally and is what real Go code should use instead.
	var once sync.Once
	var onceCnt atomic.Int32
	var wg2 sync.WaitGroup
	for i := 0; i < 64; i++ {
		wg2.Add(1)
		go func() { defer wg2.Done(); once.Do(func() { onceCnt.Add(1) }) }()
	}
	wg2.Wait()
	if onceCnt.Load() != 1 {
		panic("sync.Once should run exactly once")
	}
	fmt.Println("sync.Once constructions=", onceCnt.Load())
}
```

The Go standard library documentation for sync.Once states that the return
from f "synchronizes before" the return of any call of once.Do(f), which is
exactly the happens-before edge dimension 7's broken timeline was missing
(Go standard library, `sync` package documentation,
https://pkg.go.dev/sync#Once, verified 2026-08-14). sync.Once's own
implementation, inside the Go runtime source, is itself a fenced,
correctly-ordered version of the double-checked locking structure, so the
pattern is not avoided in Go so much as it is centralized into one audited
implementation that every program shares.

### Rust, AtomicPtr with explicit ordering versus std::sync::OnceLock

Rust requires the programmer to name the memory ordering on every atomic
operation, which makes the fast-path-versus-slow-path distinction, and the
acquire and release pairing that makes it safe, explicit in the source rather
than implicit in a keyword.

```rust
use std::sync::atomic::{AtomicPtr, AtomicI32, Ordering};
use std::sync::{Mutex, OnceLock};
use std::thread;
use std::ptr;

struct Config { value: i32 }

static INSTANCE: AtomicPtr<Config> = AtomicPtr::new(ptr::null_mut());
static LOCK: Mutex<()> = Mutex::new(());
static CONSTRUCTIONS: AtomicI32 = AtomicI32::new(0);

fn get_instance() -> &'static Config {
    let p = INSTANCE.load(Ordering::Acquire); // fast path
    if !p.is_null() {
        return unsafe { &*p };
    }
    let _guard = LOCK.lock().unwrap();
    let p = INSTANCE.load(Ordering::Acquire); // slow-path re-check
    if !p.is_null() {
        return unsafe { &*p };
    }
    CONSTRUCTIONS.fetch_add(1, Ordering::SeqCst);
    let boxed = Box::new(Config { value: 42 });
    let raw = Box::into_raw(boxed);
    INSTANCE.store(raw, Ordering::Release); // publish after construction
    unsafe { &*raw }
}

fn main() {
    let handles: Vec<_> = (0..64).map(|_| thread::spawn(get_instance)).collect();
    for h in handles { h.join().unwrap(); }
    assert_eq!(CONSTRUCTIONS.load(Ordering::SeqCst), 1,
        "expected exactly one construction");
    println!("hand-rolled constructions={}", CONSTRUCTIONS.load(Ordering::SeqCst));

    // The idiomatic replacement.
    static CELL: OnceLock<Config> = OnceLock::new();
    let handles: Vec<_> = (0..64)
        .map(|_| thread::spawn(|| CELL.get_or_init(|| Config { value: 7 }).value))
        .collect();
    for h in handles { h.join().unwrap(); }
    println!("OnceLock value={}", CELL.get().unwrap().value);
}
```

Rust's standard library documents Once::call_once as guaranteeing that any
memory writes performed by the executed closure can be reliably observed by
other threads at this point, because there is a happens-before relation
between the closure and code executing after the return (Rust standard
library, `std::sync::Once` documentation,
https://doc.rust-lang.org/std/sync/struct.Once.html, verified 2026-08-14).
The same page notes that OnceLock<T> supersedes Once in functionality and
should be preferred for the common case where the Once is associated with
data, which is precisely the lazy-singleton use case DCL targets, and is the
reason the working code above ends on OnceLock rather than on the raw
AtomicPtr version.

### Python, the GIL caveat and the portable fix

CPython's Global Interpreter Lock guarantees that only one thread executes
Python bytecode at a time (Python 3 documentation, Glossary entry for
Global Interpreter Lock,
https://docs.python.org/3/glossary.html#term-global-interpreter-lock,
verified 2026-08-14), which in practice serializes the individual bytecode
operations that make up an assignment or an attribute read closely enough
that the classic reordering bug from dimension 7 is very hard to trigger on
stock CPython. Relying on that is still a mistake worth naming explicitly,
because it depends on an implementation detail of one interpreter, the
standard, GIL-enabled build, rather than on a language guarantee, it does not
hold on the free-threaded, no-GIL CPython build that Python 3.13 introduced
as an opt-in configuration, and it is not something a reader transplanting
the pattern into another Python implementation, or into a different language
entirely, should ever copy as if it were portable reasoning. Writing the
pattern with an explicit lock the whole time it is uncontended, which is what
most idiomatic Python code does, sacrifices the DCL optimization entirely but
removes the platform-dependent argument.

```python
import threading

class Config:
    def __init__(self):
        self.value = 42

_instance = None
_lock = threading.Lock()
_constructions = 0

def get_instance():
    global _instance, _constructions
    result = _instance
    if result is None:
        with _lock:
            result = _instance
            if result is None:
                _constructions += 1
                result = Config()
                _instance = result
    return result

threads = [threading.Thread(target=get_instance) for _ in range(64)]
for t in threads: t.start()
for t in threads: t.join()
assert _constructions == 1, "expected exactly one construction"
print(f"constructions={_constructions} value={get_instance().value}")
```

Most production Python code sidesteps the whole question by initializing the
module-level singleton at import time, relying on the import system's own
one-time-execution guarantee, or by using functools.lru_cache with an
unbounded size on a zero-argument factory function, which is safe under the
GIL for the same reason the pattern above is.

### C++, the historically broken form and std::call_once

C++ has no ecosystem-wide answer as clean as Java's single volatile keyword,
because the language exposes the underlying memory model directly and,
before C++11, had no standardized threading model at all, which is exactly
the gap Meyers and Alexandrescu's 2004 article was written into. C++11 closed
the gap with std::once_flag and std::call_once, and current guidance is to
use that facility, or a static local variable inside a function, whose
initialization the C++11 standard mandates to be thread-safe, rather than a
hand-written double-checked structure.

```cpp
#include <mutex>

struct Config { int value; };

std::once_flag flag;
Config* instance = nullptr;

Config& get_instance() {
    std::call_once(flag, [] { instance = new Config{42}; });
    return *instance;
}

// Simpler and equally safe: C++11 guarantees thread-safe static local init.
Config& get_instance_static_local() {
    static Config instance{42};
    return instance;
}
```

## 9. Known production uses

- **Spring Framework's singleton bean cache.** Spring's
  `DefaultSingletonBeanRegistry.getSingleton` reads the singletonObjects map
  outside any lock first, and only takes an explicit lock (a ReentrantLock
  field named singletonLock in current versions, historically a synchronized
  block on the map itself) and re-checks the map if the first, unsynchronized
  read finds nothing, which is the double-checked structure applied to the
  whole Spring ApplicationContext's bean lifecycle (Spring Framework source,
  `spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultSingletonBeanRegistry.java`,
  https://github.com/spring-projects/spring-framework/blob/main/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultSingletonBeanRegistry.java,
  verified 2026-08-14).
- **The Go standard library's sync.Once implementation.** The sync package
  documents that Do checks a fast-path indicator before ever touching a
  mutex, and only takes the lock on the slow path, which is the
  double-checked pattern implemented once, in the standard library, so every
  Go program that calls sync.Once gets a correctly fenced DCL without writing
  one (Go standard library, `sync` package documentation,
  https://pkg.go.dev/sync#Once, verified 2026-08-14).
- **.NET's Lazy<T> with LazyThreadSafetyMode.ExecutionAndPublication.**
  Microsoft's documentation for Lazy<T> describes this, the default thread
  safety mode, as locking so that only one instance of the lazily
  instantiated object is created no matter how many threads try to access
  it, which is the DCL guarantee delivered through a general-purpose lazy
  wrapper type rather than a hand-written accessor (Microsoft Learn, "Lazy<T>
  Class," https://learn.microsoft.com/en-us/dotnet/api/system.lazy-1,
  verified 2026-08-14). The same page documents
  LazyThreadSafetyMode.PublicationOnly as a deliberate alternative in which
  threads race to initialize the value and duplicate, discarded
  constructions are accepted as the price of avoiding the lock entirely,
  which is a real, named, production alternative to the double-checked
  structure for cases where construction is cheap and side-effect-free.

## 10. Consequences

Positive.

- Removes lock acquisition from the overwhelming majority of calls once the
  guarded value exists, which is the entire performance case for the
  pattern and is real when construction is rare and reads are frequent.
- Preserves exactly-once construction semantics for expensive or
  side-effecting initialization, unlike an unsynchronized "just build it and
  let the last write win" approach, which can construct the object multiple
  times and leak whatever resource the discarded copies opened.
- When implemented with the language's real once-primitive rather than by
  hand, the pattern is centralized in one audited implementation, so
  application code gets the fast path without carrying the memory-ordering
  argument itself.

Negative.

- The classic hand-written form is one of the most frequently cited examples
  of a concurrency bug that passes code review, passes single-threaded
  testing, and fails intermittently, only under real concurrent load, only on
  certain processor architectures or compiler optimization levels, which
  makes it expensive to diagnose after it ships.
- Correctness depends on details, the exact memory-ordering annotation on the
  guard field, that are easy to omit silently, because the code compiles and
  runs correctly in the overwhelmingly common single-threaded or
  low-contention test scenario even when it is broken.
- The pattern only pays for itself when uncontended reads vastly outnumber
  the rare construction race, so applying it to a rarely called accessor adds
  code complexity for a performance gain nobody will measure.
- It generalizes poorly to invalidation or reconstruction. the structure
  answers "build this exactly once," and adapting it to "rebuild this when
  stale" usually produces a worse, ad hoc version of a pattern meant for
  mutable cached state, such as a read-write lock over a versioned snapshot.

## 11. Failure modes and misuse

- **Symptom.** A singleton or cached object occasionally has fields that look
  zeroed, null, or default-valued when read from a thread other than the one
  that created it, and the bug reproduces only under load and only on some
  machines. **Cause.** The guard field is a plain, non-atomic, non-volatile
  reference, so the compiler or processor is free to make the reference
  visible to another thread before the constructor's writes to that object's
  fields are visible to the same thread, exactly the broken timeline in
  dimension 7. **Fix.** Declare the guard field volatile in Java, use a
  correctly ordered atomic store with release semantics paired with an
  acquire load in C++ and Rust, or replace the hand-written check entirely
  with the platform's once-primitive.
- **Symptom.** The initializer runs more than once, and a resource such as a
  socket, file handle, or thread pool is visibly leaked or duplicated.
  **Cause.** The slow-path re-check inside the lock was omitted, so every
  thread that loses the race to acquire the lock proceeds to construct a new
  instance once it finally gets the lock, instead of discovering that another
  thread already finished. **Fix.** Always re-read the guard field
  immediately after acquiring the lock, and only construct if that second
  read still finds nothing.
- **Symptom.** The code works in every test and in production for months,
  then a compiler upgrade, a new optimization flag, or a port to a new CPU
  architecture introduces the intermittent corruption described above with no
  application code change. **Cause.** The original implementation happened to
  work because a specific compiler did not perform the reordering the
  language specification permits, or the target CPU's memory model happened
  to be strong enough to forgive the missing barrier, x86 is the frequent
  culprit here because its memory model is stronger than what most language
  specifications promise. **Fix.** Never rely on an unspecified compiler or
  processor behavior for correctness. audit every DCL implementation against
  the language's actual memory model documentation, not against what worked
  in the last test run.
- **Symptom.** A code reviewer or a static analysis tool flags a variable as
  needing synchronization, and the fix applied is to mark it volatile or
  Atomic without re-verifying that the surrounding check-lock-check structure
  is still correct. **Cause.** Treating the memory-ordering annotation as a
  magic incantation that makes concurrency bugs disappear, rather than
  understanding it as the specific mechanism that supplies the
  happens-before edge the pattern's correctness argument depends on.
  **Fix.** Understand, and be able to explain, exactly which two operations
  the annotation orders relative to each other before shipping the change.
- **Symptom.** The guarded object needs to be periodically refreshed, and the
  DCL structure is extended with an extra staleness check, producing a third
  nested check and a subtle bug where a thread refreshes the object while
  another thread is mid-read against the old reference. **Cause.** Reusing
  the exactly-once shape for a value with an ongoing lifecycle instead of
  switching to a pattern designed for that, such as an atomic swap of an
  immutable snapshot or a proper cache with explicit invalidation.
  **Fix.** Recognize when the requirement has changed from build once to
  keep current, and change the pattern, not just the guard condition.

## 12. Trade-off matrix

| Concern | Double-Checked Locking (correctly fenced) | Plain lock on every access | Eager initialization at startup | Language once-primitive (std::call_once, sync.Once, OnceLock) |
|---|---|---|---|---|
| Steady-state read latency | Lowest, no lock after construction | Highest, lock on every call forever | Lowest, no check needed at all | Lowest, fast-path check with no lock |
| Correctness risk if hand-written | High if the ordering annotation is wrong or missing | Low, correctness is trivial to reason about | Low, no concurrency involved at all | Low, the primitive is centrally audited |
| Startup cost | None, deferred until first use | None, deferred until first use | Paid unconditionally, even if unused | None, deferred until first use |
| Handles expensive or rarely-used resources well | Yes, this is the pattern's purpose | Yes, but with permanent lock cost | No, always pays the cost | Yes |
| Suitable for values that must later be invalidated or refreshed | No, needs extension into a different design | Awkward, needs a rebuild-under-lock branch added | No | No, primitives are exactly-once by design |
| Code review effort to trust it | High, must verify memory-ordering reasoning | Low | Low | Low, trust is delegated to the standard library |

## 13. Related and incompatible patterns

- **Monitor Object.** Monitor Object is the general pattern for
  synchronizing all access to an object's state, and the plain-lock
  alternative in dimension 12's table is a direct application of it. DCL is
  best understood as a targeted optimization on top of a Monitor Object
  accessor for the specific case where the guarded state, once built, never
  changes again.
- **Scoped Locking.** The lock acquired on the slow path of a correct DCL
  implementation should be released deterministically even if construction
  throws, which is exactly the guarantee Scoped Locking (RAII-style guard
  objects, try/finally, Go's defer) provides. Every working code example in
  dimension 8 relies on it.
- **Thread-Specific Storage.** When the true goal is each thread getting its
  own instance rather than exactly one shared instance for all threads,
  Thread-Specific Storage is the correct pattern and sidesteps DCL's
  correctness concerns entirely, because there is no cross-thread
  publication to reason about.
- **Leader-Followers and Half-Sync-Half-Async.** These patterns coordinate
  which thread performs work at a larger architectural scale. DCL is a
  small, local synchronization idiom that can appear inside either
  architecture wherever a shared, lazily built resource needs protecting,
  but it does not compose or conflict with them structurally.
- **Not incompatible with anything named in this catalog**, though it is
  functionally superseded, for the common lazy-singleton case, by whatever
  once-primitive the target language ships, as documented in dimensions 8
  and 9.

## 14. Refactoring path in and out

**Introducing it.** Start from a correct but slow implementation, a
single lock guarding the entire accessor, never from a blank page. Profile to
confirm the lock is actually contended enough on the read path to matter.
Then, in order. First, if the language ships a once-primitive, replace the
hand-rolled lock with it and stop, this resolves the overwhelming majority of
real cases. Second, only if no suitable primitive exists, add the
unsynchronized fast-path read, add the slow-path re-check inside the existing
lock, and add the correct memory-ordering annotation to the guard field,
verifying against the language's own memory model documentation rather than
against a Stack Overflow answer. Third, write a concurrent stress test,
described in dimension 15, before considering the change complete.

**Removing it.** When a profiler shows the lock was never actually the
bottleneck, or when the surrounding code has grown a requirement to
invalidate or refresh the guarded value, collapse the double-checked
structure back down to a single lock around the whole accessor, or migrate
to a pattern built for a changing value, such as an atomic reference swap
with an immutable snapshot. Removing the fast-path check is always safe
correctness-wise. it can only make the code slower, never less correct, which
makes when in doubt, simplify to a single lock a safe default direction to
refactor toward.

## 15. Testing and verification

Single-threaded tests cannot exercise the race this pattern exists to
protect against, and they will pass against a broken implementation just as
readily as a correct one, so a passing single-threaded test suite proves
nothing about DCL's correctness. Verification needs, at minimum, a stress
test that spins up dozens to hundreds of threads and calls the accessor
concurrently before any of them has called it yet, then asserts that the
side effect of construction, a counter incremented inside the constructor in
every working example in dimension 8, happened exactly once. Every code
sample in this entry includes exactly that assertion, and it is the
practical, checkable form of the correctness argument the rest of the entry
makes in prose. Running such a test under a thread sanitizer, Go's -race
flag, or a similar data-race detector for the target language substantially
increases confidence, because these tools can catch the unsynchronized
access even on a machine and compiler combination that happens not to
manifest the corruption on a given run. Tests that merely assert the
returned reference is non-null are not sufficient. a broken implementation
can return a non-null reference to a partially constructed object, and the
test needs to check the object's internal state or construction count, not
merely its non-nullness.

## 16. Observability signals

A healthy instance shows a construction counter, or an equivalent metric on
how many times the expensive initializer actually ran, that reaches exactly
one and stays there for the life of the process, alongside a lock-acquisition
counter or histogram on the accessor that should show a large spike at
process start or at first use, then drop to near zero for the remainder of
the run. A failing instance shows either a construction counter above one,
which is the exactly-once guarantee being violated, most likely from a
missing or incorrect slow-path re-check, or a lock-acquisition rate that
never drops after the object should already be built, which usually means
the fast-path check itself is broken or was never reached, for example
because the guard field's type does not actually short-circuit correctly.
Where the runtime supports it, tracing the accessor's first several calls
during a load test, rather than sampling later, is the highest-value window,
because the race this pattern is built to survive can only be observed
during that narrow first-access period.

## 17. Security and privacy implications

The pattern's own structure carries no data-handling implications beyond
whatever the guarded resource itself carries, but a broken implementation
that publishes a partially constructed object is a genuine information
disclosure and reliability risk when the guarded object holds credentials,
cryptographic key material, or configuration secrets. a thread that observes
the object mid-construction can read zeroed, default, or otherwise incorrect
security-relevant fields, and depending on the surrounding code, act on that
incorrect state, for example proceeding as if a permission check field
defaulted to allow rather than deny. Any DCL implementation guarding
authentication state, session tokens, or cryptographic material should be
held to the memory-ordering rigor described in dimensions 7 and 8 without
exception, and, given the once-primitive alternatives documented in
dimensions 8 and 9, there is rarely a good reason to hand-write the guard for
security-sensitive state at all when a reviewed standard-library primitive is
available.

## 18. References

1. Schmidt, Douglas C., and Tim Harrison. "Double-Checked Locking, An
   Optimization Pattern for Efficiently Initializing and Accessing
   Thread-safe Objects." Pattern Languages of Program Design 3, 1996.
2. Schmidt, Douglas C., Michael Stal, Hans Rohnert, and Frank Buschmann.
   *Pattern-Oriented Software Architecture, Volume 2, Patterns for Concurrent
   and Networked Objects*. Wiley, 2000. Double-Checked Locking Optimization
   pattern.
3. Meyers, Scott, and Andrei Alexandrescu. "C++ and the Perils of
   Double-Checked Locking." Dr. Dobb's Journal, 2004.
4. Pugh, Bill, et al. "The 'Double-Checked Locking is Broken' Declaration."
   University of Maryland. https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html
   Verified 2026-08-14.
5. "Double-checked locking." Wikipedia. https://en.wikipedia.org/wiki/Double-checked_locking
   Verified 2026-08-14.
6. Go standard library, sync package documentation. https://pkg.go.dev/sync#Once
   Verified 2026-08-14.
7. Rust standard library, std::sync::Once documentation. https://doc.rust-lang.org/std/sync/struct.Once.html
   Verified 2026-08-14.
8. Microsoft Learn. "Lazy<T> Class." https://learn.microsoft.com/en-us/dotnet/api/system.lazy-1
   Verified 2026-08-14.
9. Microsoft Learn. "The lock statement." https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/lock-statement
   Verified 2026-08-14.
10. Python 3 documentation, Glossary, "Global Interpreter Lock." https://docs.python.org/3/glossary.html#term-global-interpreter-lock
    Verified 2026-08-14.
11. Spring Framework source, DefaultSingletonBeanRegistry.java. https://github.com/spring-projects/spring-framework/blob/main/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultSingletonBeanRegistry.java
    Verified 2026-08-14.
