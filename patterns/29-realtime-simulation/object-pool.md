---
name: Object Pool
slug: object-pool
family: 29-realtime-simulation
category: Real-Time Simulation
aliases: [Pool Allocator, Free List, Reusable Object Pool]
first_described: "Robert Nystrom's Object Pool chapter in Game Programming Patterns, in the book's own Optimization Patterns part"
maturity: canonical
related: [game-loop]
incompatible_with: []
verified: 2026-08-23
---

# Object Pool

## 1. Name, aliases, and lineage

An object pool maintains a fixed collection of reusable objects, allocated
once up front, and cycles them between an active and an inactive state
rather than constructing and destroying instances repeatedly. It is also
called a pool allocator, and its allocation mechanism is often implemented
as a free list.

The clearest, directly verified source is Robert Nystrom's own chapter,
which this entry fetched directly (Nystrom, Robert, "Object Pool," Game
Programming Patterns, https://gameprogrammingpatterns.com/object-pool.html,
verified 2026-08-23). Nystrom's own book places the chapter in its
Optimization Patterns part, alongside Data Locality, Dirty Flag, and
Spatial Partition, confirmed via the book's own table of contents
(https://gameprogrammingpatterns.com/contents.html, verified 2026-08-23).

## 2. Problem and context

Repeatedly allocating and freeing short-lived objects, particles, bullets,
network connections, on a hot path costs more than the allocation itself.
Nystrom's own text names two distinct costs directly. fragmentation,
"fragmentation means the free space in our heap is broken into smaller
pieces of memory instead of one large open block," and raw allocation
speed, which the chapter frames as especially costly on resource-
constrained platforms such as game consoles and mobile devices (Nystrom,
"Object Pool," verified 2026-08-23). this shows up anywhere a simulation,
a game, or a server repeatedly creates and destroys many short-lived
objects of the same kind, whether particles in a game or connections in a
database client.

## 3. Forces

Nystrom's own text names the central sizing tension directly, in both
directions at once. "When tuning, it's usually obvious when the pool is
too small (there's nothing like a crash to get your attention)" while "take
care that the pool isn't too big. A smaller pool frees up memory that could
be used for other fun stuff" (Nystrom, "Object Pool," verified 2026-08-23).
a pool exists to trade memory, held up front for the lifetime of the pool,
against the allocation and fragmentation cost from dimension 2, and getting
that trade wrong in either direction is a real, sourced cost, not a
theoretical one.

A second, counterintuitive tension appears in real production connection
pools, where a bigger pool is often worse, not better. HikariCP's own
documentation states this directly, with a real, measured result. "Reducing
the connection pool size alone, in the absence of any other change,
decreased the response times of the application from about 100ms to about
2ms, over 50x improvement," reasoning from "a basic Law of Computing that
given a single CPU resource, executing A and B sequentially will always be
faster than executing A and B simultaneously through time-slicing" (HikariCP,
"About Pool Sizing," https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing,
verified 2026-08-23). so the naive assumption, more pooled resources means
more throughput, is a real, sourced misconception this entry's own dimension
11 covers as a genuine failure mode.

## 4. Applicability and non-applicability

Object pooling applies to any short-lived object allocated and destroyed
frequently enough that the cost from dimension 2 is measurable, particles,
bullets, and enemies in a game, or connections in a client talking to a
database. PgBouncer's own configuration documentation confirms a real,
current, non-game production use directly, offering a `min_pool_size`
setting that "adds more server connections to pool if below this number,
improves behavior when the normal load suddenly comes back after a period
of total inactivity," and a `reserve_pool_size` and `reserve_pool_timeout`
pair so that "if a client has not been serviced in this time, use additional
connections from the reserve pool" (PgBouncer, "Configuration,"
https://www.pgbouncer.org/config.html, verified 2026-08-23), a direct,
documented answer to the too-small-pool stall case from dimension 3.

The pattern is a poor fit for objects that are long-lived, allocated
rarely, or expensive enough per-instance that a fixed-size pool wastes more
memory than it saves. Nystrom's own stated memory cost from dimension 3
means a pool sized for a peak load that rarely occurs holds that memory
unused most of the time, and this entry did not find a source stating this
non-applicable case explicitly, reporting it as this entry's own reasoned
inference from the pattern's own stated trade-off rather than a directly
sourced claim.

## 5. Structure

Nystrom's own text describes the simplest implementation directly. "the
simplest object pool implementation is almost trivial. create an array of
objects and reinitialize them as needed," tracked with an explicit in-use
flag per object (Nystrom, "Object Pool," verified 2026-08-23). a more
efficient variant, per the same source, overlays pointer data onto the
memory of an unused object using a union, forming "a linked list that
chains together every unused particle in the pool," giving constant-time
allocation from the pool instead of a linear scan for a free slot (Nystrom,
"Object Pool," verified 2026-08-23).

Nystrom's own Design Decisions section names two further structural
choices with real trade-offs. whether objects are tightly coupled to the
pool, which "makes sure that other code doesn't maintain references to
objects that could be unexpectedly reused" at the cost of a less generic,
non-reusable pool class, versus a decoupled, generic pool usable for any
object type. and whether the pool itself or the calling code is
responsible for initializing a reused object, trading interface simplicity
against error-handling responsibility (Nystrom, "Object Pool," verified
2026-08-23).

## 6. ASCII structure diagram

```
  pool, allocated once, fixed size:

  +------+------+------+------+------+------+
  | IN   | free | free | IN   | free | IN   |
  | USE  |      |      | USE  |      | USE  |
  +------+------+------+------+------+------+
           ^
           free-list head points to the next free slot
           each free slot's own memory doubles as a
           pointer to the NEXT free slot (a union)

  request a new object:
       |
       v
  pop the free-list head -> mark IN USE -> return it
  (no allocation call, no fragmentation, O(1))

  release an object:
       |
       v
  mark it free -> push it back onto the free-list head
  (no deallocation call, the slot is instantly reusable)
```

## 7. Dynamics

Requesting an object pops the free-list head, per dimension 5's mechanism,
marks it in use, and returns it, an O(1) operation with no allocation call
involved. Releasing an object reverses this, marking the slot free and
pushing it back onto the free-list head, so the same memory is immediately
available for the next request with no deallocation call either.

Unity's own current, official `ObjectPool<T>` API documents real,
production dynamic behaviour at the pool's own capacity boundary. "If the
pool has reached its maximum size then the instance is destroyed using the
method passed as the actionOnDestroy parameter to the constructor," and,
separately, "if the pool capacity is reached then any items returned will
be destroyed" (Unity Technologies, "ObjectPool<T>," Unity 6000.0 Scripting
Reference,
https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Pool.ObjectPool_1.html,
verified 2026-08-23), a real, documented instance of the too-many-active-
objects boundary dimension 3's sizing tension describes.

