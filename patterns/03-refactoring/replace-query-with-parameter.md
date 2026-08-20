---
name: Replace Query with Parameter
slug: replace-query-with-parameter
family: 03-refactoring
category: Refactoring
aliases: [Parameterize Query, Pass Derived Value]
first_described: "Fowler 2018"
maturity: canonical
related: [replace-parameter-with-query, change-function-declaration, separate-query-from-modifier, parameterize-function, move-function, introduce-parameter-object]
incompatible_with: []
verified: 2026-08-02
---

# Replace Query with Parameter

## 1. Name, aliases, and lineage

The canonical name is **Replace Query with Parameter**. Martin Fowler's public
catalog shows a function that reads `thermostat.currentTemperature` inside its
body, then changes the function so the caller passes that temperature as an
argument (https://refactoring.com/catalog/replaceQueryWithParameter.html,
verified 2026-08-02). The same catalog page names **Replace Parameter with
Query** as the inverse refactoring
(https://refactoring.com/catalog/replaceQueryWithParameter.html, verified
2026-08-02).

Fowler's second edition change note lists Replace Query with Parameter among
the fifteen refactorings that were new to the 2018 edition, rather than a rename
or generalization of a first edition entry
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02). Book citation. Martin Fowler, *Refactoring. Improving the Design of
Existing Code*, 2nd edition, Addison-Wesley, 2018, chapter 11, "Refactoring
APIs," section "Replace Query with Parameter." The public change note verifies
the edition and catalog presence; no page is cited here because the local
session did not verify the page number from a scanned book.

The name can sound backward on first reading. It does not mean "replace a query
method everywhere with a parameter object." It means this narrower move:
inside a function, replace an internal lookup with a value supplied through the
function boundary. The lookup may be a method call, a property read, a module
variable, a clock access, a request context lookup, or a database gateway call.
The new parameter makes that dependency explicit.

The refactoring belongs to the same API repair cluster as Change Function
Declaration, Parameterize Function, Preserve Whole Object, Replace Parameter
with Query, and Separate Query from Modifier. It is also a small local form of a
larger dependency move. Fowler's module dependency article shows the same
pressure at module scale by passing a data source to calculation code, then
discussing the trade that this grants substitution while it can spread the
parameter through many functions
(https://martinfowler.com/articles/refactoring-dependencies.html, verified
2026-08-02).

## 2. Problem and context

A function obtains information by reaching outward to something it can see:
global state, ambient process state, a receiver field, a singleton, a service
locator, a thread local, a request object, a clock, a random number generator,
or a mutable collaborator. That query is convenient because callers do not have
to pass another argument. It is harmful when the query is a dependency the
function should not own.

The smell is concrete. A price calculation calls `Currency.current()` although
the caller is already handling an invoice in a known currency. A retry policy
calls `time.Now()` although the caller is replaying an event with a recorded
timestamp. A formatter reads `RequestContext.locale()` although the caller is
formatting a batch file with a fixed locale. A permission predicate reaches into
a session object although the caller already has the authenticated principal.
The function signature says the computation depends on one or two visible
values. The body says it depends on the outside world as well.

This is a problem for movement. A function with hidden queries is hard to move
to another module because the target module must also gain the queried thing.
It is hard to test because the test must install or fake ambient state. It is
hard to run in batch jobs because the ambient state may not exist there. It is
hard to reason about in concurrent code because the query may return a different
answer later than it would have returned at the call site.

Replace Query with Parameter pulls that dependency into the signature. The
caller computes or obtains the value, then passes it. The callee stops reaching
out. After the change, the function declaration gives a more honest account of
what the function needs.

The refactoring is not a campaign against object queries. Queries are normal
code. The target is the misplaced query, the one that binds a function to an
authority, time source, execution context, or mutable object that the caller is
better placed to choose. This distinction keeps the refactoring from becoming
parameter sprawl. You are not making every value explicit. You are making the
right variation point explicit.

The pattern is common before a Move Function. If a function on `OrderService`
reads `this.taxTable` but the logic belongs in `TaxPolicy`, passing the table
or the tax rate can be the step that makes the move possible. It is also common
before extraction. If a block reads a surrounding variable, passing the value to
the extracted function tells future readers that the value is part of the
calculation, not part of the old home.

