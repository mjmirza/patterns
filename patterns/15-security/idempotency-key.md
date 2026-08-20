---
name: Idempotency Key
slug: idempotency-key
family: 15-security
category: Security
aliases: [Idempotency-Key, Idempotency Token, Client Token, Request Idempotency Key, PayPal-Request-Id]
first_described: "Common API practice before the expired IETF HTTPAPI Internet-Draft"
maturity: established
related: [retry, idempotent-consumer, transactional-outbox, saga, audit-log, rate-limiter]
incompatible_with: [ambient-authority, non-atomic-check-then-act, unbounded-replay-cache]
verified: 2026-08-02
---

# Idempotency Key

## 1. Name, aliases, and lineage

The canonical name is **Idempotency Key**. In HTTP APIs the field name often
appears as `Idempotency-Key`. The expired IETF HTTPAPI Internet-Draft by
Jayadeba Jena and Sanjay Dalal calls the header field `Idempotency-Key`, says
it carries a unique client generated value, and positions it as a way to make
non-idempotent HTTP methods such as `POST` and `PATCH` fault tolerant
([IETF HTTPAPI draft, "The Idempotency-Key HTTP Header Field"](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header),
verified 2026-08-02). The draft was published on 2025-10-15 and is recorded by
the IETF datatracker as expired, so this entry treats it as useful design
guidance, not as a current Internet Standard
([IETF HTTPAPI draft datatracker view](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header),
verified 2026-08-02).