## 8. Implementation variants

HikariCP, a real, widely used JVM database connection pool, implements the
sizing philosophy from dimension 3 as an explicit, stated design axiom.
"you want a small pool, saturated with threads waiting for connections,"
with a formula the same source gives directly, connections equals core
count times two plus the effective spindle count, worked through a
concrete example, "your little 4-Core i7 server with one hard disk should
be running a connection pool of 9, that is, (4 times 2) plus 1" (HikariCP,
"About Pool Sizing," verified 2026-08-23).

PgBouncer, a real, current PostgreSQL connection pooler, implements the
in-use versus free tracking from dimension 5 at the database-connection
level, with `default_pool_size` as "the maximum number of server
connections to allow per user/database pair," and states its own memory
efficiency directly, "low memory requirements, 2 kB per connection by
default" (PgBouncer, "Configuration," verified 2026-08-23; PgBouncer,
"Features," https://www.pgbouncer.org/features.html, verified 2026-08-23).

Unity's `ObjectPool<T>`, per dimension 7, implements a real, current,
capacity-bounded variant with a documented safety feature dimension 15
covers as a testing technique. "collection checks will throw errors if we
try to release an item that is already in the pool" (Unity Technologies,
"ObjectPool<T>," verified 2026-08-23).

## 9. Known production uses

