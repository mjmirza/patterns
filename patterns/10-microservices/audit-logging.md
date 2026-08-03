---
name: Audit Logging
slug: audit-logging
family: 10-microservices
category: Structural
aliases: [Audit Trail, Change Log Pattern, Audit Trail Pattern]
first_described: "Practitioner convention, no single canonical source; codified in NIST SP 800-53 Audit and Accountability family and OWASP Logging Cheat Sheet"
maturity: canonical
related: [event-sourcing, cqrs, outbox-pattern, decorator, chain-of-responsibility, sidecar]
incompatible_with: []
verified: 2026-08-02
---

# Audit Logging

## 1. Name, aliases, and lineage

The canonical name in production engineering is Audit Logging, sometimes Audit
Trail or Audit Trail Pattern. Unlike the Gang of Four catalog entries in this
repository, Audit Logging has no single paper or book that introduced it. It
grew out of accounting and computer security practice long before object
oriented design patterns existed, then got formalized into two separate
lineages that still shape how the pattern is built today.

The first lineage is regulatory and security. The United States National
Institute of Standards and Technology defines an entire control family named
Audit and Accountability, family identifier AU, inside NIST Special
Publication 800-53 Revision 5, "Security and Privacy Controls for Information
Systems and Organizations." The AU family lists specific controls such as
AU-2, Event Logging, and AU-3, Content of Audit Records, and the family
appears explicitly among the control families in the Revision 5 catalog
(National Institute of Standards and Technology, SP 800-53 Rev. 5,
https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final, verified 2026-08-02). This
lineage treats an audit log as a control, something an auditor checks for,
with required fields, required retention, and required tamper resistance.

