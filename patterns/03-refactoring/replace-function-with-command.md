---
name: Replace Function with Command
slug: replace-function-with-command
family: 03-refactoring
category: Refactoring
aliases: [Replace Method with Method Object, Function to Command, Method Object]
first_described: "Fowler 1999 as Replace Method with Method Object"
maturity: canonical
related: [replace-command-with-function, extract-function, move-function, introduce-parameter-object, preserve-whole-object, command]
incompatible_with: [replace-command-with-function]
verified: 2026-08-02
---

# Replace Function with Command

## 1. Name, aliases, and lineage

The canonical name in this repository is **Replace Function with Command**.
Martin Fowler's public catalog page uses that name, shows a `score` function
turned into a `Scorer` class with constructor data and an `execute()` method,
labels **Replace Method with Method Object** as an alias, and names Replace
Command with Function as the inverse
(https://refactoring.com/catalog/replaceFunctionWithCommand.html, verified
2026-08-02). Fowler's article on the second edition states that the first
edition refactoring **Replace Method with Method Object**, listed on page 135
of the first edition, was replaced by **Replace Function with Command**
(https://martinfowler.com/articles/refactoring-2nd-changes.html, verified
2026-08-02).

The earlier name comes from Martin Fowler, Kent Beck, John Brant, William
Opdyke, and Don Roberts, *Refactoring. Improving the Design of Existing Code*,
1st edition, Addison-Wesley, 1999, chapter 6, "Composing Methods", section
"Replace Method with Method Object." The second edition moves the catalog to
JavaScript and uses the broader word **Function**, because the source operation
may be a free function, a method, a local function, or a module-level
procedure. See Martin Fowler, *Refactoring. Improving the Design of Existing
Code*, 2nd edition, Addison-Wesley, 2018, chapter 11, "Refactoring APIs",
section "Replace Function with Command."

The word **Command** needs care. In this refactoring, a command is an object
that wraps one operation and exposes an execution method such as `execute`,
`run`, `call`, `perform`, `handle`, or `__invoke`. That shape overlaps with the
Gang of Four Command pattern, described by Erich Gamma, Richard Helm, Ralph
Johnson, and John Vlissides, *Design Patterns. Elements of Reusable
Object-Oriented Software*, Addison-Wesley, 1994, chapter 5, "Behavioral
Patterns", section "Command." It is not always the full GoF pattern. A method
object may exist only to make a long function easier to split. A full Command
participant may also be queued, logged, undone, retried, serialized, or invoked
by a separate invoker. This entry covers the refactoring move into that object
shape, then explains when the richer pattern has or has not been reached.

Common aliases are **Function to Command**, **Method Object**, and **Replace
Method with Method Object**. The old name remains common in object-oriented
teams because it describes the mechanical move: a method body becomes a class,
and local variables become fields. The newer name is more useful in languages
where functions are first-class and the source code may not have a method
owner.

## 2. Problem and context

A function has outgrown the flat shape that once made it clear. It has many
local variables, several branches that share intermediate state, and helper
logic that cannot be extracted cleanly because every helper would need a long
parameter list. The caller still wants one operation, but the implementation
needs smaller private steps and a place to keep intermediate values while those
steps cooperate.

The code usually feels trapped. A developer tries Extract Function, but the
candidate block reads or writes six locals. Passing all six locals makes the
new helper noisy, and returning all changed values makes it worse. Leaving the
function intact produces a long calculation where a reader must keep every
temporary variable in working memory. Moving the whole operation into a new
object gives those locals a short-lived home. Once they are fields, the new
object can grow private helper methods without threading a dozen parameters
through every call.

The context is refactoring, so the first target is behavior preservation, not a
new abstraction for its own sake. The new object starts as a mechanical wrapper
around the old function. The caller passes the same inputs to a constructor or
factory, calls one execution method, and receives the same result. After that
move, the author can split the execution method into private methods, introduce
clear names for phases, and remove temporary variables that no longer need to
span the full operation.

This refactoring also appears when a function needs operation-level state that
should not be global and should not pollute the old host class. Examples
include a parser step with a cursor and diagnostics, a scorer with several
partial totals, a bulk importer with counters and row-level errors, or a
planner that accumulates decisions before returning a plan. Engineering
judgement. In each case, the object is a workbench for one invocation. It should
make the operation smaller inside, not make every caller learn a new lifecycle.

The command may later become a real domain abstraction. If it gains retries,
authorization, audit fields, queuing, undo, cancellation, or serialization, it
has crossed from temporary method object into production command. That can be a
good outcome, but it should be an explicit design decision, not an accidental
side effect of moving code out of a long function.

