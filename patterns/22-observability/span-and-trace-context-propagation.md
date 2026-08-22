---
name: Span and Trace Context Propagation
slug: span-and-trace-context-propagation
family: 22-observability
category: Structural
aliases: [Trace Propagation]
first_described: 'no single named originator; converged industry practice, standardized by the W3C Trace Context specification, 2020, and implemented by OpenTelemetry'
maturity: canonical
related: [correlation-id, structured-logging, red-method, use-method]
incompatible_with: []
verified: 2026-08-22
---

# Span and Trace Context Propagation

## 1. Name, aliases, and lineage

Span and Trace Context Propagation. Also called Trace Propagation when referring specifically to how the context moves between processes, and closely related to the wider practice of Distributed Tracing.

No single paper or engineer is credited with inventing it. It converged across companies building distributed systems, then was formalized industry wide two ways. one way, by OpenTelemetry, which defines a span as the building block of a trace, carrying a name, a parent span ID, start and end timestamps, a span context, attributes, events, links, and a status (https://opentelemetry.io/docs/concepts/signals/traces/), and on the wire, by the W3C Trace Context specification, which standardizes the traceparent header that carries a span's identity from one process to the next.

## 2. Problem and context

A Correlation ID ties every log line from one request together with a single flat value, which answers which log lines belong to this request, but not which specific hop inside that request was slow, or how the work fanned out across parallel calls. When a request touches five services and the overall response is slow, a flat identifier tells an engineer the request was slow, not which one of the five services actually caused it.

Span and Trace Context Propagation solves this by giving each unit of work its own record, a span, with its own start time, end time, and identity, and by explicitly linking each span to the span that caused it, its parent. The result is a tree, or in more complex cases a graph, of spans sharing one trace, so an engineer can see not only that a request was slow but exactly which hop, out of however many the request touched, accounted for the time.

## 3. Forces

- A span per hop gives per-hop attribution that a single flat identifier cannot, but it costs more to create, export, and store than one identifier per request, since a request touching many services now produces many linked records instead of one.
- The W3C Trace Context specification standardizes the wire format so different vendors' tracing tools can interoperate, defining the traceparent header's trace-id, parent-id, and trace-flags fields, and requiring that a vendor receiving a traceparent header pass it on to every outgoing request it makes (https://www.w3.org/TR/trace-context/).
- A span, by the model most tracing systems use, can only have one parent, which is a real limitation for an asynchronous system where a message may be consumed by many downstream processes or none, so OpenTelemetry's own messaging conventions explain that a message creation context is correlated to its consumers through span links rather than strict parent child relationships specifically because it is the only consistent trace structure that can be guaranteed (https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/).
- Recording every single span for every single request is expensive at real traffic volumes, which pushes systems toward sampling, and OpenTelemetry itself frames the resulting tradeoff plainly, head sampling decides early and is efficient but it is not possible to make a sampling decision based on data in the entire trace, while tail sampling considers the whole trace and can guarantee capturing every error, at the cost of needing stateful systems that can accept and store a large amount of data first (https://opentelemetry.io/docs/concepts/sampling/).
- Spans are timestamped by the clocks of the hosts that created them, and those clocks drift relative to each other, which Jaeger's own documentation names directly, a server span may appear to start earlier than the client span, which should not be possible, purely because of clock skew between hosts (https://www.jaegertracing.io/docs/2.dev/deployment/configuration/).

## 4. Applicability and non-applicability

### When it applies

Use this pattern for any distributed system where knowing which specific hop caused a slowdown matters, not only which request was slow, and especially where a request fans out across several services whose individual timing needs to be visible on its own. It is the structure a RED Method Duration dashboard depends on when an engineer needs to move from a whole service's aggregate latency down to the one call that actually explains a specific slow request.

### When it does not apply (non-applicability)

Skip it, or stay with a plain Correlation ID, for a system with only one or two hops, where a flat identifier already answers every question an engineer would ask, and the extra cost of creating, exporting, and storing a full span tree buys close to nothing. It also does not fit cleanly onto a broadcast style fan-out, where one message reaches many independent, unrelated consumers with no single owning parent, a shape span links exist specifically to handle rather than the strict, single parent tree this pattern assumes by default.

## 5. Structure

- Span. one unit of work, carrying a name, a start and end timestamp, a parent span ID, a span context, attributes, events, links, and a status (https://opentelemetry.io/docs/concepts/signals/traces/).
- Trace. the full set of spans that share one trace-id, forming a tree in the simple case, or, as Jaeger's own documentation describes it, a directed acyclic graph in the general case (https://www.jaegertracing.io/docs/latest/).
- traceparent header. the W3C standardized carrier for a span's identity across a network hop, four fields, version, trace-id, parent-id, trace-flags (https://www.w3.org/TR/trace-context/).
- Baggage. a companion, independent specification for propagating arbitrary key-value context alongside, but not part of, the trace context itself, explicitly scoped as usable regardless of whether distributed tracing is used at all (https://www.w3.org/TR/baggage/).
- Span links. the mechanism used when a strict single parent relationship does not fit, most often across an asynchronous or message queue boundary.
- Tracing backend. the system that collects exported spans and assembles them by trace-id and parent references into a viewable trace, Jaeger being one named example.

## 6. ASCII structure diagram

```
  Root span, trace-id T
  (parent-id: none)
        |
        v
  traceparent header sent downstream
  (version-T-<root span id>-flags)
        |
        v
  Service B extracts context
  starts child span, trace-id T, parent-id = root span id
        |
        v
  traceparent header sent further downstream
  (version-T-<child span id>-flags)
        |
        v
  Service C extracts context
  starts grandchild span, trace-id T, parent-id = child span id
        |
        v
  All spans exported, assembled by trace-id
  into one trace tree in the backend
```

## 7. Dynamics

1. A request arrives at the edge of the system, and a root span is started, minting a new trace-id since no inbound traceparent header exists yet.
2. Before the service makes its own outbound call, it writes a traceparent header onto that outgoing request, with the root span's own ID placed in the parent-id field, exactly the rewriting behavior the W3C specification requires, the value of property parent-id must be set to a value representing the ID of the current operation (https://www.w3.org/TR/trace-context/).
3. The next service receives the request, extracts the inbound traceparent header, and starts a new span whose parent is the parent-id it read from that header, inheriting the same trace-id. OpenTelemetry's own instrumentation guidance describes this exact mechanic, if the current context already contains a span inside of it, creating a new span makes it a nested span (https://opentelemetry.io/docs/languages/go/instrumentation/).
4. This repeats at every hop, each service extracting the context it received, starting its own child span, and rewriting the header before its own outbound calls.
5. If a hop is asynchronous, a message published to a queue rather than a synchronous call, the message creation context is attached to the message itself rather than an HTTP header, and the consumer correlates back to it using a span link rather than a strict parent, since a span can only have a single parent and a queued message may have many consumers or none (https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/).
6. Every span, once it completes, is exported to a tracing backend, which groups every span sharing one trace-id and renders them as a tree, or a graph where links are involved, giving a single view of the whole request across every service it touched.

## 8. Implementation variants

- OpenTelemetry SDK based propagation. the canonical implementation, where the SDK reads and writes the traceparent header automatically through instrumentation, and application code mainly deals with starting and naming spans rather than the wire format directly.
- W3C Baggage alongside trace context. arbitrary key-value context propagated on every hop independent of tracing itself, usable even in a system that has not adopted distributed tracing at all (https://www.w3.org/TR/baggage/).
- Span links for asynchronous and fan-in relationships. the variant used wherever the strict single parent model does not fit, a message queue, a batch job pulling from many sources, or any case where one span's work is caused by more than one predecessor.
- A directed acyclic graph representation in the backend. Jaeger explicitly represents traces this way rather than as a strict tree, so a span with more than one predecessor, connected through links, still renders correctly (https://www.jaegertracing.io/docs/latest/).

## 9. Known production uses

- OpenTelemetry is the industry standard implementation of spans and trace context propagation, defining the span data model and the SDK behavior that reads and writes the W3C traceparent header across a wide range of languages and frameworks (https://opentelemetry.io/docs/concepts/signals/traces/).
- Jaeger, a CNCF project, is a named, real backend that collects exported spans and renders them as a directed acyclic graph, explicitly built to represent trace structures beyond a simple tree (https://www.jaegertracing.io/docs/latest/).
- The W3C Trace Context specification itself is adopted across tracing vendors as the interoperable wire format, so a trace started by one vendor's instrumentation can be correctly continued by another's (https://www.w3.org/TR/trace-context/).

## 10. Consequences

### Benefits

- Latency is attributable to the exact hop that caused it, not only the request as a whole, closing the gap a flat Correlation ID cannot close on its own.
- The full call tree of one request becomes visible in a single view, showing fan-out, parallelism, and sequencing that a flat log correlation never reveals.
- The W3C standardized wire format lets a trace move correctly across tools built by different vendors, rather than locking a system into one vendor's proprietary propagation format.

### Costs

- Creating, exporting, and storing a span per hop costs more than a single flat identifier per request, and that cost scales with both traffic volume and the number of hops each request touches.
- The single parent limitation of the basic span model forces an extra mechanism, span links, wherever the real relationship is not a strict tree, adding a second concept an instrumenting engineer has to understand correctly.
- Clock skew between the hosts that create different spans in the same trace can make the trace's own timeline look impossible, and correcting it automatically is itself a real, debated engineering problem, not a solved one.

## 11. Failure modes and misuse

- Trace context is not propagated across an asynchronous boundary, most often a message queue, because the receiving worker never automatically inherits the in process context the way a synchronous HTTP call would, producing an orphaned span with no connection back to the trace that caused it, exactly the failure OpenTelemetry's messaging conventions describe and the reason span links exist as the fix (https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/).
- A fan-in or broadcast relationship is forced into the strict single parent model instead of using span links, silently dropping every predecessor but one, or producing a tree structure that does not actually describe what happened.
- Head based sampling drops the one trace that actually mattered, an error, before its full shape was ever known, since a head sampling decision is made early and cannot see the rest of the trace, exactly the limitation OpenTelemetry names directly (https://opentelemetry.io/docs/concepts/sampling/).
- Uncorrected clock skew between hosts makes a child span appear to start before its own parent, corrupting the trace's visual and logical ordering, a real, documented condition Jaeger addresses with a configurable clock skew correction feature (https://www.jaegertracing.io/docs/2.dev/deployment/configuration/). Even that correction is not free of its own problems, a real engineering discussion on the Jaeger project's own issue tracker argues the correction feature can misfire, since it relies on an undocumented tag to detect distinct hosts and assumes a child span's duration is always shorter than its parent's, an assumption that does not always hold (https://github.com/jaegertracing/jaeger/issues/1459). This second point is engineering judgement drawn from a real, cited discussion, not a settled fact.
- Baggage is used to carry a large or sensitive value, forgetting that it is deliberately propagated to every downstream hop by design, whether or not that hop actually needs it.

## 12. Trade-off matrix

| Dimension | Span and Trace Context Propagation | Correlation ID alone | Structured Logging with no tracing |
|---|---|---|---|
| Attributes latency to a specific hop | Yes | No, whole request only | No |
| Shows fan-out and parallel structure | Yes | No | No |
| Implementation and storage cost | Higher, span per hop | Lower, one value per request | Lower, no propagated identity beyond the log fields |
| Works across an asynchronous boundary | Yes, via span links, needs explicit wiring | Yes, if propagated explicitly | Not applicable |
| Standardized, interoperable wire format | Yes, W3C Trace Context | No formal standard | Not applicable |

## 13. Related and incompatible patterns

Related to Correlation ID, which this pattern extends rather than replaces. the trace-id inside a traceparent header serves the same request-tying role a flat Correlation ID serves, with the added structure of parent and child spans on top.

Related to Structured Logging, since every span, once exported, is itself a structured record, and log lines emitted during a span are commonly stamped with that span's trace-id and span-id so logs and traces can be cross-referenced.

Related to the RED Method and the USE Method, since a tracing backend's per-span duration data is exactly what a RED dashboard's Duration signal needs when an engineer has to move from an aggregate service level number down to the one hop responsible for a specific slow request.

Not incompatible with anything in this catalog. it is the structured, deeper form of request correlation, most valuable once a system has outgrown what a flat Correlation ID alone can show.

## 14. Refactoring path in and out

To introduce it into a system that only has a flat Correlation ID today, start by adopting the OpenTelemetry SDK at the edge of the system, letting its instrumentation start the root span and write the traceparent header automatically rather than hand rolling the wire format. Propagate that header through every internal call, HTTP middleware, RPC interceptors, and anywhere else a request crosses a process boundary, so every hop extracts the inbound context and creates a properly parented child span. Explicitly wire span links across any message queue or other asynchronous boundary, since that hop will never propagate context automatically the way a synchronous call does. Only then add a tracing backend such as Jaeger to collect and visualize the result, since the propagation discipline matters more than the visualization tool chosen on top of it.

Removing it entirely is rare for a system carrying real traffic across more than a couple of hops, since the debugging value it provides scales with exactly the complexity that makes it expensive to remove. A team that genuinely never needs per-hop attribution, and only ever asks which request rather than which hop, may reasonably fall back to a flat Correlation ID and drop the span level instrumentation, trading detail for a lower ongoing cost.

## 15. Testing and verification

Assert that a child span's trace-id always matches its parent's trace-id, and that its parent-id field genuinely references the span that caused it, across a real call between two services, not only within one process. Assert that the traceparent header is correctly rewritten on every outbound call a service makes, with the outgoing parent-id set to the current span's own ID rather than left unchanged from what was received. Add a specific regression test for the asynchronous boundary, publishing a message and asserting the consumer's span carries a link back to the producer's span rather than starting an orphaned, disconnected trace. Test the sampling policy directly, sending a known mix of successful and failing requests and asserting the failing ones are never dropped, whichever sampling strategy is configured.

## 16. Observability signals

Watch for spans arriving at the backend with no matching parent found, since a rising count of orphaned spans is a direct, early signal that propagation has broken somewhere in the system, often at exactly the kind of asynchronous boundary this pattern's own failure modes describe. Watch the ratio of sampled to total requests against the configured sampling policy, to confirm the system is actually capturing the traces it was configured to capture rather than silently sampling far less than intended. Watch per-span duration distributions within a trace, since this is the signal that closes the loop with the RED Method, turning a whole service's aggregate Duration number into the one specific hop that actually explains a slow request.

## 17. Security and privacy implications

Span attributes and Baggage values are, like a Correlation ID, exported broadly and often reach a third party tracing backend, so the same discipline applies, treat them as non-secret by default and never embed a token, a password, or unfiltered personal data directly in either. Baggage deserves an extra degree of caution beyond a regular span attribute, since it is propagated to every downstream hop by design, whether or not that hop actually needs the value, so anything placed in Baggage reaches services that may never have asked for it and may not expect to receive it. This extended caution around Baggage specifically is engineering judgement built on the same general principle a Correlation ID already carries, not a claim drawn from a source naming Baggage's own privacy risk directly.

## 18. References

1. OpenTelemetry documentation, traces concepts. Defines a span's own components, name, parent span ID, start and end timestamps, attributes, events, links, and status, and defines a trace as the path of a request through a system. https://opentelemetry.io/docs/concepts/signals/traces/, verified 2026-08-22.
2. OpenTelemetry documentation, Go instrumentation. Describes how a new span becomes a nested, child span when created from a context that already carries a parent span. https://opentelemetry.io/docs/languages/go/instrumentation/, verified 2026-08-22.
3. W3C Trace Context specification. Defines the traceparent header's four fields and the requirement that the parent-id be rewritten to the current span's own ID before an outgoing request. https://www.w3.org/TR/trace-context/, verified 2026-08-22.
4. W3C Baggage specification. Defines Baggage as a companion, independent mechanism for propagating arbitrary key-value context, usable even without distributed tracing. https://www.w3.org/TR/baggage/, verified 2026-08-22.
5. Jaeger documentation. Describes representing traces as directed acyclic graphs rather than strict trees, to support relationships beyond a single parent. https://www.jaegertracing.io/docs/latest/, verified 2026-08-22.
6. OpenTelemetry Semantic Conventions, messaging spans. Explains why span links, not strict parent child relationships, correlate producers and consumers across an asynchronous messaging boundary. https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/, verified 2026-08-22.
7. OpenTelemetry documentation, sampling. Defines the head versus tail sampling tradeoff, early and efficient but incomplete against complete but stateful and costly. https://opentelemetry.io/docs/concepts/sampling/, verified 2026-08-22.
8. Jaeger documentation, deployment configuration. Documents the clock skew problem between hosts and the configurable correction feature Jaeger uses for it. https://www.jaegertracing.io/docs/2.dev/deployment/configuration/, verified 2026-08-22.
9. Jaeger project, GitHub issue 1459. A real engineering discussion on the pitfalls of the automatic clock skew correction feature, used here as a cited caution rather than a settled fact. https://github.com/jaegertracing/jaeger/issues/1459, verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The span data model and the traceparent rewriting mechanic (source 1, 3) are quoted directly from OpenTelemetry's own concepts documentation and the live W3C specification text. The async boundary failure mode and its span link fix (source 6) come from the authoritative OpenTelemetry semantic conventions rather than a secondary blog post. The clock skew problem is sourced from Jaeger's own documentation of its correction feature, and the caution about that correction's own limits is sourced from a real, live engineering discussion on the project's own issue tracker rather than invented.

**Unverified or unclear.** The exact year distributed tracing as a discipline first emerged, and the specific origin of the span-as-a-tree model before OpenTelemetry standardized it, were not independently confirmed with a live, dated source in this research pass, so dimension 1 states honestly that no single named originator is claimed. The Baggage-specific privacy caution in dimension 17 is stated as engineering judgement extending the Correlation ID pattern's own general privacy guidance, since no source naming Baggage's privacy risk directly was found and verified in this pass.

## Code examples

### Go, span creation and traceparent style propagation

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
)

type spanContext struct {
	traceID  string
	spanID   string
	parentID string
}

func newRootSpan() spanContext {
	return spanContext{traceID: randomHex(16), spanID: randomHex(8), parentID: ""}
}

func newChildSpan(parent spanContext) spanContext {
	return spanContext{traceID: parent.traceID, spanID: randomHex(8), parentID: parent.spanID}
}

func traceparentHeader(ctx spanContext) string {
	return fmt.Sprintf("00-%s-%s-01", ctx.traceID, ctx.spanID)
}

func randomHex(n int) string {
	b := make([]byte, n)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func main() {
	root := newRootSpan()
	fmt.Println("outbound header:", traceparentHeader(root))
	child := newChildSpan(root)
	fmt.Println("child trace id matches root:", child.traceID == root.traceID)
}
```

### Python, a minimal span tree

```python
import secrets
from dataclasses import dataclass, field


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: str | None
    name: str
    children: list["Span"] = field(default_factory=list)


def new_root_span(name):
    return Span(trace_id=secrets.token_hex(16), span_id=secrets.token_hex(8), parent_id=None, name=name)


def new_child_span(parent, name):
    child = Span(trace_id=parent.trace_id, span_id=secrets.token_hex(8), parent_id=parent.span_id, name=name)
    parent.children.append(child)
    return child


root = new_root_span("http.request")
child = new_child_span(root, "db.query")
print(child.trace_id == root.trace_id, child.parent_id == root.span_id)
```

### TypeScript, extracting and rewriting a traceparent header

```typescript
interface TraceParent {
  version: string;
  traceId: string;
  parentId: string;
  flags: string;
}

function parseTraceparent(header: string): TraceParent {
  const [version, traceId, parentId, flags] = header.split("-");
  return {version, traceId, parentId, flags};
}

function childSpanHeader(inbound: TraceParent, newSpanId: string): string {
  return `${inbound.version}-${inbound.traceId}-${newSpanId}-${inbound.flags}`;
}

const inboundHeader = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01";
const parsed = parseTraceparent(inboundHeader);
const outboundHeader = childSpanHeader(parsed, "a1b2c3d4e5f60718");
console.log(outboundHeader);
```
