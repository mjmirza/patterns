---
name: Memory Pool (Fixed Block Allocator)
slug: memory-pool
family: 28-embedded-hardware
category: Structural
aliases: [Memory Slab, Fixed-Size Block Allocator, Block Pool]
first_described: "Zephyr Project documentation, memory slabs"
maturity: canonical
related: [hardware-abstraction-layer, ring-buffer]
incompatible_with: []
verified: 2026-08-21
---

# Memory Pool (Fixed Block Allocator)

## 1. Name, aliases, and lineage

The canonical name is Memory Pool, more precisely a Fixed Block
Allocator, the pattern where a designated memory region is divided
into blocks of a single, fixed size, and allocation hands out one
whole block at a time rather than a variably-sized chunk. Zephyr's own
documentation names the mechanism directly, describing it as "a kernel
object that allows memory blocks to be dynamically allocated from a
designated memory region."

## 2. Problem and context

A general-purpose heap allocator serves requests of arbitrary size,
and repeated allocation and release of differently-sized chunks
carves the heap into a patchwork of used and free regions over time, a
condition commonly called fragmentation, where the heap may hold
enough total free memory to satisfy a request yet have no single free
region large enough to satisfy it. A Memory Pool solves this by
constraining every block to one fixed size, so a released block is
always immediately reusable by the next allocation request of that
same size, with no possibility of the free space becoming too small or
too scattered to serve a future request. Zephyr's own documentation
states this benefit directly, that fixed-size blocks allow memory to
be allocated and released efficiently, "avoiding memory fragmentation
concerns."

## 3. Forces

The pattern balances the following competing pressures.

- **Relief from fragmentation.** Favored. Zephyr's own documentation
  names this directly, since every block is a single fixed size,
  released memory is always immediately reusable by the next request
  of that size, with no possibility of the heap's free space becoming
  too fragmented to satisfy a future request.
- **Allocation and release speed.** Favored. Because every block is
  the same size, an allocator can track free blocks with a simple
  structure, such as a linked list of free blocks or a bitmap, rather
  than the more expensive size-matching search a general heap
  allocator performs.
- **Flexibility for arbitrarily-sized requests.** Sacrificed. A pool
  serves exactly one fixed block size, per Zephyr's own documented
  block-size requirement, so a request needing a size other than that
  one fixed size either wastes the unused remainder of a block or
  cannot be satisfied at all.
- **Total memory efficiency for varied-size workloads.** Sacrificed.
  A request smaller than the fixed block size still consumes an
  entire block, so a workload whose real requests vary widely in size
  wastes memory to the size of the largest common request, compared
  to a general heap allocator that can size each allocation to its
  actual need.

## 4. Applicability and non-applicability

Reach for a Memory Pool when the following hold.

- The application genuinely allocates and releases objects of one, or
  a small number, of known, fixed sizes repeatedly, over the system's
  running lifetime, such as network packet buffers or task control
  structures.
- Fragmentation-relief is genuinely a hard requirement, such as an
  embedded system that must run for a very long, unattended duration
  without a heap fragmenting into an unusable state.
- Allocation and release speed genuinely matters, since a pool's
  fixed-size bookkeeping is genuinely faster than a general heap
  allocator's size-matching search.

Do NOT reach for a Memory Pool in these cases, and the reason matters
more than the rule.

- **The application's real allocation sizes genuinely vary widely**,
  a fixed block size sized to the largest request wastes memory on
  every smaller request, a general heap allocator, or several pools
  at different fixed sizes, fits the varied real sizes better.
- **The system genuinely needs power-management control over which
  memory regions can be powered down**, per Zephyr's own documented
  distinction, a memory slab keeps its own bookkeeping inside the
  buffer itself, so the buffer cannot be powered down independently, a
  Memory Blocks Allocator with external bookkeeping, described in
  dimension 8, fits this need instead.
- **The application genuinely has only a single, one-time allocation
  need with no repeated allocate-and-release cycle**, the pattern's
  entire value comes from repeated reuse of fixed-size blocks, a
  one-time allocation does not need a pool's structure at all.

## 5. Structure

