---
name: Command
slug: command
family: 01-gof
category: Behavioral
aliases: [Action, Transaction, Operation Object]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
related: [memento, composite, chain-of-responsibility, strategy, prototype, observer, mediator]
incompatible_with: []
maturity: canonical
verified: 2026-08-02
---

# Command

## 1. Name, aliases, and lineage

The canonical name is Command. It appears in the Gang of Four catalog among the
eleven behavioral patterns, in Erich Gamma, Richard Helm, Ralph Johnson and John
Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 5, Behavioral Patterns, section Command. The book
records the intent as encapsulating a request as an object, so that clients can
be parameterised with different requests, requests can be queued or logged, and
undoable operations become supportable. That four part intent is the whole
pattern in one sentence, and each clause corresponds to a distinct production
use covered in dimension 9.

The book lists two aliases. **Action** and **Transaction**. Both are still in
live use and both carry a slight bias.

- **Action** is the name that survived in user interface toolkits. Java Swing
  ships `javax.swing.Action`, Qt ships `QAction`, and GTK ships actions bound to
  menus and accelerators. When a codebase says Action it usually means a Command
  that additionally carries presentation metadata, a label, an icon, an enabled
  flag, and a keyboard shortcut.
- **Transaction** is the name that survived in data and messaging systems. It
  emphasises that the object describes a change to apply, that the change may be
  recorded before it is applied, and that it may need to be reversed. This is
  the reading that leads to command logs, write ahead logs, and the command side
  of CQRS.
- **Operation Object** turns up in older distributed systems literature for the
  same idea, an invocation reified so it can cross a process boundary. Java's
  `java.rmi` and Cocoa's `NSInvocation` are the historical exemplars.

Two name collisions cause real damage and are worth separating immediately.