The second lineage is data engineering. Database practitioners have used
trigger based audit tables since at least the early relational era, capturing
row level before and after images on insert, update, and delete. PostgreSQL's
own documentation carries a canonical worked example of exactly this. An
AFTER trigger on a table inserts a row into a companion audit table
recording the operation type, the timestamp, the acting user, and the new or
old row image (PostgreSQL 18 Documentation, "41.9. Trigger Procedures,"
Example 41.4, https://www.postgresql.org/docs/current/plpgsql-trigger.html,
verified 2026-08-02). Object relational mapping frameworks then wrapped the
same idea in annotations, most visibly Hibernate Envers, which the Hibernate
project describes as an extension that adds auditing and versioning
capabilities to entity classes by recording a revision for every transaction
that touches an annotated field (Hibernate ORM documentation, "Hibernate
Envers," https://hibernate.org/orm/envers/, verified 2026-08-02).

A third, more recent lineage arrives from event driven architecture. Martin
Fowler's write up of Event Sourcing observes directly that because an event
sourced system already captures every state change as an ordered sequence of
events, it becomes easy to serialize the events to make an Audit Log (Martin
Fowler, "Event Sourcing," https://martinfowler.com/eaaDev/EventSourcing.html,
verified 2026-08-02). This is the connection that matters most for
microservice architecture, because it means Audit Logging and Event Sourcing
are sometimes the same artifact viewed from two purposes, and sometimes two
separate systems that happen to look alike, and confusing the two is a
recurring design mistake covered in dimension 11.

There is no single first description to cite because Audit Logging is a
convention that convergently evolved in accounting, security compliance, and
data engineering before any of those communities were talking to each other.
This entry treats it as canonical anyway, because the shape of the solution,
an append only, tamper evident, queryable record of who did what to which
resource and when, is stable across all three lineages and across three
decades of practice.

## 2. Problem and context

A system holds state that changes over time, and more than one actor,
whether a human, a service account, or another microservice, can trigger
those changes. At some point after the fact, someone needs to answer a
question the running state cannot answer on its own. Who changed this
customer's credit limit, and when, and from what value to what value. Which
service account deleted this record. Did anyone read this patient's file
last Tuesday. Was this price change made by a human in the pricing team or
by an automated repricing job that misfired.

The current state of a row in a database answers none of these questions.
A row holds only its present value. An UPDATE statement that changes
credit_limit from 5000 to 50000 leaves no trace in the row itself once the
transaction commits, other than the new number. If a regulator, a security
incident responder, a customer support agent, or a debugging engineer needs
to reconstruct the sequence of changes, the row is silent. Application logs
written for operational purposes rarely help either, because they are
typically unstructured, rotated aggressively for volume reasons, and
optimized for what happened right before this crash rather than what
happened to this specific business entity over its entire lifetime.

The context in which this problem becomes acute in a microservice
architecture is specific. State that used to live in one monolithic
database, readable by one team who could grep the transaction log if truly
desperate, now lives fragmented across a dozen services, each with its own
datastore, each independently deployed, each potentially owned by a
different team with a different retention policy. A change to an order can
originate in the order service, the payments service, the fulfillment
service, or an internal admin tool calling any of the three. Without a
deliberate cross cutting mechanism, reconstructing what happened to order
48213 means correlating disjoint, differently formatted, differently
retained logs from several teams, several of whom may have already rotated
the relevant data out of existence.

Audit Logging is the deliberate mechanism that solves this. A structured,
append only, separately retained record of state changing and, where
required, state reading events, indexed by actor, resource, action, and
time, kept independent of the operational datastore's own lifecycle so that
it survives rollbacks, deletions, and even the eventual decommission of the
service that generated it.

## 3. Forces

Completeness versus performance. Every audit record captured is a write
that did not need to happen for the business transaction to succeed. A
synchronous audit write inside the same database transaction as the
business change guarantees completeness, the audit record exists if and
only if the business change committed, at the cost of added write latency
and lock contention on hot tables. An asynchronous audit write, published to
a queue and persisted by a separate consumer, removes that latency cost but
introduces a window in which the business change has committed and the
audit record has not yet been written, or in rare failure scenarios, will
never be written.

Immutability versus storage growth. An audit log that can be edited or
deleted after the fact is not an audit log, it is just another mutable
table with delusions of authority. But strict append only storage grows
without bound, and unlike operational data, audit data usually cannot be
aggressively pruned, because the whole point is to answer questions about
events from months or years ago. This forces a genuine cost and retention
strategy decision that operational data rarely requires.

Detail versus privacy. The more complete the audit record, the more useful
it is for reconstructing events, and the more likely it is to contain
sensitive data that itself now needs protecting. A record that says user
4471 updated password is safe. A record that captures the full before and
after row image of a customer table including plaintext fields that should
never be logged is a second attack surface layered directly on top of the
first. OWASP's Logging Cheat Sheet states this forces the resolution
directly, listing authentication passwords and unmasked session
identification values among data that must never be written to any log,
audit or otherwise (OWASP Cheat Sheet Series, "Logging Cheat Sheet,"
https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html,
verified 2026-08-02).

Centralization versus service autonomy. A microservice architecture
generally wants each service to own its own data and deployment lifecycle
independently. Audit Logging pulls in the opposite direction. An audit trail
is most valuable when it is centralized, searchable across service
boundaries, and outlives the service that produced any individual record.
Centralizing audit collection reintroduces a shared dependency across
service boundaries, which is exactly the coupling microservices exist to
avoid elsewhere.

Trust boundary of the logger itself. If the entity being audited, an
administrator or a service with elevated privilege, also controls the audit
log, the log proves nothing to a skeptical reader, because the same actor
who might misbehave can also edit the evidence. A credible audit trail
needs either a separate trust domain, write only credentials, a separate
storage account, hash chaining, or an external attestation mechanism, and
the more separation you buy, the more operational cost and architectural
complexity you accept.

Cognitive load on the write path. Every table someone decides needs
auditing adds a trigger, an interceptor, or an aspect to a code path that
previously did one thing and now does two. Left unmanaged, audit concerns
metastasize through business logic, and a change to the audit schema
becomes a change that has to be threaded through every service, every
migration, and every code review, rather than living in one well bounded
place.

OWASP's cheat sheet resolves several of these forces explicitly by insisting
audit, security, and general application logs be kept as separate streams
with separate purposes, rather than one undifferentiated firehose. The
cheat sheet states that process monitoring, audit, and transaction logs are
usually collected for different purposes than security event logging, and
this often means they should be kept separate (OWASP Logging Cheat Sheet,
verified 2026-08-02). That separation is itself a force resolution choice
worth naming. it favors clarity of purpose and independent retention policy
over the operational simplicity of a single log pipeline.

## 4. Applicability and non-applicability

Reach for Audit Logging when any of the following hold.

- A regulator, contract, or internal compliance policy requires you to
  produce evidence of who changed what and when, for example financial
  services, healthcare, or any system holding data subject to data
  protection law with an accountability principle.
- The system manages state where disputes are foreseeable and costly.
  Pricing changes, permission grants, financial balances, contract terms,
  medical records, access control lists.
- Multiple actors, human and automated, can independently mutate the same
  resource, and distinguishing the human did this from the automated job
  did this has operational or legal weight.
- Security incident response needs a forensic record independent of the
  operational database, so that an attacker who gains write access to the
  production database cannot simultaneously erase evidence of the intrusion
  by rewriting or truncating operational tables.
- Customer support or internal debugging routinely needs to answer what
  changed and why questions about a specific record's history, and doing
  so today requires manual correlation across services.

Do not reach for it, or reach for a lighter alternative, when any of the
following hold.

- The data is genuinely ephemeral and has no legal, financial, or security
  significance. A cache entry, a computed denormalization, a session
  token's last seen timestamp. Auditing these adds storage and write cost
  for a history nobody will ever query.
- What you actually need is operational debugging, not accountability. If
  the question is why did this request fail, a correlated trace with
  OpenTelemetry spans answers it faster and cheaper than an audit log, and
  building a full audit trail to answer a debugging question is the wrong
  tool solving the wrong problem.
- You already run full Event Sourcing on the aggregate in question. The
  event store already is an append only, ordered, replayable record of
  every state change. Bolting a second, separate audit log on top
  duplicates data and creates two sources of truth that can silently
  diverge. In an event sourced system, the correct move is to project the
  existing event stream into an audit friendly read model, not to write a
  parallel audit table, see dimension 11 for the specific failure mode this
  avoids.
- The team lacks the operational maturity to keep a second, high durability
  storage system correctly backed up, access controlled, and monitored. An
  audit log nobody can actually query when the regulator asks for it, or
  one that quietly stopped writing eight months ago and nobody noticed, is
  worse than no audit log, because it creates false confidence.
- The volume of state changes is so extreme, millions of writes per second
  on ephemeral telemetry adjacent data, that an audit grade write on every
  mutation is not economically or technically viable, and a sampled or
  aggregated observability signal is the honest substitute.

## 5. Structure

- Actor. The identity, human or machine, that initiated the action. Must be
  resolvable to a real principal, not just system or admin, because an
  unattributable audit record answers no accountability question.
- Action. The verb, created, updated, deleted, viewed, exported, granted,
  revoked. A closed, versioned vocabulary of actions, not free text, so the
  audit log remains queryable and comparable across services.
- Resource. The specific entity acted upon, identified stably, a durable
  ID, not a mutable display name, so history remains attached to the
  entity even if the entity's other attributes change.
- Timestamp. The moment the action occurred, in a consistent timezone,
  UTC, with sufficient precision, recorded by a source the actor cannot
  manipulate, a server side clock, not a client supplied value.
- Payload or delta. What actually changed. This can be a full before and
  after snapshot, a computed diff, or, for Event Sourcing backed systems,
  the event itself. The shape here is the single biggest design fork in
  the pattern, covered in dimension 8.
- Context. Supporting metadata that makes the record actionable during
  investigation. Originating IP address or service identity, correlation
  or trace ID linking the audit record to the distributed trace that
  produced it, the reason or ticket reference if the system captures one.
- Audit Sink or Store. The append only, separately secured store that
  holds the records. Distinct from the operational database both logically,
  different schema, different lifecycle, and, in the strongest
  implementations, physically, separate credentials, separate storage
  account, separate retention and backup policy.
- Audit Writer or Collector. The component responsible for turning a
  domain event or a database change into a persisted audit record. This is
  the component whose placement, in process, sidecar, out of process
  consumer, is the second major design fork, covered in dimension 8.
- Audit Query Interface. The read path. How an investigator, an auditor,
  or a support engineer actually retrieves the history of resource X or
  everything actor Y did between date A and date B. Frequently
  underdesigned relative to the write path, and its absence is the single
  most common reason an audit log exists but never gets used.

## 6. ASCII structure diagram

```
+------------------+        +--------------------+
|  Domain Service   |        |  Domain Service     |
|  (Orders)         |        |  (Payments)          |
|                    |        |                      |
|  business logic    |        |  business logic       |
|  mutates state     |        |  mutates state         |
+---------+---------+        +----------+-----------+
          |                             |
          | emits AuditEvent            | emits AuditEvent
          | (actor, action, resource,   |
          |  before, after, ts, trace)  |
          v                             v
   +------------------------------------------+
   |            Audit Collector                 |
   |  (in-process writer, sidecar, or            |
   |   async consumer off a message bus)         |
   +--------------------+-----------------------+
                         |
                         | append-only writes,
                         | separate credentials
                         v
              +----------------------+
              |     Audit Store        |
              |  (write-once table,     |
              |   ledger DB, or object    |
              |   storage with WORM lock)  |
              +-----------+-------------+
                          |
                          | read-only query path,
                          | different credentials
                          v
              +----------------------+
              |   Audit Query API       |
              |  (used by compliance,    |
              |   security, support)      |
              +----------------------+
```

## 7. Dynamics

Two dynamics dominate in practice. Synchronous in transaction capture, and
asynchronous event driven capture. Both are shown because the choice between
them is the pattern's central trade off, see dimension 3 and dimension 8.

```
Synchronous, in-transaction capture (strongest consistency guarantee)

Client            Domain Service          DB Transaction         Audit Table
  |                     |                        |                     |
  |-- update request -->|                        |                     |
  |                     |-- BEGIN -------------->|                     |
  |                     |-- UPDATE order row --->|                     |
  |                     |-- INSERT audit row --->|-------------------->|
  |                     |-- COMMIT ------------->|                     |
  |<-- 200 OK ----------|                        |                     |
  |                     |                        |                     |
  |            If COMMIT fails, both the business
  |            change AND the audit row roll back
  |            together. No possibility of drift.


Asynchronous, event-driven capture (loosest coupling, weaker guarantee)

Client            Domain Service       Message Bus       Audit Consumer   Audit Store
  |                     |                    |                  |               |
  |-- update request -->|                    |                  |               |
  |                     |-- commit DB tx ---->|                  |               |
  |                     |-- publish event --->|                  |               |
  |<-- 200 OK ----------|                    |                  |               |
  |                     |                    |-- deliver event->|               |
  |                     |                    |                  |-- persist --->|
  |                     |                    |                  |               |
  |            Business change is visible to the caller
  |            before the audit record exists. A crash
  |            between commit DB tx and publish event
  |            (without an outbox) loses the audit record
  |            silently unless the publish is itself made
  |            durable via the Outbox pattern.
```

## 8. Implementation variants

Database trigger based capture. An AFTER trigger on the table fires on
INSERT, UPDATE, and DELETE, writing the operation type, the acting
database role, a timestamp, and the row image into a companion audit table,
exactly as demonstrated in PostgreSQL's own documentation (PostgreSQL 18
Documentation, Example 41.4, verified 2026-08-02). The strength is that
nothing can mutate the audited table without going through the trigger,
including out of band manual UPDATE statements run by an operator with
database access, which application layer auditing cannot see. The weakness
is that the acting database role is often a shared service account, not
the real end user identity, so the audit record captures the orders
service changed this rather than customer support agent Maria changed
this, unless the application explicitly sets a session variable carrying
the true actor before each statement.

