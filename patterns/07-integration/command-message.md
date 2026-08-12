---
name: Command Message
slug: command-message
family: 07-integration
category: Integration
aliases: [Command Channel, RPC over Messaging]
first_described: "Hohpe, Woolf 2003, Enterprise Integration Patterns"
maturity: canonical
related: [point-to-point-channel, invalid-message-channel, guaranteed-delivery, dead-letter-channel, messaging-bridge, datatype-channel]
incompatible_with: []
verified: 2026-08-02
---

# Command Message

## 1. Name, aliases, and lineage

The canonical name is Command Message. Gregor Hohpe and Bobby Woolf catalogued it
in *Enterprise Integration Patterns. Designing, Building, and Deploying
Messaging Solutions* (Addison-Wesley, 2003), in the Message Construction
chapter, alongside its two siblings Document Message and Event Message. The
book's companion website states the pattern plainly on its own reference
page, that a Command Message is "simply a regular message that happens to
contain a command" (enterpriseintegrationpatterns.com, Command Message,
verified 2026-08-02,
https://www.enterpriseintegrationpatterns.com/patterns/messaging/CommandMessage.html).
The name is not contested inside the messaging literature, but the same idea
surfaces under other names in adjacent communities. In CQRS and Domain-Driven
Design writing the equivalent concept is usually just called a "command," an
imperative, addressed instruction object, and in RPC-over-messaging systems
such as JMS or AMQP request-reply setups it is sometimes called a Request
Message when paired with a Reply Message. In MassTransit and NServiceBus
documentation, both frameworks distinguish "commands" from "events" as
message types with different addressing and cardinality rules, and both use
the word command in the same sense Hohpe and Woolf intended, a message that
instructs a specific receiver to do a specific thing, as opposed to a
broadcast fact. The underlying idea predates the EIP catalog. Remote
Procedure Call and its predecessor mechanisms, described in Birrell and
Nelson, "Implementing Remote Procedure Calls," ACM Transactions on Computer
Systems, 1984, already treated a network call as an instruction to invoke an
operation with given arguments, and Command Message is best understood as
that same intent carried by an asynchronous, queued transport instead of a
synchronous network call.

## 2. Problem and context

An application wants another application, or another component in the same
system, to perform a specific piece of work. The obvious tool for "do this
thing" is a direct procedure call, a REST POST, a gRPC call, a local method
invocation. That works when the caller can afford to block until the work is
done, when the callee is guaranteed to be reachable right now, and when the
caller does not care whether the work eventually completes if the callee is
temporarily down. Those three assumptions collapse constantly in a real
distributed system. The callee may be offline for a deployment. The operation
may take longer than any sane HTTP timeout. The caller may need to fire off
work from inside a database transaction and cannot risk a network call
failing mid-commit. The system may need to replay the instruction later,
audit that it happened, or retry it with the same guarantees as a database
insert.

The Command Message pattern reframes "invoke this operation" as "send a
message describing the operation to a channel," and lets the messaging
infrastructure, not the caller's thread, own the delivery, retry, and
persistence guarantees. The context in which this problem shows up is
specifically integration between two components that are decoupled in
deployment, meaning they can be released, restarted, and scaled
independently, but coupled in intent, meaning the sender genuinely wants a
specific, named action to happen and usually cares whether it happened. This
is the defining distinction from an Event Message, where the sender has no
particular receiver in mind and does not care who, if anyone, reacts. A
Command Message always has an implicit or explicit target and an expected
effect.

## 3. Forces

The pattern balances five competing pressures, and it deliberately favors
some of them at the direct cost of others.

**Availability versus certainty of intent.** A direct call fails loudly and
immediately if the receiver is down. A Command Message on a durable queue
survives the receiver being down and is delivered when it comes back, which
raises availability of the overall workflow at the cost of the sender no
longer knowing, at send time, whether the action has happened.

**Latency versus decoupling.** The pattern trades response latency for
deployment independence. Sender and receiver can be on different release
schedules, written in different languages, running in different data
centers, because the coupling is reduced to agreement on the shape of the
message, not to both sides being up simultaneously and speaking the same RPC
protocol.

**Ordering versus throughput.** Many transports that carry Command Messages,
such as Kafka partitions, SQS FIFO queues, or RabbitMQ single-consumer
queues, can guarantee ordered delivery, but usually only within a partition
or a single consumer, which caps horizontal throughput. Systems that want
maximum throughput for a class of command often give up strict global
ordering.

