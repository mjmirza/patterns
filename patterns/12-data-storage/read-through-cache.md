---
name: Read-Through Cache
slug: read-through-cache
family: 12-data-storage
category: Data and Storage
aliases: [Lazy Loading Cache, Cache-Aside with a Loader, Look-Aside Read-Through]
first_described: "Industry practice, no single canonical publication. Codified in caching-library APIs such as Guava CacheLoader (2011) and cache-provider documentation such as AWS ElastiCache Strategies"
maturity: canonical
related: [cache-aside, write-through-cache, write-behind-cache, circuit-breaker, proxy, decorator]
incompatible_with: []
verified: 2026-08-02
---

# Read-Through Cache

## 1. Name, aliases, and lineage

The canonical name in this catalog is Read-Through Cache. Unlike a Gang of Four
pattern, this one has no single paper of origin. It grew out of decades of
caching practice in database middleware, object-relational mapping layers, and
distributed caching products, and it was later given a fixed vocabulary by
cloud caching documentation and by caching library APIs.

Two related terms are used almost interchangeably in casual conversation, and
the distinction between them is the single most useful thing this entry can
establish early.

**Read-through, in the strict sense used by caching products.** The cache
itself, not the application, is responsible for loading a missing value from
the backing store. The application calls `cache.get(key)` and nothing else. If
the value is present the cache returns it. If it is absent the cache invokes a
loader function it was configured with, stores the result, and returns it. The
application code never contains an explicit if-miss-then-query-the-database
branch. Amazon ElastiCache documentation calls the application-visible variant
of this idea lazy loading, and describes the mechanism precisely as "Whenever
your application requests data, it first makes the request to the ElastiCache
cache. If the data exists in the cache and is current, ElastiCache returns the
data to your application. If the data doesn't exist in the cache or has
expired, your application requests the data from your data store" (Amazon Web
Services, "Caching strategies for Memcached", AWS documentation,
https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Strategies.html,
verified 2026-08-02). Notice that ElastiCache's own pseudocode still shows the
miss branch inside the application, which is the honest state of most
production Memcached and Redis deployments, because a plain key-value store has
no loader hook of its own. The name lazy loading is used for that
application-managed version, and read-through is reserved by the same industry
usage for the case where a caching library or a caching-aware ORM owns the
loader and hides the branch from the caller.

**Cache-Aside, the sibling pattern this one is constantly confused with.**
Cache-Aside is the same miss-then-populate flow written explicitly by the
application, with no caching product ever seeing the backing store. The two
sit on a spectrum of who owns the loader function, not two unrelated ideas.
This catalog treats Cache-Aside as its own entry and treats Read-Through Cache
as the variant where a library, framework, or managed cache owns the loading
logic behind a single `get` call. See dimension 13 for exactly where the line
falls and why it still matters even though many engineers use the two names
interchangeably in speech.

The vocabulary was made concrete for a generation of Java developers by Google
Guava's `CacheLoader` and `LoadingCache` classes, first released in Guava 10
(2011), whose Javadoc states that `CacheLoader` computes or retrieves values
"for use in populating a LoadingCache", and that a caller of
`LoadingCache.get(K)` receives an automatically computed or loaded value on a
miss (Google, Guava `CacheLoader` Javadoc, release 33.0.0-jre,
https://guava.dev/releases/33.0.0-jre/api/docs/com/google/common/cache/CacheLoader.html,
verified 2026-08-02). The same shape is exposed by Java's own `java.util.Map`
interface through `computeIfAbsent`, by Spring's `@Cacheable` annotation, and
by nearly every distributed cache product's cache-loader or read-through-
provider extension point, discussed in dimension 9.

## 2. Problem and context

An application reads the same piece of data far more often than the data
changes. The backing store that holds the authoritative copy, usually a
relational database, a remote API, or a slow computation, cannot sustain the
read volume at an acceptable latency or cost if every read goes straight to
it. The data does not need to be perfectly fresh on every single read, only
fresh enough for the use case, which is nearly always true for a product
catalog page, a user profile lookup, a configuration value, a permission
check, or a rendered fragment of a page.

The context in which this specific pattern, rather than a general "add a
cache" instinct, becomes the right answer has a recognisable shape. The
working set is large enough, or unpredictable enough, that pre-populating the
cache with everything is wasteful or impossible. The access pattern is
read-heavy relative to writes, so keeping the cache warm through reads is
cheaper than keeping it warm through writes. And critically, the loading logic
for a cache miss is non-trivial enough, spanning multiple call sites, multiple
teams, or multiple languages, that duplicating it at every call site (the
Cache-Aside shape) becomes its own maintenance burden. That last condition is
what specifically motivates centralising the loader inside the cache client or
the caching layer, which is the defining move of Read-Through Cache as
distinct from Cache-Aside.

A second common context is a managed caching product sitting in front of a
managed database, such as Amazon DynamoDB Accelerator (DAX) in front of
DynamoDB or Redis Enterprise's Auto Tiering in front of a primary store, where
the product itself, not application code, decides how to fetch on a miss. DAX
documentation frames its own value proposition around exactly this shape,
stating it "reduces the response times of eventually consistent read workloads
by an order of magnitude from single-digit milliseconds to microseconds" while
remaining API-compatible with the underlying store, and explicitly recommends
itself for "applications that require repeated reads against a large set of
data" and warns it is not ideal for "applications that are write-intensive"
(Amazon Web Services, "In-memory acceleration with DynamoDB Accelerator
(DAX)", DynamoDB Developer Guide,
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html,
verified 2026-08-02).

## 3. Forces

- **Read latency versus data freshness.** Favoured heavily toward latency. The
  pattern exists specifically to trade a bounded amount of staleness for a
  large reduction in tail latency and backing-store load. A team that needs
  strict read-your-writes consistency on every read is fighting the pattern's
  entire premise.