## 3. Forces

Engineering judgement. This section weighs the pressures that drive or resist
the refactoring.

- **Cognitive load.** The refactoring favors the maintainer inside the
  operation. Private helper methods can read shared fields instead of accepting
  long parameter lists. It sacrifices call-site simplicity, because a direct
  function call becomes object construction plus execution.
- **Coupling.** The move can reduce coupling inside the old host class by
  moving specialized calculation state out of it. It can increase coupling for
  callers if they now name a concrete command class rather than a stable
  function.
- **Consistency.** Fields give one place to hold invocation state across phases.
  That favors consistency when several helpers must read the same derived
  values. It sacrifices the discipline of explicit inputs and outputs between
  helpers.
- **Latency and allocation cost.** The pattern sacrifices one allocation per
  invocation in most implementations. That cost is noise for an expensive
  import, parse, or network operation, and it can be wrong in a tight numeric
  loop.
- **Operability.** A command object gives a natural label for logs, traces,
  metrics, and audit events. It can carry run identifiers, retry counts, and
  phase names. The cost is that a simple operation can look like a durable unit
  of work even when it is not.
- **Cost of change.** The move favors change inside the operation. New helper
  methods become cheap to add. It sacrifices deletion cost if the command class
  leaks into a public API or gets registered in a framework.
- **Team topology.** The refactoring favors teams that own the old function and
  its callers. It becomes harder when the function is public, because external
  callers may not want a command lifecycle.
- **Test design.** The command can make phase-level tests possible by exposing
  private behavior through a public execution method and observable result. It
  can also tempt teams into testing internal methods, which makes later cleanup
  harder.

The pattern favors local decomposition, operation state, and lifecycle
metadata. It pays for that with extra type count, extra allocation, and a less
direct call site.

## 4. Applicability and non-applicability

Reach for Replace Function with Command when the following conditions hold.

- A function is long because many temporary variables are shared across blocks.
- Extract Function would require a long parameter list or awkward tuple returns.
- Several small helper methods would make the operation clear if they could
  share invocation state.
- The operation has a natural noun name, such as `Scorer`, `InvoiceImporter`,
  `SchedulePlanner`, or `BatchValidator`.
- The state is scoped to one invocation, not to the lifetime of the application.
- The operation may soon need progress reporting, cancellation, retry policy,
  audit data, or tracing labels.
- The current host class is gaining fields that only make sense while one
  method runs.
- The caller can keep a compatibility wrapper, so the external API need not
  change during the first refactoring step.

Do not apply it in these cases.

- **The function is already short and clear.** A command class adds ceremony
  without buying decomposition. Prefer leaving the direct call in place.
- **The problem is one missing parameter object.** If the function has many
  parameters that always travel together, Introduce Parameter Object or
  Preserve Whole Object is the smaller move.
- **The function belongs on one of its parameters.** Feature envy calls for Move
  Function, not a new command class.
- **The function is a pure formula on primitive values.** A direct function is
  easier to read, memoize, test, and inline.
- **The command would expose only constructor and `execute`.** That may be a
  useful intermediate state during refactoring, but it is not a good final
  shape unless lifecycle or framework integration exists.
- **The language's closure support solves the state problem.** A local closure
  can share variables with its parent in TypeScript, Python, Swift, Go, and
  Rust. Prefer the closure when the helper functions do not need names outside
  the source function.
- **The operation must be transparent in a public API.** Replacing
  `calculate(price, tax)` with `new TaxCalculation(price, tax).execute()` is a
  breaking and noisier API unless the object has a real public lifecycle.
- **The operation is a hot path where allocation matters.** Measure first. A
  command per element in a parser or renderer can create avoidable allocation
  pressure.
- **The state is shared across users or requests.** A command object should not
  become a hidden singleton. Use a service, actor, or repository with a stated
  lifetime.
- **The goal is polymorphic dispatch.** If the operation varies by type, Replace
  Conditional with Polymorphism may be the better primary refactoring. Command
  can be one implementation shape, not the whole answer.
- **The goal is undo.** Use the Command pattern deliberately. Store enough data
  to reverse or compensate the action, and name the invoker and receiver.

## 5. Structure

Before the refactoring, the structure has these participants.

- **Caller.** Code that invokes the original function or method.
- **Source function.** The operation with too many locals, phases, or temporary
  values. It may be a free function or a method on an existing host.
- **Invocation inputs.** Parameters and source-object fields read by the
  function.
- **Temporary variables.** Values created during execution and shared by
  several blocks.
