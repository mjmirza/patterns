---
name: Single Source of Truth
slug: single-source-of-truth
family: 04-principles-and-laws
category: Principle
aliases: [SSOT, Single Point of Truth, SPOT]
first_described: "Practitioner term, data management and normalization tradition, no single named originator"
maturity: canonical
related: [dont-repeat-yourself, information-expert, low-coupling, high-cohesion, pure-fabrication]
incompatible_with: []
verified: 2026-08-02
---

# Single Source of Truth

## 1. Name, aliases, and lineage

The canonical name is Single Source of Truth, almost always abbreviated SSOT.
The equivalent abbreviation Single Point of Truth, SPOT, appears in older data
architecture writing and means the same thing. This entry treats SSOT and SPOT
as one principle under one name, since no source found during verification
draws a meaningful distinction between them.

Unlike a Gang of Four pattern or a named law such as Conway's Law, SSOT has no
single paper, book, or person credited with coining it. Wikipedia's own entry,
verified 2026-08-02, defines the practice but states no origin, and the
article's own history section, not quoted here since it is not a durable
citation, shows the concept accreting from database normalization writing
during the following decades, from enterprise data warehousing discourse in
the 1990s, and later from frontend state management writing in the 2010s.
Because of that lineage this entry treats the term as a practitioner
convention, not a scholarly citation, and marks the historical claim as
judgement rather than a sourced fact.

The formal root the term draws its authority from is older and better
documented. Edgar F. Codd's 1970 paper "A Relational Model of Data for Large
Shared Data Banks," Communications of the ACM, volume 13, issue 6, introduced
normalization for relational databases, the technique of decomposing data so
that each fact is stored in exactly one place and derived facts are computed
rather than duplicated. SSOT as applied to a database schema is normalization
stated as an architectural goal rather than as a schema design technique.
When the principle moved outside the database, into configuration management,
infrastructure state, and later into UI state management, the underlying idea
did not change. one authoritative record per fact, and every other view of
that fact is a read, a copy, or a derivation, never a second place to write.

The English-language Wikipedia entry, "Single source of truth," verified
2026-08-02, states the definition as "the practice of structuring information
models and associated data schemas such that every data element is mastered
(or edited) in only one place," and separately observes that "an ideal
implementation of SSOT is rarely possible in most enterprises," a caveat this
entry treats as an honest admission that the principle is aspirational at
scale, addressed directly in dimension 4 and dimension 10.

## 2. Problem and context

A fact about the world gets written down more than once, in more than one
system, in more than one file, or in more than one variable, because writing
it again was faster than routing back to where it already lives. Each copy
then drifts from the others as time passes and only one copy gets updated on
any given change. Nobody notices the drift until two views of the same fact
disagree in front of a customer, an auditor, or a teammate, and at that point
nobody can say which copy is correct without manual reconciliation.

The situation shows up at every scale a system can have. In a database schema,
a customer's shipping address is stored once on the customer record and a
second time, denormalized, on every order row, because a report needed it
without a join. In a frontend application, a form's validity is tracked in
one boolean on the parent component and duplicated into a second boolean
inside a child component, because the child needed to render a warning
without waiting for a prop update. In infrastructure, a server's configuration
lives in a runbook a human edited by hand and also in a Terraform file nobody
remembered to run, so the two describe two different machines. In a
microservice architecture, a currency exchange rate is fetched once and cached
independently inside three services, so a rate change propagates to each
service on its own schedule and a single transaction can be priced three
different ways depending on which service happened to serve it. In
documentation, an API's request shape is described in a hand-written markdown
file and separately in the code that validates the request, and the two
diverge the first time either one is edited without the other.

The common shape underneath every one of these examples is the same. A fact
exists. It has more than one place where it can be read. It has more than one
place where it can be written. The principle names the fix for the second
half of that sentence, not the first. Read access can and should be plural,
because that is what a fact being useful means. Write access must not be
plural, because that is what causes the fact to fork into two facts that were
once the same fact and are no longer guaranteed to agree.

## 3. Forces

- **Consistency.** Favoured, and this is the entire point of the principle. A
  fact mastered in one place cannot disagree with itself, because there is
  only one place a disagreement could originate.
- **Latency and read performance.** Sacrificed by default. A single authority
  usually means every reader either goes to that authority directly or reads
  a cache of it, and a cache reintroduces exactly the two-copy problem the
  principle exists to prevent, only now on purpose and with an explicit
  invalidation contract, discussed in dimension 8.
- **Availability.** Sacrificed when taken literally. If the one authoritative
  system is down, every downstream system that depends on it for the current
  value of the fact either serves stale data or serves nothing, because there
  is no second authority to fail over to.
- **Coupling.** A double-edged force. Downstream consumers become coupled to
  the shape and the availability of the one authority, which is a real cost,
  but every consumer also stops being coupled to each other's private copies
  of the fact, which is a real gain. The net effect depends on how stable the
  authority's interface is.
- **Cognitive load for the reader of a fact.** Favoured. A developer or an
  operator asking "what is the actual current value" has exactly one place to
  look, rather than a set of candidate places that must first be reconciled
  by hand or by convention.
- **Cognitive load for the writer of a fact.** Also favoured, for a different
  reason. A writer does not need to remember every place a fact is duplicated
  in order to keep them all correct, because there is only one place to write.
- **Team topology and ownership.** Favoured when the authority maps cleanly
  onto a single owning team, and a source of real conflict when it does not.
  A fact that several teams each feel they own, a customer record touched by
  sales, support, and billing being the classic case, forces an ownership
  decision the principle itself has no opinion about.
