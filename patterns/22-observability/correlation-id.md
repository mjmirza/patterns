---
name: Correlation ID
slug: correlation-id
family: 22-observability
category: Structural
aliases: [Request ID, Activity ID, Trace ID (informal usage)]
first_described: 'no single named originator; converged industry practice, formalized by the W3C Trace Context specification, 2020'
maturity: canonical
related: [correlation-identifier, structured-logging, span-and-trace-context-propagation]
incompatible_with: []
verified: 2026-08-22
---

# Correlation ID

## 1. Name, aliases, and lineage

Correlation ID. Also called Request ID in ad hoc header conventions, and Activity ID in Microsoft's own guidance for correlating distributed telemetry, which describes associating each request with a unique activity ID propagated through the system as part of the request context (https://learn.microsoft.com/en-us/azure/architecture/best-practices/monitoring).

This is a distinct pattern from the Correlation Identifier entry already catalogued under Enterprise Integration Patterns (patterns/07-integration/correlation-identifier.md), which solves a narrower problem, matching an asynchronous reply message to the original request message inside a messaging system. The Correlation ID pattern described here solves the broader observability problem of tracing one logical request end to end across every service, log line, and network hop it touches, whether or not any of those hops involve an asynchronous reply.

No single paper or engineer is credited with inventing the practice. It converged independently across companies operating distributed systems, then was formalized industry wide by the W3C Trace Context specification, which standardizes the header carrying the identifier as the traceparent field, containing a trace-id represented as a 16 byte array (https://www.w3.org/TR/trace-context/). Early production implementations predate the standard and still coexist with it, among them nginx's built in $request_id, a unique request identifier generated from 16 random bytes in hexadecimal (https://nginx.org/en/docs/http/ngx_http_core_module.html#var_request_id), and AWS X-Ray's own tracing header, where the first X-Ray integrated service that a request hits adds a trace ID and propagates it downstream (https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html).

## 2. Problem and context

A single request entering a distributed system rarely stays inside one process. It crosses a load balancer, an API gateway, several internal services, a database, a cache, and often a message queue, before a response is returned. Each of those hops writes its own log lines, and each log line, on its own, carries no information tying it back to the other hops that served the same logical request.

When something goes wrong, an engineer investigating an incident needs to answer one question first, which log lines, across which services, belong to this one failing request. Without a shared identifier threaded through every hop, that question can only be answered by correlating on approximate signals, a timestamp window, a user identifier, a source IP, none of which is reliable once traffic volume is more than trivial. The Correlation ID pattern solves exactly this problem. it generates a single identifier at, or before, the point a request enters the system, and propagates that same identifier through every downstream call and every log line the request produces, so the full path of one request can be reconstructed by a single query for one value.

## 3. Forces

- Generating and propagating an identifier is close to free in latency terms, a few bytes on the wire and a header lookup, but it must survive every hop, and a single service that drops or fails to forward it breaks the whole chain for that request.
- The identifier has to be genuinely unique across a large distributed system with many concurrent requests, without a central coordinator to hand out values, which pushes implementations toward random or pseudo random generation rather than a counter.
- Storing and indexing the identifier as a queryable log field carries a real, ongoing storage and query cost at scale, since it is present on effectively every log line the system produces.
- Because the identifier is deliberately written into logs, headers, and often returned to the client in error responses for support purposes, it must never be treated as a secret, and any value accepted from outside the system must be sanitized before it is written into a log line, since an unvalidated value can be used to inject content into the logs (https://owasp.org/www-community/attacks/Log_Injection).
- Different organizations, and different tracing vendors, converged on incompatible header names and identifier shapes before the W3C standardized one, which creates an interoperability force between legacy ad hoc conventions like X-Request-Id and the standardized traceparent header.

## 4. Applicability and non-applicability

### When it applies

Use a Correlation ID for any system where a single logical request is served by more than one process, whether that is a handful of microservices, a monolith fronted by a load balancer and a CDN, or a request that crosses into a background job or a message queue. It is close to a default requirement the moment more than one service can log about the same request, because the cost of adding it is small and the cost of debugging without it grows with the number of hops.

### When it does not apply (non-applicability)

Skip it, or treat it as unnecessary overhead, for a genuinely single process application with no network hops to correlate across, where every log line already comes from the same process and can be correlated by nothing more than the process's own log file. It is also not, by itself, a substitute for full distributed tracing. a Correlation ID alone tells you which log lines belong together, but it does not, on its own, capture the parent and child relationship between spans, their individual durations, or where time was actually spent inside the chain. That finer grained structure is the job of the related Span and Trace Context Propagation pattern in this same family, which a Correlation ID is often the simplest entry point into rather than a full replacement for.

## 5. Structure

- Identifier generator. produces a new value, almost always a random or pseudo random string such as a UUID or, in the W3C scheme, a 16 byte trace-id, at the point a request first enters the system.
- Inbound extraction step. checks whether an incoming request already carries an identifier from an upstream caller and, if it does, reuses that value instead of minting a new one, so one logical request keeps one identifier across every hop.
- Propagation carrier. the mechanism the identifier rides on between hops. an HTTP header such as traceparent or an ad hoc X-Request-Id, a message property on a queue, or an in process context object passed down a call stack.
- In process context store. holds the identifier for the duration of one request inside a single process so every log statement and every outbound call within that process can read it without it being passed explicitly as a function argument everywhere. commonly an async local storage, a thread local, or a context variable.
- Logging integration point. the piece of logging infrastructure, often a middleware or a logging filter, that reads the identifier out of the in process context and attaches it to every log line automatically.

## 6. ASCII structure diagram

```
  Request arrives at the edge
        |
        v
  Inbound extraction step
  (identifier present on the request?)
        |
   +----+----+
   |         |
  yes        no
   |         |
   v         v
  reuse it   Identifier generator mints a new value
   |         |
   +----+----+
        |
        v
  In process context store
  (holds the identifier for this request)
        |
        v
  Logging integration point   ---->   every log line carries the identifier
        |
        v
  Propagation carrier attaches the identifier
  to every downstream call (header, queue property, RPC metadata)
        |
        v
  Next service repeats the same extraction step
```

## 7. Dynamics

1. A request arrives at the system's edge, typically a load balancer, gateway, or the first service in the call chain.
2. The inbound extraction step checks the incoming request for an existing identifier, most commonly in an HTTP header. the W3C standard names this header traceparent and defines its trace-id field as a 16 byte array uniquely identifying the whole distributed trace (https://www.w3.org/TR/trace-context/).
3. If no identifier is present, the identifier generator mints a fresh one. AWS X-Ray documents this exact first hop behavior, stating that the first supported service that the HTTP request interacts with adds a trace ID header to the request and propagates it downstream (https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html).
4. The identifier is written into the in process context store for the lifetime of handling that request, so it is available without being threaded explicitly through every function call.
5. Every log line the service emits while handling the request is stamped with the identifier by the logging integration point, and every outbound call the service makes attaches the same identifier through the propagation carrier before the call leaves the process.
6. The next service in the chain repeats the same extraction step, reusing rather than replacing the identifier, so one logical request keeps exactly one identifier end to end, and every log line from every hop can later be found by a single query for that one value.

## 8. Implementation variants

- Single opaque identifier. one string, often a UUID or a random hex value, carried unchanged across every hop. Simple to implement and simple to query, but it cannot on its own distinguish which specific hop, or which specific span of work inside a hop, a given log line came from.
- Two part trace-id and span-id. the shape standardized by the W3C Trace Context specification and by OpenTelemetry, where a stable trace-id identifies the whole request and a fresh span-id is generated at each hop to identify that hop's own unit of work, with both a valid trace identifier defined as a 16 byte array and a valid span identifier as an 8 byte array (https://opentelemetry.io/docs/specs/otel/trace/api/). This variant keeps the single query benefit of the opaque identifier while also supporting per hop breakdown.
- Ad hoc header convention. a custom header such as X-Request-Id or X-Correlation-Id, generated and propagated by hand written middleware, predating and still common alongside the standardized traceparent header. Microsoft's own .NET guidance documents this as the older Hierarchical convention that transmits a custom request-id header, contrasted with the newer W3C scheme (https://learn.microsoft.com/en-us/dotnet/core/diagnostics/distributed-tracing-concepts).
- In process propagation without a header. inside a single process boundary, the identifier is carried through an async local storage, a thread local, or a context variable rather than a header, since there is no network hop to attach a header to. This variant is combined with one of the header based variants above the moment a network call actually leaves the process.
- Explicit message property on an asynchronous transport. when a hop is a message queue rather than a synchronous call, the identifier has to be attached as an explicit message property rather than an HTTP header, because a broker does not propagate in process context automatically, and a message creation context that is not attached and propagated with the message breaks correlation between the producer and the consumer traces (https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/).

## 9. Known production uses

- AWS X-Ray attaches its own trace ID to the X-Amzn-Trace-Id HTTP header at the first X-Ray integrated service a request hits, and propagates it through every downstream call in the request's path (https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html).
- nginx ships a built in $request_id variable, a unique request identifier generated from 16 random bytes in hexadecimal, available to every request nginx handles without any third party module (https://nginx.org/en/docs/http/ngx_http_core_module.html#var_request_id).
- The W3C Trace Context specification standardizes the traceparent header and its trace-id field as an interoperable identifier meant to be understood and propagated across tracing systems built by different vendors, rather than tied to any one company's tooling (https://www.w3.org/TR/trace-context/).
- Microsoft's Azure Architecture Center documents the same practice under the name activity ID, recommending that each request be associated with a unique activity ID propagated through the system as part of the request context so instrumentation data across services can be amalgamated (https://learn.microsoft.com/en-us/azure/architecture/best-practices/monitoring).

## 10. Consequences

### Benefits

- A single query for one identifier reconstructs the full, ordered path a request took across every service, closing the gap between logs that look unrelated and log lines that actually describe one incident.
- The cost of adding it is small, a header and a context lookup, against a debugging cost that otherwise grows with every additional service the request passes through.
- Once standardized on the W3C traceparent header, the identifier interoperates across tracing tools built by different vendors instead of locking a system into one vendor's proprietary header.

### Costs

- The identifier has to be threaded through every single hop by hand, or by shared middleware, and any one hop that is missed silently fragments the trace for every request that passes through it, with no error raised anywhere.
- Storing and indexing the identifier on effectively every log line is a real, ongoing storage and query cost that scales directly with request volume.
- An asynchronous boundary such as a message queue does not propagate the identifier automatically, so every team that introduces one has to remember to attach it explicitly, and this is a common place for propagation to quietly break (https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/).

## 11. Failure modes and misuse

- Propagation breaks silently across an asynchronous boundary, most often a message queue or a background job, because the identifier lives in an in process context that a worker picking up a queued message never automatically receives, and the OpenTelemetry messaging semantic conventions describe exactly this failure. consumer traces cannot be directly correlated with producer traces if the message creation context is not attached and propagated with the message (https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/).
- A service accepts an inbound identifier and writes it directly into a log line without sanitizing it first, which is a log injection vector. OWASP documents that writing invalidated user input to log files can allow an attacker to forge log entries or inject malicious content into the logs (https://owasp.org/www-community/attacks/Log_Injection), and an unsanitized correlation ID header is exactly this kind of invalidated input the moment it originates outside a trusted boundary.
- One service in the chain mints a brand new identifier instead of reusing the one it received, most often because its own instrumentation was added independently and never wired to the inbound header, which fragments what should be a single trace into two disconnected ones with no obvious symptom beyond an incomplete picture during the next incident.
- The identifier, or a value carried alongside it, is treated as if it were secret or as an authorization token. it is neither. it is deliberately written into logs, returned to end users in error messages for support purposes, and exposed in tracing dashboards, so anything that must stay confidential does not belong inside it or beside it.
- Extra business context, most often something that looks convenient to have on hand later, is embedded directly inside the identifier value itself rather than kept in a separate, purpose built field, which risks the identifier carrying personal data into every log line it touches. the general logging guidance on this point is that sensitive personal data is one of the categories that should usually not be recorded directly in logs (https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html), and an identifier is a log field like any other.

## 12. Trade-off matrix

| Dimension | Correlation ID alone | No shared identifier | Full span based distributed tracing |
|---|---|---|---|
| Reconstructs which log lines belong to one request | Yes, by a single value query | No, requires approximate correlation | Yes, plus per hop structure |
| Shows per hop timing and parent or child relationships | No | No | Yes |
| Implementation cost | Low, a header and a context lookup | None | Higher, needs a tracing backend and instrumentation |
| Storage and query cost at scale | Moderate, one indexed field | None | Higher, spans plus attributes per hop |
| Works across an asynchronous message queue hop | Only if the property is attached explicitly | Not applicable | Only if the property is attached explicitly |

## 13. Related and incompatible patterns

Related to the Correlation Identifier entry in the Enterprise Integration Patterns family (patterns/07-integration/correlation-identifier.md), which solves the narrower problem of matching an asynchronous reply message to its request inside a messaging system. a Correlation ID in the observability sense is often, in practice, carried as one of the fields inside that messaging pattern's own correlation value, but the two patterns solve different problems and neither implies the other.

Related to Structured Logging, since a Correlation ID is only useful once it is written as a consistently named field on every log line, which structured logging is what makes queryable in the first place rather than buried in free text.

Related to Span and Trace Context Propagation, which extends the single opaque identifier described here into the two part trace-id and span-id shape, adding per hop structure and parent or child relationships that a bare Correlation ID does not carry on its own.

Not incompatible with anything in this catalog. it is close to a prerequisite for effective observability in any system with more than one service, rather than a pattern in tension with an alternative.

## 14. Refactoring path in and out

To introduce it into a system that does not have one yet, start at the single edge point where all external traffic enters, a load balancer, gateway, or the first internal service, and add middleware there that extracts an inbound identifier if one exists or mints a fresh one if it does not. Next, wire that middleware's output into the service's logging integration point so every log line the service emits carries the identifier automatically, rather than relying on each call site to remember to include it. Then, extend the same middleware pattern to every other service in the chain, always preferring to reuse an inbound identifier over minting a new one. Last, and often skipped, explicitly wire propagation across any asynchronous boundary, attaching the identifier as a message property before publishing and reading it back out before processing, since this hop will not carry the identifier automatically.

Removing it entirely is rare, because the ongoing cost is low relative to the debugging value, but a team replacing it with full span based distributed tracing typically keeps the same identifier as the trace-id inside the newer scheme rather than discarding it, since OpenTelemetry's own trace-id is defined the same way a Correlation ID already is, a value uniquely identifying the whole request (https://opentelemetry.io/docs/specs/otel/trace/api/), which makes the migration additive rather than a rip and replace.

## 15. Testing and verification

Unit test the identifier generator directly for uniqueness and for producing a value in the expected shape, whether that is a UUID or a 16 byte hex value, so a regression in the generator itself is caught before it reaches production. Write an integration test that sends a request through two or more services and asserts the same identifier value appears in every service's log output for that one request, which is the actual behavior the pattern exists to guarantee and the one most likely to silently regress when a service is added or refactored. Add a specific test for the inbound extraction step, asserting that a request carrying an existing identifier reuses it rather than generating a new one, since this is the exact behavior that fragments traces when it is missing. Add a security focused test asserting that a malformed or deliberately malicious inbound identifier value, for example one containing control characters, is either rejected or sanitized before it is written into a log line, directly exercising the log injection failure mode.

## 16. Observability signals

Every log line should carry the identifier as a consistently named, indexed field, which is the entire point of the pattern and the thing every other signal below depends on. Track a metric counting requests whose log lines are missing the identifier field entirely, since a rising count of missing identifiers is the earliest, most direct signal that propagation has broken somewhere in the chain, well before anyone notices during an actual incident. In a tracing backend such as AWS X-Ray's own console or a Jaeger style UI, the identifier is the primary lookup key an engineer types in to pull up every event associated with one request, so verify during any incident review that this lookup actually returns a complete picture rather than a partial one with gaps at a specific service.

## 17. Security and privacy implications

Treat the identifier as public by default, since it is deliberately written into logs, propagated in plain HTTP headers, and often returned to end users in error responses so a support engineer can look it up. it must never be used as, or confused with, an authorization token, a session identifier, or anything else that grants access on its own, because nothing about its design assumes confidentiality. Sanitize any inbound identifier value before writing it into a log line or forwarding it downstream, since an unvalidated value accepted from outside the trust boundary is a documented log injection vector, and OWASP's guidance on this class of attack is to perform sanitization on all event data to prevent log injection attacks such as carriage return and line feed characters (https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html). Keep personal data out of the identifier value itself. it is a log field like any other, and the general guidance that sensitive personal data should usually not be recorded directly in logs (https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) applies to it the same as any other field a system writes on every request.

## 18. References

1. W3C Trace Context specification. Defines the trace-id and the traceparent HTTP header format. https://www.w3.org/TR/trace-context/, verified 2026-08-22.
2. AWS X-Ray Developer Guide, concepts page. Describes the trace ID generated at the first integrated service and propagated downstream via the X-Amzn-Trace-Id header. https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html, verified 2026-08-22.
3. nginx core module documentation, $request_id variable. A built in, production, per request identifier generated from 16 random bytes. https://nginx.org/en/docs/http/ngx_http_core_module.html#var_request_id, verified 2026-08-22.
4. OpenTelemetry Tracing API specification. Canonical definitions of a valid trace identifier and a valid span identifier. https://opentelemetry.io/docs/specs/otel/trace/api/, verified 2026-08-22.
5. OpenTelemetry Semantic Conventions, messaging spans. Documents that consumer traces cannot be correlated with producer traces unless the message creation context is explicitly attached and propagated with the message. https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/, verified 2026-08-22.
6. OWASP Community, Log Injection. Describes forging or injecting content into log files via invalidated input. https://owasp.org/www-community/attacks/Log_Injection, verified 2026-08-22.
7. OWASP Cheat Sheet Series, Logging Cheat Sheet. Sanitization guidance for event data before logging, and the categories of sensitive data that should usually not be recorded in logs. https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html, verified 2026-08-22.
8. Microsoft Learn, .NET distributed tracing concepts. Contrasts the older custom request-id header convention with the W3C traceparent scheme. https://learn.microsoft.com/en-us/dotnet/core/diagnostics/distributed-tracing-concepts, verified 2026-08-22.
9. Microsoft Learn, Azure Architecture Center, monitoring and diagnostics guidance. Documents the activity ID terminology for the same correlation practice. https://learn.microsoft.com/en-us/azure/architecture/best-practices/monitoring, verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The W3C Trace Context header format and byte lengths (source 1, 4) are quoted directly from the live specification text. The log injection and sanitization guidance (source 6, 7) comes straight from OWASP's own reference pages. The async boundary failure mode (source 5) is quoted from the authoritative OpenTelemetry semantic conventions rather than a secondary blog post.

**Unverified or unclear.** The historical lineage in dimension 1 is stated honestly as having no single named originator, since no primary source pinning the very first production use of a request correlation identifier was found and verified in this pass. If an earlier, citable origin, for example an early distributed tracing paper, is later confirmed, dimension 1 should be revised to name it.

## Code examples

### TypeScript, in process propagation via async local storage

```typescript
import {AsyncLocalStorage} from "node:async_hooks";
import {randomUUID} from "node:crypto";

interface RequestContext {
  correlationId: string;
}

const correlationStorage = new AsyncLocalStorage<RequestContext>();

function extractOrGenerateCorrelationId(inboundHeader: string | undefined): string {
  if (inboundHeader && /^[a-zA-Z0-9-]{8,64}$/.test(inboundHeader)) {
    return inboundHeader;
  }
  return randomUUID();
}

function handleRequest(inboundHeader: string | undefined, work: () => void): void {
  const correlationId = extractOrGenerateCorrelationId(inboundHeader);
  correlationStorage.run({correlationId}, work);
}

function logLine(message: string): void {
  const context = correlationStorage.getStore();
  const id = context ? context.correlationId : "none";
  console.log(`correlation_id=${id} message=${message}`);
}

handleRequest("caller-supplied-id-123", () => {
  logLine("processing request");
});
```

### Python, propagation via contextvars

```python
import contextvars
import re
import uuid

correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id")

VALID_ID = re.compile(r"^[a-zA-Z0-9-]{8,64}$")


def extract_or_generate(inbound_header):
    if inbound_header and VALID_ID.match(inbound_header):
        return inbound_header
    return str(uuid.uuid4())


def handle_request(inbound_header, work):
    correlation_id = extract_or_generate(inbound_header)
    token = correlation_id_var.set(correlation_id)
    try:
        work()
    finally:
        correlation_id_var.reset(token)


def log_line(message):
    correlation_id = correlation_id_var.get("none")
    print(f"correlation_id={correlation_id} message={message}")


handle_request(None, lambda: log_line("processing request"))
```

### Go, propagation via context.Context

```go
package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"regexp"
)

type correlationKey struct{}

var validID = regexp.MustCompile(`^[a-zA-Z0-9-]{8,64}$`)

func extractOrGenerate(inboundHeader string) string {
	if inboundHeader != "" && validID.MatchString(inboundHeader) {
		return inboundHeader
	}
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func handleRequest(ctx context.Context, inboundHeader string, work func(context.Context)) {
	correlationID := extractOrGenerate(inboundHeader)
	ctx = context.WithValue(ctx, correlationKey{}, correlationID)
	work(ctx)
}

func logLine(ctx context.Context, message string) {
	id, ok := ctx.Value(correlationKey{}).(string)
	if !ok {
		id = "none"
	}
	fmt.Printf("correlation_id=%s message=%s", id, message)
}

func main() {
	handleRequest(context.Background(), "", func(ctx context.Context) {
		logLine(ctx, "processing request")
	})
}
```
