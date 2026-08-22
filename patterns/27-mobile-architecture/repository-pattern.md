---
name: Repository Pattern (Mobile Offline-First)
slug: repository-pattern
family: 27-mobile-architecture
category: Structural
aliases: [Offline-First Repository, Single-Source-of-Truth Repository]
first_described: 'Google Android Developers, "Build an offline-first app" architecture guidance'
maturity: canonical
related: [unidirectional-data-flow, mvvm-c]
incompatible_with: []
verified: 2026-08-22
---

# Repository Pattern (Mobile Offline-First)

## 1. Name, aliases, and lineage

The canonical name is Repository Pattern in its mobile, offline-first
form, a pattern where a repository object combines a local database
and a remote network source into one interface, but treats the local
database, never the network, as the app's real, canonical source of
truth, so the app keeps working, reading and, within limits, writing,
even with no real network connection present. Google's own
architecture guidance states the core requirement plainly, "the local
data source is the canonical source of truth for the app. It should
be the exclusive source of any data that higher layers of the app
read."
Google's own definition of the offline-first goal itself is equally
direct, "an offline-first app is an app that is able to perform all,
or a critical subset of its core functionality without access to the
internet."

The alias **Offline-First Repository** names the pattern by its real,
motivating goal. **Single-Source-of-Truth Repository** names it by its
defining structural rule, Google's own stated requirement that the
local data source is the exclusive place higher layers ever read from.

## 2. Problem and context

A mobile app that reads directly from the network whenever a screen
needs data genuinely stops working the moment the device loses
connectivity, and even with a connection, every screen pays a real
network round-trip cost on every read. Reading from two different
places, sometimes the network directly, sometimes a local cache, also
genuinely creates two competing candidates for "what is the real,
current data," a real consistency risk. The Repository Pattern in its
offline-first form solves this by making the local database the
single, exclusive place the rest of the app ever reads from, per
Google's own stated rule, and by making the repository itself
responsible for keeping that local database in sync with the network
in the background. Google's own description of the resulting
requirement is exact, "a repository with network access in an
offline-first app must always have a local data source," and the
resulting real read and write behavior, per Google, Android
Developers, "Build an offline-first app,"
https://developer.android.com/topic/architecture/data-layer/offline-first,
verified 2026-08-22, "in an offline-first app, read
operations from repositories read directly from the local data
source. Write any updates to the local data source first, so that the
local data source updates its consumers since it is observable."

## 3. Forces

The pattern balances the following competing pressures.

- **The app keeps working with no real network connection.** Favored.
  Google's own definition states this directly, an offline-first app
  "is able to perform all, or a critical subset of its core
  functionality without access to the internet."
- **Exactly one real source of truth for the app's data.** Favored.
  Google's own documentation states this directly, the local data
  source "should be the exclusive source of any data that higher
  layers of the app read," genuinely eliminating the two-competing-
  candidates consistency risk named in dimension 2.
- **Consumers are updated automatically as local data changes.**
  Favored. Google's own documentation states this directly, writes go
  "to the local data source first, so that the local data source
  updates its consumers since it is observable," so a screen never
  needs to separately ask "did the network write also succeed."
- **A real, working local database is a genuine requirement, not an
  optional cache.** Sacrificed. Google's own stated rule, "a repository
  with network access in an offline-first app must always have a local
  data source," means the app cannot skip building and maintaining a
  real local persistence layer.
- **The local data can genuinely be stale relative to the real, live
  server state.** Sacrificed. Because reads genuinely come from the
  local database rather than the network directly, per Google's own
  read-path description, the data a screen shows can genuinely lag
  behind the server until the next real background sync completes.

## 4. Applicability and non-applicability

Reach for the offline-first Repository Pattern when the following
hold.

- The app genuinely needs to keep working, fully or for a real
  critical subset of its functionality, with no network connection
  present, per Google's own offline-first definition.
- The team genuinely wants exactly one place the rest of the app reads
  from, per Google's own single-source-of-truth rule, rather than
  reconciling data that could have come from either the network or a
  cache.
- The app's real data genuinely tolerates being momentarily stale
  relative to the live server, in exchange for the real availability
  and consistency benefits the pattern provides.

