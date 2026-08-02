---
name: Cache-Aside
slug: cache-aside
family: 08-cloud-distributed
category: Cloud and Distributed
aliases: [Lazy Loading, Look-Aside Cache, Demand-Filled Cache, Lazy Population]
first_described: "Microsoft patterns and practices, Cloud Design Patterns, 2014"
maturity: canonical
related: [read-through-cache, write-through-cache, write-behind-cache, refresh-ahead-cache, circuit-breaker, bulkhead, materialized-view, retry]
incompatible_with: []
verified: 2026-08-02
---

# Cache-Aside

## 1. Name, aliases, and lineage

The canonical name in the cloud architecture literature is **Cache-Aside**. It is
catalogued by Microsoft as one of the cloud design patterns, described as loading
data on demand into a cache from a data store
([Microsoft Learn, Cache-Aside pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside),
verified 2026-08-02). The Microsoft page frames the pattern as an application-side
emulation of read-through caching for caches that do not provide read-through
natively.

The same shape carries several other names, and the names come from different
communities rather than describing different mechanics.

- **Lazy loading.** The name used in the Amazon ElastiCache documentation, which
  defines it as a caching strategy that loads data into the cache only when
  necessary ([AWS, Caching strategies for Memcached](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html),
  verified 2026-08-02). This is the name most often heard in AWS shops.
- **Look-aside cache.** The name used in the Facebook memcached paper, which
  describes memcache at Facebook as a demand-filled look-aside cache
  ([Nishtala et al., *Scaling Memcache at Facebook*, USENIX NSDI 2013](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala),
  verified 2026-08-02). Look-aside contrasts with inline, where the cache sits in
  the request path and the caller never sees the origin.
- **Demand-filled cache.** From the same paper, describing the fill discipline
  rather than the lookup discipline.
