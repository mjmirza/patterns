---
name: Idempotent API
slug: idempotent-api
family: 19-api-design
category: Data Fetching
aliases: [Idempotency Key, Safe Retry Pattern]
first_described: 'Stripe, official idempotent requests documentation'
maturity: canonical
related: [webhook-receiver, pagination-pattern]
incompatible_with: []
verified: 2026-08-22
---

# Idempotent API

## 1. Name, aliases, and lineage

Idempotent API. Also called Idempotency Key or Safe Retry Pattern. The pattern is the design of a state-changing API operation so that performing the exact same request more than once, using the same client-generated idempotency key, produces the side effect exactly once, no matter how many times the request itself is retried. Stripe's own documentation states the purpose directly. the API supports idempotency for safely retrying requests without accidentally performing the same operation twice (https://docs.stripe.com/api/idempotent_requests).

The lineage runs from a plain, unavoidable fact of any network call. a client that sends a request and never receives a response genuinely cannot tell whether the operation actually happened on the server or was lost before it arrived. Stripe's documentation names the exact scenario this pattern exists for. when creating or updating an object, use an idempotency key, then, if a connection error occurs, you can safely repeat the request without risk of creating a second object or performing the update twice (https://docs.stripe.com/api/idempotent_requests).

## 2. Problem and context

A client that sends a state-changing request, creating a payment, placing an order, and does not receive a response before its own timeout fires cannot distinguish between two very different outcomes. the request never reached the server at all, or the request reached the server, succeeded, and only the response was lost on the way back. If the client simply retries in either case, and the operation genuinely happened the first time, a naive retry performs the same state-changing action a second time.

The problem this pattern solves is letting a client retry safely after any uncertain outcome, network timeout, dropped connection, an ambiguous error, without risking a duplicate side effect, by giving the server a reliable way to recognize that a retried request is the same logical operation as one it may have already completed.

## 3. Forces

- The client has to generate a key that uniquely identifies one logical operation, and reuse that exact key on every retry of that same operation, never generating a fresh key per attempt.
- The server has to store enough about the first request's outcome to answer a repeated request consistently, which costs real storage and has to expire eventually.
- Two genuinely different requests that happen to reuse the same idempotency key by mistake need a clear, safe rule for what the server does, since honoring the wrong cached result would silently corrupt one of the two operations.
- A request that is still being processed when a retry with the same key arrives needs explicit handling, since the first request has not finished long enough to have a cached result yet.
- Idempotency has to cover the entire operation, including any side effect a partial failure might have already triggered, not just the final response the client sees.

## 4. Applicability and non-applicability

Use Idempotent API for any state-changing operation whose accidental repetition would be genuinely harmful, charging a customer twice, creating a duplicate order, sending a duplicate notification, especially when the operation is reachable over an unreliable network where a client cannot always tell whether its previous attempt succeeded.

This pattern is a non-applicability fit for a read-only operation, which is naturally idempotent already, since reading the same data twice causes no side effect to duplicate in the first place. It is also unnecessary overhead for a state-changing operation whose accidental repetition is genuinely harmless, or that the caller can trivially detect and correct after the fact without any real cost.

## 5. Structure

- Idempotency key. the unique value the client generates once per logical operation and sends with the request.
- Result store. the server-side record mapping an idempotency key to the outcome of the first request that used it.
- Key expiry policy. the rule for how long a stored result is retained before the key can be safely reused for a genuinely new operation.
- Conflict rule. the server's defined behavior when the same key arrives with a request body that does not match the original request.
- In-flight marker. the server-side signal that a request with a given key is still being processed, distinct from a key that already has a completed cached result.

## 6. ASCII structure diagram

```

  Client                                  Server
  ------                                  ------------------------
  request A
  key = "abc-123"  ------------------>  no record for abc-123
                                                |
                                                v
                                          perform operation
                                                |
                                                v
                                          store result under abc-123
  response  <-------------------------------------|

  connection drops before response is seen by client

  retry, same key
  key = "abc-123"  ------------------>  found cached result for abc-123
                                                |
                                                v
                                          return the SAME cached response
                                          (operation NOT performed again)
  response  <-------------------------------------|

```

## 7. Dynamics

