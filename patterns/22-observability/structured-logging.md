---
name: Structured Logging
slug: structured-logging
family: 22-observability
category: Structural
aliases: [Key-Value Logging, JSON Logging (a common concrete shape)]
first_described: 'no single named originator; converged industry practice, reflected in language standard libraries such as Go log/slog, added in Go 1.21, 2023'
maturity: canonical
related: [correlation-id, red-method, use-method]
incompatible_with: []
verified: 2026-08-22
---

# Structured Logging

## 1. Name, aliases, and lineage

Structured Logging. Also called Key-Value Logging, since every log record is a set of named fields rather than a sentence, and often called JSON Logging in casual use, though JSON is only the most common concrete serialization of the idea rather than the pattern itself.

No single paper or engineer is credited with inventing it. It converged across languages and companies as logging volume grew past what a human reading a terminal could parse by eye. Its current, canonical statement lives in language standard libraries themselves rather than a single manifesto. Go's log/slog package, added to the standard library in Go 1.21, states its own purpose directly. it provides structured logging, in which log records include a message, a severity level, and various other attributes expressed as key-value pairs (https://pkg.go.dev/log/slog). Rust's tracing crate frames the same idea for its own ecosystem, describing its spans as structured, with the ability to record typed data as well as textual messages (https://docs.rs/tracing/latest/tracing/).

## 2. Problem and context

A traditional log line is a sentence written for a human eye, something like a request failed for user 42 after 300 milliseconds. That sentence is easy to read in isolation, and close to impossible to query reliably at scale. Finding every failed request for user 42 across a week of logs, or computing the average latency across a million such lines, means writing a fragile regular expression against a phrasing that a future code change can silently break.

Structured Logging replaces the sentence with a set of named fields, message equals request failed, user equals 42, duration_ms equals 300, so a machine can query, filter, and aggregate on any field directly, without parsing prose. The problem it solves is exactly this gap between what reads well to a person glancing at one line and what can be reliably queried across millions of lines by a system built for that purpose.

## 3. Forces

- A structured record is easier for a machine to query and aggregate, but a raw structured line, especially JSON, is harder for a person to read directly in a terminal than a well written sentence, which pushes teams toward tooling that reformats structured output for human display.
- Field names have to stay consistent across every service that emits them, or a query for one field silently misses records from a service that named the same concept differently, which is exactly the problem the OpenTelemetry semantic conventions exist to solve, stating that a common naming scheme standardized across a codebase, libraries, and platforms allows easier correlation and consumption of data (https://opentelemetry.io/docs/specs/semconv/).
- Every additional field adds real, ongoing ingestion and storage cost at scale, and unmanaged log volume can grow into an unmanageable cost, which is why Datadog's own guidance on high volume logs recommends routing log data at the earliest possible points in the pipeline, ideally at the edge, to avoid unnecessary cost (https://www.datadoghq.com/blog/optimize-high-volume-logs/).
- A field whose value has very many distinct possibilities, a user identifier or a request identifier, is exactly the kind of field that breaks a system built around indexing a bounded set of values, since a field with an effectively unbounded set of distinct values can push indexing and storage cost up with no natural ceiling as it grows.
- Because a structured field is deliberately made easy to query and export, sensitive data written into one is far easier to find and extract at scale than the same data buried in free text, which raises the stakes on the same sanitization discipline general logging guidance already calls for around session identifiers, access tokens, and personal data (https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

## 4. Applicability and non-applicability

### When it applies

Use Structured Logging for any service whose logs are aggregated, searched, or alerted on by a system rather than read one line at a time by a person, which in practice describes almost every production service running at more than a handful of requests. It is close to a prerequisite for effective observability, since the RED and USE method patterns elsewhere in this family both depend on being able to query log data reliably by field, not by parsing prose.

### When it does not apply (non-applicability)

Skip it, or treat it as unnecessary overhead, for a small, throwaway script or a local development tool whose only reader is a person tailing a terminal on their own machine, where a plain, well phrased sentence is faster to write and faster to read than a JSON object, and there is no aggregation system on the other end to benefit from the structure.

## 5. Structure

- Log record. the unit emitted per event, carrying a message, a severity level, a timestamp, and a set of named attributes.
- Structured logger. the library call site that constructs a log record from a message and a set of key-value pairs, rather than a formatted sentence, examples include Go's log/slog and Rust's tracing.
- Serialization format. the concrete shape a record is written in, most often one JSON object per line, following the JSON Lines convention (https://jsonlines.org/), or a lighter key equals value format such as the logfmt style Stripe uses for its own canonical log lines (https://stripe.com/blog/canonical-log-lines).
- Field naming convention. the shared agreement across services on what a given concept is called, so the same field means the same thing everywhere it appears, formalized industry wide by the OpenTelemetry semantic conventions.
- Ingestion and query pipeline. the downstream system that parses each structured record, indexes its fields, and answers queries and aggregations against them.

## 6. ASCII structure diagram

```
  Application code
        |
        v
  Structured logger call
  (message + key-value attributes)
        |
        v
  Serialization format
  (one JSON object, or one logfmt line, per record)
        |
        v
  Ingestion and query pipeline
  (parses each line, indexes fields)
        |
        v
  Query by field  ---->  "every record where status=500 and service=checkout"
```

## 7. Dynamics

1. Application code calls the structured logger with a short message and a set of named attributes describing the event, rather than composing a formatted sentence by hand.
2. The logger serializes the message, the severity level, and the attributes into the chosen format, most commonly one JSON object per line, so line based tools can process the output without special handling.
3. Exactly one record is written per event. Go's log/slog documents its own default output as one line per call, giving the concrete example that slog.Info with a message and a count attribute produces a single line carrying the time, the level, the message, and the count field together (https://pkg.go.dev/log/slog).
4. The ingestion pipeline reads each line, parses it into its named fields, and indexes those fields rather than the raw text, which is what makes the next step possible at all.
5. An engineer, or an automated alert, queries the indexed store directly by field name, for example every record where a status field equals 500, rather than searching for a substring inside a sentence that may or may not still be phrased the way it was when the query was written.
6. When a field naming convention is followed consistently, the same query works across every service that emits the field, which is the entire practical payoff of standardizing names in the first place.

## 8. Implementation variants

- JSON Lines. one JSON object per line, the most common concrete serialization, chosen because it works well with unix style text processing tools and shell pipelines and is described by its own specification as a great format for log files (https://jsonlines.org/).
- Logfmt and canonical log lines. a lighter key equals value format, and, in Stripe's own production practice, one long canonical log line emitted at the end of a request that carries many of the request's key characteristics together, described in Stripe's own words as machine readable and ingestible for a number of different log processing tools (https://stripe.com/blog/canonical-log-lines), trading some per event granularity for a single, easy to query summary of the whole request.
- Typed, span attached structured events. Rust's tracing crate ties structured fields not only to a single point in time but to a span representing a unit of work, so fields recorded while a span is active are structured and typed rather than textual (https://docs.rs/tracing/latest/tracing/), which composes directly with the Span and Trace Context Propagation pattern elsewhere in this family.
- Standard library key-value logging. Go's log/slog is the variant with the least ceremony, a direct call carrying a message and a flat list of key-value pairs, requiring no separate schema definition before a field can be logged.

## 9. Known production uses

- Go's standard library ships log/slog, adding structured logging with key-value attributes as a first class part of the language's own logging package since Go 1.21 (https://pkg.go.dev/log/slog).
- Rust's tracing crate is a widely used dependency across the Rust ecosystem for structured, span attached logging and instrumentation (https://docs.rs/tracing/latest/tracing/).
- Stripe emits a single canonical log line per request in production, described in its own engineering blog as the practice that lets its teams query and diagnose incidents fast, ingestible for a number of different log processing tools (https://stripe.com/blog/canonical-log-lines).

## 10. Consequences

### Benefits

- Every field is queryable and aggregatable directly, closing the gap between a log line a person can read and a log line a system can reliably act on.
- A shared field naming convention makes the same query work across every service that follows it, rather than requiring a different search phrasing per service.
- Stripe's own canonical log line practice shows the direct payoff during an incident, one line per request carries enough structured detail to diagnose a problem without hunting across scattered, differently phrased lines.

### Costs

- Every additional structured field adds real, ongoing ingestion and storage cost, and an unmanaged volume of verbose structured records can grow into a genuine cost problem at scale.
- Field naming has to be actively maintained across every service, and a service that drifts from the shared convention silently breaks queries and aggregations that assume consistency.
- A structured field is, by construction, easy to query and export, which means a sensitive value accidentally logged into one is far easier to find and extract than the same value buried in an unstructured sentence.

## 11. Failure modes and misuse

- Field names drift across services, most often because each team added its own logging independently with no shared convention, and a query written against one service's field name silently misses every other service using a different name for the same concept, exactly the class of problem the OpenTelemetry semantic conventions were built to fix (https://opentelemetry.io/docs/specs/semconv/).
- Sensitive data, a session identifier, an access token, or personal information, is logged directly as a structured field, where general logging guidance is clear that categories such as session identification values and access tokens should usually not be recorded directly in logs (https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html), and a structured field makes that same data trivially easy to query out at scale once it is in.
- Log volume grows unmanaged as more and more structured fields are added to more and more call sites, until ingestion and storage cost becomes a real budget problem, which is the exact scenario Datadog's own guidance addresses by recommending routing, filtering, and sampling as close to the source as possible (https://www.datadoghq.com/blog/optimize-high-volume-logs/).
- A field with an effectively unbounded number of distinct values, most often a user identifier or a request identifier, is added as an indexed dimension in a system built around a bounded set of values, and indexing and storage cost can rise sharply as the field's own value space and the traffic through it both grow.
- Structured and unstructured logging are mixed in the same service with no clear boundary, so downstream tooling has to handle both shapes, and queries that assume a consistent structured shape silently miss the unstructured lines.

## 12. Trade-off matrix

| Dimension | Structured logging, one record per event | Free text sentences | Canonical log line, one summary per request |
|---|---|---|---|
| Queryable by field | Yes | No, requires text search | Yes |
| Human readable directly in a terminal | Lower, needs tooling | High | Moderate, one dense line |
| Storage and ingestion cost | Moderate, scales with fields | Lower per line | Lower, one line per request |
| Cross-service consistency | Requires a shared naming convention | Not applicable | Requires the same convention |
| Best fit for incident diagnosis in one query | Good | Poor | Very good, Stripe's own stated reason for adopting it |

## 13. Related and incompatible patterns

Related to Correlation ID, since a structured log record is only fully useful once it carries a consistently named correlation field tying it to every other record from the same request, which is exactly what the Correlation ID pattern elsewhere in this family provides.

Related to the RED Method and the USE Method patterns queued in this same family, both of which depend on querying structured log and metric data reliably by field rather than parsing free text.

Not incompatible with anything in this catalog. a service can mix a small amount of unstructured debug output in local development with fully structured output in production, as long as the boundary between the two is deliberate rather than accidental.

## 14. Refactoring path in and out

To introduce it into a service that logs free text sentences today, start by adopting a structured logging library appropriate to the language, Go's log/slog or Rust's tracing being two directly citable examples, and migrate the highest volume or highest value call sites first, the ones most often searched during an incident. Next, agree a shared field naming convention across every service that will be queried together, adopting an existing standard such as the OpenTelemetry semantic conventions rather than inventing one from scratch. Then, consider consolidating the highest traffic paths into a Stripe style canonical log line, one structured record per request carrying its key characteristics, rather than many scattered structured records that each carry only a fragment of the picture.

Removing it entirely is rare, since the query and aggregation benefit compounds with scale, but a team scaling down to a single, low traffic service with no aggregation system reading its logs may reasonably revert to plain, human phrased sentences, trading queryability for the lower ceremony of writing a sentence directly.

## 15. Testing and verification

Assert that every emitted log line parses as valid structured output in its chosen format, a JSON parse or a logfmt parse succeeding on every line the service produces, so a malformed record is caught before it reaches production rather than silently breaking a downstream query. Test that field names match the team's agreed naming convention, catching drift at the point it is introduced rather than after a query has already silently missed records for weeks. Add a security focused test asserting that a known sensitive field, a token, a password, or a personal data field, is never present in a captured log record, directly exercising the sanitization discipline the pattern depends on.

## 16. Observability signals

Track log ingestion volume per service over time, since a sudden, unexplained increase is the earliest signal of the cost growth this pattern can produce if left unmanaged. Track the number of distinct values seen for any field used as an indexed dimension, watching for a field, most often an identifier, whose distinct value count is growing without bound, since that is the specific shape of failure that breaks indexing and pricing at scale. Track the proportion of log lines that conform to the agreed structured schema versus lines that fall back to free text, as a direct measure of how completely the pattern has actually been adopted across a service or a fleet of services.

## 17. Security and privacy implications

Treat every structured field as something a person could eventually query, export, and read, because that ease of access is the entire point of the pattern, and it applies to a sensitive value exactly as much as it applies to an intended one. Sanitize or omit sensitive categories before they ever reach a log call, general guidance on this point names session identification values, access tokens, authentication passwords, and personal data among the categories that should usually not be recorded directly in logs (https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html). Because a structured field is easier to query out at scale than the same value buried in free text, a sensitive value that leaks into structured logging is a materially larger exposure than the same leak in an unstructured sentence, which is worth stating plainly to anyone evaluating the risk rather than assuming the two are equivalent.

## 18. References

1. Go standard library documentation, package slog. Defines structured logging as records with a message, a severity level, and key-value attributes. https://pkg.go.dev/log/slog, verified 2026-08-22.
2. Rust tracing crate documentation. Describes structured, typed spans and events as the crate's core mechanism. https://docs.rs/tracing/latest/tracing/, verified 2026-08-22.
3. Stripe engineering blog, canonical log lines. Describes emitting one structured, machine readable log line per request for fast incident diagnosis. https://stripe.com/blog/canonical-log-lines, verified 2026-08-22.
4. JSON Lines specification. Defines the one-JSON-object-per-line convention as the standard shape for structured log files. https://jsonlines.org/, verified 2026-08-22.
5. OpenTelemetry Semantic Conventions. Standardizes field naming so telemetry, including logs, correlates consistently across services. https://opentelemetry.io/docs/specs/semconv/, verified 2026-08-22.
6. OWASP Cheat Sheet Series, Logging Cheat Sheet. Names the categories of sensitive data that should usually not be recorded directly in logs. https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html, verified 2026-08-22.
7. Datadog engineering blog, optimizing high volume logs. Documents log volume and cost management guidance including routing, filtering, and sampling near the source. https://www.datadoghq.com/blog/optimize-high-volume-logs/, verified 2026-08-22.

**Evidence grade.** high

**Most solid findings.** The Go log/slog and Rust tracing definitions (source 1, 2) are quoted directly from the libraries' own official documentation. The Stripe canonical log line practice (source 3) is quoted from Stripe's own engineering blog describing its own production system. The log volume and cost guidance (source 7) is quoted directly from vendor documentation written specifically to address that problem.

**Unverified or unclear.** No solid, independently citable source is included in this entry for the specific claim that a field with an unbounded number of distinct values pushes indexing and storage cost up sharply, so that claim in dimensions 3, 11, and 16 is stated as engineering judgement, not as a directly sourced fact, and it is scoped narrowly on purpose. The sensitive-data risk in dimension 17 is likewise stated honestly as engineering judgement built on top of the general OWASP guidance, not as a directly sourced fact, since no solid source was found narrowing that risk specifically to structured fields rather than logging generally.

## Code examples

### Go, key-value structured logging with log/slog

```go
package main

import (
	"log/slog"
	"os"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	logger.Info("request completed", "method", "GET", "path", "/checkout", "status", 200, "duration_ms", 42)
}
```

### Python, structured logging via a JSON formatter

```python
import json
import logging


class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "message": record.getMessage(),
            "level": record.levelname,
            "logger": record.name,
        }
        extra = getattr(record, "fields", None)
        if extra:
            payload.update(extra)
        return json.dumps(payload)


def build_logger():
    logger = logging.getLogger("service")
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


logger = build_logger()
logger.info("request completed", extra={"fields": {"status": 200, "duration_ms": 42}})
```

### TypeScript, one JSON object per line

```typescript
interface LogFields {
  [key: string]: string | number | boolean;
}

function logStructured(message: string, level: string, fields: LogFields): void {
  const record = {message, level, ...fields};
  console.log(JSON.stringify(record));
}

logStructured("request completed", "info", {method: "GET", path: "/checkout", status: 200, duration_ms: 42});
```
