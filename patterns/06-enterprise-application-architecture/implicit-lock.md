---
name: Implicit Lock
slug: implicit-lock
family: 06-enterprise-application-architecture
category: Concurrency
aliases: [Framework-Managed Locking, Transparent Concurrency Control]
first_described: "Fowler 2002"
maturity: canonical
related: [optimistic-offline-lock, pessimistic-offline-lock, coarse-grained-lock, layer-supertype, unit-of-work]
incompatible_with: []
verified: 2026-08-02
---

# Implicit Lock

## 1. Name, aliases, and lineage

The canonical name is Implicit Lock. It is documented as one of four offline
concurrency control patterns in Martin Fowler, *Patterns of Enterprise
Application Architecture*, Addison-Wesley, 2002, chapter 16, "Concurrency",
alongside Optimistic Offline Lock, Pessimistic Offline Lock, and Coarse-Grained
Lock. The pattern's stated intent is that it "allows framework or layer
supertype code to acquire offline locks" ([martinfowler.com, Enterprise
Application Architecture catalog](https://martinfowler.com/eaaCatalog/),
verified 2026-08-02). The individual pattern page puts the mechanism plainly.
"Locking tasks that cannot be overlooked should be handled not explicitly by
developers but implicitly by the application"
([martinfowler.com/eaaCatalog/implicitLock.html](https://martinfowler.com/eaaCatalog/implicitLock.html),
verified 2026-08-02).

Fowler does not present Implicit Lock as a standalone lock acquisition
mechanism. It has no structure of its own beyond "put the version check or the
lock acquisition somewhere the developer cannot skip it." It is a meta-pattern,
a placement rule layered over Optimistic Offline Lock or Pessimistic Offline
Lock, and it only makes sense in relation to one of those two. This is why
the aliases used in practice, framework-managed locking and transparent
concurrency control, describe the property (the developer does not write the
lock code) rather than the mechanism (which lock).

No other named author or catalog independently coined this term. It survives
in industry usage as a description of a category of ORM and framework
behavior, Hibernate's `@Version` handling, Rails' `lock_version`, EF Core's
concurrency tokens, rather than as a term developers use to name a pattern
out loud in the way they say "Factory Method" or "Repository." Practitioners
more often say "the ORM handles optimistic locking for me" than "I am using
Implicit Lock," but the underlying design decision, that locking discipline
is moved out of call sites and into a layer supertype, base class, or
code-generation step, is exactly what Fowler names.

## 2. Problem and context

Optimistic Offline Lock and Pessimistic Offline Lock both solve the problem of
detecting or preventing conflicting concurrent business transactions, but both
share a second problem that sits one layer above the mechanism. Once a team
decides to use version checking or explicit row locks, that decision has to be
applied consistently, everywhere a business transaction touches shared data,
for the lifetime of the application, by every developer who ever edits that
codebase.

Fowler states the risk directly on the pattern's page. "The key to any locking
scheme is that there are no gaps in its use"
([martinfowler.com/eaaCatalog/implicitLock.html](https://martinfowler.com/eaaCatalog/implicitLock.html),
verified 2026-08-02). If ten call sites load an entity, mutate it, and save it,
and nine of them remember to check the version column while the tenth does
not, the locking scheme has a hole. The hole is not visible in code review
unless the reviewer is specifically hunting for it, because the ninth call
site's code and the tenth call site's code both compile, both run, and both
look like ordinary persistence code. The failure only shows up when two
concurrent users happen to collide on that one omitted call site, and by then
the data is already silently corrupted, a classic lost-update outcome.

This is compounded by a second fact from the same source. "Offline
concurrency management is difficult to test, such errors might go undetected
by all of your test suites"
([martinfowler.com/eaaCatalog/implicitLock.html](https://martinfowler.com/eaaCatalog/implicitLock.html),
verified 2026-08-02). A missing lock check does not throw an exception in a
single-threaded unit test. It requires two transactions racing against the
same row, which most test suites never construct, so the gap survives code
review, survives the test suite, and ships. It is discovered in production,
usually by a support ticket describing data that "reverted" or "lost changes
someone else made five minutes ago."

The context in which Implicit Lock is the right answer is specific. A team has
already chosen a concurrency control mechanism, optimistic version checking or
pessimistic row locking, the mechanism has a repeatable shape, increment a
version column, or acquire a row lock, at a fixed point in the request or
transaction lifecycle, and the team has some place to put code that every
persistence operation is forced to pass through, whether that is a layer
supertype in Fowler's sense, an ORM's unit-of-work commit hook, an
aspect-oriented interceptor, or a code generator that stamps every generated
data-access class with the same boilerplate.

## 3. Forces

**Developer discipline versus mechanical guarantee.** Explicit locking asks
every developer, on every call site, forever, to remember one extra step.
Human discipline degrades under deadline pressure, staff turnover, and simple
fatigue. Mechanical enforcement, a base class, a framework hook, a
code-generation template, does not forget and does not get tired, but it
requires a chokepoint to exist, and not every persistence architecture has
one.

**Correctness versus flexibility.** Moving the locking decision into shared
infrastructure means every persistence operation gets the same locking
behavior. That is the entire point when uniformity is what closes the gap. It
is also the cost. A call site that genuinely needs a different locking
strategy, a read that intentionally tolerates staleness for performance, or a
batch job that deliberately wants last-writer-wins, has to fight the
infrastructure to opt out, rather than simply not opting in.

**Debuggability versus invisibility.** The stated value of Implicit Lock is
that the developer does not see the locking code at the call site. That is
also the direct cost when something goes wrong. A developer investigating a
`StaleObjectError` or an `OptimisticLockException` at 2 a.m. is looking at an
exception thrown from framework code they did not write, at a line number in
their own class that contains no visible reference to locking, versioning, or
concurrency at all. Understanding why the exception fired requires knowing
that a layer supertype or an ORM interceptor is silently rewriting every
UPDATE statement.

**Coupling to the chokepoint.** Implicit Lock only works if every write path
genuinely passes through the shared code. Raw SQL issued outside the ORM,
batch scripts run directly against the database, an administrative console
that bypasses the application layer, or a second application sharing the same
database, all defeat the guarantee silently, because the whole mechanism
depends on there being exactly one gate and everything going through it.

**Cost of building the chokepoint.** For a team with a layer supertype
already in place, or an ORM already in the stack, Implicit Lock is close to
free, a configuration decision, annotate a column, enable a feature flag,
rather than new code. For a team without such infrastructure, building a
reliable chokepoint from nothing, a custom data-access base class, an
interceptor framework, is itself a nontrivial investment that has to be
justified by the size of the team and the cost of a lost-update bug.

## 4. Applicability and non-applicability

Reach for Implicit Lock when:

- The team has already chosen Optimistic Offline Lock or Pessimistic Offline
  Lock as the concurrency strategy and needs it applied without gaps.
- A layer supertype, ORM, unit-of-work implementation, or code generator
  already sits between every business-logic call and the database, so adding
  the locking behavior there is a configuration change rather than new
  infrastructure.
- The team is larger than one person, has turnover, or has junior developers
  joining over time, so the argument "everyone will always remember to check
  the version" cannot be trusted for the life of the system.
- Concurrent access to the same row by independent business transactions is a
  real, expected occurrence, not a hypothetical edge case.
- The cost of a silent lost update (financial data, inventory counts,
  document content, appointment slots) is higher than the cost of an
  occasional retry or conflict-resolution prompt shown to the user.

Do NOT reach for Implicit Lock when:

- There is no chokepoint. If persistence code is scattered across raw JDBC,
  raw ADO.NET, or hand-written SQL with no shared base class or ORM layer,
  there is nowhere to put the implicit behavior, and building one purely to
  host a lock check is disproportionate to the problem.
- The application is genuinely single-user, or all writers are already
  coordinated by an external mechanism (a single-writer queue, a
  single-threaded worker), so there is no concurrent-write scenario for the
  lock to protect against.
- The data being written is not business-critical and an occasional
  overwrite is an acceptable, cheap-to-fix outcome, such as a UI preference
  flag or a denormalized cache column that is rebuilt on the next read.
- The team needs per-call-site control over locking behavior more than it
  needs uniformity, for example a system where some transactions must use
  optimistic locking and others must deliberately bypass it, and the
  distinction is load-bearing to the business logic rather than an oversight.
  Implicit enforcement fights this kind of intentional heterogeneity.
- Every write already goes through raw SQL for performance reasons (bulk
  loaders, ETL jobs, reporting pipelines) that bypass the ORM by design.
  Implicit Lock cannot protect writes that never pass through its
  chokepoint, and pretending it does is a false sense of safety, arguably
  worse than no locking scheme at all because the team stops thinking about
  the gap.
- The system is a single-node, single-process embedded application with no
  concurrent transactions at all, where the entire concurrency-control
  problem does not exist.

## 5. Structure

**Layer Supertype (or equivalent chokepoint).** The shared base class,
framework hook, ORM session or unit-of-work implementation, or
code-generation template that every persistence operation passes through.
This is the participant that makes Implicit Lock possible, without it the
pattern has nothing to attach to. In Hibernate this role is played by the
persistence context flush mechanism, in ActiveRecord it is the `save` method
on `ActiveRecord::Base`, in EF Core it is `DbContext.SaveChanges`.

**Locking Mechanism (Optimistic Offline Lock or Pessimistic Offline Lock).**
The actual concurrency-control strategy being made implicit. Implicit Lock
never replaces this participant, it only relocates where its code lives.
Optimistic Offline Lock contributes a version column and a version-comparison
check on write. Pessimistic Offline Lock contributes a lock table or a
database-level row lock acquired on read.

**Domain Object.** The entity being protected. It carries the version field
(for the optimistic variant) or is the row being locked (for the pessimistic
variant), but it does not itself contain any locking logic. This is the
defining structural signature of Implicit Lock, the domain object is
unaware that it is participating in a concurrency-control scheme at all.

**Business Transaction, or Call Site.** The application code that loads,
mutates, and saves the domain object. Under Implicit Lock this participant
writes ordinary-looking persistence code, calls `save()` or `SaveChanges()` or
their equivalent, and has no visible reference to versions, locks, or
concurrency. It is the participant the pattern is protecting from itself.

**Conflict Signal.** The exception or return value the chokepoint raises when
it detects a conflict, `StaleObjectError` in ActiveRecord,
`OptimisticLockException` in JPA, `DbUpdateConcurrencyException` in EF Core.
This is where implicitness ends. The failure mode is necessarily explicit,
because someone has to catch it and decide what to do next.

## 6. ASCII structure diagram

```
+-----------------------+
|   Business Transaction |
|   (ordinary call site) |
|                        |
|   person.name = "Paul" |
|   person.save()        |----+
+-----------------------+    |
                              | delegates through
                              v
+-----------------------------------------+
|          Layer Supertype / Chokepoint     |
|   (ActiveRecord::Base, DbContext,         |
|    Hibernate Session, code-gen template)  |
|                                            |
|   on save():                              |
|     1. read current version from object   |
|     2. build UPDATE ... WHERE id=? AND    |
|        version=?                          |
|     3. execute                            |
|     4. rows_affected == 0 ?               |
|          raise Conflict Signal            |
|        else                               |
|          increment stored version         |
+-----------------------------------------+
        |                          |
        | uses                     | protects
        v                          v
+------------------+    +---------------------------+
| Locking Mechanism |    |       Domain Object        |
| (Optimistic or    |    |  (no locking code, only a |
|  Pessimistic       |    |   plain "version" field)  |
|  Offline Lock)     |    +---------------------------+
+------------------+

Never appears in the Business Transaction box, version comparisons,
WHERE-clause version predicates, lock acquisition calls.
```

## 7. Dynamics

The sequence below is written for the optimistic variant, since that is the
form documented in the three production systems in dimension 9. The
pessimistic variant follows the same shape, substituting "acquire row lock on
read, inside the chokepoint" for "attach version to update, inside the
chokepoint."

```
Transaction A                Transaction B              Chokepoint / DB
     |                             |                          |
     | load Person(id=1)          |                          |
     |---------------------------------------------------->  |
     |  <-- Person{name:"John", version:5} ------------------|
     |                             |                          |
     |                             | load Person(id=1)        |
     |                             |------------------------->|
     |                             |  <-- {name:"John", v:5}--|
     |                             |                          |
     | mutate: name = "Paul"      |                          |
     | call save()                |                          |
     |---------------------------------------------------->   |
     |    (chokepoint builds                                  |
     |     UPDATE person SET name='Paul', version=6           |
     |     WHERE id=1 AND version=5)                          |
     |    rows_affected = 1, success                          |
     |  <-- OK, stored version now 6 -------------------------|
     |                             |                          |
     |                             | mutate: name = "Jane"    |
     |                             | call save()               |
     |                             |------------------------->|
     |                             |   (chokepoint builds      |
     |                             |    UPDATE person SET      |
     |                             |    name='Jane', version=6 |
     |                             |    WHERE id=1 AND version=5)|
     |                             |   rows_affected = 0        |
     |                             |  <-- Conflict Signal ------|
     |                             |   (StaleObjectError /      |
     |                             |    OptimisticLockException)|
     |                             |                          |
```

Neither Transaction A nor Transaction B wrote a single line referencing
`version`. Both loaded and saved a plain domain object. The chokepoint alone
knew that a version predicate belonged in the WHERE clause, alone compared
the affected-row count, and alone decided whether to raise the conflict
signal. Transaction B is the one that must now decide, at the point where it
catches the exception, how to resolve the conflict (retry against fresh data,
surface a merge UI, or abandon its change).

## 8. Implementation variants

**ORM-managed optimistic version column.** The most common real-world
instance. A version or timestamp column is declared once, in the entity
mapping (`@Version` in JPA, `lock_version` convention in ActiveRecord,
`[Timestamp]` or `IsConcurrencyToken()` in EF Core), and the ORM's own save
path rewrites every UPDATE to include the version predicate and to
increment or regenerate the token on success. The developer's persistence
code is identical whether or not the version column exists. This is
documented in detail for all three systems in dimension 9.

**Layer supertype with a mandatory `save()` template method.** Fowler's own
framing, a hand-written base class (not necessarily a third-party ORM) that
every domain object's persistence class extends, where the base class's
`save()` or `update()` method contains the lock-acquisition or
version-check logic and subclasses cannot override it (a `final` or
`sealed` method, or a private helper the subclass has no path around).
Common in codebases that predate widespread ORM adoption or that
deliberately avoid a full ORM.

**Interceptor, or aspect-oriented, enforcement.** An interceptor registered
against a session, a decorator wrapping a repository, or an AOP `@Around`
advice that wraps every write method, checking or acquiring the lock before
delegating to the real write. This variant is used when the codebase already
has a dependency-injection or AOP container and wants to add implicit
locking to existing code without rewriting a shared base class.

**Code-generation-enforced.** A code generator (an ORM's entity generator,
a database-first scaffolding tool) emits the version check or lock
acquisition into every generated data-access class at generation time, so
the implicitness is a compile-time property of the generated code rather
than a runtime dispatch through a shared class. The developer's hand-written
code calls the generated method and never sees the locking logic, but
unlike the layer-supertype variant, there is no single class to point at,
the enforcement is distributed across every generated file, which makes
regenerating consistently, rather than editing generated code by hand,
part of the discipline.

**Database-native pessimistic implicit locking.** `SELECT ... FOR UPDATE`
wrapped inside a queryset method or ORM call, such as Django's
`select_for_update()`, so the developer writes an ordinary queryset filter
and the row-level lock is acquired by the framework as a side effect of
calling that method inside a transaction, documented in dimension 9. The
"implicit" property here is narrower than the ORM-optimistic variant. The
developer does still call a specifically-named method, so the choice to
lock is visible at the call site even though the SQL-level lock syntax is
not.

## 9. Known production uses

**Hibernate / JPA `@Version`.** Hibernate's documentation carries a
dedicated Locking chapter (section 11) covering the `@Version` annotation,
where declaring an integer, timestamp, or UUID field as the entity's version
causes Hibernate's flush and commit machinery to append the version
predicate to every UPDATE and DELETE statement it generates for that entity,
and to raise `OptimisticLockException` when the affected-row count is zero
([docs.hibernate.org, Hibernate ORM 6.4 User Guide, section 11,
"Locking"](https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html),
verified 2026-08-02). The application's repository and service code, in the
overwhelming majority of Hibernate applications, contains no reference to
the version column at all, it calls `entityManager.persist()` or
`session.save()` on a plain entity and the version handling happens entirely
inside Hibernate's session flush cycle, which is exactly the layer-supertype
chokepoint Fowler describes.

**Ruby on Rails ActiveRecord optimistic locking.** ActiveRecord's own API
documentation states that each update to a record increments the integer
column `lock_version`, and that the locking mechanism is set up so that when
the same record has been loaded twice and both copies are later saved, the
second save raises a `StaleObjectError` because its stored version no longer
matches
([api.rubyonrails.org/classes/ActiveRecord/Locking/Optimistic.html](https://api.rubyonrails.org/classes/ActiveRecord/Locking/Optimistic.html),
verified 2026-08-02). A developer enables this by adding a `lock_version`
integer column to the table by migration, no application code, at any call
site that calls `record.save`, references locking or versioning directly.
The `ActiveRecord::Base#save` method, the shared base class every model in a
Rails application inherits from, is the chokepoint that performs the version
comparison.

**Django `select_for_update()`.** Django's ORM documentation describes
`select_for_update()` as a queryset method that "locks rows until the end of
the transaction, generating a `SELECT ... FOR UPDATE` SQL statement on
supported databases," used inside a `transaction.atomic()` block
([docs.djangoproject.com/en/5.0/ref/models/querysets/#select-for-update](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#select-for-update),
verified 2026-08-02). This is the pessimistic variant. The developer writes
`Entry.objects.select_for_update().filter(...)`, an ordinary-looking
queryset call, and Django's ORM query-compilation layer, not the developer,
emits the database-specific `FOR UPDATE` syntax and manages when the lock is
released, at transaction end, rather than requiring the developer to issue
raw `LOCK` or `FOR UPDATE` SQL themselves.

**Entity Framework Core concurrency tokens.** Microsoft's EF Core
documentation states that when a property is configured as a concurrency
token (via `[Timestamp]` or `IsRowVersion()`), "when an update or delete
operation is performed during `SaveChanges()`, the value of the concurrency
token on the database is compared against the original value read by EF
Core," and shows the framework generating `UPDATE [People] SET [FirstName] =
@p0 WHERE [PersonId] = @p1 AND [Version] = @p2` automatically, raising
`DbUpdateConcurrencyException` when zero rows are affected
([learn.microsoft.com/en-us/ef/core/saving/concurrency](https://learn.microsoft.com/en-us/ef/core/saving/concurrency),
verified 2026-08-02). The application code that calls
`context.SaveChangesAsync()` is, again, unaware of the WHERE-clause rewrite,
`DbContext.SaveChanges` is the chokepoint.

## 10. Consequences

Positive:

- Eliminates an entire class of bug (the forgotten lock check) by removing
  the possibility of forgetting rather than relying on discipline or review
  to catch it, which is a strictly stronger guarantee than any process-based
  mitigation.
- Reduces the amount of code every business-logic developer has to write and
  understand at each call site, persistence code reads as plain object
  loading and saving.
- Centralizes the locking policy in one place (or one small set of places),
  so changing the policy, switching from optimistic to pessimistic for one
  entity, adding retry-on-conflict logic, tuning the isolation level, is a
  localized change rather than a search-and-replace across the codebase.
- Makes the locking behavior consistent across the entire application by
  construction, which in turn makes it possible to reason about the system's
  concurrency guarantees as a whole rather than auditing each call site.

Negative:

- The mechanism that makes locking mandatory also makes it invisible, so a
  developer debugging a conflict exception must know that a layer supertype
  or framework hook exists and is the source of the behavior, the failure
  surfaces far from the code that "caused" it in the sense a developer
  usually means.
- Provides zero protection for any write path that bypasses the chokepoint,
  raw SQL, direct database access from another application, an
  administrative script run outside the ORM. Teams that believe "the ORM
  handles concurrency" can be surprised when a bulk-update script or a
  reporting job silently corrupts data because it never went through
  `save()`.
- Removes the option for a call site to intentionally opt out of the locking
  policy without fighting the framework, which is a genuine cost on systems
  where some writes legitimately need different, or no, concurrency control.
- Adds a dependency on the layer supertype or framework's specific
  implementation of the check, a bug or a version upgrade in the ORM's
  concurrency-token handling becomes a systemic risk across every entity
  that relies on it, rather than a localized risk in one hand-written
  function.

## 11. Failure modes and misuse

**Symptom.** Data silently reverts to an older state, or one user's change
disappears with no error shown to anyone, in a system the team believed had
concurrency protection. **Cause.** A write path that bypasses the
chokepoint, most often a batch job, a data migration script, or an
administrative tool that talks to the database directly (raw SQL, a second
connection string, a different ORM instance configured without the version
mapping). **Fix.** Audit every write path against the entity, not only the
application's primary request-handling code, and either route it through
the same chokepoint or explicitly document and accept that path as outside
the locking scheme.

**Symptom.** A production incident where `OptimisticLockException` or
`StaleObjectError` fires in a code path the team assumed was uncatchable or
that is simply never caught, producing a 500 error visible to the end user
instead of a graceful retry or merge prompt. **Cause.** Implicit Lock makes
the lock acquisition automatic, but it does not make conflict handling
automatic, someone still has to write a catch block that decides what
happens on conflict, and because the exception is thrown from framework
code rather than application code, teams sometimes never write that catch
block at all, treating the exception as a theoretical possibility rather
than an expected outcome of concurrent use. **Fix.** Treat the conflict
exception the same way network timeouts are treated, expected, and handled
at a defined boundary (a retry loop, a controller-level exception handler
that maps it to a user-facing "someone else changed this, please review and
retry" message), never left to propagate as an unhandled 500.

**Symptom.** Frequent, unexplained conflict exceptions on a single entity
that has genuinely low concurrent write volume. **Cause.** The version or
timestamp column is being touched by an unrelated write, most commonly an
ORM configuration where every property change bumps the version even for
fields the business does not treat as business-relevant (a "last viewed"
timestamp, a cache-invalidation counter updated on every read), so two
users editing genuinely different fields collide on a version that neither
of them cares about semantically. **Fix.** Scope the concurrency token
narrowly, exclude non-business fields from triggering a version bump (EF
Core's `IsConcurrencyToken()` on a specific property rather than the whole
row, or per-property optimistic locking in JPA via
`@OptimisticLock(excluded=true)` on individual attributes), or move to
field-level rather than row-level conflict detection where the framework
supports it.

**Symptom.** Long-held pessimistic locks cause application-wide slowdowns or
apparent deadlocks under load, traced back to a request that acquired a row
lock via the chokepoint and then performed a slow external call (an HTTP
request, a file upload) before committing. **Cause.** The implicit
acquisition point (entering the queryset, entering the transaction block)
is easy to reach, and easy access lowers the bar for holding the lock across
work that has nothing to do with the locked row, because the developer
never had to think explicitly about "I am now holding a database lock."
**Fix.** Keep the transaction boundary, and therefore the lock's lifetime,
as short as possible, move slow, non-database work outside the
`select_for_update()` or lock-holding block entirely, and treat "how long is
this transaction open" as a reviewed property of any pessimistic-locking
code path even though the lock acquisition itself required no explicit
review.

## 12. Trade-off matrix

| Force | Implicit Lock (wrapping Optimistic) | Explicit optimistic checks at each call site | Implicit Lock (wrapping Pessimistic) | No concurrency control |
|---|---|---|---|---|
| Consistency guarantee | Strong, cannot be forgotten at a call site inside the chokepoint | Strong in theory, degrades to whatever the weakest call site actually implements | Strong, blocks conflicting writers entirely | None, last write silently wins |
| Coverage | Total for writes through the chokepoint, zero outside it | Total only if every developer, every time, remembers | Total for writes through the chokepoint, zero outside it | Not applicable |
| Debuggability of a conflict | Lower, exception originates in framework code far from the mutating call site | Higher, the check and the failure are visible in the same function | Lower, plus the failure mode can be a hang rather than an exception if lock timeouts are not configured | Not applicable, nothing to debug until data corruption is discovered later |
| Cost to add | Low if a chokepoint (ORM, layer supertype) already exists, high if one must be built from scratch | Low per call site, but cost multiplies by number of call sites and by the discipline required to keep it correct over years | Same as optimistic column, low with an existing chokepoint | None |
| Ability to opt out per call site | Low, requires actively fighting the framework | High, simply do not add the check at that call site | Low, same as optimistic | Not applicable |
| Operational risk under contention | Retry storms possible if many transactions repeatedly collide on the same hot row | Same risk, but distributed unevenly if some call sites retry and others do not | Lock waits and timeouts or deadlocks if held too long | No contention symptoms, only silent data loss |

## 13. Related and incompatible patterns

**Optimistic Offline Lock and Pessimistic Offline Lock.** Implicit Lock is
not an alternative to either, it is a placement decision layered on top of
one of them. Every real instance of Implicit Lock documented in dimension 9
is, underneath, an implementation of one of these two patterns, Implicit
Lock answers "where does the check live," not "what does the check do."

**Coarse-Grained Lock.** When an object graph rather than a single row needs
protection, Coarse-Grained Lock defines a single lock covering the whole
graph. Implicit Lock composes cleanly with it, the chokepoint can be taught
to acquire or check the coarse-grained lock's single version stamp equally
readily as a per-row version, so the developer still never writes locking
code, regardless of whether the lock scope is one row or a whole aggregate.

**Layer Supertype.** The most common literal implementation of the
chokepoint Implicit Lock needs. Fowler's own base-class framing of Implicit
Lock is a direct application of Layer Supertype, where the shared behavior
being centralized happens to be locking rather than, say, auditing or
soft-delete handling.

**Unit of Work.** Most real Implicit Lock implementations sit inside a Unit
of Work's commit or flush step (Hibernate's session flush, EF Core's
`SaveChanges`, ActiveRecord's `save`), because the commit step is naturally
the single chokepoint every change passes through before it reaches the
database. Implicit Lock can be described as the version check Unit of Work
performs on the developer's behalf during commit.

**Aspect-Oriented Programming, or Interceptor patterns.** The interceptor
variant from dimension 8 is a direct application of AOP's cross-cutting
concern idea, with locking as the cross-cutting concern being woven into
every write path.

No pattern in this family conflicts in structure with Implicit Lock in
the way, for example, Optimistic Offline Lock and Pessimistic Offline Lock
are mutually exclusive strategies for the same row. Implicit Lock is
compatible with anything it wraps because it contributes no independent
locking semantics of its own, the only genuine incompatibility is
architectural rather than pattern-level. A codebase with no shared
persistence chokepoint at all has nowhere for Implicit Lock to attach, which
is why dimension 4 lists "no chokepoint exists" as the leading
non-applicability case rather than a competing pattern.

## 14. Refactoring path in and out

**Introducing Implicit Lock into a codebase with explicit, scattered
checks.** Start by inventorying every call site that currently performs a
manual version comparison or manual lock acquisition, this inventory is
itself valuable because it usually reveals the gaps the refactor is meant to
close. Identify or introduce the chokepoint. If an ORM is already in use,
this is usually a configuration change (mark the version column, enable the
concurrency-token mapping) rather than new code. If no ORM exists, introduce
a layer supertype that every data-access class extends, and move the
version-check or lock-acquisition logic into that base class's save method,
one entity type at a time, deleting the corresponding manual check at each
call site as it migrates. Keep both the old manual checks and the new
implicit check active simultaneously during the transition for any entity
still being migrated, rather than removing the manual check before the
implicit one is verified working, so a bug in the new mechanism does not
silently regress to no protection at all.

**Removing Implicit Lock.** This is rare, because the pattern's entire value
lies in coverage without discipline, and removing it reintroduces the exact
gap problem it was built to close. It is justified primarily when the
chokepoint itself is being removed for unrelated reasons, an ORM migration
away from the framework that hosted the check, or when a specific entity's
concurrency requirements have become heterogeneous enough (dimension 4, the
"intentional per-call-site control" case) that centralizing the policy is
actively wrong for that entity. When removing it for one entity while
keeping it for others, make the removal as loud as the introduction was
quiet, an explicit comment, a code review note, or a naming convention on
the entity that signals "this one deliberately has no automatic
concurrency check," so a future maintainer does not assume the application
wide guarantee silently covers it.

## 15. Testing and verification

Fowler's own observation, that "offline concurrency management is difficult
to test, such errors might go undetected by all of your test suites"
([martinfowler.com/eaaCatalog/implicitLock.html](https://martinfowler.com/eaaCatalog/implicitLock.html),
verified 2026-08-02), applies directly to testing Implicit Lock itself, and
the test strategy has to be built deliberately rather than falling out of
ordinary unit testing.

A useful base-case test loads two independent instances of the same entity
(simulating two separate requests or transactions reading the same row),
mutates and saves the first, then mutates and saves the second, and asserts
that the second save raises the expected conflict exception. This test
proves the chokepoint's core behavior without needing real concurrency or
real threads, it only needs two separate in-memory representations of the
same row that both claim to be based on the same original version.

A second, distinct test class is needed to prove the negative case, that a
write path a team believes goes through the chokepoint actually does. This
is best verified with an integration test that performs the write exactly
the way production code performs it (through the same repository, service,
or API endpoint used in production, never by calling the entity's setters
and a raw save method directly in the test, which can accidentally bypass
the same code paths an untested production bypass would use) and asserts
that the version column changed, or that a lock was observably held, as a
side effect.

For genuinely concurrent behavior, particularly for the pessimistic variant
where a lock's blocking behavior matters, a test that opens two real
database transactions from two real connections and asserts that the second
blocks until the first commits (or fails immediately if `nowait` is
configured) exercises behavior that in-process, single-connection tests
cannot reach. This class of test is slower and flakier than unit tests and
is usually kept in a smaller, separately-run integration suite rather than
the fast unit-test loop.

## 16. Observability signals

A healthy Implicit Lock deployment shows a low, roughly steady rate of
conflict exceptions relative to write volume, concentrated on entities that
genuinely see concurrent edits (shared documents, inventory counts, shared
configuration), and near-zero on entities that are effectively single-writer
in practice.

Log every conflict exception with enough context to distinguish "expected
contention, handled by retry" from "a bug is causing spurious conflicts",
the entity type and identifier, the version the writer expected versus the
version actually in the database at conflict time, and whether the writer's
retry succeeded. A rising rate of conflicts on an entity that previously had
none is the leading indicator either of a genuine increase in concurrent
usage (a scaling signal) or of a newly introduced write path that is
touching the version column more aggressively than intended (a regression
signal, see dimension 11's third failure mode).

For the pessimistic variant, track lock wait time and lock hold duration
separately. A rising wait time with a stable hold duration indicates
increasing contention (more writers wanting the same rows), while a rising
hold duration with stable wait time indicates transactions are doing more
work than they should while holding the lock, which is dimension 11's
fourth failure mode and the one most likely to spread into an
application-wide slowdown rather than staying contained to one entity.

A dashboard for this pattern is well served by a single panel showing
conflict, or lock-timeout, rate per entity type, per minute, with the raw
write volume for the same entity type overlaid, so a reviewer can
immediately see whether a spike in conflicts tracks a spike in writes
(expected) or is disproportionate to write volume (a signal worth
investigating).

## 17. Security and privacy implications

Implicit Lock's security surface is narrow and mostly indirect. It does not
itself handle authentication, authorization, or data classification, but two
implications are worth naming.

First, conflict-resolution flows that surface "database values" versus
"current values" to a user, the pattern EF Core's own documentation
recommends for resolving `DbUpdateConcurrencyException`
([learn.microsoft.com/en-us/ef/core/saving/concurrency](https://learn.microsoft.com/en-us/ef/core/saving/concurrency),
verified 2026-08-02), can leak data the requesting user is not authorized to
see if the merge UI naively displays every field of the conflicting row
rather than only the fields the current user is permitted to view.
Authorization checks that apply to normal reads of an entity must also apply
to the "what did the other writer change it to" view a conflict-resolution
flow presents, or the conflict path becomes an unintended read-access
bypass.

Second, because the implicit chokepoint is a single, shared piece of
infrastructure, a vulnerability or misconfiguration in it (a version column
that is nullable and silently treated as "no conflict possible" when null,
or an interceptor that is accidentally disabled for a specific entity
during a refactor) has a blast radius equal to every entity relying on that
chokepoint, rather than the blast radius of a single hand-written check.
This is the security-relevant mirror of dimension 10's consequence about
centralized risk. A bug in the shared mechanism is systemic, not localized,
which argues for treating the chokepoint's own configuration as a reviewed,
tested artifact in its own right rather than an assumed-correct piece of
framework plumbing.

Implicit Lock has no privacy implications of its own, it does not introduce
new data storage, new logging of personal data beyond what dimension 16
already recommends (entity identifiers and version numbers, not the
entity's business data), and does not change an application's data
retention posture.

## 18. References

1. Martin Fowler, *Patterns of Enterprise Application Architecture*,
   Addison-Wesley, 2002, chapter 16, "Concurrency". Catalog summary page,
   https://martinfowler.com/eaaCatalog/ (verified 2026-08-02).
2. Implicit Lock pattern page,
   https://martinfowler.com/eaaCatalog/implicitLock.html (verified
   2026-08-02).
3. Optimistic Offline Lock pattern page, part of the same chapter,
   https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html (verified
   2026-08-02), and the corresponding entry in this repository,
   `patterns/06-enterprise-application-architecture/optimistic-offline-lock.md`.
4. Hibernate ORM 6.4 User Guide, section 11, "Locking", covering `@Version`
   and optimistic locking,
   https://docs.hibernate.org/orm/6.4/userguide/html_single/Hibernate_User_Guide.html
   (verified 2026-08-02).
5. Ruby on Rails API documentation, `ActiveRecord::Locking::Optimistic`,
   https://api.rubyonrails.org/classes/ActiveRecord/Locking/Optimistic.html
   (verified 2026-08-02).
6. Django documentation, `QuerySet.select_for_update()`,
   https://docs.djangoproject.com/en/5.0/ref/models/querysets/#select-for-update
   (verified 2026-08-02).
7. Microsoft Learn, "Handling Concurrency Conflicts, EF Core",
   https://learn.microsoft.com/en-us/ef/core/saving/concurrency (verified
   2026-08-02).

## Code examples

Three languages where the pattern's shape is genuinely different in each. Python
and TypeScript show the same minimal chokepoint (a `save` method that is the
only write path, attaching and checking the version predicate). Rust shows the
same chokepoint expressed through `Result`, where the compiler forces every
caller to handle the conflict signal rather than letting an exception silently
propagate, which is the closest a statically typed, exception-free language
gets to Fowler's "cannot be overlooked" property. Java is omitted because no
Java runtime was available on the machine that authored this entry, and a
sample that was not actually run is not shipped as one that was. Go is omitted
because the pattern's idiomatic Go form (a `Save` method returning an
`ErrConflict` sentinel from a repository struct) is a straightforward
restatement of the Rust `Result` shape with no distinct lesson to add.

Every sample below was compiled or run on the authoring machine, not assumed
to work.

### Python

```python
class StaleObjectError(Exception):
    pass


class Chokepoint:
    """Layer-supertype style store. save() is the only write path and
    it silently attaches and checks the version predicate."""

    def __init__(self):
        self._rows = {}

    def load(self, entity_id):
        row = self._rows.get(entity_id)
        return dict(row) if row else None

    def save(self, entity_id, data, expected_version):
        current = self._rows.get(entity_id)
        current_version = current["version"] if current else 0
        if current_version != expected_version:
            raise StaleObjectError(
                f"expected version {expected_version}, found {current_version}"
            )
        new_row = dict(data)
        new_row["version"] = expected_version + 1
        self._rows[entity_id] = new_row
        return new_row["version"]


db = Chokepoint()
db.save("person-1", {"name": "John"}, expected_version=0)

a = db.load("person-1")
b = db.load("person-1")

db.save("person-1", {"name": "Paul"}, a["version"])  # succeeds, version 2

try:
    db.save("person-1", {"name": "Jane"}, b["version"])  # b is now stale
except StaleObjectError as exc:
    print("conflict detected", exc)
```

Run with `python3 implicit_lock.py`. Output confirmed on the authoring machine,
a printed conflict message naming the expected and found version numbers,
followed by the final row showing Paul's name and version 2, exactly the
outcome traced in dimension 7's dynamics diagram.

### TypeScript

```typescript
class StaleObjectError extends Error {}

interface Row {
  name: string;
  version: number;
}

class Chokepoint {
  private rows = new Map<string, Row>();

  load(id: string): Row | undefined {
    const row = this.rows.get(id);
    return row ? { ...row } : undefined;
  }

  save(id: string, data: Omit<Row, "version">, expectedVersion: number): number {
    const current = this.rows.get(id);
    const currentVersion = current ? current.version : 0;
    if (currentVersion !== expectedVersion) {
      throw new StaleObjectError(
        `expected version ${expectedVersion}, found ${currentVersion}`
      );
    }
    const newVersion = expectedVersion + 1;
    this.rows.set(id, { ...data, version: newVersion });
    return newVersion;
  }
}

const db = new Chokepoint();
db.save("person-1", { name: "John" }, 0);

const a = db.load("person-1")!;
const b = db.load("person-1")!;

db.save("person-1", { name: "Paul" }, a.version); // succeeds, version 2

try {
  db.save("person-1", { name: "Jane" }, b.version); // b is now stale
} catch (err) {
  if (err instanceof StaleObjectError) {
    console.log("conflict detected", err.message);
  }
}
```

Compiled with `npx tsc --strict --target es2020 --module commonjs` and run
with `node`, zero compiler errors, output matching the Python sample.

### Rust

```rust
use std::collections::HashMap;
use std::fmt;

#[derive(Debug)]
struct StaleObjectError(String);

impl fmt::Display for StaleObjectError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

#[derive(Clone, Debug)]
struct Row {
    name: String,
    version: u32,
}

struct Chokepoint {
    rows: HashMap<String, Row>,
}

impl Chokepoint {
    fn new() -> Self {
        Chokepoint { rows: HashMap::new() }
    }

    fn load(&self, id: &str) -> Option<Row> {
        self.rows.get(id).cloned()
    }

    fn save(&mut self, id: &str, name: &str, expected_version: u32) -> Result<u32, StaleObjectError> {
        let current_version = self.rows.get(id).map(|r| r.version).unwrap_or(0);
        if current_version != expected_version {
            return Err(StaleObjectError(format!(
                "expected version {}, found {}",
                expected_version, current_version
            )));
        }
        let new_version = expected_version + 1;
        self.rows.insert(
            id.to_string(),
            Row { name: name.to_string(), version: new_version },
        );
        Ok(new_version)
    }
}

fn main() {
    let mut db = Chokepoint::new();
    db.save("person-1", "John", 0).unwrap();

    let a = db.load("person-1").unwrap();
    let b = db.load("person-1").unwrap();

    db.save("person-1", "Paul", a.version).unwrap(); // succeeds, version 2

    match db.save("person-1", "Jane", b.version) {
        Ok(_) => panic!("expected StaleObjectError, none raised"),
        Err(e) => println!("conflict detected {}", e), // b is now stale
    }
}
```

Compiled with `rustc implicit_lock.rs` and run directly. The `save` method's
`Result<u32, StaleObjectError>` return type means the caller cannot reach the
new version number without a `match`, `?`, or an explicit `.unwrap()` that
documents the decision to ignore the conflict, unlike the Python and
TypeScript samples where an uncaught exception is a silent possibility until
runtime. One `dead_code` warning was emitted for the unread `name` field on
`Row`, harmless in this trimmed sample and noted rather than hidden.
