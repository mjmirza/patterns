---
name: Observer
slug: observer
family: 01-design-patterns-gof
category: Behavioral
aliases: [Dependents, Publish-Subscribe, Listener, Event Listener, Signal-Slot]
first_described: "Gamma, Helm, Johnson, Vlissides 1994"
maturity: canonical
related: [mediator, singleton, command, strategy, chain-of-responsibility, memento]
incompatible_with: []
verified: 2026-08-02
---

# Observer

## 1. Name, aliases, and lineage

The canonical name is Observer. It appears in the Gang of Four catalog among the
eleven behavioral patterns, in Erich Gamma, Richard Helm, Ralph Johnson and John
Vlissides, *Design Patterns. Elements of Reusable Object-Oriented Software*,
Addison-Wesley, 1994, chapter 5, Behavioral Patterns, section Observer. The book
states the intent as defining a one to many dependency between objects so that
when one object changes state, all its dependents are notified and updated
automatically, and it records the aliases **Dependents** and **Publish-Subscribe**
([reproduction of the GoF Observer chapter, University of North Carolina](https://www.cs.unc.edu/~stotts/GOF/hires/pat5g.htm),
verified 2026-08-02).

The lineage runs back further than the book. The same chapter states that the
first and perhaps best known example of the pattern appears in the Smalltalk
Model View Controller framework, where the Model plays Subject and the Views play
Observers, and it names InterViews, the Andrew Toolkit and Unidraw as other
systems built on the same mechanism (same source, Known Uses section, verified
2026-08-02). The Smalltalk term for the mechanism was *dependents*, which is why
the book carries Dependents as an alias.

Four other names describe the same shape in different communities, and knowing
which one a colleague means saves an argument.

- **Listener** and **Event Listener.** The prevailing name in Java, JavaScript and
  the browser. The `addEventListener` and `removeEventListener` pair on the DOM
  `EventTarget` interface is Observer with subject-side registration and an
  explicit removal call ([MDN, EventTarget.addEventListener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener),
  verified 2026-08-02).
- **Signal and Slot.** The Qt vocabulary. Qt defines a signal as emitted when a
  particular event occurs and a slot as a function called in response to a
  particular signal, and presents the mechanism as an alternative to the callback
  technique rather than as an implementation of Observer
  ([Qt 6, Signals and Slots](https://doc.qt.io/qt-6/signalsandslots.html),
  verified 2026-08-02). The connection object is the registration handle.
- **Bound property.** The JavaBeans vocabulary, where a property that fires a
  `PropertyChangeEvent` on assignment is called bound
  ([Oracle, java.beans.PropertyChangeSupport](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/beans/PropertyChangeSupport.html),
  verified 2026-08-02).
- **Reactive stream, observable, signal.** The modern descendants, treated as
  their own topic in dimension 8 and dimension 13 rather than as pure synonyms,
  because each adds semantics the GoF pattern does not carry.

The alias that causes the most damage is **Publish-Subscribe**. The GoF book
carries it as an alias, which is historically accurate for 1994 and misleading
in 2026, because the messaging community independently defined a Publish
Subscribe Channel with different properties. Dimension 13 resolves the two with
a table rather than repeating the conflation.

## 2. Problem and context

A piece of state changes, and an unknown number of other pieces of the system
need to react. The set of reactors is not known when the state holder is written,
changes at runtime, and belongs to layers the state holder must not depend on.

The situation reads like this in a real codebase. There is a class holding
authoritative state, an order, a document, a connection, a configuration, a
sensor reading, a cart. When that state changes, several things must happen. A
view must repaint. A cache must invalidate. An audit record must be written. A
metric must increment. A downstream service must be told. The direct approach
puts all five calls inside the setter. That setter now imports the view layer,
the cache, the audit writer, the metrics client and an HTTP client, which makes
the state holder untestable without all five, undeployable without all five, and
unchangeable without touching the file every team also wants to touch.

The second symptom is the polling loop. Rather than importing the five
collaborators, somebody writes a timer that reads the state every hundred
milliseconds and compares it against the last value it saw. This decouples the
state holder correctly and pays for it with latency that is half the poll
interval on average, with CPU burned on the overwhelming majority of polls that
find nothing changed, and with a race in which two changes inside one interval
collapse into one observed transition. Observer exists to convert that poll into
a callback.

The context in which Observer is the right answer has four parts, and the pattern
misbehaves when any of them is absent.

- The subject genuinely does not need to know what the observers are. If it does
  need to know, because it must sequence them or aggregate their results, a
  direct call or a Mediator is the honest design.
- The number of observers varies, either across deployments or during the life of
  one process. A fixed set of exactly two collaborators is a pair of direct calls
  with fewer moving parts.
- The reaction is a notification, not a request. Observer has no return channel.
  A subject that wants an answer from its observers is misusing the pattern, see
  dimension 4.
- The observers can be given a defined lifetime, so that registration is matched
  by deregistration. When observers outlive their usefulness and nobody removes
  them, the pattern produces the leak described at length in dimension 11.

The abstraction the GoF book names as the trigger is worth quoting in paraphrase.
It says to use Observer when an abstraction has two aspects, one dependent on the
other, so that encapsulating them separately lets each vary and be reused
independently, when a change to one object requires changing an unknown number of
others, and when an object should notify others without making assumptions about
who those others are (same UNC reproduction, Applicability section, verified
2026-08-02). The third clause is the load bearing one. Observer buys ignorance
about the identity of the receivers, and every cost the pattern imposes is the
price of that ignorance.

## 3. Forces

The weighting below is engineering judgement about which pressure carries the
most weight in ordinary service and application code. The mechanics being weighed
are sourced, the ranking is reasoning.

- **Coupling.** Strongly favoured, in one direction. The subject depends only on
  an observer interface it publishes, and nothing else. Observers depend on the
  subject's registration surface and on the payload type. The dependency arrow
  from the state holder to the reactors is removed entirely, which is the whole
  purchase.
- **Cognitive load.** Sacrificed, and more heavily than most catalogs admit. No
  call graph in the source connects the state change to the reaction. A reader
  tracing why a cache entry vanished finds a `notify` loop and has to discover
  the registration sites by searching, which in a plugin system may be a
  different repository. Control flow becomes discontinuous at the notification
  point.
- **Latency.** Favoured against polling, sacrificed against a direct call. A
  change reaches a reactor in one virtual dispatch rather than in half a poll
  interval. But the subject now pays the cost of every observer on its own
  thread in the synchronous form, so the write path's latency is the sum of all
  observer bodies, and the slowest observer sets the lower bound.
- **Consistency.** Sacrificed in a specific and dangerous way. Observers see the
  subject after the change and before any subsequent change, if and only if the
  subject notifies inside the same critical section. If it notifies afterwards,
  observers can read a state that has moved on. The GoF book flags the related
  hazard directly, warning that a seemingly harmless operation on the subject can
  cause a chain of further updates across observers and their own dependents, and
  that spurious updates from a poorly defined dependency are difficult to
  diagnose (UNC reproduction, Consequences section, verified 2026-08-02).
- **Operability.** Sacrificed. The registered set is runtime state that no source
  file lists. An operator investigating a missing side effect cannot read the
  code to learn whether the observer was attached, which is why dimension 16
  treats a registration gauge as the primary signal rather than a nicety.
- **Cost.** Favoured on machine cost against polling, since work is done only on
  change. Sacrificed on memory, because the subject holds a collection that grows
  with subscriber count and, in the naive form, never shrinks.
- **Team topology.** Strongly favoured. The subject and the observer interface are
  a published contract one team owns. Every reacting team writes its own observer
  in its own module on its own release schedule and never edits the subject. This
  is the property that makes the pattern the backbone of extensible frameworks.
- **Testability.** Mixed, and usually reported wrongly. The subject becomes easy
  to test because a recording observer replaces five collaborators. The system
  becomes harder to test because an end to end assertion now depends on wiring
  that lives elsewhere and can silently be absent.
- **Failure isolation.** Sacrificed by default. In the plain synchronous loop an
  exception from observer three prevents observers four and five from running and
  propagates into the subject's write path. Nothing in the classical pattern
  prevents this, and dimension 8 covers the variants that do.

The pattern's honest summary is that it trades static readability and write path
predictability for runtime extensibility. A team that values the first two more
than the third should not adopt it.

## 4. Applicability and non-applicability

Reach for Observer when the following hold.

- A state change must reach a set of reactors whose membership is unknown at
  compile time or varies at runtime.
- The reaction is fire and forget. The subject does not read a result, does not
  branch on one, and is correct whether zero or fifty observers are attached.
- The alternative under consideration is a polling loop, and the change rate is
  far lower than the poll rate that would be needed for acceptable latency.
- A framework must let application code react to internal lifecycle events
  without the framework naming the application types.
- Two or more views of the same underlying data must stay in agreement, which is
  the original Smalltalk MVC case.
- The reactors belong to a higher architectural layer than the state holder, so a
  direct call would invert the dependency direction the architecture requires.

Do NOT reach for Observer in the following cases. This non-applicability list is
the more useful half, and the reason attached to each entry matters more than the
entry.

- **The subject needs an answer.** If the subject inspects results, aggregates
  votes, or stops on the first observer that objects, the design is a request
  with multiple candidate handlers. That is Chain of Responsibility when one
  handler should win, or a plain collaborator call when the subject genuinely
  depends on the answer. Bolting return values onto `update` reintroduces the
  coupling the pattern removed, because the subject now depends on the meaning of
  the returned value.
- **The observer set is fixed, small and known.** Two collaborators that ship in
  the same module as the subject should be called directly. The registration
  machinery buys nothing, and it removes the compiler's ability to tell you that
  a collaborator was never wired up.
- **Ordering between observers matters.** The classical pattern gives no ordering
  contract. Java's own deprecation notice for `Observable` states plainly that
  the order of notifications delivered is unspecified
  ([Oracle, java.util.Observable](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Observable.html),
  verified 2026-08-02). Kubernetes makes the same admission for its informer
  layer, documenting that events to a single handler are delivered sequentially
  but that there is no coordination between different handlers
  ([client-go SharedInformer source](https://raw.githubusercontent.com/kubernetes/client-go/master/tools/cache/shared_informer.go),
  verified 2026-08-02). A design that needs step B after step A needs a pipeline,
  a workflow or a Mediator, not a listener list plus a comment asking people to
  register in the right sequence.
- **The reaction must be durable across a crash.** In process observers are lost
  when the process dies, and there is no redelivery, no acknowledgement and no
  dead letter path. A requirement that a downstream system eventually learns of
  the change is a messaging requirement, see the Publish Subscribe Channel row in
  dimension 12.
- **Observers cannot be deregistered.** If the observers are created by code you
  do not control, on a schedule you cannot observe, and no teardown hook exists,
  the leak in dimension 11 is not a risk but a certainty. Either add a lifetime
  owner such as Android's `LifecycleOwner`, or use a weak registry, or do not use
  the pattern.
- **The notification rate is high and the observer count is large.** The
  synchronous loop is O(observers) on the write path. A subject changing ten
  thousand times per second with two hundred observers is performing two million
  virtual calls per second inside a hot path, and coalescing or batching is
  required before the pattern is viable.
- **The dependency graph is diamond shaped and values must be consistent.** If
  observer C depends on both A and B, and A and B both derive from one root, a
  single root change delivers two notifications to C and C computes once on an
  inconsistent intermediate state. This is the glitch problem, and it is exactly
  what the pull based signal designs exist to prevent
  ([TC39 proposal-signals](https://github.com/tc39/proposal-signals), verified
  2026-08-02). Plain Observer cannot express it.
- **The pattern is being used to avoid a design decision.** A codebase where
  every module both emits and consumes events, with no direction to the graph, has
  not decoupled anything. It has replaced a readable dependency graph with an
  unreadable one and called the result an architecture.

## 5. Structure

Five participants, named for the role each plays. The first four are the GoF set,
quoted in paraphrase from the chapter's Participants section (UNC reproduction,
verified 2026-08-02). The fifth appears in the same chapter as an implementation
option and is promoted here because production systems almost always need it.

- **Subject.** Knows its observers, and any number of observers may watch one
  subject. Publishes the operations for attaching and detaching an observer, and
  the operation that walks the collection delivering notifications. It knows the
  observer only through the Observer interface.
- **Observer.** Defines the updating interface that anything wanting notification
  of a subject's change must implement. In the classical form this is a single
  method. In language-idiomatic forms it is a function value, a closure or a
  method reference, which changes nothing about the shape of the pattern.
- **ConcreteSubject.** Holds the state the observers care about, and sends a
  notification when that state changes. The decision about *when* it notifies is
  the single most consequential design choice in the pattern, see dimension 7.
- **ConcreteObserver.** Holds a reference to the concrete subject where it needs
  one, holds any state that must agree with the subject's, and implements the
  updating interface so its own state is brought back into agreement.
- **Registration handle, sometimes called a Subscription or a Token.** The value
  returned by attach, whose only job is to detach. It is not in the GoF
  participant list, and its absence is the single largest cause of the leak in
  dimension 11. Every modern library has converged on it. The .NET provider
  contract returns an `IDisposable` from `Subscribe` for exactly this purpose
  ([Microsoft, System.IObservable&lt;T&gt;](https://learn.microsoft.com/en-us/dotnet/api/system.iobservable-1),
  verified 2026-08-02). Redux returns an unsubscribe function from `subscribe`
  ([Redux Store API](https://redux.js.org/api/store), verified 2026-08-02).
  Kubernetes returns a `ResourceEventHandlerRegistration` from `AddEventHandler`
  and accepts it back in `RemoveEventHandler` (client-go source, verified
  2026-08-02).

A sixth participant appears when the mapping grows complicated. The GoF chapter
names it **ChangeManager** and describes it as an object that maps a subject to
its observers, provides the interface to maintain that mapping, defines an update
strategy, and updates all dependent observers at the request of a subject (UNC
reproduction, Implementation section, verified 2026-08-02). A ChangeManager is a
Mediator, and its presence is the signal that the design has outgrown plain
Observer, see dimension 13.

Relationships. Subject holds a collection of Observer, never of ConcreteObserver.
ConcreteObserver may hold a reference back to ConcreteSubject, which creates a
reference cycle in a reference counted runtime and a retention path in a tracing
one. That back reference is what makes the pull model possible and what makes the
leak possible, and the two facts are the same fact.

## 6. ASCII structure diagram

```
+-----------------------------+
| Subject                     |
| - observers: List<Observer> |
| + attach(o): Registration   |
| + detach(reg)               |
| # notify()                  |
+-----------------------------+
     | holds 0..*
     v
+--------------------+
| Observer           |
| + update(subject?) |
+--------------------+

+----------------------------------+
| ConcreteSubject, extends Subject |
| - state: State                   |
| + getState(): State              |
| + setState(s) -> notify()        |
+----------------------------------+
     | reads (pull), dashed back reference
     v
+----------------------------------------+
| ConcreteObserverA, implements Observer |
| - subject: ref                         |
| + update(...)                          |
+----------------------------------------+
+----------------------------------------+
| ConcreteObserverB, implements Observer |
| - cache                                |
| + update                               |
+----------------------------------------+

Solid arrow means a compile-time dependency. Dashed
arrow is the pull model's back reference, absent in the
push model. The Registration returned by attach() is
the only thing that can detach.
```

## 7. Dynamics

Two flows matter. The first is the ordinary notification cycle. The second is the
reentrant case, which is where the pattern actually breaks in production.

### Ordinary notification, pull model

```
Client        ConcreteSubject       ObserverA          ObserverB
  |                 |                   |                  |
  |-- attach(A) --->|                   |                  |
  |<-- regA --------|                   |                  |
  |-- attach(B) --->|                   |                  |
  |<-- regB --------|                   |                  |
  |                 |                   |                  |
  |-- setState(s2)->|                   |                  |
  |                 |-- state = s2      |                  |
  |                 |-- notify()        |                  |
  |                 |----- update(this) ->|                |
  |                 |<---- getState() ----|                |
  |                 |----- s2 ----------->|                |
  |                 |                   |-- reconcile      |
  |                 |<---- return -------|                  |
  |                 |----- update(this) ------------------->|
  |                 |<---- getState() ----------------------|
  |                 |----- s2 ---------------------------->|
  |                 |<---- return --------------------------|
  |<-- return ------|                   |                  |
  |                 |                   |                  |
  |-- detach(regA)->|                   |                  |
  |                 |-- observers.remove(A)                |
```

Three properties of that flow are worth stating plainly, because each one is a
place teams assume a guarantee that does not exist.

**The subject blocks until every observer returns.** `setState` does not complete
until observer B has finished. The caller of `setState` pays for both observers.
Node's `EventEmitter` documents this contract directly, stating that the emitter
calls all listeners synchronously in the order in which they were registered, and
that this sequencing avoids race conditions
([Node.js Events API](https://nodejs.org/api/events.html), verified 2026-08-02).
Node's guarantee of registration order is a property of that implementation, not
of the pattern. Java's `Observable` guaranteed nothing, which is one of the three
reasons given for its deprecation (Oracle javadoc, verified 2026-08-02).

**The observer reads state after the change.** In the pull model, observer A calls
`getState` and receives whatever the subject holds at that instant, not
necessarily the value that triggered the notification. If observer A's own work
causes a second `setState`, observer B will be notified of change one while
reading state two. This is the source of the most confusing class of bug in the
pattern.

**Detach after notification is safe, detach during notification may not be.** The
second flow covers that.

### Reentrancy: an observer mutating the subject during notification

```
Client      Subject           ObserverA            ObserverB
  |            |                  |                    |
  |- set(s2) ->|                  |                    |
  |            |- state = s2      |                    |
  |            |- notify() begins iterating observers  |
  |            |---- update() --->|                    |
  |            |                  |- decides to react  |
  |            |<--- set(s3) -----|                    |
  |            |- state = s3                           |
  |            |- notify() BEGINS AGAIN (reentrant)    |
  |            |---- update() --->|  (A sees s3)       |
  |            |---- update() ------------------------>|  (B sees s3)
  |            |<--- inner notify returns              |
  |            |<--- A returns ---|                    |
  |            |- outer notify RESUMES its iteration   |
  |            |---- update() ------------------------>|  (B sees s3 again)
  |            |                                       |
  |<- return --|   B was notified twice, A once, for two changes.
```

The failure modes visible in that trace are the ones every mature implementation
has had to answer.

- **Duplicate delivery.** Observer B is called twice and observer A once, for two
  state transitions. Neither observer can tell how many changes occurred from the
  call count.
- **Lost transition.** Neither observer ever saw state `s2`. In the pull model
  both reads returned `s3`, so a transition was skipped. An observer computing a
  running total from transitions is now wrong.
- **Concurrent modification.** If observer A attaches or detaches an observer
  during its `update`, the outer `notify` is iterating a collection that changed
  underneath it. In Java this throws `ConcurrentModificationException`, which is
  precisely the guarantee `CopyOnWriteArrayList` buys back by handing out an
  iterator over the array as it stood when the iterator was created
  ([Oracle, java.util.concurrent.CopyOnWriteArrayList](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html),
  verified 2026-08-02). In C++ it is undefined behaviour on an invalidated
  iterator.
- **Unbounded recursion.** If observer A always sets state in response to a state
  change, and the subject always notifies on set, the stack overflows. The GoF
  chapter names this hazard as a chain of updates reaching observers and their
  dependent objects, and says the resulting spurious updates are hard to track
  down (UNC reproduction, Consequences, verified 2026-08-02).

The two answers that work are both about defining the semantics rather than
hoping the case does not arise.

**Snapshot the observer list before iterating.** Redux specifies this behaviour
explicitly, stating that subscriptions are snapshotted before every `dispatch`
call, that subscribing or unsubscribing while listeners are being invoked has no
effect on the dispatch currently in progress, and that the next dispatch will use
a more recent snapshot (Redux Store API, verified 2026-08-02). The snapshot fixes
concurrent modification. It does not fix duplicate delivery.

**Suppress the notification when the value did not change.** Both major Java
mechanisms do this. `PropertyChangeSupport` states that no event is fired if the
old and new values are equal and non null (Oracle javadoc, verified 2026-08-02).
Kotlin's `StateFlow` conflates by `Any.equals`, suppressing emission when the new
value equals the previously emitted one
([Kotlin StateFlow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/),
verified 2026-08-02). Equality suppression converts many accidental update chains
into a single notification, because the reentrant write frequently writes the
value the subject already holds. It cannot terminate a genuine ping pong between
two observers that alternate values, so a depth guard is still needed for that.

Redux's third documented caveat is the one people miss. It says the listener
should not expect to see all state changes, because state may have been updated
several times during a nested dispatch before the listener runs, while
guaranteeing that all subscribers registered before the dispatch started will be
called with the latest state by the time it exits (Redux Store API, verified
2026-08-02). That is the honest contract for a synchronous observer under
reentrancy. Latest state is guaranteed. Every transition is not.

## 8. Implementation variants

**Push model.** The subject passes the changed data as an argument to `update`.
The GoF chapter describes this as the subject broadcasting detailed change
information to observers whether they need it or not, and warns that it can make
observers less reusable because the subject makes assumptions about what
observers want (UNC reproduction, Implementation section, verified 2026-08-02).
Push removes the back reference, which removes the reference cycle, which makes
the leak in dimension 11 easier to avoid. Push also makes the payload immutable
and self contained, which is what allows the notification to cross a thread or a
queue. The cost is that every change to the payload shape is a breaking change to
every observer, and observers that need one field receive all of them.

**Pull model.** The subject sends the minimal notification and observers query for
the details, which the same GoF passage describes as the opposite extreme, with
the tradeoff that the notification mechanism may become inefficient without
guidance from the subject (same source, verified 2026-08-02). Pull keeps the
subject ignorant of what observers want, which is the maximal decoupling position.
The cost is that the observer needs the back reference, the read happens after the
change so the observer can read a newer state than the one announced, and a change
that has already been reverted is indistinguishable from no change at all.

**Hybrid, and the one to prefer.** Pass an immutable event object carrying the
old value, the new value and the property identity, and do not pass the subject.
`PropertyChangeEvent` is exactly this shape, and it is what allows
`PropertyChangeSupport` to skip the notification when old equals new (Oracle
javadoc, verified 2026-08-02). It gives push's thread safety and pull's
selectivity, since an observer can ignore an event for a property it does not
watch. The cost is one allocation per notification, which matters only in the
highest frequency paths.

**Registration handle instead of a detach method.** Return a value from attach
whose disposal detaches, rather than requiring the caller to pass the same
observer instance back. This removes an entire bug class, because the caller no
longer has to keep the original function reference, which the DOM documentation
names as the reason anonymous listeners in a loop can never be removed (MDN,
verified 2026-08-02). Handles compose, since a set of handles can be disposed
together. Every modern API named in dimension 9 uses this form.

**Weak references to observers.** The subject holds weak references, so an
observer whose only remaining referrer is the subject becomes collectable. The
Wikipedia treatment of the lapsed listener problem names weak references as the
remedy, allowing observers to be collected normally without being unregistered
([Lapsed listener problem](https://en.wikipedia.org/wiki/Lapsed_listener_problem),
verified 2026-08-02). The trade off is severe enough to be its own paragraph in
dimension 11. In short, a lambda registered inline has no other referrer and dies
immediately, giving a subscription that silently never fires.

**Lifetime scoped registration.** Bind the subscription to an owner object with a
known destruction point, and detach automatically when that owner is destroyed.
Android's `LiveData` is the reference implementation, documented as removing the
observer when the corresponding `Lifecycle` moves to `DESTROYED`, so activities
and fragments are unsubscribed instantly when their lifecycles are destroyed, and
stating no memory leaks as a listed advantage
([Android LiveData overview](https://developer.android.com/topic/libraries/architecture/livedata),
verified 2026-08-02). The web equivalent is the `AbortSignal` option on
`addEventListener`, where aborting the controller removes the listener (MDN,
verified 2026-08-02). This is the strongest answer to the leak, because it makes
correct behaviour the default rather than a discipline.

**Asynchronous or queued delivery.** The subject enqueues the event and a
dispatcher delivers it on another thread or a later turn. This isolates the write
path from slow and failing observers, which the synchronous form cannot do. It
costs ordering guarantees, adds a queue that can grow without bound, and moves
errors away from the code that caused them. Kubernetes documents both the benefit
and the constraint, telling clients to process each notification promptly because
the informer is not engineered to handle a large backlog, and directing lengthy
processing to a work queue instead (client-go source, verified 2026-08-02).

**Function values instead of an observer interface.** In every language with
first class functions, the observer is a closure and the interface disappears.
This is the idiomatic form in JavaScript, Python, Go, Kotlin, Swift and Rust. It
removes a type per observer and makes the registration site read as a statement
of intent. It costs the ability to compare two registrations for identity, which
is why an API in this style must return a handle rather than expecting the
function back.

**Typed event bus over a single subject.** One dispatcher keyed by event type,
rather than one subject per source. Reduces boilerplate at the cost of turning
every subscription into a runtime lookup, which is where compile time checking of
the payload type is usually lost.

**Reactive streams.** The descendant that adds completion, error and demand to
the observer contract. The Reactive Streams specification states its purpose as
asynchronous stream processing with non blocking back pressure, and describes
back pressure as integral so that the queues mediating between threads can be
bounded ([reactive-streams.org](https://www.reactive-streams.org/), verified
2026-08-02). The .NET analogue predates it and defines three notification kinds
rather than one, where the provider calls `OnNext` with data, `OnError` with a
failure and `OnCompleted` when it will send nothing more (Microsoft
`IObservable<T>` documentation, verified 2026-08-02). Java folded the Reactive
Streams interfaces into the platform as `java.util.concurrent.Flow`, and the
Reactive Streams site records that the JDK 9 Flow interfaces are one to one
semantically equivalent to the Reactive Streams counterparts (reactive-streams.org,
verified 2026-08-02). The Java 9 deprecation notice for `Observable` points
readers at that `Flow` API for reactive streams style programming, at
`java.beans` for a richer event model, and at `java.util.concurrent` for reliable
ordered messaging between threads (Oracle javadoc, verified 2026-08-02).

**Signals, the pull based descendant.** A signal graph inverts the flow. Rather
than the subject pushing to every dependent, dependents record what they read and
recompute lazily on demand. The TC39 Signals proposal describes computed signals
as automatically finding the signals they depend on, and explains that being
pull based rather than push based avoids wasted work in both computation and DOM
writes (TC39 proposal-signals, verified 2026-08-02). That property is the answer
to the diamond problem named in dimension 4. The proposal is at Stage 1 as of the
text published in its repository, so it is a direction rather than a settled
platform feature, and this entry states that rather than implying otherwise.

## 9. Known production uses

**Node.js `EventEmitter`.** The core notification mechanism of the Node platform,
providing `on`, `once` and `off`. The documentation records that listeners are
called synchronously in registration order, that `once` removes the listener
before invoking it, and that the emitter prints a warning above ten listeners on
one event because that default helps find memory leaks. It also documents that an
`error` event with no registered listener causes the process to exit
([Node.js Events API](https://nodejs.org/api/events.html), verified 2026-08-02).

**Java Beans bound properties, `java.beans.PropertyChangeSupport`.** The utility
that maintains the listener list and dispatches `PropertyChangeEvent`. It supports
listeners registered for all properties or for one named property, and it does not
fire when old and new values are equal and non null
([Oracle javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/beans/PropertyChangeSupport.html),
verified 2026-08-02). This is the mechanism Java's own `Observable` deprecation
recommends as the richer event model (Oracle `Observable` javadoc, verified
2026-08-02).

**.NET `IObservable<T>` and `IObserver<T>`.** The framework documentation names
the pair as a generalized mechanism for push based notification, also known as
the observer design pattern, with `IObservable<T>` as the provider and
`IObserver<T>` as the receiver. `Subscribe` returns an `IDisposable` that lets an
observer cancel notifications at any time before the provider stops sending them,
and the documentation states that the interface makes no assumptions about the
number of observers or the order in which notifications are sent
([Microsoft, System.IObservable&lt;T&gt;](https://learn.microsoft.com/en-us/dotnet/api/system.iobservable-1),
verified 2026-08-02). `System.Diagnostics.DiagnosticListener` is listed there as
a derived type, which puts the pattern inside .NET's own instrumentation surface.

**Kubernetes client-go informers.** The controller layer of Kubernetes is built on
`SharedInformer`. The interface declares
`AddEventHandler(handler ResourceEventHandler) (ResourceEventHandlerRegistration, error)`
and `RemoveEventHandler(handle ResourceEventHandlerRegistration) error`, with
handler callbacks `OnAdd`, `OnUpdate` and `OnDelete`. The source documents that
events to a single handler are delivered sequentially with no coordination
between different handlers, that removal is asynchronous and stops queueing new
events without waiting for queued ones, and that clients must process each
notification promptly because the informer is not built for a large backlog
([client-go shared_informer.go](https://raw.githubusercontent.com/kubernetes/client-go/master/tools/cache/shared_informer.go),
verified 2026-08-02).

**The DOM `EventTarget` interface.** Every browser event flows through
`addEventListener` and `removeEventListener`. The `once` option removes the
listener automatically after one invocation, and the `signal` option removes it
when the owning `AbortController` is aborted
([MDN, EventTarget.addEventListener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener),
verified 2026-08-02).

**Redux `store.subscribe`.** The state container's notification surface. It
returns a function that unsubscribes, snapshots the subscription list before
every dispatch, and documents that listeners may not observe every state change
during nested dispatches while guaranteeing they see the latest state by the time
dispatch exits ([Redux Store API](https://redux.js.org/api/store), verified
2026-08-02).

**Android `LiveData`.** An observable data holder that is lifecycle aware,
notifying only observers whose lifecycle is `STARTED` or `RESUMED`, and removing
observers automatically when the associated `Lifecycle` reaches `DESTROYED`
([Android LiveData overview](https://developer.android.com/topic/libraries/architecture/livedata),
verified 2026-08-02).

**Kotlin `StateFlow`.** A hot flow whose active instance exists independently of
collectors, which always holds a value, never completes, and conflates updates by
`Any.equals` so that a value equal to the previously emitted one is not delivered
([Kotlin StateFlow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/),
verified 2026-08-02).

## 10. Consequences

Positive.

- The subject depends on nothing the observers depend on. New reactors are added
  by writing a new observer and one registration line, with no edit to the state
  holder. This is the Open Closed Principle applied to notification.
- Broadcast is free at the subject. One `notify` reaches one observer or fifty
  with identical code, and the subject's correctness does not depend on the count.
- Subscription is a runtime decision, so a feature can be switched on for one
  tenant, one environment or one request scope by controlling registration rather
  than by branching in the subject.
- Latency collapses from half a poll interval to one dispatch, and idle cost
  collapses to zero, since nothing runs when nothing changes.
- The observer interface is a versionable extension point a library can publish,
  which lets external teams extend a framework they cannot modify.
- Testing the subject in isolation becomes straightforward, since one recording
  observer stands in for every real collaborator.

Negative.

- Control flow is no longer readable from the source. The set of things that run
  on a state change is runtime data, and reconstructing it requires either a
  debugger, a registration log, or a search across repositories.
- The write path's latency is the sum of all observer bodies in the synchronous
  form, so any observer can degrade a path it does not own.
- One throwing observer stops the rest and can propagate into the subject unless
  the implementation isolates errors, which the classical form does not.
- Memory is retained for the lifetime of the subject unless deregistration is
  correct, which is the failure covered at length in dimension 11.
- Notification ordering is unspecified in the classical pattern, so any code that
  depends on it is depending on an implementation accident. Java's own deprecation
  text names this as one of the reasons the API was withdrawn (Oracle javadoc,
  verified 2026-08-02).
- Notifications and state changes are not in one to one correspondence, which is
  the second reason given in that same deprecation text. A runaway update chain
  produces more notifications than changes, and equality suppression produces
  fewer.
- Reentrancy is not addressed at all by the pattern as described, and every
  production implementation had to define semantics the pattern left open.

## 11. Failure modes and misuse

### The lapsed listener leak

This is the most common real bug in the pattern and deserves the full treatment.

**Symptom.** Heap grows monotonically across the life of the process. A heap dump
shows thousands of retained instances of a type that should be short lived, a
screen controller, a request scoped service, a closed dialog, a disposed
component. Every one of them is retained through the same path, an array or list
field on a long lived object. In a UI the visible form is a screen that was closed
minutes ago still reacting to data, updating a view that is no longer displayed,
and in the worst case throwing because the view it targets has already been torn
down. In a server the visible form is a work queue whose consumer count climbs
with uptime, or a metric emitted once per request early in the day and forty
times per request by evening. Node makes this observable directly, printing a
possible `EventEmitter` memory leak warning when more than ten listeners are
added to one event, a default the documentation says exists to help find memory
leaks (Node.js Events API, verified 2026-08-02).

**Cause.** The subject holds a strong reference to every registered observer, and
the subject outlives the observer's useful life. Because the reference runs from
the long lived object to the short lived one, the garbage collector correctly
concludes the observer is reachable and keeps it, along with everything the
observer itself holds, which in a UI is usually the entire view hierarchy. The
Wikipedia article on the problem states the mechanism plainly, that the subject
holds strong references to the observers keeping them alive, that this persists
for as long as the subject is alive which may be until the end of the
application, and that the cost is not only memory but an uninterested observer
receiving and acting on unwanted events (Lapsed listener problem, verified
2026-08-02). Three sub causes account for nearly every instance. The observer's
owner has no teardown hook and nobody noticed. The teardown hook exists but is not
called on the exception path. Or the registration used an inline anonymous
function, so no reference to it survives and removal is impossible, which MDN
names directly, noting that in the anonymous case it is not possible to call
`removeEventListener` because no reference to the anonymous function is kept
(MDN, verified 2026-08-02).

**Fix, in the order to try them.**

1. **Return a handle from attach and dispose it in the owner's teardown.** This is
   the baseline. It removes the need to keep the observer reference and lets a
   set of subscriptions be disposed together.
2. **Bind the subscription to a lifetime owner so removal is automatic.** Android's
   `LiveData` removes the observer when the lifecycle reaches `DESTROYED`, and the
   documentation lists no memory leaks as a resulting advantage (Android LiveData,
   verified 2026-08-02). The browser equivalent is one `AbortController` per
   component whose `signal` is passed to every `addEventListener` call, aborted
   once on teardown (MDN, verified 2026-08-02). This is the strongest fix because
   it makes the correct behaviour the default rather than a rule people must
   remember.
3. **Use the automatic one shot form when the subscription is genuinely one shot.**
   Node's `once` removes the listener before invoking it, and the DOM `once`
   option does the same (Node.js Events API and MDN, both verified 2026-08-02).
4. **Hold observers weakly.** See the trade off below before choosing this.
5. **Alarm on the count.** Node's ten listener warning is a template worth
   copying. A registration gauge with an alert on monotonic growth converts a slow
   leak into a page before it becomes an outage, see dimension 16.

**The weak reference remedy and its own trade off.** Holding observers weakly
solves the leak by removing the retention, and it introduces a failure that is
harder to diagnose than the leak was. A weakly held observer is collected as soon
as nothing else refers to it, and in the overwhelmingly common registration style
nothing else does. A closure passed inline to `subscribe` has exactly one referrer,
the subject, and if that reference is weak the closure is eligible for collection
the moment the statement completes. The subscription then works during
development, works under a debugger, works while the heap is small, and stops
working in production the first time a collection runs between registration and
the event. The symptom is a handler that fires reliably and then silently never
fires again, with no error, no log line and no leak. It is the worst class of bug
the pattern produces, and it is created by the fix for the second worst.

A weak registry is therefore acceptable only when three conditions hold together.
The observer is a long lived object with an independent owner, never a closure.
The API documents that the caller must retain the observer, so the retention
requirement is part of the contract rather than a surprise. And the subject
prunes cleared references on every notification, so the collection does not itself
grow without bound with dead slots. When any of those is unmet, the lifetime
scoped approach in fix two is the better answer, because it deletes the
subscription at a defined moment rather than at a moment the collector chooses.
Weak references are the right remedy for the leak and the wrong default for a
subscription API.

### Other failure modes

**Notification storm from a runaway update chain.** Symptom. A single user action
produces thousands of log lines, a CPU spike, and in the worst case a stack
overflow with the same three frames repeating. Cause. Observer A changes the
subject in response to a change, and the subject notifies on every change, so the
graph has a cycle. The GoF chapter names this hazard, describing a harmless
looking operation causing a chain of updates across observers and their dependents
(UNC reproduction, verified 2026-08-02). Fix. Suppress notification when the value
is unchanged, following `PropertyChangeSupport` which does not fire when old
equals new and is non null (Oracle javadoc, verified 2026-08-02), and add a
reentrancy depth counter that logs and refuses beyond a small bound so a genuine
cycle fails loudly rather than overflowing the stack.

**Concurrent modification during notification.** Symptom. An intermittent
`ConcurrentModificationException`, or in a native language a crash inside the
notify loop, that reproduces only when a particular observer is registered.
Cause. An observer attached or detached during `notify`, mutating the collection
being iterated. Fix. Snapshot the collection before iterating, which is the
documented Redux behaviour where subscriptions are snapshotted before every
dispatch and changes during invocation have no effect on the dispatch in progress
(Redux Store API, verified 2026-08-02). A copy on write list gives the same
property with no per notification allocation on a read heavy workload.

**One observer takes down the notification.** Symptom. Several downstream effects
stop happening at once, always the same ones, and the log shows a single stack
trace from an unrelated component. Cause. An unhandled exception from one observer
aborts the loop, so every observer after it in the iteration order is skipped, and
the exception surfaces at the subject's caller which has no idea what it means.
Fix. Wrap each observer call, log the failure with the observer's identity, and
continue. Then decide deliberately whether the subject should be told that a
notification partially failed, and if the answer is yes, say so in the contract
rather than by exception.

**Silent no op because nothing was registered.** Symptom. A feature works in
development and does nothing in one environment, with no error anywhere. Cause.
The registration line lives in wiring code that differs per environment, or in a
module that is not loaded, so `notify` iterates an empty collection successfully.
Fix. Log the observer count at the first notification, assert a minimum count at
startup for subscriptions that are mandatory, and treat an empty registry on a
mandatory event as a health check failure rather than a normal state.

**Missed events between construction and registration.** Symptom. An observer
never sees the first value, so a view starts blank until the second change, or an
audit trail is missing its first record. Cause. The subject changed state in the
window between being created and the observer attaching, and the pattern has no
replay. Fix. Deliver the current value on attach, which is what `StateFlow` does
by always having a value that a new subscriber receives (Kotlin StateFlow,
verified 2026-08-02), or make the observable state readable so the observer can
read once at attach time and then react to changes.

**Event object mutated by an observer.** Symptom. Observer one behaves correctly
and observer three receives a payload with fields it did not expect, in an order
dependent way that changes when registration order changes. Cause. A mutable
payload shared across the notification loop. Fix. Make the payload immutable. This
is one of the properties a messaging Publish Subscribe Channel gets for free by
delivering a copy of the message to each subscriber
([Enterprise Integration Patterns, Publish-Subscribe Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PublishSubscribeChannel.html),
verified 2026-08-02), and one that in process Observer must supply deliberately.

**Observer used where a return value is wanted.** Symptom. An `update` method
whose signature grew a boolean return, or an out parameter, or a mutable result
holder passed in the event. Cause. The design needs an answer from the reactors,
which Observer cannot express. Fix. Recognise it as a different pattern. Chain of
Responsibility when one handler should claim the request, a Strategy when one
policy should decide, a direct call when the subject genuinely depends on the
result.

**Unhandled error event terminating the process.** Symptom. A Node service exits
with a stack trace and no orderly shutdown. Cause. An `error` event emitted with
no listener registered for it, which the Node documentation states causes the
error to be thrown, a stack trace to be printed and the process to exit (Node.js
Events API, verified 2026-08-02). Fix. Register an error listener on every emitter
at construction, and treat a missing one as a lint failure.

## 12. Trade-off matrix

Compared against named alternatives across the forces from dimension 3. Ordering,
durability and back pressure rows are drawn from the sourced statements in
dimensions 8 and 9.

| Force | Observer, synchronous | Mediator | Publish-Subscribe Channel (Hohpe and Woolf) | Reactive Streams / Flow | Signals (TC39 proposal) | Polling loop | Direct call |
|---|---|---|---|---|---|---|---|
| Coupling, subject to reactor | None. Interface only | Both know the mediator | None. Broker in between | None. Interface only | None. Read tracked | None. Reader knows subject | Total |
| Latency of reaction | One dispatch | One dispatch plus routing | Network plus broker | One dispatch, demand gated | Deferred to next read | Half the poll interval | Immediate |
| Idle cost | Zero | Zero | Broker keeps running | Zero | Zero | Continuous | Zero |
| Ordering across reactors | Unspecified by the pattern | Mediator defines it | Per channel, per broker | Per publisher, sequential | Topological by dependency | Reader controls | Source order |
| Delivery on crash | Lost | Lost | Survives, broker persists | Lost in process | Lost | Reader retries on restart | Not applicable |
| Back pressure | None. Subject blocks | None | Broker queue plus policy | Built in and non blocking | Pull, so built in | Reader sets the rate | Not applicable |
| Glitch on a diamond graph | Yes. Double notify | Mediator can order | Yes | Yes without operators | No. That is the design goal | No. Reads once | No |
| Reactor lifetime management | Caller's problem, leaks | Mediator owns it | Broker owns subscription | Subscription handle | Watcher scope | None needed | None needed |
| Cognitive load | Medium. Flow is implicit | High. One large hub | High. Two systems | High. Operator vocabulary | Medium. Graph is implicit | Low | Lowest |
| Failure isolation | None by default | Mediator can isolate | Full. Separate processes | Per subscriber `onError` | Per computation | Full | None |
| Cross process reach | No | No | Yes. That is its purpose | With a transport | No | Yes | No |
| Operability | Poor. Registry invisible | Fair. One place to inspect | Good. Broker has metrics | Fair | Poor | Good. Loop is visible | Good |

Reading of the table. Observer wins when the reactors are in process, the reaction
is fire and forget, and the reactor set varies. Mediator wins the moment
interaction between the reactors must be sequenced or arbitrated, since that is
exactly the thing Observer refuses to express. A Publish Subscribe Channel wins
when the reaction must survive a process restart or cross a network, because it
delivers a copy of each event to every subscriber through a broker rather than
through a language level call (Enterprise Integration Patterns, verified
2026-08-02). Reactive Streams wins when the producer can outpace the consumer,
because non blocking back pressure is the thing it was specified to provide
(reactive-streams.org, verified 2026-08-02). Signals win on a dependency graph
where derived values must never be computed from an inconsistent intermediate
state, which the pull based design targets directly (TC39 proposal-signals,
verified 2026-08-02). Polling wins when the source cannot be modified to notify.
A direct call wins whenever the reactor set is fixed, which is more often than
event driven codebases admit.

## 13. Related and incompatible patterns

- **Observer versus Publish-Subscribe.** These are routinely conflated, partly
  because the GoF book itself carries Publish-Subscribe as an alias for Observer
  (UNC reproduction, verified 2026-08-02). They are different in every property
  that matters operationally. The table below resolves it.

| Property | Observer (GoF) | Publish-Subscribe Channel (messaging) |
|---|---|---|
| Coupling | Subject holds a direct reference to each observer | Publisher knows a channel, never a subscriber |
| Delivery | Synchronous method call by default | Asynchronous through a broker |
| Process boundary | Same process, same address space | Designed to cross processes and hosts |
| Payload | Shared object reference unless copied deliberately | A copy delivered to each subscriber |
| Registration | Observer registers with the subject | Subscriber registers with the channel |
| Durability | None. Lost when the process dies | Broker dependent, commonly durable |
| Back pressure | None. Subject blocks on observers | Queue depth plus a broker policy |
| Failure of one receiver | Can abort the notification | Isolated to that subscriber |
| Observability | Registry is in process memory | Broker exposes topics, lag and depth |

  The practical rule. If removing the network and the broker leaves the design
  working, it is Observer. If the design needs a component that both sides talk
  to and neither owns, it is Publish Subscribe. The messaging definition delivers
  a copy of a particular event to each receiver through one input channel that
  splits into an output channel per subscriber (Enterprise Integration Patterns,
  verified 2026-08-02), which is a topology Observer does not have.

- **Mediator.** The closest neighbour and the usual successor. Observer keeps the
  subject ignorant of the observers. Mediator makes one object knowledgeable about
  everyone so it can sequence and arbitrate. The GoF Observer chapter itself
  sketches the transition, describing a ChangeManager that maps subjects to
  observers, defines an update strategy and updates all dependents at a subject's
  request (UNC reproduction, verified 2026-08-02). That is a Mediator. When
  ordering, deduplication or transactional grouping of notifications is needed,
  the answer is to promote the ChangeManager, not to add rules to the observers.

- **Command.** Composes cleanly and is the most useful pairing in practice. Rather
  than calling `update` directly, the subject enqueues a command carrying the
  event and the target. This gives asynchronous delivery, retry, ordering by queue
  discipline, and the ability to record what was dispatched. Kubernetes directs
  users toward exactly this shape, telling handlers to pass lengthy processing off
  to a work queue rather than doing it in the callback (client-go source, verified
  2026-08-02).

- **Memento.** Composes when observers need the before value. Passing an immutable
  snapshot of the prior state alongside the new one is the hybrid push model of
  dimension 8, and `PropertyChangeEvent` with its old and new value pair is the
  canonical example (Oracle javadoc, verified 2026-08-02).

- **Strategy.** Frequently confused because both put a function behind an
  interface. Strategy substitutes how a computation is done and the caller depends
  on the result. Observer notifies that something happened and the subject depends
  on nothing. A single observer that the subject cannot function without is a
  Strategy that has been mis-registered, and it should be a constructor
  dependency so its absence is a compile error rather than a silent no op.

- **Chain of Responsibility.** The alternative when exactly one reactor should
  handle the event and the rest should be skipped. Observer broadcasts to all and
  cannot stop. Any observer implementation that grew a boolean return meaning
  handled has become a chain, and rewriting it as one restores the ability to
  reason about which handler ran.

- **Singleton.** Conflicts in practice. A process wide singleton subject makes
  every test that registers an observer order dependent, because registrations
  leak between tests through the shared instance. If a global event bus is
  genuinely wanted, give it an explicit reset for tests and inject it rather than
  reaching for it statically.

- **Model View Controller and Model View ViewModel.** Both are built on Observer.
  MVC is where the pattern was first widely used, with the Model as Subject and
  the Views as Observers (UNC reproduction, Known Uses, verified 2026-08-02). MVVM
  formalises the same relationship as data binding, and Android's `LiveData` is a
  lifetime safe version of that binding (Android LiveData, verified 2026-08-02).

- **Reactive Streams and signals.** Descendants rather than alternatives. Reactive
  Streams keeps the push direction and adds completion, error and demand
  (reactive-streams.org, verified 2026-08-02). Signals invert to a pull direction
  and add automatic dependency tracking (TC39 proposal-signals, verified
  2026-08-02). Reach for the first when a producer can outrun a consumer, and for
  the second when derived values form a graph.

## 14. Refactoring path in and out

### Introducing Observer into code that does not have it

The starting point is a method that changes state and then performs several
unrelated side effects inline.

1. **Name the event, not the reaction.** Write down the fact that occurred in the
   subject's own vocabulary. `OrderPaid`, not `SendReceiptEmail`. If the name that
   comes out is a verb phrase describing what a reactor should do, the reactor is
   not independent and the pattern will not decouple anything.
2. **Extract each side effect into its own class or function** with a single
   method taking the event. Do not change the call site yet. Run the tests. This is
   Extract Class applied per effect, and it is where most of the real work is,
   because side effects written inline usually read local variables that must
   become part of the event.
3. **Define the event payload as an immutable value** holding the old value, the
   new value and the identity of what changed. Resist passing the subject, so the
   observers cannot pull and cannot therefore read a state newer than the one
   announced.
4. **Add the registry and the notify loop to the subject.** Snapshot before
   iterating from the first version, so reentrancy cannot produce a concurrent
   modification later. Have attach return a handle. Both decisions are far cheaper
   now than after the API has callers.
5. **Move one effect at a time from the inline call to a registration.** After each
   move, run the tests. The suite should stay green because the registration in
   the wiring code replaces the inline call one for one. Any test that breaks is
   telling you that effect was not independent, which is information worth having
   before the rest of the move.
6. **Add the suppression rule.** Do not notify when the new value equals the old,
   following the `PropertyChangeSupport` contract (Oracle javadoc, verified
   2026-08-02). This is cheap now and removes an entire class of runaway update
   bug.
7. **Attach a lifetime to every subscription.** Every registration site gets an
   owner whose teardown disposes the handle. If a site has no obvious owner, that
   is the leak from dimension 11 arriving on schedule, and it is far cheaper to
   resolve at this step.
8. **Add the observability from dimension 16 before the second observer ships.**
   A registration gauge and a per observer duration histogram cost an hour now and
   save the first production investigation entirely.

The step teams skip is the eighth, and the step teams get wrong is the seventh.

### Removing Observer when it stops earning its place

Signals that it should go include a registry that has held exactly one observer
for a year, a set of observers that must run in a fixed order enforced only by
comment, or an event that no longer has a reader.

1. **Log the registrations in production for a week.** Not in staging. The whole
   point of the pattern is that the set is runtime data, so the only trustworthy
   inventory is a measured one.
2. **If exactly one observer is ever registered, and it is registered on every
   path,** replace the subscription with a constructor dependency on the
   reactor's interface. The subject now names a collaborator, which is honest,
   and its absence becomes a compile error rather than a silent no op.
3. **If several observers exist but must run in a defined order,** promote the
   registry into a Mediator that owns the sequence explicitly. This is Replace
   Implicit Ordering with an Explicit Pipeline, and it usually reduces the code
   because the retry and error handling that was duplicated across observers moves
   into one place.
4. **If the observers are all remote or all durable,** replace the in process
   registry with a Publish Subscribe Channel and delete the registry. The
   subscriber list moves to the broker, which is where operations can see it.
5. **Delete the observer interface last**, once no implementation remains. Leaving
   it in place invites a new subscriber and reverses the whole change.

Do not remove the pattern because the registry is empty in one environment. That
is the silent no op failure from dimension 11 wearing a disguise, and deleting the
event will make the missing behaviour permanent.

## 15. Testing and verification

This dimension is practice rather than sourced fact, except where a named library
behaviour is cited.

Easier because of the pattern.

- The subject can be tested with one recording observer standing in for every real
  collaborator, with no mocking framework, no network and no database. Assertions
  become questions about the recorded event list.
- Each observer is testable in complete isolation by calling its update method with
  a constructed event. No subject is needed, which makes the reactor tests fast and
  independent of the state machine that produces the events.
- Event payloads are values, so property based testing applies directly. Generate
  event sequences and assert an invariant about the observer's resulting state.

Harder because of the pattern.

- The wiring is untested by both of the above. A green subject suite and a green
  observer suite prove nothing about whether the observer is registered in
  production, which is the silent no op failure. This gap needs its own test.
- Reentrancy and ordering bugs do not appear in unit tests, because a single test
  registers one well behaved observer. They appear when two observers interact.
- Assertions about something *not* happening after deregistration require a
  negative test, which is the only test that catches a broken detach.

Techniques that apply.

- **Recording observer, sometimes called a spy.** A handwritten observer that
  appends every received event to a list. Preferred over a mocking framework
  because the assertion reads as a comparison of two event lists, which is far
  clearer than a sequence of verify calls, and because it catches a duplicate
  delivery that a lenient mock would pass.
- **Wiring test.** One test per environment configuration that builds the object
  graph the way production builds it, fires a change, and asserts the observer
  count and the resulting effect. This is the only test that catches the missing
  registration, and it is the one most suites omit.
- **Detach test.** Register, fire, assert one delivery, detach, fire again, assert
  still one delivery. Cheap, and it is the only thing that catches a detach that
  compares by identity against a value that no longer matches.
- **Leak test.** Register an observer, drop every strong reference to it, force a
  collection, and assert it is gone if the design intends weak retention, or
  assert the registry shrank after an explicit dispose if it intends handles. In
  Java this uses a `WeakReference` plus `System.gc` and is best effort by nature.
  In Python `weakref` plus `gc.collect` is deterministic enough for the reference
  counting case.
- **Reentrancy test.** Register an observer that writes to the subject inside its
  own update. Assert the process does not overflow, that the collection was not
  concurrently modified, and that the final state is the one you specified. Then
  write down which of Redux's two guarantees you are offering, since the choice
  between seeing every transition and seeing the latest state is a contract
  decision, not an implementation detail (Redux Store API, verified 2026-08-02).
- **Error isolation test.** Register three observers, make the middle one throw,
  assert the third still ran and that the subject's caller saw no exception. This
  is the test that turns a policy decision into a checked one.
- **Ordering test, only if you promise ordering.** If the implementation guarantees
  registration order, as Node's `EventEmitter` documents (Node.js Events API,
  verified 2026-08-02), test it. If it does not, write a test that asserts the set
  of deliveries rather than the sequence, so nobody comes to depend on an accident.

## 16. Observability signals

This dimension is practice. The pattern hides the subscriber set from the source,
so telemetry is the only way anyone learns what actually ran.

What to record.

- **A gauge of registered observers, labelled by event type and observer type.**
  This is the single most valuable signal, because the leak and the silent no op
  are both invisible everywhere else. Node's built in warning above ten listeners
  is the same idea implemented as a default, and its documentation states the
  purpose is to help find memory leaks (Node.js Events API, verified 2026-08-02).
  An explicit gauge is better because it is queryable and alertable.
- **A counter of notifications delivered, labelled by event type and observer
  type.** The ratio between this and the count of state changes tells you
  immediately whether update chains are running away, since a healthy ratio equals
  the observer count and a runaway one exceeds it.
- **A histogram of observer execution duration, labelled by observer type.** In the
  synchronous form this decomposes the write path's latency by reactor, which is
  the only way to attribute a slow write to the observer that caused it.
- **A counter of observer failures, labelled by observer type and error class.**
  Without this the isolation wrapper swallows failures silently, which trades one
  invisible problem for another.
- **A counter of attach and detach operations.** Attaches minus detaches should
  track the gauge. A gap between the two means a detach path is being skipped.
- **A reentrancy depth gauge or a maximum depth counter.** Healthy is one. Anything
  above one deserves a log line naming the observer that reentered.
- **Queue depth and delivery lag, for the asynchronous variant.** These are the
  back pressure signals, and their absence is why the synchronous form is easier
  to operate despite being worse in every other respect.
- **A trace span per observer invocation, as a child of the span that caused the
  change.** This is what restores the causal chain the pattern severed. Without it
  a distributed trace ends at the subject and the reactions appear as unrelated
  root spans.

A healthy instance on a dashboard. The registration gauge is flat, or moves in
steps that match deployments and tenant onboarding rather than drifting upward
between them. Notifications per state change equals the observer count. Observer
duration is flat and well under the write path's budget. Failures are zero or a
constant low rate with a known cause. Reentrancy depth is one. In the asynchronous
form, queue depth returns to zero between bursts.

A failing instance. The registration gauge climbs monotonically with uptime and
resets only on restart, which is the lapsed listener leak and nothing else. Or the
gauge is zero for an event the system depends on, which is the silent no op, and
it will not be reported by any user because nothing errors. Or notifications per
change jumps to a multiple of the observer count, which is a runaway update chain,
and it will usually coincide with a CPU step change. Or one observer's duration
histogram grows a long tail while the others stay flat, which localises the slow
reactor without reading any code. Or attaches exceed detaches by a growing margin,
which names the leaking call site directly if the counters carry a site label. Or,
in the asynchronous form, queue depth grows without returning to zero, which means
the consumer has fallen permanently behind and the memory growth is now in the
queue rather than in the registry.

## 17. Security and privacy implications

This dimension is analytical rather than sourced, except where a documented
behaviour is cited. In a closed design where every observer ships in the same
build as the subject, the pattern is close to silent on security, and claiming
otherwise would be inventing a concern. Once registration is open to code the
subject's author did not write, four genuine implications appear.

**Untrusted subscribers become an information disclosure channel.** Registration
is usually unauthenticated, because the pattern has no notion of a caller
identity. Any code that can reach the subject can attach and will then receive
every event the subject emits, including events carrying data that code has no
business seeing. In a plugin architecture this is the whole attack. A plugin
registers for a change event, and the payload contains the customer record that
changed. The mitigation is to treat the event payload as a published API with its
own data classification, to project it down to the fields subscribers actually
need rather than passing the domain object, and to authorise registration where
the runtime allows it.

**Observers run inside the subject's privileges.** In the synchronous form the
observer executes on the subject's thread, in the subject's transaction, with the
subject's credentials and inside its exception boundary. An observer that throws
can abort the subject's work, an observer that blocks can hold the subject's
monitor, and an observer that calls back into the subject can drive it into a
state the subject's own invariants did not anticipate. Where the observer set is
not fully trusted, delivery should be moved off the subject's thread and out of
its transaction, which is the queued variant, and each observer should be time
bounded.

**Denial of service through registration.** Nothing in the pattern bounds the
number of observers. An attacker who can trigger registration in a loop makes
every subsequent notification O(n) with an n they control, turning a cheap write
into an arbitrarily expensive one, and consuming memory proportional to n at the
same time. This is the same shape as the leak but adversarial and fast. Bound the
registry size, reject registration past the bound with an error rather than
silently, and alert on the bound being approached. Node's ten listener warning is a
usable default of exactly this kind (Node.js Events API, verified 2026-08-02).

**Ordering as a security boundary is unsound.** A design that registers an
authorisation observer first and a data access observer second, relying on the
first to reject, is depending on an ordering the pattern does not promise. Java's
deprecation text states that the order of notifications delivered by `Observable`
is unspecified (Oracle javadoc, verified 2026-08-02), and Kubernetes documents that
there is no coordination between different handlers (client-go source, verified
2026-08-02). Authorisation belongs before the notification, inside the subject,
where the check cannot be reordered or unregistered.

On privacy the pattern is neutral in itself, with two practical caveats. The event
payload frequently carries more than the reactors need, because it was shaped from
the domain object rather than from the consumers' requirements, and every
subscriber then holds personal data it never asked for. Project the payload
deliberately. And the observability advice in dimension 16 recommends labelling
metrics by observer type and logging the registration site. Where an observer type
name encodes a tenant, a region or a data residency tier, that label is
attributable data and needs the same retention and access controls as any other
identifier.

## Code examples

Four languages, chosen because each shows a different part of the pattern. Java
shows the classical interface form with a registration handle, snapshot iteration
and error isolation. TypeScript shows the closure form plus the `AbortSignal`
lifetime binding that answers the leak. Python shows the weak reference variant
and the trade off it carries. Go shows the handle based registration that
Kubernetes uses, since Go has no inheritance and no exceptions and therefore
reshapes the pattern most.

C# and Kotlin are omitted from the samples because the platform already ships the
pattern as a first class contract, `IObservable<T>` and `StateFlow` respectively,
and a handwritten version in either language would be a demonstration of ignoring
the standard library rather than of the pattern.

Toolchain status, stated plainly. The Python sample was run with `python3`, the Go
sample with `go run`, and the TypeScript samples were type checked with
`tsc --strict` and then executed under `node`. All three produce the output the
surrounding prose claims. The Java sample was NOT compiled, because this machine
has `javac` on the path as a stub with no Java runtime behind it, so no build was
possible. It has been hand checked against the language rules it relies on, the
record declaration, the void compatible lambda returned as an `AutoCloseable`, and
the checked exception from `close` declared on `main`. Treat it as reviewed rather
than as verified.

### Java

Classical form. The handle, the snapshot and the per observer isolation are all
present, because all three are needed and none is in the textbook version. The
snapshot is not hand rolled. `CopyOnWriteArrayList` documents that its iterator
holds a reference to the array as it stood when the iterator was created, that
this array never changes for the iterator's lifetime, and that it is guaranteed
not to throw `ConcurrentModificationException`
([Oracle javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html),
verified 2026-08-02).

```java
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.Objects;

record PriceChanged(String symbol, long oldCents, long newCents) {}

interface PriceObserver {
    void onPriceChanged(PriceChanged event);
}

final class Ticker {
    private final List<PriceObserver> observers = new CopyOnWriteArrayList<>();
    private final String symbol;
    private long cents;

    Ticker(String symbol, long cents) {
        this.symbol = symbol;
        this.cents = cents;
    }

    // Returns the only thing that can detach. Callers keep no observer reference.
    AutoCloseable attach(PriceObserver o) {
        observers.add(Objects.requireNonNull(o));
        return () -> observers.remove(o);
    }

    void setPrice(long newCents) {
        if (newCents == cents) {
            return;
        }
        PriceChanged event = new PriceChanged(symbol, cents, newCents);
        cents = newCents;
        publish(event);
    }

    private void publish(PriceChanged event) {
        // CopyOnWriteArrayList iterates a snapshot, so attach or detach
        // inside an observer cannot corrupt this loop.
        for (PriceObserver o : observers) {
            try {
                o.onPriceChanged(event);
            } catch (RuntimeException failure) {
                System.err.println("observer failed " + o.getClass().getName()
                        + " " + failure);
            }
        }
    }

    int observerCount() {
        return observers.size();
    }
}

public final class Demo {
    public static void main(String[] args) throws Exception {
        Ticker ticker = new Ticker("ACME", 1000);
        AutoCloseable logSub = ticker.attach(
                e -> System.out.println("log " + e.oldCents() + " to " + e.newCents()));
        ticker.attach(e -> { throw new IllegalStateException("bad observer"); });
        AutoCloseable alertSub = ticker.attach(
                e -> System.out.println("alert at " + e.newCents()));

        ticker.setPrice(1100);
        ticker.setPrice(1100);
        logSub.close();
        alertSub.close();
        ticker.setPrice(1200);
        System.out.println("observers left " + ticker.observerCount());
    }
}
```

### TypeScript

Closure form with a handle, then the lifetime bound form that removes the leak by
construction.

```typescript
type PriceChanged = { symbol: string; oldCents: number; newCents: number };
type Unsubscribe = () => void;

class Ticker {
  protected observers = new Set<(e: PriceChanged) => void>();

  constructor(private readonly symbol: string, private cents: number) {}

  subscribe(fn: (e: PriceChanged) => void): Unsubscribe {
    this.observers.add(fn);
    return () => { this.observers.delete(fn); };
  }

  setPrice(newCents: number): void {
    if (newCents === this.cents) return;
    const event = { symbol: this.symbol, oldCents: this.cents, newCents };
    this.cents = newCents;
    // Snapshot first. An observer may subscribe or unsubscribe during delivery.
    for (const fn of [...this.observers]) {
      try { fn(event); } catch (err) { console.error("observer failed", err); }
    }
  }

  get observerCount(): number { return this.observers.size; }
}

const ticker = new Ticker("ACME", 1000);
const stopLog = ticker.subscribe((e) => console.log("log", e.oldCents, e.newCents));
ticker.setPrice(1100);
ticker.setPrice(1100);
stopLog();
ticker.setPrice(1200);
console.log("observers left", ticker.observerCount);
```

The lifetime bound variant. One controller owns every subscription a component
made, and one abort call detaches all of them.

```typescript
class ScopedTicker extends Ticker {
  subscribeUntil(signal: AbortSignal, fn: (e: PriceChanged) => void): void {
    const off = this.subscribe(fn);
    signal.addEventListener("abort", off, { once: true });
  }
}

const scoped = new ScopedTicker("ACME", 1000);
const controller = new AbortController();
scoped.subscribeUntil(controller.signal, (e) => console.log("scoped", e.newCents));
scoped.setPrice(1050);
controller.abort();
scoped.setPrice(1075);
console.log("observers left", scoped.observerCount);
```

### Python

The weak reference variant, with the trade off from dimension 11 made visible in
the output rather than described. The bound method registered from a live owner
survives. The lambda with no other referrer does not.

```python
import weakref
from dataclasses import dataclass


@dataclass(frozen=True)
class PriceChanged:
    symbol: str
    old_cents: int
    new_cents: int


class WeakTicker:
    def __init__(self, symbol: str, cents: int) -> None:
        self.symbol = symbol
        self._cents = cents
        self._observers: list[weakref.ref] = []

    def attach(self, fn) -> None:
        ref = weakref.WeakMethod(fn) if hasattr(fn, "__self__") else weakref.ref(fn)
        self._observers.append(ref)

    def set_price(self, new_cents: int) -> None:
        if new_cents == self._cents:
            return
        event = PriceChanged(self.symbol, self._cents, new_cents)
        self._cents = new_cents
        live = []
        for ref in self._observers:
            fn = ref()
            if fn is None:
                continue
            live.append(ref)
            try:
                fn(event)
            except Exception as failure:
                print("observer failed", failure)
        self._observers = live

    @property
    def observer_count(self) -> int:
        return len(self._observers)


class Recorder:
    def __init__(self, name: str) -> None:
        self.name = name

    def on_change(self, event: PriceChanged) -> None:
        print(self.name, event.old_cents, "to", event.new_cents)


if __name__ == "__main__":
    ticker = WeakTicker("ACME", 1000)
    kept = Recorder("kept")
    ticker.attach(kept.on_change)
    ticker.attach(lambda e: print("this never fires", e.new_cents))
    ticker.set_price(1100)
    print("observers left", ticker.observer_count)
    del kept
    ticker.set_price(1200)
    print("observers left", ticker.observer_count)
```

### Go

Handle based registration, following the shape Kubernetes uses. Go has no
inheritance and no exceptions, so the subject stores its registry in a `sync.Map`
and isolation is a deferred recover.

One guarantee is deliberately weaker here than in the Java and TypeScript
samples, and the difference is worth stating rather than glossing. `sync.Map.Range`
is documented as not necessarily corresponding to any consistent snapshot of the
map's contents, visiting no key more than once but reflecting a concurrent store
or delete of a key from any point during the call, while explicitly permitting the
callback itself to call any method on the map
([Go `sync` package documentation](https://pkg.go.dev/sync#Map.Range), verified
2026-08-02). Attaching or detaching inside an observer is therefore safe, and no
observer receives the event twice, but an observer attached during delivery may or
may not be reached by the pass already in progress. That is weaker than the true
snapshot `CopyOnWriteArrayList` and the spread copy provide, where a registration
made during delivery is guaranteed not to be seen until the next notification. A
Go subject that needs the stronger guarantee must copy the registry under a mutex
before iterating, and pay an allocation per notification for it.

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type PriceChanged struct {
	Symbol   string
	OldCents int64
	NewCents int64
}

type Registration uint64

type Ticker struct {
	symbol    string
	cents     atomic.Int64
	next      atomic.Uint64
	observers sync.Map
}

func NewTicker(symbol string, cents int64) *Ticker {
	t := &Ticker{symbol: symbol}
	t.cents.Store(cents)
	return t
}

func (t *Ticker) Attach(fn func(PriceChanged)) Registration {
	reg := Registration(t.next.Add(1))
	t.observers.Store(reg, fn)
	return reg
}

func (t *Ticker) Detach(reg Registration) {
	t.observers.Delete(reg)
}

func (t *Ticker) SetPrice(newCents int64) {
	old := t.cents.Swap(newCents)
	if old == newCents {
		return
	}
	event := PriceChanged{t.symbol, old, newCents}
	// Range lets the callback call any method on the map, so Attach or Detach
	// inside an observer is safe. It is not a consistent snapshot.
	t.observers.Range(func(_, value any) bool {
		deliver(value.(func(PriceChanged)), event)
		return true
	})
}

func deliver(fn func(PriceChanged), event PriceChanged) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("observer failed", r)
		}
	}()
	fn(event)
}

func (t *Ticker) ObserverCount() int {
	n := 0
	t.observers.Range(func(_, _ any) bool { n++; return true })
	return n
}

func main() {
	ticker := NewTicker("ACME", 1000)
	logReg := ticker.Attach(func(e PriceChanged) {
		fmt.Println("log", e.OldCents, "to", e.NewCents)
	})
	ticker.Attach(func(e PriceChanged) { panic("bad observer") })

	ticker.SetPrice(1100)
	ticker.SetPrice(1100)
	ticker.Detach(logReg)
	ticker.SetPrice(1200)
	fmt.Println("observers left", ticker.ObserverCount())
}
```

## 18. References

1. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design Patterns.
   Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
   ISBN 0-201-63361-2. Chapter 5, Behavioral Patterns, section Observer. Source of
   the intent, the Dependents and Publish-Subscribe aliases, the four
   participants, the applicability conditions, the push and pull model
   distinction, the ChangeManager option, the dangling reference issue, the
   runaway update consequence, and the Smalltalk MVC attribution. The chapter
   text was verified against the reproduction hosted by the University of North
   Carolina at Chapel Hill,
   https://www.cs.unc.edu/~stotts/GOF/hires/pat5g.htm verified 2026-08-02.
   Page numbers are not cited because the reproduction is unpaginated.
2. Oracle. *Java SE 21 API Specification*, `java.util.Observable`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Observable.html
   Verified 2026-08-02. Source of the Java 9 deprecation and its three stated
   reasons, the limited event model, the unspecified notification order, and state
   changes not being in one to one correspondence with notifications, together
   with the recommended replacements `java.beans`, `java.util.concurrent` and the
   `Flow` API.
3. Oracle. *Java SE 21 API Specification*, `java.beans.PropertyChangeSupport`.
   https://docs.oracle.com/en/java/javase/21/docs/api/java.desktop/java/beans/PropertyChangeSupport.html
   Verified 2026-08-02. Source of the bound property mechanism and the rule that
   no event is fired when old and new values are equal and non null.
4. Wikipedia contributors. "Lapsed listener problem".
   https://en.wikipedia.org/wiki/Lapsed_listener_problem
   Verified 2026-08-02. Source of the named problem, the strong reference
   mechanism, the observation that the cost includes an uninterested observer
   acting on unwanted events, and the weak reference remedy.
5. Wikipedia contributors. "Observer pattern".
   https://en.wikipedia.org/wiki/Observer_pattern
   Verified 2026-08-02. Used only to confirm that the deprecation and the lapsed
   listener association are the community's common reading, not as a source of
   explanation.
6. OpenJS Foundation. *Node.js documentation, Events*.
   https://nodejs.org/api/events.html
   Verified 2026-08-02. Source of the synchronous registration order guarantee,
   the `once` semantics, the ten listener memory leak warning, and the process
   exit on an unhandled `error` event.
7. Mozilla. *MDN Web Docs, EventTarget.addEventListener()*.
   https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener
   Verified 2026-08-02. Source of the `signal` and `once` options and of the
   statement that an anonymous listener cannot be removed because no reference is
   kept.
8. Microsoft. *.NET API documentation*, `System.IObservable<T>`.
   https://learn.microsoft.com/en-us/dotnet/api/system.iobservable-1
   Verified 2026-08-02. Source of the provider and observer roles, the
   `IDisposable` returned from `Subscribe`, the three notification kinds, and the
   statement that no assumption is made about observer count or notification
   order.
9. Redux maintainers. *Redux API Reference, Store*.
   https://redux.js.org/api/store
   Verified 2026-08-02. Source of the unsubscribe function return, the snapshot
   before every dispatch, and the two contract statements about not seeing every
   state change while seeing the latest state by the time dispatch exits.
10. Kubernetes authors. *client-go, tools/cache/shared_informer.go*.
    https://raw.githubusercontent.com/kubernetes/client-go/master/tools/cache/shared_informer.go
    Verified 2026-08-02. Source of the `AddEventHandler` and `RemoveEventHandler`
    signatures, the sequential per handler delivery with no cross handler
    coordination, the asynchronous removal semantics, and the guidance to move
    lengthy processing to a work queue.
11. Google. *Android Developers, LiveData overview*.
    https://developer.android.com/topic/libraries/architecture/livedata
    Verified 2026-08-02. Source of the lifecycle aware behaviour, the active state
    definition, the automatic removal at `DESTROYED`, and the stated absence of
    memory leaks.
12. JetBrains. *kotlinx.coroutines API reference, StateFlow*.
    https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/
    Verified 2026-08-02. Source of the hot flow definition, the always present
    value, the never completing contract, and the equality based conflation by
    `Any.equals`.
13. Reactive Streams initiative. *Reactive Streams*.
    https://www.reactive-streams.org/
    Verified 2026-08-02. Source of the stated purpose, asynchronous stream
    processing with non blocking back pressure, the bounded queue rationale, the
    version 1.0.4 status, and the one to one semantic equivalence with the JDK 9
    `java.util.concurrent.Flow` interfaces.
14. TC39. *Signals proposal, proposal-signals*.
    https://github.com/tc39/proposal-signals
    Verified 2026-08-02. Source of the State and Computed signal split, the
    automatic dependency tracking, the pull based rationale for avoiding wasted
    work, and the Stage 1 status.
15. The Go Authors. *Go standard library documentation*, `sync.Map.Range`.
    https://pkg.go.dev/sync#Map.Range
    Verified 2026-08-02. Source of the statement that `Range` does not
    necessarily correspond to any consistent snapshot of the map's contents, that
    no key is visited more than once, that a concurrent store or delete may be
    reflected from any point during the call, and that the callback may itself
    call any method on the map.
16. Oracle. *Java SE 21 API Specification*,
    `java.util.concurrent.CopyOnWriteArrayList`.
    https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html
    Verified 2026-08-02. Source of the snapshot style iterator, the array that
    never changes for the iterator's lifetime, and the guarantee that
    `ConcurrentModificationException` is not thrown.
17. The Qt Company. *Qt 6 documentation, Signals and Slots*.
    https://doc.qt.io/qt-6/signalsandslots.html
    Verified 2026-08-02. Source of the signal and slot definitions used in
    dimension 1 and of Qt's own framing of the mechanism as an alternative to the
    callback technique.
18. Gregor Hohpe and Bobby Woolf. *Enterprise Integration Patterns*,
    Publish-Subscribe Channel.
    https://www.enterpriseintegrationpatterns.com/patterns/messaging/PublishSubscribeChannel.html
    Verified 2026-08-02. Source of the messaging definition used in dimension 13,
    one input channel splitting into one output channel per subscriber, with a
    copy of the message delivered to each.
