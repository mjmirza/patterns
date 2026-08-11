---
name: Optimistic Offline Lock
slug: optimistic-offline-lock
family: 06-enterprise-application-architecture
category: Concurrency
aliases: [Optimistic Concurrency Control, Version Stamping, ETag Concurrency]
first_described: "Fowler 2002"
maturity: canonical
related: [unit-of-work, pessimistic-offline-lock, coarse-grained-lock, identity-map]
incompatible_with: [pessimistic-offline-lock]
verified: 2026-08-02
---

# Optimistic Offline Lock

## 1. Name, aliases, and lineage

The canonical name is Optimistic Offline Lock. It was catalogued by Martin
Fowler in *Patterns of Enterprise Application Architecture*, Addison-Wesley,
2002, chapter 16, Concurrency Patterns. The pattern's stated intent on
Fowler's own catalog page is to prevent conflicts between concurrent business
transactions by detecting a conflict and rolling back the transaction
(martinfowler.com, "Optimistic Offline Lock",
https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html, verified
2026-08-02). The word "offline" in the name refers to a business transaction
that spans a user think time or a multi-request conversation, not to an
application running without a network connection. Fowler contrasts it with a
system transaction, which is bounded by a single database commit and is
already protected by the database's own locking.

The wider industry name for the same idea is Optimistic Concurrency Control,
a term with an older, more general lineage in distributed systems research,
predating the enterprise-pattern catalog by two decades. H. T. Kung and John
T. Robinson, "On Optimistic Methods for Concurrency Control", ACM
Transactions on Database Systems, Volume 6, Issue 2, June 1981, pages
213 to 226, proposed validating a transaction against conflicting writes at
commit time instead of acquiring locks up front, and is the earliest
peer-reviewed source for the read-validate-write shape this pattern
specializes for the enterprise data-access layer. Fowler's contribution is
narrower and more concrete than Kung and Robinson's database-kernel
technique, in that it names the specific mechanism of a version number or
timestamp carried on a domain object across a business transaction, and it
names the counterpart pattern, Pessimistic Offline Lock, that a team chooses
between.

Version Stamping and ETag Concurrency are the names the same technique takes
in two adjacent communities. Version Stamping is the term used inside object
relational mapping documentation for the counter or timestamp column itself,
for example the JPA specification's `@Version` annotation, described in
Jakarta Persistence 3.1 Specification, Eclipse Foundation, section 3.4.2,
Optimistic Locking, https://jakarta.ee/specifications/persistence/3.1/,
verified 2026-08-02. ETag Concurrency is the HTTP-native form, where the
version is carried as an opaque entity tag and the conflict check is
performed by the `If-Match` conditional request header rather than by
application code, described in the HTTP semantics specification, RFC 9110,
"HTTP Semantics", Internet Engineering Task Force, June 2022, section 13.1.1,
If-Match, https://www.rfc-editor.org/rfc/rfc9110#name-if-match, verified
2026-08-02, and summarized at Mozilla Developer Network, "If-Match",
https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Match, verified
2026-08-02.

## 2. Problem and context

A business transaction in an enterprise application often spans more than
one system transaction. A person opens an edit screen, which issues a
database read and commits it. The person then looks at the data, thinks,
perhaps steps away for lunch, and eventually submits a change, which issues a
second, independent database write and commits that. Between the read and
the write there is no open database transaction holding any lock, because
holding a database lock across human think time would starve every other
session waiting on the same row. This gap is the exact thing the word
offline names in the pattern's title, offline with respect to the database,
not offline with respect to the network.

If a second person reads the same record during that gap, edits a different
field, and saves first, the first person's eventual save silently overwrites
the second person's change, because the database sees two ordinary,
independently valid UPDATE statements and has no idea they were racing
against the same in-memory snapshot. This is the lost update problem, and it
is invisible to both users. Neither screen shows an error. The first
person's screen still shows the stale data they started from, and their save
appears to succeed. The second person's earlier change simply vanishes from
the database with no log entry that anything unusual happened, unless the
application explicitly detects it.

The problem context has three necessary conditions. First, a business
transaction that reads data, holds it across a gap with no open database
transaction, and later writes it back, the classic read modify write cycle.
Second, more than one such business transaction can legitimately target the
same row concurrently, which rules out this pattern for genuinely
single-writer data. Third, true collisions are rare enough in practice that
paying the cost of a failed transaction and a retry, rather than paying the
cost of blocking every reader behind a lock, is the better trade for the
application's actual contention profile. When collisions are frequent, this
pattern degrades into repeated wasted work and Pessimistic Offline Lock
usually serves better, a point Fowler makes directly on the same catalog
page cited above.

## 3. Forces

**Consistency versus throughput.** A version check catches every conflicting
write without exception, so the consistency guarantee is exact, but it
buys that guarantee by discarding completed work whenever two writers do
collide, which is a throughput cost concentrated on the unlucky transaction
rather than spread evenly across all of them.

**Latency versus safety during the think-time gap.** Because no lock is held
while the user is looking at the screen, every other user reading the same
row experiences zero added latency during that gap. The safety net only
activates at the moment of the write, which is the opposite latency profile
of Pessimistic Offline Lock, where the first reader's lock adds latency to
every subsequent reader for as long as the first reader holds it.