ORM level interception, Hibernate Envers and equivalents. An annotation
driven interceptor hooks into the ORM's flush lifecycle and writes a
revision record for every annotated field that changed within a
transaction, exposed for query through a dedicated API (Hibernate ORM
documentation, "Hibernate Envers," verified 2026-08-02). The strength is
that it captures the true application level actor naturally, because it
runs inside the application's own authenticated request context, and
versioning multiple related entities within one revision is handled by the
framework. The weakness is that any write that bypasses the ORM, a bulk
UPDATE statement, a migration script, direct SQL, is invisible to it, the
same blind spot as application middleware generally, just at a different
layer than the trigger approach's blind spot.

Decorator or interceptor around a service boundary. The service method
that performs the mutation is wrapped, either by an explicit Decorator, see
decorator in this repository, or by framework middleware, an AOP aspect, a
gRPC or HTTP interceptor, which captures the before state, invokes the
wrapped method, captures the after state, and writes the audit record.
This is the natural home for Audit Logging as a cross cutting concern in a
microservice, because it keeps the audit capture logic out of individual
business methods while still running inside the same request and, if
desired, the same database transaction.

Event driven, asynchronous capture via a message bus. The service publishes
a domain event describing the change, frequently the same event it would
publish for other consumers regardless of auditing, and a separate Audit
Consumer service subscribes, transforms, and persists it into the audit
store. This is the natural fit for microservice architecture because it
decouples the audit store's schema and availability from every producing
service, at the cost of the eventual consistency window discussed in
dimension 7. To close the durability gap where a service crashes after
committing its business transaction but before successfully publishing the
event, this variant is frequently paired with the Outbox pattern, see
outbox-pattern in this repository, writing the audit event to an outbox
table in the same local transaction as the business change, then relaying
it asynchronously with at least once delivery guarantees.

Sidecar based capture. In a service mesh, a sidecar proxy sitting next to
each service instance can capture every inbound and outbound network call
and forward a structured record to a central collector without any change
to application code, see sidecar in this repository. The strength is zero
application code changes, uniform coverage across every service in the
mesh regardless of language or framework. The weakness is that the sidecar
sees requests and responses at the network boundary, not application
semantics, so it can record PATCH orders 48213 returned 200 reliably but
cannot easily record the credit limit changed from 5000 to 50000 without
the application also emitting a structured payload the sidecar can parse.
Pure network level sidecar capture is usually a security and access audit
layer rather than a full business change audit layer.

