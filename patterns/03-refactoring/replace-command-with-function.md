---
name: Replace Command with Function
slug: replace-command-with-function
family: 03-refactoring
category: Refactoring
aliases: [Replace Command Object with Function, Collapse Command Object]
first_described: "Fowler 2018"
maturity: canonical
related: [replace-function-with-command, inline-class, move-function, change-function-declaration, parameterize-function, remove-dead-code]
incompatible_with: [command]
verified: 2026-08-02
---

# Replace Command with Function

## 1. Name, aliases, and lineage

The canonical name is **Replace Command with Function**. Martin Fowler includes
it in *Refactoring. Improving the Design of Existing Code*, 2nd edition,
Addison-Wesley, 2018, chapter 11, "Refactoring APIs." Fowler's public catalog
page shows the move from a `ChargeCalculator` class with constructor data and
an `execute()` method to a `charge(customer, usage)` function, and labels it as
the inverse of Replace Function with Command
(https://refactoring.com/catalog/replaceCommandWithFunction.html, verified
2026-08-02). Fowler's public note on changes for the second edition lists
Replace Command with Function as one of the refactorings newly added in that
edition (https://martinfowler.com/articles/refactoring-2nd-changes.html,
verified 2026-08-02).

The older name one hears in teams is **Replace Command Object with Function**.
That name is useful because it says which object is being removed. In this
entry, **command** means the refactoring sense of a command object, a class that
wraps one operation and exposes a method such as `execute`, `run`, `call`, or
`handle`. It is not the Gang of Four Command pattern in full. The GoF pattern
supports decoupled invocation and can carry undo or queuing behavior. This
refactoring applies when those extra powers are absent or no longer needed.

The inverse refactoring is **Replace Function with Command**. Fowler's catalog
page for that inverse shows a free function moved into a class named `Scorer`
with constructor arguments and an `execute()` method, and records the alias
Replace Method with Method Object
(https://refactoring.com/catalog/replaceFunctionWithCommand.html, verified
2026-08-02). That pairing matters. Replace Function with Command is a good move
when a function has too much temporary state, needs smaller helper methods, or
needs object lifetime. Replace Command with Function is the cleanup move when
that object lifetime has collapsed to parameter passing.

## 2. Problem and context

A codebase has a class whose only purpose is to perform one calculation or one
small action. The caller constructs the class, passes all the data into the
constructor, calls one method, receives the result, and discards the instance.
The class has no independent identity, no long-lived state, no meaningful
collaborators, and no operations that make sense apart from the single call.

The code reads like this. A service method needs a charge. Instead of calling
`charge(customer, usage)`, it creates `new ChargeCalculator(customer, usage)`,
then calls `execute()`. A reader has to open the class to learn that it holds
two constructor fields and multiplies one value by another. The command object
adds ceremony but not domain language. It makes the operation look like a unit
of work with lifecycle, scheduling, or undo, when the real behavior is a pure
calculation.

The context is refactoring, so behavior is meant to stay the same. The target
is not every class with an `execute` method. It is the narrow shape where the
object boundary is no longer earning its cost. The command might have been a
reasonable intermediate step while extracting logic from a long function. It
might have been created because local variables made extraction awkward. It
might have carried helper methods during a difficult change. After the dust
settled, the command may now contain one public operation, no subclassing, no
reuse through a command interface, and no reason for callers to allocate it.

The result is a named function or method with explicit parameters and an
explicit return value. Constructor fields become parameters. The `execute`
method body becomes the function body. Helper methods either become nested
private functions, sibling private functions, or inlined expressions. The call
site becomes a direct call. The system loses a type and keeps the behavior.

This entry uses **function** broadly, matching Fowler's second edition language.
In Java the target may be a static method or an instance method on a better
owner. In Python, TypeScript, Go, Rust, and Swift it may be a free function, a
module function, or a closure. The shape matters more than the syntax.

## 3. Forces

Engineering judgement. This section weighs pressures that are usually present
when the refactoring is considered. The exact balance depends on call volume,
language, tooling, and team norms.

- **Cognitive load.** Replace Command with Function favors the reader who wants
  to know what work happens at the call site. A direct call has a name,
  arguments, and a return type in one expression. A command object splits those
  facts across a constructor and an invocation method.