- **Auditability.** Favoured. A single point of write is a single point where
  a change history, an audit log, or a permission check can be attached with
  certainty that nothing bypassed it.

The principle is not free. Its cost is paid in availability, in read latency
absent a caching layer, and in the coupling every downstream system takes on
to the one authority. The gain is paid in consistency, in a bounded surface
for correctness bugs, and in a place to put access control and history that
actually covers every write.

## 4. Applicability and non-applicability

Reach for a single source of truth when the following hold.

- A fact has business, legal, financial, or safety consequences if two views
  of it disagree, such as a price, an account balance, a permission, an
  inventory count, or a patient's medication list.
- The fact changes over its lifetime, so a duplicate risks becoming stale in a
  way a truly constant value cannot.
- More than one part of the system currently reads the fact, or plausibly will,
  which is what makes the duplication temptation arise in the first place.
- The system already has, or can reasonably be given, one place that is
  naturally positioned to own the fact, whether that is a database table, a
  configuration service, a piece of application state, or an external system
  of record such as an ERP or a payroll system.
- A dispute about "which value is correct" has already happened once, which is
  usually the loudest possible signal that the fact needs an owner.

Do NOT reach for a single source of truth, or apply it more strictly than the
situation calls for, in these cases.

- **The value is a derived or computed fact, not a stored one.** A person's
  age computed from a stored birth date is not a second source of truth for
  age, it is a projection of the one source, the birth date. Caching the
  computed age and forgetting it is derived is the actual mistake, not the
  existence of the cached value. Do not build machinery to enforce single
  ownership of something that was never independently writable.
- **The system is offline-first or must tolerate network partition, and an
  eventually-consistent model is the honest answer.** A note-taking app that
  must work on an airplane cannot have one live authority the device
  round-trips to on every keystroke. The correct model there is Conflict-free
  Replicated Data Types or a similar merge strategy, which explicitly accepts
  concurrent writes to what are, briefly, multiple sources, and resolves them
  after the fact. Forcing a single point of write onto that architecture
  either breaks offline support or produces a lock users will experience as
  the app freezing.
- **The cost of centralizing outweighs the cost of the drift it prevents.** A
  cached exchange rate that is thirty seconds stale in a low-stakes internal
  dashboard is not worth building a synchronous call chain to eliminate. Match
  the rigor of the enforcement to the actual cost of the fact being wrong, per
  dimension 10.
- **Two systems each need their own authoritative copy for genuinely different
  purposes, and treating one as a copy of the other is a category error.** A
  product's marketing description in a CMS and its technical specification in
  a PLM system are not two copies of one fact, they are two different facts
  that happen to describe the same product. Merging them into one authority
  produces a document nobody can write cleanly, because the two audiences
  want different things from it.
- **The team lacks the operational maturity to run the centralizing system
  reliably.** A single source of truth that goes down and takes every
  dependent system down with it is worse for the business than the
  inconsistency it was meant to prevent, if the inconsistency was rare and
  low-stakes and the outage is frequent and high-stakes. Wikipedia's own entry,
  verified 2026-08-02, states plainly that "an ideal implementation of SSOT is
  rarely possible in most enterprises," which this entry reads as a caution
  against chasing a theoretically perfect single authority past the point
  where doing so serves the business.
- **The fact is a snapshot that must be preserved even after the source
  changes.** An invoice must record the price and tax rate that applied at
  the moment it was issued, not a live pointer back to the current price,
  because the current price will change and the invoice must not. This is
  intentional, sanctioned duplication, a snapshot, not a violation of the
  principle, and conflating the two is a common and costly mistake, covered
  further in dimension 11.

## 5. Structure

Single Source of Truth is a principle, not a design pattern with named
classes, so its structure is described in terms of roles a system's
components play rather than in terms of participants with method signatures.

- **The Authority.** The one component, service, table, or piece of state
  designated to hold the current, correct value of a given fact. The authority
  is where a write to that fact must land, and it is the only place a write
  to that fact is allowed to land.
- **Consumers.** Any component that reads the fact. There can be, and usually
  should be, many consumers. Read fan-out is not a violation of the
  principle, only write fan-out is.
- **Derivations.** A value computed from the authority's data, potentially
  cached for performance, but never independently writable. A derivation
  that becomes independently writable, even by accident, silently turns into
  a second authority, which is the most common way the principle is violated
  in practice.
- **The Propagation Path.** The mechanism by which a change at the authority
  reaches its consumers and derivations. This can be synchronous, a direct
  read on every access, or asynchronous, an event, a webhook, a cache
  invalidation, or a periodic sync. The propagation path is where staleness
  enters the system, and it is the piece most catalogs of the principle
  underspecify, addressed at length in dimension 8.
- **The Boundary.** The scope within which single authority is enforced. A
  boundary can be a single process, a single database, a bounded context in
  the domain-driven design sense, or an entire organization. The principle
  says nothing about how wide the boundary should be, only that within
  whatever boundary is chosen, one fact has one write path.

## 6. ASCII structure diagram

```
                         +---------------------+
                         |      Authority       |
                         |  (owns the write)     |
                         |  e.g. Orders table,    |
                         |  config service, or    |
                         |  a single React state  |
                         +----------+------------+
                                    |
                     writes land   | propagation path
                     only here     | (sync read, event,
                                    | cache invalidation,
                                    | webhook, poll)
                    +---------------+---------------+
                    |               |                |
                    v               v                v
           +----------------+ +----------------+ +----------------+
           |   Consumer A    | |   Consumer B    | |  Derivation D  |
           | (read only)     | | (read only)     | | (computed,     |
           |                 | |                 | |  never written |
           +----------------+ +----------------+ | to directly)   |
                                                    +----------------+

   Write arrows point only into Authority.
   Read arrows fan out freely from Authority to every consumer.
   A Derivation may cache, but a cache is a copy of a read, never
   a second place a client is permitted to write the fact.
```