- **Backing-store load.** Strongly favoured. Every cache hit is a read the
  backing store never sees. This is usually the dominant motivation in
  practice, expressed either as a latency win or as a direct cost saving on
  provisioned read capacity, as DAX's own documentation states plainly.
- **Cache-miss penalty.** Sacrificed, and this cost is often invisible until
  measured. ElastiCache's own guidance is explicit that "each cache miss
  results in three trips" (initial request for data from the cache, query of
  the database for the data, writing the data to the cache), which is
  strictly more latency than a direct database read for that one unlucky
  request (AWS, "Caching strategies for Memcached", cited above). The pattern
  is a net win only when the hit rate is high enough to amortise this
  penalty.
- **Operational simplicity of the client.** Favoured, when the loader is
  truly centralised behind the cache. Application code calls one method and
  stops thinking about the backing store. This is sacrificed the moment the
  loader logic still needs application-specific context, such as tenant
  isolation or authorization, which forces the loader to be parameterised in
  ways that erode the simplicity gain.
- **Resilience to a cold or partially failed cache.** Favoured over a
  write-through-only design. A newly provisioned cache node, or a node lost
  and replaced, serves correctly, only slowly, because every request is a
  miss until the cache warms. ElastiCache states this directly as an
  advantage of lazy loading, that "node failures aren't fatal for your
  application" because "your application continues to function, though with
  increased latency" (AWS, cited above).
- **Cost of stale reads.** Sacrificed. Because population happens only on a
  miss, a value already in the cache is never refreshed by a write elsewhere
  unless a separate invalidation or TTL mechanism runs. ElastiCache names
  this directly as a disadvantage, that "data in the cache can become stale"
  because "there are no updates to the cache when data is changed in the
  database" (AWS, cited above).
- **Thundering herd risk under high concurrency.** Sacrificed unless
  deliberately mitigated. A hot key that expires or is evicted while many
  concurrent requests are in flight can cause all of them to miss
  simultaneously and hammer the backing store at once. This force is not
  something the pattern solves on its own, see dimension 8 for the
  mitigation it requires.

A pattern that gave up nothing would not need the write-through or write-behind
siblings described in dimension 13. The price here is paid in staleness and in
a variable, sometimes multi-hop, miss path.

## 4. Applicability and non-applicability

Reach for Read-Through Cache when the following hold.

- Reads dominate writes for the data in question, often by one or more orders
  of magnitude, and the backing store is the measured bottleneck or the
  measured cost driver.
- The working set is large or unbounded, so eagerly loading the whole set into
  a cache at startup (a pre-warmed or push-based cache) is wasteful, and the
  natural request stream is the cheapest way to decide what deserves to be
  cached.
- A bounded amount of staleness, measured in seconds to minutes depending on
  the domain, is acceptable to the business. Product listings, rendered HTML
  fragments, computed recommendations, and permission checks with a short TTL
  are typical fits.
- The loading logic on a miss is non-trivial and shared across many call
  sites, so centralising it inside a cache client, an ORM second-level cache,
  or a caching product's loader hook removes duplicated fetch-then-populate
  code from application call sites.
- Node loss must not be an outage. A read-through cache degrades to the
  backing store's own latency on a cold cache rather than serving errors.

Do NOT reach for Read-Through Cache in these cases, and the reason matters
more than the rule.

- **The data must be strongly consistent on every read.** A financial ledger
  balance immediately after a debit, a feature flag that gates a legal
  disclosure, or an inventory count during a flash sale where overselling is
  unacceptable cannot tolerate the staleness window this pattern introduces
  by design. Read the backing store directly, or use a cache invalidation
  strategy strong enough to guarantee freshness, which is a materially
  different and more expensive design than a plain read-through cache.
- **Writes dominate reads, or writes and reads are roughly balanced.** A
  read-through cache does nothing for write load, and if most keys are
  written far more often than they are read, the cache spends most of its
  effort holding values nobody asks for again before the next write
  invalidates them. Write-Through or Write-Behind Cache, or no cache at all,
  fits better, see dimension 13.
- **The working set is small and fits comfortably in application memory
  already.** If every instance of the service can hold the entire dataset in
  a local map that is refreshed on a schedule, a full pre-load is simpler than
  a partial, miss-driven cache and avoids the miss penalty entirely. This is
  sometimes called a fully-cached or push-based design and is not this
  pattern.
- **The backing store is already fast enough and cheap enough for the actual
  load.** Adding a cache is not free. It adds an operational component, a
  consistency model to reason about, and a new class of bug, the stale read.
  Measure before reaching for this pattern, per the profiling discipline that
  should precede any performance-motivated architectural change.
- **DAX-style scenario mismatch.** AWS states DAX itself is "not ideal for"
  applications that "require strongly consistent reads", that "do not require
  microsecond response times", or that are "write-intensive", and that DAX
  "performs best when cache hit rates exceed 90 percent" with lower hit rates
  actually consuming more cluster resources than not caching at all (AWS,
  DynamoDB Accelerator documentation, cited above). This is a specific,
  sourced instance of the general rule that a read-through cache under a low
  hit rate is a net negative, not a neutral addition.
- **The loader has side effects beyond fetching.** If "reading" the value also
  triggers a write, a metric side effect, or a downstream call that must
  happen exactly once per logical read, a cache sitting transparently in front
  of that call will silently suppress those side effects on every hit. The
  loader must be a pure read.

## 5. Structure

Four participants, named by the role they play.

- **Client.** The application code that wants a value for a key. It issues one
  call, typically `get(key)`, and receives a value. It has no branch for hit
  versus miss, because that branch lives inside the cache.
- **Cache.** The component that holds an in-memory or near-memory map from key
  to value, answers hits directly, and on a miss invokes the Loader,
  publishes the result into its own storage, and returns it to the Client.
  The cache also owns eviction policy (size-bound, TTL-bound, or both) and, in
  distributed deployments, replication between cache nodes.
