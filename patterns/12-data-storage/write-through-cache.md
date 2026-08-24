---
name: Write-Through Cache
slug: write-through-cache
family: 12-data-storage
category: Data and Storage
aliases: [Synchronous Cache Update, Write-Through Caching Strategy]
first_described: "Industry practice, no single named originator. Formalized in CPU cache literature and later reused for application caches."
maturity: canonical
related: [cache-aside, write-behind-cache, read-through-cache, refresh-ahead-cache, circuit-breaker]
incompatible_with: [write-behind-cache]
verified: 2026-08-02
---

# Write-Through Cache

## 1. Name, aliases, and lineage

The canonical name is Write-Through Cache, sometimes written write through cache
or spelled as one policy term, write-through. It names a write policy for a
cache sitting in front of a slower store, where every write is applied to the
cache and to the backing store as one operation, and the write is not
acknowledged to the caller until both have succeeded.

The term has no single named inventor the way Factory Method has Gamma, Helm,
Johnson and Vlissides. It comes out of CPU memory hierarchy design, where the
choice between updating main memory on every store instruction and updating it
only when a dirty line is evicted has been studied since the earliest cache
designs. Hennessy and Patterson describe the write-through and write-back
policies as the two standard choices for keeping a cache consistent with the
next level of the memory hierarchy, in the appendix that surveys cache basics
(John L. Hennessy and David A. Patterson, *Computer Architecture. A
Quantitative Approach*, 6th edition, Morgan Kaufmann, 2017, Appendix B, "Review
of Memory Hierarchy", the section comparing write-through and write-back cache
policies).

The application-level use of the same term, a cache object sitting between a
service and a database, an object store, or a remote service, adopted the
hardware vocabulary directly because the trade-off is the same one degree
removed. Amazon Web Services documents it under exactly this name in its
caching strategy material for Amazon ElastiCache and Amazon DynamoDB
Accelerator, describing write-through as writing data into the cache and the
corresponding database at the same time
([Amazon ElastiCache for Memcached, "Caching strategies for Memcached", the
"Adding a data caching layer" section describing write-through](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html),
verified 2026-08-02). Oracle Coherence uses the identical term for its
`CacheStore` integration, and Ehcache names the same behaviour `write-through`
mode on its `CacheWriter` interface, cited fully in dimension 9.

**Synchronous Cache Update** is a descriptive alias used in some database
textbooks and vendor material to avoid confusion with the CPU-cache sense of
the word, because "write-through" alone, spoken in a room with both database
engineers and hardware engineers, can mean two related but distinct
mechanisms. This entry covers the application-layer, network-attached cache
sense throughout, and calls out the CPU-cache sense only where the analogy is
useful.

A short definition that separates it cleanly from its two closest relatives.
Write-through updates the cache and the store together, synchronously, on
every write. Write-behind, also called write-back at the application layer,
updates the cache immediately and the store later, asynchronously. Cache-aside
does not intercept writes at all, the application writes to the store directly
and the cache is only populated on a read miss or invalidated on a write.

## 2. Problem and context

A service reads the same records far more often than it writes them, and the
backing store, whether a relational database, a document store, or a remote
API, is the slowest part of the read path. The obvious answer is a cache. The
question this pattern answers is narrower than "should we cache reads", it is
"what happens to the cache the moment a write arrives".

Two naive answers exist and both create the class of bug this pattern exists
to prevent. The first naive answer is to write to the store and do nothing to
the cache. The next read either serves stale data from the cache until it
expires, or the cache key happens to line up with a lazy invalidation and the
read falls through to the store, which reintroduces the exact latency the
cache was built to avoid, right after every write. The second naive answer is
to write to the store and then invalidate the cache entry rather than update
it. This avoids serving stale data, at the price of a guaranteed cache miss on
the very next read of that key, which is often the read that follows a write
in the same request, for example an API that writes a resource and returns it
in the same response.

Write-through exists for the case where the application can tolerate the
latency of writing to two places on every write, in exchange for a guarantee
that a read immediately after a write, from any replica of the cache that has
already observed the write, returns the value that was just written, with no
window of staleness and no forced miss. The context in which this trade makes
sense has three properties. Reads outnumber writes by a wide margin, so the
extra latency on the rarer operation is worth paying to keep the common
operation fast and correct. The store must be durable and is the system of
record, the cache is disposable and can be rebuilt from the store at any time.
And correctness of the very next read matters more than raw write throughput,
which rules the pattern out for write-heavy, latency-sensitive ingestion paths
such as a metrics collector or a click stream, see dimension 4.

## 3. Forces

- **Read latency after a write.** Favoured, and this is the pattern's whole
  reason to exist. The cache is guaranteed current the instant the write call
  returns, so the next read pays cache latency, not store latency.
- **Write latency.** Sacrificed. Every write now pays for two round trips
  instead of one, the cache write and the store write, and the caller waits
  for both.
- **Consistency between cache and store.** Favoured, within the bounds of
  dimension 11's discussion of partial failure. There is no window in which
  the store has a value the cache does not, because the write is not
  considered successful until both are updated.
- **Availability of the write path.** Sacrificed. The write path now has two
  dependencies where it used to have one, so a cache outage can take down
  writes even though the cache exists purely to speed up reads.
- **Cache freshness under normal operation.** Favoured. Because the cache is
  updated on every write and not merely invalidated, the cache never needs a
  read-through fetch to repopulate a key that was just written.
- **Operational simplicity.** Mixed. The single-writer-updates-both-places
  shape is easy to reason about compared to write-behind's asynchronous queue,
  but harder than cache-aside's simple invalidate-on-write, because the write
  path now owns two systems instead of one and must decide what to do when
  they disagree, see dimension 11.