**Idempotency burden versus at-least-once delivery.** Nearly every practical
messaging transport gives at-least-once delivery, not exactly-once, so the
pattern shifts the cost of duplicate suppression onto the command handler.
This is a real, ongoing engineering cost, not a one-time design decision, and
the pattern is honest about it rather than hiding it.

**Cognitive load and debuggability versus flexibility.** A synchronous call
can be stepped through in a debugger across two processes with a tracing
tool set to a breakpoint-adjacent view. A queued command requires reasoning
about two independently deployed pieces of code connected only by a message
schema, which is harder to trace end to end and requires correlation
identifiers and distributed tracing to reconstruct.

## 4. Applicability and non-applicability

Reach for a Command Message when the caller needs an action performed by a
specific, known receiver, the receiver may be temporarily unavailable and
that must not lose the instruction, the action can tolerate being processed
asynchronously because the caller does not need the result in the same
request, or the action must survive the sending process crashing immediately
after it decides to act, or the action needs to be retried, throttled, or
rate limited independently of the caller's own request rate. It also fits
well when the command needs to be persisted for audit or replay, because a
durable queue or log naturally gives that for free, and when the command
must not be lost even if the handler crashes mid-processing, which a
transactional outbox plus a Command Message channel provides more cleanly
than a bare synchronous call retried by hand.

Do not reach for it in these situations, with the reason stated.

**When the caller needs the result synchronously and cannot proceed without
it.** A Command Message on its own gives fire-and-forget semantics. Getting a
result back requires layering a Request-Reply pattern with a correlation
identifier and a reply channel on top, which adds real complexity that a
plain synchronous call does not need. If every call in a code path needs an
immediate answer, a direct call or a synchronous RPC framework is simpler and
should be preferred.

**When the operation must happen exactly once and duplicates are
unacceptable, and the team has no appetite to build idempotency handling.**
At-least-once delivery is the practical default of nearly every message
broker, as documented for standard SQS queues, which states standard queues
support "at-least-once message delivery" (AWS SQS Developer Guide, verified
2026-08-02, https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html).
So a command handler that is not idempotent will eventually double-charge a
customer or double-ship an order. If the team cannot invest in idempotency
keys, do not use a queued command for that operation. Use a synchronous
transactional call instead.

**When the two components are so tightly coupled in deployment that they are
effectively one unit, such as a monolith's internal function calls.**
Wrapping an in-process function call in a message and a broker adds latency,
an additional failure mode from the broker itself, and operational surface
area for zero decoupling benefit, because the two "components" are never
deployed separately.

**When the caller needs strict global ordering across many independent
producers and the chosen transport cannot provide it without collapsing to a
single partition.** Forcing every command through one ordered channel to get
correctness often destroys the throughput benefit that justified messaging in
the first place. A different pattern, an Aggregator or a strongly consistent
data store, may be a better fit.

**When the command's side effect cannot be made idempotent and the transport
gives no deduplication.** Some operations, an irreversible physical action or
a one-time email that must never be sent twice with real, lasting fallout,
should go through a synchronous, transactionally-guarded call with an
explicit idempotency key check at the data layer rather than a queued
command, unless the team builds a deduplication table keyed on a message
identifier.

## 5. Structure

The participants are the Command Sender, the Command Message itself, the
Command Channel it travels on, and the Command Executor, also called the
handler, consumer, or service activator depending on the framework.

The **Command Sender** decides that an action should occur, constructs the
message, and places it on the channel. It does not know, and in the canonical
form does not need to know, which physical instance of the executor will
process it, only that some conforming executor eventually will. The Command
Sender's responsibility ends at successful enqueue, which is itself a
promise, in the Guaranteed Delivery sense, that the message will not be
silently lost by the channel.

The **Command Message** is a regular message, a well-defined envelope
carrying headers and a body, whose payload is structured as a verb plus its
arguments, not as a record of something that already happened. This is the
detail that most cleanly distinguishes it from a Document Message, which
carries data with no implied action, and an Event Message, which carries the
fact that something already happened, addressed to nobody in particular. The
command's name is typically an imperative verb phrase, ShipOrder,
CancelSubscription, RebuildIndex, and its body carries exactly the arguments
that verb needs.

The **Command Channel** is usually a Point-to-Point Channel, see
`patterns/07-integration/point-to-point-channel.md`, because a command has
exactly one intended executor and must not be processed twice by two
different consumers competing for the same unit of work, though a single
logical channel is commonly backed by several physical consumer instances
for horizontal scaling, with the channel itself, not the sender, responsible
for delivering each message to exactly one of them.

