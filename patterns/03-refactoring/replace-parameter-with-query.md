---
name: Replace Parameter with Query
slug: replace-parameter-with-query
family: 03-refactoring
category: Refactoring
aliases: [Replace Parameter with Method, Remove Redundant Parameter]
first_described: "Fowler 1999"
maturity: canonical
related: [preserve-whole-object, replace-query-with-parameter, separate-query-from-modifier, change-function-declaration, introduce-parameter-object, move-function]
incompatible_with: []
verified: 2026-08-02
---

# Replace Parameter with Query

## 1. Name, aliases, and lineage

The canonical name is **Replace Parameter with Query**. Martin Fowler's public
catalog shows a call that passes `anEmployee.grade` and then a revised call that
passes only `anEmployee`, while the callee obtains the grade from the employee
inside the function (https://refactoring.com/catalog/replaceParameterWithQuery.html,
verified 2026-08-02). The same catalog page names **Replace Parameter with
Method** as an alias and lists **Replace Query with Parameter** as the inverse
refactoring (https://refactoring.com/catalog/replaceParameterWithQuery.html,
verified 2026-08-02).

Fowler's 2018 note on the second edition catalog says the first edition
refactoring named Replace Parameter with Method, page 292, was replaced by
Replace Parameter with Query in the second edition
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02). InformIT's online excerpt from *Refactoring. Improving the Design
of Existing Code*, 2nd edition, also places Replace Parameter with Query at page
324 and links it to the Long Parameter List smell
(https://www.informit.com/articles/article.aspx?p=2952392&seqNum=4, verified
2026-08-02).

Book citation. Martin Fowler, *Refactoring. Improving the Design of Existing
Code*, 1st edition, Addison-Wesley, 1999, chapter 10, "Making Method Calls
Simpler," section "Replace Parameter with Method." Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 11, "Refactoring APIs," section "Replace
Parameter with Query," page 324 confirmed by the InformIT excerpt above.

The word "query" here has its ordinary object design meaning. A query returns
information without changing observable state. Fowler credits Bertrand Meyer
with coining Command Query Separation and describes queries as operations that
return a result without changing observable state
(https://martinfowler.com/bliki/CommandQuerySeparation.html, verified
2026-08-02). That matters because this refactoring is sound only when the
replacement expression is a query in that sense, or close enough that repeating
it inside the function is not a hidden command.

## 2. Problem and context

A caller computes a value, then passes that value to a function that already has
access to the data needed to compute the same value. The parameter is not a
choice made by the caller. It is a copy of knowledge already reachable from
another parameter, the receiver, a stable field, or a request context that the
callee already owns.

The smell is easy to recognise in review. A call reads
`priceFor(order, order.customer.discountTier)`, `renewalDate(contract,
contract.termMonths)`, or `canEdit(request, request.user, article)`. The second
argument looks like a fact about the first argument. The callee can ask the first
argument for the same fact. The call site has been made responsible for a
calculation that belongs nearer the data.

This is not mainly about shorter signatures. It is about removing a second
source of truth. While both `employee` and `grade` travel as parameters, a bug
can pass an employee from one record and a grade from another. The function
body cannot know whether the two values match unless it adds an assertion,
which means the interface invited a state that the domain does not accept.

The context that makes the refactoring pay has three parts.

- The callee already receives or owns an object from which the parameter can be
  obtained.
- The query is cheap enough, stable enough, and side effect free enough for the
  callee to run it at the point of use.
- The caller is not meant to vary the value independently of that object.

When those three conditions hold, the parameter is ceremony. When any condition
fails, the parameter may be a real dependency boundary. Dimension 4 gives the
explicit non-applicability list.

There is a second context: API repair after growth. A function often starts
with one caller. The caller already has every local value on screen, so passing
one more value feels harmless. Later there are twelve callers, and each has
copied the same extraction. At that point the extraction is part of the
function's protocol. Every caller must know the same recipe, and every later
change to the recipe becomes a search across the codebase. Replace Parameter
with Query moves that recipe behind the function boundary.

The refactoring is also a useful test for names. If the removed parameter had a
domain name, such as `approvalLimit`, and the query has the same domain name,
the parameter was probably duplicate knowledge. If the removed parameter has a
different domain name, such as `requestedLimit`, the caller may be expressing
intent rather than copying data. Similar types are not proof of sameness. Two
strings, two integers, or two dates can represent different facts. The safe
question is not "can I compute this value." The safe question is "is the
computed value the only valid value for this call."

