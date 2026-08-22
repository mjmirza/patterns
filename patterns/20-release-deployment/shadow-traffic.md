---
name: Shadow Traffic
slug: shadow-traffic
family: 20-release-deployment
maturity: canonical
category: Deployment
aliases: [Traffic Mirroring, Dark Traffic, Traffic Shadowing]
first_described: 'Istio traffic mirroring documentation; Envoy Proxy RequestMirrorPolicy documentation'
related: [canary-release, blue-green-deployment]
verified: true
---

# Shadow Traffic

## Name and Lineage

Shadow Traffic (also called Traffic Mirroring, Dark Traffic, or Traffic Shadowing) duplicates live production traffic and sends the copy to a new or candidate version of a service, while the copy's response is discarded or only logged for comparison, never returned to the real client. The mechanism and its risk-free framing are documented directly in Istio's traffic mirroring feature and in Envoy Proxy's RequestMirrorPolicy, both service mesh and proxy layers that implement mirroring as a first-class routing capability.

## Problem and Context

A team wants to know how a new version of a service behaves under real production traffic and load, not synthetic test traffic, before that version is trusted to serve a single real user. Canary Release exposes a small percentage of real users to the new version's actual responses, which means any defect in the new version, however small the percentage, is felt by real people. Shadow Traffic solves the same real-traffic-validation problem with zero user-facing risk, by sending a copy of the traffic to the new version and discarding its output entirely, so the new version is stress-tested against real conditions without ever being in the response path a user sees.

## Forces

- The new version must be able to receive a duplicated request without any side effect the primary path would not also have, since the request is real (its response is discarded, but if the request itself writes to a shared database or sends a real email, mirroring it duplicates that side effect too).
- Mirroring adds real infrastructure load, since every mirrored request costs compute and network capacity on top of the primary request, even though its response is thrown away.
- Comparing the shadow version's output against the primary version's output (when that comparison is done at all) requires infrastructure to log, diff, or otherwise analyze two response streams instead of one.
- The shadow version's latency and errors must not be allowed to affect the primary request path, which requires mirroring to happen out of band, fire and forget, never blocking on the shadow response.
- A destructive or non-idempotent operation (a write, a charge, a send) is unsafe to mirror as-is, and typically needs shadow-specific isolation (a shadow database, a stubbed downstream) before shadow traffic can safely include it.

## Applicability

Use Shadow Traffic when a new version needs to be validated against real production traffic and load, with zero tolerance for any user-facing risk during that validation, and when the operations being mirrored are read-only or can be made safe to duplicate without a real side effect.

### Non-applicability

Not the right choice when the operation being tested is inherently destructive or non-idempotent (a payment charge, a message send, a write with side effects) and cannot be safely isolated from the mirrored copy, since mirroring a write means that write happens twice for real. Not the right choice when the goal is to observe how real users respond to the new version's actual behavior, which requires Canary Release's real, user-facing exposure rather than a discarded response. Not the right choice when the infrastructure cannot absorb the extra load of duplicating every mirrored request on top of the primary traffic.

## Structure

A proxy or service mesh sits in front of the live service and is configured with a mirror policy naming the shadow destination. For every request (or a configured percentage of requests) that the proxy routes to the primary service, it also sends a copy to the shadow destination, out of band of the critical request path. The shadow destination processes the request and returns a response, which the proxy discards, logs, or forwards to a comparison system, but never sends back to the original client.

## ASCII Diagram

```
  client --> [Live Service v1] --> response returned to client
                    |
                    +--- mirrored copy --> [Shadow Service v2]
                                                |
                                                v
                                          response discarded
                                          or logged for comparison
                                          never returned to client
```

## Dynamics

A real client request arrives at the proxy or mesh sidecar in front of the live service. The proxy forwards the request to the primary (live) version and, per its mirror policy, also forwards a copy to the shadow version. The primary version processes the request and its response is returned to the client immediately, without waiting on the shadow version at all. The shadow version processes its copy independently and returns a response, which the proxy or a separate comparison pipeline discards or logs, never returning it to the real client. Because the mirroring happens fire and forget, a slow or failing shadow version has no effect on the primary request's latency or success.

## Implementation Variants

- **Service mesh mirroring.** Istio's traffic mirroring, configured on a VirtualService, mirrors a percentage of traffic from one service version to another.
- **Proxy-level mirroring.** Envoy's RequestMirrorPolicy, configured on a route, shadows traffic from one upstream cluster to another.
- **Load-balancer or gateway mirroring.** an API gateway or load balancer configured to duplicate a request stream to a secondary backend.
- **Application-level shadowing.** the service itself forks an outbound call to a shadow endpoint after handling the primary request, used when no proxy-level mirroring is available.

## Known Production Uses

