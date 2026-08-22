---
name: Webhook Receiver
slug: webhook-receiver
family: 19-api-design
category: Data Fetching
aliases: [Webhook Endpoint, Push Notification Receiver]
first_described: 'Stripe, official webhooks documentation'
maturity: canonical
related: [grpc-streaming, idempotent-api]
incompatible_with: []
verified: 2026-08-22
---

# Webhook Receiver

## 1. Name, aliases, and lineage

Webhook Receiver. Also called Webhook Endpoint or Push Notification Receiver. The pattern is an HTTP endpoint an application exposes so a third-party service can push an asynchronous event notification to it, the moment the event happens, rather than the application repeatedly asking whether anything new has occurred. Because the sender controls delivery and the network sits between the two sides, a well built receiver has to treat every incoming delivery as potentially repeated. Stripe's own webhooks documentation states this directly. webhook endpoints might occasionally receive the same event more than once (https://docs.stripe.com/webhooks).

The lineage runs from the practical reality that a webhook sender guarantees delivery at least once, not exactly once, and cannot itself know for certain whether a given attempt was received. every mature provider's own documentation, Stripe's among the clearest, turns that reality into two concrete conventions for the receiver. deduplicate by event identity, and verify the payload actually came from the claimed sender before acting on it.

## 2. Problem and context

An application that wants to react to something happening in a third-party system, a payment succeeding, a repository receiving a new commit, a support ticket changing status, either has to poll that system repeatedly asking whether anything changed, or expose an endpoint the third-party system can call directly the moment the event occurs. Polling wastes calls on the common case of nothing having changed, and adds a delay bounded by the polling interval before the application notices a real change.

