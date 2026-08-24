---
name: Copy-on-Write
slug: copy-on-write
family: 09-concurrency
category: Concurrency
aliases: [COW, Clone-on-Write, Lazy Copy]
first_described: "Bell Labs Unix (fork semantics, 1970s); formalized as a general technique across operating systems and languages through the 1980s and 1990s"
maturity: canonical
related: [flyweight, immutable-value-object, memento, prototype, snapshot-isolation, reference-counting]
incompatible_with: [in-place-mutation-with-shared-mutable-state]
verified: 2026-08-14
---

# Copy-on-Write

## 1. Name, aliases, and lineage

The canonical name is Copy-on-Write, almost always abbreviated COW. It is also
called Clone-on-Write in languages whose standard library exposes it as a
named type, and Lazy Copy in older systems literature, because the defining
behaviour is that a copy is deferred until the moment it becomes necessary
rather than performed eagerly at the point where a share of the same data is
requested.

Copy-on-write does not have a single named inventor or a single catalog entry
the way the Gang of Four patterns do. It is an operating-systems technique
first, described as a memory-management optimisation for the Unix `fork`
system call, where a child process is given the illusion of a full copy of the
parent's address space while the kernel actually shares the underlying pages
and duplicates a page only when either process writes to it. The Linux manual
page for `fork(2)` states this plainly in its own words. "Under Linux, fork()
is implemented using copy-on-write pages, so the only penalty that it incurs
is the time and memory required to duplicate the parent's page tables, and to
create a unique task structure for the child" (Linux man-pages project,
`fork(2)`, NOTES section,
https://man7.org/linux/man-pages/man2/fork.2.html, verified 2026-08-14).

From that operating-system origin the same idea was generalised into
programming languages as a value-semantics optimisation. A language or library
that wants to give the programmer the mental model of independent, immutable
values, while an eager deep copy on every assignment or function call would be
too costly, implements its container types with shared internal storage plus a
reference count or uniqueness check, and copies the storage only on the first
write after a share occurred. Rust's standard library formalises this exact
idea as a named type, `std::borrow::Cow`, described in its own documentation
as "a smart pointer providing clone-on-write functionality. it can enclose and
provide immutable access to borrowed data, and clone the data lazily when
mutation or ownership is required" (The Rust Project, `std::borrow::Cow`
documentation, https://doc.rust-lang.org/std/borrow/enum.Cow.html, verified
2026-08-14). Swift's Array and Dictionary types use the same idea without
exposing it as a distinct type, choosing instead to make it an invisible
property of the built-in value types themselves, documented in the standard
library's own source as follows. "Arrays, like all variable-size collections in the
standard library, use copy-on-write optimization. Multiple copies of an array
share the same storage until you modify one of the copies" (Apple Inc., Swift
standard library source, `stdlib/public/core/Array.swift`, doc comment on
`Array`, https://github.com/apple/swift/blob/main/stdlib/public/core/Array.swift,
verified 2026-08-14).

There is a third lineage worth naming separately because it is easy to
conflate with the first two, filesystem and storage-layer copy-on-write, where
a filesystem or a container image layering system treats a block, a file, or a
directory tree the same way, keeping a single physical copy shared between a
base layer and any number of derived layers, and materialising a private copy
of exactly the block or file that is written to. ZFS and Btrfs implement this
at the block level for the whole filesystem. Docker's OverlayFS-based storage
driver implements it at the file level for container images, described in
Docker's own documentation as follows. "Copy-on-write is a strategy of sharing and
copying files for maximum efficiency. If a file or directory exists in a lower
layer within the image, and another layer (including the writable layer)
needs read access to it, it just uses the existing file... The first time
another layer needs to modify the file (when building the image or running
the container), the file is copied into that layer and modified" (Docker
Inc., "Storage drivers", https://docs.docker.com/storage/storagedriver/,
verified 2026-08-14).

All three lineages, operating-system memory pages, language-level container
types, and storage-layer blocks or files, share one structural idea, which is
the definition this entry uses throughout. multiple logical owners reference
one physical copy of data, reads never trigger duplication, and a write
triggers duplication of exactly the granule being written, scoped to the
smallest unit the system tracks (a page, a container, a block, a file).

## 2. Problem and context

The problem copy-on-write solves is a specific tension between two things a
system wants at once, the ability to hand out what looks like an independent
copy of a piece of data cheaply and often, and the actual cost of duplicating
that data, which is proportional to its size and is paid whether or not the
copy is ever mutated.

The context in which this tension becomes acute has three ingredients that
recur across the operating-system, language, and storage lineages described in
dimension 1.

First, sharing is requested far more often than mutation actually happens.
When a process calls `fork`, the overwhelmingly common case historically was
an immediate `exec` that replaced the child's whole address space anyway, so
an eager full copy of the parent's memory was wasted work in the majority of
calls. When a Swift function receives an `Array` parameter and only reads from
it, an eager copy at the call boundary is wasted work. When a container image
is built from a base layer and ninety-nine files out of a hundred are never
touched by the derived layer, an eager copy of the whole image at build time
is wasted work.

Second, the data being shared is large enough, or the sharing frequent enough,
that the cost of copying is measurable against the cost of the operation that
triggers the sharing. A `fork` of a process with a multi-gigabyte heap, an
`Array` passed through several layers of a hot code path, or a multi-gigabyte
container image are all situations where an eager deep copy dominates the
actual work being done.

Third, the language, runtime, or system already has, or can cheaply build, a
mechanism that distinguishes "this piece of data has exactly one owner" from
"this piece of data has more than one owner", because that distinction is what
lets a write decide, at the moment it happens, whether it is safe to mutate in
place or whether it must duplicate first. In an operating system this
mechanism is the page table plus a reference count per physical page. In a
managed language it is a reference count or an object identity check on the
backing storage. In a filesystem it is a block pointer plus a reference count
in the metadata tree.

Where these three ingredients are present, copy-on-write turns an operation
whose cost is proportional to the size of the shared data into an operation
whose cost is proportional to the size of the write, amortised across however
many reads happened before the write. Where any of the three is absent, for
example when mutation is the common case rather than the rare case, the
technique adds overhead (the reference-count check on every access) without
recovering the saving it exists to provide.

## 3. Forces

