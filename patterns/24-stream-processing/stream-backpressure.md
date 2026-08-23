---
name: Stream Backpressure
slug: stream-backpressure
family: 24-stream-processing
category: Stream Processing
aliases: [Credit-Based Flow Control, Watermark Alignment (Flink)]
first_described: "Reactive Streams JVM SIG, 2013 to 2015, general application-level formalization, the subject of the sibling Backpressure entry; Apache Flink 1.5, credit-based network stack, 2018, the stream-processing-engine-specific protocol this entry documents"
maturity: established
related: [backpressure, watermark, event-time-processing, exactly-once-processing]
incompatible_with: []
verified: 2026-08-23
---

## 1. Name, aliases, and lineage

Stream Backpressure is the application of the general backpressure idea, a
consumer signaling a producer to slow down rather than being overwhelmed, to
the specific structural problem of a distributed stream-processing engine. a
directed graph of parallel operator subtasks, each running as its own thread
or process, connected by network shuffles that cross machine boundaries. The
general mechanism, the demand-signaling contract of the Reactive Streams
specification, TCP's sliding window, Node.js's write-then-drain protocol, is
the subject of the sibling Backpressure entry in family 09-concurrency, and
this entry deliberately does not re-derive that material. What is genuinely
distinct here is how a stream-processing engine propagates a slow-consumer
signal transitively across many parallel operator instances at once, and how
that propagation interacts with the engine's own checkpointing and
event-time machinery, neither of which exists in a single-process reactive
pipeline.

Apache Flink's credit-based flow control is the primary, most precisely
documented instance of this specialization. Flink's own 2019 engineering
blog post on the network stack states the protocol directly. "Receivers
will announce the availability of buffers as credits to the sender, one
buffer equals one credit." The post frames this as a deliberate replacement
for an older, TCP-based approach used before Flink 1.5, in which a single
multiplexed TCP connection carrying several logical channels between two
TaskManagers would stall entirely once any one of its channels became
backpressured, a head-of-line blocking problem the credit-based redesign
was built to remove, since the post states that "with flow control, a
channel in a multiplex cannot block another of its logical channels."
Source. Apache Flink, "A Deep-Dive [through] Flink's Network Stack,"
verified 2026-08-23, https://flink.apache.org/2019/06/05/a-deep-dive-into-flinks-network-stack/.

The complementary, source-side half of the picture is Kafka's deliberately
pull-based consumer design, which the sibling Backpressure entry already
covers at the level of the max.poll.records and pause and resume
configuration. Confluent's own documentation of Kafka's design states the
architectural choice plainly. Kafka follows a pull-based design where "data
is pushed by the producer to the broker and pulled from the broker by the
consumer," contrasting this with push-based systems named directly, Scribe
and Apache Flume, and naming the reason. "if a consumer falls behind
production, they can catch up," which gives the consumer, not the broker,
control over its own rate of consumption, a property a push-based system
cannot offer without either dropping data or buffering it somewhere the
broker does not control. Source. Confluent documentation, "Kafka Consumer
Design," verified 2026-08-23,
https://docs.confluent.io/kafka/design/consumer-design.html.

## 2. Problem and context

In a single-process reactive pipeline the backpressure problem is a pair, one
producer and one consumer, and a demand-signaling or buffer-based protocol
between the two is sufficient. A stream-processing engine has a structurally
harder version of the same problem. a topology of many parallel operator
subtasks, potentially hundreds, spread across many machines, connected by a
shuffle in which every subtask of one operator may send to every subtask of
the next. If any single downstream subtask falls behind, whether from a
genuinely slow user function, a skewed key distribution sending it more data
than its peers, or a transient resource contention on its host, the naive
outcome is that every upstream subtask feeding it keeps sending at full rate
into a buffer that has nowhere bounded to grow, and unlike a single
process's heap, an unbounded buffer inside a long-running TaskManager
degrades the whole machine, not just one queue, through garbage-collection
pressure and eventually out-of-memory failure.

The problem is compounded by two things the general reactive-pipeline case
does not have to contend with. First, the slowdown must propagate
transitively, not just from the one overloaded subtask to its immediate
upstream neighbors, but chained backward through however many operator
stages sit before it, all the way to the sources, or the sources will keep
ingesting data the pipeline as a whole cannot digest. Second, the engine's
own fault-tolerance mechanism, periodic checkpointing, is itself sensitive
to how much data is sitting in transit inside network buffers at any given
moment, a dependency documented directly in Flink's own checkpointing
material and covered in Dynamics and Consequences below.

## 3. Forces

Buffer footprint versus throughput headroom. Flink's own network memory
tuning documentation gives a concrete formula for how many buffers a
sustained throughput target requires. "number_of_buffers = expected_throughput
times buffer_roundtrip divided by buffer_size," and the same page's worked
example, 320 megabytes per second of throughput at 1 millisecond round-trip
latency, yields roughly 10 actively used buffers. Undersizing this pool
relative to real throughput produces spurious backpressure, the engine
throttling a genuinely healthy pipeline because its buffer accounting, not
its actual processing capacity, is the bottleneck. Source. Apache Flink
documentation, "Network Memory Tuning Guide," verified 2026-08-23,
https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/deployment/memory/network_mem_tuning/.

Checkpoint duration versus sustained backpressure. Flink's own checkpointing
documentation states the tension directly for the default, aligned
checkpoint mode. checkpoint barriers travel embedded in the data stream
itself, so under backpressure a barrier queues up behind the same
already-full buffers the data itself is stuck behind, and checkpoint
duration becomes coupled to current throughput rather than to the actual
amount of state being snapshotted. Source. Apache Flink documentation,
"Checkpointing," verified 2026-08-23,
https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/datastream/fault-tolerance/checkpointing/.

Buffer occupancy versus in-flight state size, the watermark-specific
instance of this same force. The 2021 comparative paper already cited in the
sibling Watermark entry names the identical structural tension from the
opposite direction. "Unaligned source watermarks can lead to a significant
increase in state size to buffer in-flight data." A source racing ahead of
its slower peers is, mechanically, the same fast-producer-into-a-bounded-
downstream problem this entry documents, just triggered by event-time drift
rather than by buffer occupancy, and Related and incompatible patterns below
returns to this in detail.

## 4. Applicability and non-applicability

Stream Backpressure, the credit-based, engine-internal variant documented
here, is the right lens whenever the system in question is a distributed
stream-processing engine with parallel operator instances and network
shuffles between them, Flink being the most precisely sourced example.
Reasoning about flow control at this layer means reasoning about buffer
pools, credits, and checkpoint alignment, not about a single Publisher and
Subscriber pair.

It is the wrong lens, and unnecessary complexity, for a single-process
pipeline with one producer and one consumer, or for an application built
directly on a reactive library such as RxJava, Project Reactor, or Node.js
streams, where the general demand-signaling or buffer-and-drain protocols
already documented in the sibling Backpressure entry are the complete
answer, and where introducing a distributed engine's checkpoint-coupled
credit protocol would be pure overhead with no corresponding benefit, since
there is no multi-hop shuffle for it to protect.

## 5. Structure

Flink's network stack, per its own architecture blog, is built from a small
set of participants on each side of a channel between two subtasks. On the
sending side, a ResultSubpartition tracks its own outstanding channel
credits and the current backlog, how many buffers are queued and waiting to
be sent for that specific logical channel. On the receiving side, an
InputChannel owns a pool of buffers drawn from two sources, a fixed number
of exclusive buffers dedicated to that one channel, and a shared pool of
floating buffers drawn from across the whole input gate, the receiving
subtask's collection of all its incoming channels. The network memory tuning
page states the exact default sizing. exclusive buffers default to 2 per
channel, floating buffers default to 8 per gate, and the total buffer
budget for a gate is computed as the channel count times the per-channel
exclusive allotment, plus the floating pool.

## 6. ASCII structure diagram

```
  Upstream subtask                          Downstream subtask
  +-------------------+                     +-------------------+
  | ResultSubpartition |   credits granted   |   InputChannel     |
  | (tracks backlog,   | <------------------ |  exclusive buffers |
  |  per-channel       |                     |  (default 2)       |
  |  credit balance)   |   data + backlog    |                    |
  |                    | -------------------> |  floating buffers  |
  +-------------------+   count (per buffer)  |  (default 8,       |
                                               |   shared per gate) |
                                               +---------+---------+
                                                         |
                                          buffer pool exhausted?
                                                         |
                                                     yes v  no
                                        subtask marked "backpressured"  keep granting
                                        no further credit granted       credits
                                                         |
                                              stall propagates upstream
                                              to THIS subtask's own
                                              upstream senders in turn
```