Another useful context is incident repair. Many production bugs are not caused
by a wrong formula, but by a correct formula reading the wrong environment. A
batch job runs under the server's time zone rather than the account's time zone.
A replay tool evaluates an event against current feature flags rather than the
flags that existed when the event was accepted. A background worker reads a
thread local request id left behind by reused infrastructure. In these cases
the query is attractive because it is nearby and easy to call. The failure
comes from the fact that nearby is not the same as authoritative. Replacing the
query with a parameter lets the boundary that knows the request, event,
account, or replay snapshot choose the value.

## 3. Forces

Engineering judgement. This dimension weighs design pressure rather than
reporting a universal fact about every codebase.

- **Coupling.** Favoured for the callee. The function no longer depends on the
  source of the value. Sacrificed at call sites, which now must know how to
  supply the value or receive it from their own caller.
- **Consistency.** Mixed. Passing a value can freeze a coherent snapshot. It
  can also permit an invalid pairing, such as an order from one tenant and a
  tax rate from another, unless the caller boundary is trusted.
- **Latency.** Favoured when the query is remote, lazy, repeated, or costly.
  The caller can obtain the value once. Sacrificed when every caller must run
  a query that some code paths never use.
- **Operability.** Favoured because trace and log boundaries can record the
  explicit parameter. Sacrificed when call sites pass many ordinary values and
  the operational signal becomes diluted.
- **Cost of change.** Favoured when the callee will move, when tests need a
  fake value, or when the source of the value varies by caller. Sacrificed when
  the derivation changes globally, because each caller may need an edit.
- **Team topology.** Favoured when a platform team owns a pure calculation and
  application teams own context lookup. Sacrificed when every product team must
  repeat configuration that one shared module used to hide.
- **Cognitive load.** Favoured inside the callee because all inputs are named
  at the boundary. Sacrificed at call sites because there is one more argument
  to read, order, name, and test.
- **Security and privacy.** Mixed. Passing an authorization result can prevent
  the callee from reading a whole session. Passing raw identity values can also
  let a buggy caller spoof authority.

The refactoring favours explicit inputs, portability, and substitutability. It
pays with broader signatures and a higher burden on callers. That price is fair
when the query was a hidden dependency. It is wasteful when the query was the
callee's own domain knowledge.

## 4. Applicability and non-applicability

Reach for Replace Query with Parameter when the following hold.

- A function reads global or ambient state, and the value is a true input to
  the function's result.
- A query binds a function to a module, receiver, singleton, request object, or
  service locator that blocks moving the function to a better home.
- Tests must patch process state, monkeypatch a module, install a singleton, or
  sleep until the real clock changes.
- The caller already has the value, or can obtain it from a better authority
  than the callee.
- The value must be frozen at call time for replay, audit, concurrency, or
  deterministic retry.
- A query is expensive and several internal calls repeat it.
- You want to split policy from mechanism. The caller chooses the policy value.
  The callee applies it.
- A public function currently hides access to sensitive context, and a narrower
  scalar or value object would reduce the data it touches.

Do NOT reach for it in these cases.

- **The query expresses the callee's core responsibility.** A function named
  `customerDiscount(customer)` should ask the customer or discount policy for
  the facts it needs. Passing every field separately scatters domain logic.
- **The caller cannot choose a valid value.** If only the callee knows which
  tenant, currency, snapshot, or version is legal, moving that decision outward
  creates invalid states.
- **The parameter would duplicate another parameter.** Passing both `order` and
  `order.currency` is often worse than the query. Use Replace Parameter with
  Query when the second value has no independent variation.
- **The value is an implementation detail.** A cache key, shard index, SQL hint,
  or internal flag may not belong in the public signature.
- **The query is cheap, pure, local, and stable.** A getter on an immutable
  value object is not a harmful dependency. Removing it usually buys little.
- **The signature is already overloaded.** A six argument function may need
  Introduce Parameter Object, Combine Functions into Class, or Extract Class
  before another parameter can be read without mistakes.
- **The value changes by design during the function.** Polling the current time,
  reading queue depth, or sampling a cancellation token may be the behavior.
  Passing a fixed value would change semantics.
- **The function is part of a published contract.** Removing an internal query
  by adding an argument breaks callers unless you run a versioned migration.