## 3. Forces

Engineering judgement. The forces below are a reading of the trade, not a
sourced claim about all codebases.

- **Coupling.** Favoured at the call site. Callers no longer know how a derived
  value is reached. Sacrificed inside the callee when the query introduces a new
  dependency on a richer object or context.
- **Consistency.** Favoured. The callee observes one source object and derives
  related facts from it, which removes mismatched parameter pairs.
- **Cognitive load.** Favoured for readers of call sites because fewer values
  must be matched by eye. Sacrificed for readers of the callee when a local
  query hides work that used to be visible at the call.
- **Latency.** Neutral to negative. Replacing a passed value with a query is
  cheap when the query reads memory. It is harmful when the query performs I/O,
  touches a lazy relation, parses input, or recomputes an expensive aggregate.
- **Operability.** Mixed. Fewer explicit parameters mean fewer labels are
  available at the boundary. If the derived value matters in incidents, record
  it inside the callee.
- **Cost of change.** Favoured when the derivation changes, because only the
  callee changes. Sacrificed when callers need to supply an override for tests,
  simulations, migrations, or partial data.
- **Team topology.** Favoured when one team owns the object model and wants all
  consumers to use its query. Sacrificed when a platform team wants a pure
  function whose dependencies are clear from its argument list.
- **Security and privacy.** Mixed. Removing a caller supplied identity or policy
  parameter can prevent spoofing. Querying ambient context can hide access to
  sensitive data.

The pattern therefore favours local consistency and smaller public APIs. It
pays for those gains with greater dependence on the callee's reachable context.

There is one force that tends to be underweighted: reviewability. A reviewer can
spot `approve(request, request.user)` and ask whether the user should come from
the request. A reviewer cannot as easily spot twenty lines above the call where
the user was taken from the request, stored in `actor`, and passed later. After
the refactoring, the review question moves from call sites to the callee body:
is the query the right authority, and is it cheap at this point? That is usually
a better place for the question because the callee is where the value is used.

## 4. Applicability and non-applicability

Reach for Replace Parameter with Query when the following hold.

- A parameter is obtained by asking another parameter, for example
  `ship(order, order.destination())`.
- A method on an object receives a parameter that can be obtained from the same
  object through a side effect free method or property.
- Many call sites repeat the same extraction before calling the same function.
- A pair of parameters can become inconsistent, and one member is the source of
  the other.
- The derived value is part of the callee's normal responsibility, not caller
  policy.
- You are preparing a later Move Function or Extract Function and want the new
  function to carry fewer accidental inputs.
- The query is deterministic for the duration of the function call.

Do NOT reach for it in these cases.

- **The caller is allowed to vary the value.** If a caller may price an order
  using a preview tier, a historical tier, or a test tier, the parameter is a
  policy input. Removing it erases a valid mode.
- **The query adds a dependency you are trying to remove.** Fowler's catalog
  lists Replace Query with Parameter as the inverse
  (https://refactoring.com/catalog/replaceQueryWithParameter.html, verified
  2026-08-02). Use the inverse when the callee must be moved away from a global,
  module variable, context object, database handle, clock, or request.
- **The query is not a query.** If obtaining the value logs in a user, advances
  an iterator, opens a socket, consumes a stream, mutates a cache with visible
  effects, or changes a cursor, the refactoring hides a command behind a clean
  name. Separate Query from Modifier first.
- **The query is slow or remote.** A parameter can be an intentional cache of a
  value the caller already paid to compute. Moving the computation inward can
  turn one database read into many.
- **The value must be frozen at call time.** In concurrent or async code, the
  caller may pass a snapshot because the object can change before the callee
  uses it. Querying later changes semantics.
- **The object may be partial.** Deserialised events, search results, and API
  DTOs may contain the derived value but omit the source relation. Asking the
  object for data it does not carry forces an extra load.
- **The query would cross a privacy boundary.** A function that receives a
  permission boolean may be safe to share. A function that queries `request.user`
  or an account object may now touch personal data.
- **The parameter documents a domain decision.** A name such as
  `taxJurisdiction` or `settlementCurrency` may look derivable from address or
  account, but the caller may be recording a legal choice. Keep the parameter
  until the domain owner confirms it is derived.