- **Coupling.** It favors coupling to behavior over coupling to object shape.
  Callers depend on one callable contract instead of a concrete class, its
  constructor, and its method name. It sacrifices the option of satisfying a
  broader command interface without an adapter.
- **Latency and allocation cost.** It favors hot paths that allocate a command
  per call. The win is small for most business code and can be visible in tight
  loops or request middleware that creates a wrapper object for every item.
- **Consistency.** It favors APIs where input and output are explicit. The old
  command can hide results in fields after `execute()`, which invites order
  bugs. The function returns what it computes.
- **Operability.** It sacrifices a natural place to attach per-command metadata
  such as command name, queue id, retry count, or audit status. If those fields
  are used in logs or traces, the function must receive context or the caller
  must instrument the operation.
- **Cost of change.** It favors deleting scaffolding. One less class means fewer
  files, fewer tests for pure delegation, and fewer names to keep aligned. It
  sacrifices a future extension point if the operation later needs lifecycle
  again.
- **Team topology.** It favors teams that own both the caller and the command.
  It is riskier when other teams instantiate the command class, because the
  class may be a published API even if it looks small locally.
- **Test design.** It favors direct unit tests. A function can be tested by
  passing values and checking a return value. It sacrifices tests that depend on
  replacing a command implementation behind a command interface.

The trade is clear. A function is easier to read, cheaper to call, and simpler
to test. A command object is better when the operation needs identity, lifecycle,
or protocol beyond one call.

## 4. Applicability and non-applicability

Reach for Replace Command with Function when these conditions hold.

- The class has one public execution method and no public behavior that is
  meaningful apart from that method.
- The constructor receives the data needed for one execution, and the instance
  is discarded after the call.
- Fields are copied from constructor parameters and are not mutated across
  several calls.
- The result can be returned directly, or a small result object can replace
  output fields.
- The command has no `undo`, `redo`, `cancel`, `retry`, `serialize`,
  `authorize`, or `schedule` behavior.
- No framework requires the concrete command class by reflection,
  configuration, serialization, dependency injection, or a plugin contract.
- Tests already treat the class as an implementation detail rather than a
  published abstraction.
- The function name can say the domain action as well as or better than the
  command class name plus `execute`.

Do not apply it in these cases.

- **The command is a GoF Command participant.** If an invoker stores commands,
  queues them, retries them, logs them as requests, or invokes them without
  knowing their concrete type, the class is doing real design work. Replacing it
  with a function removes the object identity that the pattern needs.
- **Undo or compensation exists.** A command with `undo`, `compensate`, or a
  reversible event record is not only a function call. Keep the object, or split
  a pure calculation out while leaving the command shell intact.
- **The command is serialized.** If instances cross a process boundary, sit in a
  message queue, or are stored for later replay, a function cannot carry that
  payload without a separate message type. In that case the message type is the
  real abstraction.
- **The object carries policy over time.** If fields change between calls, or
  the command tracks attempts, deadlines, idempotency keys, user identity, or
  circuit state, a single function call hides lifecycle that should be visible.
- **A framework constructs it.** Job runners, command buses, dependency
  injection containers, CLI frameworks, and HTTP routers may require a class or
  callable object. Change the framework binding only when the framework supports
  the target shape.
- **Subclasses vary the execution.** If a command hierarchy uses polymorphism to
  select behavior, replacing each class with a separate function may be fine,
  but replacing the hierarchy with one function and a type check is regression.
- **The constructor validates a public invariant.** If callers rely on the type
  to reject invalid combinations before execution, moving to a function may
  delay errors or repeat validation. Keep a value object or parameter object.
- **The function would need a huge parameter list.** A command with many fields
  may be hiding a missing domain object. Prefer Introduce Parameter Object,
  Preserve Whole Object, or Combine Functions into Class before collapsing it.
- **The class name is part of telemetry or audit.** If dashboards, alert routes,
  audit reports, or support tools group behavior by command class, first design
  the replacement labels.
- **The command is published API.** Deleting a public class can be a breaking
  change. Keep an adapter class that delegates to the new function until the
  compatibility window closes.

## 5. Structure

Before the refactoring, the structure has four participants.

- **Caller.** The code that needs the work done. It knows which command class to
  construct and when to call the execution method.
- **Command class.** The wrapper object. It owns constructor fields copied from
  the caller and exposes one execution method.
- **Execution method.** The method named `execute`, `run`, `call`, `handle`, or
  similar. It contains the real calculation or action.
- **Result.** The value returned from the execution method, or the state written
  into an output field that the caller reads after execution.

After the refactoring, the structure has three participants.

- **Caller.** It calls a named function with explicit arguments.
- **Function.** It owns the operation name, receives all required inputs as
  parameters, and returns the result directly.
- **Result.** It remains the same value or becomes a small return object when
  the old command exposed several outputs.

The main relationship change is that construction disappears. Data moves from
object fields to function parameters. The operation name moves from the class
name plus a generic verb to a function name that says the work. If the old class
was `ChargeCalculator` with `execute`, the new function should be `charge`, not
`executeChargeCalculator`.

Helper methods need a separate decision. A helper used only by the old
execution method can become a private function near the new function. A helper
that reads one field from the command often becomes a local expression after the
field turns into a parameter. A helper that is useful elsewhere may deserve to
stay as a named sibling function.

## 6. ASCII structure diagram

```
Before

  +---------------------+       constructs        +----------------------+
  |       Caller        | ----------------------> |    Command class     |
  |---------------------|                         |----------------------|
  | + serviceMethod()   |                         | - inputA             |
  +---------------------+                         | - inputB             |
            |                                      | + execute(): Result  |
            | calls execute                        +----------------------+
            |                                                |
            v                                                v
  +---------------------+                         +----------------------+
  |       Result        | <---------------------- |   Execution method   |
  +---------------------+       returns or reads   +----------------------+


After

  +---------------------+          calls          +----------------------+
  |       Caller        | ----------------------> |       Function       |
  |---------------------|                         |----------------------|
  | + serviceMethod()   |                         | + work(a, b): Result |
  +---------------------+                         +----------------------+
            ^                                                |
            |                                                v
            |                                      +----------------------+
            +------------------------------------- |        Result        |
                         returns directly          +----------------------+
```

## 7. Dynamics

At runtime the old flow uses two steps before doing the work. First the caller
copies values into a new object. Then it sends a generic execution message to
that object. The new flow sends the same values to a named function in one step.

```
Before

Caller                 Command object                  Collaborator
  |                          |                              |
  |-- new Command(a, b) ---->|                              |
  |                          |-- stores a and b in fields   |
  |<-------- instance -------|                              |
  |                          |                              |
  |-- execute() ------------>|                              |
  |                          |-- reads fields               |
  |                          |-- calls helper()             |
  |                          |-- maybe calls collaborator ->|
  |                          |<-----------------------------|
  |<-------- result ---------|                              |
  |                          |                              |

After

Caller                 function work(a, b)              Collaborator
  |                          |                              |
  |-- work(a, b) ---------->|                              |
  |                          |-- reads parameters           |
  |                          |-- calls helper()             |
  |                          |-- maybe calls collaborator ->|
  |                          |<-----------------------------|
  |<-------- result ---------|                              |
  |                          |                              |
```

The behavior-preserving part is that the same values enter the same statements
in the same order. The design-changing part is that the temporary object no
longer exists. If the old command was observable through identity, class name,
or lifecycle hooks, that observation must be recreated on purpose or the
refactoring is not behavior-preserving from the system's point of view.

## 8. Implementation variants

**Pure function.** The safest target is a pure function. Every constructor field
turns into a parameter, the return value is explicit, and no hidden mutation
remains. This is the best fit for calculations, formatting, parsing, scoring,
validation, and mapping.

**Module or package private function.** In languages with modules, the function
can stay private to the module that used to hold the command. This keeps the
public API small while still removing the object. Python modules, Go packages,
Rust modules, and Swift files all support some form of this locality.

**Static method on an existing owner.** In Java, a static method on a utility
class or domain type can be the cleanest home when the operation has no need
for instance state. Use this sparingly. A static dumping ground can become the
same smell in another shape.

