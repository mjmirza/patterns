---
name: Slide Statements
slug: slide-statements
family: 03-refactoring
category: Refactoring
aliases: [Consolidate Duplicate Conditional Fragments, Move Declaration Closer to Use, Code Sinking]
first_described: "Fowler 2018"
maturity: established
related: [extract-function, split-loop, split-variable, move-statements-into-function, move-statements-to-callers, separate-query-from-modifier]
incompatible_with: []
verified: 2026-08-02
---

# Slide Statements

## 1. Name, aliases, and lineage

The canonical name is **Slide Statements**. Martin Fowler lists it in
*Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 8, "Moving Features," section "Slide
Statements." Fowler's public catalog also names the refactoring and gives the
same small example shape, where a derived value is moved next to the statement
that creates the value it depends on, https://refactoring.com/catalog/slideStatements.html,
verified 2026-08-02.

The older alias is **Consolidate Duplicate Conditional Fragments**. Fowler's
public notes on the second edition say the first-edition refactoring with that
name was replaced by Slide Statements,
https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02. That history matters because the old name describes one narrow
case. If both branches of a conditional contain the same trailing statement,
the statement can often be slid after the conditional. Slide Statements is the
wider operation. It moves one or more neighboring statements earlier or later
inside the same behavior boundary so related work sits together.

Two aliases appear in production code review and compiler contexts. **Move
declaration closer to use** is the phrasing seen in normal commits. GNOME's
2017 commit archive includes a librsvg commit titled "marker.rs: Move
declarations closer to their use,"
https://mail.gnome.org/archives/commits-list/2017-March/date.html, verified
2026-08-02. EngineHub's WorldEdit build history includes a change that
restructures `EditSession.hollowOutRegion` and says it moved declarations
closer to their usage, https://builds.enginehub.org/job/worldedit?branch=improve-hollow,
verified 2026-08-02. **Code sinking** is the compiler term for a related
machine operation, moving computations later so they execute only on paths that
need them. LLVM documents a `sink` pass with that purpose,
https://llvm.org/docs/Passes.html, verified 2026-08-02. A human refactoring and
a compiler optimization have different contracts, but both depend on the same
core fact. Statement order is not sacred when data dependencies, control flow,
and observable effects allow movement.

This entry treats Slide Statements as a source-level refactoring, not as a
compiler optimization. Any compiler reference is used only as corroboration
that code motion around dependencies is a real engineering concern in production
systems, not as authority for how humans should edit application code.

## 2. Problem and context

A function contains statements that are related by data, intent, or later
extraction, but those statements are separated by other work. The function may
still be correct. The problem is that the order makes a reader reconstruct the
relationship mentally.

The common case is a declaration or derived value created far from its first
use. A function obtains a `pricing_plan`, then retrieves an order, then creates
several temporary values, then eventually reads `pricing_plan.unit_price`. The
reader sees the derived value after losing the context that made it meaningful.
Sliding the unit price calculation next to the plan retrieval makes the local
story easier to read. Fowler's public catalog shows this general shape with
`pricingPlan`, `order`, and `chargePerUnit`,
https://refactoring.com/catalog/slideStatements.html, verified 2026-08-02.

Another case is duplicate setup on both sides of a conditional. If both arms
finish with the same statement, the duplicated statement might belong after the
conditional. If both arms begin with the same statement, the duplicate might
belong before it. The old alias, Consolidate Duplicate Conditional Fragments,
describes that narrower case. The second-edition replacement broadens the
practice from conditionals to statement order in general,
https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02.

The context is small movement inside one behavior-preserving edit. Slide
Statements does not invent a new abstraction, split a type, or change an API.
It prepares the ground for those moves. After related statements are adjacent,
Extract Function, Split Loop, Move Statements into Function, or Separate Query
from Modifier often becomes simple. Before the slide, those larger
refactorings look risky because the candidate code is tangled with unrelated
work.

Judgement. This refactoring is at its best when it is almost boring. A reviewer
should be able to scan the diff and say, "same statements, new order, no new
decision." If the reviewer must reason about a changed branch, a changed
exception path, or a changed mutation order, the edit is no longer a slide
alone.

## 3. Forces

Judgement. The forces below are engineering trade-offs, not quoted claims from
a source.