- **Loader.** A function or object supplied to the Cache at construction time,
  responsible for fetching or computing the value for a given key from the
  Origin. It is the one piece of code that knows how to reach the backing
  store, and it is called once per miss, never once per Client call.
  Guava's `CacheLoader` and Spring's underlying `CacheLoader` behind
  `@Cacheable` both play exactly this role.
- **Origin.** The authoritative backing store, a relational or NoSQL database,
  a remote HTTP service, or an expensive computation. It never receives a
  request from the Client directly in the read-through shape, only from the
  Loader.

A subtlety worth naming here because it is the most common source of
confusion when comparing this pattern to Cache-Aside. In the strict
read-through shape, the Client's dependency graph contains the Cache and
nothing else. It does not import a database client, an HTTP client, or any
type belonging to the Origin. That is the structural signature that separates
this pattern from Cache-Aside, where the Client (or a service wrapping it)
depends on both the Cache and the Origin and coordinates between them itself.

## 6. ASCII structure diagram

```
+-------------------------------+
| Client (no origin dependency) |
+-------------------------------+
           | get(k)
           v
+-----------------------------------+
| Cache                             |
| map<K,V> store                    |
| eviction policy (TTL, size bound) |
+-----------------------------------+
           | value, returned to Client above
           |
           | load(k), only on a cache miss
           v
+-------------+
| Loader      |
| fetch(K): V |
+-------------+
           | value, returned to Cache above
           |
           | query
           v
+-------------------------------------+
| Origin                              |
| database, API, or expensive compute |
+-------------------------------------+

A cache hit answers from the Cache directly, no Loader
call. The Client's only compile-time dependency is
Cache. Origin is reachable only through Loader, which
the Cache owns and calls, never the Client.
```

## 7. Dynamics

Two flows exist, and the entire value of the pattern is that the Client's code
is identical for both.

```
Cache hit flow.

Client            Cache                Loader              Origin
  |                  |                    |                   |
  |-- get(k) ------->|                    |                   |
  |                  |-- lookup in map -->|                   |
  |                  |   (found, valid)   |                   |
  |<-- v -----------|                    |                   |
  |                  |                    |                   |
```

```
Cache miss flow.

Client            Cache                Loader              Origin
  |                  |                    |                   |
  |-- get(k) ------->|                    |                   |
  |                  |-- lookup in map -->|                   |
  |                  |   (absent or       |                   |
  |                  |    expired)        |                   |
  |                  |-- load(k) ----------->|                |
  |                  |                    |-- query(k) ------>|
  |                  |                    |<-- v -------------|
  |                  |<-- v --------------|                   |
  |                  |-- store(k, v) into map, set TTL         |
  |<-- v -----------|                    |                   |
  |                  |                    |                   |
```

Two timing notes matter in production. First, a concurrent miss on the same
hot key by many simultaneous callers must be serialised inside the Cache, or
every one of those callers triggers its own Loader call against the Origin at
once, the thundering herd condition named in dimension 3 and mitigated in
dimension 8. Second, the write into the map and the return to the Client are
not atomic across a distributed cache tier, so a caller racing a concurrent
eviction can, in rare implementations, see the value it just loaded evicted
before a second caller's read, which reappears as an apparent flapping hit
rate rather than a correctness bug, because the second caller simply triggers
another miss.

## 8. Implementation variants

**In-process loading cache.** The Cache lives inside the application process,
typically as a bounded map with size and TTL eviction, and the Loader runs on
the calling thread or a dedicated executor. Guava's `LoadingCache` and its
successor Caffeine are the reference shape in the JVM ecosystem. Fastest
possible hit path, no network hop, but the cache is not shared across process
instances, so a fleet of N instances each maintains its own copy and the
Origin sees up to N times the miss traffic of a single instance.

**Out-of-process distributed cache with a loader extension.** The Cache is a
separate service, such as Redis, Memcached, or Hazelcast, and a loader plugin
or side-loading client library performs the population on a miss. Hazelcast's
`MapLoader` interface and Ehcache's `CacheLoaderWriter` are the reference
shapes here. Shared across the fleet, so the Origin sees one miss per key per
TTL window regardless of instance count, at the cost of a network hop even on
a hit.

**Managed read-through caching product in front of a managed store.** The
cache and its loading behaviour are both provided by the platform, with no
application-visible Loader object at all, only configuration. DAX in front of
DynamoDB is the reference example, and it is API-compatible with the
DynamoDB SDK so that switching to it requires "only minimal functional
changes" (AWS, DAX documentation, cited above).

**Lazy-loading application code, no dedicated loader abstraction.**
The application writes the miss branch itself against a plain key-value
store with no built-in loader hook, which is what most Redis or Memcached
deployments actually look like and what ElastiCache's own pseudocode
demonstrates. This is the boundary case with Cache-Aside, discussed further
in dimension 13, and many teams call this shape read-through in casual speech
even though the loading logic is not centralised behind a single interface.

**Refresh-ahead, a common extension rather than a separate pattern.** The
Cache proactively re-invokes the Loader for a key shortly before its TTL
expires, asynchronously, so that Client requests continue to hit a fresh
value without ever observing the miss penalty. Guava's
`CacheBuilder.refreshAfterWrite` implements exactly this idea. It does not
remove the pattern's staleness window, it only shrinks the probability that a
Client request lands exactly inside it.

**Request coalescing (single-flight) to prevent the thundering herd.** When
many concurrent Client calls miss on the same key, the Cache must guarantee only
one Loader call happens, with every other caller awaiting that same
in-flight call rather than issuing its own. Guava's `LoadingCache` performs
this coalescing internally per key. Distributed caches without native
support for this need an explicit distributed lock or a load-once-and-
broadcast-the-result mechanism, and omitting it is the single most common
cause of an origin outage triggered by a cache expiry event, see dimension
11.