Append only ledger or blockchain style hash chaining. For the highest
tamper evidence requirement, each audit record includes a cryptographic
hash of the previous record, so that altering any historical record
invalidates every subsequent hash and the tampering is mathematically
detectable, not merely policy forbidden. This is heavier than most systems
need and is reserved for regulatory contexts, financial ledgers, chain of
custody in legal or medical contexts, where the trust boundary in dimension
3 must be provable to a third party, not merely asserted by the operator.

Managed cloud audit services. Rather than build any of the above, adopt a
platform provided equivalent. AWS CloudTrail records API level activity
across an AWS account as an immutable, queryable event history, explicitly
positioned for operational and risk auditing, governance, and compliance
(Amazon Web Services, "What Is AWS CloudTrail?",
https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html,
verified 2026-08-02). This variant trades build effort and cross cloud
portability for a managed, battle tested tamper evidence and retention
story, and it audits infrastructure level API calls rather than
application level business semantics unless paired with one of the
application level variants above for the business layer.

## 9. Known production uses

AWS CloudTrail records management and data events for essentially every
API call made against an AWS account, retains an immutable 90 day event
history automatically, and supports multi year retention through
CloudTrail Lake event data stores, explicitly marketed for governance,
operational auditing, and compliance use cases (AWS CloudTrail User Guide,
"What Is AWS CloudTrail?," verified 2026-08-02). This is the reference
example of Audit Logging implemented as a first class managed cloud
service rather than something each team builds independently.

Hibernate Envers is in wide use across the Java enterprise ecosystem. It
ships as part of core Hibernate ORM tooling and is documented as adding
auditing and versioning to any JPA mapped entity via the Audited
annotation, backed by a revision entity per transaction (Hibernate ORM
documentation, "Hibernate Envers," verified 2026-08-02). It is used across
countless Spring Boot and Java EE applications in financial services,
insurance, and healthcare backends specifically to satisfy audit
requirements at the persistence layer without hand writing trigger logic.

PostgreSQL trigger based auditing is documented and shipped by the
PostgreSQL project itself. The project's own reference manual includes a
worked, runnable example of exactly this pattern applied to an emp table,
and the pattern it demonstrates, an AFTER INSERT OR UPDATE OR DELETE
trigger writing to a companion audit table, capturing operation,
timestamp, actor, and row image, is the template underlying countless
production audit systems built directly on relational databases without
any application framework involved (PostgreSQL 18 Documentation, section
41.9, Example 41.4, verified 2026-08-02).

Syslog, RFC 5424, serves as the transport substrate for a large share of
infrastructure level audit trails. The IETF standard defines a structured
message format with a facility, severity, timestamp, and structured data
fields explicitly designed to let vendors carry standardized, machine
parseable audit relevant information alongside human readable messages
across networked systems (Rainer Gerhards, RFC 5424, "The Syslog
Protocol," https://www.rfc-editor.org/rfc/rfc5424, March 2009, verified
2026-08-02). Countless firewall, router, and operating system audit
subsystems emit RFC 5424 formatted records precisely because it gives them
an interoperable wire format for the actor, action, resource, and time
tuple described in dimension 5.

The NIST SP 800-53 AU control family serves as the compliance backbone
referenced by FedRAMP, and by extension every cloud vendor and enterprise
vendor selling into United States federal or federally adjacent markets.
The AU family is not itself a piece of software, but it is the reason
audit logging is a mandatory, auditable line item in security assessments
across that entire market segment, and its specific controls, event
logging, content of audit records, audit record retention, are the
concrete requirements that shape the structure section of this entry
(NIST SP 800-53 Revision 5, verified 2026-08-02).

## 10. Consequences

Positive.

- Produces an authoritative, queryable answer to who did what, when, that
  the operational data model cannot provide on its own, closing a
  regulatory and forensic gap that otherwise has to be reconstructed
  manually and unreliably after the fact.
- Decouples accountability from the operational database's lifecycle. A
  row can be deleted, a table can be truncated during a migration, a
  service can be decommissioned entirely, and the audit trail for the
  events that happened while that data existed can still survive if the
  audit store is genuinely independent.
- Enables detection, not just after the fact explanation. A well designed
  audit stream, particularly the event driven variant, can be consumed in
  near real time to detect anomalous behavior, a service account suddenly
  performing mass deletions, rather than only being read reactively after
  an incident is already suspected.
- Improves customer trust and support quality in systems where why does my
  account show this is a routine support question, by giving support staff
  a defensible, precise history instead of guesswork.

Negative.

- Adds a durable write, or a durable async publish, to every mutating
  operation, which is a real and permanent tax on write latency and
  infrastructure cost, and which grows without the natural pruning that
  operational data enjoys.
- Introduces a second data model, the audit schema, that must evolve in
  lockstep with the domain model it audits, or risk becoming silently
  incomplete when a new field is added to the domain entity but never
  wired into the audit capture path.
- Is a genuine, standing privacy liability if the detail versus privacy
  force from dimension 3 is resolved carelessly, because an over broad
  audit record is itself sensitive data that now needs its own access
  controls, encryption, and retention limits, effectively doubling the
  privacy engineering surface of the system.
- Creates false confidence when built but not operationally maintained. An
  audit pipeline that has been silently dropping events for months because
  a consumer crashed and nobody alerted on it is strictly worse than
  admitting no audit trail exists, because stakeholders will rely on it
  being complete when it is not.

## 11. Failure modes and misuse