1. The client generates a unique idempotency key for a logical operation, before sending the request for the first time.
2. The server checks whether that key already has a stored result, and finding none, marks the key as in-flight and performs the operation.
3. On success or failure, the server stores the resulting status and body under that key, because Stripe's idempotency works by saving the resulting status code and body of the first request made for any given idempotency key, regardless of whether it succeeds or fails (https://docs.stripe.com/api/idempotent_requests).
4. The server returns the response to the client, but the response may never arrive due to a dropped connection or a client-side timeout.
5. If the client retries with the same key, the server finds the stored result and returns it directly, because subsequent requests with the same key return the same result, including 500 errors (https://docs.stripe.com/api/idempotent_requests), without performing the underlying operation a second time.
6. Once the key's expiry window passes, the stored result is discarded, and that key becomes available again for a genuinely new logical operation in the future.

## 8. Implementation variants

- Client-generated key, server-side cache. the client mints the key, and the server stores the full result keyed by it, the shape most public APIs expose to their own callers.
- Deterministic key derivation. the key is computed from the request's own content, such as a hash of its meaningful fields, rather than an arbitrary client-chosen value, at the cost of two genuinely different requests colliding if their meaningful fields happen to match.
- Database-level idempotency via a unique constraint. the operation itself writes a row with a unique constraint on the idempotency key, letting the database reject a duplicate insert directly rather than relying on an application-level cache lookup.
- In-flight locking. the server holds a lock on a key while the first request is still being processed, so a retry that arrives before the first attempt finishes waits rather than racing to perform the operation twice.

## 9. Known production uses

- Stripe's payments API is the reference implementation most developers learn this pattern from directly, with documented idempotency key behavior across its create and update endpoints.
- PayPal's REST API supports a client-supplied request identifier on payment-creating endpoints for the same safe-retry purpose.
- AWS's API Gateway and several individual AWS service APIs, including EC2's instance launch operation, accept a client token for the same duplicate-prevention purpose on resource-creating calls.

## 10. Consequences

Benefits.

- A client can retry a state-changing request after any uncertain network outcome without risking a duplicate side effect.
- The server has a single, well defined answer for what happens on a genuine retry, rather than leaving the caller to reason about it case by case.
- Retry logic at the client becomes simpler, since it no longer has to distinguish a safe retry from an unsafe one.

Costs.

- The server has to store and eventually expire a result per idempotency key, which is real storage and operational overhead an operation without this pattern does not carry.
- A conflict between two different requests that accidentally reuse the same key has to be handled explicitly, or it silently returns the wrong result to one of the two callers.
- The client bears responsibility for generating and consistently reusing the key correctly, and a client bug that generates a fresh key per retry defeats the pattern entirely.

## 11. Failure modes

- Fresh key per retry. a client that mistakenly generates a new idempotency key on every retry attempt gets no protection at all, since the server never recognizes the retries as the same operation.
- Unhandled key conflict. a server that returns the cached result for a key without checking whether the new request body actually matches the original silently answers a different operation with a stale result.
- Race between concurrent retries. two retries with the same key arriving at nearly the same time, before the first attempt's result is stored, can both proceed to perform the operation if the server has no in-flight locking.
- Premature key expiry. a stored result that expires too soon lets a legitimate retry, arriving after the expiry window, perform the operation a second time.

## 12. Trade-off matrix

| Dimension | With this pattern | Without this pattern |

|---|---|---|

| Safety of a client retry after a timeout | Safe, no duplicate side effect | Unsafe, may duplicate the operation |
| Server-side storage cost | One stored result per key, until expiry | None |
| Client implementation complexity | Must generate and reuse a key correctly | Simpler, no key management |
| Handling of a genuine key collision | Requires an explicit conflict rule | Not applicable |
| Debuggability of a retried request | Traceable to one logical operation via the key | Hard to tell a retry from a new request |

## 13. Related and incompatible patterns

Related to Webhook Receiver, whose own processed-event log applies the identical deduplication idea to an inbound event delivery rather than an outbound client request. Related to Pagination Pattern, a different discipline for the same underlying network-reliability concern, letting a client resume a large read safely rather than retry a write safely. Not incompatible with a naturally idempotent operation, such as a plain read, which needs no idempotency key at all because repeating it has no side effect to duplicate in the first place.

## 14. Refactoring path in and out

Introducing it.

1. Identify every state-changing endpoint whose accidental repetition would be genuinely harmful.
2. Add an idempotency key parameter to each such endpoint, documenting that the client must generate one key per logical operation and reuse it on every retry.
3. Build the server-side result store, keyed by the idempotency key, and store the full outcome, success or failure, of the first request under that key.
4. Add the conflict rule for a key reused with a mismatched request body, and the in-flight handling for a retry that arrives before the first attempt finishes.

Removing it.

1. Confirm the operation genuinely no longer needs protection, typically because it has become naturally idempotent through a different mechanism, such as a database-level unique constraint on the operation's own natural key.
2. Remove the idempotency key parameter from the endpoint's contract, coordinating the change with every client that currently sends one.
3. Remove the server-side result store and its expiry job once no client is expected to send a key anymore.
4. Confirm the replacement safety mechanism is actually in place and tested before the explicit idempotency handling is removed.

## 15. Testing and verification

- Test that two requests sent with the same idempotency key and the same body produce exactly one occurrence of the underlying side effect.
- Test the conflict rule directly, sending two requests with the same key but different bodies, and asserting the server responds according to its documented conflict behavior rather than silently returning either result.
- Test the in-flight case, sending a second request with the same key before the first has finished processing, and asserting no duplicate side effect occurs.
- Test that a key past its expiry window is treated as a genuinely new operation, not as a cached retry.

## 16. Observability signals

- Idempotency key reuse rate, the fraction of incoming requests whose key already had a stored result, a useful signal for how often clients are actually retrying.
- Conflict rate, the fraction of key reuses whose request body did not match the original, which should stay near zero and signals a client bug when it does not.
- Result store size and growth rate, watched against the configured expiry window.
- In-flight collision rate, the frequency of a retry arriving while the first attempt for the same key is still being processed.

## 17. Security and privacy implications

An idempotency key is scoped to a single client's own operations, and a server that fails to scope the result store per authenticated caller risks one client's cached result being returned to a different client who happens to guess or reuse the same key value. The stored result itself typically contains the same sensitive response data the original request would have returned, so the result store needs the same access control and retention discipline as the underlying resource it represents, and should not outlive its documented expiry window.

## 18. Code examples

### Swift

```swift

struct StoredResult {
    let requestHash: Int
    let response: String
}

final class IdempotencyStore {
    private var results: [String: StoredResult] = [:]

    // Returns a cached response for a matching retry, or nil for a genuinely new key.
    func lookup(key: String, requestHash: Int) -> String? {
        guard let stored = results[key] else {
            return nil
        }
        precondition(stored.requestHash == requestHash,
            "idempotency key reused with a different request")
        return stored.response
    }

    // Stores the result of a first-time request under its idempotency key.
    func store(key: String, requestHash: Int, response: String) {
        results[key] = StoredResult(requestHash: requestHash, response: response)
    }
}

```

### Kotlin

```kotlin

data class StoredResult(val requestHash: Int, val response: String)

class IdempotencyStore {
    private val results = mutableMapOf<String, StoredResult>()

    // Returns a cached response for a matching retry, or null for a genuinely new key.
    fun lookup(key: String, requestHash: Int): String? {
        val stored = results[key] ?: return null
        require(stored.requestHash == requestHash) {
            "idempotency key reused with a different request"
        }
        return stored.response
    }

    // Stores the result of a first-time request under its idempotency key.
    fun store(key: String, requestHash: Int, response: String) {
        results[key] = StoredResult(requestHash, response)
    }
}

```

### Python

```python

class IdempotencyStore:
    def __init__(self):
        self.results = {}

    def lookup(self, key, request_hash):
        """Returns a cached response for a matching retry, or None for a new key."""
        stored = self.results.get(key)
        if stored is None:
            return None
        stored_hash, response = stored
        if stored_hash != request_hash:
            raise ValueError("idempotency key reused with a different request")
        return response

    def store(self, key, request_hash, response):
        """Stores the result of a first-time request under its idempotency key."""
        self.results[key] = (request_hash, response)

```

## 19. References

- Stripe, official idempotent requests documentation, https://docs.stripe.com/api/idempotent_requests