The **Command Executor** consumes the message, deserializes it into the
verb-plus-arguments shape, validates it, rejecting malformed commands to an
Invalid Message Channel, see `patterns/07-integration/invalid-message-channel.md`,
performs the action, and, if the interaction requires it, sends a result back
on a separate reply channel correlated to the original command's identifier.

## 6. ASCII structure diagram

```
+-----------------+          +----------------------+
|  Command Sender  |          |   Command Executor    |
|                  |          |  (handler / consumer)  |
|  decide: "do X"  |          |                        |
|  build Command   |          |  validate command      |
|  Message         |          |  perform action        |
+---------+--------+          |  ack / nack channel     |
          |                   +-----------+------------+
          | send                          ^
          v                               | consume
   +--------------------------------------+---------+
   |         Command Channel                        |
   |  (point to point, one logical destination)      |
   |  headers: commandName, commandId, correlationId  |
   |  body: verb + arguments                          |
   +--------------------------------------------------+
                     |
                     v (on malformed command)
        +---------------------------+
        |  Invalid Message Channel   |
        +---------------------------+
```

## 7. Dynamics

The runtime flow starts when the Command Sender decides an action must
happen. It constructs a Command Message, giving it a stable command name, a
unique command identifier for deduplication and tracing, and, if a reply is
expected, a reply-to address and a correlation identifier the eventual reply
will echo back. The sender then places the message on the Command Channel,
and the send itself is typically wrapped in the sender's own transaction via
a transactional outbox, so the command is only durably recorded if the
triggering business decision itself commits.

```
Dynamics, fire-and-forget command with delivery guarantee

Sender          Command Channel          Executor
  |                    |                     |
  |--send(Command)---->|                     |
  |                    |--persist message--->|
  |<--ack (enqueued)---|                     |
  |                    |--deliver----------->|
  |                    |                     |--validate
  |                    |                     |--execute action
  |                    |<---ack (processed)--|
  |                    |--remove from queue-->|
  |                    |                     |
  |  (if executor crashes before ack,        |
  |   message becomes visible again and      |
  |   is redelivered to another consumer)     |
```

```
Dynamics, request-reply variant with correlation

Sender                Command Channel     Executor      Reply Channel
  |                          |                |               |
  |--send(cmd, replyTo,      |                |               |
  |        correlationId)--->|                |               |
  |                          |--deliver------>|               |
  |                          |                |--execute      |
  |                          |                |--build Reply  |
  |                          |                |  (same        |
  |                          |                |   correlationId)|
  |                          |                |--send-------->|
  |<-------------------------poll / consume---|---------------|
  |  correlate reply to original request       |               |
  |  by correlationId                          |               |
```

The channel is responsible for at-least-once delivery. If the executor
crashes or fails to acknowledge before a visibility timeout expires, the
broker redelivers the message, potentially to a different executor instance.
This is precisely why the executor must be idempotent, because the sender's
single logical send can, from the executor's point of view, arrive more than
once.

## 8. Implementation variants

**Fire-and-forget, no reply.** The simplest variant. The sender enqueues and
moves on. Used for commands whose completion the sender does not need to
observe synchronously, such as sending a transactional email or rebuilding a
search index.