HikariCP is a real, current, widely used JVM connection pool shipped in
production Java applications, and its own documentation, per dimension 8,
carries a measured real-world result. reducing pool size cut response time
by over fifty times in one reported case (HikariCP, "About Pool Sizing,"
verified 2026-08-23), strong direct evidence the pattern is applied at real
scale rather than only described in theory.

PgBouncer is a real, current, widely used PostgreSQL connection pooler
deployed in front of production databases, per dimension 8, and Unity's
`ObjectPool<T>` is a real, current, official, shipped API used across
production games built on the engine, per dimensions 7 and 8. all three are
current, live-verified sources rather than deprecated or historical
examples.

## 10. Consequences

The pattern removes the allocation and fragmentation cost from dimension 2
entirely from the hot path, since a pooled request and release are both
O(1) operations with no allocator call involved, per dimension 7. this
consequence compounds under sustained churn, a game spawning and
destroying hundreds of particles per second, or a server handling a steady
stream of short-lived database queries, exactly the workloads dimension 4
names as the pattern's own best fit.

The trade, per dimension 3, is memory held for the pool's full configured
size regardless of instantaneous demand, and, per dimension 5's coupling
design decision, either a less generic pool implementation or a real risk
of a stale reference to a reused slot if the calling code is not careful
about ownership. HikariCP's own counterintuitive finding from dimension 3,
that a larger pool can make things slower under contention, is a direct
consequence of the pattern's own sizing choice interacting with the
underlying resource it pools, not a flaw in the pattern itself.

## 11. Failure modes and misuse

Sizing the pool wrong is the most directly sourced failure mode, in both
directions, per dimension 3's own quoted text. too small, and "your
attempt to reuse an object from the pool will fail because they are all in
use," with "nothing like a crash to get your attention." too large, and the
pool wastes memory "that could be used for other fun stuff" (Nystrom,
"Object Pool," verified 2026-08-23).

A second, subtler failure mode is a stale reference to a reused slot. code
elsewhere in the program holding onto a reference to a pooled object after
it has been released and reused for something else reads or writes data
that no longer means what it thinks it means. Nystrom's own text addresses
this risk directly, though not by a specific name, as the reason tight
coupling to the pool is one design option. it "makes sure that other code
doesn't maintain references to objects that could be unexpectedly reused"
(Nystrom, "Object Pool," verified 2026-08-23). this entry could not find a
second, citable source using a specific term such as zombie object for this
exact bug within the available research, and reports that absence honestly
rather than asserting the term is standard vocabulary.

A third, real, sourced misuse is HikariCP's own counterintuitive finding
from dimension 3, sizing a connection pool larger under the assumption that
more pooled connections always means more throughput, when the source's
own measured result shows the opposite under CPU contention (HikariCP,
"About Pool Sizing," verified 2026-08-23).

## 12. Trade-off matrix

| Dimension | Object pool | Allocate and free directly |
|---|---|---|
| Allocation cost on the hot path | O(1), no allocator call, dimension 7 | Real allocator overhead every time |
| Fragmentation | Avoided, one contiguous block up front | A real risk under sustained churn, dimension 2 |
| Memory footprint | Fixed, held for the pool's full size, dimension 10 | Scales exactly with live object count |
| Stale-reference risk | Real, per dimension 11, needs coupling discipline | Not applicable, memory is truly freed |
| Best fit | Frequent, short-lived, same-type objects, dimension 4 | Rare or long-lived allocations |
| Sizing sensitivity | High, wrong size fails or wastes memory, dimension 3 | Low, the allocator handles variable demand |

## 13. Related and incompatible patterns

Nystrom's own See Also section names exactly two related patterns, and
this entry verified the section does not name a third. Flyweight and Data
Locality (Nystrom, "Object Pool," verified 2026-08-23). the distinction from
Flyweight, per the source, is temporal rather than structural. both manage
reusable objects, but Flyweight shares one instance simultaneously among
multiple logical owners, while Object Pool reuses a slot sequentially over
time, reclaimed and handed out again later rather than shared concurrently.
Data Locality is named as complementary, since a pool's own contiguous
backing array is exactly the memory layout Data Locality wants for cache-
friendly iteration.