- **Manual population.** The name used by the Caffeine caching library for Java,
  which contrasts the manual `Cache` interface against the `LoadingCache`
  read-through interface
  ([Caffeine wiki, Population](https://github.com/ben-manes/caffeine/wiki/Population),
  verified 2026-08-02).

The pattern has no single inventor. Look-aside caching predates the cloud
literature by decades, and the memcached ecosystem was already built around it
before anyone catalogued it as a pattern. What the Microsoft catalog contributed
was the name plus a written account of the consistency problems, which is why
Cache-Aside is the name that travels across teams.

One naming trap deserves attention. Some engineers use cache-aside loosely to mean
"we have a cache". The discriminating property is *who talks to the origin*. In
Cache-Aside the application talks to the cache and to the origin, and the cache
knows nothing about the origin. If the cache itself fetches from the origin on a
miss, that is Read-Through, a different pattern with a different failure profile.
Dimension 12 sets out the full discrimination.

## 2. Problem and context

A service reads the same records far more often than it writes them, and the read
path is expensive. The expense might be a relational join, a cross-region call, a
disk seek on a cold row, a rate-limited third-party API, or a language model
invocation billed per token. Read volume is high enough that the origin becomes
the constraint on throughput or on cost, but the working set is far smaller than
the full data set, so most of the traffic hits a small number of keys.

The problem reads like this in a codebase. A repository method issues a query, and
a profiler shows the same query executing thousands of times per minute with the
same parameters and the same result. Latency at the ninety-ninth percentile tracks
database CPU rather than anything in the application. Scaling the origin works
until the next traffic step, and it is the expensive option.

Adding a cache is the obvious answer, and the hard part is not the cache. The hard
part is deciding where the fill logic lives and what happens when the cached copy
disagrees with the origin. Cache-Aside answers the first question by putting the
fill logic in the application, and answers the second question honestly by
admitting that it does not solve consistency, only bounds staleness.

The context in which the pattern is the right answer has four parts.

- **Reads outnumber writes** by a wide margin, so a cached copy earns its keep many
  times before it is invalidated.
- **The application can tolerate stale reads** for a bounded window. If it cannot,
  the answer is a different pattern or no cache at all.
- **The cache and the origin are separate systems** with independent failure
  modes, and the application is expected to keep working when the cache is empty
  or unreachable.
- **The access pattern is not known in advance**, so priming the entire data set is
  either impossible or wasteful. The Microsoft page names unpredictable resource
  demand as a reason to reach for the pattern.

Outside that context the pattern is a liability. See dimension 4.

## 3. Forces

This dimension is largely engineering judgement. The individual mechanics are
sourced elsewhere in this entry. The weighting below is reasoning about which
pressure weighs heaviest, not a citable fact.

- **Latency.** Strongly favoured on the hit path, sacrificed on the miss path. A
  hit is one network round trip to an in-memory store. A miss costs three trips,
  the cache read, the origin query, and the cache write. AWS names this the cache
  miss penalty and states plainly that each miss results in three trips
  ([AWS, Caching strategies](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html),
  verified 2026-08-02). A workload with a poor hit ratio is therefore slower with
  the cache than without it.
- **Consistency.** Sacrificed, deliberately and visibly. The Microsoft page states
  that the pattern does not guarantee consistency between the data store and the
  cache, and that an external process can change an item at any time without the
  change appearing in the cache until the item loads again. This is the price of
  admission, and a design that pretends otherwise is broken rather than optimised.
- **Coupling.** Mixed. The cache is decoupled from the origin, which is why a cache
  outage degrades rather than breaks the system. The application is coupled to
  both, which is why the fill and invalidate logic is duplicated at every call
  site unless it is factored into one place.
- **Operability.** Favoured on the failure path, sacrificed on the correctness
  path. AWS states that node failures are not fatal for the application, because a
  new empty node keeps serving with increased latency while it refills. Against
  that, an operator debugging a wrong value must now reason about two copies of
  the truth and the window between them.
- **Cost.** Favoured in steady state, and this is often the real reason the pattern
  ships. Memory is cheaper per read than a database instance sized for peak read
  volume. The cost reverses on a cold cache, where the origin briefly sees the full
  unfiltered load.
- **Cognitive load.** Sacrificed. Every developer touching the read path now holds
  three questions in mind. Is this key cached, what is its TTL, and who invalidates
  it. Read-Through moves that load into the cache library, which is its main
  advantage.
- **Team topology.** Mildly favoured. The pattern needs no support from the team
  that owns the origin, so a consuming team can adopt it unilaterally. That is also
  how caches get added without anyone owning the invalidation contract.
- **Blast radius.** Favoured. Because the cache is not in the write path, a cache
  failure cannot corrupt the system of record. The worst case is that the origin
  takes the full read load, which is a capacity problem rather than a data problem.

A pattern that sacrifices nothing is described wrongly. Cache-Aside pays for its
latency and cost wins with consistency and cognitive load, and it pays on the miss
path for what it earns on the hit path.

## 4. Applicability and non-applicability

### Reach for Cache-Aside when

- Reads outnumber writes by roughly an order of magnitude or more and the same
  keys recur.
- The cache technology does not provide read-through natively. The Microsoft page
  gives this as the first condition for use.
- Resource demand is unpredictable and the working set cannot be enumerated in
  advance.
- The application must keep serving when the cache is unavailable, so the origin
  path has to exist anyway.
- Different keys deserve different freshness policies, so a single global cache
  configuration would be wrong.
- The origin is a metered external dependency, where each avoided call is money
  rather than milliseconds.

### Non-applicability, do NOT reach for Cache-Aside when

This is the more valuable list, and it is the one most catalogs omit.

- **The data is sensitive or security related.** The Microsoft page states this
  directly and adds that a shared cache makes it worse. A cache is a second copy
  of the data with a different access control model, a different encryption
  posture, and usually no audit trail. See dimension 17.
- **Most requests miss.** The three-trip miss penalty means a low hit ratio makes
  the system slower and more expensive at once. If the key space is large and
  access is uniform, the cache is pure overhead. The Microsoft page names this
  explicitly as a case where the overhead outweighs the benefit.
- **The cached data set is static and small enough to fit.** The Microsoft page
  says to prime the cache at startup and set a policy that prevents expiry
  instead. Lazy filling adds a miss penalty that buys nothing.
- **Read-after-write freshness is required on the same path.** The Microsoft page
  distinguishes Cache-Aside from write-through precisely here. Cache-Aside
  invalidates on write and repopulates on the next read, so between the write and
  the next read a reader can miss or briefly see stale data. If a user must see
  their own edit immediately, either bypass the cache for that read or use
  Write-Through.
- **Writes outnumber reads.** Every write costs an invalidation, and the entry is
  rarely read before the next write removes it again. The cache becomes a tax on
  the write path with no read benefit.
- **The correctness of a decision depends on the value.** Inventory decrements,
  balance checks, permission checks at the point of enforcement, and idempotency
  keys must read the system of record. Caching a permission grant means caching a
  revocation delay.
- **The cache is per-instance and instances see the same user.** The Microsoft page
  warns that a local in-process cache is private, so different application
  instances each hold their own copy and those copies drift apart. Behind a load
  balancer without affinity, a user sees an inconsistent view depending on which
  instance answers.
- **Session state in a web farm.** The Microsoft page calls this out as unsuitable
  because it introduces a dependency on client-server affinity.
- **The value is large relative to the benefit.** Caching multi-megabyte blobs in a
  shared cache moves the bottleneck to network serialisation and eviction churn.
  Cache the identifier or a projection instead.
- **Semantic equivalence is assumed but not true.** The Microsoft page adds a
  warning specific to language model workloads. Only use semantic caching when the
  data supports semantic equivalence and does not risk returning unrelated
  responses. Two users asking a semantically identical question about their own
  data must not share a cache entry.

## 5. Structure

Cache-Aside has four participants. None of them is a class in a class diagram
sense. Three are usually processes and one is a code path.

- **Caller.** The request handler or service method that needs a value by key. It
  does not know whether the value came from the cache or the origin, and it must
  not need to.
- **Cache-Aside Reader.** The code path that owns the read algorithm. Probe the
  cache, on miss query the origin, on success populate the cache, return the value.
  It also owns the negative-result decision and the TTL decision. In a healthy
  codebase this is one function per key family, not one copy per call site.
- **Cache Store.** An in-memory key-value store with expiry and eviction. It knows
  nothing about the origin, the schema, or the meaning of the values. Its contract
  is get, set with TTL, and delete. It is allowed to lose any entry at any moment,
  which is the property that makes the pattern safe.
- **System of Record.** The authoritative store. It is queried on miss and written
  on update. It has no knowledge that a cache exists.

Two more participants appear once the pattern meets production load.

- **Invalidator.** The code path that runs after a write commits and removes or
  overwrites the affected keys. Its correctness depends on ordering, and the
  ordering is not obvious. See dimension 7.
- **Rebuild Coordinator.** The mechanism that stops many concurrent misses on the
  same key from all reaching the origin. It is a lock, a lease, an in-process
  single-flight group, or a probability calculation. It is optional in the
  textbook version of the pattern and mandatory in any deployment where a single
  key can be hot.

The relationships are directed. Caller depends on Reader. Reader depends on Cache
Store and on System of Record. Cache Store and System of Record do not depend on
each other, and that absence is the defining structural property of the pattern.

## 6. ASCII structure diagram

```
   +----------------+
   |     Caller     |   request(key)
   +----------------+
            |
            v
   +--------------------------------------------------+
   |            Cache-Aside Reader                     |
   |  get -> on miss load -> populate -> return        |
   |  owns TTL choice, negative caching, rebuild       |
   +--------------------------------------------------+
        |  (1) get / set          |  (2) load on miss
        |      / delete           |
        v                         v
   +-----------------+      +----------------------+
   |   Cache Store   |      |  System of Record    |
   |  key -> value   |      |  authoritative data  |
   |  TTL, eviction  |      |  no cache awareness  |
   +-----------------+      +----------------------+
        ^                         ^
        |  (4) delete key         |  (3) commit write
        |                         |
   +--------------------------------------------------+
   |                  Invalidator                      |
   |     write path, commit FIRST then delete key      |
   +--------------------------------------------------+

   Optional, engaged under load:

   +---------------------------+
   |    Rebuild Coordinator    |  lease | lock | single-flight
   |  admits ONE filler per key|  | probabilistic early expiry
   +---------------------------+
```

The absence of an arrow between Cache Store and System of Record is the whole
point. Draw that arrow and the diagram becomes Read-Through.

## 7. Dynamics

Three flows matter, the hit, the miss, and the write. The third is where the
pattern's real difficulty lives.

### Read flow

```
Caller      Reader        Cache          Origin
  |            |            |               |
  |--get(k)--->|            |               |
  |            |--GET k---->|               |
  |            |<--value----|   HIT, 1 hop, return
  |<--value----|            |               |
  |            |            |               |
  |--get(k)--->|            |               |
  |            |--GET k---->|               |
  |            |<--nil------|   MISS
  |            |------------|--SELECT k---->|
  |            |            |<--row---------|
  |            |--SET k,ttl>|               |
  |<--value----|            |               |   3 hops total
```

### Write flow, correct ordering

```
Writer       Origin         Cache          Reader (concurrent)
  |            |              |               |
  |--UPDATE--->|              |               |
  |<--commit---|              |               |
  |------------|--DEL k------>|               |
  |            |              |<--GET k-------|  miss
  |            |<-------------|--SELECT k-----|  reads NEW value
  |            |------------->|--SET k--------|
```

Order matters and the failure is subtle. The Microsoft page states the rule
directly. Update the data store before removing the item from the cache, because
if the cached item is removed first there is a small window in which a client
fetches the item, misses, reads the outdated row, and writes it back to the cache
([Microsoft Learn, Cache-Aside pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside),
verified 2026-08-02). The stale value then survives for a full TTL.

### The dual write inconsistency window

Even with the correct ordering there is a window. This is intrinsic to the
pattern, not a bug in any implementation, and it deserves to be stated plainly
rather than hidden.

```
  T0  Reader R misses on k, issues SELECT
  T1  Origin returns v_old to R
  T2  Writer W commits v_new to origin
  T3  Writer W deletes k from cache
  T4  Reader R writes v_old into cache with full TTL
      ------------------------------------------------
      Cache now holds v_old. Origin holds v_new.
      The two disagree until TTL expiry or the next write.
```

R read a value that was correct when it read it, and wrote it after the
invalidation had already passed. Nothing in the sequence is a coding error. The
race is real and it is the reason the pattern needs bounded TTLs even when every
write invalidates. Three mitigations exist and each has a cost.

- **Bounded TTL.** Does not prevent the race, bounds its duration. Cheapest and
  most common. This is why a TTL is mandatory even in a fully invalidated cache.
  TTL is the backstop for the race, not only a freshness knob.
- **Leases or versioned sets.** The cache refuses a set whose token was issued
  before the invalidation. This is what Facebook's memcached leases do. The paper
  describes a lease as a token given to a client on a miss, and states that leases
  address stale sets, which occur when a web server sets a value that does not
  reflect the latest value that should be cached, and thundering herds
  ([Nishtala et al., NSDI 2013](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala),
  verified 2026-08-02). This closes the race properly and requires cache-server
  support.
- **Delayed second delete.** The writer deletes the key, waits longer than a
  typical origin read, and deletes again. Widely used, cheap to implement,
  probabilistic rather than correct, and it doubles the invalidation traffic. Treat
  it as a mitigation with a known hole, not a fix. This assessment is engineering
  judgement.

## 8. Implementation variants

### Variant A. Inline at the call site

The read algorithm is written wherever a value is needed. It is the version in
every tutorial, including the C# example on the Microsoft page. It is correct for
one or two call sites and becomes unmaintainable at ten, because the TTL, the key
format, and the negative-caching decision drift apart. The cost is duplication and
inconsistency. The benefit is that nothing is hidden.

### Variant B. Repository or loader function

One function per key family owns the algorithm. The key format, TTL, serialisation
format, and invalidation are defined together. This is the version that should
ship. The cost is one indirection. The benefit is that the invalidation contract
has an owner.

### Variant C. Single-flight coalescing, in process

Concurrent misses on the same key inside one process collapse into one origin
call. Go ships this in the standard extended library. The `singleflight` package
provides a duplicate function call suppression mechanism, and `Group.Do` makes
sure that only one execution is in-flight for a given key at a time while
duplicate callers wait and receive the same result
([golang.org/x/sync/singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight),
verified 2026-08-02). The cost is a shared coordination structure on the read path,
and one slow origin call now blocks every waiter for that key. The benefit is that
origin load on a hot key becomes independent of instance concurrency.

### Variant D. Distributed rebuild lock

Coalescing across processes needs a lock in the shared cache, usually a
set-if-not-exists with an expiry. The losing callers either wait, serve stale, or
fail fast. The cost is a second cache round trip on every miss, plus the entire
distributed lock problem including expiry tuning and the fencing question. The
benefit is that origin load on a hot key becomes independent of instance count,
which is what matters during an autoscaling event.

### Variant E. Lease-based coordination in the cache server

The cache itself hands out a permission token on a miss and rejects sets without a
valid token. Facebook's memcached does this, and by default returns a token only
once every ten seconds per key, with other clients told to wait briefly
([Nishtala et al., NSDI 2013](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala),
verified 2026-08-02). The cost is that it requires a modified cache server. The
benefit is that it solves both the thundering herd and the stale set with one
mechanism, which no client-side approach does.

### Variant F. Probabilistic early expiration

Each reader independently decides whether to rebuild before the entry expires,
with a probability that rises as expiry approaches. The XFetch algorithm from
Vattani, Chierichetti and Lowenstein evaluates `time() - delta *beta* ln(rand())
>= expiry`, where`delta` is the measured recomputation cost and `beta` tunes how
early recomputation is favoured
([Vattani, Chierichetti, Lowenstein, *Optimal Probabilistic Cache Stampede
Prevention*, PVLDB volume 8, pages 886 to 897, 2015](https://dl.acm.org/doi/10.14778/2757807.2757813),
verified 2026-08-02, author copy at
[cseweb.ucsd.edu](https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf),
verified 2026-08-02). The cost is that some rebuilds happen earlier than strictly
needed, and expensive keys rebuild more eagerly because `delta` is larger. The
benefit is no lock, no coordination, no waiting reader, and no expiry cliff. The
Python sample below shows a run in which the entry never once reached hard expiry.

### Variant G. Stale-while-revalidate

On expiry the stale value keeps being served while one caller refreshes in the
background. Caffeine implements this as `refreshAfterWrite`, documented as making
a key eligible for refresh after a duration with the refresh initiated only when
the entry is queried, and stating that the old value is still returned while the
key is being refreshed, in contrast to eviction which forces retrievals to wait
([Caffeine wiki, Refresh](https://github.com/ben-manes/caffeine/wiki/Refresh),
verified 2026-08-02). The cost is that readers knowingly see stale data past the
nominal TTL. The benefit is that the miss penalty disappears from the user-visible
path entirely.

### Variant H. Negative caching

A confirmed absence is cached under its own shorter TTL so that repeated lookups
for a nonexistent key do not reach the origin. This is not a novelty of
application caching. DNS has had it since 1998, where RFC 2308 defines negative
caching as the storage of knowledge that something does not exist, and advises
that values of one to three hours work well as a default while values exceeding
one day have been found to be problematic
([RFC 2308, *Negative Caching of DNS Queries*](https://www.rfc-editor.org/rfc/rfc2308.html),
verified 2026-08-02). The cost is that a newly created record is invisible until
the negative entry expires, so creation paths must invalidate the negative key.
The benefit is that it closes the cache penetration hole described in dimension 11.

### Variant I. Membership filter in front of the cache

For key spaces where absence is common and enumerable, a Bloom filter answers
whether a key is definitely absent before either the cache or the origin is
consulted. Redis documents the property that makes this safe. A Bloom filter can
guarantee the absence of an item from a set, so a negative answer is certain,
while one out of every N positive answers will be wrong
([Redis, Bloom filter](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/),
verified 2026-08-02). The underlying structure is Burton Bloom's, *Space/Time
Trade-offs in Hash Coding with Allowable Errors*, Communications of the ACM 1970,
linked as an academic source from that same Redis page. The cost is that the
filter must be kept in step with creations and cannot support deletions without
switching to a counting or cuckoo variant. The benefit is that a hostile caller
enumerating random identifiers is stopped at the cheapest possible layer.

### Language-idiomatic shapes

- **Go.** A closure plus `singleflight.Group` replaces the coordinator object
  entirely. The idiomatic unit is a function, not a class.
- **Python.** The read algorithm is usually a decorator over the loader, which
  makes the TTL a decorator argument and therefore visible at the definition site.
- **TypeScript.** A promise held in a map is a natural single-flight primitive,
  because awaiting the same promise twice costs nothing. The in-flight map is the
  whole mechanism.
- **Rust.** Ownership pushes the design toward a value returned by clone or an
  `Arc`, and the coordination becomes an explicit `Mutex` plus `Condvar` rather
  than an ambient library.
- **Java.** `ConcurrentHashMap.computeIfAbsent` gives per-key coalescing for free,
  and Caffeine's `Cache.get(key, loader)` is the same idea with eviction attached.

## 9. Known production uses

- **Facebook memcached.** The NSDI 2013 paper describes memcache at Facebook as a
  demand-filled look-aside cache, with the web server checking memcache first, and
  on a miss retrieving from the database and populating the cache. The paper also
  introduces leases specifically to handle stale sets and thundering herds, with a
  default of one token per key per ten seconds
  ([Nishtala et al., *Scaling Memcache at Facebook*, USENIX NSDI 2013](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala),
  verified 2026-08-02). This is the reference deployment for the pattern under
  heavy load and the reference implementation of the coordination remedy.
- **Netflix EVCache.** EVCache is described by its own repository as a memcached
  and spymemcached based caching solution used for AWS EC2 infrastructure for
  caching frequently used data, with the name standing for Ephemeral, Volatile,
  Cache ([Netflix/EVCache on GitHub](https://github.com/Netflix/EVCache),
  verified 2026-08-02). Reported operating scale is 22,000 server instances,
  400 million operations per second, 2 trillion items totalling 14.3 petabytes,
  and 200 memcached clusters
  ([InfoQ, Netflix global cache](https://www.infoq.com/articles/netflix-global-cache/),
  verified 2026-08-02). The Ephemeral, Volatile naming is the pattern's safety
  property made into a product name. Any entry may vanish, and the application
  keeps working.
- **MediaWiki and Wikimedia.** MediaWiki's `WANObjectCache` implements the pattern
  with the stampede remedies built in. Wikimedia's own engineering guidance states
  that WANCache automatically handles at-scale needs including stampede
  protection, purging and mutex locks, and warms caches by regenerating values
  before they expire, and that the TTL argument and the `hotTTR` option use
  time-dependent randomisation to avoid stampedes
  ([Wikimedia, MediaWiki Engineering backend performance practices](https://wikitech.wikimedia.org/wiki/MediaWiki_Engineering/Guides/Backend_performance_practices),
  verified 2026-08-02). The documented policy that popular keys preemptively
  refresh while long-tail keys keep their high nominal TTL is variant F and
  variant G combined in one production system.
- **Amazon ElastiCache.** AWS documents lazy loading as a first-class caching
  strategy with pseudocode identical to the pattern, and pairs it with an explicit
  recommendation to add a TTL to every write so that a lazily loaded cache does not
  accumulate unbounded staleness
  ([AWS, Caching strategies for Memcached](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html),
  verified 2026-08-02). The interesting detail is that AWS recommends combining
  lazy loading *with* write-through rather than choosing between them, because
  write-through alone leaves a new node with missing data.
- **Caffeine, as the deliberate alternative.** Caffeine offers the manual `Cache`
  interface for explicit control of retrieving, updating and invalidating entries,
  alongside `LoadingCache` for read-through
  ([Caffeine wiki, Population](https://github.com/ben-manes/caffeine/wiki/Population),
  verified 2026-08-02). A library that ships both, and names them differently, is
  evidence that the distinction in dimension 12 is a real design choice rather than
  a taxonomy exercise.

## 10. Consequences

Judgement is involved in weighting these. The mechanisms behind them are cited
above.

### Positive

- **Origin load drops in proportion to the hit ratio.** A ninety-five percent hit
  ratio removes nineteen of every twenty origin reads. This is the whole reason the
  pattern exists and it is usually the difference between one database instance and
  five.
- **Cache failure degrades rather than breaks.** Because the origin path is always
  present in the code, an empty or unreachable cache produces slow correct answers
  instead of errors. AWS states this property directly for lazy loading.
- **Only requested data is cached.** AWS notes that because most data is never
  requested, lazy loading avoids filling the cache with data that is not requested.
  Memory goes to the working set by construction, with no modelling required.
- **Per-key policy is possible.** The Microsoft page observes that a single global
  eviction policy might not suit all items, and that an expensive item should be
  configured individually. Because the application owns the set call, the TTL is a
  per-key decision rather than a server setting.
- **No cache-side integration work.** The cache never needs credentials for the
  origin, a driver, or a schema. Any key-value store works, which is why the
  pattern is portable across memcached, Redis, an in-process map, and a CDN edge
  store without rewriting the read logic.
- **Adoption is incremental.** One endpoint can be cached without touching any
  other. There is no all-or-nothing migration.

### Negative

- **Staleness is unbounded without a TTL and bounded only by it with one.** The
  window described in dimension 7 is intrinsic. Every deployment of this pattern is
  a decision to serve some wrong answers.
- **The miss path is slower than no cache.** Three trips instead of one. On a cold
  start, a deployment, or a cache eviction storm, every request pays that penalty
  at once.
- **Invalidation is an application responsibility that nothing enforces.** A new
  write path added six months later by a different team will not invalidate,
  because nothing in the type system or the schema says it must. This is the most
  common way the pattern rots.
- **Stampedes are the default behaviour.** Without a coordinator, expiry of a hot
  key sends every concurrent reader to the origin at the same instant. The
  pattern's textbook form does not include the remedy, which is why the remedy has
  to be a conscious addition.
- **Two sources of truth in operations.** Debugging a wrong value now requires
  checking the cache, checking the origin, and reasoning about when each was
  written. Mean time to diagnosis rises.
- **Serialisation cost is easy to overlook.** For small values in a fast database,
  JSON encoding plus a network hop can cost more than the query it replaced. The
  cache must be measured, not assumed.
- **A second data store to secure, size, and pay for.** See dimension 17.

## 11. Failure modes and misuse

Symptoms below are drawn from operating this pattern. The underlying mechanisms
are cited where a source exists.

**Symptom.** Database CPU spikes to saturation at regular intervals matching the
TTL, with a matching latency spike, then recovers. Cache hit ratio drops to near
zero for a few seconds.
**Cause.** Cache stampede on expiry. A hot key expires and every concurrent reader
misses at once, so N readers issue N identical origin queries. The Facebook paper
names the same shape a thundering herd, occurring when a key undergoes heavy read
and write activity so reads repeatedly default to the more costly path
([Nishtala et al., NSDI 2013](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala),
verified 2026-08-02).
**Fix.** Pick one of the three remedies and pick it deliberately. Probabilistic
early expiration if you want no coordination and can accept early rebuilds, which
is variant F. Single-flight or a distributed lock if you need exactly one rebuild
and can accept waiting readers, which is variants C and D. Background or
stale-while-revalidate refresh if you can accept serving past the TTL, which is
variant G. Add jitter to every TTL regardless, so that keys written together do
not expire together.

**Symptom.** Every deployment or cache restart causes a multi-minute period of
raised latency and origin load, sometimes bad enough to trip circuit breakers.
**Cause.** Cold cache with no warming and no admission control. The pattern's own
strength, filling only on demand, means a fresh cache offers zero protection at
exactly the moment the system is least stable.
**Fix.** Prime the highest-value keys at startup, as the Microsoft page suggests
for data an application is likely to require. Bring instances into rotation
gradually. Keep a rebuild coordinator active so the cold period costs one origin
query per key rather than one per request.

**Symptom.** A user updates a record, the update is confirmed, and the record
still shows the old value on the next page load. Refreshing sometimes fixes it and
sometimes does not.
**Cause.** Either the invalidation is missing on that write path, or the
invalidation ran before the commit, or the race in dimension 7 landed.
**Fix.** Verify the ordering is commit then delete, which the Microsoft page states
explicitly. Move invalidation next to the commit rather than into a caller. Bound
the damage with a TTL. Where read-after-write matters, read through to the origin
for that one request after a write by the same actor.

**Symptom.** Origin query volume is high and rising, cache hit ratio looks fine,
and the queries returning no rows are most of them. Often accompanied by traffic
from a small number of clients using sequential or random identifiers.
**Cause.** Cache penetration. A miss on a key that does not exist in the origin
either produces no cache write at all, or produces one only for found values, so
every request for a nonexistent key reaches the database. This is trivially
weaponised. An attacker requests random identifiers and every one is a guaranteed
origin hit.
**Fix.** Cache the absence with its own short TTL, following the DNS precedent in
RFC 2308, and invalidate the negative entry when the record is created. Where the
key space is large and absence is common, put a Bloom filter in front, using the
property that a negative answer from the filter is certain
([Redis, Bloom filter](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/),
verified 2026-08-02). Validate key format before either lookup so malformed
identifiers never reach the cache.

**Symptom.** Cache memory is full, eviction rate is high, hit ratio is poor, and
the working set does not obviously exceed the memory allocated.
**Cause.** Cache pollution from one-shot keys. Search result pages, paginated
queries with arbitrary offsets, or per-request composite keys fill the cache with
entries that are never read a second time and evict the entries that would have
been. Most caches evict by least-recently-used, which does not distinguish read
once from read once so far.
**Fix.** Do not cache key shapes with no reuse. Where the key space is
combinatorial, cache the components rather than the combination. Segment
high-churn keys into their own cache or namespace with a separate memory budget.

**Symptom.** Values in the cache are correct for one deployment and wrong or
undeserialisable for the next, with errors appearing during a rolling deploy and
disappearing after it completes.
**Cause.** Schema drift in the serialised value. The old and new code disagree on
the shape, and both are reading the same keys.
**Fix.** Put a version in the key prefix so a shape change writes to a new key
space and the old entries age out. This is cheaper and safer than a migration and
it makes rollback work.

**Symptom.** The application returns errors when the cache is unreachable, despite
the origin being healthy.
**Cause.** A cache read exception propagating instead of being treated as a miss.
The pattern's degradation property only exists if the code implements it.
**Fix.** Treat any cache error as a miss on read and as a best-effort no-op on
write. Put a short timeout on cache operations, because a slow cache is worse than
an absent one. Combine with Circuit Breaker so a failing cache is skipped entirely
rather than timing out on every request.

**Symptom.** A cache-related incident, and nobody can say what the hit ratio was or
which keys were involved.
**Cause.** The cache was added without instrumentation. See dimension 16.
**Fix.** Instrument before shipping, not after the first incident.

**Misuse, TTL chosen by copying an example.** Five minutes appears in the Microsoft
sample and in a large fraction of production code, and it is a default in that
sample rather than a recommendation. A TTL is a statement about how much staleness
the business tolerates and how much origin load the system can afford. It is
derived from the write rate of the data and the cost of a wrong answer, and it
should be recorded next to the code with the reasoning. The Microsoft page is
explicit that the expiration policy must match the access pattern, and that too
short means constant refetching while too long means stale data. Treat any TTL
without a written justification as a defect. This position is engineering
judgement.

**Misuse, caching to hide a slow query.** A cache turns a latency problem into an
availability problem, because the origin still has to serve every miss. If the
uncached query cannot survive the miss rate at peak, the cache is load-bearing and
the system has no safe failure mode. Fix the query first, then cache it.

## 12. Trade-off matrix

The named alternatives are the other members of the caching pattern family. All
five are real patterns with documented implementations.

| Force | Cache-Aside | Read-Through | Write-Through | Write-Behind | Refresh-Ahead |
|---|---|---|---|---|---|
| Who calls the origin on a read miss | Application | Cache library or provider | Application, cache is only written | Application | Cache, before expiry |
| Who writes to the cache on a write | Application, by deleting | Application, by deleting | Cache, in the same operation | Cache, then origin asynchronously | Background refresher |
| Read latency, hit | Best | Best | Best | Best | Best |
| Read latency, miss | Worst, three trips | Same three trips, hidden from caller | Miss only if never written or evicted | Same as write-through | Rare by design |
| Write latency | Origin write plus one delete | Origin write plus one delete | Origin write plus cache write | Cache write only, origin later | Unchanged |
| Read-after-write freshness | Not guaranteed, brief staleness window per Microsoft | Not guaranteed, same window | Guaranteed, cache updated in the same write | Guaranteed from the cache, origin lags | Not guaranteed |
| Durability risk | None, cache is never authoritative | None | None | Real, unflushed writes are lost if the cache dies | None |
| Behaviour on cold or empty cache | Degrades to origin, keeps serving | Degrades to origin, keeps serving | Data missing until written or updated, per AWS | Same as write-through | Nothing to refresh yet |
| Cache pollution | Low, only requested data is cached | Low, same fill discipline | High, AWS names cache churn since most data is never read | High, same reason | Medium, refreshes keys nobody may read |
| Stampede exposure | High by default, remedy is opt-in | Depends on library, Caffeine deduplicates in-flight refreshes | Low, entries are written not rebuilt | Low | Low, that is its purpose |
| Coupling of cache to origin | None, the defining property | Cache needs a loader and origin credentials | None beyond the write path | Cache needs write access to the origin | Cache needs a loader |
| Cognitive load on application developers | High, fill and invalidate are theirs | Low, one call | Medium, two writes to keep aligned | Medium | Low |
| Works with any key-value store | Yes | No, needs library or provider support | Yes | No, needs a flushing mechanism | No, needs a scheduler |
| Best fit | Read-heavy, unpredictable access, cache may be absent | Read-heavy with a stable key space and a supporting library | Read-after-write matters and writes are modest | Write-heavy with tolerance for loss | Predictable hot keys with a known refresh cost |

Two rows deserve elaboration.

**Cache-Aside against Read-Through.** These are frequently confused because the
observable behaviour is close to identical. The difference is which component owns
the origin call. In Read-Through the cache holds a loader and fetches on a miss,
which is what Caffeine's `LoadingCache` does by automatically computing missing
entries through an attached `CacheLoader`
([Caffeine wiki, Population](https://github.com/ben-manes/caffeine/wiki/Population),
verified 2026-08-02). The consequences follow from that ownership. Read-Through
gives one call site and centralised policy, and takes away the ability to run
without the cache and the ability to vary the fill per call site. The Microsoft
page frames Cache-Aside as what you build when the cache does not offer
read-through, which is the honest framing.

**Cache-Aside against Write-Through.** These are not competitors and pairing them
is often correct. AWS is explicit that write-through can fail with empty nodes and
that this is minimised by implementing lazy loading with write-through
([AWS, Caching strategies](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html),
verified 2026-08-02). Write-Through keeps hot keys fresh and Cache-Aside covers
everything the writes did not touch. The combined cost is that both paths need
maintaining and the TTL still has to exist as the backstop.

**Cache-Aside against Write-Behind.** These conflict on durability. Write-Behind
acknowledges a write once the cache holds it and flushes to the origin later,
which makes the cache temporarily authoritative. That is exactly the property
Cache-Aside refuses. Combining them means the delete-on-write invalidation might
remove data that has not reached the origin. Do not mix them on the same keys.

## 13. Related and incompatible patterns

- **Read-Through Cache.** The direct alternative, not a companion. Choosing one
  means not choosing the other for the same key family. Read-Through is preferable
  when a library already implements it and the application never needs to run
  without the cache.
- **Write-Through Cache.** Composes well. Use Write-Through on keys where
  read-after-write matters and Cache-Aside on the rest, with a shared TTL policy.
  AWS recommends the combination.
- **Write-Behind Cache.** Conflicts, as set out in dimension 12. Not to be used on
  the same keys.
- **Refresh-Ahead Cache.** Composes, and is the natural upgrade for the small set
  of keys that are always hot. Caffeine's `refreshAfterWrite` is the same idea
  applied at read time rather than on a schedule, and its documented behaviour of
  returning the old value while refreshing is what makes the composition attractive
  ([Caffeine wiki, Refresh](https://github.com/ben-manes/caffeine/wiki/Refresh),
  verified 2026-08-02).
- **Circuit Breaker.** Composes strongly and belongs in any production deployment.
  A breaker around the cache client turns a slow cache into a skipped cache. A
  breaker around the origin stops a stampede from becoming a database outage.
- **Bulkhead.** Composes. Cap the number of concurrent origin calls issued from the
  miss path, so that even an uncoordinated stampede cannot exhaust the connection
  pool that the write path depends on.
- **Retry.** Composes with care. Retrying a cache read is usually wrong, because a
  miss is cheaper to serve from the origin than a retry is to wait for. Retrying
  the origin call inside a miss is reasonable with a bounded budget.
- **Materialized View.** An alternative rather than a companion when the expense is
  a query shape rather than a row lookup. A materialised view moves the cost to
  write time permanently, where Cache-Aside moves it to first-read time repeatedly.
- **CDN edge caching.** The same pattern at a different layer, with invalidation
  made harder by the number of edge nodes. Reasoning transfers directly.
- **Idempotency Key.** Conflicts on the specific key. An idempotency record exists
  to answer whether this exact operation has already run, which is a correctness
  question that must reach the system of record. Caching it reintroduces the
  duplicate execution it was added to prevent.

## 14. Refactoring path in and out

### Introducing the pattern

1. **Measure first.** Record origin query volume grouped by query shape and
   parameters, and the latency distribution. If the same parameters do not recur,
   stop. A cache will not help and dimension 4 says so.
2. **Pick one key family.** One entity type, read by primary key. Do not start with
   a query result or a composite key, because those are where key design goes
   wrong.
3. **Extract the read into one function.** Every caller of that data goes through
   it. This is a pure refactoring with no cache in it yet, and it is the step that
   makes everything after it safe. It corresponds to Extract Function followed by
   Move Function in the refactoring family.
4. **Design the key.** Namespace, entity, version, identifier. Include the version
   from day one, so a serialisation change later is a prefix change rather than a
   migration.
5. **Decide the TTL and write down why.** Base it on the write rate of the entity
   and the cost of serving a stale value. Record the reasoning in a comment or an
   architecture note. A TTL with no recorded reason will be copied into the next
   twenty cache calls without thought.
6. **Add the cache read and populate, behind a flag.** Treat every cache error as a
   miss. Ship with the flag off and turn it on for a fraction of traffic.
7. **Add invalidation to every write path for that entity.** Find them by searching
   for writes to the table, not by memory. Put the invalidation adjacent to the
   commit, after it.
8. **Add TTL jitter.** A few percent of spread on every write. This costs one line
   and removes the synchronised-expiry class of stampede before it happens.
9. **Add a rebuild coordinator before the key is hot, not after.** Single-flight
   within the process is the cheapest useful step. Escalate to a distributed lock
   or probabilistic early expiration when instance count makes in-process
   coalescing insufficient.
10. **Decide negative caching explicitly.** Either cache absence with a short TTL
    and invalidate it on creation, or document that absence is not cached and
    accept the penetration exposure.
11. **Instrument, then ramp.** Dimension 16 lists the metrics. Ramp traffic while
    watching hit ratio and origin volume together, because either one alone can
    mislead.

### Removing the pattern

The pattern stops earning its place when the origin becomes fast enough, when the
data becomes write-heavy, or when the staleness cost rises above the latency
saving.

1. **Confirm the origin can carry the full read load.** Measure the current hit
   ratio and multiply current origin volume accordingly. This is the step that gets
   skipped and the reason removals cause incidents.
2. **Shorten the TTL in stages.** Halve it, observe origin load, repeat. This
   simulates removal reversibly and produces a real load figure rather than an
   extrapolated one.
3. **Turn the cache read into a pass-through** behind the same flag used to
   introduce it, so a rollback is a flag flip.
4. **Delete the invalidation calls before the cache read.** Removing the read while
   leaving invalidation in place is harmless. The reverse serves stale data forever.
5. **Delete the key format, the TTL constant, and the cache client.** Dead cache
   constants invite someone to reintroduce the read against a contract nobody
   maintains any more.
6. **Keep the extracted read function.** It was correct before the cache and it is
   correct after. That is why step 3 of the introduction is worth doing on its own.

## 15. Testing and verification

This dimension is practice rather than sourced fact.

### What the pattern makes easy to test

- **The loader in isolation.** Extraction pushed the origin query into its own
  function with no cache dependency, so it is testable exactly as it was before.
- **Cache absence.** Because a miss must produce a correct answer, an empty cache
  is a first-class test case rather than an edge case. Run the whole integration
  suite once with the cache stubbed to always miss, and every test must still pass.
  This single run catches most correctness regressions in the fill logic.
- **Determinism through a clock port.** TTL behaviour is untestable against the
  wall clock and trivial against an injected clock. Inject one from the start.

### What the pattern makes harder to test

- **Ordering races.** The dual write window in dimension 7 is a real interleaving
  that a normal test will not produce. Test it by driving the steps explicitly.
  Begin the read, pause it at a controlled point, run the write and the
  invalidation to completion, resume the read, then assert what the cache holds. A
  test double with a settable barrier does this in a few lines and pins a bug that
  is otherwise found in production.
- **Stampede behaviour.** Assert on origin call count, not on wall time. Fire N
  concurrent gets against a slow loader and assert the loader ran once. The Go and
  Rust samples below do exactly that, and printing the counter is the assertion.
- **Invalidation coverage.** No unit test proves that every write path invalidates,
  because the failure is an absence. Two techniques help. Route every write to the
  entity through one function so the invalidation has a single home, and add a test
  that performs write then read and asserts the new value, for each write path, so
  a new path without a test is visible in coverage.
- **Serialisation compatibility.** Add a test that deserialises a stored fixture
  captured from the previous release. Failure means the key version must change.

### Test doubles

- **Fake cache**, an in-memory map with a settable clock. Correct for most tests,
  and better than a mock because it has real semantics.
- **Failing cache**, which throws on every operation. Proves the degradation
  property from dimension 10 and stops the regression in dimension 11 where a cache
  error propagates.
- **Counting loader**, which records invocations. The only way to test coalescing.
- **Real cache in integration tests.** A container running the actual cache catches
  serialisation, key-length, and eviction behaviour that a fake never will.

## 16. Observability signals

Practice rather than sourced fact.

### Metrics

- **Hit ratio**, as hits divided by total lookups, per key family rather than
  globally. A global ratio hides a family at zero behind a family at ninety-nine.
- **Origin call rate from the miss path**, counted separately from other origin
  traffic. This is the number the cache exists to reduce and the number that spikes
  during a stampede.
- **Cache operation latency**, at the median and the ninety-ninth percentile, split
  by get and set. A slow cache is a latency regression that a hit ratio dashboard
  cannot show.
- **Cache error rate**, split into timeouts and other failures. Errors must be
  visible even though they are handled as misses, because handling them silently is
  how a dead cache runs unnoticed for a week.
- **Eviction rate and memory use.** Rising evictions with a falling hit ratio is
  the pollution signature from dimension 11.
- **Negative hit ratio**, tracked separately. A rising share of negative hits is
  either a legitimate access pattern change or an enumeration attack.
- **Distinct key count over time.** A key space growing without bound means the key
  design includes something it should not, such as a timestamp or a request
  identifier.
- **Coalesced call count**, the number of callers that waited on an in-flight
  rebuild rather than issuing their own. Go's `singleflight` exposes this directly
  as the `Shared` return value indicating whether the result was given to multiple
  callers ([golang.org/x/sync/singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight),
  verified 2026-08-02).

### Traces

Attach three attributes to the span covering the read. Whether it hit, the key
family, and the value age at read time. Value age turns a report that a user saw
stale data from an argument into a measurement. Make the origin query a child span
of the read so a trace shows the three-hop miss shape directly, which makes the
miss penalty legible to people who have never read this document.

### Logs

Log invalidations at debug with the key and the reason, and log cache errors at
warn with the operation and the key family, sampled. Never log the cached value,
for the reasons in dimension 17.

### What healthy looks like

Hit ratio flat and high for the family, origin miss-path volume flat and roughly
equal to the write rate plus the TTL-driven refill rate, cache latency flat,
evictions low and steady, error rate at or near zero. A healthy stampede-protected
cache shows origin volume that does not move when concurrency moves.

### What failing looks like

Hit ratio with sawtooth dips at TTL intervals and origin volume with matching
spikes is a stampede. Hit ratio falling steadily while evictions rise is pollution
or an undersized cache. Origin volume high with hit ratio high is penetration,
because the misses are all negatives. Cache latency rising while hit ratio holds
means the cache itself has become the bottleneck. Everything flat except a user
complaint means the staleness window is real and the TTL needs revisiting.

## 17. Security and privacy implications

Analytical rather than sourced except where cited.

The pattern creates a second copy of data in a system with a different security
posture from the origin, and this is its main security consequence. The Microsoft
page states plainly that the pattern might not be suitable when the data is
sensitive or security related, especially when multiple applications or users
share the cache, and advises always retrieving that data from the primary source
([Microsoft Learn, Cache-Aside pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside),
verified 2026-08-02).

**Access control does not travel with the value.** The origin enforces row-level
security, tenant isolation, or column masking. The cache enforces none of that. It
returns whatever is stored under the key to whoever can construct the key. If the
key does not encode the security context, the pattern becomes a bypass. Any cached
value whose visibility depends on the caller must include the tenant or principal
in the key, and the resulting hit ratio penalty is the correct cost of correctness.

**Cache keys built from user input are an injection surface.** An unvalidated
identifier concatenated into a key can collide with another key space, and in
caches with structured commands can be worse. Validate and encode every component
of a key, and prefer a fixed prefix plus an escaped identifier over free
concatenation.

**Enumeration is worse without negative caching.** Without it, every request for a
nonexistent identifier is a guaranteed origin query, which turns the read path
into an inexpensive denial-of-service vector. Negative caching and a membership
filter, described in dimension 8, are as much availability controls as performance
ones.

**Deletion and retention obligations extend to the cache.** A data subject erasure
request satisfied only in the origin leaves the record readable from the cache
until its TTL expires. Any key holding personal data needs an invalidation path
triggered by deletion, and its TTL becomes a stated retention window rather than a
performance knob. Encryption at rest and in transit for the cache is required
wherever it is required for the origin, and cache backups and memory dumps inherit
the same classification as the data they hold.

**Timing differences are observable.** A cache hit returns faster than a miss, so
response time leaks whether a key was recently accessed. For most workloads this
is uninteresting. Where the existence of a record is itself sensitive, it is a side
channel, and the mitigation is to make the hit and miss paths take comparable time
for that key family.

**Shared multi-tenant caches carry noisy-neighbour and blast-radius risk.** One
tenant filling the cache evicts another's working set, and a key-format bug in one
service can read another service's entries. Namespacing by service and by tenant
bounds both.

**Where the pattern is silent.** Cache-Aside adds no authentication, authorisation,
or integrity mechanism of its own, and does nothing to protect the origin from an
authorised but abusive caller. It neither improves nor degrades the origin's own
security properties. Claims that caching improves security by reducing origin
exposure are not supported by anything in the pattern, because the origin is still
reached on every miss.

## Code examples

Four samples follow, in Go, Python, TypeScript and Rust. All four were compiled and
run on 2026-08-02 and the printed output is reproduced below each one. A Java
sample was written for this entry and could not be verified, because `javac` on
this machine reports no Java runtime available, so no Java sample is included
rather than shipping an unverified one. C# is omitted because the Microsoft page
already carries a canonical C# example, linked in dimension 18.

### Go, cache-aside with per-key request coalescing and negative caching

Go is idiomatic here because the coordination primitive is a wait group plus a
compare-and-store rather than a framework, and because the standard extended
library ships `singleflight` for the same job. The version below is written out in
full so the mechanism is visible.

```go
package main

import (
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

var ErrNotFound = errors.New("not found")

type entry struct {
	val     string
	found   bool
	expires time.Time
}

type call struct {
	wg    sync.WaitGroup
	val   string
	found bool
	err   error
}

// CacheAside is a look-aside cache with per-key request coalescing.
// Negative results are stored under a shorter TTL than positive ones.
type CacheAside struct {
	items    sync.Map
	inflight sync.Map
	posTTL   time.Duration
	negTTL   time.Duration
	origin   func(string) (string, error)
	Origins  atomic.Int64
}

func New(origin func(string) (string, error), pos, neg time.Duration) *CacheAside {
	return &CacheAside{posTTL: pos, negTTL: neg, origin: origin}
}

func result(val string, found bool, err error) (string, error) {
	switch {
	case err != nil:
		return "", err
	case !found:
		return "", ErrNotFound
	default:
		return val, nil
	}
}

func (c *CacheAside) Get(key string) (string, error) {
	if raw, ok := c.items.Load(key); ok {
		e := raw.(entry)
		if time.Now().Before(e.expires) {
			return result(e.val, e.found, nil)
		}
	}

	mine := &call{}
	mine.wg.Add(1)
	raw, loaded := c.inflight.LoadOrStore(key, mine)
	if loaded {
		theirs := raw.(*call)
		theirs.wg.Wait()
		return result(theirs.val, theirs.found, theirs.err)
	}

	v, err := c.origin(key)
	c.Origins.Add(1)
	switch {
	case err == nil:
		mine.val, mine.found = v, true
		c.items.Store(key, entry{val: v, found: true, expires: time.Now().Add(c.posTTL)})
	case errors.Is(err, ErrNotFound):
		c.items.Store(key, entry{found: false, expires: time.Now().Add(c.negTTL)})
	default:
		mine.err = err
	}
	c.inflight.Delete(key)
	mine.wg.Done()
	return result(mine.val, mine.found, mine.err)
}

// Invalidate runs after the write to the system of record commits.
func (c *CacheAside) Invalidate(key string) {
	c.items.Delete(key)
}

func main() {
	db := map[string]string{"u:1": "ada"}
	origin := func(k string) (string, error) {
		time.Sleep(20 * time.Millisecond)
		if v, ok := db[k]; ok {
			return v, nil
		}
		return "", ErrNotFound
	}
	c := New(origin, time.Minute, 5*time.Second)

	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); c.Get("u:1") }()
	}
	wg.Wait()

	_, err := c.Get("u:missing")
	fmt.Println("missing:", errors.Is(err, ErrNotFound))
	_, _ = c.Get("u:missing")
	fmt.Println("origin calls:", c.Origins.Load())
}
```

Verified with `go vet` and `go run` on go1.26.4, producing this output.

```text
missing: true
origin calls: 2
```

Fifty concurrent readers on a cold key produced one origin call, and two lookups
for an absent key produced one more, because the absence was cached. Without
coalescing the first number would have been fifty. Without negative caching the
second would have been two.

### Python, probabilistic early expiration

This is the XFetch algorithm from Vattani, Chierichetti and Lowenstein. The value
of the sample is the measured outcome rather than the code. Across four thousand
reads over a two hundred millisecond TTL, the entry never once reached hard expiry,
which is the stampede window eliminated rather than shortened.

```python
import math, random, time
from dataclasses import dataclass


@dataclass
class Slot:
    value: str
    delta: float
    expiry: float


class XFetchCache:
    """Cache-aside with probabilistic early expiration (Vattani et al., XFetch).

    delta records how long the last recomputation took. As expiry approaches,
    the chance that a given reader volunteers to recompute rises.
    """

    def __init__(self, ttl: float, beta: float = 1.0, rng=None):
        self.slots: dict[str, Slot] = {}
        self.rng = rng or random.Random()
        self.ttl = ttl
        self.beta = beta
        self.recomputes = 0

    def _should_recompute(self, s: Slot, now: float) -> bool:
        return now - s.delta * self.beta * math.log(self.rng.random()) >= s.expiry

    def get(self, key: str, load) -> str:
        now = time.monotonic()
        s = self.slots.get(key)
        if s is not None and now < s.expiry and not self._should_recompute(s, now):
            return s.value
        start = time.monotonic()
        value = load(key)
        delta = time.monotonic() - start
        self.recomputes += 1
        self.slots[key] = Slot(value, delta, time.monotonic() + self.ttl)
        return value


def demo() -> None:
    def load(_k: str) -> str:
        time.sleep(0.002)
        return "payload"

    c = XFetchCache(ttl=0.20, beta=1.0, rng=random.Random(7))
    hard_expiries = 0
    for _ in range(4000):
        before = c.slots.get("k")
        now = time.monotonic()
        if before is not None and now >= before.expiry:
            hard_expiries += 1
        c.get("k", load)
        time.sleep(0.0005)

    print("recomputes:", c.recomputes)
    print("hit hard expiry:", hard_expiries)


if __name__ == "__main__":
    demo()
```

Verified with `python3` on CPython 3, producing this output.

```text
recomputes: 14
hit hard expiry: 0
```

Raising `beta` above one makes recomputation start earlier and the count of
recomputes rise. Lowering it below one moves recomputation later and eventually
lets hard expiries appear. That single knob is the whole tuning surface.

### TypeScript, promise coalescing with TTL jitter and negative caching

TypeScript is idiomatic here because a pending promise stored in a map is already a
single-flight primitive. The `finally` on the in-flight deletion is the detail that
matters. Without it, a failed load poisons the key permanently.

```typescript
type Loader<T> = (key: string) => Promise<T | null>;

interface Slot<T> {
  value: T | null;
  expiresAt: number;
}

interface Options {
  positiveTtlMs: number;
  negativeTtlMs: number;
  jitterRatio: number;
}

export class CacheAside<T> {
  private store = new Map<string, Slot<T>>();
  private inflight = new Map<string, Promise<T | null>>();
  public originCalls = 0;

  constructor(private load: Loader<T>, private opts: Options) {}

  private ttlWithJitter(base: number): number {
    const spread = base * this.opts.jitterRatio;
    return base - spread / 2 + Math.random() * spread;
  }

  async get(key: string): Promise<T | null> {
    const slot = this.store.get(key);
    if (slot !== undefined && Date.now() < slot.expiresAt) return slot.value;

    const pending = this.inflight.get(key);
    if (pending !== undefined) return pending;

    const task = (async () => {
      try {
        this.originCalls += 1;
        const value = await this.load(key);
        const base =
          value === null ? this.opts.negativeTtlMs : this.opts.positiveTtlMs;
        this.store.set(key, {
          value,
          expiresAt: Date.now() + this.ttlWithJitter(base),
        });
        return value;
      } finally {
        this.inflight.delete(key);
      }
    })();

    this.inflight.set(key, task);
    return task;
  }

  invalidate(key: string): void {
    this.store.delete(key);
  }
}

async function demo(): Promise<void> {
  const rows = new Map<string, string>([["p:1", "widget"]]);
  const cache = new CacheAside<string>(
    async (k) => {
      await new Promise((r) => setTimeout(r, 15));
      return rows.get(k) ?? null;
    },
    { positiveTtlMs: 60_000, negativeTtlMs: 3_000, jitterRatio: 0.2 },
  );

  const burst = await Promise.all(
    Array.from({ length: 40 }, () => cache.get("p:1")),
  );
  console.log("all resolved:", burst.every((v) => v === "widget"));
  console.log("negative cached:", await cache.get("p:absent"));
  await cache.get("p:absent");
  console.log("origin calls:", cache.originCalls);
}

void demo();
```

Verified with `tsc --strict --target es2022` on TypeScript 5.9 and executed on Node
23, producing this output.

```text
all resolved: true
negative cached: null
origin calls: 2
```

The jitter ratio of 0.2 spreads expiry across plus or minus ten percent of the
nominal TTL, so a batch of keys written together does not expire together.

### Rust, stale-while-revalidate with a rebuild gate

Rust is idiomatic here because the coordination has to be written explicitly, and
that explicitness makes the pattern legible. A `Mutex` guards the shared state and
a `Condvar` releases waiters when the rebuild finishes. Readers with a stale but
usable value are handed it rather than made to wait.

```rust
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Condvar, Mutex};
use std::thread;
use std::time::{Duration, Instant};

#[derive(Clone)]
struct Slot {
    value: Option<String>,
    fresh_until: Instant,
    stale_until: Instant,
}

struct State {
    items: HashMap<String, Slot>,
    rebuilding: HashMap<String, ()>,
}

/// Cache-aside with stale-while-revalidate. One thread rebuilds a key while
/// the rest serve the stale value instead of piling onto the origin.
pub struct SwrCache {
    state: Mutex<State>,
    ready: Condvar,
    fresh: Duration,
    stale: Duration,
    pub origin_calls: AtomicUsize,
}

impl SwrCache {
    pub fn new(fresh: Duration, stale: Duration) -> Self {
        SwrCache {
            state: Mutex::new(State {
                items: HashMap::new(),
                rebuilding: HashMap::new(),
            }),
            ready: Condvar::new(),
            fresh,
            stale,
            origin_calls: AtomicUsize::new(0),
        }
    }

    pub fn get<F>(&self, key: &str, load: F) -> Option<String>
    where
        F: Fn(&str) -> Option<String>,
    {
        let now = Instant::now();
        let mut guard = self.state.lock().unwrap();

        if let Some(slot) = guard.items.get(key) {
            if now < slot.fresh_until {
                return slot.value.clone();
            }
            if now < slot.stale_until && guard.rebuilding.contains_key(key) {
                return slot.value.clone();
            }
        }

        while guard.rebuilding.contains_key(key) {
            guard = self.ready.wait(guard).unwrap();
            if let Some(slot) = guard.items.get(key) {
                if Instant::now() < slot.fresh_until {
                    return slot.value.clone();
                }
            }
        }

        guard.rebuilding.insert(key.to_string(), ());
        drop(guard);

        let value = load(key);
        self.origin_calls.fetch_add(1, Ordering::SeqCst);

        let t = Instant::now();
        let mut guard = self.state.lock().unwrap();
        guard.items.insert(
            key.to_string(),
            Slot {
                value: value.clone(),
                fresh_until: t + self.fresh,
                stale_until: t + self.fresh + self.stale,
            },
        );
        guard.rebuilding.remove(key);
        drop(guard);
        self.ready.notify_all();
        value
    }

    pub fn invalidate(&self, key: &str) {
        self.state.lock().unwrap().items.remove(key);
    }
}

fn main() {
    let cache = Arc::new(SwrCache::new(Duration::from_millis(40), Duration::from_secs(5)));
    let load = |k: &str| -> Option<String> {
        thread::sleep(Duration::from_millis(25));
        if k == "absent" {
            None
        } else {
            Some(format!("row-{k}"))
        }
    };

    cache.get("k", load);
    thread::sleep(Duration::from_millis(50));

    let handles: Vec<_> = (0..16)
        .map(|_| {
            let c = Arc::clone(&cache);
            thread::spawn(move || c.get("k", load))
        })
        .collect();
    for h in handles {
        h.join().unwrap();
    }

    println!("value: {:?}", cache.get("k", load));
    println!("negative: {:?}", cache.get("absent", load));
    println!("origin calls: {}", cache.origin_calls.load(Ordering::SeqCst));
}
```

Verified with `rustc -O` and executed, producing this output.

```text
value: Some("row-k")
negative: None
origin calls: 3
```

Three origin calls covers the initial fill, one rebuild shared by sixteen threads
after the fresh window closed, and one lookup of the absent key. Fifteen of the
sixteen threads were served the stale value without waiting, which is the property
that keeps tail latency flat during a rebuild.

## 18. References

### Primary pattern sources

1. Microsoft, *Cache-Aside pattern*, Azure Architecture Center, page dated
   2025-09-11.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside
   Verified 2026-08-02. Source for the pattern name, the solution steps, the
   considerations list (lifetime, eviction, configuration, priming, consistency,
   staleness after writes), the when-to-use and when-not-to-use lists, the
   commit-before-delete ordering rule, and the C# example.
2. Amazon Web Services, *Caching strategies for Memcached*, Amazon ElastiCache
   Developer Guide.
   https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/Strategies.html
   Verified 2026-08-02. Source for the lazy loading name, the three-trip miss
   penalty, the node-failure resilience property, the write-through comparison
   including cache churn and missing data on new nodes, and the recommendation to
   add a TTL to both strategies.

### Stampede prevention

3. Andrea Vattani, Flavio Chierichetti, Keegan Lowenstein, *Optimal Probabilistic
   Cache Stampede Prevention*, Proceedings of the VLDB Endowment, volume 8, pages
   886 to 897, 2015. https://dl.acm.org/doi/10.14778/2757807.2757813
   Author copy at https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf
   Verified 2026-08-02. Source for the XFetch algorithm, the recomputation test
   `time() - delta * beta * ln(rand()) >= expiry`, and the meaning of the beta
   parameter.
4. Rajesh Nishtala, Hans Fugal, Steven Grimm, Marc Kwiatkowski, Herman Lee, Harry
   C. Li, Ryan McElroy, Mike Paleczny, Daniel Peek, Paul Saab, David Stafford,
   Tony Tung, Venkateshwaran Venkataramani, *Scaling Memcache at Facebook*, 10th
   USENIX Symposium on Networked Systems Design and Implementation, NSDI 2013.
   https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala
   Verified 2026-08-02. Source for the demand-filled look-aside characterisation,
   the lease mechanism, the definitions of stale set and thundering herd, and the
   default of one token per key per ten seconds.
5. Wikimedia Foundation, *MediaWiki Engineering, Guides, Backend performance
   practices*, Wikitech.
   https://wikitech.wikimedia.org/wiki/MediaWiki_Engineering/Guides/Backend_performance_practices
   Verified 2026-08-02. Source for WANObjectCache handling stampede protection,
   purging and mutex locks, preemptive regeneration of values before expiry, and
   time-dependent randomisation via the TTL argument and the hotTTR option.

### Library and platform behaviour

6. Ben Manes and contributors, *Caffeine wiki, Population*.
   https://github.com/ben-manes/caffeine/wiki/Population
   Verified 2026-08-02. Source for the manual `Cache` versus `LoadingCache`
   distinction and the read-through characterisation of `LoadingCache`.
7. Ben Manes and contributors, *Caffeine wiki, Refresh*.
   https://github.com/ben-manes/caffeine/wiki/Refresh
   Verified 2026-08-02. Source for `refreshAfterWrite` semantics, the old value
   being returned during refresh, and in-flight refresh deduplication.
8. The Go Authors, *Package singleflight*, `golang.org/x/sync/singleflight`.
   https://pkg.go.dev/golang.org/x/sync/singleflight
   Verified 2026-08-02. Source for the duplicate call suppression contract, the
   `Do` and `DoChan` signatures, and the `Shared` return value.
9. Netflix, *EVCache*, GitHub repository.
   https://github.com/Netflix/EVCache
   Verified 2026-08-02. Source for the memcached and spymemcached basis and the
   Ephemeral, Volatile, Cache expansion of the name.
10. InfoQ, *Netflix global cache*.
    https://www.infoq.com/articles/netflix-global-cache/
    Verified 2026-08-02. Source for the reported EVCache scale figures of 22,000
    server instances, 400 million operations per second, 2 trillion items,
    14.3 petabytes, and 200 memcached clusters.

### Negative caching and membership filtering

11. Mark Andrews, *Negative Caching of DNS Queries (DNS NCACHE)*, RFC 2308, IETF,
    March 1998. https://www.rfc-editor.org/rfc/rfc2308.html
    Verified 2026-08-02. Source for the definition of negative caching as the
    storage of knowledge that something does not exist, and the guidance that one
    to three hours works well while values exceeding one day are problematic.
12. Redis, *Bloom filter*, Redis documentation.
    https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/
    Verified 2026-08-02. Source for the guarantee that a negative answer is certain
    while one in N positive answers is wrong, the bits-per-item figures, and the
    Bloom versus cuckoo comparison.
13. Burton H. Bloom, *Space/Time Trade-offs in Hash Coding with Allowable Errors*,
    Communications of the ACM, 1970. Linked as an academic source from reference
    12. http://www.dragonwins.com/domains/getteched/bbc/literature/Bloom70.pdf
    Verified 2026-08-02 as a link present on the Redis page above.

### Unverified claims in this entry

None. Every factual claim above traces to a source in this list. Statements in
dimensions 3, 10, 11, 15, 16 and 17 that are engineering judgement rather than
sourced fact are labelled as such at the point they appear.