- **The caller has already validated or normalised the value.** If callers pass
  a cleaned value because raw source data is hostile, querying the raw source in
  the callee can reintroduce parsing and validation bugs. Move the normalising
  query into the source object first, then remove the parameter.
- **The function is deliberately pure.** A calculation library may accept only
  numbers, dates, and value objects so it can run in batch jobs, tests, and
  browser code. Adding a query against a database model, HTTP request, or
  process context makes that library less portable.
- **The parameter is part of a published protocol.** Removing it from an
  internal function is cheap. Removing it from an SDK, plugin hook, RPC schema,
  or event contract needs a versioned migration. Otherwise external code breaks
  even if the new design is cleaner.

The non-applicability rule is simple. If the parameter represents variation,
time, trust, cost, or authority, treat it as real input.

One practical decision rule helps. If you can write an assertion in the callee
that says `oldParameter == query(source)` and expect it never to fail in real
traffic, the refactoring is likely valid. If you expect valid failures, the
parameter is not redundant. If you cannot write the assertion because the query
is slow, remote, nondeterministic, or effectful, stop and fix that fact before
changing the signature.

## 5. Structure

The refactoring has four roles.

- **Caller.** It currently obtains a value and passes it as a parameter.
- **Callee.** It currently receives the value and uses it as if it were local
  knowledge.
- **Source object or context.** The receiver, another argument, a field, or a
  request scoped object that can answer the same question.
- **Query.** The side effect free operation that returns the value formerly
  passed by the caller.

Before the refactoring, the Caller depends on both the Callee and the query used
to obtain the value. After the refactoring, the Caller depends only on the
Callee. The Callee owns the query. The Source object becomes more central, so
the move is not free. It shifts dependency inward.

The smallest mechanical shape is this.

1. Add the query inside the Callee and use a local variable to hold the result.
2. Remove uses of the old parameter from the Callee body.
3. Remove the parameter from the declaration.
4. Update all callers.

In a method, the source may be `this`. In a function, it is usually another
parameter. In a request handler, it may be a request context. The last form is
powerful but risky because context can hide dependencies.

The Callee should usually store the query result in a local variable with the
old parameter name during the first edit. That keeps the rest of the body stable
and lets tests isolate the signature change from the calculation change. After
the migration is settled, the local may be inlined if the expression is short
and the name adds no domain meaning. Keeping the local is often better when the
name records a business concept.

## 6. ASCII structure diagram

```
Before

  +-----------------------+       passes source and copied fact
  |        Caller         |-----------------------------------+
  |-----------------------|                                   |
  | grade = employee.grade|                                   v
  | vacation(employee,    |                         +------------------+
  |          grade)       |                         |      Callee      |
  +-----------------------+                         |------------------|
            |                                      | vacation(emp, g) |
            | queries                              | uses g           |
            v                                      +------------------+
  +-----------------------+
  |     Source object     |
  |-----------------------|
  | grade                 |
  +-----------------------+

After

  +-----------------------+       passes source only
  |        Caller         |-----------------------------+
  |-----------------------|                             |
  | vacation(employee)    |                             v
  +-----------------------+                   +----------------------+
                                              |        Callee        |
                                              |----------------------|
                                              | vacation(employee)   |
                                              | grade = employee...  |
                                              +----------------------+
                                                        |
                                                        | queries
                                                        v
                                              +----------------------+
                                              |    Source object     |
                                              |----------------------|
                                              | grade                |
                                              +----------------------+
```

## 7. Dynamics

The runtime change is a movement of responsibility, not a new collaboration.
The same query still runs. The difference is the place where it runs and the
moment at which its result is captured.

```
Before

Caller              Source object             Callee
  |                      |                       |
  |-- grade() ---------->|                       |
  |<-- "A" --------------|                       |
  |-- vacation(obj,"A") ----------------------->|
  |                      |                       |
  |                      |        uses "A"       |
  |<--------------------------------------------|

After

Caller              Source object             Callee
  |                      |                       |
  |-- vacation(obj) --------------------------->|
  |                      |                       |
  |                      |<------ grade() -------|
  |                      |------- "A" ---------->|
  |                      |        uses "A"       |
  |<--------------------------------------------|
```

The dynamic risk is timing. Before the refactoring, the value is captured before
the call. After the refactoring, the value is captured inside the callee. If the
source object can change between those two points, the refactoring changes
behaviour. The safe path is to add an assertion during migration that compares
the passed value with the queried value, run the test suite and selected
production shadow checks, then remove the parameter.