**Negative caching.** The Loader can cache the fact that a key does not exist
in the Origin, usually with a shorter TTL than a positive result, to avoid
repeatedly hammering the Origin for a key that legitimately has no value,
such as a request for a deleted or never-created resource.

## 9. Known production uses

**Google Guava `LoadingCache` and its successor Caffeine.** Guava's
`CacheLoader` Javadoc states it exists to "compute or retrieve values, based
on a key, for use in populating a LoadingCache" and shows the canonical usage
`LoadingCache<Key, Graph> cache = CacheBuilder.newBuilder().build(loader)`
followed by transparent population on `cache.get(key)` (Google, Guava
`CacheLoader` API documentation, release 33.0.0-jre,
https://guava.dev/releases/33.0.0-jre/api/docs/com/google/common/cache/CacheLoader.html,
verified 2026-08-02). This is the textbook in-process read-through cache used
across a large fraction of production JVM services.

**Amazon DynamoDB Accelerator (DAX).** DAX sits in front of DynamoDB as a
DynamoDB-API-compatible in-memory cache and is described as reducing
"response times of eventually consistent read workloads by an order of
magnitude from single-digit milliseconds to microseconds", explicitly
recommended for "applications that require repeated reads against a large
set of data" (AWS, "In-memory acceleration with DynamoDB Accelerator (DAX)",
DynamoDB Developer Guide,
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html,
verified 2026-08-02). This is the managed, product-level read-through cache
shape.

**Amazon ElastiCache, documented lazy loading strategy.** AWS's own
ElastiCache strategies documentation names lazy loading as one of its two
primary caching strategies, alongside write-through, and provides the
canonical get-with-miss-population pseudocode this entry's dynamics section
mirrors (AWS, "Caching strategies for Memcached", ElastiCache for Redis OSS
User Guide,
https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Strategies.html,
verified 2026-08-02). This is one of the most widely deployed instances of
the application-managed variant of this pattern in the industry.

**Spring Framework declarative caching, `@Cacheable`.** Spring's cache
abstraction reference states that "the Spring Framework provides support for
transparently adding caching to an existing Spring application" allowing
"consistent use of various caching solutions with minimal impact on the
code" (VMware, "Cache Abstraction", Spring Framework Reference Documentation,
https://docs.spring.io/spring-framework/reference/integration/cache.html,
verified 2026-08-02). A method annotated `@Cacheable` is checked against the
configured cache before it runs, and its return value is stored into the
cache automatically on a miss, which is the read-through shape applied at the
method-call boundary rather than at a raw key-value boundary.

## 10. Consequences

Positive.

- Backing-store read load drops sharply for any workload with a
  non-trivial hit rate, directly reducing provisioned capacity, cost, and
  tail latency, as documented for DAX's read-heavy and hot-key use cases.
- The Client's code is uniform for hits and misses, because the branch lives
  inside the Cache or the Loader, which removes duplicated fetch-then-cache
  logic from every call site that would otherwise need it.
- The system degrades gracefully rather than failing outright when a cache
  node is lost or newly provisioned, continuing to serve correct data at
  higher latency until the cache rewarms, as ElastiCache documents
  explicitly.
- Only data that is actually requested ever occupies cache space, which for
  most real workloads is a small, hot fraction of the full dataset, avoiding
  the wasted memory of a naive full pre-load.
- Centralising the Loader creates one place to add instrumentation, request
  coalescing, negative caching, and refresh-ahead behaviour, all of which
  benefit every call site at once.

Negative.

- Data can be stale between the moment the Origin changes and the moment the
  corresponding cache entry expires or is explicitly invalidated, which
  ElastiCache's own documentation names as the central disadvantage of this
  strategy.
- Every miss costs strictly more latency than a direct read of the Origin
  would have, because a miss is a cache lookup plus an Origin query plus a
  cache write, so the pattern is a net loss under a low hit rate, exactly as
  AWS states for DAX below a 90 percent hit rate.
- A hot key expiring under concurrent load can cause a burst of simultaneous
  Origin queries unless request coalescing is implemented, turning a routine
  TTL expiry into an Origin-side incident.
- The system now has two sources of truth in flight at once, even if only
  briefly, which complicates reasoning about correctness for any code that
  assumes a single, immediately consistent read path.
- Operationally the cache is a new component with its own failure modes,
  memory pressure, eviction tuning, and monitoring surface, adding to the
  system's total operational burden.

## 11. Failure modes and misuse

**Thundering herd on a hot-key expiry.** Symptom. A sudden, sharp spike in
Origin query volume and latency that correlates precisely with a TTL boundary
for one or a small number of keys, followed by recovery once the cache
repopulates. Cause. Many concurrent Client requests missed on the same key at
once and each independently invoked the Loader against the Origin, because
the Cache implementation does not coalesce concurrent misses on the same key.
Fix. Use a cache implementation with built-in single-flight semantics such as
Guava's `LoadingCache`, or add an explicit per-key lock or a stale-while-
revalidate strategy so only one Loader call happens per expiry event.

**Cache stampede at cold start.** Symptom. A newly deployed service instance,
or a freshly failed-over cache cluster, produces an Origin load spike at
startup that dwarfs steady-state traffic, sometimes tripping an unrelated
rate limiter or connection pool exhaustion on the Origin. Cause. Every key
the service needs is a miss simultaneously, because the cache started empty.
Fix. Stagger instance startup, pre-warm the cache from a snapshot or a known
hot-key list before serving traffic, or apply a request-rate limiter in front
of the Loader independent of the Client's own rate.

