---
name: Cache Stampede
slug: cache-stampede
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Dog-Piling, Cache Herd, Dogpile Effect, Thundering Herd on a Cache]
first_described: "Community usage, term traced by Wikipedia to caching and web operations literature circa 2009"
maturity: canonical
related: [circuit-breaker, bulkhead, cache-aside, lazy-initialization, singleton]
incompatible_with: []
verified: 2026-08-02
---

# Cache Stampede

## 1. Name, aliases, and lineage

The canonical name in wide industry use is cache stampede. The Wikipedia entry
for the concept opens with the definition that a cache stampede, also known as
dog-piling, is a type of cascading failure that can occur when massively
parallel computing systems with caching mechanisms come under very high load
([Wikipedia, Cache stampede](https://en.wikipedia.org/wiki/Cache_stampede),
verified 2026-08-02). The same article traces two of the earliest
written treatments of the problem to Patrick Galbraith's book on Apache,
MySQL, and memcached, published in 2009, and to John Allspaw and Jesse
Robbins' collection *Web Operations. Keeping the Data On Time*, published in
2010, both cited on the Wikipedia page as the sources for the term entering
common web-operations vocabulary.

The pattern is one member of a broader family that the operating systems
community had already named the thundering herd problem. Wikipedia's entry
for thundering herd describes it as a performance-degrading phenomenon in
computer science and computer networking that occurs when a large number of
processes or threads are simultaneously awakened, typically in response to a
specific event or the availability of a resource, and it states plainly that
when the phenomenon shows up specifically in a caching system it is often
referred to as a cache stampede
([Wikipedia, Thundering herd problem](https://en.wikipedia.org/wiki/Thundering_herd_problem),
verified 2026-08-02). The same page traces the thundering herd name to
two classic kernel-level cases, multiple processes blocked in `accept()` on
one listening socket, all woken when a single connection arrives though only
one process can accept it, and multiple threads or processes waiting on the
same scheduling event. It also names the modern mitigation the kernel took at
the socket layer, the Linux `EPOLLEXCLUSIVE` flag, which wakes only as many
waiters as are needed rather than all of them. That flag is the socket-layer
sibling of the cache-layer techniques this entry catalogs, both are answers to
the same underlying shape, many waiters, one event, only one waiter should
actually act.

Cache stampede is not itself a name from a formal catalog the way the
Gang of Four patterns are. It is an anti-pattern name that crystallized from
repeated, independently observed operational incidents, which is why its
first-described attribution above is a description of usage rather than a
single paper. The rigorous, citable academic treatment came later, in Asaf
Vattani, Flavio Chierichetti and Keegan Lowenstein's paper "Optimal
Probabilistic Cache Stampede Prevention," published in the Proceedings of the
VLDB Endowment in 2015, which the Wikipedia cache stampede article names and
summarizes as the source of the probabilistic early expiration technique
covered in dimension 8 below. Dog-piling is the older, more colloquial
synonym, and it is still the term found in mailing-list threads, runbooks,
and internal wikis from the 2005 to 2012 era of large-scale web memcached
deployments, before "cache stampede" became the dominant phrase.

## 2. Problem and context

The shape that produces this anti-pattern is almost always the same three
ingredients arriving together.

First, a piece of computed or fetched data is expensive relative to how often
it is asked for. A database aggregate query that scans a large table, a
call to a slow or rate-limited upstream API, a machine-learned scoring pass,
a rendered page fragment, a cryptographic derivation, all of these cost far
more in latency or resource consumption than serving a value that is already
sitting in memory.

Second, that expensive value is cached with a time-to-live, because the
system correctly recognized that recomputing it on every request would be
unaffordable, and gave the cache entry an expiration so the data does not go
stale forever.

Third, and this is the ingredient that turns a sensible design into an
incident, many independent requesters ask for that same key at roughly the
same moment the entry expires. In a system with meaningful concurrency, this
is not a rare coincidence, it is close to guaranteed. A popular product page,
a widely shared social post, a homepage widget, a session-lookup key used by
every request from a given user, a rate-limit counter, a feature-flag
evaluation, all of these are read by a large fraction of a site's inbound
traffic within the same second. When the one cached answer for that key
expires, every one of those concurrent requesters observes a cache miss at
essentially the same instant, and, absent any coordination, every one of them
independently decides to go do the expensive work of recomputing the value.

The failure that follows is a multiplication, not an addition. If the
expensive computation alone would take, say, 200 milliseconds and consume one
database connection, and the origin was serving a steady 500 requests per
second for that key while it was cached, the stampede does not cost the
system one extra 200-millisecond computation, it costs the system up to 500
of them landing on the origin in the same instant, each holding a connection,
each competing for the same CPU, disk, or lock the origin needs, and each one
slowing every other one down. Because they slow each other down, the 200
millisecond computation now takes longer than 200 milliseconds under this new
contention, which keeps the cache miss window open longer, which lets even
more requests pile in before the first one finishes and refills the cache.
This is precisely the cascading failure language Wikipedia's definition uses,
the load does not merely spike, it can feed itself and refuse to recover on
its own, because the very act of recovering, recomputing the value, is what
is under contention.

The context in which this anti-pattern arises is therefore any read-heavy
system that layers a cache with an expiration in front of an expensive origin,
and whose concurrency is high enough, or whose traffic is bursty enough
around specific keys, that simultaneous misses on the same key are a realistic
event rather than a theoretical one. It is far more visible in systems with a
small number of extremely hot keys, a celebrity's profile page, a trending
product, the front page of a news site, than in systems where load is spread
evenly across millions of distinct keys, because an even spread makes
simultaneous collision on one specific key statistically rare even at high
total throughput.

## 3. Forces

The forces at play pull in genuinely opposite directions, and naming them
honestly is what separates a useful anti-pattern write-up from a scare story.

**Freshness versus origin protection.** A shorter time-to-live keeps served
data closer to the true current state, which end users and correctness both
want. But every expiration is a moment of vulnerability, a shorter time-to-live
means more expirations per unit time, which means more opportunities for a
stampede. Origin protection wants long, or staggered, or soft expirations.
Freshness wants short, synchronized ones. The pattern lives exactly in that
tension.

**Simplicity versus coordination cost.** The naive cache-aside code, check the
cache, on a miss call the origin, store the result, is the simplest code
anyone will ever write for this problem, and it is also exactly the shape
that produces a stampede. Every mitigation this entry documents, a lock, a
lease, a probabilistic recompute decision, a background refresh, adds real
complexity, more state, more failure modes of its own, more to reason about
when something goes wrong at 3 in the morning. The forces favor simplicity
until the traffic and the key concentration make the simple version
unaffordable, and they favor coordination exactly when that line is crossed.

**Latency for the unlucky requester versus latency for everyone.** Under a
lock-based mitigation, the single requester who acquires the lock and does the
real work experiences the full origin latency, while every other concurrent
requester waits for that one requester to finish, or is served a stale value
instead. This trades a worse experience for one request against a much better
aggregate experience for the population, and it is a genuine trade-off, not a
free win, because the waiting requesters now depend on the leader finishing
promptly rather than on their own independent path to the origin.

**Consistency versus availability during the refill window.** Serving a
slightly stale value while a fresh one is computed, the stale-while-revalidate
family of techniques, sacrifices strict per-request freshness for continuous
availability and a flat load profile on the origin. Systems where staleness is
actually dangerous, a real-time balance check before an irreversible
transaction, cannot make this trade at all, and must instead pay full latency
or reach for a lock-based approach.

**Cost of coordination infrastructure versus cost of overload.** Locks and
leases usually require a shared coordination point, a distributed lock in
Redis, a database row, an atomic flag in the cache layer itself. That
coordination point is itself a dependency with its own availability profile,
and under sufficiently pathological conditions it can become the next
bottleneck. The forces here weigh the operational cost and failure surface of
adding a coordinator against the demonstrated cost of not having one.

**Team topology and cognitive load.** A single small team owning both the
cache layer and the origin can reason about a lock-based fix end to end. A
platform team that owns a shared caching layer used by dozens of independent
services usually cannot assume every caller will implement coordination
correctly, which pushes the platform team toward baking a stampede mitigation
into the shared caching client itself, so individual feature teams get the
protection without having to understand or implement it. This is a real,
observed organizational force, not only a technical one.

## 4. Applicability and non-applicability

Cache stampede is not a pattern to apply, it is a failure mode to recognize
and to design against. The applicability question here is really deciding
when guarding against a stampede is worth the engineering cost, and the
non-applicability list is where the actual judgment lives.

Guard against a stampede when the situation matches any of the following.

- The cached value is expensive to recompute, meaningfully more expensive
  than serving a byte already in memory, whether that cost is measured in
  latency, database load, third-party API quota, or compute.
- The key has enough concurrent readers around its expiration moment that
  simultaneous misses are plausible, not merely theoretically possible. A
  handful of readers per minute on a key almost never collide.
- The origin has a hard capacity ceiling that a burst of simultaneous
  recomputation could exceed, a fixed connection pool, a rate-limited
  upstream, a single write-lock-holding resource.
- The system has already suffered, or a load test has reproduced, a visible
  latency or error spike correlated with a cache entry's expiration.

Do not reach for stampede mitigation, or reach for the cheapest version of
it, when the situation matches any of the following instead.

- The underlying computation is already cheap enough that recomputing it on
  every concurrent request costs little more than the network round trip
  itself. Adding a lock here adds real complexity and a new failure mode for
  a problem that was never actually expensive.
- The key space is large and evenly distributed enough that any one key
  rarely if ever sees more than one concurrent reader at expiration, a
  per-user session lookup with millions of distinct users and even traffic is
  the common example. The stampede risk scales with concurrency per key, not
  with total system throughput.
- The origin is naturally idempotent, cheap to overload gracefully, and
  already protected by its own independent rate limiting or autoscaling that
  comfortably absorbs the worst plausible burst. Duplicating that protection
  at the cache layer is redundant work for no measurable benefit.
- The team cannot operate the coordination primitive a mitigation would
  require, adding a distributed lock service, or a feature of the caching
  client that nobody on the team understands, is itself an operational risk
  greater than the stampede it prevents. A worse-understood fix is not an
  improvement.
- Strict correctness makes any staleness at all unacceptable and the
  workload's absolute volume is low enough that per-request full-latency
  fetches are affordable, financial ledger reads immediately before a
  transfer are the classic case. Here the stale-serving family of mitigations
  is simply the wrong tool, and only exclusive locking or no caching at all
  is appropriate.

## 5. Structure

A cache-stampede-prone system has three participants, and the anti-pattern is
entirely a property of how they interact, not of any one participant alone.

- **Requester.** Any client of the cached value, a request handler, a
  worker, another service. In a healthy system there are many concurrent
  requesters for the same key around the moment of expiration, and that
  concurrency is the precondition for the failure.
- **Cache.** The fast store holding the computed value with an associated
  expiration. It has no built-in notion that someone is already refilling
  this key, which is exactly the missing coordination that produces the
  anti-pattern. A plain key-value store with a time-to-live, used naively,
  is structurally incapable of preventing a stampede on its own.
- **Origin.** The expensive source of truth, a database, an upstream API,
  a compute job. It has a real, finite capacity, and the anti-pattern is the
  event where that capacity is exceeded by simultaneous, duplicated demand
  that a coordinating layer could have collapsed into one piece of work.

The mitigated versions of this structure add one more role.

- **Coordinator.** A mechanism, in-process or distributed, that lets exactly
  one requester's miss become the one that talks to the origin, while every
  other concurrent requester either waits on that one's result, is served a
  stale value from the cache in the meantime, or is probabilistically steered
  away from recomputing at all. A mutex keyed by cache key, a lease token
  stored alongside the cached value, or a background refresh process that
  requesters never race against, are all instances of this role.

## 6. ASCII structure diagram

```
Unmitigated (the anti-pattern)

  Requester 1  --\
  Requester 2  ---\
  Requester 3  ----\        miss, miss, miss ...
  Requester 4  -----> [ Cache ] ----------------> [ Origin ]
  Requester 5  ----/        (key expired,          (N simultaneous
       ...     --/           no coordination)       expensive calls)
  Requester N  -/

  N requesters -> N origin calls -> origin overload


Mitigated with a coordinator (lock or lease)

  Requester 1  --\
  Requester 2  ---\
  Requester 3  ----\
  Requester 4  -----> [ Cache ] --> [ Coordinator ] --> [ Origin ]
  Requester 5  ----/     |                |                 |
       ...     --/       |         acquires lock       1 call only
  Requester N  -/         \-- others wait or get stale value

  N requesters -> 1 origin call -> origin protected
```

## 7. Dynamics

The unmitigated sequence, the one that produces the incident, runs like this
for a single expiring key under load.

```
time  requester         cache                         origin
----  ---------------   ---------------------------   -----------------
t0    ...               key K holds value V, live      idle
tE    key K expires     entry for K is now stale
tE+1  R1 reads K        MISS                            -
tE+1  R2 reads K        MISS                            -
tE+1  R3 reads K        MISS                            -
tE+1  ... R_n reads K   MISS  (all in the same tick)     -
tE+2  R1 calls origin                                    call 1 starts
tE+2  R2 calls origin                                    call 2 starts
tE+2  R3 calls origin                                    call 3 starts
tE+2  ... R_n calls                                       call n starts
                                                          origin queues,
                                                          contends, slows
tE+X  R1 origin returns  R1 writes V' to cache
tE+X  R2 origin returns  R2 writes V' to cache (again)
tE+X  ...                each writer redundantly
                          overwrites the same key
tE+Y  origin recovers    key K now live again
```

The redundant writes at the end are their own minor cost, every requester
that lost the race still finished its own duplicate origin call and then
wrote a value nobody needed written twice, but the dominant cost is entirely
in the `tE+2` to `tE+X` window, where the origin receives n simultaneous
expensive calls instead of one.

The mitigated sequence with a coordinating lock replaces the fan-out at
`tE+2` with a single winner and a set of followers.

```
time  requester         cache / lock                  origin
----  ---------------   ---------------------------   -----------------
tE+1  R1 reads K        MISS, attempts lock, wins       -
tE+1  R2 reads K        MISS, attempts lock, loses      -
tE+1  R3 reads K        MISS, attempts lock, loses      -
tE+1  R2, R3, ... wait  waiting on R1's result           -
tE+2  R1 calls origin                                    call 1 starts,
                                                          alone
tE+X  origin returns     R1 writes V' to cache,
                          releases lock
tE+X  R2, R3, ... wake   read V' from cache, no
                          origin call made
```

The stale-serving variant changes what waiters do while they wait, instead of
blocking, they are handed the last known value immediately, and only the
winning requester's completed refill changes what future readers see, which
keeps observed latency flat for everyone except the one requester doing the
real work.

## 8. Implementation variants

There is no single canonical implementation of stampede protection, there is
a family of variants that trade off differently along the forces in dimension
3, and production systems frequently combine two or three of them.

**Mutex or lock around the fill.** The requester that misses attempts to
acquire a lock scoped to that specific cache key before calling the origin.
The winner calls the origin and writes the result, then releases the lock.
Losers either block until the winner finishes and then re-read the cache, or
poll the cache briefly, or immediately fall back to serving a stale value if
one exists. In a single process this lock can be an ordinary in-memory mutex
keyed by the cache key, shown running in the code samples below. Across a
fleet of processes, the lock has to be a distributed primitive, most commonly
implemented with an atomic conditional write. Redis documents exactly this
shape as a documented pattern, `SET resource-name anystring NX EX
max-lock-time`, where `NX` means only set the key if it does not already
exist and `EX` attaches an expiration so a crashed lock holder cannot wedge
the lock forever ([Redis documentation, SET
command](https://redis.io/docs/latest/commands/set/), verified
2026-08-02). The same page is explicit that this exact single-key pattern is
discouraged in favor of the Redlock algorithm, which is only a bit more
complex to implement but offers better guarantees and is fault tolerant,
which is the correct honest caveat, a single-node lock has real failure modes
under partition and clock skew that a five-node Redlock quorum addresses.

**Leases returned alongside a miss.** Rather than a separate lock key, the
cache itself is extended so that a miss response can optionally hand the
requester a lease token, a proof that this requester is the one authorized to
refill the value, while every other concurrent miss on the same key is told
to wait rather than being handed a lease of its own. This is the same
coordination as a lock conceptually, folded into the cache's own miss
response so the client does not need a second round trip to a separate
locking service.

**Request coalescing, in-process.** Inside one process, when many concurrent
requests for the same key would each independently call the origin, the
process instead recognizes the in-flight call already under way and hands
every waiting caller the same pending result once it resolves, rather than
starting a second call. This does not require any lock semantics at all
because it never crosses a process boundary, a shared map from key to
in-flight promise or future, guarded by a simple mutex, is sufficient, exactly
as demonstrated in the code below. This is the cheapest and lowest-risk
mitigation available, and it is the correct default whenever a single process
or a single edge node is the one seeing the concurrent misses, which is the
common case for a web server's local in-memory cache layer or for a CDN edge
node's cache in front of an origin.

**Serving stale while revalidating.** Instead of making any requester wait,
the cache continues to serve the last known value past its nominal
expiration, for a bounded grace window, while exactly one background refresh
updates it. This is standardized at the HTTP layer by RFC 5861, whose
abstract states that it defines Cache-Control extensions that allow control
over the use of stale responses by caches, specifically
`stale-while-revalidate`, which lets a cache serve an expired response for an
additional bounded window while it revalidates in the background, and
`stale-if-error`, which lets a cache serve an expired response if the origin
is returning errors rather than surfacing the error to the end user ([RFC
5861](https://www.rfc-editor.org/rfc/rfc5861), verified
2026-08-02). nginx implements the same idea for its reverse-proxy cache with
the `updating` parameter to `proxy_cache_use_stale`, whose documentation
states that this parameter permits using a stale cached response if it is
currently being updated, and pairs it with `proxy_cache_lock`, whose
documentation states that when enabled, only one request at a time will be
allowed to populate a new cache element, and other requests of the same
cache element will either wait for a response to appear in the cache or for
the cache lock for this element to be released ([nginx documentation,
ngx_http_proxy_module, proxy_cache_lock and proxy_cache_use_stale](https://nginx.org/en/docs/http/ngx_http_proxy_module.html),
verified 2026-08-02). This is the single named production implementation
that most cleanly combines both the locking variant and the stale-serving
variant into one pair of directives.

**Building block conditional writes at the cache-protocol level.** The
memcached text protocol offers an `add` command distinct from `set`, defined
as storing data only if the server does not already hold data for this key,
failing with a `NOT_STORED` response rather than overwriting existing data
when the key is already present ([memcached protocol specification, storage
commands](https://raw.githubusercontent.com/memcached/memcached/master/doc/protocol.txt),
verified 2026-08-02). This single primitive is exactly the atomic
conditional write that a home-grown lock-key scheme needs, an application
can attempt `add lock:K 1 30` before recomputing K, and only the caller for
whom the `add` succeeds proceeds to hit the origin, with the 30-second
expiration on the lock key itself acting as the same crash-safety valve the
Redis `EX` option provides.

**Probabilistic early expiration, the XFetch family.** Rather than a hard
boundary at which the cache entry becomes invalid, each read of a
near-expiring entry makes an independent, randomized decision about whether
to treat the entry as already expired and go recompute it early. Vattani,
Chierichetti and Lowenstein's VLDB 2015 paper, as summarized on Wikipedia's
cache stampede page, formalizes this with an exponential-distribution
formula in which the probability of triggering an early recomputation
increases the closer the current time is to the entry's nominal expiration,
scaled by a tunable parameter beta, with beta equal to one reported as
effective in practice ([Wikipedia, Cache stampede, mitigation
strategies](https://en.wikipedia.org/wiki/Cache_stampede), verified
2026-08-02). Because the decision is independently randomized per reader
rather than coordinated by a lock, this technique spreads recomputation out
in time across many readers who are polling the same key at slightly
different moments, which is exactly the situation of many independent edge
caches or many independent long-lived polling processes staggered against a
shared origin refresh schedule. The code in dimension 15 below demonstrates,
by actually running it, that this technique does not by itself deduplicate a
truly simultaneous burst of first-time misses on a cold key, because every
reader in that burst independently observes no cached value at all rather
than a near-expiring one, and the formula only ever applies to a value that
already exists. Probabilistic early expiration and request coalescing solve
overlapping but distinct halves of the problem, and production systems that
care about both a cold start burst and a staggered near-expiry burst
typically implement both.

## 9. Known production uses

nginx's reverse proxy cache module ships `proxy_cache_lock` as a first-class
directive precisely for this problem, documented as allowing only one request
at a time to populate a new cache element while other requests for that same
element wait for the response or for the lock to be released, and pairs it
with `proxy_cache_use_stale updating` so that a request arriving while the
lock is held can be served the previous stale response instead of waiting
([nginx documentation, ngx_http_proxy_module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html),
verified 2026-08-02). This is deployed in front of an enormous share of the
production web, making it one of the most widely operated stampede
mitigations in existence, even where the operator never uses the word
stampede.

Redis documents the single-key `SET key value NX EX seconds` idiom as an
explicit, named pattern for building a distributed lock, the exact primitive
that application-level cache-refill coordination is built on top of, while
also documenting its own honest limitation, that this simple form is
superseded by the multi-node Redlock algorithm for cases that need fault
tolerance under node failure ([Redis documentation, SET
command, Patterns section](https://redis.io/docs/latest/commands/set/),
verified 2026-08-02). Because Redis sits in front of an origin as a cache
in a very large number of production architectures, this documented pattern
is the mechanism most commonly reached for by teams building their own
stampede-protected cache-aside layer on top of Redis rather than relying on
an edge proxy.

memcached's `add` command, defined in the project's own protocol
specification as a conditional store that fails when the key already exists
rather than overwriting it, is the conditional-write primitive that
lock-key based stampede protection has been built on since memcached became
a standard caching layer for large web deployments in the 2000s ([memcached
protocol specification](https://raw.githubusercontent.com/memcached/memcached/master/doc/protocol.txt),
verified 2026-08-02). Any application-level dogpile-lock library that stores
its lock as a memcached key rather than a Redis key is, structurally, using
this exact command as its coordination primitive.

## 10. Consequences

Positive, for a well chosen mitigation, not for the raw anti-pattern.

- Origin load becomes bounded and predictable at the moment of expiration
  rather than proportional to concurrent reader count, which turns a
  traffic-dependent failure mode into a traffic-independent one.
- Overall system latency under load improves for the population even when
  one requester, the lock holder or the request that triggers a probabilistic
  early recompute, pays the full origin latency, because every other
  concurrent requester is served in cache-hit time instead of also paying
  origin latency.
- Origin capacity planning becomes simpler, because the worst case for a
  single key's refill is one concurrent origin call rather than an
  unbounded multiple of the read concurrency on that key.

Negative, the price every mitigation on this list pays somewhere.

- Added system complexity and a new class of bug, a lock that is never
  released because the process holding it crashed before releasing it, a
  stale-serving window configured too generously so genuinely wrong data is
  served for longer than intended, an in-process coalescing map that leaks
  entries if an exception path forgets to clean one up.
- A single point of coordination, whether an in-memory mutex, a distributed
  lock key, or a lease token, is itself now something that can be wrong, slow,
  or unavailable, and its own failure mode has to be reasoned about
  separately from the origin's failure mode.
- Waiting requesters under a blocking mitigation now depend on the timeliness
  of the one requester doing the real work, if that requester is unusually
  slow this run, every waiter is unusually slow too, which can turn one slow
  origin call into a synchronized slow response for the whole waiting cohort
  rather than the smoother distribution of latency that no coordination would
  have produced.
- Stale-serving mitigations introduce a deliberate, bounded window of
  incorrectness that must be an explicit, reviewed business decision, not an
  accident of configuration, because it directly trades correctness for
  availability.

## 11. Failure modes and misuse

**Symptom.** A dashboard shows a sudden, sharp spike in origin database
connection count or CPU that recurs at a period matching a cache
time-to-live, followed by elevated request latency across the whole system,
not only for the hot key.
**Cause.** No coordination exists between concurrent misses on the same key,
every miss independently calls the origin, exactly the unmitigated dynamics
in dimension 7.
**Fix.** Introduce request coalescing or a lock around the fill path, as in
dimension 8, scoped to the smallest layer where the concurrency actually
occurs, in-process coalescing if the concurrency is within one process, a
distributed lock if it spans a fleet.

**Symptom.** After adding a distributed lock, the system experiences
occasional total outages on a specific key where every requester waits
indefinitely and none is ever served, worse than the stampede it replaced.
**Cause.** The lock key has no expiration, or an expiration far longer than
the origin call is expected to take, so a crashed or hung lock holder wedges
the lock and every waiter blocks forever with no forward progress. This is
exactly the failure the Redis documentation's `EX` option and memcached's
`add`-with-expiration idiom exist to prevent, and it is a common
implementation mistake when a team rolls its own locking without reading
that guidance.
**Fix.** Attach a conservative expiration to the lock itself, shorter than
any reasonable timeout on waiters, and make waiters re-attempt to acquire the
lock rather than block on the specific holder that may never release it.

**Symptom.** The system serves visibly wrong data, a price shown after a
known change, a stock count that does not reflect a completed transaction,
for a period much longer than the configured cache time-to-live.
**Cause.** A stale-while-revalidate window was configured without an upper
bound, or the background refresh path itself silently started failing, so
the cache keeps serving the same increasingly stale value because nothing is
actually rewriting it, and nobody notices because the stale-serving path was
designed precisely to hide misses from users.
**Fix.** Bound the stale-serving window explicitly and alert on refresh
failures separately from alerting on origin errors, so a broken background
refresh is visible even though end users never see an error.

**Symptom.** Origin load is still spiking exactly at expiration despite
having implemented probabilistic early expiration.
**Cause.** The technique was applied to a key that experiences genuine cold
starts or true simultaneous first-time misses, for example a key that is
deliberately evicted or that has never been populated before a burst arrives,
where there is no existing near-expiry entry for the probabilistic decision to
apply to. This is the exact failure mode the running code in dimension 15
demonstrates directly, 200 concurrent cold misses on a key with no prior
value produced 200 origin calls under the probabilistic approach alone.
**Fix.** Pair probabilistic early expiration with request coalescing or a
lock for the cold-start case, they solve different halves of the same named
problem and neither alone is sufficient for both halves.

**Symptom.** Adding a stampede mitigation made the common case, low
concurrency, uncontended keys, measurably slower.
**Cause.** The mitigation was applied unconditionally to every cache read,
paying the cost of a lock acquisition attempt or a coalescing map lookup even
when there was never any concurrent contention to protect against, violating
the non-applicability guidance in dimension 4.
**Fix.** Scope the mitigation to the keys and traffic patterns that actually
exhibit meaningful concurrent read pressure, and measure before assuming
every cache read needs the full mechanism.

## 12. Trade-off matrix

| Force | Mutex or lock around the fill | Request coalescing, in-process | Stale-while-revalidate | Probabilistic early expiration |
|---|---|---|---|---|
| Waiter experience during refill | Waits for lock holder, or blocked latency | Waits for the in-flight call, shared latency | No wait, gets last-known value immediately | No wait for readers who did not trigger recompute |
| Handles cold-start bursts | Yes, waiters block or fall back | Yes, this is the ideal case for it | Only if a prior value exists to serve | No, requires a pre-existing entry, see dimension 11 |
| Requires cross-process coordination | Yes, for a distributed lock variant | No, in-process only | Depends on implementation, often none | No, purely per-reader randomized decision |
| Correctness during refill window | Strict, no stale data served | Strict, no stale data served | Deliberately relaxed, bounded staleness | Strict for the hit case, standard TTL semantics otherwise |
| New failure mode introduced | Wedged lock if not expired correctly | Leaked in-flight entry on unhandled exception | Silent staleness if refresh path breaks | Requires tuning beta, mistuning under- or over-triggers |
| Best fit | Fleet-wide coordination needed, correctness matters | Single-process or single-edge-node hot key | Availability matters more than per-request freshness | Many independent staggered readers near a shared TTL |

## 13. Related and incompatible patterns

**Circuit breaker.** A circuit breaker protects a caller from a failing
downstream dependency by tripping open once failures accumulate, and it
composes naturally downstream of stampede protection, the coordinator's
single origin call should itself be wrapped in a circuit breaker so that a
genuinely unhealthy origin does not simply turn one blocked lock holder into
one very slow lock holder over and over.

**Bulkhead.** A bulkhead isolates a limited pool of resources, connections,
threads, for a specific dependency so that pressure on one dependency cannot
starve the rest of the system. It composes with stampede protection at the
origin side, bounding the origin connection pool means even the single
coordinated call a stampede mitigation allows through cannot itself exhaust a
shared resource pool needed elsewhere.

**Cache-aside.** Cache stampede is a specific, well known way that a naive
cache-aside implementation fails under concurrent load. Every mitigation in
dimension 8 is a modification of the cache-aside read path, and it is fair to
describe stampede-protected cache-aside as the production-grade version of
plain cache-aside, not as a separate pattern.

**Lazy initialization.** The double-checked locking idiom historically used to
make lazy initialization thread-safe in a single process is structurally the
same shape as the in-process request-coalescing mitigation here, check
without a lock, then acquire a lock and check again before doing the
expensive work, applied to a cache entry's first fill instead of to a
singleton instance's construction.

**Singleton.** The classic thread-safety concerns around lazily constructing
a singleton, exactly one construction across many concurrent first accesses,
are the single-process, single-key special case of the same coordination
problem a distributed cache-stampede lock solves at larger scale.

There is no pattern this entry is fundamentally incompatible with, since it
is a failure mode rather than a structural design choice, but stale-while-
revalidate specifically conflicts with any correctness requirement that
forbids serving data known to be out of date, and should not be applied
alongside patterns or business rules that assume every read reflects the
current state exactly.

## 14. Refactoring path in and out

Introducing stampede protection into an existing plain cache-aside
implementation follows a small number of concrete steps, and the order
matters because each step is independently safe to ship and observe before
the next.

1. Measure first. Instrument the existing cache-aside path to count
   concurrent origin calls per key around expiration, before changing any
   behavior. Confirm the anti-pattern is actually occurring for real keys
   under real traffic rather than assuming it from the architecture alone.
2. Add the cheapest applicable mitigation first. If the concurrency observed
   in step one is within a single process, introduce in-process request
   coalescing, a map from key to in-flight future guarded by a mutex, exactly
   as shown in dimension 15. This requires no new infrastructure and no
   cross-service coordination, and it eliminates the cold-start burst case
   entirely for that process.
3. If concurrency spans multiple processes or hosts, add a distributed lock
   scoped to the specific keys that measurement showed are actually
   contended, using an existing shared cache or coordination store, with an
   expiration on the lock itself shorter than any acceptable wait time.
4. Where the workload can tolerate bounded staleness, layer stale-while-
   revalidate on top so that waiters are served the previous value instead of
   blocking, converting a latency cost for waiters into a pure background
   refresh cost paid by the system rather than by any individual requester.
5. Where reads are frequent, independent, and staggered relative to a shared
   time-to-live, add probabilistic early expiration as a complement, not a
   replacement, to the coalescing or locking already in place, so that
   near-expiry reads spread their recomputation attempts out in time rather
   than clustering at the exact expiration boundary.

Removing stampede protection, the reverse direction, is appropriate when
measurement in step one, repeated periodically as traffic patterns change,
shows that a previously hot key's concurrency has dropped enough that the
coordination overhead now costs more than the stampede risk it guards
against, exactly the non-applicability signal in dimension 4. The safe order
is to remove the most complex layer first, probabilistic tuning, then
stale-serving, then the lock, watching the same measurement at each step,
rather than removing everything at once.

## 15. Testing and verification

This dimension is the one place in this entry where the claims are backed by
code that was actually compiled and executed rather than described, and the
numbers below are the real output of that run, not illustrative estimates.

The most direct verification technique is a concurrency test that fires many
simultaneous cold reads for the same never-before-seen key against both an
unmitigated and a mitigated cache implementation, and counts how many times
the expensive backend function was actually invoked. A correct mitigation
should reduce that count to exactly one regardless of how many concurrent
readers there were, and an incorrect or absent mitigation should show the
count scale with the number of concurrent readers.

Running the TypeScript implementation in the code samples below, compiled
with `tsc --strict` against TypeScript 7.0.2 and executed with Node.js,
against 200 simultaneous cold reads of one key, produced the following two
lines of real output.

```
naive (no coalescing): 200 backend calls for 200 concurrent cold reads
coalescing (in-flight dedup): 1 backend calls for 200 concurrent cold reads
```

The equivalent Python implementation, run with `python3` using a
`ThreadPoolExecutor` of 200 worker threads to genuinely exercise concurrent
threads rather than cooperative single-threaded scheduling, produced the
same shape of result.

```
naive (no coalescing): 200 backend calls for 200 concurrent cold reads
coalescing (per-key lock): 1 backend calls for 200 concurrent cold reads
```

The equivalent Go implementation, run with `go run` under Go 1.26.4 using
200 real goroutines and a `sync.WaitGroup`, agreed again.

```
naive (no coalescing): 200 backend calls for 200 concurrent cold reads
coalescing (singleflight-style): 1 backend calls for 200 concurrent cold reads
```

All three independently implemented, independently executed programs agree,
200 uncoordinated concurrent misses produce 200 origin calls, and the
identical concurrency pattern routed through any of a shared JavaScript
promise, a Python thread lock, or a Go channel-backed wait group collapses
to exactly one origin call. This is the empirical demonstration that the
mitigation, not merely its description, does what dimension 8 claims.

A separate test run, of the probabilistic-early-expiration TypeScript
implementation against the same 200-concurrent-cold-reader scenario, was
also executed and produced one line of output.

```
backend calls for 200 concurrent reads on a 1s ttl: 200
```

This result was not the intended outcome of that experiment and is reported
here precisely because it is the honest, useful negative result described in
dimension 11, probabilistic early expiration alone, correctly implemented per
the formula in Wikipedia's summary of the Vattani, Chierichetti and
Lowenstein paper, does not deduplicate a cold-start burst, because every one
of the 200 readers observed no existing cache entry at all rather than a
near-expiry one, and the technique's formula has no branch that applies to
that case. A correct test suite for a system using probabilistic early
expiration must therefore include two distinct test scenarios, a cold-start
concurrent burst, which this technique alone does not protect, and a
warm-key near-expiry scenario with staggered, non-simultaneous readers over
a window approaching the time-to-live, which is the scenario the technique
is actually designed for and which a correct implementation should show
spreads recomputation attempts out rather than clustering them at the exact
expiration instant.

Beyond direct call counting, a fault-injection technique for a lock-based
mitigation is to have the winning lock holder's origin call intentionally
hang or throw partway through the test, and assert that waiters are released
within the configured lock expiration rather than blocking forever, directly
exercising the wedged-lock failure mode named in dimension 11. A
fault-injection technique for a stale-while-revalidate mitigation is to make
the background refresh path fail repeatedly and assert that an alert or
metric fires distinguishing a broken refresh from a healthy one continuing to
serve intentionally bounded stale data, since the two look identical to an
end user and only distinguishable through the system's own instrumentation.

## 16. Observability signals

The single most load-bearing signal is a per-key or per-key-pattern counter
of origin calls attributable to a cache miss, sampled or aggregated over a
short enough window, one second or less, to distinguish a burst from a
steady rate. A healthy, protected system shows this counter capped at one per
key per refill cycle even under heavy concurrent read load. An unprotected or
mis-protected system shows this counter spike proportionally with concurrent
reader count at expiration moments, and that spike is the leading indicator
that appears before the downstream latency and error-rate metrics degrade.

A lock-based mitigation should expose lock acquisition wait time as its own
histogram, separate from overall request latency, because a growing tail on
this specific histogram is the earliest sign of a wedging lock, well before
waiters start timing out and the failure becomes visible in aggregate
latency dashboards.

A stale-while-revalidate mitigation should expose the age of the value being
served at read time as a histogram or gauge, not merely a boolean
hit-or-miss, because the entire risk of this mitigation is silent unbounded
staleness, and age is the only signal that distinguishes an intentionally
short grace-window stale value from data that has been wrong for an hour
because the refresh path quietly broke.

A probabilistic early expiration implementation should expose the rate at
which early recomputation actually triggers, compared against the
theoretical rate the configured beta parameter predicts, since a mistuned
beta either triggers far too rarely, which reintroduces stampede risk at the
hard expiration boundary, or triggers far too often, which defeats the
purpose of caching at all by recomputing almost every read.

Across all variants, correlating any of these signals against the
cache-key's own configured time-to-live on a shared timeline is the single
most useful dashboard construction, because it turns a general observation
that origin load is high into the answerable question of whether that
origin load is periodic, and whether the period matches a specific key's
expiration.

## 17. Security and privacy implications

The attack surface a cache stampede opens is primarily an availability one,
and it is directly exploitable as a denial-of-service vector distinct from a
generic traffic flood. An attacker who can identify a specific expensive,
cacheable key, a search query known to be costly, a report-generation
endpoint, a computed aggregate on a public resource, and can predict or force
that key's expiration, for example by observing response headers that reveal
a time-to-live, can time a burst of concurrent requests to arrive exactly at
the expiration moment and achieve a disproportionate origin load relative to
the request volume actually sent, because the unmitigated system will itself
multiply that burst into simultaneous origin calls rather than serving the
attacker from cache. This is a materially cheaper denial-of-service technique
for the attacker than a generic volumetric flood, because it exploits the
system's own caching architecture as the amplifier, and it is exactly the
reason origin-protection mitigations in dimension 8 have security value, not
only performance value.

A distributed lock used as the coordination mechanism introduces a narrower,
secondary surface, if the lock key or lease token is guessable or is derived
from user-controllable input without proper scoping, a malicious actor could
in principle attempt to hold or repeatedly acquire and release a lock for a
key they do not legitimately own, though this requires the lock's key
namespace to be poorly isolated from user input in the first place, a general
input-validation concern rather than one specific to this pattern.

There is no data-handling or privacy implication specific to cache stampede
itself, the pattern concerns request coordination and load, not the content
or classification of the cached data. Whatever privacy controls already
govern the cached value in its normal, non-stampeded path, encryption at
rest, access scoping, retention limits, apply identically whether or not a
stampede mitigation is present, and this entry has no additional privacy
guidance beyond what already governs the cache and the origin independently.

## 18. References

1. Wikipedia contributors, "Cache stampede," Wikipedia, The Free
   Encyclopedia, https://en.wikipedia.org/wiki/Cache_stampede, verified
   2026-08-02. Source for the definition, the dog-piling alias, the
   attribution to Galbraith 2009 and Allspaw and Robbins 2010, and the
   summary of the Vattani, Chierichetti, and Lowenstein probabilistic early
   expiration formula.
2. Wikipedia contributors, "Thundering herd problem," Wikipedia, The Free
   Encyclopedia, https://en.wikipedia.org/wiki/Thundering_herd_problem,
   verified 2026-08-02. Source for the operating-systems origin of the
   broader problem family, the `accept()` and process-scheduling cases, and
   the `EPOLLEXCLUSIVE` kernel-level mitigation.
3. Asaf Vattani, Flavio Chierichetti, and Keegan Lowenstein, "Optimal
   Probabilistic Cache Stampede Prevention," Proceedings of the VLDB
   Endowment, 2015, as cited and summarized in reference 1. The original
   paper itself was not independently fetched for this entry, its content is
   reported here as summarized by reference 1.
4. nginx documentation, "Module ngx_http_proxy_module," directives
   `proxy_cache_lock` and `proxy_cache_use_stale`,
   https://nginx.org/en/docs/http/ngx_http_proxy_module.html, verified
   2026-08-02. Source for the named production single-flight and
   stale-serving implementation.
5. Redis documentation, "SET," https://redis.io/docs/latest/commands/set/,
   verified 2026-08-02. Source for the `NX` and `EX` conditional-write lock
   pattern and for Redis's own documented caveat that this pattern is
   superseded by Redlock for fault-tolerant use.
6. memcached project, "Protocol specification," storage commands section,
   https://raw.githubusercontent.com/memcached/memcached/master/doc/protocol.txt,
   verified 2026-08-02. Source for the `add` command's conditional-store
   semantics.
7. M. Nottingham, "HTTP Cache-Control Extensions for Stale Content," RFC
   5861, Internet Engineering Task Force, May 2010,
   https://www.rfc-editor.org/rfc/rfc5861, verified 2026-08-02. Source for
   the `stale-while-revalidate` and `stale-if-error` standardized directives.

Engineering judgement disclosure. Dimension 3, forces, dimension 10,
consequences, dimension 11, failure modes, and dimension 16, observability
signals, draw on general, widely shared operational experience with caching
systems rather than on a single citable source for every individual
statement, and are labeled here as judgement per the entry template's
distinction between sourced claims and engineering reasoning. A widely
referenced production use of a lease-based mechanism at a large-scale social
media memcache deployment was deliberately omitted from dimension 9 because
the primary paper describing it could not be independently fetched and
verified during authoring, and an unverifiable claim was judged worse than a
shorter, fully verified list of three named production systems.

## Code examples

Three languages, each independently compiled or run, and each producing the
same real numbers reported in dimension 15. TypeScript and Go both give an
async or goroutine-native shape to the coalescing cache, which is the shape
most production HTTP services actually use. Python gives the equivalent
thread-based shape, which is the shape a synchronous WSGI-style application
server uses. All three implement the same two caches side by side, a naive
cache-aside with no coordination and a coalescing cache that deduplicates
in-flight misses, and drive 200 concurrent cold reads of one key through
each so the difference is directly observable rather than asserted.

### TypeScript

```typescript
type Fetcher<T> = () => Promise<T>;

class NaiveCache<T> {
  private store = new Map<string, { value: T; expiresAt: number }>();

  async get(key: string, ttlMs: number, fetcher: Fetcher<T>): Promise<T> {
    const hit = this.store.get(key);
    const now = Date.now();
    if (hit && hit.expiresAt > now) {
      return hit.value;
    }
    const value = await fetcher();
    this.store.set(key, { value, expiresAt: Date.now() + ttlMs });
    return value;
  }
}

class CoalescingCache<T> {
  private store = new Map<string, { value: T; expiresAt: number }>();
  private inflight = new Map<string, Promise<T>>();

  async get(key: string, ttlMs: number, fetcher: Fetcher<T>): Promise<T> {
    const hit = this.store.get(key);
    const now = Date.now();
    if (hit && hit.expiresAt > now) {
      return hit.value;
    }
    const existing = this.inflight.get(key);
    if (existing) {
      return existing;
    }
    const promise = (async () => {
      try {
        const value = await fetcher();
        this.store.set(key, { value, expiresAt: Date.now() + ttlMs });
        return value;
      } finally {
        this.inflight.delete(key);
      }
    })();
    this.inflight.set(key, promise);
    return promise;
  }
}

async function burst(
  label: string,
  n: number,
  run: (fetcher: Fetcher<number>) => Promise<number>
): Promise<void> {
  let backendCalls = 0;
  const backend = async (): Promise<number> => {
    backendCalls += 1;
    await new Promise((r) => setTimeout(r, 10));
    return backendCalls;
  };
  const requests: Promise<number>[] = [];
  for (let i = 0; i < n; i += 1) {
    requests.push(run(backend));
  }
  await Promise.all(requests);
  console.log(`${label}: ${backendCalls} backend calls for ${n} concurrent cold reads`);
}

async function main() {
  const naive = new NaiveCache<number>();
  await burst("naive (no coalescing)", 200, (f) => naive.get("hot-key", 1000, f));

  const coalescing = new CoalescingCache<number>();
  await burst("coalescing (in-flight dedup)", 200, (f) => coalescing.get("hot-key", 1000, f));
}

main();
```

Compiled with `tsc --strict --target es2020 --module commonjs` against
TypeScript 7.0.2 with zero errors, then run with `node`. Real output.

```
naive (no coalescing): 200 backend calls for 200 concurrent cold reads
coalescing (in-flight dedup): 1 backend calls for 200 concurrent cold reads
```

### Python

```python
import threading
import time
from concurrent.futures import ThreadPoolExecutor


class NaiveCache:
    def __init__(self):
        self._store = {}

    def get(self, key, ttl, fetcher):
        entry = self._store.get(key)
        now = time.monotonic()
        if entry and entry[1] > now:
            return entry[0]
        value = fetcher()
        self._store[key] = (value, time.monotonic() + ttl)
        return value


class CoalescingCache:
    def __init__(self):
        self._store = {}
        self._locks = {}
        self._guard = threading.Lock()

    def get(self, key, ttl, fetcher):
        entry = self._store.get(key)
        now = time.monotonic()
        if entry and entry[1] > now:
            return entry[0]

        with self._guard:
            entry = self._store.get(key)
            now = time.monotonic()
            if entry and entry[1] > now:
                return entry[0]
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock

        with lock:
            entry = self._store.get(key)
            now = time.monotonic()
            if entry and entry[1] > now:
                return entry[0]
            value = fetcher()
            self._store[key] = (value, time.monotonic() + ttl)
            with self._guard:
                self._locks.pop(key, None)
            return value


def burst(label, n, run_one):
    calls = {"count": 0}
    call_lock = threading.Lock()

    def backend():
        with call_lock:
            calls["count"] += 1
        time.sleep(0.01)
        return calls["count"]

    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(run_one, backend) for _ in range(n)]
        for f in futures:
            f.result()

    print(f"{label}: {calls['count']} backend calls for {n} concurrent cold reads")


def main():
    naive = NaiveCache()
    burst("naive (no coalescing)", 200, lambda backend: naive.get("hot-key", 1.0, backend))

    coalescing = CoalescingCache()
    burst(
        "coalescing (per-key lock)",
        200,
        lambda backend: coalescing.get("hot-key", 1.0, backend),
    )


if __name__ == "__main__":
    main()
```

Run with `python3`, no errors. Real output.

```
naive (no coalescing): 200 backend calls for 200 concurrent cold reads
coalescing (per-key lock): 1 backend calls for 200 concurrent cold reads
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
	value     int
	expiresAt time.Time
}

type NaiveCache struct {
	mu    sync.Mutex
	store map[string]entry
}

func NewNaiveCache() *NaiveCache {
	return &NaiveCache{store: make(map[string]entry)}
}

func (c *NaiveCache) Get(key string, ttl time.Duration, fetch func() int) int {
	c.mu.Lock()
	e, ok := c.store[key]
	c.mu.Unlock()
	if ok && time.Now().Before(e.expiresAt) {
		return e.value
	}
	value := fetch()
	c.mu.Lock()
	c.store[key] = entry{value: value, expiresAt: time.Now().Add(ttl)}
	c.mu.Unlock()
	return value
}

type call struct {
	wg    sync.WaitGroup
	value int
}

type CoalescingCache struct {
	mu     sync.Mutex
	store  map[string]entry
	flight map[string]*call
}

func NewCoalescingCache() *CoalescingCache {
	return &CoalescingCache{store: make(map[string]entry), flight: make(map[string]*call)}
}

func (c *CoalescingCache) Get(key string, ttl time.Duration, fetch func() int) int {
	c.mu.Lock()
	if e, ok := c.store[key]; ok && time.Now().Before(e.expiresAt) {
		c.mu.Unlock()
		return e.value
	}
	if inFlight, ok := c.flight[key]; ok {
		c.mu.Unlock()
		inFlight.wg.Wait()
		return inFlight.value
	}
	cl := &call{}
	cl.wg.Add(1)
	c.flight[key] = cl
	c.mu.Unlock()

	value := fetch()

	c.mu.Lock()
	c.store[key] = entry{value: value, expiresAt: time.Now().Add(ttl)}
	delete(c.flight, key)
	c.mu.Unlock()

	cl.value = value
	cl.wg.Done()
	return value
}

func burst(label string, n int, run func(fetch func() int) int) {
	var callCount int
	var callMu sync.Mutex
	backend := func() int {
		callMu.Lock()
		callCount++
		result := callCount
		callMu.Unlock()
		time.Sleep(10 * time.Millisecond)
		return result
	}

	var wg sync.WaitGroup
	wg.Add(n)
	for i := 0; i < n; i++ {
		go func() {
			defer wg.Done()
			run(backend)
		}()
	}
	wg.Wait()

	fmt.Printf("%s: %d backend calls for %d concurrent cold reads\n", label, callCount, n)
}

func main() {
	naive := NewNaiveCache()
	burst("naive (no coalescing)", 200, func(fetch func() int) int {
		return naive.Get("hot-key", time.Second, fetch)
	})

	coalescing := NewCoalescingCache()
	burst("coalescing (singleflight-style)", 200, func(fetch func() int) int {
		return coalescing.Get("hot-key", time.Second, fetch)
	})
}
```

Run with `go run` under Go 1.26.4, no errors. Real output.

```
naive (no coalescing): 200 backend calls for 200 concurrent cold reads
coalescing (singleflight-style): 1 backend calls for 200 concurrent cold reads
```

Swift, Java, and Rust are omitted from this entry because the three languages
above already exercise the pattern's three most common concurrency shapes,
event-loop promises, OS threads with locks, and goroutines with channels, and
a fourth idiomatic variant would repeat the same coordinating-mutex shape
already shown rather than reveal a genuinely different implementation
concern.
