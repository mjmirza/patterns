---
name: No Caching Strategy
slug: no-caching-strategy
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Ad Hoc Caching, Accidental Cache, Cache by Hope, Undisciplined Caching]
first_described: "industry cache design practice, no single canonical origin"
maturity: established
related: [cache-aside, read-through-cache, write-through-cache, cache-stampede, circuit-breaker, bulkhead, throttling, stale-while-revalidate]
incompatible_with: [cache-as-database, no-store-everywhere]
verified: 2026-08-02
---

# No Caching Strategy

## 1. Name, aliases, and lineage

No Caching Strategy is the anti-pattern where a system uses caches, browser
headers, CDN rules, local maps, materialized views, or shared key-value stores
without a declared policy for what may be cached, how long it may live, how it
is invalidated, how misses are controlled, and how stale data is detected. The
term is descriptive rather than canonical. It does not have one named author or
one first publication. The lineage comes from three older bodies of practice:
HTTP caching semantics, database and application cache patterns, and production
capacity engineering.

HTTP gives the oldest shared vocabulary. RFC 9111 defines how HTTP caches store,
reuse, validate, and invalidate responses, and describes cache keys, freshness,
validation, `Vary`, `Cache-Control`, and stale reuse rules
(https://www.rfc-editor.org/rfc/rfc9111, verified 2026-08-02). MDN's HTTP
caching guide explains the practical split between private caches, shared
caches, managed caches, validation, `no-store`, `no-cache`, and cache busting
(https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching, verified
2026-08-02). Application caches use the same ideas with different names:
cache-aside, read-through, write-through, TTL, explicit invalidation, eviction,
and request coalescing.

The anti-pattern appears under several aliases in teams. **Ad Hoc Caching**
means each call site invents its own rule. **Accidental Cache** means the cache
exists because a framework, browser, CDN, ORM, database, or library turned it on
by default. **Cache by Hope** means engineers add `set(key, value)` and trust
that time-to-live values or manual deletes will work out. **Undisciplined
Caching** means the system has cache code but no ownership, contract, or
telemetry.

This entry treats No Caching Strategy as established, not canonical. The failure
mode is named by practitioners more often than by catalog authors. AWS
Well-Architected lists related caching anti-patterns, including caching data
that changes often, treating cached data as durable, ignoring consistency, and
not monitoring cache efficiency
(https://docs.aws.amazon.com/wellarchitected/2024-06-27/framework/perf_data_access_patterns_caching.html,
verified 2026-08-02). That set is close to the core of this entry, but the
anti-pattern here is wider: it covers a missing decision model across all cache
layers.

## 2. Problem and context

A service becomes slower or more expensive as traffic grows. The first response
is often local and reasonable: cache a query result, add a CDN rule, store a
computed object in Redis, add a browser `max-age`, memoize a function, or keep a
map inside a worker. Each step may be correct on its own. The anti-pattern
appears when the system accumulates several of these steps with no shared answer
to basic questions.

What is the cache key. What is the source of truth. What level of staleness is
allowed. Which writes invalidate which reads. Which layer owns the value. What
happens when the cache is cold. What happens when a popular key expires. Which
data is private. Which data may be shared. Which metric proves that the cache
helps. Which alert fires when it hurts.

The context is a read-heavy or compute-heavy system where repeated work exists.
Examples include product pages, account summaries, timeline fan-out, feature
flags, access-control checks, generated recommendations, dashboards, static
assets, API responses, and expensive derived data. In such systems, caching is
not a small performance trick. It changes the correctness model. A read may
return old data by design. A write may need to clear more than one key. A cache
miss may become the most expensive path in the system. A cache warm-up plan may
decide whether a deploy is boring or painful.

The failure is not "no cache." Some systems can run well without a cache. The
failure is using caches without a strategy. That is why the name is No Caching
Strategy rather than No Cache. A system with no cache and enough capacity is
plain. A system with five cache layers and no rules is fragile.

Engineering judgement. The smell usually enters quietly because the early wins
are real. A single cached query can reduce latency and database load. A single
CDN rule can cut bandwidth. A local memoized function can remove repeated work
inside one request. The debt appears later, when different caches disagree,
operators cannot explain a stale result, and the backend is sized around a hit
rate that nobody measures.

## 3. Forces

Engineering judgement. This anti-pattern is a bad balance among real forces,
not a refusal to care about performance.

- **Latency.** The system wants shorter response time. Caching can satisfy a
  request without touching a slow database, service, disk, or remote API. AWS
  describes caching as a high-speed layer that stores transient copies for later
  reuse (https://aws.amazon.com/caching/, verified 2026-08-02). No Caching
  Strategy chases this force without defining correctness boundaries.
- **Coupling.** A cache couples reads to writes through invalidation. If the
  coupling is not named, it spreads through controllers, jobs, hooks, cron
  tasks, and CDN dashboards. The source code may show a read path but hide the
  write path that makes it safe.
- **Consistency.** Cached data is often stale by design. RFC 9111 permits
  reuse only under freshness, validation, or allowed stale rules for HTTP
  responses (https://www.rfc-editor.org/rfc/rfc9111, verified 2026-08-02).
  Application caches need an equivalent rule, even when they do not use HTTP.
- **Operability.** A cache must be visible. Without hit rate, miss cost, key
  count, eviction, invalidation, and stale-serve metrics, the team cannot tell
  whether the cache is saving the origin or masking a capacity fault.
- **Cost.** A good cache can cut database, compute, egress, and third-party API
  spend. A poor cache can increase cost by duplicating data, causing stampedes,
  or forcing broad invalidations that reload the same values many times.
- **Team topology.** Caches sit between ownership areas. Frontend teams set
  browser headers. Platform teams tune CDN policy. Backend teams populate Redis.
  Data teams own derived tables. No Caching Strategy lets each group optimize
  its layer while the user sees one inconsistent product.
- **Cognitive load.** Every cache adds hidden state. A reader must know whether
  a value came from memory, Redis, a CDN, a browser, a service worker, an ORM
  identity map, or the database. A strategy lowers load by making common
  answers boring.
- **Failure isolation.** Caches can protect an origin from spikes, but they can
  become hard dependencies. Google SRE describes services whose steady-state
  capacity depends on warm caches and warns that cold caches can put the service
  at outage risk (https://sre.google/sre-book/addressing-cascading-failures/,
  verified 2026-08-02).

The anti-pattern favors local latency relief and short-term delivery speed. It
sacrifices consistency, diagnosis, cost control, and capacity planning. A
healthy caching strategy does not remove the trade-off. It makes the trade-off
explicit per data class.

## 4. Applicability and non-applicability

Reach for the corrective pattern, a declared caching strategy, when these
conditions hold.

- A read path repeats the same database query, RPC, file read, render, or
  computation for many users or many requests.
- The data has a named freshness tolerance, such as "profile changes visible in
  sixty seconds" or "inventory must validate against the source during
  checkout."
- The origin cannot handle cold-cache traffic at expected peak, or cold-cache
  traffic would require wasteful overprovisioning.
- More than one cache layer can store the same answer, such as browser plus CDN
  plus service cache.
- A write path changes data that read paths cache under more than one key.
- Personalized or permission-scoped data could cross a private or shared cache
  boundary.
- Operators need to answer stale-data tickets or backend overload alerts from
  telemetry rather than code archaeology.

Do NOT apply caching as the answer in these cases.

- **The origin is fast, cheap, and sized for peak load.** A cache would add a
  second state store and an invalidation problem without buying useful room.
- **The data has no acceptable stale window.** A bank transfer execution result,
  a one-time token, or a permission revocation check may need source-of-truth
  reads. RFC 9111's `must-revalidate` rule exists for responses that cannot be
  reused stale without successful validation (https://www.rfc-editor.org/rfc/rfc9111,
  verified 2026-08-02).
- **The access pattern scans unique keys.** Caching a stream where each key is
  rarely requested again fills memory while producing few hits. AWS warns that
  some access patterns are not suited to caching, such as broad sweeps through a
  changing key space (https://aws.amazon.com/caching/best-practices/, verified
  2026-08-02).
- **The value is larger than the work it saves.** If serialization, transfer,
  compression, and memory pressure cost more than recomputation, the cache is a
  tax.
- **The value includes secrets or personal data and the cache boundary is
  shared.** Use private client storage or no shared cache. MDN states that
  personalized content in a shared cache can leak information and describes the
  `private` directive for browser-local storage
  (https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching, verified
  2026-08-02).
- **The write path cannot name the reads it invalidates.** If the domain model
  cannot express the relation, adding cache keys will hide the design gap.
- **The team cannot observe misses and stale reads.** A cache that nobody can
  see will become folklore. Start with measurement or keep the read direct.
- **The cache is being used as durable storage.** AWS Well-Architected calls out
  relying on cached data as if it were durably stored and always available as a
  common anti-pattern
  (https://docs.aws.amazon.com/wellarchitected/2024-06-27/framework/perf_data_access_patterns_caching.html,
  verified 2026-08-02).

Non-applicability list. Do not use this anti-pattern label for a deliberate
source-of-truth-only design, a read path whose cache was removed after a
measured miss rate, a security choice to prevent storage, or a prototype that
has no shared cache and no production traffic. Those may be valid engineering
choices. The anti-pattern needs two facts: cache behavior exists, and the rules
for it are absent or contradictory.

## 5. Structure

No Caching Strategy has recognizable participants.

- **Origin.** The database, service, file store, external API, render pipeline,
  or compute function that owns the current value.
- **Reader.** The code path that wants the value. It may be a handler, worker,
  batch job, edge function, browser, or service.
- **Writer.** The path that changes the origin value. It may be a command
  handler, admin panel, import job, webhook, migration, or scheduled task.
- **Cache layer.** Any store that can serve a copy. Common layers are browser
  cache, CDN, reverse proxy, in-process map, Redis, Memcached, ORM cache, query
  result cache, and materialized view.
- **Cache key.** The identity rule for the copy. A good key includes every input
  that changes the answer. An incomplete key mixes users, permissions, locales,
  devices, versions, or query parameters.
- **Freshness policy.** The rule for whether a cached value can be returned.
  Examples are TTL, validator, version token, event invalidation, write-through,
  or immutable asset hashing.
- **Invalidator.** The path that removes or marks copies stale. It can be a
  write hook, event consumer, CDN purge, tag purge, version bump, or short TTL.
- **Miss controller.** The part that prevents a miss from overloading the
  origin. Techniques include request coalescing, single-flight loading, stale on
  error, background refresh, rate limiting, and backpressure.
- **Observer.** Logs, metrics, traces, and dashboards that make the cache
  behavior visible.

In the anti-pattern, these participants exist by accident. Readers know a key.
Writers may know a different key. The invalidator may run in another repository.
The TTL may be copied from an example. The CDN may add a default rule. The
observer may record only origin latency, which makes cache errors appear as
database or API problems.

The corrected structure names the data classes first. For each class, record
owner, origin, cache layers, key schema, freshness, invalidation, miss control,
privacy class, and telemetry. The cache code then implements that record rather
than inventing policy at each call site.

## 6. ASCII structure diagram

```
No Caching Strategy

   +---------+        reads         +-----------+
   | Reader  | -------------------> |  Origin   |
   +---------+                      +-----------+
        |                                ^
        | ad hoc get/set                 | writes
        v                                |
   +------------+                   +---------+
   | Cache A    |                   | Writer  |
   | ttl = ?    |                   +---------+
   | key = ?    |                        |
   +------------+                        | maybe purge
        ^                                v
        | browser, CDN, Redis       +------------+
        +-------------------------- | Cache B    |
                                    | rule = ?   |
                                    +------------+

Missing contracts:

   data class -> key schema -> freshness -> invalidation -> miss control
   ownership  -> privacy    -> metrics   -> cold start   -> runbook
```

Corrected shape

```
   +---------------- Caching Policy for ProductSummary ----------------+
   | origin: product-db                                                |
   | layers: CDN, service Redis                                        |
   | key: product:{id}:locale:{locale}:priceVersion:{version}          |
   | freshness: 60 s for browse, source read for checkout              |
   | invalidation: ProductChanged event, CDN tag product:{id}          |
   | miss control: single-flight load, stale-if-error for browse       |
   | privacy: public, no user attributes in key or value               |
   | telemetry: hit rate, miss cost, stale served, purge lag           |
   +-------------------------------------------------------------------+
             |                     |                     |
             v                     v                     v
        Reader code           Writer code           Operations
```

## 7. Dynamics

The runtime failure often begins with a successful optimization.

```
Request        Reader        Cache        Origin        Writer
  |              |             |             |             |
  |-- read A --->|             |             |             |
  |              |-- get K --->|             |             |
  |              |<-- miss ----|             |             |
  |              |----------- load -------->|             |
  |              |<---------- value --------|             |
  |              |-- set K, ttl ? --------->|             |
  |<-- value ----|             |             |             |
  |              |             |             |             |
  |              |             |             |-- update -->|
  |              |             |             |<-- ok ------|
  |              |             |             |             |
  |-- read A --->|             |             |             |
  |              |-- get K --->|             |             |
  |              |<-- old -----|             |             |
  |<-- stale ----|             |             |             |
```

The second failure is a cold or expired hot key.

```
Many requests        Cache           Miss controller          Origin
     |                 |                    |                   |
     |-- get hot K --->|                    |                   |
     |<-- miss --------|                    |                   |
     |-- get hot K --->|                    |                   |
     |<-- miss --------|                    |                   |
     |-- get hot K --->|                    |                   |
     |<-- miss --------|                    |                   |
     |                 |-- no coalescing -->|                   |
     |                 |--------------------------------------->|
     |                 |--------------------------------------->|
     |                 |--------------------------------------->|
     |                 |                    |          overloaded
```

In a corrected flow, the first miss owns the load, other requests wait or get an
allowed stale value, and the write path has a named invalidation route.

```
Many requests        Cache           Single flight          Origin
     |                 |                  |                   |
     |-- get hot K --->|                  |                   |
     |<-- miss --------|                  |                   |
     |                 |-- load K ------>|                   |
     |                 |                  |-- one load ------>|
     |-- get hot K --->|                  |                   |
     |<-- wait/stale --|                  |                   |
     |                 |                  |<-- value ---------|
     |                 |<-- fill K -------|                   |
     |<-- value -------|                  |                   |
```

RFC 9111 names request collapse as a cache behavior where multiple incoming
misses may be combined into one forward request
(https://www.rfc-editor.org/rfc/rfc9111, verified 2026-08-02). The same runtime
idea appears in application caches under names such as single-flight, coalesced
loading, or stampede protection.

## 8. Implementation variants

**Cache-aside with owned invalidation.** The reader checks a cache, loads from
the origin on miss, stores the value, and returns it. The writer deletes or
versions the same key. AWS describes lazy caching, also called cache-aside, as a
common approach where the application checks the cache, queries the database on
miss, stores the value, and returns it
(https://aws.amazon.com/caching/best-practices/, verified 2026-08-02). Trade-off:
simple reads, but every writer must know the invalidation rule.

**Read-through cache.** The cache client owns the loader. Callers ask the cache
for a key and the cache invokes a loader on miss. Trade-off: repeated miss logic
is centralized, but the cache library now knows how to call the origin.

**Write-through cache.** Writes update the cache and origin in the same path.
Trade-off: fresh reads after a successful write, but write latency and write
failure handling become harder.

**Write-behind cache.** Writes land in the cache or queue and reach the origin
later. Trade-off: low write latency, but data loss and ordering risks must be
owned. This is rarely the right repair for No Caching Strategy unless the system
already has durable queues and replay.

**TTL-only cache.** Values expire after a fixed time. Trade-off: easy to ship,
but freshness is a guess. It works for data where stale windows are acceptable
and writes do not need immediate visibility.

**Versioned key cache.** The key includes a version, revision, hash, ETag, build
id, or updated-at token. Trade-off: invalidation becomes a new key rather than a
delete, but orphaned old keys need eviction.

**Tag or prefix purge.** Cached objects carry tags such as `product:17`, and a
write purges that tag. Cloudflare documents purge by URL, hostname, tag, prefix,
and whole-zone purge (https://developers.cloudflare.com/cache/how-to/purge-cache/,
verified 2026-08-02). Trade-off: broad changes are easy, but purge volume and
rate limits become capacity concerns.

**Stale-while-revalidate.** Readers receive a stale value while one background
load refreshes it. RFC 9111 defines core stale response rules, while MDN
documents the `stale-while-revalidate` directive among standard cache-control
directives (https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control,
verified 2026-08-02). Trade-off: low tail latency, but users may see old data
inside the allowed window.

**Stale-if-error.** The cache serves an old value when the origin fails. Trade-off:
better availability, but a business owner must approve which data may be stale
during an outage.

**Negative caching.** Misses or errors are cached for a short time. Trade-off:
protects the origin from repeated absent-key lookups, but can hide newly created
data until the negative entry expires.

**Local in-process cache.** A process keeps hot values in memory. Trade-off:
very low latency, but each process has a different view, warm-up repeats after
restart, and memory pressure is local.

**Shared distributed cache.** Redis, Memcached, or a managed cache is shared by
many processes. Trade-off: shared hit rate and central eviction policy, but
every read adds another network hop and the cache service becomes part of the
request path.

**No-store by policy.** Some data should not be cached. This is still a caching
strategy because it states a rule. MDN describes `no-store` as the directive
that asks caches not to store a response
(https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching, verified
2026-08-02). Trade-off: highest freshness and lower leakage risk, but no cache
relief.

## 9. Known production uses

The named systems below are production evidence that large services treat cache
policy as architecture, not scattered syntax.

**Facebook memcache.** Meta's engineering article says Facebook began using
memcached in 2005 as page-load queries grew, and later built a cache
infrastructure serving billions of requests per second
(https://engineering.fb.com/2013/04/15/core-infra/scaling-memcache-at-facebook/,
verified 2026-08-02). The article names social graph fan-out, hot objects, and
fast product changes as scaling pressures. This is the opposite of the
anti-pattern: the cache is an owned infrastructure layer.

**Netflix EVCache.** Netflix's EVCache docs describe an in-memory distributed
data service backed by memcached, with clusters in zones, local-zone reads,
multi-zone writes, TTL-bound inconsistency, retries, fallback behavior, and
consistency repair options (https://netflix.github.io/EVCache/introduction/,
verified 2026-08-02). The feature page describes replicated cache clusters,
topology-aware operations, fallbacks, global replication, and operational
insight (https://netflix.github.io/EVCache/features/, verified 2026-08-02).
Those choices show a declared caching strategy around latency, availability,
and accepted inconsistency.

**Wikimedia CDN.** Wikimedia describes MediaWiki support for cache proxies using
`Cache-Control` headers, HTTP PURGE on page edits, and rendering limits so
content can be cached predictably. The same article says Wikimedia moved from
Squid to Varnish and Apache Traffic Server and added caching clusters across
regions (https://diff.wikimedia.org/2023/05/08/around-the-world-how-wikipedia-became-a-multi-datacenter-deployment/,
verified 2026-08-02). This is production use of explicit HTTP caching and purge
rules at public-web scale.

**Cloudflare cache purge.** Cloudflare documents production cache management
through purge by URL, hostname, tag, prefix, purge everything, varied images,
and zone versions (https://developers.cloudflare.com/cache/how-to/purge-cache/,
verified 2026-08-02). The API docs describe the `purge_cache` endpoint and
cache-key details for single-file purge with headers
(https://developers.cloudflare.com/api/resources/cache/methods/purge/, verified
2026-08-02). This use matters because CDN caching without purge ownership is
one of the common routes into No Caching Strategy.

## 10. Consequences

Engineering judgement.

Negative consequences.

- Stale data becomes a customer-visible defect rather than an accepted product
  rule.
- Cache misses become unbounded load on the origin, and a hot-key expiry can
  turn a success path into a traffic spike.
- Writes grow hidden responsibilities. A writer must update the origin, publish
  events, clear service caches, purge CDN objects, and maybe change asset
  versions. Without a strategy, one of those steps is missed.
- Capacity plans become fictional. The team sizes the origin around a hit rate
  but does not know the hit rate under deploy, restart, regional failover, or
  incident traffic.
- Privacy boundaries blur. A shared cache may store a response that was meant
  for one user unless `private`, `no-store`, key scoping, or equivalent policy
  blocks it.
- Debugging slows down. A stale value may come from browser cache, CDN, edge
  function, service memory, Redis, ORM, or a materialized view.
- Cost can rise. Low-hit caches pay storage, serialization, network, and
  invalidation costs while still loading the origin.
- Teams lose trust in caches. After enough stale-data incidents, engineers add
  broad purge calls or `no-store` headers everywhere, destroying valid cache
  wins.

Positive consequences, if the anti-pattern is corrected.

- Data classes get explicit freshness contracts.
- Cache keys become reviewable design artifacts.
- Writes and invalidation paths can be tested together.
- Operators can see hit rate, miss cost, stale serves, purge lag, and cold-start
  behavior.
- Product owners can choose where stale data is acceptable, instead of leaving
  that choice inside incidental TTLs.
- Security review can distinguish public, private, permission-scoped, and
  secret-bearing responses.

The main cost of correction is design time. A cache strategy asks teams to write
down rules they previously left implicit. That cost is real, but it is smaller
than diagnosing a cache incident during peak traffic.

## 11. Failure modes and misuse

Engineering judgement. Each item is written as an observable triple.

**Symptom.** Users see an old profile photo, price, feature flag, or article
after a successful update. Support can reproduce it only in one browser or one
region. **Cause.** The write path changed the origin but did not invalidate all
cache layers or all key variants. **Fix.** Map every cached read for that data
class, add event or tag invalidation, and add a test that writes once then reads
through each cache path.

**Symptom.** Database CPU spikes at the top of the hour, after deploy, or after
a cache flush. Application latency rises at the same time as cache hit rate
falls. **Cause.** Many hot keys expire together, or a broad purge creates a cold
cache with no miss coalescing. **Fix.** Add TTL jitter, single-flight loading,
stale-while-revalidate, gradual warm-up, and origin backpressure.

**Symptom.** One user receives another user's dashboard, recommendations, or
account summary from a shared cache. **Cause.** The key omits user, tenant,
authorization state, locale, or cookie-varying inputs, or a shared HTTP cache
stores personalized content. **Fix.** Mark the response private or no-store,
include all permission inputs in the key, and add a privacy test that compares
two users with the same URL.

**Symptom.** Redis memory climbs until eviction begins, then hit rate drops and
origin load rises. **Cause.** Keys are never expired, key cardinality is higher
than expected, or versioned keys are abandoned without eviction. Redis documents
eviction policy choices when memory limits are reached
(https://redis.io/docs/latest/develop/reference/eviction/, verified
2026-08-02). **Fix.** Define max memory, eviction policy, TTL, key cardinality
budget, and alerts for memory, evictions, and rejected writes.

**Symptom.** A rare object remains wrong for hours even though common objects
refresh quickly. **Cause.** The cache relies on demand-driven refresh, and the
object is not read often enough to repair itself after an origin change.
**Fix.** Use write invalidation, versioned keys, or a repair job for low-read
objects whose correctness matters.

**Symptom.** A deploy is followed by mixed JavaScript, CSS, or API schema
versions in the browser. **Cause.** Long-lived assets and short-lived HTML use
the same cache rule, or assets are mutated under stable URLs. **Fix.** Use
hashed asset URLs with long TTLs, keep HTML on validation or short freshness,
and test an upgrade from the previous build.

**Symptom.** Operators purge everything to fix one bad page, then the origin
falls over. **Cause.** The system lacks precise purge keys or tags. **Fix.**
Add object tags, prefixes, version keys, or entity-scoped purge operations, and
rate-limit broad purge tools.

**Symptom.** A cache outage becomes a full application outage even though the
origin is healthy. **Cause.** The cache was treated as a capacity dependency or
durable store, and callers have no fallback or load shedding. **Fix.** Decide
whether the cache is a latency cache or capacity cache, then add fallback,
degraded mode, or explicit unavailability semantics.

## 12. Trade-off matrix

| Force | No Caching Strategy | Deliberate No Cache | Cache-Aside | Read-Through Cache | CDN Edge Caching | Materialized View |
|---|---|---|---|---|---|---|
| Latency | Unpredictable. Hits are fast, misses hurt | Predictable origin latency | Good on hot reads | Good on hot reads | Excellent for public content | Good for derived reads |
| Coupling | Hidden read-write coupling | Low cache coupling | Writer must invalidate | Loader coupling moves to cache client | HTTP and purge coupling | Data pipeline coupling |
| Consistency | Accidental stale windows | Source is current | Tunable by TTL and delete | Tunable by loader policy | Tunable by headers and purge | Tunable by refresh model |
| Operability | Poor. Few useful signals | Simple origin metrics | Hit, miss, stale, delete metrics | Central miss metrics | CDN hit and purge metrics | Lag and refresh metrics |
| Cost | Can waste cache and origin spend | Higher origin spend | Lower origin spend on hot keys | Lower origin spend on hot keys | Lower egress and origin load | Storage and refresh cost |
| Team topology | Cross-team blame | Clear owner at origin | App owns policy | Platform or library owns loader | Edge and app teams share policy | Data team shares ownership |
| Cognitive load | High because rules differ | Low | Medium | Medium | Medium for HTTP semantics | Medium to high |
| Cold start risk | Unknown | None beyond origin peak | Known if tested | Known if tested | Regional cold misses | Refresh or backfill lag |
| Privacy risk | High when keys are incomplete | Low cache leakage | Medium if keys are wrong | Medium if keys are wrong | High for personalized HTTP | Medium if rows mix scopes |

Reading of the table. Deliberate No Cache is often better than accidental cache
state. Cache-Aside is the usual first repair when the application can own both
read and write logic. Read-Through helps when many readers need one loader
contract. CDN Edge Caching is strongest for public or carefully varied HTTP
responses. Materialized View fits expensive derived data where refresh lag can
be measured and named.

## 13. Related and incompatible patterns

- **Cache-Aside.** The main replacement in application code. It keeps the cache
  passive and puts policy in the application. It conflicts with No Caching
  Strategy only when each call site invents its own version.
- **Read-Through Cache.** A replacement when miss handling should be centralized
  in a cache client. It lowers repetition but can hide origin calls unless
  telemetry is required.
- **Write-Through Cache.** Useful when reads after writes must see a fresh cache
  entry. It conflicts with ad hoc invalidation because writes become the policy
  point.
- **Write-Behind.** Related but dangerous. It should be paired with durable
  queues, ordering rules, and replay. Without those, it turns a cache into an
  unsafe write buffer.
- **Stale-While-Revalidate.** A latency and availability companion. It replaces
  synchronized expiry with background refresh when old data is acceptable for a
  declared window.
- **Circuit Breaker and Bulkhead.** Complements for cache misses. They limit
  damage when the origin slows down or a cache cluster has trouble.
- **Throttling.** Complements miss control by keeping hot-key reloads and broad
  purges from overwhelming shared systems.
- **Event-Driven Invalidation.** A common repair. Domain events carry enough
  identity to delete or version cached reads after writes.
- **Cache Stampede Protection.** A required companion for hot keys. It prevents
  many identical misses from becoming many origin calls.
- **Cache as Database.** Incompatible. A cache can be a configured data service
  for transient data, as EVCache describes for some Netflix uses
  (https://netflix.github.io/EVCache/features/, verified 2026-08-02), but a
  normal cache of source-of-truth data must not be treated as durable storage.
- **No-Store Everywhere.** A reaction pattern, not a strategy. It avoids stale
  data by throwing away good cache cases. Use it only for data classes that need
  it.

## 14. Refactoring path in and out

Refactoring in starts with inventory, not code.

1. List every cache layer that can affect the user path: browser, CDN, service
   worker, edge, reverse proxy, application memory, Redis, Memcached, ORM,
   database result cache, and materialized views.
2. Pick one high-value data class. Do not start with every key in the system.
   Use traffic, cost, stale-data tickets, or incident history to choose.
3. Write the contract: origin, owner, allowed staleness, privacy class, key
   schema, cache layers, invalidation trigger, miss control, cold-start stance,
   and metrics.
4. Move key construction into one named function or type. Include every input
   that changes the result. Add tests for user, tenant, locale, authorization,
   version, and query parameters.
5. Move cache reads through one small wrapper. The wrapper records hit, miss,
   load time, stale serve, and error.
6. Connect writer and invalidator. Prefer versioned keys or entity-scoped
   invalidation over broad purge.
7. Add miss coalescing for hot keys before lowering TTLs or adding broad purge
   operations.
8. Add dashboard panels and alerts before declaring the cache safe.
9. Run a cold-cache test. Flush or bypass the cache in staging, replay a peak
   slice, and record whether the origin can survive.
10. Repeat per data class, then delete one-off cache calls that do not match a
   contract.

Refactoring out is needed when the cache no longer earns its place.

1. Prove low value with hit rate, miss cost, memory use, invalidation cost, and
   stale-data incidents.
2. Add a feature flag or config switch that bypasses the cache for one data
   class.
3. Compare latency, origin load, error rate, and cost with the cache bypassed.
4. If the origin remains healthy and cost is acceptable, remove the cache
   wrapper and delete invalidation code in the same change.
5. Remove dashboards and alerts only after the stale keys have expired or been
   purged.
6. Record the decision so the same cache is not reintroduced later by local
   optimization.

The named refactorings are Extract Function for key creation, Introduce
Parameter Object for cache policy, Replace Magic Number with Symbolic Constant
for TTLs, Move Method for invalidation ownership, and Inline Class when a cache
wrapper proves unnecessary.

## 15. Testing and verification

Engineering judgement. Caching tests must cover correctness, load behavior, and
operational visibility.

Correctness tests.

- **Key isolation tests.** Two users, tenants, locales, permissions, or feature
  versions that should differ must produce different keys or different
  non-cacheable decisions.
- **Write then read tests.** A write to the origin must make the next read
  return the new value through the normal cache path or through a stated stale
  allowance.
- **TTL boundary tests.** A fake clock should test fresh, expired, stale allowed,
  and stale forbidden paths.
- **Negative cache tests.** Absent data cached for a short time must not hide a
  later create beyond the allowed window.
- **Header tests.** HTTP responses should assert `Cache-Control`, `ETag`,
  `Vary`, and privacy directives for representative public, private, and
  no-store pages.
- **Purge tests.** A change to an entity should purge or version every cached
  shape of that entity, including list pages and detail pages.

Load and failure tests.

- **Stampede test.** Fire many concurrent requests for one expired key and
  assert that the origin loader runs once or within a small bound.
- **Cold-cache test.** Start with an empty cache and run a peak traffic slice.
  The result decides whether the cache is a latency cache or a capacity cache.
- **Cache outage test.** Make Redis, Memcached, or the CDN unavailable and
  check whether the service falls back, degrades, or fails according to policy.
- **Broad purge test.** Purge a tag, prefix, or region and measure origin load
  during refill.
- **Serialization test.** Store and load the cached value across deployed
  versions so old values do not crash new code.

Verification techniques.

- Use fake clocks rather than sleeps.
- Use loader counters to prove hit and miss behavior.
- Use contract tests shared by each cache layer for the same data class.
- Use trace assertions in integration tests so cache decisions are visible.
- Run browser tests for static asset upgrade behavior.

The examples below were compiled or run locally with `npx tsc` plus `node`,
`python3`, `go run`, and `rustc`.

## 16. Observability signals

Engineering judgement. A cache without telemetry is an invisible production
dependency.

Record these metrics per data class and cache layer.

- Hit count, miss count, and hit ratio.
- Loader latency and loader error rate.
- Stale value served count, with reason.
- Invalidation count, source, fan-out, and lag.
- Eviction count and memory used.
- Key count and top key cardinality.
- Cache payload size before and after serialization.
- Miss coalescing waiters per key.
- Cold-start duration after deploy, restart, or regional failover.
- Origin load attributed to cache misses.
- Purge rate and broad purge count.

Trace attributes should include cache layer, data class, decision, key hash, hit
or miss, freshness age, and loader duration. Do not put raw user identifiers or
secrets in trace fields. Use stable hashes when a key component is sensitive.

A healthy dashboard shows hit ratios near expected values for each data class,
flat loader latency, low eviction churn, bounded key cardinality, small purge
lag, and no unexplained broad purge. A failing dashboard shows miss spikes after
deploy, rising stale serves outside a launch window, many unique one-hit keys,
evictions followed by origin load, purge lag after writes, or one hot key with
many waiters.

Log events should be rare and useful. Log cache policy load at startup, broad
purge, stale-if-error activation, loader failure after miss, duplicate key
registration, and rejected cache writes due to size or privacy policy. Avoid
logging every hit on high-traffic paths unless sampling is in place.

Runbooks should answer five questions. How do we bypass this cache. How do we
purge one entity. How do we warm a region. How do we tell stale data from an
origin bug. How do we lower origin load if the cache is empty.

## 17. Security and privacy implications

The security risk is not caching itself. The risk is storing or reusing a value
outside its authority boundary.

Personal data must not cross from a private context into a shared cache. MDN
warns that personalized content stored outside a private cache can be visible to
other users and recommends `private` for responses meant only for the user's
browser cache (https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching,
verified 2026-08-02). For application caches, the equivalent is a key that
includes tenant and permission scope, or a policy that forbids shared storage.

Authorization changes are write events. A role removal, logout, password reset,
session revocation, plan downgrade, or account deletion must invalidate cached
answers that depend on the old authority state. If that invalidation cannot be
made reliable, read the source of truth for the security decision.

Cache poisoning is another risk. If an attacker can control headers, hostnames,
query parameters, or body fields that are missing from the cache key, they may
cause one response to be reused for another request. HTTP `Vary` exists because
request headers can change response selection, and RFC 9111 states that a cache
must not reuse a stored response when nominated `Vary` fields do not match
(https://www.rfc-editor.org/rfc/rfc9111, verified 2026-08-02). Application
caches need the same discipline for non-HTTP inputs.

Secrets should not be cached by default. Tokens, password reset links, signed
URLs, private documents, raw payment data, and access decisions deserve an
explicit storage rule and a short lifetime if cached at all. Treat cache dumps,
snapshots, and debug tooling as sensitive because they may contain copied
production data.

Operational controls matter. Purge APIs can remove large fractions of capacity
protection. Cloudflare documents purge methods and limits for cache operations
(https://developers.cloudflare.com/cache/how-to/purge-cache/, verified
2026-08-02). In any system, broad purge rights should be limited, audited, and
rate-limited. A purge-all button is an outage tool unless the origin is sized
for the resulting cold cache.

## Code examples

The examples show small corrected strategies rather than the anti-pattern. Each
has one policy point: key, freshness, invalidation, and loader behavior are
visible in code.

### TypeScript

```typescript
type Loader<K, V> = (key: K) => V;
type Clock = () => number;

class CacheAside<K, V> {
  private values = new Map<K, { value: V; expiresAt: number }>();

  constructor(private readonly ttlMs: number, private readonly now: Clock) {}

  get(key: K, loader: Loader<K, V>): V {
    const found = this.values.get(key);
    if (found && found.expiresAt > this.now()) return found.value;
    const value = loader(key);
    this.values.set(key, { value, expiresAt: this.now() + this.ttlMs });
    return value;
  }

  invalidate(key: K): void {
    this.values.delete(key);
  }
}

let loads = 0;
let time = 1000;
const cache = new CacheAside<string, string>(50, () => time);
const loadUser = (id: string) => {
  loads += 1;
  return `user:${id}:v${loads}`;
};

console.log(cache.get("42", loadUser));
console.log(cache.get("42", loadUser));
time = 1060;
console.log(cache.get("42", loadUser));
console.log(`loads=${loads}`);
```

### Python

```python
from __future__ import annotations


class VersionedCache:
    def __init__(self) -> None:
        self.values: dict[str, tuple[int, str]] = {}

    def get(self, key: str, version: int, loader) -> str:
        found = self.values.get(key)
        if found and found[0] == version:
            return found[1]
        value = loader(key)
        self.values[key] = (version, value)
        return value

    def invalidate(self, key: str) -> None:
        self.values.pop(key, None)


loads = 0


def load_product(key: str) -> str:
    global loads
    loads += 1
    return f"product:{key}:load:{loads}"


cache = VersionedCache()
print(cache.get("sku-7", 3, load_product))
print(cache.get("sku-7", 3, load_product))
print(cache.get("sku-7", 4, load_product))
print(f"loads={loads}")
```

### Go

```go
package main

import "fmt"

type Entry struct {
    value     string
    expiresAt int
}

type ReadThroughCache struct {
    values map[string]Entry
    ttl    int
    now    int
}

func (c *ReadThroughCache) Get(key string, load func(string) string) string {
    if entry, ok := c.values[key]; ok && entry.expiresAt > c.now {
        return entry.value
    }
    value := load(key)
    c.values[key] = Entry{value: value, expiresAt: c.now + c.ttl}
    return value
}

func (c *ReadThroughCache) Invalidate(key string) {
    delete(c.values, key)
}

func main() {
    loads := 0
    cache := ReadThroughCache{values: map[string]Entry{}, ttl: 10, now: 100}
    load := func(key string) string {
        loads++
        return fmt.Sprintf("order:%s:v%d", key, loads)
    }
    fmt.Println(cache.Get("9", load))
    fmt.Println(cache.Get("9", load))
    cache.now = 120
    fmt.Println(cache.Get("9", load))
    fmt.Printf("loads=%d\n", loads)
}
```

### Rust

```rust
use std::collections::HashMap;

#[derive(Clone)]
struct Entry {
    value: String,
    expires_at: u64,
}

struct Cache {
    values: HashMap<String, Entry>,
    ttl: u64,
    now: u64,
}

impl Cache {
    fn get<F>(&mut self, key: &str, load: F) -> String
    where
        F: FnOnce(&str) -> String,
    {
        if let Some(entry) = self.values.get(key) {
            if entry.expires_at > self.now {
                return entry.value.clone();
            }
        }
        let value = load(key);
        self.values.insert(
            key.to_string(),
            Entry { value: value.clone(), expires_at: self.now + self.ttl },
        );
        value
    }
}

fn main() {
    let mut loads = 0;
    let mut cache = Cache { values: HashMap::new(), ttl: 5, now: 10 };
    println!("{}", cache.get("a", |key| {
        loads += 1;
        format!("feature:{}:{}", key, loads)
    }));
    println!("{}", cache.get("a", |_| unreachable!()));
    cache.now = 20;
    println!("{}", cache.get("a", |key| {
        loads += 1;
        format!("feature:{}:{}", key, loads)
    }));
    println!("loads={}", loads);
}
```

## 18. References

- Mark Nottingham, RFC 9111, "HTTP Caching", Internet Standard, sections 2, 3,
  4, 4.1, 4.2, 4.2.4, 4.4, and 5.2, https://www.rfc-editor.org/rfc/rfc9111,
  verified 2026-08-02.
- MDN Web Docs, "HTTP caching", sections on private caches, shared caches,
  managed caches, `no-store`, `no-cache`, validation, and cache busting,
  https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching, verified
  2026-08-02.
- MDN Web Docs, "Cache-Control header", directive reference,
  https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control,
  verified 2026-08-02.
- Amazon Web Services, "What is Caching?", overview of cache purpose and storage
  model, https://aws.amazon.com/caching/, verified 2026-08-02.
- Amazon Web Services, "Caching Best Practices", sections "How to apply
  caching" and "Caching design patterns",
  https://aws.amazon.com/caching/best-practices/, verified 2026-08-02.
- AWS Well-Architected Framework, "PERF03-BP05 Implement data access patterns
  that utilize caching", common anti-patterns and implementation guidance,
  https://docs.aws.amazon.com/wellarchitected/2024-06-27/framework/perf_data_access_patterns_caching.html,
  verified 2026-08-02.
- Redis Documentation, "Key eviction", eviction policy reference,
  https://redis.io/docs/latest/develop/reference/eviction/, verified
  2026-08-02.
- Rajesh Nishtala and Venkat Venkataramani, Meta Engineering, "Scaling memcache
  at Facebook", 2013-04-15,
  https://engineering.fb.com/2013/04/15/core-infra/scaling-memcache-at-facebook/,
  verified 2026-08-02.
- Netflix Open Source, "EVCache Introduction",
  https://netflix.github.io/EVCache/introduction/, verified 2026-08-02.
- Netflix Open Source, "EVCache Features",
  https://netflix.github.io/EVCache/features/, verified 2026-08-02.
- Wikimedia Diff, "Around the world. How Wikipedia became a multi-datacenter
  deployment", 2023-05-08,
  https://diff.wikimedia.org/2023/05/08/around-the-world-how-wikipedia-became-a-multi-datacenter-deployment/,
  verified 2026-08-02.
- Cloudflare Docs, "Purge cache",
  https://developers.cloudflare.com/cache/how-to/purge-cache/, verified
  2026-08-02.
- Cloudflare API Docs, "Purge Cached Content",
  https://developers.cloudflare.com/api/resources/cache/methods/purge/,
  verified 2026-08-02.
- Google SRE, "Addressing Cascading Failures", sections on resource exhaustion
  and cold caching,
  https://sre.google/sre-book/addressing-cascading-failures/, verified
  2026-08-02.