**Cognitive load.** Slide Statements favors the reader who wants a local story.
Values are introduced near their use. Cleanup sits near acquisition. Repeated
fragments sit outside the branch that no longer owns them. The cost is that the
historical order of the code is disturbed, which can make `git blame` and old
review comments less direct.

**Coupling.** The refactoring can expose hidden coupling. When moving one line
requires moving three others, the function is telling you those statements form
a unit. That is useful information. The cost is that a slide may make this
coupling more visible without reducing it yet.

**Consistency.** The refactoring favors consistency of local intent. Related
statements occupy one area instead of being scattered. It can sacrifice
temporal consistency if a statement was deliberately early to fail fast, warm a
cache, or record an audit event before later work.

**Latency.** Source-level slides are often latency-neutral. Moving a pure
calculation closer to its use usually changes no work performed. Moving a call
later can change when work happens, and moving it inside a branch can change
whether work happens. That second case is not a plain slide unless the skipped
path could never observe the call.

**Operability.** A slide can make logs and spans read in a better order when
setup, action, and cleanup are grouped. It can also make incident timelines
harder if log emission moves across a statement that can fail.

**Cost.** The edit is cheap when tests are present and dependencies are obvious.
The cost rises in languages or codebases with implicit effects, destructors,
deferred cleanup, lazy properties, global state, signals, reflection, or
macros.

**Team topology.** Slide Statements fits code ownership boundaries because it
is usually local to one function. It can still create review conflict when a
team uses strict blame ownership, because a whitespace-sized refactoring can
touch lines last edited by many people.

**Mutation safety.** The pattern favors shorter live ranges for mutable locals.
That lowers the chance of reading a stale or half-updated value. It sacrifices
nothing when movement is over pure statements, but it is unsafe across writes,
reads, locks, resource lifetimes, awaits, yields, and exception boundaries
unless those interactions are proven irrelevant.

## 4. Applicability and non-applicability

Reach for Slide Statements when the following hold.

- A value is declared long before its first real use, and the intervening
  statements neither need that value nor depend on its creation.
- Several statements use the same object or local value, but unrelated work
  splits them apart.
- Two branches contain the same statement at the same edge of the branch, and
  moving it before or after the conditional preserves behavior.
- A later Extract Function or Move Statements into Function is blocked only
  because the candidate statements are not adjacent.
- A loop mixes two independent concerns and you want to group each concern
  before deciding whether Split Loop is valid.
- A resource acquisition and its cleanup are far apart, and sliding nearby
  setup or validation clarifies the lifetime without changing when release
  happens.
- A mutable local has a wide live range because it is assigned early and read
  late, and moving the assignment later narrows the span where it can be
  misread or overwritten.

Do NOT reach for Slide Statements in these cases.

- **The statement has observable effects.** Do not move database writes, network
  calls, event publication, log emission, metrics, random number generation,
  time reads, file operations, or audit records across other work unless the
  external order is part of the tested contract and remains unchanged.
- **The statement can throw or return an error.** Moving a failing statement
  changes which earlier effects have already happened when failure occurs.
- **The statement participates in locking.** Do not move lock acquisition,
  release, condition waits, atomic operations, or memory fences across ordinary
  code. The apparent cleanup can introduce a race.
- **The code crosses an `await`, `yield`, callback, goroutine launch, thread
  spawn, or coroutine suspension.** Values visible before and after suspension
  may have different lifetime and scheduling meaning.
- **A destructor, `defer`, `finally`, context manager, or RAII scope is in play.**
  Moving declarations in these regions can change release order.
- **The statement reads or writes global state.** A local move can alter shared
  process behavior when globals, singletons, environment variables, feature
  flags, or static caches are touched.
- **The code relies on short-circuit evaluation.** A statement moved out of a
  branch may now run when the branch would not have run.
- **A macro, annotation processor, reflection rule, or framework convention
  depends on source order.** The code may compile after the slide but be
  interpreted differently by tooling.
- **The slide is hiding a larger design fault.** If related statements are spread
  across hundreds of lines because the function has several jobs, Extract
  Function, Split Phase, or Split Loop may be the real repair.
- **The target order is only a personal taste preference.** A refactoring should
  buy understandability, enable a later change, narrow a live range, or remove
  duplication. It should not churn code only to match one reader's habit.

## 5. Structure