## 7. Dynamics

The credit protocol itself, per the network stack blog, runs continuously
during normal operation. each result subpartition tracks its own channel
credits, "buffers are only forwarded to the lower network stack if credit is
available and each sent buffer reduces the credit score by one," and the
receiver communicates its queue depth back to the sender by additionally
sending "information about the current backlog size which specifies how
many buffers are waiting in this subpartition's queue," letting the receiver
decide how aggressively to replenish credit based on real, current demand
rather than a fixed, static allotment.

Detection and monitoring run on a separate, sampled cadence, per Flink's own
backpressure monitoring documentation. "Internally, back pressure is judged
based on the availability of output buffers. If a task has no available
output buffers, then that task is considered back pressured." Three metrics
are tracked per subtask, backPressuredTimeMsPerSecond, idleTimeMsPerSecond,
and busyTimeMsPerSecond, which "are adding up approximately to 1000ms" at
any given moment, updated "every couple of seconds," with the reported value
representing the average over that sampling window. The web UI translates
the backpressured ratio into three named states, OK for zero to ten percent,
LOW for ten to fifty percent, HIGH for fifty to one hundred percent.

The checkpointing interaction is a distinct, separately-triggered dynamic.
under the default aligned mode, a checkpoint barrier travelling downstream
cannot overtake the data already queued ahead of it in a backpressured
channel, so checkpoint duration stretches out under sustained backpressure.
Flink's own documentation names the specific fix, unaligned checkpoints,
which "contain data stored in buffers as part of the checkpoint state,
which allows checkpoint barriers to overtake these buffers," so that
"checkpoint duration becomes independent of the current throughput." A
related, automatic fallback also documented on the same page is
execution.checkpointing.aligned-checkpoint-timeout, which lets a checkpoint
"start aligned" and switch to unaligned mid-flight "if during checkpointing,
checkpoint start delay exceeds this timeout."

## 8. Implementation variants

Flink's credit-based network stack, the primary variant this entry
documents in depth above, since Flink 1.5, 2018, replacing an earlier
TCP-multiplexed approach that suffered head-of-line blocking across
unrelated logical channels sharing one physical connection.

Kafka's pull-based consumer model, the source-side complement rather than a
competing implementation of the same idea. Because the consumer, not the
broker, decides when and how much to pull, per Confluent's own consumer
design documentation quoted in Name, aliases, and lineage above, a Kafka
source operator feeding a stream-processing engine is architecturally
incapable of being force-fed faster than it chooses to poll, which is a
different mechanism from Flink's internal credit protocol but composes with
it directly. a Kafka source that is itself backpressured by a downstream
operator's exhausted buffer pool simply stops issuing poll calls, the two
mechanisms meeting at the boundary between the external system and the
engine's own network stack. The sibling Backpressure entry already covers
the specific max.poll.records and pause and resume configuration surface
in depth, and this entry does not repeat it.

Watermark alignment, a third, event-time-triggered variant, unique to
engines that implement the watermark model. covered in full in Related and
incompatible patterns below, since it is best understood in direct
comparison to the two mechanisms above rather than as a standalone
implementation note.

General-purpose, single-process reactive backpressure, the Reactive
Streams demand-signaling contract, blocking and asynchronous bounded
queues, and Node.js's write-then-drain protocol, is deliberately out of
scope here and fully documented in the sibling Backpressure entry, family
09-concurrency, which this entry cross-references rather than duplicates.

## 9. Known production uses

Bouygues Telecom, per Apache Flink's own production-users page, runs "30
production applications powered by Flink and is processing 10 billion raw
events per day," a throughput at which an unbounded or naively-sized buffer
pool would be a direct operational liability, making the credit-based
protocol's bounded-memory guarantee load-bearing infrastructure rather than
an optional tuning knob. Source. Apache Flink, "Powered By Flink," verified
2026-08-23, https://flink.apache.org/what-is-flink/powered-by/.