The pattern balances the following competing pressures.

- **Memory and I/O cost versus latency of the sharing operation.** Favours
  keeping the sharing operation (fork, assignment, layer creation) fast and
  cheap, at the cost of adding a small, constant check on every subsequent
  access to the shared data.
- **Predictability of latency.** Sacrificed at the tail. Most writes are cheap,
  but the first write after a wide sharing event pays for the whole
  duplication in one step, which can show up as a latency spike exactly at
  the moment least convenient for the caller, for example the first mutating
  operation on a very large array that was just passed through several
  function calls.
- **Isolation guarantees.** Favoured. Two logical owners of copy-on-write data
  can never observe each other's writes, because a write always privatises its
  own copy first. This is a strictly stronger isolation guarantee than shared
  mutable state protected only by a lock, and it is the property that lets
  `fork` be safe without the child and parent needing to coordinate at all.
- **Space overhead per owner.** Favoured while unmodified, sacrificed once
  modified. Ten unmodified copies of a large array cost the same memory as
  one. Ten independently modified copies eventually cost the same memory as
  ten separate arrays would have, because each write privatises its own
  granule.
- **Complexity of the reference-tracking mechanism.** Sacrificed. The
  technique is only as sound as its uniqueness or reference-count check.
  Getting that check wrong, described in dimension 11, produces either data
  corruption (a mutation observed by an owner who did not request it) or a
  correctness stall (a copy made every single time because the check can
  never prove uniqueness).
- **Concurrency model fit.** Favoured for reader-heavy, writer-rare workloads
  under a single mutator per copy. Sacrificed, or requires an entirely
  different mechanism (an atomic pointer swap plus epoch reclamation, see
  dimension 13), when many threads must mutate logically-shared state
  concurrently, because the reference count or uniqueness check itself becomes
  a point of contention.
- **Debuggability.** Sacrificed mildly. Because the duplication is invisible
  at the call site, a profiler or a debugger session is usually the only way
  to see that a particular line triggered a multi-megabyte copy, whereas an
  explicit `.clone()` call at least names the cost in the source.

Copy-on-write is not free of cost, it relocates the cost from every share to
the first write after every share, and bets that writes are rarer than shares.
Where that bet is wrong the technique is a net loss.

## 4. Applicability and non-applicability

Reach for copy-on-write when the following hold.

- Sharing (assignment, function parameter passing, process creation, layer
  derivation) happens far more often than mutation of the shared data.
- The data being shared is large enough, or shared often enough, that an
  eager copy at the sharing point would be a measurable cost against the
  operation triggering the share.
- The runtime or system already provides, or can cheaply add, a reliable
  way to distinguish a uniquely-owned copy from a shared one, whether that is
  a reference count, an object identity check, or a page-table entry.
- Readers vastly outnumber writers, and no writer needs to observe another
  writer's in-flight mutation, meaning full snapshot isolation between
  logical owners is actually the guarantee wanted, not an accidental side
  effect to work around.
- The unit of copying can be made small relative to the unit of sharing, so a
  single write does not force duplication of far more data than the write
  actually touches. This is why `fork` copies at the page granularity rather
  than the whole address space at once, and why Docker's layered filesystem
  copies at the file granularity rather than the whole image.

Do NOT reach for copy-on-write in these cases, and the reason matters more
than the rule.

- **Mutation is the common case, not the rare case.** If most owners of a
  shared value are going to write to it shortly after acquiring it, the
  reference-count check pays for itself on every single access and the
  privatising copy happens almost every time anyway, so the technique adds
  overhead with none of its benefit realised. A value type with eager,
  unconditional copying, or a genuinely mutable shared structure protected by
  a lock or an actor, is the honest shape here.
- **Multiple threads need to mutate logically-shared state concurrently, in
  place, and observe each other's writes.** Copy-on-write privatises on
  write, which is the opposite of what a shared mutable counter, a shared
  cache being updated by many workers, or a producer-consumer queue needs.
  Reach for a lock, an atomic type, or a lock-free structure designed for
  concurrent mutation instead, see dimension 13.
- **The reference-tracking mechanism cannot be made reliable in the language
  or runtime being used.** A hand-rolled reference count in a language
  without deterministic destruction, or a uniqueness check that can be fooled
  by an alias the tracking mechanism does not see (a raw pointer taken to the
  backing storage, an unsafe cast, a foreign-function-interface boundary that
  hands out the buffer address), will silently corrupt data the first time
  two owners believe they hold private copies but actually share storage.
  This is the failure mode in dimension 11 that has caused real production
  incidents.
- **The data is small.** Below some size that depends on the language and
  allocator, an eager copy is cheaper than the bookkeeping copy-on-write
  requires. Swift's own `Array` implementation still eagerly copies small
  fixed arrays inline in some contexts precisely because the reference-count
  machinery is not free. A four-element tuple does not need copy-on-write.
- **Determinism of latency matters more than average throughput.** A
  real-time audio callback, a hard-deadline control loop, or any code path
  where an unpredictable multi-millisecond copy on the first write after a
  share is unacceptable should avoid copy-on-write collections and use a
  structure whose worst case is bounded and known ahead of time.
- **The system already has an immutable persistent data structure available**
  (a persistent vector, a hash array mapped trie) that shares structure
  between versions without any privatise-on-write step at all, because every
  version is genuinely immutable rather than merely deferred-copy. Where that
  is available and the workload needs many long-lived versions rather than a
  single mutable value with occasional sharing, a persistent data structure
  is usually the better fit, see dimension 13.

## 5. Structure

Four participants, named by the role they play. The names below are the
generic roles; dimension 8 shows how each language lineage names them
concretely.

- **Value (or Shared Storage).** The actual data being protected, an array's
  backing buffer, a process's memory page, a file inside a container layer.
  It exists exactly once in physical memory or on disk at any given time,
  regardless of how many logical owners reference it.
- **Owner (or Handle).** The thing a caller actually holds, an `Array`
  variable, a process's page-table entry, a container layer's file-system
  view. Every Owner points at the same Value until a write forces a split.