**Instance method on a better owner.** If the old command spent most of its
time reading one parameter, Move Function may be a better end state. For
example, `new PremiumCharge(customer, usage).execute()` may become
`customer.chargeFor(usage)` when charge policy belongs to the customer type.

**Closure that captures stable dependencies.** A command may exist because it
needs a repository, clock, logger, or pricing table. If that dependency is
stable across many calls and the per-call data is small, use a function factory
that returns a closure. The created closure carries the dependency, while each
call passes request data explicitly.

**Callable object retained as adapter.** For a published API, keep the old
class as a thin adapter:
`execute()` delegates to the new function. Mark the class deprecated in the
normal project style. This gives clients time to migrate and lets new code use
the function immediately.

**Function plus parameter object.** A command with many constructor fields can
be replaced by a function that takes one value object. This is not a retreat
from the refactoring if the value object has domain meaning. It is a retreat if
the parameter object is named `CommandData` and exists only to avoid a long
argument list.

**Function plus result object.** Some commands write multiple public fields
after execution. Replace those fields with a returned record, tuple, struct, or
small class. That makes call order explicit. The caller cannot read a result
before the function returns.

**Framework callback.** Some frameworks already prefer functions over command
classes. Click documents that command line commands are commonly declared by
decorating functions, while its lower-level non-decorator interface is reserved
for advanced use (https://click.palletsprojects.com/en/stable/quickstart/,
verified 2026-08-02). Flask documents route registration through view functions
and says the `route()` decorator is a shortcut for registering a function with a
URL rule (https://flask.palletsprojects.com/en/stable/api/, verified
2026-08-02). When moving a local command into such a framework, the target may
be the framework's function callback shape.

## 9. Known production uses