Klaviyo, per the same page, "deduplicates and aggregates over a million
events per second," a workload shape, high-cardinality aggregation across
many parallel keys, directly exposed to the skew scenario named in Forces
above, where one key's subtask can legitimately run behind its peers and
must be able to signal that without the whole pipeline's memory footprint
growing unbounded.

Neither company's own page states in as many words that credit-based flow
control specifically is the mechanism they depend on. the causal link
between the documented throughput figures and the network stack's bounded-
buffer design is this entry's own reasoned inference from how Flink's
architecture works, not a direct company statement, and is flagged as such
per the Evidence confidence addendum below.

## 10. Consequences

The gain is a bounded, predictable memory footprint per channel regardless
of how skewed the workload becomes, and a signal that propagates
transitively and automatically across an entire operator DAG with no
per-pipeline wiring required, since it is Flink's default architecture
rather than an opt-in feature.

The cost is threefold, each traced to a force named above. checkpoint
duration couples to throughput under sustained backpressure unless unaligned
checkpoints or the alignment timeout are explicitly configured, buffer pool
sizing is a real tuning surface with a documented formula rather than a
single universal default, and network memory tuning's own guidance that
"for best throughput, we recommend using the default values" implicitly
concedes that deviating from the defaults, in either direction, is a
deliberate trade-off a team must reason about rather than a free lunch.

## 11. Failure modes and misuse

Undersized exclusive buffer pools causing spurious backpressure in
low-throughput, latency-sensitive setups. the network memory tuning page's
own remedy, "in the case of backpressure in low throughput setups, you
should consider reducing the number of exclusive buffers," is itself an
acknowledgment that the default sizing can misfire in the opposite
direction from the usual concern, throttling a pipeline that is not
actually short on real processing capacity.

Checkpoint duration silently ballooning under sustained backpressure when a
team has not configured unaligned checkpoints or an alignment timeout,
turning what looks like a throughput problem into a fault-tolerance
problem, since a checkpoint that takes minutes instead of seconds under
backpressure also means minutes of reprocessing on the next failure.

Assuming the credit-based protocol protects a slow external call made
inside a user function's own process method. the protocol documented above
governs buffers moving between operator subtasks across the network stack,
not a synchronous, blocking call an operator's own code makes to an
external system inside its process method. a slow downstream API call
embedded in user code stalls that one subtask's own thread and will
eventually surface as backpressure on ITS inbound channels once its own
input buffers fill, but the credit protocol itself has no visibility into,
and provides no protection for, the external call's latency directly. This
is this entry's own reasoning about the documented scope of the protocol,
labeled as inference rather than a directly-quoted warning, since Flink's
own documentation does not phrase the distinction in these terms.

## 12. Trade-off matrix

Flink's credit-based flow control propagates a slowdown transitively across
an entire multi-hop operator DAG automatically, at the cost of a real
buffer-sizing tuning surface and a checkpoint-duration coupling under the
default aligned mode.

Kafka's pull-based consumer model gives the source operator itself direct,
simple control over its own ingestion rate, at the cost of only protecting
the single hop between the external broker and the source operator, not
anything downstream of it, which is what the engine's own internal protocol
exists to cover.

The general Reactive Streams demand-signaling contract, RxJava, Project
Reactor, Akka Streams, per the sibling Backpressure entry, gives the finest
per-item control and the strongest composability guarantee within a single
process, at the cost of having no native answer to a distributed,
multi-machine shuffle at all, which is exactly the gap Flink's engine-level
protocol fills.

Load shedding, dropping or dead-lettering excess data instead of buffering
or signaling upstream, trades correctness and completeness for a hard,
predictable latency and memory ceiling, the right choice when a pipeline's
downstream SLA cannot tolerate the propagation delay backpressure itself
introduces, and the natural companion strategy is named directly in Related
and incompatible patterns below.

## 13. Related and incompatible patterns

Backpressure, the general sibling entry in family 09-concurrency, is the
umbrella this entry specializes for the distributed stream-processing-engine
case. every general mechanism, Reactive Streams demand signaling, TCP's
sliding window, Node.js's drain protocol, blocking and asynchronous bounded
queues, the LMAX Disruptor's ring buffer, gRPC's HTTP/2 flow control, and
adaptive concurrency limiting, is documented there in depth and
deliberately not repeated here.