## 7. Dynamics

The two flows worth tracing separately are a write and a stale-read recovery,
because most SSOT bugs live in the second one, not the first.

```
Writer               Authority              Cache/Derivation      Consumer
  |                      |                         |                  |
  |-- write(fact) ------>|                         |                  |
  |                      |-- persist -------------->|                  |
  |                      |                          |                  |
  |<-- ack --------------|                          |                  |
  |                      |                          |                  |
  |                      |-- invalidate/publish --->|                  |
  |                      |   (event, webhook,       |                  |
  |                      |    cache-bust, poll)     |                  |
  |                      |                          |-- refresh ------>|
  |                      |                          |   (re-read from  |
  |                      |                          |    Authority)    |
  |                      |                          |                  |
  |                      |<-------- read (cache miss, or TTL expired) -|
  |                      |-- current value --------->|                  |
  |                      |                          |-- serves fresh -->|
```

The dangerous window is the gap between the top ack and the bottom refresh.
During that window a consumer reading from a derivation or a cache sees a
value that is technically stale relative to the authority, and the system
design has to decide, explicitly, whether that staleness is acceptable for
this fact. A bank balance display that is five seconds stale during a
transfer is usually fine. A bank balance used to authorize a second
concurrent withdrawal is not, and that difference is exactly why the same
principle produces both eventually-consistent read replicas, which accept the
staleness window, and strict single-writer locks with synchronous reads,
which refuse to.

## 8. Implementation variants

**Direct read on every access.** The simplest and strictest form. Every
consumer queries the authority for the current value on every use, with no
intermediate cache. This eliminates the staleness window entirely at the cost
of load on the authority and latency for every consumer. Appropriate for
low-traffic facts with high correctness cost, such as an account's current
permission set checked on every request.

**Cache with explicit invalidation.** The authority remains the only writable
copy, but consumers or an intermediate layer hold a time-bounded or
event-invalidated copy for performance. The propagation path from dimension 7
becomes the load-bearing part of the design. A cache with no invalidation
path, only a time-to-live, silently reintroduces a staleness window bounded
by the TTL, which is a deliberate trade of consistency for load, not a bug,
provided the TTL is chosen with that trade in mind rather than left at a
framework default.

**Event-driven propagation, sometimes called Change Data Capture.** The
authority publishes an event on every write, and every consumer maintains its
own materialized, read-optimized copy that it updates by consuming the event
stream. This is the shape behind most modern data warehousing and behind
patterns such as event sourcing, where the event log itself becomes the
single source of truth and every read model, including the current-state
table, is a derivation rebuilt from the log. The cost moves from query-time
load to eventual-consistency risk, since a consumer that has not yet
processed the latest event serves a stale materialized view.

**Single owning service in a microservice architecture.** One service owns a
bounded context's data outright, and no other service is permitted a direct
write to that service's database, only calls through its published API. Other
services either call the owning service synchronously for the current value
or subscribe to its events and keep a local read model. This is the
distributed-systems restatement of the database-normalization form of the
principle, and it is the shape referenced by the domain-driven design idea of
a bounded context owning its own aggregate.

**Lifted state in a UI framework.** In component-based UI frameworks, state
that more than one component needs is moved, "lifted," to the nearest common
ancestor and passed down as a read-only value, with a callback passed down
for the child to request a change rather than mutate its own copy. React's own
documentation, verified 2026-08-02, states this explicitly. "For each unique
piece of state, you will choose the component that 'owns' it. This principle
is also known as having a 'single source of truth'." The Redux state
management library takes the same idea to the level of an entire application,
stating as its first of three principles, verified 2026-08-02, "The global
state of your application is stored in an object tree within a single store."

**Infrastructure as code.** A declarative configuration file, rather than the
running infrastructure itself, is treated as the authority, and a tool
reconciles the actual infrastructure to match the file. HashiCorp's Terraform
documentation, verified 2026-08-02, describes the purpose of its state
mechanism as follows. "Terraform uses your workspace's state to map real
world resources to your configuration, keep track of metadata, and to improve
performance for large infrastructures." The practical consequence teams
adopt as policy is that manual, out-of-band changes to the running
infrastructure, so-called configuration drift, are treated as bugs to be
reconciled back toward the file, not as a legitimate second way to change the
system. This is a judgement about how the tool is typically operated in
practice, not a claim the documentation itself makes in those words.

**Consensus-backed key-value store as the cluster authority.** Distributed
systems that must agree on a single current state across many nodes often
delegate that state to a consensus-based store rather than trying to keep
every node's local copy consistent by convention. Kubernetes uses etcd this
way. The Kubernetes documentation on control plane components, verified
2026-08-02, describes etcd as a "Consistent and highly-available key value
store for all API server data," and every other Kubernetes control plane
component treats etcd, not its own in-memory view, as the authority for
cluster state.

## 9. Known production uses

