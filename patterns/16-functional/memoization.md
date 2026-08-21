---
name: Memoization
slug: memoization
family: 16-functional
category: Functional
aliases: [Memo Functions, Function Memoization, Result Caching, Tabling]
first_described: "Michie 1968"
maturity: canonical
related: [dynamic-programming, lazy-evaluation, referential-transparency, pure-function, caching, flyweight]
incompatible_with: [impure-functions, volatile-inputs, unbounded-key-space, secret-bearing-cache-keys]
verified: 2026-08-02
---

# Memoization

## 1. Name, aliases, and lineage

The canonical name is Memoization. The older phrase is **memo functions**.
Donald Michie's 1968 Nature article, "Memo" Functions and Machine Learning,
is the usual lineage point for the name. OpenAIRE records the article as
Donald Michie, Nature, volume 218, pages 19-22, published 1 April 1968, with
DOI records linked from the page
(https://explore.openaire.eu/search/publication?pid=10.1038%2F218019a0,
verified 2026-08-02). The same record summarizes Michie's proposal as a way
for computers to learn from experience during execution by using a simple rote
learning facility inside a programming language
(https://explore.openaire.eu/search/publication?pid=10.1038%2F218019a0,
verified 2026-08-02).

The modern term means this. A function remembers the result it computed for a
given input key. Later calls with the same key return the saved result instead
of recomputing it. The pattern is strongest when the function is referentially
transparent, because the same key always denotes the same result. Clojure's
core API uses that contract directly. It says `memoize` returns a memoized
version of a referentially transparent function and keeps a mapping from
arguments to results
(https://clojure.github.io/clojure/branch-master/clojure.core-api.html,
verified 2026-08-02).

Common aliases carry slightly different emphasis.

- **Memo functions.** The historical name from Michie's work. It frames the
  cache as part of the function's evaluation apparatus.
- **Function memoization.** The everyday library name in functional and
  dynamic language communities.
- **Result caching.** A broader systems term. It can mean memoization, but it
  can also mean HTTP caching, database query caching, object caching, or page
  fragment caching.
- **Tabling.** A logic programming term for remembering subgoal answers. It
  overlaps with memoization but belongs to a different execution model.

Engineering judgement. In this catalog, Memoization is narrower than general
caching. A Redis cache for arbitrary records is a cache pattern. A wrapper
around `fib(n)` or `parse(grammar, text, offset)` that keys by arguments and
returns prior function results is Memoization. The boundary matters because
memoization inherits the function's purity, key identity, argument lifetime,
and call concurrency issues.

## 2. Problem and context

A program repeatedly asks the same pure question, and each answer costs more
than a map lookup.

The shape shows up in many codebases. A recursive algorithm recomputes the
same subproblem from different paths. A parser asks whether a grammar rule
matches at the same input offset. A route planner recalculates a derived score
for the same node. A UI component transforms a large list during render, then
does the same transformation again because unrelated state changed. A compiler
analysis walks a graph to find a property, then another pass asks for the same
property on the same node.

Without memoization, the code treats every call as new work. That is accurate
for a function whose result changes with time, I/O, global state, random
numbers, mutable inputs, or caller identity. It is wasteful for a function
whose value is determined by its inputs. In the wasteful case, the program
spends CPU, stack, allocation, database calls, or network waits to rediscover
an answer it already paid for.

Memoization changes the call boundary. The function becomes two-part. The
first part maps arguments to a cache key. The second part either returns a
cached value or calls the original function and stores its result. The caller
keeps calling a function, not a cache API. That wrapper shape is why
memoization reads as a functional pattern even when implemented with mutation
inside the wrapper.

The context that makes the pattern fit has four parts.

- The calculation has stable answers for stable keys.
- Repeated keys occur often enough to repay the lookup, storage, and invalid
  entry costs.
- The result can be safely reused by all callers who share that key.
- The cache lifetime is clear. It may be one request, one component instance,
  one object instance, one process, or one compiler run.

The last point is often missed. A memoized function with a hidden process-wide
cache makes a promise about time. It says a result from this morning may answer
a call tonight unless eviction, invalidation, or restart intervenes. That is a
fine promise for a pure mathematical function. It is a dangerous promise for a
feature flag lookup, an authorization decision, or a record read from a mutable
database.

Memoization is also different from precomputation. Precomputation builds a
table before calls arrive. Memoization fills the table on demand from calls
that occur in a real run. That makes it attractive when the input space is much
larger than the subset touched by normal traffic.

The pattern is also different from storing a local variable. A local variable
remembers one answer inside one call. A memo table remembers answers across
calls that are separated by stack frames, render passes, recursive paths, or
later requests inside the same scope. That shift is why memoization can change
an algorithm's growth curve, not only its constant factors. The shift is also
why the key must be treated as part of the function contract. When a caller can
make two calls that look equal to the memoizer but mean different things to the
domain, the wrapper has become a source of wrong answers.