- **Cost.** Sacrificed relative to cache-aside. A write that never gets read
  again, for example an audit log entry, still pays to populate the cache,
  which is wasted work and wasted cache memory. AWS's own material calls this
  out directly, warning that write-through causes cache churn when most
  written data is rarely read
  ([Amazon DynamoDB Accelerator (DAX) documentation, "DAX and DynamoDB
  consistency models", the discussion of write-through behaviour and its
  cost](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.consistency.html),
  verified 2026-08-02).

No pattern gives up nothing. Write-through trades write latency and write-path
availability for guaranteed post-write read freshness, and it trades cache
efficiency for simplicity of the freshness guarantee.

## 4. Applicability and non-applicability

Reach for write-through when the following hold.

- Reads to a given key happen soon after a write to that key, and stale data
  in that window would be visibly wrong to a user, for example a shopping
  cart total, an account balance display, or a profile page shown immediately
  after the user edits it.
- The write rate is low relative to the read rate, so the extra write latency
  is paid rarely and the freshness benefit is enjoyed constantly.
- The system of record is a durable store that the team trusts, and the cache
  is explicitly disposable, rebuildable from the store with no data loss if
  the cache is flushed.
- The application can afford to wait for both the cache and the store to
  acknowledge a write before returning success to the caller, and treating a
  cache-write failure as a whole-operation failure is an acceptable trade,
  see dimension 11.
- The workload benefits from cache population happening on the write path
  rather than lazily on the read path, because the first reader after a write
  should not pay a cold-cache penalty. This is the same shape DAX documents as
  its default behaviour for DynamoDB item writes
  ([Amazon DynamoDB Accelerator (DAX), "How it works", description of write
  operations updating both the table and the DAX cluster before returning
  success](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.concepts.html),
  verified 2026-08-02).

Do NOT reach for write-through in these cases.

- **The write rate is high and most written values are read rarely or never.**
  An event ingestion pipeline, a metrics collector, or an audit trail writes
  constantly and reads occasionally through a dashboard. Populating the cache
  on every write fills it with entries nobody asks for and evicts entries that
  matter, which is exactly the churn AWS warns about. Cache-aside, populating
  on read miss only, is the honest shape here.
- **Write latency is on the critical path and every millisecond counts.** A
  payment authorization step, a high-frequency trading order path, or any
  write where the caller is latency-sensitive should not be made to wait on a
  second system that exists purely to speed up an unrelated read path.
  Write-behind, accepting the write into the cache and flushing to the store
  asynchronously, exists for exactly this case, at the cost of a durability
  window discussed in dimension 13.
- **The backing store is the sole system of record and the cache client
  cannot tolerate the store being briefly unavailable for writes.** If the
  cache sits on the write path and the cache is down, the naive
  implementation now blocks all writes, turning a performance optimisation
  into a new single point of failure. See the failure-mode discussion in
  dimension 11 for the mitigation, and weigh whether that added complexity is
  worth it before choosing this pattern.
- **The data changes are computed, not supplied by the writer.** If the value
  that should end up in the cache is the product of a database-side
  computation, a trigger, a default value, or a generated identifier, the
  application does not actually know the final value at write time and cannot
  write it into the cache without a second read from the store, which
  defeats the purpose. A read-through or cache-aside shape that re-fetches
  after the write is more honest here.
- **Multiple independent writers can write the same key concurrently and the
  store enforces its own conflict resolution, such as optimistic
  concurrency control or a last-writer-wins timestamp.** A write-through
  cache that is not made aware of a rejected or reordered store write can end
  up holding a value the store never actually committed, see dimension 11.

## 5. Structure

Three participants, named by the role they play.

- **Client.** The application code that performs a write. It calls one
  operation, conceptually "set", and expects a single success or failure
  result, not two separate operations to coordinate itself.
- **CacheStore, sometimes called the write-through wrapper or the cache
  facade.** The component that receives the client's write and is responsible
  for applying it to both the Cache and the BackingStore, in a defined order,
  before returning to the Client. This is the seat where the ordering
  decision and the failure-handling decision from dimension 11 actually live.
  In Ehcache and Oracle Coherence this role is filled by the `CacheWriter` or
  `CacheStore` interface implementation, called by the cache library itself
  rather than hand-written by application code, see dimension 9.
- **Cache and BackingStore.** Two independent stores with different latency
  and durability characteristics. Cache is fast and usually volatile,
  typically an in-memory store such as Redis or Memcached, or a managed
  service such as DAX. BackingStore is slower and durable, typically a
  relational database, a document store, or a remote service that the
  application does not own.

The defining structural fact, the one that separates this from cache-aside, is
that the CacheStore is a single seam both the write path and the read path go
through. A cache-aside implementation has the application write to
BackingStore directly and separately, optionally, invalidate Cache. A
write-through implementation has the application call one method on
CacheStore, and CacheStore owns writing to both underlying stores in the same
call.

## 6. ASCII structure diagram

```
   +--------+          +------------------------+
   | Client |  write   |       CacheStore        |
   |        |--------->|  (write-through wrapper) |
   +--------+          +------------------------+
        ^                    |              |
        | read (fast path)   | write        | write
        |                    v              v
   +----------+        +----------+   +---------------+
   |  Cache   |<-------|  Cache   |   | BackingStore  |
   | (fast,   |  (same |          |   | (slow,        |
   |  usually |  store)+----------+   |  durable,     |
   |  volatile)                       |  system of    |
   +----------+                       |  record)      |
                                       +---------------+

   Write path. Client -> CacheStore -> Cache AND BackingStore, both
   before the write is acknowledged back to Client.
   Read path. Client -> Cache directly, bypassing CacheStore and
   BackingStore on a hit, because Cache is already current.
```