**Silent staleness mistaken for a bug.** Symptom. A support ticket reporting
that a user's change "did not save", when in fact it saved correctly to the
Origin but a stale cached read is still being served to that user or to
other users. Cause. No write-side invalidation exists, or the invalidation
missed a cache node in a multi-node deployment, and the TTL has not yet
expired. Fix. Add explicit invalidation on write when read-your-writes
matters even loosely, or document the TTL as the system's actual freshness
guarantee and communicate it, rather than silently promising freshness the
design does not provide.

**Loader with a hidden side effect.** Symptom. A metric, a counter, or a
downstream call fires far fewer times than expected relative to the number
of logical reads, because most of those reads are being served from the
cache and never reach the Loader. Cause. The Loader function was written
under the assumption it runs on every logical read, when in a read-through
design it runs only on a miss. Fix. Move the side effect out of the Loader
and into either the Client, guaranteed to run on every call, or an explicit,
separately triggered process, and keep the Loader a pure fetch.

**Unbounded cache growth.** Symptom. Steadily climbing memory usage in the
process or cache cluster hosting the Cache, eventually triggering evictions,
out-of-memory errors, or, in a managed product like DAX, the metadata
exhaustion AWS specifically warns about for applications using "an unbounded
number of attribute names" as keys (AWS, DAX documentation, cited above).
Cause. No size bound was configured on the Cache, or the key space is itself
effectively unbounded, such as using a timestamp or a session identifier as
part of the key. Fix. Configure an explicit maximum size with an eviction
policy, and audit key construction for unbounded cardinality.

**Low hit rate making the cache a net negative.** Symptom. P99 latency for
reads is worse after introducing the cache than before, and Origin load has
not measurably dropped. Cause. The workload does not have the read-skew the
pattern assumes, so most requests miss, and every miss now pays the
lookup-plus-query-plus-write penalty on top of what a direct Origin read
would have cost. Fix. Measure hit rate before committing to the pattern, and
remove or bypass the cache for key spaces or workloads that measure below a
threshold appropriate to the Origin's own latency, consistent with AWS's
stated 90 percent guidance for DAX.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Read-Through Cache | Cache-Aside | Write-Through Cache | Write-Behind Cache | No cache, direct reads |
|---|---|---|---|---|---|
| Who owns the miss-fill logic | Cache or Loader, centralised | Application, at each call site | Cache, on the write path | Cache, on the write path | Not applicable |
| Read latency, cache hit | Lowest, single hop to cache | Same as read-through on a hit | Lowest, entries are always fresh on write | Lowest, entries are always fresh on write | Origin latency on every read |
| Read latency, cache miss | Higher than direct read, three hops | Same three-hop cost, application-managed | Rare, only for keys never written yet | Rare, same as write-through | Origin latency, no extra hop |
| Data freshness | Bounded by TTL, can be stale | Bounded by TTL, can be stale, same as read-through | Always fresh for written keys | Fresh in cache, Origin can lag | Always fresh, by definition |
| Origin load under read-heavy skew | Sharply reduced | Sharply reduced, same benefit | Unchanged for reads, reduced by cache instead | Unchanged for reads | Full load, unmitigated |
| Origin load under write-heavy workload | Unaffected by writes at all | Unaffected by writes at all | Every write also costs a cache write | Writes batched, lower Origin write load | Full load, unmitigated |
| Behaviour on cold cache or node loss | Degrades to Origin latency, self-heals | Degrades to Origin latency, self-heals | Missing entries until a write occurs, as AWS notes | Same missing-entry gap as write-through | Not applicable, no cache to lose |
| Code centralisation | High, one Loader for all callers | Low, duplicated at each call site unless refactored | High, one write-path hook | High, one write-path hook | Not applicable |
| Risk of thundering herd | Present, needs coalescing | Present, application must add its own coalescing | Absent for reads, present for a cold cache's first writes | Absent for reads | Not applicable |

Reading of the table. Read-Through Cache and Cache-Aside solve the same
problem and share the same freshness and Origin-load profile, differing only
in whether the fill logic lives behind one interface or is repeated by hand.
Write-Through and Write-Behind solve a materially different problem, keeping
already-cached data fresh on writes, and are frequently combined with a
read-through or lazy-loading strategy rather than substituted for it, exactly
as AWS's own strategies documentation recommends pairing lazy loading with a
TTL or with write-through to offset each one's specific weakness.

## 13. Related and incompatible patterns

- **Cache-Aside.** The closest relative and the one most often confused with
  this pattern in casual usage. The structural difference established in
  dimension 5 is the deciding factor. In Cache-Aside the calling code depends
  on both the Cache and the Origin and coordinates the miss-then-populate
  sequence itself, while in Read-Through Cache that sequence is centralised
  behind a single interface the caller depends on alone. When a team's actual
  code looks like ElastiCache's own lazy-loading pseudocode, with the miss
  branch written by hand at the call site, it is Cache-Aside in this
  catalog's terms even if the team calls it read-through in conversation.
  When the miss branch is owned by a `CacheLoader`, a `MapLoader`, or a
  managed product like DAX, it is Read-Through Cache proper.
- **Write-Through Cache.** Composes cleanly and is frequently paired with
  this pattern. Write-Through keeps already-cached entries fresh whenever a
  write happens, directly addressing the staleness weakness this pattern
  accepts on its own. AWS's ElastiCache guidance recommends exactly this
  pairing, noting write-through's own weakness, that missing data after a
  cold start "can minimize this by implementing lazy loading with
  write-through".
- **Write-Behind Cache.** Composes similarly to Write-Through but batches or
  defers the write to the Origin, trading a durability window for reduced
  write amplification on the Origin. It addresses a different force, write
  load rather than read load, and is orthogonal to this pattern rather than a
  substitute for it.
- **Circuit Breaker.** Composes usefully around the Loader. If the Origin is
  failing or overloaded, a circuit breaker wrapping the Loader call can fail
  fast and serve a stale or default value rather than compounding an Origin
  outage with a flood of retried Loader calls, which is a materially
  different and more resilient response than letting every miss retry
  independently.