Slide Statements has a small cast of participants.

- **Movable statement.** The statement or block being moved. It may be a
  declaration, assignment, calculation, guard, duplicate branch fragment, or
  nearby setup line.
- **Anchor statement.** The statement the movable statement should sit near.
  It might produce the value used by the movable statement, consume the value
  produced by it, or mark the branch edge where a duplicate fragment belongs.
- **Intervening statements.** The statements between the original position and
  the target position. Each must be checked for data dependency, control
  dependency, resource lifetime, and observable effect order.
- **Behavior boundary.** The smallest region that owns the behavior. Usually it
  is one function body, one branch, one loop body, or one cleanup scope. A slide
  should stay inside this boundary unless another refactoring is being applied.
- **Safety proof.** The reason movement preserves behavior. In a tiny change the
  proof may be obvious from reads and writes. In a risky change it should be
  backed by tests, static analysis, or a smaller step.

The central relationship is dependency. A statement may slide over another
statement only when the two can be reordered without changing observable
behavior. Data reads and writes are the first check. Effects and failure order
are the second check. Lifetime and concurrency are the third check.

## 6. ASCII structure diagram

```
Before

  +====================== function ======================+
  | A. pricing_plan = retrieve_pricing_plan()            |
  | B. order = retrieve_order()                          |
  | C. charge = 0                                        |
  | D. charge_per_unit = pricing_plan.unit_price         |
  | E. charge = order.units * charge_per_unit            |
  +======================================================+

  D depends on A.
  D does not depend on B or C.
  B and C do not depend on D.

After

  +====================== function ======================+
  | A. pricing_plan = retrieve_pricing_plan()            |
  | D. charge_per_unit = pricing_plan.unit_price         |
  | B. order = retrieve_order()                          |
  | C. charge = 0                                        |
  | E. charge = order.units * charge_per_unit            |
  +======================================================+

  The dependency cluster is now adjacent:

       pricing_plan
            |
            v
       charge_per_unit

  The order-related cluster remains intact:

       order
         |
         v
       charge
```

## 7. Dynamics

At runtime nothing special is introduced. The same statements run in a new
legal order. The refactoring process is where the dynamics matter.

```
  t0  choose one movable statement
       |
       v
  t1  identify the anchor it should sit near
       |
       v
  t2  list each statement between old and new positions
       |
       v
  t3  for every intervening statement, ask four questions
       |
       +=> data. does either statement read a value the other writes?
       |
       +=> control. can branch, return, break, continue, panic, or throw differ?
       |
       +=> effect. can outside code observe the order?
       |
       +=> lifetime. can cleanup, lock scope, borrow scope, or ownership differ?
       |
       v
  t4  move the statement one safe hop or one small cluster
       |
       v
  t5  run focused tests and compile checks
       |
       v
  t6  repeat only if the next hop has the same safety proof
```

The one-hop rule is a practical guard. If a statement must cross five unrelated
statements, move it across the first safe boundary, compile, and inspect again.
That rhythm keeps the refactoring reversible and helps a reviewer see the proof.

## 8. Implementation variants

**Declaration closer to first use.** This is the most common variant in C,
C++, Java, Go, Rust, Swift, TypeScript, and Python. A local value is created
near the place it is consumed. In Rust this can also shorten a borrow. In Go it
can keep the `err` value near the call that produced it. In Swift it can keep a
`guard` result near the view or model code that uses it.

**Derived value beside its source.** A calculation that depends on one object is
moved next to the statement that obtains that object. Fowler's catalog example
has this shape with a charge-per-unit value derived from a pricing plan,
https://refactoring.com/catalog/slideStatements.html, verified 2026-08-02.

**Duplicate branch fragment out of a conditional.** When both arms start or end
with the same statement, move the common statement outside the conditional if
failure and effect order remain the same. This is the old Consolidate Duplicate
Conditional Fragments case, renamed under Slide Statements in Fowler's
second-edition change notes,
https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02.

**Preparation for Extract Function.** Related statements are slid together so
the next refactoring can extract them as one named function. This variant often
has no lasting value by itself. Its value is that the next step becomes
mechanical.

**Preparation for Split Loop.** Statements inside one loop are grouped by
purpose before the loop is split. If the statements can be grouped without
dependency, they may also be separable into two loops. If they cannot be
grouped, the loop probably has a real dependency that Split Loop must respect.