**Coupling to a mutable version field.** The pattern couples every writer of
a row to a shared, mutable version column, which means schema evolution
that adds a new write path (a bulk import job, a direct SQL patch script, a
message consumer applying an event) must also increment that version field
or it silently defeats the whole mechanism for that path.

**Operability and the retry burden.** Detecting a conflict is cheap. Handling
it well is not. The pattern shifts real engineering work onto the retry and
conflict-resolution logic, and a system that detects conflicts but merely
surfaces a raw database exception to the end user has implemented half the
pattern, a recurring failure mode discussed in dimension 11.

**Cost of false positives from coarse granularity.** A version field on an
entire aggregate root, rather than on individual fields, means two edits
that touch unrelated fields on the same row are treated as a conflict even
though they could have been merged. Coarse-Grained Lock, Fowler, *Patterns
of Enterprise Application Architecture*, 2002, chapter 16, is the companion
pattern for deciding the granularity at which the version lives, and it
directly trades false-positive conflict rate against the bookkeeping cost of
tracking finer-grained versions.

**Cognitive load on the client.** The client, whether a browser tab or an
API caller, must now be a participant in the protocol, carrying the version
it read forward to the write call, which means every write endpoint gains a
required field that has nothing to do with the business data itself and
everything to do with the concurrency mechanism.

Fowler names the central trade directly. optimism about how often two
transactions actually collide is the whole premise of the pattern's name,
and when that optimism is wrong for the workload, the pattern's own cost
model inverts (Fowler, *Patterns of Enterprise Application Architecture*,
2002, chapter 16, Concurrency, https://martinfowler.com/eaaCatalog/, verified
2026-08-02).

## 4. Applicability and non-applicability

Use Optimistic Offline Lock when the following hold together.

- The business transaction spans human think time or a multi-step
  conversation, so holding a database lock for the whole duration is either
  impossible or unacceptably expensive.
- Genuine write-write collisions on the same row are rare relative to the
  total number of reads and writes, so most transactions never pay the
  retry cost.
- The application, or the person using it, can respond in a useful way to a
  detected conflict, by re-showing the current data, merging, or asking the
  user to redo the edit. A conflict detected but silently swallowed is worse
  than no detection at all.
- The write path can be made to carry the version the reader saw, which is
  natural in a request-response web application (a hidden form field, an
  ETag round-tripped through `If-Match`) and natural in an ORM with a
  managed entity, but awkward in fire-and-forget messaging where the
  producer never sees a response.
- Losing a completed unit of work occasionally to a retry is an acceptable
  cost, both technically (the work is cheap to redo) and from a product
  perspective (the user is not devastated by having to redo a long form).

Do NOT use Optimistic Offline Lock when any of these hold.

- Collisions are frequent, for example a shared inventory counter under
  flash-sale load, a shared queue cursor, or any hot row updated many times
  per second by many writers. Here almost every optimistic write loses the
  race and retries, which wastes more work than a short-held pessimistic
  lock would have, and Fowler recommends Pessimistic Offline Lock for
  exactly this profile on the same catalog page cited in dimension 1.
- The business operation must never fail visibly to the user for
  correctness reasons that outweigh the throughput cost, for example a
  single-operator control system issuing a physical actuator command where
  a discarded write with no operator watching for the retry is dangerous.
  a pessimistic lock or a single-writer design removes the failure mode
  entirely rather than detecting and reporting it.
- There is no code path capable of reacting to a conflict at all, most
  commonly a batch job or an at-least-once message consumer with no return
  channel to a human or a compensating process. an optimistic check there
  either silently drops work on conflict or must retry blindly, which
  reduces to Pessimistic Offline Lock's guarantees without its benefits.
- The data model genuinely has a single writer by construction, for example
  a per-session, per-user private draft that is never read or written by a
  second process. the version field adds bookkeeping cost with no
  corresponding safety benefit, because there is nothing to collide with.
- Regulatory or audit requirements demand that every read that will inform
  a later write be protected from the moment of read, not merely validated
  at write time, which is a pessimistic requirement by definition.

## 5. Structure

**System Transaction.** The short-lived database transaction that performs
the actual version check and the actual write. It is opened only at the
point of writing, never held open across the offline gap.

**Business Transaction.** The full, sometimes long-running unit of work
from the user's perspective, spanning a read, a period of no open database
transaction, and a later write. This is the span the pattern protects.

**Version Field.** A monotonically comparable value, most often an integer
counter or a timestamp, stored on the record being protected. It is read
alongside the business data and must be present in the write's WHERE clause
or condition expression.

**Conflict Detector.** The mechanism that compares the version read at the
start of the business transaction against the version currently stored, at
the moment of write. In a relational database this is an `UPDATE ... WHERE
id = ? AND version = ?` whose affected-row count reveals the outcome. In
HTTP this is the server evaluating the `If-Match` header against the
resource's current ETag before performing the write. In a document database
it is a compare against the document's revision token.