This entry explicitly checked whether Object Pool's own See Also section
names Spatial Partitioning and confirmed it does not, despite both sitting
in the same Optimization Patterns part of the book, per dimension 1. this
entry also explicitly checked Update Method's own See Also section for a
reference back to Object Pool and confirmed one is not present there
either. so, unlike this catalogue's own Game Loop, Entity-Component-System,
and Spatial Partitioning entries, which share a documented bridge through
Update Method, Object Pool has no sourced connection to that per-frame
cadence, and this entry reports that absence directly rather than
inventing a pairing.

Object Pool has no directly incompatible pattern named in the sourced
material.

## 14. Refactoring path in and out

Refactoring direct allocation into an object pool starts by measuring
whether the allocation and fragmentation cost from dimension 2 is real for
the target workload, since Nystrom's own text frames the pattern as an
optimization applied to a measured problem, not a default. build the fixed-
size array and choose an in-use flag or a free-list implementation, per
dimension 5, then decide the two design axes from that same dimension,
coupling to the pool and who initializes reused objects, before wiring the
pool into the request and release paths from dimension 7. size the pool by
measuring real peak concurrent demand, per dimension 3, rather than
guessing, and verify the choice against both stated failure directions,
too small causing stalls, too large wasting memory.

Refactoring out of an object pool, back to direct allocation, is driven by
discovering the measured cost from dimension 2 was never significant for
the actual workload, or by HikariCP's own counterintuitive finding from
dimension 11, that the pooled resource itself becomes the bottleneck under
contention regardless of pool size, a case where reducing or removing
pooling, not resizing it, is the correct fix.

## 15. Testing and verification

Unity's own `ObjectPool<T>` documents a real, citable, production testing
technique built directly into the API. "collection checks will throw
errors if we try to release an item that is already in the pool" (Unity
Technologies, "ObjectPool<T>," verified 2026-08-23), a runtime assertion
that catches the double-release class of bug, releasing the same object
twice, which would otherwise silently corrupt the free-list from dimension
5 by inserting a duplicate entry.

This entry explicitly checked for, and could not find, a citable source
describing a named "assert the pool never exceeds its configured maximum
size" unit-test pattern, and the primary book source does not discuss
testing methodology for the pattern at all. this is reported as an honest,
open gap rather than an invented technique. in its absence, the reasoned,
generally applicable approach follows directly from Unity's own real
mechanism. assert that a released object matches an object the pool
actually issued and has not already reclaimed, and assert that a request
against a fully-occupied pool behaves exactly as the implementation
documents, per dimension 7's own boundary behaviour, whether that is a
failure, a wait, or a destroy-and-replace.

## 16. Observability signals

Pool exhaustion rate, requests that arrive when the pool is fully occupied,
measured directly, is the most direct signal for the sizing failure mode
from dimension 11. a nonzero, sustained exhaustion rate is the same
condition Nystrom's own text calls a crash-worthy signal, caught earlier
and less destructively through a metric than through a production
incident.

Wait time for a pooled resource, distinct from exhaustion, names PgBouncer's
own reserve-pool condition from dimension 4 directly, the time a client
spends waiting before an additional connection is granted from the reserve.
a rising wait time under stable load is the leading indicator that
precedes outright exhaustion.

Utilization, the share of the pool actually in use at a point in time,
sampled over a representative load window, is the signal HikariCP's own
counterintuitive finding from dimension 3 depends on. a pool that never
approaches full utilization is a direct, measured case for shrinking it,
per dimension 3's own real, quoted result that a smaller pool measurably
outperformed a larger one under contention.

## 17. Security and privacy implications

A pooled connection or object that is reused without being fully reset
carries a real, practical security risk this entry did not find directly
addressed in either PgBouncer's or HikariCP's own fetched documentation,
though the concern follows directly from the pattern's own reuse mechanism
from dimension 5. a database connection returned to the pool after one
tenant's request and handed to a different tenant's request without
resetting session-level state, a role, a search path, a temporary setting,
can leak that prior tenant's context into the new request. this is
reported as this entry's own reasoned extension of the pattern's own
structure, not a citation from the sourced material, and it argues for
resetting connection-level state on return to the pool as a default,
never an opt-in.

