---
name: Replace Temp with Query
slug: replace-temp-with-query
family: 03-refactoring
category: Refactoring
aliases: [Replace Temporary Variable with Query, Replace Temp with Method]
first_described: "Fowler 1999"
maturity: canonical
related: [extract-function, inline-variable, split-variable, replace-query-with-parameter, replace-derived-variable-with-query, separate-query-from-modifier]
incompatible_with: []
verified: 2026-08-02
---

# Replace Temp with Query

## 1. Name, aliases, and lineage

The canonical name is **Replace Temp with Query**. Martin Fowler names the
refactoring in *Refactoring. Improving the Design of Existing Code*, 1st
edition, Addison-Wesley, 1999, chapter 6, "Composing Methods." Fowler's public
errata for that book confirms the mechanics around page 119 and page 120,
including the correction that the right side of the assignment must be checked
for side effects and that references to the temporary are replaced with the new
method, not with the original expression
(https://martinfowler.com/refactoringErrata.html, verified 2026-08-02).

Fowler kept the name in the second edition catalog. His public catalog page
shows a local `basePrice` variable becoming a `basePrice` getter, and the
second edition change list records "Replace Temp with Query" as a kept
refactoring from page 120 of the first edition
(https://refactoring.com/catalog/replaceTempWithQuery.html, verified
2026-08-02; https://martinfowler.com/articles/refactoring-2nd-changes.html,
verified 2026-08-02). The book citation for the current form is Martin Fowler,
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings."

The common aliases are **Replace Temporary Variable with Query** and **Replace
Temp with Method**. The second alias appears in teams that use "method" for
all object operations. This entry uses **query** because it carries an
important constraint. The extracted operation returns information and must not
change observable state. That aligns with command-query separation, a term
Fowler attributes to Bertrand Meyer in his discussion of methods that either
return information or change state
(https://martinfowler.com/bliki/CommandQuerySeparation.html, verified
2026-08-02).

This refactoring is narrower than **Replace Derived Variable with Query**.
Replace Temp with Query removes a local variable inside a method. Replace
Derived Variable with Query removes a stored field or cached state member. The
two refactorings often share code shape, but the risk is different. A local
temp can make extraction awkward and can hide meaning. A stored derived value
can drift away from its source data.

## 2. Problem and context

A method calculates an intermediate value, stores it in a local variable, then
uses that variable in one or more later statements. The variable started as a
kindness to the reader. It gave a name to an expression or avoided repeating a
small calculation. Over time, the method grew around it. Now the assignment is
far from the reads, the local scope is crowded, and a reader must keep the
variable in memory while reading unrelated code.

The pressure becomes sharper when the next refactoring is blocked. A branch,
loop body, or group of statements wants to become its own method, but the
candidate block reads a temp declared earlier. Extract Function now needs an
extra parameter. A second extraction needs the same parameter. A third one
needs the same calculation and introduces a copy. The temp has become a local
anchor that keeps behavior trapped inside the original method.

Replace Temp with Query moves the calculation into a small side-effect-free
method or property, then replaces reads of the temp with calls to that query.
The calling method stops carrying the intermediate state. Other methods on the
same object can ask for the same meaning by name.

The context matters. This is not a campaign against all local variables. A
short-lived local often makes code clearer, especially when it holds the result
of an expensive call, a value that must be captured at one point in time, or a
name that makes a complex expression readable. Replace Temp with Query pays off
when the calculation is stable for the duration of the call, cheap enough to
repeat or easy to memoize, and meaningful enough to deserve a name at object or
module scope.

The best example is a method that calculates a subtotal, threshold, age,
eligibility state, parsed token, selected rate, or normalized path component
from data the object already owns. The query says, "this is a fact about this
object right now." The temp says, "this was a fact at the point where this line
ran." Choosing between those two statements is the core design decision.

The pattern is most valuable in code that is already moving toward smaller
methods. A long method often contains several stages: gather data, derive
facts, decide, then perform an action. Temporary variables blur those stages
when facts from the derivation stage are read in the decision stage and again
in the action stage. Moving a fact into a query does not complete the design,
but it removes one strand from the knot. After that, the decision branch can
often move into a method named after the policy, and the action branch can move
into a command named after the outcome.

A weaker but common context is defensive reading. A reader sees `gross`,
`adjusted`, `candidate`, `effective`, or `result` and has to scan backward to
learn which business rule the name stands for. A query with a precise name can
turn that reverse scan into a direct statement. `eligibleSpend()` says more
than `adjusted`, and `billingCountry()` says more than `country` when the
system has shipping, tax, and legal addresses. The refactoring earns its keep
when the name carries a domain distinction that the assignment line cannot
carry alone.

## 3. Forces

This dimension is engineering judgement. The citations establish lineage and
named examples. The force weighting below is design reasoning.

- **Cognitive load.** Favoured when the extracted query has a strong domain
  name and the original method becomes shorter. Sacrificed when the reader must
  jump between methods to understand a one-line expression.
- **Coupling.** Favoured inside the object or module, because repeated callers
  depend on a named query rather than duplicated expression details. Sacrificed
  if the query is exposed as public API before its meaning is stable.
- **Consistency.** Favoured when the same calculation had started to appear in
  several methods. One query gives one definition. Sacrificed if the query reads
  mutable inputs at different times and callers expected a snapshot.
- **Latency.** Sacrificed when a once-only temp becomes repeated work. Favoured
  when the calculation is cheap, branch-local, or optimized by the compiler.
  If cost matters, add memoization at the query boundary or keep a local after
  the query is extracted.
- **Operability.** Favoured when logs, traces, and tests can refer to the named
  query. Sacrificed when property syntax hides database calls, network calls,
  lock acquisition, or heavy parsing.
- **Cost.** Favoured because future edits change one query instead of several
  local copies. Sacrificed because the first refactoring creates another named
  member and may need tests around it.
- **Team topology.** Favoured when a team owns a domain object and can define
  its own named facts. Sacrificed when many teams consume a public query and a
  small name change becomes an API migration.
- **Debuggability.** Mixed. The query can be breakpointed and tested directly.
  A local temp can be inspected in a debugger without stepping into another
  call. Which one wins depends on the tools and the cost of the expression.
- **API surface.** Favoured when the query remains private and creates a stable
  internal vocabulary. Sacrificed when a private helper becomes public because
  another class wants convenience. A public query invites external dependency
  on a calculation that may have started as a local clean-up step.
- **Temporal precision.** Sacrificed when the old temp intentionally captured a
  point-in-time observation. Favoured when the code always wanted the current
  value and the temp was an accidental stale copy.
- **Refactoring momentum.** Favoured. Many larger moves, including Extract
  Function and Move Function, become easier after local intermediates stop
  pinning behavior to one method body.

The pattern favors clearer extraction and shared meaning. It sacrifices some
locality and, sometimes, the implicit caching that a temp provided.

## 4. Applicability and non-applicability

Reach for Replace Temp with Query when these conditions hold.

- The temp is assigned once and then read. If it is assigned more than once,
  split it first with Split Variable.
- The right side of the assignment is side-effect free. Fowler's errata for the
  first edition explicitly corrects the mechanics to add that check
  (https://martinfowler.com/refactoringErrata.html, verified 2026-08-02).
- The expression explains a domain fact, not a machine detail. `netAmount()`,
  `eligibleForRenewal()`, and `normalizedSku()` are stronger candidates than
  `x()` or `intermediate()`.
- The same expression is needed by a second method, or an Extract Function move
  would otherwise require passing the temp as a parameter.
- The value may be calculated from fields, parameters already held by the
  receiver, or immutable data available to the module.
- The extra call is cheap enough, or the query can own a cache that is easier
  to reason about than scattered local caches.

Do NOT reach for it in these cases.

- **The temp captures a snapshot.** If the code must compare "value before" with
  "value after," a query will read current state and erase the time boundary.
  Keep a local named `previousBalance`, `startedAt`, or `originalOwner`.
- **The calculation has side effects.** A query that sends an email, increments
  a counter, advances an iterator, writes a metric, reads from a socket, or
  mutates hidden state is not a query. Use Separate Query from Modifier first.
- **The expression is expensive and called repeatedly.** Database calls, remote
  requests, filesystem walks, regex compilation, decompression, and large
  aggregations should not hide behind a property. Keep a local, pass a value, or
  make a method whose name signals cost.
- **The value belongs to a narrower scope.** If only two adjacent lines need the
  name, Extract Variable may be clearer. Moving that name to class scope makes
  the object API noisier.
- **The query would need many parameters.** A query with four locals passed in
  is often an Extract Function candidate, not Replace Temp with Query. The
  method has not found a better owner yet.
- **The expression depends on loop iteration state.** A temp inside a loop may
  represent the current element, accumulator, or branch result. Moving it to a
  receiver query can blur which iteration supplied the data.
- **The temp prevents repeated reads of changing data.** A local copy of
  `clock.now()`, `random.next()`, `request.body()`, or `queue.poll()` may be
  intentional. Replacing it with a query changes behavior.
- **The language idiom favors local binding.** In Go, Rust, and Python, a short
  local binding can be clearer than a method when the expression has no domain
  status outside the current function.
- **The query name would lie.** A method named like data but doing policy,
  lookup, or allocation misleads readers. Rename the operation or keep the temp.
- **The temp is part of a transaction script.** Some application-service
  methods read as a deliberate sequence of facts and commands. Extracting every
  intermediate into a query can scatter the story. Prefer keeping locals when
  the method is already short and the sequence itself is the clearest model.
- **The expression is easier to audit inline.** Security checks, financial
  formulas, and migration scripts sometimes benefit from visible arithmetic at
  the point of use. A query is still possible, but it should have tests and
  review ownership that match the audit need.
- **The query would cross an ownership boundary.** If an order method has to
  inspect internal fields of a pricing engine to compute the temp, the new query
  belongs on the pricing engine, not on the order. Use Move Function or Extract
  Class before naming the wrong owner.

## 5. Structure

The participants are small, but their roles must stay separate.

- **Source owner.** The class, module, record, or closure that already owns the
  data needed to compute the value. In an object-oriented design this is often
  `Order`, `Invoice`, `Customer`, or `Path`. In a functional module it may be a
  state value plus a selector function.
- **Original method.** The method that currently declares the temp. It is the
  place where local state is causing friction.
- **Temporary variable.** The local binding assigned from a pure expression. It
  carries the meaning that will become the query name.
- **Query.** A side-effect-free method, property, getter, or function that
  returns the same value the temp held.
- **Call sites.** Reads of the temp inside the original method, and later reads
  from other methods after the query earns broader use.
- **Optional cache.** A private memoized field or local binding inside the query
  when repeated calculation would be too expensive. The cache is not the
  pattern. It is a performance variant that must be governed by invalidation
  rules.

The dependency change is simple. Before the refactoring, later statements
depend on a local variable. After the refactoring, those statements depend on a
named query. If the query reads only stable receiver state, behavior is
unchanged. If it reads volatile state, the refactoring is unsafe until the
volatility is isolated.

There is also a visibility decision. The first query should usually be private.
That keeps the move reversible and prevents a local clean-up from becoming a
published contract. Promote the query only when a second real caller appears
and the name has survived review. In modules rather than classes, the same rule
means keeping the function unexported until another package or directory needs
it for a reason stronger than convenience.

The query should sit near the behavior it serves. In class-based code, place it
with other derived facts, not among mutating commands. In a module, group it
with selectors or read-only helpers. This makes accidental command-query mixing
easier to spot during review.

## 6. ASCII structure diagram

```
Before

  +------------------------------+
  | Original method              |
  |------------------------------|
  | source data                  |
  | temp = expression(source)    |
  | if temp ...                  |
  | return f(temp)               |
  +------------------------------+
              |
              | local reads
              v
        +-------------+
        | temp value  |
        +-------------+

After

  +------------------------------+       +--------------------------+
  | Original method              |       | Query                    |
  |------------------------------|       |--------------------------|
  | if query() ...               | ----> | expression(source)       |
  | return f(query())            | <---- | return value             |
  +------------------------------+       +--------------------------+
              ^
              |
  +------------------------------+
  | Other method, later          |
  |------------------------------|
  | can call query() by name     |
  +------------------------------+

  The expression moves behind a name. The source data stays in one owner.
```

## 7. Dynamics

At runtime the important change is the time of evaluation. A temp evaluates
once when execution reaches the assignment. A query evaluates each time a caller
asks, unless the query caches.

```
Before

Caller        Original method          Source data          Temp
  |                 |                       |                 |
  | call            |                       |                 |
  |---------------->|                       |                 |
  |                 | read source data      |                 |
  |                 |---------------------->|                 |
  |                 |<----------------------|                 |
  |                 | assign temp                             |
  |                 |---------------------------------------->|
  |                 | read temp                               |
  |                 |<----------------------------------------|
  |                 | read temp again                         |
  |                 |<----------------------------------------|
  |<----------------| result                                  |

After

Caller        Original method          Query                Source data
  |                 |                     |                    |
  | call            |                     |                    |
  |---------------->|                     |                    |
  |                 | query()             |                    |
  |                 |-------------------->|                    |
  |                 |                     | read source data   |
  |                 |                     |------------------->|
  |                 |                     |<-------------------|
  |                 |<--------------------| value              |
  |                 | query()             |                    |
  |                 |-------------------->|                    |
  |                 |                     | read source data   |
  |                 |                     |------------------->|
  |                 |                     |<-------------------|
  |                 |<--------------------| value              |
  |<----------------| result              |                    |
```

There are three safe dynamic shapes.

First, the source data is immutable during the call. Repeated query calls return
the same value. This is the cleanest case.

Second, the source data can change, and callers want the current value each
time. The query expresses that the result is live.

Third, the source data can change, but the method wants one observed value. In
that case, stop short after extracting the query and keep a local:
`const base = this.basePrice`. The query names the calculation while the local
preserves the snapshot.

## 8. Implementation variants

**Private method query.** The calculation becomes a private method. This is the
standard object-oriented form in Java, TypeScript classes, C#, Swift, and
Python classes. It fits calculations that are meaningful inside the class but
not part of the public contract.

**Computed property or getter.** The query is exposed as property syntax. This
reads well for cheap facts such as path suffix, subtotal, display name, or
empty state. Python's `pathlib.PurePath.suffix` and `PurePath.stem` are
documented as derived properties of the path's final component
(https://docs.python.org/3/library/pathlib.html, verified 2026-08-02). The
danger is cost opacity. A property that performs I/O is hostile to callers.

**Pure module function.** The temp becomes a top-level function such as
`base_price(order)`. This is often the best shape in Go, Rust, and functional
TypeScript when the data is a value rather than an object with behavior.

**Selector.** The query is a named selector over a state tree:
`selectVisibleInvoices(state)`. This is the UI-state cousin of the pattern. It
keeps derived data out of local component state and gives callers a named read
model. The selector can later be memoized.

**Memoized query.** The query caches by input identity, version, or value. This
keeps the API of a query while restoring the once-only cost of a temp. It is
valid only when invalidation is explicit. Rails ActiveRecord's `Relation#size`
is a production example of a query method that branches on loaded state: it
uses loaded records when present and otherwise delegates to `count(:all)`
(https://api.rubyonrails.org/classes/ActiveRecord/Relation.html, verified
2026-08-02).

**Snapshot plus query.** The expression first becomes a query, but the original
method keeps a local binding to one call. This is the right variant when the
value should not be recalculated after later mutations. It is also the lowest
risk migration for expensive calculations.

**Polymorphic query.** A superclass or interface declares the query and
subtypes calculate it differently. This is no longer only Replace Temp with
Query. It becomes a step toward Replace Conditional with Polymorphism. Use it
when the calculation varies by type and the type already owns the variation.

**Generated accessor.** Some languages or frameworks produce accessors from
records, data classes, or model declarations. This can hide the same result
behind a method. Treat generated queries like handwritten ones: they must be
side-effect free, named after their meaning, and visible in tests.

**Naming variants.** Use noun phrases for cheap facts, such as `subtotal`,
`basePrice`, `billingCountry`, or `fileStem`. Use verb phrases for work the
caller should notice, such as `countMatchingRows()` or `loadExchangeRate()`.
Avoid names that describe implementation, such as `computedValue`, because the
old temp already described implementation. The query should name the business
or domain fact.

**Visibility variants.** Private queries are refactoring tools. Package-visible
queries are collaboration tools inside a bounded module. Public queries are API
contracts. Promote only when callers outside the owner need the fact and the
owner is willing to support the wording, return type, error behavior, and cost.

**Error-handling variants.** A query over total in-memory data should usually
return a value. A query over malformed input may return an optional, a result
type, or raise an exception, depending on local idiom. Do not bury a failure
policy inside a property whose call site looks like a field read. In Rust, an
`Option` return for path parsing communicates absence. In Python, a property is
reasonable only when absence has a normal representation, such as an empty
string or `None`.

**Compiler-assisted variants.** Inlining and escape analysis can make the extra
call cost vanish in optimized builds, but the entry does not rely on that as a
sourced fact because compiler behavior varies by language, version, flags, and
call shape. Engineering judgement: write the clearest query first, measure if
the path is hot, then choose a local binding or cache based on evidence.

### TypeScript

```typescript
type Line = { quantity: number; unitPrice: number };

class Invoice {
  constructor(private readonly lines: Line[], private readonly taxRate: number) {}

  totalBeforeRefactor(): number {
    const subtotal = this.lines.reduce(
      (sum, line) => sum + line.quantity * line.unitPrice,
      0,
    );
    return subtotal + subtotal * this.taxRate;
  }

  total(): number {
    return this.subtotal + this.subtotal * this.taxRate;
  }

  private get subtotal(): number {
    return this.lines.reduce(
      (sum, line) => sum + line.quantity * line.unitPrice,
      0,
    );
  }
}

const invoice = new Invoice(
  [
    { quantity: 2, unitPrice: 30 },
    { quantity: 1, unitPrice: 40 },
  ],
  0.1,
);
console.log(invoice.total());
```

TypeScript supports getters, so a cheap domain fact can read as a property. Use
a method such as `calculateSubtotal()` instead if the calculation performs
work a caller must notice.

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Quote:
    quantity: int
    unit_price: float
    discount_rate: float

    def total_before_refactor(self) -> float:
        base_price = self.quantity * self.unit_price
        if base_price > 1000:
            return base_price * (1 - self.discount_rate)
        return base_price

    @property
    def base_price(self) -> float:
        return self.quantity * self.unit_price

    def total(self) -> float:
        if self.base_price > 1000:
            return self.base_price * (1 - self.discount_rate)
        return self.base_price


print(Quote(12, 100.0, 0.05).total())
```

Python property syntax fits cheap derived facts. For a query that touches a
database, filesystem, or network, a verb phrase method is clearer than
property syntax.

### Go

```go
package main

import "fmt"

type Line struct {
	Quantity int
	UnitCents int
}

type Cart struct {
	Lines []Line
	TaxRate float64
}

func (c Cart) TotalBeforeRefactor() int {
	subtotal := 0
	for _, line := range c.Lines {
		subtotal += line.Quantity * line.UnitCents
	}
	return subtotal + int(float64(subtotal)*c.TaxRate)
}

func (c Cart) Subtotal() int {
	total := 0
	for _, line := range c.Lines {
		total += line.Quantity * line.UnitCents
	}
	return total
}

func (c Cart) Total() int {
	return c.Subtotal() + int(float64(c.Subtotal())*c.TaxRate)
}

func main() {
	cart := Cart{
		Lines: []Line{{Quantity: 2, UnitCents: 500}, {Quantity: 1, UnitCents: 250}},
		TaxRate: 0.1,
	}
	fmt.Println(cart.Total())
}
```

Go has no property syntax. The query is a method or function. In performance
paths, bind `subtotal := c.Subtotal()` inside `Total` after the query is
extracted.

The three examples all leave the "before" method in place so the behavioral
equivalence is visible. In a real refactoring, delete the before method once
tests pass. Keeping both permanently creates duplicate sources for the same
rule and defeats the main benefit.

## 9. Known production uses

The sources below are production examples of the resulting design shape:
named, side-effect-free query methods or properties that expose a derived fact
instead of requiring each caller to calculate and store its own local temp.
They are not claims that the maintainers performed Fowler's named refactoring.

- **CPython pathlib.** Python documents `PurePath.suffix` as the final
  dot-separated portion of a path's final component and `PurePath.stem` as the
  final path component without its suffix
  (https://docs.python.org/3/library/pathlib.html, verified 2026-08-02). These
  are query properties over path data. A caller can ask for `path.stem` instead
  of binding a local split result at every call site.
- **Rust standard library Path.** Rust documents `Path::extension()` as a method
  that extracts the extension without the leading dot and `Path::file_stem()` as
  a method used in examples with `Path::new("./foo/bar.txt")`
  (https://doc.rust-lang.org/std/path/struct.Path.html, verified 2026-08-02).
  The methods put path parsing behind named queries and return optional values
  rather than forcing each caller to repeat string parsing.
- **Ruby on Rails ActiveRecord::Relation.** Rails documents `Relation#size` as
  returning the size of records, with source showing that it returns
  `records.length` when loaded and `count(:all)` otherwise
  (https://api.rubyonrails.org/classes/ActiveRecord/Relation.html, verified
  2026-08-02). The query hides the loaded-versus-unloaded branch behind a
  stable name. That is the same end-state benefit as replacing a local
  `loaded ? records.length : count(:all)` temp with a named query.
- **Kaique Silveira's refactoring catalog implementation.** The public GitHub
  repository lists a `replace-temp-with-query` submodule and describes the
  repository as a working implementation with tests and step-by-step histories
  for Fowler catalog refactorings
  (https://github.com/kaiosilveira/refactoring, verified 2026-08-02). This is a
  teaching production artifact rather than an application runtime, but it is a
  named system that implements the refactoring as code.

## 10. Consequences

This dimension is engineering judgement, grounded in the pattern mechanics and
the cited catalog lineage.

Positive consequences.

- The calculation gains a stable name. A reader can understand why the value
  exists without decoding the expression at every use.
- Extract Function gets easier. New methods can call the query rather than
  accepting another parameter copied from the old method.
- Duplicate calculations can collapse into one definition. Future rule changes
  move to the query.
- Tests can target the calculation directly if the language permits access, or
  through public behavior that depends on it.
- The original method often shrinks enough that control flow becomes visible.
- A later optimization has one place to live. The query can cache, precompute,
  or delegate without touching every caller.

Negative consequences.

- The code gains indirection. A reader may need to jump to another method for a
  calculation that used to be visible inline.
- Repeated calls may repeat work. A temp was a local cache by default.
- Property syntax can hide cost. A cheap-looking read can execute heavy work.
- The query can become public too early. Once external callers depend on it,
  renaming or changing semantics costs more.
- A query over mutable data can return different answers within one operation.
  The old temp may have intentionally captured one answer.
- A weak name makes the code worse. `value()`, `amount()`, and `data()` add
  indirection without meaning.
- The query may attract unrelated callers. A private helper named well can
  become a magnet for code that wants a nearby calculation but does not belong
  to the same abstraction.
- A query can hide sequencing requirements. If callers must read the value only
  after validation or normalization, the query name should reveal that state or
  the owner should enforce it.
- Inheritance can complicate the meaning. A protected query may be overridden
  in subclasses, turning a simple extraction into late-bound behavior.

## 11. Failure modes and misuse

This dimension is engineering judgement. Each item is written as an observable
Symptom, Cause, Fix triple.

- **Symptom.** A method returns different results after refactoring when a field
  changes midway through the method. **Cause.** The temp captured a snapshot,
  while the query reads live mutable state on each call. **Fix.** Keep a local
  snapshot initialized from the query, or move mutation after all reads.
- **Symptom.** Request latency rises and CPU samples show the same calculation
  repeated. **Cause.** A once-only temp became several query calls. **Fix.**
  Bind the query result locally in the hot method, or memoize inside the query
  with clear invalidation.
- **Symptom.** A property read unexpectedly hits the database. **Cause.** The
  team used property syntax for an expensive query. **Fix.** Rename to a method
  that signals work, pass preloaded data, or make the cost visible in tracing.
- **Symptom.** Tests become flaky after replacing a temp with `now()`,
  `random()`, or an iterator read. **Cause.** The original local captured a
  single value, but the query produces a new value per call. **Fix.** Inject the
  clock or generator and store one observed value where a snapshot is required.
- **Symptom.** The class fills with one-line private methods that no caller
  reuses. **Cause.** The pattern was applied mechanically to every temp. **Fix.**
  Inline weak queries and keep locals where they improve locality.
- **Symptom.** Extracted methods still need many parameters. **Cause.** The
  temp was not the real blocker. The behavior belongs on another object or the
  data should be grouped first. **Fix.** Consider Introduce Parameter Object,
  Preserve Whole Object, or Extract Class.
- **Symptom.** A query named as a fact changes state. **Cause.** The extracted
  expression included a modifier or lazy initialization with observable
  effects. **Fix.** Separate Query from Modifier, then choose whether caching
  belongs behind the query.
- **Symptom.** Debugging takes longer because intermediate values no longer
  appear in the local variable list. **Cause.** The method now hides the value
  behind calls. **Fix.** Add focused tests, use debugger watches on the query,
  or keep a local with a clear name in diagnostic-heavy code.
- **Symptom.** A subclass changes a protected query and breaks a base method.
  **Cause.** The refactoring made a calculation overridable without designing
  an extension point. **Fix.** Keep the query private, mark it final where the
  language allows, or split the deliberate variation into a named strategy.
- **Symptom.** A public query becomes impossible to rename after external use.
  **Cause.** A local clean-up escaped as API too early. **Fix.** Deprecate the
  weak name, add the better name, and keep the old one as a forwarding wrapper
  until consumers migrate.
- **Symptom.** A query result differs across repeated calls in the same log
  event. **Cause.** The query reads a mutable collection while another thread or
  async task mutates it. **Fix.** Copy the collection before the operation,
  guard it with the project's concurrency primitive, or pass an immutable view.

## 12. Trade-off matrix

| Force | Replace Temp with Query | Extract Variable | Inline Variable | Extract Function | Replace Query with Parameter |
|---|---|---|---|---|---|
| Cognitive load | Names a reusable fact but adds a jump | Names local meaning with no jump | Removes a weak name | Names a whole behavior block | Makes inputs explicit at call site |
| Coupling | Couples callers to source owner query | Stays inside one method | Stays inside one expression | Couples callers to a new function | Couples caller to value calculation |
| Consistency | One definition for repeated calculation | One method still owns the value | No shared definition | Shared behavior when block repeats | Caller controls consistency |
| Latency | May repeat work unless cached | Calculates once | Repeats expression if duplicated | Depends on extracted body | Calculates before call, often once |
| Operability | Query can be logged and traced | Local debugger value is visible | No named signal | Function boundary is traceable | Inputs can be logged by caller |
| Cost of change | Rule changes in one query | Rule changes in one method | Rule changes at every duplicate | Behavior changes in one function | Signature changes may ripple |
| Team topology | Good when owner team owns the fact | Good for one-owner methods | Good for tiny code | Good for shared module behavior | Good across ownership boundaries |
| Debuggability | Breakpointable query, less local state | Easy local inspection | Fewer names to inspect | Breakpointable function | Caller can test supplied value |

## 13. Related and incompatible patterns

**Extract Function** often follows Replace Temp with Query. Once a temp is no
longer tying a block to its parent method, the block can move with fewer
parameters. Fowler's public catalog and second-edition change list place both
refactorings in the same current catalog
(https://refactoring.com/catalog/replaceTempWithQuery.html, verified
2026-08-02; https://martinfowler.com/articles/refactoring-2nd-changes.html,
verified 2026-08-02).

**Extract Variable** is the sibling in the other direction. It gives a local
expression a name. Use Extract Variable when the name matters only in the
current method. Use Replace Temp with Query when that name wants to become a
reusable fact.

**Inline Variable** can be a preparatory or reversal step. If the temp adds no
meaning, inline it rather than creating a query. If a query adds no meaning,
inline it back into the caller.

**Split Variable** comes first when one temp is reassigned for different
meanings. Replace Temp with Query needs a single assignment and one meaning.

**Separate Query from Modifier** is a guardrail. If extracting the expression
would create a method that changes state while returning a value, split the
state change from the read before calling it a query. Fowler's command-query
separation note describes the distinction between methods that return
information and methods that change state
(https://martinfowler.com/bliki/CommandQuerySeparation.html, verified
2026-08-02).

**Replace Query with Parameter** is a partial opposite. Use it when a query
would hide an external dependency, volatile state, clock read, random value, or
authorization context. Passing the value can make the dependency honest.

**Replace Derived Variable with Query** is broader and targets stored derived
state. It removes a field or state entry that can be computed from source data.
Replace Temp with Query targets a local variable.

**Memoization** composes with the pattern when repeated calculation costs too
much. It conflicts when cache invalidation rules are unclear.

## 14. Refactoring path in and out

Path in.

1. Identify the temp and all reads. Confirm it has one meaning.
2. Check that the assignment runs before every read and that no read depends on
   a partially updated state.
3. Confirm the right side has no side effects. Fowler's errata records this as
   an explicit mechanics correction for the first edition
   (https://martinfowler.com/refactoringErrata.html, verified 2026-08-02).
4. If the temp is assigned more than once, apply Split Variable first.
5. Extract the right side into a private query with a domain name.
6. Run tests.
7. Replace one temp read with the query.
8. Run tests again.
9. Replace the remaining reads.
10. Delete the temp when no reads remain.
11. If repeated calls matter, bind one local from the query in the caller or add
    memoization inside the query.
12. Look for blocked Extract Function opportunities and move the next coherent
    block.

Path out.

1. Find query callers. If there is one caller and the query name adds little,
   inline it.
2. If the query is expensive and repeatedly called by one method, keep the query
   but store one local result inside that method.
3. If the query reads volatile state and callers need explicit inputs, apply
   Replace Query with Parameter.
4. If the query has grown side effects, apply Separate Query from Modifier or
   split it into command plus read.
5. If the query's data belongs elsewhere, move the function to the owner of the
   data or extract a value object.

The safest migration is reversible at every step. Extract a query, run tests,
replace one read, run tests. The goal is to move meaning without changing
observable behavior.

Refactoring in a branch with many readers needs one more habit: keep commits
small. One commit can introduce the query and replace reads in the original
method. A later commit can extract the newly freed block. A third commit can
promote visibility if a second caller appears. Reviewers can then check
behavior preservation before they judge the larger design move.

Refactoring generated or framework-owned code needs a different path. Do not
edit generated files by hand. Change the template, model declaration, or
extension point that produces the temp. If no extension point exists, wrap the
generated object with a query in owned code and leave the generated file alone.

## 15. Testing and verification

This dimension is engineering judgement.

Characterization tests come first when the original method has no focused
tests. Capture current behavior at the public boundary before moving the
calculation.

Unit tests for the query are useful when the query is public, package-visible,
or can be tested through a small public behavior. Private query tests are a
judgement call. Testing only private methods can cement implementation details,
but ignoring a complex private calculation can leave the refactoring
under-protected. Prefer public tests unless the repository already tests
private helpers.

Property-based tests fit numeric and parsing queries. For example, a subtotal
query can be tested across random line items, and a path query can be tested
across generated file names.

Mutation tests are useful when the query controls a branch. If changing `>` to
`>=` survives, the test suite did not capture the threshold behavior.

Performance tests matter when the removed temp was an implicit cache. Measure
the old method and the new method when the expression touches collections,
regular expressions, parsing, compression, database counts, or remote services.

Concurrency tests matter when the query reads mutable shared state. A local temp
could have hidden a race by reading once. A query that reads twice can reveal or
introduce inconsistent observations. Prefer immutable input snapshots in
multi-threaded code.

Verification checklist.

- The query returns the same value as the temp for representative inputs.
- The query has no externally visible side effects.
- Repeated calls are either acceptable or intentionally cached.
- The caller still observes one value when one value is required.
- The query name matches domain language.
- Extract Function opportunities no longer need the removed temp as a
  parameter.
- Public visibility was not widened by accident.
- Snapshot requirements are captured by a local binding where needed.
- Logs and traces do not reveal sensitive query values.

For legacy code, approval tests can guard the original method while the query is
introduced. For domain calculations, table-driven tests are usually clearer
than one test per branch because they keep the input, expected derived fact, and
expected outcome in one place. For parsing queries, keep malformed inputs in the
table as first-class cases. For money calculations, include rounding boundaries
and threshold edges.

When testing memoized queries, test both value and invalidation. A cache that
returns the right first answer but the wrong second answer is worse than no
cache because it hides stale behavior behind a trusted name.

## 16. Observability signals

This dimension is engineering judgement.

Most instances of Replace Temp with Query need no production signal. A cheap
calculation over in-memory values should disappear into ordinary code. Add
signals only when the query is expensive, cached, security-relevant, or
business-critical.

Useful signals.

- Query duration, tagged by query name and input size bucket.
- Cache hit and miss counts when memoization is added.
- Number of backing data reads when the query can trigger a database count,
  lazy load, filesystem stat, or remote call.
- Branch outcomes when the query controls pricing, eligibility, routing, or
  authorization.
- Error count for query failures when the calculation can reject malformed
  source data.

A healthy dashboard shows stable query latency, stable cache hit ratios after
warmup, and no surprise increase in backing data reads after deployment. A
failing dashboard shows repeated query execution inside one request, rising
database count calls, cache churn, or branch outcome shifts that are not tied to
a product change.

Do not log raw values by default. A query often returns business data, path
data, account status, or authorization facts. Log a query name and coarse
classification first. Add value-level logging only under a redaction policy.

## 17. Security and privacy implications

This dimension is engineering judgement.

The refactoring is usually security-neutral. It moves a calculation from a
local variable into a query and should not change what data is read or returned.
The security risk comes from making the query more reachable than the temp was.

If the query becomes public, it may expose a derived fact that used to be
private to one operation. A boolean such as `isHighRiskCustomer`, a price such
as `internalMargin`, or a path component such as `tenantRoot` can reveal policy
or sensitive structure. Keep queries private until an external contract is
deliberate.

If the query computes authorization or eligibility, repeated evaluation must be
consistent with the security model. A local temp can capture the decision made
at the start of a request. A query that re-reads roles or feature flags midway
through the request can produce time-of-check to time-of-use bugs. In that case
use a request-scoped authorization snapshot.

If memoization is added, cached values must not cross tenants, users, sessions,
or permission scopes. Key the cache by every input that affects the answer, or
keep the cache local to one request.

If observability is added, derived values may be personal data. Path stems,
invoice totals, account tiers, and eligibility reasons can identify a user or
business. Prefer counts, categories, and hashes that meet the project's privacy
rules.

## 18. References

- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
  edition, Addison-Wesley, 1999, chapter 6, "Composing Methods."
- Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
  edition, Addison-Wesley, 2018, chapter 6, "A First Set of Refactorings."
- Martin Fowler, "Replace Temp with Query,"
  https://refactoring.com/catalog/replaceTempWithQuery.html, verified
  2026-08-02.
- Martin Fowler, "Errata for Refactoring,"
  https://martinfowler.com/refactoringErrata.html, verified 2026-08-02.
- Martin Fowler, "Changes for the 2nd Edition of Refactoring,"
  https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
  2026-08-02.
- Martin Fowler, "Command Query Separation,"
  https://martinfowler.com/bliki/CommandQuerySeparation.html, verified
  2026-08-02.
- Python Software Foundation, "pathlib. Object-oriented filesystem paths,"
  Python 3.14 documentation, https://docs.python.org/3/library/pathlib.html,
  verified 2026-08-02.
- Rust Project Developers, "Path in std::path," Rust standard library
  documentation, https://doc.rust-lang.org/std/path/struct.Path.html, verified
  2026-08-02.
- Ruby on Rails API, "ActiveRecord::Relation,"
  https://api.rubyonrails.org/classes/ActiveRecord/Relation.html, verified
  2026-08-02.
- Kaique Silveira, "refactoring,"
  https://github.com/kaiosilveira/refactoring, verified 2026-08-02.
