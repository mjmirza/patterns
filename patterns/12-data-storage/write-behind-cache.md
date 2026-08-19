---
name: Write-Behind Cache
slug: write-behind-cache
family: 12-data-storage
category: Data and Storage
aliases: [Write-Back Cache, Deferred Write Cache, Asynchronous Write Cache]
first_described: "Practitioner and systems-literature term, in wide industrial use since at least the CPU cache write-back policies of the 1970s and formalized for application caches by commercial cache-store products in the late 1990s and 2000s"
maturity: canonical
related: [cache-aside, write-ahead-log, change-data-capture, log-compaction, buffer-pool]
incompatible_with: [strong-consistency-via-consensus]
verified: 2026-08-02
---

# Write-Behind Cache

## 1. Name, aliases, and lineage

The canonical name in application caching literature is Write-Behind Cache. The
same idea is called Write-Back Cache in computer architecture and operating
systems, where it describes a hardware or kernel cache line that is written
only in memory or in the CPU cache and marked dirty, with the write to the
backing store deferred until the line is evicted or a background process
flushes it. Deferred Write Cache and Asynchronous Write Cache appear as plain
descriptive names in vendor documentation and in engineering blog posts, and
they mean the same mechanism.

There is no single paper that introduces write-behind the way Gamma, Helm,
Johnson and Vlissides introduce Factory Method. The idea is older than the
software patterns movement. CPU cache write-back policy, as distinct from
write-through, is standard material in computer architecture courses and
textbooks by the 1980s, for example John L. Hennessy and David A. Patterson,
*Computer Organization and Design*, 5th edition, Morgan Kaufmann, 2013, chapter
5, Large and Fast, Exploiting Memory Hierarchy, where write-back and
write-through are presented as the two policies for handling a store to a
cache line. The application-cache variant, where an object cache defers
writing a modified entry to a database, entered mainstream distributed systems
practice through commercial cache products. Oracle Coherence documents it
explicitly as Write-Behind caching, one of four data-source caching strategies
alongside read-through, write-through and refresh-ahead, in its cache store
architecture (["Read-Through, Write-Through, Write-Behind, and Refresh-Ahead
Caching"](https://docs.oracle.com/cd/E16459_01/coh.350/e14510/readthrough.htm),
Oracle Coherence 3.5 User Guide, verified 2026-08-02). Hazelcast documents the
same mechanism under the same name for its distributed map, configured through
a `MapStore` (["MapStore Overview"](https://docs.hazelcast.com/hazelcast/5.5/mapstore/working-with-external-data),
Hazelcast 5.5 documentation, verified 2026-08-02). The convergence of two
independent vendor cache products on the identical name, write-behind, for the
identical mechanism, is the reason this entry treats the term as canonical
rather than as one vendor's private vocabulary.

A related but distinct idea is write-around, which writes directly to the
backing store and skips the cache entirely on write, populating the cache only
on subsequent read. Write-around is sometimes confused with write-behind
because both avoid a synchronous write to the store on the write path, but
write-around never makes the cache the temporary system of record for an
unwritten value, and write-behind always does. This entry is about
write-behind only. Write-through, where the cache and the store are updated
synchronously in the same request, is covered in the write-through variant
discussion in dimension 8 and treated as the baseline write-behind is
compared against throughout this entry.

## 2. Problem and context

A service holds hot, frequently mutated state in a fast in-memory or
in-cluster cache, and every mutation must eventually reach a durable backing
store, typically a relational database, a document store, or a distributed
key-value store. If every write to the cache is also a synchronous write to
the backing store, the write latency the caller experiences is bounded below
by the store's write latency, and the store's write throughput becomes the
throughput ceiling for the whole system, even though the cache itself could
absorb writes far faster.

This shows up concretely in three shapes. First, a counter or gauge that
receives many updates per second for the same key, a page view counter, a
leaderboard score, a rate-limit bucket, where writing every single increment
to the database is wasteful because only the latest value at read time
matters. Second, a session store or a shopping cart, where the same key is
updated repeatedly within a short user interaction and the intermediate
values are never read by anyone. Third, a write-heavy ingestion path, log
lines, metrics, telemetry events, where the producer needs to be
acknowledged quickly and the actual persistence can lag behind by a bounded
window without violating the system's actual durability contract, because the
contract is expressed in seconds of acceptable loss rather than in zero loss.

The context that makes write-behind the right answer, rather than a
dangerous shortcut, has three parts. The application can tolerate a bounded
window of data loss on an ungraceful failure, because the business already
accepts eventual consistency or has an independent recovery path, such as a
source system that can be replayed. The write pattern has meaningful temporal
locality, the same key is written multiple times close together, so
coalescing writes into one flush actually reduces the number of store
operations rather than merely delaying them one for one. And the backing
store's write cost, whether latency, IOPS, or a metered API cost per write, is
high enough relative to the cache's write cost that batching and delaying
pays for itself. Absent all three, write-behind adds operational risk for
little benefit, and cache-aside or write-through is the better default.

## 3. Forces

**Write latency versus durability window.** Write-behind buys a caller-facing
write latency close to the cache's own latency, typically sub-millisecond for
an in-process or same-rack cache, at the cost of a durability window during
which a value exists only in the cache and a crash of the cache node loses it.
The pattern is a direct trade of latency for a bounded, and non-zero,
probability of loss.

**Throughput versus store load.** Coalescing and batching reduce the number of
operations the backing store sees, sometimes by orders of magnitude for
hot keys, which is often the entire point of adopting the pattern rather than
scaling the store. The force in tension is that batching adds queueing delay
and code complexity in the flush path, and a batch failure now affects many
logical writes instead of one.

**Consistency versus availability of the read path.** A read against the
cache after a write always returns the latest value, because the cache is
updated synchronously on write and the store update is deferred. A read that
bypasses the cache and goes straight to the store, whether accidentally
through a second read path or deliberately through an analytics job, sees a
stale value until the next flush. This is the same read skew that
cache-aside avoids by never allowing the cache to be ahead of the store, and
write-behind deliberately reintroduces it in exchange for the write-side
gains above.

**Operability versus simplicity.** A synchronous write-through path has one
failure mode to reason about at write time, the write either lands in the
store or the caller sees an error. Write-behind moves failure handling to a
background flusher that must retry, must not silently drop entries, must
expose backpressure when the store is slow, and must be observable, because
a failing flusher produces no caller-visible symptom until the cache node is
lost or memory pressure forces an eviction of dirty data. The pattern favors
throughput and latency, and it openly sacrifices simplicity and the tightness
of the durability guarantee.

**Cost.** For a cache backed by a metered store, DynamoDB write capacity
units, a hosted Postgres instance billed on IOPS, or a third-party API billed
per call, coalescing writes converts a cost that scales with the number of
mutations into a cost that scales with the number of distinct dirty keys per
flush window, which is frequently a large multiplier of savings for hot-key
workloads and close to zero savings for uniformly random key access.

## 4. Applicability and non-applicability

When to reach for it.

- The write path is hot, high frequency updates to a small number of keys,
  such as counters, gauges, presence, session state, or rate-limit buckets,
  and only the current value matters at read time.
- The business already tolerates a bounded window of loss on catastrophic
  failure, either because the data is derived and can be recomputed, because
  the source event stream can be replayed, or because a short window of stale
  or lost data is an accepted operational cost, not a compliance violation.
- The backing store's write cost, whether latency or metered price, is high
  enough that batching pays for itself, and the workload has real temporal
  locality on the same keys so coalescing actually reduces operation count.
- Caller-facing write latency is on the system's critical path and must be
  close to the cache's own latency rather than the store's.

When not to reach for it.

- The write concerns money movement, an inventory decrement that must never
  be double-applied or lost, an audit log, or any record a regulator or an
  external counterparty will later ask to see with a guarantee it was
  durable the instant the caller was told it succeeded. A payment ledger
  entry must be write-through or written directly with a durable
  acknowledgment, never write-behind, because "the write happened, trust me,
  it will land eventually" is not an acceptable answer to an auditor. Martin
  Kleppmann's discussion of write-back caching in the context of durability
  guarantees makes the same point about any store that acknowledges before
  fsync, that the write is not durable until it is actually on stable
  storage (Martin Kleppmann, *Designing Data-Intensive Applications*,
  O'Reilly, 2017, chapter 3, "Storage and Retrieval").
- The read path frequently bypasses the cache, for example a reporting job
  that queries the database directly, or a second service that reads the
  same table without going through the cache tier. Write-behind guarantees
  the cache is authoritative, not the store, and any reader that does not
  respect that guarantee sees stale or missing data.
- The workload has low temporal locality, effectively unique keys on every
  write, such as an append-only event stream where each event is written
  once and read once. Coalescing has nothing to coalesce, and the pattern
  becomes pure added latency and pure added risk with none of its throughput
  benefit.
- The team cannot commit to building and operating the flush pipeline
  correctly, including retry with backoff, dead-letter handling for
  poison entries, backpressure when the store is degraded, and monitoring for
  a growing dirty set. An unmonitored write-behind cache degrades silently.
- Multiple writers can update the same key from different cache nodes
  without a single owner for that key's flush. Without a defined leader per
  key or per partition, two nodes can each hold a different "latest" value
  for the same key with no way to reconcile which one is actually latest,
  producing lost updates that are worse than the ones write-behind is
  usually trying to avoid on the store side.

## 5. Structure

- **Client.** The caller that performs `put(key, value)` and `get(key)`. It
  observes the cache's latency, never the store's, on the write path.
- **Cache (fast tier).** Holds the current value for every known key and a
  marker, explicit or implicit, for which keys are dirty, meaning cache-only
  and not yet reflected in the store. Serves every read from this tier so
  the client always observes its own writes.
- **Dirty set (write queue).** The record of keys that must still be flushed,
  together with the value, or a reference to it, to write. This can be a
  separate in-memory structure, a flag on each cache entry, or an external
  durable queue, and the choice materially changes the pattern's durability
  properties, discussed in dimension 8.
- **Flusher.** A background process, thread, or scheduled task that drains
  the dirty set on a delay, a size threshold, or both, and issues the actual
  writes to the backing store. It owns retry, batching, and coalescing
  policy.
- **Backing store.** The durable system of record the flusher eventually
  writes to. It is not authoritative for the current value of a dirty key
  until the flush that carries that key completes.
- **Coalescing policy.** The rule that decides, when a key is written
  multiple times before its scheduled flush, whether all intermediate values
  are sent to the store or only the last one. Hazelcast exposes this
  explicitly as the `write-coalescing` configuration flag, true by default,
  meaning only the latest value per key is written within a delay window
  (["Write-Behind Configuration Parameters"](https://docs.hazelcast.com/hazelcast/5.5/mapstore/configuration-guide),
  Hazelcast 5.5 documentation, verified 2026-08-02).

## 6. ASCII structure diagram

```
                       reads and writes
    +--------+  ------------------------->  +----------------+
    | Client |                              |  Cache (fast)  |
    +--------+  <-------------------------  |  key -> value  |
                    value returned          |  dirty set     |
                    immediately after       +----------------+
                    write, no store round          |
                    trip on the write path         | periodic drain
                                                    | (delay elapsed
                                                    |  or batch full)
                                                    v
                                          +--------------------+
                                          |     Flusher        |
                                          |  batch + coalesce  |
                                          |  retry on failure  |
                                          +--------------------+
                                                    |
                                                    | write batch
                                                    v
                                          +--------------------+
                                          |  Backing store     |
                                          |  (system of record |
                                          |   once flushed)    |
                                          +--------------------+
```

## 7. Dynamics

The two independent flows are the write path, which is synchronous and
cache-only, and the flush path, which is asynchronous and store-bound. They
share the dirty set as their only coordination point.

```
Write path, single key, three writes close together
-----------------------------------------------------
t0   client.put(k, v1)   -> cache[k] = v1, dirty[k] = v1, client returns
t1   client.put(k, v2)   -> cache[k] = v2, dirty[k] = v2 (coalesced), returns
t2   client.put(k, v3)   -> cache[k] = v3, dirty[k] = v3 (coalesced), returns
t3   client.get(k)       -> returns v3 immediately, cache is authoritative

Flush path, same key, delay window elapses at t4
-----------------------------------------------------
t4   flusher wakes on timer or batch-size trigger
t5   flusher snapshots dirty set, then clears the key from dirty
t6   flusher writes batch to store, store.write(k, v3)
t7a  write succeeds  -> store now holds v3, key stays out of dirty set
t7b  write fails     -> flusher re-inserts k into dirty set for retry,
                         unless a newer write already replaced it, in which
                         case the newer pending value is left in place

Crash scenario, node dies between t3 and t6
-----------------------------------------------------
     v1 and v2 are permanently unobservable, by design, coalesced away
     v3 exists only in the crashed cache node's memory, never reached
     the store, and is now lost unless the cache itself is durably
     replicated, see dimension 8, durable dirty set variant
```

The crash scenario is the load-bearing line in this diagram. It is the exact
cost the trade-off in dimension 3 describes, made concrete, and it is why
dimension 4 insists the applicability decision be made before this pattern
is adopted, not discovered after an incident.

## 8. Implementation variants

- **In-memory dirty set, single-node cache.** The simplest form. The dirty
  set is a plain map or a dirty bit per entry, held in the same process as
  the cache. Cheapest to build, and the entire dirty set is lost on process
  crash. Appropriate only when the tolerable loss window is genuinely small
  and the workload can survive it, for example a metrics rollup that
  recomputes from raw events on recovery.

- **Durable dirty set via a local write-ahead log.** The cache writes each
  mutation to a local append-only log before acknowledging the caller, then
  the flusher reads from the log and writes to the store, truncating the log
  as entries are confirmed flushed. This converts the cache's own durability
  problem into the write-ahead log pattern's durability problem, and the
  caller-facing latency now includes one local disk append, still far
  cheaper than a network round trip to a remote store. This is the shape
  used inside a single database engine's buffer pool, where a modified page
  is written to the write-ahead log immediately and to the data file lazily,
  the write-back policy for the buffer pool itself. See the
  [Write-Ahead Log](write-ahead-log.md) entry in this catalog for the log
  side of this composition.

- **Delay plus batch-size dual trigger.** The flusher drains either when a
  configured delay elapses since the oldest dirty entry, or when the dirty
  set reaches a configured size, whichever comes first. This bounds both the
  worst-case staleness of any single key and the worst-case batch size sent
  to the store in one call. Hazelcast's `MapStore` exposes exactly these two
  knobs, `write-delay-seconds` and `write-batch-size`
  (["Write-Behind Configuration Parameters"](https://docs.hazelcast.com/hazelcast/5.5/mapstore/configuration-guide),
  Hazelcast 5.5 documentation, verified 2026-08-02).

- **Coalescing versus ordered replay.** With coalescing on, only the latest
  value per key survives to the flush, which is correct when the store only
  needs to reflect current state. With coalescing off, every intermediate
  write is preserved and replayed in order, which is required when the
  store's write path has side effects beyond storing a value, for example an
  audit trigger or a change-data-capture consumer downstream that expects to
  see every transition, not only the final one. Hazelcast's
  `write-coalescing` flag makes this an explicit configuration choice rather
  than an implicit behavior, same source as above.

- **Kernel and CPU write-back, for contrast.** Operating system page caches
  use the same mechanism at a different layer. A write to a memory-mapped
  file or a buffered file write dirties a page in the page cache and returns
  immediately, and a background kernel flusher thread writes dirty pages to
  disk once they age past `dirty_expire_centisecs` or once the fraction of
  dirty memory crosses `dirty_background_ratio`
  (["Documentation for /proc/sys/vm/"](https://docs.kernel.org/admin-guide/sysctl/vm.html),
  Linux kernel documentation, verified 2026-08-02). This is architecturally
  identical to an application-level write-behind cache, delay-based
  triggers, coalescing of repeated writes to the same page, and a real
  window of loss on power failure, which is exactly why databases that need
  stronger durability call `fsync` or open files with direct I/O to bypass
  it for their own write-ahead log.

- **Write-through, as the comparison baseline.** In write-through, the cache
  and the store are both updated synchronously as part of the same logical
  write, and the caller only receives success after the store confirms.
  Write-through has no dirty-set loss window, and its cost is that every
  write pays the store's latency. Oracle Coherence documents write-through
  and write-behind as two configurations of the identical `CacheStore`
  interface differing only in whether the store call happens inline or is
  deferred, which is the cleanest illustration that write-behind is a
  scheduling policy layered onto write-through's mechanism, not a
  fundamentally different architecture
  (["Read-Through, Write-Through, Write-Behind, and Refresh-Ahead
  Caching"](https://docs.oracle.com/cd/E16459_01/coh.350/e14510/readthrough.htm),
  Oracle Coherence 3.5 User Guide, verified 2026-08-02).

## 9. Known production uses

- **Oracle Coherence CacheStore, write-behind mode.** Coherence documents
  write-behind explicitly by name, stating that modified entries are
  written to the data source asynchronously after a configured delay, and
  that because of this "the cache is the system-of-record" until the
  write-behind queue is persisted, which the documentation flags as a
  business-regulation consideration for teams evaluating the pattern
  (["Read-Through, Write-Through, Write-Behind, and Refresh-Ahead
  Caching"](https://docs.oracle.com/cd/E16459_01/coh.350/e14510/readthrough.htm),
  Oracle Coherence 3.5 User Guide, verified 2026-08-02).
- **Hazelcast IMap, MapStore write-behind mode.** Hazelcast's distributed
  map supports a pluggable `MapStore` with a `write-delay-seconds` setting.
  A nonzero delay makes the store write-behind rather than write-through,
  with configurable `write-batch-size` for batching and `write-coalescing`,
  true by default, so only the latest value per key within the delay
  window is written
  (["MapStore Overview"](https://docs.hazelcast.com/hazelcast/5.5/mapstore/working-with-external-data)
  and
  ["Write-Behind Configuration Parameters"](https://docs.hazelcast.com/hazelcast/5.5/mapstore/configuration-guide),
  Hazelcast 5.5 documentation, verified 2026-08-02).
- **Linux kernel page cache writeback.** Every buffered write to a regular
  file on Linux is a write-behind write at the operating system layer. The
  write lands in the page cache and is marked dirty. The `write` system call
  returns without touching disk, and kernel flusher threads write dirty
  pages back once `dirty_expire_centisecs` elapses or the dirty-memory
  ratio crosses `dirty_background_ratio`
  (["Documentation for /proc/sys/vm/"](https://docs.kernel.org/admin-guide/sysctl/vm.html),
  Linux kernel documentation, verified 2026-08-02). This is the mechanism a
  plain `write()` call relies on by default, and it is the reason a program
  that needs a stronger guarantee must call `fsync` explicitly.

Judgement, not sourced beyond the three uses above. The same write-behind
shape recurs inside relational database engines at the buffer-pool level.
A modified page is marked dirty in the in-memory buffer pool and written to
the data file lazily by a background writer, while durability for the
committed transaction itself is carried by the write-ahead log rather than
by the page write. This entry does not cite a specific engine's internals
for that claim because engine implementations vary and change across
versions. Readers who want a sourced treatment of that specific mechanism
should consult the [B-Tree](b-tree.md) and [Write-Ahead Log](write-ahead-log.md)
entries in this catalog, which cite it directly.

## 10. Consequences

Positive.

- Write latency observed by the caller is close to the cache's own latency,
  not the backing store's, which can be an order of magnitude or more
  improvement for a remote or high-latency store.
- Store write volume drops in proportion to the workload's temporal
  locality, sometimes dramatically for hot keys, which reduces both
  infrastructure load and, for metered stores, direct cost.
- The backing store sees a smoother, batched write pattern instead of a
  spike per caller request, which is friendlier to storage engines whose
  write amplification or IOPS cost scales with operation count rather than
  with byte volume.
- The cache and the store can be decoupled in availability. A transient
  store outage does not have to fail caller-facing writes, as long as the
  dirty set can be held and retried once the store recovers.

Negative.

- A window of unflushed data exists at all times, and if the cache node
  holding it is lost before the flush completes, that data is gone unless
  the dirty set itself is durably replicated, which reintroduces most of
  the write-through cost the pattern was adopted to avoid.
- The store is no longer authoritative for current state, which silently
  breaks any consumer that reads the store directly instead of through the
  cache, including ad hoc queries, reporting jobs, and any second service
  sharing the same table.
- Failure handling moves from the request path, where an error is visible
  to the caller immediately, to a background process, where a failure can
  accumulate silently as a growing dirty set until it is caught by
  monitoring or until it causes an out-of-memory condition.
- Coalescing, when enabled, means any consumer that needs to see every
  intermediate value, not only the final one, cannot be served by this
  cache and needs a separate change-capture path.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| Data present in the cache during an incident but missing from the database after recovery | The dirty set lived only in the crashed node's memory and the flush window had not elapsed | Back the dirty set with a durable local write-ahead log, or replicate dirty entries to a standby before acknowledging the caller, and size the flush delay against the actual tolerable loss window, not against convenience |
| Two application servers report a different current value for the same key after a network partition heals | Two cache nodes both accepted writes for the same key with no single owner for its flush, and each flushed its own last-write independently | Route all writes for a given key to a single owning node or partition, for example through consistent hashing, so there is exactly one flusher for that key at any time |
| The database shows values that are minutes or hours old under normal load, even though monitoring shows no errors | The flusher's dirty set is growing faster than it drains, usually because batch size or flush frequency was tuned for a lighter historical load and never revisited | Alert on dirty-set size and oldest-pending-entry age directly, not only on flush errors, and treat a growing backlog as a capacity signal |
| A downstream analytics job or a second read-only service reports numbers that do not match what users see in the application | The downstream job reads the backing store directly, bypassing the cache, and sees the pre-flush value | Route every reader through the cache, or explicitly document and accept the staleness for that specific downstream consumer, with a bound on how stale it can be |
| A retried flush after a transient store failure double-applies a non-idempotent write, for example an increment rather than a set | The flush retry logic re-sends the same batch without the store operation being idempotent | Make the store-side write idempotent, an upsert of an absolute value rather than a relative increment where possible, or carry an idempotency key per flush attempt |
| Memory usage on the cache tier grows without bound during a store outage | The dirty set has no size cap, and the flusher keeps accumulating entries while retries fail against a degraded store, with no backpressure on new writes | Cap the dirty set, apply backpressure or reject new writes once the cap is reached, and separately alert operators the moment the cap is approached |
| A key that was deleted from the cache reappears in the database after a delay | A stale flush for the pre-delete value was already in flight when the delete happened, and it landed in the store after the delete was applied elsewhere | Version each dirty entry, and have the flusher discard or overwrite based on a monotonically increasing version rather than blind last-write-wins by wall-clock arrival |

## 12. Trade-off matrix

Compared against cache-aside, write-through, and change data capture, the
other three common ways of keeping a cache and a store connected.

| Force | Write-Behind | [Cache-Aside](../08-cloud-distributed/cache-aside.md) | Write-Through | [Change Data Capture](change-data-capture.md) |
|---|---|---|---|---|
| Write latency to caller | Cache-tier only, lowest of the four | Store-tier, cache is not involved in the write | Store-tier, highest, blocked on store confirm | Store-tier for the primary write, the cache update happens later via a stream |
| Data loss on cache node crash | Bounded window of loss unless dirty set is durably backed | None, store is written directly on every write | None, store confirms before caller does | None, store is written directly, the cache lags but never loses data |
| Store write volume | Reduced by coalescing, best for hot keys | Equal to the application's actual write rate | Equal to the application's actual write rate | Equal to the application's actual write rate, but decoupled from the cache update cost |
| Read consistency with store | Store can lag the cache by the flush window | Cache can be stale between invalidation and next read, never ahead | Cache and store agree at every read, both are current | Cache can lag the store by stream propagation delay |
| Operational complexity | Highest, needs a flusher, retry, backpressure, and monitoring of a hidden queue | Low, the cache is a pure accelerator with a simple invalidate-on-write rule | Low, one path, one failure mode | High, needs a change-capture pipeline and stream consumer, but decoupled from the cache |
| Best fit | Hot, high-frequency, tolerant-of-loss keys | General-purpose read acceleration | Anything that must never diverge from the store, low write volume | Fan-out to many downstream consumers, not primarily a caching concern |

## 13. Related and incompatible patterns

- **[Cache-Aside](../08-cloud-distributed/cache-aside.md).** The default
  companion when read-through-style population is also needed. Cache-aside
  populates the cache lazily on a read miss and never lets the cache get
  ahead of the store. Write-behind lets the cache get ahead of the store on
  purpose, on the write side. A system frequently runs both at once, read
  misses handled by cache-aside population, writes handled by write-behind
  flushing, sharing the same cache tier.
- **[Write-Ahead Log](write-ahead-log.md).** The standard technique for
  making the dirty set itself durable without paying the full cost of a
  synchronous store write. A local log absorbs the write cheaply and the
  cache's own crash recovery replays it, converting the write-behind
  cache's durability problem into the write-ahead log pattern's already
  well-understood durability problem.
- **[Change Data Capture](change-data-capture.md).** A different way to
  decouple a fast write path from downstream consumers, one that keeps the
  store itself as the immediate system of record and streams changes out
  after the fact, rather than deferring the store write itself. The two
  compose when a write-behind cache's own flush needs to notify other
  systems, the flush becomes the producer of a change event.
- **[Log Compaction](log-compaction.md).** Shares the coalescing idea,
  keeping only the latest value per key and discarding superseded ones, but
  applied to a persistent log rather than to an in-memory dirty set. A
  write-behind flusher that itself writes to a compacted log, rather than
  directly to a row store, combines both ideas.
- **[Buffer Pool](b-tree.md).** A database engine's buffer pool is a
  write-behind cache for on-disk pages, and this entry cross-references it
  rather than duplicating it because the buffer-pool literature already
  covers the page-eviction and dirty-page-writer mechanics in database
  engine terms.
- **Incompatible with strong consistency via consensus.** Any workload that
  requires linearizable reads across replicas, where every reader must
  observe every prior write immediately and identically regardless of which
  replica it talks to, cannot tolerate a component that is deliberately
  ahead of its own system of record. Write-behind and a consensus-backed
  strongly consistent store answer different questions, and layering
  write-behind in front of one defeats the guarantee the consensus layer
  exists to provide.

## 14. Refactoring path in and out

Introducing write-behind into a write-through system. Start from a working
write-through path, where every write already reaches the store
synchronously and correctly. Introduce the dirty set and the flusher first,
wired so that the flusher fires immediately after every write, effectively a
delay of zero, which should be behaviorally identical to write-through and
is a safe point to verify against the existing test suite. Increase the
delay and the batch size gradually while watching the staleness window and
the store's write volume, rather than jumping straight to a large delay.
Add coalescing only after confirming, for the specific workload, that no
consumer needs to see intermediate values. At every step, keep the ability
to force an immediate synchronous flush for a specific key, needed for
shutdown, for administrative tools, and for any code path that must read
its own write from the store directly rather than through the cache.

Removing write-behind, reverting to write-through or cache-aside. Stop
accepting new writes into the dirty path, force a full drain of the
existing dirty set, and confirm the drain completed and the store reflects
every previously cached key before switching the write path to synchronous.
This ordering matters. Switching the write path first, while a dirty set
still exists from before the switch, leaves the previously deferred writes
permanently stranded unless the flusher is explicitly kept running until
the dirty set is empty. Removing write-behind is safe to do incrementally
per key range or per shard, which lets an operator revert one hot shard at
a time if the pattern turns out to be the wrong fit for only part of the
workload.

## 15. Testing and verification

Write-behind makes two things easier to test and one thing meaningfully
harder. It is easy to test the read-your-own-writes property in isolation,
because the cache always answers from its own state regardless of the
flusher, and a unit test can assert `get` reflects the latest `put` without
any interaction with a real store at all. It is easy to test coalescing in
isolation, by writing the same key several times and asserting the flush
receives exactly one entry for that key with the last value written, which
is what the code examples in dimension 19 verify directly.

What becomes harder is testing the crash-and-recovery path, because it
requires deliberately killing the process, or the equivalent inside a test
runner, between a write and its flush, and then asserting on what
survived. A test double for the backing store that can be configured to
fail on demand is the standard technique. Run a sequence of writes, force
the fake store to reject the next flush attempt, assert the dirty set still
contains the rejected entries afterward rather than having silently dropped
them, then let the store succeed and assert the entries eventually land.
Property-based testing is a good fit for the coalescing and ordering
invariants specifically. Generate a random interleaving of writes to a
small set of keys and assert that, after a full drain with coalescing
enabled, the store holds exactly the last value written per key, and, with
coalescing disabled, that every value was written to the store in the same
relative order it was written to the cache.

Integration testing should include an explicit backpressure test. Fill the
dirty set to its configured cap with a store double that never succeeds,
and assert that a subsequent write either blocks, is rejected with a clear
error, or is otherwise handled by policy rather than silently accepted and
then silently dropped, because silent dropping past the cap is the failure
mode dimension 11 names directly.

## 16. Observability signals

A healthy write-behind cache shows a dirty-set size that oscillates within a
bounded, predictable range tied to the configured flush delay and the
workload's write rate, and an age-of-oldest-dirty-entry metric that never
exceeds roughly the configured delay by more than the store's own write
latency. The flush-success rate should sit at or near 100 percent under
normal operation, with any sustained drop treated as an incident, not
noise, because a drop in flush success is the earliest visible signal of
the exact loss-of-durability risk this pattern accepts by design.

Signals to expose, at minimum. Dirty-set size, both current and as a
distribution over time. Age of the oldest dirty entry. Flush batch size,
both configured and actual, since coalescing can make actual batches
smaller than the size limit. Flush success and failure counts, tagged by
error class. A specific alert when the dirty-set size crosses a fraction of
its configured cap, well before the cap is reached, since reaching the cap
means new writes are already being throttled or rejected. And a
crash-recovery counter, incremented whenever the cache tier restarts,
correlated against the dirty-set size immediately before the restart, so
that observers can answer how much was just lost from a dashboard rather
than by reconstructing it by hand after the fact. A dashboard that shows
flush throughput and store latency side by side makes the
throughput-versus-store-load trade-off from dimension 3 directly visible,
which is useful evidence when deciding whether to widen or narrow the
flush delay.

## 17. Security and privacy implications

Write-behind extends the window during which sensitive data exists only in
volatile memory and has not yet reached whatever access controls, audit
logging, or encryption-at-rest the backing store provides. For personal
data subject to a deletion request, a value already in the dirty set at the
moment a deletion request arrives must be handled explicitly. Either the
flusher must check for a pending deletion before writing a stale value that
would resurrect deleted data, or deletion requests must themselves flow
through the same dirty-set-and-flush path with a version or tombstone that
wins over any earlier pending write. This is the same version-ordering
concern flagged in dimension 11's table for the reappearing-key failure
mode, applied specifically to a right-to-erasure obligation rather than to
an ordinary correctness bug.

A cache node holding a large dirty set is also, briefly, holding a larger
amount of not-yet-durable, not-yet-audited data than a write-through system
would ever accumulate, which changes the blast radius of a compromised or
misbehaving cache node from whatever was cached to whatever was cached,
plus every mutation not yet flushed. Where the backing store enforces
row-level or field-level access control as part of the write path, for
example a database trigger that rejects a write violating a business rule,
that check is bypassed entirely for the duration a value sits in the dirty
set, and only enforced once the flush actually reaches the store. A
write-behind cache is not a safe place to also enforce a security-relevant
invariant that the application depends on the store to reject.

## 18. References

- Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, *Design
  Patterns. Elements of Reusable Object-Oriented Software*, Addison-Wesley,
  1994. Cited in this entry for the general software-patterns lineage this
  catalog follows, not for write-behind specifically, which the book does
  not cover.
- John L. Hennessy, David A. Patterson, *Computer Organization and Design*,
  5th edition, Morgan Kaufmann, 2013, chapter 5, "Large and Fast, Exploiting
  Memory Hierarchy." Source for the write-back versus write-through cache
  policy distinction at the hardware level.
- Martin Kleppmann, *Designing Data-Intensive Applications*, O'Reilly, 2017,
  chapter 3, "Storage and Retrieval." Source for the durability-window
  reasoning applied to buffered and deferred writes.
- Oracle, ["Read-Through, Write-Through, Write-Behind, and Refresh-Ahead
  Caching"](https://docs.oracle.com/cd/E16459_01/coh.350/e14510/readthrough.htm),
  Oracle Coherence 3.5 User Guide, verified 2026-08-02.
- Hazelcast, ["MapStore
  Overview"](https://docs.hazelcast.com/hazelcast/5.5/mapstore/working-with-external-data),
  Hazelcast 5.5 documentation, verified 2026-08-02.
- Hazelcast, ["Write-Behind Configuration
  Parameters"](https://docs.hazelcast.com/hazelcast/5.5/mapstore/configuration-guide),
  Hazelcast 5.5 documentation, verified 2026-08-02.
- The Linux Kernel Organization, ["Documentation for
  /proc/sys/vm/"](https://docs.kernel.org/admin-guide/sysctl/vm.html), Linux
  kernel documentation, verified 2026-08-02.

## 19. Code examples

The same write-behind cache, coalescing writer, and batching flusher,
implemented three times. Each example demonstrates the three properties
that define the pattern. A write returns without waiting on the store. A
read immediately after a write observes the new value. And multiple writes
to the same key before a flush are coalesced into a single store write
carrying only the last value.

### TypeScript

```typescript
type FlushFn<K, V> = (entries: [K, V][]) => Promise<void>;

class WriteBehindCache<K, V> {
  private store = new Map<K, V>();
  private dirty = new Map<K, V>();
  private timer: ReturnType<typeof setInterval> | null = null;
  private flushing = false;

  constructor(
    private readonly flush: FlushFn<K, V>,
    private readonly delayMs = 200,
    private readonly maxBatch = 100,
  ) {
    this.timer = setInterval(() => void this.drain(), this.delayMs);
  }

  put(key: K, value: V): void {
    this.store.set(key, value);
    this.dirty.set(key, value);
  }

  get(key: K): V | undefined {
    return this.store.get(key);
  }

  private async drain(): Promise<void> {
    if (this.flushing || this.dirty.size === 0) return;
    this.flushing = true;
    const batch = [...this.dirty.entries()].slice(0, this.maxBatch);
    for (const [k] of batch) this.dirty.delete(k);
    try {
      await this.flush(batch);
    } catch {
      for (const [k, v] of batch) if (!this.dirty.has(k)) this.dirty.set(k, v);
    } finally {
      this.flushing = false;
    }
  }

  async shutdown(): Promise<void> {
    if (this.timer) clearInterval(this.timer);
    while (this.dirty.size > 0) await this.drain();
  }
}

async function main(): Promise<void> {
  const written: [string, number][] = [];
  const cache = new WriteBehindCache<string, number>(async (batch) => {
    written.push(...batch);
  }, 50, 10);

  cache.put("a", 1);
  cache.put("a", 2);
  cache.put("b", 5);

  if (cache.get("a") !== 2) throw new Error("read-your-writes failed");

  await cache.shutdown();

  const aWrites = written.filter(([k]) => k === "a");
  if (aWrites.length !== 1) throw new Error("expected one coalesced write");
}

void main();
```

### Python

```python
import threading
import time
from typing import Callable, Dict, List, Tuple, TypeVar, Generic

K = TypeVar("K")
V = TypeVar("V")


class WriteBehindCache(Generic[K, V]):
    def __init__(self, flush: Callable[[List[Tuple[K, V]]], None],
                 delay_seconds: float = 0.05, max_batch: int = 100) -> None:
        self._store: Dict[K, V] = {}
        self._dirty: Dict[K, V] = {}
        self._lock = threading.Lock()
        self._flush = flush
        self._delay = delay_seconds
        self._max_batch = max_batch
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def put(self, key: K, value: V) -> None:
        with self._lock:
            self._store[key] = value
            self._dirty[key] = value

    def get(self, key: K) -> V:
        with self._lock:
            return self._store[key]

    def _drain(self) -> None:
        with self._lock:
            if not self._dirty:
                return
            items = list(self._dirty.items())[: self._max_batch]
            for k, _ in items:
                del self._dirty[k]
        try:
            self._flush(items)
        except Exception:
            with self._lock:
                for k, v in items:
                    self._dirty.setdefault(k, v)

    def _loop(self) -> None:
        while not self._stop.is_set():
            time.sleep(self._delay)
            self._drain()

    def shutdown(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)
        while True:
            with self._lock:
                if not self._dirty:
                    break
            self._drain()


def main() -> None:
    written: List[Tuple[str, int]] = []
    cache: WriteBehindCache[str, int] = WriteBehindCache(
        lambda batch: written.extend(batch), delay_seconds=0.02, max_batch=10
    )

    cache.put("a", 1)
    cache.put("a", 2)
    cache.put("b", 5)

    assert cache.get("a") == 2, "read-your-writes failed"

    cache.shutdown()

    a_writes = [w for w in written if w[0] == "a"]
    assert len(a_writes) == 1, "expected one coalesced write"


if __name__ == "__main__":
    main()
```

### Go

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type entry struct {
	key   string
	value int
}

type WriteBehindCache struct {
	mu       sync.Mutex
	store    map[string]int
	dirty    map[string]int
	flush    func([]entry) error
	maxBatch int
	stop     chan struct{}
	done     chan struct{}
}

func NewWriteBehindCache(delay time.Duration, maxBatch int, flush func([]entry) error) *WriteBehindCache {
	c := &WriteBehindCache{
		store:    make(map[string]int),
		dirty:    make(map[string]int),
		flush:    flush,
		maxBatch: maxBatch,
		stop:     make(chan struct{}),
		done:     make(chan struct{}),
	}
	go c.loop(delay)
	return c
}

func (c *WriteBehindCache) Put(key string, value int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.store[key] = value
	c.dirty[key] = value
}

func (c *WriteBehindCache) Get(key string) (int, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	v, ok := c.store[key]
	return v, ok
}

func (c *WriteBehindCache) drain() {
	c.mu.Lock()
	if len(c.dirty) == 0 {
		c.mu.Unlock()
		return
	}
	batch := make([]entry, 0, len(c.dirty))
	for k, v := range c.dirty {
		batch = append(batch, entry{k, v})
		if len(batch) >= c.maxBatch {
			break
		}
	}
	for _, e := range batch {
		delete(c.dirty, e.key)
	}
	c.mu.Unlock()

	if err := c.flush(batch); err != nil {
		c.mu.Lock()
		for _, e := range batch {
			if _, still := c.dirty[e.key]; !still {
				c.dirty[e.key] = e.value
			}
		}
		c.mu.Unlock()
	}
}

func (c *WriteBehindCache) loop(delay time.Duration) {
	ticker := time.NewTicker(delay)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			c.drain()
		case <-c.stop:
			close(c.done)
			return
		}
	}
}

func (c *WriteBehindCache) Shutdown() {
	close(c.stop)
	<-c.done
	for {
		c.mu.Lock()
		empty := len(c.dirty) == 0
		c.mu.Unlock()
		if empty {
			return
		}
		c.drain()
	}
}

func main() {
	var mu sync.Mutex
	var written []entry

	cache := NewWriteBehindCache(20*time.Millisecond, 10, func(batch []entry) error {
		mu.Lock()
		written = append(written, batch...)
		mu.Unlock()
		return nil
	})

	cache.Put("a", 1)
	cache.Put("a", 2)
	cache.Put("b", 5)

	if v, _ := cache.Get("a"); v != 2 {
		panic("read-your-writes failed")
	}

	cache.Shutdown()

	count := 0
	for _, e := range written {
		if e.key == "a" {
			count++
		}
	}
	if count != 1 {
		panic(fmt.Sprintf("expected one coalesced write, got %d", count))
	}
}
```

All three samples were compiled and run locally against the exact commands
this repository's checkers use. TypeScript was checked with `tsc --noEmit
--strict` against a scratch project carrying `typescript@5` and
`@types/node@22`. Python was checked with `python3 -m py_compile` and also
executed directly with `python3`. Go was checked with `go vet` and also
built and executed with `go run`. All three produced the expected coalesced
single write for the repeated key and the expected read-your-writes result
on the direct execution runs.