**Command the GoF pattern is not Command Query Separation.** Command Query
Separation is a method design principle coined by Bertrand Meyer in *Object
Oriented Software Construction*, which divides every method into a query that
returns a result without changing observable state, and a command that changes
state and returns nothing
([Martin Fowler, CommandQuerySeparation](https://martinfowler.com/bliki/CommandQuerySeparation.html),
verified 2026-08-02). Meyer's command is a method. The GoF command is an object.
The two agree only on the intuition that state changing work deserves its own
name.

**Command the GoF pattern is not the C of CQRS.** CQRS uses a different model to
update information than the model used to read it
([Martin Fowler, CQRS](https://martinfowler.com/bliki/CQRS.html), verified
2026-08-02). CQRS is an architectural split of an entire model. The GoF pattern
is an object level technique that CQRS implementations very often use to carry
the update request across the split. Dimension 8 works through the relationship
in detail, because conflating them produces both bad architecture and bad
object design.

A useful discriminator for the GoF pattern itself. If the object exists so that
a request can be held, passed, stored, delayed, repeated, or reversed, it is a
Command. If the object exists so that an algorithm can be substituted at the
point it runs, it is a Strategy. The shapes are close to identical in code and
the difference is entirely in why the object exists.

## 2. Problem and context

An invoker needs to trigger work without knowing what the work is, who performs
it, or when it will actually run.

The situation shows up in a codebase in a recognisable way. A menu item, a
toolbar button, a keyboard shortcut, an HTTP handler and a scheduled job all
need to trigger the same operation. The first implementation wires the operation
directly into the button click handler. The second call site copies it. By the
fourth one the operation exists in four places with four slightly different
validation rules, and the widget class now imports the persistence layer.

A second and sharper version of the problem. A user does something and then
wants it undone. The naive implementation writes the new value over the old one
and the old value is gone. Adding undo after the fact means finding every write
in the application and retrofitting a way to reverse it, which is a
cross cutting change to every feature at once. The application ends up with an
undo that works for some operations and silently does nothing for others, which
is worse than no undo, because the user cannot tell which is which.

A third version. Work needs to happen later, elsewhere, or repeatedly. A request
arrives on a web thread but the work takes thirty seconds and belongs on a
worker. A batch of operations needs to run against a production database at
midnight after a human approves the batch. A failed operation needs a retry with
identical arguments. In every case the work has to survive the disappearance of
the stack frame that requested it, and a stack frame is not a value.

The context that makes Command the right answer has four parts.

- The trigger and the work are owned by different code, and the trigger should
  not name the work.
- The set of operations grows over time and the invoker should not grow with it.
- The request needs a lifetime independent of the call that produced it, whether
  because it is stored, queued, delayed, replayed, or reversed.
- Something needs to be done uniformly to every request, whether that is
  logging, authorisation, auditing, retry, rate limiting, or undo. A uniform
  treatment needs a uniform type.

Where none of those four hold, the pattern is overhead. A direct method call
carries less machinery and reads better. Dimension 4 gives the non-applicability
list in full.

## 3. Forces

The pattern balances the following competing pressures.

- **Coupling.** Strongly favoured. This is the pattern's main purchase. The
  invoker depends only on an execute contract. It never names a receiver, never
  imports a service, and never grows when an operation is added. The dependency
  from invoker to concrete operation is removed entirely and replaced by a
  dependency from the wiring code to both.
- **Temporal decoupling.** Strongly favoured and unusual among the behavioral
  patterns. A reified request outlives the call site, which is what makes
  queueing, scheduling, retry, and replay possible at all. `Executor` states the
  point directly, describing itself as decoupling task submission from the
  mechanics of how each task will be run
  ([Java SE 21, `java.util.concurrent.Executor`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Executor.html),
  verified 2026-08-02).
- **Reversibility.** Favoured, and available in no other GoF pattern at this
  granularity. Because every change goes through one type, adding an undo method
  to that type retrofits undo across the whole application in one change rather
  than one per feature.
- **Auditability.** Favoured. A request that is an object can be serialised,
  written to a log, replayed, and diffed. Redis exploits exactly this, logging
  every write operation received by the server and replaying the log at startup
  to reconstruct the dataset
  ([Redis persistence documentation](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/),
  verified 2026-08-02).
- **Cognitive load.** Sacrificed, and the sacrifice is larger than most catalogs
  admit. Following an operation from the button that triggers it to the code that
  performs it now requires resolving a virtual call, and in a queued system
  requires crossing a process boundary and a persistence format. A stack trace
  taken inside a command tells you nothing about who submitted it.
- **Class count.** Sacrificed. One type per operation. An application with two
  hundred user actions has two hundred command types unless a parameterised or
  closure based variant is used, see dimension 8.
- **Latency.** Mildly sacrificed in the synchronous case, one allocation and one
  virtual call per request. Substantially changed in the asynchronous case, where
  the operation gains queue wait time and loses the caller's stack context. That
  is a design change rather than a cost, but it is often adopted accidentally.
- **Consistency.** Sacrificed in the queued form, favoured in the transactional
  form. A queued command is applied later, so the caller sees an eventual result
  rather than an immediate one. A macro command applied under a lock is the
  opposite, it makes a group of changes atomic in a way individual calls were
  not.
- **Operability.** Mixed. A command queue is an operable object, it can be
  measured, drained, paused, and inspected, which a stack of direct calls cannot.
  Against that, a failure in a command has no caller to report to, so error
  handling has to be designed rather than inherited.
- **Cost.** Sacrificed in storage terms whenever commands are logged or an undo
  stack is retained, because history has a size and history grows.
- **Team topology.** Favoured. The command type is a published contract between
  a team that owns the invoker and dispatch machinery, and teams that own
  individual operations. New operations arrive in their own modules without
  touching the shared dispatcher.

The pattern gives up immediacy and type count in exchange for time, reversal,
and a single chokepoint. Any description that omits the class count and the lost
stack context is describing the pattern favourably rather than accurately.

## 4. Applicability and non-applicability

Reach for Command when the following hold.

- Several trigger points, a menu, a shortcut, a context menu, an API route, a
  script, need to run the same operation, and the operation should be defined
  once.
- Undo, redo, or rollback is required or plausibly will be. Retrofitting undo
  later is far more expensive than adopting the pattern early, because the
  retrofit touches every mutation in the codebase.
- Work must be deferred, queued, scheduled, or executed on a different thread or
  a different machine.
- Requests must be logged, audited, or replayed, whether for crash recovery,
  compliance, or debugging.
- A uniform cross cutting concern applies to every operation, for example
  authorisation, rate limiting, idempotency keys, or retry with backoff. A
  uniform type gives a single place to implement it.
- Operations need to be composed, so that a group of changes is treated as one
  reversible unit. This is the macro command form in dimension 8.
- The operation set is open and extended by code the invoker's author has never
  seen, which is the plugin case.

Do NOT reach for Command in the following cases. This non-applicability list is
the part most catalogs leave out, and the reason each entry appears matters more
than the entry itself.

- **A single call site and no deferral.** A method call already encapsulates a
  request. Wrapping it in an object that is constructed and immediately executed
  on the next line adds a type and removes a stack frame's worth of readability
  and gives nothing back. This is the most common misuse in practice.
- **The work returns a result the caller needs right now.** Command's shape is
  built for fire and forget. When a value is needed synchronously, an ordinary
  method or a Strategy reads better. Java acknowledges this by splitting the two,
  `Runnable` represents an operation that does not return a result, while
  `Callable` is a task that returns a result and may throw
  ([Java SE 21, `java.util.concurrent.Callable`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Callable.html),
  verified 2026-08-02). If the answer is always needed immediately, the ceremony
  buys nothing.
- **The undo requirement is not real.** Undo is the most cited reason to adopt
  the pattern and the most frequently unused. Building command objects with
  `undo()` methods that nothing calls produces dead code that every future
  operation is obliged to implement, and that obligation quietly becomes
  `throw new UnsupportedOperationException()` in half the classes.
- **The state change is not reversible by any means available.** Sending an
  email, charging a card, launching a rocket. A command interface that promises
  undo across a set of operations where some cannot honour it produces an undo
  stack that is a lie. Model those as compensating actions with their own
  vocabulary, or partition the interface so only reversible operations carry
  `undo()`.
- **The language has first class functions and there is no published extension
  contract.** In TypeScript, Python, Go, Kotlin, Rust and modern Java a closure
  is a command. Writing a class with a single `execute()` method and no state
  reproduces a lambda with five times the syntax. See dimension 8.
- **The real problem is decoupling a sender from many receivers.** That is
  Observer or a message bus. Command decouples a sender from one receiver by
  reifying the request. If the requirement is broadcast, adding a command type
  does not address it.
- **The real problem is finding the right handler.** That is Chain of
  Responsibility or a dispatch table. Command says nothing about who handles the
  request, and a system that mostly needs routing will find its routing logic
  living awkwardly inside command constructors.
- **The team is reaching for CQRS by reflex.** Fowler warns plainly that one
  should be very cautious about using CQRS, that it adds complexity, and that
  most systems fit a CRUD model better
  ([Martin Fowler, CQRS](https://martinfowler.com/bliki/CQRS.html), verified
  2026-08-02). Adopting command objects because a talk mentioned CQRS is
  cargo cult architecture, and the resulting code carries the cost of the split
  with none of the read scaling that motivates it.

## 5. Structure

Five participants, named by the role each plays rather than by a class name.

- **Command.** The interface every request implements. Its minimum shape is a
  single parameterless operation, conventionally `execute()`. When undo is in
  scope it also declares `undo()`, and often `canUndo()` so the invoker can
  disable the menu item rather than fail at click time. When the command set is
  persisted, this type also carries the serialisation contract, which is a
  heavier commitment than it first appears, see dimension 17.
- **ConcreteCommand.** One implementation per operation. It holds a reference to
  its Receiver and the arguments captured at the moment the request was made.
  Those captured arguments are what make the object independent of the call
  stack, and capturing them by value rather than by reference is the difference
  between a command that can be replayed and one that cannot, see dimension 11.
  When undo is supported it also holds whatever is needed to reverse itself,
  which is either the inverse operation plus its arguments, or a Memento of the
  receiver's prior state.
- **Receiver.** The object that knows how to perform the work. A ConcreteCommand
  should contain almost no domain logic, it should translate a request into calls
  on a Receiver. A command that contains the business rules rather than
  delegating them is a transaction script wearing a pattern's name, and it will
  be untestable without the whole application present.
- **Invoker.** Holds and triggers commands without knowing what they do. A
  button, a keyboard shortcut table, a thread pool, a queue consumer, a scheduler.
  The invoker is also the natural home for the history stack, the queue, and the
  log, because it is the only participant that sees every command.
- **Client.** Constructs a ConcreteCommand, gives it its Receiver and arguments,
  and installs it into the Invoker. The client is the only participant that knows
  both a concrete command type and a concrete receiver type, and pushing that
  knowledge to the wiring edge of the system is the point of the whole
  arrangement.

Relationships. Invoker holds Command, never ConcreteCommand. ConcreteCommand
holds Receiver. Client depends on all three and is depended on by none. The
dependency graph has no cycle, and the only place a concrete operation name
appears is the client, which is normally a composition root, a menu definition
file, or a registration table.

A sixth participant appears once undo is real. **History**, usually two stacks,
one of executed commands and one of undone commands. It belongs to the invoker
side rather than to any command. Its semantics are covered in dimension 7.

## 6. ASCII structure diagram

```
  +-----------+  creates and configures   +---------------------+
  |  Client   |- - - - - - - - - - - - -> |  ConcreteCommandA   |
  +-----------+                           |---------------------|
        |                                 | - receiver          |
        | installs                        | - args (by value)   |
        v                                 | + execute()         |
  +-----------------+                     | + undo()            |
  |    Invoker      |    holds            +---------------------+
  |-----------------|-------------------->          |
  | - history: [ ]  |                      implements|
  | + run(Command)  |                                v
  | + undo()        |                     +---------------------+
  | + redo()        |                     |      Command        |
  +-----------------+                     |  (interface)        |
                                          |---------------------|
                                          | + execute()         |
                                          | + undo()            |
                                          +---------------------+
                                                     ^
                                                     | implements
                                          +---------------------+
                                          |  ConcreteCommandB   |
                                          +---------------------+
                                                     |
                                                     | calls
                                                     v
                                          +---------------------+
                                          |      Receiver       |
                                          |---------------------|
                                          | + doTheWork(...)    |
                                          +---------------------+

  The Invoker never names ConcreteCommandA or the Receiver.
  Only the Client, at the wiring edge, knows both concrete types.
```

## 7. Dynamics

Three runtime flows matter and they behave differently. Immediate execution,
undo and redo, and deferred execution.

Immediate execution with history recording.

```
Client        Invoker         ConcreteCommandA        Receiver
  |              |                    |                   |
  |- new CmdA(receiver, args) ------->|                   |
  |              |                    |                   |
  |- run(cmd) -->|                    |                   |
  |              |- execute() ------->|                   |
  |              |                    |- doTheWork(args) ->|
  |              |                    |<-- ok ------------ |
  |              |<-- ok ------------ |                   |
  |              |                    |                   |
  |              | push cmd on undo stack                 |
  |              | clear redo stack                       |
  |<-- ok -------|                    |                   |
```

The clearing of the redo stack on a fresh execution is not an optimisation, it
is a correctness requirement. Applying a new change invalidates the previously
undone ones, so the redo stack is discarded as soon as a new operation is
registered, which prevents redo from returning the model to a state that never
existed
([Apple, Undo Architecture, Undo Manager](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/UndoArchitecture/Articles/UndoManager.html),
verified 2026-08-02).

Undo and redo, showing the stack transfer.

```
Invoker                    undo stack        redo stack
  |                        [ A, B, C ]       [ ]
  |
  |- undo()
  |    pop C, call C.undo()
  |                        [ A, B ]          [ C ]
  |
  |- undo()
  |    pop B, call B.undo()
  |                        [ A ]             [ C, B ]
  |
  |- redo()
  |    pop B, call B.execute()
  |                        [ A, B ]          [ C ]
  |
  |- run(D)   <-- a new command arrives
  |                        [ A, B, D ]       [ ]   redo discarded
```

Deferred execution across a boundary.

```
Producer            Queue / Log            Consumer          Receiver
   |                    |                      |                 |
   |- submit(cmd) ----->|                      |                 |
   |   (serialise)      |                      |                 |
   |<-- accepted -------|                      |                 |
   |                    |                      |                 |
   |   ... time passes, process may restart ...                  |
   |                    |                      |                 |
   |                    |<-- poll ------------ |                 |
   |                    |--- cmd bytes ------->|                 |
   |                    |                      |- deserialise    |
   |                    |                      |- execute() ---->|
   |                    |                      |<-- ok --------- |
   |                    |<-- ack ------------- |                 |
```

Three timing properties are worth stating because each is a source of production
incidents. First, once a command crosses the queue boundary the producer's
result is an acknowledgement of acceptance, not of completion, and code written
as if it were the latter will report success for work that later fails. Second,
a command that survives a restart must have captured its arguments by value at
construction time, because the objects it referenced will not exist on the other
side. Third, at least once delivery is the normal guarantee, so a command will
sometimes be executed twice, which makes idempotency a property of the command
rather than of the queue.

## 8. Implementation variants

**Minimal command, execute only.** A single method interface with no undo. This
is the form that covers the decoupling and deferral motivations without paying
for reversal. It is by far the most common form in production and the one most
tutorials skip past on the way to undo.

**Command with undo, inverse operation form.** The command stores the arguments
needed to reverse itself and `undo()` applies the inverse. Adding ten to a
balance is undone by subtracting ten. This form is compact and composes well,
and Fowler makes the same observation for events, that reversal is at its most
direct when the change is expressed as a difference rather than as an absolute
value
([Martin Fowler, Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html),
verified 2026-08-02). The limitation is that not every operation has a clean
inverse. Setting a field to a new value has no inverse without knowing the old
one.

**Command with undo, memento form.** Before executing, the command asks the
receiver for a snapshot of the relevant state, and `undo()` restores it. This is
the Command and Memento pairing, and it is the reason the two patterns are
usually taught together. Memento allows reverting the state of an object and
lists undo as its primary application, with an originator that owns the state, a
memento that captures it, and a caretaker that holds the memento without reading
it
([Memento pattern, Wikipedia](https://en.wikipedia.org/wiki/Memento_pattern),
verified 2026-08-02). The trade against the inverse form is memory. A memento of
a large document per keystroke is not affordable, which is why real editors
snapshot narrowly, capturing only the affected range rather than the document.
The rule of thumb. Use the inverse form where the operation is a difference, use
the memento form where the operation overwrites, and never mix the two inside a
single command because reasoning about partial restoration becomes intractable.

**Macro command, the Composite pairing.** A command that holds a list of child
commands, executes them in order, and undoes them in reverse order. This is
Composite applied to Command and it is what gives an application a single undo
step for a multi part edit. The failure case deserves design attention. If child
three of five throws, the macro must undo children one and two before
propagating, otherwise the model is left in a state no undo step can describe.

**Merging or coalescing commands.** Consecutive small commands of the same kind
collapse into one history entry, so that typing a word is one undo step rather
than five. Qt implements this with an `id()` on each command and a `mergeWith()`
that combines two, and the stack attempts a merge only when the identifiers match
and are not the sentinel value
([Qt 6, `QUndoCommand`](https://doc.qt.io/qt-6/qundocommand.html), verified
2026-08-02). Swing does the same through `addEdit()`, which returns true when one
edit has been absorbed into another, described in the API as a way to coalesce
smaller edits into a larger compound edit
([Java SE 21, `javax.swing.undo.UndoableEdit`](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/javax/swing/undo/UndoableEdit.html),
verified 2026-08-02). Two independent toolkits arriving at the same mechanism is
a strong signal that a real undo stack needs it.

**Closure replaces the class.** In any language where a function is a value, a
command is a closure over its receiver and arguments. This removes the class per
operation entirely, which is the pattern's largest cost. The trade is real and
runs in both directions. A closure has no name, cannot be serialised, cannot be
compared for merging, and cannot carry metadata such as a label or an
authorisation scope. So the rule is. Use closures where the requirement is
decoupling and deferral only. Use named types where the requirement is undo,
logging, replay, persistence, or a published extension contract. Java's own
library sits on the closure side, `Runnable` being a functional interface whose
functional method is `run()`, so any lambda is a command as far as an executor is
concerned
([Java SE 21, `java.lang.Runnable`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Runnable.html),
verified 2026-08-02).

**Degenerate command, the runnable task.** `Runnable` and `Callable` are Command
with the pattern's optional parts removed. `Runnable` predates lambdas and its
Java 17 documentation states its purpose plainly, that it provides the means for
a class to be active while not subclassing `Thread`, by instantiating a thread
and passing itself as the target
([Java SE 17, `java.lang.Runnable`](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Runnable.html),
verified 2026-08-02). That is the invoker and command split exactly, `Thread` is
the invoker and the runnable is the command. `Callable` adds a return value and
a checked exception, and its own documentation frames it as similar to
`Runnable`, differing in that a runnable returns no result and cannot throw a
checked exception. Neither declares undo, neither is serialisable, and neither
names a receiver, so both are the minimal form of the pattern rather than the
full one. Calling them degenerate is descriptive rather than dismissive, they
are the most widely deployed instance of the pattern in existence.

**Command as a data record, the message form.** The command is a plain data
structure with no behaviour, and a separate handler performs the work. This is
the form used across process boundaries and the form CQRS implementations
normally adopt. It gives up the polymorphic `execute()` and gains
serialisability, schema evolution, and the ability to validate a request without
the ability to perform it. Dispatch moves to a registry mapping command type to
handler, which reintroduces a lookup that the classic form avoids.

**The CQRS command side, and how it differs.** CQRS separates the write model
from the read model, using a different model to update information than the one
used to read it. Its commands are usually the data record form above, named in
the imperative, validated, and rejected or accepted as a whole. Three
differences from the GoF pattern are worth holding onto. First, scope. GoF
Command is an object level technique, CQRS is a model level split, and adopting
one does not require the other. A CQRS system can accept commands as method
arguments on a service, and a GoF Command implementation can exist inside a
single unified model. Second, undo. GoF Command's headline capability is
reversal, while a CQRS command is normally not reversible, correction is done by
issuing a compensating command rather than by undoing the original. Third,
symmetry. GoF Command says nothing about reads, whereas the query half is half
of CQRS by definition.

**Command logging and replay, and its relationship to Event Sourcing.** Because
every request is an object, the request stream can be written to durable storage
before it is applied, and reapplied later. Redis is the plainest production
example, appending every write command it receives and replaying the file at
startup to rebuild state. This is close to Event Sourcing but it is not the same
thing and the distinction carries weight. Event Sourcing captures all changes
to application state as a sequence of events, storing the event objects in the
order they were applied. The difference is tense and authority. A command is a
request that may be rejected, expressed in the imperative, whereas an event is a
fact that already happened and cannot be rejected. A log of commands replayed
against different code, or against a service whose external dependency now
answers differently, can produce a different state, because a command may
consult the world when it runs. A log of events replayed reproduces the same
state by construction, because the decisions were already made. Systems that log
commands and call it Event Sourcing discover this on the first replay after a
behaviour change, and the symptom is a rebuilt read model that disagrees with
the old one on historical records. The safe arrangement is to accept commands,
validate them, and record the resulting events, which is why the two patterns
appear together so often without being the same pattern.

**Command with metadata, the Action form.** The command carries presentation and
policy attributes alongside its behaviour, a display name, an icon, an enabled
predicate, a keyboard binding, a required permission. This is what user interface
toolkits ship, and it is what makes one command object drivable from a menu, a
toolbar, a palette and a shortcut without any of those trigger points knowing
each other. The cost is that the command type now depends on presentation
concepts, which makes it awkward to reuse the same type on a server. The usual
resolution is to keep behaviour in a plain command and wrap it in an action that
adds the metadata.

## 9. Known production uses

**Java Swing undo framework, `javax.swing.undo.UndoableEdit` and
`UndoManager`.** The interface describes an edit that may be undone, or redone
if already undone, and states that it is designed to be used with `UndoManager`,
to which edits are added as they are generated. `addEdit()` provides the
coalescing described in dimension 8, returning true when one edit has been
incorporated into another, with text editors given as the motivating example.
Java SE 21 API documentation, `javax.swing.undo.UndoableEdit`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/javax/swing/undo/UndoableEdit.html
verified 2026-08-02.

**Qt, `QUndoCommand` and `QUndoStack`.** A `QUndoCommand` represents a single
editing action with virtual `undo()` and `redo()` methods, and the documentation
states the contract precisely, that after `undo()` is called the document state
should be the same as before `redo()` was called. Commands are owned by the
stack they are pushed onto, and the stack deletes an undone command when a new
one is pushed, which is the redo discard rule made concrete in an ownership
model. Qt 6 documentation, `QUndoCommand`, https://doc.qt.io/qt-6/qundocommand.html
verified 2026-08-02.

**Cocoa and Foundation, `NSUndoManager`.** An undo operation is described as a
method for reverting a change to an object along with the arguments needed to
revert it, which is the command's captured state stated as a definition.
Operations are collected into undo groups that represent whole revertible
actions and are stored on a stack, so that performing undo reverts an entire
group. During undo, objects register the reverse operations, which become the
redo stack, and registering a new undo operation clears any existing redo stack.
Apple Developer Archive, Undo Architecture, "Undo Manager",
https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/UndoArchitecture/Articles/UndoManager.html
verified 2026-08-02.

**Visual Studio Code, the commands API.** Commands trigger actions in the
editor, `vscode.commands.registerCommand` binds a command identifier to a
handler function, and `vscode.commands.executeCommand` runs a command
programmatically. The same identifier is reachable from the Command Palette,
from a keybinding, from a menu contribution guarded by a `when` clause, and from
another extension. This is the many trigger points motivation from dimension 2
in its purest deployed form, one command definition and five unrelated ways to
fire it. Visual Studio Code API documentation, "Commands",
https://code.visualstudio.com/api/extension-guides/command verified 2026-08-02.

**Java concurrency, `Executor` and `ExecutorService`.** `Executor` is described
as an object that executes submitted `Runnable` tasks, providing a way of
decoupling task submission from the mechanics of how each task will be run,
including thread use and scheduling. `execute(Runnable command)` names its
parameter `command`, and its contract states that the command may run in a new
thread, a pooled thread, or the calling thread at the implementation's
discretion. That is invoker and command with the binding between them deferred to
runtime configuration. Java SE 21 API documentation,
`java.util.concurrent.Executor`,
https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Executor.html
verified 2026-08-02.

**Redis append only file persistence.** AOF persistence logs every write
operation received by the server, and those operations are replayed at server
startup to reconstruct the original dataset, using the same format as the Redis
protocol itself. Log rewriting compacts the history into the shortest command
sequence that rebuilds the current dataset, which is the command log analogue of
snapshotting a long undo stack. Redis documentation, "Redis persistence",
https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
verified 2026-08-02.

## 10. Consequences

Positive.

- The invoker is decoupled from the operation completely. Adding an operation
  requires no change to any trigger point, which is the Open Closed Principle
  applied to behaviour rather than to construction.
- One operation definition serves every trigger point, so a menu item, a
  shortcut and an API route cannot drift apart.
- Requests gain a lifetime. They can be stored, queued, scheduled, retried,
  batched, and shipped to another process, none of which a stack frame allows.
- Undo and redo become a property of the framework rather than a per feature
  effort. Once the history stack exists, a new reversible operation costs one
  `undo()` implementation.
- Cross cutting concerns get a single chokepoint. Authorisation, audit logging,
  rate limiting, metrics and retry are implemented once against the command
  interface rather than once per operation.
- Operations become composable. A macro command turns a group of changes into
  one atomic, reversible unit without any of the individual operations knowing
  about the grouping.
- Testing gains a natural seam, covered in dimension 15. A command is a small
  object with an obvious contract and no user interface attached.

Negative.

- Type count grows linearly with the operation count. Two hundred operations is
  two hundred types, plus their tests, plus their registration.
- Indirection costs traceability. No source line connects the button to the
  work, and in a queued system a stack trace inside a command does not identify
  the submitter. Correlation identifiers become mandatory rather than optional,
  see dimension 16.
- Error handling has to be designed. A deferred command has no caller waiting
  for its exception, so failure has a destination only if one was built.
- History has a memory cost, and it is unbounded by default. An undo stack of
  memento based commands over a large document will consume as much memory as
  the edit session lasts unless a depth limit exists.
- Serialised commands become a schema. Once a command has been written to a
  queue or a log, its field layout is a compatibility contract with every future
  version of the code that will read it.
- Partial application is possible in the macro form. A composite that fails
  midway leaves the model in a state that neither the executed nor the unexecuted
  history describes, unless rollback was implemented deliberately.
- The pattern invites over adoption. Because it is easy to describe and easy to
  apply anywhere, codebases acquire command objects for operations that have one
  caller and no reversal, which is pure cost.

## 11. Failure modes and misuse

**Undo that leaves the model wrong.** Symptom. A user performs three edits,
presses undo twice, and the document is not in the state it held after the first
edit, usually with one field stale. Cause. The command's `undo()` reverses its
own change but the receiver had a derived value, a cached total, a modified
timestamp, a dirty flag, that was updated as a side effect and never reversed.
Fix. Make `undo()` restore through the same code path that `execute()` changed,
or capture a memento wide enough to include the derived state. Add the round trip
property test from dimension 15, which catches this class before release.

**Redo resurrecting an impossible state.** Symptom. A user undoes two steps,
makes a new edit, presses redo, and the model jumps to a state it was never in,
often with a duplicated or orphaned element. Cause. The redo stack was not
cleared when the new command executed. Fix. Clear the redo stack on every fresh
execution, which is the rule both Cocoa and Qt build into their own APIs.

**Command holding a reference rather than a value.** Symptom. A queued command
executes with different arguments than the ones the user supplied, or a command
replayed from a log fails with a null reference. Cause. The command captured a
mutable object or a live handle rather than copying the values it needed, and by
execution time that object has changed or no longer exists. Fix. Copy scalar
arguments at construction, and store identifiers rather than object references
for anything crossing a boundary.

**The command that is really the whole application.** Symptom. A command class
of four hundred lines that imports the database, the mail sender and the HTTP
client, and that cannot be tested without a running environment. Cause. The
Receiver participant was skipped and domain logic was written directly into
`execute()`. Fix. Extract the logic into a receiver and reduce the command to
argument capture plus one delegating call.

**Undo declared on operations that cannot honour it.** Symptom. Pressing undo
appears to succeed, the history entry disappears, and the external effect
remains, an email is still sent or a charge is still made. Cause. A single
command interface with `undo()` was applied to irreversible operations, and the
implementations either do nothing or throw and are silently caught. Fix. Split
the interface so only reversible operations declare `undo()`, and have the
invoker refuse to push a non reversible command onto the undo stack, or model
the reversal explicitly as a compensating command with its own user visible
semantics.

**Duplicate execution after a retry.** Symptom. Two identical rows, two charges,
or a counter that is double what it should be, appearing only under load or after
a deployment. Cause. At least once delivery in the queue combined with a command
that is not idempotent, so a redelivery after a lost acknowledgement applies the
change twice. Fix. Give the command an identifier assigned at construction and
make the receiver reject an identifier it has already applied. Retry safety is a
property of the command, not of the transport.

**Unbounded history.** Symptom. Steadily climbing heap in a long lived editor
session, with retention traced to a list held by the invoker. Cause. An undo
stack with no depth limit, holding mementos of the model. Fix. Cap the stack
depth, and prefer inverse commands over mementos where the operation is a
difference.

**The command log replayed against changed behaviour.** Symptom. A rebuilt state
disagrees with the live state on historical records, often only for records
created before a specific deployment. Cause. Commands rather than events were
logged, and the code that interprets a command now decides differently, or
consults an external service that answers differently. Fix. Record the resulting
events rather than the incoming requests, and treat the command log as an audit
of what was asked rather than as the source of truth for what happened.

**One class per operation for operations with one caller.** Symptom. A directory
of eighty command classes, most with an empty constructor, a single `execute()`
that calls one method, and no `undo()`. Cause. The pattern applied where a method
call or a closure was sufficient. Fix. Collapse the single caller commands into
direct calls or lambdas, keeping named types only where undo, logging, or a
published contract requires them.

**Losing the causal chain across the queue.** Symptom. An operator can see that a
command failed but cannot determine which user request produced it, so the
failure cannot be attributed or reproduced. Cause. The command was serialised
without the trace context of its submission. Fix. Carry the correlation and trace
identifiers as fields on the command itself, see dimension 16.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3.

| Force | Command | Strategy | Observer | Chain of Responsibility | Closure or function value | Direct method call | Event Sourcing |
|---|---|---|---|---|---|---|---|
| Invoker coupling to work | Very low. Sees `execute()` only | Low. Sees the algorithm interface | Very low. Sees a subscriber list | Low. Sees the first handler | Very low. Sees a signature | High. Names the callee | Very low. Publishes a fact |
| Adding an operation | New type, no edits | New type, no edits | New subscriber, no edits | New handler in the chain | New function, no edits | Edit the caller | New event type plus handler |
| Deferral and queueing | Strong. Its purpose | Not addressed | Weak. Delivery only | Not addressed | Strong if serialisation is not needed | Impossible | Strong. Log is the queue |
| Undo and redo | Strong. Its headline capability | Not addressed | Not addressed | Not addressed | Weak. No place for `undo()` | Not addressed | Medium. Reverse by compensation |
| Logging and replay | Strong when serialisable | Not addressed | Medium. Event log | Not addressed | Poor. Closures do not serialise | Not addressed | Strong. Its purpose |
| Type count | Plus one per operation | Plus one per algorithm | Plus one per subscriber | Plus one per handler | No new types | No new types | Plus one per event type |
| Cognitive load | Medium to high | Low | High. Flow is implicit | High. Chain order is implicit | Low | Very low | High. State is derived |
| Return of a result | Awkward. Fire and forget shape | Natural | Not applicable | Natural | Natural | Natural | Not applicable |
| Latency | One alloc plus one dispatch | One dispatch | One dispatch per subscriber | One dispatch per link | One indirect call | Inlinable | Write plus projection lag |
| Operability | Good. Queue and history are inspectable | Neutral | Poor. Fan out is hard to see | Poor. Where it stopped is hard to see | Neutral | Neutral | Good. The log is the record |
| Memory cost | History and queue depth | None | Subscriber list | None | None | None | Full log retention |
| Team topology | Good. Command type is the contract | Good | Medium. Implicit dependencies | Medium | Neutral | Poor. Shared caller is a hotspot | Good. Schema is the contract |

How to read the table. Command wins wherever the request needs to exist as a
value, whether that is for time, reversal, or auditing. Strategy wins where the
work happens now and a result is wanted. A closure wins wherever Command's shape
is wanted but none of its optional capabilities are, which is most of the time in
a language with first class functions. Observer wins on fan out, which Command
does not address. Event Sourcing wins on historical truth, and its column is the
reminder that a command log and an event log answer different questions.

## 13. Related and incompatible patterns

- **Memento.** The standard partner for undo. Where a command's change cannot be
  expressed as an invertible difference, the command captures a memento of the
  receiver before executing and restores it on undo. The division of
  responsibility matters. The receiver is the originator and owns the state, the
  command is the caretaker and holds the memento without inspecting it. A command
  that reaches into the memento to read individual fields has broken the
  encapsulation that made the memento worth having.
- **Composite.** Composes directly. A macro command is a Composite of commands,
  giving a group of changes one history entry and one atomic reversal. This is
  one of the cleanest compositions in the catalog because Composite requires no
  adaptation, a command that holds commands satisfies the same interface.
- **Prototype.** Applies where commands must be recorded and replayed. Rather
  than reconstructing a command from scratch, the history clones a prototype and
  fills in the captured arguments. This matters for macro recording features
  where the recorded command must be replayable with different arguments.
- **Strategy.** The nearest neighbour and the most confused with it. Identical
  in structure, opposite in intent. Strategy substitutes how a step is performed
  inside an algorithm that runs now. Command reifies what should be done so that
  it can be handled later or reversed. When a code review cannot tell which one a
  class is, ask whether anything ever holds the object without calling it. If
  nothing does, it is a Strategy.
- **Chain of Responsibility.** Complementary. Chain answers who should handle a
  request, Command answers what the request is. A request travelling down a chain
  is very often a command object, and the two together give a system that can
  both route and record.
- **Observer.** Adjacent and often mistaken for it. Observer notifies many
  listeners that something has happened. Command asks one receiver to make
  something happen. Direction differs, and so does the number of parties on the
  far end. Systems that need both usually accept commands on the write path and
  publish events on the notify path, which is the CQRS shape.
- **Mediator.** Composes above it. A mediator that coordinates several components
  is frequently implemented as a command dispatcher, with each interaction
  expressed as a command the mediator routes.
- **Interpreter.** A relative. An interpreter builds a tree of expression objects
  that are evaluated, which is in shape a composite of commands. The difference
  is that an interpreter's nodes are defined by a grammar and Command has no
  grammar.
- **Singleton.** Conflicts in practice. A command implemented as a process wide
  singleton cannot carry per request arguments and cannot appear twice on a
  history stack with different values, which removes both the deferral and the
  undo capabilities. Where a command is genuinely stateless, a shared immutable
  instance is safe, but the moment arguments appear the singleton must go.
- **Active Record.** Conflicts with the command log form. If commands mutate
  through objects that write themselves to the database on assignment, the
  ordering between the command log and the persistence writes is not controlled,
  so a replay after a crash can produce a state neither log describes.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. The named refactoring
closest to this is Replace Method with Method Object, see the refactoring family
entry. Ordered steps, each safe on its own.

1. Pick one operation that already exists as a method and that has more than one
   caller, or that is about to acquire a second trigger point. Do not start with
   the operation that needs undo, start with the one that needs a second caller,
   because the second caller justifies the change immediately.
2. Extract the operation into a class with a single `execute()` method. Move the
   parameters to constructor fields. The body is unchanged. Run the tests.
3. Replace the original method body with construction plus execution of the new
   command. Every existing caller still works and no signature changed. Run the
   tests.
4. Introduce the Command interface once a second operation has been converted.
   Introducing it with one implementation is speculative, and the interface will
   be shaped wrongly because one example is not enough to see the contract.
5. Change the trigger point to hold a Command rather than to call the method.
   At this point the invoker no longer names the operation, which is where the
   pattern begins paying.
6. If undo is a requirement, add `undo()` to the interface only after at least
   three commands exist, and implement it for all of them before shipping. A
   partially implemented undo is worse than none, per dimension 11.
7. Add the history stack to the invoker, with the redo discard rule from
   dimension 7 and a depth limit from the start rather than later.
8. Add the round trip test from dimension 15 for every reversible command before
   the feature is exposed to users.

Removing the pattern when it stops earning its place. The signals are a command
set where nothing is ever deferred, no `undo()` exists or every `undo()` throws,
and every command has exactly one construction site.

1. Confirm no command is stored, queued, logged, or reversed. If any is, the
   pattern is still earning something and only the unearning subset should move.
2. For each single caller command, inline the construction and execution into the
   caller. This is Inline Class, see the refactoring family entry. Run the tests
   after each one.
3. For commands whose only role was decoupling a trigger from work, replace the
   class with a function value held by the trigger. The wiring code keeps the
   substitutability and the type disappears.
4. Delete the Command interface once no implementation remains that needs a
   common type.
5. If a command log exists and is being retired, keep the log readable for the
   retention period the audit requirement demands, and record the schema even
   after the code that writes it has gone. Deleting the reader before the
   retention window closes turns an audit trail into unreadable bytes.

## 15. Testing and verification

Easier because of the pattern.

- A command is a small object with one entry point and explicit constructor
  arguments, so it is testable without any user interface, transport, or
  scheduler present. This is the single largest testability gain, and it is why
  moving logic out of event handlers into commands raises coverage in practice
  rather than in theory.
- The invoker is testable against a recording fake command that notes it was
  executed. History, ordering, redo discard, and depth limiting are all
  verifiable without a single real operation.
- Cross cutting behaviour is testable once rather than per operation. An
  authorisation decorator over the command interface has one test, not one per
  command.
- Queue behaviour is testable by submitting commands to an in memory invoker that
  executes them synchronously, which removes timing from most tests of the calling
  code.

Harder because of the pattern.

- Verifying that the right command was constructed for a given user gesture
  requires an assertion on the constructed object, since no call to the receiver
  happens at gesture time. Tests become two staged, one for construction and one
  for execution, and forgetting the first stage leaves the wiring untested.
- End to end behaviour crosses a queue, so tests either accept asynchrony or
  substitute a synchronous invoker, and the substitution can hide ordering bugs
  that only appear with real concurrency.
- Serialised commands need compatibility tests against previously written
  payloads, which is a test category that does not exist before the pattern is
  adopted.

Techniques that apply.

- **Round trip property test for undo.** For each reversible command, assert that
  applying it to a model and then undoing it yields a model equal to the
  original, across generated inputs. This is the highest value test in the whole
  pattern because it catches the derived state failure from dimension 11 that
  example based tests reliably miss.
- **History invariant test.** Assert that executing then undoing then redoing
  leaves the same state as executing once, and that a fresh execution empties the
  redo stack. Both are properties of the invoker rather than of any command, so
  one test protects every operation.
- **Macro rollback test.** Build a composite where a middle child fails, execute
  it, and assert the model equals its pre execution state. Without this test the
  partial application failure ships.
- **Idempotency test for queued commands.** Execute the same command instance
  twice against a fresh receiver and assert the state matches a single execution.
  This is the only test that catches the duplicate delivery failure before
  production does.
- **Serialisation compatibility test.** Keep a fixture of command payloads
  produced by earlier releases and assert each still deserialises and executes.
  Generate new fixtures at each release rather than editing the old ones.
- **Contract test across implementations.** One abstract test class written
  against the Command interface, subclassed per concrete command, asserting the
  common properties, that `execute()` is not called during construction, that
  `undo()` after `execute()` restores, and that repeated `execute()` is either
  idempotent or documented as not.
- **Test double choice.** Prefer a handwritten fake command over a mocking
  framework. The interface has one or two methods, so the fake costs three lines
  and records ordering, which a strict mock makes awkward.

## 16. Observability signals

The pattern moves work away from the call site, so telemetry has to carry what
the stack no longer does. Without instrumentation a command queue is a place
where work goes and nothing can be said about it.

What to record.

- On submission, a span or log line holding the command type, the submitting
  actor, the correlation identifier, and the command's own identifier. The
  command identifier is what allows a single request to be followed from
  submission through retries to completion.
- Trace context carried as fields on the command itself, not only in the
  submission log. A command that crosses a queue loses ambient context, so the
  linkage between the submitting span and the executing span exists only if the
  command carries it.
- A counter of commands submitted and a counter of commands completed, both
  labelled by command type. The gap between the two is the in flight population
  and is the first number to look at during an incident.
- A counter of command failures labelled by command type and error class, kept
  separate from the completion counter so that a rising failure rate is visible
  without arithmetic.
- A histogram of queue wait time, from submission to the start of execution,
  labelled by command type. This is distinct from execution duration and the two
  fail for different reasons, wait time grows when consumers are starved and
  execution time grows when a receiver slows down.
- A histogram of execution duration, labelled the same way.
- A gauge of queue depth, and for a scheduled invoker a gauge of the delay
  between the scheduled time and the actual start.
- A counter of retries and of duplicate detections, labelled by command type. A
  climbing duplicate count with a flat retry count means the transport is
  redelivering rather than the application retrying.
- For an interactive application with undo, a gauge of undo stack depth and a
  counter of undo and redo invocations by command type. The undo counter is a
  product signal as much as an operational one, a command undone far more often
  than average is usually a user interface defect.

A healthy instance on a dashboard. Submitted and completed counters track each
other with a small constant offset. Queue depth is low and flat, or sawtooths
within a bounded range for a batching consumer. Queue wait time is a small
fraction of execution time. The failure counter is near zero and its rate does
not correlate with deployment times. Undo stack depth grows during a session and
resets on save or document close, rather than growing without bound.

A failing instance. Queue depth climbing steadily while completion stays flat,
which is a stalled consumer rather than a slow one and needs a different
response. Wait time growing while execution time stays flat, which is a capacity
problem in the consumer pool. Duplicate detection counts rising after a
deployment, which usually means acknowledgement timing changed. One command type
failing while every other type succeeds, which localises the fault to a receiver
without reading code. Undo stack depth rising and never falling in a long lived
process, which is the unbounded history leak from dimension 11. A command type
appearing in production that no current trigger point constructs, which means
either an old queued payload is still being consumed or an unexpected client is
submitting.

## 17. Security and privacy implications

The pattern has genuine security consequences, and they cluster in the forms
that persist or transport commands. In the purely synchronous in process form it
is close to neutral, and saying otherwise would be inventing a concern.

**Deserialisation of commands is remote code execution shaped.** A command
written to a queue or a log is deserialised by a consumer and then executed. If
the serialisation format allows the payload to name the type to instantiate, an
attacker who can write to the queue chooses which code runs. This is the classic
insecure deserialisation failure and the command form makes it directly
exploitable, because execution is what the object is for. The mitigation is a
closed allowlist of deserialisable command types, resolved from a registry rather
than from a name in the payload, plus a data only format that cannot express
arbitrary object graphs.

**Authorisation must be checked at execution, not only at submission.** A command
carries the intent of whoever created it, and by the time it executes that person
may have lost the right to perform it, or the command may have been replayed from
a log by an operator. Checking permission in the user interface that constructed
the command and nowhere else produces a system where anything that can enqueue can
do anything. Carry the acting identity on the command and re evaluate the
authorisation decision in the invoker or the receiver.

**Command payloads become a data retention surface.** Arguments captured at
construction are precisely the data the user supplied, which for many operations
is personal data. Once those arguments are on a durable queue or in an append only
log, they inherit the retention and deletion obligations of that data, and an
append only log is by construction hostile to a deletion request. Decide before
adopting command logging which fields may be persisted, keep identifiers rather
than values where the value is sensitive, and design a redaction or crypto
shredding path rather than discovering the requirement after the log has years of
history in it.

**Replay is an attack primitive as well as a recovery tool.** A captured command
that is valid when submitted remains valid indefinitely unless something prevents
its reuse. In a system with at least once delivery the application is already
tolerant of duplicates, which means an attacker replaying a captured payload
looks like the transport doing its job. Bind commands to a nonce or an
identifier the receiver records, and give commands an expiry beyond which the
receiver refuses them.

**Undo can be a security control or a hole, depending on scope.** An undo stack
that spans a security boundary allows one principal to revert another principal's
change, which is a privilege escalation that reads as a feature. Scope the
history to the session and the actor, and treat an undo of another actor's change
as a distinct operation with its own authorisation.

**The macro command multiplies whatever it contains.** A composite of a thousand
children is one submission and a thousand executions, so a request path that
accepts an attacker influenced list and turns it into a macro command converts a
cheap request into an expensive one. Bound the child count at the boundary that
constructs the composite.

On privacy in the interactive case, the undo history holds prior versions of user
content by design, including content the user deleted deliberately. Where the
application autosaves, a naive implementation persists the undo stack alongside
the document, so text a user removed before saving survives on disk. Decide
explicitly whether history is persisted, and where it is, say so in the product
rather than leaving it to be discovered.

## Code examples

Four languages chosen to show different points on the variant axis. Java shows
the classical form with a receiver, an invoker and undo. TypeScript shows the
same shape and then the closure form that replaces it when undo is not needed.
Python shows the data record form used for queueing and replay. Go shows the
function value form that is idiomatic where the language has no inheritance. C++
and Rust are omitted from the examples rather than from the discussion, because
in both the interesting content is ownership of the history stack rather than the
pattern shape, and that is covered in dimension 8.

### Java

```java
import java.util.ArrayDeque;
import java.util.Deque;

interface Command {
    void execute();
    void undo();
}

final class Document {
    private final StringBuilder text = new StringBuilder();

    void insert(int at, String s) { text.insert(at, s); }
    void delete(int at, int len) { text.delete(at, at + len); }
    String read() { return text.toString(); }
}

final class InsertText implements Command {
    private final Document doc;
    private final int at;
    private final String value;

    InsertText(Document doc, int at, String value) {
        this.doc = doc;
        this.at = at;
        this.value = value;
    }

    public void execute() { doc.insert(at, value); }
    public void undo() { doc.delete(at, value.length()); }
}

final class History {
    private final Deque<Command> done = new ArrayDeque<>();
    private final Deque<Command> undone = new ArrayDeque<>();
    private final int limit;

    History(int limit) { this.limit = limit; }

    void run(Command c) {
        c.execute();
        done.push(c);
        undone.clear();
        while (done.size() > limit) {
            done.removeLast();
        }
    }

    void undo() {
        if (done.isEmpty()) return;
        Command c = done.pop();
        c.undo();
        undone.push(c);
    }

    void redo() {
        if (undone.isEmpty()) return;
        Command c = undone.pop();
        c.execute();
        done.push(c);
    }
}

public final class Demo {
    public static void main(String[] args) {
        Document doc = new Document();
        History history = new History(100);
        history.run(new InsertText(doc, 0, "world"));
        history.run(new InsertText(doc, 0, "hello "));
        System.out.println(doc.read());
        history.undo();
        System.out.println(doc.read());
        history.redo();
        System.out.println(doc.read());
    }
}
```

### TypeScript

The first half is the classical form with undo. The second half is the closure
form, which removes both command classes and is correct wherever deferral is
wanted and undo is not.

```typescript
interface Command {
  execute(): void;
  undo(): void;
}

class Counter {
  value = 0;
}

class AddCommand implements Command {
  constructor(private readonly target: Counter, private readonly by: number) {}

  execute(): void {
    this.target.value += this.by;
  }

  undo(): void {
    this.target.value -= this.by;
  }
}

class UndoHistory {
  private done: Command[] = [];
  private undone: Command[] = [];

  run(c: Command): void {
    c.execute();
    this.done.push(c);
    this.undone = [];
  }

  undo(): void {
    const c = this.done.pop();
    if (!c) return;
    c.undo();
    this.undone.push(c);
  }
}

const counter = new Counter();
const undoHistory = new UndoHistory();
undoHistory.run(new AddCommand(counter, 5));
undoHistory.run(new AddCommand(counter, 3));
undoHistory.undo();
console.log(counter.value);

type Task = () => void;

class Queue {
  private pending: Task[] = [];

  submit(t: Task): void {
    this.pending.push(t);
  }

  drain(): void {
    while (this.pending.length > 0) {
      const t = this.pending.shift();
      if (t) t();
    }
  }
}

const q = new Queue();
const c2 = new Counter();
q.submit(() => { c2.value += 5; });
q.submit(() => { c2.value += 3; });
q.drain();
console.log(c2.value);
```

### Python

The data record form, with dispatch through a registry. This is the shape used
where commands are serialised and replayed.

```python
from dataclasses import dataclass, asdict
from typing import Callable


@dataclass(frozen=True)
class Deposit:
    account: str
    minor_units: int


@dataclass(frozen=True)
class Withdraw:
    account: str
    minor_units: int


class Ledger:
    def __init__(self) -> None:
        self.balances: dict[str, int] = {}

    def apply_deposit(self, cmd: Deposit) -> None:
        self.balances[cmd.account] = self.balances.get(cmd.account, 0) + cmd.minor_units

    def apply_withdraw(self, cmd: Withdraw) -> None:
        current = self.balances.get(cmd.account, 0)
        if current < cmd.minor_units:
            raise ValueError("insufficient funds")
        self.balances[cmd.account] = current - cmd.minor_units


class Dispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[object], None]] = {}

    def register(self, name: str, handler: Callable[[object], None]) -> None:
        if name in self._handlers:
            raise KeyError(f"duplicate handler for {name}")
        self._handlers[name] = handler

    def dispatch(self, cmd: object) -> None:
        name = type(cmd).__name__
        handler = self._handlers.get(name)
        if handler is None:
            raise KeyError(f"no handler for {name}")
        handler(cmd)


if __name__ == "__main__":
    ledger = Ledger()
    dispatcher = Dispatcher()
    dispatcher.register("Deposit", ledger.apply_deposit)
    dispatcher.register("Withdraw", ledger.apply_withdraw)

    log: list[tuple[str, dict]] = []
    for cmd in [Deposit("a", 1000), Withdraw("a", 250)]:
        dispatcher.dispatch(cmd)
        log.append((type(cmd).__name__, asdict(cmd)))

    print(ledger.balances)

    replayed = Ledger()
    replay = Dispatcher()
    replay.register("Deposit", replayed.apply_deposit)
    replay.register("Withdraw", replayed.apply_withdraw)
    types = {"Deposit": Deposit, "Withdraw": Withdraw}
    for name, payload in log:
        replay.dispatch(types[name](**payload))

    print(replayed.balances)
```

### Go

Go has no inheritance, so the pattern lands as a small interface plus function
values. Both forms are shown because Go uses each in different places.

```go
package main

import "fmt"

type Command interface {
	Execute()
	Undo()
}

type Stack struct {
	items []int
}

type PushCommand struct {
	target *Stack
	value  int
}

func (c PushCommand) Execute() {
	c.target.items = append(c.target.items, c.value)
}

func (c PushCommand) Undo() {
	if len(c.target.items) == 0 {
		return
	}
	c.target.items = c.target.items[:len(c.target.items)-1]
}

type History struct {
	done []Command
}

func (h *History) Run(c Command) {
	c.Execute()
	h.done = append(h.done, c)
}

func (h *History) Undo() {
	if len(h.done) == 0 {
		return
	}
	last := h.done[len(h.done)-1]
	h.done = h.done[:len(h.done)-1]
	last.Undo()
}

type Task func()

func drain(tasks []Task) {
	for _, t := range tasks {
		t()
	}
}

func main() {
	s := &Stack{}
	h := &History{}
	h.Run(PushCommand{target: s, value: 1})
	h.Run(PushCommand{target: s, value: 2})
	h.Undo()
	fmt.Println(s.items)

	total := 0
	drain([]Task{
		func() { total += 5 },
		func() { total += 3 },
	})
	fmt.Println(total)
}
```

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Command. Source
   of the intent, the Action and Transaction aliases, and the five participants.
   Same chapter, section Memento, for the state restoration pairing.
2. Bertrand Meyer. *Object Oriented Software Construction*, 2nd edition.
   Prentice Hall, 1997. ISBN 0-13-629155-4. Source of Command Query Separation,
   cited through Fowler in dimension 1 rather than by page, because the page was
   not independently confirmed.
3. Martin Fowler. "CommandQuerySeparation".
   https://martinfowler.com/bliki/CommandQuerySeparation.html
   Verified 2026-08-02. Source for the attribution to Meyer and the query versus
   modifier distinction in dimension 1.
4. Martin Fowler. "CQRS". https://martinfowler.com/bliki/CQRS.html
   Verified 2026-08-02. Source for the CQRS definition, its relationship to
   event collaboration, and the caution quoted in dimension 4.
5. Martin Fowler. "Event Sourcing". https://martinfowler.com/eaaDev/EventSourcing.html
   Verified 2026-08-02. Source for the Event Sourcing definition, the complete
   rebuild and temporal query facilities, and the observation that reversal is
   most direct when a change is expressed as a difference.
6. Oracle. *Java SE 17 API Specification*, `java.lang.Runnable`.
   https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Runnable.html
   Verified 2026-08-02. Source for the statement that Runnable lets a class be
   active without subclassing Thread.
7. Oracle. *Java SE 21 API Specification*, `java.lang.Runnable`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Runnable.html
   Verified 2026-08-02. Source for the current wording, an operation that does
   not return a result, and for the functional interface status.
8. Oracle. *Java SE 21 API Specification*, `java.util.concurrent.Callable`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Callable.html
   Verified 2026-08-02. Source for the Callable contract and its stated
   difference from Runnable.
9. Oracle. *Java SE 21 API Specification*, `java.util.concurrent.Executor`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Executor.html
   Verified 2026-08-02. Source for the decoupling of task submission from
   execution mechanics and the `execute(Runnable command)` contract.
10. Oracle. *Java SE 21 API Specification*, `javax.swing.undo.UndoableEdit`.
    https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/javax/swing/undo/UndoableEdit.html
    Verified 2026-08-02. Source for the Swing undo production use and the
    `addEdit()` coalescing mechanism.
11. The Qt Company. *Qt 6 documentation*, `QUndoCommand`.
    https://doc.qt.io/qt-6/qundocommand.html
    Verified 2026-08-02. Source for the undo and redo contract, stack ownership,
    and the `id()` plus `mergeWith()` compression mechanism.
12. Apple. *Undo Architecture*, article "Undo Manager", Apple Developer Archive.
    https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/UndoArchitecture/Articles/UndoManager.html
    Verified 2026-08-02. Source for the definition of an undo operation, undo
    grouping, and the rule that registering a new undo operation clears the redo
    stack.
13. Microsoft. *Visual Studio Code API documentation*, "Commands".
    https://code.visualstudio.com/api/extension-guides/command
    Verified 2026-08-02. Source for `registerCommand`, `executeCommand`, and the
    binding of one command to the palette, keybindings, and menus.
14. Redis. *Redis documentation*, "Redis persistence".
    https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
    Verified 2026-08-02. Source for AOF logging every write operation, replay at
    startup, and log rewriting.
15. Wikipedia contributors. "Command pattern".
    https://en.wikipedia.org/wiki/Command_pattern
    Verified 2026-08-02. Used to confirm the four participant naming and the
    undo stack description, not as a source of explanation.
16. Wikipedia contributors. "Memento pattern".
    https://en.wikipedia.org/wiki/Memento_pattern
    Verified 2026-08-02. Used to confirm the originator, caretaker and memento
    roles and the undo application referenced in dimension 8.

Code verification note, recorded 2026-08-02. The Python example was executed and
printed two matching ledger states, which is the replay assertion it exists to
demonstrate. The Go example was compiled and run with `go run`. The TypeScript
block was type checked clean with `tsc --strict --target es2020`, and the undo
history class is named `UndoHistory` because `History` collides with the DOM
global of that name. The Java example was NOT compiled, because the authoring
machine has no Java runtime installed, only the macOS `javac` stub, so it is
reviewed rather than verified. No example depends on a third party library.