**Conflict Handler.** The code that runs when the Conflict Detector reports
zero rows changed, an `If-Match` failure, or an equivalent signal. Its job
is to translate a silent lost-update into a visible outcome the caller can act on,
most commonly by aborting the write, reloading the current state, and
surfacing the conflict to the caller.

## 6. ASCII structure diagram

```
+---------------------+          +----------------------+
|   Business           |          |   Record             |
|   Transaction        |          |   (in the database)  |
|-----------------------|          |-----------------------|
| reads Record           |------->|  id                  |
| holds a copy in        |          |  ...business data... |
| memory across think    |          |  version: N          |
| time, no DB lock held  |          +----------------------+
+---------------------+                     ^
        |                                   |
        | later, writes back                |
        v                                   |
+---------------------+          +----------------------+
|   Conflict           |          |   System             |
|   Detector            |<--------|   Transaction         |
|-----------------------|          |   (short lived,       |
| compares version read  |          |    opened only here)  |
| against version now     |          +----------------------+
| stored                  |
+---------------------+
        |
        +--- versions match -----> write proceeds, version incremented
        |
        +--- versions differ -----> Conflict Handler invoked
                                       |
                                       +--> abort write
                                       +--> reload current Record
                                       +--> surface conflict to caller
```

## 7. Dynamics

```
User A                 User B                 Database
  |                       |                       |
  |--- read record ------------------------------>|
  |<-- record, version=1 -------------------------|
  |                       |                       |
  |                       |--- read record ------->|
  |                       |<-- record, version=1 --|
  |                       |                       |
  |   (both users think, edit, no DB lock held)    |
  |                       |                       |
  |--- write, expect ver=1 ----------------------->|
  |                       |     UPDATE ... WHERE   |
  |                       |     id=X AND version=1 |
  |                       |     1 row affected     |
  |<-- success, version now 2 ---------------------|
  |                       |                       |
  |                       |--- write, expect ver=1 ->|
  |                       |     UPDATE ... WHERE   |
  |                       |     id=X AND version=1 |
  |                       |     0 rows affected,   |
  |                       |     actual version is 2 |
  |                       |<-- conflict detected --|
  |                       |                       |
  |                       |--- reload record, ---->|
  |                       |    version=2           |
  |                       |<-- current state ------|
  |                       |                       |
  |                (User B re-applies edit or       |
  |                 is shown a merge screen)         |
```

## 8. Implementation variants

**Version counter column.** A single integer column, incremented by exactly
one on every successful write, compared with strict equality. This is the
default JPA and Hibernate behaviour under `@Version`, described in the
Jakarta Persistence 3.1 Specification, section 3.4.2, Optimistic Locking,
https://jakarta.ee/specifications/persistence/3.1/, verified 2026-08-02, and
in the Hibernate ORM User Guide, chapter 15, Locking,
https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#locking-optimistic,
verified 2026-08-02. Its strength is that it is unambiguous, two writers
racing on the same version always produce a strict loser. Its weakness is
that a rolled-back client transaction still leaves the version unchanged,
so a counter alone reveals nothing about how many attempts were made.

**Timestamp version.** The version field is a last-modified timestamp
instead of a counter. This variant is common where the timestamp is also
used for auditing or caching, and where clock resolution is fine enough
that two genuinely concurrent writes are exceedingly unlikely to share the
identical stamp. Its risk is clock skew across application instances in a
distributed deployment, which can make two writes appear to have the same
or an out-of-order timestamp even when they did not race.

**Opaque token, ETag.** The version is an implementation-defined string the
client never interprets, only stores and returns unchanged, transported by
the HTTP `If-Match` request header and compared against the resource's
current `ETag` response header. RFC 9110, section 13.1.1, If-Match,
https://www.rfc-editor.org/rfc/rfc9110#name-if-match, verified 2026-08-02,
specifies that a server returns 412 Precondition Failed when the supplied
tag does not match the resource's current entity tag. This variant pushes
the mechanism to the transport layer, so it composes cleanly with a stateless
REST API and requires no dedicated database column if the server can derive
the ETag from an existing field, most often a hash of the resource body or a
last-modified timestamp.

**Document revision token.** In a document database the version is a
compound identifier combining a monotonic counter and a content hash, so
that divergent branches of the same logical document can be told apart even
after both increment the same counter. This is how Apache CouchDB's `_rev`
field works, in that every write must supply the current `_rev`, or the
exact wording of the API documentation, "specified revision is not latest
for target document", triggers an HTTP 409 Conflict, per Apache CouchDB
documentation, "Common Document API",
https://docs.couchdb.org/en/stable/api/document/common.html, verified
2026-08-02.

**Conditional expression, key-value stores.** In a key-value or wide-column
store with no built-in transaction isolation across a read-then-write gap,
the version check is expressed as a condition attached to the write request
itself rather than as a separate comparison step, so the check and the
write are atomic at the storage layer. Amazon DynamoDB implements this
through `ConditionExpression` on `PutItem` and `UpdateItem`, which returns a
`ConditionalCheckFailedException` when the expression evaluates to false,
per Amazon Web Services, "Working with Items and Attributes",
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html,
section "Conditional writes", verified 2026-08-02.