A Memory Pool has three structural parts.

- **The buffer**, the designated memory region divided into blocks,
  Zephyr's own documentation describing it as "an array of fixed-size
  blocks, with no wasted space between the blocks."
- **The free-block tracking**, the structure, commonly a linked list
  or a bitmap, that records which blocks are currently free and
  available for allocation.
- **The waiting queue**, for callers requesting a block when none is
  currently free, Zephyr's own documentation describing the ordering
  directly, that a freed block goes "to the highest-priority thread
  that has waited the longest."

## 6. ASCII structure diagram

```
  buffer, divided into N fixed-size blocks
  +------+------+------+------+------+
  | used | free | used | free | free |
  +------+------+------+------+------+
             |
             +-- free-block tracking, records which blocks are free
             |
  a request for a block
             |
             v
  a free block is handed out, or, if none is free, the requester
  joins the waiting queue until one is released
```

## 7. Dynamics

The trace below shows one complete allocate-and-release cycle.

```
A thread requests a block

the allocator checks the free-block tracking structure for an
available block
   |-- if a free block exists, it is handed to the requester
       immediately, marked as no longer free
   |-- if no free block exists, per Zephyr's own documented ordering,
       the requesting thread joins the waiting queue, ordered by
       priority and then by how long each thread has waited

A thread releases a block

the thread returns the block to the allocator once it is finished
   |-- the block is marked free again in the tracking structure
   |-- if a thread is waiting, per Zephyr's own documented ordering,
       the newly-freed block is handed directly to the highest-
       priority, longest-waiting thread in the queue, rather than
       simply being marked free for the next fresh request
```

## 8. Implementation variants

**Memory slab, internal bookkeeping.** The canonical Zephyr form, where
the tracking of which blocks are allocated lives inside the buffer's
own memory region, per Zephyr's own documentation describing memory
slabs directly.

**Memory blocks allocator, external bookkeeping.** Zephyr's own
documentation describes this distinct variant directly, that
"bookkeeping of allocated blocks" is "done outside of the associated
buffer," which, per that same documentation, "allows the buffer to
reside in memory regions where these can be powered down to conserve
energy," a capability the internal-bookkeeping memory slab variant
does not have.

**Free list, the classic C implementation.** Free blocks are linked
together into a singly-linked list using space inside each currently-
free block itself, so allocation pops the head of the list and release
pushes the returned block back onto it, an approach requiring no
separate tracking structure at all, at the cost of the internal-
bookkeeping trade-off described above.

## 9. Known production uses

**Zephyr's own documentation, defining the memory slab mechanism and
its fragmentation-relief benefit.** Zephyr states the definition and
the benefit directly. A memory slab is "a kernel object that allows
memory blocks to be dynamically allocated from a designated memory
region," where fixed-size blocks allow allocation and release
"efficiently and avoiding memory fragmentation concerns." Zephyr also
states the waiting-queue ordering directly, that a freed block goes to
"the highest-priority thread that has waited the longest." Zephyr
Project, "Memory Slabs,"
https://docs.zephyrproject.org/latest/kernel/memory_management/slabs.html,
verified 2026-08-21.

**Zephyr's own documentation, on the distinct external-bookkeeping
variant this pattern also supports.** Zephyr states the distinction
directly. "The Memory Blocks Allocator allows memory blocks to be
dynamically allocated from a designated memory region, where all
memory blocks have a single fixed size," with "bookkeeping of
allocated blocks done outside of the associated buffer," which "allows
the buffer to reside in memory regions where these can be powered down
to conserve energy." Zephyr Project, "Memory Blocks Allocator,"
https://docs.zephyrproject.org/latest/kernel/memory_management/sys_mem_blocks.html,
verified 2026-08-21.

## 10. Consequences

Positive.

- Fragmentation is never possible within the pool, per
  Zephyr's own documented benefit, since every block is the same
  fixed size, so a released block is always immediately usable by the
  next request of that size.
- Allocation and release are genuinely fast, since the allocator only
  ever tracks fixed-size blocks, avoiding the size-matching search a
  general heap allocator performs.
