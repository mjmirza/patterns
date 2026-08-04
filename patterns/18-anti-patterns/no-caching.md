---
name: No Caching
slug: no-caching
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Uncached Read Path, Compute Every Time, Cache Absence, Naive Recomputation]
first_described: "Folk knowledge, systems performance engineering practice, no single named originator"
maturity: established
related: [cache-aside, read-through, write-through, write-behind, n+1-query, chatty-i-o, busy-database]
incompatible_with: []
verified: 2026-08-02
---

# No Caching

## 1. Name, aliases, and lineage

No Caching is the anti-pattern of recomputing or refetching the same expensive
result on every request instead of storing it once and reusing it. It has no
single named originator the way Gang of Four patterns do. it is a folk term in
systems and performance engineering, closer in status to N+1 Query or Chatty
I/O than to a pattern from a 1994 catalog. The name appears informally across
performance engineering literature and vendor documentation rather than in one
canonical publication.

The clearest formal framing of the problem it names comes from database and
web caching theory rather than from a single book. Django's own documentation
states the underlying trade-off plainly. "A fundamental trade-off in dynamic
websites is, well, they're dynamic. Each time a user requests a page, the web
server makes all sorts of calculations, from database queries to template
rendering to business logic, to create the page that your site's visitor
sees." Django then defines the fix in one line. "To cache something is to save
the result of an expensive calculation so that you don't have to perform the
calculation next time" (Django Software Foundation, Django cache framework
documentation, version 5.2, "Django's cache framework" topic guide,
https://docs.djangoproject.com/en/5.2/topics/cache/, verified 2026-08-02).

No Caching is the state that exists before any caching pattern is applied. it
is the absence, not an implementation choice someone deliberately makes with a
name attached. It earns a catalog entry for the same reason Magic Numbers and
God Object do. it is a recurring, recognizable, costly mistake that a reader
needs a name for, so a code review or an incident postmortem can point at it
directly. Related entries in this catalog (Cache-Aside, Read-Through,
Write-Through, Write-Behind) describe the cures. this entry describes the
disease.

## 2. Problem and context

A system computes or fetches a value that is expensive relative to how often
it is actually needed fresh, and it does that computation or fetch again, in
full, on every single request that needs the value, even when the underlying
data has not changed since the last time.

The concrete situation looks like this. A product page handler runs a
five-table join to build a "related products" list on every page view, even
though the underlying catalog changes a handful of times a day. A currency
conversion service calls an external exchange-rate API on every checkout,
even though exchange rates are published once an hour. A dashboard recomputes
a rolling 30-day aggregate over millions of rows on every load, even though
the same aggregate was computed ninety seconds ago for a different user
looking at the same report. A configuration value is read from a remote
config service on every request handler invocation, even though the value
changes a few times a month.

The problem shows up as latency the user feels directly, as load that
threatens to take down the database or the upstream API, and as cost, because
every one of those recomputations or refetches is billed, whether in database
CPU time, in API request quota, or in cloud compute minutes. It is one of the
most common performance findings in a code review of a system that has never
been profiled, because the absence of caching produces no error, no warning,
and no test failure. It only produces a bill and a stopwatch, both of which
are silent until someone measures them.