- **Result.** The returned value, raised error, output record, or external
  effect produced by the function.

After the refactoring, the structure has these participants.

- **Compatibility wrapper.** The old function, kept at first. It constructs the
  command, calls the execution method, and returns the result.
- **Command object.** A new class or struct with fields for invocation inputs
  and selected temporary variables.
- **Execution method.** The public method that preserves the old operation's
  behavior. Its name is usually `execute`, `run`, `call`, `perform`, `handle`,
  or the language's callable hook.
- **Private phase methods.** Small methods extracted from the old function once
  state has a home.
- **Receiver or collaborator.** Any existing service or domain object the
  command calls to do work. In the full GoF Command pattern this role is called
  the receiver, per Gamma, Helm, Johnson, and Vlissides, *Design Patterns*,
  chapter 5, section "Command."

The key structural move is lifetime control. Variables that were trapped inside
one large function become fields on an object whose lifetime matches one
operation. That move is useful only when the fields let the implementation
split into named phases. If no phase methods appear after the move, the command
is probably a refactoring scaffold that should be removed by Replace Command
with Function.

## 6. ASCII structure diagram

```text
Before

  +----------------------+             +-----------------------------+
  |        Caller        | ----------> |       source function       |
  |----------------------|    call     |-----------------------------|
  | needs one result     |             | params                      |
  +----------------------+             | temp a, temp b, temp c      |
                                       | long body with many phases  |
                                       +--------------+--------------+
                                                      |
                                                      v
                                            +------------------+
                                            |      Result      |
                                            +------------------+

After

  +----------------------+             +-----------------------------+
  |        Caller        | ----------> |   compatibility wrapper     |
  +----------------------+    call     +--------------+--------------+
                                                      |
                                                      | constructs
                                                      v
                                       +-----------------------------+
                                       |       Command object        |
                                       |-----------------------------|
                                       | input fields                |
                                       | phase state fields          |
                                       | execute()                   |
                                       | parseInputs()               |
                                       | scoreRules()                |
                                       | buildResult()               |
                                       +--------------+--------------+
                                                      |
                                                      v
                                            +------------------+
                                            |      Result      |
                                            +------------------+
```

## 7. Dynamics

Runtime interaction is simple at first, then the internal flow becomes clearer
as phase methods are extracted.

```text
Caller          Wrapper function       Command object        Collaborator
  |                    |                     |                    |
  |-- score(args) ---->|                     |                    |
  |                    |-- new Command(args) -------------------->|
  |                    |<--------------------|                    |
  |                    |-- execute() ------->|                    |
  |                    |                     |-- loadInputs()     |
  |                    |                     |-- deriveFacts()    |
  |                    |                     |-- ask service ---->|
  |                    |                     |<-- service data ---|
  |                    |                     |-- buildResult()    |
  |                    |<-- result ----------|                    |
  |<-- result ---------|                     |                    |
```

Two timing rules matter. First, populate fields before `execute()` starts, then
treat them as invocation state. Mutating them during phases is acceptable when
it replaces tangled locals, but those mutations should not leak after the
result is returned. Second, do not reuse one command instance for several
invocations unless that is the chosen design. A reusable command turns
invocation state into object state, which is a different pattern with different
failure modes.

The wrapper is tactical. It keeps callers stable while the command is carved
out. Later, the wrapper may remain as the public API, or callers may be moved to
construct commands directly because a queue, scheduler, or invoker needs the
object.

## 8. Implementation variants

**Method object for decomposition.** The new class is private or package-local.
It exists to split one long function into methods. This is the closest variant
to Fowler's first edition "Replace Method with Method Object" chapter entry.
It is low risk when the old function remains as a wrapper. Its cost is a type
that may outlive the reason it was created.

**Public command for lifecycle.** The command becomes part of the public model.
Callers create it, pass it to an invoker, or place it on a queue. This variant
can carry audit id, actor id, idempotency key, retry policy, and cancellation
token. It costs more API surface and must be versioned.

**Callable object.** Python's `__call__`, Swift's `callAsFunction`, Rust's
closure traits, and Java's `Callable` or `Runnable` let an object be invoked
like a function or through a small standard interface. This keeps call sites
compact while still giving the operation fields and helper methods.

**Struct command.** Go and Rust often use a struct with a method such as `Run`
or `execute`. There is no inheritance requirement. The command is a value that
owns inputs and mutable working state. This variant fits command-line tools,
batch jobs, and parsers.

**Nested local class or closure pair.** Some languages allow a local class or
closures inside the old function. This keeps the new structure near the old
call site. It is useful when the command should not become a reusable type.
The trade is weaker tool support and less room for tests that name the command.