**Code sinking for execution control.** A calculation is moved later, often
inside a branch, so it runs only when needed. LLVM documents a `sink` pass that
moves instructions into successor blocks when possible so unneeded paths do not
execute them, https://llvm.org/docs/Passes.html, verified 2026-08-02. In human
source code, this variant is no longer a pure readability slide if it changes
whether the statement runs. Treat it as a behavior-sensitive optimization unless
tests prove the skipped work had no observable effect.

**Code hoisting for duplication removal.** A duplicate statement is moved
earlier out of two branches. This is the mirror image of sinking. It is safe
only when the statement should run on every path that reaches the new location.

**Language-level block extraction instead of sliding.** Some languages let you
wrap a local cluster in a block, closure, or immediately invoked function to
limit scope without changing statement order. Use that variant when source
order is important but scope still needs to shrink.

Judgement. A useful way to choose a variant is to classify the movable
statement before touching it.

**Green statements.** These are usually safe to slide after a quick dependency
check. Examples include binding a constant from an already available immutable
value, calculating a derived scalar from local values, naming an expression, or
moving a comment with the statement it describes. Even green statements still
need dominance checks. The moved value must still be assigned before every use,
and it must not cross a branch that would skip the assignment.

**Yellow statements.** These need a test or a smaller hop. Examples include
reading from a collection that another statement may mutate, calling a helper
that is meant to be pure but is not visibly pure, changing the position of a
validation guard, or moving a statement near a cleanup block. Yellow statements
often expose a weak name or weak boundary. If the safety proof takes longer to
explain than the extraction that follows, apply the extraction instead of
making a large slide.

**Red statements.** These are not Slide Statements candidates until another
refactoring changes their nature. Examples include writes to external systems,
message sends, audit records, lock operations, thread or task launches, time
reads used for ordering, random value generation, and calls into plugin code.
Moving red statements may be a valid behavior change, but it should be reviewed
as a behavior change with a test that names the new order.

The classification is intentionally conservative. A statement can move from
yellow to green after Inline Function reveals it is pure, or from red to yellow
after Separate Query from Modifier splits a read from a write. Slide Statements
is often the tiny move in the middle of that chain, not the first move.

## 9. Known production uses

**GNOME librsvg, `marker.rs`.** GNOME's public commit archive for March 2017
lists a librsvg change titled "marker.rs: Move declarations closer to their
use," authored by Federico Mena Quintero,
https://mail.gnome.org/archives/commits-list/2017-March/date.html, verified
2026-08-02. That is a named production graphics library using the declaration
proximity form of Slide Statements.

**EngineHub WorldEdit, `EditSession.hollowOutRegion`.** EngineHub's WorldEdit
build history for the `improve-hollow` branch lists a restructuring commit that
created a dedicated `startingPositions` collection and moved declarations
closer to their usage, https://builds.enginehub.org/job/worldedit?branch=improve-hollow,
verified 2026-08-02. WorldEdit is a named editing tool, and the commit message
identifies a real method where statement sliding accompanied a larger local
restructure.

**LLVM, `sink` pass and MachineSink.** LLVM documents a `sink` transform that
moves instructions into successor blocks when possible so paths that do not
need the result do not execute the instruction, https://llvm.org/docs/Passes.html,
verified 2026-08-02. LLVM's generated source documentation for
`MachineSink.cpp` shows safety checks before sinking a machine instruction and
comments about sinking instructions to reduce register pressure,
https://llvm.org/doxygen/MachineSink_8cpp_source.html, verified 2026-08-02.
This is a production compiler analogue, not a manual source refactoring.

**Standard ML of New Jersey, MLRiscGen.** The SML/NJ history notes that
MLRiscGen performs code motion and moves some floating-point and heap-pointer
address computations to their use sites when there is only one use,
https://www.smlnj.org/dist/working/110.80/HISTORY.html, verified 2026-08-02.
This is another production compiler analogue that names the use-site movement
directly.

## 10. Consequences

Positive.

- Related code becomes adjacent, so the reader spends less effort holding a
  distant value in memory.
- Mutable locals can have shorter live ranges, which reduces the time window in
  which a later statement can read or overwrite them incorrectly.
- The diff can prepare a larger refactoring without changing names, APIs, or
  type structure.