- The waiting-queue ordering, per Zephyr's own documented priority-
  and-wait-time rule, gives predictable, fair behavior when many
  threads contend for a limited number of blocks.

Negative.

- A request smaller than the fixed block size still consumes an
  entire block, wasting the unused remainder, a real cost for a
  workload whose real request sizes vary.
- A request larger than the fixed block size cannot be satisfied at
  all, so an application with genuinely varied allocation sizes needs
  either a general heap allocator or several distinct pools, each at
  its own fixed size.
- The internal-bookkeeping memory slab variant cannot have its buffer
  powered down independently, per Zephyr's own documented power-
  management distinction, a real cost for an energy-constrained
  system that does not use the external-bookkeeping variant instead.

## 11. Failure modes and misuse

**Sizing the fixed block to the largest observed request rather than
the actual common request size, wasting memory on every smaller
allocation.** Symptom. The system runs low on available blocks, or
consumes far more total memory than the application's real working
set needs, even though the pool itself is functioning correctly.
Cause. Choosing one fixed block size sized to accommodate a rare, large
outlier request, so every smaller, far more common request still
consumes a full, oversized block. Fix. Measure the application's real
distribution of request sizes, and either size the pool to the common
case with a separate path for the rare large request, or use several
distinct pools, each sized to a genuinely common request size.

**A thread that allocates a block and never releases it, exhausting
the pool over the system's running lifetime.** Symptom. Over time,
fewer and fewer blocks are available, and threads increasingly wait or
fail to allocate, even though no single allocation was individually
wrong, a slow, cumulative failure that a short-lived test run does not
reveal. Cause. A code path that allocates a block but has no matching
release, whether from a missed release call, an early return that
skips the release, or an error path that abandons the block without
returning it. Fix. Pair every allocation with a guaranteed release on
every exit path, including error paths, and test the pool's block
count over a long-running, repeated allocate-and-release cycle to
confirm the count returns to its starting value every time.

**Choosing the internal-bookkeeping memory slab variant for a buffer
that genuinely needs to be power-cycled independently.** Symptom. The
system cannot power down the memory region the pool's buffer occupies,
even though the application's real power budget depends on doing so,
because the pool's own tracking metadata lives inside that same
buffer. Cause. Defaulting to the canonical memory slab variant without
first confirming whether the target buffer's memory region genuinely
needs independent power control. Fix. Use the external-bookkeeping
memory blocks allocator variant, per Zephyr's own documented
distinction, whenever the buffer's memory region genuinely needs to be
powered down independently of the rest of the system.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Memory Pool | General heap allocator | Static, compile-time allocation |
|---|---|---|---|
| Relief from fragmentation | Strong, per Zephyr's own documented benefit, every block is the same size | Weak, varied-size allocation and release fragments the heap over time | Strong, nothing is dynamically allocated at all |
| Allocation and release speed | Strong, fixed-size bookkeeping avoids a size-matching search | Moderate to weak, a general allocator must search for a suitably-sized free region | Strongest, no runtime allocation cost at all |
| Flexibility for arbitrarily-sized requests | Weak, exactly one fixed block size per pool | Strong, any size can be requested | None, the size is fixed at compile time |
| Total memory efficiency for varied-size workloads | Weak, a smaller request still consumes a full block | Strong, each allocation is sized to its actual need | Strong for a known, fixed workload, but cannot adapt to a varying one |

Reading of the table. A Memory Pool wins specifically when the
application's real request sizes cluster around one or a small number
of fixed sizes and fragmentation-relief or allocation speed genuinely
matters. A workload with genuinely varied sizes fits a general heap
allocator better, and a workload with a genuinely fixed, known set of
objects with no runtime variation at all fits static allocation
better still.

## 13. Related and incompatible patterns

- **Hardware Abstraction Layer.** A memory pool implementation is
  frequently accessed through a hardware abstraction layer's own
  allocation interface, keeping the choice of which pool, or which
  variant, an implementation detail hidden from the code that merely
  requests a block.
- **Ring Buffer.** Both patterns manage a fixed region of memory with
  predictable, bounded behavior, but a ring buffer streams elements
  continuously in a strict order while a memory pool hands out and
  recovers whole, interchangeable blocks in no particular order, a
  genuinely different shape suited to a genuinely different need.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to code currently using a general heap allocator
for objects that are, in practice, one or a few fixed sizes.

1. Measure the real distribution of allocation sizes the application
   actually requests, confirming they genuinely cluster around one or
   a small number of fixed sizes.
2. Choose the fixed block size, or sizes, that cover the real common
   case, per Zephyr's own documented block-size and alignment
   requirements.
3. Replace the general heap allocation and release calls with the
   pool's own allocate and release calls, confirming every allocation
   still has a matching release on every exit path.
4. Confirm, under a real, sustained workload, the pool's block count
   returns to its starting value after every allocate-and-release
   cycle, catching any leaked block before it reaches production.

Removing the pattern when it stops earning its place, most relevant
when the application's real allocation sizes have genuinely grown too
varied for a fixed block size to serve efficiently.

1. Confirm, concretely, that the real request-size distribution has
   genuinely become too varied for the pool's fixed size, rather than
   assuming it has.
2. Move to a general heap allocator, or to several distinct pools at
   different fixed sizes matching the real, now-varied common cases.
3. Confirm the resulting fragmentation behavior, under the
   application's real long-running workload, is genuinely acceptable
   before shipping the change.

## 15. Testing and verification

Easier because of the pattern.

- A test can drive a long, repeated allocate-and-release cycle and
  assert the pool's available-block count returns to its starting
  value every time, directly catching the leaked-block failure mode
  from dimension 11.
- Because every block is the same fixed size, a test can assert a
  request never returns a block smaller than the documented fixed
  size, a simple, deterministic check a general heap allocator's
  variable sizing does not offer.

Harder because of the pattern.

- Confirming the fixed block size genuinely matches the application's
  real request-size distribution needs a test driven by real,
  representative production data, not an assumption about typical
  sizes.
- Verifying the waiting-queue ordering, priority first and then wait
  time, per Zephyr's own documented rule, is genuinely correct under
  real contention needs a test that can drive several competing
  threads at once, not a single-threaded sequence.

Techniques that apply.

- **Leaked-block detection tests.** Drive a long, repeated allocate-
  and-release cycle and assert the pool's available-block count
  returns to its starting value every time.
- **Fixed-size assertion tests.** Assert every block handed out by the
  pool is genuinely the documented fixed size, never smaller.
- **Contention-ordering tests.** Drive several competing threads
  against a pool with fewer blocks than requesters, and assert the
  waiting-queue ordering genuinely matches the documented priority-
  and-wait-time rule.
- **Real-distribution sizing verification.** Confirm the chosen fixed
  block size genuinely matches the application's real, measured
  request-size distribution, not an assumed typical size.

## 16. Observability signals

What to record.

- The pool's current available-block count, sampled over the
  system's real running lifetime, since a steadily declining count
  directly points at the leaked-block failure mode from dimension 11.
- The rate of requests that had to wait for a block to become
  available, since a rising wait rate directly signals the pool is
  undersized for the application's real, current workload.

A healthy state. The available-block count returns to its starting
value after every real allocate-and-release cycle, with no long-term
downward trend, and the wait rate stays low and stable under the
application's real, sustained workload.

A failing state. The available-block count trends steadily downward
over the system's running lifetime, pointing directly at a leaked
block somewhere in the application, or the wait rate rises under a
real, sustained workload, pointing at a pool that is genuinely
undersized for the application's actual needs.

## 17. Security and privacy implications