Do NOT reach for the offline-first Repository Pattern in these cases,
and the reason matters more than the rule.

- **The app genuinely has no real requirement to function offline,
  and every screen's data genuinely must reflect the live server state
  at the moment it is read**, the real cost of building and
  maintaining a local database purely as an intermediary adds
  structure without matching real benefit.
- **The real data volume or update frequency genuinely makes a local,
  synced copy impractical**, such as a real-time video stream or a
  constantly changing live feed, where the network genuinely is the
  only real source of truth at read time.
- **The team genuinely cannot commit to building and maintaining the
  real local data source Google's own rule requires**, a repository
  that claims to be offline-first without one is not genuinely
  following the pattern, and the app should be built as a
  network-only client instead, with that trade-off stated plainly.

## 5. Structure

The offline-first Repository Pattern has three structural parts, per
Google's own description.

- **The local data source**, Google's own stated "canonical source of
  truth for the app," the exclusive place higher layers of the app
  read from.
- **The remote data source**, the network, used by the repository to
  fetch and push updates, but never read from directly by the rest of
  the app, per Google's own single-source-of-truth rule.
- **The repository itself**, Google's own description, "responsible
  for combining data sources to provide app data," owning the real
  logic that reads from local, writes to local first, and
  synchronizes local with remote in the background.

## 6. ASCII structure diagram

```
  Rest of the app (ViewModel, view, etc.)
        |
        |  reads exclusively from here
        v
  Repository
    |         |
    v         v
  Local DB   Remote network source
  (source     (fetched and pushed by
   of truth)   the repository, in the
               background)
```

## 7. Dynamics

The trace below shows one complete read-and-sync cycle, per Google's
own described behavior.

```
The app reads data

per Google's own description, "read operations from repositories read
directly from the local data source"
   |-- the repository returns data from the local database only, with
       no real, blocking network call on the read path

A real write happens, locally or from a background sync

per Google's own description, "write any updates to the local data
source first, so that the local data source updates its consumers
since it is observable"
   |-- the local database is updated first
   |-- because the local database is observable, per Google's own
       description, every consumer reading from it is automatically
       notified of the new data, with no separate signal needed

The repository synchronizes with the network in the background

per Google's own requirement, "a repository with network access in an
offline-first app must always have a local data source"
   |-- the repository fetches real, updated data from the network and
       writes it into the local database
   |-- that local write, per the same observable mechanism, again
       flows automatically to every real consumer
```

## 8. Implementation variants

**Single-writer local database, the canonical Google-described form.**
The local database is the only real place the rest of the app writes
to or reads from, and the repository is the only real code that talks
to the network, exactly as Google's own documentation describes.

**Optimistic-write variant.** A variant where a local write is applied
immediately and marked pending, the repository then attempts the real
network write in the background, and on a real failure the pending
write is retried or surfaced to the user, trading a small window of
optimism for a real, faster-feeling write experience.

**Multi-source repository.** A variant where the repository combines
more than one real local or remote source, such as a local cache plus
two different backend services, while still presenting one, unified
interface and one real local source of truth to the rest of the app.

## 9. Known production uses

**Google, Android Developers, "Build an offline-first app", the
pattern's own core definition and requirements.** Google states the
core rules directly. "An offline-first app is an app that is able to
perform all, or a critical subset of its core functionality without
access to the internet." "The local data source is the canonical
source of truth for the app. It should be the exclusive source of any
data that higher layers of the app read." "Repositories in the data
layer are responsible for combining data sources to provide app
data." "A repository with network access in an offline-first app must
always have a local data source." The real read and write behavior,
"read operations from repositories read directly from the local data
source. Write any updates to the local data source first, so that the
local data source updates its consumers since it is observable."
Google, Android Developers, "Build an offline-first app,"
https://developer.android.com/topic/architecture/data-layer/offline-first,
verified 2026-08-22.

## 10. Consequences

Positive.

- The app genuinely keeps working, fully or for a real critical
  subset of functionality, with no network connection present, per
  Google's own offline-first definition.