**Dirty field check instead of version field.** Rather than a single
version, the write's WHERE clause repeats the original values of every
column the transaction actually read, so the write only succeeds if none of
those specific fields changed. Fowler catalogues this as a distinct variant
under the same pattern, because it narrows the granularity of the conflict
check to only the fields the business transaction actually depended on,
trading a wider WHERE clause for fewer false-positive conflicts (Fowler,
*Patterns of Enterprise Application Architecture*, 2002, chapter 16,
Optimistic Offline Lock, https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html,
verified 2026-08-02).

## 9. Known production uses

**Jakarta Persistence (JPA) and Hibernate.** The `@Version` annotation is
part of the Jakarta Persistence specification itself, not a Hibernate
extension, and every persistence provider implementing the spec must
support it, throwing `jakarta.persistence.OptimisticLockException` when the
version comparison fails at flush time. Jakarta Persistence 3.1
Specification, Eclipse Foundation, section 3.4.2, Optimistic Locking,
https://jakarta.ee/specifications/persistence/3.1/, verified 2026-08-02.
Hibernate's own user guide documents the same mechanism as its default
optimistic locking strategy and also supports the dirty-field
variant through `OptimisticLockType.DIRTY`. Hibernate ORM 6.4 User Guide,
chapter 15, Locking, https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#locking-optimistic,
verified 2026-08-02.

**HTTP conditional requests, RFC 9110.** The `If-Match` request header and
the 412 Precondition Failed response together specify a transport-level
Optimistic Offline Lock usable by any HTTP API, independent of any
particular database or framework. RFC 9110, "HTTP Semantics", Internet
Engineering Task Force, June 2022, section 13.1.1, If-Match,
https://www.rfc-editor.org/rfc/rfc9110#name-if-match, verified 2026-08-02.
This mechanism underlies conditional updates in public HTTP APIs that
expose ETags on resources, an approach documented as the "Preventing Lost
Updates" use case for `If-Match` by the Mozilla Developer Network,
https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Match,
verified 2026-08-02.

**Apache CouchDB.** Every document carries a `_rev` field, and every update
must supply the revision it read, or the server rejects the write with
HTTP 409 Conflict and the message "specified revision is not latest for
target document". Apache CouchDB Documentation, "Common Document API",
https://docs.couchdb.org/en/stable/api/document/common.html, verified
2026-08-02. This makes CouchDB's Multi-Version Concurrency Control model a
built-in, non-optional instance of Optimistic Offline Lock at the storage
engine level, rather than an opt-in feature applications must add
themselves.

**Amazon DynamoDB conditional writes.** `PutItem` and `UpdateItem` accept a
`ConditionExpression`, and the standard pattern for optimistic concurrency
documented by AWS itself is to condition the write on the item's current
version attribute equalling the value the caller last read, returning
`ConditionalCheckFailedException` when a competing writer has already
advanced it. Amazon Web Services, "Working with Items and Attributes in
DynamoDB", section "Conditional writes",
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html,
verified 2026-08-02. The same document works through the canonical Alice
and Bob lost-update scenario to motivate the feature, which mirrors the
dynamics diagram in dimension 7 of this entry.

## 10. Consequences

Positive.

- No lock is held across user think time, so read throughput and read
  latency for every other concurrent user are unaffected by how long one
  user takes to edit and save.
- Lost updates become detectable and visible instead of silent, which is a
  strict correctness improvement over doing nothing at all.
- The mechanism composes cleanly with stateless application servers scaled
  application servers, because no server-side lock state has to be held or
  replicated between the read and the write, judgement based on the
  pattern's shape rather than a sourced claim.
- The cost of the mechanism, in the common case where no collision occurs,
  is a single extra column comparison in the WHERE clause or a single
  extra HTTP header, both close to free.

Negative.

- Completed work is discarded on conflict, and that work must either be
  manually redone by a user or automatically retried by application code
  that the team must still write and test.
- The version field is a shared mutable point of coupling across every
  write path to the row, and a write path that forgets to check or
  increment it silently defeats the pattern for that path with no error at
  the time the omission is introduced.
- Under high write contention on a single row, the pattern produces
  repeated failed round trips rather than any throughput improvement,
  judgement drawn from the pattern's core trade-off described in
  dimension 3, rather than a sourced claim.
- User experience for the losing transaction requires deliberate design,
  reloading the form, merging fields, or asking for confirmation, none of
  which the pattern itself provides, only the detection signal that makes
  such design possible.

## 11. Failure modes and misuse

**Silent conflict swallowing.** Symptom, a user reports that an edit they
made earlier is missing, with no error ever shown to them or to the other
user who overwrote it. Cause, the write path checks the version, catches
the `OptimisticLockException` or equivalent, and logs it or ignores it
without informing the caller or retrying. Fix, treat every conflict
detection as a mandatory branch in the write handler, either surfacing it
to the caller as a distinct error the UI must handle, or retrying with a
freshly reloaded version, never letting the exception disappear into a
generic catch-all.