- **The query is a security check, not data lookup.** Do not replace
  `authorize(request)` with a caller supplied `isAuthorized` boolean unless
  the caller is inside the same trusted boundary.
- **The new parameter would become tramp data.** If ten layers must accept a
  value only to pass it onward, the better move may be dependency injection at
  construction time, a context object with strict rules, or moving the callee.
- **The caller would repeat fragile setup.** Fowler's dependency article warns
  that passing a data source with each call grants dynamic substitution but can
  duplicate creation knowledge in application modules
  (https://martinfowler.com/articles/refactoring-dependencies.html, verified
  2026-08-02).
- **You are hiding a command behind a parameter.** If the old query mutated
  state, ran I/O, or consumed a stream, first separate the command from the
  query. Then decide which result belongs in the signature.

The non-applicability rule is this. If the value is not a caller choice, not a
snapshot, not a dependency boundary, and not a cost boundary, do not add it as a
parameter.

## 5. Structure

The refactoring has five roles.

- **Caller.** The code that invokes the function. After the refactoring, it is
  responsible for providing the value or receiving it from its own caller.
- **Callee.** The function whose body contains the query. After the
  refactoring, it receives the value directly and no longer knows the queried
  source.
- **Queried source.** The object, module, global, singleton, context, clock, or
  collaborator currently accessed by the callee.
- **Extracted value.** The result of the query. It should have a domain name,
  not a mechanical name such as `value`.
- **Boundary invariant.** The behavior must stay the same for every valid
  caller after the query is moved outward.

Before the refactoring, the callee has a hidden edge to the queried source.
After the refactoring, that edge moves to the caller or to a higher layer that
already owned the source. The new parameter is the visible contract between the
two.

The structure is often temporary. In a small function, the new parameter may be
the final design. In a larger migration, it may expose tramp data. That is not
failure by itself. It can reveal the next refactoring: move the function closer
to the value, group values into an object, or inject a collaborator once rather
than passing it on every call.

## 6. ASCII structure diagram

```text
BEFORE

  +----------+        calls         +--------------------+
  | Caller   | -------------------> | Callee             |
  +----------+                      |--------------------|
                                    | result = query(S)  |
                                    | use(result)        |
                                    +---------+----------+
                                              |
                                              | hidden dependency
                                              v
                                    +--------------------+
                                    | Queried source S   |
                                    +--------------------+

AFTER

  +----------+    query(S)     +--------------------+
  | Caller   | --------------> | Queried source S   |
  +----+-----+                 +--------------------+
       |
       | calls with result
       v
  +---------------------------+
  | Callee(result)            |
  |---------------------------|
  | use(result)               |
  +---------------------------+

The dependency did not vanish. It moved to the boundary that owns the choice.
```

## 7. Dynamics

```text
BEFORE

  Caller            Callee                         Source
    |                 |                              |
    |-- work(a) ----->|                              |
    |                 |-- currentValue() ----------->|
    |                 |<-- v ------------------------|
    |                 |-- compute from a and v       |
    |<-- result ------|                              |

AFTER

  Caller            Source                         Callee
    |                 |                              |
    |-- currentValue() ----------------------------->|
    |<-- v ------------------------------------------|
    |                                                |
    |-- work(a, v) --------------------------------->|
    |                                                |-- compute
    |<-- result -------------------------------------|

The call now carries a snapshot. The callee no longer decides when or where
the value is obtained.
```

At runtime, this can change timing even when the final value is the same. The
old code queried during execution of the callee. The new code queries before
the call. If the queried source is mutable, remote, lazy, or time based, that
timing difference is observable. Safe application requires either a stable
query, a test that pins the intended timing, or an explicit decision that the
new snapshot timing is the desired behavior.

The refactoring also changes failure location. If `currentValue()` can fail,
the exception or error now appears at the call site. That can improve error
handling because the caller often knows which request, batch, retry, or
transaction is in progress. It can also scatter error handling if every caller
must repeat the same recovery path.

## 8. Implementation variants

**Scalar value parameter.** The callee reads a single fact, such as a date,
locale, currency, temperature, or tenant id. The caller passes that fact. This
is the smallest form and the easiest to review. It becomes dangerous when the
scalar has weak type information. Prefer domain value types for ids, money,
units, and authority data.

