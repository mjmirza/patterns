---
name: Thundering Herd
slug: thundering-herd
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Cache Stampede, Dogpile Effect, Cache Avalanche, Wake-One Storm]
first_described: "The Jargon File, entry for thundering herd problem, describing the Unix accept() wakeup case; the term predates web caching and was later reapplied to cache expiry storms"
maturity: canonical
related: [circuit-breaker, retry-with-backoff, bulkhead, cache-aside, rate-limiter]
incompatible_with: []
verified: 2026-08-02
---

# Thundering Herd

## 1. Name, aliases, and lineage

The canonical name is thundering herd, sometimes written thundering herd
problem. It comes from operating systems folklore, not from caching. The
Jargon File records it as the situation where many sleeping processes are
woken by a single event, all rush to check whether the event concerns them,
and all but one find that it does not, having wasted a scheduling cycle each.
Wikipedia's summary of the term states it plainly, a thundering herd is "a
performance-degrading phenomenon in computer science and computer networking
that occurs when a large number of processes or threads are simultaneously
awakened, typically in response to a specific event or the availability of a
resource," where only one process can actually do useful work and the rest
"fail and go back to sleep, wasting system resources" (Wikipedia, Thundering
herd problem, verified 2026-08-02,
https://en.wikipedia.org/wiki/Thundering_herd_problem).

The name reached its first fame through a very specific Unix mechanic.
Several worker processes or threads call `accept()` on the same listening
socket, the kernel wakes every one of them when a connection arrives, and
only the process that wins the race actually gets the file descriptor.
Everyone else was woken for nothing. That specific case has its own well
documented history in the Linux kernel, covered below under production uses.

The web-caching variant of the same phenomenon acquired its own vocabulary
over time, and the aliases are not fully interchangeable, though they overlap
heavily in casual use. Cache stampede is the most common alternative, and it
specifically names the case where a hot cache key expires and many concurrent
readers all miss at once, each independently deciding to recompute or refetch
the value. Dogpile effect is an older, slightly folksier synonym for the same
cache-expiry case, seen in memcached and Django community documentation from
the 2000s. Cache avalanche is used by some distributed-cache vendors for a
related but distinct failure, a large number of DIFFERENT keys expiring at
the same moment, often because they were all written with the same TTL, so
the backend is hit by many distinct queries rather than many duplicate
queries for one key. This entry treats thundering herd as the umbrella term
for "many actors independently converge on one scarce resource because they
all reacted to the same trigger without coordinating," and it calls out where
the cache-stampede and cache-avalanche sub-cases diverge in mechanism.

This is an anti-pattern entry, not a design pattern entry. It describes a
failure shape that recurs across unrelated layers of a system, wakeup
scheduling, cache invalidation, retry logic, connection pooling, cron
scheduling, and it catalogs the deliberate patterns (request coalescing,
jittered backoff, probabilistic early expiration, exclusive wakeup) that exist
specifically to prevent it.

## 2. Problem and context

Picture a cached product page. Ten thousand requests a second hit a CDN edge
or an application cache for the same product. The cached value has a
time-to-live of sixty seconds. At second sixty, the entry expires. All ten
thousand requests that land in the next few milliseconds see a cache miss at
the same time. Each one, independently and with no knowledge of the others,
decides the correct action is to go fetch the value from the origin database
or the origin service. The origin, which had been serving zero real queries
because the cache was absorbing everything, is suddenly hit by ten thousand
simultaneous identical queries. If the origin was provisioned to handle steady
traffic rather than instantaneous full-fanout traffic, it falls over, the
responses come back slowly or with errors, the cache stays empty because
nothing succeeded fast enough to repopulate it, and the next wave of requests
repeats the same stampede against an origin that is already unhealthy. This
is a self-reinforcing failure. The cache, whose entire purpose is to protect
the origin, becomes the trigger that destroys it.

The same shape recurs anywhere N independent actors react to one shared
signal without any mechanism to elect a single actor to do the work on
everyone else's behalf. A distributed lock expires and every node that was
waiting for it wakes at once and races to acquire it. A leader crashes and
every follower simultaneously tries to become the new leader, generating an
election storm. A service that clients poll on a fixed interval restarts, and
every client's next poll lands in the same fraction of a second because their
clocks and intervals were all aligned by a synchronized deploy or a
synchronized cron schedule. A circuit breaker closes after a cooldown and
every queued request that had been rejected during the open period fires at
the exact millisecond the breaker closes, rather than trickling back in.

The context in which the problem arises has three necessary ingredients.
First, a shared trigger, an event, an expiry, a wakeup, a reconnect signal,
that many independent actors observe at the same moment. Second, no
coordination mechanism between those actors, so each one reasons only from
its own local state and reaches the same conclusion independently. Third, a
scarce downstream resource, an origin database, a lock, a leader election
quorum, a listening socket's accept queue, that cannot absorb the full
fan-out of every actor acting simultaneously, even though it can comfortably
absorb the same aggregate load spread over a slightly longer window. Remove
any one ingredient and the herd does not thunder. If the trigger is
staggered rather than shared, the actors never converge. If the actors
coordinate, one of them can act while the rest wait. If the downstream
resource has enough headroom to absorb full fan-out, the surge is merely
wasteful rather than catastrophic.

## 3. Forces

Independence versus coordination is the central tension. Actors that never
talk to each other are simpler to build, easier to reason about individually,
and horizontally scalable in the steady state. That same independence is
exactly what removes any brake on simultaneous action. Coordination, a lock,
a leader, a coalescing layer, fixes the stampede but introduces a new single
point of contention and a new failure mode of its own, namely what happens
when the coordinator itself is unavailable.

Freshness versus load is the second force, specific to the cache-expiry
variant. A short time-to-live keeps served data close to the source of
truth, which matters for prices, inventory counts, and anything where a
stale value is a correctness bug. A long time-to-live smooths the traffic to
the origin but widens the window during which clients may see outdated data.
Thundering herd defense techniques that serve stale data during
recomputation, described in dimension 8, exist precisely to let a system
choose a short logical TTL for freshness while behaving, from the origin's
perspective, as though the TTL were much longer.

Latency versus fairness is the third force, specific to the wakeup variant.
Waking every blocked thread and letting them race for a resource is low
latency for the winner, the CPU does not have to first pick a winner before
anyone can proceed, but it wastes cycles on every loser and, at scale,
produces measurable imbalance. The LWN.net account of the Linux
`SO_REUSEPORT` work notes that under the older single-socket-many-acceptor
design, wake-ups from `accept()` are not fair, so incoming connections can
be distributed across worker threads in "a very unbalanced fashion" under
high load, with Google reporting a threefold difference between the busiest
and quietest thread in one measured case (LWN.net, "Improving load
balancing with SO_REUSEPORT," verified 2026-08-02,
https://lwn.net/Articles/542629/). Waking exactly one thread, the
exclusive-wakeup approach, is fair and wastes nothing, but it adds a small
amount of kernel bookkeeping and, in some designs, a small amount of extra
latency for that one thread to be scheduled before work can proceed.

Simplicity versus resilience budget is the fourth force. Every mitigation in
this entry, mutex-guarded recomputation, jittered backoff, probabilistic
early expiration, request coalescing, costs code, costs a small amount of
added latency on the cold path, and costs a class of bug that did not exist
before, races in the coalescing logic itself, clock skew in the jitter
calculation, a lock that is never released because of an unhandled
exception. A team must decide how much of that cost the actual blast radius
justifies. A thundering herd against an internal admin dashboard hit by
twelve engineers is an inconvenience. A thundering herd against a payments
database backing a public storefront on a sale day is an outage with a
dollar figure attached, and the resilience budget should be spent
accordingly.

## 4. Applicability and non-applicability

Reach for a deliberate thundering-herd defense when a cache-fronted resource
serves traffic whose peak concurrent request rate for a single key is high
enough that a full cache miss on that key would itself overload the origin,
when many independent processes wake on a shared external signal (a socket
becoming readable, a distributed lock's TTL expiring, a leader crashing) and
the work triggered by that wakeup is expensive enough that doing it N times
instead of once matters, when client retry logic can plausibly synchronize
across a large fleet, for instance after a shared outage, a shared deploy, or
a cron-like schedule with no jitter, and when the downstream resource being
protected has a hard concurrency ceiling, a connection pool limit, a rate
limit imposed by a third party, a fixed number of database connections,
rather than headroom that scales elastically with load.

Do not build thundering-herd defenses in these situations, because the added
complexity buys nothing.

The traffic pattern genuinely has low concurrency per key. If a cache key is
requested a handful of times a minute, a miss on expiry produces at most a
handful of duplicate origin calls, which is wasteful but never dangerous, and
a coalescing layer adds code and a new class of bug to prevent a problem that
was never going to happen.

The origin can already absorb full fan-out. A stateless origin service that
autoscales faster than the herd can arrive, or a key-value store rated for
far more queries per second than the cache's total keyspace could ever
generate on simultaneous expiry, does not need protection it will never use.
Measure this rather than assume it. It is a common and expensive mistake to
build coalescing logic against an origin that was, in fact, never at risk.

The trigger event is inherently rare and already naturally staggered, for
example independent user sessions expiring on their own individual
schedules rather than on a shared clock tick. There is no herd to defend
against if the actors were never going to converge.

The system is single-writer or single-reader by construction, for instance
a background job that runs on exactly one instance with a leader-election
mechanism already in place for an unrelated reason. A stampede requires
multiple independent actors reacting to the same event; remove the
multiplicity and the pattern in this entry has nothing to protect.

The fix under consideration is "make the cache never expire." That is not a
thundering-herd defense, it is a decision to trade correctness for load
avoidance, and it belongs under cache invalidation strategy, not here. A
system that genuinely cannot tolerate any staleness must solve the freshness
problem directly rather than disguising a stale-data policy as a performance
fix.

## 5. Structure

The problem shape has four participants, independent of which specific
mitigation is applied.

The Trigger is the shared event, a cache-entry expiry, a socket becoming
readable, a lock's lease timing out, a leader process crashing, a scheduled
job firing. It is observable simultaneously, or near-simultaneously, by
every Actor.

The Actor is any of the many independent participants that observe the
Trigger and decide to act. In the caching case an Actor is a request handler
that saw a cache miss. In the wakeup case an Actor is a blocked thread or
process. In the retry case an Actor is a client that had an in-flight
request fail.

The Scarce Resource is whatever downstream target the Actors converge on,
an origin database, a listening socket's single connection slot, a lock, a
leader-election quorum, a third-party API with a rate limit. It has a
capacity ceiling that full simultaneous fan-out from every Actor can exceed
even when the Actors' aggregate steady-state demand would not.

The Coordinator, when one exists, is the component that a mitigation
introduces to break the independence between Actors, an exclusive-wakeup
kernel primitive, an in-process mutex or coalescing map, a distributed lock
with a single-flight guarantee, a jitter source that desynchronizes retry
timing. Without a Coordinator, the four-participant structure collapses to
three, and the herd runs unopposed.

## 6. ASCII structure diagram

```
  Without a Coordinator (the anti-pattern)

    Trigger  (cache entry expires at T)
        |
        |  observed simultaneously by every Actor
        v
   +---------+   +---------+   +---------+        +---------+
   | Actor 1 |   | Actor 2 |   | Actor 3 |  . . .  | Actor N |
   +---------+   +---------+   +---------+        +---------+
        |             |             |                   |
        |  each Actor independently decides to act
        v             v             v                   v
   +--------------------------------------------------------+
   |                    Scarce Resource                     |
   |         (origin DB, socket, lock, quorum, ...)          |
   +--------------------------------------------------------+
        N simultaneous demands hit a resource sized for 1


  With a Coordinator (a mitigation from dimension 8)

   +---------+   +---------+   +---------+        +---------+
   | Actor 1 |   | Actor 2 |   | Actor 3 |  . . .  | Actor N |
   +---------+   +---------+   +---------+        +---------+
        |             |             |                   |
        +------+------+------+------+-------------------+
               |
               v
        +-------------+
        | Coordinator |   (mutex, single-flight map, exclusive
        +-------------+    wakeup, jitter source, cache lock)
               |
               |  exactly one demand reaches the resource;
               |  the rest wait for, or share, its result
               v
      +--------------------+
      |   Scarce Resource   |
      +--------------------+
```

## 7. Dynamics

The stampede sequence, without a defense, runs like this. At time T the
cached value for key K expires or is evicted. Between T and T plus a few
milliseconds, some number of request handlers, R, each look up K in the
cache and each independently observe a miss. Each of those R handlers,
having no way to know that R minus one other handlers just made the same
observation, independently issues a request to the origin for the value
behind K. The origin now receives R simultaneous, identical requests where
it would normally have received zero, because the cache had been absorbing
all of them. If R exceeds the origin's safe concurrency, response latency
for all R requests rises, some fraction of them time out or error, and the
handlers that failed either retry immediately, worsening the situation, or
give up and serve a degraded response. Because none of the R requests
completed fast enough, or completed at all, the cache for K may still be
empty a moment later, and the next wave of incoming requests for K repeats
the entire sequence against an origin that is now already under load from
the first wave's stragglers.

The coalesced sequence, with a request-coalescing Coordinator in front of
the origin, runs differently. At time T the cache for K expires. The first
handler to observe the miss, call it handler A, acquires an exclusive slot
in the Coordinator for key K and begins the origin fetch. Every other
handler that misses on K in the same window checks the Coordinator, finds
that a fetch for K is already in flight, and instead of issuing its own
origin request, it registers to receive the result of A's in-flight fetch.
When A's fetch completes, the Coordinator delivers that single result to
every registered waiter simultaneously, repopulates the cache, and releases
the slot for K. Exactly one request reached the origin, regardless of how
many handlers observed the miss.

The jittered-backoff sequence, for the retry variant, runs as follows.
Client set C, numbering in the thousands, all have an in-flight request to
service S fail at approximately the same instant, for instance because S
briefly restarted. Each client in C independently schedules a retry. If
every client uses a fixed retry delay, for example exactly one second, the
entire set C re-arrives at S in the same narrow window one second later,
producing a second, self-inflicted outage at S even though S itself has
already recovered. If each client instead schedules its retry after a base
delay plus a random jitter drawn independently per client, the arrivals
spread across a window rather than a point, and S sees a manageable ramp
instead of a spike. The AWS Builders Library and the Google SRE book both
describe this as the standard remedy, and the SRE book states the principle
directly. if retries are not randomly distributed over the retry window,
"a small perturbation (e.g., a network blip) can cause retry ripples to
schedule at the same time," and those synchronized ripples then compound
into a much larger surge (Google, Site Reliability Engineering, chapter 22,
Addressing Cascading Failures, verified 2026-08-02,
https://sre.google/sre-book/addressing-cascading-failures/).

## 8. Implementation variants

Request coalescing, also called single-flight, is the most direct defense
against the cache-stampede sub-case. It is implemented as an in-process (or,
for a multi-instance service, a distributed) map from cache key to an
in-flight future or promise. When a lookup misses, the code checks the
coalescing map before going to the origin. If an entry for that key already
exists, the code awaits that existing future rather than starting a new
origin call. If no entry exists, the code creates one, performs the origin
call, delivers the result to every waiter, and removes the entry. The three
runnable examples under this entry all implement exactly this variant, in
TypeScript with a promise map, in Go with a `sync.WaitGroup`-backed call
struct guarded by a mutex (the shape Go's own
`golang.org/x/sync/singleflight` package formalizes), and in Python with an
`asyncio.Future` keyed by cache key. The trade-off of this variant is that
it only protects a single process; a fleet of many instances still allows
one in-flight origin call per instance, so a distributed lock or a
distributed single-flight service is needed when the fan-out risk exceeds
what one instance's own concurrency could produce.

Cache locking at the reverse-proxy layer is the same idea implemented
outside application code. NGINX's `proxy_cache_lock` directive, when
enabled, makes it so that "only one request at a time will be allowed to
populate a new cache element... Other requests of the same cache element
will either wait for a response to appear in the cache or the cache lock for
this element to be released" (NGINX, ngx_http_proxy_module documentation,
proxy_cache_lock directive, verified 2026-08-02,
http://nginx.org/en/docs/http/ngx_http_proxy_module.html). This variant
requires no application-code change at all, provided the caching layer
already sits at the reverse proxy, but it only protects against duplicate
requests reaching the origin through that proxy tier; it does nothing for
stampedes that originate elsewhere in the system.

Stale-while-revalidate, sometimes described as serving stale data during
recomputation, decouples the cache-expiry moment from the origin-fetch
moment. Rather than treating an expired entry as absent, the cache continues
to serve the expired value to every reader except the one that was elected
(via a lock, or via the coalescing variant above) to refresh it in the
background. Readers never see a miss at all, only a brief window of slightly
stale data, and the origin sees exactly one refresh request per expiry
rather than a fan-out. This variant trades a small, bounded amount of
staleness for the complete elimination of miss-triggered load spikes, and it
is the correct choice whenever the applicability analysis in dimension 4
concludes that brief staleness is acceptable.

Probabilistic early expiration recomputes a cache entry slightly before its
nominal expiry, with a probability that rises the closer the entry gets to
its TTL, so that instead of every reader missing at exactly the same
instant, a small and increasing fraction of readers trigger an early,
staggered recompute in the window leading up to expiry. By the time the
entry would actually have expired, it has usually already been refreshed by
one of the early triggers, and no herd ever forms because there was never a
single shared instant at which everyone missed simultaneously. This variant
adds no locking at all; it trades a small amount of extra (but well spread)
recompute work for eliminating the shared-instant property that makes a
stampede possible in the first place. It composes well with, and is often
implemented alongside, request coalescing as a second line of defense.

Jittered exponential backoff addresses the retry-storm sub-case rather than
the cache-expiry sub-case. Each client, on a failed call, waits a base delay
that grows exponentially with the retry count, and adds a random component
so that clients which failed at the same instant do not retry at the same
instant. The AWS Architecture Blog's canonical treatment names several
concrete jitter strategies, full jitter, where the wait is a uniformly random
value between zero and the exponential cap, and equal jitter, where half the
wait is fixed and half is random, and the Google SRE book endorses the same
principle under the heading "Always use randomized exponential backoff when
scheduling retries" (Google, Site Reliability Engineering, chapter 22,
verified 2026-08-02, https://sre.google/sre-book/addressing-cascading-failures/).
This variant is orthogonal to the caching-layer variants above; a system
under retry-storm risk from client reconnects needs jitter on the client
side regardless of what caching strategy the server uses.

Exclusive kernel-level wakeup addresses the original accept()-queue
sub-case directly rather than through application logic. Linux's
`SO_REUSEPORT` socket option, added in the 3.9 kernel and documented on
LWN.net, lets multiple sockets bind to the same address and port, with the
kernel load-balancing incoming connections across them rather than waking
every listener for every connection (LWN.net, "Improving load balancing
with SO_REUSEPORT," verified 2026-08-02, https://lwn.net/Articles/542629/).
Separately, Linux 4.5 introduced the `EPOLLEXCLUSIVE` flag for `epoll`,
which the Wikipedia summary of the thundering herd problem describes as a
mechanism that makes the kernel wake only one thread or process blocked on a
shared file descriptor, rather than all of them (Wikipedia, Thundering herd
problem, verified 2026-08-02, https://en.wikipedia.org/wiki/Thundering_herd_problem).
This variant is not something application engineers implement themselves;
it is a platform capability that web servers and load-balancing proxies
adopt so that application code never has to reason about the wakeup-fairness
sub-case at all.

## 9. Known production uses

The Linux kernel's own network stack is the clearest documented instance of
the wakeup sub-case being fixed at the platform level. Before `SO_REUSEPORT`
existed, a common deployment pattern had many worker processes calling
`accept()` on one shared listening socket, and LWN.net's account of the
`SO_REUSEPORT` patch explains that under that older design, "wake-ups are
not fair, so that, under high load, incoming connections may be distributed
across threads in a very unbalanced fashion," with a factor-of-three
imbalance observed by Google engineers between the busiest and quietest
worker thread. `SO_REUSEPORT`, merged into the mainline kernel during the
3.9 development cycle, and the later `EPOLLEXCLUSIVE` flag, added in Linux
4.5, both exist specifically to remove this thundering-herd behavior from
socket-level wakeups (LWN.net, verified 2026-08-02,
https://lwn.net/Articles/542629/; Wikipedia, Thundering herd problem,
verified 2026-08-02, https://en.wikipedia.org/wiki/Thundering_herd_problem).
Modern high-concurrency servers, including NGINX and HAProxy, take advantage
of `SO_REUSEPORT` for exactly this reason.

NGINX ships a directive, `proxy_cache_lock`, whose entire purpose, per its
own reference documentation, is to prevent the cache-stampede sub-case at
the reverse-proxy tier, so that "only one request at a time" populates a
newly expired cache entry while concurrent requests for that same entry wait
rather than each independently hitting the upstream server (NGINX,
ngx_http_proxy_module documentation, verified 2026-08-02,
http://nginx.org/en/docs/http/ngx_http_proxy_module.html). This is a
first-party, named, and widely deployed production mechanism built
specifically to prevent the pattern described in this entry.

Google's own internal engineering guidance, published externally in the
Site Reliability Engineering book, treats synchronized client retries as a
named production failure category, cascading failure driven by
synchronized retry storms, and mandates randomized exponential backoff as the standing
practice across Google's production services rather than as an optional
tuning knob. "Always use randomized exponential backoff when scheduling
retries," with the chapter's own epigraphs from Google engineers
underscoring both the exponential-backoff and the jitter halves of the
recommendation (Google, Site Reliability Engineering, chapter 22,
Addressing Cascading Failures, verified 2026-08-02,
https://sre.google/sre-book/addressing-cascading-failures/). Amazon Web
Services documents the same practice, under the name jittered backoff, as
standing guidance for any client calling an AWS service, describing full
jitter and equal jitter as the concrete strategies AWS recommends to avoid
retry-storm compounding (AWS, Timeouts, retries, and backoff with jitter,
Builders' Library, verified 2026-08-02,
https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter).

## 10. Consequences

Positive, none. This is an anti-pattern, describing a failure mode, and
dimension 10 is included in this entry only to name the "consequence" of
recognizing and mitigating it, which is that a system gains resilience to a
class of self-inflicted overload that is otherwise invisible until the
exact moment it happens in production, usually at the worst possible time,
a traffic spike, a sale event, or a mass client reconnect after an
unrelated outage.

Negative, if the pattern is left unmitigated in a system with the
applicability conditions from dimension 4. origin overload precisely at the
moment the cache was supposed to be protecting the origin, which is the
opposite of the cache's purpose and therefore especially damaging to
on-call trust in the caching layer. A self-reinforcing failure loop, where
an overloaded origin causes the refresh attempts that were meant to repair
the cache to themselves fail or time out, so the cache stays empty and the
next wave of traffic repeats the stampede. A retry multiplier effect,
where clients whose requests failed during the stampede retry without
jitter, converting one stampede into a second, self-inflicted stampede a
fixed delay later. Wasted work in the wakeup sub-case, every thread or process
woken but unable to make progress still consumed a scheduling slot and
possibly a context switch, which under high concurrency is measurable CPU
and latency cost even when it does not cause an outright outage.

Negative, as a cost of the mitigations themselves, which is a judgement
call rather than a sourced fact. request coalescing introduces a new
in-process or distributed synchronization primitive that itself needs to be
correct under concurrent access, released on every code path including
exceptions, and bounded so that a hung origin call does not leave every
subsequent caller for that key permanently blocked. Stale-while-revalidate
and probabilistic early expiration trade a bounded amount of staleness for
load reduction, which is the correct trade for most read-heavy systems but
is a real, deliberate weakening of consistency that must be acceptable to
the business logic reading the data. Jittered backoff adds latency
variance, by design, to the retry path, which is invisible in aggregate
metrics but can be surprising to an engineer debugging a single slow
request who does not expect the delay to be randomized.

## 11. Failure modes and misuse

**Symptom.** Origin database or backend service CPU and connection-pool
utilization spikes to its ceiling at a regular, predictable interval, often
exactly matching a cache TTL.
**Cause.** No coalescing or stale-serving mechanism exists, so every cache-
entry expiry produces a full fan-out of duplicate origin requests from every
concurrent reader of that key.
**Fix.** Add request coalescing in front of the origin call, or switch the
cache policy to stale-while-revalidate so readers never observe a hard miss.

**Symptom.** A brief, unrelated network blip or a short service restart is
immediately followed by a second, larger outage a fixed number of seconds
later, with the second outage's traffic graph showing a sharp, narrow spike
rather than a gradual ramp.
**Cause.** Client-side retry logic uses a fixed delay with no jitter, so
every client that failed during the first blip retries in the same narrow
window, and the service that had already recovered is knocked back down by
the synchronized retry wave.
**Fix.** Switch client retry logic to exponential backoff with per-client
jitter, so retries spread across a window rather than converging on a
point.

**Symptom.** A worker fleet behind a shared listening socket shows heavily
imbalanced load, with some worker processes near their CPU ceiling and
others nearly idle, even though the incoming connections are, in aggregate,
evenly distributable work.
**Cause.** All workers call `accept()` on one shared socket and rely on the
kernel to wake and distribute connections fairly, but the older wakeup
mechanism does not guarantee fairness under load, so a subset of workers
systematically wins the accept race more often.
**Fix.** Adopt `SO_REUSEPORT` so each worker binds its own socket with
kernel-level load balancing across them, or move to a proxy or load
balancer that already implements exclusive-wakeup semantics on the
workers' behalf.

**Symptom.** A distributed lock's holder crashes or the lock's lease times
out, and immediately afterward every node that had been waiting on that
lock attempts to acquire it at the same instant, producing a burst of
failed acquisition attempts and, in some lock implementations, a burst of
load against the coordination service (etcd, ZooKeeper, a database row used
as a lock) itself.
**Cause.** The lock-waiting logic has no built-in randomization on retry
timing after observing the lock become free, so every waiter's next attempt
lands in the same narrow window.
**Fix.** Add jitter to the lock-retry interval, and consider a queue-based
or ticket-based acquisition mechanism rather than a bare compare-and-swap
race when the number of waiters is large.

**Symptom.** A team adds request coalescing to fix a cache stampede, but the
stampede persists, or a new failure mode appears where a single slow origin
call causes every subsequent request for that key to hang until a timeout,
across the entire fleet.
**Cause.** The coalescing map is per-process rather than shared across
instances, so a fleet of many application instances still allows one
in-flight origin request per instance, up to N times the intended
concurrency, and separately, the coalescing logic has no timeout or
circuit-breaker of its own, so a hung origin call blocks every waiter
indefinitely rather than failing fast.
**Fix.** Move coalescing to a shared layer, a reverse proxy with cache
locking, or a distributed single-flight service, when the fleet has more
than one instance, and always bound the in-flight call with its own timeout
so a hung origin degrades gracefully rather than hanging every waiter.

## 12. Trade-off matrix

| Approach | Prevents cache stampede | Prevents retry storm | Prevents wakeup imbalance | Added latency on miss path | Distributed (multi-instance) safe |
|---|---|---|---|---|---|
| No mitigation | No | No | No | None | N/A |
| Request coalescing (single-flight) | Yes | No | No | Small, waiters block on the single in-flight call | Only with a shared/distributed coalescing layer |
| Reverse-proxy cache lock (NGINX proxy_cache_lock) | Yes, at the proxy tier only | No | No | Small, configurable wait timeout | Yes, if all traffic passes through the shared proxy tier |
| Stale-while-revalidate | Yes, and eliminates the miss window entirely | No | No | None on the read path; refresh happens in background | Needs a shared refresh-election mechanism to avoid duplicate refreshes |
| Probabilistic early expiration | Reduces likelihood sharply, does not guarantee zero | No | No | Small, extra recompute work spread before expiry | Yes, no coordination needed between instances |
| Jittered exponential backoff | No | Yes | No | Adds randomized delay to the retry path by design | Yes, purely client-local |
| SO_REUSEPORT / EPOLLEXCLUSIVE | No | No | Yes | None, kernel-level, no application latency cost | N/A, operates within a single host's socket layer |

## 13. Related and incompatible patterns

Circuit Breaker composes directly with thundering-herd defenses. Where
request coalescing and cache locking prevent an origin from being
overloaded by duplicate concurrent requests for the same key, a circuit
breaker protects the origin when it is already unhealthy for unrelated
reasons, and the two are frequently deployed together, coalescing to
prevent self-inflicted overload, circuit breaking to fail fast once the
origin is overloaded regardless of cause.

Retry with Backoff, specifically its jittered-exponential variant, is the
direct fix for the retry-storm sub-case of thundering herd, and the two
entries should be read together; this entry names the failure shape, the
retry pattern describes the client-side mechanism in full.

Bulkhead composes with coalescing in a complementary way, a bulkhead limits
how much concurrency any one caller or tenant can consume against a shared
resource, which bounds the worst case even if a coalescing layer is
imperfect or absent for some code path, acting as a second line of defense
rather than a replacement for it.

Cache-Aside is the base pattern whose naive implementation, look up the
cache, on a miss go to the origin and populate the cache, is exactly what
produces the cache-stampede sub-case when it has no coalescing or
stale-serving refinement. This entry should be treated as a required
reading companion to any cache-aside implementation serving concurrent
traffic, not as an alternative to it.

Rate Limiter is a partial mitigant but not a fix. A rate limiter placed in
front of the origin bounds the damage a stampede can do, by rejecting
requests past a threshold, but it does not prevent the stampede itself and
converts an overload into a wave of rejected requests instead, which is
often preferable to an outage but is still a symptom of the underlying
uncoordinated fan-out rather than a cure for it.

There are no patterns that are structurally incompatible with recognizing
or mitigating thundering herd; the mitigations in dimension 8 are additive
defenses that layer onto whatever caching or retry architecture a system
already has.

## 14. Refactoring path in and out

To introduce request coalescing into an existing cache-aside implementation,
first identify the hot keys, the small number of cache entries whose
concurrent read volume is high enough that a simultaneous miss would exceed
the origin's safe concurrency; instrumenting cache miss rate per key for a
representative traffic window is the cheapest way to find them. Second,
introduce a coalescing layer scoped to exactly those keys rather than
rewriting the entire caching path at once, since a narrow rollout limits the
blast radius of a bug in the new synchronization logic. Third, add a bounded
timeout to the coalesced origin call itself, so a hung origin call cannot
leave every coalesced waiter blocked indefinitely, and add a test, described
under dimension 15, that specifically exercises the timeout path. Fourth,
once the narrow rollout is proven correct under load, generalize the
coalescing layer to the full cache-aside path, or replace it with a
proxy-tier mechanism, such as `proxy_cache_lock`, if the traffic already
flows through a shared reverse proxy and per-application-instance coalescing
is therefore redundant.

To remove request coalescing once it has stopped earning its place, first
confirm the removal is safe by checking whether the origin's own
provisioned capacity now exceeds the theoretical worst-case fan-out for the
protected key, which can happen after an origin migration to a system with
substantially higher concurrency headroom. Second, remove the coalescing
layer behind the same feature flag or narrow rollout discipline used to add
it, watching origin load metrics during the removal window rather than
assuming the earlier analysis still holds. Third, keep the stale-while-
revalidate or probabilistic-early-expiration layer, if one exists, even
after removing coalescing, since those layers are cheap, harmless on an
over-provisioned origin, and continue to provide a second line of defense
against a future capacity regression.

## 15. Testing and verification

Testing a thundering-herd defense is testing a concurrency property, not a
functional one, and the test must actually create concurrent contention
rather than merely asserting the coalescing function's individual behavior
in isolation. The standard shape, demonstrated in all three code examples
under this entry, is to fire N concurrent callers at the same key
simultaneously, using `Promise.all` in TypeScript, a `sync.WaitGroup` fan-out
in Go, or `asyncio.gather` in Python, against a fake backend that counts how
many times it was actually invoked, and to assert that the backend call
count is exactly one regardless of N, while every caller still receives the
correct, identical result. This is easy to test because the coalescing
layer's entire contract is that single invariant, one backend call per
overlapping window, and it becomes harder to test correctly once the origin
call itself has a realistic, variable latency, since a naive test with an
instantaneous fake backend can pass even when the coalescing window is too
narrow to catch real-world overlapping requests; introducing a small, fixed
artificial delay in the fake backend, as the examples in this entry do, is
what makes the concurrent overlap actually observable in a test run rather
than a coincidence of scheduling.

A second required test exercises the failure path specifically, what
happens to waiting callers when the single in-flight origin call itself
errors or times out. The correct behavior is that every waiter receives the
same error, or the same fallback, rather than the coalescing layer silently
swallowing the failure for the caller who happened to initiate the call
while returning something different to callers who joined afterward. This
test is what catches the misuse pattern from dimension 11 where a hung
origin call blocks every waiter forever; the test should assert that a
bounded timeout on the origin call is actually observed by every waiter
within the expected bound, not merely by the initiating caller.

For the retry-storm sub-case specifically, testing jittered backoff is
testing a statistical property, not an exact value, since jitter is
deliberately random. The correct test asserts that repeated retry-delay
calculations for the same input produce a distribution rather than a
constant, for example by asserting the observed delays fall within the
documented jitter bounds across many samples, and separately, a fixed-seed
deterministic test of the underlying pseudo-random generator to catch
regressions in the jitter algorithm itself without relying on true
randomness inside the automated test suite.

## 16. Observability signals

For the cache-stampede sub-case, the primary signal is origin request rate
plotted against cache hit rate on the same timeline; a healthy system shows
origin request rate staying flat and low even as cache hit rate dips
briefly around a TTL boundary, while an unmitigated stampede shows a sharp,
narrow spike in origin request rate that coincides exactly with the cache
miss. A coalescing layer, once introduced, should expose its own metric,
coalesced call count versus actual origin call count for the same key and
window; a healthy coalescing layer shows this ratio far above one during a
traffic spike and close to one during quiet periods, and a ratio that stays
near one even during a known spike indicates the coalescing layer is not
actually engaging, often because keys are not being normalized consistently
between callers.

For the retry-storm sub-case, the signal to watch is the standard deviation,
not merely the mean, of client retry arrival times following a known
upstream blip; a system with effective jitter shows retries spread across
the intended backoff window, while a system without jitter shows retries
clustered into a narrow spike a fixed delay after the original failure,
visible as a secondary traffic spike on the same dashboard that first showed
the original outage.

For the wakeup sub-case, per-worker connection-acceptance count, sampled
over a load-test window, is the direct signal; a healthy `SO_REUSEPORT`
deployment shows roughly even acceptance counts across workers, while an
imbalanced single-socket design shows the kind of multiple-fold skew
between the busiest and quietest worker that the LWN.net account of the
`SO_REUSEPORT` motivation describes.

A healthy dashboard, across all sub-cases, shows load smoothing out over a
window proportional to the mitigation's design, a coalescing window's
length, a jitter range's width, rather than concentrating into a spike; a
failing dashboard shows periodicity, a repeating spike at a fixed interval
that matches a TTL, a retry delay, or a cron schedule, which is itself a
strong diagnostic signal pointing directly at the missing mitigation.

## 17. Security and privacy implications

A cache-stampede vulnerability is, in effect, a cost-multiplying vector for
a denial-of-service attack, and this is analytical rather than a sourced
claim about any specific incident. An attacker who can predict or trigger a
cache-entry expiry, or who can simply issue enough concurrent requests for
an uncached or rarely-cached key, can turn a small number of attacker
requests into a much larger number of origin requests if no coalescing
defense exists, which is a materially cheaper attack than a conventional
volumetric denial-of-service attempt because the attacker's own request
volume does not need to match the load inflicted on the origin.

Request-coalescing layers introduce their own, narrower security surface.
Because a coalescing map is keyed by cache key, a coalescing layer that
incorrectly derives its key from partially attacker-controlled input, for
instance a cache key built from an unvalidated query parameter, can be
manipulated to either force excessive fan-out, by making every request use
a distinct key so it never benefits from coalescing, or, more subtly,
to have one caller's request incorrectly reuse another caller's in-flight
result if the key derivation collapses two logically distinct requests into
the same coalescing key. The latter case is a data-leakage risk
specifically when the origin call's result depends on caller-specific
context, such as an authorization check or a per-user personalization,
that the coalescing key does not capture; a coalescing layer must always
key on the full set of inputs that affect the result, including any
authorization context, or it can leak one user's response to a different
user who happened to request the same nominal resource concurrently.

Jittered backoff has no privacy implication of its own, though the
randomness source used to generate the jitter should be a standard
pseudo-random generator seeded appropriately for the runtime, since a
predictable jitter sequence defeats the purpose of desynchronizing clients
and, in an adversarial setting, could in principle let an attacker who
controls many clients still synchronize their retries by predicting the
jitter values, though this is a low-severity, largely theoretical concern
for the common case of client-local jitter used purely for load smoothing
rather than for any security-sensitive timing property.

## 18. References

1. Wikipedia. "Thundering herd problem." Verified 2026-08-02.
   https://en.wikipedia.org/wiki/Thundering_herd_problem
2. LWN.net. "Improving load balancing with SO_REUSEPORT." Verified
   2026-08-02. https://lwn.net/Articles/542629/
3. Google. Site Reliability Engineering, chapter 22, "Addressing Cascading
   Failures." Verified 2026-08-02.
   https://sre.google/sre-book/addressing-cascading-failures/
4. NGINX. ngx_http_proxy_module documentation, proxy_cache_lock directive.
   Verified 2026-08-02. http://nginx.org/en/docs/http/ngx_http_proxy_module.html
5. Amazon Web Services. "Timeouts, retries, and backoff with jitter,"
   Builders' Library. Verified 2026-08-02.
   https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter

## Code examples

Every example below implements the same request-coalescing Coordinator
against a fake, artificially delayed backend, fires fifty concurrent
callers at one key, and asserts the backend was invoked exactly once.

### TypeScript

```typescript
// Request coalescing: concurrent callers for the same key share one
// in-flight promise instead of each triggering a backend fetch.
class Coalescer<T> {
  private inFlight = new Map<string, Promise<T>>();

  async run(key: string, load: () => Promise<T>): Promise<T> {
    const existing = this.inFlight.get(key);
    if (existing) return existing;

    const promise = load().finally(() => this.inFlight.delete(key));
    this.inFlight.set(key, promise);
    return promise;
  }
}

async function fakeBackendFetch(calls: { count: number }): Promise<string> {
  calls.count += 1;
  await new Promise((r) => setTimeout(r, 20));
  return "value-from-backend";
}

async function main() {
  const coalescer = new Coalescer<string>();
  const calls = { count: 0 };

  const results = await Promise.all(
    Array.from({ length: 50 }, () =>
      coalescer.run("product:42", () => fakeBackendFetch(calls))
    )
  );

  console.log(`backend calls: ${calls.count}`);
  console.log(`callers served: ${results.length}`);
  console.log(`all identical: ${results.every((r) => r === results[0])}`);
}

main();
```

Run and verified output.

```
backend calls: 1
callers served: 50
all identical: true
```

### Go

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// call represents a single in-flight backend load for a key.
type call struct {
	wg    sync.WaitGroup
	value string
}

// Coalescer ensures only one backend load runs per key at a time.
// Every other caller for the same key waits on the same result.
type Coalescer struct {
	mu    sync.Mutex
	calls map[string]*call
}

func NewCoalescer() *Coalescer {
	return &Coalescer{calls: make(map[string]*call)}
}

func (c *Coalescer) Do(key string, load func() string) string {
	c.mu.Lock()
	if existing, ok := c.calls[key]; ok {
		c.mu.Unlock()
		existing.wg.Wait()
		return existing.value
	}

	ongoing := &call{}
	ongoing.wg.Add(1)
	c.calls[key] = ongoing
	c.mu.Unlock()

	ongoing.value = load()
	ongoing.wg.Done()

	c.mu.Lock()
	delete(c.calls, key)
	c.mu.Unlock()

	return ongoing.value
}

func main() {
	coalescer := NewCoalescer()
	var backendCalls int32
	var mu sync.Mutex

	load := func() string {
		mu.Lock()
		backendCalls++
		mu.Unlock()
		time.Sleep(20 * time.Millisecond)
		return "value-from-backend"
	}

	var wg sync.WaitGroup
	results := make([]string, 50)
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			results[idx] = coalescer.Do("product:42", load)
		}(i)
	}
	wg.Wait()

	allSame := true
	for _, r := range results {
		if r != results[0] {
			allSame = false
		}
	}

	fmt.Printf("backend calls: %d\n", backendCalls)
	fmt.Printf("callers served: %d\n", len(results))
	fmt.Printf("all identical: %v\n", allSame)
}
```

Run and verified output.

```
backend calls: 1
callers served: 50
all identical: true
```

### Python

```python
import asyncio
import random


class Coalescer:
    """Ensures only one backend load runs per key. Every other caller
    for the same key awaits the same future instead of triggering a
    fresh load."""

    def __init__(self):
        self._inflight: dict[str, asyncio.Future] = {}

    async def run(self, key: str, load):
        existing = self._inflight.get(key)
        if existing is not None:
            return await existing

        future = asyncio.ensure_future(load())
        self._inflight[key] = future
        try:
            return await future
        finally:
            del self._inflight[key]


async def main():
    coalescer = Coalescer()
    backend_calls = 0

    async def fake_backend_fetch():
        nonlocal backend_calls
        backend_calls += 1
        await asyncio.sleep(0.02 + random.uniform(0, 0.005))
        return "value-from-backend"

    results = await asyncio.gather(
        *[coalescer.run("product:42", fake_backend_fetch) for _ in range(50)]
    )

    print(f"backend calls: {backend_calls}")
    print(f"callers served: {len(results)}")
    print(f"all identical: {all(r == results[0] for r in results)}")


asyncio.run(main())
```

Run and verified output.

```
backend calls: 1
callers served: 50
all identical: True
```

Java, Rust, Swift, C#, and Kotlin were not run for this entry. The three
languages above cover a single-threaded event-loop runtime (Node.js), a
goroutine-and-mutex concurrency model (Go), and a coroutine-based async
runtime (Python), which together demonstrate the coalescing pattern across
the three dominant concurrency models it is implemented against in
production; the pattern translates directly to Java (a `ConcurrentHashMap`
of `CompletableFuture`), Rust (a `Mutex<HashMap<K, Shared<...>>>` guarding
a shared future), and Kotlin (a `Mutex`-guarded map of `Deferred` values)
without a structural change to the approach.