## 7. Dynamics

The dynamics have two flows worth separating, the write flow, where the
pattern does its real work, and the read flow, which is deliberately ordinary
once the write flow has done its job.

```
Client         CacheStore              Cache            BackingStore
  |                 |                    |                    |
  |-- write(k, v) ->|                    |                    |
  |                 |-- write BackingStore first ------------>|
  |                 |                    |                    |
  |                 |<-- ack or error --------------------------|
  |                 |                    |                    |
  |                 | (only if BackingStore ack succeeded)     |
  |                 |-- set(k, v) ------>|                    |
  |                 |<-- ack ------------|                    |
  |                 |                    |                    |
  |<-- success -----|                    |                    |
  |                 |                    |                    |
  |-- read(k) --------------------------->|                    |
  |<-- v (cache hit, no store round trip)-|                    |
```

The ordering shown, BackingStore first, Cache second, is the safer of the two
possible orderings and is discussed at length in dimension 11 because getting
it backwards is the single most common implementation mistake in this
pattern. Writing the store first means a cache failure after a successful
store write leaves the cache stale rather than leaves the store holding data
nobody durably committed. A stale cache is recoverable by eviction or a
read-through refetch. A store that never received a write that the cache
already reflects is a silent data-loss bug, because the client believes the
write succeeded.

Two further timing notes. First, when the Cache is a distributed system with
its own replication, the "cache write acknowledged" step in the diagram may
itself only guarantee the write reached one replica, and a reader hitting a
different replica can still observe staleness for a short window, this is a
property of the Cache's own consistency model, not of the write-through
pattern itself, and DAX's own documentation is explicit that DAX write-through
consistency is per-cluster, not instantaneous across every client connection
([Amazon DynamoDB Accelerator (DAX), "DAX and DynamoDB consistency models"](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.consistency.html),
verified 2026-08-02). Second, when CacheStore batches several client writes
into one underlying store call for efficiency, the acknowledgement to each
individual client must not be sent until that client's specific write is
durably part of the batch that succeeded, batching write-through writes
without preserving this per-write acknowledgement boundary reintroduces the
write-behind durability window under a write-through name.

## 8. Implementation variants