Watermark, the published sibling entry, states the relationship from its
own side directly, quoted verbatim. "Flink's watermark alignment is,
functionally, a targeted form of backpressure, deliberately pausing a
fast-progressing source's consumption to bound in-flight state, the same
lever general backpressure uses, triggered here specifically by watermark
drift rather than by downstream queue depth." From this entry's own side,
watermark alignment is a third variant alongside the two documented in
Implementation variants above. where credit-based flow control throttles on
buffer occupancy and Kafka's pull model throttles on the consumer's own
poll cadence, watermark alignment throttles a source based on its
event-time progress relative to its peers, a signal orthogonal to both
buffer state and poll rate, and one that exists specifically because a
source can be buffer-healthy and poll-cadence-healthy while still racing
ahead of its peers in event time, a failure mode neither of the other two
mechanisms can see.

Event-Time Processing, the published sibling entry, is related only
transitively, through Watermark, and is not itself a backpressure mechanism.

Exactly-Once Processing, queued and being authored alongside this entry,
has a genuine, direct compositional dependency on this pattern, not merely
a thematic one, documented in Dynamics above. Flink's default aligned
checkpoint mode couples checkpoint duration to backpressure precisely
because a checkpoint barrier cannot overtake data already queued in a
backpressured channel, and the unaligned checkpoint mode exists
specifically to decouple the two.

Dead-Letter Topic, queued and being authored alongside this entry, is the
natural companion strategy named in Trade-off matrix above. when a
pipeline's downstream SLA genuinely cannot tolerate the propagation delay
backpressure introduces, routing excess data to a dead-letter sink instead
of letting the slowdown ripple upstream is the documented alternative.

Incompatible or in direct tension. fire-and-forget messaging, a system with
no acknowledgment or feedback channel from consumer to producer at all,
which is structurally incapable of participating in any backpressure
protocol, credit-based or otherwise, since there is no channel for a credit
or a demand signal to travel back on, the same incompatibility already
named in the sibling Backpressure entry's own frontmatter and repeated here
because it applies identically at this layer.

## 14. Refactoring path in and out

A team migrating a hand-rolled, unbounded-queue-based stream pipeline onto
Flink inherits credit-based flow control for free, since it is the
engine's default architecture rather than an opt-in setting, no explicit
migration step is required beyond adopting the DataStream API itself. The
genuine refactoring work begins once backpressure is first observed in
production, per the monitoring signals documented in Dynamics and
Observability signals. tune buffer pool sizing against the documented
formula if the pool is genuinely undersized for real throughput, and adopt
unaligned checkpoints or the alignment-timeout fallback if checkpoint
duration is coupling to throughput under sustained backpressure. The
network memory tuning page names a newer, more automatic alternative to
manual buffer-pool tuning directly. "If the amount of in-flight data is
causing issues, enabling buffer debloating is recommended," letting the
engine adjust its own buffer sizing dynamically rather than requiring a
human to compute the formula by hand.

The path out, away from this entry's specific mechanism, applies when a
team's actual need is a single-process, single-hop producer-consumer
relationship with no distributed shuffle to protect, in which case Flink's
whole distributed checkpoint-and-credit machinery is unnecessary weight,
and the general reactive-library mechanisms documented in the sibling
Backpressure entry are the right, simpler descope.

## 15. Testing and verification

Verifying that a pipeline's backpressure handling behaves as intended means
driving a subtask deliberately slow, an injected delay in one operator's
user function, an under-provisioned parallelism relative to a skewed key
distribution, and then observing the documented metrics respond as
expected. a genuinely backpressured subtask should show
backPressuredTimeMsPerSecond rising while its immediate upstream neighbors'
own busyTimeMsPerSecond correspondingly drops as they stall waiting on
credit, and the web UI's OK, LOW, HIGH classification should move from OK
toward HIGH specifically at the injected bottleneck and nowhere else in the
graph, confirming the propagation reaches exactly the subtasks it should
and does not falsely trigger elsewhere. Verifying the checkpoint-alignment
interaction specifically means measuring checkpoint duration under the
same injected slowdown with aligned checkpoints enabled, then again with
unaligned checkpoints enabled, and confirming the documented decoupling,
checkpoint duration becoming independent of current throughput, actually
holds in a real test run rather than only in the documentation. This
entry's own reasoning connects the sourced metrics from Dynamics to this
testing approach. Flink's documentation does not itself prescribe a named
test methodology, so the specific test setup shape here is inference, not a
directly quoted testing procedure.