**Request-reply with a temporary or shared reply channel.** The sender
attaches a `replyTo` address and a `correlationId`, then either blocks on a
temporary queue, the classic JMS request-reply idiom, or polls or subscribes
asynchronously. Spring Integration formalizes this as a Messaging Gateway,
whose documentation states that "a gateway hides the messaging API provided
by Spring Integration. It lets your application's business logic be unaware
of the Spring Integration API," letting calling code look like a plain method
call while the gateway does the send-and-await underneath (Spring
Integration Reference, Messaging Gateway, verified 2026-08-02,
https://docs.spring.io/spring-integration/reference/gateway.html).

**Command with an idempotency key checked at the executor.** The executor
stores processed command identifiers in a deduplication table, or relies on
the transport's own deduplication, such as SQS FIFO's message deduplication
identifier, and short-circuits a redelivered command by returning the
previously computed result instead of re-executing the side effect. This is
the standard fix for the at-least-once delivery force named in dimension 3.

**Command bus in-process, transport-agnostic later.** Many application
frameworks, MediatR in .NET, Symfony Messenger in PHP, Axon Framework in
Java, implement an in-process "command bus" abstraction where sending a
command is a local method call that dispatches to a registered handler by
type, and the same abstraction can later be backed by a real message broker
without changing calling code. This variant trades some of the pattern's
deployment-decoupling benefit for a simpler mental model during early
development, with the option to swap in a real transport later.

**Language-idiomatic shape in a functional language.** In languages with
first-class functions, the "command" can be a plain closure captured with its
arguments and placed on a channel or queue, rather than a named class with a
handler registry. Go's `chan func()` pattern and Rust's `mpsc::channel` fed
with boxed closures are common lightweight expressions of this, at the cost
of losing the introspectable command name that a named struct or class gives
you for logging and routing.

## 9. Known production uses

**Apache Camel's messaging endpoint model**, where routes commonly express a
Content Based Router or Recipient List in front of a service that expects an
imperative-shaped message body, and Camel's own EIP catalog page is a
maintained, direct restatement of the Hohpe and Woolf patterns, evidence that
the pattern is treated as a first-class, implemented routing shape rather
than a purely theoretical one (Apache Camel, Enterprise Integration Patterns
implemented by Camel, verified 2026-08-02,
https://camel.apache.org/components/latest/eips/enterprise-integration-patterns.html).

**Amazon SQS as the command channel underneath countless production
architectures**, where a producer enqueues a unit of work for a decoupled
consumer fleet to process, with the guide explicitly describing "producers
(components that send messages to the queue) and consumers (components that
receive messages from the queue)" with redundant, durable storage across
servers (AWS SQS Developer Guide, What is Amazon SQS, verified 2026-08-02,
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html).
SQS's own basic architecture section models exactly the Command Sender to
Command Channel to Command Executor structure of dimension 5, at internet
scale.

**Spring Integration's Messaging Gateway and Service Activator components**,
used across a large number of Java enterprise integration deployments to
expose a plain Java interface, for example a `Cafe.placeOrder(Order order)`
method, that internally sends a Command Message onto a request channel and,
where configured, awaits a correlated reply, exactly the request-reply
variant described in dimension 8 (Spring Integration Reference, Messaging
Gateway chapter, verified 2026-08-02,
https://docs.spring.io/spring-integration/reference/gateway.html).

**MassTransit and NServiceBus in the .NET ecosystem**, both of which enforce
a structural distinction between "Command" message types, sent to a single
specific consumer using an imperative verb naming convention, and "Event"
message types, published to any number of subscribers, directly mirroring
the Hohpe and Woolf Command Message versus Event Message distinction as a
routing-time constraint rather than a mere naming convention, documented
across both frameworks' public documentation as a foundational modeling rule
for message-based .NET systems.

## 10. Consequences

Positive consequences. The sender and receiver can be deployed, scaled, and
restarted independently, because the only coupling is the message schema,
not a live network connection. The instruction survives the sender's process
crashing immediately after deciding to act, when combined with a
transactional outbox, because the message is durably recorded before the
sender's own transaction is visible to anyone else. Retrying a failed
execution becomes a broker-level concern, retries, backoff, a dead-letter
channel per `patterns/07-integration/dead-letter-channel.md`, instead of
hand-rolled retry logic scattered through calling code. The command's
lifecycle becomes independently observable and auditable, because it exists
as a durable record on a channel rather than as an ephemeral stack frame that
vanishes the instant the call returns. Throughput can be scaled by adding
consumer instances behind the same logical channel without the sender
changing at all.

Negative consequences. The sender loses the ability to know, at send time,
whether the action succeeded, unless a request-reply layer is added, which
itself adds a temporary channel, a correlation mechanism, and a timeout
policy that has to be designed and tested. At-least-once delivery is the
practical norm, so every command handler must either be naturally idempotent
or explicitly build deduplication, and forgetting this is one of the most
common production incidents involving this pattern, a double-charged
customer, a duplicate shipment. Debugging a chain of commands across
services requires distributed tracing and correlation identifiers, because a
stack trace stops at the boundary of the sending process. Without deliberate
investment in tracing, a production incident involving three hops of Command
Messages can take substantially longer to diagnose than the equivalent
synchronous call chain. Message schema evolution becomes a first-class
concern, because a command's shape is now a durable, versioned contract that
outlives any single deployment of either the sender or the receiver, unlike
an in-process function signature that the compiler checks at build time.

## 11. Failure modes and misuse

**Symptom.** A customer is charged twice, or an order ships twice, with no
obvious bug in the handler code. **Cause.** The command handler performs a
non-idempotent side effect, a charge, a shipment, with no deduplication
against the command's unique identifier, and the broker redelivers the
message after a crash, a slow acknowledgment, or a visibility timeout expiry
during normal at-least-once operation. **Fix.** Store processed command
identifiers in a deduplication table with a unique constraint, or rely on the
transport's native deduplication, such as SQS FIFO message deduplication
identifiers, and make the side effect itself idempotent at the data layer,
for example an upsert keyed on the command identifier rather than an
unconditional insert.

**Symptom.** Commands silently pile up in the queue with no processing, and
nobody notices for hours or days. **Cause.** The consumer fleet was scaled
to zero, crashed on startup, or is failing every message and the failures
are routed into a dead-letter channel that nobody monitors. **Fix.** Alert on
queue depth and age-of-oldest-message, and treat the dead-letter channel,
`patterns/07-integration/dead-letter-channel.md`, as a monitored, actionable
destination, not a silent graveyard.

**Symptom.** A command is processed correctly but the sender never learns the
result, and downstream code that assumed a synchronous reply hangs or times
out unpredictably. **Cause.** The team implemented fire-and-forget send but
the calling code was written as though it were request-reply, often because
the developer copied a synchronous call pattern without realizing the
underlying transport changed. **Fix.** Make the sender's API explicit about
which shape it implements, fire-and-forget or request-reply, and never let a
caller assume request-reply semantics from a fire-and-forget send.

**Symptom.** Two different services both consume the same command and both
perform the action, causing duplicated side effects that look like a race
condition. **Cause.** The channel was actually implemented as a
publish-subscribe topic, where every subscriber gets every message, rather
than a genuine point-to-point channel where exactly one consumer instance
gets each message, a common misconfiguration when a team reuses an existing
pub-sub topic for what should have been a command channel. **Fix.** Verify
the channel's delivery semantics match Point-to-Point Channel,
`patterns/07-integration/point-to-point-channel.md`, not Publish-Subscribe,
before treating anything sent on it as a command.

**Symptom.** The command handler throws on a message it cannot parse, and
that one bad message blocks the entire queue from making progress.
**Cause.** A malformed or unversioned message was allowed onto the command
channel with no validation step, and the consumer's naive retry loop
redelivers the same poison message forever instead of routing it aside.
**Fix.** Validate incoming commands and route anything malformed to an
Invalid Message Channel, `patterns/07-integration/invalid-message-channel.md`,
and cap redelivery attempts before routing to a dead-letter channel.

**Symptom.** Commands processed out of order cause incorrect final state, for
example a cancellation processed before the order it cancels was created.
**Cause.** The transport does not guarantee ordering across the relevant
scope, a common trap with a naive fan-out across many partitions or many
parallel consumers of a single logical entity's commands. **Fix.** Partition
or key commands for the same logical entity onto the same ordered
sub-channel, a Kafka partition key or an SQS FIFO message group identifier,
so commands touching one entity are always processed in send order while
other entities' commands proceed in parallel.

## 12. Trade-off matrix

| Force | Command Message (queued) | Direct synchronous call (REST/gRPC) | Event Message (pub-sub) |
|---|---|---|---|
| Sender knows result immediately | No, unless request-reply layer added | Yes | No, never by design |
| Survives receiver being down | Yes, message waits on channel | No, call fails immediately | Yes, but no single intended receiver |
| Deployment coupling | Low, schema only | High, both must be up simultaneously | Low, schema only |
| Delivery guarantee | Typically at-least-once, durable | None beyond the single call attempt | Typically at-least-once, durable |
| Ordering guarantee | Depends on transport, often per-key | Implicit, single call is atomic in time | Depends on transport, often none globally |
| Idempotency burden on receiver | High, must be designed for | None, call either happened or did not | High, must be designed for |
| Debuggability via stack trace | Low, needs distributed tracing | High, single call stack | Low, needs distributed tracing |
| Intended receiver cardinality | Exactly one | Exactly one | Zero or more, unknown to sender |

## 13. Related and incompatible patterns

**Point-to-Point Channel**, `patterns/07-integration/point-to-point-channel.md`,
is the channel type a Command Message almost always rides on, because a
command has exactly one intended executor and must not be duplicated across
competing consumers claiming the same unit of work. Using a Publish-Subscribe
Channel instead is the misuse described in dimension 11.

**Event Message** is the pattern's sibling and its conceptual opposite in
intent. An Event Message states a fact that already happened and is
addressed to nobody in particular, while a Command Message requests an
action and is implicitly or explicitly addressed to a specific, known
executor. The two are frequently confused in naming, for example a message
named `OrderShipped` that is actually consumed by exactly one specific
billing service acting on it as an instruction is really a Command Message
wearing an Event Message's name.

**Document Message** carries data with no implied action and no implied
recipient responsibility to act. A Command Message can be thought of as a
Document Message plus an obligation, which is the defining semantic addition.

**Invalid Message Channel**, `patterns/07-integration/invalid-message-channel.md`,
composes directly with Command Message as the destination for a command that
fails validation, keeping poison messages from blocking the primary channel.

**Dead Letter Channel**, `patterns/07-integration/dead-letter-channel.md`,
composes as the destination for a command that repeatedly fails processing
after exhausting retry attempts.

**Guaranteed Delivery**, `patterns/07-integration/guaranteed-delivery.md`, is
frequently layered under a Command Message channel so the sender's enqueue is
itself durable before the sender's own transaction commits, closing the gap
where a crash between deciding to act and sending the message would silently
lose the command.

**Datatype Channel**, `patterns/07-integration/datatype-channel.md`, is
sometimes used to give each distinct command type its own channel, so
consumers do not need to branch on a command name field to know how to
deserialize the body, at the cost of proliferating channels as the number of
command types grows.

**Messaging Bridge**, `patterns/07-integration/messaging-bridge.md`, can carry
a Command Message across two different messaging systems, for example
translating a command from an internal RabbitMQ exchange to a partner's SQS
queue, when two organizations integrate over different transports.

No pattern in this family is structurally incompatible with Command Message.
The pattern's cost is entirely about the operational discipline, idempotency,
tracing, monitoring, it demands from the team, not a structural conflict with
any neighboring pattern.

## 14. Refactoring path in and out

Introducing a Command Message into code that currently does a direct
synchronous call proceeds in five steps. First, identify the call site and
confirm the caller genuinely does not need a synchronous result, or is
willing to add a request-reply layer if it does. This is the single most
important decision and reversing it later is expensive. Second, define the
command's message shape explicitly as a named type, a class, struct, or
schema, with a stable command name and a unique identifier field, resisting
the temptation to reuse an existing internal data transfer object whose shape
may drift for unrelated reasons. Third, introduce the channel and wire the
existing call site to enqueue onto it instead of calling directly, ideally
behind the same interface the caller already used, an Anti-Corruption Layer
applied to the call site so callers do not need to change. Fourth, build the
executor as a new consumer that performs the same logic the old synchronous
handler performed, adding an idempotency check keyed on the command's unique
identifier before any side effect executes. Fifth, run both paths, the old
synchronous call and the new queued command, in parallel behind a feature
flag or a percentage rollout, comparing outcomes, before retiring the
synchronous path entirely.

Removing a Command Message when it stops earning its place, for example the
receiver's uptime became reliable enough and the team decided the
operational cost of idempotency and tracing was no longer worth it for this
particular low-volume, low-criticality operation, proceeds in reverse.
Verify no in-flight or queued messages remain, replace the enqueue call with
a direct synchronous call to the same underlying logic, which the executor
already isolated in step four above, making this the easy direction of the
refactor, and finally decommission the channel and its dead-letter
counterpart. The Encapsulate Channel technique from the family of
message-oriented refactorings, documented in Hohpe and Woolf's own book
alongside a parallel set of messaging refactorings, is directly applicable
here, because if the original introduction wrapped the send behind an
interface, removing the queue becomes a change to a single implementation,
not to every call site.

## 15. Testing and verification

Testing code built around a Command Message splits cleanly into three
layers, and each layer becomes easier to test in isolation than an
equivalent tightly coupled synchronous call, at the cost of needing all
three layers tested for full confidence.

The sender's responsibility, deciding to send and building the message
correctly, is tested by asserting that, given a triggering condition, the
correct command type with the correct arguments was placed on a channel. A
test double standing in for the channel, an in-memory fake queue or a
captured list of sent messages, is sufficient and does not require a real
broker, which keeps this layer of tests fast.

The executor's responsibility, correctly interpreting and acting on a
command, is tested by constructing a command message directly, in memory,
and asserting the resulting side effect, again without needing a real
broker. This is where idempotency must be explicitly tested by sending the
identical command twice and asserting the side effect happened exactly once.

The end-to-end wiring, whether a real message actually flows from the real
sender through the real channel to the real executor, is tested with an
integration test against a real or embedded broker, an embedded ActiveMQ or a
Testcontainers-managed RabbitMQ or Kafka instance are common choices, and
this layer should be kept deliberately small in number, because it is slow
and brittle compared to the first two layers. Its job is only to catch
serialization mismatches and channel misconfiguration that the in-memory
tests cannot see.

A useful technique specific to this pattern is contract testing on the
message schema itself, a JSON Schema, an Avro schema, or a Protobuf
definition validated in CI against both the sender's and the executor's
expectations, which catches the case where the sender and executor drift
apart in their understanding of a command's shape even though each side's
own unit tests still pass.

## 16. Observability signals

A healthy Command Message channel shows a queue depth that oscillates near
zero under normal load and returns to zero shortly after any burst, an
age-of-oldest-unprocessed-message metric that stays low, seconds to low
minutes depending on the SLA the command carries, a dead-letter channel that
receives essentially zero messages in steady state, and a processing
duration histogram per command type that is stable release over release.

Log the command's unique identifier, command name, and correlation
identifier if request-reply, at both send time and at consume time, so a
single command's path from send to execution can be reconstructed from logs
alone even without a full tracing system. This is the cheapest observability
investment for this pattern and should be treated as non-optional.

Trace the send-to-execute span using a distributed tracing system,
OpenTelemetry is the current widely adopted standard, that propagates a
trace context through the message headers, because without this a
production incident spanning a Command Message hop is much harder to
diagnose than one confined to a single process's stack trace.

A failing instance of this pattern shows a growing queue depth with no
corresponding increase in processing rate, meaning consumers are stuck,
crashed, or scaled to zero, a rising dead-letter rate meaning commands are
systematically failing validation or execution, a rising duplicate-execution
rate as observed by the idempotency check's hit rate, meaning redelivery is
happening more than expected, often signaling the executor is too slow
relative to the transport's visibility timeout and is losing the race to
acknowledge before redelivery fires, or a widening gap between commands sent
and commands consumed over a sliding time window, which is the single
clearest early warning signal of a backlog forming before it becomes an
incident.

## 17. Security and privacy implications

A Command Message channel is an attack surface if the channel accepts
messages from any producer with network access to it, because an attacker
who can place a well-formed command onto the channel can trigger the same
privileged action a legitimate sender would trigger. The channel therefore
needs the same authentication and authorization discipline as any other
privileged API surface, not an implicit trust based on being internal.
Amazon's own SQS documentation makes this an explicit, first-class concern,
stating that "you control who can send messages to and receive messages from
an Amazon SQS queue" through IAM policy, and separately documenting
server-side encryption options for message contents (AWS SQS Developer
Guide, Benefits of using Amazon SQS, verified 2026-08-02,
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html).

Command payloads frequently carry personal or sensitive data as command
arguments, a customer identifier, a payment amount, an address, and because
the message is durably persisted on the channel and in any dead-letter
channel it may land in, that data at rest inherits whatever retention and
encryption policy the broker enforces. A command containing sensitive
arguments that lands in a dead-letter channel and is retained indefinitely
for debugging is a common, easily overlooked data retention violation.

Replay is a distinct risk from duplicate delivery. An attacker who can
capture and re-send a previously valid command message, for example a
RefundPayment command, may be able to trigger the action again if the
executor's idempotency check is keyed on something the attacker can control
or omit, rather than on a server-generated, unforgeable identifier tied to
the original authorization context. The idempotency key must be
cryptographically tied to the original request, not merely a client-supplied
field, when the command authorizes a financially or operationally
irreversible action.

Audit logging of who sent which command, with what arguments, and when it
was executed, is a natural and valuable byproduct of the pattern's durable,
recorded nature, and should be treated as a security control in its own
right for any command that changes privileged state, not merely an
operational convenience.

## 18. References

1. Gregor Hohpe, Bobby Woolf. *Enterprise Integration Patterns. Designing,
   Building, and Deploying Messaging Solutions.* Addison-Wesley, 2003. The
   Message Construction chapter defines Command Message, Document Message,
   and Event Message as the three message-content patterns.
2. Enterprise Integration Patterns website, Command Message page, verified
   2026-08-02. https://www.enterpriseintegrationpatterns.com/patterns/messaging/CommandMessage.html
3. Amazon Web Services. What is Amazon Simple Queue Service. AWS SQS
   Developer Guide, verified 2026-08-02.
   https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html
4. Spring Integration Reference Documentation, Messaging Gateway chapter,
   verified 2026-08-02. https://docs.spring.io/spring-integration/reference/gateway.html
5. Apache Camel, Enterprise Integration Patterns implemented by Camel,
   verified 2026-08-02.
   https://camel.apache.org/components/latest/eips/enterprise-integration-patterns.html
6. Andrew D. Birrell, Bruce Jay Nelson. Implementing Remote Procedure Calls.
   ACM Transactions on Computer Systems, Volume 2, Issue 1, February 1984.
   Foundational description of the invoke-a-remote-operation intent that
   Command Message reimplements over asynchronous messaging.
7. Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides. *Design
   Patterns. Elements of Reusable Object-Oriented Software.* Addison-Wesley,
   1994. Chapter 5, the Command pattern, describes encapsulating a request as
   an object, the object-oriented ancestor of the Command Message's
   verb-plus-arguments payload shape.

## Code examples

### TypeScript. Command Message with an in-memory point-to-point channel

```typescript
interface ShipOrderCommand {
  commandName: "ShipOrder";
  commandId: string;
  orderId: string;
  carrier: string;
}

class CommandChannel<T extends { commandId: string }> {
  private queue: T[] = [];
  private processed = new Set<string>();

  send(command: T): void {
    this.queue.push(command);
  }

  drain(handle: (command: T) => void): void {
    while (this.queue.length > 0) {
      const command = this.queue.shift()!;
      if (this.processed.has(command.commandId)) {
        continue;
      }
      handle(command);
      this.processed.add(command.commandId);
    }
  }
}

function shipOrder(command: ShipOrderCommand): void {
  console.log(`shipping order ${command.orderId} via ${command.carrier}`);
}

const channel = new CommandChannel<ShipOrderCommand>();
channel.send({
  commandName: "ShipOrder",
  commandId: "cmd-1",
  orderId: "order-42",
  carrier: "dhl",
});
channel.send({
  commandName: "ShipOrder",
  commandId: "cmd-1",
  orderId: "order-42",
  carrier: "dhl",
});
channel.drain(shipOrder);
```

### Java. Command Message with a bounded queue and an idempotent executor

```java
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

final class ShipOrderCommand {
    final String commandId;
    final String orderId;
    final String carrier;

    ShipOrderCommand(String commandId, String orderId, String carrier) {
        this.commandId = commandId;
        this.orderId = orderId;
        this.carrier = carrier;
    }
}

final class CommandExecutor {
    private final Set<String> processedCommandIds = new HashSet<>();

    void execute(ShipOrderCommand command) {
        if (!processedCommandIds.add(command.commandId)) {
            System.out.println("duplicate command " + command.commandId + " ignored");
            return;
        }
        System.out.println("shipping order " + command.orderId + " via " + command.carrier);
    }
}

public final class CommandMessageDemo {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<ShipOrderCommand> channel = new LinkedBlockingQueue<>();
        CommandExecutor executor = new CommandExecutor();

        channel.put(new ShipOrderCommand("cmd-1", "order-42", "dhl"));
        channel.put(new ShipOrderCommand("cmd-1", "order-42", "dhl"));

        while (!channel.isEmpty()) {
            executor.execute(channel.take());
        }
    }
}
```

### Go. Command Message over a channel with idempotent handling

```go
package main

import "fmt"

type shipOrderCommand struct {
	commandID string
	orderID   string
	carrier   string
}

type commandExecutor struct {
	processed map[string]bool
}

func newCommandExecutor() *commandExecutor {
	return &commandExecutor{processed: make(map[string]bool)}
}

func (e *commandExecutor) execute(cmd shipOrderCommand) {
	if e.processed[cmd.commandID] {
		fmt.Printf("duplicate command %s ignored\n", cmd.commandID)
		return
	}
	e.processed[cmd.commandID] = true
	fmt.Printf("shipping order %s via %s\n", cmd.orderID, cmd.carrier)
}

func main() {
	channel := make(chan shipOrderCommand, 10)
	channel <- shipOrderCommand{commandID: "cmd-1", orderID: "order-42", carrier: "dhl"}
	channel <- shipOrderCommand{commandID: "cmd-1", orderID: "order-42", carrier: "dhl"}
	close(channel)

	executor := newCommandExecutor()
	for cmd := range channel {
		executor.execute(cmd)
	}
}
```