## 3. Forces

Engineering judgement. These forces describe the trade between direct
recomputation and remembering function results.

- **Latency.** Favoured on cache hits because the call returns after key
  construction and lookup. Sacrificed on misses because the wrapper adds key
  construction, lookup, storage, and often locking around the original work.
- **CPU cost.** Favoured when the same expensive calculation repeats. Sacrificed
  when the function is cheap, the key is costly to hash, or the hit rate is low.
- **Memory cost.** Sacrificed. Every retained key and value stays alive until
  eviction, clearing, object death, request end, or process exit.
- **Coupling.** Mixed. The caller couples to an ordinary function, which is
  good. The function now couples to a cache policy, key semantics, and sometimes
  a clock.
- **Consistency.** Favoured for stable pure functions. Sacrificed for inputs
  that hide mutable state, because the cache can return a value that no longer
  matches the world.
- **Operability.** Mixed. Hit and miss counters make repeated work visible.
  Hidden caches can also hide stale data and make a production incident depend
  on call history.
- **Cost.** Favoured when a small wrapper prevents repeated expensive work.
  Sacrificed when the team must tune eviction, lock contention, invalidation,
  and metrics.
- **Team topology.** Favoured when a library team can publish a memoized
  function with a clear lifetime contract. Risky when many teams share a global
  cache whose keys and invalidation rules are owned by no one.
- **Cognitive load.** Sacrificed. A reader must ask whether a call ran the
  function or returned a prior result, whether misses can race, and who clears
  the cache.

The pattern favours repeated local work over storage pressure. It favours
functions whose identity is mathematical over functions whose identity is
operational. It favours reads over writes. It favours stable keys over rich
object graphs. A claim that memoization is a free speedup usually means the
cache lifetime, key space, or mutation story has not been examined.

Concurrency adds another force. A memoized function can allow duplicate
in-flight work, or it can coalesce concurrent calls for the same key. Python's
`functools.cache` and `functools.lru_cache` documentation says the cache data
structure remains coherent across threads, but the wrapped function can be
called more than once when a second thread arrives before the first result has
been stored
(https://docs.python.org/3/library/functools.html?highlight=total_ordering,
verified 2026-08-02). That is often a reasonable trade for low lock
contention. It is wrong when the original work must run once, such as charging
a payment or allocating a scarce external resource.

## 4. Applicability and non-applicability

Reach for Memoization when these conditions hold.

- A function is pure or can be treated as pure within a named lifetime.
- Calls repeat the same keys across one useful cache lifetime.
- The function cost is higher than key construction, lookup, and retention.
- Values are safe to share or are immutable snapshots.
- Memory can be bounded or the key space is naturally small.
- The cache owner can observe hit rate, miss cost, size, eviction, and stale
  result reports.
- Duplicate in-flight misses are harmless, or the memoizer has single-flight
  semantics.
- The result of the call is not a capability, secret, authorization decision,
  or user-specific value unless the key includes the full security context.

Non-applicability list.

- **The function has side effects.** A memoizer can skip the call and therefore
  skip the effect. Observable symptoms include missing audit events, skipped
  writes, missing emails, and tests that pass only when run in a certain order.
- **The result depends on time.** A function that reads the clock, an expiring
  token, or current market data needs an explicit freshness model. A bare
  memoizer has no reason to recompute.
- **The result depends on mutable input objects.** If a list, map, model, AST
  node, or request object can mutate after key creation, a prior result may no
  longer match the current object.
- **The key space is unbounded and attacker influenced.** Public request
  parameters can fill a process cache with one-off keys. That turns a speed
  pattern into a memory denial of service.
- **The function is cheap.** If the work is cheaper than hashing and locking,
  the wrapper makes the hot path slower.
- **The result must be unique per call.** Fresh IDs, nonces, file handles,
  streams, iterators, random values, and mutable builders must not be reused by
  argument equality.
- **The cache lifetime is unclear.** A hidden module-level cache with no owner
  is hard to tune, test, or clear during incidents.
- **The problem is cross-process data reuse.** A local memoizer does not share
  data across hosts or restarts. Use a distributed cache or storage-backed
  materialization when that is the problem.
- **The problem is bulk reuse across many keys.** A batch algorithm, dynamic
  programming table, database index, or materialized view may fit better when
  callers need a large related set of answers.

Engineering judgement. Memoization should be introduced after measuring a
repeat pattern or after proving duplicate subproblems from the algorithm. It is
weak as a guess, because the wrong key or lifetime can make code slower and
less trustworthy.

## 5. Structure

The participants are named by runtime role rather than by class name.

- **Caller.** Invokes a function by its ordinary API. It should not know whether
  the result came from computation or from a prior call.
- **Memoized function.** The public function value after wrapping. It preserves
  the argument and return contract of the original function, while adding cache
  lookup and store behavior.