- Duplicate branch fragments can disappear when a common statement moves out
  of a conditional.
- Review can focus on reorder safety, because the code text mostly stays the
  same.
- Tests often need no new fixtures, since the public behavior is meant to be
  unchanged.

Negative.

- A slide can silently change failure order when a moved statement can throw,
  return an error, panic, or reject a promise.
- A slide can change effect order when logs, metrics, writes, or external calls
  move across each other.
- A readability-only slide can create noisy blame history if done across large
  areas without a feature need.
- Moving declarations can change resource release timing in languages with
  deterministic cleanup or scoped ownership.
- The refactoring can give a false sense of safety. Same statements do not
  always mean same behavior.
- Code review can become harder when many independent slides are batched in one
  commit.

## 11. Failure modes and misuse

Judgement. These triples describe common ways the refactoring fails in real
code review and production debugging.

**Symptom.** A log line appears after an error instead of before it, or an
incident timeline loses the last known input value. **Cause.** A logging
statement was treated as cosmetic and slid across a statement that can fail.
**Fix.** Move the log back or split it into two logs, one before the failing
operation and one after success.

**Symptom.** A database row, message, or metric count changes even though the
diff appears to reorder only locals. **Cause.** One moved statement called a
function with hidden effects. **Fix.** Inline or name the effect, then repeat
the slide only across pure statements.

**Symptom.** A Rust borrow checker error appears after moving a declaration
closer to use, or a previous error disappears for the wrong reason. **Cause.**
The move changed the lifetime of a borrow or owner. **Fix.** Treat the lifetime
change as part of the refactoring. Add a small block or clone only where the
ownership model calls for it.

**Symptom.** A Python context manager, Java `try` with resources, Swift `defer`,
or Go `defer` releases a resource at a different point. **Cause.** A statement
was moved into or out of a cleanup scope. **Fix.** Keep acquisition and release
scope unchanged, then slide only statements inside that scope.

**Symptom.** Two threads sometimes observe values in a new order. **Cause.** A
slide crossed a lock, atomic write, memory fence, goroutine launch, task start,
or callback registration. **Fix.** Restore the synchronization boundary and add
a concurrency test or stress test around the original invariant.

**Symptom.** A branch now performs work that used to happen only on one path.
**Cause.** A duplicate-looking statement was hoisted out of a conditional even
though one branch reached it under different conditions. **Fix.** Rebuild the
control-flow table and move only the truly common fragment.

**Symptom.** A later Extract Function has a long parameter list after sliding
statements together. **Cause.** The slide grouped statements that share a topic
in prose but not data. **Fix.** Split by data dependency, or use Introduce
Parameter Object before extraction.

**Symptom.** A review becomes a debate about style instead of behavior. **Cause.**
The slide did not enable a named follow-up refactoring, remove duplication, or
reduce a visible risk. **Fix.** Drop the change or pair it with the follow-up
that makes the value clear.

## 12. Trade-off matrix

| Force | Slide Statements | Extract Function | Split Loop | Separate Query from Modifier | Inline Variable |
|---|---|---|---|---|---|
| Primary move | Reorder nearby statements | Name a block as a function | Separate loop responsibilities | Split read from write | Remove a temporary |
| Coupling | Exposes local coupling | Creates a call boundary | Exposes per-loop concern | Exposes effect boundary | Reduces name coupling |
| Cognitive load | Lower when order tells a local story | Lower at caller, higher by navigation | Lower per loop | Lower by clearer effect contract | Lower if the name was noise |
| Consistency | Groups related statements | Names one unit | One concern per loop | Read calls stay effect-free | Expression is single source |
| Latency | Usually neutral | Usually neutral, call overhead may exist | May add iteration cost | May add a call or second operation | Neutral |
| Operability | Risk if logs or errors move | Better if extracted unit logs | Better per concern metrics | Better audit of effects | Neutral |
| Cost | Low per small hop | Medium when parameters are many | Medium when data dependencies exist | Medium when API users exist | Low |
| Team topology | Local change, small review | New named unit may need owner | Larger review if loop is hot | Contract change may cross teams | Local change |
| Best use | Prepare or clarify local order | Give a cluster a name | Untangle loop jobs | Separate effects from reads | Remove weak temporary names |
| Main risk | Hidden order dependency | Over-extraction | Repeated traversal cost | API churn | Losing explanatory name |