- **Reference Tracker.** The mechanism that answers whether a Value currently
  has more than one Owner. This is a reference count (Swift's
  `isKnownUniquelyReferenced`, an operating system's per-page reference
  count), or an explicit enum discriminant (Rust's `Cow<Borrowed, Owned>`), or
  a layer-membership check (a filesystem's block pointer plus a dirty bit).
- **Write Gate.** The code path every mutating operation passes through
  before it touches the Value. The Write Gate consults the Reference Tracker.
  if the Value is uniquely owned it mutates in place, and if the Value is
  shared it first allocates a private duplicate, retargets the Owner at the
  duplicate, decrements the tracker on the old Value, and only then performs
  the mutation on the new, now uniquely-owned copy.

The critical structural property is that the Write Gate is the ONLY path
allowed to mutate the Value. Any code that reaches the Value through a
back-channel that bypasses the Write Gate, an unsafe pointer, a raw buffer
handed to a foreign function, a debugger poking memory directly, breaks the
guarantee the whole pattern exists to provide, because the Reference Tracker
was never consulted.

## 6. ASCII structure diagram

```
   Before any write, two Owners share one Value:

   +-----------+          +-----------------------------+
   |  OwnerA   | -------> |          Value               |
   +-----------+          |  (backing storage / page /   |
                           |   file, refcount = 2)        |
   +-----------+          +-----------------------------+
   |  OwnerB   | -------------------^
   +-----------+

   OwnerB performs a mutating operation, hitting the Write Gate:

   +-----------+          +-----------------------------+
   |  OwnerA   | -------> |          Value               |
   +-----------+          |   (original, refcount = 1)   |
                           +-----------------------------+
   +-----------+          +-----------------------------+
   |  OwnerB   | -------> |       Value' (private copy)  |
   +-----------+          |     (mutated, refcount = 1)  |
                           +-----------------------------+

              +------------------------+
              |      Write Gate        |
              |------------------------|
              | if refcount(Value) > 1 |
              |     Value' = copy(V)   |
              |     OwnerB -> Value'   |
              |     refcount(V) -= 1   |
              | mutate(OwnerB.target)  |
              +------------------------+
```

## 7. Dynamics

The runtime flow has one property worth stating plainly, mirrored across all
three lineages. the check-then-copy-then-mutate sequence happens entirely
inside the write operation itself, invisibly to the caller, and a read never
triggers it at all.

```
Caller A          Caller B         Write Gate           Reference Tracker      Value
   |                  |                  |                      |                |
   |-- assign a = b -------------------->|                      |                |
   |                  |                  |-- increment refcount --------------->|
   |                  |                  |<-- refcount now 2 --------------------|
   |                  |                  |                      |                |
   |-- read a[0] --------------------------------------------------------------->|
   |<-- value (no copy, no gate involved) -----------------------------------------|
   |                  |                  |                      |                |
   |                  |-- b.append(x) -->|                      |                |
   |                  |                  |-- check refcount --->|                |
   |                  |                  |<-- refcount is 2 -----|                |
   |                  |                  |-- allocate Value' -------------------->|
   |                  |                  |-- copy contents of Value into Value'   |
   |                  |                  |-- decrement refcount(Value) --------->|
   |                  |                  |-- retarget b -> Value'                |
   |                  |                  |-- append x to Value'                  |
   |                  |<-- returns ------|                      |                |
   |                  |                  |                      |                |
   |-- read a[0] --------------------------------------------------------------->|
   |<-- unchanged, still points at original Value ---------------------------------|
```

Two timing notes carry across every lineage. First, the privatising copy is
paid exactly once per divergence, on the FIRST write after a share, never on
every subsequent write from the same owner, because after the copy that
owner's Value has a reference count of one and every later write takes the
cheap in-place path through the Write Gate. Second, the cost of the copy is
proportional to the size of the Value at the moment of the first write, not
to the number of writes that follow, which is why a caller who is about to
perform many small mutations on data it just received as a shared parameter
sometimes benefits from forcing the privatising copy once, explicitly, up
front, rather than letting the first of many small mutations pay for it as a
surprise.

## 8. Implementation variants

**Reference-counted backing storage with a language-native uniqueness check
(Swift, and similar approaches in other managed languages).** Every
copy-on-write value type wraps a single reference to a heap-allocated buffer.
The Write Gate is implemented with a language primitive,
`isKnownUniquelyReferenced`, that answers the reference-count question in
constant time using the retain count Automatic Reference Counting already
maintains, so no separate bookkeeping structure is needed. This is the
cheapest variant to build on top of an existing ARC or GC runtime because the
reference count already exists for memory-management purposes and copy-on-write
piggybacks on it.

**Explicit two-state enum (Rust's `Cow<'a, B>`).** Rather than hiding the
state behind a hidden reference count, the type itself is one of two named
variants, `Borrowed(&'a B)` or `Owned(<B as ToOwned>::Owned)`, and the
compiler's borrow checker, not a runtime reference count, is what guarantees
the borrowed variant cannot outlive its source. `to_mut()` is the Write Gate.
called on a `Borrowed` value it clones into an `Owned` value and returns a
mutable reference to it, called on an already-`Owned` value it returns the
mutable reference directly with no copy. This variant trades runtime
reference counting for a compile-time proof, at the cost of the type being
visible in every function signature that uses it, which some callers read as
API friction and others read as honest documentation of the cost model.

**Kernel page-table copy-on-write (POSIX `fork`, and similarly `mmap` with
`MAP_PRIVATE`).** The Value is a physical memory page, the Reference Tracker
is the page's reference count in the kernel's physical memory manager, and
the Write Gate is a hardware page-fault trap. the page table entry is marked
read-only for both processes after `fork`, so any write by either process
faults into the kernel, which then allocates a fresh physical page, copies
the faulting page's contents into it, updates that process's page table entry
to point at the new page and mark it writable, and resumes the faulting
instruction. This variant is the only one on this list where the Write Gate
is enforced by hardware (the MMU) rather than by software convention, which
is what makes it safe even against a process that has no cooperation with the
mechanism at all.

**Layered filesystem copy-on-write (OverlayFS, ZFS, Btrfs).** The Value is a
block, or in OverlayFS's case a whole file, the Reference Tracker is metadata
in the filesystem's own block-pointer tree recording which layer or snapshot
owns which physical block, and the Write Gate is the filesystem driver's
write path, which performs a "copy up" of the entire file (OverlayFS) or
allocates a new block and rewrites the pointer tree (ZFS, Btrfs) rather than
overwriting the physical block that an earlier snapshot still references.
This variant is unusual among the four in that the unit of copying is
sometimes coarser than the unit of the write, OverlayFS specifically copies
the entire file up on the first byte written, which is a real cost worth
knowing before choosing it for workloads that make small writes to very large
files, see dimension 11.

**Structural sharing without any privatising copy at all (persistent data
structures).** Not strictly copy-on-write by this entry's definition, but
close enough in intent that it is worth distinguishing precisely because it
is so often confused with it, see dimension 13. A persistent vector or hash
array mapped trie shares tree nodes between an old version and a new version,
and a write allocates only the path of nodes from the root to the changed
leaf, never a full copy of the whole structure and never a mutation of a
node another version can still see. There is no Reference Tracker asking
whether it is unique, because nothing is ever mutated in place, every
version is permanently, genuinely immutable.

**Manual copy-on-write with a hand-rolled reference count (C and C++ prior to
smart pointers, or any language without a language-provided uniqueness check,
notably the classic `std::string` implementations some early C++ standard
libraries shipped before the C++11 standard effectively outlawed the
technique for `std::string`, see dimension 11).** The programmer implements
the Reference Tracker and Write Gate by hand, which is the highest-risk
variant on this list because every access site must correctly go through the
Write Gate for the guarantee to hold, and a single raw pointer taken to the
underlying buffer, common in C interop, silently defeats the whole mechanism.

## 9. Known production uses

**Linux `fork(2)`, kernel page-table copy-on-write.** Every `fork` call on
Linux gives the child process a page-table copy of the parent's address space
with every page marked read-only and shared, and a page is duplicated only
when either process writes to it. Linux man-pages project, `fork(2)`, NOTES
section, https://man7.org/linux/man-pages/man2/fork.2.html, verified
2026-08-14.

**Rust standard library, `std::borrow::Cow`.** Used throughout the Rust
ecosystem anywhere a function wants to accept either a borrowed reference or
an owned value and defer allocation until a caller actually needs to mutate
or take ownership of the result, documented as a smart pointer providing
clone-on-write functionality that can enclose and provide immutable access to
borrowed data, and clone the data lazily when mutation or ownership is
required. The Rust Project, `std::borrow::Cow` documentation,
https://doc.rust-lang.org/std/borrow/enum.Cow.html, verified 2026-08-14.

**Redis RDB and AOF persistence, fork-based snapshotting.** Redis performs
point-in-time snapshots by calling `fork()` and letting the child process
write the dataset to disk while the parent keeps serving clients, explicitly
relying on the operating system's copy-on-write to avoid duplicating the
whole in-memory dataset up front. Redis forks, giving a child and a parent
process, the child starts writing the dataset to a temporary RDB file, and
this method allows Redis to benefit from copy-on-write semantics. Redis Ltd.,
"Redis persistence", section "Snapshotting", "How it works",
https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/,
verified 2026-08-14.

**Swift standard library, `Array` and `Dictionary`.** Every value-type
collection in the Swift standard library is implemented with copy-on-write
backing storage so that assignment and function-parameter passing are cheap
reference copies, and a private copy is made only on the first mutating
operation after a share. Arrays, like all variable-size collections in the
standard library, use copy-on-write optimization, and multiple copies of an
array share the same storage until one copy is modified. Apple Inc., Swift
standard library source, `stdlib/public/core/Array.swift`, doc comment on
`Array`,
https://github.com/apple/swift/blob/main/stdlib/public/core/Array.swift,
verified 2026-08-14.

**Docker's `overlay2` storage driver.** Container image layers are stacked
read-only filesystems, and a container's writable layer shares every file
with the layers beneath it until the container actually writes to a file, at
which point the driver performs a "copy up" of that one file into the
writable layer. Copy-on-write is a strategy of sharing and copying files for
maximum efficiency, and the first time another layer needs to modify a file,
the file is copied into that layer and modified. Docker Inc., "Storage
drivers", https://docs.docker.com/storage/storagedriver/, verified
2026-08-14.

## 10. Consequences

Positive.

- Sharing (assignment, parameter passing, process creation, layer derivation)
  becomes a cheap, constant-time operation regardless of the size of the
  underlying data, because it only ever manipulates a reference and a count.
- Read access has zero copy-on-write overhead beyond, at most, a reference
  bump, since reads never consult the Write Gate at all.
- Multiple owners are given full snapshot isolation from each other's writes
  without needing a lock, a critical section, or any coordination protocol,
  which is precisely why `fork` can be safe with no cooperation from the
  child process at all.
- Memory or storage that would otherwise be duplicated stays shared for as
  long as it remains unmodified, which for read-mostly workloads can be the
  large majority of the data's lifetime.
- The cost of a copy is paid exactly once per divergence and amortised across
  every subsequent operation on the now-privately-owned copy, rather than
  being paid on every operation the way a naive "always copy on read too"
  scheme would.

Negative.

- The cost of the first write after a wide share is a latency spike whose
  size is proportional to the size of the shared data, and that spike is
  invisible at the call site, making it a common source of "this one call is
  mysteriously slow sometimes" bug reports.
- The reference-tracking mechanism must be correct and must see every path
  that could mutate the Value, or the guarantee silently fails and two owners
  who both believe they hold private data actually share it, see dimension
  11.
- Under concurrent access from multiple threads, the Reference Tracker itself
  becomes contended, and naive implementations can produce a race between the
  uniqueness check and the mutation that follows it, described in dimension
  11 as the classic C++ `std::string` COW race.
- Total memory or storage usage after many independent writes converges to
  the same cost as if the data had never been shared at all, so
  copy-on-write is a latency and throughput optimisation for the sharing
  phase, not a permanent memory-saving strategy for a workload that mutates
  most of its shared copies.
- Debugging and profiling require specific tooling awareness, because a stack
  trace showing time spent "inside array append" does not, on its own, reveal
  that the real cost was an implicit multi-megabyte copy rather than the
  append itself.

## 11. Failure modes and misuse

**The classic C++ `std::string` copy-on-write data race.** Symptom. A
multi-threaded C++ program built against a pre-C++11 standard library whose
`std::string` used reference-counted copy-on-write storage would occasionally
produce corrupted string contents or crashes under concurrent read access
from multiple threads, with no thread ever calling a mutating method. Cause.
Even a `const` accessor like `operator[]` on a non-const string had to be
able to return a mutable reference for API compatibility, so it went through
the Write Gate and touched the reference count, and two threads calling that
accessor concurrently on copies sharing one buffer could race on the
reference-count increment or on the check-then-copy sequence itself, without
either thread doing anything the language considered a mutation. Fix. The
C++11 standard added the requirement that `std::string`'s internal
representation is contiguous and, in effect, outlawed reference-counted
copy-on-write implementations of `std::string`, forcing standard library
vendors including `libstdc++` to move to small-string-optimisation, eager
storage instead. The general lesson for any hand-rolled variant. a Write Gate
that can be reached by an operation the type system calls "read-only" is not
actually a Write Gate, and the fix is either to make the reference count
itself atomic and lock-free correctly, or to abandon copy-on-write for that
type under concurrency and use immutable, genuinely shared, or thread-local
storage instead.

**A bypassed reference count via an unsafe alias.** Symptom. A mutation
through one owner is unexpectedly observed by a second owner that believed it
held an independent copy, producing data corruption that reproduces
intermittently and only under specific call patterns. Cause. Some code path
took a raw pointer, an unsafe buffer, or a foreign-function-interface handle
to the Value's backing storage without going through the language's normal
retain or borrow machinery, so the Reference Tracker never learned that a
second owner existed, and the Write Gate mutated in place believing itself
unique. Fix. Audit every place the backing storage is exposed outside the
type's own API (`withUnsafeBufferPointer` in Swift, `as_ptr()` in Rust, a raw
buffer handed across a C boundary) and confirm the exposure is scoped so the
alias cannot outlive the call that requested it, or force an explicit private
copy before handing out the raw pointer at all.

**The surprise-latency-spike production incident.** Symptom. A request
handler that was fast in every load test suddenly takes ten to a hundred
times longer under real production traffic, with the slow path traced to one
specific line performing what looks like a trivial single-element mutation
on a collection. Cause. The collection had been passed through several
layers of shared, cached, or memoised state before reaching the handler, so
its reference count was far above one, and the "trivial" mutation was
actually the first write since that wide sharing, forcing a full privatising
copy of a collection whose size the load test's synthetic data never
approached. Fix. Either restructure the hot path to mutate a build-once,
mutate-locally value that never gets shared before its mutation phase ends,
or force the copy explicitly and early, outside the latency-sensitive
section, so the cost is visible and predictable rather than hidden inside an
innocuous-looking append.

**OverlayFS "copy up" amplification on large files.** Symptom. A container
workload that writes a single byte to a large file inside its writable layer
takes much longer, and consumes far more disk I/O, than the size of the
write would suggest, and this gets worse the larger the base image's file is.
Cause. OverlayFS's Write Gate copies the ENTIRE file up into the writable
layer on the first write, not just the modified byte range, so a one-byte
write to a multi-gigabyte file triggered a multi-gigabyte copy operation.
Fix. Keep large, frequently-written files (databases, log files, caches) on a
bind-mounted volume outside the layered image filesystem entirely, rather
than inside a path that lives in a lower image layer, so the write path never
touches the copy-on-write layering mechanism at all.

**Confusing copy-on-write with true immutability, and mutating the "shared"
copy anyway.** Symptom. A caller receives what it believes is an independent
snapshot, mutates it as if that were safe, and a second caller sharing the
same underlying value observes the mutation because the language's
copy-on-write mechanism was never actually triggered, most often because the
mutation went through an in-place, non-Write-Gated API on the same object
rather than through an operation the type's copy-on-write machinery
recognises as mutating. Cause. Treating "this collection type is
copy-on-write" as a blanket guarantee that ANY operation on it is safe to
perform concurrently or without further thought, rather than understanding
that the guarantee only holds for operations that correctly route through
the type's own Write Gate. Fix. Read the actual API surface of the
copy-on-write type in use and confirm which operations are documented as
mutating (and therefore Write-Gated) versus which return a new value or
operate through an escape hatch that bypasses the mechanism.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Copy-on-Write | Eager (defensive) deep copy | Lock-protected shared mutable state | Persistent (structurally shared) data structure | Immutable value with explicit `.clone()` |
|---|---|---|---|---|---|
| Cost of sharing (assign, pass, fork) | Constant time, cheap | Proportional to data size, paid every time | Constant time, but requires acquiring a lock to read safely in the general case | Constant time, cheap | Constant time, but every subsequent independent-mutation intent needs an explicit clone |
| Cost of first write after a share | Proportional to data size, paid once per divergence | Already paid at share time, so writes are always cheap afterward | Constant, but contends with every other reader and writer for the lock | Proportional only to the changed path, not the whole structure | Proportional to data size, paid at the explicit clone call |
| Isolation between owners | Full, automatic, no coordination needed | Full, automatic, no coordination needed | None by default; correctness depends entirely on correct lock discipline | Full, automatic, and permanent since nothing is ever mutated in place | Full once cloned, but only if the clone actually happened before divergence |
| Concurrent multi-writer mutation of the same logical value | Poor fit; each writer privatises its own copy rather than merging | Poor fit for the same reason | Designed for exactly this | Poor fit; designed for many read-only versions, not concurrent in-place writers | Poor fit; same as copy-on-write without even the automatic privatisation |
| Cost visibility at the call site | Hidden; the copy happens inside an innocuous-looking mutating call | Visible; the copy is exactly where the assignment or pass happens | Visible as a lock acquisition, but contention cost is not visible | Hidden inside the structure's own mutating operations, though the cost is smaller | Visible; the `.clone()` call names the cost explicitly |
| Memory cost with many independently-mutated copies | Converges to the same total as if never shared | Already at that total from the start | One shared copy always, by construction | Lower than either, because unchanged parts of the structure remain shared forever | Converges to the same total as if never shared, same as COW |
| Correctness risk from implementation bugs | High if the reference tracker can be bypassed (dimension 11) | Low; there is no hidden sharing to get wrong | High if lock discipline is violated (missed lock, wrong lock, lock ordering deadlock) | Low; correctness follows from genuine immutability rather than a runtime check | Low; correctness follows from the clone happening, which is visible in the source |

Reading of the table. copy-on-write wins specifically in the reader-heavy,
occasional-writer, single-mutator-per-copy regime, which is exactly the
regime `fork`, Swift's collections, Rust's `Cow`, and container image layers
all sit in. A lock-protected shared mutable structure wins the moment more
than one thread must genuinely mutate the same logical value and observe
each other's writes. A persistent data structure wins when the workload
needs to hold on to many long-lived versions simultaneously, where
copy-on-write's all-or-nothing privatisation would end up duplicating data
that a structurally-shared tree would have kept shared indefinitely.

## 13. Related and incompatible patterns

- **Flyweight.** A close cousin at the structural level. both share one
  physical instance across many logical references to cut memory or
  allocation cost. The distinction is what happens on divergence. A Flyweight
  is shared because it is treated as permanently immutable by contract, with
  no privatising path at all, while a copy-on-write value expects to diverge
  eventually and has a defined Write Gate for exactly that moment.
- **Prototype.** A superficial resemblance and a real difference. Prototype
  is about cloning an object as a way to construct a new one, with the clone
  always happening eagerly and explicitly at the point the pattern is
  invoked. Copy-on-write defers that same clone until a write actually
  occurs, and never clones at all if one never does.
- **Immutable Value Object.** The foundation copy-on-write is usually built on
  top of. A copy-on-write type presents the external API contract of an
  immutable value (equality by content, no observable aliasing) while
  internally optimising the implementation with mutable, shared, reference-
  counted storage. Where a language or library can afford true, permanent
  immutability instead, that is the simpler and safer choice; copy-on-write
  earns its place specifically where mutation is occasionally needed but
  should still behave, from the outside, like value semantics.
- **Persistent data structure (structural sharing).** A genuine alternative,
  not a synonym, despite the frequent confusion. A persistent vector or hash
  array mapped trie never mutates a node in place at all, it always allocates
  a new path from the root to the changed leaf and lets old and new versions
  share every untouched node forever. There is no Reference Tracker asking
  whether it is unique, because nothing is ever mutated once created. Reach
  for a persistent data structure instead of copy-on-write when the workload
  needs many simultaneously-live versions of a large structure with small,
  frequent edits between them, since copy-on-write's all-or-nothing
  privatisation on first write would duplicate far more than a
  structurally-shared tree needs to.
- **Snapshot Isolation (databases).** The same idea at the transaction level.
  A database using snapshot isolation gives every transaction a
  copy-on-write view of the data as it existed at the transaction's start,
  and a writing transaction creates a new version of exactly the rows it
  touches rather than locking the whole table, which is structurally the
  same trade-off as language-level copy-on-write, applied to rows and
  multi-version concurrency control instead of pages or array buffers.
- **Reference counting.** A supporting mechanism, not a competing pattern.
  Copy-on-write's Reference Tracker is very often implemented as, or built on
  top of, ordinary reference counting, so the two are usually found together
  rather than as alternatives to choose between.
- **Lock-protected shared mutable state.** Incompatible in intent, not merely
  a different trade-off. Copy-on-write exists specifically to avoid needing a
  lock for the common read-mostly case; introducing a lock around
  copy-on-write data to permit true concurrent in-place mutation defeats the
  point of choosing copy-on-write in the first place, and signals the
  workload has moved out of copy-on-write's applicable regime, see dimension
  4.

## 14. Refactoring path in and out

Introducing the pattern into code that currently performs eager, defensive
deep copies at every share point. Ordered steps.

1. Find every place the data is copied "just to be safe" at an assignment or
   a function-parameter boundary, and confirm the copy is genuinely there for
   isolation (preventing one owner's later mutation from being observed by
   another) rather than for some other reason such as normalising a format.
2. Confirm the three ingredients from dimension 2 actually hold for this
   data. sharing happens far more often than mutation, the data is large
   enough for the copy cost to matter, and the language or runtime already
   provides, or can cheaply add, a uniqueness check.
3. Introduce a reference-counted (or borrow-checked, in Rust) backing storage
   type that wraps the data, with the public API unchanged so callers cannot
   tell the difference from the outside yet.
4. Route every mutating method through a single Write Gate function that
   checks uniqueness first and privatises the backing storage before mutating
   if the check fails. Do this for one mutating method at a time, running the
   full test suite after each, since a missed mutating path is exactly the
   failure mode in dimension 11.
5. Replace every eager copy found in step 1 with a plain reference assignment
   now that the type itself guarantees isolation. Run the tests after each
   site, watching specifically for a test that depended on the old eager
   copy's timing (a test that mutated one copy and asserted the other was
   unaffected should still pass, since that is exactly the guarantee
   copy-on-write provides; a test that somehow depended on the copy
   happening at share time rather than at write time is a sign the eager
   copy was hiding a real ordering bug).
6. Audit every place the backing storage's raw pointer or buffer is exposed
   outside the type's own API and either remove the exposure or scope it so
   an alias cannot outlive the call that requested it, closing the bypass
   failure mode from dimension 11 before it can occur.
7. If the workload is concurrent, confirm the Reference Tracker's
   increment, decrement, and check-then-copy sequence is genuinely atomic
   under the concurrency model in use, per the C++ `std::string` lesson in
   dimension 11, or restrict the type to single-threaded use with an explicit
   annotation the compiler or a linter can check.

Removing the pattern when it stops earning its place. Signals that it should
go include a profiler consistently showing time spent inside the Write Gate's
privatising copy rather than in the mutation itself, meaning the writes are
no longer the rare case, or a growing number of workarounds where callers
force an early copy to avoid the surprise-latency-spike failure mode from
dimension 11.

1. Measure, with a profiler, what fraction of calls into the Write Gate
   actually take the privatising-copy branch versus the cheap in-place
   branch. A high fraction confirms mutation has become the common case.
2. Replace the copy-on-write backing storage with either eager, unconditional
   copying (if isolation is still needed and mutation is now dominant) or a
   directly, openly mutable shared structure behind an explicit lock or actor
   (if concurrent mutation with observation is actually what the workload
   needs).
3. Delete the Reference Tracker and Write Gate machinery. This removes the
   invisible-cost problem from dimension 10 by making the cost model explicit
   again, either "always pay the copy" or "always pay the lock", both of
   which are easier to reason about than "usually free, sometimes an
   unpredictable spike".
4. Re-run the full test suite, paying particular attention to any test that
   was implicitly relying on copy-on-write's isolation guarantee, since a
   naive lock-protected replacement does not provide the same automatic
   snapshot isolation and those tests may need to change from "assert the
   other copy is unaffected" to "assert the lock correctly serialised the
   two operations".

## 15. Testing and verification

Easier because of the pattern.

- Isolation between owners is trivially testable and, when the mechanism is
  correct, always passes. mutate one copy, assert the other is unchanged.
  This is the single most valuable test to write for any copy-on-write type,
  because it is exactly the property the failure modes in dimension 11
  violate when the mechanism is broken.
- Reads require no synchronisation to test concurrently, since copy-on-write
  types are safe for concurrent read access by construction, so a
  stress test that spawns many reader threads against one shared value needs
  no locking in the test itself.

Harder because of the pattern.

- Whether a specific call triggered a privatising copy is invisible from the
  return value alone, so asserting "this operation did not allocate" requires
  either a language-specific allocation-tracking facility or an explicit
  uniqueness check exposed for testing purposes (Swift's
  `isKnownUniquelyReferenced` can be called directly in a test).
- A bug from dimension 11's "bypassed reference count via an unsafe alias"
  failure mode is inherently non-deterministic in a garbage-collected or
  reference-counted language, because it depends on the exact moment an
  unsafe alias outlives its intended scope, which can differ between test
  runs and between debug and optimised builds.

Techniques that apply.

- **The mutate-one-assert-the-other-unaffected test**, described above, run
  for every mutating method the type exposes, not just the obvious ones.
  Every method that CAN mutate needs this test, because a single method that
  forgot to route through the Write Gate is exactly how the pattern silently
  breaks.
- **An explicit no-copy assertion using the language's own uniqueness
  primitive.** Where the language exposes one, call it directly in a test
  after a share to assert the reference count is genuinely above one, and
  again after a mutation to assert it has dropped back to one, proving the
  privatisation actually happened rather than merely trusting that it did.
- **Fuzzing the alias-exposure surface.** For types that expose an unsafe
  buffer or raw pointer accessor, a targeted test that deliberately holds
  the raw pointer past the scope the API intends, then triggers a mutation
  through the normal API, is the most direct way to reproduce the bypass
  failure mode from dimension 11 in a controlled setting rather than waiting
  for it to appear in production.
- **A benchmark, not just a correctness test, for the privatising-copy
  cost.** Because the cost of the Write Gate's copy branch is exactly the
  thing that produces the surprise-latency-spike failure mode, a
  microbenchmark that measures the cost of a mutation after a share, against
  the cost of a mutation with no prior share, quantifies the spike ahead of
  it showing up in production traffic.

## 16. Observability signals

The pattern hides the privatising copy from the call site, so the copy has to
appear in telemetry or nobody can diagnose an unexplained latency spike.

What to record.

- A counter of Write Gate invocations that took the privatising-copy branch,
  labelled by the call site or the type involved where the language or
  runtime allows attributing the copy to a source location. This is the
  single most useful signal, because its rate directly answers whether
  mutation is becoming the common case, which is the exact question
  dimension 14's removal criteria depend on.
- A histogram of the size of data copied by the Write Gate, since the cost of
  each individual copy is proportional to size, and the histogram reveals
  whether the copies triggering are small and cheap or occasionally very
  large.
- At the operating-system level, for `fork`-based systems specifically, the
  page-fault rate attributable to copy-on-write faults (visible via
  `/proc/<pid>/stat` minor fault counters on Linux, or equivalent platform
  tooling), which tells an operator how much of a forked child's early
  runtime is being spent materialising private pages rather than doing real
  work.
- For storage-layer copy-on-write, a counter of "copy up" operations and the
  total bytes copied up, since a single unexpectedly large copy-up (the
  OverlayFS failure mode from dimension 11) is directly visible as a spike in
  this metric.

A healthy instance on a dashboard. The privatising-copy rate is low and
roughly proportional to the actual rate of first-writes-after-a-share the
workload is expected to perform, and the size histogram is dominated by
small, cheap copies consistent with the data the system normally handles.

A failing instance. The privatising-copy rate climbs steadily over time with
no matching change in workload shape, which usually means a caching layer or
memoisation table upstream started sharing the same value more widely than
before, so every write downstream now diverges from a larger and larger
number of prior owners. Or the size histogram develops a heavy tail on one
specific call site, localising exactly which operation is paying the
surprise-latency-spike cost from dimension 11 without needing to read any
code. Or, for the OverlayFS variant specifically, the bytes-copied-up metric
shows large copy-up events correlated with a specific container image or
file, which localises the file that needs to move to a bind-mounted volume.

## 17. Security and privacy implications

Judgement. this dimension is largely analytical reasoning about attack
surface rather than sourced facts, since copy-on-write's security
implications are not the subject of a dedicated specification the way its
memory-sharing behaviour is.

Copy-on-write's core guarantee, that a write is invisible to other owners
until it happens and privatises its own copy, is itself a useful security
property in one direction. it prevents an accidental cross-tenant or
cross-request data leak through shared mutable state, because there is no
shared mutable state to leak through once the copy has occurred. This is part
of why `fork`-based process isolation is a reasonable building block for
privilege separation, a parent process can hand a child a copy-on-write view
of its memory without granting the child any ability to corrupt the parent's
live state.

The reverse direction carries the real risk, and it recurs across all three
lineages. Because copy-on-write is an optimisation implemented BELOW the
language or API's visible contract, an attacker or a bug that can reach the
underlying shared storage through a side channel the Reference Tracker does
not see, exactly the bypass failure mode described in dimension 11, gains
either an information-disclosure primitive (reading a "private" copy that is
still, unbeknownst to the victim, aliased to attacker-influenced storage) or
a data-integrity primitive (corrupting one owner's data through a write the
owner never made and never authorised). This is the class of bug the
`std::string` COW race belonged to, and while that specific historical
example was a correctness bug rather than a demonstrated exploit, the same
shape, a Write Gate reachable through a path the type system did not classify
as mutating, is the pattern worth auditing for in any hand-rolled variant.

At the operating-system layer, `fork`'s copy-on-write memory sharing has been
the substrate for a specific, well-documented class of side-channel research
across the industry. because copy-on-write pages between a parent and a
forked child, or between two processes sharing a page through deduplication
mechanisms built on the same underlying idea (memory deduplication features
that merge identical pages across unrelated processes to save memory), remain
physically the same page until one side writes, the TIMING of a write
(whether it triggers a page fault and duplication, or completes immediately
because the page was already private) can leak information about whether
another process holds an identical page, which some research communities have
used as a covert channel or a Rowhammer-adjacent bit-flip target. This is a
property of memory deduplication and copy-on-write generally at the
operating-system level, not of any single implementation named in this entry,
and virtualisation platforms and browsers have in some cases disabled
cross-tenant memory deduplication specifically because of this class of
concern. Where the deployment model shares physical memory across mutually
untrusting tenants, this is worth confirming with the specific hypervisor or
container runtime's own security documentation rather than assumed away.

On privacy specifically, storage-layer copy-on-write (Docker layers, ZFS or
Btrfs snapshots) has a quieter but real implication. an unmodified base layer
or an earlier snapshot continues to physically exist, unmodified, for as long
as anything still references it, even after a "later" version has diverged
and appears, from the outside, to be the current state. Data a user believed
was deleted or overwritten, and would expect to be gone, can remain
physically present in an earlier layer or snapshot that copy-on-write kept
around specifically because deleting it would have required duplicating
everything that still depended on it. Any deletion or retention policy that
assumes overwriting a file removes its prior contents needs to account for
whether the underlying storage is copy-on-write, and if so needs to confirm
earlier snapshots or layers are also purged on the same schedule.

## 18. References

1. Linux man-pages project. `fork(2)` manual page, NOTES section.
   https://man7.org/linux/man-pages/man2/fork.2.html
   Verified 2026-08-14. Source for kernel page-table copy-on-write and the
   Linux `fork` production use.
2. The Rust Project. `std::borrow::Cow` documentation, standard library
   API reference.
   https://doc.rust-lang.org/std/borrow/enum.Cow.html
   Verified 2026-08-14. Source for the `Cow` type's intent, the two-state
   enum implementation variant, and the `to_mut` Write Gate semantics.
3. Redis Ltd. "Redis persistence", sections "Snapshotting" and "How it
   works".
   https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
   Verified 2026-08-14. Source for the Redis fork-based RDB snapshotting
   production use.
4. Apple Inc. Swift standard library source, `Array` type documentation
   comment, `stdlib/public/core/Array.swift`.
   https://github.com/apple/swift/blob/main/stdlib/public/core/Array.swift
   Verified 2026-08-14. Source for the Swift `Array` and `Dictionary`
   copy-on-write production use and the `isKnownUniquelyReferenced`
   implementation variant.
5. Docker Inc. "Storage drivers".
   https://docs.docker.com/storage/storagedriver/
   Verified 2026-08-14. Source for the OverlayFS layered-filesystem
   copy-on-write production use and the "copy up" amplification failure
   mode.

## Code examples

Three languages where the pattern is genuinely idiomatic in distinct ways.
Swift shows the invisible, language-native form built into every value-type
collection. Rust shows the explicit, compiler-checked, named-type form. Go is
included as a third form built by hand from first principles (a manual
reference count plus an explicit `Clone` method), because Go has no built-in
copy-on-write collection type and the language's explicit style makes the
Write Gate mechanics unusually easy to see step by step. TypeScript is
omitted, because JavaScript's arrays and objects are always eagerly,
structurally distinct on assignment of a shallow copy, or always aliased on a
plain reference assignment, with no built-in middle ground, so a faithful
implementation would need to hand-roll the same reference-counting machinery
Go's example already demonstrates, adding a second worked example of the same
underlying mechanic rather than a genuinely different idiom.

### Swift

```swift
final class Storage<T> {
    var elements: [T]
    init(_ elements: [T]) { self.elements = elements }
    func copy() -> Storage<T> { Storage(elements) }
}

struct COWArray<T> {
    private var storage: Storage<T>

    init(_ elements: [T]) {
        storage = Storage(elements)
    }

    var count: Int { storage.elements.count }

    subscript(index: Int) -> T {
        get { storage.elements[index] }
        set {
            if !isKnownUniquelyReferenced(&storage) {
                storage = storage.copy()
            }
            storage.elements[index] = newValue
        }
    }
}

var a = COWArray([1, 2, 3])
var b = a
b[0] = 99
print(a[0], b[0])
```

### Rust

```rust
use std::borrow::Cow;

fn normalize(input: &str) -> Cow<'_, str> {
    if input.contains(' ') {
        Cow::Owned(input.replace(' ', "_"))
    } else {
        Cow::Borrowed(input)
    }
}

fn main() {
    let clean = "already_clean";
    let dirty = "needs fixing";

    let a = normalize(clean);
    let b = normalize(dirty);

    match &a {
        Cow::Borrowed(_) => println!("a: no allocation, still {}", a),
        Cow::Owned(_) => println!("a: allocated"),
    }
    match &b {
        Cow::Borrowed(_) => println!("b: no allocation"),
        Cow::Owned(_) => println!("b: allocated, now {}", b),
    }
}
```

### Go

```go
package main

import "fmt"

type storage struct {
	refs int
	data []int
}

type cowSlice struct {
	s *storage
}

func newCOWSlice(data []int) cowSlice {
	return cowSlice{s: &storage{refs: 1, data: data}}
}

func (c cowSlice) share() cowSlice {
	c.s.refs++
	return c
}

func (c *cowSlice) set(index, value int) {
	if c.s.refs > 1 {
		fresh := make([]int, len(c.s.data))
		copy(fresh, c.s.data)
		c.s.refs--
		c.s = &storage{refs: 1, data: fresh}
	}
	c.s.data[index] = value
}

func (c cowSlice) get(index int) int {
	return c.s.data[index]
}

func main() {
	a := newCOWSlice([]int{1, 2, 3})
	b := a.share()
	b.set(0, 99)
	fmt.Println(a.get(0), b.get(0))
}
```