There is also an ordering risk in validation code. Before the refactoring, a
caller might validate the derived value before calling the function. After the
refactoring, validation may happen later or not at all. The cure is to make the
query return an already valid domain value, not raw data. For example, a request
query should return a parsed `AccountId`, not a bare string from a route
parameter, when the callee relies on account identity.

## 8. Implementation variants

**Query another parameter.** The most common form. The callee keeps the source
object parameter and removes the fact parameter. This is the form shown in
Fowler's catalog example
(https://refactoring.com/catalog/replaceParameterWithQuery.html, verified
2026-08-02).

**Query the receiver.** An instance method receives a parameter that can be
computed from `this`. The body replaces the parameter with a private method or
property. This is clean when the method belongs to the same aggregate as the
data. It is poor when the method was meant to be moved out of the class.

**Query a request or execution context.** Web frameworks often make request
data available through an object or context, so app code does not pass every
header, route parameter, session field, and user separately. This shortens
handlers, but it couples helper code to a live request.

**Inline the old argument expression first.** When the call site has a named
temporary, inline it into the call before changing the callee. That reveals
whether every caller uses the same expression. If one caller passes a different
expression, stop and decide whether it is valid variation.

**Keep a compatibility overload.** In Java, TypeScript, Swift, and Go packages
with external callers, remove the parameter in two releases. Add a new function
or method first, make the old declaration delegate after checking equivalence,
then delete the old declaration after callers migrate.

**Use an assertion during the transition.** For a short period, compute the
query inside the callee and compare it with the parameter. The assertion should
fail in tests and logs rather than alter user output. This catches mismatched
callers before the public signature changes.

**Batch the query.** If the value is cheap per object but expensive across a
collection due to lazy loading, prefetch the relation before calling the callee.
Do not pass the derived value back as a parameter unless the prefetch cannot be
made part of the source object's query contract.

**Query object variant.** When the callee needs a small number of related
queries but should not depend on a large domain object, pass a narrow query
object. For example, pass `PricingFacts` with methods for tier and region
rather than the full `Customer`. This is a middle path between explicit scalar
parameters and a broad object dependency. It is helpful at module boundaries
where a rich domain object would drag in storage, validation, or web concerns.

**Snapshot variant.** When time matters, create a snapshot object at the
boundary and query the snapshot inside the callee. This preserves the "one
source object" shape while avoiding late reads from mutable state. The snapshot
must be a value object. If it points back to live state, it has not solved the
timing issue.

**Language note.** Python and TypeScript make this refactoring pleasant because
call sites are easy to update and object properties are idiomatic queries. Go
uses explicit methods and values, so the trade is often between a small struct
method and a free function with fewer parameters. Java needs more care when
overloads preserve binary compatibility.

## 9. Known production uses

Engineering judgement. These are named production API shapes that apply the
same design move, not public claims that their maintainers performed this named
refactoring.

**Flask request context.** Flask documents that request level data is tracked in
a request context and that, instead of passing the request object to each
function running during a request, code accesses `request` and `session`
proxies (https://flask.palletsprojects.com/en/stable/reqcontext/, verified
2026-08-02). This is the context variant of the pattern. A helper can query the
current request for `args`, `headers`, or session state rather than receiving
each item as a parameter. The source also warns that using the proxy outside a
request context raises a runtime error, which is the failure mode for hidden
context dependency.

**Ruby on Rails Action Controller.** Rails documents that request parameters,
session data, and the full request object are available to controller actions
through accessor methods, and that `params` returns request parameters
(https://api.rubyonrails.org/classes/ActionController/Base.html, verified
2026-08-02). Rails controller actions therefore commonly query `params` and
`request` from the controller rather than accept each route value, form value,
header, or method as an explicit action parameter. The design shortens action
signatures and centralises request parsing in the controller.

**Django admin permission hooks.** Django documents `ModelAdmin.has_change_permission(request,
obj=None)` as the hook for edit permission and requires admin setups to include
`AuthenticationMiddleware`
(https://docs.djangoproject.com/en/6.0/ref/contrib/admin/, verified
2026-08-02). Django's authentication middleware source assigns `request.user`
on incoming requests
(https://github.com/django/django/blob/main/django/contrib/auth/middleware.py,
verified 2026-08-02). A custom admin permission method therefore receives the
request and object, then queries `request.user` instead of taking a separate
user parameter. That removes one mismatch risk: the permission hook cannot be
called with one request and a different user without custom code fabricating the
request.