- The rest of the app has exactly one real place to read from, per
  Google's own single-source-of-truth rule, genuinely eliminating the
  network-versus-cache consistency risk.
- Consumers are updated automatically, per Google's own observable
  local-database mechanism, with no separate polling or manual
  refresh logic needed anywhere in the app.

Negative.

- The team must genuinely build and maintain a real local database,
  per Google's own stated requirement, a real, ongoing engineering
  cost.
- The data a screen shows can genuinely be momentarily stale relative
  to the live server, since reads come from the local database rather
  than the network directly.
- The repository itself now owns real, involved synchronization
  logic, deciding when and how to reconcile local and remote data,
  logic that did not exist at all in a network-only design.

## 11. Failure modes and misuse

**Letting a screen or a view model read directly from the network,
bypassing the repository's own local data source, breaking the
single-source-of-truth guarantee Google's own rule requires.**
Symptom. The screen genuinely shows data that disagrees with what the
rest of the app, reading through the repository, believes is current,
because two real, different paths to the data now exist. Cause.
Reaching for a direct network call from a screen or view model,
perhaps for a value that felt too small to route through the
repository, rather than genuinely treating the local database as the
exclusive source Google's own rule requires. Fix. Confirm every real
read in the app goes through the repository's own local-data-source
path, per Google's own description, and treat any direct network read
elsewhere in the app as a structural bug reintroducing the
two-competing-candidates problem the pattern exists to remove.

**Building a repository that claims to be offline-first but genuinely
has no real local data source, only an in-memory cache that is lost
on every app restart or network loss.** Symptom. The app genuinely
stops functioning the moment the network is unavailable, despite being
described as offline-first, because there was never a real, durable
local source of truth backing it. Cause. Treating an in-memory cache
as equivalent to Google's own stated requirement, "a repository with
network access in an offline-first app must always have a local data
source," when an in-memory cache does not survive a real restart or
a real network loss the way a genuine local database does. Fix.
Confirm the repository's local data source is genuinely durable, a
real local database, not a transient in-memory structure, before
claiming the app is offline-first.