**Store first, then cache (recommended default).** The BackingStore write
completes and is acknowledged before the Cache write is attempted. A Cache
failure after a successful store write is a fail-open in favour of a stale
cache, correctable by eviction, TTL expiry, or a subsequent read-through.
This is the ordering shown in dimension 7 and the ordering Oracle Coherence's
`CacheStore` contract assumes, where the store write happens as part of the
`put()` call before the operation is considered complete
([Oracle Coherence documentation, "Read-Through, Write-Through, Refresh-Ahead
and Write-Behind Caching"](https://docs.oracle.com/cd/E14039_01/coh.320/coh32ug/read_through.htm),
verified 2026-08-02).

**Cache first, then store.** The opposite ordering, attempted sometimes to
minimise the latency the client observes, since the cache write usually
completes faster and some implementations return to the client once the
faster of the two operations succeeds while the store write continues in the
background. This variant quietly becomes write-behind, and inherits its
durability window, the moment the client is allowed to proceed before the
store write is confirmed. If the client genuinely waits for both, the latency
saving is illusory, because the client is still blocked on the slower
operation regardless of which one started first. This variant is included
here only to name it and warn against it, see dimension 11.

**Library-managed write-through, application supplies a loader and a
writer.** The caching library itself sits at the CacheStore seat and exposes
two extension points, a loader for read-through misses and a writer for
write-through writes, and the application never calls the store directly.
Ehcache's `CacheWriter` interface is this shape. A cache `put()` triggers the
configured `CacheWriter.write()` call automatically, before cache listeners
are notified, and if the writer throws, the exception propagates back through
the `put()` call ([Ehcache 2.8 documentation, "Write-through and Write-behind
Caching"](https://www.ehcache.org/documentation/2.8/apis/write-through-caching.html),
verified 2026-08-02). This variant is the one to prefer in application code
whenever the caching library offers it, because the ordering and the
failure-propagation guarantee are the library's tested responsibility rather
than a hand-rolled seam the application team must get right and keep right
across every call site.

**Application-managed write-through, no library support.** The application
writes its own thin wrapper, as shown in dimension 6, calling the store and
the cache client directly with plain SDK calls. This is common when the cache
technology, for example Redis via a general-purpose client library, has no
opinion about write-through at all, it is purely a key-value store, and the
"through" behaviour is entirely application logic. The risk this variant
carries is that the wrapper is easy to bypass by accident, a different
code path that writes to the store directly and forgets the cache reproduces
the stale-cache problem the pattern exists to solve. Enforcing a single write
seam, for example by never exposing a raw database client to feature code, is
the practical mitigation.

**Managed write-through service.** The cache and the write-through behaviour
are provided together as one managed offering, and the application's write
call already goes to a single endpoint that internally fans out to the
durable store and the cache. Amazon DynamoDB Accelerator is this shape for
DynamoDB, the application calls the DAX client's `putItem`, and DAX itself
writes to DynamoDB and to its own item cache before returning success
([Amazon DynamoDB Accelerator (DAX) overview, description of DAX as a
read-through and write-through cache for DynamoDB](https://aws.amazon.com/blogs/database/amazon-dynamodb-accelerator-dax-a-read-throughwrite-through-cache-for-dynamodb),
verified 2026-08-02). This variant removes the application's own
implementation risk entirely, in exchange for coupling the application to
that specific managed product's consistency and failure semantics.

**Write-through combined with a short TTL as a safety net.** Even with a
write-through cache faithfully implemented, entries still carry a
time-to-live so that a bug, a bypassed write path, or a manual store edit
outside the application self-heals within a bounded window rather than
staying wrong forever. This does not change the pattern's core mechanism, it
is a defensive addition that most production write-through deployments carry
in practice.

## 9. Known production uses

**Amazon DynamoDB Accelerator (DAX).** DAX is described in AWS's own
documentation as a write-through caching service for DynamoDB, where a write
operation updates the underlying DynamoDB table and the DAX item cache before
the operation is considered successful, so a subsequent read of the same key
through the same DAX cluster reflects the write immediately. Amazon Web
Services, "DAX and DynamoDB consistency models",
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.consistency.html
verified 2026-08-02.

**Ehcache `CacheWriter` in write-through mode.** Ehcache, the Java caching
library used widely in Spring and Hibernate second-level cache
configurations, exposes a `write-mode` cache configuration attribute with
`write-through` as its documented default, where a `CacheWriter`
implementation is invoked synchronously on every `put` and `remove`, and a
failure in the writer is thrown back to the caller of `put`. Ehcache Project,
"Write-through and Write-behind Caching", version 2.8 documentation,
https://www.ehcache.org/documentation/2.8/apis/write-through-caching.html
verified 2026-08-02.

**Oracle Coherence `CacheStore` with `write-delay-seconds` set to zero.**
Oracle Coherence, a distributed in-memory data grid used in enterprise Java
deployments, implements write-through by configuring a `CacheStore` binding
where a store update is performed synchronously as part of every `put()`
call, distinguished from write-behind mode by setting the write-delay
configuration to zero rather than to a positive number of seconds. Oracle
Corporation, "Read-Through, Write-Through, Refresh-Ahead and Write-Behind
Caching", Coherence 3.2 User Guide,
https://docs.oracle.com/cd/E14039_01/coh.320/coh32ug/read_through.htm
verified 2026-08-02.

**CPU cache write-through policy, the originating usage.** Outside the
application layer, write-through is a standard write policy studied in
computer architecture for keeping an L1 or L2 CPU cache consistent with main
memory, where every store instruction updates both the cache line and main
memory rather than marking the line dirty for a later write-back. Hennessy
and Patterson present this as one of the two canonical cache write policies
in their standard architecture reference. John L. Hennessy and David A.
Patterson, *Computer Architecture. A Quantitative Approach*, 6th edition,
Morgan Kaufmann, 2017, Appendix B, "Review of Memory Hierarchy". This is
included as the pattern's conceptual origin rather than as a fourth
independent application-layer production system, since dimensions 5 through 7
of this entry describe the network-attached, application-level form.

## 10. Consequences

Positive.

- A read that follows a write to the same key, through the same cache
  instance or cluster, never observes stale data and never pays a forced
  cache-miss penalty, because the cache was updated as part of the write, not
  invalidated by it.
- The cache is always populated by the exact value the application intended
  to write, with no separate read-back from the store needed to warm the
  cache after a write.
- The failure semantics are relatively easy to reason about compared to
  write-behind, because a write either fully succeeds across both stores or
  it fails, there is no asynchronous window during which the two stores
  disagree under normal operation.
- The pattern composes cleanly with a read path that trusts the cache fully,
  since nothing in the system relies on lazily repairing cache staleness on
  read, which simplifies the read path considerably.

Negative.

- Every write pays the latency of the slower of the two stores, plus
  coordination overhead, which can double or worse the write path's latency
  budget compared to writing to the store alone.
- The write path now depends on the cache's availability, turning a
  performance optimisation into a potential single point of failure for
  writes, unless the failure-handling strategy in dimension 11 is deliberately
  chosen and tested.
- Cache memory is spent on every write, including writes to keys nobody will
  ever read again, which both wastes memory and evicts genuinely hot entries
  under memory pressure, the churn effect AWS documents explicitly.
- The pattern does nothing for the first read of a key that has never been
  written through this code path, for example on cache node replacement or
  after a cache flush, a read-through or lazy-load fallback is still needed
  for that cold-start case, see dimension 13.

## 11. Failure modes and misuse

**Cache write fails after the store write already succeeded.** Symptom. The
client receives a success response, and later reads of the same key from a
different cache node, or after the local cache entry is evicted, return an
older value or nothing, even though the store has the latest write. Cause.
The CacheStore treated the cache write as best-effort, or the failure was
silently swallowed rather than surfaced or retried. Fix. Decide explicitly
whether a cache write failure fails the whole client operation or is logged
and tolerated as a stale-cache condition that a short TTL or an async repair
job will correct. Never let the failure disappear silently, because a silent
failure here means nobody notices the cache and the store have diverged until
a customer reports wrong data.

**Store write fails but the cache write already happened.** Symptom. The
client receives an error, correctly, but a subsequent read from the same
cache instance returns the value the client just tried and failed to write,
because the cache was updated first and never rolled back. Cause. The
implementation used the cache-first ordering variant from dimension 8, or
attempted the two writes in parallel rather than sequentially. Fix. Order the
writes store-first, as shown in the canonical dynamics, so that a store
failure never leaves a phantom value in the cache. If parallel writes are
required for latency reasons, the CacheStore must explicitly invalidate or
roll back the cache entry when the store write fails.

**Read-modify-write races bypass the cache entirely.** Symptom. Two
concurrent writers to the same key, each going through the write-through
path correctly, produce a cache and a store that agree with each other but
disagree with what either writer expected, a classic lost update. Cause.
Write-through solves cache-versus-store consistency, it does nothing about
concurrent-writer consistency, which is an orthogonal problem the store's own
concurrency control, an optimistic lock, a compare-and-swap, or a database
transaction, must solve independently. Fix. Apply the store's native
concurrency control on the write, and only update the cache with the value
the store actually persisted, not the value the client attempted to write,
particularly when the store might reject, transform, or auto-generate part of
the value.

**Cold cache node serves nothing for a key the store has always had.** Symptom.
A newly added cache node, or a cache flushed for maintenance, returns misses
for keys that were written through this pattern long ago, and if there is no
fallback, the application either errors or, worse, silently treats the miss
as "the record does not exist". Cause. Write-through only guarantees
freshness for writes that happen after the cache node exists, it says nothing
about backfilling a cache that starts empty. Fix. Pair write-through with a
read-through or lazy-load fallback on miss, so a cold node self-heals from
the store on the next read rather than staying empty until the next write to
each key.

**Batched writer loses the per-write acknowledgement boundary.** Symptom. A
batching optimisation groups several client writes into one store call for
throughput, and a client is told its write succeeded before that specific
write's place in the batch is confirmed durable, so a batch failure after
partial acknowledgement causes data loss the client believes did not happen.
Cause. Batching was added for efficiency without preserving write-through's
core guarantee, that a success response means the write is durably in both
places. Fix. Only acknowledge a client once its specific write is confirmed
part of a successfully committed batch, or do not acknowledge on submission
to the batch at all.

**Applying write-through to a high-cardinality, rarely-read write stream.**
Symptom. Cache hit ratio for genuinely hot keys degrades over time, and cache
memory usage grows without a matching improvement in read latency. Cause.
Every write, including writes that are never read again, is populating the
cache, evicting entries that matter under an LRU or similar policy. Fix.
This is not a bug to patch, it is the wrong pattern for the workload, see
dimension 4's non-applicability list, switch to cache-aside for this data.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Write-Through | Cache-Aside | Write-Behind (Write-Back) | Read-Through (read side only) |
|---|---|---|---|---|
| Freshness of the very next read after a write | Guaranteed, no window | Stale until next read triggers reload, or invalidated so next read misses | Guaranteed if the read goes through the same cache, since the cache holds the latest value | Not addressed, this is a read-side pattern only |
| Write latency | Highest, pays both stores synchronously | Lowest, writes only the store | Lowest client-observed latency, cache write only, store write deferred | Not addressed |
| Durability window on write | None under normal operation | None, store is written directly | Exists, a window during which the write lives only in the cache | Not addressed |
| Write-path availability dependency | Depends on both cache and store being up | Depends only on the store | Depends only on the cache being up at write time | Not addressed |
| Cache churn from rarely-read writes | High, every write populates the cache | None, cache only fills on read | High, same as write-through on the cache side | Not addressed |
| Implementation complexity | Moderate, one seam, clear ordering rule | Low, no coordination needed on write | High, needs a durable queue and retry logic for the deferred flush | Low to moderate, one seam on the read side |
| Cold-cache behaviour | Needs a read-side fallback, does nothing for pre-existing gaps | Naturally self-heals on first read | Needs a read-side fallback, same limitation as write-through | This is exactly what it solves |
| Best-suited write to read ratio | Low write, high read | Any ratio, especially unpredictable read patterns | High write, latency-sensitive write path | Not a write-side concern |

Reading of the table. Write-through and write-behind share the property that
the cache is always current for reads immediately after a write, and they
differ entirely in when the store is actually updated and what that costs the
write path. Cache-aside gives up the immediate-freshness guarantee in
exchange for the simplest and cheapest write path. Read-through solves a
different half of the problem, how a cache miss is filled, and is usually
paired with one of the three write-side patterns rather than compared against
them directly.

## 13. Related and incompatible patterns

- **Cache-Aside.** The most common alternative and the default choice when
  write-through's non-applicability conditions from dimension 4 apply. Where
  write-through updates the cache as part of every write, Cache-Aside leaves
  the cache alone on write, at most invalidating the key, and repopulates it
  lazily on the next read miss. The two are mutually exclusive per data type,
  a given key's write path is either through the cache or around it, though a
  single system can legitimately use write-through for some data and
  cache-aside for other data.
- **Write-Behind (Write-Back) Cache.** The nearest relative and the one most
  often confused with write-through, since both keep the cache current on
  write. Write-behind accepts the write into the cache and defers the store
  write to a background process, trading the durability guarantee for lower
  write latency. Because the two solve the same read-freshness problem with
  opposite trade-offs on write latency versus durability, a single write
  path should implement exactly one of them, mixing the two, for example
  acknowledging the client before the store write completes while still
  calling it write-through, is the ordering bug named in dimension 11.
- **Read-Through Cache.** Complementary rather than competing. Read-through
  addresses what happens on a cache miss during a read, fetching from the
  store and populating the cache transparently to the caller. Write-through
  addresses the opposite direction, what happens on a write. The two are
  frequently implemented together in the same CacheStore seat, and Oracle
  Coherence and Ehcache both document them as a paired configuration rather
  than two unrelated features.
- **Refresh-Ahead Cache.** A read-side optimisation that proactively
  refreshes a cache entry before its TTL expires, when it is accessed close
  to expiry. It composes with write-through without conflict, refresh-ahead
  concerns entries that are aging out, write-through concerns entries that
  were just written, and they do not touch the same code path.
- **Circuit Breaker.** A practical companion once write-through's
  availability trade-off in dimension 3 is taken seriously. Wrapping the
  cache write inside a circuit breaker lets the write path degrade to
  store-only writes, with the cache treated as best-effort, when the cache is
  unhealthy, rather than letting a cache outage take down all writes. This
  is an operational mitigation, not a structural part of the pattern itself.
- **Two-Phase Commit and distributed transactions.** A theoretically stronger
  but rarely used relative. A team that needs the cache and the store to be
  transactionally atomic, not merely sequentially updated, could reach for a
  two-phase commit across both systems. In practice this is almost never done
  for application caches, because the cache is explicitly meant to be
  disposable and rebuildable, and paying two-phase commit's latency and
  coordinator complexity defeats the purpose of having a fast cache at all.
  It is worth naming here only so a team considering it understands they are
  trading away the entire point of the pattern.

## 14. Refactoring path in and out

Introducing write-through into a system that currently uses cache-aside or has
no cache at all.

1. Identify the write call sites for the data in question, and confirm they
   are already funneled through one function or one class, not scattered
   directly against the database client across the codebase. If they are
   scattered, consolidate them first, this refactor is a prerequisite, not an
   optional cleanup, because write-through only works if there is exactly one
   place the write actually happens.
2. Introduce the CacheStore seat as a thin wrapper around the existing store
   write, initially a pass-through that changes nothing observable. Run the
   existing tests to confirm behaviour is unchanged.
3. Add the cache write inside the wrapper, ordered after the store write
   succeeds, per the safer ordering in dimension 8. Do not yet remove any
   existing cache-aside invalidation logic elsewhere in the codebase.
4. Decide and implement the failure-handling policy from dimension 11 for a
   cache write failure, whether it fails the whole operation or is logged and
   tolerated. Write a test that forces a cache failure and asserts the chosen
   behaviour, not merely that the code compiles.
5. Confirm the read path already trusts the cache, meaning a cache hit is
   served without a store round trip. If the read path was previously
   validating cache freshness against the store on every read, that check can
   now be safely removed, since write-through provides the freshness
   guarantee structurally.
6. Remove the now-redundant cache-aside invalidation calls from any other
   write path for this data, once every write path has been migrated through
   the same CacheStore seat. A stray invalidate-only call left behind is
   harmless but is dead code that misleads the next reader into thinking
   staleness is still possible.
7. Add a TTL as the defensive safety net described in dimension 8, sized to
   the acceptable staleness window if the write-through guarantee is ever
   silently broken by a future code change.

Removing the pattern when it stops earning its place. The signal to watch for
is the cache-churn symptom from dimension 11, or a write latency regression
that traces back to the synchronous cache write.

1. Confirm which specific data type is causing the problem, since a system
   often has several data types sharing one cache, and only one may need to
   change strategy.
2. Change the CacheStore wrapper's cache write to fire-and-forget, or remove
   it entirely, so the write path returns to the caller as soon as the store
   write succeeds.
3. Add invalidation of the cache entry at the same point the cache write used
   to happen, so reads fall through to the store, do not leave a now-stale
   entry sitting in the cache with no path to correction.
4. Confirm the read path has a cache-aside fallback, fetch from the store on
   miss and populate the cache, since removing write-through removes the
   guarantee that the cache is ever populated by a write alone.
5. Watch cache hit ratio and write latency after the change to confirm the
   trade actually improved the metric that motivated it.

## 15. Testing and verification

Easier because of the pattern.

- The freshness guarantee is directly testable. Write a value through the
  CacheStore, immediately read the same key from the cache alone, bypassing
  the store entirely in the test's read call, and assert the value matches
  what was written. This single test, run against a real or in-memory cache
  implementation, is the core correctness assertion for this pattern and
  catches the most common regression, someone adding a new write path that
  bypasses the CacheStore seat.
- Because the write seam is centralised, a test double for BackingStore can
  be substituted at the CacheStore boundary to assert exactly what was sent
  to the store, without needing a real database in unit tests.

Harder because of the pattern.

- The partial-failure behaviour from dimension 11 needs deliberate,
  explicit tests, a happy-path test alone will not exercise the ordering
  decision or the failure-propagation decision, and these are exactly the
  code paths most likely to be wrong on first implementation.
- Testing the cache-node-replacement or cold-cache scenario requires
  simulating an empty cache with a store that already has data, which is
  easy to forget to test because the happy path, cache already warm from
  prior writes, works during normal development and only breaks during an
  operational event such as a cache cluster resize.

Techniques that apply.

- **Fault injection on the cache client.** Use a fake or a proxy in front of
  the real cache client that can be told to fail the next call, and assert
  the CacheStore's chosen behaviour, either the whole write fails or the
  operation is logged and the store write still succeeded. This directly
  proves the ordering and failure policy from dimension 11 rather than
  assuming it from reading the code.
- **Fault injection on the store client, symmetric to the above.** Assert
  that a store failure never results in the cache holding the attempted
  value, proving the store-first ordering is actually implemented and not
  merely intended.
- **Write-then-read-elsewhere test.** In a distributed cache, write through
  one client connection or one node, then read from a different node or
  connection, to catch the case where the cache write only reached one
  replica and the freshness guarantee silently only holds for the writer's
  own connection.
- **Property test asserting idempotence of repeated writes.** Writing the
  same key and value twice through the CacheStore should leave both cache
  and store in the identical state as writing it once, a useful invariant to
  assert with a property-based test generating random keys and values, since
  it catches accidental side effects hidden in the writer, such as an
  unconditional counter increment on every write call.

## 16. Observability signals

What to record.

- A counter of write-through operations, labelled by outcome, both stores
  succeeded, store succeeded but cache failed, store failed. This single
  metric answers the question dimension 11 is built around, is the write
  path actually keeping the two stores in agreement in production.
- A histogram of write latency, split into the store-write component and the
  cache-write component separately, not only the total. A total-only
  histogram hides which of the two stores is the actual bottleneck when
  latency regresses.
- A counter of reads served from the cache versus reads that had to fall
  through to the store, so the team can see whether the cache is actually
  doing its job, a healthy write-through cache should show a high hit rate
  for any key that has ever been written.
- A gauge or counter tracking cache eviction rate, specifically watching for
  the churn symptom from dimension 3 and dimension 11, a rising eviction
  rate alongside a falling hit rate for known-hot keys is the signature of
  write-through being applied to write-heavy, rarely-read data.

A healthy instance on a dashboard. The both-succeeded outcome dominates the
write-outcome counter, close to all of it. Cache-write latency is a small,
stable fraction of total write latency, and store-write latency tracks the
store's own baseline. Cache hit rate for keys with recent writes is close to
one hundred percent, since a write-through cache with any other reading
would indicate the guarantee is not actually holding.

A failing instance. The store-failed or cache-failed outcome counters climb
above their normal near-zero baseline, which should page someone, since this
is exactly the condition dimension 11 warns causes silent divergence if it
goes unnoticed. Cache-write latency grows disproportionately to store-write
latency, suggesting the cache itself, not the store, has become the
bottleneck the pattern was meant to avoid introducing. Eviction rate climbing
alongside a falling hit rate for known-important keys points at the pattern
being misapplied to a write-heavy data type, a signal to revisit dimension 4.

## 17. Security and privacy implications

The pattern itself does not open a new network-facing attack surface, it
reuses whatever access paths the cache and the store already have, but it
does have two genuine implications worth stating plainly.

**Data duplication widens the retention and access-control surface.** Once a
write-through cache exists, every value that used to live only in the durable
store, subject to that store's access controls, encryption at rest, and
retention policy, now also lives in the cache, which frequently has weaker or
different controls, shorter or no encryption at rest, and a separate access
policy that the security review may not have covered when the cache was
originally introduced for performance reasons alone. Personal data or secrets
written through the pattern must be governed by the stricter of the two
systems' policies, not the store's alone, and a cache flush or eviction
policy should be treated as part of the data's retention story, not an
implementation detail.

**A cache write failure that is silently tolerated can mask a security-
relevant write.** If the failure-handling policy in dimension 11 chooses to
log and tolerate a cache write failure rather than fail the whole operation,
that same tolerance applies uniformly, including to a permission change, an
access revocation, or a credential rotation written through the same path.
An access-revoking write that succeeded in the store but silently failed to
update the cache leaves the cache serving a stale, more permissive value
until the TTL or a manual flush corrects it, which is a real window of
incorrect authorization data if the cache is ever consulted for an
access decision. Where the data written through this pattern is
security-sensitive, a cache write failure should fail the whole operation
rather than be tolerated, even though tolerating it is the cheaper default
for ordinary data.

The pattern is silent on encryption and transport security specifically,
those are properties of the chosen Cache and BackingStore technologies, not
of the write-through coordination logic itself, and no additional claim is
made here beyond the two points above.

## 18. References

1. John L. Hennessy and David A. Patterson. *Computer Architecture. A
   Quantitative Approach*, 6th edition. Morgan Kaufmann, 2017.
   ISBN 978-0-12-811905-1. Appendix B, "Review of Memory Hierarchy", the
   comparison of write-through and write-back cache write policies. Source
   for the pattern's originating usage in dimension 1 and dimension 9.
2. Amazon Web Services. "Caching strategies for Memcached", Amazon
   ElastiCache for Memcached User Guide.
   https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html
   Verified 2026-08-02. Source for the write-through definition and the
   cache-churn cost warning in dimensions 1 and 3.
3. Amazon Web Services. "DAX and DynamoDB consistency models", Amazon
   DynamoDB Developer Guide.
   https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.consistency.html
   Verified 2026-08-02. Source for the DAX write-through consistency model
   in dimensions 3, 4, and 7.
4. Amazon Web Services. "DAX. How it works", Amazon DynamoDB Developer
   Guide.
   https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.concepts.html
   Verified 2026-08-02. Source for the DAX write-through behaviour
   description in dimension 4 and dimension 8.
5. Amazon Web Services. "Amazon DynamoDB Accelerator (DAX). A
   Read-Through/Write-Through Cache for DynamoDB", AWS Database Blog.
   https://aws.amazon.com/blogs/database/amazon-dynamodb-accelerator-dax-a-read-throughwrite-through-cache-for-dynamodb
   Verified 2026-08-02. Source for the DAX production use in dimension 8 and
   dimension 9.
6. Ehcache Project. "Write-through and Write-behind Caching", Ehcache 2.8
   Documentation.
   https://www.ehcache.org/documentation/2.8/apis/write-through-caching.html
   Verified 2026-08-02. Source for the `CacheWriter` write-through default
   mode and its synchronous failure propagation, in dimensions 8 and 9.
7. Oracle Corporation. "Read-Through, Write-Through, Refresh-Ahead and
   Write-Behind Caching", Coherence 3.2 User Guide.
   https://docs.oracle.com/cd/E14039_01/coh.320/coh32ug/read_through.htm
   Verified 2026-08-02. Source for the `CacheStore` write-through
   configuration and the `write-delay-seconds` distinction, in dimensions 8
   and 9.

## Code examples

Three languages, chosen because the pattern is a coordination shape rather
than a language feature, so the same logic reads clearly in a
strongly-typed, class-based language, a duck-typed scripting language, and a
statically compiled systems language with no inheritance. TypeScript, Python,
and Go. Java, Rust, and Swift are omitted for this entry, not because the
pattern does not translate, it translates trivially, a plain method on a
class in any of those languages, but because the interesting content of the
pattern is the ordering and failure-handling policy shown fully in the three
languages below, and repeating the identical shape three more times would add
length without adding depth. Each example implements the same in-memory
store-first ordering with an explicit failure policy, runnable with no
external dependencies.

### TypeScript

```typescript
interface Store {
  save(key: string, value: string): Promise<void>;
}

interface Cache {
  set(key: string, value: string): Promise<void>;
  get(key: string): Promise<string | undefined>;
}

class WriteThroughCacheStore {
  constructor(
    private readonly store: Store,
    private readonly cache: Cache,
    private readonly failCacheErrors: boolean
  ) {}

  async write(key: string, value: string): Promise<void> {
    await this.store.save(key, value);
    try {
      await this.cache.set(key, value);
    } catch (err) {
      if (this.failCacheErrors) {
        throw err;
      }
      console.error(`cache write failed for ${key}, store already durable`, err);
    }
  }

  async read(key: string): Promise<string | undefined> {
    return this.cache.get(key);
  }
}

class InMemoryStore implements Store {
  private readonly data = new Map<string, string>();
  async save(key: string, value: string): Promise<void> {
    this.data.set(key, value);
  }
}

class InMemoryCache implements Cache {
  private readonly data = new Map<string, string>();
  async set(key: string, value: string): Promise<void> {
    this.data.set(key, value);
  }
  async get(key: string): Promise<string | undefined> {
    return this.data.get(key);
  }
}

async function main() {
  const cacheStore = new WriteThroughCacheStore(
    new InMemoryStore(),
    new InMemoryCache(),
    true
  );
  await cacheStore.write("user-1", "Ada Lovelace");
  console.log(await cacheStore.read("user-1"));
}

main();
```

### Python

```python
from abc import ABC, abstractmethod


class Store(ABC):
    @abstractmethod
    def save(self, key: str, value: str) -> None: ...


class Cache(ABC):
    @abstractmethod
    def set(self, key: str, value: str) -> None: ...

    @abstractmethod
    def get(self, key: str) -> str | None: ...


class WriteThroughCacheStore:
    def __init__(self, store: Store, cache: Cache, fail_on_cache_error: bool = True):
        self._store = store
        self._cache = cache
        self._fail_on_cache_error = fail_on_cache_error

    def write(self, key: str, value: str) -> None:
        self._store.save(key, value)
        try:
            self._cache.set(key, value)
        except Exception as err:
            if self._fail_on_cache_error:
                raise
            print(f"cache write failed for {key}, store already durable, {err}")

    def read(self, key: str) -> str | None:
        return self._cache.get(key)


class InMemoryStore(Store):
    def __init__(self):
        self._data: dict[str, str] = {}

    def save(self, key: str, value: str) -> None:
        self._data[key] = value


class InMemoryCache(Cache):
    def __init__(self):
        self._data: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def get(self, key: str) -> str | None:
        return self._data.get(key)


if __name__ == "__main__":
    cache_store = WriteThroughCacheStore(InMemoryStore(), InMemoryCache())
    cache_store.write("user-1", "Ada Lovelace")
    print(cache_store.read("user-1"))
```

### Go

```go
package main

import (
	"errors"
	"fmt"
	"log"
	"sync"
)

type Store interface {
	Save(key, value string) error
}

type Cache interface {
	Set(key, value string) error
	Get(key string) (string, bool)
}

type WriteThroughCacheStore struct {
	store           Store
	cache           Cache
	failCacheErrors bool
}

func NewWriteThroughCacheStore(store Store, cache Cache, failCacheErrors bool) *WriteThroughCacheStore {
	return &WriteThroughCacheStore{store: store, cache: cache, failCacheErrors: failCacheErrors}
}

func (w *WriteThroughCacheStore) Write(key, value string) error {
	if err := w.store.Save(key, value); err != nil {
		return fmt.Errorf("store write failed, cache left untouched, %w", err)
	}
	if err := w.cache.Set(key, value); err != nil {
		if w.failCacheErrors {
			return fmt.Errorf("cache write failed, store already durable, %w", err)
		}
		log.Printf("cache write failed for %s, store already durable, %v", key, err)
	}
	return nil
}

func (w *WriteThroughCacheStore) Read(key string) (string, bool) {
	return w.cache.Get(key)
}

type InMemoryStore struct {
	mu   sync.Mutex
	data map[string]string
}

func NewInMemoryStore() *InMemoryStore {
	return &InMemoryStore{data: make(map[string]string)}
}

func (s *InMemoryStore) Save(key, value string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if key == "" {
		return errors.New("empty key rejected by store")
	}
	s.data[key] = value
	return nil
}

type InMemoryCache struct {
	mu   sync.Mutex
	data map[string]string
}

func NewInMemoryCache() *InMemoryCache {
	return &InMemoryCache{data: make(map[string]string)}
}

func (c *InMemoryCache) Set(key, value string) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[key] = value
	return nil
}

func (c *InMemoryCache) Get(key string) (string, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	v, ok := c.data[key]
	return v, ok
}

func main() {
	cacheStore := NewWriteThroughCacheStore(NewInMemoryStore(), NewInMemoryCache(), true)
	if err := cacheStore.Write("user-1", "Ada Lovelace"); err != nil {
		log.Fatal(err)
	}
	value, ok := cacheStore.Read("user-1")
	fmt.Println(value, ok)
}
```
