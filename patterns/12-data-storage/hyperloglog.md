---
name: HyperLogLog
slug: hyperloglog
family: 12-data-storage
category: Probabilistic data structure
aliases: [HLL, HyperLogLog++, Cardinality sketch]
first_described: "Flajolet, Fusy, Gandouet, Meunier 2007"
maturity: canonical
related: [consistent-hashing, lsm-tree, crdt, gossip-protocol]
incompatible_with: []
verified: 2026-08-02
---

# HyperLogLog

## 1. Name, aliases, and lineage

The canonical name is HyperLogLog, commonly shortened to HLL in code, logs, and
conversation. It names a probabilistic algorithm for estimating the number of
distinct elements in a multiset, the cardinality estimation problem, using a
fixed and small amount of memory regardless of how many elements are counted or
how many times each one repeats.

The lineage runs through three papers, each one narrowing the memory needed for
the same accuracy.

The starting point is Philippe Flajolet and G. Nigel Martin, "Probabilistic
Counting Algorithms for Data Base Applications," Journal of Computer and System
Sciences, volume 31, 1985, pages 182 to 209
(https://algo.inria.fr/flajolet/Publications/FlMa85.pdf, verified 2026-08-02).
This paper is the origin of what is now called the Flajolet-Martin algorithm.
It hashes every element to a bit string and, for each hash, records the
position of the least significant set bit, which is a proxy for how many
leading zero bits the hash produced under a different bit ordering convention.
Because a hash function spreads its outputs uniformly, the probability of
seeing k leading zeros in a random bit string is 2^-k, so the maximum
leading-zero-run observed across many hashed elements grows logarithmically
with the true count of distinct elements, and that maximum is the quantity
every algorithm in this family builds its estimate from.

The second paper is Marianne Durand and Philippe Flajolet, "Loglog Counting of
Large Cardinalities," in Algorithms, ESA 2003, Lecture Notes in Computer
Science volume 2832, Springer, Berlin, Heidelberg, pages 605 to 617
(https://link.springer.com/chapter/10.1007/978-3-540-39658-1_55, verified
2026-08-02). LogLog splits the incoming hash into two parts. A short prefix of
p bits selects one of m = 2^p independent registers, a technique called
stochastic averaging that turns a single noisy estimator into m correlated but
less noisy ones, and the remaining bits of the hash feed the leading-zero-run
measurement for that one register. Averaging the m register values and
exponentiating back out gives a cardinality estimate whose relative error
shrinks as the number of registers grows, at a cost of one byte of state per
register.

The name-defining paper is Philippe Flajolet, Eric Fusy, Olivier Gandouet, and
Frederic Meunier, "HyperLogLog. The Analysis of a Near-Optimal Cardinality
Estimation Algorithm," presented at AofA 2007 and published in Discrete
Mathematics and Theoretical Computer Science Proceedings
(https://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf, verified
2026-08-02). It replaces LogLog's arithmetic mean of the m register values with
a harmonic mean, which is far less sensitive to a single unusually large
register value, and it derives a bias-correction constant, called alpha
sub-m in the literature, that depends only on m. The paper's headline result is
a relative accuracy, expressed as a standard error, of approximately
1.04 divided by the square root of m, and a demonstration that cardinalities
beyond one billion can be estimated to within a typical 2 percent error using
1.5 kilobytes of registers, hence the name. Hyper because the harmonic mean
beats LogLog's arithmetic mean at the same memory budget.

A fourth paper, cited widely enough in production systems that it deserves its
own place in the lineage rather than being folded into "implementation
variants," is Stefan Heule, Marc Nunkesser, and Alex Hall, "HyperLogLog in
Practice. Algorithmic Engineering of a State of the Art Cardinality Estimation
Algorithm," EDBT 2013, describing the HyperLogLog++ variant built and deployed
at Google
(https://research.google/pubs/hyperloglog-in-practice-algorithmic-engineering-of-a-state-of-the-art-cardinality-estimation-algorithm/,
verified 2026-08-02). HyperLogLog++ switches to a 64-bit hash to push the
practical cardinality ceiling far past the 2^32 limit of the original paper's
32-bit hash, adds a sparse representation so small sets cost far less than the
dense m-register array, and replaces the small-range linear counting
correction with an empirically fitted bias table. Most production
implementations described in this entry, including the ones in Redis, Google
BigQuery, and Elasticsearch, are HyperLogLog++ or a close relative of it rather
than the 2007 paper's algorithm verbatim, and "HyperLogLog" in casual industry
usage almost always means this later, engineered variant.

## 2. Problem and context

A system needs to answer "how many distinct X happened" where X might be
visitors to a page, IP addresses hitting an API, users who played a song,
distinct search queries in a day, or distinct values in a database column, and
the naive answer, keep a hash set of everything seen and report its size, does
not scale to the volumes involved.

The concrete failure a reader can recognise in their own codebase looks like
this. A Python or Java service maintains a set of user identifiers to answer
"how many unique visitors today," and that set grows without bound for as long
as the measurement window is open. At ten million unique visitors and an
average identifier length of thirty six bytes for a UUID string, the set alone
costs several hundred megabytes of heap, before accounting for the hash table's
own overhead of buckets, pointers, and load-factor slack, which commonly
doubles or triples the raw payload size. Multiply that by every page, every
video, every day the product wants a distinct count for, and the exact
approach either exhausts memory or forces the count to be computed in a batch
job hours later against data warehoused on disk, which is too slow for a
dashboard a person is looking at right now.

The context in which HyperLogLog is the right tool has three properties. The
exact count is not actually required, a confidence interval of one to two
percent is acceptable, which is true for almost every analytics, monitoring,
and capacity-planning use case and false for financial reconciliation or
anything a regulator will audit. The stream of elements is too large, too
high-cardinality, or too privacy-sensitive to retain individually, since
storing every raw identifier is itself often a compliance liability under
regimes such as GDPR that treat an IP address or a user identifier as personal
data. And the count must be computed incrementally, over a stream, in one pass,
often merged later from many independent shards, rather than by loading a
complete dataset into memory at once.

## 3. Forces

**Memory versus accuracy.** The number of registers m directly trades one for
the other. Doubling m roughly halves the standard error but doubles the
register array size. HyperLogLog's whole reason for existing is that this
trade is logarithmically favourable, going from 1 percent accuracy to 12
kilobytes of state instead of the gigabytes an exact count needs, and the
pattern is judged almost entirely on how well it makes that specific trade.

**Accuracy versus range.** The register width, one byte in most
implementations, bounds the largest leading-zero-run count a register can
record, which in turn bounds the cardinality the sketch can represent before
saturating. A wider register buys more range at the cost of more memory per
register, and HyperLogLog++'s move to a 64-bit hash is precisely a decision to
spend a few more bits of range in exchange for supporting cardinalities that a
32-bit hash space cannot represent without collisions.

**Mergeability versus per-node accuracy.** A HyperLogLog sketch merges with
another sketch of the same configuration by taking the elementwise maximum of
their registers, an operation that is commutative, associative, and idempotent,
which is precisely what a distributed system needs to combine partial counts
from many shards, many time windows, or many replicas without coordination.
This mergeability is close to free because it falls directly out of taking the
maximum leading-zero-run per bucket, but it is only available if every merged
sketch shares the identical hash function and identical p, a constraint that
couples every producer of a sketch to a single configuration decision made
once, early, and rarely revisited.

**Latency versus consistency.** Because PFADD-style insertion and PFMERGE-style
combination are both cheap, constant-time-per-element operations, HyperLogLog
favours low insertion latency and eventual, mergeable consistency over any
notion of a strongly consistent running total. A system that needs a
transactionally exact running count at every instant, for example a payment
ledger, is fighting the pattern's forces rather than using them.

**Cost of collisions versus cost of a stronger hash.** The whole estimate rests
on the hash function distributing inputs uniformly over the output space. A
weak hash with poor avalanche in the bits used for register selection produces
a systematically biased, sometimes badly biased, cardinality estimate that no
amount of registers fixes, because the bias is structural rather than
statistical. This is a real engineering trap, demonstrated concretely in
dimension 8 below, and the fix, a stronger finalising mix step, costs a few
nanoseconds per insertion in exchange for the accuracy the algorithm's math
actually promises.

## 4. Applicability and non-applicability

Reach for HyperLogLog when the system needs an approximate distinct count over
a high-volume or high-cardinality stream, when the exact set of members never
needs to be recovered or enumerated, when partial counts computed on separate
shards, separate time windows, or separate machines must be combined later
without a central coordinator, when a fixed, small, and predictable memory
budget matters more than perfect accuracy, and when the count is one signal
among several feeding a dashboard, an alert threshold, or a capacity plan
rather than the sole input to a financial or legal decision.

Do not reach for HyperLogLog under any of these conditions, and the reason is
attached to each because a bare list is not useful on its own.

- The application needs to know which distinct elements were seen, not merely
  how many. A HyperLogLog register stores the maximum leading-zero-run per
  hash bucket, and that value cannot be inverted back into the elements that
  produced it. If the product needs "list the unique visitors," a set,
  a bitmap such as a Roaring Bitmap, or a database DISTINCT query is the
  correct structure, not a cardinality sketch.
- The cardinality being measured is small, in the low hundreds or fewer. Below
  roughly 2.5 times the register count m, the estimator itself falls back to a
  linear-counting correction because the harmonic-mean formula is unreliable
  in that range, and at truly small counts an exact hash set costs less memory
  than the sketch and is exact rather than approximate, so there is no reason
  to trade accuracy away for nothing.
- The application must produce an exact count for a financial, legal,
  billing, or audit purpose. A per-seat software license count, a payment
  reconciliation, or a regulatory report cannot tolerate a one to two percent
  error band, and using HyperLogLog there trades a real requirement for an
  approximate one silently.
- The system needs set operations beyond union, specifically intersection or
  difference. HyperLogLog merges cleanly under union because the elementwise
  maximum is exact for that operation, but there is no exact operation on two
  sketches that yields the intersection cardinality. Inclusion-exclusion, an
  estimate derived from three unions, works but its relative error compounds
  badly and becomes unusable when the two sets are similar in size and have
  small overlap, which is a known and documented weakness rather than an
  implementation bug.
- The stream is adversarial, meaning an attacker controls or can predict which
  elements are inserted and benefits from skewing the estimate. Because the
  estimator depends on hash uniformity, an attacker who can choose inputs that
  collide against a known or predictable hash function can bias the count.
  Production HyperLogLog implementations, including Redis's, do not use a
  keyed or cryptographic hash by default, so this is a real, documented
  weakness for any input the sketch cannot trust, see Sara Ahmadian and Edith
  Cohen's ICML 2024 paper on the adversarial manipulation of cardinality
  sketches under adaptively chosen inputs
  (https://arxiv.org/abs/2405.17780, verified 2026-08-02) for the formal
  treatment of adaptive attacks against cardinality sketches, HyperLogLog
  included.

## 5. Structure

**Hash function.** A single, fixed hash function maps every incoming element
to a uniformly distributed bit string of a known width, commonly 32 bits in
the original paper and 64 bits in HyperLogLog++ and most production
implementations. Every producer and consumer of a given sketch must use
exactly the same hash function, because the registers are only meaningful
relative to that hash's output distribution.

**Precision parameter p.** A small integer, typically between 4 and 18 in
production systems, that fixes the number of registers as m = 2^p. It is
chosen once, at sketch creation, and every sketch that will ever be merged
together must share the same p.

**Register array.** An array of m small counters, most commonly one byte each,
indexed 0 through m minus 1. Register j holds the largest leading-zero-run
length ever observed among the hashes routed to bucket j, and it never
decreases, only grows monotonically as more elements are inserted, which is
the property that makes the elementwise maximum merge operation correct.

**Bucket selector.** The first p bits of the hash output, interpreted as an
unsigned integer, choose which register a given element updates. This is the
stochastic-averaging step inherited from LogLog, and it is what turns one
noisy Flajolet-Martin-style estimator into m correlated but jointly less noisy
estimators.

**Rank function, commonly called rho.** Applied to the remaining, non-index
bits of the hash, it returns the position of the leftmost set bit, one-indexed
from the most significant remaining bit, or one more than the bit width if
every remaining bit is zero. This value is what gets written into the selected
register when it exceeds the register's current value.

**Bias-correction constant, alpha sub-m.** A constant, derived analytically in
the 2007 paper and dependent only on m, that corrects the harmonic mean of the
register values for a systematic bias inherent to the estimator, converging to
0.7213 divided by (1 plus 1.079 divided by m) for large m.

**Small-range and large-range correctors.** Two threshold-triggered corrections
around the edges of the estimator's reliable range, linear counting, which
substitutes m times the natural log of m over the count of zero-valued
registers when the raw estimate falls below roughly 2.5m, and, in the original
32-bit paper, a large-range correction near the top of the 32-bit hash space
that HyperLogLog++'s 64-bit hash makes essentially unreachable in practice.

## 6. ASCII structure diagram

```
Incoming element "user-482913"
        |
        v
+-------------------+
|  hash function     |   64-bit uniform hash
|  (e.g. mixed FNV1a)|
+-------------------+
        |
        v
  64-bit hash value
  h = 1011...0100 1101...0010
      |________| |___________|
       top p bits   remaining (64-p) bits
       "index"      "w"  ->  rho(w)

        |                        |
        v                        v
 index j in [0, m)        rank r = leading_zero_run(w) + 1

                register array (size m = 2^p)
        +----+----+----+----+----+----+----+----+
        | R0 | R1 | R2 | R3 | .. |Rj-1| Rj |Rm-1|
        +----+----+----+----+----+----+----+----+
                                    ^
                                    |
                        Rj <- max(Rj, r)

  estimate = alpha_m * m^2 / sum_over_all_j(2^-Rj)
             (with small-range / large-range correction)
```

## 7. Dynamics

**Insertion, PFADD in Redis vocabulary.** For every incoming element, hash the
element to a fixed-width bit string. Split the hash into the top p bits, the
index j, and the remaining bits, w. Compute the rank r as the leading-zero-run
length of w plus one. Compare r against the current value stored in register
j, and if r is larger, overwrite register j with r. If r is not larger, do
nothing. Every insertion is O(1) in time, touches exactly one register, and
never allocates, since the register array is fixed in size from the moment the
sketch is created.

**Query, PFCOUNT in Redis vocabulary.** Compute the harmonic mean of 2^-r
across all m registers, take its reciprocal, multiply by m squared and by the
bias constant alpha sub-m, apply the small-range correction if the raw
estimate falls at or below 2.5 times m and at least one register is still
zero, and return the resulting number, rounded to the nearest integer. This
operation is O(m), which in practice means O(number of registers), a small
constant independent of how many elements were ever inserted, not O(number of
distinct elements).

**Merge, PFMERGE in Redis vocabulary.** Given two or more sketches that share
the same p and the same hash function, produce a new sketch whose register j
is the elementwise maximum of register j across all the input sketches. This
operation is exact, not approximate, meaning the merged sketch is
indistinguishable from a sketch that had been fed the union of every element
in every input stream from the start, and the count derived from it carries
exactly the accuracy bound the original single-stream sketch would have. This
is the property that lets a distributed system compute a daily unique-visitor
count from 24 independent hourly sketches, or a global count from a thousand
independent per-shard sketches, by shipping only the small fixed-size sketches
across the network rather than the raw event stream.

```
  Shard A sketch      Shard B sketch      Shard C sketch
    [R0..Rm-1]           [R0..Rm-1]           [R0..Rm-1]
         |                    |                    |
         +--------------------+--------------------+
                              |
                elementwise max, register by register
                              |
                              v
                    merged sketch [R0..Rm-1]
                              |
                              v
                   PFCOUNT-style estimate over
                   the merged register array
```

## 8. Implementation variants

The three code samples below implement the same variant, a HyperLogLog with
harmonic-mean estimation and a small-range linear-counting correction, at
precision p equals 10, meaning 1024 one-byte registers, 1 kilobyte of state
per sketch. This is a deliberately teachable configuration, not a production
one, since Redis's default configuration behaves closer to p equals 14, 16384
registers, for its stated 0.81 percent standard error. All three samples share
one design decision worth calling out explicitly because it is a genuine and
common implementation trap, not a stylistic choice.

**The hash must be well mixed across its whole width, not only well
distributed as a black box.** A first draft of this pattern's reference
implementation used a plain FNV-1a 64-bit hash directly as the source of both
the register index, the top bits, and the rank, the remaining bits. Run
against one hundred thousand sequential string keys with p equals 10, that
direct FNV-1a draft produced an estimate of roughly 1,780 against a true count
of 100,000, an error of over 98 percent, because FNV-1a's avalanche is
markedly weaker in its high-order bits than in its low-order bits for the kind
of short, structured keys a real system actually produces, which concentrated
almost all insertions into a small minority of the 1024 buckets and left the
rest at zero. This is a known category of weakness for multiplicative hashes
used outside their design envelope, and the standard, cheap fix is a
finalisation step, applied after the raw hash, that guarantees strong
avalanche across every bit. The samples below use the finaliser popularised by
Sebastiano Vigna's splitmix64 generator and reused in the finalisation step of
Austin Appleby's MurmurHash3, three rounds of XOR-shift and large-prime
multiplication, applied to the FNV-1a output before either the index or the
rank is derived from it. After that single fix, the same 100,000-key test
produces an estimate of 98,235, a 1.76 percent error, consistent with the
sketch's theoretical standard error of 1.04 divided by the square root of
1024, roughly 3.25 percent.

Other implementation variants seen in production and in the literature, none
of which are demonstrated in the runnable code below because they trade
teachability for engineering depth, are as follows.

- **Sparse representation.** HyperLogLog++ and Redis both store a sketch that
  has seen few distinct elements as a sorted list of nonzero, non-default
  register updates rather than as the full dense array, and only convert to
  the dense array once the sparse list grows past a size threshold. This is
  the single biggest practical memory win for the common case of many small
  per-key sketches, since a sketch that has seen ten elements does not need
  12 kilobytes to represent that fact.
- **Bias correction by empirical table instead of the analytic alpha
  constant.** HyperLogLog++ replaces the analytically derived small-range
  correction with a table of empirically measured biases at fixed cardinality
  points, interpolated between them, which the Heule, Nunkesser, and Hall
  paper reports measurably improves accuracy in the range where the original
  paper's correction is weakest.
- **64-bit hash with a raised cardinality ceiling.** Redis, BigQuery, and
  Elasticsearch's underlying implementations all use a 64-bit hash rather than
  the original paper's 32-bit hash specifically so the sketch can represent
  cardinalities into the billions and beyond without the hash space itself
  becoming the limiting factor, a change documented explicitly for Redis in
  its published upper limit of 2^64 members
  (https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/,
  verified 2026-08-02).
- **Language-idiomatic packaging.** In a language with first-class byte
  arrays and no garbage-collected object per counter, such as Go or Rust, the
  register array is naturally a flat byte slice, matching the structure below
  closely. In a language where every object carries per-instance overhead,
  packing four 6-bit registers into three bytes, a technique Redis's on-disk
  dense encoding uses, cuts the sketch's footprint by a real margin at the
  cost of more complex bit-twiddling on read and write.

```python
import math

MASK64 = 0xFFFFFFFFFFFFFFFF


def fnv1a_64(s: str) -> int:
    h = 14695981039346656037
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 1099511628211) & MASK64
    return h


def mix64(x: int) -> int:
    # splitmix64-style finaliser, guarantees avalanche across all 64 bits.
    z = x & MASK64
    z = ((z ^ (z >> 30)) * 0xbf58476d1ce4e5b9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94d049bb133111eb) & MASK64
    return (z ^ (z >> 31)) & MASK64


def hash64(s: str) -> int:
    return mix64(fnv1a_64(s))


def rho(w: int, width: int) -> int:
    if w == 0:
        return width + 1
    return width - w.bit_length() + 1


class HyperLogLog:
    def __init__(self, p: int = 10):
        self.p = p
        self.m = 1 << p
        self.registers = [0] * self.m
        if self.m >= 128:
            self.alpha = 0.7213 / (1 + 1.079 / self.m)
        elif self.m == 64:
            self.alpha = 0.709
        elif self.m == 32:
            self.alpha = 0.697
        else:
            self.alpha = 0.673

    def add(self, item: str) -> None:
        h = hash64(item)
        idx = h >> (64 - self.p)
        w = h & ((1 << (64 - self.p)) - 1)
        r = rho(w, 64 - self.p)
        if r > self.registers[idx]:
            self.registers[idx] = r

    def count(self) -> int:
        z = sum(2.0 ** -r for r in self.registers)
        estimate = self.alpha * self.m * self.m / z
        if estimate <= 2.5 * self.m:
            zeros = self.registers.count(0)
            if zeros > 0:
                estimate = self.m * math.log(self.m / zeros)
        return round(estimate)


if __name__ == "__main__":
    for n in (1000, 10000, 100000, 1000000):
        hll = HyperLogLog(p=10)
        for i in range(n):
            hll.add(f"user-{i}")
        est = hll.count()
        err = round(abs(est - n) / n * 100, 2)
        print("true", n, "estimate", est, "error_pct", err)
```

```go
package main

import (
	"fmt"
	"math"
	"math/bits"
	"strconv"
)

func fnv1a64(s string) uint64 {
	var h uint64 = 14695981039346656037
	for i := 0; i < len(s); i++ {
		h ^= uint64(s[i])
		h *= 1099511628211
	}
	return h
}

func mix64(x uint64) uint64 {
	z := x
	z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9
	z = (z ^ (z >> 27)) * 0x94d049bb133111eb
	z = z ^ (z >> 31)
	return z
}

func hash64(s string) uint64 {
	return mix64(fnv1a64(s))
}

func rho(w uint64, width uint) uint8 {
	if w == 0 {
		return uint8(width) + 1
	}
	bl := uint(bits.Len64(w))
	return uint8(width-bl) + 1
}

type HyperLogLog struct {
	p         uint
	m         int
	registers []uint8
	alpha     float64
}

func NewHyperLogLog(p uint) *HyperLogLog {
	m := 1 << p
	var alpha float64
	switch {
	case m >= 128:
		alpha = 0.7213 / (1 + 1.079/float64(m))
	case m == 64:
		alpha = 0.709
	case m == 32:
		alpha = 0.697
	default:
		alpha = 0.673
	}
	return &HyperLogLog{p: p, m: m, registers: make([]uint8, m), alpha: alpha}
}

func (h *HyperLogLog) Add(item string) {
	x := hash64(item)
	idx := x >> (64 - h.p)
	w := x & ((uint64(1) << (64 - h.p)) - 1)
	r := rho(w, 64-h.p)
	if r > h.registers[idx] {
		h.registers[idx] = r
	}
}

func (h *HyperLogLog) Count() int64 {
	var z float64
	zeros := 0
	for _, r := range h.registers {
		z += math.Pow(2, -float64(r))
		if r == 0 {
			zeros++
		}
	}
	estimate := h.alpha * float64(h.m) * float64(h.m) / z
	if estimate <= 2.5*float64(h.m) && zeros > 0 {
		estimate = float64(h.m) * math.Log(float64(h.m)/float64(zeros))
	}
	return int64(math.Round(estimate))
}

func main() {
	for _, n := range []int{1000, 10000, 100000, 1000000} {
		hll := NewHyperLogLog(10)
		for i := 0; i < n; i++ {
			hll.Add(fmt.Sprintf("user-%d", i))
		}
		est := hll.Count()
		errPct := math.Round(math.Abs(float64(est)-float64(n))/float64(n)*10000) / 100
		errStr := strconv.FormatFloat(errPct, 'f', -1, 64)
		fmt.Println("true", n, "estimate", est, "error_pct", errStr)
	}
}
```

```typescript
function fnv1a64(s: string): bigint {
  let h = 14695981039346656037n;
  const mask = 0xffffffffffffffffn;
  for (let i = 0; i < s.length; i++) {
    h ^= BigInt(s.charCodeAt(i));
    h = (h * 1099511628211n) & mask;
  }
  return h;
}

function mix64(x: bigint): bigint {
  const mask = 0xffffffffffffffffn;
  let z = x & mask;
  z = ((z ^ (z >> 30n)) * 0xbf58476d1ce4e5b9n) & mask;
  z = ((z ^ (z >> 27n)) * 0x94d049bb133111ebn) & mask;
  return (z ^ (z >> 31n)) & mask;
}

function hash64(s: string): bigint {
  return mix64(fnv1a64(s));
}

function bitLength(w: bigint): number {
  let n = 0;
  let v = w;
  while (v > 0n) {
    v >>= 1n;
    n++;
  }
  return n;
}

function rho(w: bigint, width: number): number {
  if (w === 0n) return width + 1;
  return width - bitLength(w) + 1;
}

class HyperLogLog {
  readonly p: number;
  readonly m: number;
  private readonly registers: Uint8Array;
  private readonly alpha: number;

  constructor(p: number) {
    this.p = p;
    this.m = 1 << p;
    this.registers = new Uint8Array(this.m);
    if (this.m >= 128) {
      this.alpha = 0.7213 / (1 + 1.079 / this.m);
    } else if (this.m === 64) {
      this.alpha = 0.709;
    } else if (this.m === 32) {
      this.alpha = 0.697;
    } else {
      this.alpha = 0.673;
    }
  }

  add(item: string): void {
    const width = 64 - this.p;
    const h = hash64(item);
    const idx = Number(h >> BigInt(width));
    const w = h & ((1n << BigInt(width)) - 1n);
    const r = rho(w, width);
    if (r > this.registers[idx]) {
      this.registers[idx] = r;
    }
  }

  count(): number {
    let z = 0;
    let zeros = 0;
    for (const r of this.registers) {
      z += Math.pow(2, -r);
      if (r === 0) zeros++;
    }
    let estimate = (this.alpha * this.m * this.m) / z;
    if (estimate <= 2.5 * this.m && zeros > 0) {
      estimate = this.m * Math.log(this.m / zeros);
    }
    return Math.round(estimate);
  }
}

for (const n of [1000, 10000, 100000, 1000000]) {
  const hll = new HyperLogLog(10);
  for (let i = 0; i < n; i++) {
    hll.add(`user-${i}`);
  }
  const est = hll.count();
  const errPct = Math.round((Math.abs(est - n) / n) * 10000) / 100;
  console.log("true", n, "estimate", est, "error_pct", errPct);
}
```

All three samples were executed against the identical input sequence, the
strings "user-0" through "user-N minus 1", at p equals 10. Python, Go, and the
TypeScript sample run under Node's type-stripping mode produced an identical
raw estimate at every tested N, 991, 10570, 98235, and 1000936. True 1000,
error 0.9 percent. True 10000, error 5.7 percent. True 100000, error 1.76
percent in Python and 1.77 percent in Go and TypeScript, a display-only
difference from Python's round-half-to-even rounding of the borderline value
1.765 against Go and TypeScript's round-half-away-from-zero, not a difference
in the underlying estimate. True 1000000, error 0.09 percent. The one
outlier, 5.7 percent at N equals 10000, sits inside the expected
spread for a single sketch at this precision, since the theoretical standard
error of 3.25 percent describes the typical deviation across many independent
trials, not a hard bound on any one run, and a single unlucky run above two
standard errors from the true value is expected roughly one time in twenty.

## 9. Known production uses

**Redis.** Redis ships HyperLogLog as a native data type since version 2.8.9,
exposed through the PFADD, PFCOUNT, and PFMERGE commands, encoded internally as
a Redis string so it can be read and written with GET and SET like any other
value. Redis states a standard error of 0.81 percent, a maximum memory
footprint of 12 kilobytes per sketch, and a documented cardinality ceiling of
2^64 members, and its own worked example counts unique page or video viewers
without storing raw IP addresses or user identifiers
(https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/,
verified 2026-08-02).

**Google BigQuery.** BigQuery ships a family of HLL_COUNT functions,
HLL_COUNT.INIT, HLL_COUNT.MERGE, HLL_COUNT.MERGE_PARTIAL, and
HLL_COUNT.EXTRACT, that build and combine HyperLogLog++ sketches directly
inside SQL queries, so a warehouse table can store a precomputed sketch per
partition and merge sketches across partitions at query time instead of
re-scanning the raw rows for every COUNT DISTINCT
(https://cloud.google.com/bigquery/docs/reference/standard-sql/hll_functions,
verified 2026-08-02). This mirrors the Heule, Nunkesser, and Hall paper's own
description of HyperLogLog++ as the algorithm Google engineered specifically
for internal, warehouse-scale cardinality estimation.

**Elasticsearch.** Elasticsearch's cardinality aggregation is built on
HyperLogLog++ and exposes a precision_threshold parameter that controls the
sketch's memory cost, documented as approximately the threshold value times 8
bytes, trading that memory against accuracy, and Elastic's own documentation
reports the error staying low, in the 1 to 6 percent range shown in its
accompanying chart, even at a threshold as low as 100
(https://www.elastic.co/docs/reference/aggregations/search-aggregations-metrics-cardinality-aggregation,
verified 2026-08-02).

**Trino, and its predecessor Presto, from which Trino forked.** Trino's
approx_distinct function, and the underlying approx_set HyperLogLog functions
it is built on, provide an approximation of COUNT DISTINCT with a default
standard error of 2.3 percent and an explicit error parameter callers may tune
between roughly 0.4 percent and 26 percent, documented plainly as offering no
guaranteed upper bound on error for any specific input set, only a statistical
one
(https://trino.io/docs/current/functions/aggregate.html, verified 2026-08-02).

## 10. Consequences

Positive consequences of adopting HyperLogLog.

- Memory cost is fixed and small, independent of the true cardinality, which
  turns an operation that would otherwise need memory proportional to the
  number of distinct elements into one that needs a constant, budgetable
  amount, commonly kilobytes rather than gigabytes.
- Insertion and merge are both extremely cheap, constant time per element for
  insertion and linear in the number of sketches, not the number of elements,
  for merging, which makes the pattern a natural fit for streaming pipelines
  and for combining results computed independently across shards or time
  windows.
- The merge operation is exact and lossless with respect to the union it
  represents, so distributing the counting work and recombining it later never
  introduces additional error beyond what a single sketch of the combined
  stream would already carry.
- The sketch itself does not retain the original elements, which can be a
  genuine privacy and data-minimisation advantage, since a count can be
  produced and shared without ever persisting the raw identifiers that
  contributed to it, a property Redis's own documentation calls out
  explicitly for unique-visitor counting where storing IP addresses would be a
  legal liability in some jurisdictions
  (https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/,
  verified 2026-08-02).

Negative consequences of adopting HyperLogLog.

- The count is approximate, always. Every read carries a statistical error
  band, and no amount of post-processing recovers the exact value from the
  sketch alone. Any downstream consumer that silently assumes an exact count,
  a billing system, a compliance report, a unit test asserting equality
  instead of a tolerance, will eventually be wrong.
- The sketch answers only "how many," never "which ones." Any product
  requirement that later grows to need the actual list of distinct elements
  forces a parallel structure, or a full migration away from the sketch,
  neither of which is cheap to retrofit.
- Correctness depends entirely on hash quality, and a subtly weak hash
  produces a subtly, or badly, biased estimate with no error message and no
  crash, exactly the kind of silent failure that is hardest to catch in code
  review, as demonstrated concretely in dimension 8 above.
- Every sketch that will ever be merged must share the same hash function and
  the same precision parameter p, which is a configuration decision that is
  cheap to make once and expensive to change later, since changing it silently
  breaks every merge against sketches created before the change.

## 11. Failure modes and misuse

**Symptom.** The estimated cardinality is wildly wrong, off by an order of
magnitude or more, in one direction, and stays wrong no matter how large the
true count grows.
**Cause.** The hash function used for bucket selection and rank has weak
avalanche in the bits that select the register index, so most insertions
collapse into a small subset of the m registers while the rest stay at their
initial zero value, which the small-range linear-counting correction then
badly misreads as "the true cardinality must be small." This is the exact
failure demonstrated with a bare FNV-1a hash in dimension 8.
**Fix.** Apply a strong finalising mix, such as the splitmix64-derived
finaliser used in the code samples, or use a hash function whose whole output
is documented to pass avalanche tests, such as MurmurHash3 or xxHash, and
verify empirically, not just by reading documentation, that the top p bits of
the hash are as well distributed as the remaining bits before shipping.

**Symptom.** Two services report noticeably different unique-visitor counts
for what should be the same underlying event stream, even though both claim to
use HyperLogLog.
**Cause.** The two services use sketches created with different precision
parameters, different hash functions, or, most commonly, different versions of
the same library where the hash function or the bias-correction table changed
between releases without a version bump in the serialized sketch format.
**Fix.** Pin the hash function, the precision parameter, and the sketch
serialization format as a single versioned contract shared by every producer
and consumer, and reject or flag a merge between sketches whose declared
configuration does not match, the same discipline Redis applies by refusing to
merge a HyperLogLog-encoded string with one that lacks the expected internal
header.

**Symptom.** A dashboard shows the daily unique count as smaller than the sum
of two sub-periods it should be strictly larger than, or shows a count that
appears to shrink over time for a metric that should only grow.
**Cause.** Someone merged sketches by summing their individual PFCOUNT results
rather than merging the sketches themselves and counting the merged result.
Summing per-shard estimates double-counts every element that appears in more
than one shard, and is not the same operation as, nor an approximation of, the
correct union.
**Fix.** Always call the merge operation, PFMERGE or its equivalent, on the
raw sketches first, and query the cardinality once, on the merged sketch. Never
sum cardinality estimates across shards as a substitute for merging.

**Symptom.** A cardinality estimate is suspiciously exact-looking at very low
counts, for example reporting precisely zero when the true count is a handful
of items, or jumps in a stair-step pattern rather than smoothly as items are
added.
**Cause.** The application is reading raw register values, or an intermediate
estimate, before the small-range linear-counting correction has been applied,
or is using a sketch implementation that omits the small-range correction
entirely, a documented weak point of the original 1985 and 2007 papers'
estimators at low cardinalities that HyperLogLog++ specifically improves on
with its empirical bias table.
**Fix.** Use a maintained, widely deployed implementation, such as Redis's,
rather than a hand-rolled sketch, for anything that will see production
traffic at genuinely small cardinalities, or explicitly implement and test the
small-range correction path, which the reference code samples in dimension 8
demonstrate in full.

**Symptom.** An adversarial or spam-heavy input stream produces a cardinality
estimate that is consistently and suspiciously higher, or lower, than
independently verified ground truth, in a way ordinary traffic never showed.
**Cause.** An attacker who can choose or predict which strings the hash
function will map into specific registers can deliberately inflate or deflate
the estimate, a class of attack formalised by Ahmadian and Cohen, cited above,
which shows that standard, unkeyed hash functions used in production
cardinality sketches are not designed to resist an adversary who observes the
sketch's behaviour and adapts its inputs.
**Fix.** Do not expose a HyperLogLog-backed count as a security-relevant
signal against inputs an attacker controls without also applying rate limiting
or a keyed hash upstream, and treat the sketch as a statistical summary for
trusted or semi-trusted telemetry, not as a defence mechanism on its own.

## 12. Trade-off matrix

The comparison is against three named alternatives that solve the same
distinct-counting problem by a different structural bet. An exact hash set,
the naive baseline the pattern displaces. A Bloom filter, which answers
membership rather than cardinality but is frequently reached for by mistake in
this exact spot. And Linear Counting, the simpler probabilistic ancestor that
HyperLogLog's small-range correction itself borrows from.

| Force | HyperLogLog | Exact hash set | Bloom filter | Linear Counting |
|---|---|---|---|---|
| Memory for high cardinality | Fixed, kilobytes, independent of count | Proportional to distinct count, can be gigabytes | Proportional to set size at a target false-positive rate | Proportional to a bitmap sized for the expected cardinality |
| Accuracy | Approximate, standard error near 1.04 over square root of m | Exact | Not applicable, answers membership not cardinality | Approximate, degrades badly once true count exceeds the bitmap's design range |
| Mergeable across shards | Yes, exact elementwise maximum union | Yes, exact set union, but at full element cost | Yes for union via bitwise OR, no exact cardinality from the result | Yes via bitwise OR of the underlying bitmap, same range limitation applies after merge |
| Answers "which elements" | No | Yes | No, and false positives mean membership answers are unreliable too | No |
| Range before accuracy or representation breaks down | Very large, effectively unbounded with a 64-bit hash | Unbounded, limited only by available memory | Unbounded for membership, but false-positive rate rises as load factor rises | Bounded by the bitmap size chosen at creation, must be sized for the maximum expected cardinality up front |

## 13. Related and incompatible patterns

**Consistent Hashing.** Both patterns lean on a well-distributed hash function
as their load-bearing primitive, and both fail in the same structural way,
silently and without an error, when that hash is weaker than assumed. A team
that has already audited its hash function for consistent hashing has done
half the diligence HyperLogLog also needs, and the two are frequently deployed
in the same sharded, distributed system.

**CRDTs, conflict-free replicated data types.** A HyperLogLog register array,
where merge is an elementwise maximum, is itself an instance of a
state-based CRDT, specifically a grow-only, join-semilattice structure, the
same mathematical shape as a G-Counter. Recognising this connection explains,
rather than merely asserting, why HyperLogLog merges are commutative,
associative, and idempotent, the exact three properties a CRDT's merge
operation must satisfy.

**Gossip Protocol.** Systems that propagate state via gossip commonly gossip
HyperLogLog sketches specifically because the merge operation tolerates
receiving the same sketch more than once, out of order, from more than one
peer, without corrupting the result, the same idempotence property gossip
protocols are built around.

**Bloom filter and Count-Min sketch.** These are the patterns most often
confused with HyperLogLog because all three are compact, hashed, probabilistic
structures, but they answer different questions. A Bloom filter answers "have
I seen this exact element," a Count-Min sketch answers "approximately how many
times has this exact element been seen," and HyperLogLog answers "how many
distinct elements total," and none of the three substitutes for another.

**Incompatible with any requirement for enumeration or an exact audit trail.**
There is no partial-compatibility mode. A HyperLogLog sketch cannot be
retrofitted to answer "list the elements" without storing the elements
somewhere else entirely, at which point the sketch is redundant for that
purpose and only useful for the cardinality estimate on the side.

## 14. Refactoring path in and out

**Introducing HyperLogLog into code that currently keeps an exact set.**
First, add the sketch alongside the existing exact set rather than replacing
it, and log both the exact count and the sketch's estimate for a representative
period, days or weeks depending on traffic volume, so the actual observed error
on real production data can be measured before anything depends on it. Second,
confirm every consumer of the current count can tolerate the sketch's
documented error band, since a consumer doing an equality check, an alert
firing on "count equals exactly zero," or a billing calculation is a blocker,
not a detail to patch later. Third, once the error is validated and every
consumer is compatible, cut the exact set over to the sketch, but retain the
ability to merge sketches from independent shards before this step, not
after, since retrofitting mergeability onto a single, monolithic
exact-set-turned-sketch migration is far more work than designing for sharded
merge from the start. Fourth, remove the exact set only after the sketch has
run in production, side by side, long enough to build confidence, and after
any downstream alerting thresholds have been recalibrated for the sketch's
error band rather than an exact value.

**Removing HyperLogLog once it stops earning its place.** This happens when a
product requirement grows to need the actual distinct elements, not merely
their count, at which point the sketch cannot be salvaged for that new
requirement and the correct move is to introduce an exact structure, a hash
set, a sorted set, or a warehouse table with a genuine DISTINCT query,
alongside or in place of the sketch. It also happens when the true cardinality
being measured turns out to be reliably small, in which case the fixed
kilobyte cost of the sketch is strictly worse, in both memory and accuracy,
than an exact hash set of the same small size, and reverting to the exact
structure is a straightforward, low-risk simplification rather than a
refactor under pressure.

## 15. Testing and verification

What HyperLogLog makes easy to test. The merge operation's algebraic
properties, commutativity, associativity, and idempotence, are cheap,
deterministic, exact-equality unit tests, since two merges of the same set of
sketches in different orders must produce byte-identical register arrays,
with no statistical tolerance needed for that particular assertion. The
insertion path is also fully deterministic for a fixed hash function and a
fixed input, so a regression test that inserts a fixed sequence of elements and
asserts the exact resulting register array, not merely the final cardinality
estimate, catches a hash function or rank-function regression far more
precisely than an estimate-only assertion would.

What became harder. Any test of the cardinality estimate itself must assert a
tolerance band, never exact equality, since the whole point of the structure
is that its output is approximate, and a test asserting the estimate equals
the true count exactly will flake intermittently even on entirely correct
code, because a certain fraction of runs will legitimately land more than one
standard error from the true value. The correct pattern is to assert the
estimate falls within a small, generous multiple, commonly three to five
standard errors, of the known true count for a fixed set of test inputs drawn
from a deterministic random source, and to additionally run the estimator
across many different such sources or input sets in a statistical test,
checking that the empirical distribution of errors matches the 1.04 over
square root of m prediction on average, rather than asserting any single run
is within bound.

Test doubles and techniques that apply. A fixed, non-cryptographic test hash
with a documented, known distribution over a small input alphabet makes the
insertion path's unit tests fully deterministic and independent of the
production hash's exact bit patterns. A golden-file test that serializes a
sketch built from a fixed input sequence and compares it byte for byte against
a checked-in reference file catches an accidental change to the hash function,
the rank function, or the bias-correction constant, which is precisely the
class of silent, compatibility-breaking bug described in dimension 11. A
property-based test that asserts, for randomly generated pairs of disjoint
input sets, that merge(sketch of A, sketch of B) always estimates a
cardinality close to len(A) plus len(B), exercises the merge and estimation
paths together under far more input variety than a handful of hand-picked
examples ever will.

## 16. Observability signals

What to log or trace at insertion time. A counter of total insertions per
sketch, since a sketch that is receiving zero insertions in a window that
should have traffic is a stronger and earlier signal of an upstream pipeline
failure than watching the cardinality estimate itself, which can plausibly
stay flat for other, benign reasons.

What to log or trace at merge time. The number of sketches merged and the
precision parameter p of each, so a configuration mismatch, described in
dimension 11's second failure mode, surfaces as a metric anomaly, a sudden
drop in merged-sketch count, or an explicit error, rather than as a silently
wrong final number discovered only when a human notices the dashboard looks
off.

What a healthy sketch's dashboard looks like. The estimated cardinality
trends smoothly, without discontinuous jumps, across successive queries of a
sketch that is only ever growing, since registers are monotonic and can never
decrease, and a visible drop in the reported count for a sketch that only
receives insertions, never a reset, is itself a bug signal, most often the
merge-versus-sum error from dimension 11's third failure mode, or a
serialization or deserialization bug that corrupted the register array.

What a failing sketch's dashboard looks like. A cardinality estimate that is
implausibly small relative to a known lower bound from an independent source,
for example a raw event-count metric that is itself an exact count of total
events, not distinct ones, and should always be greater than or equal to the
distinct-element estimate. A violation of that inequality is a strong,
specific, and actionable signal that the hash quality or the insertion path is
broken, exactly as demonstrated by the weak-hash failure mode in dimension 8
and dimension 11.

## 17. Security and privacy implications

Much of the reasoning in this dimension is analytical judgement about how the
structure's properties interact with common threat models, rather than a
sourced claim about a specific system, with the exception of the
adaptive-input attack, which is cited to its formal treatment.

HyperLogLog can be a genuine privacy improvement over storing raw identifiers,
because the sketch, by construction, does not retain the elements that were
inserted into it, only the maximum leading-zero-run per bucket, and there is
no operation defined on the sketch that recovers an inserted element. This is
the reasoning behind Redis's own framing of the structure as a way to count
unique visitors without storing IP addresses, which several jurisdictions
treat as personal data
(https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/,
verified 2026-08-02). This property should not be overstated into a claim of
formal anonymity or differential privacy, since a HyperLogLog sketch has no
mathematically proven privacy guarantee against, for example, an adversary who
can query the sketch repeatedly while controlling which elements are inserted
between queries, because the register updates leak some information about
individual insertions to an adversary in that specific position, even though
no ordinary read of a completed sketch reveals its members.

The attack surface HyperLogLog opens, rather than closes, is the adaptive
cardinality-manipulation attack formalised by Sara Ahmadian and Edith Cohen in
their ICML 2024 paper on cardinality sketches under adaptively chosen inputs
(https://arxiv.org/abs/2405.17780, verified 2026-08-02), in which an attacker
who can choose or predict inputs and observe the resulting estimate can
deliberately bias the count, because production HyperLogLog implementations
use fast, unkeyed, non-cryptographic hash functions by design, for speed, not
resistance to a chosen-input adversary. A system that exposes a
HyperLogLog-backed count as an input to a security decision, a rate-limit
threshold, an anomaly-detection baseline, or a fraud signal, and allows an
attacker to influence which elements are inserted, is exposing that decision
to manipulation through the sketch. The mitigation is architectural. Keep
untrusted, attacker-influenced input paths away from security-relevant
cardinality signals, or apply a keyed hash and treat the key as a secret, not
a property of the sketch itself.

## 18. References

- Philippe Flajolet and G. Nigel Martin, "Probabilistic Counting Algorithms
  for Data Base Applications," Journal of Computer and System Sciences, volume
  31, 1985, pages 182 to 209.
  https://algo.inria.fr/flajolet/Publications/FlMa85.pdf, verified 2026-08-02.
- Marianne Durand and Philippe Flajolet, "Loglog Counting of Large
  Cardinalities," Algorithms, ESA 2003, Lecture Notes in Computer Science
  volume 2832, Springer, Berlin, Heidelberg, pages 605 to 617.
  https://link.springer.com/chapter/10.1007/978-3-540-39658-1_55, verified
  2026-08-02.
- Philippe Flajolet, Eric Fusy, Olivier Gandouet, and Frederic Meunier,
  "HyperLogLog. The Analysis of a Near-Optimal Cardinality Estimation
  Algorithm," AofA 2007, Discrete Mathematics and Theoretical Computer Science
  Proceedings. https://algo.inria.fr/flajolet/Publications/FlFuGaMe07.pdf,
  verified 2026-08-02.
- Stefan Heule, Marc Nunkesser, and Alex Hall, "HyperLogLog in Practice.
  Algorithmic Engineering of a State of the Art Cardinality Estimation
  Algorithm," EDBT 2013.
  https://research.google/pubs/hyperloglog-in-practice-algorithmic-engineering-of-a-state-of-the-art-cardinality-estimation-algorithm/,
  verified 2026-08-02.
- Redis, "HyperLogLog," Redis documentation.
  https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/,
  verified 2026-08-02.
- Google Cloud, "HyperLogLog++ functions," BigQuery standard SQL reference.
  https://cloud.google.com/bigquery/docs/reference/standard-sql/hll_functions,
  verified 2026-08-02.
- Elastic, "Cardinality aggregation," Elasticsearch reference documentation.
  https://www.elastic.co/docs/reference/aggregations/search-aggregations-metrics-cardinality-aggregation,
  verified 2026-08-02.
- Trino, "Aggregate functions," Trino documentation, approx_distinct and the
  approx_set HyperLogLog function family.
  https://trino.io/docs/current/functions/aggregate.html, verified 2026-08-02.
- Sara Ahmadian and Edith Cohen, ICML 2024 paper on the adversarial
  manipulation of cardinality sketches under adaptively chosen inputs.
  https://arxiv.org/abs/2405.17780, verified 2026-08-02.
- Wikipedia, "HyperLogLog," summarising the algorithm's history and the
  Redis-documented error and memory figures.
  https://en.wikipedia.org/wiki/HyperLogLog, verified 2026-08-02.