These examples also show the boundary of the pattern. Flask and Rails use
ambient request access, which is concise but harder to test outside a request
cycle. Django keeps the request explicit, which makes the dependency visible
while still letting the hook query `request.user`.

## 10. Consequences

Positive.

- Call sites shrink, and the remaining parameters better represent true
  variation.
- The derived value has one authority. The callee obtains it from the source
  object rather than trusting a copied value.
- Changes to the derivation move to one function body instead of many callers.
- The refactoring often exposes a better home for behaviour. If the callee is
  always asking the same object for data, Move Function may be next.
- Tests at the caller level need fewer fixtures because they no longer compute
  values that are not the caller's concern.
- Public APIs become harder to call incorrectly because mismatched source and
  derived parameters disappear.

Negative.

- The callee gains a dependency on the source object, receiver state, or
  context from which it queries the value.
- The query may run more often than before, especially when a loop calls the
  callee repeatedly.
- The exact value used by the callee is less visible at the call site.
- Tests for the callee may need a richer source object or context fixture.
- If the query touches mutable state, the refactoring can change the time at
  which the value is observed.
- Public API migration can be noisy because every caller must update the
  function signature.

## 11. Failure modes and misuse

Engineering judgement. These are common production failure shapes and review
smells.

**Symptom.** A database query count rises after a small signature cleanup.
**Cause.** The old parameter carried a value the caller loaded once. The new
callee query follows a lazy relation on every call. **Fix.** Prefetch the
relation, cache inside the source object for the request, or keep the parameter
when prefetch cannot be expressed cleanly.

**Symptom.** A test that passed with a supplied `now` value becomes flaky near
midnight or month end. **Cause.** The callee now queries the clock instead of
receiving a snapshot. **Fix.** Keep time as a parameter, or pass a clock object
and query that object once at the boundary.

**Symptom.** A helper raises "working outside request context" in a background
job. **Cause.** The refactoring replaced explicit request data with an ambient
request query. **Fix.** Move the helper back to explicit parameters or pass a
small context object that can exist outside HTTP handling.

**Symptom.** A permission check starts authorising the wrong user in a test or
admin script. **Cause.** The callee queries a mutable request object that was
reused or patched. **Fix.** Build a fresh request fixture per test and assert
the request user before the permission call, or keep identity explicit in code
that crosses trust boundaries.

**Symptom.** Callers lose the ability to ask for a dry run, preview, historical
calculation, or simulation. **Cause.** The removed parameter was not redundant.
It represented a mode or policy. **Fix.** Restore the parameter with a better
name, or model the mode as a Strategy or Parameter Object.

**Symptom.** A function becomes harder to move to another module. **Cause.** It
now queries fields or globals from its old module. **Fix.** Use Replace Query
with Parameter, then Move Function.

**Symptom.** A public package update breaks downstream code at compile time.
**Cause.** The parameter was removed without a compatibility period. **Fix.**
Ship an overload or wrapper, mark it deprecated, record use, then remove in the
next major version.

**Symptom.** Logs lose a useful dimension after the change. **Cause.** The
parameter value used to be logged at the boundary, but now exists only as a
local value. **Fix.** Log the queried value inside the callee with the same
cardinality control as before.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Replace Parameter with Query | Preserve Whole Object | Introduce Parameter Object | Replace Query with Parameter | Dependency Injection | Move Function |
|---|---|---|---|---|---|---|
| Coupling | Caller loses derivation knowledge, callee gains source dependency | Caller passes source object, callee gains broad object dependency | Callee depends on a new value type | Callee loses source dependency, caller gains work | Callee depends on an injected provider | Function moves to object that owns data |
| Consistency | Strong when query source is authoritative | Strong when the whole object is authoritative | Strong inside the parameter object | Depends on caller discipline | Depends on provider scope | Strong if moved to the data owner |
| Cognitive load | Lower at call sites, higher inside callee | Lower than field lists, object may be broad | New type name may clarify the group | More explicit but longer calls | Wiring adds a concept | Location may be clearer |
| Latency | Risk if query is expensive | Risk if callee walks broad object graph | Usually neutral | Caller can cache or batch | Provider may cache | Often neutral |
| Operability | Derived value must be logged inside callee | Source object identity is visible | Parameter object can carry labels | Value visible at boundary | Provider name can be logged | Owner method logs near data |
| Team topology | Good when data owner team owns query | Good when teams share domain object | Good when teams agree on value type | Good across service or module boundaries | Good for platform owned services | Good when ownership follows data |
| Testing | Needs source fixture | Needs richer object fixture | Easy to build test value | Easy to pass literals | Needs fake provider | Tests move with method |
| API stability | Signature shrinks, break on removal | Signature may shrink more | Signature changes to new type | Signature grows | Constructor or setup changes | Call target changes |