**Value object parameter.** The query returns a set of related facts, such as a
pricing context or render context. Passing one value object avoids a long
parameter list and carries invariants in one place. It costs a new type and can
grow into an unowned bag if teams keep adding fields.

**Collaborator parameter.** The callee used to construct or locate a service.
The caller now passes a port, interface, function, or closure. This is the form
shown in Fowler's module dependency article when data source functions are
passed to calculation code
(https://martinfowler.com/articles/refactoring-dependencies.html, verified
2026-08-02). It grants substitution and test fakes, but it can spread
configuration knowledge.

**Context parameter.** Go's standard `context` package documents the convention
that functions needing a context should take it explicitly as the first
parameter and should not store it in a struct
(https://pkg.go.dev/context, verified 2026-08-02). This is not the same as
passing any random value through context. The same documentation limits context
values to request scoped data that crosses APIs and processes
(https://pkg.go.dev/context, verified 2026-08-02). Used well, context
parameters make cancellation, deadlines, and trace state explicit enough for
tooling to check propagation.

**Clock or random source parameter.** A function that reads process time or
randomness becomes deterministic when it accepts a clock, instant, seed, or
random generator. The Java `LocalDate.now(Clock)` API obtains the date from a
specified clock, and the JDK documentation says this permits alternate clocks
for testing through dependency injection
(https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/LocalDate.html#now(java.time.Clock),
verified 2026-08-02).

**Higher order function parameter.** In TypeScript, Python, Go, Rust, and Swift,
a function can accept another function that supplies the value. This delays the
query while removing the callee's dependency on the source. It fits code that
needs lazy evaluation or retry. It is heavier than passing the value when the
value is already known.

**Constructor parameter instead of call parameter.** If every call uses the
same source, pass the dependency when creating the object and store it. Fowler's
dependency article treats per call data source parameters as useful for
substitution, then notes that repeated setup at each call can become confusing
and duplicated
(https://martinfowler.com/articles/refactoring-dependencies.html, verified
2026-08-02). Constructor injection is often the next step when the parameter is
stable across calls.

## 9. Known production uses

**Java SE `java.time`.** `LocalDate.now()` reads the system clock in the default
time zone, while `LocalDate.now(Clock)` obtains the date from a caller supplied
clock
(https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/LocalDate.html#now(java.time.Clock),
verified 2026-08-02). The broader `Clock` API describes `Clock` as a pluggable
representation of the current instant and names `System.currentTimeMillis()` and
`TimeZone.getDefault()` as static sources that a clock object can stand in for
(https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/Clock.html,
verified 2026-08-02). This is Replace Query with Parameter in library form:
the caller can pass the time source instead of forcing the date code to query
the process default.

**Go standard library `context`.** The Go `context` package says code should
pass `context.Context` explicitly to each function that needs it, normally as
the first parameter, and should not store contexts inside structs
(https://pkg.go.dev/context, verified 2026-08-02). This is a named production
API convention in the Go standard library. It replaces hidden lookup of request
state, cancellation, and deadlines with an explicit parameter that crosses API
boundaries.

**OpenTelemetry Go instrumentation.** The OpenTelemetry Go documentation shows
parent and child spans being propagated by passing `context.Context` into
`parentFunction` and then into `childFunction`, where the child span is started
from that context
(https://opentelemetry.io/docs/languages/go/instrumentation/, verified
2026-08-02). The same page shows retrieving the current span from a context the
code already has
(https://opentelemetry.io/docs/languages/go/instrumentation/, verified
2026-08-02). That design avoids an implicit "current span" global in ordinary
application code and makes trace parentage an explicit function input.

**Kubernetes scheduler and disruption controller clocks.** Kubernetes exposes a
`WithClock` scheduler option that sets the clock for the priority queue, with
`clock.RealClock{}` as the default in scheduler options
(https://github.com/kubernetes/kubernetes/blob/master/pkg/scheduler/scheduler.go,
verified 2026-08-02). Kubernetes scheduler tests pass
`testingclock.NewFakeClock(time.Now())` through `internalqueue.WithClock`
(https://github.com/kubernetes/kubernetes/blob/master/pkg/scheduler/scheduler_test.go,
verified 2026-08-02). The disruption controller source also has an internal
constructor that accepts a clock and notes that it is for tests
(https://github.com/kubernetes/kubernetes/blob/master/pkg/controller/disruption/disruption.go,
verified 2026-08-02). These are production code examples of replacing direct
time queries with parameters or options so control loops can be tested without
waiting for wall time.

## 10. Consequences

Engineering judgement. The consequences below describe usual outcomes, not a
promise about every codebase.

Positive consequences.

- The callee's dependencies become visible in its signature.
- The function becomes easier to move because it no longer reaches into its old
  module, receiver, or ambient context.
- Tests can pass fixed values, fake clocks, fake randomness, fake principals,
  or fixture data without patching global state.
- The caller can provide a snapshot, which is valuable for event replay,
  retries, batch work, and audit trails.
- Expensive queries can be run once at a higher layer and reused across calls.
- Security review can see whether a function is receiving an authorization
  decision, a principal, a tenant id, or a full session.
- Parallel execution becomes easier when the callee no longer consults mutable
  shared state.

Negative consequences.

- The function signature grows, and call sites become noisier.
- Callers can pass inconsistent values that the old internal query could not
  produce.
- Responsibility may move to the wrong layer, especially when the caller now
  knows domain details that belonged inside the callee.
- Public APIs need migration work, overloads, or versioning.
- Error handling can spread outward if the moved query can fail.
- Tramp data can appear when many intermediate functions pass a value without
  using it.
- The parameter can outlive its purpose after later refactorings, leaving a
  stale argument that nobody questions.

The healthiest result is not the longest signature. It is a function whose
parameters match the real variation points of the computation. If the refactoring
does not move the code closer to that shape, use the inverse.

## 11. Failure modes and misuse

Engineering judgement. Each item names an observable symptom, the likely cause,
and a fix.

| Symptom | Cause | Fix |
|---|---|---|
| Call sites pass `x, x.y, x.z` together across the codebase. | A query was replaced with parameters even though the fields have no independent variation. | Use Preserve Whole Object or Replace Parameter with Query so the callee receives `x` and asks for the fields. |
| Tests pass values that production code could never produce. | The new parameter has weak type or no validation. | Introduce a value object or validate at the boundary that creates the parameter. |
| A formerly deterministic calculation now differs between callers. | Each caller duplicated the old query or used a different authority. | Move the query to one higher layer, name that layer as the authority, and route callers through it. |
| A value is threaded through five functions that do not use it. | The refactoring exposed a hidden dependency but stopped before relocating the behavior. | Move Function toward the value, inject the collaborator at construction, or introduce a narrow context object. |
| Production logs no longer show which tenant, clock, or principal was used. | The old query logged at the source, while the new parameter path did not add boundary logging. | Log or trace the parameter at the callee boundary with redaction rules. |
| A retry or replay uses a new current time rather than the event time. | The caller passed a supplier function when it should have passed a snapshot value. | Pass the instant, date, or version captured at the event boundary. |
| An authorization bypass appears in review. | A trusted callee query was replaced by a caller supplied boolean. | Pass a principal or capability object from a trusted authentication boundary, not a naked boolean from untrusted code. |
| Performance regresses after the change. | Every caller now performs setup or a remote lookup before calling, including paths that the callee would not have used. | Pass a lazy supplier, move the branch above the query, or keep the query in the callee. |
| A public SDK minor release breaks consumers. | The signature changed without a compatibility layer. | Add an overload or new method, deprecate the old one, document the migration, then remove it in a major release. |
| Reviewers cannot tell what the new parameter means. | The name describes the source, such as `fromContext`, rather than the domain fact, such as `requestDeadline`. | Rename the parameter to the fact being passed and use a domain type where possible. |

Misuse often starts from a half-truth: explicit dependencies are good. They are,
but only when they name real variation. A parameter that every caller computes
the same way is not explicit design. It is duplicated ceremony.

One abuse deserves separate attention because it often passes code review. A
team removes a query from a pure function and passes the value in, then leaves
the old query helper public. New callers now have two paths: the old helper and
the new parameter. Over time they diverge, not because anyone intended two
policies, but because both paths remain available. The observable symptom is a
bug report where two screens display different results for the same record. The
fix is to close the old path after migration, or to keep one named authority
that every caller uses before passing the value.

## 12. Trade-off matrix

| Alternative | Coupling | Consistency | Latency | Operability | Team fit | Best use |
|---|---|---|---|---|---|---|
| Replace Query with Parameter | Lowers callee coupling, raises caller duty | Depends on caller correctness | Good when query is costly or repeated | Good when logged at boundary | Good when caller owns context | Move code away from hidden state |
| Replace Parameter with Query | Lowers caller duty, raises callee knowledge | Strong when one source object is authoritative | Good for cheap local queries | Boundary has fewer labels | Good when model team owns derivation | Remove duplicate argument pairs |
| Preserve Whole Object | Keeps related facts together | Strong when object is valid | Depends on object access cost | Logs need field extraction | Good when caller already has object | Avoid scalar argument lists |
| Introduce Parameter Object | Groups values under one type | Strong if constructor validates | Neutral | Good when object has clear fields | Good for shared contracts | Several values vary together |
| Dependency Injection | Keeps calls small after setup | Strong for stable collaborators | Good after construction | Good if configuration is visible | Good for platform services | Same dependency used across many calls |
| Service Locator | Hides caller wiring | Weak when locator is mutable | Depends on lookup | Harder because dependency is implicit | Good only for constrained legacy seams | Transitional repair where signatures cannot change |

The matrix shows the central trade. Replace Query with Parameter is strongest
when an input belongs at the call boundary. It is weaker than constructor
injection when the same collaborator is used on every call. It is weaker than
Preserve Whole Object when the parameter is only a field of another argument.

## 13. Related and incompatible patterns

**Replace Parameter with Query** is the inverse. Use it when a parameter is
duplicate knowledge that the callee can derive from another input. Fowler's
catalog explicitly links the two as inverses
(https://refactoring.com/catalog/replaceQueryWithParameter.html, verified
2026-08-02).

**Change Function Declaration** is the mechanical wrapper around the change.
Adding the new parameter, updating callers, and later removing an old overload
are all signature changes.

**Separate Query from Modifier** should come first when the old query changes
state. If a lookup advances a cursor or refreshes a token with visible effects,
do not bury that behavior in a new argument. Split the command from the value
read, then pass the value if it still belongs at the boundary.

**Parameterize Function** is broader. It turns a constant or fixed choice into
a parameter. Replace Query with Parameter is narrower because the replaced
constant is not literal in the callee. It is obtained through a query.

**Introduce Parameter Object** composes with this refactoring when several
queries move outward together. It is the escape hatch when the new signature
becomes hard to read.

**Move Function** often follows. After a function no longer queries its old
receiver or module, it can move to the module that owns the computation.

**Dependency Injection** is the object lifetime version of the same pressure.
When the queried source is a stable collaborator rather than a per call value,
constructor or factory injection may be clearer than passing the collaborator on
every call.

**Service Locator** often conflicts. A locator hides the dependency that this
refactoring tries to reveal. It may be useful as a migration bridge when a
published API cannot change, but it should not be the target design for a small
pure calculation.

**Context Object** can compose or conflict. A narrow request context can carry
cancellation, trace state, and request scoped values across API boundaries. A
wide context object can become a disguised global. Go's context documentation
draws this line by limiting values to request scoped data that crosses process
and API boundaries (https://pkg.go.dev/context, verified 2026-08-02).

## 14. Refactoring path in and out

Path in.

1. Name the query and the value it returns. If you cannot name the value in
   domain language, pause.
2. Add a characterization test around the callee. Include one case where the
   queried value matters.
3. Add the new parameter to the callee while leaving the old query in place.
4. Inside the callee, assert or compare that the parameter equals the query for
   a short migration window when the query is cheap and safe. Do not keep this
   check if it calls remote systems or exposes private data.
5. Replace use of the internal query with the parameter.
6. Update callers one group at a time. Prefer compiler guided changes in typed
   code. In dynamic code, search for every call form and run focused tests.
7. Remove the internal query dependency from the callee imports, fields, or
   receiver.
8. If the new parameter passes through functions that do not use it, decide
   whether to move the callee, introduce a parameter object, or inject a stable
   collaborator.
9. Delete any temporary overload, default, or compatibility wrapper after all
   callers move.

Path out.

1. Look for repeated call forms such as `work(order, order.currency())`.
2. Ask whether callers ever pass a different value for valid business reasons.
3. If no, apply Replace Parameter with Query and remove the redundant
   parameter.
4. If many values always travel together, use Introduce Parameter Object or
   Preserve Whole Object.
5. If the value is the same for every call on an object, move it to
   constructor injection.
6. If the parameter is part of a public API, keep an adapter layer until
   consumers have migrated.

The safest migration preserves behavior first, then improves shape. Do not
combine this refactoring with a policy change such as switching from system
time to event time unless the tests name that policy change.

## 15. Testing and verification

Engineering judgement. Testing should prove two things: the function still
computes the same result for the same input, and the hidden dependency is gone.

Use characterization tests before the edit. Pin cases where the old query
affects the result: current date, locale, tenant, feature flag, discount rate,
permission, random seed, or trace parent. After adding the parameter, rerun the
same cases with fixed values. The test should no longer patch globals or install
ambient context for the callee.

Use test doubles at the boundary that now owns the query. If the caller passes a
clock, use a fake clock. If it passes a principal, use a minimal principal value
from the authentication test builder. If it passes a data source function, pass
a stub function that returns a fixed record. Avoid mocks that assert call order
inside the callee after the dependency has been removed; the point of the change
is that the callee no longer talks to that source.

Add mismatch tests when invalid pairings are possible. For example, if a caller
passes `tenantId` and `invoice`, test that the boundary rejects an invoice from
another tenant. This test belongs where the parameter is created, not deep in
the pure calculation unless the calculation is the security boundary.

For concurrency and replay, test timing. Capture the old behavior if it matters:
query at call time, query at use time, or repeated query. Then select the new
behavior on purpose. A snapshot value and a supplier function are different
designs, and tests should make that visible.

Verification is also static. Search the callee for imports or references to the
queried source after the change. If the source is still present, the
refactoring did not finish. In typed languages, make the old dependency
unavailable to the callee package where possible. In dynamic languages, add a
small test that runs the callee without the old module initialized.

For public APIs, verification includes compatibility. A deprecation test can
prove that the old overload still delegates to the new implementation during
the migration window. A contract test can prove that serialized request and
response formats did not change when the internal function signature changed.
Those tests are not about the refactoring mechanics. They protect consumers
while the codebase moves from hidden dependency to explicit input.

## 16. Observability signals

Engineering judgement. Observability should make the new boundary visible
without logging private data.

Record the parameter when it explains behavior: clock type, event date, tenant
id hash, locale, currency, policy version, data source name, feature flag
snapshot, trace id, or request deadline. Avoid raw tokens, emails, full names,
addresses, and unredacted principals. When the parameter is a collaborator, log
its stable name or type, not its object dump.

A healthy dashboard shows stable distributions. Clock source is almost always
`real` in production and `fake` in tests. Policy version matches the deployment
or experiment plan. Locale and currency cardinality match the served markets.
Trace parent presence matches inbound traffic. Data source names match approved
configuration.

A failing instance has different shapes. Cardinality spikes after callers begin
passing raw ids. A sudden rise in `unknown` policy version means callers are
using defaults. Mixed clock sources in one production process may signal a test
fake leaked into runtime configuration. A drop in trace parent propagation after
adding context parameters means one call path forgot to pass the context onward.
Repeated expensive query spans at many call sites mean the lookup moved outward
but was not centralized.

Trace both sides during migration. At the caller boundary, record that the value
was obtained. At the callee boundary, record that the value was consumed. Once
the migration is complete, keep only the signal needed for operations and
security review.

## 17. Security and privacy implications

Engineering judgement. The refactoring changes where trust is placed.

Security improves when the callee no longer needs a large context object. A
function that receives `tenantId`, `policyVersion`, or `canViewInvoices` may no
longer need access to the whole HTTP request, session, or account object. That
shrinks accidental data exposure and makes data flow easier to audit.

Security worsens when the caller supplied value is treated as authority without
checking its source. A boolean named `isAdmin` is unsafe if it can come from an
HTTP body. A tenant id is unsafe if it can be paired with another tenant's
record. A clock is unsafe in expiry code if untrusted callers can move time
backward. The fix is to pass values from trusted boundaries, or pass capability
objects that cannot be forged inside the process.

Privacy can improve when a narrow value replaces a broad context. A renderer
that receives `locale` does not need the user's profile. A calculation that
receives an account tier does not need the account object. Privacy can worsen
when the value is copied into logs, traces, messages, or job payloads. Treat the
new parameter as part of the data flow map.

The pattern is silent on access control. It makes dependencies visible; it does
not decide who is allowed to supply them. That decision belongs at the trust
boundary around the caller.

## Code examples

### TypeScript

```typescript
type Customer = {
  id: string;
  discountRate: number;
};

function totalAfterDiscount(subtotal: number, discountRate: number): number {
  return Math.round(subtotal * (1 - discountRate));
}

function invoiceTotal(customer: Customer, subtotal: number): number {
  return totalAfterDiscount(subtotal, customer.discountRate);
}

console.log(invoiceTotal({ id: "c-17", discountRate: 0.15 }, 200));
```

Before the refactoring, `totalAfterDiscount` might have accepted `customer` and
queried `customer.discountRate` internally. Passing `discountRate` gives the
calculation a narrower input and lets a pricing caller supply a historical rate
for replay.

### Python

```python
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Contract:
    start: date
    trial_days: int


def trial_expired(contract: Contract, today: date) -> bool:
    age = (today - contract.start).days
    return age >= contract.trial_days


contract = Contract(start=date(2026, 1, 1), trial_days=30)
print(trial_expired(contract, date(2026, 2, 1)))
```

The function receives `today` instead of reading `date.today()`. Tests, replay
jobs, and backfills can choose the date without patching the Python standard
library or sleeping until a calendar changes.

### Go

```go
package main

import (
	"fmt"
	"time"
)

type Subscription struct {
	RenewsAt time.Time
}

func renewalWindowOpen(sub Subscription, now time.Time) bool {
	start := sub.RenewsAt.Add(-72 * time.Hour)
	return !now.Before(start) && now.Before(sub.RenewsAt)
}

func main() {
	sub := Subscription{RenewsAt: time.Date(2026, 8, 10, 12, 0, 0, 0, time.UTC)}
	now := time.Date(2026, 8, 8, 12, 0, 0, 0, time.UTC)
	fmt.Println(renewalWindowOpen(sub, now))
}
```

The Go example passes a snapshot time. If the function called `time.Now()`
inside, tests would depend on wall time and event replay would be harder to
reason about.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 11, "Refactoring APIs," section
  "Replace Query with Parameter."
- Martin Fowler, "Replace Query with Parameter," refactoring catalog,
  https://refactoring.com/catalog/replaceQueryWithParameter.html, verified
  2026-08-02.
- Martin Fowler, "Changes for the 2nd Edition of Refactoring,"
  https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
  2026-08-02.
- Martin Fowler, "Refactoring Module Dependencies,"
  https://martinfowler.com/articles/refactoring-dependencies.html, verified
  2026-08-02.
- Oracle, "Class Clock," Java SE 17 API specification,
  https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/Clock.html,
  verified 2026-08-02.
- Oracle, "LocalDate.now(Clock)," Java SE 17 API specification,
  https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/time/LocalDate.html#now(java.time.Clock),
  verified 2026-08-02.
- The Go Authors, "Package context," Go standard library documentation,
  https://pkg.go.dev/context, verified 2026-08-02.
- OpenTelemetry Authors, "Instrumentation," OpenTelemetry Go documentation,
  https://opentelemetry.io/docs/languages/go/instrumentation/, verified
  2026-08-02.
- Kubernetes Authors, "pkg/scheduler/scheduler.go," Kubernetes source,
  https://github.com/kubernetes/kubernetes/blob/master/pkg/scheduler/scheduler.go,
  verified 2026-08-02.
- Kubernetes Authors, "pkg/scheduler/scheduler_test.go," Kubernetes source,
  https://github.com/kubernetes/kubernetes/blob/master/pkg/scheduler/scheduler_test.go,
  verified 2026-08-02.
- Kubernetes Authors, "pkg/controller/disruption/disruption.go," Kubernetes
  source,
  https://github.com/kubernetes/kubernetes/blob/master/pkg/controller/disruption/disruption.go,
  verified 2026-08-02.