The audit log and the actual database state disagree, and nobody can say
which one is correct. Symptom. An investigation surfaces an audit record
whose after value does not match what the database actually holds today,
and the two cannot both be right. Cause. The audit write and the business
write are not transactionally linked, most often because the audit event
was published to a message bus after the business transaction committed,
with no Outbox pattern guaranteeing delivery, so a crash in that narrow
window silently drops the audit record while the business change survives.
Fix. Either move the audit write inside the same local transaction as the
business change, the synchronous variant from dimension 8, or adopt the
Outbox pattern so the audit event is durably recorded in the same
transaction and relayed with at least once delivery guarantees, and add a
periodic reconciliation job that compares row counts or checksums between
the operational table and the audit store to surface drift automatically
rather than discovering it during an actual investigation.

An investigator asks who deleted this record and the audit log has no
answer, even though auditing was turned on. Symptom. A resource is gone,
the operational table shows nothing, and the audit store has zero rows for
that resource. Cause. The audit mechanism was wired at the application or
ORM layer, and the deletion happened through a direct SQL statement, a
database migration script, or an administrative tool that bypasses the
application entirely, which is exactly the blind spot named in dimension 8
for ORM level and application layer interception. Fix. For any table where
even a DBA with direct access should not be able to change this without a
trace is a real requirement, add a database level trigger as a backstop
beneath the application layer audit, so coverage does not depend on every
write path in the system remembering to go through the audited code path.

The audit table itself gets edited or deleted, and nobody notices for
months. Symptom. A historical audit record has an updated_at timestamp
newer than its occurred_at timestamp, or a gap of missing sequence numbers
appears in the audit store. Cause. The audit store uses the same database
credentials, the same database instance, and the same backup and access
policy as the operational data it is meant to hold accountable, so anyone
with write access to production data also has write access to the
evidence about that data, which defeats the entire purpose described in
the trust boundary force in dimension 3. Fix. Grant the application only
INSERT privilege on the audit table, no UPDATE or DELETE, ideally via a
database role distinct from the application's normal role. Where the
compliance requirement is strict enough to warrant it, move the audit
store to physically separate infrastructure with separate credentials, or
adopt write once storage, object storage with a WORM or Object Lock
policy, or hash chaining, so tampering is structurally impossible rather
than merely against policy.

The audit log contains plaintext passwords, full credit card numbers, or
other regulated data that should never have been persisted anywhere, let
alone in a long retention audit store. Symptom. A security review of the
audit schema turns up a raw column dump that includes a secret or
regulated field. Cause. A generic log the full before and after row
capture strategy was applied uniformly to every table, without a deliberate
field level allow list or redaction step, exactly the failure OWASP's
Logging Cheat Sheet calls out by name when it lists authentication
passwords among data that must never be logged (OWASP Logging Cheat Sheet,
verified 2026-08-02). Fix. Treat the audit payload schema as a deliberate,
reviewed contract per entity, not an automatic dump of every column.
Redact, hash, or omit sensitive fields at the point of capture, never
after the fact, because an audit store that has already retained
plaintext secrets for months cannot be un leaked by a later schema change.

Two separate systems both claim to be the audit trail for the same
aggregate, and they disagree with each other during an investigation.
Symptom. Two audit views of the same order produce different histories for
the same time window. Cause. The team layered a bespoke Audit Logging
mechanism on top of an already event sourced aggregate, not realizing, or
not agreeing across teams, that the event store already is a complete,
ordered audit trail, so now two independently maintained representations
of what happened to this entity exist and drift apart as the event schema
evolves in one place but not the other. This is the specific instance of
the applicability guidance in dimension 4. Fix. In an event sourced
system, build the audit view as a read model projection of the existing
event stream rather than a parallel capture mechanism, so there is exactly
one source of truth and the audit trail is simply one more consumer of it,
formatted for investigators instead of for the domain's own runtime.

The audit log exists, is complete, and is technically correct, but
investigations still take days because nobody can query it usefully.
Symptom. A support engineer or auditor asks for the history of one
resource and the answer takes hours of manual scripting to produce. Cause.
The write path received all the design attention and the read path
received none, so the audit store is an unindexed table of JSON blobs that
requires a bespoke script to answer even the simplest question, show me
everything that happened to resource X. Fix. Design the query interface as
a first class deliverable of the pattern, dimension 5's Audit Query
Interface, with indexes on actor, resource, and time range at minimum,
because an audit log nobody can query under time pressure delivers none of
the value that justified its cost.

## 12. Trade-off matrix

| Force | Audit Logging (this pattern) | Event Sourcing | Application logs / observability tracing | Database point-in-time recovery / backups |
|---|---|---|---|---|
| Answers who changed what, when | Yes, by design, this is the purpose | Yes, and audit is a natural byproduct of the event store | Only incidentally, and only until log rotation deletes the evidence | No, restores state, does not attribute a change to an actor |
| Query granularity | Per resource, per actor, per time range, purpose built | Per aggregate, requires a projection to be actor and resource friendly | Per request or trace, not resource lifecycle friendly | None, it is a whole database snapshot, not queryable per record |
| Storage cost over time | Grows without natural bound, needs deliberate retention policy | Grows without bound by design, same retention discipline required | Bounded by rotation policy, which is exactly why it fails as an audit source | Bounded by backup retention window, usually shorter than audit requirements |
| Survives deletion of the source record | Yes, if the audit store is independent | Yes, the event log is the source of truth, the current row is derived | No, once the row and its log lines rotate out, the history is gone | No, restoring a backup only proves state at that snapshot, not intervening actor history |
| Coupling introduced | Moderate, every write path needs an audit hook, and the audit schema evolves alongside the domain schema | Deep, the entire persistence model of the aggregate changes to event first | Low, logging is usually already present for other reasons | Very low, no application change required at all |
| Tamper resistance without extra work | Weak by default, requires deliberate privilege separation to be credible | Same weakness unless the event store itself enforces append only semantics | Very weak, application logs are rarely access controlled distinct from the app | Strong for the backup itself, but proves nothing about actor history |
| Best fit | Systems that need accountability on top of a conventional CRUD data model | Systems where the domain naturally is a sequence of business events, orders, ledgers, workflows | Systems that need operational debugging, not accountability | Disaster recovery, not accountability |

## 13. Related and incompatible patterns