**PostgreSQL foreign key constraints as an enforcement mechanism.** A foreign
key constraint mechanically prevents a dependent table from referencing a row
that does not exist in its parent table, which is the database engine
enforcing that the parent table remains the single authority for which rows
of the referenced kind actually exist. The PostgreSQL documentation, verified
2026-08-02, states, "A foreign key constraint specifies that the values in a
column (or a group of columns) must match the values appearing in some row of
another table," and gives the concrete effect. "Now it is impossible to
create orders with non-NULL product_no entries that do not appear in the
products table." PostgreSQL documentation, "Constraints," section 5.4.5,
Foreign Keys, https://www.postgresql.org/docs/current/ddl-constraints.html
verified 2026-08-02.

**Redux, single store for application state.** Redux's own documentation
names single-store state as the first of its three founding principles, using
the exact language of "a single store" for "the global state of your
application." Redux documentation, "Three Principles,"
https://redux.js.org/understanding/thinking-in-redux/three-principles
verified 2026-08-02.

**React, lifting state up.** React's official documentation dedicates a page
to the pattern and explicitly names it as an instance of single source of
truth. React documentation, "Sharing State Between Components,"
https://react.dev/learn/sharing-state-between-components verified 2026-08-02.

**HashiCorp Terraform, state as the mapping authority between configuration
and real infrastructure.** Terraform's state file is the mechanism the tool
uses to know which real-world resources correspond to which declared
resources, and the tool's reconciliation model depends on that state being
trustworthy and singular per workspace. HashiCorp Terraform documentation,
"State," https://developer.hashicorp.com/terraform/language/state verified
2026-08-02.

**Kubernetes, etcd as the cluster's backing store.** Every Kubernetes control
plane component, the API server, the scheduler, and the controller manager,
reads and writes cluster state through etcd rather than maintaining an
independently authoritative copy of cluster state in its own process.
Kubernetes documentation, "Kubernetes Components,"
https://kubernetes.io/docs/concepts/overview/components/ verified 2026-08-02.

## 10. Consequences

Positive.

- Consistency bugs caused by two copies of a fact disagreeing become
  structurally impossible within the boundary the authority governs, rather
  than merely unlikely.
- A single place exists to attach validation, an audit trail, and access
  control, so those concerns cover every write instead of needing to be
  reimplemented at every duplication site.
- Debugging a wrong value becomes a search for one authority rather than a
  search across every place the fact might have been copied to.
- New consumers can be added cheaply, because they read from an existing
  authority rather than needing their own synchronization logic with every
  other consumer.
- The system gains a natural place to reason about the fact's lifecycle,
  creation, update, and deletion, since all three happen in one place.

Negative.

- The authority becomes a single point of failure for the fact it owns. Its
  outage degrades or blocks every dependent system, a cost that must be
  weighed against the inconsistency cost the principle is preventing.
- Read performance for consumers far from the authority, geographically or
  organizationally, often requires a cache, and every cache reopens a
  staleness window that must be reasoned about explicitly.
- Centralizing a fact can create an organizational bottleneck if the
  authority is owned by a team that becomes a required approver or a shared
  dependency for every other team's work.
- Migrating an existing system toward a single authority, where duplication
  has accumulated for years, is expensive and risky, because the migration
  itself must reconcile disagreeing copies without knowing in advance which
  one, if either, was correct.
- Over-application produces synchronous coupling where an asynchronous,
  eventually-consistent design would have served the business better, which
  is the failure mode covered in dimension 4's non-applicability list.

## 11. Failure modes and misuse

**The shadow copy.** Symptom. A value that was supposed to be read-only,
cached, or derived quietly grows its own edit path, often through a "quick
fix" that lets an operator edit the cached value directly to correct a
production incident. Cause. Someone needed the fact fixed faster than the
authority's normal update path allowed, and the shortcut was never removed.
Fix. Remove the edit path, and if operators genuinely need faster correction,
build that as an explicit, audited fast path into the authority, not around
it.

**Denormalization mistaken for a second authority.** Symptom. A duplicated
column in a database, added deliberately for query performance, drifts from
the authoritative column because an application code path updates one and
forgets the other. Cause. The team denormalized for a real performance reason
but did not build the synchronization the denormalization implicitly promised,
often a database trigger or an application-level write-through. Fix. Either
add the missing synchronization mechanically, so the denormalized column
cannot drift, or remove the denormalization and solve the performance problem
with an index or a materialized view instead.

**Confusing a snapshot with a stale duplicate.** Symptom. A team "fixes"
historical invoices to reflect the current price after a price change, then
discovers this violates accounting requirements and breaks reconciliation with
a payment processor. Cause. Treating an intentionally frozen record, the
invoice, as if it were a cache of the authority that should always reflect
the latest value. Fix. Recognize that a point-in-time record is not a
violation of single source of truth for the current price, it is a separate
fact, the price that was charged, and it has its own, different authority,
which is the transaction itself, not the live price list.

**The authority nobody agreed on.** Symptom. Two teams both believe their own
system is the authority for the same fact, most often a customer or a product
record shared between a CRM and an ERP, and both systems allow writes,
producing conflicting values with no mechanical way to say which is correct.
Cause. Single source of truth was never explicitly assigned as an
organizational decision, only implicitly assumed by each team from its own
side. Fix. This is not a code fix. It requires an explicit decision, usually
made above the engineering team, about which system is authoritative for the
fact, with the other system's copy of that field made strictly read-only or
removed.

**Chatty synchronous calls masquerading as SSOT.** Symptom. A service makes a
network call to the authority on every single request, including requests
where the fact rarely changes, producing latency and cascading failure risk
that traces back entirely to strict adherence to "always read from the
authority." Cause. Direct-read-on-every-access, the strictest implementation
variant from dimension 8, was applied to a fact whose actual correctness
requirement did not need that strictness. Fix. Introduce a cache with an
invalidation or short TTL appropriate to the fact's actual volatility and
correctness requirement, rather than defaulting to zero staleness tolerance
for every fact regardless of its cost of being briefly stale.

**Eventual consistency treated as a bug.** Symptom. A support ticket reports
that a change "did not take effect," when in fact it did take effect at the
authority and simply had not yet propagated to a cached read model, and an
engineer spends hours looking for a data-loss bug that does not exist. Cause.
The propagation path's staleness window, an accepted and designed-for part of
the system in dimension 7, was never documented or communicated to support
staff or to users. Fix. Make the staleness window visible, a "last updated"
timestamp on the derived view, and document the expected propagation delay so
it is recognized as expected behavior rather than investigated as a defect
every time it is observed.

## 12. Trade-off matrix

Compared against named alternatives that address the same underlying
"multiple copies of a fact" problem, across the forces from dimension 3.

| Force | Single Source of Truth | Multi-master replication | Eventual consistency / CRDTs | Denormalization with sync trigger | No coordination, independent copies |
|---|---|---|---|---|---|
| Consistency guarantee | Strong, structural | Weak to strong, depends on conflict resolution | Eventually consistent, converges after propagation | Strong if the trigger is correct, silent drift if not | None, drift is the default outcome |
| Availability under partition | Poor at the authority, good for cached reads | Good, every node can accept writes | Good, every replica can accept writes | Good, both copies are locally writable | Good, but for the wrong reason |
| Read latency far from authority | Poor without caching | Good, read the nearest replica | Good, read the nearest replica | Good, denormalized copy is local | Good, but value may be wrong |
| Write conflict handling | Not applicable, only one writer | Requires an explicit resolution strategy | Requires a merge function (CRDT) or last-writer-wins | Not applicable if only the authority writes | Undefined, conflicts are silent |
| Operational complexity | Low to moderate | High, conflict resolution and replication topology | High, merge semantics must be designed per data type | Moderate, one trigger or write-through path per copy | Low to build, high to debug later |
| Auditability | Strong, one write path to log | Moderate, must merge logs from every writer | Moderate to strong depending on CRDT design | Weak, two write paths to audit | Very weak |
| Appropriate for | Facts with real consistency cost | Multi-region systems needing local write availability | Offline-first apps, collaborative editing | Read-heavy queries where sync can be guaranteed mechanically | Nothing, this is the anti-pattern the principle names |

Reading of the table. Single Source of Truth wins decisively where a fact's
correctness genuinely matters and the authority's availability can be
engineered to an acceptable level. Multi-master replication and
CRDT-based eventual consistency are not violations of the principle so much
as more sophisticated answers to the same underlying question, who is
allowed to say what the current value is, for situations where the SSOT
non-applicability conditions in dimension 4 hold, most often partition
tolerance. Denormalization with a synchronization trigger is single source
of truth in disguise, the trigger exists specifically to prevent the second
copy from ever becoming a second authority. The last column, uncoordinated
independent copies, is not a real alternative design, it is the failure mode
the whole principle exists to prevent, included here to make the contrast
explicit.

## 13. Related and incompatible patterns

- **Don't Repeat Yourself.** The nearest sibling principle, and frequently
  conflated with it. DRY is about not duplicating logic or knowledge in code.
  SSOT is about not duplicating a fact's authoritative storage. A codebase can
  violate DRY, duplicated validation logic in two files, without violating
  SSOT, since the underlying data might still have exactly one authoritative
  home. A system can violate SSOT, a customer's address stored in two tables,
  while the code that reads each table is not itself duplicated. The two
  principles compose well and are often pursued together, but they are not
  the same principle and a fix for one does not automatically fix the other.
- **Information Expert.** Compatible and complementary. Information Expert
  says to assign a responsibility to the class that has the information
  needed to fulfil it. Applied to data ownership, the class or service that is
  the information expert for a fact is a natural candidate to also be its
  single source of truth, since it already holds the data the fact depends
  on.
- **Pure Fabrication.** Compatible. A pure fabrication, a class invented
  purely for a design reason with no direct analogue in the problem domain,
  is a common shape for the authority itself, when no existing domain object
  naturally owns the fact. A dedicated "PricingService" that owns the single
  authoritative price for a product, rather than the price living
  inconsistently on either the product record or the order record, is a pure
  fabrication introduced specifically to establish a single source of truth.
- **Low Coupling and High Cohesion.** In tension, honestly. Establishing one
  authority for a fact necessarily couples every consumer of that fact to the
  authority, which is a real increase in coupling compared to each consumer
  holding its own copy. The trade is accepted because the coupling that
  results is explicit and centralized, while the coupling avoided is implicit
  and scattered, a form of coupling that is harder to see and therefore
  harder to manage.
- **CQRS, Command Query Responsibility Segregation.** A refinement rather than
  a conflict. CQRS explicitly splits the write model, which remains the
  single source of truth, from one or more read models, which are
  derivations optimized for query performance and are never independently
  writable. CQRS is, in the terms of dimension 5, an architecture that makes
  the Authority and Derivation roles into separate, explicitly named
  components rather than leaving the distinction implicit.
- **Event Sourcing.** A specific and strict implementation of single source
  of truth, where the append-only event log is the one true authority for
  everything that has ever happened, and every other view, including the
  current-state table most of the application actually queries, is a
  derivation rebuilt by replaying the log. Event Sourcing is compatible with
  SSOT to an unusually literal degree, since it makes the authority
  immutable and every read model provably reconstructible.