**Version field bypassed by a second write path.** Symptom, conflicts stop
being detected for records touched by a particular batch job, admin tool,
or direct SQL script, even though the same records are protected correctly
when edited through the normal application flow. Cause, the alternate write
path issues an UPDATE that does not increment the version column, or worse,
writes to the table without going through the ORM entity at all. Fix,
either route every write path through the same persistence layer that
manages the version, or, where that is impractical, explicitly and
deliberately increment the version column in every write path that touches
the row, and add a test that exercises the conflict scenario against each
distinct write path.

**Retrying blindly without reloading.** Symptom, an automatic retry after a
conflict fails again immediately, or worse, silently overwrites the second
writer's change on the retry attempt. Cause, the retry logic resubmits the
exact same stale data with a bumped version number rather than reloading
the current record and reapplying the intended change to the fresh data.
Fix, a correct retry always re-reads the current state after a conflict and
reapplies the caller's intended delta to that fresh state, never simply
resends the original payload.

**Treating a distributed system's clock as a reliable version source.**
Symptom, two writes issued at effectively the same wall-clock instant from
different application server instances both succeed, producing a lost
update that the pattern was supposed to prevent. Cause, the timestamp
version variant relies on system clock resolution and ordering that can be
coarser than the actual write rate, or on clocks across instances that are
not perfectly synchronized. Fix, prefer a monotonic counter maintained by
the database itself, or a hash-based revision token, over a wall-clock
timestamp whenever multiple writer processes exist.

**Version supplied from the wrong scope.** Symptom, a user's save fails
with a conflict error even though no one else touched the record, on nearly
every save. Cause, the version the client supplies is stale for a reason
unrelated to a real conflict, most often a cached page, a back-button
navigation to an old form render, or a client that stores the version in a
long-lived session rather than refreshing it per request. Fix, tie the
carried version tightly to the specific form render or API response it came
from, and make any client-side cache invalidate it whenever the underlying
data might have changed for reasons other than the pattern's own protected
write.

## 12. Trade-off matrix

| Force | Optimistic Offline Lock | Pessimistic Offline Lock | Coarse-Grained Lock (as the granularity choice) |
|---|---|---|---|
| Latency added to concurrent readers | None, no lock held during think time | Readers can block behind the lock holder for the full duration of the business transaction | Depends on the granularity chosen, not a separate mechanism itself |
| Behaviour under high collision rate | Degrades, repeated failed writes and retries | Degrades gracefully into serialized access, no wasted write work | Reduces collision surface by aggregating checks, but does not change the underlying detection strategy |
| Failure visibility | Explicit, detected at write time and must be handled | Explicit, detected at lock-acquisition time, before any work is lost | Not applicable on its own, it is a granularity decision layered on top of either lock strategy |
| Operational complexity | Version field plus conflict-handling code in every write path | Lock table or lock manager, deadlock detection, and lock timeout policy | Adds bookkeeping to track which fields or aggregates share one version |
| Deadlock risk | None, there is no held lock to deadlock on | Present, and requires explicit deadlock detection or lock ordering discipline | Inherits the deadlock profile of whichever lock strategy it wraps |
| Best fit workload | Low collision rate, long think-time gaps, human-driven edits | High collision rate, or correctness demands that a conflict never even be attempted | Any workload where the natural unit of consistency spans multiple rows or fields |

Pessimistic Offline Lock is documented in Fowler, *Patterns of Enterprise
Application Architecture*, 2002, chapter 16, Pessimistic Offline Lock,
https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html, verified
2026-08-02, as the direct counterpart pattern this table compares against.
Coarse-Grained Lock is documented in the same chapter,
https://martinfowler.com/eaaCatalog/coarseGrainedLock.html, verified
2026-08-02, as an orthogonal granularity decision rather than a competing
locking strategy, which is why the table marks its own row differently from
the first two.

## 13. Related and incompatible patterns

**Unit of Work.** Fowler, *Patterns of Enterprise Application Architecture*,
2002, chapter 2, Base Patterns, Unit of Work, tracks the set of objects
changed by a business transaction so they can be written together. Unit of
Work is the natural place to attach the version-checking logic, because it
already knows which entities were read and are about to be written, and it
is the common integration point where ORMs implement `@Version` checking
automatically at flush time.

**Coarse-Grained Lock.** Directly composes with Optimistic Offline Lock by
answering the question of what unit the version field actually covers, a
single row, or an entire aggregate of related rows treated as one
consistency boundary. Choosing a coarser grain reduces the number of
distinct version fields to manage at the cost of more false-positive
conflicts between edits that do not actually overlap.

**Identity Map.** Fowler, *Patterns of Enterprise Application Architecture*,
2002, chapter 11, Object-Relational Behavioral Patterns, Identity Map,
keeps a single in-memory representative per database row within one
session. It composes with Optimistic Offline Lock because it is the
natural place to remember the version that was read, so the write path does
not need to separately track it.

**Pessimistic Offline Lock.** The direct alternative strategy for the same
problem, and the two are architecturally incompatible for the same record
within the same code path. A row's concurrency strategy is chosen once, in
that a system can use pessimistic locking for one hot table and optimistic
locking for another, cooler table, but mixing both strategies for the same
table produces confusing, hard-to-reason-about behaviour, because a
pessimistic lock holder assumes no one else can be mid-write, an
assumption an optimistic writer on the same row does not honour.