Reading of the table. Replace Parameter with Query wins when the removed
parameter is a duplicate of data already owned by a source object. Preserve
Whole Object wins when several parameters come from the same object. Introduce
Parameter Object wins when the parameters travel together but have no existing
owner. Replace Query with Parameter wins when dependency direction matters more
than signature length. Dependency Injection wins when the value comes from an
external service. Move Function wins when the callee is already doing another
object's work.

## 13. Related and incompatible patterns

- **Preserve Whole Object.** Often precedes this refactoring. First pass the
  object rather than many fields, then remove any remaining parameter that the
  callee can ask from that object.
- **Replace Query with Parameter.** The inverse. Use it when the query is an
  unwanted dependency, when the value must be a caller snapshot, or when the
  function is being moved to code that cannot see the query source.
- **Separate Query from Modifier.** A guardrail. This refactoring assumes the
  replacement operation is a query. If it modifies observable state, split the
  modifier from the read before changing the signature.
- **Change Function Declaration.** The mechanical wrapper. Removing the
  parameter is a change to the declaration and all callers.
- **Introduce Parameter Object.** A sibling answer to Long Parameter List. Use
  it when a group of parameters is coherent but not derivable from one another.
- **Move Function.** A common follow-up. If a function keeps querying the same
  object for many facts, the behaviour may belong on that object.
- **Command.** Can replace the refactoring when a call needs a rich execution
  context, retry state, audit data, and policy values. In that case a command
  object names the call state better than a hidden query.
- **Global context and Service Locator.** Often conflict. Querying ambient state
  can hide dependencies. Flask documents its request proxy model
  (https://flask.palletsprojects.com/en/stable/reqcontext/, verified
  2026-08-02), but application code should still treat that as a scoped
  dependency, not free data.

## 14. Refactoring path in and out

Introducing the refactoring.

1. Pick one parameter that appears derivable from another parameter, the
   receiver, or a context the callee already owns.
2. Name the query expression in the callee as a local variable, but keep the old
   parameter.
3. Add a temporary assertion or diagnostic that compares the old parameter with
   the queried value. Use this only during migration.
4. Run the unit tests and at least one integration path that covers a real
   caller.
5. Replace reads of the old parameter with reads of the local queried value.
6. Change the function declaration to remove the parameter.
7. Update callers one group at a time. Remove local variables that existed only
   to supply the old parameter.
8. Remove the temporary assertion once all callers use the new form.
9. Review the callee for a new dependency smell. If it now envies the source
   object, consider Move Function.

Removing the refactoring when it stops earning its place.

1. Identify the query inside the callee and decide whether it is expensive,
   time sensitive, security sensitive, or a dependency you want to move out.
2. Add the parameter back with a name that states the variation, for example
   `pricingClock`, `authorizingUser`, or `snapshotTier`.
3. At each caller, pass the same value that the callee used to query. Keep this
   as a behaviour preserving step.
4. Delete the internal query.
5. If the caller now repeats a bundle of values, consider Introduce Parameter
   Object rather than returning to a long unstructured list.

The named path out is Replace Query with Parameter. Fowler's public catalog
lists it as the inverse of this refactoring
(https://refactoring.com/catalog/replaceQueryWithParameter.html, verified
2026-08-02).

For published APIs, use a slower path. Add the new declaration and keep the old
one as a wrapper. In the wrapper, compute the query and compare it with the
caller supplied value. If they differ, emit a deprecation diagnostic that names
the caller if your platform can do that safely. Then call the new declaration.
This wrapper gives downstream users two pieces of information: the old parameter
is going away, and their current value may not match the source object. A plain
deprecation warning gives only the first. Remove the wrapper on the next major
release or the release policy's normal breaking change point.

