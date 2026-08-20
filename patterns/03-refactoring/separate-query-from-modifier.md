---
name: Separate Query from Modifier
slug: separate-query-from-modifier
family: 03-refactoring
category: Refactoring
aliases: [Command Query Separation, CQS, Separate Command from Query, Split Query and Modifier]
first_described: "Fowler 1999"
maturity: canonical
related: [replace-temp-with-query, extract-function, change-function-declaration, remove-setting-method, replace-derived-variable-with-query, cqrs]
incompatible_with: [toggle-function, hidden-side-effect-query]
verified: 2026-08-02
---

# Separate Query from Modifier

## 1. Name, aliases, and lineage

The canonical refactoring name is **Separate Query from Modifier**. Martin
Fowler keeps that name in the public second-edition catalog page for
*Refactoring. Improving the Design of Existing Code*, where the example splits
a function that calculates money owed and sends a bill into a calculation
function and a sending function
(https://refactoring.com/catalog/separateQueryFromModifier.html, verified
2026-08-02). Fowler's public note on second-edition changes also lists
Separate Query from Modifier as a kept refactoring from the first edition
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02). The book citation is Martin Fowler, *Refactoring. Improving the
Design of Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 11,
"Refactoring APIs." The first-edition lineage is Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, Addison-Wesley, 1999, chapter 10,
"Making Method Calls Simpler."

The design rule behind the refactoring is normally called **Command Query
Separation**, or **CQS**. Fowler's bliki note credits Bertrand Meyer with
coining the term in *Object-Oriented Software Construction* and states the
division between methods that answer and methods that change observable state
(https://martinfowler.com/bliki/CommandQuerySeparation.html, verified
2026-08-02). The book citation for the principle is Bertrand Meyer,
*Object-Oriented Software Construction*, 2nd edition, Prentice Hall, 1997,
chapter 23, "The principles of class design." No page number is cited here
because the page was not live-verified in this session.