Reading the table. Slide Statements is the smallest move. It should often come
before Extract Function, Split Loop, or Separate Query from Modifier because it
reveals whether the later move is mechanically simple. It should not replace
those refactorings when the code needs a new name, a new boundary, or a clearer
effect contract.

## 13. Related and incompatible patterns

- **Extract Function.** Slide Statements often prepares it. Related statements
  must be adjacent before they can be extracted without taking unrelated code
  along for the ride.
- **Move Statements into Function.** Slide first when the statements that
  belong inside the function are scattered around the call site. Once adjacent,
  moving them into the function is lower risk.
- **Move Statements to Callers.** The inverse preparation also appears. Slide
  the varying statements to the edge of the called function, then move them to
  each caller.
- **Split Loop.** Slide statements within the loop body to see whether there are
  two independent groups. If the groups share mutation each iteration, Split
  Loop may not be valid.
- **Split Variable.** When a variable is assigned, reassigned, then read much
  later, sliding often exposes that one name is carrying two meanings. Split
  Variable is then the better move.
- **Separate Query from Modifier.** Sliding can put reads on one side and writes
  on the other. If a single function both answers and mutates, this related
  refactoring handles the deeper issue.
- **Inline Variable.** Sometimes the right way to move a derived value close to
  use is to remove the temporary. Use Inline Variable when the name adds no
  intent.
- **Command Query Separation.** Compatible as a design principle. It gives a
  reason not to slide a modifier into a group of queries, because that would
  blur the effect boundary.
- **Service Locator and global state.** Incompatible in practice. When
  dependencies are hidden behind global lookup, a statement that looks like a
  read may mutate shared state, making reorder safety hard to prove.
- **Concurrency patterns.** Locks, actors, futures, and channels create order
  contracts. Slide Statements must respect those contracts rather than treating
  them as local syntax.

## 14. Refactoring path in and out

Introducing Slide Statements into code that does not have the target order.

1. Pick one function. Do not start with a whole file.
2. Identify one goal: move a declaration near first use, group a cluster for
   Extract Function, remove a duplicate branch fragment, or narrow a mutable
   live range.
3. Mark the movable statement and the anchor statement.
4. Inspect every statement between them for reads, writes, effects, failure,
   cleanup, locking, and suspension.
5. If any intervening statement is unsafe, stop or make a smaller refactoring
   that exposes the dependency.
6. Move the statement one safe hop or move the smallest adjacent block that has
   one safety proof.
7. Run the narrowest fast test. If there is no test, compile and add a
   characterization test before doing a risky slide.
8. Repeat until the statements are adjacent enough for the goal.
9. If the goal was preparation, immediately apply the follow-up refactoring or
   leave a small commit message that names it.

A safe commit sequence is often better than one large reorder. First commit the
pure slides that move declarations near use. Second commit a branch-fragment
consolidation if one exists. Third commit the larger Extract Function or Split
Loop that the slides made possible. That sequence gives reviewers a narrow
question in each diff. Did order stay legal? Did duplicate code truly become
common code? Did the new boundary keep the same inputs and outputs?

When the code has few tests, add the characterization test before the slide.
The test does not need to describe the refactoring. It should describe the
observable contract that could be broken by reordering: emitted events,
repository calls, return values on failure, or cleanup order. After that test
exists, the slide becomes a normal small refactoring rather than a trust
exercise.

Moving out of Slide Statements means undoing an order that stopped paying rent.

1. If the new order hides a fail-fast check, move that check back to the top.
2. If a local cluster grew too dense, Extract Function so the cluster has a
   name instead of only proximity.
3. If a derived value near its source is read much later, move it near the read
   or inline it if the expression is clear.
4. If a hoisted duplicate statement now runs too often, sink it back into only
   the branch that needs it.
5. If order now encodes a resource lifetime, replace proximity with an explicit
   scope, context manager, `try` with resources, `defer`, or RAII block.

Cross references. Use Extract Function after statement groups become adjacent.
Use Split Loop after independent loop clusters are visible. Use Split Variable
when movement exposes reused locals. Use Separate Query from Modifier when the
reason a slide is unsafe is that a query also mutates state.

## 15. Testing and verification