**Server Session State.** In a web application, a version carried across an
offline gap must live somewhere between requests, either round-tripped
through the client as a hidden field or ETag, or held in a server-side
session. Choosing to hold it server-side reintroduces some of the state
management concerns Optimistic Offline Lock otherwise avoids, and most
production implementations therefore prefer round-tripping it through the
client.

## 14. Refactoring path in and out

**Introducing the pattern into code without it.** Add a version column to
the table, or a version field to the aggregate root, initialised to a
starting value for every existing row in a single migration. Change every
existing write path for that table to include the version in its WHERE
clause or condition expression and to increment it on success, verifying
this with a targeted integration test that performs two concurrent writes
and asserts exactly one succeeds. Change every read path that will
eventually feed a write to carry the version forward, as a hidden form
field, a response header, or an entity field managed by the ORM. Add
explicit conflict-handling code at every write endpoint, so that the
transition from silent lost updates to detected conflicts does not simply
trade one failure mode, invisible data loss, for another, unhandled
exceptions surfacing as generic server errors. Roll this out one write path
at a time, verifying with the concurrent-write test at each step, rather
than converting an entire schema in one changeset.

**Removing the pattern.** Confirm, with real production data on write
frequency and collision rate for the specific table, that the collision
rate is negligible or that the table has become genuinely single-writer,
for example because a feature that allowed shared editing was removed.
Remove the version check from write paths only after confirming no client
still depends on the version field being present in its request or response
contract, since removing it from a public API is itself a breaking change
requiring its own deprecation path. Retain the version column briefly after
removal to allow rollback, then drop it in a later migration once the
removal has run in production without incident.

## 15. Testing and verification

What Optimistic Offline Lock makes easy to test is the conflict detection
itself, since it reduces to a deterministic, narrow assertion. read a
record, write it twice with two independently obtained copies of the
version, and assert the second write is rejected while the first succeeds.
This is a fast, reliable integration test against a real or embedded
database, with no need to simulate timing or thread interleaving, because
the two writes can be issued sequentially in the test and the version
mismatch alone triggers the rejection, whichever order the two writes
execute in.

What it makes harder to test is the conflict-handling user experience,
because that requires driving the system to the point of a genuine conflict
and then asserting on the resulting behaviour, error message, retry, or
reload, which needs either two cooperating test clients or an explicit test
seam that lets a single test thread simulate "someone else wrote to this
row" between the read and the write.

Useful techniques. A repository or data-access test double that lets a test
force a stale version onto a specific write call, without requiring an
actual second concurrent client, isolates the conflict-handling branch from
the database entirely. For the ORM-managed case, a test that flushes two
separate persistence contexts against the same row inside one test method,
committing the first before the second, reliably reproduces the exact
`OptimisticLockException` path a real two-user race would hit. For the HTTP
ETag variant, a contract test asserting that a `PUT` with a stale `If-Match`
value returns 412 Precondition Failed, and that a `PUT` with the current
value succeeds and returns a new `ETag`, verifies the protocol-level
behaviour independent of any particular database.

## 16. Observability signals

A healthy instance of this pattern shows a low, steady rate of detected
conflicts relative to total writes on the protected table or resource, with
that rate roughly tracking the application's actual concurrent-edit rate
rather than spiking independently of it. The signal to log at the moment of
detection is the entity identifier, the version the writer expected, and
the version actually found, which together let an operator distinguish a
genuine two-user race from a bug in a write path that forgot to advance the
version.

A dashboard tracking this pattern in production counts conflict events as a
distinct metric from generic write errors, because conflicts are an
expected, healthy part of the system's normal operation up to some baseline
rate, not an incident on their own. A sudden step change in the conflict
rate, rather than the raw count, is the signal worth alerting on, since it
points at either a new write path that bypasses the version check, a
client that stopped refreshing its cached version between renders, or a
genuine change in user behaviour such as a new feature that increased
concurrent editing of the same records.

A failing instance shows either a conflict rate near zero on a table that
is known to have concurrent editors, which suggests the check has been
silently defeated by a write path that no longer increments the version, or
a conflict rate that keeps climbing under otherwise steady load, which
suggests the workload has crossed from the optimistic pattern's applicable
range into the collision-heavy range this entry's dimension 4 describes as
non-applicable.

## 17. Security and privacy implications

The version field itself carries no sensitive information in the common
case, being either a monotonic integer or an opaque hash, and exposing it
to the client is standard and expected for the pattern to function, so
this dimension is largely quiet with respect to data confidentiality.

One implication worth naming plainly, as engineering judgement rather than a
sourced claim, is that a version or ETag value is a legitimate input the
server must still validate for shape and origin, since it arrives from an
untrusted client, even though it is opaque, so that a malformed or forged
version value produces a clean rejection rather than an unhandled error or,
worse, a code path that mistakenly treats a malformed value as a wildcard
match and performs an unconditional write. The `If-Match: *` form defined in
RFC 9110, section 13.1.1, https://www.rfc-editor.org/rfc/rfc9110#name-if-match,
verified 2026-08-02, is explicitly a wildcard meaning any current
representation, and an implementation must not confuse a missing or
malformed specific tag with that wildcard form, or it accidentally grants
an unconditional write where a conditional one was intended.