**Click command callbacks.** Click is a Python framework for command line
interfaces. Its quickstart says command declaration is based on decorators and
that decorating a function with `command()` turns it into a callable command
line tool. The API reference says `click.command` creates a `Command` and uses
the decorated function as the callback
(https://click.palletsprojects.com/en/stable/quickstart/ and
https://click.palletsprojects.com/en/stable/api/, verified 2026-08-02). This is
the production version of the target shape: user code is a function, while the
framework supplies any command wrapper it needs.

**Black's `main` command.** The Black formatter uses Click. Its source imports
`click`, applies `@click.command(...)` and many `@click.option(...)` decorators
to a function named `main`, then runs the formatter from that function
(https://github.com/psf/black/blob/main/src/black/__init__.py, verified
2026-08-02). The named production use is Black's command line entry point, where
the application behavior is expressed as a function callback rather than as a
handwritten one-off command class.

**Flask view functions.** Flask maps routes to view functions. Its quickstart
shows a minimal app where `@app.route("/")` attaches a URL to a function that
returns the response, and the API reference states that `route()` is a shortcut
for `add_url_rule(..., view_func=index)`
(https://flask.palletsprojects.com/en/stable/quickstart/ and
https://flask.palletsprojects.com/en/stable/api/, verified 2026-08-02). The
production use is Flask's request dispatch model for ordinary endpoints: a
function is the unit of behavior.

**React function components.** React supports class components but its reference
documentation recommends defining components as functions for new code, and
its learning documentation introduces a component as a JavaScript function that
returns markup (https://react.dev/reference/react/Component and
https://react.dev/learn/your-first-component, verified 2026-08-02). The named
production use is React's function component model: a render command object is
often replaced by a plain function when local lifecycle is not needed.

## 10. Consequences

Engineering judgement. Consequences here describe normal codebase effects, not
guarantees.

Positive.

- The operation becomes easier to scan. The call site names the operation and
  shows every input in the argument list.
- Allocation disappears for commands that were created only for one call.
- The number of files and public names falls. Navigation gets shorter.
- Tests can call the function directly without building an object in the exact
  constructor shape used by production.
- Output becomes explicit when result fields are changed into return values.
- Helper functions can be named after substeps rather than hidden behind a
  one-off object's private method list.
- The refactoring makes accidental ceremony visible. If the function still
  needs ten inputs, the real smell is no longer hidden in constructor fields.

Negative.

- A class-level extension point disappears. Code that replaced the command with
  a subclass or mock now needs a function parameter, interface, or adapter.
- Metadata formerly attached to the command instance must move. That includes
  audit ids, operation names, attempt counters, and user context.
- A function with too many parameters can be less readable than the command it
  replaces.
- Public API compatibility may require keeping a delegating class for a while,
  so the repo temporarily has both shapes.
- If the command held expensive dependencies, a naive function conversion may
  pass those dependencies through many call layers. A closure or better owner
  may be needed.
- Some tooling treats classes as first-class navigation units. Deleting the
  class can make generated docs or dependency graphs less granular.

## 11. Failure modes and misuse

Engineering judgement. Each item names a symptom that a developer, tester, or
operator can observe, followed by the likely cause and a concrete fix.

**Lost command identity.** Symptom. After the refactor, traces show a generic
function name or no operation label, and support staff can no longer group
failures by the old command class. Cause. Telemetry depended on the command
object's class name. Fix. Add an explicit operation label at the call site or
inside the new function before deleting the class.

**Parameter spill.** Symptom. The new function has eight or more parameters, and
call sites contain repeated groups of values in the same order. Cause.
Constructor fields were converted mechanically without finding the domain
object they represented. Fix. Use Preserve Whole Object or Introduce Parameter
Object, then retry the command collapse.

**Hidden mutation preserved.** Symptom. The function returns one value, but
tests still need to inspect mutated arguments to assert full behavior. Cause.
The command wrote to fields or collaborators during `execute`, and the
conversion kept those side effects. Fix. Return a result object for all outputs,
or split the modifier from the query before replacing the command.

**Undo broken by deletion.** Symptom. Keyboard undo, workflow rollback, or
message replay stops working for one operation after the class is removed.
Cause. The command participated in an invoker protocol even though its body
looked small. Fix. Restore the command shell and extract only the pure
calculation into a helper function.

**Mocking seam removed.** Symptom. Tests that used to replace a command class
now hit a database, clock, network client, or filesystem. Cause. The command
class was serving as a dependency boundary. Fix. Pass the function as a
dependency, introduce a small interface around the side effect, or keep an
adapter for tests and production wiring.

**Reflection binding failure.** Symptom. The application compiles but a job
runner, dependency injection container, or router fails at startup because a
configured class name no longer exists. Cause. The command was referenced in
configuration rather than source. Fix. Search configuration, queue payloads,
and migration data before deleting the class. Leave a delegating compatibility
class when external references exist.

**Changed evaluation order.** Symptom. A test fails only when arguments call
methods with side effects, or production logs show a dependency queried earlier
than before. Cause. The conversion moved expressions from constructor
arguments, field initializers, and `execute` into a different order. Fix. Store
argument values in locals in the old order, then call the new function.

**Name regression.** Symptom. The new function is named `executeCharge` or
`runCalculator`, and reviewers still have to open it to understand the domain
action. Cause. The generic command method name was carried into the function.
Fix. Rename the function after the business operation, such as `charge`,
`scoreCandidate`, or `formatInvoice`.

**Class deleted too early.** Symptom. Downstream packages fail after release
even though local tests pass. Cause. The command was part of a public API. Fix.
Restore the class as a delegating adapter, document the replacement function,
and remove it only after the project's compatibility period.

## 12. Trade-off matrix

| Force | Replace Command with Function | Replace Function with Command | GoF Command | Strategy | Template Method | Function object or closure |
|---|---|---|---|---|---|---|
| Cognitive load | Low when parameter list is short | Medium, behavior split across class and call | Medium, protocol must be known | Medium, algorithm selected elsewhere | High, flow split across hooks | Low to medium |
| Coupling | Caller couples to one callable | Caller couples to class construction | Invoker couples to command interface | Context couples to strategy interface | Subclass couples to base algorithm | Caller couples to callable type |
| Allocation cost | No per-call wrapper | One object per command unless reused | Often one object per request | Usually one object reused | Object already exists | Closure may allocate once |
| Lifecycle support | Weak | Strong inside object | Strong, identity is central | Medium | Strong through inheritance | Medium through capture |
| Undo and replay | Poor without extra message type | Possible | Strong | Not the purpose | Not the purpose | Poor unless paired with data |
| Testability | Direct value tests | Good when fields simplify setup | Good for invoker tests | Good for algorithm substitution | Harder due to inherited flow | Good with injected functions |
| Operability | Needs explicit labels | Class name can label work | Command id labels work | Strategy label needed | Subclass label needed | Function label needed |
| Team topology | Good for local code | Good for complex local refactor | Good across platform boundaries | Good across product variants | Good inside frameworks | Good in functional modules |
| Best use | One-shot calculation or action | Function needs state or helpers | Queued or reversible requests | Swappable algorithms | Fixed algorithm with hooks | Dependency capture without class |

Reading of the table. Replace Command with Function wins when the command's
object identity has no job. GoF Command wins when invocation is decoupled from
execution. Strategy wins when behavior varies behind a stable interface.
Template Method wins when a base algorithm controls the sequence. A closure
wins when the operation needs stable dependencies but no named class.

## 13. Related and incompatible patterns

**Replace Function with Command.** This is the inverse. Use it when a function
needs state, helper methods, or object protocol. Use Replace Command with
Function when that object protocol no longer pays rent.

**Inline Class.** The command class often becomes empty after `execute` is moved
to a function. At that point Inline Class describes the deletion of the wrapper
type and movement of any remaining fields.

**Move Function.** A one-off command may be a sign that the behavior belongs on
one of its parameters. Replace Command with Function can first make the inputs
visible, then Move Function can place the behavior on the better owner.

**Change Function Declaration.** Constructor parameters and `execute` arguments
become a new function signature. Use Change Function Declaration to rename,
reorder, group, or split parameters without changing behavior.

**Parameterize Function.** Several tiny command classes with near-identical
execution bodies may collapse into one function with an explicit parameter,
provided the variation is a value choice rather than true polymorphism.

**Remove Dead Code.** After the call sites use the new function, the command
class, private helpers, and tests that only check delegation may be dead code.
Delete them in the same refactoring chain.

**GoF Command.** This pattern conflicts when the command object is used by an
invoker, queue, macro recorder, undo stack, or scheduler. In those designs, the
object is the point. Collapsing it to a function removes the thing the invoker
stores.

**Strategy.** Strategy can replace a command hierarchy when the object is used
only to vary an algorithm. The strategy instance is usually longer lived than a
one-shot command, and the context names the variation point.

**Template Method.** A command subclass hierarchy with an inherited `execute`
method and overridable hooks is usually Template Method, not a disposable
command. Do not flatten it unless the inherited algorithm is gone.

## 14. Refactoring path in and out

Path in, from command class to function.

1. Find a command class that is constructed and executed in one short sequence.
   Search for `new ClassName`, `ClassName(...)`, `.execute()`, `.run()`,
   `.handle()`, and framework registration.
2. Check public use. If the class is exported, configured by name, serialized,
   or referenced by another package, plan a delegating adapter before deletion.
3. Add a characterization test around one representative caller. The assertion
   should cover the returned value and any side effect that must remain.
4. Add the new function next to the command class or in the module that owns the
   domain operation. Give it the domain verb, not the old generic method name.
5. Copy the execution method body into the function.
6. Convert reads of command fields into parameter reads. Preserve the original
   evaluation order by storing call-site expressions in locals when needed.
7. Convert output fields into a return value. If there are several outputs,
   return a result object with named fields.
8. Change one caller to call the function directly. Run the focused tests.
9. Change the old command's execution method to delegate to the function. This
   keeps compatibility while the migration continues.
10. Migrate the remaining callers in small batches, running tests after each
    batch.
11. Delete the command class when no production or test caller uses it and no
    external contract requires it.
12. Run dead-code search for private helpers that existed only for the command.

Path out, from function back to command.

1. Watch for the function gaining many temporary variables, local helper
   closures, or parameters that are passed together on every call.
2. Create a command class named for the operation. Put stable dependencies in
   the constructor first, then per-call data only when a one-shot object is
   actually wanted.
3. Move the function body into `execute`, `run`, `handle`, or the project's
   normal execution verb.
4. Turn groups of local variables into fields only when they are shared by
   extracted helper methods.
5. Keep the original function as a delegating wrapper until callers are moved.
6. If the new class is meant for a queue, undo stack, or command bus, add the
   protocol methods in the same change so the class earns its shape.

## 15. Testing and verification

Engineering judgement. The test goal is to prove the object boundary changed
without changing behavior.

Start with characterization tests. Pick inputs that cover normal behavior,
branch behavior, error behavior, and boundary values. Run those tests against
the old command before editing. After the function exists, run the same cases
against the function and one migrated caller.

Test the new function directly. Pure calculations should have table-driven
tests: input values in, result value out. For actions with side effects, inject
the side-effecting collaborator as a parameter or closure dependency, and use a
fake that records calls. Avoid tests that recreate the old command ceremony
only to call the new function through it.

Keep adapter tests short. If public compatibility requires the command class to
remain, one test should prove `Command(...).execute()` returns the same value
as the function for a representative case. The behavior suite belongs to the
function, not to both shapes.

Watch for order-sensitive expressions. When constructor arguments perform work,
write a small test that records the order before and after the refactor. The
mechanical transformation can accidentally move an expensive or side-effecting
expression from construction time to execution time.

For typed languages, compile every sample after the signature change. In Java,
that means checking all constructor and method references. In Go and Rust,
prefer package tests that compile the public function from a caller package,
because unexported names can hide migration gaps.

For dynamic languages, add at least one test that calls the public entry point
rather than only the function. Python and JavaScript will not catch stale
constructor calls until runtime if those paths lack coverage.

## 16. Observability signals

Engineering judgement. A command class often gave operations a visible name.
When it disappears, telemetry should keep the operation visible.

Record an operation label when the operation has production meaning. Use the
new function name if it is stable and domain-specific. If old dashboards were
grouped by class name, emit the old name as a compatibility label during the
migration window and add the new name as the future label.

Measure call count and error count around the function when the old command was
on a request path, job path, or billing path. For pure functions in CPU-heavy
loops, measure duration only when profiling shows cost worth tracking. Do not
turn every small function into a span.

A healthy migration looks boring. The old command class count drops to zero,
the new function call count matches the old command execution count, error
rates do not move, and dashboards keep their grouping labels through the
release. Allocation profiles may show fewer short-lived objects if the command
was hot.

A failing migration has sharp signals. Startup errors mention missing class
names. Queue consumers cannot deserialize old payloads. Trace cardinality
changes because labels now include raw function arguments. Error rates rise
only on paths whose caller migrated. Heap pressure may fall, but that is a
performance observation, not proof that behavior is correct.

## 17. Security and privacy implications

Engineering judgement. The refactoring is usually security-neutral when it
collapses local calculation code. The risks appear around boundaries.

Authorization can move by accident. If the command constructor checked user
permissions and the new function copied only the execution body, callers may
bypass the check. Keep authorization in the caller or in the new function, and
add a test for denied access before deleting the command.

Audit identity can disappear. A command object may have carried user id,
request id, tenant id, reason code, or approval id. A function that accepts only
business inputs can perform the action without audit context. Make audit
context an explicit parameter when the operation changes money, access, or
stored data.

Deserialization boundaries need care. If old command objects are stored in job
queues or event logs, deleting the class may break replay or recovery. Keep a
reader for old messages and map them to the new function. Do not rewrite old
history merely to match the new code shape.

Privacy can improve if the command stored personal data longer than needed.
A one-shot function can receive the data, compute, and return without retaining
fields on an object captured by logs, debug dumps, or heap snapshots. Privacy
can get worse if the new function logs argument values that the old command
never logged. Prefer operation names and stable ids over raw personal data in
function-level telemetry.

Dependency injection changes can affect least privilege. A command class might
have received a narrow collaborator from the container. A function moved to a
module may reach for a global client instead. Keep dependencies explicit so the
operation keeps the same permission boundary after the refactor.

## Code examples

The examples use TypeScript, Python, and Go because each language has a natural
function target. The TypeScript example shows class collapse in a common
application language. Python shows direct module functions. Go shows the target
shape that Go programmers usually wanted from the start, a function over small
structs rather than a one-method type.

### TypeScript

```typescript
type Customer = {
  rate: number;
  discount: number;
};

class ChargeCommand {
  constructor(
    private readonly customer: Customer,
    private readonly usage: number,
  ) {}

  execute(): number {
    const gross = this.customer.rate * this.usage;
    return gross - this.customer.discount;
  }
}

function charge(customer: Customer, usage: number): number {
  const gross = customer.rate * usage;
  return gross - customer.discount;
}

const customer: Customer = { rate: 0.4, discount: 3 };
const before = new ChargeCommand(customer, 20).execute();
const after = charge(customer, 20);

if (before !== after) {
  throw new Error(`mismatch ${before} ${after}`);
}

console.log(after);
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Customer:
    rate: float
    discount: float


class ChargeCommand:
    def __init__(self, customer: Customer, usage: float) -> None:
        self.customer = customer
        self.usage = usage

    def execute(self) -> float:
        gross = self.customer.rate * self.usage
        return gross - self.customer.discount


def charge(customer: Customer, usage: float) -> float:
    gross = customer.rate * usage
    return gross - customer.discount


if __name__ == "__main__":
    customer = Customer(rate=0.4, discount=3.0)
    before = ChargeCommand(customer, 20.0).execute()
    after = charge(customer, 20.0)
    assert before == after
    print(after)
```

### Go

```go
package main

import "fmt"

type Customer struct {
	Rate     float64
	Discount float64
}

type ChargeCommand struct {
	customer Customer
	usage    float64
}

func (c ChargeCommand) Execute() float64 {
	gross := c.customer.Rate * c.usage
	return gross - c.customer.Discount
}

func Charge(customer Customer, usage float64) float64 {
	gross := customer.Rate * usage
	return gross - customer.Discount
}

func main() {
	customer := Customer{Rate: 0.4, Discount: 3}
	before := ChargeCommand{customer: customer, usage: 20}.Execute()
	after := Charge(customer, 20)
	if before != after {
		panic("mismatch")
	}
	fmt.Println(after)
}
```

## 18. References

1. Martin Fowler. *Refactoring. Improving the Design of Existing Code*. 2nd
   edition. Addison-Wesley, 2018. Chapter 11, "Refactoring APIs," section
   "Replace Command with Function." Source for the canonical name and the
   refactoring's catalog placement.
2. Martin Fowler. "Replace Command with Function." Refactoring catalog.
   https://refactoring.com/catalog/replaceCommandWithFunction.html. Verified
   2026-08-02. Source for the public before and after shape and inverse
   relationship.
3. Martin Fowler. "Replace Function with Command." Refactoring catalog.
   https://refactoring.com/catalog/replaceFunctionWithCommand.html. Verified
   2026-08-02. Source for the inverse refactoring and the older alias Replace
   Method with Method Object.
4. Martin Fowler. "Changes for the 2nd Edition of Refactoring." 5 September
   2018. https://martinfowler.com/articles/refactoring-2nd-changes.html.
   Verified 2026-08-02. Source for the statement that Replace Command with
   Function was new in the second edition.
5. Pallets. *Click Documentation*, version 8.5.x, "Quickstart."
   https://click.palletsprojects.com/en/stable/quickstart/. Verified
   2026-08-02. Source for function-decorated command declaration.
6. Pallets. *Click Documentation*, version 8.5.x, "API."
   https://click.palletsprojects.com/en/stable/api/. Verified 2026-08-02.
   Source for `click.command` creating a `Command` with the decorated function
   as callback.
7. Python Software Foundation. "black/src/black/`__init__.py`."
   https://github.com/psf/black/blob/main/src/black/__init__.py. Verified
   2026-08-02. Source for Black's Click-decorated `main` function.
8. Pallets. *Flask Documentation*, version 3.1.x, "Quickstart."
   https://flask.palletsprojects.com/en/stable/quickstart/. Verified
   2026-08-02. Source for the minimal route function example.
9. Pallets. *Flask Documentation*, version 3.1.x, "API."
   https://flask.palletsprojects.com/en/stable/api/. Verified 2026-08-02.
   Source for `route()` as a shortcut for registering a view function.
10. Meta Open Source. *React Documentation*, "Component."
    https://react.dev/reference/react/Component. Verified 2026-08-02. Source
    for the recommendation to define new components as functions rather than
    classes.
11. Meta Open Source. *React Documentation*, "Your First Component."
    https://react.dev/learn/your-first-component. Verified 2026-08-02. Source
    for React components as JavaScript functions.
