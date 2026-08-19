---
name: Bloom Filter
slug: bloom-filter
family: 12-data-storage
category: Data and Storage
aliases: [Bloom Membership Filter, Probabilistic Set Membership Filter]
first_described: "Bloom 1970"
maturity: canonical
related: [lsm-tree, consistent-hashing, quorum, sharding, cache-aside]
incompatible_with: []
verified: 2026-08-02
---

# Bloom Filter

## 1. Name, aliases, and lineage

The canonical name is Bloom Filter, after Burton Howard Bloom, who described the
technique in "Space/Time Trade-offs in Hash Coding with Allowable Errors,"
Communications of the ACM, volume 13, issue 7, July 1970, pages 422 to 426
([Redis academic sources page](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/),
verified 2026-08-02, which links the original Bloom 1970 paper and the later
scalable-filter extension). Bloom worked at the time on hyphenation dictionary
lookups, where checking every word against a full dictionary on disk was slow,
and he wanted a cheap way to answer, before paying for the expensive lookup,
whether a word was almost certainly absent.

No alternate name is in wide circulation for the base structure itself, though
several derivative structures carry their own names and are frequently confused
with the base filter in casual conversation. A **counting Bloom filter**
replaces each single bit with a small counter so that deletion becomes possible,
a variant introduced by Li Fan, Pei Cao, Jussara Almeida, and Andrei Z. Broder in
"Summary Cache. A Scalable Wide-Area Web Cache Sharing Protocol," published at
ACM SIGCOMM 1998 and later in IEEE/ACM Transactions on Networking, volume 8,
number 3, June 2000, pages 281 to 293
([search results summarizing the paper's authorship and venue](https://www.cs.utexas.edu/~lam/396m/papers/SummaryCache.pdf),
verified 2026-08-02). A **scalable Bloom filter**, described by Almeida, Baquero,
Preguica, and Hutchison, chains progressively larger sub-filters so the
structure can grow without knowing the final item count in advance ([the
Scalable Bloom Filters paper linked from the Redis academic sources
page](https://gsd.di.uminho.pt/members/cbm/ps/dbloom.pdf), verified 2026-08-02).
A **cuckoo filter**, published by Bin Fan, David G. Andersen, Michael Kaminsky,
and Michael D. Mitzenmacher at ACM CoNEXT 2014 under the title "Cuckoo Filter.
Practically Better Than Bloom," is not a variant of the Bloom filter at all but
a competing structure built on cuckoo hashing that adds deletion and often uses
less space at moderate false positive rates
([Wikipedia's Cuckoo filter article](https://en.wikipedia.org/wiki/Cuckoo_filter),
verified 2026-08-02). This entry treats the classic, non-counting Bloom filter as
the primary subject and covers the counting and scalable variants as named
implementation variants in dimension 8, because conflating any of these three
under one label is the single most common source of confusion when engineers
discuss "using a Bloom filter" in a design review.

## 2. Problem and context

A system needs to answer one question over and over, at high volume, with low
latency. Does this key already exist. The honest answer requires consulting the
authoritative store, and that store is usually slow relative to the rate of the
question. It might be a value sitting on a spinning or solid state disk behind a
seek, a row inside a compacted, multi-file log-structured storage engine, a
remote service across a network hop, or a large hash set that does not fit in
the CPU cache. Most of the time the answer to the question is no, the key is
absent, and paying the full cost of the authoritative lookup only to learn "not
found" is waste repeated at scale.

The context in which this problem becomes acute is any system where negative
lookups vastly outnumber positive ones, and where a negative answer needs to be
fast because a positive answer is already expensive by nature. A log-structured
merge tree storage engine such as the one described in `patterns/12-data-storage/lsm-tree.md`
may hold a key across many on-disk files, and probing every file for a key that
was never written anywhere is pure waste on every read. A web crawler tracking
which URLs it has already visited faces billions of candidate URLs where the
overwhelming majority, on a re-crawl of a live web, have already been seen
before, and re-fetching the visited set from a database on every candidate URL
would dominate the crawl's total cost. A password breach checking service needs
to answer whether a submitted password appears in a corpus of hundreds of
millions of known-compromised passwords, without exposing the corpus itself to
every caller, and without paying a full-text search cost per submission. A
username registration form needs to reject an already-taken name in
milliseconds, at signup volume, without hitting the primary user table for
every keystroke of a live-typing availability check.

The structural feature these situations share is asymmetry. A false "maybe
present" costs one extra confirming lookup against the authoritative source, a
tolerable cost paid rarely if the filter is tuned well, while a false "not
present at all" for a key that truly is present would be a correctness bug, an
unacceptable outcome for a filter used as a fast-path gate before a
confirmation step. Any structure proposed for this context must, therefore,
never produce a false negative, and may trade some false positive rate for
enormous savings in memory relative to storing the full set of keys.

## 3. Forces

**Memory versus accuracy.** A Bloom filter's whole reason for existing is that
it trades exactness for space. Storing a hash set of a million 40-byte keys
outright, with typical per-entry overhead in a general-purpose hash set,
consumes tens of megabytes. A Bloom filter tuned for one percent false
positives over the same million keys needs roughly 9.6 bits per item, under 1.2
megabytes, an order of magnitude reduction (figures derived from the standard
formula, cross-checked against RocksDB's documented default of about 10 bits
per key for a roughly one percent rate, see
[the RocksDB Bloom Filter wiki page](https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter),
verified 2026-08-02). Tightening the false positive target buys accuracy at a
cost that grows logarithmically, not linearly, in the target rate, which is a
favorable trade until the target rate becomes extremely small and the per-item
bit cost starts approaching the cost of storing something closer to the full
key.

**Read latency versus write cost.** Every insertion touches k independent bit
positions, and every membership query touches the same k positions. Both
operations are constant time in the number of items already stored, which is
the property that makes the structure attractive for hot paths, but the
constant itself, the number of hash functions k, is a tuning knob that trades
insertion and query cost against accuracy. More hash functions lower the false
positive rate up to a point, then start raising it again as the bit array
saturates faster, so the force is not monotonic and must be tuned rather than
maximized.

**Deletability versus space.** The classic filter has no deletion operation at
all, because clearing a bit that a departing key set might share with a
surviving key would silently corrupt the surviving key's membership signal.
Systems that need deletion pay for it, typically by replacing single bits with
small counters, at three to four times the base memory
([Wikipedia's Bloom filter article, counting filter section](https://en.wikipedia.org/wiki/Bloom_filter),
verified 2026-08-02), or by switching data structures entirely to a cuckoo
filter, which supports deletion natively at a different space and latency
profile. A team choosing this structure has to decide, before deployment,
whether the set of keys it filters will ever need item-level removal, because
retrofitting deletion after the fact means a new data structure and a rebuild,
not a configuration change.

**Coupling to the authoritative source.** A Bloom filter is never a replacement
for the source of truth. It is a probabilistic gate placed in front of one. This
creates an operational coupling. The filter must be built from, and kept
consistent with, the same set of keys the authoritative store actually holds,
or its guarantee (no false negatives) silently breaks. A filter built from a
stale snapshot, or built before a batch of new keys finished writing to the
store behind it, will wrongly say "definitely not present" for a key the store
now genuinely has, which is worse than having no filter at all, because callers
trust the negative answer and skip the confirming lookup entirely.

**Cost versus team topology.** A Bloom filter is a small piece of code with a
sharp edge, tuning the size and hash count wrong is easy and the failure mode is
silent degradation rather than a crash. Teams that adopt a battle-tested
implementation, RedisBloom, Guava's `BloomFilter`, or RocksDB's built-in filter
policy, absorb almost none of this operability risk, because sizing, hashing,
and serialization are handled by a library maintained by people who specialize
in it. Teams that hand-roll one, usually because the language or runtime has no
mature library, take on the full tuning and testing burden themselves, and this
is a real cost that should weigh into the decision to build one from scratch
against reaching for an existing one.

## 4. Applicability and non-applicability

Reach for a Bloom filter when all of the following hold together. The set of
keys being tested is large enough that storing it outright is expensive, the
overwhelming majority of membership queries are expected to return "not
present," a false positive is affordable, because it only triggers one extra
confirming lookup against an authoritative source that is always consulted
after a positive filter result, a false negative is never affordable, because
callers act on a negative answer without further checking, and the set changes
slowly enough, or is rebuilt periodically enough, that keeping the filter
synchronized with the authoritative source is a solved problem in the design
rather than an afterthought.

Concrete applicability. Gating expensive disk reads in a log-structured storage
engine before checking each on-disk file, per-table filters in Cassandra and
per-block filters in RocksDB being the production examples in dimension 9,
gating a network round trip to a remote cache or a downstream service when the
local process can cheaply rule out most requests before making the call,
de-duplicating a high-volume event stream where re-processing an already-seen
event id is wasteful but not catastrophic, because the downstream consumer is
already idempotent, content recommendation systems that need to avoid
re-showing an item a user has already seen, at scale, without storing the full
per-user history in a fast-access tier, and connection-level filtering in
lightweight blockchain clients, historically used by SPV Bitcoin wallets to ask
full nodes for only the transactions relevant to a wallet's addresses, defined
in Bitcoin Improvement Proposal 37
([BIP 37 on GitHub](https://github.com/bitcoin/bips/blob/master/bip-0037.mediawiki),
verified 2026-08-02).

Non-applicability, the list most catalogs skip.

- **Do not use it when a false positive is unacceptable and there is no
  confirming step behind the filter.** If the caller trusts the positive answer
  outright, for example a security allowlist that grants access on a positive
  match with no secondary check, the filter's error rate becomes a direct
  security defect rather than a tolerable performance cost.
- **Do not use it when items must be removed from the set later**, unless the
  variant chosen explicitly supports deletion (counting filter, cuckoo filter),
  because clearing a bit in a classic filter to "remove" one key can silently
  produce false negatives for other keys that happen to share that bit.
- **Do not use it when the set is small enough that a plain hash set already
  fits comfortably in memory or in cache.** For a few thousand items, the space
  savings of a Bloom filter do not outweigh the added complexity, the extra
  hash computations, and the loss of exact membership semantics. A hash set is
  simpler to reason about and just as fast at that scale.
- **Do not use it when the application needs to enumerate the set's members.**
  A Bloom filter answers "is this specific key in the set," never "what are the
  members of the set." There is no traversal operation, by design, because the
  structure discards per-key identity entirely in favor of a shared bit array.
- **Do not use it as the sole authority for anything, ever.** Every legitimate
  production use in dimension 9 places the filter strictly in front of an
  authoritative source, never in place of one. A team reaching for a Bloom
  filter because it wants to avoid building or operating the authoritative
  store has misunderstood the pattern.
- **Do not use it when the false positive rate needed is extremely low, below
  roughly one in a million, without checking the memory math first.** The bits
  per item required grows with the negative log of the target rate, and at very
  low target rates the per-item cost can approach or exceed a compact exact
  structure such as a cuckoo filter or a trie, eroding the entire reason for
  choosing a probabilistic structure in the first place.

## 5. Structure

A Bloom filter has three participants.

- **The bit array.** A fixed-size array of m bits, all initialized to zero,
  allocated up front based on the expected number of items and the desired
  false positive rate. It carries no per-item metadata, no key material, and no
  way to recover which items set which bits, which is the source of both the
  structure's space efficiency and its inability to support deletion or
  enumeration.
- **The hash function family.** A set of k independent, uniformly distributed
  hash functions, h_1 through h_k, each mapping an arbitrary input to an index
  in the range zero to m minus one. In practice almost no production
  implementation computes k genuinely independent hash functions. Instead it
  derives k index values from two base hash computations using a technique
  called double hashing, covered in dimension 8, because computing k truly
  independent hash functions per operation would itself be the dominant cost.
- **The tuning parameters n, m, k, and p.** n is the expected number of items
  the filter will hold, p is the target false positive probability chosen by
  the operator, and m and k are derived from n and p using closed-form
  formulas, m equal to the ceiling of negative n times the natural log of p,
  divided by the natural log of two squared, and k equal to the rounded value
  of m over n times the natural log of two ([both formulas confirmed on the
  Redis Bloom filter documentation page, "Total size of a Bloom filter"
  section](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/),
  verified 2026-08-02, and independently on the RocksDB Bloom filter wiki page,
  verified 2026-08-02).

There is no separate "insert" participant and "query" participant as distinct
objects. Both operations are methods on the same filter instance, differing
only in whether the k computed bit positions are set to one (insert) or merely
read (query). This symmetry is deliberate. The query path must visit exactly
the bits the insert path would have set, or the guarantee that "if I inserted
it, a query for it always returns true" breaks.

## 6. ASCII structure diagram

```
                     Bloom Filter (m bits, k hash functions)

  key "order-4471"
        |
        v
  +-----------+     +-----------+     +-----------+
  |   h1(x)   |     |   h2(x)   | ... |   hk(x)   |     k independent
  +-----------+     +-----------+     +-----------+     hash functions
        |                 |                 |
        v                 v                 v
  bit array (m bits, all zero at start)

  0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 ... m-1
  [0 0 1 0 0 1 0 0 0 1 0  0  0  1  0 ...  0 ]
        ^     ^           ^
        |     |           |
       h1(x) h2(x)       hk(x)   <-- set to 1 on insert(x)
                                       read on mightContain(x)

  add(x):          for i in 1..k: bits[h_i(x)] = 1
  mightContain(x):  for i in 1..k: if bits[h_i(x)] == 0 return false
                     return true   (may be a false positive)
```

## 7. Dynamics

The runtime behavior splits into two paths, insertion and query, and both
follow the same hash-then-index shape, differing only in the final bit
operation.

On **insertion** of a key, the filter computes the two base hashes described in
dimension 8, derives k index positions from them, and sets each of those k bits
in the array to one, unconditionally, without checking their current value
first. A bit that is already one from an earlier, unrelated insertion stays
one. This is the mechanism by which two different keys can share a bit position
and is the direct source of the false positive rate, with no error, no signal,
and no way for the filter to detect or report the collision at insertion time.

On a **membership query** for a key, the filter recomputes the same k index
positions using the same hash functions, deterministically, so a query for a
key that was genuinely inserted will always compute the exact same positions
that were set to one during that insertion. It then reads each of the k bits.
If any single one of them is zero, the filter returns false immediately, a
guaranteed true negative, because a bit that is zero could not have been set by
this key's own insertion, and the absence of even one of its k bits is
conclusive proof the key was never added. If all k bits are found set to one,
the filter returns true, meaning "probably present," and the query stops there,
having visited at most k bit positions regardless of how many keys the filter
holds.

```
   insert("order-4471")                query("order-4471")
   ---------------------                --------------------
   h1 = hash_a("order-4471")            h1 = hash_a("order-4471")
   h2 = hash_b("order-4471")            h2 = hash_b("order-4471")
   for i in 0..k                        for i in 0..k
     slot = (h1 + i*h2) mod m             slot = (h1 + i*h2) mod m
     bits[slot] = 1                       if bits[slot] == 0
                                             return DEFINITELY_ABSENT
   done, key's k bits now set            return PROBABLY_PRESENT

   query("order-9999"), never inserted
   ------------------------------------
   h1, h2 computed the same way
   slot 1 -> bits[slot] == 1  (collision from another key, unlucky)
   slot 2 -> bits[slot] == 0  <-- stops here
   result: DEFINITELY_ABSENT   (the correct answer, one bit saved it)
```

The second block in the diagram is the case that matters operationally. Even
though the key "order-9999" happens to collide with an earlier insertion on one
of its k positions, a single zero bit among the remaining positions is enough
to produce the correct negative answer. The false positive only occurs in the
rare case where every one of a queried key's k positions happens to have been
set by the collective insertions of other keys, and the probability of that
happening is exactly the false positive formula derived in dimension 3 and
confirmed against the Redis documentation in dimension 5.

## 8. Implementation variants

**Double hashing (Kirsch-Mitzenmacher technique).** Almost every production
implementation, including the reference code in this entry, avoids computing k
genuinely independent hash functions per operation. Instead it computes two
independent base hashes, h1 and h2, typically using two different, fast,
non-cryptographic hash functions such as FNV-1a and a Murmur-family hash, or two
differently seeded invocations of the same hash, and derives the i-th of the k
index positions as h1 plus i times h2, modulo m. This produces statistically
sufficient independence for the false positive analysis to hold in practice
while paying the cost of only two hash computations per operation instead of k.
This is exactly the technique demonstrated in the four reference implementations
below, and it is the technique RedisBloom, Guava, and most other production
libraries use internally, though the specific base hash functions differ by
implementation.

**Counting Bloom filter.** Replace each single bit in the array with a small
fixed-width counter, commonly four bits. Insertion increments the k counters
instead of setting bits, and a deletion operation, absent from the classic
filter, decrements them. A counter reaching its maximum value on overflow must
either saturate, permanently over-reporting membership for that slot, or the
implementation must widen the counter, and this is the primary tuning
sensitivity of the variant. Fan, Cao, Almeida, and Broder introduced this
variant specifically to support removing stale entries from a web cache summary
without rebuilding the whole structure ([the Summary Cache paper's abstract and
introduction](https://www.cs.utexas.edu/~lam/396m/papers/SummaryCache.pdf),
verified 2026-08-02). The cost is three to four times the bit budget of the
classic filter for the same false positive target, because a counter needs
several bits where a plain filter needs one.

**Scalable Bloom filter.** Chain a sequence of sub-filters, each with a tighter
false positive target than the last, starting a new sub-filter once the current
one approaches its designed capacity. A query checks each sub-filter from
newest to oldest until one returns true or all return false, and an insertion
always goes to the newest sub-filter. This solves the problem of not knowing n,
the eventual item count, in advance, at the cost of a query latency that grows
with the number of chained sub-filters rather than staying strictly constant.
RedisBloom implements this directly as its default scaling behavior, controlled
by an `EXPANSION` parameter on `BF.RESERVE`, and documents the same
newest-to-oldest query cost trade-off ([the Redis Bloom filter documentation
page, "Scaling" section](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/),
verified 2026-08-02).

**Block-based and cache-line-aligned filters.** RocksDB's default filter
construction, `NewBloomFilterPolicy` with `use_block_based_builder` set to
false, builds a single "full filter" per SST file rather than one small filter
per data block, which is faster to query and more space-efficient but must be
loaded into memory as one contiguous block ([the RocksDB Bloom Filter wiki
page](https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter), verified
2026-08-02). More advanced implementations, including RocksDB's own Ribbon
Filter successor, align a filter's structure to CPU cache lines so that all of a
single query's bit checks land in one cache line, trading a small amount of
theoretical space efficiency for a much lower constant factor in practice, a
concern that only shows up once a filter is queried at very high throughput.

**Registered-key, whole-key versus prefix filtering.** RocksDB additionally
supports filtering on a key prefix rather than the whole key, controlled by the
`whole_key_filtering` option, useful when queries commonly probe by a shared
prefix (a user id, say) rather than by exact key, letting one filter answer
"does anything with this prefix exist" cheaply ([the same RocksDB Bloom Filter
wiki page](https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter),
verified 2026-08-02). This is not a distinct data structure so much as a
different choice of what string gets hashed, but it changes the applicability
analysis meaningfully for range-query-heavy workloads.

**Cuckoo filter, as the frequently-substituted alternative.** Not a Bloom filter
variant by construction, a cuckoo filter stores short fingerprints of each key
in a cuckoo hash table rather than setting shared bits, which lets it support
deletion natively, at generally lower space overhead than a space-optimized
Bloom filter for false positive rates below about three percent, at the cost of
occasional, bounded relocation work on insertion when the cuckoo hash table
needs to displace an existing entry
([Wikipedia's Cuckoo filter article, properties section](https://en.wikipedia.org/wiki/Cuckoo_filter),
verified 2026-08-02). Teams choosing between the two should treat "do I need
deletion, and how often" as the first and most decisive question, because the
cuckoo filter answers it structurally while the Bloom filter answers it only
through the counting variant's added memory cost.

## 9. Known production uses

**Apache Cassandra** places one Bloom filter per SSTable on disk, consulted
before any read touches that SSTable's index or data files, tunable per table
through the `bloom_filter_fp_chance` setting, with the Cassandra documentation
stating plainly that the filter lets Cassandra determine "the data definitely
does not exist in the given file, or the data probably exists in the given
file," and recommending typical values between 0.01 and 0.1
([the Apache Cassandra documentation, "Bloom Filters" page](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/bloom_filters.html),
verified 2026-08-02).

**RocksDB**, the embedded storage engine underlying MyRocks, TiKV, and
CockroachDB's earlier storage layer among others, builds a Bloom filter for
every SST file by default when `filter_policy` is configured, using
`NewBloomFilterPolicy(bits_per_key)` with a documented default of about ten bits
per key yielding roughly a one percent false positive rate
([the RocksDB Bloom Filter wiki page](https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter),
verified 2026-08-02).

**Redis, through the RedisBloom module**, ships Bloom filters as a first-class
data type with commands `BF.RESERVE`, `BF.ADD`, and `BF.EXISTS`, and its
documentation lists concrete production use cases the module was built for,
including fraud detection ("has the user paid from this location before"), ad
de-duplication, and username or slug availability checks at signup, each
described with the specific per-item bit cost trade-off the operator is
choosing ([the Redis Bloom filter documentation
page](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/),
verified 2026-08-02).

**Google Chrome** historically used a Bloom filter, downloaded to the client, to
perform a fast, offline first check of whether a URL a user was about to visit
matched Google's Safe Browsing malicious-site list, escalating to a full,
privacy-preserving online check only on a filter hit, so that the overwhelming
majority of benign URL visits never triggered a network call at all
([Wikipedia's Bloom filter article, applications
section](https://en.wikipedia.org/wiki/Bloom_filter), verified 2026-08-02).

**Bitcoin**, via BIP 37, let lightweight (SPV) wallet clients send a Bloom
filter of their own addresses and transaction identifiers to a full node, which
then used the filter to decide which transactions to forward to that client,
letting the client avoid downloading full blocks while still receiving every
transaction relevant to its own wallet, at the cost of an adjustable and
disclosed false positive rate that the wallet software could tune for its own
bandwidth versus privacy trade-off ([BIP 37's specification
text](https://github.com/bitcoin/bips/blob/master/bip-0037.mediawiki), verified
2026-08-02). Note that this specific application was later shown to leak wallet
address information to a sufficiently motivated observer of the filter's
contents across multiple connections, a privacy failure covered further in
dimension 17.

**Google Guava**, the widely used Java utility library, ships a generic,
type-safe `BloomFilter<T>` class with a documented one-sided error guarantee,
stating "if it claims that an element is contained in it, this might be in
error, but if it claims that an element is not contained in it, then this is
definitely true," alongside a default false positive probability of three
percent when none is specified
([the Guava BloomFilter Javadoc](https://guava.dev/releases/33.5.0-jre/api/docs/com/google/common/hash/BloomFilter.html),
verified 2026-08-02).

**Medium**, the publishing platform, uses a per-user Bloom filter to track which
article ids a reader has already seen, so the recommendation system can cheaply
avoid re-surfacing an already-read article without storing a complete,
per-user, exact reading history in the hot recommendation path ([Wikipedia's
Bloom filter article, applications
section](https://en.wikipedia.org/wiki/Bloom_filter), verified 2026-08-02).

## 10. Consequences

Positive.

- **Space usage is a small, fixed, and predictable function of item count and
  target error rate, independent of key size.** A filter over million-character
  URLs costs exactly the same memory as one over eight-character order ids at
  the same n and p, because the filter never stores the key itself, only its
  hashed positions. This is the property no comparably fast exact structure
  offers.
- **Insertion and query are both constant time in the number of items already
  in the filter**, bounded strictly by k, the fixed hash count, which does not
  grow as the filter fills toward its designed capacity, unlike a chained hash
  table whose bucket lengths grow under load.
- **The filter is trivially mergeable across shards when built with identical
  parameters (same m, same hash functions).** Two filters over disjoint key
  sets can be combined into one filter covering the union of both sets with a
  single bitwise OR across the arrays, an operation several production systems,
  including RedisBloom's replication model, depend on.
- **No false negatives, ever, by construction, for any key genuinely
  inserted.** This is the guarantee every other property in this entry depends
  on, and it holds unconditionally as long as the bit array is never corrupted
  and hash computation is deterministic.

Negative.

- **False positives are unavoidable and grow as the filter approaches its
  designed capacity**, meaning capacity planning is not optional. An operator
  who inserts twice as many items as the filter was sized for gets a
  dramatically worse false positive rate than planned, silently, with no error
  raised at insertion time.
- **The structure cannot answer "what are the members," cannot iterate its own
  contents, and (in the classic, non-counting form) cannot answer "remove this
  member."** Every one of these is a hard architectural constraint, not a
  missing feature that a future version might add without becoming a
  meaningfully different data structure.
- **The filter must be kept synchronized with whatever authoritative source it
  gates**, adding an operational dependency and a class of bugs, a filter built
  before a write completes, or rebuilt from a stale snapshot, that are entirely
  absent in systems that skip the filter and query the source directly.
- **Choosing m and k wrong is a silent failure mode, not a loud one.** An
  undersized filter still returns answers, they are simply wrong more often
  than the operator believes, and this class of bug tends to surface only under
  production load, well after the filter shipped.

## 11. Failure modes and misuse

**Symptom.** Cache hit rate or filter-skip rate degrades gradually over weeks,
with no code change and no obvious external cause.
**Cause.** The filter was sized for an expected item count n that the real data
has since exceeded, often because nobody wired an alert to the actual insertion
count against the designed capacity, so the false positive rate has been
silently climbing along the well-understood degradation curve as the bit array
saturates.
**Fix.** Instrument the filter's current fill ratio (fraction of bits set) or
insertion count directly, alert well before the designed capacity is reached,
and either rebuild at a larger size or switch to a scalable Bloom filter
variant that grows automatically instead of degrading.

**Symptom.** A confirmed, real key is reported as "definitely absent" by the
filter, and a caller that trusted the negative answer skips it entirely,
producing an outright correctness bug rather than a performance regression.
**Cause.** This should be structurally impossible for a correctly operated
Bloom filter, so its presence almost always means the filter and the
authoritative store have drifted out of sync, the filter was built from an
older snapshot than the store currently reflects, or a deployment race let
reads against the new filter begin before the corresponding writes to it
finished.
**Fix.** Treat filter construction and the underlying write path as one atomic
unit from the caller's perspective, insert into the filter synchronously as
part of the same write transaction or write-ahead log entry that persists the
key, and add a regression test that specifically inserts a key and immediately
queries for it before any other operation, on every deploy.

**Symptom.** The filter appears to work correctly in unit tests with dozens of
keys, but production false positive rates run far above the configured target
the moment real traffic arrives.
**Cause.** The two base hash functions used to derive the k index positions are
not sufficiently independent for the key distribution actually seen in
production, most commonly because a hand-rolled hash function was used that
correlates on the specific structure of the real keys, for example numeric ids
that increment sequentially hashed with a weak function that maps nearby inputs
to nearby outputs.
**Fix.** Replace hand-rolled hash functions with well-studied, well-distributed
non-cryptographic hashes (FNV-1a, MurmurHash3, xxHash), and add a distribution
test that inserts a realistic sample of production-shaped keys and measures the
actual false positive rate empirically against the theoretically predicted one,
failing the build if the two diverge past a set tolerance.

**Symptom.** A team building an SPV-style lightweight client using Bloom filter
address filtering, following the BIP 37 pattern, later discovers that an
observer connected to multiple full nodes can reconstruct which addresses
belong to a given wallet by comparing the filters that wallet sent to each
node.
**Cause.** A Bloom filter's false positive rate provides only statistical
obfuscation, not cryptographic privacy, and an adversary who can observe the
same client's filter across several connections, or who can query the filter
against a large, known candidate address space, can narrow down set membership
with enough confidence to de-anonymize the underlying set, a weakness in this
specific application that was analyzed publicly and contributed to newer
lightweight client protocols moving away from BIP 37-style filtering.
**Fix.** Never use a Bloom filter as the sole privacy mechanism for sensitive
set membership disclosed to an untrusted party. Treat its false positive rate
as a bandwidth-versus-accuracy tuning knob only, and reach for a purpose-built
privacy technique, such as private set intersection or a trusted intermediary,
when the set membership itself must stay confidential from the party receiving
the filter.

**Symptom.** Query latency for the filter grows noticeably as the number of
items stored grows, which the team assumed could never happen because Bloom
filter lookups are supposed to be constant time.
**Cause.** In almost every real occurrence of this symptom, the actual data
structure in use is a scalable Bloom filter chaining several sub-filters, and
the growth in latency tracks the growing number of chained sub-filters a query
must check from newest to oldest, not the classic filter's genuinely constant
per-lookup cost, a distinction the team had not made when they adopted the
"scalable" variant for its convenience without reading its documented query
cost trade-off.
**Fix.** Read the documentation for the specific variant in use before
attributing a performance characteristic to "Bloom filters" generically, and if
sub-filter chain length has grown past a small, bounded number, either
pre-size the initial filter closer to the true expected item count to avoid
chaining altogether, or periodically compact the chain into a single new filter
sized for the current total count.

## 12. Trade-off matrix

| Force | Bloom Filter | Cuckoo Filter | Plain Hash Set | Quorum-Read Confirmation |
|---|---|---|---|---|
| Space per item at 1% false positive rate | Roughly 9.6 bits, key-size independent (see dimension 3) | Somewhat lower at low target rates, still key-size independent | Full key plus overhead, typically far larger | No filter at all, zero extra space, full cost paid every read |
| Supports deletion | No, in the classic form. Yes only in the counting variant at 3-4x cost | Yes, natively | Yes, natively | Not applicable, no membership structure exists |
| Query latency at scale | Constant, bounded by k | Constant, bounded by at most 2 bucket probes | Constant on average, degrades under hash collisions or resizing | The full authoritative round trip, every time |
| False negatives | Never, by construction | Never, by construction | Never | Never, it is the authoritative source itself |
| False positives | Yes, tunable, unavoidable | Yes, tunable, unavoidable | No, exact | No, exact |
| Best fit from dimension 4 | High-volume negative-lookup gating in front of an expensive source | Same use case, when deletion is a hard requirement | Small sets, or when exact membership must be queryable | When there is no expensive source to gate at all, or correctness admits no probabilistic layer |

## 13. Related and incompatible patterns

**LSM Tree** (`patterns/12-data-storage/lsm-tree.md`) is the pattern this entry's
motivating example belongs to most directly. An LSM tree accumulates data across
many immutable, sorted on-disk files, and a read for a key that does not exist
anywhere would otherwise have to probe every one of those files. A Bloom filter
per file lets the storage engine skip files it can prove do not contain the key,
which is precisely why Cassandra and RocksDB, both LSM-based engines, ship this
pattern as a core, load-bearing component rather than an optional add-on.

**Consistent Hashing** (`patterns/12-data-storage/consistent-hashing.md`)
composes with Bloom filters in sharded systems where each shard maintains its
own filter over the keys it owns, and a router first hashes a request to a
shard via consistent hashing, then consults that shard's local filter before
issuing the actual read, layering two independent hashing schemes for two
independent purposes, routing and membership, that should not be confused with
each other despite both relying on hash functions.

**Sharding** (`patterns/08-cloud-distributed/sharding.md`) relates the same way.
In a sharded key-value store, a client that does not yet know which shard owns
a key can sometimes broadcast a lightweight Bloom filter query to every shard in
parallel far more cheaply than issuing a full read to every shard, cutting the
fan-out cost of a scatter-gather lookup for keys that turn out to exist on only
one or a few shards.

**Cache-Aside** (`patterns/08-cloud-distributed/cache-aside.md`) is a common
neighbor. A Bloom filter placed in front of a cache-aside read path protects
against cache stampede on keys that are guaranteed absent from the backing
store entirely, a classic cache-penetration attack pattern where an attacker
requests known-nonexistent keys specifically to force expensive backing-store
misses on every request, because the filter can rule those requests out before
they ever reach the cache-aside logic at all.

**Quorum** (`patterns/12-data-storage/quorum.md`) is related only loosely. Both
patterns tune an accuracy-versus-cost knob, quorum size, or filter false
positive rate, against a workload's read and write pattern, but they solve
different problems and are not substitutable for one another. A quorum read
answers "what is the current, consistent value," a Bloom filter answers only
"could this key possibly exist at all."

No pattern in this catalog is flatly incompatible with the Bloom filter in the
sense of the two never being safely combined. The closest thing to an
incompatibility is architectural misuse. Placing a Bloom filter as the sole
authority in a system that also claims strong consistency guarantees is a
direct contradiction, because the filter's tunable false positive rate is
itself an admission of approximate, not strong, correctness for positive
answers.

## 14. Refactoring path in and out

**Introducing a Bloom filter into an existing system.** Start by measuring the
actual read pattern of the expensive lookup being targeted, specifically the
ratio of queries that return "not found" against those that return a genuine
hit, because the entire benefit case for a Bloom filter depends on that ratio
being high. A system where most lookups are genuine hits gains little from
adding one. Next, choose the target false positive rate p and confirm the
resulting memory cost, using the formula from dimension 5, is actually smaller
than what would be saved in avoided lookups, since a mis-tuned filter can, in
degenerate cases, cost more in wasted CPU on hash computation than it saves.
Wire filter insertion into the exact same write path that persists the
authoritative key, ideally in the same transaction or the same write-ahead log
append, so the two structures cannot drift apart, per the failure mode analyzed
in dimension 11. Place the filter query strictly as a fast-path gate before the
existing expensive lookup, never replacing it, so a positive filter result
falls through to the unchanged, correct lookup path, and only a negative filter
result short-circuits it. Finally, add the distribution and false-positive-rate
regression tests described in dimension 15 before calling the introduction
complete, because a Bloom filter that silently drifts to a false positive rate
far above its target is worse than useless, it is a performance regression
dressed as an optimization.

**Removing a Bloom filter that has stopped earning its place.** This becomes
worth doing when the ratio of "not found" lookups drops because the workload
shifted, when the authoritative source itself became fast enough that the extra
hop no longer matters, or when the operational cost of keeping the filter
synchronized with the source has produced more incidents than the filter has
ever saved in latency. Removal is close to risk free, structurally, because the
filter is strictly additive, a fast-path gate in front of the real lookup, so
deleting the gate and always falling through to the original lookup path cannot
introduce a correctness regression by construction. The only real risk in
removal is a latency or cost regression on the hot path the filter was
protecting, so measure the expensive lookup's actual cost under real load
before and after removal, and roll the removal out gradually, behind a feature
flag if the lookup sits on a critical path, rather than deleting the filter and
its call site in one uncontrolled step.

## 15. Testing and verification

Testing code that uses a Bloom filter splits cleanly into two layers, and both
matter, testing that the filter's own logic behaves correctly, and testing that
the system correctly treats the filter as a fast-path gate rather than an
authority.

For the filter's own logic, an example-based test asserting "insert x, then
query x, expect true" catches almost nothing interesting, because that
assertion holds trivially for any correct or incorrect implementation with a
deterministic hash. The test that actually exercises the guarantee this
structure exists to provide is a property-based one. Generate a large random
set of keys, insert every one, then assert that every single inserted key
queries true, with zero exceptions, across many randomized runs, because a
single false negative anywhere in that check is a hard bug, never an acceptable
statistical outcome, unlike a false positive. A second property test should
generate a disjoint set of keys, guaranteed never inserted, query each one, and
assert that the empirically measured false positive rate across the whole
disjoint set falls within a defined tolerance band around the theoretically
predicted rate from dimension 5, catching the "hash functions are not
independent enough" failure mode from dimension 11 before it reaches
production.

For the system-level integration, the useful technique is a test double that
wraps the real Bloom filter and asserts an invariant on the calling code rather
than on the filter itself. Force the wrapped filter's `mightContain` to always
return true, effectively disabling the fast-path skip entirely, and confirm the
system under test still produces correct answers, only slower, proving the
filter genuinely sits on the fast path rather than having quietly become part
of the correctness logic somewhere in the codebase. A complementary test forces
`mightContain` to always return false for every key including genuinely present
ones and confirms this produces a clear, loud test failure specifically because
that scenario should be structurally impossible for a correctly synchronized
filter. This is the direct regression test for the "definitely absent for a
real key" failure mode from dimension 11.

What testing becomes easier because of this pattern. Isolating the expensive
lookup's own correctness tests from concerns about scale, because the filter
sits entirely outside that lookup's logic. What becomes harder. Reasoning about
end-to-end latency in a test environment with a tiny key set, because a filter
sized and tuned for a million items behaves very differently, and can hide bugs
differently, than the same filter code path exercised against a hundred test
keys, so load-representative testing at something close to production scale
should be part of the pre-launch checklist rather than an afterthought.

## 16. Observability signals

A healthy Bloom filter, visible on a dashboard, shows a stable, low, and
roughly flat false positive rate over time, tracked either by directly counting
"filter said maybe, authoritative lookup said no" events, the most accurate
signal, or by comparing the filter's current fill ratio, the fraction of set
bits, against its designed capacity, a cheaper proxy signal that correlates
strongly with the true false positive rate as derived in dimension 3. A filter
operating within its designed parameters should show this false positive rate
sitting close to the target p chosen at construction time, with normal
statistical variance, never a sustained upward trend.

A failing or degraded filter shows one or more of these signals climbing away
from baseline. The empirically measured false positive rate rising steadily
above the target p, almost always meaning the filter's real item count has
exceeded its designed capacity, the fix from dimension 11's first failure mode.
The ratio of filter-positive-but-authoritative-negative results spiking sharply
and suddenly rather than gradually, which more often points to a hash
distribution problem introduced by a recent code change than to organic growth.
And, most seriously, any occurrence at all of a filter-negative result for a
key later proven to exist in the authoritative source, which should be alerted
on as a page-worthy correctness incident rather than logged as a routine
metric, because it can only mean the filter and the source have drifted out of
sync.

Specific metrics worth exporting from any production Bloom filter. Current item
count against designed capacity, expressed as a percentage. The empirically
measured false positive rate over a rolling window, alongside the theoretically
configured target for direct comparison on the same chart. Total insertions per
second and total queries per second, since a sudden change in the insert-to-
query ratio is often the earliest sign of a workload shift that will eventually
demand re-tuning. And, for scalable Bloom filter deployments specifically, the
current number of chained sub-filters, since query latency is a direct function
of that count as covered in dimension 11's final failure mode.

## 17. Security and privacy implications

The security surface a Bloom filter opens is narrow but real, and the single
most documented instance is the BIP 37 wallet address filtering weakness
covered in dimension 11. Sending a Bloom filter of sensitive set members,
wallet addresses in that case, to an untrusted party leaks statistical
information about set membership, and an adversary who can observe multiple
filters from the same source, or who can test the filter against a large,
enumerable candidate space, can often recover set membership with high
confidence despite the filter's nominal false positive rate. The general
principle this establishes. A Bloom filter's false positive rate is a
performance and space tuning parameter, never a privacy or confidentiality
guarantee, and treating it as the latter is a security defect, not a design
choice with an acceptable trade-off.

Data handling. Because the filter never stores the original key material, only
positions derived from a hash of it, recovering the exact set of inserted keys
from the bit array alone is not directly possible, which gives the structure a
mild, incidental privacy property for the data at rest inside the filter
itself. This incidental property should never be relied upon as an intentional
privacy control, because membership testing against a known or guessable
candidate key space, exactly the BIP 37 scenario, defeats it entirely for
anyone who can query the filter, as opposed to anyone who merely obtains a copy
of its raw bits.

Where a system uses a Bloom filter to gate access decisions rather than merely
skip expensive lookups, for example an allowlist check performed with no
confirming step behind it, the filter's false positive rate becomes directly
security relevant, because it means some fraction of disallowed requests will
be incorrectly treated as allowed. This use case sits squarely in the
non-applicability list from dimension 4, and any system found using a Bloom
filter this way should be treated as carrying a real defect, not an
optimization opportunity, until a confirming authoritative check is added
behind it.

Where the entry is silent, stated plainly. The classic Bloom filter has no
built-in resistance to a denial-of-service style attack that deliberately
inserts, or, against a filter accepting untrusted input for construction,
crafts, a specific set of keys chosen to collide heavily and drive the false
positive rate up for a targeted victim key, though this concern applies
specifically to filters built partly or wholly from untrusted, adversarially
chosen input, a scenario outside the scope of the internal, backend-only
production uses catalogued in dimension 9, and this entry makes no claim about
mitigations for that adversarial-input scenario beyond noting that a
cryptographically keyed hash function, rather than a fast non-cryptographic
one, is the standard mitigation direction when untrusted input construction is
a genuine threat model.

## Code examples

The four implementations below share one design, computing two independent
base hashes per key and deriving k index positions from them using the
double-hashing technique from dimension 8, rather than computing k separate
hash functions directly. Every sample was compiled or run against the toolchain
listed at the end of this entry, and every sample was verified to correctly
report a genuinely inserted key as present and a genuinely absent key as
absent on the exact test data shown.

### TypeScript

```typescript
class BloomFilter {
  private readonly bits: Uint8Array;
  private readonly numBits: number;
  private readonly numHashes: number;

  constructor(expectedItems: number, falsePositiveRate: number) {
    this.numBits = Math.ceil(
      (-expectedItems * Math.log(falsePositiveRate)) / Math.log(2) ** 2
    );
    this.numHashes = Math.max(
      1,
      Math.round((this.numBits / expectedItems) * Math.log(2))
    );
    this.bits = new Uint8Array(Math.ceil(this.numBits / 8));
  }

  private fnv1a(value: string, seed: number): number {
    let hash = 0x811c9dc5 ^ seed;
    for (let i = 0; i < value.length; i++) {
      hash ^= value.charCodeAt(i);
      hash = Math.imul(hash, 0x01000193);
    }
    return hash >>> 0;
  }

  private slots(value: string): number[] {
    const h1 = this.fnv1a(value, 0);
    const h2 = this.fnv1a(value, 0x9e3779b9) || 1;
    const out: number[] = [];
    for (let i = 0; i < this.numHashes; i++) {
      out.push((h1 + i * h2) % this.numBits);
    }
    return out;
  }

  add(value: string): void {
    for (const slot of this.slots(value)) {
      this.bits[slot >> 3] |= 1 << (slot & 7);
    }
  }

  mightContain(value: string): boolean {
    return this.slots(value).every(
      (slot) => (this.bits[slot >> 3] & (1 << (slot & 7))) !== 0
    );
  }
}

const filter = new BloomFilter(1000, 0.01);
filter.add("order-4471");
console.log(filter.mightContain("order-4471"));
console.log(filter.mightContain("order-9999"));
```

### Python

```python
import hashlib
import math


class BloomFilter:
    def __init__(self, expected_items: int, false_positive_rate: float) -> None:
        self.num_bits = math.ceil(
            -expected_items * math.log(false_positive_rate) / math.log(2) ** 2
        )
        self.num_hashes = max(
            1, round((self.num_bits / expected_items) * math.log(2))
        )
        self.bits = bytearray((self.num_bits + 7) // 8)

    def _slots(self, value: str) -> list[int]:
        h1 = int.from_bytes(hashlib.sha256(value.encode()).digest()[:8], "big")
        h2 = int.from_bytes(
            hashlib.blake2b(value.encode(), digest_size=8).digest(), "big"
        ) or 1
        return [(h1 + i * h2) % self.num_bits for i in range(self.num_hashes)]

    def add(self, value: str) -> None:
        for slot in self._slots(value):
            self.bits[slot >> 3] |= 1 << (slot & 7)

    def might_contain(self, value: str) -> bool:
        return all(
            self.bits[slot >> 3] & (1 << (slot & 7)) for slot in self._slots(value)
        )


if __name__ == "__main__":
    bloom = BloomFilter(expected_items=1000, false_positive_rate=0.01)
    bloom.add("order-4471")
    print(bloom.might_contain("order-4471"))
    print(bloom.might_contain("order-9999"))
```

### Go

```go
package main

import (
	"fmt"
	"hash/fnv"
	"math"
)

type BloomFilter struct {
	bits      []byte
	numBits   uint32
	numHashes int
}

func NewBloomFilter(expectedItems int, falsePositiveRate float64) *BloomFilter {
	n := float64(expectedItems)
	numBits := uint32(math.Ceil(-n * math.Log(falsePositiveRate) / (math.Ln2 * math.Ln2)))
	numHashes := int(math.Round((float64(numBits) / n) * math.Ln2))
	if numHashes < 1 {
		numHashes = 1
	}
	return &BloomFilter{
		bits:      make([]byte, (numBits+7)/8),
		numBits:   numBits,
		numHashes: numHashes,
	}
}

func (b *BloomFilter) slots(value string) []uint32 {
	h1 := fnv.New32a()
	h1.Write([]byte(value))
	sum1 := h1.Sum32()

	h2 := fnv.New32()
	h2.Write([]byte(value))
	sum2 := h2.Sum32()
	if sum2 == 0 {
		sum2 = 1
	}

	slots := make([]uint32, b.numHashes)
	for i := 0; i < b.numHashes; i++ {
		slots[i] = (sum1 + uint32(i)*sum2) % b.numBits
	}
	return slots
}

func (b *BloomFilter) Add(value string) {
	for _, slot := range b.slots(value) {
		b.bits[slot>>3] |= 1 << (slot & 7)
	}
}

func (b *BloomFilter) MightContain(value string) bool {
	for _, slot := range b.slots(value) {
		if b.bits[slot>>3]&(1<<(slot&7)) == 0 {
			return false
		}
	}
	return true
}

func main() {
	filter := NewBloomFilter(1000, 0.01)
	filter.Add("order-4471")
	fmt.Println(filter.MightContain("order-4471"))
	fmt.Println(filter.MightContain("order-9999"))
}
```

### Rust

```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

struct BloomFilter {
    bits: Vec<u8>,
    num_bits: u64,
    num_hashes: u32,
}

impl BloomFilter {
    fn new(expected_items: u64, false_positive_rate: f64) -> Self {
        let n = expected_items as f64;
        let num_bits = (-n * false_positive_rate.ln() / (2f64.ln().powi(2))).ceil() as u64;
        let num_hashes = ((num_bits as f64 / n) * 2f64.ln()).round().max(1.0) as u32;
        BloomFilter {
            bits: vec![0u8; ((num_bits + 7) / 8) as usize],
            num_bits,
            num_hashes,
        }
    }

    fn hash_pair(value: &str) -> (u64, u64) {
        let mut h1 = DefaultHasher::new();
        value.hash(&mut h1);
        let sum1 = h1.finish();

        let mut h2 = DefaultHasher::new();
        (value, 0x9e3779b9u64).hash(&mut h2);
        let sum2 = h2.finish().max(1);

        (sum1, sum2)
    }

    fn slots(&self, value: &str) -> Vec<u64> {
        let (sum1, sum2) = Self::hash_pair(value);
        (0..self.num_hashes as u64)
            .map(|i| (sum1.wrapping_add(i.wrapping_mul(sum2))) % self.num_bits)
            .collect()
    }

    fn add(&mut self, value: &str) {
        for slot in self.slots(value) {
            self.bits[(slot >> 3) as usize] |= 1 << (slot & 7);
        }
    }

    fn might_contain(&self, value: &str) -> bool {
        self.slots(value)
            .iter()
            .all(|slot| self.bits[(*slot >> 3) as usize] & (1 << (slot & 7)) != 0)
    }
}

fn main() {
    let mut filter = BloomFilter::new(1000, 0.01);
    filter.add("order-4471");
    println!("{}", filter.might_contain("order-4471"));
    println!("{}", filter.might_contain("order-9999"));
}
```

All four samples were compiled or run directly during authoring. TypeScript
passed `tsc --noEmit --strict` against a scratch project with `typescript@5`
and `@types/node@22` installed. Python passed `python3 -m py_compile` and ran
correctly, printing `True` then `False`. Go passed `go vet` and ran correctly
with `go run`, printing `true` then `false`. Rust compiled cleanly with
`rustc --edition 2021` and ran correctly, printing `true` then `false`. Java and
Swift samples were not included in this entry because four languages already
exceed the three-language minimum and the double-hashing technique shown is
identical in shape across every mainstream language, so a fifth or sixth sample
would repeat the same logic without adding a genuinely new implementation
consideration.

## 18. References

1. Burton H. Bloom, "Space/Time Trade-offs in Hash Coding with Allowable
   Errors," Communications of the ACM, volume 13, issue 7, July 1970, pages 422
   to 426, cited via the academic sources section of the Redis Bloom filter
   documentation, https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/,
   verified 2026-08-02.
2. "Bloom filter," Wikipedia, https://en.wikipedia.org/wiki/Bloom_filter,
   verified 2026-08-02.
3. Li Fan, Pei Cao, Jussara Almeida, Andrei Z. Broder, "Summary Cache. A
   Scalable Wide-Area Web Cache Sharing Protocol," IEEE/ACM Transactions on
   Networking, volume 8, number 3, June 2000, pages 281 to 293,
   https://www.cs.utexas.edu/~lam/396m/papers/SummaryCache.pdf, verified
   2026-08-02.
4. "Scalable Bloom Filters," Almeida, Baquero, Preguica, Hutchison, linked from
   the Redis Bloom filter documentation's academic sources section,
   https://gsd.di.uminho.pt/members/cbm/ps/dbloom.pdf, verified 2026-08-02.
5. "Bloom filter," Redis documentation, "Total size of a Bloom filter" and
   "Reserving Bloom filters" sections,
   https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/,
   verified 2026-08-02.
6. "RocksDB Bloom Filter," RocksDB wiki,
   https://github.com/facebook/rocksdb/wiki/RocksDB-Bloom-Filter, verified
   2026-08-02.
7. "Bloom Filters," Apache Cassandra documentation,
   https://cassandra.apache.org/doc/latest/cassandra/managing/operating/bloom_filters.html,
   verified 2026-08-02.
8. "BloomFilter (Guava 33.5.0-jre API)," Guava documentation,
   https://guava.dev/releases/33.5.0-jre/api/docs/com/google/common/hash/BloomFilter.html,
   verified 2026-08-02.
9. Bin Fan, David G. Andersen, Michael Kaminsky, Michael D. Mitzenmacher,
   "Cuckoo Filter. Practically Better Than Bloom," ACM CoNEXT 2014, cited via
   "Cuckoo filter," Wikipedia, https://en.wikipedia.org/wiki/Cuckoo_filter,
   verified 2026-08-02.
10. "BIP 37. Connection Bloom filtering," Bitcoin Improvement Proposals,
    https://github.com/bitcoin/bips/blob/master/bip-0037.mediawiki, verified
    2026-08-02.