- **Proxy.** The Cache, viewed structurally, is a Proxy in front of the
  Origin. It controls access, adds a layer of indirection, and can add
  behaviour, caching, transparently to the Client, which is exactly the GoF
  Proxy pattern's intent applied to a data-access boundary rather than an
  object reference.
- **Decorator.** A Loader wrapped with request coalescing, negative caching,
  or metrics is a Decorator composed around the base fetch function, and many
  real caching libraries implement exactly this layering internally.
- **Singleton, in its process-wide caching-instance form.** Frequently paired
  in practice, since an in-process `LoadingCache` is usually held as a single
  shared instance per application process, but the two patterns are not
  coupled in principle and a read-through cache can be scoped more narrowly
  when a single shared instance would leak state between unrelated tenants
  or requests.
- **Materialized View, as a stronger-consistency alternative.** When
  staleness genuinely cannot be tolerated but read load must still be
  reduced, a materialised view kept synchronously or near-synchronously
  consistent with the Origin is the pattern to reach for instead, at
  significantly higher implementation and operational cost than a
  TTL-bounded cache.

## 14. Refactoring path in and out

Introducing the pattern into code that reads directly from an Origin on every
call, ordered steps.

1. Measure the current read pattern. Confirm read-to-write ratio, key
   cardinality, and current Origin read latency and load before writing any
   caching code. This is the step teams skip and the reason the pattern
   sometimes makes things worse, per dimension 11's low-hit-rate failure mode.
2. Identify a single, narrow read path to introduce the cache around first,
   not the whole read surface at once. A single hot endpoint or a single
   repository method is enough to validate the design.
3. Extract the existing fetch logic for that path into a standalone function
   or class with no cache awareness. This becomes the Loader. Nothing about
   its behaviour should change in this step, and its existing tests should
   still pass unmodified.
4. Introduce the Cache as a thin wrapper around the Loader, using an
   off-the-shelf library such as Guava, Caffeine, or the caching abstraction
   already provided by the application's framework, rather than a hand-built
   map. Configure an explicit size bound and TTL from the start, never an
   unbounded cache.
5. Redirect the one chosen call site to call the Cache instead of the Loader
   directly. Verify hit rate, Origin load, and latency against the baseline
   measured in step 1.
6. Add request coalescing if the library does not provide it natively and the
   key space includes plausible hot keys, before expanding to more call
   sites, because the thundering herd failure mode in dimension 11 gets more
   expensive to retrofit the more call sites depend on the cache.
7. Repeat steps 2 through 6 for additional read paths only once the first is
   proven in production, rather than wrapping the entire data-access layer at
   once.

Removing the pattern when it stops earning its place. Signals that it should
go include a measured hit rate persistently below the threshold that makes
the miss penalty worthwhile, per dimension 11, or a consistency requirement
that has tightened since the cache was introduced.

1. Confirm the measured hit rate and the current consistency requirements for
   the cached data, not the requirements at the time the cache was added.
2. Route the call site directly to the Loader function, bypassing the Cache,
   while leaving the Cache and Loader both in place and monitored.
3. Compare latency and Origin load with the cache bypassed against the
   cached baseline, over a representative traffic window, to confirm removal
   is actually beneficial rather than assumed.
4. Delete the Cache wrapper and inline the Loader back into the call site, or
   leave it as a plain, uncached data-access function if it is called from
   multiple places, which is Inline Class applied to the Cache wrapper, see
   the refactoring family entry.
5. Remove any cache-specific instrumentation, coalescing, or invalidation
   hooks that no longer have a caller.

## 15. Testing and verification

Easier because of the pattern.

- The Loader is a plain function with a clear input and output and no caching
  concerns baked in, so it can be unit tested exactly like any other
  data-access function, with the backing store faked or mocked as usual.
- The Cache's hit-versus-miss behaviour can be tested independently of the
  Loader, using a test-only Loader that counts its own invocations, which
  makes miss-penalty and coalescing behaviour directly assertable rather than
  inferred.
- Because the Client's dependency is only the Cache interface, a test double
  Cache that returns fixed values with zero Loader calls makes testing
  Client-side logic fast and free of any real caching or persistence
  concerns.

Harder because of the pattern.

- Correctness now depends on timing, specifically TTL expiry and eviction
  order, which is inherently harder to test deterministically than pure
  functions, and tests that rely on real wall-clock TTLs are flaky by
  construction unless the clock is controlled.
- Concurrency behaviour, specifically whether concurrent misses on the same
  key coalesce into a single Loader call, requires a genuinely multi-threaded
  test setup to exercise, not a simple sequential unit test.
- Staleness bugs by definition do not show up in a single-request test. They
  require a test that writes to the Origin, confirms a stale read from the
  cache within the TTL window, and confirms freshness after expiry or
  explicit invalidation.

Techniques that apply.

- **Loader invocation counter, injected as a test double.** Wrap the real
  Loader in a counting decorator in tests and assert the exact number of
  Loader calls for a given sequence of Client calls, which is the most
  direct way to prove hit and miss behaviour, including coalescing, without
  reasoning about internals.
- **Controlled clock for TTL tests.** Inject a fake clock or a
  library-provided ticker, such as Guava's `Ticker`, so TTL expiry can be
  tested by advancing simulated time deterministically rather than sleeping
  the test thread.
- **Concurrent miss test with a barrier.** Launch several threads that all
  request the same missing key simultaneously, gated by a start barrier, and
  assert the Loader was called exactly once, which is the direct test for
  the thundering-herd mitigation described in dimension 8.
- **Staleness window integration test.** Write a value to the Origin behind
  the cache, read through the Cache to confirm the pre-write value or a
  cached absence is served within the TTL, then advance past the TTL and
  confirm the updated value now appears, exercising the full contract the
  pattern actually promises rather than an idealised always-fresh
  assumption.