## 16. Observability signals

Three per-subtask metrics, per Flink's own backpressure monitoring
documentation. backPressuredTimeMsPerSecond, idleTimeMsPerSecond, and
busyTimeMsPerSecond, summing to approximately 1000ms and refreshed on a
sampled, multi-second cadence, are the primary, first-class signal, and
the same page's web UI translates the backpressured ratio directly into
three named operational states, OK, zero to ten percent, LOW, ten to fifty
percent, and HIGH, fifty to one hundred percent, giving an operator a
single number to alert on rather than requiring manual interpretation of
the raw millisecond breakdown. Source. Apache Flink documentation, "Monitoring
Back Pressure," verified 2026-08-23,
https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/ops/monitoring/back_pressure/.
Checkpoint duration itself, tracked per Flink's own checkpointing
statistics, is a secondary but directly load-bearing signal for this
pattern specifically, since Dynamics above establishes that a rising
checkpoint duration under otherwise-stable state size is a documented,
mechanical consequence of sustained backpressure interacting with the
default aligned checkpoint mode, not a separate, unrelated failure.

## 17. Security and privacy implications

The credit and backlog counts the protocol exchanges between subtasks are
control-plane accounting values, buffer counts and queue depths, not
application payload data, so the protocol itself carries no direct data-
exposure risk. The genuine, indirect risk this entry's own reasoning
surfaces, not a directly documented warning, is resource exhaustion. a
custom or misconfigured source connector that does not properly participate
in the network stack's credit accounting, or an operator configuration that
disables the credit protocol's bounding effect through misconfigured
buffer pools, reopens the same unbounded, memory-exhaustion risk the whole
protocol exists to close, and the watermark-skew paper's own "significant
increase in state size to buffer in-flight data" language, already quoted
in Forces above, describes exactly this failure shape from the event-time
side of the same underlying concern.

## 18. References

Apache Flink. "A Deep-Dive [through] Flink's Network Stack." Verified
2026-08-23. https://flink.apache.org/2019/06/05/a-deep-dive-into-flinks-network-stack/.

Confluent documentation. "Kafka Consumer Design." Verified 2026-08-23.
https://docs.confluent.io/kafka/design/consumer-design.html.

Apache Flink documentation. "Network Memory Tuning Guide." Verified
2026-08-23.
https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/deployment/memory/network_mem_tuning/.

Apache Flink documentation. "Checkpointing." Verified 2026-08-23.
https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/datastream/fault-tolerance/checkpointing/.

Apache Flink documentation. "Monitoring Back Pressure." Verified 2026-08-23.
https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/ops/monitoring/back_pressure/.

Apache Flink. "Powered By Flink." Verified 2026-08-23.
https://flink.apache.org/what-is-flink/powered-by/.

Apache Flink documentation. "Generating Watermarks." Verified 2026-08-23.
https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/.

**Evidence grade.** medium-high.

Most solid findings. the credit protocol's mechanics, buffer defaults, the
monitoring metrics, and the checkpoint-alignment interaction are each
sourced to a direct, live-fetched quote from Flink's own current
documentation, verified 2026-08-23.

Unverified or unclear. the causal link between the two named production
deployments and credit-based flow control specifically, dimension 9, is
this entry's own reasoned inference from documented throughput figures, not
a direct company statement. the failure-mode claim about a slow external
call inside user code, dimension 11, and the testing methodology, dimension
15, are similarly this entry's own reasoning about the documented scope of
the protocol rather than directly quoted warnings or procedures. WebSearch
was unavailable for the session this entry was researched in, so source
discovery relied on direct WebFetch against known or reconstructed
canonical URLs rather than a search-assisted pass, and two guessed URLs, a
dedicated buffer-debloating page and an initial checkpointing-page guess,
returned 404 before the correct pages were located.

## Code examples