**A block released back to the pool without its previous contents
being cleared can leak the prior occupant's data to whichever thread
receives that same block next.** Because a pool reuses the exact same
physical memory for every allocation of a given block, a block
released without clearing its contents still holds whatever data the
previous occupant wrote there, and the next thread to receive that
block, whether through the normal free-list handoff or the priority-
ordered waiting-queue handoff described in dimension 7, can read that
stale content directly, a real information-disclosure risk when the
pool is used for objects that may hold sensitive data, such as a
network packet buffer or a credential structure. Clearing a block's
contents before it re-enters the pool's free-block tracking, rather
than only at the moment of the next allocation, is a real, necessary
part of a security-conscious memory pool implementation for any
application handling sensitive data.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. C models the fixed-block, free-list shape directly, the
language most embedded memory pool implementations are actually
written in. Python shows the same conceptual shape using a minimal,
host-testable simulation, the pattern's leaked-block-detection-
testable variant from dimension 15, expressed portably. Swift shows
the same conceptual shape using a minimal model, analogous to how a
native application's own object-reuse pool might track fixed-size
slots. Java, Go, and Rust are omitted, since the pattern's real home
is C and the two languages chosen already cover its production and
its testable-simulation shapes.

### C

```c
#include <stdio.h>
#include <stdint.h>

#define BLOCK_COUNT 4

typedef struct {
    int value;
} block_t;

static block_t pool[BLOCK_COUNT];
static int free_list[BLOCK_COUNT];
static int free_count;

static void pool_init(void) {
    for (int i = 0; i < BLOCK_COUNT; i++) {
        free_list[i] = i;
    }
    free_count = BLOCK_COUNT;
}

static int pool_alloc(void) {
    if (free_count == 0) {
        return -1;
    }
    free_count--;
    return free_list[free_count];
}

static void pool_free(int index) {
    pool[index].value = 0;
    free_list[free_count] = index;
    free_count++;
}

static void print_status(const char *label, int index, int remaining) {
    printf("%s block %d, %d remaining", label, index, remaining);
    putchar(10);
}

int main(void) {
    pool_init();

    int a = pool_alloc();
    int b = pool_alloc();
    print_status("allocated", a, free_count);
    print_status("allocated", b, free_count);

    pool_free(a);
    print_status("released", a, free_count);

    int c = pool_alloc();
    print_status("allocated", c, free_count);

    return 0;
}
```

### Python

```python
from typing import Optional


class MemoryPool:
    def __init__(self, block_count: int):
        self.block_count = block_count
        self.free_list = list(range(block_count))

    def alloc(self) -> Optional[int]:
        if not self.free_list:
            return None
        return self.free_list.pop()

    def free(self, index: int) -> None:
        self.free_list.append(index)

    def available(self) -> int:
        return len(self.free_list)


if __name__ == "__main__":
    pool = MemoryPool(block_count=4)

    a = pool.alloc()
    b = pool.alloc()
    print("allocated blocks", a, "and", b, ",", pool.available(), "remaining")

    if a is not None:
        pool.free(a)
        print("released block", a, ",", pool.available(), "remaining")

    c = pool.alloc()
    print("allocated block", c, ",", pool.available(), "remaining")
```

### Swift

```swift
final class MemoryPool {
    private var freeList: [Int]

    init(blockCount: Int) {
        freeList = Array(0..<blockCount)
    }

    func alloc() -> Int? {
        guard !freeList.isEmpty else {
            return nil
        }
        return freeList.removeLast()
    }

    func free(_ index: Int) {
        freeList.append(index)
    }

    var available: Int {
        freeList.count
    }
}

let pool = MemoryPool(blockCount: 4)

let a = pool.alloc()
let b = pool.alloc()
print("allocated blocks", a as Any, "and", b as Any, ",", pool.available, "remaining")

if let a = a {
    pool.free(a)
    print("released block", a, ",", pool.available, "remaining")
}

let c = pool.alloc()
print("allocated block", c as Any, ",", pool.available, "remaining")
```

## 18. References

1. Zephyr Project. "Memory Slabs".
   https://docs.zephyrproject.org/latest/kernel/memory_management/slabs.html
   Verified 2026-08-21. Source of the memory slab definition,
   fragmentation-relief benefit, block structure, and waiting-queue
   ordering quotes used in dimensions 1, 2, 3, 5, 6, 7, 9, and 10.
2. Zephyr Project. "Memory Blocks Allocator".
   https://docs.zephyrproject.org/latest/kernel/memory_management/sys_mem_blocks.html
   Verified 2026-08-21. Source of the external-bookkeeping variant and
   power-management distinction quotes used in dimensions 4, 8, 9,
   10, and 11.