The stale-reference risk from dimension 11 has a security-adjacent reading
too. an object reused while an old reference to it is still held elsewhere,
per Nystrom's own stated coupling rationale, can let one part of a program
read or write data it should no longer have access to, through a reference
it should no longer hold, which is a data-integrity and access-control
concern as much as a correctness bug.

## 18. References

1. Nystrom, Robert, "Object Pool," Game Programming Patterns,
   https://gameprogrammingpatterns.com/object-pool.html, verified
   2026-08-23.
2. Nystrom, Robert, "Game Programming Patterns," table of contents,
   https://gameprogrammingpatterns.com/contents.html, verified 2026-08-23.
3. HikariCP, "About Pool Sizing,"
   https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing,
   verified 2026-08-23.
4. PgBouncer, "Configuration," https://www.pgbouncer.org/config.html,
   verified 2026-08-23.
5. PgBouncer, "Features," https://www.pgbouncer.org/features.html, verified
   2026-08-23.
6. Unity Technologies, "ObjectPool<T>," Unity 6000.0 Scripting Reference,
   https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Pool.ObjectPool_1.html,
   verified 2026-08-23.

## Code

TypeScript, Python, and Go implementations of an object pool using the
free-list mechanism from dimension 5, with double-release detection
following Unity's own collection-checks approach from dimension 15.

```typescript
class ObjectPool<T> {
  private free: T[] = [];
  private issued = new Set<T>();

  constructor(
    private factory: () => T,
    private reset: (item: T) => void,
    initialSize: number
  ) {
    for (let i = 0; i < initialSize; i++) {
      this.free.push(this.factory());
    }
  }

  acquire(): T {
    const item = this.free.pop() ?? this.factory();
    this.issued.add(item);
    return item;
  }

  release(item: T): void {
    if (!this.issued.has(item)) {
      throw new Error("released an item not currently issued by this pool");
    }
    this.issued.delete(item);
    this.reset(item);
    this.free.push(item);
  }

  size(): { free: number; issued: number } {
    return { free: this.free.length, issued: this.issued.size };
  }
}
```

```python
from typing import Callable, Generic, List, Set, TypeVar

T = TypeVar("T")


class ObjectPool(Generic[T]):
    def __init__(
        self,
        factory: Callable[[], T],
        reset: Callable[[T], None],
        initial_size: int,
    ) -> None:
        self._factory = factory
        self._reset = reset
        self._free: List[T] = [factory() for _ in range(initial_size)]
        self._issued: Set[int] = set()

    def acquire(self) -> T:
        item = self._free.pop() if self._free else self._factory()
        self._issued.add(id(item))
        return item

    def release(self, item: T) -> None:
        if id(item) not in self._issued:
            raise ValueError("released an item not currently issued by this pool")
        self._issued.discard(id(item))
        self._reset(item)
        self._free.append(item)

    def sizes(self) -> tuple:
        return (len(self._free), len(self._issued))
```

```go
package objectpool

import "fmt"

type Pool[T any] struct {
	factory func() T
	reset   func(*T)
	free    []*T
	issued  map[*T]bool
}

func New[T any](factory func() T, reset func(*T), initialSize int) *Pool[T] {
	p := &Pool[T]{
		factory: factory,
		reset:   reset,
		issued:  make(map[*T]bool),
	}
	for i := 0; i < initialSize; i++ {
		v := factory()
		p.free = append(p.free, &v)
	}
	return p
}

func (p *Pool[T]) Acquire() *T {
	var item *T
	if n := len(p.free); n > 0 {
		item = p.free[n-1]
		p.free = p.free[:n-1]
	} else {
		v := p.factory()
		item = &v
	}
	p.issued[item] = true
	return item
}

func (p *Pool[T]) Release(item *T) error {
	if !p.issued[item] {
		return fmt.Errorf("released an item not currently issued by this pool")
	}
	delete(p.issued, item)
	p.reset(item)
	p.free = append(p.free, item)
	return nil
}

func (p *Pool[T]) Sizes() (free int, issued int) {
	return len(p.free), len(p.issued)
}
```