A second, narrower implication concerns information disclosure through
conflict responses. returning the full current state of a record inside a
conflict error, so the caller can see what changed, is convenient for
building a merge UI, but it does mean the conflict-handling code path is now
also a read path and must be checked against the same authorization rules
as any other read, rather than being treated as an error branch exempt from
access control review.

## 18. References

1. Martin Fowler, "Optimistic Offline Lock", martinfowler.com,
   https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html, verified
   2026-08-02.
2. Martin Fowler, "Pessimistic Offline Lock", martinfowler.com,
   https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html, verified
   2026-08-02.
3. Martin Fowler, "Coarse-Grained Lock", martinfowler.com,
   https://martinfowler.com/eaaCatalog/coarseGrainedLock.html, verified
   2026-08-02.
4. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 16, Concurrency Patterns, and chapter 2,
   Base Patterns, Unit of Work, and chapter 11, Object-Relational Behavioral
   Patterns, Identity Map.
5. H. T. Kung and John T. Robinson, "On Optimistic Methods for Concurrency
   Control", ACM Transactions on Database Systems, Volume 6, Issue 2, June
   1981, pages 213 to 226.
6. Eclipse Foundation, Jakarta Persistence 3.1 Specification, section
   3.4.2, Optimistic Locking, https://jakarta.ee/specifications/persistence/3.1/,
   verified 2026-08-02.
7. Hibernate ORM 6.4 User Guide, chapter 15, Locking,
   https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#locking-optimistic,
   verified 2026-08-02.
8. Internet Engineering Task Force, RFC 9110, "HTTP Semantics", June 2022,
   section 13.1.1, If-Match, https://www.rfc-editor.org/rfc/rfc9110#name-if-match,
   verified 2026-08-02.
9. Mozilla Developer Network, "If-Match",
   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Match,
   verified 2026-08-02.
10. Apache CouchDB Documentation, "Common Document API",
    https://docs.couchdb.org/en/stable/api/document/common.html, verified
    2026-08-02.
11. Amazon Web Services, "Working with Items and Attributes in DynamoDB",
    section "Conditional writes",
    https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html,
    verified 2026-08-02.

## Code examples

Optimistic Offline Lock is idiomatic wherever a language has either a
mainstream ORM with built-in version support, or a client for a store that
exposes conditional writes as a first class feature. TypeScript, Python, and Java are shown
below because each represents a distinct variant, a raw SQL version check
against a relational store, a version check against an in-memory store
standing in for a document database's revision token, and the ORM-managed
`@Version` field respectively. Go is shown as a fourth example using the
raw SQL variant against SQLite to demonstrate the pattern with no ORM at
all. Rust and Swift are omitted from working code here because the pattern
adds no language-specific idiom beyond what a version comparison and a
conditional write already express, and a fifth and sixth near-identical raw
SQL example would not demonstrate a new variant, only repeat the Go example
in a different syntax.

### TypeScript, raw SQL version column against SQLite

```typescript
import { DatabaseSync } from "node:sqlite";

interface Account {
  id: number;
  balance: number;
  version: number;
}

class ConflictError extends Error {
  constructor(id: number) {
    super(`Conflict updating account ${id}, version changed`);
  }
}

class AccountRepository {
  constructor(private db: DatabaseSync) {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        balance INTEGER NOT NULL,
        version INTEGER NOT NULL
      )
    `);
  }

  read(id: number): Account {
    const stmt = this.db.prepare(
      "SELECT id, balance, version FROM accounts WHERE id = ?"
    );
    const row = stmt.get(id) as Account | undefined;
    if (!row) throw new Error(`No account ${id}`);
    return row;
  }

  applyDeposit(read: Account, amount: number): void {
    const stmt = this.db.prepare(
      `UPDATE accounts
       SET balance = balance + ?, version = version + 1
       WHERE id = ? AND version = ?`
    );
    const result = stmt.run(amount, read.id, read.version);
    if (result.changes === 0) {
      throw new ConflictError(read.id);
    }
  }
}

function main() {
  const db = new DatabaseSync(":memory:");
  const repo = new AccountRepository(db);
  db.exec("INSERT INTO accounts (id, balance, version) VALUES (1, 100, 1)");

  const readByA = repo.read(1);
  const readByB = repo.read(1);

  repo.applyDeposit(readByA, 50);
  console.log("A succeeded, new balance:", repo.read(1).balance);

  try {
    repo.applyDeposit(readByB, 30);
  } catch (e) {
    if (e instanceof ConflictError) {
      console.log("B correctly rejected:", e.message);
    } else {
      throw e;
    }
  }
}

main();
```

### Python, revision token against an in-memory store standing in for a document database

```python
from dataclasses import dataclass, replace
from typing import Dict


class ConflictError(Exception):
    def __init__(self, doc_id: str):
        super().__init__(f"Conflict updating {doc_id}, revision changed")


@dataclass(frozen=True)
class Document:
    doc_id: str
    body: dict
    rev: str