**Dependency-injected command handler.** Application frameworks often split a
serializable command message from a handler object. That is not the exact
mechanical refactoring in Fowler, but it is a common destination. The message
holds data. The handler has collaborators and a `handle` method. It suits
systems where commands cross a process boundary.

**Framework command class.** CLI, queue, and job frameworks may require a class
with a specific method. Rails Active Job uses job classes with `perform`; the
Rails guide describes Active Job as a framework for declaring and executing
background jobs and shows `retry_on` and `discard_on` around `perform`
(https://guides.rubyonrails.org/active_job_basics.html, verified
2026-08-02). Django management commands require subclasses of `BaseCommand` to
implement `handle()` and provide parser, system check, and output behavior
(https://docs.djangoproject.com/en/4.2/howto/custom-management-commands/,
verified 2026-08-02). In these cases the framework contract chooses the shape.

**Immutable command.** Constructor fields are final or read-only, and phase
methods return new values rather than mutating fields. This preserves much of
the clarity of a function while giving helper methods a home. It can become
verbose when many derived values must be returned between phases.

**Mutable workbench command.** Inputs are read-only, but intermediate values
are fields assigned by phases. This is the variant that breaks the local
variable knot. It is also the variant most likely to create order coupling
between private methods, so phase method names and execution order must be
plain.

## 9. Known production uses

**Ruby on Rails Active Job.** Rails documents Active Job as a framework for
declaring background jobs and executing them on a queue backend. A job is
written as a class, and the guide shows job lifecycle features such as
callbacks, bulk enqueueing, and `retry_on` or `discard_on` declarations around
the `perform` method (https://guides.rubyonrails.org/active_job_basics.html,
verified 2026-08-02). Engineering judgement. This is a production command
object shape: work that could be written as a function is represented by a
class because queueing, retries, callbacks, priority, and execution context
matter.

**Celery task classes.** Celery's task documentation says all tasks inherit
from `app.Task`, that the `run()` method becomes the task body, and that a
decorated function is represented roughly as a generated task class. It also
states that a task object is registered as a global instance rather than
instantiated for every request, and gives a base task class that caches a
database connection (https://docs.celeryq.dev/en/stable/userguide/tasks.html,
verified 2026-08-02). Engineering judgement. Celery is a named production use
of the command-object destination because a callable unit gains identity,
registry membership, retry behavior, request context, and process lifetime.

**Django management commands.** Django's documentation has a section named
"Command objects." It states that `BaseCommand` is the base class for
management commands, that subclasses must implement `handle()`, and that the
base class supplies parser creation, system checks, error handling, style, and
standard command options
(https://docs.djangoproject.com/en/4.2/howto/custom-management-commands/,
verified 2026-08-02). Engineering judgement. Django uses the command object
shape because command-line work needs more than a plain function: parser
configuration, framework checks, output channels, and a uniform invocation
protocol.