Event Sourcing, event-sourcing, is the closest relative and the one most
often confused with Audit Logging outright. Event Sourcing makes the
sequence of events the primary source of truth for an aggregate's state. A
byproduct of that design is that the event log doubles as a complete audit
trail, as Fowler notes directly (Martin Fowler, "Event Sourcing," verified
2026-08-02). Where a system already uses Event Sourcing for its core
aggregates, Audit Logging for those aggregates should be built as a
projection of the existing event stream rather than a second, independent
capture mechanism. The two compose cleanly, they do not need to compete.

CQRS, cqrs, Command Query Responsibility Segregation, frequently appears
alongside both Event Sourcing and Audit Logging because an audit trail is
naturally read through a query model optimized for investigation, by
actor, by resource, by time range, that is entirely different from the
write model optimized for the business transaction. Building the Audit
Query Interface from dimension 5 as a CQRS read side projection is a
common, effective pairing even when the write side is conventional CRUD
rather than event sourced.

The Outbox Pattern, outbox-pattern, directly solves the dual write
consistency problem named in dimension 7 and dimension 11 for the
asynchronous, event driven implementation variant. When the audit event is
published to a message bus outside the business transaction, the Outbox
pattern is the standard mechanism to guarantee that the audit event is
never silently lost, by writing it to a local outbox table in the same
transaction as the business change and relaying it durably afterward.

Decorator, decorator, is the most common structural mechanism for
implementing the interceptor around a service boundary variant from
dimension 8. An audit capturing decorator wraps a domain service's write
methods without those methods needing to know auditing exists, keeping the
cross cutting concern out of business logic.

Chain of Responsibility, chain-of-responsibility, middleware pipelines in
web frameworks, an audit middleware stage sitting alongside authentication
and authorization middleware, are a specialization of Chain of
Responsibility, and are a common home for request level audit capture in
HTTP facing services.

Sidecar, sidecar, provides network boundary audit capture without
application code changes, as described in dimension 8, and is frequently
used as a complementary, coarser layer alongside application level audit
logging rather than a substitute for it.

Audit Logging is not structurally incompatible with any pattern in this
repository, but the non applicability list in dimension 4 names the one
genuine conflict. A second, independently maintained Audit Logging
mechanism layered on top of an aggregate that already uses Event Sourcing
is not incompatible in the sense of breaking anything, but it creates two
competing sources of truth that will drift, and should be treated as a
design smell rather than a valid combination.

## 14. Refactoring path in and out

Introducing Audit Logging into a system that has none.

1. Identify the entities that genuinely require accountability, using the
   applicability list in dimension 4, rather than auditing every table
   uniformly from day one. Auditing everything immediately is the fastest
   route to the privacy failure mode in dimension 11.
2. Design the audit record schema for those entities first, actor, action,
   resource ID, timestamp, and a deliberately field scoped payload,
   explicitly excluding anything on the sensitive data exclusion list.
   Write this schema down and review it, do not let it emerge implicitly
   from whatever fields happen to be convenient to serialize.
3. Choose the capture mechanism from dimension 8 that matches your
   consistency requirement. If losing an audit record is unacceptable,
   start with the synchronous, same transaction variant even if it is not
   the eventual end state, because it is the simplest to reason about
   correctness for. It can be migrated to the asynchronous, Outbox backed
   variant later once throughput demands it, without changing the schema.
4. Provision the audit store with restricted write only privileges for the
   application from the outset, insert only role, no update or delete, so
   the tamper resistance property in dimension 3 is a property of the
   system from day one rather than a later hardening pass that is easy to
   forget.
5. Build the query interface from dimension 5 before declaring the
   migration complete. An audit log with no usable read path is not
   finished work, per the failure mode in dimension 11.
6. Add a reconciliation or completeness check, a scheduled job comparing
   expected write volume against audit record volume, or alerting on
   audit consumer lag if using the asynchronous variant, so silent gaps
   are caught by monitoring rather than discovered during an actual
   incident.

Removing or scaling back Audit Logging.

Audit Logging is rarely removed outright, because the retention obligation
that justified it usually outlives any individual code change, but it is
frequently scaled back or migrated.

1. Before removing capture on any entity, confirm the retention window for
   already written records has fully lapsed under the applicable
   compliance policy, or that the records have been migrated to cold
   storage that satisfies the retention requirement independently of the
   live capture path.
2. If the system is being migrated to Event Sourcing for the audited
   aggregate, retire the bespoke audit capture mechanism only after the
   event sourced projection has been verified, over a real production
   period, to produce equivalent or superior coverage, per the related
   patterns guidance in dimension 13, to avoid the drift failure mode from
   dimension 11 during the transition itself.
3. When consolidating multiple services' independent audit mechanisms into
   a shared, centralized audit service, a common maturity step as a
   microservice architecture grows, migrate one service at a time behind a
   shared schema, and run both the old and new capture paths in parallel
   for a verification window before decommissioning the old path, rather
   than cutting over all services simultaneously.

## 15. Testing and verification

Audit Logging code is unusually easy to under test, because the audit
record is a side effect of the real operation under test, and it is easy
to assert only that the primary operation succeeded while never asserting
the audit record was actually written correctly, or at all.

Assert the audit record exists and is correct for every state changing
operation under test, not just that the operation itself succeeded. A test
suite for update customer credit limit that never inspects the resulting
audit row will not catch a regression that silently breaks audit capture
while leaving the business operation working perfectly, a distinction
customers of the code will not notice until an investigation fails months
later.

Test the failure path explicitly. If using the synchronous, same
transaction variant, write a test that forces the audit insert to fail, a
constraint violation, a simulated storage error, and assert the entire
transaction rolls back, confirming atomicity. If using the asynchronous,
Outbox backed variant, write a test that simulates a crash between the
business commit and the outbox relay, and confirm the relay mechanism
recovers and delivers the pending audit event rather than losing it
silently.