## 16. Observability signals

The pattern's entire value proposition, latency and Origin-load reduction, is
invisible unless it is measured, so instrumentation here is not optional
polish.

What to record.

- A hit-and-miss counter per cache, and ideally per key prefix or key type
  where cardinality allows, since AWS's own DAX guidance ties recommended
  usage directly to a hit-rate threshold, and the same threshold discipline
  applies to any read-through deployment.
- A histogram of Loader execution duration, separate from the Cache's own
  hit-path latency, so a slowdown in the Origin is visible as a distinct
  signal from a slowdown in the cache tier itself.
- A counter of Loader invocations per key over a time window, to detect
  thundering-herd behaviour directly rather than inferring it from an Origin
  load spike after the fact.
- Cache size and eviction rate, labelled by eviction cause where the library
  exposes it, size-based versus TTL-based, since a size-driven eviction storm
  on a workload assumed to be TTL-bound points at an undersized cache rather
  than a data-freshness problem.
- Origin query rate and latency, monitored as a signal independent of the
  cache's own metrics, since the two together are what proves or disproves
  the pattern is delivering its intended benefit.

A healthy instance on a dashboard. Hit rate is high and stable for the
workload's actual read skew, consistent with the 90 percent-plus figure AWS
associates with DAX's recommended use case. Loader duration is flat and
matches the Origin's normal latency profile. Loader invocations per key stay
at roughly one per TTL window even under high concurrent read volume for the
same key, evidence that coalescing is working. Origin query rate sits well
below the Client's total request rate, by a factor consistent with the hit
rate.

A failing instance. Hit rate drops and stays low after a deployment or a key
scheme change, which usually means key construction changed in a way that
fragmented what used to be a small number of hot keys into many distinct
ones. Loader invocations per key spike sharply and briefly around a TTL
boundary, which is the thundering herd pattern in dimension 11 made visible.
Origin query latency and error rate rise in lockstep with a cache eviction or
restart event, which is the expected, tolerable cold-start behaviour if brief
and self-correcting, but an incident if sustained, pointing at an
undersized cache or a cache that never finishes warming under steady traffic.

## 17. Security and privacy implications

The pattern introduces a second location, separate from the Origin, where
data at rest exists, and that fact alone carries real implications once the
cached data is anything other than fully public.

**Data residing outside the Origin's own access controls.** A cache is
frequently a simpler system than the Origin database, and it is easy for its
authentication, encryption, and access-control posture to lag behind the
Origin's, especially for an in-process cache that is invisible to database
access auditing entirely. Data containing personal information, credentials,
or anything subject to a data-residency requirement needs the same access
control and encryption-at-rest posture in the cache as in the Origin, not a
lesser one by default. DAX documentation is explicit about supporting both
server-side encryption at rest and encryption in transit as first-class
options specifically because caching sensitive data without them would be an
unacceptable gap (AWS, DAX documentation, cited above).

**Stale authorization decisions.** Caching a permission check, a role
assignment, or an authorization decision behind a TTL means a revoked
permission remains effectively granted for up to the TTL window after
revocation. This is a genuine security implication, not merely a data-
freshness inconvenience, and any cache placed in front of an authorization
decision needs either an explicit invalidation path triggered on revocation,
or a TTL short enough that the residual-access window is an accepted, sized
risk rather than an unexamined one.

**Cache poisoning through a manipulable key.** If the cache key is derived
from user-controllable input without normalisation, an attacker can
construct inputs that collide with, or that generate an unbounded number of,
distinct cache keys. The former can serve one user's cached response to
another under crafted input, and the latter reproduces the unbounded-key
denial-of-service concern named in dimension 11 as a deliberate attack rather
than an accident. Keys derived from user input should be normalised and, where
they include an identity component, should include the caller's own
authenticated identity as part of the key rather than trusting an unvalidated
input alone.

**Amplified denial-of-service surface at the Loader.** Because a miss costs
more than a direct read, an attacker who can force cache misses at scale,
by requesting a large number of distinct never-cached keys, can put more
load on the Origin per request than a cache-free system would, inverting the
pattern's intended benefit into an amplification vector. Rate limiting and
negative caching for known-invalid keys, both named in dimension 8, are the
direct mitigations.

On privacy specifically, the pattern is otherwise neutral, with one practical
caveat matching the one in the Factory Method entry in this catalog. A TTL and
an eviction policy determine how long a piece of personal data persists in
the cache after it was last requested, which for compliance purposes is a
retention duration in its own right, separate from the Origin's own retention
policy, and should be accounted for in any data-retention or right-to-erasure
process rather than assumed to be governed solely by the Origin's rules.

## Code examples

Three languages where the pattern's shape is genuinely idiomatic in
different ways. TypeScript shows a minimal from-scratch read-through cache
with request coalescing, the shape most services actually hand-roll when no
library is pulled in. Python shows the same coalescing shape using
`asyncio`, since Python's dominant caching libraries, `functools.lru_cache`
and `cachetools`, do not coalesce concurrent async misses on their own. Go is
included because its standard library ecosystem provides
`golang.org/x/sync/singleflight` as the idiomatic building block for exactly
this pattern in Go services, and the example below hand-rolls the same idea
with the standard library alone so it runs with no external dependency. Java
is omitted from a full example because Guava's `LoadingCache`, already
quoted in dimension 9, is the reference implementation and reproducing it
would only restate the library's own documented behaviour rather than add
anything original.

### TypeScript