- **Cache-Aside and Read-Through Caching.** Compatible when done correctly,
  the leading cause of SSOT violation when done carelessly. A cache is
  supposed to be a disposable, rebuildable copy of a read from the authority.
  The moment application code writes to the cache directly, bypassing the
  authority, in order to "keep it in sync" faster than invalidation allows,
  the cache has silently become a second, un-audited authority, which is the
  shadow-copy failure mode from dimension 11.
- **Service Locator and Global Mutable State (anti-patterns).** Superficially
  similar, actually opposed. Global mutable state that any code anywhere can
  write is the opposite of single source of truth in spirit, even though both
  involve a single shared location, because SSOT is defined by controlled,
  bounded write access through a known path, while unconstrained global state
  is defined by the absence of any such control. A single global variable
  that fifty unrelated functions all write to is not an authority, it is an
  uncoordinated free-for-all that happens to share an address.

## 14. Refactoring path in and out

Introducing single authority into a codebase where a fact has silently
duplicated. Ordered steps.

1. Identify every place in the system that currently stores a writable copy
   of the fact. This step alone often surprises a team, since duplicate
   copies accrete gradually and nobody has an inventory of them until they
   grep for the field name across the whole codebase and every database.
2. Pick the authority. Prefer the copy that is updated most reliably today,
   or the system with the strongest natural claim to own the underlying
   domain concept, over the copy that happens to be easiest to change first.
3. Add a read path from every other consumer to the chosen authority, running
   it in parallel with the existing duplicated read, and log or assert when
   the two disagree. This surfaces the actual scope of existing drift before
   any writes are touched, which is essential, since the migration cannot
   assume the duplicate copies currently agree.
4. Reconcile the disagreements found in step 3. This is a data-quality task,
   not a code task, and it is usually the most time-consuming part of the
   migration.
5. Convert every non-authoritative write path into either a call to the
   authority's write path, or a read-only derivation with no write path at
   all. Do this one consumer at a time, verifying after each conversion that
   the disagreement logging from step 3 goes silent for that consumer.
6. Once every write path routes through the authority, remove the
   now-redundant storage for the duplicate copies, or convert it into an
   explicitly cached, invalidated derivation per the variants in dimension 8
   if the read performance actually requires a local copy.
7. Add the consistency checks from dimension 15 as a permanent regression
   guard, so a future accidental reintroduction of a write path to a
   supposed derivation is caught automatically rather than rediscovered the
   same way this migration started.

Loosening strict single authority when it has become the wrong shape for the
system, most commonly discovered when the authority's availability
requirement has outgrown what a single point of write can sustain.

1. Confirm the actual requirement has changed, typically to partition
   tolerance across regions or to offline support, rather than assuming a
   performance complaint alone justifies loosening a correctness guarantee.
2. Choose an explicit conflict resolution strategy before allowing a second
   write path to exist, whether that is last-writer-wins with a vector clock,
   an operational-transform or CRDT merge function, or a manual reconciliation
   queue for genuine conflicts. Never allow multiple writers to exist with no
   stated resolution strategy, that state is the uncoordinated-copies failure
   mode from the trade-off table in dimension 12, not a real design.
3. Instrument the new multi-writer path from day one with conflict-rate
   metrics, per dimension 16, since the whole justification for accepting the
   loosened guarantee depends on conflicts actually being rare enough to
   tolerate.
4. Keep the ability to fall back to a single authority for the subset of
   facts, if any, that turn out to need the stronger guarantee after all, an
   account balance inside a system that is otherwise fine with eventual
   consistency for, say, display preferences, being the common split.

## 15. Testing and verification

Easier because of the principle.

- A test that exercises the authority's write path exercises the entire
  system's truth for that fact, so one well-written test suite at the
  authority substitutes for what would otherwise be a combinatorial set of
  tests checking every duplicated copy stayed in sync.
- Fixtures and test data need to be seeded in exactly one place, since there
  is exactly one authoritative store to seed, rather than needing the test
  setup to keep several duplicated stores consistent with each other before
  the test under scrutiny even runs.
- A consumer or a derivation can be tested against a fake or stub authority
  with a controlled, deterministic value, since the consumer's only
  dependency on the fact is a read from one known interface.

Harder because of the principle.

- Testing the propagation path from dimension 7, the gap between a write at
  the authority and a consumer observing the new value, requires either
  asynchronous test infrastructure or an explicit synchronous flush hook,
  since a naive test that reads immediately after writing may observe stale
  data and either pass or fail nondeterministically depending on timing.
- Testing failure modes of the authority itself, what every consumer does
  when the one authority is unreachable, requires deliberately simulating
  that unavailability, which most test suites for the individual consumers
  do not naturally exercise unless someone adds it.

Techniques that apply.

- **Consistency assertion tests, run continuously in production, not only at
  build time.** A background job that periodically compares a sampled set of
  values between the authority and any remaining cached or denormalized
  copies, alerting on disagreement, is the direct testing analogue of the
  shadow-copy failure mode from dimension 11, and is the single most useful
  verification technique for large existing systems where a full migration
  to strict single authority is not yet complete.
- **Contract tests on the authority's public interface**, so that a consumer
  written against the authority today keeps working if the authority's
  internal storage changes, provided the published contract does not change.
  This is a standard contract-testing technique applied specifically to the
  authority's role as the one legitimate write path.
- **Write-path coverage audits.** A static or dynamic check that enumerates
  every code path that can mutate the fact's storage, and fails the build if
  a new mutation site appears outside the designated authority's module or
  service boundary. This turns the shadow-copy failure mode into a build-time
  or CI-time failure rather than a production incident discovered weeks
  later.