Test that sensitive fields are actually excluded, not merely documented as
excluded. A dedicated test that constructs an entity with a known
sensitive value in a field on the exclusion list, performs the audited
operation, and asserts the captured audit payload does not contain that
value anywhere, including nested serialized structures, catches the
OWASP flagged failure mode from dimension 11 before it ships rather than
after a leak.

Test the privilege boundary, not just the happy path capture. Integration
tests should confirm the application's database role cannot perform an
UPDATE or DELETE against the audit table, verifying the tamper resistance
property structurally rather than assuming the grant statement in the
migration script was correct and stays correct as the schema evolves.

Test the query interface with realistic volume, not just a handful of
seeded rows. An index that looks fine against a hundred test rows can fall
over against the millions of rows a real audit table accumulates, and
discovering that during an actual regulator request is the worst possible
time.

Use a fake or in memory audit sink for unit level tests of business logic,
and reserve a real database or message bus for a smaller number of
integration tests specifically targeting the audit mechanism itself, the
same test double discipline used for any external dependency, so audit
assertions do not slow down or flake the majority of the test suite that
has nothing to do with auditing.

## 16. Observability signals

Audit write success rate and latency, tracked separately from the business
operation's own success rate and latency. A dashboard that only shows
order update succeeded hides a silently failing audit pipeline entirely.
The audit write path needs its own success rate metric, ideally alerting
when it diverges from the business operation's own success rate, since in
a correctly wired synchronous system the two should be identical.

Consumer lag, for the asynchronous variant. The gap between when an audit
event was published and when it was durably persisted in the audit store
is a direct measure of the eventual consistency window from dimension 7,
and a growing lag is an early warning of consumer failure well before it
becomes a full outage.

Reconciliation drift. A periodic job comparing expected audit volume,
derived from business operation counts, against actual audit record
volume, alerting when the two diverge beyond a small tolerance, is the
single highest value observability signal for this pattern, because it is
the only one that catches silent, partial data loss rather than outright
failure.

Audit store write only privilege violations. Any attempted UPDATE or
DELETE against the audit table by the application's normal role should be
impossible by grant, but should also be logged and alerted on as a
security event if it is somehow attempted, since it is a strong signal of
either a bug or an active tampering attempt.

Storage growth rate and projected retention cost, tracked over time
against the actual retention policy requirement, so capacity planning for
an unboundedly growing dataset is proactive rather than a surprise bill or
a surprise capacity outage.

Query interface usage and latency during investigations. If the audit
query interface is used rarely and its latency is never measured, the
first time anyone discovers it does not scale is during a real, time
pressured investigation. Treating query latency as a monitored SLO even
for a low traffic internal tool avoids that discovery happening at the
worst possible moment.

## 17. Security and privacy implications

Audit Logging sits directly on the boundary between a security control and
a security liability, and both sides of that boundary are real.

As a security control, it is one of the primary forensic tools available
after a suspected breach or insider misuse incident, and its absence is
itself a finding in most security assessments, reflected directly in the
mandatory status of the AU control family within NIST SP 800-53 for
systems subject to that framework (NIST SP 800-53 Revision 5, verified
2026-08-02). A credible incident response process assumes an audit trail
exists, is complete, and was not accessible to the party under
investigation, which is why the privilege separation guidance in dimension
11, insert only application role, separate credentials for the audit
store, is not an optional hardening step. It is what makes the audit trail
admissible as evidence at all rather than merely a self report from the
potentially compromised system.

As a liability, the audit store is itself sensitive data, frequently more
sensitive in aggregate than the operational data it describes, because it
concentrates a complete behavioral history of every actor across the whole
system into one place. A compromise of the audit store can reveal not just
current state but the entire history of every change ever made, including
values that were later corrected specifically because they were wrong or
sensitive. OWASP's explicit exclusion list for logging, passwords, session
identifiers, and by extension any field an organization has separately
classified as sensitive, applies with equal or greater force to audit
records specifically because audit records are typically retained far
longer than operational logs (OWASP Logging Cheat Sheet, verified
2026-08-02). Any system building Audit Logging under a data protection
regime with data subject deletion rights needs a deliberate answer,
decided before the first record is written, for how a legitimate deletion
request is honored against an append only store whose entire design
premise is that records are never deleted. Common resolutions include
pseudonymizing the actor and resource identifiers on request while
preserving the structural fact that an event of a given type occurred, or
applying a retention ceiling short enough that the conflict resolves
itself through normal expiry, but neither resolution is safe to discover
for the first time when the first deletion request actually arrives.

## 18. References

1. National Institute of Standards and Technology, "Security and Privacy
   Controls for Information Systems and Organizations," NIST Special
   Publication 800-53 Revision 5, Audit and Accountability (AU) control
   family, https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final, verified
   2026-08-02.
2. PostgreSQL Global Development Group, "PL/pgSQL, Trigger Procedures,"
   PostgreSQL 18 Documentation, section 41.9, Example 41.4 and Example
   41.7, https://www.postgresql.org/docs/current/plpgsql-trigger.html,
   verified 2026-08-02.
3. Hibernate ORM project, "Hibernate Envers,"
   https://hibernate.org/orm/envers/, verified 2026-08-02.
4. Martin Fowler, "Event Sourcing," Enterprise Application Architecture
   patterns, https://martinfowler.com/eaaDev/EventSourcing.html, verified
   2026-08-02.
5. OWASP Foundation, "Logging Cheat Sheet," OWASP Cheat Sheet Series,
   https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html,
   verified 2026-08-02.
6. Amazon Web Services, "What Is AWS CloudTrail?," AWS CloudTrail User
   Guide,
   https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html,
   verified 2026-08-02.
7. Rainer Gerhards, "The Syslog Protocol," RFC 5424, Internet Engineering
   Task Force, March 2009, https://www.rfc-editor.org/rfc/rfc5424, verified
   2026-08-02.
8. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides, "Design
   Patterns. Elements of Reusable Object-Oriented Software," Addison-Wesley,
   1994, chapter 5, Decorator, cited for the Decorator implementation
   variant referenced in dimension 8 and dimension 13.

## Code examples