```typescript
type Loader<K, V> = (key: K) => Promise<V>;

interface Entry<V> {
  value: V;
  expiresAt: number;
}

class ReadThroughCache<K, V> {
  private readonly store = new Map<K, Entry<V>>();
  private readonly inFlight = new Map<K, Promise<V>>();

  constructor(
    private readonly loader: Loader<K, V>,
    private readonly ttlMs: number,
  ) {}

  async get(key: K): Promise<V> {
    const hit = this.store.get(key);
    if (hit && hit.expiresAt > Date.now()) {
      return hit.value;
    }

    const pending = this.inFlight.get(key);
    if (pending) {
      return pending;
    }

    const promise = this.loader(key)
      .then((value) => {
        this.store.set(key, { value, expiresAt: Date.now() + this.ttlMs });
        return value;
      })
      .finally(() => {
        this.inFlight.delete(key);
      });

    this.inFlight.set(key, promise);
    return promise;
  }
}

async function demo() {
  let originCalls = 0;
  const cache = new ReadThroughCache<number, string>(async (id) => {
    originCalls += 1;
    return `user-${id}`;
  }, 5000);

  const results = await Promise.all([cache.get(1), cache.get(1), cache.get(1)]);
  console.log(results, "origin calls", originCalls);
}

demo();
```

### Python

```python
import asyncio
import time
from typing import Awaitable, Callable, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ReadThroughCache(Generic[K, V]):
    def __init__(self, loader: Callable[[K], Awaitable[V]], ttl_seconds: float):
        self._loader = loader
        self._ttl_seconds = ttl_seconds
        self._store: dict[K, tuple[V, float]] = {}
        self._in_flight: dict[K, asyncio.Future[V]] = {}

    async def get(self, key: K) -> V:
        entry = self._store.get(key)
        if entry is not None:
            value, expires_at = entry
            if expires_at > time.monotonic():
                return value

        pending = self._in_flight.get(key)
        if pending is not None:
            return await pending

        future: asyncio.Future[V] = asyncio.get_event_loop().create_future()
        self._in_flight[key] = future
        try:
            value = await self._loader(key)
            self._store[key] = (value, time.monotonic() + self._ttl_seconds)
            future.set_result(value)
            return value
        finally:
            del self._in_flight[key]


async def demo() -> None:
    origin_calls = 0

    async def loader(user_id: int) -> str:
        nonlocal origin_calls
        origin_calls += 1
        await asyncio.sleep(0.01)
        return f"user-{user_id}"

    cache: ReadThroughCache[int, str] = ReadThroughCache(loader, ttl_seconds=5.0)
    results = await asyncio.gather(cache.get(1), cache.get(1), cache.get(1))
    print(results, "origin calls", origin_calls)


if __name__ == "__main__":
    asyncio.run(demo())
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
	value     string
	expiresAt time.Time
}

type ReadThroughCache struct {
	mu        sync.Mutex
	store     map[int]entry
	inFlight  map[int]*sync.WaitGroup
	results   map[int]string
	ttl       time.Duration
	loader    func(int) string
	loadCalls int
}

func NewReadThroughCache(loader func(int) string, ttl time.Duration) *ReadThroughCache {
	return &ReadThroughCache{
		store:    make(map[int]entry),
		inFlight: make(map[int]*sync.WaitGroup),
		results:  make(map[int]string),
		ttl:      ttl,
		loader:   loader,
	}
}

func (c *ReadThroughCache) Get(key int) string {
	c.mu.Lock()
	if e, ok := c.store[key]; ok && e.expiresAt.After(time.Now()) {
		c.mu.Unlock()
		return e.value
	}

	if wg, ok := c.inFlight[key]; ok {
		c.mu.Unlock()
		wg.Wait()
		c.mu.Lock()
		v := c.results[key]
		c.mu.Unlock()
		return v
	}

	wg := &sync.WaitGroup{}
	wg.Add(1)
	c.inFlight[key] = wg
	c.mu.Unlock()

	c.mu.Lock()
	c.loadCalls++
	c.mu.Unlock()
	value := c.loader(key)

	c.mu.Lock()
	c.store[key] = entry{value: value, expiresAt: time.Now().Add(c.ttl)}
	c.results[key] = value
	delete(c.inFlight, key)
	c.mu.Unlock()
	wg.Done()

	return value
}

func main() {
	cache := NewReadThroughCache(func(id int) string {
		time.Sleep(5 * time.Millisecond)
		return fmt.Sprintf("user-%d", id)
	}, 5*time.Second)

	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			fmt.Println(cache.Get(1))
		}()
	}
	wg.Wait()
	fmt.Println("origin calls", cache.loadCalls)
}
```

## 18. References

1. Amazon Web Services. "Caching strategies for Memcached". Amazon ElastiCache
   for Redis OSS User Guide.
   https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Strategies.html
   Verified 2026-08-02. Source for the lazy loading definition, hit and miss
   flow, the pseudocode referenced in dimension 7, and the write-through
   pairing recommendation in dimension 13.
2. Amazon Web Services. "In-memory acceleration with DynamoDB Accelerator
   (DAX)". Amazon DynamoDB Developer Guide.
   https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DAX.html
   Verified 2026-08-02. Source for the DAX production use, its use-case and
   anti-use-case guidance in dimension 4, the 90 percent hit-rate threshold,
   the unbounded-attribute-name failure mode in dimension 11, and the
   encryption features cited in dimension 17.
3. Google. Guava `CacheLoader` API documentation, release 33.0.0-jre.
   https://guava.dev/releases/33.0.0-jre/api/docs/com/google/common/cache/CacheLoader.html
   Verified 2026-08-02. Source for the `LoadingCache` and `CacheLoader`
   production use in dimension 9 and the naming lineage in dimension 1.
4. VMware. "Cache Abstraction". Spring Framework Reference Documentation.
   https://docs.spring.io/spring-framework/reference/integration/cache.html
   Verified 2026-08-02. Source for the `@Cacheable` production use in
   dimension 9.
5. Amazon Web Services. "Database Caching". AWS Caching solutions overview.
   https://aws.amazon.com/caching/database-caching/
   Verified 2026-08-02. Corroborating source discussing lazy population as an
   application-level query-then-cache flow, consulted alongside source 1.