Judgement. Tests for Slide Statements are mainly regression tests. The
refactoring should not create new user-visible behavior.

For pure local calculations, compile plus existing unit tests are often enough.
For effectful code, add a characterization test that records order. A fake
repository can record `["load", "save"]`. A fake clock can record when time is
read. A fake logger can record whether an error log happens before or after the
operation that fails.

For branch-fragment movement, build a path table. Each row is an input class,
the branch taken, whether the moved statement runs before, and whether it runs
after. The columns must match. If one row changes, the edit is not a behavior
preserving slide.

For exceptions and errors, test the failing path, not only the successful path.
The main risk is that an exception now occurs before or after a visible effect.
In Go, test returned errors and any side effects recorded before return. In
Python, test raised exceptions and context manager exits. In Rust, test `Result`
paths and drop-sensitive behavior when ownership matters.

For concurrency, favor a small stress test plus a deterministic unit test around
the synchronization contract. If a statement crosses a lock or task boundary,
that is usually a signal to stop rather than to write a larger test.

Static checks help. Compilers catch many declaration and ownership mistakes.
Linters can flag unused values after a slide. Type checkers can catch a moved
assignment that no longer dominates a use. They cannot prove external effect
order, so they do not replace tests around I/O, logging, metrics, and
concurrency.

## 16. Observability signals

Judgement. Slide Statements is a source refactoring, so it usually does not
need new production telemetry. The exception is when the slide touches effect
order, resource timing, or a hot path.

Record order when order is part of behavior. A span can carry events named
`input_validated`, `cache_checked`, `external_call_started`, and
`external_call_finished`. A healthy trace after a slide has the same event
order as before unless the change was an intentional optimization with its own
review.

Measure count when a statement moved across a branch. A counter for the moved
operation should keep the same rate if the slide was only readability. If the
rate drops, the edit changed whether work runs. That may be desired for code
sinking, but it is not a plain refactoring.

Measure duration when the moved statement is expensive. If moving a calculation
later or earlier changes tail latency, the statement was not operationally
neutral. Keep a timer around the enclosing operation, and when possible label
the path through the branch rather than the internal line.

Watch resource gauges when a declaration or acquisition moved across a scope.
Open file count, live connection count, lock wait time, task count, and memory
retention can reveal a lifetime change that unit tests missed.

For compiler-style sinking, use compiler metrics rather than application logs.
LLVM's public documentation frames `sink` as a transform that can avoid
executing instructions on paths where results are not needed,
https://llvm.org/docs/Passes.html, verified 2026-08-02. The matching signals
are code size, dynamic instruction count, register pressure, and path-specific
execution time.

## 17. Security and privacy implications

Judgement. Slide Statements is security-neutral when it reorders pure local
calculations inside one function. It becomes security-relevant when order
affects validation, authorization, audit, cleanup, or data exposure.

Do not slide work before validation unless the work is safe on untrusted input.
Parsing, normalization, logging, and metric labels can all expose sensitive
data if moved before redaction. A statement that looked like a harmless derived
value may call a method that formats personal data.

Do not slide authorization checks downward to group them with other user
context code. A fail-fast authorization check often protects every statement
after it. Moving it later may create a path where data is read, cached, logged,
or sent before access is denied.

Do not move audit records across the action being audited without a clear
reason. An audit log before an action means "attempted." An audit log after
success means "completed." Sliding can swap those meanings while keeping the
same words.

Be careful with cleanup. Moving resource release later can extend the time
secrets remain in memory or on disk. Moving it earlier can break later
redaction or deletion. In languages with deterministic destruction, statement
placement can be a privacy control.

When statement order is part of a security invariant, write that invariant as a
test. The test should name the order directly: validate before query, authorize
before load, redact before log, audit after commit, release after final use.

## Code examples

The examples use Python, Go, and Rust because each language makes a different
aspect visible. Python shows a pure local calculation and an executable
behavior check. Go shows the common `err` and declaration-near-use style. Rust
shows how moving a derived value can keep borrowing simple. Each sample was run
or compiled locally with the tool named in the language heading.

### Python

Run with `python3`.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class PricingPlan:
    unit_price: int


@dataclass(frozen=True)
class Order:
    units: int