**Writing to the network first and only updating the local database
on a successful response, rather than writing locally first per
Google's own described order.** Symptom. A real write the user made
while offline is genuinely lost entirely, rather than being retried
later, because the local database, the only place the app would have
remembered it, was never updated. Cause. Ordering the write path
network-first, so a real network failure discards the write entirely,
rather than following Google's own described order, "write any
updates to the local data source first." Fix. Confirm every real
write path updates the local database first, per Google's own
described order, and treats the network write as a background
operation the repository retries or surfaces as pending, never as the
gate a local write must first pass through.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Offline-first Repository (Google's own mechanism) | Direct network reads, no local database | A cache-only repository with no durable local source |
|---|---|---|---|
| The app keeps working with no real network connection | Strong, per Google's own offline-first definition | None, the app genuinely stops functioning offline | Weak, functions only until the process restarts or the cache is evicted |
| Exactly one real source of truth | Strong, per Google's own exclusive-local-source rule | None, the network itself is the only real source, with no local reconciliation needed but no offline benefit either | Weak, the cache and the network can genuinely disagree after a restart |
| Consumers updated automatically on write | Strong, per Google's own observable local-database mechanism | Weak, a screen usually must re-fetch to see a new value | Moderate, depends on the specific cache implementation's own notification support |
| Real engineering cost of a durable local layer | Real, a genuine local database must be built and maintained | None, no local layer exists | Lower, but the durability Google's own rule requires is genuinely absent |

Reading of the table. The offline-first Repository Pattern wins
specifically when the app genuinely needs to function without a
network connection and wants exactly one, consistent, real source of
truth. An app with no real offline requirement, where every read
genuinely must reflect the live server, fits direct network reads
better, and a cache-only approach fails to deliver the pattern's own
real offline guarantee at all.

## 13. Related and incompatible patterns

- **Unidirectional Data Flow (Mobile).** A genuinely complementary
  concern, the repository is commonly the real state-producing
  logic's own data source, feeding the single source of truth that
  entry's own state-down-events-up cycle renders from.
- **MVVM-C (Model-View-ViewModel-Coordinator).** A genuinely
  complementary concern, a view model commonly reads from and writes
  through a repository exactly as it would read from and write through
  any other data dependency, with no real conflict between the two
  patterns.

## 14. Refactoring path in and out

Introducing the pattern into an app that currently reads directly from
the network. Ordered steps, most relevant when the app has a genuine,
real requirement to work offline that it does not yet meet.

1. Build a real, durable local database, per Google's own stated
   requirement, "a repository with network access in an offline-first
   app must always have a local data source."
2. Introduce a repository object that owns the real read path,
   reading exclusively from the local database, per Google's own
   single-source-of-truth rule.
3. Route every real write through the repository, updating the local
   database first, per Google's own described order, before the
   repository attempts the real network write in the background.
4. Confirm no screen or view model in the app still reads directly
   from the network, replacing any such call with a read through the
   repository's own local data source.

Removing the pattern when it stops earning its place, most relevant
when the app's real offline requirement has genuinely gone away, or
was never genuinely present.

1. Confirm, concretely, that the app genuinely no longer needs to
   function without a real network connection.
2. Replace the repository's local-read path with a direct network
   read, removing the local database's role as the source of truth.
3. Confirm no other part of the app still depends on the local
   database's observable-update behavior before removing it entirely.

## 15. Testing and verification

Easier because of the pattern.

- The repository's own real behavior, reading from local, writing
  locally first, then syncing remotely, can be tested with a fake or
  in-memory local database and a fake network source, with no real
  device or real connectivity needed at all.
- A screen or view model that reads exclusively through the
  repository, per Google's own single-source-of-truth rule, can be
  tested by supplying the repository a known, fixed set of local data,
  with no real network dependency in the test at all.

Harder because of the pattern.

- Verifying the real, full offline-to-online transition, a write made
  while genuinely offline, followed by a real reconnect and a real
  successful sync, needs a test that can simulate real connectivity
  changes over time, not only one static state.
- Confirming no code path anywhere bypasses the repository and reads
  the network directly, per the reintroduced-two-sources failure mode
  in dimension 11, needs discipline enforced across the whole
  codebase, not a single localized check.

Techniques that apply.

- **Repository behavior tests.** Assert the repository reads from a
  fake local source and writes there first, with a fake network
  source standing in for the real one, with no real device needed.
- **Offline-write tests.** Simulate a real write while the fake
  network source is unavailable, and assert the write is genuinely
  retried once the fake network source becomes available again.
- **Single-source audits.** Confirm no code path in the app reads
  from the network directly, catching the reintroduced-two-sources
  failure mode from dimension 11.
- **Durability tests.** Confirm the local data source genuinely
  survives a real process restart, catching the fake-durability
  failure mode from dimension 11.

## 16. Observability signals

What to record.

- Whether any code path genuinely reads from the network directly,
  bypassing the repository's own local data source, since any such
  read points directly at the reintroduced-two-sources failure mode
  from dimension 11.
- The real, measured time between a local write and its successful
  remote sync, since a growing, unbounded backlog of unsynced writes
  points directly at a broken or stalled background-sync mechanism.

A healthy state. Every real read in the app goes through the
repository's own local data source, and the real backlog of unsynced
local writes stays small and bounded over time.

A failing state. A direct network read is found bypassing the
repository, pointing directly at reintroduced dual sources, or the
real backlog of unsynced writes grows without bound, pointing directly
at a broken background-sync mechanism.

## 17. Security and privacy implications

**Because the local database, per Google's own description, is the
app's real, canonical source of truth, it genuinely holds a durable,
on-device copy of every piece of data the app has ever synced,
including any real sensitive data such as a user's private messages or
health records, for as long as the local database retains it, which is
a real, broader and longer-lived exposure surface than a purely
network-backed app that never persists that data on the device at
all.** Because the pattern's own real durability requirement, "a
repository with network access in an offline-first app must always
have a local data source," means sensitive data genuinely persists on
the device between sessions, the local database itself must be
genuinely encrypted at rest, and any sensitive record must be
genuinely and promptly deleted from the local database when the user
deletes it or revokes consent, not merely marked deleted on the
remote server while a stale, real local copy lingers. Confirming the
local database is genuinely encrypted, and that a real deletion
request is propagated to the local copy and not only the remote
source, are necessary parts of a security-conscious offline-first
Repository implementation.

## Code examples

Three languages where the pattern is genuinely idiomatic in different
ways. Kotlin models Google's own original mechanism directly, the
language and platform the pattern's own canonical documentation is
written for. Swift shows the same conceptual shape on iOS, an
idiomatic composition of a repository type backed by a local
persistence layer and a network client. Python shows the same
conceptual shape using a minimal, host-testable simulation, useful for
verifying the repository's own local-first read and write behavior in
isolation, per dimension 15, expressed portably. Java, Go, and Rust
are omitted, since the pattern's real home is mobile-app data layers,
and the three languages chosen already cover its two production
platforms and its testable-simulation shape.

### Kotlin

```kotlin
interface LocalDataSource {
    fun read(): List<String>
    fun write(items: List<String>)
}

interface RemoteDataSource {
    fun fetch(): List<String>
}

class ItemsRepository(
    private val local: LocalDataSource,
    private val remote: RemoteDataSource
) {
    fun read(): List<String> = local.read()

    fun sync() {
        val fresh = remote.fetch()
        local.write(fresh)
    }
}

class InMemoryLocal : LocalDataSource {
    private var items = listOf<String>()
    override fun read() = items
    override fun write(items: List<String>) {
        this.items = items
    }
}

class FakeRemote : RemoteDataSource {
    override fun fetch() = listOf("Ada", "Grace")
}

fun main() {
    val repo = ItemsRepository(InMemoryLocal(), FakeRemote())
    println(repo.read())
    repo.sync()
    println(repo.read())
}
```

### Swift

```swift
protocol LocalDataSource {
    func read() -> [String]
    func write(_ items: [String])
}

protocol RemoteDataSource {
    func fetch() -> [String]
}

final class ItemsRepository {
    private let local: LocalDataSource
    private let remote: RemoteDataSource

    init(local: LocalDataSource, remote: RemoteDataSource) {
        self.local = local
        self.remote = remote
    }

    func read() -> [String] {
        local.read()
    }

    func sync() {
        let fresh = remote.fetch()
        local.write(fresh)
    }
}

final class InMemoryLocal: LocalDataSource {
    private var items: [String] = []
    func read() -> [String] { items }
    func write(_ items: [String]) { self.items = items }
}

final class FakeRemote: RemoteDataSource {
    func fetch() -> [String] { ["Ada", "Grace"] }
}

let repo = ItemsRepository(local: InMemoryLocal(), remote: FakeRemote())
print(repo.read())
repo.sync()
print(repo.read())
```

### Python

```python
from typing import List, Protocol


class LocalDataSource(Protocol):
    def read(self) -> List[str]: ...
    def write(self, items: List[str]) -> None: ...


class RemoteDataSource(Protocol):
    def fetch(self) -> List[str]: ...


class ItemsRepository:
    def __init__(self, local: LocalDataSource, remote: RemoteDataSource):
        self.local = local
        self.remote = remote

    def read(self) -> List[str]:
        return self.local.read()

    def sync(self) -> None:
        fresh = self.remote.fetch()
        self.local.write(fresh)


class InMemoryLocal:
    def __init__(self):
        self.items: List[str] = []

    def read(self) -> List[str]:
        return self.items

    def write(self, items: List[str]) -> None:
        self.items = items


class FakeRemote:
    def fetch(self) -> List[str]:
        return ["Ada", "Grace"]


if __name__ == "__main__":
    repo = ItemsRepository(InMemoryLocal(), FakeRemote())
    print(repo.read())
    repo.sync()
    print(repo.read())
```

## 18. References

1. Google, Android Developers. "Build an offline-first app".
   https://developer.android.com/topic/architecture/data-layer/offline-first
   Verified 2026-08-22. Source of the offline-first definition, the
   single-source-of-truth rule, the repository's own combining role,
   the local-data-source requirement, and the read/write ordering,
   used in dimensions 1, 2, 3, 5, 7, 9, and 10.