class DocumentStore:
    def __init__(self):
        self._docs: Dict[str, Document] = {}
        self._counter = 0

    def put_initial(self, doc_id: str, body: dict) -> Document:
        self._counter += 1
        doc = Document(doc_id, body, rev=f"1-{self._counter}")
        self._docs[doc_id] = doc
        return doc

    def get(self, doc_id: str) -> Document:
        return self._docs[doc_id]

    def update(self, expected: Document, new_body: dict) -> Document:
        current = self._docs.get(expected.doc_id)
        if current is None or current.rev != expected.rev:
            raise ConflictError(expected.doc_id)
        self._counter += 1
        gen = int(expected.rev.split("-")[0]) + 1
        updated = replace(
            current, body=new_body, rev=f"{gen}-{self._counter}"
        )
        self._docs[expected.doc_id] = updated
        return updated


def main() -> None:
    store = DocumentStore()
    store.put_initial("order-42", {"status": "pending"})

    read_by_a = store.get("order-42")
    read_by_b = store.get("order-42")

    store.update(read_by_a, {"status": "shipped"})
    print("A succeeded, doc now:", store.get("order-42"))

    try:
        store.update(read_by_b, {"status": "cancelled"})
    except ConflictError as e:
        print("B correctly rejected:", e)


if __name__ == "__main__":
    main()
```

### Java, ORM-style `@Version` field with explicit version checking, no framework dependency

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

final class OptimisticLockException extends RuntimeException {
    OptimisticLockException(long id) {
        super("Conflict updating entity " + id + ", version changed");
    }
}

final class Invoice {
    final long id;
    final int amountCents;
    final long version;

    Invoice(long id, int amountCents, long version) {
        this.id = id;
        this.amountCents = amountCents;
        this.version = version;
    }
}

final class InvoiceRepository {
    private final Map<Long, Invoice> storage = new HashMap<>();

    void save(Invoice invoice) {
        storage.put(invoice.id, invoice);
    }

    Optional<Invoice> find(long id) {
        return Optional.ofNullable(storage.get(id));
    }

    synchronized void update(Invoice readCopy, int newAmount) {
        Invoice current = storage.get(readCopy.id);
        if (current == null || current.version != readCopy.version) {
            throw new OptimisticLockException(readCopy.id);
        }
        Invoice updated = new Invoice(
            readCopy.id, newAmount, current.version + 1
        );
        storage.put(readCopy.id, updated);
    }
}

public class OptimisticOfflineLockDemo {
    public static void main(String[] args) {
        InvoiceRepository repo = new InvoiceRepository();
        repo.save(new Invoice(1L, 10000, 1L));

        Invoice readByA = repo.find(1L).orElseThrow();
        Invoice readByB = repo.find(1L).orElseThrow();

        repo.update(readByA, 12000);
        System.out.println(
            "A succeeded, new amount: "
            + repo.find(1L).orElseThrow().amountCents
        );

        try {
            repo.update(readByB, 9000);
        } catch (OptimisticLockException e) {
            System.out.println("B correctly rejected: " + e.getMessage());
        }
    }
}
```

### Go, conditional write equivalent to `UPDATE ... WHERE version = ?`, no external driver

The store below stands in for a relational table row. The mutex plus the
explicit version comparison inside `ApplyDeposit` is the same shape a raw
`database/sql` driver produces through `res.RowsAffected()` after an
`UPDATE ... WHERE id = ? AND version = ?`, kept dependency free here so the
example compiles with the standard library alone.

```go
package main

import (
	"errors"
	"fmt"
	"sync"
)

type Account struct {
	ID      int64
	Balance int64
	Version int64
}

var ErrConflict = errors.New("conflict, version changed")

type AccountStore struct {
	mu       sync.Mutex
	accounts map[int64]Account
}

func NewAccountStore() *AccountStore {
	return &AccountStore{accounts: make(map[int64]Account)}
}

func (s *AccountStore) Insert(a Account) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.accounts[a.ID] = a
}

func (s *AccountStore) Read(id int64) (Account, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	a, ok := s.accounts[id]
	if !ok {
		return Account{}, fmt.Errorf("no account %d", id)
	}
	return a, nil
}

func (s *AccountStore) ApplyDeposit(read Account, amount int64) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	current, ok := s.accounts[read.ID]
	if !ok || current.Version != read.Version {
		return ErrConflict
	}
	current.Balance += amount
	current.Version++
	s.accounts[read.ID] = current
	return nil
}

func main() {
	store := NewAccountStore()
	store.Insert(Account{ID: 1, Balance: 100, Version: 1})

	readByA, err := store.Read(1)
	if err != nil {
		panic(err)
	}
	readByB, err := store.Read(1)
	if err != nil {
		panic(err)
	}

	if err := store.ApplyDeposit(readByA, 50); err != nil {
		panic(err)
	}
	after, _ := store.Read(1)
	fmt.Println("A succeeded, new balance:", after.Balance)

	err = store.ApplyDeposit(readByB, 30)
	if errors.Is(err, ErrConflict) {
		fmt.Println("B correctly rejected:", err)
	} else if err != nil {
		panic(err)
	}
}
```