- **Original function.** The calculation that produces the value on a miss. It
  should be pure within the memoizer's lifetime.
- **Key function.** Converts arguments into a stable cache key. In simple
  libraries, this is implicit and uses the argument tuple or a language hash
  map key.
- **Memo table.** The storage mapping keys to results, promises, errors, or
  entries with metadata.
- **Entry policy.** Optional policy that controls maximum size, time to live,
  weak references, error caching, single-flight loading, and explicit clearing.
- **Observer.** Optional metrics, logs, or trace code that records hits, misses,
  evictions, load time, and current size.

The key function is the most underestimated participant. If the key ignores an
argument that affects the result, the memoizer returns wrong values. If it
includes an argument that does not affect the result, the cache fragments into
many entries that cannot hit. Clojure's `core.memoize` documentation describes
an argument function metadata hook for cases where one or more arguments are
irrelevant for memoization, such as a mutable JDBC connection argument
(https://clojure.github.io/core.memoize/, verified 2026-08-02).

The memo table may store values or in-flight computations. Storing values is
simple. Storing promises or futures coalesces concurrent misses, but it raises
policy questions around cancellation, errors, and timeouts. The structure is
still memoization when the unit stored is "the answer for this key", even if
the answer is not ready yet.

Engineering judgement. Treat the memo table as private state of the memoized
function unless a library deliberately exposes it. Exposing the table can be
useful for tests, snapshots, and incident response, but public mutation of the
table makes the function harder to reason about. A caller that writes entries
directly can bypass validation, poison a value, or create a key that the key
function would never produce. A clear API is safer than an open table: get by
calling the function, clear by key when the owner approves it, and inspect
through read-only metrics or snapshots.

## 6. ASCII structure diagram

```text
  +---------+       call(args)        +----------------------+
  | Caller  | --------------------->  | Memoized function    |
  +---------+                         |----------------------|
                                      | keyFn(args)          |
                                      | table.get(key)       |
                                      | original(args)       |
                                      | table.put(key,value) |
                                      +----------+-----------+
                                                 |
                          lookup key             |
                                                 v
                                      +----------------------+
                                      | Memo table           |
                                      |----------------------|
                                      | key -> value         |
                                      | key -> in-flight     |
                                      | key -> error entry   |
                                      +----------+-----------+
                                                 ^
                    miss computes                |
                                                 |
                                      +----------------------+
                                      | Original function    |
                                      |----------------------|
                                      | pure calculation     |
                                      | returns value        |
                                      +----------------------+

  Optional policy wraps the table. Optional observer records hit, miss,
  eviction, load time, and size.
```

## 7. Dynamics

The runtime flow has two branches. The hit branch returns without calling the
original function. The miss branch computes, stores, and returns.

```text
Caller        Memoized fn        Key fn        Memo table       Original fn
  |               |                |               |                |
  |-- call(args)->|                |               |                |
  |               |-- key(args) -->|               |                |
  |               |<-- key --------|               |                |
  |               |-- get(key) ------------------>|                |
  |               |<-- hit(value) ----------------|                |
  |<-- value -----|                |               |                |
  |               |                |               |                |
  |-- call(args)->|                |               |                |
  |               |-- key(args) -->|               |                |
  |               |<-- key --------|               |                |
  |               |-- get(key) ------------------>|                |
  |               |<-- miss ----------------------|                |
  |               |-- original(args) ----------------------------->|
  |               |<-- value --------------------------------------|
  |               |-- put(key,value) ------------>|                |
  |<-- value -----|                |               |                |
```

Concurrent misses add a third branch.

```text
Thread A          Memoized fn          Memo table          Thread B
   |                  |                    |                  |
   |-- call(k) ------>|                    |                  |
   |                  |-- reserve(k) ----->|                  |
   |                  |<-- owner ----------|                  |
   |                  |                                      |
   |                  |<---------------------- call(k) -------|
   |                  |-- reserve(k) ----->|                  |
   |                  |<-- wait(entry) ----|                  |
   |-- compute ------>|                    |                  |
   |                  |-- publish(value) ->|                  |
   |<-- value --------|                    |-- wake ----------|
   |                  |                    |<----- value -----|
```

The single-flight branch is not universal. Some memoizers choose duplicate
work over wait queues. That choice must be visible in the API or at least in
the operational notes, because it controls whether misses are safe for
expensive but idempotent work only, or safe for work that must run once.

## 8. Implementation variants

**Unbounded per-function table.** The wrapper stores every key it has ever
seen. Python's `functools.cache` is documented as a lightweight unbounded
function cache and as equivalent to `lru_cache(maxsize=None)`
(https://docs.python.org/3/library/functools.html?highlight=total_ordering,
verified 2026-08-02). This variant is small and fast. It fits finite domains,
compiler runs, one-request memo tables, and mathematical functions with bounded
input. It is dangerous for services that accept unbounded user keys.

**Bounded least-recently-used table.** The wrapper evicts older entries under a
size cap. Python's `lru_cache` saves up to a configured number of recent calls,
uses a dictionary for cached results, exposes `cache_info()` for hits, misses,
max size, and current size, and offers `cache_clear()` for invalidation
(https://docs.python.org/3/library/functools.html?highlight=total_ordering,
verified 2026-08-02). This variant fits long-running processes when recent use
predicts near-future use. It can fail when a scan workload pushes out valuable
hot entries.

**Instance memoization.** The value is cached on one object instance.
`cached_property` is the common shape. Django's performance guide says its
`cached_property` decorator saves a property's returned value and returns the
saved value on the next access for the same instance
(https://docs.djangoproject.com/en/4.2/topics/performance/, verified
2026-08-02). This variant has a clear lifetime, because the entry dies with
the object. It fits expensive derived attributes of immutable or effectively
immutable objects.

**Render-scope memoization.** The cache belongs to a UI component instance or a
server render request. React documents `useMemo` as a Hook that caches a
calculation result between re-renders and returns the prior value when its
dependencies have not changed
(https://react.dev/reference/react/useMemo, verified 2026-08-02). React also
says `useMemo` should be treated as a performance optimization, not a semantic
requirement, because React may discard the cached value for named reasons
(https://react.dev/reference/react/useMemo, verified 2026-08-02). This variant
fits view calculations whose dependencies are explicit.

**Pluggable policy memoization.** The memoizer accepts a cache backend or
policy object. Clojure's `core.memoize` describes pluggable memoization,
manipulable memoization, LRU, FIFO, LU, TTL, clearing, reset, snapshots, and
custom key selection
(https://clojure.github.io/core.memoize/, verified 2026-08-02). This variant
fits libraries that need the same function wrapper but different retention
rules per deployment.

**Loading cache as memoizer.** A general cache API can act as a memoizer when
the loader is the original function and the key is the function argument.
Guava's cache guide says caches fit cases where a value is expensive to compute
or retrieve and will be needed for the same input more than once. It also
distinguishes `Cache` from `ConcurrentMap` by automatic eviction to constrain
memory
(https://github.com/google/guava/wiki/cachesexplained, verified 2026-08-02).
This variant fits Java services that want eviction, stats, refresh, listeners,
and concurrency behavior around a computed value.

**Memoized analysis nodes.** A compiler or static analyzer may store a derived
answer on the IR node that asked for it. LLVM's MemorySSA documentation says a
walker API can cache information as part of a `MemoryAccess`, and that
optimizing every `MemoryDef` has quadratic time complexity and is not done by
default
(https://www.llvm.org/docs/MemorySSA.html, verified 2026-08-02). This is a
memoization variant bound to an analysis graph rather than a public function
wrapper.

**Error and promise memoization.** Some systems store failed results or
in-flight promises. This can avoid repeated failure storms or duplicate
network calls. It can also pin transient errors until expiry. The policy must
say whether exceptions are cached, for how long, and whether cancellation
removes the entry.

**Recursive self-memoization.** The function refers to its memoized wrapper
when making recursive calls. The Go and Python examples below use that shape.
It is common for Fibonacci-like demonstrations, parsers, and graph searches.
The benefit is that every recursive subproblem passes through the table. The
risk is initialization order. In languages where a function value must be
assigned before the body can call it, the wrapper setup needs care.

**External table threading.** The memo table is passed as an argument, often as
a mutable map owned by one algorithm run. The Rust example below uses this
shape because borrowing rules make hidden shared mutation less natural for a
small sample. The benefit is lifetime clarity. The caller can see when the
table is created and discarded. The cost is API noise, because every recursive
call must carry the table.

**Decorator or annotation.** The language or framework wraps a function through
metadata. This is concise and can preserve the visible API. It can also hide
policy. Engineering judgement. A decorator is best when the defaults are safe
for the domain, such as bounded size or instance lifetime. It is weaker when
the correct key, tenant scope, or expiry needs careful review.

```python
from functools import lru_cache

calls = 0


@lru_cache(maxsize=128)
def ways_to_climb(steps: int) -> int:
    global calls
    calls += 1
    if steps < 0:
        return 0
    if steps == 0:
        return 1
    return ways_to_climb(steps - 1) + ways_to_climb(steps - 2)


if __name__ == "__main__":
    print(ways_to_climb(20))
    print(calls)
    print(ways_to_climb.cache_info())
```

```typescript
function memoize<A extends readonly unknown[], R>(
  fn: (...args: A) => R,
  keyOf: (...args: A) => string
): (...args: A) => R {
  const table = new Map<string, R>();
  return (...args: A): R => {
    const key = keyOf(...args);
    if (table.has(key)) {
      return table.get(key) as R;
    }
    const value = fn(...args);
    table.set(key, value);
    return value;
  };
}

const priceBand = memoize(
  (price: number, rate: number) => Math.round(price * rate),
  (price, rate) => `${price}:${rate}`
);

console.log(priceBand(129, 0.2));
console.log(priceBand(129, 0.2));
```

```go
package main

import "fmt"

func MemoizeInt(fn func(int) int) func(int) int {
	cache := map[int]int{}
	return func(n int) int {
		if value, ok := cache[n]; ok {
			return value
		}
		value := fn(n)
		cache[n] = value
		return value
	}
}

func main() {
	var fib func(int) int
	fib = MemoizeInt(func(n int) int {
		if n < 2 {
			return n
		}
		return fib(n-1) + fib(n-2)
	})
	fmt.Println(fib(30))
}
```

```rust
use std::collections::HashMap;

fn paths(n: u32, memo: &mut HashMap<u32, u64>) -> u64 {
    if n <= 1 {
        return 1;
    }
    if let Some(value) = memo.get(&n) {
        return *value;
    }
    let value = paths(n - 1, memo) + paths(n - 2, memo);
    memo.insert(n, value);
    value
}

fn main() {
    let mut memo = HashMap::new();
    println!("{}", paths(40, &mut memo));
    println!("{}", memo.len());
}
```

## 9. Known production uses

**Python standard library, `functools.cache`, `lru_cache`, and
`cached_property`.** Python documents `functools.cache` as an unbounded
function cache sometimes called memoize, `lru_cache` as a memoizing callable
that saves recent calls, and `cached_property` as a once-per-instance computed
property cache
(https://docs.python.org/3/library/functools.html?highlight=total_ordering,
verified 2026-08-02). This is a named production use in a language standard
library used by Python programs rather than an application-specific helper.

**React, `useMemo` and `cache`.** React documents `useMemo` for caching a
calculation between re-renders, with dependencies compared across renders
(https://react.dev/reference/react/useMemo, verified 2026-08-02). React also
documents `cache` for Server Components to skip duplicate work and share a
memoized result across components during a server request
(https://react.dev/reference/react/cache, verified 2026-08-02). These APIs are
production memoization facilities in the React framework.

**Guava, `Cache` and `LoadingCache`.** Guava's cache guide presents
`LoadingCache<Key, Graph>` examples where an expensive graph is created on
cache miss and then reused by key. It describes automatic loading, size and
time eviction, refresh, removal listeners, and statistics
(https://github.com/google/guava/wiki/cachesexplained, verified 2026-08-02).
This is a production Java library use when the cache loader is the memoized
function.

**Clojure, `clojure.core/memoize` and `clojure.core.memoize`.** Clojure core
documents `memoize` as returning a memoized version of a referentially
transparent function and says it trades memory for speed when repeated calls
use the same arguments
(https://clojure.github.io/clojure/branch-master/clojure.core-api.html,
verified 2026-08-02). The `core.memoize` library adds pluggable and
manipulable memoization policies
(https://clojure.github.io/core.memoize/, verified 2026-08-02).

**Django, `cached_property`.** Django's performance guide documents
`cached_property` as saving a value returned by a property and returning that
saved value on later access by the same instance
(https://docs.djangoproject.com/en/4.2/topics/performance/, verified
2026-08-02). This is instance-scoped memoization in a web framework.

## 10. Consequences

Positive consequences.

- Repeated calls with the same key avoid duplicate work.
- Recursive algorithms with overlapping subproblems can shift from exponential
  recomputation to one computation per reachable key.
- The caller API stays simple. It calls a function rather than managing a cache.
- Measured hit rate exposes whether repeated work exists.
- Instance or request-scoped memoization gives a natural cache lifetime.
- A memoized wrapper can be removed with little caller churn if the function
  contract stays the same.
- The table created by memoization can reveal the active subproblem set during
  tests or profiling.

Negative consequences.

- Memory retention grows with key and value count.
- Mutable inputs and hidden dependencies can return stale or wrong results.
- A cache miss is slower than a direct call because the wrapper does extra work.
- Hidden process-wide caches can make tests order-dependent.
- Errors, cancellation, and concurrent misses need policy choices.
- Cache entries can retain secrets or user data beyond the request where they
  were created.
- A memoized function can hide that the original calculation is too slow or too
  chatty.
- A poor key can either collapse distinct calls into one wrong answer or split
  equal calls into many misses.

Engineering judgement. The main consequence is a change in ownership. Before
memoization, the function owns computation. After memoization, someone must own
the lifetime and meaning of retained answers.

## 11. Failure modes and misuse

Engineering judgement. Each item below is written as an observable symptom,
the likely cause, and a practical fix.

**Symptom.** Users see stale configuration, stale permissions, or stale prices
until a process restarts.
**Cause.** A memoized function reads mutable external state but keys only by
the visible arguments.
**Fix.** Remove memoization, narrow the lifetime to one request, or include a
version, timestamp bucket, tenant epoch, or invalidation signal in the key.

**Symptom.** Memory rises over hours and drops only after restart.
**Cause.** An unbounded memo table receives a large or attacker-controlled key
space.
**Fix.** Add a maximum size, TTL, explicit clearing, request scope, or reject
high-cardinality keys before memoization.

**Symptom.** Two callers receive the same mutable object and changes by one
caller appear in the other.
**Cause.** The memoized function returns a mutable value that callers treat as
private.
**Fix.** Return immutable values, copy on read, copy on write, or avoid
memoizing values with caller-owned mutation.

**Symptom.** A supposedly cached function still recomputes on every call.
**Cause.** The key includes a new object identity, a changing timestamp, a
fresh callback, or keyword argument order that differs between calls. Python
documents that distinct keyword argument patterns may be treated as separate
cache entries by `lru_cache`
(https://docs.python.org/3/library/functools.html?highlight=total_ordering,
verified 2026-08-02).
**Fix.** Normalize keys. Sort unordered arguments, extract stable IDs, or use a
custom key function.

**Symptom.** Concurrent traffic creates a thundering herd on a slow dependency
despite memoization.
**Cause.** The memoizer does not coalesce in-flight misses. Python documents
that the wrapped function can be called more than once under concurrent first
calls before the value is cached
(https://docs.python.org/3/library/functools.html?highlight=total_ordering,
verified 2026-08-02).
**Fix.** Store promises or futures, use a single-flight loader, or move the
cache behind a loading cache with per-key coordination.

**Symptom.** A transient outage causes errors to persist after the dependency
recovers.
**Cause.** The memoizer caches exceptions or failed futures without a short
error TTL.
**Fix.** Do not cache failures, or cache them with a small TTL and separate
metrics for negative entries.

**Symptom.** Tests fail only when run after another test.
**Cause.** A global memo table survives across test cases.
**Fix.** Expose `clear`, reset in test setup, inject the memo table, or scope
memoization to the object under test.

**Symptom.** Cache hit rate is high, but latency does not improve.
**Cause.** Key construction, hashing, serialization, locking, or copying costs
more than the skipped work.
**Fix.** Profile hit and miss paths separately. Simplify the key, move the
memoizer inward, or remove it.

## 12. Trade-off matrix

| Force | Memoization | Dynamic Programming Table | Lazy Evaluation | Flyweight | Distributed Cache |
|---|---|---|---|---|---|
| Latency | Fast on repeated keys, slower on misses | Fast after table fill | Defers work until demanded | Reduces construction cost | Network hop can dominate |
| Memory | Retains key-value entries | Retains planned table | Retains thunks or values | Shares object state | Moves storage out of process |
| Consistency | Strong only for pure or scoped functions | Strong for one algorithm run | Strong for pure expressions | Depends on shared state discipline | Needs expiry and invalidation |
| Coupling | Caller sees a function | Caller often sees table shape | Caller sees lazy value | Caller sees shared object identity | Caller sees cache service policy |
| Operability | Needs hit, miss, size metrics | Table size is known | Space leaks can be subtle | Object sharing bugs can be subtle | Has external metrics and outages |
| Team topology | Owned near the function | Owned by algorithm author | Owned by language or library model | Owned by object model owner | Owned by platform and app teams |
| Best fit | Repeated calls discovered on demand | Known overlapping subproblems | Work that may not be needed | Many equal immutable objects | Cross-process reuse |
| Main risk | Stale or unbounded hidden state | Building unused cells | Deferred failure and retention | Shared mutable state | Serialization, staleness, network |

Engineering judgement. Memoization and dynamic programming are closest. The
difference is not the recurrence. It is the ownership of the table. Dynamic
programming usually makes the table an explicit part of an algorithm.
Memoization hides the table behind calls and fills it only for keys reached by
the run.

## 13. Related and incompatible patterns

**Dynamic Programming** often uses memoization as its top-down implementation.
A bottom-up table is better when the reachable subproblem set is dense and the
iteration order is clear.

**Lazy Evaluation** composes with memoization when a deferred expression is
evaluated once and then reused. It differs because laziness is about when work
starts, while memoization is about whether repeated work is skipped.

**Referential Transparency** is the property that makes memoization safe.
Without it, the key is incomplete because some hidden input controls the
result.

**Pure Function** is the natural unit to memoize. A pure function has no
observable side effects and its result is determined by inputs.

**Flyweight** shares object state rather than function results. It composes
when a memoized constructor returns canonical immutable objects.

**Proxy** can implement memoization by standing between caller and original
function. The proxy role is structural. The memoization policy is behavioral.

**Circuit Breaker** may wrap a memoized loader, but the two should not be
confused. A breaker limits calls to a failing dependency. Memoization reuses
answers for equal keys.

**Impure Functions** conflict with memoization because skipping a call skips
the effect.

**Observer-dependent Security Checks** conflict unless the key contains the
full subject, tenant, policy version, and resource version. An authorization
answer cached under only a resource ID is a defect.

**Mutable Iterator and Stream Results** conflict when the result is consumed.
Returning the same consumed iterator on the second call gives a different
behavior from recomputation.

## 14. Refactoring path in and out

To introduce Memoization:

1. Measure or prove repeated calls. Use a counter keyed by candidate arguments,
   a profiler, or an algorithmic proof of overlapping subproblems.
2. State the purity boundary. Write down which inputs determine the result and
   how long that statement remains true.
3. Choose the smallest lifetime that pays. Prefer request, render, object, or
   algorithm-run scope before process-wide scope.
4. Design the key. Normalize equivalent inputs and exclude irrelevant ones only
   when you can state why they do not affect the result.
5. Add a wrapper with counters for hits, misses, current size, and clear
   events.
6. Add tests that call the function twice and prove the second call does not
   run the original work.
7. Add tests for key collision, key fragmentation, and clearing.
8. Add a size cap or expiry unless the key space is finite and documented.
9. Roll out behind measurement. Keep direct-call timing so the cache can be
   removed when it loses value.

Named refactorings that often appear nearby include Extract Function, because
the calculation must be isolated before it can be memoized, and Replace Temp
with Query, when an expensive query becomes a named method whose value can be
cached on the object. Those names come from Martin Fowler, *Refactoring*,
second edition, Addison-Wesley, 2018, catalog entries "Extract Function" and
"Replace Temp with Query". No page number is cited here because this session
did not verify page locations.

To remove Memoization:

1. Read hit rate, miss cost, size, and stale result reports.
2. Add a flag or dependency injection path that calls the original function
   directly.
3. Run tests with the cache disabled. Failures reveal hidden reliance on
   identity reuse, stale values, or skipped effects.
4. Remove cache-specific key normalization only after callers no longer depend
   on it.
5. Delete metrics and clear hooks after the direct path has run in production.
6. Keep the extracted pure function if it improved design by itself.

Engineering judgement. The cleanest exit is possible when the memoized wrapper
is a separate function value. The hardest exit is a decorator or annotation
that many callers discover through reflection or framework magic.

## 15. Testing and verification

Memoized code needs two classes of tests. The first class proves semantic
equivalence. The second proves cache behavior.

Semantic tests call the memoized function with representative inputs and
compare results against the original function or a trusted oracle. Property
tests are useful for pure functions because they can generate many equivalent
argument forms. For example, if two argument orders should produce the same
normalized key, the property should exercise both orders.

Behavior tests use a spy or counter around the original function. Call the
memoized function twice with the same key and assert the counter increased
once. Call it with a different key and assert the counter increased again. If
the cache is bounded, fill past capacity and assert the selected victim is
recomputed. If the cache has TTL, inject a fake clock. Guava's cache guide
describes using the `Ticker` interface to test timed eviction without waiting
for real time
(https://github.com/google/guava/wiki/cachesexplained, verified 2026-08-02).

Concurrency tests depend on the chosen contract. If duplicate in-flight work is
allowed, test that the table remains coherent and both callers receive a valid
value. If single-flight behavior is required, block the original function,
start two callers, release it, and assert the original ran once. Do the same
for errors and cancellation.

Mutation tests are valuable. Pass a mutable object, mutate it after the first
call, then call again. The expected result should be explicit. Many teams
decide to reject mutable objects at the key boundary or key by immutable
snapshots.

Security tests should include tenant and user boundaries. A memoized permission
or data shaping function must include the subject and policy version in its key
or avoid memoization. A test should call as user A, then user B, and assert no
cross-user value reuse.

Verification in CI should compile code samples and run cache gates. For this
entry, the Python, TypeScript, Go, and Rust samples were compiled or run with
the local toolchain before completion.

## 16. Observability signals

Engineering judgement. A memoized function is production-visible only when the
cache path reports its behavior. Without signals, the team sees a black-box
function whose performance and correctness depend on call history.

Record these metrics per memoized function name and scope:

- request count
- hit count and hit rate
- miss count
- load duration on misses
- current entry count
- approximate retained bytes when practical
- eviction count by cause
- explicit clear count
- stale result reports
- duplicate in-flight miss count
- error entry count if failures are cached

Trace attributes should include the memoized function name, hit or miss, key
class, key cardinality bucket, and load duration. Do not log raw keys when keys
can contain personal data, secrets, tokens, query text, or tenant names. Log a
hash or a classified key shape instead.

A healthy dashboard shows stable or improving hit rate under the workload that
motivated the memoizer, bounded entry count, low eviction churn, miss duration
that matches the original work, and no stale result alarms. It also shows that
hit rate is near zero for workloads where no repetition is expected, because
that can be the signal to remove the wrapper.

A failing dashboard shows one of four patterns.

- **Low hit rate plus growing size.** The cache is storing one-off keys.
- **High hit rate plus stale result reports.** The lifetime or key omits a
  hidden input.
- **High miss latency plus many duplicate in-flight misses.** The memoizer is
  not coalescing work under concurrency.
- **High eviction churn.** The size cap is too small, the key is fragmented, or
  the workload does not have temporal locality.

Guava exposes cache statistics such as hit rate, average load penalty, and
eviction count through `CacheStats` when `recordStats()` is enabled
(https://github.com/google/guava/wiki/cachesexplained, verified 2026-08-02).
Python exposes `cache_info()` on `lru_cache` wrappers, including hits, misses,
max size, and current size
(https://docs.python.org/3/library/functools.html?highlight=total_ordering,
verified 2026-08-02).

## 17. Security and privacy implications

Memoization is silent about authorization. It makes prior answers easier to
reuse, which is safe only when the key contains every security-relevant input
or the result is public across all callers sharing the cache.

The main security risks are cache key under-specification, secret retention,
and unbounded cardinality. A permission result keyed only by resource ID can
leak access from one user to another. A rendered fragment keyed only by URL can
leak tenant-specific content. A memoized token introspection result can outlive
revocation unless the key or lifetime includes the token's expiry and policy
version. A public endpoint that feeds raw query strings into an unbounded
memoizer can be used to consume memory.

The main privacy risk is retention. Keys and values often contain more personal
data than the function name suggests. A memoized search, recommendation,
normalization, or profile computation can retain names, emails, addresses,
medical terms, query text, or internal IDs. Treat the memo table as a data
store for classification, logging, retention, and deletion purposes.

Practical rules:

- Include tenant, subject, locale, policy version, and data version in keys
  when they affect the result.
- Prefer short lifetimes for user-specific data.
- Avoid raw secret-bearing keys. Use keyed hashes when equality is needed.
- Do not cache authorization failures or successes beyond the policy lifetime.
- Bound attacker-influenced key spaces.
- Clear memo tables on logout, tenant switch, policy reload, and test reset
  when the cache scope crosses those events.
- Do not log raw keys. Log key type and a redacted or hashed form.

Engineering judgement. Memoization is safest for pure public computations, such
as parsing a grammar file in a build or computing a mathematical value. It is
riskiest when applied to security, billing, identity, and personalization code,
because "same arguments" is rarely the full question in those domains.

Incident response should include a cache bypass path for high-risk memoizers.
That path can be a process restart, a clear endpoint guarded by operations
controls, or a configuration flag that disables the wrapper. The exact shape
depends on the system, but the requirement is simple: when the table is the
suspect, the team needs a way to prove it quickly. A memoized function that can
only be cleared by redeploying every process raises recovery time and makes a
stale-value incident harder to contain.

## 18. References

- Donald Michie, "'Memo' Functions and Machine Learning", Nature, volume 218,
  pages 19-22, 1968. OpenAIRE record with DOI links and bibliographic metadata:
  https://explore.openaire.eu/search/publication?pid=10.1038%2F218019a0,
  verified 2026-08-02.
- Python Software Foundation, "functools. Higher-order functions and
  operations on callable objects", Python 3.14 documentation, sections
  `functools.cache`, `functools.cached_property`, and `functools.lru_cache`:
  https://docs.python.org/3/library/functools.html?highlight=total_ordering,
  verified 2026-08-02.
- React documentation, "`useMemo`", React 19.2 API Reference:
  https://react.dev/reference/react/useMemo, verified 2026-08-02.
- React documentation, "`cache`", React 19.2 API Reference:
  https://react.dev/reference/react/cache, verified 2026-08-02.
- Google Guava project, "CachesExplained", Guava wiki:
  https://github.com/google/guava/wiki/cachesexplained, verified 2026-08-02.
- Clojure API documentation, "`clojure.core/memoize`", Clojure v1.13.0 API:
  https://clojure.github.io/clojure/branch-master/clojure.core-api.html,
  verified 2026-08-02.
- Clojure core.memoize documentation, "core.memoize API Reference":
  https://clojure.github.io/core.memoize/, verified 2026-08-02.
- Django Software Foundation, "Performance and optimization",
  `cached_property` section, Django documentation:
  https://docs.djangoproject.com/en/4.2/topics/performance/, verified
  2026-08-02.
- LLVM project, "MemorySSA", LLVM documentation, "Use and Def optimization":
  https://www.llvm.org/docs/MemorySSA.html, verified 2026-08-02.
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, second
  edition, Addison-Wesley, 2018, catalog entries "Extract Function" and
  "Replace Temp with Query". Page numbers not cited because they were not
  verified in this session.