For internal code, prefer the narrow path. Change one function, update all
callers, run tests, then commit. Avoid mixing this refactoring with renames,
module moves, formatting, or product logic changes. The behavioural diff should
say one thing: the callee now obtains the value from the source it already had.
That small diff is what lets reviewers reason about time, cost, and authority
without reading unrelated edits.

## 15. Testing and verification

Engineering judgement. Tests should prove that the parameter was redundant, not
only that the compiler accepts the new signature.

- **Equivalence tests before removal.** While both values exist, assert that the
  passed parameter and the queried value match for representative objects.
- **Caller cleanup tests.** Update tests at the call sites so they no longer
  construct the removed value. If a caller test still needs that value, the
  parameter may have represented caller policy.
- **Contract tests for the query.** The source object query now carries more
  responsibility. Test it across boundary values, missing data, and null or
  empty states.
- **Mutation tests for mismatched values.** Before the refactoring, create a
  case where source and derived value disagree. After the refactoring, that
  mismatch should be impossible through the public API.
- **Performance regression tests.** For loops and list pages, count database
  queries or mock calls before and after. A cleaner signature that adds N plus
  1 reads is not a win.
- **Context tests.** If the query uses request context, test the helper inside
  and outside a request. The outside case should fail early with a clear error
  or accept explicit data through another entry point.

Test doubles that apply. Use a simple fake source object for pure queries. Use a
spy query object when you must assert call count. Avoid partial mocks of the
callee because they can hide the dependency move that the refactoring is meant
to expose.

Review checklist after the tests pass.

1. Every removed parameter has exactly one query source.
2. The query source is already in the callee's authority.
3. The query has no observable side effects.
4. The query result is stable for the duration of the call.
5. The query cost is known in loops, batch jobs, and page rendering.
6. The removed parameter was not a policy, mode, snapshot, or override.
7. Tests cover at least one former mismatch case.
8. Logs or traces still contain the derived value when operators need it.
9. Public callers have a compatibility path if the API is published.
10. The new dependency does not block a planned Move Function.

Two regression tests are worth keeping after migration. The first is a contract
test for the query source. It proves that the source object can answer the
question for normal, empty, boundary, and invalid states. The second is a caller
test that constructs only the source object and calls the new signature. That
test prevents future code from rebuilding the removed value and passing it
through another helper, which would recreate the same duplication under a new
name.

## 16. Observability signals

Engineering judgement. Observability should make the hidden query visible
without recreating the old public parameter.

Record these signals when the derived value affects routing, money, permission,
or data selection.

- A debug log or span attribute with the queried value, using bounded
  cardinality labels where possible.
- A counter for calls by source type or context type, so operators can see which
  path supplied the value.
- A histogram around the query when it can touch storage, parse data, or consult
  a cache.
- A counter for fallback or missing value paths.
- During migration, a mismatch counter for old parameter versus queried value.
  It should stay at zero before the parameter is removed.

A healthy dashboard shows stable call counts and stable query latency after the
signature change. A failing dashboard shows higher query latency, a new error
rate for missing context, or a mismatch counter above zero during migration.
For request context variants, a useful alert is "context access outside request
scope," because that marks helper code that escaped the web request lifecycle.

## 17. Security and privacy implications

Engineering judgement. The refactoring is security neutral in pure domain code,
but three implications appear near identity, request data, and logging.

First, it can close a spoofing hole. A function that receives both `request` and
`user` can be called with a valid request and a different user. Querying the
user from the request removes that mismatch if the request object is trusted.
Django's authentication middleware source sets `request.user` from the request
and session machinery
(https://github.com/django/django/blob/main/django/contrib/auth/middleware.py,
verified 2026-08-02), which is why Django admin hooks can use the request as
the authority.

Second, it can open a hidden dependency on sensitive data. A helper that once
received `isAdmin` may now query an entire user record. That can widen data
access and make audit logs less clear. Keep explicit parameters at trust
boundaries unless the richer object is already part of the callee's authority.

Third, telemetry can leak the queried value. Dimension 16 recommends logging
derived values when they matter, but values such as account tier, location,
email domain, user id, or tenant id may be personal or commercially sensitive.
Hash, bucket, or omit values according to the system's privacy policy. Do not
turn a removed parameter into a new high cardinality log label without review.

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 1st
   edition. Addison-Wesley, 1999. Chapter 10, "Making Method Calls Simpler,"
   section "Replace Parameter with Method." Source for the original name and
   first edition placement.
2. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
   edition. Addison-Wesley, 2018. Chapter 11, "Refactoring APIs," section
   "Replace Parameter with Query," page 324. Page confirmed through the
   InformIT excerpt cited below.
3. Martin Fowler. "Replace Parameter with Query."
   https://refactoring.com/catalog/replaceParameterWithQuery.html
   Verified 2026-08-02. Source for the public catalog name, example shape,
   alias, and inverse link.
4. Martin Fowler. "Replace Query with Parameter."
   https://refactoring.com/catalog/replaceQueryWithParameter.html
   Verified 2026-08-02. Source for the inverse refactoring.
5. Martin Fowler. "Changes for the 2nd Edition of Refactoring."
   https://martinfowler.com/articles/refactoring-2nd-changes.html
   Verified 2026-08-02. Source for the rename from Replace Parameter with
   Method to Replace Parameter with Query.
6. Martin Fowler and Kent Beck. "Long Parameter List," excerpt from
   *Refactoring. Improving the Design of Existing Code*, 2nd edition.
   https://www.informit.com/articles/article.aspx?p=2952392&seqNum=4
   Verified 2026-08-02. Source for the Long Parameter List connection and page
   references to Replace Parameter with Query, Preserve Whole Object, Introduce
   Parameter Object, and Remove Flag Argument.
7. Martin Fowler. "Command Query Separation."
   https://martinfowler.com/bliki/CommandQuerySeparation.html
   Verified 2026-08-02. Source for the query and command terminology and
   attribution to Bertrand Meyer.
8. Pallets. "The Request Context," Flask Documentation 3.1.x.
   https://flask.palletsprojects.com/en/stable/reqcontext/
   Verified 2026-08-02. Source for Flask request and session proxies.
9. Ruby on Rails. "ActionController::Base."
   https://api.rubyonrails.org/classes/ActionController/Base.html
   Verified 2026-08-02. Source for Rails controller accessors for params,
   session data, and request data.
10. Django Software Foundation. "The Django admin site," Django documentation.
    https://docs.djangoproject.com/en/6.0/ref/contrib/admin/
    Verified 2026-08-02. Source for `ModelAdmin.has_change_permission(request,
    obj=None)` and admin middleware requirements.
11. Django Software Foundation. `django.contrib.auth.middleware`, Django source.
    https://github.com/django/django/blob/main/django/contrib/auth/middleware.py
    Verified 2026-08-02. Source for `AuthenticationMiddleware` assigning
    `request.user`.

## Code examples

The examples use TypeScript, Python, and Go. They are small enough to run
without framework setup and show the same change in three type systems.

### TypeScript

```typescript
type Customer = {
  id: string;
  loyaltyTier: "standard" | "gold";
};

type Order = {
  customer: Customer;
  subtotal: number;
};

function discountRate(order: Order): number {
  return order.customer.loyaltyTier === "gold" ? 0.15 : 0;
}

function totalAfterDiscount(order: Order): number {
  const rate = discountRate(order);
  return order.subtotal * (1 - rate);
}

const order: Order = {
  customer: { id: "c1", loyaltyTier: "gold" },
  subtotal: 200,
};

console.log(totalAfterDiscount(order).toFixed(2));
```

Before the refactoring, the signature would be
`totalAfterDiscount(order, discountRate(order))`. The revised function asks the
order for the rate source itself, so the caller cannot pass a gold customer with
a standard discount rate.

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Employee:
    grade: str
    years: int


def allowance_weeks(employee: Employee) -> int:
    grade = employee.grade
    base = 4 if grade == "senior" else 3
    return base + (1 if employee.years >= 10 else 0)


if __name__ == "__main__":
    print(allowance_weeks(Employee(grade="senior", years=12)))
```

The removed parameter would have been `grade`. Keeping only `employee` makes the
grade and years come from the same source record.

### Go

```go
package main

import "fmt"

type Account struct {
	Region string
	Plan   string
}

func taxRegion(account Account) string {
	if account.Region == "" {
		return "domestic"
	}
	return account.Region
}

func invoiceLabel(account Account) string {
	region := taxRegion(account)
	return fmt.Sprintf("%s-%s", region, account.Plan)
}

func main() {
	account := Account{Region: "eu", Plan: "pro"}
	fmt.Println(invoiceLabel(account))
}
```

The Go version keeps the query as a free function because that is idiomatic for
a small value type in many packages. A method `account.TaxRegion()` would be
equally valid when the query belongs to the type's public contract.