Istio (https://istio.io/latest/docs/tasks/traffic-management/mirroring/) documents traffic mirroring as a built-in VirtualService capability for validating a new service version against real traffic. Envoy Proxy ships RequestMirrorPolicy as a native route configuration option, used by services running behind an Envoy-based mesh or gateway to shadow traffic between clusters.

## Consequences

### Benefits

- The new version is validated against real production traffic and load with zero risk to actual users, since its response is never served.
- Performance, error rate, and behavior under real conditions can be measured before the new version ever serves a single real response.
- A slow or failing shadow version has no effect on the primary request's latency or success, since mirroring is fire and forget.

### Costs

- Every mirrored request costs real infrastructure capacity on top of the primary request, doubling load for the mirrored portion of traffic.
- Any operation with a real side effect (a write, a charge, a send) is unsafe to mirror without isolating the shadow path from production data.
- Comparing the shadow version's behavior against the primary version's, when that comparison matters, requires building and maintaining a separate analysis pipeline.

## Failure Modes

- **Duplicated side effects.** a mirrored write, charge, or send happens for real against production systems, because the operation was not made safe to duplicate before mirroring was enabled.
- **Unbounded resource use.** the shadow destination is under-provisioned for the mirrored load and falls behind or crashes, without anyone noticing because its failures never surface to a real user.
- **Stale or misleading comparison.** the shadow version diverges from the primary version's environment (a different downstream mock, a different data snapshot) so its behavior under shadow traffic does not actually predict its behavior once it goes live for real.
- **Silent mirror-policy drift.** a mirror policy is left enabled long after its validation purpose is done, quietly costing capacity with no ongoing benefit.

## Trade-off Matrix

| Dimension | Shadow Traffic | Canary Release | Blue-Green Deployment |
|---|---|---|---|
| User-facing risk during validation | None (response discarded) | Some (a percentage of real users see it) | None during the rollout, full risk at the instant of cutover |
| Extra infrastructure load | Real traffic duplicated to the shadow version | None beyond the canary group's own traffic | Full second environment during rollout |
| Safe for non-idempotent operations | No, without isolation | Yes (real responses are served normally) | Yes |
| What it validates | Real traffic and load against unseen output | Real traffic and real user-facing behavior | The new version once it takes over all traffic |

## Related and Incompatible Patterns

Related to Canary Release and Blue-Green Deployment, both alternative pre-release validation strategies. Shadow Traffic is often used as a validation step BEFORE a Canary Release or a Blue-Green cutover, since it proves the new version can handle real load before any real user is exposed to its actual output. Incompatible with mirroring a non-idempotent operation without first isolating its side effects, since the mirrored copy is a real request against production systems.

## Refactoring Path

### Introducing It

Start from testing a new version only against synthetic or staging traffic. Introduce a proxy or service mesh capable of request mirroring (Istio, Envoy, or an application-level fork), configure a mirror policy naming the new version as the shadow destination, and confirm any operation being mirrored is safe to duplicate before enabling the policy.

### Removing It

Once the shadow version has been validated against enough real traffic and load, remove the mirror policy and move to Canary Release (to observe real user-facing behavior) or directly to a Blue-Green Deployment or Rolling Deployment cutover, depending on how much additional real-user validation is wanted.

## Testing and Verification

Verify the mirror policy actually discards the shadow response and never returns it to the real client, by inspecting the response the client receives during a test with the shadow destination intentionally returning a different value. Verify any operation the mirror policy applies to is idempotent or has been isolated from production side effects, by running the mirrored path against a staging or shadow-specific backend first. Verify the primary request's latency and success rate are unaffected by a slow or failing shadow destination.

## Observability Signals

Track the volume and error rate of mirrored requests separately from primary requests, the latency and resource usage of the shadow destination under mirrored load, and, where a comparison pipeline exists, the divergence rate between primary and shadow responses for the same request.

## Security and Privacy Implications

A mirrored request carries the same real user data as the primary request, so the shadow destination must meet the same data-handling, access-control, and retention requirements as the primary service. Logging or storing shadow responses for comparison must not retain more real user data than the primary service itself is permitted to retain, and any authentication or authorization applied to the primary request must also be honored (or the request rejected) on the shadow path.

## Code Examples

### Swift

```swift
struct ShadowTrafficRouter {
    var forwardPrimary: (String) -> String
    var forwardShadow: (String) -> Void

    // Forwards the request to the primary path and mirrors it to the
    // shadow path without waiting on or returning the shadow response.
    func handle(request: String) -> String {
        forwardShadow(request)
        return forwardPrimary(request)
    }
}
```

### Kotlin

```kotlin
class ShadowTrafficRouter(
    private val forwardPrimary: (String) -> String,
    private val forwardShadow: (String) -> Unit
) {
    // Forwards the request to the primary path and mirrors it to the
    // shadow path without waiting on or returning the shadow response.
    fun handle(request: String): String {
        forwardShadow(request)
        return forwardPrimary(request)
    }
}
```

### Python

```python
class ShadowTrafficRouter:
    def __init__(self, forward_primary, forward_shadow):
        self.forward_primary = forward_primary
        self.forward_shadow = forward_shadow

    def handle(self, request):
        # Forwards the request to the primary path and mirrors it to the
        # shadow path without waiting on or returning the shadow response.
        self.forward_shadow(request)
        return self.forward_primary(request)
```

## References

- Istio, Mirroring, https://istio.io/latest/docs/tasks/traffic-management/mirroring/
- Envoy Proxy, RequestMirrorPolicy (route_components.proto), https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto
