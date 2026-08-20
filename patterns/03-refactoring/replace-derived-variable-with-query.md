---
name: Replace Derived Variable with Query
slug: replace-derived-variable-with-query
family: 03-refactoring
category: Refactoring
aliases: [Replace Derived State with Query, Replace Cached Derived Value with Query]
first_described: "Fowler 2018"
maturity: canonical
related: [inline-variable, extract-function, encapsulate-variable, split-variable, separate-query-from-modifier, combine-functions-into-transform]
incompatible_with: []
verified: 2026-08-02
---

# Replace Derived Variable with Query

## 1. Name, aliases, and lineage

The canonical name is **Replace Derived Variable with Query**. Martin Fowler
lists it in his public refactoring catalog and shows the move from a stored
`discountedTotal` field, updated when `discount` changes, to a getter that
calculates the value from `baseTotal` and `discount`
(https://refactoring.com/catalog/replaceDerivedVariableWithQuery.html, verified
2026-08-02). Fowler's public note about the 2018 catalog update says the
catalog entries on refactoring.com are the refactorings from the second edition
book (https://martinfowler.com/articles/201811-update-refactoring-com.html,
verified 2026-08-02). The book citation is Martin Fowler, *Refactoring.
Improving the Design of Existing Code*, 2nd edition, Addison-Wesley, 2018,
chapter 9, "Organizing Data."