The context in which the problem becomes acute is any read path with a
skewed access pattern, specifically a value that is read far more often than
it is written, or a value whose computation cost is out of proportion to how
often its inputs actually change. AWS's own caching guidance frames this
directly around database protection. it describes lazy caching populating a
cache "when the application first requests" a value so that "the cache only
contains objects that the application actually requests," and separately
warns that when a cache is cold and many requests arrive at once, "each
[request] will hit the same database query in parallel," creating a real hit
on the database (Amazon Web Services, "Caching Overview. Best Practices",
https://aws.amazon.com/caching/best-practices/, verified 2026-08-02). No
Caching is what that guidance describes as the starting condition every cache
is introduced to fix.

## 3. Forces

Correctness versus speed. A cache can serve a value that is technically stale
relative to the source of truth. No Caching gives up nothing on this axis,
because every read is fresh by construction. it buys that freshness by paying
in latency and load on every single request, no exceptions.

Memory and storage cost versus compute and I/O cost. Caching trades memory
(or a dedicated cache tier's storage) for saved compute or saved network
round trips. No Caching spends zero extra memory but spends full compute and
full I/O on every access. When the underlying computation is genuinely cheap
and the cache management overhead would exceed the savings, this is the
correct trade. when the computation is expensive and reused often, it is not.

Simplicity versus operability. A system with no caching layer has one less
moving part to reason about. there is no cache invalidation logic, no
eviction policy, no stale-read bug class, no cache stampede to defend against.
Phil Karlton's oft-repeated line that "there are only two hard things in
Computer Science, cache invalidation and naming things" is a standing
acknowledgment that adding a cache is not free engineering effort. No Caching
is simpler to build and simpler to reason about correctness for. it is more
expensive to operate at any real scale.

Read-to-write ratio. The single force that decides whether No Caching is a
defect or a defensible choice. A value read a thousand times for every one
time it is written is exactly the shape caching exists to serve. A value
written as often as it is read gains little from caching and may lose
correctness guarantees for the gain.

Blast radius under load. An uncached read path degrades along with request
volume until it hits a hard resource limit, at which point it degrades
sharply, because every concurrent request is doing full work at the same
time and competing for the same downstream resource, a connection pool, a
lock, a rate limit. A cached path degrades more gently because the
downstream system only sees a fraction of the traffic the frontend sees.

Cost accounting. Cloud-billed compute, database read-capacity units,
managed-API call quotas, and egress bandwidth are all metered. No Caching
multiplies every one of those meters by the request volume instead of by the
change frequency of the underlying data, which is very often orders of
magnitude smaller.

## 4. Applicability and non-applicability

No Caching is the correct choice, and adding a cache would be the actual
anti-pattern, when any of these hold.

The computation is already cheap relative to the request rate. reading a
single row by primary key from a well-indexed table that fits in the
database's own buffer pool is frequently faster, end to end, than a network
round trip to a separate cache tier. Adding an external cache here adds
latency and a new failure mode for little real gain.

Correctness requires strict read-your-writes or linearizable consistency on
every read, and the business cannot tolerate any staleness window, however
small. a financial ledger balance shown at the exact moment of a transfer, an
inventory count used to decide whether to accept the very next order, a
one-time authorization token that must never be reused. these need a cache
invalidated so aggressively and synchronously that it stops functioning as a
cache and starts functioning as a second source of truth that must itself be
kept perfectly consistent, which usually costs more than it saves.

The value is read once per write, or close to it. a personalized value
computed uniquely for a single session with no reuse across requests gains
nothing from a cache and only pays the cache's storage and management cost.

The system is at a scale where the added operational surface, a new
dependency to run, monitor, patch, and reason about failure modes for, is not
justified by the traffic it would offload. a low-traffic internal tool with
ten users does not need a Redis tier.

The data changes so often, and unpredictably, that any cache TTL short
enough to bound staleness to an acceptable window would also be short enough
to give a negligible hit rate, making the cache pure overhead.

No Caching is the wrong choice, and represents a genuine defect, when any of
these hold.

The same expensive computation or fetch is repeated for many requests in
quick succession with no change to its inputs. this is the textbook shape.

The read path is measurably the costliest step in a profiled hot path, and
the underlying data's write frequency is lower, by a real margin, than its
read frequency.

An upstream dependency, a third-party API, a legacy system, a rate-limited
service, has a request quota or a cost per call that the uncached traffic
volume threatens to exceed.

A cold-start stampede risk exists. multiple concurrent requests independently
triggering the same expensive recomputation because nothing coordinates or
remembers that the work is already being done, or was done a moment
ago.

The absence of caching is not a deliberate, documented, load-tested decision,
but simply the fact that nobody added one. this is the most common real-world
case. the code was never wrong on a small dataset in development, and nobody
revisited it once traffic grew.

## 5. Structure

No Caching has no participants in the sense a design pattern does, because it
is defined by the absence of a component, not the presence of one. It is
useful instead to name the structure of the uncached path so its shape is
recognizable, and to name the components that a correct fix (Cache-Aside)
would introduce, so the contrast is clear.

The uncached path has three elements. a Caller, which issues a request that
needs a Value. a Computation or Fetch, which is the expensive step that
produces the Value from its inputs, a database query, a remote API call, a
CPU-bound calculation, or a template render. and a Source of Truth, which
holds the underlying data the Computation reads. Every single Caller
invocation walks the full path from Caller through Computation to Source of
Truth and back, with no shortcut, regardless of whether the previous Caller,
a moment earlier, asked for the identical Value.

The corrected structure, using the Cache-Aside shape as the reference fix,
introduces a fourth element, a Cache, sitting between the Caller and the
Computation. The Caller first asks the Cache. On a hit, the Cache returns the
Value directly, and the Computation and Source of Truth are never touched.
On a miss, the Caller falls through to the Computation, gets the Value from
the Source of Truth, and writes it into the Cache before returning, so the
next Caller with the same request gets a hit.

## 6. ASCII structure diagram

```
NO CACHING (every request pays full cost)

  Caller 1  ---\
  Caller 2  ----\        ______________       ______________
  Caller 3  -----+----> | Computation  | --> | Source of    |
  Caller 4  ----/       | or Fetch     |     | Truth        |
  Caller N  ---/        |______________|     |______________|

  N callers asking for the SAME value trigger N full round trips.
  Latency and load scale with request volume, not with how often
  the underlying value actually changes.


WITH CACHING (Cache-Aside, for contrast)

                          hit
  Caller 1  --\      ___________
  Caller 2  ---+--->| Cache     |----(hit)----> returned directly
  Caller 3  --/     |___________|
                          |
                        miss
                          |
                          v
                   ______________       ______________
                  | Computation  | --> | Source of    |
                  | or Fetch     |     | Truth        |
                  |______________|     |______________|
                          |
                    write result
                       into Cache
                    (populate for
                     next request)
```

## 7. Dynamics

Under No Caching, the runtime sequence is identical for every request,
regardless of whether an identical request was served a millisecond ago.

```
Request arrives at handler
    |
    v
Handler needs Value V
    |
    v
Handler executes full Computation/Fetch for V
    (database query, API call, CPU work, template render)
    |
    v
Source of Truth returns raw data
    |
    v
Handler transforms raw data into V
    |
    v
Handler returns V to caller
    |
    v
V is discarded. Nothing about this
work is remembered for the next request.
```

The dynamics become dangerous under concurrency, in a shape usually called
the thundering herd or cache stampede when it happens even in a system that
does have a cache but the cache went cold. AWS's caching guidance
describes the mechanism directly. "If your cache goes down and all traffic
routes directly to your database, the sudden increase in traffic could cause
severe latency issues or make your database completely unresponsive," and
under a cold cache, "each [request] will hit the same database query in
parallel" (Amazon Web Services, "Caching Overview. Best Practices",
https://aws.amazon.com/caching/best-practices/, verified 2026-08-02). No
Caching is the permanent, structural version of this failure mode. it is not
a transient state the system recovers from when the cache warms back up,
because there is no cache to warm. Every burst of concurrent identical
requests is, by definition, always a full-strength thundering herd against
the Source of Truth, every single time.

```
Concurrent burst under NO CACHING (worst case, always present)

  t=0   Request A, B, C, D, E all arrive within the same millisecond,
        all needing the identical Value V.
    |
    v
  t=0   Each of A, B, C, D, E independently begins its own full
        Computation/Fetch. Five identical, unnecessary, simultaneous
        round trips to the Source of Truth.
    |
    v
  t=1   Source of Truth (a database, an API) processes five
        redundant identical queries at once, competing for the
        same connection pool, lock, or rate limit budget.
    |
    v
  t=2   All five callers get their answer, five times slower in
        aggregate than necessary, having spent five times the
        resource budget a single computation plus reuse would
        have required.
```

## 8. Implementation variants

There is no implementation variant of No Caching itself, since it is an
absence, but it is useful to name the concrete forms it takes in real code,
because each form has a distinct signature a reviewer learns to spot.

The repeated query variant. an ORM or raw SQL query re-executed inside a loop
or on every request handler invocation, where the query's result set does
not depend on anything unique to that invocation. This is the sibling of the
N+1 Query anti-pattern, but broader. N+1 Query is specifically about a single
logical operation issuing N redundant queries where one batched query would
do. No Caching is about the same expensive query being reissued across many
separate top-level requests over time.

The recomputed derived-value variant. a value that is a pure function of
slowly changing inputs, a hashed password comparison salt lookup, a parsed
and validated configuration object, a compiled regular expression, a rendered
template, rebuilt from scratch on every use instead of computed once and
reused for the lifetime the inputs remain valid.

The uncached remote-call variant. an HTTP or RPC call to another service,
issued fresh on every request, for data that changes far less often than the
call is made. This is the variant HTTP caching headers exist to solve. MDN's
HTTP caching documentation states the underlying mechanism plainly. "The HTTP
cache stores a response associated with a request and reuses the stored
response for subsequent requests" (Mozilla Developer Network, "HTTP caching",
https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching, verified
2026-08-02). A server or client that never sets or honors Cache-Control,
ETag, or Last-Modified headers, and that never stores a response for reuse,
shows this variant at the protocol level.

The missing memoization variant. a pure, deterministic, CPU-bound function
called repeatedly with the same arguments inside a single request or a
single process lifetime, recomputed every call instead of memoized. This is
the smallest-scoped form of the anti-pattern, often fixable with a single
in-process memoization wrapper rather than an external cache tier.

The cold-path-every-time variant, specific to frameworks with a declarative
caching abstraction available but unused. Spring's own documentation
describes exactly the fix this variant is missing. "The Spring Framework
provides support for transparently adding caching to an existing Spring
application. Similar to the transaction support, the caching abstraction
allows consistent use of various caching solutions with minimal impact on the
code," delivered through the `@Cacheable` annotation and JSR-107 support
(Spring Framework Reference Documentation, "Cache Abstraction",
https://docs.spring.io/spring-framework/reference/integration/cache.html,
verified 2026-08-02). A Spring service method that recomputes an expensive
result on every call, with no `@Cacheable` annotation and no equivalent
manual caching, and no documented reason for the omission, is this variant.

## 9. Known production uses

No Caching cannot itself have a "known production use" the way a design
pattern does, since nobody deliberately ships the absence of a feature as a
named architectural decision. What is genuinely well documented, and serves
the same evidentiary role for this entry, is the caching infrastructure that
entire industries have built specifically because the uncached default does
not scale, which is strong indirect evidence for how costly and common the
anti-pattern is in the code these tools exist to fix.

Django ships a first-class, multi-backend cache framework, per-site,
per-view, template fragment, and a low-level API, over Memcached, Redis,
database, filesystem, or local-memory backends, explicitly because, per its
own documentation, dynamic page generation is expensive enough on every
request that the framework treats caching as a core, documented concern
rather than an optional add-on (Django Software Foundation, "Django's cache
framework", https://docs.djangoproject.com/en/5.2/topics/cache/, verified
2026-08-02).

Spring Framework ships a Cache Abstraction, present since Spring 3.1,
specifically so that adding caching to "an existing Spring application" can
be done "transparently" and "with minimal impact on the code" (Spring
Framework Reference Documentation, "Cache Abstraction",
https://docs.spring.io/spring-framework/reference/integration/cache.html,
verified 2026-08-02). The framework's own description, that caching is added
to an existing application, is itself evidence that the uncached starting
state is the common, unremarkable default that later needs correcting.

Amazon Web Services publishes dedicated caching best-practices guidance
built around the specific failure mode this entry describes, what happens
to a database when every request is served without a cache, alongside the
thundering-herd risk description quoted in dimension 7 (Amazon Web Services,
"Caching Overview. Best Practices",
https://aws.amazon.com/caching/best-practices/, verified 2026-08-02). The
existence of a major cloud provider's dedicated best-practices page, aimed
at customers whose applications lack this infrastructure, is direct evidence
of how often production systems ship without it.

HTTP itself, as a protocol, carries a dedicated caching layer for exactly
this reason. every browser, CDN, and reverse proxy honoring Cache-Control,
ETag, and Last-Modified exists to prevent origin servers from having to
regenerate and retransmit identical responses on every request, which MDN
documents as the mechanism where "the HTTP cache stores a response associated
with a request and reuses the stored response for subsequent requests"
(Mozilla Developer Network, "HTTP caching",
https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching, verified
2026-08-02). Any site that fails to set these headers, or sets them
incorrectly, shows No Caching at internet scale, and this is common enough
that web performance tooling such as Lighthouse and WebPageTest flags
missing or weak cache headers as a standard finding.

## 10. Consequences

Positive consequences of leaving a path uncached, where that absence is
deliberate.

Every read reflects the true, current state of the Source of Truth with no
staleness window whatsoever, which matters where correctness genuinely
cannot tolerate any lag.

The system has fewer moving parts. no cache to provision, monitor, size,
evict from, or reason about invalidation for, and no new failure mode where
the cache itself becomes unavailable or serves corrupted data.

There is no class of stale-read bug, no cache-invalidation bug, and no
cache-stampede risk, because none of that machinery exists to fail.

Negative consequences, which outweigh the above once request volume or
computation cost crosses a real threshold.

Latency scales with the cost of the Computation or Fetch on every single
request, with no discount for repeated identical work, so the user-facing
response time never benefits from the fact that the same answer was already
computed a moment ago.

Load on the Source of Truth scales with request volume rather than with how
often the underlying data actually changes, which is very often orders of
magnitude lower, and under bursty concurrent demand that scaling turns sharp
and sudden.

Cost scales the same way. metered database read units, third-party API call
quotas, and cloud compute minutes are all billed per invocation, so an
uncached hot path multiplies spend by request volume instead of by data
change frequency.

The system has no headroom against traffic spikes. a marketing campaign, a
viral post, or a batch job that suddenly increases request volume translates
directly into proportional load on every downstream dependency, with no
buffer absorbing the difference.

Failure modes propagate upward. when the Source of Truth is slow or briefly
unavailable, every request depending on it is slow or fails, with no cached
fallback to serve a slightly stale but still useful answer.

## 11. Failure modes and misuse

Symptom. p99 latency on a specific endpoint or handler is much higher than
the median, and profiling shows the same expensive database query or
external API call appearing repeatedly across unrelated requests with
identical arguments. Cause. the query or call result is not being reused
across requests that need the identical value. Fix. introduce a cache-aside
layer keyed on the query's arguments, with a TTL bounded by how stale the
business can tolerate the value being.

Symptom. Database CPU or connection-pool utilization spikes sharply and out
of proportion during traffic increases, well before application-server CPU
becomes the bottleneck. Cause. every application request is generating a
fresh database round trip for data that changes far less often than it is
read. Fix. cache the read path, and separately verify the query itself is
indexed correctly, since caching a slow query hides but does not fix a
missing index, and the cache miss path will still be slow.

Symptom. A third-party API integration starts returning 429 Too Many
Requests errors under normal, not even unusually high, traffic. Cause. the
integration issues a fresh call for the same external value on every
internal request that happens to need it, with no local caching of a value
that the third party itself may update far less often than it is queried.
Fix. cache the external response locally with a TTL aligned to how often
the third party's data actually changes, and respect any Cache-Control or
rate-limit headers the third party's response provides.

Symptom. During a traffic spike or right after a deploy that clears
in-memory state, error rates and latency spike sharply for a short window,
then recover on their own. Cause. cold-start thundering herd, many
concurrent requests independently recomputing or refetching the same value
because nothing coordinates the work or remembers it was already done. Fix.
introduce request coalescing or a single-flight guard in front of the
Computation, so concurrent identical requests share one in-flight
computation rather than issuing N redundant ones, in addition to a cache for
subsequent requests.

Symptom. A pure, deterministic, CPU-heavy function shows up prominently in a
CPU profiler's flame graph, called from many different call sites with a
narrow, repeating set of argument values. Cause. missing memoization inside a
single request or process lifetime. Fix. wrap the function with a bounded,
process-local memoization cache keyed on its arguments.

Misuse in the opposite direction is worth naming here because it is the
mirror-image mistake a reader chasing this entry sometimes makes next.
caching a value that changes on every read, caching a value unique to a
single caller with no reuse, or caching without any invalidation strategy so
the cache silently drifts from the Source of Truth forever. That mistake is
covered by the companion entries for Cache-Aside, Write-Through, and
Write-Behind, not by this one. this entry's failure modes are specifically
about the absence of caching where caching was warranted, not about caching
done badly.

## 12. Trade-off matrix

| Force | No Caching | Cache-Aside | Read-Through | Write-Through |
|---|---|---|---|---|
| Read latency under repeat load | Full cost every time, no improvement with repetition | Fast on hit, full cost on miss, first caller pays the miss | Fast on hit, cache library owns the miss path, transparent to caller | Fast, since writes populate the cache proactively |
| Staleness window | None, always current | Bounded by TTL or explicit invalidation | Bounded by TTL or explicit invalidation | Very small, cache updated in the same transaction as the write |
| Operational surface | Minimal, no cache to run | A cache tier plus invalidation logic in application code | A cache tier plus a caching library or proxy that owns population | A cache tier plus write-path coupling to the cache |
| Cold-start stampede risk | Always present at full strength on any burst | Present on cache miss unless coalesced | Present on cache miss unless coalesced | Not applicable to reads, since the cache is always warm from writes |
| Correctness on write-heavy data | Perfect, since there is nothing to invalidate | Requires careful invalidation on every write path | Requires careful invalidation on every write path | Strong, since every write updates the cache directly |
| Best fit | Cheap computation, strict consistency requirement, very low read-to-write ratio | High read-to-write ratio, tolerant of a short staleness window | Same as Cache-Aside, when a library or proxy can own the pattern | Read-heavy and write-frequent, where staleness must be kept small |

## 13. Related and incompatible patterns

Cache-Aside (Lazy Loading) is the most direct fix for No Caching. the caller
checks the cache first, falls through to the Source of Truth on a miss, and
populates the cache before returning. It is the pattern most often introduced
the first time a team notices this anti-pattern in a profiler.

Read-Through moves the population logic that Cache-Aside puts in the
caller's code into the cache layer itself, so the caller only ever talks to
the cache and the cache owns fetching from the Source of Truth on a miss.
This composes with No Caching's fix the same way Cache-Aside does, differing
only in where the miss-handling responsibility lives.

Write-Through and Write-Behind address the write side of caching and are
complementary rather than alternative fixes to No Caching, since No Caching
as defined here is specifically about redundant reads or recomputation, not
about how writes propagate to a cache.

N+1 Query is a narrower, related anti-pattern. it names the specific case
where a single logical operation issues N separate queries where one batched
query would suffice. No Caching is broader and applies across separate
top-level requests over time, not only within one operation, though the two
frequently occur together in the same codebase and are worth fixing
together.

Chatty I/O names the general problem of making many small round trips where
fewer, larger ones would do. No Caching is one specific mechanism by which
Chatty I/O shows up, when the "many round trips" are all fetching or
recomputing the identical thing.

Busy Database is a frequent downstream consequence of No Caching at scale.
a database that has become a system's bottleneck, receiving load it should
never have seen, is very often a database sitting directly behind an
uncached read path.

There is no genuine incompatibility to list, since No Caching is an absence
rather than a competing design choice, and it composes trivially with every
other pattern in this catalog by simply not being present.

## 14. Refactoring path in and out

Refactoring out of No Caching, meaning introducing a cache where one is
missing, follows a repeatable sequence.

Identify the hot path with a profiler or with request tracing, rather than
guessing. this entry's failure modes in dimension 11 describe the concrete
symptoms to look for. Confirm the read-to-write ratio for the specific value
in question, since caching a value that changes as often as it is read gains
little. Choose the caching pattern that fits the access pattern, most often
Cache-Aside for a first pass, since it requires no new infrastructure beyond
a key-value store and is the easiest to reason about and roll back. Choose a
TTL, or an explicit invalidation trigger, bounded by how stale the business
can genuinely tolerate the value being, and write that bound down somewhere
a future reader will find it. Add a single-flight or request-coalescing
guard if the value is expensive enough, and the concurrency high enough, for
a cold-start stampede to be a real risk. Instrument the cache with hit and
miss counters from the first deploy, per dimension 16, so the fix's actual
effect is measured rather than assumed. Roll out behind a flag or to a
percentage of traffic first, since a caching bug that serves stale or wrong
data can be far more damaging in the short term than the slowness it
replaces.

Refactoring into No Caching, meaning deliberately removing a cache that no
longer earns its place, is the less common but still real direction. This
applies when a cache's hit rate has fallen so low, because the underlying
access pattern changed, that the cache's storage and invalidation-bug
surface cost more than the compute it saves, or when a correctness
requirement has tightened to the point where any staleness window is
unacceptable and no bounded TTL satisfies it. The path here is to confirm
the low hit rate or the tightened correctness requirement with real
measurement first, per dimension 16, then remove the cache and its
invalidation logic in one change, and re-measure the downstream load impact
immediately afterward to confirm the underlying Computation or Source of
Truth can genuinely absorb the returned traffic.

## 15. Testing and verification

Testing that a path has no cache is trivially easy, since the absence
requires no test at all, which is itself part of why the anti-pattern is
common. nothing fails a test suite when caching is simply missing.

The useful testing effort goes the other direction, verifying that a
suspected uncached hot path really is redundant work, and later verifying
that the fix actually reduced it. A load or benchmark test that issues the
same logical request N times in a short window, and asserts that the
downstream dependency, a mocked database, a mocked HTTP client, was invoked
fewer than N times after a cache is introduced, directly proves the fix
works. Before the fix, that same test, asserting invocation count equals N,
documents the anti-pattern's presence as a regression test that will fail
the moment someone reintroduces the redundant call later.

Contract or characterization tests around the Computation or Fetch itself
are worth writing before introducing a cache, since a cache can otherwise
mask a subtly broken underlying computation by serving its first, possibly
wrong, result repeatedly rather than letting the error surface on every
call.

Concurrency tests specifically targeting the thundering-herd scenario from
dimension 7, many simultaneous identical requests against a cold cache or a
still-uncached path, are the right way to verify a single-flight or
request-coalescing guard actually collapses concurrent duplicate work into
one execution, rather than merely reducing but not eliminating it.

## 16. Observability signals

The single most direct signal that No Caching is present and costly is a
profiler or distributed trace showing the same query, the same external
call, or the same computation, with identical arguments, appearing
repeatedly across distinct top-level requests within a short time window.

Database-side signals include a specific query pattern accounting for an
out-of-proportion share of total query volume or total query time, visible
in a slow-query log or a query-performance dashboard, where the query's
arguments recur far more often than the underlying rows change.

Application-side signals include latency histograms where a specific
handler's p50 and p99 track closely together and both track the cost of an
identifiable downstream call, rather than the p50 being fast, served from
somewhere cheap, and only the p99 reflecting the expensive path, which is
the shape a working cache produces instead.

Once a cache is introduced as the fix, the signal that proves it is
functioning, rather than merely present, is a hit-rate metric, hits divided
by hits plus misses, tracked over time, alongside downstream call volume to
the Source of Truth, which should drop in proportion to the hit rate. A
cache with a near-zero hit rate is not solving No Caching, it is adding
overhead on top of it, and this is only visible if hit rate is instrumented
and watched from day one, not added later once someone happens to wonder
why the fix did not help.

Cost dashboards, specifically metered database read-capacity consumption,
third-party API call counts, and cloud compute-minute billing broken down
by endpoint or handler, are a slower but very reliable secondary signal,
since No Caching's cost impact is frequently visible in a monthly bill
before it is visible in a latency graph.

## 17. Security and privacy implications

No Caching itself, being an absence, introduces no new attack surface, and
in one narrow respect is the more conservative choice. there is no cached
copy of sensitive data sitting in a secondary store with its own access
control, retention, and encryption-at-rest posture to get right.

The implication runs the other way once a fix is introduced, which is worth
naming here since it is the practical next step a reader takes after
reading this entry. Adding a cache to fix No Caching creates a new place
where data, potentially including personally identifiable or otherwise
sensitive data, is stored, which inherits its own security and privacy
obligations independent of the Source of Truth's controls. access controls
on the cache tier must match or exceed those on the Source of Truth, since a
cache is a copy of the data, not a lesser-privileged view of it, unless it
is deliberately built to be one. Sensitive values cached with a TTL that is
too long can outlive a legitimate reason to retain them, or outlive a user's
deletion or consent-withdrawal request against the Source of Truth, creating
a data-residue problem the Source of Truth's own deletion logic does not
reach. HTTP-level caching specifically carries a documented, well-known risk
of a shared or intermediary cache, a CDN, a corporate proxy, inadvertently
storing a response intended only for one authenticated user and later
serving it to a different user, which is exactly why MDN's caching
documentation distinguishes a private cache, "tied to a specific client" such as a browser cache, from a shared cache, and why responses containing
per-user data should be marked `Cache-Control: private` or `no-store`
(Mozilla Developer Network, "HTTP caching",
https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching, verified
2026-08-02).

No Caching, by contrast, is silent on all of the above, not because it
solves these problems well, but because there is no cache present for them
to apply to.

## 18. References

1. Django Software Foundation. "Django's cache framework." Django
   documentation, version 5.2.
   https://docs.djangoproject.com/en/5.2/topics/cache/. Verified 2026-08-02.
2. Amazon Web Services. "Caching Overview. Best Practices."
   https://aws.amazon.com/caching/best-practices/. Verified 2026-08-02.
3. Mozilla Developer Network. "HTTP caching."
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching.
   Verified 2026-08-02.
4. Spring Framework Reference Documentation. "Cache Abstraction," Integration
   section. https://docs.spring.io/spring-framework/reference/integration/cache.html.
   Verified 2026-08-02.

## Code examples

Three languages follow. each shows the anti-pattern first (a handler that
recomputes an expensive aggregate on every call) and then the minimal fix
(a bounded, TTL-aware cache-aside wrapper). All three were compiled or run
directly against the toolchain on the authoring machine.

### TypeScript

```typescript
// no-caching.ts. the anti-pattern: every call redoes the expensive work.
function expensiveAggregate(rows: number[]): number {
  let total = 0;
  for (const r of rows) total += r * r;
  return total;
}

function handlerNoCaching(rows: number[]): number {
  return expensiveAggregate(rows);
}

// cache-aside.ts. the fix: reuse the result while it is still valid.
type CacheEntry<T> = { value: T; expiresAt: number };

class TtlCache<K, V> {
  private store = new Map<K, CacheEntry<V>>();
  constructor(private ttlMs: number) {}

  getOrCompute(key: K, compute: () => V): V {
    const now = Date.now();
    const hit = this.store.get(key);
    if (hit && hit.expiresAt > now) return hit.value;
    const value = compute();
    this.store.set(key, { value, expiresAt: now + this.ttlMs });
    return value;
  }
}

const cache = new TtlCache<string, number>(30_000);

function handlerCached(key: string, rows: number[]): number {
  return cache.getOrCompute(key, () => expensiveAggregate(rows));
}

const rows = [1, 2, 3, 4, 5];
console.log("no caching:", handlerNoCaching(rows));
console.log("cache-aside:", handlerCached("demo", rows));
console.log("cache-aside (second call, served from cache):", handlerCached("demo", rows));
```

### Python

```python
# no_caching.py. the anti-pattern: every call redoes the expensive work.
import time


def expensive_aggregate(rows: list[int]) -> int:
    return sum(r * r for r in rows)


def handler_no_caching(rows: list[int]) -> int:
    return expensive_aggregate(rows)


# cache_aside.py. the fix: reuse the result while it is still valid.
class TtlCache:
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[int, float]] = {}

    def get_or_compute(self, key: str, compute) -> int:
        now = time.monotonic()
        hit = self._store.get(key)
        if hit is not None and hit[1] > now:
            return hit[0]
        value = compute()
        self._store[key] = (value, now + self.ttl_seconds)
        return value


cache = TtlCache(ttl_seconds=30.0)


def handler_cached(key: str, rows: list[int]) -> int:
    return cache.get_or_compute(key, lambda: expensive_aggregate(rows))


if __name__ == "__main__":
    rows = [1, 2, 3, 4, 5]
    print("no caching:", handler_no_caching(rows))
    print("cache-aside:", handler_cached("demo", rows))
    print("cache-aside (second call, served from cache):", handler_cached("demo", rows))
```

### Go

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// no_caching.go. the anti-pattern: every call redoes the expensive work.
func expensiveAggregate(rows []int) int {
	total := 0
	for _, r := range rows {
		total += r * r
	}
	return total
}

func handlerNoCaching(rows []int) int {
	return expensiveAggregate(rows)
}

// cache_aside.go. the fix: reuse the result while it is still valid.
type entry struct {
	value     int
	expiresAt time.Time
}

type TtlCache struct {
	mu    sync.Mutex
	ttl   time.Duration
	store map[string]entry
}

func NewTtlCache(ttl time.Duration) *TtlCache {
	return &TtlCache{ttl: ttl, store: make(map[string]entry)}
}

func (c *TtlCache) GetOrCompute(key string, compute func() int) int {
	c.mu.Lock()
	defer c.mu.Unlock()
	now := time.Now()
	if hit, ok := c.store[key]; ok && hit.expiresAt.After(now) {
		return hit.value
	}
	value := compute()
	c.store[key] = entry{value: value, expiresAt: now.Add(c.ttl)}
	return value
}

func handlerCached(cache *TtlCache, key string, rows []int) int {
	return cache.GetOrCompute(key, func() int { return expensiveAggregate(rows) })
}

func main() {
	rows := []int{1, 2, 3, 4, 5}
	fmt.Println("no caching:", handlerNoCaching(rows))

	cache := NewTtlCache(30 * time.Second)
	fmt.Println("cache-aside:", handlerCached(cache, "demo", rows))
	fmt.Println("cache-aside (second call, served from cache):", handlerCached(cache, "demo", rows))
}
```

C#, Swift, and Kotlin are omitted here. the pattern translates directly
(a dictionary or map keyed cache with an expiry check), and the three
languages above already demonstrate the idiomatic shape across a
garbage-collected dynamic language, a garbage-collected static language, and
a compiled language with explicit concurrency control.