def charge_before(plan: PricingPlan, order: Order) -> int:
    charge = 0
    minimum_charge = 5
    unit_price = plan.unit_price
    charge = order.units * unit_price
    return max(charge, minimum_charge)


def charge_after(plan: PricingPlan, order: Order) -> int:
    unit_price = plan.unit_price
    charge = 0
    minimum_charge = 5
    charge = order.units * unit_price
    return max(charge, minimum_charge)


if __name__ == "__main__":
    plan = PricingPlan(unit_price=7)
    order = Order(units=3)
    assert charge_before(plan, order) == charge_after(plan, order)
    print(charge_after(plan, order))
```

### Go

Run with `go run`.

```go
package main

import "fmt"

type Plan struct {
	UnitPrice int
}

type Order struct {
	Units int
}

func chargeBefore(plan Plan, order Order) int {
	total := 0
	minimum := 5
	unitPrice := plan.UnitPrice
	total = order.Units * unitPrice
	if total < minimum {
		return minimum
	}
	return total
}

func chargeAfter(plan Plan, order Order) int {
	unitPrice := plan.UnitPrice
	total := 0
	minimum := 5
	total = order.Units * unitPrice
	if total < minimum {
		return minimum
	}
	return total
}

func main() {
	plan := Plan{UnitPrice: 7}
	order := Order{Units: 3}
	if chargeBefore(plan, order) != chargeAfter(plan, order) {
		panic("slide changed behavior")
	}
	fmt.Println(chargeAfter(plan, order))
}
```

### Rust

Compile and run with `rustc`.

```rust
#[derive(Clone, Copy)]
struct Plan {
    unit_price: i32,
}

#[derive(Clone, Copy)]
struct Order {
    units: i32,
}

fn charge_before(plan: Plan, order: Order) -> i32 {
    let minimum = 5;
    let unit_price = plan.unit_price;
    let total = order.units * unit_price;
    total.max(minimum)
}

fn charge_after(plan: Plan, order: Order) -> i32 {
    let unit_price = plan.unit_price;
    let minimum = 5;
    let total = order.units * unit_price;
    total.max(minimum)
}

fn main() {
    let plan = Plan { unit_price: 7 };
    let order = Order { units: 3 };
    assert_eq!(charge_before(plan, order), charge_after(plan, order));
    println!("{}", charge_after(plan, order));
}
```

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*, 2nd
   edition. Addison-Wesley, 2018. Chapter 8, "Moving Features," section "Slide
   Statements." Source for the canonical name and catalog placement.
2. Martin Fowler. "Slide Statements." Refactoring catalog.
   https://refactoring.com/catalog/slideStatements.html. Verified 2026-08-02.
   Source for the public catalog entry, alias listing, and example shape.
3. Martin Fowler. "Changes for the 2nd Edition of Refactoring."
   https://martinfowler.com/articles/refactoring-2nd-changes.html. Verified
   2026-08-02. Source for the replacement of Consolidate Duplicate Conditional
   Fragments by Slide Statements.
4. Martin Fowler. "Refactoring."
   https://www.martinfowler.com/books/refactoring.html. Verified 2026-08-02.
   Source for the second-edition publication context and public description of
   refactoring as small behavior-preserving transformations.
5. GNOME. "commits-list 2017-March Archive by Date."
   https://mail.gnome.org/archives/commits-list/2017-March/date.html. Verified
   2026-08-02. Source for the librsvg `marker.rs` production use.
6. EngineHub. "WorldEdit Builds, branch improve-hollow."
   https://builds.enginehub.org/job/worldedit?branch=improve-hollow. Verified
   2026-08-02. Source for the WorldEdit `EditSession.hollowOutRegion`
   production use.
7. LLVM Project. "LLVM's Analysis and Transform Passes."
   https://llvm.org/docs/Passes.html. Verified 2026-08-02. Source for the
   `sink` pass production compiler analogue.
8. LLVM Project. "`MachineSink.cpp` Source File."
   https://llvm.org/doxygen/MachineSink_8cpp_source.html. Verified 2026-08-02.
   Source for machine-instruction sinking safety checks and register-pressure
   comments.
9. Standard ML of New Jersey project. "Standard ML of New Jersey Change Log."
   https://www.smlnj.org/dist/working/110.80/HISTORY.html. Verified
   2026-08-02. Source for the MLRiscGen use-site code motion analogue.