The common aliases are **Replace Derived State with Query** and **Replace
Cached Derived Value with Query**. The first alias appears most often in user
interface state work. React's learning material has a named principle,
"Avoid redundant state," and says calculated information from props or current
state should not be stored in component state
(https://react.dev/learn/choosing-the-state-structure, verified 2026-08-02).
The second alias appears in data stores and domain models, where the derived
value may have started life as a cache for speed rather than as UI state.

This refactoring is related to older advice on database normalization and
derived attributes, but its software design shape is narrower. It applies when
a program stores a value that can be calculated from other values already held
by the same object, record, component, aggregate, or store. The replacement is a
query in the broad refactoring sense: a side effect free operation that answers
a question from current source data. It may be a getter, method, selector,
computed property, SQL expression, view, or pure function.

The name can mislead if read too broadly. It does not say "delete every cache."
It says to remove the stored value when the storage mainly exists because the
code has not yet been shaped around a reliable query. A cache whose invalidation
contract is explicit, measured, and needed for latency is a different design
choice. Engineering judgement. The test for this entry is not moral purity
about state. It is whether a stored derived value is making change harder than
recalculation would.

## 2. Problem and context

You have two facts in memory. One is source data. The other is calculated from
that source data. The code stores both, and every update path must keep them in
agreement. At first this looks harmless. A class keeps `subtotal`, `discount`,
and `total`. A React component stores `firstName`, `lastName`, and `fullName`.
A Redux slice stores all todos and a second array of completed todos. A domain
object stores line items and a line count. Then a new update path changes the
source and forgets to update the derived value. The next read returns a value
that used to be true.

The context is refactoring, so the goal is behavior preservation while the
internal representation changes. The user-visible behavior should stay the
same for valid states. The invalid states become impossible or much harder to
represent. Instead of writing source data and derived data together, the code
writes source data only. The derived value is calculated at the read boundary.

The typical smell has this shape.

- A field, state variable, or column is never entered by a user and never
  received as authoritative data from outside the boundary.
- Its value can be expressed as a deterministic calculation over nearby source
  values.
- Several commands or event handlers update the source values.
- Every one of those commands or handlers also contains small synchronization
  logic for the derived value.
- A bug report describes stale output after one particular edit path, retry
  path, undo path, or import path.

The refactoring changes the question from "Did every writer remember the
secondary assignment?" to "Can the reader calculate the answer from current
source data?" That is a large shift in failure shape. A forgotten write becomes
unrepresentable because there is no secondary write. The remaining risks move
to query cost, query purity, and clarity of the source data.

The pattern is most valuable where writes have multiplied. One setter can keep
two fields aligned. Ten mutation paths cannot be trusted by inspection, and the
cost rises when teams add features in parallel. It is also valuable in UI code,
because rendering already asks a question of current state. React's "You Might
Not Need an Effect" guide shows this as removing a state variable and an effect
that recalculates `fullName` after `firstName` or `lastName` changes; the
replacement calculates `fullName` during rendering
(https://react.dev/learn/you-might-not-need-an-effect, verified 2026-08-02).

This refactoring is not a request to make queries huge. If the formula is
complex, extract a named query. If it is reused, move it behind a method or
selector. If it is expensive and measured on a hot path, use memoization with
clear invalidation. The core move remains the same: the source of truth is the
minimal source data, not a second copy of its consequence.

## 3. Forces

Engineering judgement. The exact balance depends on mutation frequency, read
frequency, runtime cost, team ownership, and the observability model.

- **Consistency.** This refactoring strongly favors consistency. A query reads
  current source data, so it cannot be stale unless the source data itself is
  stale or the query is wrong. The sacrificed side is that a stored value can
  represent a deliberately frozen snapshot, and replacing it with a live query
  would remove that snapshot meaning.
- **Coupling.** It favors lower coupling among writers. Commands no longer need
  to know which derived values depend on the fields they change. It may raise
  coupling at read sites if many readers now know the formula, which is why the
  formula should usually be named once.
- **Latency.** It sacrifices read latency when the query is costly and reads are
  frequent. It favors write latency and write simplicity because writes update
  fewer fields. Memoized query variants trade memory and invalidation rules for
  read speed.
- **Cognitive load.** It favors readers who want one source of truth. It
  sacrifices the local simplicity of seeing a stored field. A reader must know
  that a method or property is derived, and must inspect the query when the
  formula matters.
- **Operability.** It favors diagnosis of stale-data incidents because there is
  one state value less to inspect. It sacrifices direct metric visibility if
  the stored value was queried by dashboards, exported in snapshots, or used as
  a cheap audit field.
- **Cost.** It favors maintenance cost when many update paths exist. It may
  raise CPU cost when derived values are expensive and accessed at high volume.
  It can also raise database cost if a query replaces a denormalized column
  without indexes or materialization.
- **Team topology.** It favors teams that own source data and derived behavior
  together. It can be difficult when one team owns writes and another team owns
  read models, because the storage boundary may be part of a contract rather
  than an implementation detail.
- **Change safety.** It favors local changes to formulas. A formula changes in
  one query rather than in every mutation path. It sacrifices easy historical
  reconstruction if past stored values represented the rule that was true when
  the event occurred.

The pattern pays for itself when the strongest risk is divergence. It loses
when the stored value is a required snapshot, a measured performance cache, or
an integration contract.

## 4. Applicability and non-applicability

**Reach for this refactoring when the following hold.**

- The variable is fully derivable from source data that is already available
  within the same consistency boundary.
- The formula is deterministic for the lifetime of the read. It does not depend
  on the current clock, random data, remote calls, process-local mutable state,
  or a database read outside the object being queried.
- Several write paths must update both the source value and the derived value.
- Bugs or tests show stale derived values after partial updates, retries,
  undo operations, imports, merges, or optimistic UI changes.
- The derived value is read often enough to deserve a name, but not so costly
  that every read must use a stored cache.
- The stored value is not part of an external contract. Removing it will not
  break a serialized format, database migration policy, public API, or audit
  trail.
- A query name can express the domain concept better than a synchronization
  assignment can.

**Do NOT reach for this refactoring, and treat the case as non-applicability,
when the following hold.**

- **The value is a historical snapshot.** An invoice total, exchange rate,
  signed amount, tax basis, or approval score may need to preserve what was
  true at a business event. A live query would rewrite history when source
  data changes later. Store the snapshot and name it as a snapshot.
- **The source data is outside the same consistency boundary.** If calculating
  the value requires another service, a remote database, or a current market
  feed, the query may fail or change between reads. Store the value when the
  business action needs a stable answer.
- **The derived value is a measured hot-path cache.** If profiling shows the
  formula dominates request time, keep a cache or materialized value. Make the
  invalidation contract explicit and test it.
- **The value is indexed for search or filtering.** A database may store a
  denormalized field because queries need an index. Replace with a query only
  when the database can compute and index the expression, or when read volume
  allows it.
- **The field is an integration contract.** External clients may depend on a
  JSON field or column even if it is derived. Keep the outward field and
  compute it at serialization, or deprecate it with a versioned migration.
- **The formula has side effects.** A query that logs billing events, opens a
  socket, mutates a cache without bounds, or fetches remote data is not a
  query. First separate query from modifier.
- **The calculation is nondeterministic by design.** Values based on `now`,
  random choice, process uptime, or sequence numbers should not be recomputed
  each time unless changing answers are intended.
- **The code needs independent override.** If operators or users can manually
  adjust the value away from its formula, it is not derived. Model it as source
  data with validation, not as a query result.
- **The stored value is used for forensic recovery.** Some systems store both
  source inputs and the calculated answer so later audits can detect defects in
  old formulas. In that case, store it as an audit artifact and avoid calling
  it derived state.

## 5. Structure

The refactoring has five participants.

- **Source data.** The fields, state variables, collection, event stream, or
  record values that hold authoritative facts. Writers change these values.
- **Derived variable.** The stored value calculated from source data. Before
  the refactoring, writers keep it synchronized by assignment. After the
  refactoring, this participant is removed or kept only as a backward
  compatible serialization field.
- **Synchronizing writers.** Setters, reducers, command handlers, migrations,
  event handlers, or import code that update source data and then update the
  derived variable. These are the places where stale-value bugs enter.
- **Query.** A side effect free operation that calculates the derived answer
  from current source data. It may be a getter, method, selector, computed
  property, SQL expression, view, or pure function.
- **Readers.** Code that needs the derived answer. Readers move from reading
  the stored variable to calling the query. In UI code, the render function is
  often the reader. In domain code, reports, validators, and policy checks are
  common readers.

Relationships before the refactoring are write-heavy. Every writer must know
that changing source data also requires changing the derived variable.
Relationships after the refactoring are read-oriented. Writers know only source
data. Readers ask the query. The query knows the formula.

The query belongs as close as possible to the source data without crossing a
module boundary that would make dependencies worse. On an object, a getter or
method is natural. In Redux, official docs describe selectors as functions that
take state and return data based on it, including derived values
(https://redux.js.org/usage/deriving-data-selectors, verified 2026-08-02). In
Vue, computed properties are query-like values that track reactive dependencies
and update dependent bindings when those dependencies change
(https://vuejs.org/guide/essentials/computed, verified 2026-08-02).

## 6. ASCII structure diagram

```
Before

   +--------------------+        updates        +--------------------+
   | Synchronizing      | ---------------------> | Source data        |
   | writer             |                        | base, discount     |
   +--------------------+                        +--------------------+
             |
             | also updates
             v
   +--------------------+        read by        +--------------------+
   | Derived variable   | <-------------------- | Readers            |
   | discounted_total   |                       | reports, UI, rules |
   +--------------------+                       +--------------------+

Risk

   writer path A updates source and derived value
   writer path B updates source only
   readers cannot tell which path produced the state

After

   +--------------------+        updates        +--------------------+
   | Writer             | ---------------------> | Source data        |
   |                    |                        | base, discount     |
   +--------------------+                        +--------------------+
                                                        |
                                                        | read by
                                                        v
   +--------------------+        calls          +--------------------+
   | Readers            | ---------------------> | Query              |
   | reports, UI, rules |                       | base - discount    |
   +--------------------+                       +--------------------+

Only source data is stored. The derived value is calculated when asked.
```

## 7. Dynamics

The runtime change is easiest to see on an update followed by a read. Before
the refactoring, the update path performs two writes. After the refactoring,
the update path performs one write and the read performs the calculation.

```
Before

Client        Writer              Source data          Derived variable
  |             |                       |                       |
  | setDiscount |                       |                       |
  |------------>|                       |                       |
  |             | write discount        |                       |
  |             |---------------------->|                       |
  |             | calculate total       |                       |
  |             |---------------------------------------------->|
  |             |                       |                       |
  | read total  |                       |                       |
  |------------------------------------------------------------>|
  |<------------------------------------------------------------|

After

Client        Writer              Source data          Query
  |             |                       |                 |
  | setDiscount |                       |                 |
  |------------>|                       |                 |
  |             | write discount        |                 |
  |             |---------------------->|                 |
  |             |                       |                 |
  | read total  |                       |                 |
  |----------------------------------------------------->|
  |             |                       | read base       |
  |             |                       |<----------------|
  |             |                       | read discount   |
  |             |                       |<----------------|
  |<-----------------------------------------------------|

Failure removed

Before, a writer can forget the second write. After, there is no second write.
```

A memoized query adds one more step. The query first compares the current source
inputs with the cached inputs. If the inputs match, it returns the cached answer.
If they differ, it recalculates and replaces the cached answer. Redux documents
this shape for memoized selectors built with Reselect: input selectors produce
values, and the output selector can skip work when the inputs match the prior
call (https://redux.js.org/usage/deriving-data-selectors, verified 2026-08-02).

## 8. Implementation variants

**Getter or computed property.** The derived value remains property-like at the
read site. `order.total` reads better than `order.calculate_total()` when the
operation is cheap, deterministic, and side effect free. This is idiomatic in
TypeScript, Python, Swift, and Java records or classes with accessor methods.
The cost is that property syntax can hide expensive work. Use a method name
when readers need to notice cost.

**Named method.** A method such as `total()` or `discountedTotal()` makes the
query visible as behavior. This is common in Java, Go, and Rust, where methods
make ownership clear. The cost is slightly more call-site syntax.

**Pure selector function.** The query is a function outside the data structure:
`selectVisibleTodos(state)`. Redux calls selectors a standard, widely used
pattern and describes them as functions that can derive values from state
(https://redux.js.org/usage/deriving-data-selectors, verified 2026-08-02). This
variant works well when state is a plain tree and behavior is organized by
module rather than by object.

**Memoized selector.** The query stores its last inputs and output. This keeps
the source of truth minimal while avoiding repeated expensive derivation. React
Redux's `useSelector` docs state that selectors may return derived values and
that the hook compares prior and current selector results by strict reference
equality by default (https://react-redux.js.org/api/hooks, verified
2026-08-02). The cost is cache invalidation, reference stability, and memory
shape. Memoization is a performance tool, not a license to hide mutation.

**Reactive computed value.** Vue computed properties track reactive
dependencies and cache based on those dependencies
(https://vuejs.org/guide/essentials/computed, verified 2026-08-02). This is a
framework-provided query cache. It fits UI derivations such as filtered lists,
labels, and enablement flags. It does not fit values with side effects.

**Database generated column or view.** The derived value is moved out of
application writes and into a database expression. This is still a query from
the application perspective, but storage engines may materialize or index it.
Use this when the formula belongs with relational data and must be shared by
several services. The cost is migration complexity and vendor-specific SQL.

**Read model materialization.** Event-sourced and CQRS systems may keep a
materialized projection because read volume or query shape demands it. This is
not the pure version of the refactoring. It is the performance-oriented exit
from it. The rule is to name the projection as a projection, give it a rebuild
path, and measure lag.

**Serialization-only field.** A public API may still emit the derived field for
compatibility. Internally the field is gone; the serializer calls the query.
This variant lets clients keep their contract while the domain model stops
storing redundant state.

## 9. Known production uses

**React component state.** React's official guide "Choosing the State
Structure" tells developers to avoid redundant state and not store information
that can be calculated from props or existing state during rendering
(https://react.dev/learn/choosing-the-state-structure, verified 2026-08-02).
The same docs show `fullName` removed from component state and calculated from
`firstName` and `lastName`. This is the UI-state form of Replace Derived
Variable with Query.

**React effects.** React's guide "You Might Not Need an Effect" shows a form
that stores `fullName` and uses an effect to update it after `firstName` or
`lastName` changes. The guide replaces that state and effect with a render-time
calculation, and says this avoids a stale render followed by a second render
(https://react.dev/learn/you-might-not-need-an-effect, verified 2026-08-02).
That is the same refactoring applied to effect-managed derived state.

**Redux selectors and Reselect.** Redux's official usage guide recommends
keeping Redux state minimal and deriving values from state when possible, with
selector functions as the usual place for derivation. The same page describes
memoized selectors with Reselect and explains that `createSelector` can return a
cached result when input selector values match the prior call
(https://redux.js.org/usage/deriving-data-selectors, verified 2026-08-02).
This is the store-level form of the pattern.

**Vue computed properties.** Vue's official guide describes computed properties
as getter-based values that track their reactive dependencies. It says a
computed property updates bindings that depend on it when its dependencies
change, and that computed properties are cached based on reactive dependencies
(https://vuejs.org/guide/essentials/computed, verified 2026-08-02). This is a
framework-supported derived query over reactive source state.

These examples are named production frameworks, not sample apps. They show the
same move at different scales: local component state in React, application
store state in Redux, and reactive component data in Vue.

## 10. Consequences

Engineering judgement. The following effects are typical outcomes, not laws.

Positive.

- One source of truth replaces a pair of values that could disagree.
- Writers become shorter. They mutate source data and stop carrying
  synchronization logic for every derived value.
- Invalid states disappear when they existed only because the derived variable
  could lag behind source data.
- Formula changes move to one named query instead of every update path.
- Tests can assert the query directly against source data, without constructing
  many mutation histories to prove the stored value stays aligned.
- UI code often renders fewer stale intermediate states because it calculates
  current answers during render rather than waiting for a later update.
- Serialization can keep the same outward field while internal storage becomes
  smaller and easier to reason about.

Negative.

- Reads can become more expensive. A stored value is one memory read. A query
  may scan a collection, sort, filter, allocate, or touch a database.
- A property-like query can hide work behind innocent syntax.
- Expensive derivations may need memoization, which reintroduces cache state and
  invalidation concerns.
- Debugging may lose an inspectable field. The answer exists only when the
  debugger evaluates the query.
- Historical snapshots can be lost if the value was mistakenly treated as
  derived even though the business needed the old answer.
- External contracts may still require the field, so the implementation must
  keep compatibility at the boundary.
- Query logic can become duplicated if the formula is inlined at many readers
  rather than named once.

## 11. Failure modes and misuse

Engineering judgement. Each item gives an observable symptom, likely cause, and
fix.

**Stale dashboard total.** Symptom. A user edits a line item, the line list
shows the new amount, but the displayed total stays old until a reload. Cause.
The update path changed the source collection and forgot to update the stored
total. Fix. Delete the stored total and calculate it from the line items in a
getter, selector, or computed property.

**Double-render flicker.** Symptom. A React component briefly renders a stale
label, then renders again with the corrected label after an effect runs. Cause.
The label is stored as state and recalculated in an effect after source state
changes. Fix. Calculate the label during render, or use memoization only for an
expensive calculation.

**Memoization hides mutation.** Symptom. A selector keeps returning an old list
even though a nested object was mutated. Cause. The memoized query compares
input references, and source data was mutated in place. Fix. Use immutable
updates or change the memoization inputs so the changed value participates in
the cache key.

**Query turns into a command.** Symptom. Reading `total` writes a cache row,
updates `lastViewedAt`, emits an event, or changes logs at high volume. Cause.
The replacement query was allowed to do side effects. Fix. Apply Separate Query
from Modifier. Move writes to an explicit command, and keep the query pure.

**Hot read regression.** Symptom. CPU rises after deployment, with profiles
showing repeated sorting or filtering in a getter. Cause. A stored derived value
was removed without measuring read frequency or calculation cost. Fix. Add a
memoized query, precompute at a batch boundary, or keep a materialized read
model with tested invalidation.

**Snapshot rewritten by live data.** Symptom. Old invoices change total after a
customer record, tax table, or discount rule changes. Cause. The stored
business snapshot was misclassified as redundant derived data. Fix. Restore the
snapshot field, give it a name such as `totalAtIssue`, and calculate only
preview or draft totals from current source data.

**Duplicated query formula.** Symptom. Three screens show three different
answers for what the team calls the same concept. Cause. Developers removed the
stored field but copied the formula into each reader. Fix. Create one named
query in the owning module and route all readers through it.

**Database read explosion.** Symptom. A page that listed 100 records now issues
101 database queries. Cause. The replacement query calls the database per
record instead of calculating from already loaded source data. Fix. Batch-load
source data, move the calculation into SQL, or materialize a read model.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Replace Derived Variable with Query | Encapsulate Variable | Memoized Selector | Materialized View | Event-Sourced Projection | Keep Snapshot Field |
|---|---|---|---|---|---|---|
| Consistency | Strong. No secondary stored value | Medium. Writes can be guarded | Strong if inputs are immutable | Strong after refresh | Eventual, depends on lag | Strong for history, not live data |
| Read latency | Depends on formula cost | Fast if field is stored | Fast on cache hit | Fast for supported queries | Fast for projection reads | Fast |
| Write latency | Low, fewer writes | Medium, guarded write | Low for source write | May pay refresh cost | Writes events, projection later | Medium, source plus snapshot |
| Coupling | Writers know less | Writers call setter API | Readers depend on selector | App depends on database feature | Readers depend on projection schema | Business code owns snapshot rule |
| Cognitive load | One source of truth, query to inspect | Hidden update rules | Cache rules to understand | SQL or database behavior to inspect | Projection lag and rebuilds | Distinguish live value from snapshot |
| Operability | Track query cost and errors | Track setter paths | Track cache hit rate | Track refresh age and failures | Track lag and replay health | Track audit policy |
| Team topology | Best inside one owning module | Good for shared mutable object | Good for UI or store team | Good with database ownership | Good with platform event ownership | Good with finance or audit ownership |
| Cost of change | Formula changes in one query | Setter changes in one API | Formula plus cache behavior | Migration and index work | Projection versioning and replay | Migration and audit changes |

Reading of the table. Replace Derived Variable with Query is the clearest move
when the value is live, deterministic, and cheap enough to calculate. Encapsulate
Variable is an intermediate step when callers still write the field directly.
Memoized Selector keeps the source model minimal while addressing expensive
reads. Materialized View and Event-Sourced Projection are read-optimized
alternatives when query cost or query shape exceeds application-level
calculation. Keep Snapshot Field wins when the value is part of the business
record rather than a redundant cache.

## 13. Related and incompatible patterns

- **Encapsulate Variable.** Often comes first. If callers write both source data
  and the derived field directly, wrap the fields so updates pass through a
  controlled API. Once the write paths are visible, remove the derived storage.
- **Inline Variable.** A small local derived variable that is used once may be
  inlined instead of promoted to a query. Inline Variable removes an unhelpful
  name. Replace Derived Variable with Query removes unhelpful storage.
- **Extract Function.** A derived formula that is repeated at readers should be
  extracted into a named function or method. This is how the query becomes one
  reusable concept rather than copied arithmetic.
- **Separate Query from Modifier.** A replacement query must not mutate state.
  If the calculation currently writes caches, counters, or audit events, split
  those writes out before trusting the query as a read.
- **Combine Functions into Transform.** When many derived values are needed
  together for a report or API response, a transform can calculate them in one
  pass from the source record. This avoids many separate queries scanning the
  same data.
- **Memoization.** Composes with the refactoring when recalculation cost is
  real. It also conflicts when used as a silent return to stored derived state.
  The cache must be treated as a performance detail with clear invalidation.
- **CQRS and Projection.** A projection is a deliberate derived read model. It
  replaces the pure query when read volume, query language, or service
  boundaries make live calculation too costly. It must have replay and lag
  monitoring.
- **Snapshot Field.** This actively conflicts when the value is historical. A
  snapshot field says, "store the answer that was true at this event." A live
  query says, "calculate the answer from current source data." Mixing the two
  names causes accounting and audit defects.

## 14. Refactoring path in and out

Introducing the pattern into code that stores a derived value.

1. Identify the source fields and write the formula in one place as a private
   query. Do not remove the stored field yet.
2. Add characterization tests around current behavior. Include the update paths
   most likely to have caused stale values: edit, delete, undo, import, retry,
   and bulk update.
3. Compare the stored field with the query in tests. If they disagree, decide
   whether the query is wrong, the stored value is stale, or the value is really
   a snapshot.
4. Replace internal readers with the query. Keep the stored field temporarily
   for compatibility and comparison.
5. Remove synchronization assignments from writers one at a time. After each
   removal, run the tests that cover that writer.
6. Delete the stored field from the internal model. If the field exists in a
   database or API, keep serialization compatibility by calculating it at the
   boundary until a migration removes it.
7. If the query is expensive, measure before adding memoization. Add a cache
   only with tests for invalidation or input identity.
8. Remove stale tests that asserted the old synchronization assignments, and
   add direct query tests over source data.

Refactoring out when the query stops earning its place.

1. Confirm the reason. Common reasons are measured read cost, external API
   compatibility, indexed search, or historical snapshot requirements.
2. Give the stored value a precise name. Use `cachedTotal`, `indexedTotal`, or
   `totalAtIssue` rather than `total` when that distinction matters.
3. Encapsulate writes through one command, reducer, trigger, or projection
   builder. Do not scatter synchronization assignments across readers and
   writers.
4. Add tests that mutate every source input and assert the stored value changes
   or deliberately stays fixed, depending on the contract.
5. Add observability for stale age, projection lag, or cache hit rate.
6. Keep the query as a verification function when possible. In tests or
   background checks, compare stored values against recalculation to detect
   drift.

Cross references in the refactoring family. Encapsulate Variable prepares the
field for controlled change. Extract Function names the formula. Inline
Variable handles local single-use derivations. Separate Query from Modifier
cleans up calculations that write. Combine Functions into Transform is the
batch form when several derived values are needed together.

## 15. Testing and verification

Engineering judgement. Testing should prove two things: the formula is correct,
and the old stale-state failure cannot reappear through normal writes.

Easier because of the pattern.

- Query tests are direct. Build source data, call the query, assert the answer.
- Mutation-path tests become shorter because they no longer assert every
  synchronized value after every write.
- Property tests work well. Generate source records, calculate a reference
  answer with a simple independent function, and compare the query.
- UI tests no longer need to wait for a second state update when the derived
  value is calculated during render.
- Serializer tests can verify that a removed internal field is still emitted
  for compatibility when needed.

Harder because of the pattern.

- Performance must be tested or profiled for expensive derivations. A correct
  query can still be too slow.
- Memoized queries need tests for identity and invalidation. Mutating an input
  in place should be caught if the cache depends on references.
- Historical behavior needs explicit tests. A draft total may be live, while an
  issued invoice total must stay fixed.
- Debugging a missing stored field requires evaluating the query or logging its
  inputs and output.

Test techniques that apply.

- **Golden formula tests.** Give the query a small table of source inputs and
  expected outputs. Include zero, empty collection, rounding, null or missing
  value, and boundary cases.
- **Mutation coverage tests.** For each command that changes source data, assert
  the query answer after the command. This proves writers no longer need
  secondary assignments.
- **Invariance tests.** Assert properties such as `remaining = total - done`,
  or `fullName` changes when either name changes. This catches partial update
  paths.
- **Cache behavior tests.** For memoized selectors, assert same inputs return
  the same reference when that contract matters, and changed inputs recalculate.
- **Migration tests.** When deleting a database column or state field, load an
  old fixture, migrate it, and verify the query answer matches the old outward
  value where compatibility requires it.

Verification for this entry. The TypeScript, Python, Go, and Rust samples below
were run locally with `npx tsc`, `python3`, `go run`, and `rustc`.

## 16. Observability signals

Engineering judgement. The pattern makes stale derived storage disappear, but
it can move cost to read time. Observability should watch correctness at
boundaries and cost at query execution.

What to record.

- Query duration for any derived value that scans collections, sorts, filters,
  or touches storage.
- Query invocation count by query name and caller. A query that was cheap in
  one place can become expensive when called inside a loop.
- Cache hit rate, miss rate, eviction count, and cache size for memoized
  variants.
- Projection lag or materialized-view freshness when the design exits to a
  stored read model.
- Drift checks during migration. While both stored and queried values exist,
  compare them in a background job or sampled log and count disagreements.
- Serialization compatibility checks. Count requests or clients that still read
  a derived field scheduled for removal.

A healthy instance. Query latency is flat and small compared with the enclosing
operation. Cache hit rate is stable where memoization exists. Drift count is
zero during the migration window. UI traces show one render for source updates
that formerly caused a stale render followed by a correction. Projection lag is
bounded and visible if a materialized alternative is used.

A failing instance. Query latency grows with collection size and becomes the top
CPU consumer. A selector allocates a new array for every store update and causes
wide rerenders. Cache size rises without bound. Drift checks find stored values
that disagree with the query during migration. A live query appears in an audit
path where a snapshot was required. These signals do not mean the refactoring
was wrong in all places. They tell you which variant is wrong for the workload.

## 17. Security and privacy implications

Engineering judgement. The core refactoring is mostly silent on security. It
removes redundant mutable state, which can reduce stale authorization or stale
privacy labels, but it can also expose new timing and data-boundary concerns.

**Authorization derived from current facts.** If access is stored as a derived
boolean, for example `canViewReport`, it can become stale after a role, tenant,
or document owner changes. Replacing it with a query over current authorization
facts reduces that stale-permission risk. The query must run inside the same
trusted boundary as the authorization facts.

**Historical authorization decisions.** Some decisions must be logged as facts:
who approved, which policy version applied, and what answer was given at that
time. Do not replace those with live queries. Keep the audit record and name it
as an audit record.

**Privacy labels and data residency.** A stored derived privacy label can lag
behind source data classification. A query over current labels can reduce that
lag. The risk is that the query may need to inspect fields the caller should not
see. Keep the query in a privileged policy module and return only the derived
answer.

**Side channels through query cost.** If query time depends on hidden data size,
callers may infer facts from latency. This matters most in multi-tenant systems
where the query crosses tenant boundaries or reports counts. Bound the source
data, precompute under a trusted job, or return coarse answers where needed.

**Cache leakage.** Memoized queries can retain data after a request, user, or
tenant context ends. Scope caches to the request or tenant, clear them on
logout, and avoid process-wide caches for values containing personal data.

**Logs.** During migration, drift logs may include both source inputs and
derived outputs. Treat those logs as sensitive when the formula touches personal
data, prices, health data, permissions, or location. Log identifiers and counts
where possible instead of raw inputs.

## Code examples

Four languages are shown because the refactoring is idiomatic across object,
function, and method-oriented styles. TypeScript shows UI/store style. Python
shows a property on a domain object. Go shows a method over a struct. Rust shows
a side effect free method over owned data.

### TypeScript

```typescript
type Line = { sku: string; cents: number; quantity: number };

class CartBefore {
  private totalCents = 0;

  constructor(private lines: Line[]) {
    this.totalCents = this.lines.reduce(
      (sum, line) => sum + line.cents * line.quantity,
      0,
    );
  }

  changeQuantity(sku: string, quantity: number): void {
    this.lines = this.lines.map((line) =>
      line.sku === sku ? { ...line, quantity } : line,
    );
    this.totalCents = this.lines.reduce(
      (sum, line) => sum + line.cents * line.quantity,
      0,
    );
  }

  total(): number {
    return this.totalCents;
  }
}

class CartAfter {
  constructor(private lines: Line[]) {}

  changeQuantity(sku: string, quantity: number): void {
    this.lines = this.lines.map((line) =>
      line.sku === sku ? { ...line, quantity } : line,
    );
  }

  total(): number {
    return this.lines.reduce(
      (sum, line) => sum + line.cents * line.quantity,
      0,
    );
  }
}

const cart = new CartAfter([
  { sku: "book", cents: 1500, quantity: 2 },
  { sku: "pen", cents: 200, quantity: 3 },
]);
cart.changeQuantity("pen", 5);
console.log(cart.total());
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Line:
    sku: str
    cents: int
    quantity: int


class Cart:
    def __init__(self, lines: list[Line]) -> None:
        self._lines = list(lines)

    def change_quantity(self, sku: str, quantity: int) -> None:
        self._lines = [
            Line(line.sku, line.cents, quantity)
            if line.sku == sku
            else line
            for line in self._lines
        ]

    @property
    def total_cents(self) -> int:
        return sum(line.cents * line.quantity for line in self._lines)


cart = Cart([Line("book", 1500, 2), Line("pen", 200, 3)])
cart.change_quantity("pen", 5)
print(cart.total_cents)
```

### Go

```go
package main

import "fmt"

type Line struct {
	SKU      string
	Cents    int
	Quantity int
}

type Cart struct {
	lines []Line
}

func (c *Cart) ChangeQuantity(sku string, quantity int) {
	for i := range c.lines {
		if c.lines[i].SKU == sku {
			c.lines[i].Quantity = quantity
		}
	}
}

func (c Cart) TotalCents() int {
	total := 0
	for _, line := range c.lines {
		total += line.Cents * line.Quantity
	}
	return total
}

func main() {
	cart := Cart{lines: []Line{
		{SKU: "book", Cents: 1500, Quantity: 2},
		{SKU: "pen", Cents: 200, Quantity: 3},
	}}
	cart.ChangeQuantity("pen", 5)
	fmt.Println(cart.TotalCents())
}
```

### Rust

```rust
#[derive(Clone)]
struct Line {
    sku: String,
    cents: i32,
    quantity: i32,
}

struct Cart {
    lines: Vec<Line>,
}

impl Cart {
    fn change_quantity(&mut self, sku: &str, quantity: i32) {
        for line in &mut self.lines {
            if line.sku == sku {
                line.quantity = quantity;
            }
        }
    }

    fn total_cents(&self) -> i32 {
        self.lines
            .iter()
            .map(|line| line.cents * line.quantity)
            .sum()
    }
}

fn main() {
    let mut cart = Cart {
        lines: vec![
            Line { sku: "book".to_string(), cents: 1500, quantity: 2 },
            Line { sku: "pen".to_string(), cents: 200, quantity: 3 },
        ],
    };
    cart.change_quantity("pen", 5);
    println!("{}", cart.total_cents());
}
```

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
   edition. Addison-Wesley, 2018. Chapter 9, "Organizing Data." Source for the
   canonical name and refactoring family placement.
2. Martin Fowler. "Replace Derived Variable with Query."
   https://refactoring.com/catalog/replaceDerivedVariableWithQuery.html
   Verified 2026-08-02. Source for the catalog name and public before and after
   example.
3. Martin Fowler. "Update to refactoring.com."
   https://martinfowler.com/articles/201811-update-refactoring-com.html
   Verified 2026-08-02. Source for the statement that the updated public
   catalog tracks the second edition refactorings.
4. Meta Open Source. React documentation, "Choosing the State Structure."
   https://react.dev/learn/choosing-the-state-structure
   Verified 2026-08-02. Source for React's redundant state guidance and the
   `fullName` example.
5. Meta Open Source. React documentation, "You Might Not Need an Effect."
   https://react.dev/learn/you-might-not-need-an-effect
   Verified 2026-08-02. Source for removing effect-managed derived state.
6. Redux documentation. "Deriving Data with Selectors."
   https://redux.js.org/usage/deriving-data-selectors
   Verified 2026-08-02. Source for minimal Redux state, selectors, and Reselect
   memoized selector behavior.
7. React Redux documentation. "Hooks."
   https://react-redux.js.org/api/hooks
   Verified 2026-08-02. Source for `useSelector` derived return values and
   reference comparison behavior.
8. Vue documentation. "Computed Properties."
   https://vuejs.org/guide/essentials/computed
   Verified 2026-08-02. Source for reactive computed values, dependency
   tracking, and computed caching.