**Symfony Console commands.** Symfony's Console documentation defines commands
as classes and describes a lifecycle with `initialize`, `interact`, and
`__invoke()` or `execute()`; it also documents method-based commands in Symfony
8.1 as a newer callable alternative
(https://symfony.com/doc/current/console.html, verified 2026-08-02).
Engineering judgement. Symfony shows both sides of the trade: command classes
when lifecycle hooks are useful, and method-based callables when a full class
would carry more ceremony than the operation needs.

## 10. Consequences

Positive.

- A long function can be split into named private phases without long helper
  signatures.
- Temporary variables with shared lifetime get a defined owner.
- The old host class loses fields and helper methods that only existed for one
  operation.
- A command object gives instrumentation a stable operation name and a place to
  store run context.
- If the operation later needs queueing, retry, cancellation, undo, or audit, a
  command object is already a plausible host.
- The old function can remain as a wrapper, which lowers migration risk.

Negative.

- The call site becomes less direct. Readers see construction and execution
  instead of one call.
- One operation now has one more type, and many such moves can produce a
  directory full of tiny classes.
- Mutable fields can hide data flow that function parameters made explicit.
- A command class can be mistaken for a durable domain object even when it is
  only a per-call workbench.
- Allocation cost may matter in tight loops.
- If public callers begin constructing the command, later cleanup becomes an
  API migration rather than a local refactoring.

## 11. Failure modes and misuse

Engineering judgement. These are failure patterns to watch for in review,
tests, and production telemetry.

**Symptom.** A command instance succeeds on its first call and returns wrong
data on the second. **Cause.** Invocation state is stored in mutable fields, and
the instance is reused after `execute()`. **Fix.** Create a new command per
call, or add an explicit `reset` phase and test two consecutive executions.

**Symptom.** Private phase methods must be called in a hidden order, and a
future edit inserts a call before the field it reads has been assigned.
**Cause.** The refactoring turned local variable order into object field order
without naming the state transitions. **Fix.** Keep `execute()` as the only
orchestrator, group assignments by phase, and return phase result objects when
ordering becomes hard to see.

**Symptom.** A command has one constructor, one `execute` method, no helpers,
and no lifecycle metadata six months after extraction. **Cause.** The method
object was an intermediate scaffold that became permanent. **Fix.** Apply
Replace Command with Function, or inline the command behind the old wrapper.

**Symptom.** Tests assert private helper methods or inspect internal fields.
**Cause.** The new class made internals tempting to test because they now have
names. **Fix.** Test through `execute()` and stable result values. Use private
method tests only during a short refactoring window, then delete them.

**Symptom.** Logs show `execute` everywhere with no way to distinguish the work
being done. **Cause.** The operation name moved into a class, but telemetry
kept a generic method label. **Fix.** Log the command class or operation name,
phase, outcome, and correlation id.

**Symptom.** A queue worker fails to deserialize old commands after a deploy.
**Cause.** A method object became a serialized public command without versioned
payload rules. **Fix.** Separate command message from handler, version the
message shape, and keep old handlers until old queue entries drain.

**Symptom.** A request can trigger thousands of command allocations and heap
pressure rises under load. **Cause.** The refactoring was applied inside a
per-element loop. **Fix.** Move the command to the batch level, or keep the hot
inner operation as a function.

**Symptom.** Authorization checks are split between the caller and command, and
some call paths skip one. **Cause.** The command now has lifecycle meaning, but
security policy stayed at the old function boundary. **Fix.** Put policy at one
boundary, normally before `execute()`, and make direct helper calls impossible
from outside the command.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

<table>
<thead>
<tr>
<th>Force</th>
<th>Replace Function with Command</th>
<th>Extract Function</th>
<th>Introduce Parameter Object</th>
<th>Move Function</th>
<th>GoF Command</th>
</tr>
</thead>
<tbody>
<tr>
<td>Cognitive load</td>
<td>Lower inside a tangled operation, higher at the call site.</td>
<td>Lower when helpers need few values.</td>
<td>Lower when parameters travel together.</td>
<td>Lower when one receiver owns the behavior.</td>
<td>Higher, because invoker, command, and receiver must be understood.</td>
</tr>
<tr>
<td>Coupling</td>
<td>Couples callers to a command class unless a wrapper remains.</td>
<td>Keeps the same owner and API.</td>
<td>Couples callers to a data shape.</td>
<td>Couples behavior to a better domain owner.</td>
<td>Decouples invoker from receiver through a command interface.</td>
</tr>
<tr>
<td>Consistency</td>
<td>Shared fields keep phase state together.</td>
<td>Parameters and returns keep data flow explicit.</td>
<td>Groups related input values.</td>
<td>Uses the receiver's invariants.</td>
<td>Can store request data for later replay.</td>
</tr>
<tr>
<td>Latency</td>
<td>Adds allocation and method dispatch.</td>
<td>No new object needed.</td>
<td>May add one value object.</td>
<td>No new command allocation.</td>
<td>May add allocation, queueing, and persistence.</td>
</tr>
<tr>
<td>Operability</td>
<td>Gives a named unit for logs and phases.</td>
<td>Depends on caller instrumentation.</td>
<td>Gives better input labels, not operation lifecycle.</td>
<td>Uses owner-level telemetry.</td>
<td>Strong when commands are audited, queued, or retried.</td>
</tr>
<tr>
<td>Cost of change</td>
<td>Good for changing internals, worse if public.</td>
<td>Best for local cleanup.</td>
<td>Best for parameter churn.</td>
<td>Best when ownership was wrong.</td>
<td>Best for adding invokers, undo, queues, or logs.</td>
</tr>
<tr>
<td>Team topology</td>
<td>Works best when one team owns callers and callee.</td>
<td>Local to one owner.</td>
<td>Requires agreement on the value object.</td>
<td>Requires the receiver-owning team to accept behavior.</td>
<td>Fits platform teams exposing an invocation protocol.</td>
</tr>
</tbody>
</table>

Reading of the matrix. Replace Function with Command wins when the obstacle is
local decomposition under shared temporary state. Extract Function wins when
data flow is already small. Introduce Parameter Object wins when the parameter
list, not the body shape, is the real issue. Move Function wins when behavior
belongs to an existing domain object. The GoF Command pattern wins when
invocation itself needs to be stored, scheduled, reversed, or mediated.

## 13. Related and incompatible patterns

- **Replace Command with Function.** This is the inverse cleanup. Apply it when
  the command object no longer has helpers, lifecycle, framework integration,
  or identity.
- **Extract Function.** This is often attempted first. If extraction fails
  because too many locals must cross the helper boundary, command extraction
  gives those locals a field-level home.
- **Introduce Parameter Object.** This is the smaller move when many inputs are
  related. It composes well with command extraction: the command constructor
  can accept one parameter object rather than many scalar values.
- **Preserve Whole Object.** This can reduce constructor noise by passing a
  domain object instead of several values read from it. Use it when the command
  already needs the domain object's concept, not only its primitive fields.
- **Move Function.** This may replace the refactoring. If the operation mainly
  uses one parameter's data, move the behavior to that type.
- **Command.** The GoF pattern is a richer destination. Replace Function with
  Command creates an object that may later participate in a full command
  protocol with invoker and receiver roles.
- **Template Method.** A command with a fixed `execute()` skeleton and overriden
  phase methods becomes Template Method. That combination can be useful in
  frameworks, but it is heavy for local refactoring.
- **Strategy.** Strategy replaces an algorithm behind a stable interface.
  Command wraps one invocation. If there are several interchangeable operations
  and no per-invocation state, Strategy may read better.
- **Memento.** Memento composes with a reversible command by storing prior
  state for undo. It is unrelated to a short-lived method object with no undo.
- **Service Locator.** This conflicts in practice. A command that pulls hidden
  collaborators from a global locator becomes hard to test and hides required
  dependencies. Prefer constructor injection.

## 14. Refactoring path in and out

Introducing the pattern into existing code.

1. Pick one function whose main problem is shared temporary state. Do not start
   with a public API migration.
2. Add characterization tests around the old function. Keep them at the public
   boundary and capture error cases as well as happy paths.
3. Create a command class named for the operation. Give it a constructor that
   accepts the old function's parameters and any source object it must read.
4. Add an execution method. Copy the old function body into it, with no behavior
   edits.
5. Change the old function to construct the command and call the execution
   method. Run the tests. At this point the public API is unchanged.
6. Promote only the variables that block extraction into fields. Leave narrow,
   local temporaries inside methods.
7. Extract private phase methods from the execution method. Name phases after
   domain work, not after syntax.
8. Replace output fields with a return value or result object unless a framework
   requires field-based output.
9. Add command-level telemetry only if the operation is worth observing as a
   unit. Do not add logs as decoration.
10. Decide whether callers should ever construct the command directly. If not,
   keep it private and keep the wrapper.

Moving out of the pattern.

1. Look for a command class with one execution method, no private phase methods,
   no lifecycle data, and no framework registration.
2. Inline private helpers back into one expression or a few local functions if
   they no longer need fields.
3. Convert constructor fields to function parameters. Preserve the old wrapper
   name where possible.
4. Move the execution body into the function. Run tests.
5. Replace direct command construction with the function call.
6. Delete the command class once no public callers, serializers, job queues, or
   framework registries refer to it.
7. If the class is public, deprecate it first and leave an adapter that delegates
   to the function through the compatibility window.

Named refactorings involved on the way in include Extract Function, Move
Function, Introduce Parameter Object, and Preserve Whole Object. Named
refactorings involved on the way out include Replace Command with Function,
Inline Function, Inline Class, and Remove Dead Code.

## 15. Testing and verification

Engineering judgement. The testing goal is to protect behavior while changing
the shape of the operation.

Before the move, add characterization tests around the old function. Cover
normal output, boundary input, error paths, and externally visible side effects.
Those tests should keep passing while the wrapper delegates to the command.

After the move, keep most tests at the wrapper or `execute()` boundary. The
command's private phase methods are implementation details. Testing them
directly is acceptable during a short refactoring window if a phase is hard to
stabilize, but those tests should be deleted or moved back to public behavior
tests before the command is treated as finished.

Useful techniques.

- **Golden master tests.** For formatters, scorers, and converters, capture old
  outputs for representative inputs, then compare the command result to those
  outputs while refactoring internals.
- **Spy collaborator.** If the command calls a service, inject a small fake that
  records calls. This verifies call order and arguments without exposing command
  fields.
- **Result object assertions.** If the old function used output parameters or
  mutated fields, introduce a result object and assert its fields directly.
- **Two-run test.** Execute the same command instance twice only if reuse is
  supported. Otherwise test that callers create a fresh command per run.
- **Property tests.** For scoring and validation commands, assert invariants
  across many generated inputs, such as "invalid inputs never produce approved
  results."
- **Contract tests for framework commands.** For Rails, Celery, Django, or
  Symfony style commands, test through the framework's invocation helper where
  practical, because the framework supplies parsing, retry, queue, or output
  behavior.

What became easier. The operation now has a named unit for testing phase-level
behavior through one public call. Collaborators can be constructor-injected.
State that was implicit in a long method can be observed through a result.

What became harder. A reader must know whether a command instance is single-use.
Mutation between phase methods can hide data flow. Framework command classes may
need integration tests because direct calls to `execute()` or `handle()` skip
framework behavior.

## 16. Observability signals

Engineering judgement. A command object is a natural unit of work, so telemetry
should answer four questions: which command ran, who or what asked for it, how
far it got, and what result it produced.

Record these fields for commands that matter in production.

- Command name or class.
- Invocation id or correlation id.
- Actor id, tenant id, or job id when those identifiers are already permitted in
  telemetry.
- Start time, duration, and outcome.
- Phase name for long commands.
- Retry attempt and prior failure class for queued commands.
- Input size, not raw input, for bulk operations.
- Result class or status code.

Healthy telemetry shows command duration within its service budget, stable
success rate, a small and expected retry rate, and phase timings that match the
known cost of the work. For queue-backed commands, enqueue lag and execution
duration should be separated. A slow queue and a slow command are different
incidents.

Failing telemetry often has one of these shapes. A command enters a phase and
never exits, which points to a missing timeout or blocking collaborator. Retry
attempts rise with the same error class, which points to a deterministic bug
rather than a transient fault. Input-size labels rise before duration rises,
which points to batch growth. A command name appears in production that should
be test-only, which points to registration or packaging drift.

Do not log all constructor fields by default. A command often collects data
that used to be scattered across a function, and that can include personal data
or secrets. Prefer sizes, ids, and enum-like labels over raw payloads.

## 17. Security and privacy implications

Engineering judgement. The refactoring is security-neutral when the command is
private, short-lived, and called only by the old wrapper. Risks appear when the
command becomes a public invocation unit.

**Authorization boundary.** A function often relies on its caller to check
permission. Once it becomes a command, more callers may discover it and invoke
it. Put authorization at the command boundary or keep the constructor private
behind an authorized wrapper.

**Replay and idempotency.** A queued or serialized command can run later, run
twice, or run after the world has changed. Commands that change state should
carry an idempotency key or derive one from stable business data. They should
also re-check permissions and preconditions at execution time.

**Deserialization.** If commands cross process boundaries, never deserialize
arbitrary classes from untrusted input. Use a small message schema, map message
type to a known handler, and reject unknown fields or versions. The refactoring
itself does not require serialization, so adding it should be a separate design
choice.

**Sensitive fields.** Temporary variables promoted to fields become easier to
dump in logs, debugger views, traces, and error reports. Treat command fields as
data inventory. Redact tokens, credentials, health data, payment data, and raw
customer text before logging.

**Dependency injection.** Commands often gain collaborators through the
constructor. That is good for tests, but a framework container can also inject a
broader service than the command needs. Prefer narrow interfaces so the command
cannot perform unrelated actions.

**Confused deputy risk.** A command invoked by a scheduler or worker may run
with service credentials rather than the original user's authority. Include the
actor or tenant context in the command message and check it before performing
state changes.

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*. 2nd
   edition. Addison-Wesley, 2018. Chapter 11, "Refactoring APIs", section
   "Replace Function with Command." Source for the canonical second edition
   name and inverse relationship.
2. Martin Fowler, Kent Beck, John Brant, William Opdyke, Don Roberts.
   *Refactoring. Improving the Design of Existing Code*. 1st edition.
   Addison-Wesley, 1999. Chapter 6, "Composing Methods", section "Replace
   Method with Method Object." Source for the earlier name and method-object
   mechanics.
3. Martin Fowler. "Replace Function with Command."
   https://refactoring.com/catalog/replaceFunctionWithCommand.html
   Verified 2026-08-02. Source for the public catalog name, alias, example
   shape, and inverse link.
4. Martin Fowler. "Changes for the 2nd Edition of Refactoring."
   https://martinfowler.com/articles/refactoring-2nd-changes.html
   Verified 2026-08-02. Source for the mapping from first edition Replace
   Method with Method Object to second edition Replace Function with Command.
5. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   Chapter 5, "Behavioral Patterns", section "Command." Source for the related
   GoF Command roles and distinction.
6. Ruby on Rails Guides. "Active Job Basics."
   https://guides.rubyonrails.org/active_job_basics.html
   Verified 2026-08-02. Source for Active Job classes, `perform`, callbacks,
   retry, discard, and queue behavior.
7. Celery Project. "Tasks. Celery 5.6.3 documentation."
   https://docs.celeryq.dev/en/stable/userguide/tasks.html
   Verified 2026-08-02. Source for task classes, `run()`, registry behavior,
   and task instance lifetime.
8. Django Software Foundation. "How to create custom django-admin commands."
   https://docs.djangoproject.com/en/4.2/howto/custom-management-commands/
   Verified 2026-08-02. Source for `BaseCommand`, `handle()`, parser behavior,
   system checks, and command output behavior.
9. Symfony. "Console Commands."
   https://symfony.com/doc/current/console.html
   Verified 2026-08-02. Source for Console command classes, lifecycle methods,
   and method-based commands.

## Code examples

Three languages are shown because they represent different idioms. TypeScript
shows the common class extraction from a scoring function. Python shows a
callable object, which keeps function-like invocation while giving state a
home. Go shows the command-as-struct form used in languages without classical
inheritance.

### TypeScript

```typescript
type Candidate = {
  years: number;
  incidents: number;
  certifications: number;
};

type Guide = {
  incidentPenalty: number;
  certificationBonus: number;
};

class CandidateScorer {
  private score = 0;

  constructor(
    private readonly candidate: Candidate,
    private readonly guide: Guide,
  ) {}

  execute(): number {
    this.score = this.baseScore();
    this.applyIncidents();
    this.applyCertifications();
    return Math.max(0, this.score);
  }

  private baseScore(): number {
    return this.candidate.years * 10;
  }

  private applyIncidents(): void {
    this.score -= this.candidate.incidents * this.guide.incidentPenalty;
  }

  private applyCertifications(): void {
    this.score +=
      this.candidate.certifications * this.guide.certificationBonus;
  }
}

function scoreCandidate(candidate: Candidate, guide: Guide): number {
  return new CandidateScorer(candidate, guide).execute();
}

console.log(
  scoreCandidate(
    { years: 4, incidents: 1, certifications: 2 },
    { incidentPenalty: 7, certificationBonus: 3 },
  ),
);
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ImportRow:
    sku: str
    quantity: int
    unit_price: int


class InvoiceImport:
    def __init__(self, rows: list[ImportRow]) -> None:
        self.rows = rows
        self.accepted: list[ImportRow] = []
        self.errors: list[str] = []

    def __call__(self) -> dict[str, int]:
        self._validate_rows()
        subtotal = self._subtotal()
        return {"accepted": len(self.accepted), "errors": len(self.errors),
                "subtotal": subtotal}

    def _validate_rows(self) -> None:
        for row in self.rows:
            if row.quantity <= 0:
                self.errors.append(row.sku)
            else:
                self.accepted.append(row)

    def _subtotal(self) -> int:
        return sum(row.quantity * row.unit_price for row in self.accepted)


def import_invoice(rows: list[ImportRow]) -> dict[str, int]:
    return InvoiceImport(rows)()


if __name__ == "__main__":
    print(import_invoice([
        ImportRow("A-1", 2, 500),
        ImportRow("B-2", 0, 900),
    ]))
```

### Go

```go
package main

import "fmt"

type LineItem struct {
	SKU      string
	Quantity int
	Cents    int
}

type PriceResult struct {
	Accepted   int
	Rejected   int
	TotalCents int
}

type PriceBatchCommand struct {
	items      []LineItem
	accepted   int
	rejected   int
	totalCents int
}

func NewPriceBatchCommand(items []LineItem) *PriceBatchCommand {
	return &PriceBatchCommand{items: items}
}

func (c *PriceBatchCommand) Execute() PriceResult {
	for _, item := range c.items {
		c.apply(item)
	}
	return PriceResult{c.accepted, c.rejected, c.totalCents}
}

func (c *PriceBatchCommand) apply(item LineItem) {
	if item.Quantity <= 0 {
		c.rejected++
		return
	}
	c.accepted++
	c.totalCents += item.Quantity * item.Cents
}

func priceBatch(items []LineItem) PriceResult {
	return NewPriceBatchCommand(items).Execute()
}

func main() {
	result := priceBatch([]LineItem{
		{SKU: "A-1", Quantity: 2, Cents: 500},
		{SKU: "B-2", Quantity: 0, Cents: 900},
	})
	fmt.Println(result)
}
```