Minimal, illustrative simulations of the credit-based flow control protocol
described above. a fixed pool of credits per channel, a sender that only
transmits while credit remains, and a receiver that grants credit back as
it drains its buffer. These are teaching illustrations of the protocol's
shape, not a reimplementation of Flink's own network stack.

### TypeScript

```typescript
type FlowBuffer = { id: number };

class CreditChannel {
  private credits: number;
  private readonly capacity: number;
  private readonly pending: FlowBuffer[] = [];
  private backpressuredMs = 0;

  constructor(capacity: number) {
    this.capacity = capacity;
    this.credits = capacity;
  }

  send(buf: FlowBuffer): boolean {
    if (this.credits <= 0) {
      this.backpressuredMs += 1;
      return false;
    }
    this.credits -= 1;
    this.pending.push(buf);
    return true;
  }

  drain(): FlowBuffer | undefined {
    const buf = this.pending.shift();
    if (buf !== undefined && this.credits < this.capacity) {
      this.credits += 1;
    }
    return buf;
  }

  backlog(): number {
    return this.pending.length;
  }

  backpressuredTimeMs(): number {
    return this.backpressuredMs;
  }
}

function simulate(sourceRate: number, sinkRate: number, ticks: number): CreditChannel {
  const channel = new CreditChannel(8);
  let produced = 0;
  let consumed = 0;
  for (let tick = 0; tick < ticks; tick += 1) {
    for (let i = 0; i < sourceRate; i += 1) {
      if (channel.send({ id: produced })) {
        produced += 1;
      }
    }
    for (let i = 0; i < sinkRate; i += 1) {
      const buf = channel.drain();
      if (buf !== undefined) {
        consumed += 1;
      }
    }
  }
  return channel;
}
```

### Python

```python
from collections import deque
from dataclasses import dataclass


@dataclass
class Buffer:
    seq: int


class CreditChannel:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.credits = capacity
        self.pending: deque[Buffer] = deque()
        self.backpressured_ticks = 0

    def send(self, buf: Buffer) -> bool:
        if self.credits <= 0:
            self.backpressured_ticks += 1
            return False
        self.credits -= 1
        self.pending.append(buf)
        return True

    def drain(self) -> Buffer | None:
        if not self.pending:
            return None
        buf = self.pending.popleft()
        if self.credits < self.capacity:
            self.credits += 1
        return buf

    def backlog(self) -> int:
        return len(self.pending)


def simulate(source_rate: int, sink_rate: int, ticks: int) -> CreditChannel:
    channel = CreditChannel(capacity=8)
    produced = 0
    consumed = 0
    for _ in range(ticks):
        for _ in range(source_rate):
            if channel.send(Buffer(seq=produced)):
                produced += 1
        for _ in range(sink_rate):
            buf = channel.drain()
            if buf is not None:
                consumed += 1
    return channel
```

### Go

```go
package streambackpressure

type Buffer struct {
	Seq int
}

type CreditChannel struct {
	Capacity           int
	Credits            int
	Pending            []Buffer
	BackpressuredTicks int
}

func NewCreditChannel(capacity int) *CreditChannel {
	return &CreditChannel{Capacity: capacity, Credits: capacity}
}

func (c *CreditChannel) Send(buf Buffer) bool {
	if c.Credits <= 0 {
		c.BackpressuredTicks++
		return false
	}
	c.Credits--
	c.Pending = append(c.Pending, buf)
	return true
}

func (c *CreditChannel) Drain() (Buffer, bool) {
	if len(c.Pending) == 0 {
		return Buffer{}, false
	}
	buf := c.Pending[0]
	c.Pending = c.Pending[1:]
	if c.Credits < c.Capacity {
		c.Credits++
	}
	return buf, true
}

func (c *CreditChannel) Backlog() int {
	return len(c.Pending)
}

func Simulate(sourceRate, sinkRate, ticks int) *CreditChannel {
	channel := NewCreditChannel(8)
	produced := 0
	consumed := 0
	for tick := 0; tick < ticks; tick++ {
		for i := 0; i < sourceRate; i++ {
			if channel.Send(Buffer{Seq: produced}) {
				produced++
			}
		}
		for i := 0; i < sinkRate; i++ {
			_, ok := channel.Drain()
			if ok {
				consumed++
			}
		}
	}
	return channel
}
```