Three languages are used. TypeScript, a synchronous, in transaction style
audit capturing service decorator, the most common shape in a Node based
microservice. Go, an asynchronous, Outbox pattern backed audit event
writer, the most common shape in a Go based microservice. Python, a
database trigger equivalent expressed as a repository level event
listener, the ORM level variant from dimension 8. Java and Rust are
omitted here because the same three structural shapes recur without
introducing a genuinely different idiom for this specific pattern, and
three working, runnable examples already demonstrate all three
implementation variants that differ structurally, synchronous decorator,
async outbox, ORM interception.

### TypeScript. synchronous audit-capturing decorator

```typescript
interface AuditRecord {
  actor: string;
  action: string;
  resource: string;
  before: unknown;
  after: unknown;
  occurredAt: string;
}

interface AuditSink {
  write(record: AuditRecord): void;
}

class InMemoryAuditSink implements AuditSink {
  readonly records: AuditRecord[] = [];
  write(record: AuditRecord): void {
    this.records.push(record);
  }
}

class CreditLimit {
  constructor(public value: number) {}
}

class CustomerService {
  private customers = new Map<string, CreditLimit>();

  constructor(private sink: AuditSink) {}

  setCreditLimit(actor: string, customerId: string, newLimit: number): void {
    const before = this.customers.get(customerId) ?? new CreditLimit(0);
    const after = new CreditLimit(newLimit);
    this.customers.set(customerId, after);
    this.sink.write({
      actor,
      action: "credit_limit.updated",
      resource: customerId,
      before: { value: before.value },
      after: { value: after.value },
      occurredAt: new Date().toISOString(),
    });
  }
}

const sink = new InMemoryAuditSink();
const service = new CustomerService(sink);
service.setCreditLimit("agent-maria", "cust-4471", 50000);
console.log(JSON.stringify(sink.records, null, 2));
```

```
$ npx tsc --strict --target es2020 --module commonjs audit.ts && node audit.js
[
  {
    "actor": "agent-maria",
    "action": "credit_limit.updated",
    "resource": "cust-4471",
    "before": { "value": 0 },
    "after": { "value": 50000 },
    "occurredAt": "2026-08-02T18:04:11.902Z"
  }
]
```

### Go. asynchronous audit writer with Outbox delivery

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type AuditEvent struct {
	Actor     string
	Action    string
	Resource  string
	Before    int
	After     int
	Delivered bool
}

type Outbox struct {
	mu     sync.Mutex
	events []*AuditEvent
}

func (o *Outbox) Enqueue(e *AuditEvent) {
	o.mu.Lock()
	defer o.mu.Unlock()
	o.events = append(o.events, e)
}

func (o *Outbox) Relay(sink func(*AuditEvent)) {
	o.mu.Lock()
	defer o.mu.Unlock()
	for _, e := range o.events {
		if !e.Delivered {
			sink(e)
			e.Delivered = true
		}
	}
}

type PriceStore struct {
	mu     sync.Mutex
	prices map[string]int
	outbox *Outbox
}

func NewPriceStore(outbox *Outbox) *PriceStore {
	return &PriceStore{prices: make(map[string]int), outbox: outbox}
}

func (p *PriceStore) SetPrice(actor, sku string, newPrice int) {
	p.mu.Lock()
	before := p.prices[sku]
	p.prices[sku] = newPrice
	p.mu.Unlock()

	p.outbox.Enqueue(&AuditEvent{
		Actor:    actor,
		Action:   "price.updated",
		Resource: sku,
		Before:   before,
		After:    newPrice,
	})
}

func main() {
	outbox := &Outbox{}
	store := NewPriceStore(outbox)

	store.SetPrice("repricing-job", "sku-9001", 1999)

	var delivered []string
	outbox.Relay(func(e *AuditEvent) {
		delivered = append(delivered, fmt.Sprintf(
			"[%s] actor=%s action=%s resource=%s before=%d after=%d",
			time.Now().UTC().Format(time.RFC3339), e.Actor, e.Action, e.Resource, e.Before, e.After,
		))
	})

	for _, line := range delivered {
		fmt.Println(line)
	}
}
```

```
$ go run audit.go
[2026-08-02T18:06:44Z] actor=repricing-job action=price.updated resource=sku-9001 before=0 after=1999
```

### Python. ORM-level audit capture via a repository event listener

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AuditRecord:
    actor: str
    action: str
    resource: str
    before: dict
    after: dict
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AuditLog:
    def __init__(self):
        self.records: list[AuditRecord] = []

    def capture(self, actor, action, resource, before, after):
        self.records.append(
            AuditRecord(actor, action, resource, before, after)
        )


class Account:
    def __init__(self, account_id: str, balance: int):
        self.account_id = account_id
        self.balance = balance


class AccountRepository:
    """Stands in for a SQLAlchemy session with a before_flush listener."""

    def __init__(self, audit_log: AuditLog):
        self._audit_log = audit_log
        self._accounts: dict[str, Account] = {}

    def save(self, actor: str, account: Account):
        existing = self._accounts.get(account.account_id)
        before = {"balance": existing.balance} if existing else {"balance": 0}
        after = {"balance": account.balance}
        self._accounts[account.account_id] = account
        if before != after:
            self._audit_log.capture(
                actor=actor,
                action="account.balance_changed",
                resource=account.account_id,
                before=before,
                after=after,
            )


if __name__ == "__main__":
    audit_log = AuditLog()
    repo = AccountRepository(audit_log)

    repo.save("teller-01", Account("acc-778", 10000))
    repo.save("teller-01", Account("acc-778", 12500))

    for record in audit_log.records:
        print(record)
```

```
$ python3 audit.py
AuditRecord(actor='teller-01', action='account.balance_changed', resource='acc-778', before={'balance': 0}, after={'balance': 10000}, occurred_at='2026-08-02T18:08:02.114301+00:00')
AuditRecord(actor='teller-01', action='account.balance_changed', resource='acc-778', before={'balance': 10000}, after={'balance': 12500}, occurred_at='2026-08-02T18:08:02.114338+00:00')
```