Other names are product specific. PayPal uses `PayPal-Request-Id` for its REST
API idempotency mechanism, and describes it as a unique user generated ID
stored by the server for a period of time
([PayPal REST API idempotency reference](https://developer.paypal.com/api/rest/reference/idempotency/),
verified 2026-08-02). Amazon EC2 documentation uses **client token** wording
for request idempotency in several mutating APIs, while AWS Lambda Powertools
uses **idempotency key** for the value extracted from an event payload and
stored in an idempotency record
([AWS Lambda Powertools idempotency utility](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/),
verified 2026-08-02). Square places an `idempotency_key` field in the JSON body
of CreatePayment requests rather than in an HTTP header
([Square CreatePayment API reference](https://developer.squareup.com/reference/square/payments-api/create-payment),
verified 2026-08-02). Adyen uses the lowercase HTTP header name
`idempotency-key` in its API docs and states that HTTP headers must be handled
case insensitively
([Adyen API idempotency docs](https://docs.adyen.com/development-resources/api-idempotency),
verified 2026-08-02).

The lineage is not the same as HTTP method idempotence. RFC 9110 defines an
HTTP method as idempotent when multiple identical requests have the same
intended server effect as one request, and lists `PUT`, `DELETE`, and safe
methods as idempotent among the methods it defines
([RFC 9110, section 9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods),
verified 2026-08-02). An idempotency key is a higher level application
contract for operations whose natural HTTP shape is often `POST`, such as
charging a payment method, creating an order, or starting a job. The key gives
the server a stable name for one logical command so retries do not become new
commands.

Engineering judgement. This pattern belongs in the security family because it
protects people and systems from duplicate money movement, duplicate account
changes, and replay ambiguity. It is also a distributed systems reliability
pattern. The security reading is strongest when the operation has externally
visible authority, such as payment capture, refund, shipment release, identity
change, or privileged workflow approval.

## 2. Problem and context

A client sends a mutating request and then loses the answer. The request might
not have reached the server. It might have reached the server and failed before
the side effect. It might have completed the side effect and failed while the
response was on the way back. From the client's side, those cases can look the
same. Stripe's public engineering article on idempotency frames this as the
ambiguous failure case in networked APIs, where a connection can fail before,
during, or after a server operation
([Stripe engineering blog article on idempotency](https://stripe.com/blog/idempotency),
verified 2026-08-02).

Without an idempotency key, the client has two bad choices. If it retries, it
may create a second charge, refund, order, email, shipment, password reset, or
workflow approval. If it does not retry, it may leave a customer, worker, or
partner stuck with no result even though the original command might have been
lost before the server acted. HTTP `PUT` can solve this when the client names a
resource and sends the replacement state, but many real commands are append,
allocate, capture, or start operations where the server owns the final resource
identifier or state transition. RFC 9110's idempotent method definition covers
the method's intended effect, not a payment provider's custom command semantics
([RFC 9110, section 9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods),
verified 2026-08-02).

The idempotency key pattern adds a command identity. The client generates a key
once for one logical operation and resends the same key on retries of that same
operation. The server stores the key, the request fingerprint, the processing
state, and eventually the result. A first request claims the key and performs
the operation. A later retry with the same key and the same fingerprint receives
the prior result or a clear "still in progress" response. A later request with
the same key and different material request content is rejected as key reuse.
The IETF draft describes the same high level split: first requests are
processed normally, completed duplicates receive the previous result, and
concurrent duplicates can receive conflict responses
([IETF HTTPAPI draft, sections 2.4 through 2.7](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header),
verified 2026-08-02).

The context is a system that accepts retries, either because clients retry
explicitly, SDKs retry, queues redeliver messages, gateways replay failed
calls, mobile networks drop connections, or users repeat a submit action. The
pattern is less about suppressing duplicate packets and more about defining the
unit of work that may be retried without applying the work twice.

## 3. Forces

Engineering judgement. The pattern balances these pressures.

- **Consistency.** Favoured. The server can converge repeated attempts of one
  command onto one recorded result. The sacrifice is that the server must now
  keep request history for at least a configured window.
- **Latency.** Mixed. A first request pays a storage read or conditional write
  before the business operation and a result write after it. A duplicate
  request can be faster because it returns stored output.
- **Coupling.** Mixed. Client and server agree on key generation, key scope,
  expiry, and retry rules. That coupling buys a shared command identity.
- **Operability.** Favoured when implemented with logs and metrics. Operators
  can group retries by key. Operability is sacrificed when keys are opaque but
  not logged, or when the store cannot reveal which state a key is in.
- **Cost.** Sacrificed. The system needs a strongly consistent record store,
  cleanup policy, result retention, and extra traffic during retry storms.
- **Team topology.** Favoured when a platform team owns a middleware or shared
  library and product teams add endpoint-specific fingerprints. It is
  sacrificed when every endpoint invents a different header, body field, expiry
  rule, and conflict response.
- **Cognitive load.** Sacrificed. Developers must think in terms of logical
  commands, attempts, fingerprints, in-progress records, stored failures, and
  replay windows.
- **Security.** Favoured for duplicate side effects and replay ambiguity, but
  sacrificed if keys become bearer-like references to stored responses or if a
  tenant boundary is missing from the lookup key.

The pattern favours correctness during ambiguous failure over raw first-attempt
speed. It favours explicit retry semantics over a thin stateless API. It gives
up the simplicity of handling every `POST` as a new command.

## 4. Applicability and non-applicability

Reach for Idempotency Key when these conditions hold.

- A client can receive an unknown result after a mutating operation, especially
  after a timeout, connection close, process crash, queue redelivery, or SDK
  retry.
- The operation is expensive, irreversible, externally visible, or harmful when
  repeated. Payment capture, refund, shipment release, account creation, job
  submission, and message send all fit this shape.
- The operation is naturally expressed as a command, not as a complete
  replacement of a named resource.
- The client can hold a stable key across retry attempts. A web checkout flow
  can bind it to the order attempt. A background worker can bind it to the job
  ID. A process manager can bind it to the step ID.
- The server has access to a store that can atomically claim "this key is new"
  under the correct scope.
- The organization is prepared to publish expiry, key length, retry, and error
  behavior. The IETF draft says a resource should publish idempotency
  requirements and expiry policy when it applies
  ([IETF HTTPAPI draft, sections 2.3 and 2.5](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header),
  verified 2026-08-02).

Do NOT reach for Idempotency Key in these cases.

- **The operation is already a pure read.** `GET` and `HEAD` do not need a
  command replay record. Normal HTTP caching, request tracing, or request IDs
  solve different problems.
- **A natural resource identifier makes `PUT` correct.** If the client can say
  `PUT /users/alice@example.com` with the whole target representation, HTTP
  method idempotence may be cleaner than a `POST` plus key.
- **The server cannot make the claim atomic.** A read followed by a later insert
  admits races. Use a database uniqueness constraint, conditional write, or
  transactional lock before applying the side effect.
- **The key is generated inside the retry loop.** A new key per attempt tells
  the server to create a new command each time. Fix the client workflow first.
- **The duplicate would be harmless and cheap.** A status refresh, no-op cache
  warm, or recalculation with no external effect may not be worth a replay
  store.
- **The server cannot store enough request identity to detect misuse.** If a
  reused key with different amount, account, tenant, or operation would be
  accepted, the pattern creates a silent data integrity risk.
- **The needed contract is sequencing, not de-duplication.** Idempotency does
  not order commands. Use optimistic concurrency, version checks, leases, or a
  single-writer queue when the problem is "apply B only after A".
- **The required window is unbounded.** If a duplicate must be suppressed
  forever, the key store becomes a permanent ledger. Model it as domain state
  with normal retention, indexing, and audit rules.
- **The operation includes multiple systems that cannot share a command
  identity.** A local key around only the first database write does not protect
  a later third-party call unless that call also receives a stable key or is
  otherwise idempotent.
- **The team wants to hide a business uniqueness rule.** Unique invoice number,
  unique booking reference, or one active subscription per account should be a
  domain invariant. An idempotency key can protect retries around that
  invariant, but it should not replace it.

## 5. Structure

The pattern has seven participants.

- **Client command issuer.** Creates one key for one logical command and keeps
  it stable across retries. It must not derive the key from mutable presentation
  state unless the server also validates a request fingerprint.
- **Transport carrier.** Carries the key. Common carriers are the
  `Idempotency-Key` HTTP header, a product-specific header such as
  `PayPal-Request-Id`, or a JSON body field such as Square's
  `idempotency_key`
  ([PayPal REST API idempotency reference](https://developer.paypal.com/api/rest/reference/idempotency/),
  verified 2026-08-02;
  [Square CreatePayment API reference](https://developer.squareup.com/reference/square/payments-api/create-payment),
  verified 2026-08-02).
- **Scope resolver.** Adds tenant, account, credential, endpoint, method, or
  operation type to the lookup. PayPal documents uniqueness per request and API
  call type, while Adyen documents key uniqueness at company account level
  ([PayPal REST API idempotency reference](https://developer.paypal.com/api/rest/reference/idempotency/),
  verified 2026-08-02;
  [Adyen API idempotency docs](https://docs.adyen.com/development-resources/api-idempotency),
  verified 2026-08-02).
- **Fingerprint builder.** Canonicalizes the relevant request content and stores
  a digest or selected field set. The IETF draft names whole-payload checksums,
  selected elements, field matches, and request digest or signature as
  fingerprint approaches
  ([IETF HTTPAPI draft, section 2.4](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header),
  verified 2026-08-02).
- **Idempotency store.** Persists key, scope, fingerprint, status, expiry, and
  response data. It must support an atomic "create if absent" operation.
  PostgreSQL documents `INSERT ... ON CONFLICT` as a way to choose another
  action when a unique constraint or exclusion constraint would be violated
  ([PostgreSQL INSERT documentation](https://www.postgresql.org/docs/current/sql-insert.html),
  verified 2026-08-02). DynamoDB condition expressions can make a `PutItem`
  proceed only when the primary key does not already exist
  ([DynamoDB condition expression docs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html),
  verified 2026-08-02). Redis `SET` has an `NX` option that sets a key only
  when it does not already exist
  ([Redis SET command documentation](https://redis.io/docs/latest/commands/set/),
  verified 2026-08-02).
- **Command handler.** Performs the side effect after the key is claimed. It
  writes the final response or failure into the store before the client-visible
  attempt is considered complete.
- **Replay responder.** Returns a stored result, rejects a fingerprint mismatch,
  or reports that a matching command is still in progress. Stripe documents
  saving the status code and body from the first request for a key and returning
  the same result on later requests, including failures
  ([Stripe idempotent requests reference](https://docs.stripe.com/api/idempotent_requests?lang=curl),
  verified 2026-08-02).

## 6. ASCII structure diagram

```text
 +--------------------+        +---------------------+
 | Client command     |        | Retry policy        |
 | issuer             |------->| same key per retry  |
 +---------+----------+        +----------+----------+
           |                              |
           | request plus key             |
           v                              |
 +---------+------------------------------+----------+
 | API boundary                                     |
 |  carrier parser, scope resolver, fingerprint     |
 +---------+------------------------------+----------+
           | scoped key plus fingerprint
           v
 +---------+----------+    claim/read     +----------+---------+
 | Idempotency store  |<----------------->| Command handler    |
 | key, scope, hash   |                   | applies side effect|
 | state, result, TTL |------------------>| stores final result|
 +---------+----------+                   +----------+---------+
           |
           | stored result, mismatch, or in-progress state
           v
 +---------+----------+
 | Replay responder   |
 | same response,     |
 | conflict, or error |
 +--------------------+
```

## 7. Dynamics

The runtime flow is a small state machine around a large side effect. The
states are usually `absent`, `in_progress`, `complete`, `failed`, and
`expired`. AWS Lambda Powertools documents an idempotency record with a key,
status, expiry timestamp, in-progress expiry timestamp, response data, and
payload hash, and names `INPROGRESS` and `COMPLETE` statuses
([AWS Lambda Powertools idempotency utility](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/),
verified 2026-08-02).

```text
Client A        API              Store             Side effect
   |             |                  |                    |
   | POST K,F    |                  |                    |
   |------------>| claim K,F        |                    |
   |             |----------------->| absent -> progress |
   |             |<-----------------| claimed            |
   |             |--------------------------------------->|
   |             |                  |       apply once    |
   |             | save result R    |                    |
   |             |----------------->| progress -> done   |
   |<------------| 201 R            |                    |
   |             |                  |                    |
   | POST K,F    |                  |                    |
   |------------>| read K,F         |                    |
   |             |----------------->| done, result R     |
   |             |<-----------------| R                  |
   |<------------| 201 R            |                    |

Client B        API              Store
   | POST K,G    |                  |
   |------------>| read K,G         |
   |             |----------------->| K exists with F
   |             |<-----------------| mismatch
   |<------------| 422 or domain error

Client C        API              Store             Side effect
   | POST K,F    |                  |                    |
   |------------>| read K,F         |                    |
   |             |----------------->| in progress        |
   |             |<-----------------| not finished       |
   |<------------| 409 or retryable |
```

The first attempt must claim before the side effect. If the side effect happens
first and the key is stored after, a crash between those steps can make the
retry apply the effect again. If the key is claimed but the process dies before
writing a final result, the in-progress expiry decides whether a later attempt
may take over, report conflict, or trigger human repair.

## 8. Implementation variants

**HTTP header, server retained response.** The client sends
`Idempotency-Key`. The server stores the final status code and body and returns
that stored output on repeat attempts. Stripe documents this model for POST
requests, with keys up to 255 characters and automatic pruning after keys are
at least 24 hours old
([Stripe idempotent requests reference](https://docs.stripe.com/api/idempotent_requests?lang=curl),
verified 2026-08-02). This variant gives the cleanest client experience but
can store sensitive response data unless the response is reduced or encrypted.

**Product-specific header.** PayPal's `PayPal-Request-Id` is a named header for
REST API idempotency. PayPal documents that the server returns the latest
status of the previous request for the same header and that not every API
supports the header
([PayPal REST API idempotency reference](https://developer.paypal.com/api/rest/reference/idempotency/),
verified 2026-08-02). This variant fits legacy APIs and provider-specific
contracts, but client middleware cannot infer behavior from a common header
name.

**Body field.** Square requires an `idempotency_key` string in the
CreatePayment request body
([Square CreatePayment API reference](https://developer.squareup.com/reference/square/payments-api/create-payment),
verified 2026-08-02). Body fields are easy for generated SDKs to model, but
harder for generic HTTP gateways to enforce before body parsing.

**Message or job key.** A queue consumer can use a message ID, job ID, order
step ID, or business command ID as the key. This composes with the
Idempotent Consumer pattern, but the replay result may be an acknowledgement
rather than an HTTP body.

**Natural business key.** A unique invoice ID, booking reference, or external
order ID can double as a replay key when the business key already represents
the command. Engineering judgement. This is attractive because the domain
already audits it, but it is risky when one business object has several
distinct commands, such as authorize, capture, refund, and cancel.

**Derived payload hash.** AWS Lambda Powertools can derive the key from the
whole event or from selected fields, and can validate payload fields to detect
changed input for a prior key
([AWS Lambda Powertools idempotency utility](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/),
verified 2026-08-02). This variant reduces client burden inside event systems,
but small irrelevant changes can create new keys unless extraction is chosen
with care.

**PostgreSQL style conditional insert.** A relational table uses a unique
constraint over `(tenant_id, operation, key)` and claims the key with
`INSERT`. On conflict, the handler reads the existing row and decides whether
to replay, reject, or report progress. PostgreSQL documents `ON CONFLICT DO
NOTHING` and `ON CONFLICT DO UPDATE` for conflict handling
([PostgreSQL INSERT documentation](https://www.postgresql.org/docs/current/sql-insert.html),
verified 2026-08-02).

**Redis short window claim.** `SET key value NX EX seconds` can claim a short
retry window. Redis documents `NX` for setting only absent keys and `EX` for
expiry
([Redis SET command documentation](https://redis.io/docs/latest/commands/set/),
verified 2026-08-02). Engineering judgement. This is useful for low-value,
short-lived commands, but a cache eviction or failover can turn a duplicate
into a new operation unless the business effect has its own protection.

The following examples are minimal, original, and runnable. They use in-memory
stores so the shape is clear. Production code must replace the map with a
store that provides atomic claim semantics across processes.

TypeScript, API boundary wrapper.

```typescript
type Status = "in_progress" | "complete";

type RecordEntry = {
  fingerprint: string;
  status: Status;
  response?: { statusCode: number; body: string };
};

class IdempotencyStore {
  private rows = new Map<string, RecordEntry>();

  claim(scopedKey: string, fingerprint: string): "claimed" | RecordEntry {
    const existing = this.rows.get(scopedKey);
    if (existing) return existing;
    const row: RecordEntry = { fingerprint, status: "in_progress" };
    this.rows.set(scopedKey, row);
    return "claimed";
  }

  complete(scopedKey: string, response: { statusCode: number; body: string }) {
    const row = this.rows.get(scopedKey);
    if (!row) throw new Error("missing idempotency row");
    row.status = "complete";
    row.response = response;
  }
}

function createPayment(
  store: IdempotencyStore,
  account: string,
  key: string,
  amountCents: number,
): { statusCode: number; body: string } {
  const scopedKey = `${account}:create-payment:${key}`;
  const fingerprint = `amount=${amountCents}`;
  const claim = store.claim(scopedKey, fingerprint);

  if (claim !== "claimed") {
    if (claim.fingerprint !== fingerprint) {
      return { statusCode: 422, body: "idempotency key reused" };
    }
    if (claim.status !== "complete" || !claim.response) {
      return { statusCode: 409, body: "request still in progress" };
    }
    return claim.response;
  }

  const response = { statusCode: 201, body: `payment:${amountCents}` };
  store.complete(scopedKey, response);
  return response;
}

const store = new IdempotencyStore();
console.log(createPayment(store, "acct_1", "k1", 500).body);
console.log(createPayment(store, "acct_1", "k1", 500).body);
console.log(createPayment(store, "acct_1", "k1", 700).statusCode);
```

Python, decorator around a command handler.

```python
from dataclasses import dataclass


@dataclass
class Entry:
    fingerprint: str
    status: str
    response: str | None = None


class Store:
    def __init__(self) -> None:
        self.rows: dict[str, Entry] = {}

    def claim(self, key: str, fingerprint: str) -> Entry | None:
        row = self.rows.get(key)
        if row is not None:
            return row
        self.rows[key] = Entry(fingerprint=fingerprint, status="in_progress")
        return None

    def complete(self, key: str, response: str) -> None:
        self.rows[key].status = "complete"
        self.rows[key].response = response


def submit_job(store: Store, tenant: str, key: str, image: str) -> str:
    scoped_key = f"{tenant}:submit-job:{key}"
    fingerprint = f"image={image}"
    existing = store.claim(scoped_key, fingerprint)
    if existing:
        if existing.fingerprint != fingerprint:
            return "422 key reused with different input"
        if existing.status != "complete":
            return "409 still running"
        return existing.response or "500 missing response"

    response = f"job-created:{image}"
    store.complete(scoped_key, response)
    return response


store = Store()
print(submit_job(store, "tenant-a", "key-1", "img-9"))
print(submit_job(store, "tenant-a", "key-1", "img-9"))
print(submit_job(store, "tenant-a", "key-1", "img-10"))
```

Go, handler core with an explicit store.

```go
package main

import "fmt"

type Entry struct {
	Fingerprint string
	Status      string
	Response    string
}

type Store struct {
	rows map[string]Entry
}

func NewStore() *Store {
	return &Store{rows: map[string]Entry{}}
}

func (s *Store) Claim(key, fingerprint string) (Entry, bool) {
	entry, found := s.rows[key]
	if found {
		return entry, true
	}
	s.rows[key] = Entry{Fingerprint: fingerprint, Status: "in_progress"}
	return Entry{}, false
}

func (s *Store) Complete(key, response string) {
	entry := s.rows[key]
	entry.Status = "complete"
	entry.Response = response
	s.rows[key] = entry
}

func Refund(store *Store, merchant, key string, cents int) string {
	scopedKey := merchant + ":refund:" + key
	fingerprint := fmt.Sprintf("cents=%d", cents)
	entry, found := store.Claim(scopedKey, fingerprint)
	if found {
		if entry.Fingerprint != fingerprint {
			return "422 key reused"
		}
		if entry.Status != "complete" {
			return "409 in progress"
		}
		return entry.Response
	}
	response := fmt.Sprintf("refund-created:%d", cents)
	store.Complete(scopedKey, response)
	return response
}

func main() {
	store := NewStore()
	fmt.Println(Refund(store, "m1", "k1", 900))
	fmt.Println(Refund(store, "m1", "k1", 900))
	fmt.Println(Refund(store, "m1", "k1", 901))
}
```

## 9. Known production uses

**Stripe API.** Stripe documents idempotency for safely retrying requests that
create or update objects. Its API accepts idempotency keys on all `POST`
requests, stores the first result for a key, compares later parameters to the
original request, and says clients should not send keys on `GET` or `DELETE`
because those requests are idempotent by definition
([Stripe idempotent requests reference](https://docs.stripe.com/api/idempotent_requests?lang=curl),
verified 2026-08-02).

**PayPal REST APIs.** PayPal documents `PayPal-Request-Id` as the request
header used to enforce idempotency on supported REST API `POST` calls. It says
the value is a unique user generated ID stored by the server, and that a retry
with the same header receives the latest status of the previous request rather
than duplicating the action
([PayPal REST API idempotency reference](https://developer.paypal.com/api/rest/reference/idempotency/),
verified 2026-08-02).

**Adyen APIs.** Adyen documents API idempotency for retrying payment requests
without processing the payment twice. It uses the `idempotency-key` header,
recommends a UUID, states that keys are stored at company account level, gives
a minimum validity period of seven days, and documents transient and conflict
responses for concurrent requests
([Adyen API idempotency docs](https://docs.adyen.com/development-resources/api-idempotency),
verified 2026-08-02).

**Square Payments API.** Square's CreatePayment endpoint requires an
`idempotency_key` request body field, described as a unique string identifying
the CreatePayment request
([Square CreatePayment API reference](https://developer.squareup.com/reference/square/payments-api/create-payment),
verified 2026-08-02).

**AWS Lambda Powertools.** AWS Lambda Powertools for Python ships an
idempotency utility that stores idempotency records, returns previous
successful results within a time window, supports DynamoDB and Redis-compatible
stores, handles concurrent requests, and allows event-field based key
extraction
([AWS Lambda Powertools idempotency utility](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/),
verified 2026-08-02).

## 10. Consequences

Engineering judgement. Positive consequences.

- Retried mutating requests become safe within a defined replay window.
- Client retry code becomes simpler because an unknown result can be retried
  with the same key.
- Duplicate user actions, such as double submit in a checkout flow, can map to
  one command when the UI keeps the same key.
- Operators can correlate all attempts for a command by key, account, and
  operation.
- API documentation becomes explicit about retry behavior, expiry, and error
  handling.
- Expensive commands can return stored results for duplicates rather than
  repeating work.
- Security reviews gain a concrete control for replay ambiguity around
  privileged mutations.

Engineering judgement. Negative consequences.

- The first request is slower and more complex because it touches an
  idempotency store before and after the side effect.
- Storage cost grows with traffic, retention window, and result size.
- The store becomes a dependency for the availability of mutating endpoints.
  Adyen documents that idempotent processing depends on a stateful data store
  and can return service unavailable when that store is unavailable
  ([Adyen API idempotency docs](https://docs.adyen.com/development-resources/api-idempotency),
  verified 2026-08-02).
- Stored responses can contain sensitive data and become subject to retention,
  deletion, and access control policy.
- Long running commands need an in-progress policy, not a single completed
  result path.
- Payload fingerprinting creates canonicalization work. JSON field order,
  irrelevant metadata, generated timestamps, and id fields can all affect
  whether two attempts are considered the same command.
- Expiry creates a hard edge. After the window, the same key may be treated as
  new. Stripe documents that it can generate a new request if a key is reused
  after the original is pruned
  ([Stripe idempotent requests reference](https://docs.stripe.com/api/idempotent_requests?lang=curl),
  verified 2026-08-02).

## 11. Failure modes and misuse

Engineering judgement. Each failure mode is stated as Symptom, Cause, Fix.

**Duplicate side effect after timeout.** Symptom. A customer is charged twice,
two jobs start, or two emails are sent after one client action and one timeout.
Cause. The handler writes the idempotency record after the side effect, or uses
a non-atomic read then write. Fix. Claim the scoped key before the side effect
with a unique constraint, conditional write, or equivalent atomic primitive.

**Every retry is treated as new.** Symptom. Logs show a different key on each
retry attempt for the same button click, job, or command. Cause. The client
creates the key inside the retry loop or on each render. Fix. Create the key
when the logical command is created and pass it through every retry.

**Key collision across tenants.** Symptom. One tenant receives a replayed
response or conflict caused by another tenant's request. Cause. The server
stores only the raw key and omits tenant, account, credential, and operation
scope. Fix. Use a compound lookup key that includes the authority boundary and
operation name.

**Mismatched payload is accepted.** Symptom. A retry with the same key but a
different amount or target account returns the old response, or worse, applies
the new request. Cause. The server stores no fingerprint or fingerprints only
irrelevant fields. Fix. Store a canonical fingerprint of the fields that define
the command and reject mismatches.

**Permanent in-progress rows.** Symptom. Clients keep receiving `409` or
"still running" for a key whose worker died hours ago. Cause. The claim has no
in-progress expiry or takeover path. Fix. Store an in-progress deadline and
define recovery. A later attempt can take over only when the side effect can be
proven absent or repaired.

**Stored failure freezes a transient outage.** Symptom. Retrying with the same
key always returns the first `500`, even after the dependency has recovered.
Cause. The implementation persists every failure as the final result. Stripe
documents returning the same result, including `500` errors, for a given key
([Stripe idempotent requests reference](https://docs.stripe.com/api/idempotent_requests?lang=curl),
verified 2026-08-02). Fix. Decide per endpoint which failures are terminal
and which leave the key retryable, then document that contract.

**Replay store leaks sensitive output.** Symptom. A lower-privilege credential
that knows a key can recover an older response containing personal or financial
data. Cause. The lookup checks the key but not the current authorization scope,
or stores full responses longer than needed. Fix. Include principal scope in
the key, re-check authorization on replay, minimize stored response data, and
encrypt sensitive fields.

**Cache eviction turns duplicates into new commands.** Symptom. Duplicate side
effects appear during cache pressure or Redis failover. Cause. A volatile cache
is the only de-duplication store for high-value commands. Fix. Use durable
storage for high-value effects, or pair cache claims with domain uniqueness.

**Clock and TTL edge creates surprise.** Symptom. A retry near expiry sometimes
replays and sometimes creates a new command. Cause. Nodes disagree about time
or cleanup removes records at the edge of the documented window. Fix. Evaluate
expiry in one store or with one clock source, keep a grace window, and publish
the minimum retention guarantee.

**Outbox side effect escapes the boundary.** Symptom. Database state is
deduplicated, but a downstream webhook or third-party call fires twice. Cause.
The idempotency guard covers only the local transaction, not every externally
visible effect. Fix. Put follow-up messages in a Transactional Outbox with the
same command key, and pass stable idempotency keys to downstream APIs.

## 12. Trade-off matrix

| Force | Idempotency Key | Natural HTTP PUT | Unique Business Constraint | Idempotent Consumer | Distributed Lock |
|---|---|---|---|---|---|
| Best fit | Retried commands with unknown result | Client named resource replacement | Domain invariant such as invoice number | Duplicate message delivery | Temporary exclusive access |
| Consistency | High inside retention window | High for resource replacement | High for one invariant | High per consumer side effect | Mixed, depends on lock safety |
| Latency | Adds claim and completion writes | No extra replay store | Constraint check in domain store | Adds consumer state lookup | Adds lock acquire and release |
| Coupling | Client and server share key rules | Client and server share resource URI | Callers know business uniqueness | Producer and consumer share message identity | Participants share lock service |
| Operability | Strong when key is logged | Good through resource IDs | Good through domain records | Good through consumer metrics | Often hard during lock leaks |
| Cost | Replay store plus cleanup | Low | Low to medium | Consumer store plus cleanup | Lock service plus failure handling |
| Team topology | Platform can provide middleware | API design must expose resource names | Domain team owns invariant | Messaging team and consumers coordinate | Infrastructure team owns primitive |
| Cognitive load | Medium to high | Low when resource model fits | Medium, tied to domain language | Medium | High under partitions |
| Security effect | Reduces replay ambiguity | Reduces duplicate replacement effects | Blocks forbidden duplicates | Blocks duplicate consumption | Can serialize sensitive work |
| Main weakness | Retention and atomicity mistakes | Poor fit for append commands | Does not return prior response by itself | Does not help synchronous client retry alone | Does not record command result |

## 13. Related and incompatible patterns

**Retry** composes directly with Idempotency Key. Retry decides when another
attempt is made. Idempotency Key decides whether another attempt is safe.
Without the key, retrying non-idempotent mutations can amplify damage.

**Idempotent Consumer** is the event-processing sibling. It records message or
command identity at the consumer so at-least-once delivery does not apply the
same effect twice. Idempotency Key is usually client-to-server or
command-to-handler, while Idempotent Consumer is message-to-consumer.

**Transactional Outbox** composes when a command writes local state and emits
messages. The command key can become part of the outbox message identity so
downstream consumers can deduplicate follow-up work.

**Saga and Process Manager** compose when a workflow sends several commands.
Each step should carry its own stable key, often derived from workflow ID plus
step name plus attempt intent. A single workflow key is too coarse if capture,
refund, reserve, and cancel are distinct effects.

**Audit Log** complements the pattern. The idempotency store is a runtime
control and may expire. The audit log records who attempted which command, when
it was accepted, and what result was exposed.

**Rate Limiter** is not a replacement. A rate limiter reduces traffic volume
but cannot distinguish one logical command retried three times from three
different commands.

**Distributed Lock** can protect a small concurrent section, but it does not
answer a later retry with the prior result. It also does not by itself detect a
payload mismatch.

**Ambient Authority** conflicts with the pattern when any credential that knows
the key can read stored output. Replays must be scoped and authorized like the
original operation.

**Non-atomic Check Then Act** conflicts with the pattern. If the code checks
for a key, performs work, and inserts the key after, the core guarantee is
absent.

**Unbounded Replay Cache** conflicts operationally. Keeping every key forever
without a domain retention model turns a retry helper into an unmanaged data
store.

## 14. Refactoring path in and out

Engineering judgement. Introduce the pattern in small steps.

1. Pick one endpoint or handler with a proven duplicate side-effect risk.
2. Define the logical command. Name what one key represents, such as
   `create-payment`, `capture-authorization`, or `submit-render-job`.
3. Add a required or optional key to the public contract. For HTTP, decide
   whether the carrier is a common header, product-specific header, or body
   field.
4. Define scope. Include tenant, merchant, account, credential, endpoint, and
   operation where they affect authority or uniqueness.
5. Define the fingerprint. Include amount, currency, target resource, source
   account, and other fields that would make a same-key retry unsafe if
   changed. Exclude trace IDs and volatile timestamps unless they define the
   command.
6. Create the store with a uniqueness rule over scope plus key, status,
   fingerprint, expiry, in-progress expiry, response summary, and timestamps.
7. Wrap the handler with an atomic claim before any external side effect.
8. Store the final result before acknowledging the command to the client.
9. Add replay responses for complete, in-progress, mismatched, expired, and
   missing-key cases.
10. Publish retry rules, expiry, maximum key length, and error responses.
11. Add metrics and logs from dimension 16.
12. Roll out in observe-only mode only if the operation is protected by another
   invariant. Otherwise, use a guarded endpoint release with a narrow client
   set.

Named refactorings that often apply are **Extract Function** for separating
fingerprint creation, **Extract Class** for the idempotency store, **Introduce
Parameter Object** for carrying scope, key, fingerprint, and operation name,
and **Replace Conditional with Polymorphism** only when each operation has a
different replay policy.

Refactor out when the pattern no longer earns its cost.

1. Confirm from metrics that duplicate attempts no longer arrive or that a
   better domain invariant fully absorbs them.
2. Shorten retention first and watch duplicate side effects, mismatch errors,
   and support tickets.
3. Move any permanent audit data out of the idempotency store.
4. Replace stored-response replay with a domain read if clients can fetch the
   result by resource ID.
5. Keep accepting old keys during a deprecation window, but stop requiring new
   keys only after clients have migrated.
6. Drop the store after the longest documented retention window has passed.

## 15. Testing and verification

Engineering judgement. The pattern is testable because the hard behavior can
be expressed as attempt sequences.

- **Same key, same fingerprint, success.** Send the same command twice. Assert
  the side effect counter is one and both responses match the contract.
- **Same key, different fingerprint.** Change amount, target account, tenant,
  or operation. Assert the second attempt is rejected and no new side effect
  occurs.
- **Concurrent same key.** Start two attempts at once. Assert only one reaches
  the side-effect stub. The other should see in-progress, conflict, or stored
  result according to the contract.
- **Crash after claim.** Simulate a process stop after the key is marked
  in-progress. Assert later behavior follows the in-progress expiry policy.
- **Crash after side effect but before result write.** Use a fake downstream
  system that records command IDs. Assert recovery does not repeat the external
  effect.
- **Expired key.** Advance time past retention. Assert the documented behavior,
  either new command creation or explicit expiry rejection.
- **Authorization on replay.** Repeat a key with a credential that lacks access
  to the original account. Assert the stored response is not disclosed.
- **Canonicalization.** Send semantically identical JSON with fields ordered
  differently. Assert the fingerprint behavior matches the published contract.
- **Store unavailable.** Force database, Redis, or DynamoDB failure. Assert the
  endpoint fails closed for high-value commands rather than silently disabling
  idempotency.

Useful test doubles are a fake store with deterministic claim results, a spy
side-effect service counting calls, a controllable clock for expiry, and a
barrier or latch to force concurrent attempts into the same window. Property
tests can generate attempt sequences where each sequence has one logical
command and many transport attempts, then assert the side-effect count never
exceeds one before expiry.

Verification must include the real storage primitive. Unit tests with an
in-memory map do not prove atomicity across processes. Add an integration test
against the chosen database using the real unique constraint, conditional put,
or cache command.

## 16. Observability signals

Engineering judgement. Log the key in a form that supports correlation without
creating a secret. A common choice is a keyed hash or redacted prefix, combined
with tenant, operation, request ID, and principal ID. Never log full request
payloads to make fingerprint debugging easier.

Healthy signals.

- First-attempt claim rate tracks normal mutating traffic.
- Duplicate replay rate is low but nonzero for mobile, queue, and partner
  traffic.
- Fingerprint mismatch rate is near zero.
- In-progress conflict rate has short spikes during client retry storms, then
  returns to baseline.
- Store latency is a small fraction of endpoint latency.
- Expired-key retries are rare and tied to old clients or manual replay.

Failing signals.

- Duplicate side-effect incidents with no matching idempotency record.
- Many records stuck in `in_progress` beyond the worker timeout.
- Mismatch errors grouped by one client version after a release.
- Replay responses served across tenant or credential boundaries.
- High store error rate, followed by either mutation failure or duplicate
  effects.
- Sudden growth in stored response size.
- Cleanup lag that pushes the store beyond capacity.

Dashboard panels should split first claims, replays, conflicts, mismatches,
expired retries, and store failures by operation. Trace spans should include
idempotency state transitions: `claim.new`, `claim.exists`, `fingerprint.match`,
`fingerprint.mismatch`, `result.stored`, and `result.replayed`. Alerts should
page on duplicate high-value side effects, cross-scope replay attempts, and
store failure on operations that cannot run safely without idempotency.

## 17. Security and privacy implications

Engineering judgement. Idempotency keys reduce one replay class while creating
another data access surface.

The pattern closes the duplicate mutation risk caused by ambiguous transport
failure. That matters most for operations with money, inventory, identity,
access, or legal effect. It also gives incident responders a command identity
for correlating repeated attempts.

The pattern opens a stored-response access path. If the key alone retrieves a
past response, the key behaves like a capability. Adyen warns that using unique
random keys helps prevent two API credentials under the same account from
accessing each other's responses, and also notes that lowering credential
access later does not stop retrieval of prior responses when the user still has
access to prior keys
([Adyen API idempotency docs](https://docs.adyen.com/development-resources/api-idempotency),
verified 2026-08-02). The safe design checks current authorization and scope on
every replay, not only on first execution.

Keys should be high entropy. The IETF draft recommends UUIDs or similar random
identifiers and says keys must not be reused with a different payload
([IETF HTTPAPI draft, section 2.2](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header),
verified 2026-08-02). Sequential keys make guessing and collision easier.
Embedding personal data, email addresses, or card details in keys creates
avoidable privacy exposure in logs, metrics, and URLs. Keys should not be sent
in query strings because query strings are widely logged by intermediaries.

Stored fingerprints and responses need retention policy. A fingerprint can
still reveal sensitive structure if it is built from raw fields and logged.
Store only what replay and mismatch detection need. Encrypt or tokenize stored
responses for sensitive operations. Give cleanup the same audit treatment as
other security-relevant data deletion.

The pattern is silent on authorization correctness, business rule correctness,
and downstream trust. It does not prove the caller was allowed to issue the
first command. It does not stop a malicious authorized caller from issuing two
different keys for two real commands. It does not make a non-idempotent
downstream provider safe unless the provider receives its own stable key or the
local system has another recovery strategy.

## 18. References

- Adyen. "API idempotency." Adyen Docs.
  <https://docs.adyen.com/development-resources/api-idempotency>. Verified
  2026-08-02.
- Amazon Web Services. "Idempotency utility." Powertools for AWS Lambda
  Python documentation.
  <https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/>.
  Verified 2026-08-02.
- Amazon Web Services. "DynamoDB condition expression CLI example." Amazon
  DynamoDB Developer Guide.
  <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html>.
  Verified 2026-08-02.
- IETF HTTPAPI Working Group, Jayadeba Jena and Sanjay Dalal.
  "The Idempotency-Key HTTP Header Field." Internet-Draft
  draft-ietf-httpapi-idempotency-key-header-07, published 2025-10-15, expired
  2026-04-18.
  <https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header>.
  Verified 2026-08-02.
- Leach, Brandur. Stripe Engineering Blog article on idempotency, 2017-02-22.
  <https://stripe.com/blog/idempotency>. Verified 2026-08-02.
- Nottingham, Mark, Erik Wilde, and Sanjay Dalal. RFC 9457, "Problem Details
  for HTTP APIs." Internet Engineering Task Force, July 2023.
  <https://www.rfc-editor.org/rfc/rfc9457.html>. Verified 2026-08-02.
- PayPal. "Idempotency." PayPal Developer REST API reference.
  <https://developer.paypal.com/api/rest/reference/idempotency/>. Verified
  2026-08-02.
- PostgreSQL Global Development Group. "INSERT." PostgreSQL 18 Documentation.
  <https://www.postgresql.org/docs/current/sql-insert.html>. Verified
  2026-08-02.
- Redis. "SET." Redis command documentation.
  <https://redis.io/docs/latest/commands/set/>. Verified 2026-08-02.
- Reschke, Julian, Mark Nottingham, and Roy T. Fielding. RFC 9110, "HTTP
  Semantics." Internet Engineering Task Force, June 2022, section 9.2.2.
  <https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods>.
  Verified 2026-08-02.
- Square. "Create payment." Square Payments API reference.
  <https://developer.squareup.com/reference/square/payments-api/create-payment>.
  Verified 2026-08-02.
- Stripe. "Idempotent requests." Stripe API Reference.
  <https://docs.stripe.com/api/idempotent_requests?lang=curl>. Verified
  2026-08-02.