- **Chaos testing the authority's unavailability**, deliberately taking the
  authority offline in a staging environment and observing whether every
  consumer degrades the way its design intends, rather than crashing or
  silently serving incorrect data.

## 16. Observability signals

Because the whole value of the principle is a promise about correctness, the
signals that matter are the ones that would reveal the promise being broken.

What to record.

- A write-path counter at the authority, labelled by which consumer or
  service issued the write, if the authority is shared, so an unexpected
  writer showing up is visible immediately rather than discovered by
  accident.
- A staleness gauge on every cache or derivation, recording the age of the
  data relative to the authority's last write, so the propagation window
  from dimension 7 is a number on a dashboard rather than an assumption.
- A consistency-check metric, the count and rate of disagreements found by
  the background consistency assertion job from dimension 15, which should
  sit at or near zero for a system where the migration to single authority
  is genuinely complete.
- An authority-availability metric, since every downstream system's
  behavior during an authority outage depends on this being visible in real
  time, not reconstructed after the fact from logs.
- A cache hit and miss ratio for any read-through or cache-aside layer sitting
  in front of the authority, since a collapsing hit ratio is often the first
  sign that load on the authority is about to spike.

A healthy instance on a dashboard. The write-path counter shows writes coming
from exactly the expected set of callers, matching the system's documented
ownership. The staleness gauge stays under the value the business has
explicitly agreed is acceptable for that fact, and does not creep upward over
time. The consistency-check metric sits at zero or at a rate low enough to be
explainable by the propagation window alone, never by an unexplained,
persistent drift. The authority's availability tracks its service level
objective.

A failing instance. The write-path counter shows a caller that should not
exist, which is the shadow-copy failure mode surfacing in telemetry before a
human notices the data itself disagreeing. The staleness gauge trends upward
without bound, which usually means the propagation mechanism, an event
consumer or a cache-invalidation webhook, has silently stopped running. The
consistency-check metric spikes after a deployment, which usually pinpoints
the exact release that introduced a new, unintended write path. The
authority's own error rate climbs while every downstream consumer's error
rate climbs in lockstep shortly after, which is the single-point-of-failure
cost from dimension 10 showing up as an incident rather than as an abstract
risk on a whiteboard.

## 17. Security and privacy implications

Single source of truth changes both the attack surface and the compliance
posture of a system, in ways that cut in both directions.

**Access control concentrates, for better and for worse.** Because there is
exactly one write path to a fact, a permission check placed at the authority
covers every write to that fact, with no way for a bypassing write to skip
it, which is a genuine security improvement over a system where the same
fact can be written from several places, each with its own, potentially
inconsistent, authorization logic. The cost is that the authority becomes a
single, high-value target. Compromising the authority compromises every
consumer's view of the fact simultaneously, whereas compromising one of
several duplicated copies in a non-SSOT system, while itself a real breach,
would not automatically corrupt every downstream reader's data.

**Audit trails become trustworthy rather than merely convenient.** An audit
log attached to the authority's single write path can claim, correctly, to
be a complete record of every change to the fact. An audit log attached to
one of several possible write paths in a non-SSOT system cannot make that
claim, since a change made through a different, unaudited path would be
invisible to it. This matters directly for regulatory requirements, such as
financial record-keeping or healthcare data change tracking, where a
demonstrably complete audit trail is often a legal requirement, not merely a
best practice.

**Personal data minimization is easier to reason about and easier to get
wrong.** If a piece of personal data genuinely has one authoritative home, a
data subject access or deletion request under a privacy regulation such as
the GDPR has one clear place to fulfil it. If the same personal data has
silently duplicated into caches, denormalized columns, logs, or analytics
pipelines, none of which are the acknowledged authority, a deletion request
fulfilled only at the authority leaves personal data behind in every shadow
copy, which is a compliance failure that traces directly back to the
shadow-copy failure mode described in dimension 11. This is judgement drawn
from how data-protection deletion obligations typically work, not a claim
sourced to a specific regulation's text, and any team relying on this
argument in a real compliance context should confirm the applicable
regulation's exact requirements rather than treating this paragraph as legal
advice.

**Denial of service risk concentrates at the authority.** Because every write,
and in the strict direct-read variant from dimension 8 every read as well,
routes through one component, that component is also the single most
effective target for a resource-exhaustion attack against the fact it
protects. A rate limit, a circuit breaker, and a caching layer sized for
worst-case load are not optional hardening for an SSOT authority under
adversarial conditions, they are part of the design, not an afterthought,
precisely because the principle deliberately removed the natural load
distribution that duplicated, independent copies would otherwise have
provided.

## 18. References

1. Wikipedia contributors. "Single source of truth."
   https://en.wikipedia.org/wiki/Single_source_of_truth verified 2026-08-02.
   Source of the definition quoted in dimension 1 and the "rarely possible in
   most enterprises" caveat used in dimension 4.
2. E. F. Codd. "A Relational Model of Data for Large Shared Data Banks."
   Communications of the ACM, volume 13, issue 6, 1970. Source of the
   normalization foundation the principle generalizes, referenced in
   dimension 1 as engineering-history judgement about lineage, not a directly
   quoted claim.
3. Redux maintainers. "Three Principles," Redux documentation.
   https://redux.js.org/understanding/thinking-in-redux/three-principles
   verified 2026-08-02. Source of the single-store principle quoted in
   dimensions 8 and 9.
4. React core team. "Sharing State Between Components," React documentation.
   https://react.dev/learn/sharing-state-between-components verified
   2026-08-02. Source of the lifting-state-up and single-source-of-truth
   language quoted in dimensions 8 and 9.