The names vary because communities draw the boundary at different scales.
Object-oriented design uses **command** and **query** for methods. Refactoring
catalogs often use **modifier** rather than command, because "command" is also
the name of the Gang of Four Command pattern. API design often speaks of safe
methods, read operations, write operations, mutations, or actions. GraphQL names
the two root operation types query and mutation; its specification says
top-level mutation fields are expected to perform side effects and are executed
serially, while non-mutation fields are expected to be side-effect-free and
idempotent (https://spec.graphql.org/September2025/, verified 2026-08-02).

This entry uses **query** for a callable unit whose purpose is to return
information without changing observable state. It uses **modifier** for a
callable unit whose purpose is to change observable state. Observable state is
the key phrase. A query that fills a private memoization cache may alter memory,
but that cache is not part of the contract if callers cannot observe it except
through lower latency. A method that writes an audit row, advances an iterator,
sends an email, mutates a passed-in object, spends a rate limit token, or changes
authorization state is a modifier, no matter how harmless its name sounds.

## 2. Problem and context

A method is used like a question but behaves like an action. The caller writes
`if (cart.totalDue() > 0)` and expects a number. Hidden inside `totalDue`, the
method records an invoice, applies a discount, advances a cursor, marks a
notification as read, updates a cache that other clients can see, or sends a
message. The return value makes the method attractive in expressions, logs,
assertions, retry checks, template rendering, validation, and debugger watches.
The side effect makes every extra call risky.

The problem appears most often after useful work accretes around an existing
getter. A team starts with `nextInvoiceNumber()`, then adds "reserve the number
so nobody else gets it." A service starts with `findEligibleUsers()`, then adds
"mark them as selected." A UI starts with `unreadCount()`, then adds "clear the
badge once the user sees it." The name remains query-shaped, and callers keep
treating it as query-shaped, but the behavior has crossed a boundary.

The refactoring context is a codebase where behavior must be preserved while
the contract becomes honest. The first move is not to delete the side effect.
The first move is to give the side effect a separate operation and make call
sites say when they want it. After the split, a query can be repeated, logged,
cached, reordered, used in a condition, or called by a monitoring probe without
performing the action. The modifier can be named as an action, guarded by
authorization, retried with care, traced as a write, and documented as
non-idempotent or idempotent.

The shape is smaller than CQRS. CQRS separates read and write models, often at
an architectural boundary. Fowler's CQRS note says CQRS splits the conceptual
model for updates and display, and warns that the added complexity fits a
minority of systems (https://martinfowler.com/bliki/CQRS.html, verified
2026-08-02). Separate Query from Modifier is a method-level refactoring. It can
be applied inside a class, module, endpoint handler, command-line tool, or API
client without introducing separate databases, read models, message buses, or
event sourcing.

The refactoring also changes how teams talk about defects. Before the split,
the bug report tends to sound odd: "checking the balance sent a notice," or
"rendering the page claimed the job." After the split, the report has a cleaner
shape: the read path called a modifier, or the modifier was missing a guard.
That vocabulary matters in larger codebases because hidden writes cross team
boundaries. A reporting team may own the page that calls a query, while a
billing team owns the side effect hidden under that query. The split makes the
ownership boundary visible in code review.

## 3. Forces

Engineering judgement. This section weighs design pressures. The citations in
the entry establish the named sources and production examples, while the force
ranking below is judgement from practice.

- **Coupling.** The pattern reduces temporal coupling between asking and
  acting. A caller can ask without knowing how to undo an action. It may raise
  call-site coupling where callers now need to call two functions in the right
  order.
- **Consistency.** A combined method can compute and change under one lock or
  transaction. Splitting it can expose an interleaving gap unless the modifier
  rechecks its preconditions. The pattern favors readable contracts over
  implicit atomicity.
- **Latency.** Splitting may add an extra call or an extra round trip when the
  query and modifier used to share loaded data. It can reduce latency for paths
  that only need the answer, because they no longer pay for writes, locks,
  emails, or audit work.
- **Operability.** The split makes telemetry cleaner. Reads and writes can have
  different log levels, alerts, dashboards, and retry policy. The cost is that a
  business action that needs both operations now has two spans or two log lines.
- **Cost.** The immediate cost is call-site migration and test updates. The
  longer-term saving is lower incident cost when a diagnostic read cannot
  trigger production behavior.
- **Team topology.** The pattern helps when platform teams expose read APIs used
  by many product teams. A query contract that hides writes turns every consumer
  into an accidental operator of another team's state.
- **Cognitive load.** The split improves local reasoning. Function names and
  return types tell a more truthful story. The trade is a larger surface area,
  since one operation becomes two.
- **Concurrency.** Queries that do not change observable state are easier to
  run in parallel. Modifiers need serialization, locking, idempotency keys, or
  conflict handling. GraphQL reflects this split by permitting normal execution
  order for non-mutation fields while serializing mutation root fields
  (https://spec.graphql.org/September2025/, verified 2026-08-02).

The pattern favors explicit contracts, repeatable reads, and operational
control. It sacrifices compact call sites and sometimes sacrifices atomic
read-and-write behavior. If the atomic behavior was intentional, keep it behind
an action-shaped method and add a separate query only for code that needs a
read.

A practical rule of thumb is to ask what would happen if a profiler, logger,
template engine, or test assertion called the method twice. If the second call
would change user-visible behavior, spend money, consume capacity, alter a
cursor, or change authorization state, the method is not a query. If the second
call only repeats CPU work or touches private memoized data, the design pressure
is weaker. The refactoring earns its cost when the second call is dangerous.

## 4. Applicability and non-applicability

Reach for Separate Query from Modifier when these conditions hold.

- A function returns a value and changes observable state.
- A method name starts with `get`, `find`, `is`, `has`, `count`, `total`,
  `current`, or `next`, but a call also writes, sends, reserves, consumes, or
  advances.
- A method appears in conditions, logging, template rendering, assertions, or
  monitoring probes, and a second call would change behavior.
- Tests need awkward setup because reading a value also causes cleanup,
  persistence, billing, notification, cursor movement, or time changes.
- A debugger watch expression, metrics scraper, cache warmer, link checker, or
  retry loop could invoke the method more than once.
- An API has a read operation that performs the same work as a write operation
  because returning the result after the write felt convenient.
- A public method has a name that needs "and" to be truthful, such as
  `getTotalAndSendBill`.

Do NOT reach for it in these cases.

- **The action is the concept.** `pop`, `readLine`, `receive`, and
  `nextIteratorItem` often combine returning data with consuming a position.
  Splitting into `peek` and `advance` may be right, but only when clients
  benefit from peeking. Otherwise the split can make a single domain action
  harder to use.
- **The modifier must be atomic with the value it returns.** A payment capture
  that returns a receipt ID, a database insert that returns the created row, or
  a compare-and-swap that returns success is an action whose result belongs to
  the action. Keep the method action-shaped. Add a separate query only for
  callers that need a read without the action.
- **The side effect is private memoization.** If the only mutation is a private
  cache invisible to other objects, users, files, clocks, metrics, and external
  systems, splitting normally adds noise. Document the cache only if it affects
  memory or latency expectations.
- **The system has no safe way to query first.** Some external systems expose
  only destructive reads, such as consuming a message from a queue. A wrapper
  can name the operation honestly, but it cannot turn the external behavior
  into a true query.
- **The caller needs a transaction script.** If every correct use must query,
  validate, modify, and return a new view under one transaction, expose one
  command method and put the query logic inside it. A separate public query may
  invite stale decisions.
- **The split leaks authorization policy.** If the query reveals data the caller
  may only see after a write has been authorized, splitting can widen the read
  surface. Add explicit read authorization before exposing the query.
- **The problem is a whole read/write architecture.** If the read side needs a
  different database, projection, or scaling path, the refactoring is too small.
  Consider CQRS with care, and cite Fowler's warning that most systems pay more
  complexity than they gain (https://martinfowler.com/bliki/CQRS.html, verified
  2026-08-02).

## 5. Structure

The refactoring has six participants.

- **Mixed Operation.** The existing function that both returns a value and
  changes observable state. It often has a query-shaped name, which is why
  callers misuse it.
- **Extracted Query.** A new function that returns the same information the old
  function returned, but performs no observable write. It owns the calculation,
  lookup, formatting, filtering, or validation answer.
- **Extracted Modifier.** A renamed or rewritten function that performs the
  state change. It returns no domain answer, or returns only an action result
  that cannot be obtained without performing the action.
- **Client.** Any caller of the mixed operation. During migration, clients split
  into read-only clients, action clients, and clients that need both.
- **Observable State.** The state that other code, users, storage, time,
  metrics, locks, queues, or remote systems can detect. This boundary decides
  whether an operation is a query.
- **Ordering Guard.** A transaction, lock, precondition check, idempotency key,
  or version check used when the old mixed operation relied on atomicity.

The important relationship is ownership of the return value. The extracted
query owns the old return value. The extracted modifier owns the old side
effect. Clients that only need the answer call the query. Clients that need the
action call the modifier, and if they also need an answer they call the query at
an explicit point chosen by the business rule.

The modifier should not secretly call the query and return its value to preserve
the old shape. That creates a second mixed operation. It is acceptable for the
modifier to use private query-like helper code internally when the result is
needed to perform the write, but the public contract should read as an action.

The extracted query should be written as if it may run under wider automation
than the original method ever did. Search crawlers, cache warmers, dashboard
refreshes, health checks, speculative UI rendering, and test fixtures all call
read methods in places where an action would be wrong. The extracted modifier
should be written as if retries and partial failure are normal. Once the action
has its own name, it becomes reasonable to add idempotency keys, optimistic
versions, and permission checks that would have looked excessive on a method
named like a getter.

## 6. ASCII structure diagram

```text
Before

  +------------------+       getInvoiceTotalAndSend()
  |      Client      | -------------------------------+
  +------------------+                                |
                                                      v
                                      +-----------------------------+
                                      |        BillingService       |
                                      |-----------------------------|
                                      | + getInvoiceTotalAndSend()  |
                                      |   returns Money             |
                                      |   sends email               |
                                      |   writes sent_at            |
                                      +-----------------------------+
                                                  |
                                                  v
                                      +-----------------------------+
                                      | Observable state changes    |
                                      | email, database, audit log  |
                                      +-----------------------------+

After

  +------------------+       totalOutstanding()
  |  Read-only path  | -------------------------------+
  +------------------+                                |
                                                      v
                                      +-----------------------------+
                                      |        BillingService       |
                                      |-----------------------------|
                                      | + totalOutstanding(): Money |
                                      | + sendBill(): void          |
                                      +-----------------------------+
                                                      ^
  +------------------+       sendBill()               |
  |   Action path    | -------------------------------+
  +------------------+

  Query returns an answer. Modifier changes observable state.
```

## 7. Dynamics

The runtime change is a change in caller intent. A read-only caller no longer
travels through the write path. An action caller states the action directly.
When both are needed, ordering is visible at the call site or inside a named
transaction script.

```text
Read-only flow

Client              BillingService            InvoiceStore
  |                       |                         |
  | totalOutstanding()    |                         |
  |---------------------->|                         |
  |                       | read invoices           |
  |                       |------------------------>|
  |                       |<------------------------|
  |<----------------------| Money                   |
  |                       |                         |
  | No email. No sent_at write. No audit action.    |

Action flow

Client              BillingService            Mailer        InvoiceStore
  |                       |                         |              |
  | sendBill()            |                         |              |
  |---------------------->|                         |              |
  |                       | render bill             |              |
  |                       | send email              |              |
  |                       |------------------------>|              |
  |                       |<------------------------|              |
  |                       | mark sent               |              |
  |                       |--------------------------------------->|
  |<----------------------| void or action receipt                  |
```

Ordering decisions now have names. If the business rule says "send the bill
only if the total is positive," the caller can write `if total > 0` and then
call `sendBill`. If the rule must be atomic, the service should expose
`sendBillIfOutstanding` as a modifier that checks and writes under one lock.
That action may return a receipt or status because the return value is a result
of the action, not a free-standing query.

## 8. Implementation variants

**Pure split.** The old method becomes two public functions. The query returns
the old value. The modifier returns nothing. This is the clearest form and the
best default for in-process domain code.

**Action with receipt.** The modifier returns an action result such as a receipt
ID, affected row count, version token, or boolean success flag. This does not
violate the pattern when the value cannot be known without performing the
action. The query remains available for reading before or after the action.

**Peek and consume.** For streams, queues, stacks, and iterators, one operation
may expose `peek` or `current`, and a separate operation exposes `advance`,
`ack`, `consume`, or `pop`. Use this when clients need to inspect without
consuming. Do not add it when every valid caller consumes immediately.

**Query object plus command object.** A service layer can split a mixed handler
into a query handler and command handler. Keep this modest. The method-level
refactoring does not require CQRS infrastructure.

**HTTP surface split.** A resource API can route reads through safe HTTP methods
and writes through unsafe methods. RFC 9110 defines GET, HEAD, OPTIONS, and
TRACE as safe, and says the distinction supports automated retrieval and cache
optimization without fear of harm (https://www.rfc-editor.org/rfc/rfc9110.html,
verified 2026-08-02). A URI such as `GET /orders/123?sendReceipt=true` violates
that spirit because a query parameter selects an action under a safe method.

**GraphQL operation split.** A schema can place reads under the root query type
and writes under the root mutation type. GitHub's GraphQL documentation says
the GitHub GraphQL API helps clients define the data they want to fetch and
points users to queries and mutations as separate call forms
(https://docs.github.com/en/graphql, verified 2026-08-02). The GraphQL
specification gives the execution reason for that split: mutation root fields
are expected to perform side effects and run serially, while other field
resolution is expected to be side-effect-free and idempotent
(https://spec.graphql.org/September2025/, verified 2026-08-02).

**Language effect markers.** Some languages or frameworks give partial help.
TypeScript can use `readonly` types but cannot prove an object graph is
unchanged. Python communicates mostly through naming and tests. Go encourages
explicit return values and simple methods but has no purity marker. Rust's
borrow checker distinguishes shared and mutable borrows, which can make many
mutations syntactically visible, although interior mutability still exists. The
refactoring remains a design move, not something most mainstream compilers can
fully prove.

**Compatibility wrapper.** Public APIs sometimes need to keep the old mixed
operation for one release train. In that case, mark it deprecated, make its
documentation state the side effect in the first sentence, and implement it by
calling the new modifier plus the new query in the old order. This wrapper is
not the desired design. It is a migration bridge. It should have telemetry so
the team can see which clients still depend on it.

**Batch split.** A mixed batch operation often returns the selected records and
marks them claimed. Split it into a query that previews candidate IDs and a
modifier that claims a supplied set under a version check. This variant makes
review screens and dry runs safe. It also reveals a concurrency choice: the
modifier must reject stale IDs, skip already-claimed IDs, or claim the still
valid subset. That policy belongs in the action name or documentation.

## 9. Known production uses

**GitHub GraphQL API.** GitHub exposes its GraphQL API with query and mutation
call forms. The GitHub docs describe the API as a way to retrieve data and
automate workflows, and the docs explicitly teach clients to create and run
queries and mutations (https://docs.github.com/en/graphql, verified
2026-08-02). The production pattern use is the public API contract. Reads are
expressed as queries; changes are expressed as mutations.

**Amazon S3 object API.** Amazon S3 names `GetObject` as the operation that
retrieves an object and `PutObject` as the operation that adds an object to a
bucket (https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObject.html,
verified 2026-08-02;
https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html, verified
2026-08-02). The two operations are a production-scale example of separating
the read from the write even though a write response can return metadata such
as an ETag. The query does not create the object, and the modifier is named as
an object write.

**Kubernetes API server.** Kubernetes documents its API as a resource-based
HTTP interface that retrieves, creates, updates, and deletes resources through
standard HTTP verbs, and it gives `GET` URI forms for returning resource
collections and individual resources
(https://kubernetes.io/docs/reference/using-api/api-concepts/, verified
2026-08-02). The production use is not a single class method; it is the API
surface that keeps read verbs distinct from write verbs, while update paths use
the verbs Kubernetes documents for creation, replacement, patching, and
deletion on resources.

**HTTP itself.** RFC 9110 is not one vendor system, but it is the production
protocol contract behind a vast amount of deployed software. It defines safe
methods and explains that automated retrieval and caching rely on the safety
distinction (https://www.rfc-editor.org/rfc/rfc9110.html, verified
2026-08-02). This is the protocol-level ancestor of the same pressure: a read
operation must not surprise clients by performing an unsafe action.

## 10. Consequences

Engineering judgement. The lists below describe recurring outcomes rather than
properties guaranteed by a cited specification.

Positive.

- Read-only callers gain a function they can call repeatedly without triggering
  writes, notifications, cursor movement, or external actions.
- Function names become more honest. The query can be named as a fact or
  question. The modifier can be named as a verb.
- Tests become smaller for read behavior. A query test can check return values
  without asserting hidden writes.
- Monitoring, logging, rendering, and debugging can call queries without
  causing production work.
- Telemetry becomes clearer because reads and writes can use different metrics,
  traces, and alerts.
- Authorization can be separated. Read permission and write permission no
  longer have to be bundled because one method does both.
- Retry policy becomes less dangerous. Queries can often be retried freely;
  modifiers need idempotency and conflict rules.
- Review quality improves because reviewers can challenge a query that writes
  or a modifier that returns a free-standing domain answer.
- Documentation can be shorter and more precise. A query describes the answer.
  A modifier describes the state transition and its failure cases.

Negative.

- Call sites that need both behaviors become longer.
- The split can introduce a race when a caller queries and then modifies based
  on stale information.
- A transaction that used to be hidden inside one method may need a new
  action-shaped wrapper.
- API compatibility can be painful. Existing callers may depend on the old
  return value, the old side effect, or both.
- Two names must be maintained. Poor names such as `doThing` and `getThing`
  still hide intent.
- The modifier may duplicate lookup work that the old combined method shared
  with the query.
- Teams can overapply the rule and reject useful idioms such as stack `pop` or
  queue `receive`, where consuming and returning are one domain action.
- The split may expose missing domain language. If no one can name the modifier
  without using "process" or "handle," the original method may have been hiding
  several actions rather than one.
- Backward compatibility wrappers can keep the smell alive. Without a removal
  date and caller telemetry, the mixed method may survive as the most used API.

## 11. Failure modes and misuse

Engineering judgement. Each item names an observable symptom, a likely cause,
and a fix.

**Log line changes data.** Symptom. Adding a log, metric label, template
binding, or debugger watch causes emails to send twice, records to move state,
or counters to advance. Cause. A method used as a query hides a modifier. Fix.
Extract a side-effect-free query and move the action into a verb-named modifier.

**Condition performs the action twice.** Symptom. Code such as
`if service.nextItem() != null` followed by `service.nextItem()` skips every
other item. Cause. A query-looking method consumes a cursor. Fix. Add `current`
or `peek` for the query and `advance` or `consume` for the modifier, or rename
the method to make consumption explicit.

**Race after a split.** Symptom. A caller checks availability, then the action
fails or affects a different version because another actor changed the record.
Cause. The old mixed method provided accidental atomicity. Fix. Keep an
action-shaped method that checks and modifies inside one transaction, and keep
the separate query for display or preflight only.

**Modifier returns a disguised query.** Symptom. New code calls `sendBill()` in
an expression because it returns the same total as the old mixed method. Cause.
The migration preserved the old return value to reduce edits. Fix. Make the
modifier return void, a receipt, or an action status. Route total reads through
the query.

**Query writes to shared cache.** Symptom. A supposedly read-only endpoint
changes results seen by other tenants or changes authorization decisions.
Cause. The cache is not private implementation state; it is observable shared
state. Fix. Treat cache population as a modifier, or isolate the cache so its
only observable effect is latency.

**Authorization remains bundled.** Symptom. A user with read permission can
trigger a write through a query endpoint, or a user with write permission cannot
read the value needed for a confirmation screen. Cause. The old mixed operation
had one authorization check for two different capabilities. Fix. Add separate
read and write checks, then audit every caller that used the mixed method.

**CQS theater.** Symptom. The code has query classes and command classes, but
queries still publish events or commands still leak read models in return
values. Cause. The team adopted naming conventions without changing effects.
Fix. Define observable state for the module, test for no writes in queries, and
trace modifiers as writes.

**Network split without latency budget.** Symptom. An endpoint doubles its p95
latency after a client now makes a read call and a write call. Cause. The split
was applied across a remote boundary where an in-process split would have been
cheap. Fix. Keep a command endpoint for the business action and expose a
separate query endpoint for callers that only read.

## 12. Trade-off matrix

| Force | Separate Query from Modifier | Keep Mixed Operation | Rename to Action | Command pattern | CQRS | HTTP safe and unsafe methods |
|---|---|---|---|---|---|---|
| Coupling | Callers choose read or write | Callers are coupled to both | Coupling remains, name improves | Invoker decouples action from receiver | Read and write models split | Clients rely on protocol method |
| Consistency | Needs guard for query-then-write | Can keep one transaction | Can keep one transaction | Depends on command handler | Eventual consistency may appear | Server defines semantics per method |
| Latency | Cheaper reads, possible two-step actions | One call, often extra hidden work | Same as mixed operation | Extra object dispatch | Extra storage or messaging cost | Caches can speed safe reads |
| Operability | Separate read and write telemetry | Blurred metrics | Better logs, still mixed effects | Good for action tracing | Separate dashboards | Mature proxy and cache behavior |
| Cost | Call-site migration | No migration | Low edit cost | More types | High architecture cost | Requires API surface design |
| Team topology | Clear ownership of reads and writes | Shared confusion | Naming helps within one team | Good for workflow owners | Fits separate read and write teams | Fits public API teams |
| Cognitive load | Two names, clearer contracts | One name, hidden effects | One action name, no safe query | Handler indirection | High model count | Familiar to web clients |
| Concurrency | Queries can run freely | Reads may serialize behind writes | Same as mixed operation | Depends on queue or bus | Reads and writes scale apart | Safe methods can be automated |
| Best fit | Method-level refactoring | Atomic domain action | Honest destructive read | Deferred or undoable action | Different read and write models | Resource APIs |

Reading of the table. Separate Query from Modifier wins when callers truly need
a read that does not act. Rename to Action wins when the operation is
destructive by nature and no separate read is useful. Command wins when the
action needs queuing, undo, retries, scheduling, or an invoker. CQRS wins only
when separate models pay their cost. HTTP method design is the public API form
of the same idea.

## 13. Related and incompatible patterns

- **Command Query Separation.** This is the principle the refactoring repairs
  toward. CQS is the desired contract; Separate Query from Modifier is the
  mechanical path when a method violates it.
- **CQRS.** Related but larger. CQRS separates read and update models.
  Separate Query from Modifier separates methods or endpoints. Use the small
  refactoring before reaching for architectural split.
- **Extract Function.** The usual first move. Extract the calculation into a
  query, then leave the side effect behind as a modifier.
- **Change Function Declaration.** Often follows the split. The query may need
  a noun-like name and no hidden output parameters. The modifier may need an
  action name and a return type change.
- **Replace Temp with Query.** Composes well when the query calculation is
  currently stored in a temporary variable inside the mixed method.
- **Remove Setting Method.** Related when the modifier side is a setter that
  should not remain public after construction.
- **Command pattern.** Often confused because of the word command. The GoF
  Command pattern turns a request into an object for invocation control. This
  refactoring splits effects from answers.
- **Iterator.** Can conflict. Many iterator APIs combine returning the current
  value and advancing. Do not split them unless peek or current access has a
  real caller.
- **Lazy loading.** Can conflict when a getter fetches remote data and updates
  object state. If the loaded state is observable or alters persistence, treat
  it as a modifier. If it is private memoization, the split may be noise.
- **Event Sourcing.** Composes at the boundary. Commands append events, queries
  read projections. Do not import event sourcing only to satisfy a method-level
  CQS preference.

## 14. Refactoring path in and out

Introducing the split.

1. Find a method that both returns a value and changes observable state. Write
   down the return value and every effect: fields, database rows, messages,
   metrics, locks, cursors, files, remote calls, and passed-in objects.
2. Add characterization tests for the old behavior. Include a test that calls
   the old method twice if double-call behavior is part of the risk.
3. Extract the return calculation into a new query. Name it as a fact or
   question, for example `totalOutstanding`, `eligibleUsers`, `hasCredit`, or
   `currentVersion`.
4. Make the old method call the new query internally and keep the old effect.
   Run tests. This keeps behavior stable while clients migrate.
5. Migrate read-only callers to the query. This is the highest-value part of
   the refactoring because it removes accidental writes from read paths.
6. Rename the old method to an action name, or create a new modifier with an
   action name and route action callers to it.
7. Remove the query-shaped return value from the modifier. If callers need an
   action result, return a receipt, status, affected count, or version token.
8. For callers that need query then write, decide whether the sequence can be
   non-atomic. If not, create a named modifier that performs the check and write
   together under the right guard.
9. Delete the mixed operation when no callers remain. If public compatibility
   forbids deletion, deprecate it and make the documentation say it modifies
   state.

Refactoring out.

1. If every valid caller always asks and then acts under the same transaction,
   create an action-shaped method that owns the whole operation.
2. Inline the public query into the action only when no read-only callers remain.
3. Remove stale query tests that assert a no-longer-public behavior, but keep
   tests for the action result.
4. If the method is destructive by nature, prefer Rename Function over hiding
   the action behind a query name.
5. If the split grew into separate query and command handler layers with no
   operational benefit, collapse the layers with Inline Function or Inline
   Class and keep the query/modifier naming distinction.

## 15. Testing and verification

Engineering judgement. Tests should prove both parts of the new contract:
queries answer without effects, and modifiers perform effects without forcing
callers through a read.

For the query, write return-value tests using fixed input. Then add a
no-effect assertion at the boundary that matters. In a domain object, compare
the object state before and after. In a repository, use a transaction or fake
store and assert no writes were recorded. In an API handler, assert no command
bus messages, emails, audit records, or mutation queries were sent. A spy is
useful here because the absence of calls is the contract.

For the modifier, assert the effect directly. Check that a bill was sent, a row
was updated, an event was appended, a cursor advanced, or a queue message was
acknowledged. Avoid asserting the old query result through the modifier unless
the result is an action receipt. That test would preserve the smell.

For the migration, keep characterization tests around the old mixed operation
until all callers move. A high-signal test calls the query twice and asserts the
second call observes the same state as the first. Another calls the modifier
twice only when retry behavior matters, then documents whether the modifier is
idempotent.

Concurrency tests are needed when the old mixed operation held a lock or
transaction. Test stale read behavior, optimistic version failures, duplicate
submission, retry after timeout, and interleaving between query and modifier.
If the replacement is a single action method such as `reserveIfAvailable`, test
two contenders and assert that only one wins.

API tests should match protocol semantics. For HTTP, safe endpoints should not
write domain state. RFC 9110 allows incidental logging around safe requests,
but a safe method must not perform the requested unsafe action
(https://www.rfc-editor.org/rfc/rfc9110.html, verified 2026-08-02). For
GraphQL, test that fields placed under query do not mutate the data system, and
put write tests under mutations.

## 16. Observability signals

Engineering judgement. The split is successful in production when reads and
writes become visible as different kinds of work.

Log or trace every modifier with the action name, actor, target resource,
idempotency key where one exists, version or precondition, and outcome. Do not
log sensitive query results merely because a modifier used to return them.
Trace queries with lower cardinality labels: query name, resource type, cache
hit, data store, and latency bucket. Avoid labels that contain raw user data.

Metrics should separate query count from modifier count. A healthy instance has
far more query calls than write calls in many business systems, stable modifier
failure rates, and query latency that is not affected by write-side retries.
After the refactoring, read-only endpoints should show no domain write counter
increments. A dashboard that cannot answer "which reads wrote state" is not
testing the pattern in production.

Useful alerts include a write counter increasing from a query endpoint, a query
span containing a mailer or command bus child span, a modifier called without an
idempotency key where retries are common, and a rise in stale-version failures
after splitting query then write. The last signal does not always mean the
refactoring was wrong. It may reveal concurrency that the mixed method hid.

During migration, add a temporary counter for calls to the deprecated mixed
operation. Break it down by caller or endpoint if the runtime can provide that
without high cardinality. The counter tells the team when the compatibility
method can be removed.

For data stores, a simple canary is a no-write assertion around read routes in
non-production traffic. Count SQL statements by operation class, or tag command
bus dispatches and message sends. A read route that begins producing writes
after a refactor is easier to catch with this signal than by manually reviewing
every helper it calls. For in-process domain code, the same idea can be applied
with a fake repository that records read and write calls during tests.

## 17. Security and privacy implications

Engineering judgement. The pattern does not authenticate users or sanitize data
by itself. Its security value comes from making read and write intent visible.

A mixed query can bypass write authorization because it looks like a read. When
the operation is split, the query should pass only read authorization, and the
modifier should pass write authorization. This matters for APIs, admin tools,
report generation, and UI preview flows. A preview call that sends a message or
marks content as approved is a security bug disguised as convenience.

The split can also widen the read surface. A value formerly returned only after
a write may now have a public query. Review whether that value contains
personal data, secrets, fraud signals, moderation status, or commercial
information. If the data was safe only because the write path checked a stronger
permission, the new query needs its own permission check.

Queries are attractive for caching. Keep privacy boundaries in the cache key:
tenant, actor, authorization scope, locale, data classification, and version
where needed. A query that is safe from writes can still leak data if cached
under a broad key.

Modifiers need replay protection. After a split, clients may retry reads more
freely and may also retry writes after timeouts. Use idempotency keys, version
checks, or duplicate detection for modifiers that send money, email, shipment
requests, password reset messages, or external tickets.

Finally, safe HTTP semantics are not a substitute for server checks. RFC 9110
says resource owners are responsible for disabling unsafe actions when action
parameters appear under a safe method
(https://www.rfc-editor.org/rfc/rfc9110.html, verified 2026-08-02). Treat that
as a security rule for crawlers, prefetchers, chat unfurlers, and link scanners.

## Code examples

The examples use TypeScript, Python, and Go because the split is idiomatic in
all three and the local toolchain can run them. Java, Rust, and Swift are
omitted here to keep the entry focused; the pattern translates directly, but
three working samples are enough for the repository contract.

### TypeScript

```typescript
type Invoice = { amount: number; sent: boolean };

class BillingAccount {
  constructor(private readonly invoices: Invoice[]) {}

  totalOutstanding(): number {
    return this.invoices
      .filter((invoice) => !invoice.sent)
      .reduce((sum, invoice) => sum + invoice.amount, 0);
  }

  markOutstandingSent(): void {
    for (const invoice of this.invoices) {
      if (!invoice.sent) {
        invoice.sent = true;
      }
    }
  }
}

const account = new BillingAccount([
  { amount: 40, sent: false },
  { amount: 2, sent: false },
]);

console.log(account.totalOutstanding());
account.markOutstandingSent();
console.log(account.totalOutstanding());
```

### Python

```python
from dataclasses import dataclass


@dataclass
class Job:
    name: str
    claimed: bool = False


class Queue:
    def __init__(self, jobs: list[Job]) -> None:
        self._jobs = jobs

    def next_available_name(self) -> str | None:
        for job in self._jobs:
            if not job.claimed:
                return job.name
        return None

    def claim_next(self) -> None:
        for job in self._jobs:
            if not job.claimed:
                job.claimed = True
                return


queue = Queue([Job("render"), Job("email")])
print(queue.next_available_name())
print(queue.next_available_name())
queue.claim_next()
print(queue.next_available_name())
```

### Go

```go
package main

import "fmt"

type Cart struct {
	items []int
	paid  bool
}

func (c *Cart) Total() int {
	total := 0
	for _, amount := range c.items {
		total += amount
	}
	return total
}

func (c *Cart) MarkPaid() {
	c.paid = true
}

func main() {
	cart := &Cart{items: []int{12, 30}}
	fmt.Println(cart.Total())
	fmt.Println(cart.paid)
	cart.MarkPaid()
	fmt.Println(cart.paid)
}
```

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 11, "Refactoring APIs."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
  Addison-Wesley, 1999, chapter 10, "Making Method Calls Simpler."
- Martin Fowler, "Separate Query from Modifier," refactoring.com catalog,
  https://refactoring.com/catalog/separateQueryFromModifier.html, verified
  2026-08-02.
- Martin Fowler, "Changes for the 2nd Edition of Refactoring,"
  https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
  2026-08-02.
- Martin Fowler, "Command Query Separation,"
  https://martinfowler.com/bliki/CommandQuerySeparation.html, verified
  2026-08-02.
- Martin Fowler, "CQRS," https://martinfowler.com/bliki/CQRS.html, verified
  2026-08-02.
- Bertrand Meyer, *Object-Oriented Software Construction*, 2nd edition,
  Prentice Hall, 1997, chapter 23, "The principles of class design."
- R. Fielding, M. Nottingham, and J. Reschke, RFC 9110, "HTTP Semantics,"
  June 2022, sections 9.2.1 and 9.3,
  https://www.rfc-editor.org/rfc/rfc9110.html, verified 2026-08-02.
- GraphQL Foundation, *GraphQL Specification*, September 2025 edition,
  sections 6.2 and 6.3.4, https://spec.graphql.org/September2025/, verified
  2026-08-02.
- GitHub Docs, "GitHub GraphQL API documentation,"
  https://docs.github.com/en/graphql, verified 2026-08-02.
- Amazon Web Services, "GetObject. Amazon S3 API Reference,"
  https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObject.html, verified
  2026-08-02.
- Amazon Web Services, "PutObject. Amazon S3 API Reference,"
  https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html, verified
  2026-08-02.
- Kubernetes Documentation, "Kubernetes API Concepts,"
  https://kubernetes.io/docs/reference/using-api/api-concepts/, verified
  2026-08-02.
