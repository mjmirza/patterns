---
name: Coarse-Grained Lock
slug: coarse-grained-lock
family: 06-enterprise-application-architecture
category: Concurrency
aliases: [Root Lock, Aggregate Lock, Root Version]
first_described: "Rice, Foemmel in Fowler et al. 2002"
maturity: canonical
related: [optimistic-offline-lock, pessimistic-offline-lock, unit-of-work, identity-map, aggregate]
incompatible_with: []
verified: 2026-08-02
---

# Coarse-Grained Lock

## 1. Name, aliases, and lineage

The canonical name is Coarse-Grained Lock. It is catalogued in Martin Fowler,
*Patterns of Enterprise Application Architecture*, Addison-Wesley, 2002,
chapter 16 (Concurrency), with the entry itself credited to David Rice and Matt
Foemmel, two of the pattern contributors Fowler names for the concurrency
chapter. The published web summary of the entry states the intent plainly,
in one sentence. "Locks a set of related objects with a single lock"
([Fowler, catalog page, Coarse-Grained Lock](https://martinfowler.com/eaaCatalog/coarseGrainedLock.html),
verified 2026-08-02). The same page names the worked example the book uses,
a customer object together with its dependent address objects, locked as one
unit rather than address by address.

The pattern has no single competing name the way some entries do, but three
terms are used interchangeably for the same mechanism in practitioner writing
and in framework documentation, and it helps to keep them apart.

- **Coarse-Grained Lock (Fowler, book term).** A single version number or a
  single database row lock, held on behalf of an entire object graph rooted
  at one designated object, so that any change anywhere in the graph is
  detected, or blocked, through that one point.
- **Root Lock (practitioner shorthand).** The same idea, named after the
  object that holds the lock rather than after the scope it covers. Common in
  Domain-Driven Design writing, where the locked object is called the
  aggregate root.
- **Aggregate Lock.** Used interchangeably with Root Lock in Domain-Driven
  Design writing, tying the concurrency mechanism directly to Eric Evans's
  aggregate concept, where a group of associated objects is treated as one
  unit for the purpose of data changes
  (Vaughn Vernon, "Effective Aggregate Design, Part I. Modeling a Single
  Aggregate",
  [dddcommunity.org, 2011](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf),
  verified 2026-08-02, states the rule that a single transaction should
  modify only one aggregate instance).

Coarse-Grained Lock is not itself a locking algorithm. It is a scoping
decision layered on top of one of two algorithms that Fowler catalogs in the
same chapter, Optimistic Offline Lock (a version number compared at commit
time) or Pessimistic Offline Lock (an explicit lock record acquired before
editing begins). The contribution of Coarse-Grained Lock is answering a
question those two patterns leave open, namely what the lock covers. Reading
Coarse-Grained Lock as a third, independent locking mechanism is the most
common misreading of the name, addressed again in dimension 11.

## 2. Problem and context

An object graph in an enterprise application is rarely a single row. A
customer has addresses. An order has line items. A purchase order has
approval steps. A shopping cart has line items and a coupon. In every one of
these, the objects form one conceptually coherent unit from the point of view
of the business rule that governs them, and they are usually loaded,
displayed, and edited together in a single screen or a single API call.

The naive translation of "protect this data from concurrent conflicting
writes" into code is to protect every persistent object individually. Give
the `Address` table its own version column. Give the `Customer` table its own
version column. Check both, independently, before saving either. This looks
correct at first read and starts to fail as soon as three things happen
together, all of which are ordinary in a real system.

- A screen edits a customer's name and, in the same save, adds a new address.
  The new address has no prior version to compare against, so the
  address-level check cannot detect a conflict on the address at all, only
  on the customer.
- A second user, in a second session, deletes one of the customer's existing
  addresses at the same moment the first user is adding a new one. Neither
  edit touches a row the other edit also touches, so neither individual,
  fine-grained version check fires, and the business invariant that a
  customer must have at least one billing address can be silently violated
  by two edits that are each, in isolation, valid.
- The screen needs to discover every object it must lock before it can even
  start editing. For a customer with a deep object graph, address, phone
  numbers, preferences, that lookup step means walking and loading the
  entire graph before a single lock can be checked, which is exactly the
  performance cost Fowler's catalog page calls out as the first reason to
  avoid fine-grained locking (Fowler, catalog page,
  [Coarse-Grained Lock](https://martinfowler.com/eaaCatalog/coarseGrainedLock.html),
  verified 2026-08-02).

The context in which Coarse-Grained Lock earns its place has three
properties present at the same time. There is a natural cluster of objects
that are always loaded, edited, and saved together as one conceptual unit.
The business invariants that matter span more than one object in that
cluster, so a lock or version check confined to a single object cannot detect
every conflict that matters. And the application already has, or can
identify, one member of the cluster that is a natural anchor, a root, from
which every other member is reachable by navigation. Outside that context, in
particular where objects in the cluster are genuinely edited independently by
different users at different times, forcing them under one lock trades a
real problem for a worse one, contention on objects that never needed to be
serialized against each other at all.

## 3. Forces

- **Consistency.** Favoured, and this is the whole reason to reach for the
  pattern. A single version check, or a single lock acquisition, on the root
  detects any conflicting change anywhere in the graph, including additions
  and deletions that fine-grained per-object checks cannot see, because a
  newly inserted or newly deleted row has no prior version of its own to
  compare.
- **Concurrency and throughput.** Sacrificed, deliberately and by design.
  Two edits that touch different members of the same locked cluster, and
  that would have been safe to apply concurrently under fine-grained
  locking, are now serialized against each other because they share one
  lock. The pattern trades throughput for correctness at cluster
  boundaries, and the size of that trade is set entirely by where the
  cluster boundary is drawn.
- **Lookup cost.** Favoured. Fine-grained locking needs code that finds
  every object in the graph before it can lock any of them, an expensive
  walk when the graph is large or when it spans a lazy-loaded object-relational
  mapping. Coarse-Grained Lock needs to find, and lock, exactly one object,
  the root, and the version or lock record for the whole cluster travels
  with it.
- **Lock table size.** Favoured, when the underlying algorithm is
  Pessimistic Offline Lock. One lock record per cluster is dramatically
  cheaper to hold, scan, and expire than one lock record per member object,
  which matters directly for lock table contention under load.
- **Coupling between objects.** Increased. Members of the cluster now share
  fate at the concurrency layer even where they had no coupling at the
  domain layer. A phone number and a billing address on the same customer
  become concurrency-coupled purely because they share a root, which is
  correct when the business invariant genuinely spans them and wrong when
  it does not.
- **Boundary correctness.** This is the force the pattern is most sensitive
  to and the one the catalog is quietest about. Drawing the cluster boundary
  too wide serializes work that should be independent. Drawing it too
  narrow reintroduces the exact conflict-blindness the pattern exists to
  remove. There is no mechanical rule for finding the right boundary, only
  the domain's own transactional invariants, which is why Domain-Driven
  Design ties the same boundary decision to the aggregate concept rather
  than treating it as a purely technical choice (Vernon, "Effective
  Aggregate Design, Part I",
  [dddcommunity.org, 2011](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf),
  verified 2026-08-02).
- **Simplicity of the check itself.** Favoured. One version number, one
  comparison, one place in the code that decides whether a save proceeds.
  Fine-grained locking multiplies that decision point by the number of
  object types in the cluster.

## 4. Applicability and non-applicability

Reach for Coarse-Grained Lock when the following hold together.

- A group of objects is always loaded, edited, and persisted together, in
  the same conversation or the same request, and never independently.
- A business invariant spans more than one object in the group, so a lock
  or version check confined to a single object cannot detect every conflict
  that matters, including additions to and removals from the group.
- One member of the group is a natural root, reachable to and from every
  other member, and already carries, or can be given, an identity that the
  rest of the persistence layer can key a version or a lock record on.
- The write rate to different members of the same group, from different
  users, at the same time, is low enough that serializing those writes
  against each other does not become the throughput bottleneck of the
  system.

Do NOT reach for Coarse-Grained Lock when any of these hold.

- The objects in the candidate group are, in fact, edited independently by
  different actors on different timelines, for example two line items on a
  large shared purchase order maintained by different departments. Forcing
  them under one root lock manufactures contention between edits that were
  never in conflict, which is the opposite of what locking exists to
  provide, per the trade-off Fowler's catalog frames the whole pattern
  around
  ([Fowler, catalog page](https://martinfowler.com/eaaCatalog/coarseGrainedLock.html),
  verified 2026-08-02).
- The group is large and write-heavy, and the business invariants that
  actually need protecting are local to small subsets of it. In that case a
  smaller aggregate boundary, or several smaller coarse-grained locks, each
  scoped to the actual invariant, out-performs and out-scales one lock over
  the whole group. Vernon's aggregate-design guidance states this directly
  as a design rule, favour small aggregates, not one large one, precisely
  because a large aggregate over-serializes unrelated writes (Vernon,
  "Effective Aggregate Design, Part I",
  [dddcommunity.org, 2011](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf),
  verified 2026-08-02).
- The system has no natural root object, the objects form a graph with
  several equally valid entry points, or membership in the group changes
  based on which use case is running. Bolting an artificial root onto such
  a graph purely to hang a lock on it adds a structural concept the domain
  does not actually have.
- Reads far outnumber writes, and writes are rare enough that the conflict window
  fine-grained locking misses in practice never fires. Adding the pattern's
  coupling and serialization cost ahead of a real, observed conflict is
  solving a problem that has not shown up yet.
- The underlying store already provides row-range or table-partition
  locking that achieves the same effect at the storage layer, for example a
  clustered index range lock that covers a customer and its dependent rows
  by physical co-location. Layering an application-level coarse-grained
  lock on top duplicates a guarantee the store already gives, at extra
  application complexity.

## 5. Structure

- **Root.** The single designated member of the object cluster that the
  lock or version is attached to. Every other member of the cluster is
  reachable from the root by navigation, and the root's identity is the key
  used to acquire the lock or to store the version.
- **Dependent members.** The rest of the objects in the cluster. They do not
  carry their own version or lock record for this purpose. Any change to a
  dependent member, including creating a new one or deleting an existing
  one, is required to also touch the root's version so the shared lock
  detects the change.
- **Lock manager or version store.** The mechanism that actually enforces
  exclusivity or detects conflict. Under Optimistic Offline Lock this is a
  version column read at load time and compared, and incremented, at
  commit time. Under Pessimistic Offline Lock this is an explicit lock
  table row keyed by the root's identity, acquired before editing begins
  and released on commit or rollback.
- **Version propagation path.** The code path, whether hand-written,
  framework-supplied, or unit-of-work-driven, that guarantees a change to
  any dependent member forces the root's version forward, or forces the
  root's lock record to be touched. This path is the part of the
  implementation most often missing when the pattern fails silently, see
  dimension 11.
- **Save participant or Unit of Work.** The transaction boundary that
  collects every change to the cluster, root and dependents together, and
  applies the single version check, or the single lock acquisition and
  release, exactly once per save, rather than once per object touched.

## 6. ASCII structure diagram

```
                 +-------------------------------+
                 |            Customer            |  <- root
                 |  id = 4471                      |
                 |  version = 7                    |  <- one version for
                 +---------------+-----------------+     the whole cluster
                                 |
              +------------------+------------------+
              |                                     |
    +---------v---------+               +-----------v---------+
    |      Address       |               |     PhoneNumber      |
    |  id = A-1           |               |  id = P-1              |
    |  (no own version)   |               |  (no own version)     |
    +---------------------+               +------------------------+

    A change to Address A-1, PhoneNumber P-1, or Customer 4471 itself
    all bump Customer.version. A save that reads Customer.version = 7
    and finds it is still 7 at commit time is the ONLY check performed,
    for every object in the graph.
```

## 7. Dynamics

```
User A session                 Root lock / version store          User B session
      |                                    |                              |
      | load Customer 4471                 |                              |
      | (graph = address, phone)           |                              |
      |<-- version = 7 -------------------|                              |
      |                                    |                              |
      |                                    |         load Customer 4471   |
      |                                    |<--------------------------- |
      |                                    |-- version = 7 -------------->|
      |                                    |                              |
      | edit Address A-1                   |                              |
      |                                    |          edit PhoneNumber P-1|
      | save (root version still 7)        |                              |
      |----------------------------------->|                              |
      | check stored version == 7? yes     |                              |
      | commit, version -> 8               |                              |
      |<-- OK -----------------------------|                              |
      |                                    |       save (sends version 7) |
      |                                    |<----------------------------|
      |                                    | check stored version == 7?  |
      |                                    | NO, stored version is now 8. |
      |                                    |----------------------------->|
      |                                    |    StaleObjectStateException |
```

Under Pessimistic Offline Lock the same diagram changes shape at the edges.
User A's load acquires an exclusive lock record keyed by Customer 4471
before editing begins. User B's load blocks, or fails immediately, at that
same acquisition point rather than being allowed to proceed and only being
told about the conflict at save time. The scoping decision, one lock for
the whole cluster keyed on the root, is identical either way, only the
moment of detection moves earlier.

## 8. Implementation variants

- **Version-number propagation (the most common variant).** The root
  carries an integer or timestamp version column. Every write path that
  touches a dependent member is required to also mark the root dirty, so
  the unit of work increments the root's version on commit regardless of
  which specific member actually changed. This is the variant Fowler's
  catalog worked example uses, and it composes directly with Optimistic
  Offline Lock
  ([Fowler, catalog page](https://martinfowler.com/eaaCatalog/coarseGrainedLock.html),
  verified 2026-08-02).
- **Timestamp-touch propagation.** Instead of an integer version, the root
  carries a last-modified timestamp, and any save of a dependent member
  updates that timestamp as a side effect. Ruby on Rails implements exactly
  this as a first-class association option (`belongs_to :customer, touch: true`
  on the dependent). Its documentation states that if true, the associated
  object will be touched (the `updated_at` / `updated_on` attributes set to
  current time) when this record is either saved or destroyed
  ([Rails API documentation, `ActiveRecord::Associations::ClassMethods`,
  `belongs_to`](https://api.rubyonrails.org/classes/ActiveRecord/Associations/ClassMethods.html),
  verified 2026-08-02). This is a lighter-weight relative of Coarse-Grained
  Lock, it detects that the root's cluster changed, without alone giving a
  monotonic count or a hard conflict exception, so it is most often paired
  with a separate optimistic-locking column on the root for the actual
  conflict check, with the touch behaviour used to keep caches and derived
  views coherent with the same cluster boundary.
- **Explicit root-scoped lock record.** Under Pessimistic Offline Lock, the
  lock table stores one row keyed by the root's identity and type, never
  one row per dependent object. Acquiring, checking, and releasing that one
  row is the entire locking protocol for the cluster.
- **Framework-level per-entity optimistic locking, applied deliberately at
  the root only.** Object-relational mapping tools such as Hibernate ORM
  give every mapped entity its own optimistic-locking configuration
  independently, through `OptimisticLockType.NONE`, `VERSION`, `DIRTY`, or
  `ALL`. `ALL` means "optimistic locking based on all fields of the
  entity", every field of the entity is included in the comparison clause,
  while `DIRTY` restricts that comparison to the fields that actually
  changed
  ([Hibernate ORM Javadoc, `org.hibernate.annotations.OptimisticLockType`](https://docs.hibernate.org/orm/current/javadocs/org/hibernate/annotations/OptimisticLockType.html),
  verified 2026-08-02). Hibernate does not, by itself, decide which entity
  in a graph is the coarse-grained root. That decision, and the discipline
  of mapping only the root with a `@Version` column while dependents are
  mapped without one and are only ever reached through the root, is applied
  by the application's own mapping, following the same pattern.
- **Version comparison via a dedicated field on the root, checked by the
  ORM's flush, in Doctrine ORM.** Its documentation states, "when changes to
  such an entity are persisted at the end of a long-running conversation the
  version of the entity is compared to the version in the database and if
  they don't match, an `OptimisticLockException` is thrown", and the version
  check runs on `EntityManager#flush()`
  ([Doctrine ORM documentation, "Transactions and Concurrency"](https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/transactions-and-concurrency.html),
  verified 2026-08-02). Doctrine, like Hibernate, versions individual
  entities. Scoping the version field to the aggregate root and to no other
  entity in the graph is the application's own design choice, which is the
  variant this pattern names.

## 9. Known production uses

- **Ruby on Rails, `ActiveRecord::Associations`, the `touch` option on
  `belongs_to`.** A first-class, documented association option that propagates a
  change on a dependent record up to a designated parent's timestamp,
  making the parent the detectable anchor for changes anywhere in its
  associated cluster
  ([Rails API documentation, `belongs_to`](https://api.rubyonrails.org/classes/ActiveRecord/Associations/ClassMethods.html),
  verified 2026-08-02).
- **Hibernate ORM.** Its `@Version` annotation and `OptimisticLockType`
  configuration give application code the exact per-entity building block
  the coarse-grained variant relies on, mapping the version field onto only
  the aggregate root while dependents are versioned implicitly through it
  ([Hibernate ORM Javadoc, `OptimisticLockType`](https://docs.hibernate.org/orm/current/javadocs/org/hibernate/annotations/OptimisticLockType.html),
  verified 2026-08-02).
- **Doctrine ORM.** The same building block, a `#[Version]` field checked
  automatically on flush and throwing `OptimisticLockException` on
  mismatch, used across PHP applications built on Symfony and Doctrine to
  scope optimistic locking to a chosen entity rather than to every entity
  in a graph
  ([Doctrine ORM documentation, "Transactions and Concurrency"](https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/transactions-and-concurrency.html),
  verified 2026-08-02).
- **Domain-Driven Design aggregate practice.** Vaughn Vernon's widely cited
  aggregate-design guidance names the aggregate root as the transactional
  and consistency boundary for its whole cluster, stating the rule that a
  single transaction should modify only one aggregate instance, which is
  the same design decision Coarse-Grained Lock names from the persistence
  side rather than the domain-modelling side
  ([Vernon, "Effective Aggregate Design, Part I", dddcommunity.org, 2011](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf),
  verified 2026-08-02).

## 10. Consequences

Positive.

- One check, or one lock acquisition, detects every conflicting change in
  the cluster, including additions and deletions that per-object,
  fine-grained checks cannot see because the new or removed row has no
  prior version of its own to compare against.
- Lookup cost drops from walking the entire graph to find every lockable
  object down to loading and locking exactly one object, the root.
- The lock table, under Pessimistic Offline Lock, holds one row per
  cluster instead of one row per member object, which reduces contention on
  the lock table itself under concurrent load.
- The concurrency-control code has exactly one place to look, the root's
  version or lock record, which simplifies auditing whether a given save
  actually checked for conflicts.

Negative.

- Writes to different, genuinely independent members of the same cluster
  are serialized against each other even when their invariants never
  overlap, reducing throughput for exactly the workloads where two users
  edit two different dependents of the same root at the same time.
- The version-propagation path becomes a correctness-critical piece of
  code that must be exercised on every write path that touches any
  dependent, and a single write path that forgets to mark the root dirty
  silently reintroduces the conflict blindness the pattern exists to
  remove, see dimension 11.
- Choosing the wrong cluster boundary is expensive to fix later. Members
  added to, or removed from, the locked cluster after other code has
  already been written against the old boundary require touching every
  write path that reaches those members.
- The root becomes a hot object under load, since every write anywhere in
  the cluster now also writes to the root, which can turn a previously
  quiet row into a contended one purely as a side effect of adopting the
  pattern.

## 11. Failure modes and misuse

Judgement. The symptoms below are drawn from common experience with the
pattern rather than sourced from a single publication, and are stated as
symptom, cause, fix triples so the diagnosis can be acted on directly.

Symptom. A save of a newly added dependent object succeeds silently even
though another user concurrently removed the entire cluster the dependent
belongs to.
Cause. The write path that creates the new dependent forgot to also mark
the root dirty, so the root's version was never checked or incremented for
that save, and the coarse-grained lock never engaged for this one code
path.
Fix. Audit every write path that reaches a dependent member, not only the
paths that update an existing one, and route every one of them through the
same unit-of-work step that bumps the root's version. Treat whether a
change touches the root as a required item in code review for any change
inside the cluster.

Symptom. Two users editing two unrelated dependents of the same root, for
example one editing a customer's phone number and the other editing an
unrelated address on the same customer, repeatedly see stale-version
conflicts and one of them loses work on every collision.
Cause. The cluster boundary was drawn too wide. The two edits never
actually conflict at the level of the business invariant, but they are
forced to share one lock because they share one root.
Fix. Reconsider the aggregate boundary. Either split the cluster into two
smaller, independently versioned roots that each cover only the objects
whose invariants genuinely span them, or accept the throughput cost as a
deliberate trade, documented, rather than an accident.

Symptom. Performance degrades specifically on the customer or order table,
even though the actual edits users are making are almost entirely to line
items or addresses, and the root table itself is rarely read for its own
data.
Cause. The root has become a hot row purely because it now absorbs a write
on every change anywhere in its cluster, which is the direct cost named in
dimension 10 and is expected, but was not sized for in capacity planning.
Fix. Confirm the boundary is still correct, then address the hot-row cost
directly, for example by moving the version column to a lightweight
sidecar row that is written on every dependent change instead of writing
the full root record, so the frequently-read parts of the root are not
also the frequently-written parts.

Symptom. Code review or a new team member treats Coarse-Grained Lock as a
distinct locking algorithm and tries to implement it independently of
Optimistic Offline Lock or Pessimistic Offline Lock, inventing a third,
ad-hoc conflict-detection mechanism.
Cause. The pattern name is read as naming an algorithm rather than naming a
scoping decision layered on top of one of the two algorithms Fowler's same
chapter already defines.
Fix. Point back to dimension 1. Coarse-Grained Lock answers what the lock
covers, Optimistic Offline Lock and Pessimistic Offline Lock each answer
how the check is performed. Pick one of the two algorithms, then apply it
at the scope the Coarse-Grained Lock decision names.

Symptom. A batch job or an administrative script bypasses the application's
normal save path, for example writing directly to a dependent table with
raw SQL, and production incidents follow where legitimate user edits are
silently overwritten with no exception raised.
Cause. The bypassing write never touches the root, so the coarse-grained
version check has nothing to compare against for that write and the
conflict is invisible to every other session that is following the
pattern correctly.
Fix. Route every write path, including operational and batch tooling,
through the same layer that owns the version-propagation logic, or, where
that is genuinely impossible, treat the bypass as an explicit, documented
exception and add a separate reconciliation check that can detect drift
introduced outside the normal path.

## 12. Trade-off matrix

Compared against the two named alternatives from the same catalog chapter,
per-object Optimistic Offline Lock and per-object Pessimistic Offline Lock,
across the forces named in dimension 3.

| Force | Coarse-Grained Lock (root-scoped) | Per-object Optimistic Offline Lock | Per-object Pessimistic Offline Lock |
|---|---|---|---|
| Detects additions and deletions in the cluster | Yes, through the root's version | No, a newly inserted or deleted row has no prior version to compare | No, same gap, unless an explicit lock is separately taken for the container |
| Lookup cost before locking | One object, the root | Must find and check every member individually | Must find and lock every member individually |
| Lock table size (pessimistic variant) | One row per cluster | Not applicable | One row per member object |
| Independent-edit throughput within the cluster | Lower, all writes serialize against one version | Higher, unrelated members do not contend | Lower still, blocking rather than detecting late |
| Correctness sensitivity to cluster boundary | High, wrong boundary either over-serializes or misses conflicts | Low, boundary is implicitly one row | Low, same |
| Implementation complexity | Moderate, needs a propagation path from every dependent write to the root | Low, each object's check is local to itself | Low to moderate, needs lock acquisition and release discipline |

## 13. Related and incompatible patterns

- **Optimistic Offline Lock.** The most common algorithm Coarse-Grained
  Lock is layered on top of. Optimistic Offline Lock supplies the
  version-comparison mechanism. Coarse-Grained Lock supplies the decision
  to scope one such version to a whole cluster rather than to each member.
- **Pessimistic Offline Lock.** The other algorithm Coarse-Grained Lock can
  be layered on top of, trading detection-at-save-time for
  blocking-at-load-time, with the scoping decision identical either way.
- **Unit of Work.** The transaction-collecting mechanism that makes
  version propagation practical. A Unit of Work that tracks every object
  touched in a conversation is the natural place to implement the rule
  that any dependent write also marks the root dirty, since it already
  sees every object that changed before it commits.
- **Aggregate (Domain-Driven Design).** The domain-modelling twin of this
  pattern. An aggregate names the same cluster boundary from the
  perspective of business invariants. Coarse-Grained Lock names it from the
  perspective of the persistence and concurrency layer. In a system that
  already models aggregates, the aggregate root is almost always the
  correct object to carry the coarse-grained lock, and the two decisions
  should be made together rather than separately, per Vernon's guidance
  that the aggregate boundary is itself the transactional boundary
  ([Vernon, "Effective Aggregate Design, Part I"](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf),
  verified 2026-08-02).
- **Identity Map.** Guarantees that every code path within one conversation
  that loads a dependent object gets back the same in-memory instance,
  which is what makes it possible for a single Unit of Work to reliably
  notice that a dependent changed and route that change to the root.
- **Incompatible with treating members of the cluster as independently
  transactable resources elsewhere in the same system.** If any part of
  the application saves a dependent object outside the cluster's own save
  path, for example through a separate microservice that owns that table
  directly, the coarse-grained version check on the root cannot see that
  write, and the pattern silently stops protecting the cluster for that
  write path. This is not a conflict between two named patterns so much as
  a structural incompatibility between Coarse-Grained Lock and any
  architecture that splits ownership of a single aggregate's tables across
  more than one write path.

## 14. Refactoring path in and out

Introducing the pattern into code that currently locks, or checks versions
on, every object individually.

1. Identify the cluster and its natural root. Confirm, concretely, which
   business invariants span more than one object in the candidate cluster.
   If none do, stop, the pattern is not warranted, per dimension 4.
2. Add a single version column, or confirm the lock-table key, on the root
   only. Remove, or stop relying on, version columns on the dependents for
   this purpose. Leave them in place only if they serve an unrelated
   purpose such as row-level auditing.
3. Find every write path that creates, updates, or deletes a dependent
   member. This is the step most often under-scoped, since it is easy to
   find the paths that update existing dependents and easy to miss the
   paths that add a brand-new one or remove an existing one entirely.
4. Route every one of those write paths through a single point, ideally
   the application's Unit of Work commit step, that marks the root dirty
   whenever any dependent in its cluster changed, so the root's version
   check, or lock acquisition, fires for every one of them without each
   write path having to remember to do it individually.
5. Remove the now-redundant fine-grained checks on individual dependents,
   or, if a mixed strategy is intentional, document explicitly which
   objects are covered by the coarse-grained root check and which retain
   their own independent check, and why.
6. Add the regression coverage described in dimension 15 before removing
   the old fine-grained checks, so the transition itself does not
   introduce a window where neither mechanism is protecting the data.

Removing the pattern when the cluster boundary has grown wrong, most often
because independent-edit throughput has become the dominant cost named in
dimension 10.

1. Confirm, with real contention data rather than a guess, which pairs of
   members are actually being edited independently and colliding on the
   shared root lock without their edits genuinely conflicting.
2. Split the cluster along a real invariant boundary, not an arbitrary
   line, so that each resulting smaller cluster still has its own coherent
   root and its own coherent set of spanning invariants.
3. Give each new, smaller cluster its own version column or lock key on its
   own root, and repeat the same write-path audit from the introduction
   path above for each new cluster.
4. Migrate write paths one cluster at a time, keeping the old, wider check
   in place until every write path for a given member has been confirmed
   to route through its new, narrower root, to avoid a window where a
   dependent is covered by neither the old nor the new check.
5. Retire the old, wider version column only after every write path has
   been migrated and verified, since a single missed path here reproduces
   exactly the silent-conflict failure mode named in dimension 11.

## 15. Testing and verification

What becomes easy to test because of the pattern. A single, deterministic
scenario, load the cluster, have a second session modify any one dependent
and commit, then attempt to save the first session's change and assert a
conflict is raised, exercises the entire concurrency guarantee for the
whole cluster in one test. There is no need to write a separate version of
this test per dependent type, since correctness of the pattern means every
dependent's changes are visible through the one root check.

What becomes harder to test. Confirming completeness, that every write
path which touches a dependent actually propagates to the root, cannot be
verified by a single happy-path test. It needs an explicit inventory test.
Enumerate every code path that creates, updates, or deletes a member of the
cluster, and for each one, assert that after it runs, the root's version
has advanced, or the root's lock record has been touched. A test suite that
only exercises the update path on an existing dependent will pass green
while the create path or the delete path silently bypasses the root
entirely, which is the exact failure named as the first symptom in
dimension 11.

Recommended additions to the regression suite.

- One test per write path that reaches a dependent, asserting the root's
  version advances as a result, and not only that the write itself succeeds.
- A concurrent-conflict test using two separate in-memory representations
  of the same cluster, simulating two sessions, asserting that a
  conflicting save on the second session is rejected even when the two
  sessions touched two different dependent objects.
- A negative test confirming that a write path which is intentionally
  excluded from the pattern, if any exists, for example an operational
  script with a documented exception, is exercised and its behaviour under
  concurrent access is explicitly known rather than assumed.
- Under the pessimistic variant, a test that confirms the lock record is
  released on both commit and on rollback or exception, since a lock
  record leaked on an exception path silently blocks every future editor
  of that cluster rather than failing loudly.

Test doubles that apply. A fake or in-memory version store, keyed by root
identity to an integer, is sufficient to exercise every scenario above
without a real database, and keeping that fake simple, a single map from
root id to version integer, is itself a useful executable description of
what the pattern actually guarantees.

## 16. Observability signals

- **Version-mismatch rate on the root, per cluster type.** A count of
  rejected saves due to a stale root version, tagged by which entity type
  is acting as root. A healthy system shows this rate roughly tracking the
  rate of genuinely concurrent edits to the same cluster. A rate near zero
  across a high-traffic cluster type is worth investigating, since it can
  mean either genuinely low contention or a write path silently bypassing
  the root check, which looks identical from this metric alone and needs
  the write-path audit from dimension 15 to distinguish.
- **Root write amplification.** The ratio of writes to the root's own
  storage versus writes to the cluster overall. Under this pattern that
  ratio should approach one, since every write to any dependent also
  writes the root. A ratio well below one is a signal that some dependent
  write paths are not propagating to the root at all.
- **Lock hold duration and lock wait time, under the pessimistic variant.**
  Tracked per root identity or per root type, since the pattern
  concentrates all lock contention for a cluster onto one lock record.
  Rising wait time on a small number of hot root identities is the
  expected, visible cost named in dimension 10, and is the first place to
  look when overall save latency degrades after adopting the pattern.
- **Retry rate after a version conflict, at the caller.** How often the
  calling code reloads the root and retries the save after a rejected
  conflict, and how often that retry itself then also conflicts. A rising
  retry-of-a-retry rate signals genuine, sustained contention on that
  cluster rather than a one-off collision, and is the metric that should
  trigger reconsidering the cluster boundary per dimension 14.
- **Root row size and root row read latency, over time.** If the version
  column is co-located with frequently read root data, a hot-write root
  can start to show up as read latency too, through cache invalidation or
  lock contention with concurrent reads. Tracking this alongside the
  write-amplification metric above surfaces the sidecar-version mitigation
  named in dimension 11 before it becomes a production incident.

## 17. Security and privacy implications

The pattern itself does not open a new data-exposure surface. It operates
entirely on version numbers or lock records, not on the data content of the
locked objects. Two implications are worth naming rather than leaving
silent.

A version-conflict error message returned to a client can, if it repeats the
current stored version or a diff of what changed, leak the existence and
timing of another user's edit to a cluster the requesting user might not
otherwise be authorized to know was recently modified. Error responses
should confirm only that a conflict occurred and require the caller to
reload the current state through the normal, authorization-checked read
path, rather than embedding the conflicting version's details directly in
the error.

Under the pessimistic variant, a lock record keyed by root identity is, in
effect, a side channel that reveals which clusters are currently being
edited, by identity, to anything with visibility into the lock table.
Where the root identity itself is sensitive, for example a customer
identifier in a jurisdiction with strict data-subject protections, access
to the lock table should be restricted with the same care as access to the
underlying data, since the presence of a lock row is itself information
about who is doing what, right now.

## Code examples

Three languages where the propagation discipline is easy to see end to end.
TypeScript and Go show the same shape with static typing and explicit error
handling. Python shows the same shape with dynamic typing and exceptions. All
three share one design, a `VersionStore` that holds exactly one version per
root identity, never one per dependent, and a unit of work that routes every
change to a dependent, an addition or a removal, through the same commit path
that checks and advances the root's version. Java is omitted here because no
usable JDK was available on this machine to compile and run it, and the same
shape in Java would be a direct translation of the TypeScript class layout
with no idiom the other three languages do not already show.

### TypeScript

```typescript
class VersionConflictError extends Error {}

class Address {
  constructor(public id: string, public street: string) {}
}

class Customer {
  version: number;
  addresses: Address[] = [];
  constructor(public id: string, public name: string, version: number) {
    this.version = version;
  }
}

// One version per root identity. This map is the entire lock.
class VersionStore {
  private versions = new Map<string, number>();

  initialize(rootId: string, version: number): void {
    this.versions.set(rootId, version);
  }

  current(rootId: string): number {
    const v = this.versions.get(rootId);
    if (v === undefined) {
      throw new Error(`unknown root ${rootId}`);
    }
    return v;
  }

  commit(rootId: string, expected: number): void {
    if (this.current(rootId) !== expected) {
      throw new VersionConflictError(
        `stale version for ${rootId}, expected ${expected}`
      );
    }
    this.versions.set(rootId, expected + 1);
  }
}

// Every write to a dependent, addition or removal, flows through this one
// object, so the root's version check in save() covers the whole cluster.
class CustomerUnitOfWork {
  private loadedVersion: number;

  constructor(private store: VersionStore, private customer: Customer) {
    this.loadedVersion = customer.version;
  }

  addAddress(address: Address): void {
    this.customer.addresses.push(address);
  }

  removeAddress(addressId: string): void {
    this.customer.addresses = this.customer.addresses.filter(
      (a) => a.id !== addressId
    );
  }

  save(): void {
    this.store.commit(this.customer.id, this.loadedVersion);
  }
}

function demo(): void {
  const store = new VersionStore();
  store.initialize("cust-1", 7);

  const sessionA = new CustomerUnitOfWork(
    store,
    new Customer("cust-1", "Jane", 7)
  );
  const sessionB = new CustomerUnitOfWork(
    store,
    new Customer("cust-1", "Jane", 7)
  );

  sessionA.addAddress(new Address("addr-1", "1 Main St"));
  sessionA.save();

  try {
    sessionB.removeAddress("addr-0");
    sessionB.save();
    console.log("unexpected: no conflict detected");
  } catch (err) {
    if (err instanceof VersionConflictError) {
      console.log("conflict detected as expected:", err.message);
    } else {
      throw err;
    }
  }
}

demo();
```

Compiled clean with `tsc --noEmit --strict`, and running it prints
`conflict detected as expected, stale version for cust-1, expected 7`,
confirming that session B's edit to a different dependent, an address
removal rather than session A's address addition, is still caught by the one
shared root version.

### Python

```python
class VersionConflictError(Exception):
    pass


class Address:
    def __init__(self, address_id: str, street: str) -> None:
        self.address_id = address_id
        self.street = street


class Customer:
    def __init__(self, customer_id: str, name: str, version: int) -> None:
        self.customer_id = customer_id
        self.name = name
        self.version = version
        self.addresses: list[Address] = []


class VersionStore:
    def __init__(self) -> None:
        self._versions: dict[str, int] = {}

    def initialize(self, root_id: str, version: int) -> None:
        self._versions[root_id] = version

    def current(self, root_id: str) -> int:
        return self._versions[root_id]

    def commit(self, root_id: str, expected: int) -> None:
        if self.current(root_id) != expected:
            raise VersionConflictError(
                f"stale version for {root_id}, expected {expected}"
            )
        self._versions[root_id] = expected + 1


class CustomerUnitOfWork:
    def __init__(self, store: VersionStore, customer: Customer) -> None:
        self._store = store
        self._customer = customer
        self._loaded_version = customer.version

    def add_address(self, address: Address) -> None:
        self._customer.addresses.append(address)

    def remove_address(self, address_id: str) -> None:
        self._customer.addresses = [
            a for a in self._customer.addresses if a.address_id != address_id
        ]

    def save(self) -> None:
        self._store.commit(self._customer.customer_id, self._loaded_version)


def demo() -> None:
    store = VersionStore()
    store.initialize("cust-1", 7)

    session_a = CustomerUnitOfWork(store, Customer("cust-1", "Jane", 7))
    session_b = CustomerUnitOfWork(store, Customer("cust-1", "Jane", 7))

    session_a.add_address(Address("addr-1", "1 Main St"))
    session_a.save()

    try:
        session_b.remove_address("addr-0")
        session_b.save()
        print("unexpected: no conflict detected")
    except VersionConflictError as err:
        print("conflict detected as expected:", err)


if __name__ == "__main__":
    demo()
```

Ran directly with `python3` and printed
`conflict detected as expected, stale version for cust-1, expected 7`,
the same outcome as the TypeScript version.

### Go

```go
package main

import (
	"errors"
	"fmt"
)

var ErrVersionConflict = errors.New("stale root version")

type Address struct {
	ID     string
	Street string
}

type Customer struct {
	ID        string
	Name      string
	Version   int
	Addresses []Address
}

// One version per root identity, keyed by the customer's own id.
type VersionStore struct {
	versions map[string]int
}

func NewVersionStore() *VersionStore {
	return &VersionStore{versions: make(map[string]int)}
}

func (s *VersionStore) Initialize(rootID string, version int) {
	s.versions[rootID] = version
}

func (s *VersionStore) Commit(rootID string, expected int) error {
	current, ok := s.versions[rootID]
	if !ok {
		return fmt.Errorf("unknown root %s", rootID)
	}
	if current != expected {
		return fmt.Errorf("%w: root %s expected %d, found %d", ErrVersionConflict, rootID, expected, current)
	}
	s.versions[rootID] = expected + 1
	return nil
}

// Both AddAddress and RemoveAddress leave the actual version check to Save,
// so neither write path can forget to touch the root.
type CustomerUnitOfWork struct {
	store         *VersionStore
	customer      *Customer
	loadedVersion int
}

func NewCustomerUnitOfWork(store *VersionStore, customer *Customer) *CustomerUnitOfWork {
	return &CustomerUnitOfWork{store: store, customer: customer, loadedVersion: customer.Version}
}

func (u *CustomerUnitOfWork) AddAddress(a Address) {
	u.customer.Addresses = append(u.customer.Addresses, a)
}

func (u *CustomerUnitOfWork) RemoveAddress(id string) {
	kept := u.customer.Addresses[:0]
	for _, a := range u.customer.Addresses {
		if a.ID != id {
			kept = append(kept, a)
		}
	}
	u.customer.Addresses = kept
}

func (u *CustomerUnitOfWork) Save() error {
	return u.store.Commit(u.customer.ID, u.loadedVersion)
}

func main() {
	store := NewVersionStore()
	store.Initialize("cust-1", 7)

	sessionA := NewCustomerUnitOfWork(store, &Customer{ID: "cust-1", Name: "Jane", Version: 7})
	sessionB := NewCustomerUnitOfWork(store, &Customer{ID: "cust-1", Name: "Jane", Version: 7})

	sessionA.AddAddress(Address{ID: "addr-1", Street: "1 Main St"})
	if err := sessionA.Save(); err != nil {
		panic(err)
	}

	sessionB.RemoveAddress("addr-0")
	if err := sessionB.Save(); err != nil {
		fmt.Println("conflict detected as expected:", err)
	} else {
		fmt.Println("unexpected: no conflict detected")
	}
}
```

Passed `go vet` clean and, run with `go run`, printed
`conflict detected as expected, stale root version, root cust-1 expected 7, found 8`,
matching the same scenario in the other two languages.

## 18. References

- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 16, "Coarse-Grained Lock", entry credited to
  David Rice and Matt Foemmel. Catalog summary confirmed at
  [martinfowler.com/eaaCatalog/coarseGrainedLock.html](https://martinfowler.com/eaaCatalog/coarseGrainedLock.html),
  verified 2026-08-02.
- Vaughn Vernon, "Effective Aggregate Design, Part I. Modeling a Single
  Aggregate", dddcommunity.org, 2011,
  [dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf),
  verified 2026-08-02.
- Rails API documentation, `ActiveRecord::Associations::ClassMethods`,
  `belongs_to`, the `touch` option,
  [api.rubyonrails.org/classes/ActiveRecord/Associations/ClassMethods.html](https://api.rubyonrails.org/classes/ActiveRecord/Associations/ClassMethods.html),
  verified 2026-08-02.
- Hibernate ORM Javadoc, `org.hibernate.annotations.OptimisticLockType`,
  [docs.hibernate.org/orm/current/javadocs/org/hibernate/annotations/OptimisticLockType.html](https://docs.hibernate.org/orm/current/javadocs/org/hibernate/annotations/OptimisticLockType.html),
  verified 2026-08-02.
- Doctrine ORM documentation, "Transactions and Concurrency",
  [doctrine-project.org/projects/doctrine-orm/en/current/reference/transactions-and-concurrency.html](https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/transactions-and-concurrency.html),
  verified 2026-08-02.