5. HashiCorp. "State," Terraform documentation.
   https://developer.hashicorp.com/terraform/language/state verified
   2026-08-02. Source of the state-as-mapping-authority description quoted in
   dimensions 8 and 9.
6. Kubernetes maintainers. "Kubernetes Components," Kubernetes documentation.
   https://kubernetes.io/docs/concepts/overview/components/ verified
   2026-08-02. Source of the etcd backing-store description quoted in
   dimensions 8 and 9.
7. PostgreSQL Global Development Group. "Constraints," PostgreSQL 17
   documentation, section 5.4.5, Foreign Keys.
   https://www.postgresql.org/docs/current/ddl-constraints.html verified
   2026-08-02. Source of the foreign-key referential-integrity quotation used
   in dimension 9.

## Code examples

Three languages, chosen because the principle appears idiomatically in each in
a different shape. TypeScript shows the frontend, lifted-state form. Python
shows a small backend authority with an explicitly enforced write path and a
derived, read-only cache. Go shows a concurrent-safe authority using a mutex,
which is the systems-programming shape of exactly one place a value can be
written, with everything else reading a consistent snapshot.

### TypeScript

Lifted state as the single source of truth for a form's validity, with two
child components reading the same fact rather than each tracking its own
copy.

```typescript
interface FormState {
  email: string;
  isValid: boolean;
}

function computeValidity(email: string): boolean {
  return email.includes("@") && email.length > 3;
}

class SignupForm {
  private state: FormState = { email: "", isValid: false };
  private listeners: Array<(s: FormState) => void> = [];

  onSubscribe(listener: (s: FormState) => void): void {
    this.listeners.push(listener);
    listener(this.state);
  }

  setEmail(email: string): void {
    this.state = { email, isValid: computeValidity(email) };
    for (const listener of this.listeners) {
      listener(this.state);
    }
  }

  getState(): FormState {
    return this.state;
  }
}

function submitButtonLabel(state: FormState): string {
  return state.isValid ? "Sign up" : "Enter a valid email";
}

function warningBanner(state: FormState): string {
  return state.isValid ? "" : "Please check your email address.";
}

const form = new SignupForm();
form.onSubscribe((s) => console.log(submitButtonLabel(s)));
form.onSubscribe((s) => console.log(warningBanner(s)));
form.setEmail("not-an-email");
form.setEmail("person@example.com");
```

### Python

A small in-process authority for a product's price, with a read-only cache
that must be invalidated rather than written directly, so the write path
stays singular.

```python
import time


class PriceAuthority:
    def __init__(self) -> None:
        self._prices: dict[str, float] = {}
        self._version = 0

    def set_price(self, sku: str, price: float) -> None:
        if price < 0:
            raise ValueError("price cannot be negative")
        self._prices[sku] = price
        self._version += 1

    def get_price(self, sku: str) -> float:
        if sku not in self._prices:
            raise KeyError(f"unknown sku {sku}")
        return self._prices[sku]

    @property
    def version(self) -> int:
        return self._version


class PriceCache:
    def __init__(self, authority: PriceAuthority, ttl_seconds: float) -> None:
        self._authority = authority
        self._ttl = ttl_seconds
        self._entries: dict[str, tuple[float, float, int]] = {}

    def get_price(self, sku: str) -> float:
        now = time.monotonic()
        cached = self._entries.get(sku)
        if cached is not None:
            price, fetched_at, seen_version = cached
            fresh = now - fetched_at < self._ttl
            same_version = seen_version == self._authority.version
            if fresh and same_version:
                return price
        price = self._authority.get_price(sku)
        self._entries[sku] = (price, now, self._authority.version)
        return price


authority = PriceAuthority()
authority.set_price("widget-1", 9.99)
cache = PriceCache(authority, ttl_seconds=30)
print(cache.get_price("widget-1"))
authority.set_price("widget-1", 12.50)
print(cache.get_price("widget-1"))
```

### Go

An authority guarded by a mutex so that concurrent goroutines never observe a
torn write, which is the concurrency-level version of exactly one place a
fact can be mutated.

```go
package main

import (
	"errors"
	"fmt"
	"sync"
)

type InventoryAuthority struct {
	mu     sync.RWMutex
	counts map[string]int
}

func NewInventoryAuthority() *InventoryAuthority {
	return &InventoryAuthority{counts: make(map[string]int)}
}

func (a *InventoryAuthority) SetStock(sku string, qty int) error {
	if qty < 0 {
		return errors.New("quantity cannot be negative")
	}
	a.mu.Lock()
	defer a.mu.Unlock()
	a.counts[sku] = qty
	return nil
}

func (a *InventoryAuthority) Reserve(sku string, qty int) error {
	a.mu.Lock()
	defer a.mu.Unlock()
	current, ok := a.counts[sku]
	if !ok {
		return fmt.Errorf("unknown sku %s", sku)
	}
	if current < qty {
		return fmt.Errorf("insufficient stock for %s: have %d, want %d", sku, current, qty)
	}
	a.counts[sku] = current - qty
	return nil
}

func (a *InventoryAuthority) Stock(sku string) int {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.counts[sku]
}

func main() {
	authority := NewInventoryAuthority()
	if err := authority.SetStock("widget-1", 10); err != nil {
		panic(err)
	}

	var wg sync.WaitGroup
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_ = authority.Reserve("widget-1", 1)
		}()
	}
	wg.Wait()

	fmt.Println("remaining stock:", authority.Stock("widget-1"))
}
```
