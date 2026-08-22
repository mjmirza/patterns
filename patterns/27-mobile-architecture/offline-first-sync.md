---
name: Offline-First Sync
slug: offline-first-sync
family: 27-mobile-architecture
category: Structural
aliases: [Local-First Sync, Sync Engine, Replication Layer]
first_described: 'CouchDB/PouchDB project, replication and conflict-resolution guidance'
maturity: canonical
related: [repository-pattern, unidirectional-data-flow]
incompatible_with: []
verified: 2026-08-22
---

# Offline-First Sync

## 1. Name, aliases, and lineage

Offline-First Sync. Also called Local-First Sync, a Sync Engine, or a Replication Layer. The name describes the guarantee it makes. every write lands in a local data store immediately, the app is fully usable with no network at all, and a background process reconciles local changes with a remote backend whenever connectivity is present.

The lineage traces back to CouchDB and its mobile companion PouchDB, which built replication and conflict resolution into the database itself rather than treating sync as an application-level afterthought. The PouchDB team put the priority bluntly. CouchDB is bad at everything, except syncing, and it turns out that is the most important feature you could ever ask for, for many types of software (https://pouchdb.com/guides/replication.html). A second, more recent lineage comes from Conflict-Free Replicated Data Types (CRDTs), formalized in academic distributed-systems research and popularized for application developers by libraries such as Automerge and Yjs, which let concurrent edits on different devices merge automatically without a central coordinator.

## 2. Problem and context

A mobile device is not always connected. a subway ride, an airplane, a rural area, or simply a flaky cell tower all take the network away mid-session. An app whose every action requires a live request either blocks the person entirely or, worse, appears to work and then silently loses the change when the request fails. Neither is acceptable for anything the person expects to persist, a drafted message, a completed task, a logged workout.

The deeper problem is not only tolerating disconnection, it is RECONCILING two histories once connectivity returns. If the same record was edited on two devices while both were offline, or edited locally while the server also changed it, something has to decide the outcome. Automerge's own framing of the underlying mechanism is direct. When a network connection is available, Automerge figures out which changes need to be synced from one device to another, and brings them into the same state (https://automerge.org/docs/hello/). That reconciliation step, done well, is invisible to the person. done badly, it silently drops one side's edits, which is the single most damaging failure an offline-capable app can produce, because it destroys trust in the app's basic promise that a save is a save.

## 3. Forces

- The write must land locally before any network round trip, or the app is not actually offline-capable, only offline-tolerant with a spinner.
- Two devices, or a device and the server, can each hold a change to the same record made while disconnected from each other, and both are legitimate.
- Conflict resolution must be either fully automatic (a CRDT merges deterministically) or surfaced to a human decision, but never silently dropped.
- Sync traffic competes with battery and data budget, so a naive full-resync on every reconnect wastes both once the user base is large.
- The local store's schema and the remote API's schema tend to drift over time, and the sync layer is where that drift becomes a real bug instead of a theoretical one.

## 4. Applicability and non-applicability

Use offline-first sync for any app whose person expects an action to feel instantaneous and durable regardless of connectivity, a note-taking app, a task manager, a field-service app used in low-signal locations, or a collaborative document editor. It is the right fit whenever data can plausibly be edited from more than one device or more than one session, since that is exactly the condition that produces conflicts worth resolving deliberately.

Skip it for data that is read-only from the client's perspective (a content feed the app only displays) or for an app whose every action is by its nature an online transaction with no valid offline state, such as a real-time payment authorization. Forcing a full sync engine onto pure read-through caching or onto strictly server-authoritative transactions is non-applicability in the other direction, since it adds conflict-resolution machinery for data that, by construction, cannot conflict.

## 5. Structure

- Local store. an embedded database (SQLite, an object store, or a purpose-built local-first engine) that every read and write goes through first, regardless of network state.
- Change log or oplog. an ordered record of local mutations since the last successful sync, used to replay changes to the remote and to detect what actually changed rather than diffing full records.
- Sync engine. the component that opens a connection when one is available, pushes the local change log, pulls remote changes, and drives the reconciliation step.
- Conflict resolver. the policy that decides the outcome when the same record changed on both sides. deterministic merge (a CRDT, or CouchDB's revision-tree winner selection), a last-write-wins rule, or a surfaced choice for the person.
- Sync state tracker. persisted metadata (a cursor, a revision vector, a last-synced timestamp) that lets the next sync resume incrementally instead of re-transferring everything.

## 6. ASCII structure diagram

```
  local write
      |
      v
  +--------------+       +----------------+
  |  Local Store |------>|  Change Log     |
  +--------------+       +----------------+
      ^                        |
      |                        v
      |                 +----------------+       network
      |                 |  Sync Engine   |<---- available? --->
      |                 +----------------+
      |                        |
      |                        v
  +--------------+       +----------------+
  | Conflict     |<------|  Remote pull   |
  | Resolver     |       +----------------+
  +--------------+
      |
      v
  merged state written back to Local Store
```

## 7. Dynamics

1. The person performs an action. the app writes it to the Local Store immediately and updates the UI from that local write, never waiting on the network.
2. The write is appended to the Change Log so the Sync Engine knows what has not yet reached the remote.
3. When the Sync Engine detects connectivity, it pushes the Change Log entries to the remote and pulls any remote changes made since the last sync, using the Sync State Tracker's cursor to fetch only the delta.
4. For each record touched on both sides, the Conflict Resolver decides the outcome. a CRDT-based resolver merges automatically, per Automerge's own description. Automerge is a Conflict-Free Replicated Data Type, which allows concurrent changes on different devices to be merged automatically without requiring any central server (https://automerge.org/docs/hello/). A revision-tree resolver instead picks a deterministic winner while preserving the losing branch, matching CouchDB's approach, which will choose an arbitrary winner that every node can agree upon deterministically, however, conflicts are still stored in the revision tree similar to a Git history tree, which means that app developers can either surface the conflicts to the user, or leave them unresolved (https://pouchdb.com/guides/replication.html).
5. The merged result is written back to the Local Store, the Sync State Tracker's cursor advances, and the UI updates again if the merge changed anything the person is currently viewing.
6. If the network drops mid-sync, the Sync Engine retries from the last confirmed cursor position on the next connectivity event, never assuming a partial push succeeded.

## 8. Implementation variants

- Deterministic revision-tree merge. the CouchDB and PouchDB model, where every write creates a new revision, conflicting revisions are both retained, and a documented deterministic rule (not last-write-wins by clock, which is unsafe under clock skew) picks the visible winner while the loser stays recoverable.
- CRDT-based automatic merge. Automerge and Yjs represent state as a data structure engineered so that any two divergent copies merge to the same result regardless of order, removing the need for a conflict policy at the application level entirely for the fields the CRDT covers.
- Operational transform. an older approach (used in early collaborative editors) that transforms concurrent operations against each other so they can be applied in a different order and still converge, largely superseded by CRDTs for new systems but still present in legacy collaborative-editing infrastructure.
- Server-authoritative with client queue. the client simply queues mutations locally and replays them against a server that owns the final resolution logic, trading some client autonomy for a simpler, centralized conflict policy.

## 9. Known production uses

- CouchDB and PouchDB are the reference implementation of the revision-tree sync model, used across offline-capable web and mobile apps that need peer-to-peer or client-to-server replication with retained conflict history (https://pouchdb.com/guides/replication.html).
- Automerge, described on its own documentation as a library of data structures for building collaborative applications, where you can have a copy of the application state locally on several devices which may belong to the same user, or to different users (https://automerge.org/docs/hello/), powers collaborative and local-first applications that need automatic CRDT-based merging without a coordinating server.
- Note-taking, task-management, and field-service apps across the industry commonly build an internal equivalent of this pattern, layering a local SQLite or object store with a custom sync engine, specifically because their users work in low-connectivity environments where a network-first design would be unusable.

## 10. Consequences

### Benefits

- The app is fully usable with no network, which removes an entire class of person-facing failure (blocked actions, lost input) that a network-first design cannot avoid.
- Writes feel instantaneous, since the UI reflects the local write rather than waiting on a round trip.
- A well-chosen conflict policy (a CRDT, or a documented deterministic winner) makes multi-device editing safe by construction rather than by convention.

### Costs

- Conflict resolution is genuinely hard to get right, and a naive policy (a wall-clock last-write-wins) is unsafe under clock skew and can silently lose data.
- The local store and the sync engine add real complexity and a real surface area for bugs, compared to a stateless network-first client.
- Debugging a sync issue requires reasoning about two histories and their merge, which is a much harder mental model than debugging a single request-response failure.

## 11. Failure modes and misuse

- Silent data loss. a last-write-wins policy by wall-clock time discards a genuinely later edit made on a device whose clock is behind, and the person never sees a warning.
- Sync storm. a full resync triggered on every reconnect instead of an incremental delta, draining battery and data on a flaky connection that reconnects and drops repeatedly.
- Unbounded conflict accumulation. a revision-tree model that retains every conflicting branch forever without ever surfacing or pruning them grows storage without bound and never actually resolves anything for the person.
- Schema drift. the local store's shape diverges from the remote API's shape over app versions, and the sync engine either crashes on an old client's unsynced data or silently drops fields it does not recognize.
- Merge blind spots. a CRDT or merge policy that covers most fields but treats one field (a status enum, a relationship reference) with plain overwrite semantics, producing an inconsistent result exactly where it matters most.

## 12. Trade-off matrix

| Dimension | Deterministic revision-tree (CouchDB/PouchDB) | CRDT-based automatic merge (Automerge/Yjs) |
|---|---|---|
| Conflict visibility | Retained and inspectable, app decides whether to surface | Merged transparently, no retained losing branch |
| Implementation complexity | Moderate, built into the database's replication protocol | Higher, requires the data model to be expressed in CRDT types |
| Works without a coordinating server | Yes, peer-to-peer replication supported | Yes, this is the core design goal |
| Best fit | Document stores with a clear winner-takes-visible-slot semantic | Collaborative, structured data where a true field-level merge is wanted |
| Storage growth from conflicts | Unbounded unless pruned | Bounded, merge is applied rather than retained |

## 13. Related and incompatible patterns

### Related

- Repository Pattern (Mobile Offline-First). the repository is the local-first READ and WRITE boundary a feature talks to; the sync engine is the background process that keeps the repository's local store consistent with the remote.
- Unidirectional Data Flow (Mobile). a merged sync result flows back into state the same way any other state change does, through the same one-way update path rather than a special-cased sync-only mutation.

### Incompatible with

- None directly, though a strictly server-authoritative, always-online transaction (a live payment) should not route through a local-first sync layer, since that layer's entire value proposition assumes offline validity the transaction cannot actually have.

## 14. Refactoring path in and out

### Introducing it

1. Identify which data genuinely needs offline durability versus which is safe to treat as a live, network-only read.
2. Introduce a local store for the offline-durable data and route all reads and writes for it through that store first, even before any sync engine exists.
3. Add a Change Log that records local mutations, so the eventual sync engine has a real delta to work from instead of needing to diff full snapshots.
4. Build the Sync Engine and Conflict Resolver, choosing a conflict policy deliberately (CRDT, deterministic revision winner, or server-authoritative) rather than defaulting to last-write-wins by clock.
5. Roll out sync behind a flag against a small, low-risk data type first, verify conflict behavior under real multi-device use, then extend to the rest.

### Removing it

1. Confirm the data no longer needs offline durability or multi-device edit safety, which is rare but possible after a product pivot to single-device, always-online use.
2. Migrate any locally-queued, unsynced changes to the remote before removing the Sync Engine, so no in-flight local write is lost.
3. Replace the Local Store access pattern with a direct network call, and delete the Change Log and Conflict Resolver once nothing depends on them.

## 15. Testing and verification

- Test the local write path in complete isolation from the network, asserting the app remains fully functional with the network interface disabled.
- Test the Conflict Resolver directly against constructed conflicting-edit scenarios (the same record changed on two simulated devices), asserting the merge outcome matches the documented policy, not an accidental one.
- Test resumability. kill the Sync Engine mid-push and mid-pull, restart it, and assert it resumes from the last confirmed cursor rather than re-sending already-synced data or skipping unsent data.
- Add an integration test that flips connectivity on and off rapidly during a sync cycle, asserting no data loss and no duplicate writes on the remote.
- Verify clock-skew safety explicitly if any part of the policy touches timestamps, since this is the single most common source of a silent-data-loss bug in this pattern.

## 16. Observability signals

- Track sync success and failure rates, and the age of the oldest un-synced local change, so a person stuck offline (or hitting a silent sync bug) is visible before they notice data missing on a second device.
- Track conflict rate per record type, since a type with an unexpectedly high conflict rate often signals a UX problem (two features racing to write the same field) rather than a genuine multi-device edit.
- Track sync payload size and duration over time, to catch a regression toward full-resync behavior instead of incremental delta sync before it shows up as a battery or data complaint.

## 17. Security and privacy implications

- Data that is local-first sits on the device unencrypted by default in many embedded databases, so sensitive fields need explicit at-rest encryption if the local store is not already covered by the platform's full-disk protections.
- A sync engine that retries indefinitely on an authentication failure can leak stale credentials in logs or retry loops. fail fast and surface re-authentication rather than looping silently.
- Retained conflicting revisions (the revision-tree model) can retain data the person believed was overwritten or deleted, which has real privacy and compliance implications. a genuine delete request must purge every retained branch, not only the visible winner.
- Multi-device sync means a compromised or lost device can pull the full sync history, so access revocation on device loss must be able to cut that device off from future sync, not merely lock its screen.

## Code examples

### Python

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Record:
    id: str
    revision: int
    data: dict


class SyncEngine:
    def __init__(self) -> None:
        self._local = {}
        self._pending_changes = []

    def write(self, record_id, data):
        current = self._local.get(record_id)
        revision = (current.revision + 1) if current else 1
        record = Record(id=record_id, revision=revision, data=data)
        self._local[record_id] = record
        self._pending_changes.append(record)
        return record

    def sync(self, remote_records):
        for remote in remote_records:
            local = self._local.get(remote.id)
            if local is None or remote.revision > local.revision:
                self._local[remote.id] = remote
            elif remote.revision == local.revision and remote.data != local.data:
                self._local[remote.id] = _resolve_conflict(local, remote)
        pushed, self._pending_changes = self._pending_changes, []
        return pushed


def _resolve_conflict(local, remote):
    winner_id = min(local.id, remote.id)
    return local if local.id == winner_id else remote


engine = SyncEngine()
engine.write('note-1', {'title': 'grocery list'})
pushed = engine.sync(remote_records=[])
print('pending push count', len(pushed))
```

### Kotlin

```kotlin
data class Record(val id: String, val revision: Int, val data: Map<String, Any>)

class SyncEngine {
    private val local = mutableMapOf<String, Record>()
    private val pendingChanges = mutableListOf<Record>()

    fun write(recordId: String, data: Map<String, Any>): Record {
        val currentRevision = local[recordId]?.revision ?: 0
        val record = Record(recordId, currentRevision + 1, data)
        local[recordId] = record
        pendingChanges.add(record)
        return record
    }

    fun sync(remoteRecords: List<Record>): List<Record> {
        for (remote in remoteRecords) {
            val existing = local[remote.id]
            when {
                existing == null || remote.revision > existing.revision ->
                    local[remote.id] = remote
                remote.revision == existing.revision && remote.data != existing.data ->
                    local[remote.id] = resolveConflict(existing, remote)
            }
        }
        val pushed = pendingChanges.toList()
        pendingChanges.clear()
        return pushed
    }

    private fun resolveConflict(local: Record, remote: Record): Record =
        if (local.id <= remote.id) local else remote
}

val engine = SyncEngine()
engine.write('note-1', mapOf('title' to 'grocery list'))
val pushed = engine.sync(remoteRecords = emptyList())
println('pending push count ' + pushed.size)
```

### Swift

```swift
struct Record {
    let id: String
    let revision: Int
    let data: [String: String]
}

final class SyncEngine {
    private var local: [String: Record] = [:]
    private var pendingChanges: [Record] = []

    func write(recordId: String, data: [String: String]) -> Record {
        let currentRevision = local[recordId]?.revision ?? 0
        let record = Record(id: recordId, revision: currentRevision + 1, data: data)
        local[recordId] = record
        pendingChanges.append(record)
        return record
    }

    func sync(remoteRecords: [Record]) -> [Record] {
        for remote in remoteRecords {
            let existing = local[remote.id]
            if existing == nil || remote.revision > existing!.revision {
                local[remote.id] = remote
            } else if remote.revision == existing!.revision && remote.data != existing!.data {
                local[remote.id] = resolveConflict(local: existing!, remote: remote)
            }
        }
        let pushed = pendingChanges
        pendingChanges.removeAll()
        return pushed
    }

    private func resolveConflict(local: Record, remote: Record) -> Record {
        return local.id <= remote.id ? local : remote
    }
}

let engine = SyncEngine()
_ = engine.write(recordId: "note-1", data: ["title": "grocery list"])
let pushed = engine.sync(remoteRecords: [])
print("pending push count " + String(pushed.count))
```

## 18. References

- PouchDB, Replication and Sync guide (https://pouchdb.com/guides/replication.html)
- Automerge documentation, Hello (https://automerge.org/docs/hello/)