The problem this pattern solves is receiving that event notification the instant it happens, while handling the two realities that come with accepting an inbound push from an untrusted network path. the same event may arrive more than once, and any request claiming to be from the sender has to be verified rather than trusted on its face, since without verification, an attacker could send fake webhook events to your endpoint to trigger actions like fulfilling orders, granting account access, or modifying records (https://docs.stripe.com/webhooks).

## 3. Forces

- The sender's own retry logic, reacting to a timeout, a transient network failure, or a slow response, can deliver the exact same event to the receiver more than once.
- A receiver that does slow processing work inside the request handler risks the sender timing out and retrying, which produces exactly the duplicate delivery the receiver has to guard against in the first place.
- Verifying a payload's signature has to happen before any of that payload's content is trusted or acted on, but the verification step itself adds work to every single request, including the vast majority that are genuinely legitimate.
- The receiver's endpoint is, by necessity, reachable from the public internet, which makes it a target for a request that merely resembles a real event without originating from the real sender.
- Event ordering is not guaranteed. two related events can arrive out of the order they actually occurred in, so a receiver cannot assume delivery order matches occurrence order.

## 4. Applicability and non-applicability

Use Webhook Receiver whenever an application needs to react to an event happening inside a third-party system it does not control, and that third-party system offers a webhook delivery mechanism, favoring this over polling whenever near-real-time reaction matters more than the operational simplicity of a scheduled poll.

This pattern is a non-applicability fit when the third-party system offers no webhook mechanism at all, leaving polling as the only option regardless of preference. It is also a poor fit for an application that cannot expose a publicly reachable HTTP endpoint at all, since a webhook, unlike an outbound poll, requires the receiver to be reachable from the sender's network.

## 5. Structure

- Receiving endpoint. the publicly reachable HTTP route the third-party sender calls whenever a subscribed event occurs.
- Signature verification. the step that confirms the incoming request's payload genuinely originated from the claimed sender, before any of its content is trusted.
- Event identifier. the unique id the sender attaches to each event, the key a receiver uses to recognize and discard a duplicate delivery.
- Processed-event log. the record of every event identifier the receiver has already handled, checked before processing a newly arrived event.
- Fast acknowledgement. the receiver's prompt response confirming receipt, decoupled from any slower processing the event itself triggers.

## 6. ASCII structure diagram

```

  Third-party sender                    Receiver
  --------------------                  ------------------------
  event occurs
     |
     v
  POST /webhooks/events  -------------->  verify signature
     (event id, payload)                        |
                                                 v
                                          seen this event id?
                                                 |
                                   +-------------+-------------+
                                   |                           |
                                  yes                          no
                                   |                           |
                                   v                           v
                             respond 200                log event id
                             (no-op, dup)                      |
                                                                v
                                                          respond 200
                                                                |
                                                                v
                                                     queue slower processing

```

## 7. Dynamics

1. An event occurs inside the third-party sender's system, and the sender issues an outbound HTTP request to the receiver's registered webhook endpoint, carrying the event's unique identifier and its payload.
2. The receiver verifies the request's signature against a shared secret before trusting any of the payload's content, following the same discipline Stripe's own guidance states. always verify that webhook events originate from Stripe before acting on them (https://docs.stripe.com/webhooks).
3. The receiver checks the event's identifier against its processed-event log, and if the identifier has already been logged, it responds successfully without re-processing, because you can guard against duplicated event receipts by logging the event ids you have processed, and then not processing already-logged events (https://docs.stripe.com/webhooks).
4. For a genuinely new event, the receiver logs the identifier and responds with a fast acknowledgement, before any slower downstream processing begins.
5. If the sender does not receive a timely acknowledgement, it retries delivery of the same event, which is exactly the duplicate-delivery case the identifier check in step 3 exists to catch on the retried attempt.
6. The slower processing work the event actually triggers runs after acknowledgement, decoupled from the sender's own retry and timeout behavior.

## 8. Implementation variants

- Synchronous fast-path handling. the receiver does its entire, genuinely cheap, unit of work directly inside the request handler and returns the final result immediately.
- Acknowledge-then-queue. the receiver verifies and deduplicates the event, immediately acknowledges, then hands the event off to a background queue for the actual processing.
- Signed-header verification. the sender includes a cryptographic signature of the payload in a request header, computed with a shared secret, which the receiver recomputes and compares.
- Time-bounded replay window. the receiver rejects any request whose timestamp is older than a configured window, closing off a captured-and-replayed request even if its signature would otherwise still verify.

## 9. Known production uses

- Stripe's own webhook delivery system is the reference implementation many developers learn this pattern from directly, with documented signature verification and duplicate-event handling guidance.
- GitHub delivers repository and organization events, a push, a pull request opening, a check run completing, to a registered webhook endpoint using the same signed-payload and at-least-once delivery model.
- Shopify delivers order, product, and customer events to merchant-configured webhook endpoints, requiring the same signature verification before a merchant's system acts on an incoming event.

## 10. Consequences

Benefits.

- The receiving application reacts to an event the moment it happens, instead of waiting for the next scheduled poll.
- No wasted calls checking for a change that has not happened, unlike polling.
- The receiving application controls its own processing pace once an event is acknowledged, rather than being tied to the sender's request timeout.

Costs.

- The receiver has to be built to handle a duplicate delivery correctly, since the sender's own retry behavior guarantees at-least-once, not exactly-once, delivery.
- Signature verification and the processed-event log both add real implementation and operational work that a simple polling loop does not need.
- The receiver has to stay reachable and respond quickly enough that the sender does not time out and unnecessarily retry an event that was actually received.

## 11. Failure modes

- Skipped signature verification. a receiver that trusts an incoming request's payload without verifying its signature can be tricked into acting on a forged event, exactly the risk of triggering actions like fulfilling orders, granting account access, or modifying records that verification exists to prevent (https://docs.stripe.com/webhooks).
- No deduplication. a receiver that reprocesses every delivery, including a retried one, can double-apply an action, charging a customer twice or sending a duplicate notification.
- Slow synchronous processing. a receiver that performs its full downstream work inside the request handler causes the sender to time out and retry, generating the very duplicate delivery a fast acknowledgement is meant to avoid.
- Unbounded processed-event log. a log of every seen event identifier that is kept forever, with no expiry or bound, grows without limit as the receiver stays in production.

## 12. Trade-off matrix

| Dimension | Webhook receiver | Polling |

|---|---|---|

| Time to react to an event | Near-immediate | Bounded by the polling interval |
| Wasted calls on no change | None | One per poll that finds nothing |
| Duplicate-delivery handling required | Yes, at-least-once delivery | Not applicable |
| Public endpoint required | Yes | No |
| Signature verification required | Yes | Not applicable |

## 13. Related and incompatible patterns

Related to gRPC Streaming, an alternative way to deliver a sequence of events over time, holding one long-lived connection open rather than pushing each event as its own separate call. Related to Idempotent API, the discipline the processed-event log applies directly. handling a repeated delivery safely by recognizing it rather than assuming it never happens. Not incompatible with polling. an application can use a webhook for near-real-time reaction and a periodic poll as a reconciliation safety net in case a webhook delivery was ever missed entirely.

## 14. Refactoring path in and out

Introducing it.

1. Confirm the third-party service offers webhook delivery, and read its own documented conventions for event identifiers, signature format, and retry behavior.
2. Build the receiving endpoint with signature verification as its first step, rejecting any request that fails verification before touching its payload content.
3. Add a processed-event log keyed by the sender's event identifier, checked before any processing begins.
4. Separate the fast acknowledgement from any slower downstream work, so the sender never times out waiting for processing that could happen after the response is sent.

Removing it.

1. Confirm the application genuinely no longer needs near-real-time reaction to this event, typically because it has moved to a polling or batch reconciliation model instead.
2. Unregister the webhook subscription with the third-party sender, so it stops attempting delivery.
3. Remove the receiving endpoint, its signature verification, and its processed-event log once no delivery is expected to arrive.
4. Confirm any downstream processing that depended on the webhook's event is now triggered by whatever replaced it.

## 15. Testing and verification

- Test the signature verification step in isolation, asserting a correctly signed payload passes and a tampered or unsigned payload is rejected.
- Test that delivering the exact same event identifier twice results in the event being processed exactly once.
- Test the fast-acknowledgement path directly, asserting the response returns before any slower downstream processing completes.
- Test the receiver's behavior on a malformed or unexpected payload shape, confirming it rejects the request rather than crashing or silently accepting invalid data.

## 16. Observability signals

- Signature verification failure rate, distinguishing a genuine attack attempt from a misconfigured shared secret.
- Duplicate-delivery rate, the fraction of incoming events whose identifier was already in the processed-event log, a useful signal for how often the sender is retrying.
- Time from request receipt to acknowledgement, since a rising trend here risks tipping the sender into unnecessary retries.
- Processed-event log size and growth rate, watched against whatever expiry or bound has been configured for it.

## 17. Security and privacy implications

A receiver that skips signature verification is directly exposed to a forged request, since without verification, an attacker could send fake webhook events to your endpoint to trigger actions like fulfilling orders, granting account access, or modifying records (https://docs.stripe.com/webhooks). The shared secret used to verify a signature is itself sensitive and needs the same handling as any other credential, never logged and never committed to source control. A receiver that logs the full payload of every event for debugging purposes has to be careful that the payload does not carry personal or sensitive data that should not sit in a general-purpose log store.

## 18. Code examples

### Swift

```swift

import CryptoKit

struct WebhookReceiver {
    let secret: SymmetricKey
    var processedEventIds: Set<String> = []

    // Returns true only for a genuinely new, correctly signed event.
    mutating func accept(eventId: String, payload: Data, signature: Data) -> Bool {
        let computed = HMAC<SHA256>.authenticationCode(for: payload, using: secret)
        guard Data(computed) == signature else {
            return false
        }
        guard !processedEventIds.contains(eventId) else {
            return false
        }
        processedEventIds.insert(eventId)
        return true
    }
}

```

### Kotlin

```kotlin

import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class WebhookReceiver(private val secret: ByteArray) {
    private val processedEventIds = mutableSetOf<String>()

    // Returns true only for a genuinely new, correctly signed event.
    fun accept(eventId: String, payload: ByteArray, signature: ByteArray): Boolean {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret, "HmacSHA256"))
        val computed = mac.doFinal(payload)
        if (!computed.contentEquals(signature)) return false
        if (processedEventIds.contains(eventId)) return false
        processedEventIds.add(eventId)
        return true
    }
}

```

### Python

```python

import hashlib
import hmac

class WebhookReceiver:
    def __init__(self, secret):
        self.secret = secret
        self.processed_event_ids = set()

    def accept(self, event_id, payload, signature):
        """Returns True only for a genuinely new, correctly signed event."""
        computed = hmac.new(self.secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(computed, signature):
            return False
        if event_id in self.processed_event_ids:
            return False
        self.processed_event_ids.add(event_id)
        return True

```

## 19. References

- Stripe, official webhooks documentation, https://docs.stripe.com/webhooks
