---
name: Static Stability
slug: static-stability
family: 21-sre-operations
category: Structural
aliases: [Bimodal Behavior Avoidance, Statically Stable Design, Single Normal Mode]
first_described: 'AWS, Static Stability Using Availability Zones, Builders Library'
maturity: canonical
related: [graceful-degradation, error-budget]
incompatible_with: []
verified: 2026-08-22
---

# Static Stability

## 1. Name, aliases, and lineage

Static Stability. Also called Bimodal Behavior Avoidance, Statically Stable Design, or Single Normal Mode. The term and the practice come directly from AWS's own engineering practice, in a Builders Library article on multi availability zone resilience. In a statically stable design, the overall system keeps working even when a dependency becomes impaired (https://aws.amazon.com/builders-library/static-stability-using-availability-zones/).

The lineage runs from a specific, hard-won operational lesson about multi availability zone systems. a system that behaves one way when everything is healthy and a genuinely different way once a peer or a control plane becomes unreachable is far riskier than one that always behaves the same way. AWS's own Well-Architected Framework states the resulting principle directly. workloads should be statically stable and only operate in a single normal mode (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html).

## 2. Problem and context

A distributed system spread across multiple availability zones or regions often relies on real-time coordination with a central control plane, or with its peers, to make decisions. That coordination usually works, so the system's normal, tested behavior assumes it will keep working. The problem appears exactly when that assumption breaks. a zone loses connectivity to the control plane or to a peer region, and the system now has to behave in a mode nobody has tested nearly as thoroughly as the normal one.

This is the bimodal behavior problem this pattern names directly. a system with two distinct behaviors, one for the common case and one for the rare, poorly exercised failure case, is more likely to fail in a new and surprising way exactly when it is under the most stress. The problem this pattern solves is designing the system so each independent unit can keep operating using only its own already known, statically cached state, so there is only one behavior to test, trust, and rely on.

## 3. Forces

- Relying on real-time coordination is often simpler to build and keeps data fresher than relying on statically cached state.
- A statically cached copy of state can go stale, so the system needs a deliberate refresh strategy that keeps the cache close enough to correct without depending on it being perfectly current.
- A rarely exercised failure-mode behavior is inherently less trusted than the normal, constantly exercised one, since it has far fewer real production runs behind it.
- Designing every independent unit to operate on its own local, cached state, rather than a shared, centrally coordinated one, adds real engineering complexity up front.
- A system already built around real-time coordination has to be deliberately refactored toward this pattern, which is a genuine migration, not a small config change.

## 4. Applicability and non-applicability

Use Static Stability for any distributed system spread across multiple availability zones or regions, where losing connectivity to a central control plane or a peer zone is a real, plausible failure mode, and where continuing to operate on already known state is clearly better than stopping or behaving differently. It is especially valuable for the components closest to serving live traffic, where a bimodal failure would directly and immediately affect the person using the system.

Skip it for a system with a single point of coordination that has no meaningful multi-zone or multi-region failure mode to design around, since building statically cached fallback state for a dependency that genuinely cannot fail independently adds complexity with no real resilience benefit.

## 5. Structure

- Independent unit. the zone-scoped or region-scoped component that must keep operating on its own, without relying on a live connection to a peer or a central control plane.
- Statically cached state. the already known, locally held copy of the data or configuration the independent unit needs to keep operating.
- Refresh path. the mechanism that keeps the statically cached state reasonably current during normal operation, without the unit depending on it being perfectly fresh.
- Single normal mode. the one behavior the unit exhibits whether the control plane or a peer is reachable or not, deliberately avoiding a second, rarely exercised failure-mode behavior.
- Impairment boundary. the explicit scope of what can become unreachable (a peer zone, a central control plane) without the independent unit's own behavior changing.

## 6. ASCII structure diagram

```
  Independent unit
  (zone-scoped or region-scoped)
        |
        v
  reads from Statically cached state
  (kept current by the Refresh path
   during normal operation)
        |
        v
  control plane or peer reachable?
        |
  yes ---+--- no
        |         |
        v         v
  Single normal mode (identical behavior either way)
```

## 7. Dynamics

1. During normal operation, the refresh path keeps each independent unit's statically cached state reasonably current, updating from the control plane or from peers as that coordination succeeds.
2. Each independent unit always reads from its own statically cached state to make decisions, rather than depending on a live round trip to a peer or a central control plane for every decision.
3. If the control plane or a peer becomes unreachable, crossing the impairment boundary, the independent unit simply keeps operating on the state it already has, exactly matching AWS's own framing. the overall system keeps working even when a dependency becomes impaired (https://aws.amazon.com/builders-library/static-stability-using-availability-zones/).
4. Because the unit's behavior does not change based on whether the control plane is reachable, there is only a single normal mode to test, trust, and operate, matching the Well-Architected Framework's own statement that this static stability design verifies the workload only operates in a single mode (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html).
5. Once the control plane or the peer becomes reachable again, the refresh path resumes updating the statically cached state, and normal operation continues exactly as it did throughout, with no separate recovery mode to trigger or verify.

## 8. Implementation variants

- Local configuration cache. each independent unit holds its own cached copy of routing or feature configuration, refreshed periodically, and continues serving on the last known copy if the refresh fails.
- Pre-provisioned capacity. capacity for each zone is provisioned in advance based on a static plan, rather than dynamically requested from a central control plane at the moment it is needed, so a control-plane outage does not prevent a zone from having the capacity it needs.
- Local decision-making. a unit makes its own routing or scaling decisions from its own local, cached view of the system, rather than querying a central coordinator for every decision.
- Degraded-but-consistent fallback. when the cached state does go stale, the unit's behavior degrades predictably and consistently, rather than switching to a genuinely different failure-mode code path.

## 9. Known production uses

- AWS's own Builders Library documents this pattern directly, describing how a statically stable design keeps the overall system working even when a dependency becomes impaired (https://aws.amazon.com/builders-library/static-stability-using-availability-zones/), grounded in AWS's own multi availability zone operational experience.
- The AWS Well-Architected Framework's Reliability Pillar publishes static stability as a named best practice, stating that a workload should only operate in a single normal mode (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html), used as guidance across AWS customers designing multi-zone systems.
- Organizations across the industry that operate multi availability zone or multi-region systems commonly apply this pattern to their most traffic-critical components, favoring locally cached state and pre-provisioned capacity over real-time cross-zone coordination for exactly the components that must not fail together.

## 10. Consequences

### Benefits

- The system keeps working through a real, plausible failure mode (losing connectivity to a control plane or a peer), rather than failing or behaving unpredictably at exactly that moment.
- A single normal mode is far more thoroughly and continuously tested than a rarely exercised failure-mode behavior would ever be, so the behavior a person actually experiences during a real outage is the same well understood behavior seen every day.
- Pre-provisioned capacity and locally cached state remove a whole class of dependency on a central control plane being reachable at the exact moment a decision needs to be made.

### Costs

- Building each independent unit to operate on its own cached state, rather than a simpler, centrally coordinated one, is real, upfront engineering complexity.
- Statically cached state can go stale, so the refresh path itself needs to be designed and maintained carefully.
- Pre-provisioning capacity in advance can mean paying for capacity that goes unused during normal, low-traffic periods.

## 11. Failure modes and misuse

- Building a system that still has a second, distinct behavior for the impaired case, reintroducing the exact bimodal behavior this pattern exists to avoid.
- A refresh path that silently stops working, so the statically cached state drifts far out of date long before anyone notices.
- Assuming static stability removes the need for capacity planning, when pre-provisioned capacity still needs to be sized correctly for the traffic each independent unit actually needs to serve.
- Applying this pattern to a component with no genuine multi-zone or multi-region failure mode, adding real complexity with no corresponding resilience benefit.
- Treating the statically cached state as a substitute for genuine testing, when the single normal mode still needs to be verified directly against real impairment conditions.

## 12. Trade-off matrix

| Dimension | Real-time coordination | Static stability |
|---|---|---|
| Data freshness | Always current | Only as current as the last refresh |
| Behavior when a peer is unreachable | Often changes, a distinct failure mode | Unchanged, a single normal mode |
| Engineering complexity upfront | Lower | Higher |
| Confidence in the failure-mode behavior | Lower, rarely exercised | Higher, it is the same behavior tested every day |
| Capacity cost | Dynamic, requested as needed | Higher, pre-provisioned in advance |

## 13. Related and incompatible patterns

### Related

- Graceful Degradation. both patterns keep a system functioning under adverse conditions, but this pattern is about surviving a coordination failure with unchanged behavior, while degradation is about serving a reduced-quality response under load.
- Error Budget. an outage caused by a control-plane dependency this pattern is designed to survive would otherwise consume real error budget, so this pattern is a direct investment in protecting it.

### Incompatible with

- None directly, though a design that keeps a distinct, rarely exercised failure-mode behavior around works against this pattern's own intent, even though it may still be labeled as statically stable.

## 14. Refactoring path in and out

### Introducing it

1. Identify the independent units (zone-scoped or region-scoped components) whose loss of connectivity to a control plane or a peer is a real, plausible failure mode.
2. Design the statically cached state each unit needs to keep operating on its own, and build the refresh path that keeps it reasonably current during normal operation.
3. Remove any distinct, separate failure-mode behavior, so the unit exhibits the same single normal mode whether the control plane is reachable or not.
4. Pre-provision capacity for each independent unit based on a static plan, rather than depending on dynamic, on-demand provisioning from a central control plane.
5. Test the design directly, ideally as part of a Game Day exercise, by genuinely cutting off a unit's connectivity to the control plane and confirming its behavior does not change.

### Removing it

1. Confirm the independent unit no longer has a genuine multi-zone or multi-region failure mode to design around, or the system is being retired.
2. Retire the refresh path and the statically cached state, returning the unit to relying on real-time coordination.
3. Retire the pre-provisioned capacity plan alongside it, if it is no longer needed.

## 15. Testing and verification

- Test each independent unit directly by cutting off its connectivity to the control plane or to a peer, confirming its behavior genuinely does not change, matching the single normal mode the design intends.
- Test the refresh path explicitly, confirming the statically cached state stays reasonably current during normal operation.
- Verify pre-provisioned capacity is actually sized correctly for the traffic each unit needs to serve, not just present in name.
- Periodically re-run the impairment test as the system evolves, confirming static stability has not silently regressed as new dependencies were added.

## 16. Observability signals

- Track the staleness of each independent unit's statically cached state, as a primary measure of whether the refresh path is genuinely keeping it current.
- Track whether an independent unit's observed behavior actually changes when its connectivity to a peer or control plane is lost, confirming the single normal mode holds in practice, not only in design.
- Track pre-provisioned capacity utilization, confirming it is sized appropriately rather than significantly over or under-provisioned relative to real traffic.

## 17. Security and privacy implications

- Statically cached state that includes access control or authorization data needs its own refresh and revocation strategy, since a stale cached permission could grant access that has since been revoked at the control plane.
- The refresh path itself is a real operational dependency, and access to it should be scoped and monitored with the same rigor as any other control-plane-adjacent mechanism.
- Pre-provisioned capacity that sits idle should still be secured and patched to the same standard as actively serving capacity, since an idle but reachable unit is still a real attack surface.

## 18. References

- AWS Builders Library, Static stability using Availability Zones (https://aws.amazon.com/builders-library/static-stability-using-availability-zones/)
- AWS Well-Architected Framework, Reliability Pillar, Withstand component failures using static stability (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_withstand_component_failures_static_stability.html)

## Code examples

### Python

```python
from dataclasses import dataclass


@dataclass
class StaticallyCachedState:
    routing_config: dict
    last_refreshed_at: float


class IndependentUnit:
    def __init__(self, cached_state):
        self.cached_state = cached_state

    def refresh(self, new_config, timestamp):
        self.cached_state = StaticallyCachedState(new_config, timestamp)

    def route_request(self, request_key):
        return self.cached_state.routing_config.get(
            request_key, "default-backend"
        )


unit = IndependentUnit(
    StaticallyCachedState(
        routing_config={"search": "search-backend"},
        last_refreshed_at=0.0,
    )
)
print('routed', unit.route_request("search"))
print('routed on control plane loss', unit.route_request("search"))
```

### Kotlin

```kotlin
data class StaticallyCachedState(
    val routingConfig: Map<String, String>,
    val lastRefreshedAt: Double,
)

class IndependentUnit(private var cachedState: StaticallyCachedState) {
    fun refresh(newConfig: Map<String, String>, timestamp: Double) {
        cachedState = StaticallyCachedState(newConfig, timestamp)
    }

    fun routeRequest(requestKey: String): String {
        return cachedState.routingConfig[requestKey] ?: "default-backend"
    }
}

fun main() {
    val unit = IndependentUnit(
        StaticallyCachedState(
            routingConfig = mapOf("search" to "search-backend"),
            lastRefreshedAt = 0.0,
        )
    )
    println("routed " + unit.routeRequest("search"))
    println("routed on control plane loss " + unit.routeRequest("search"))
}
```

### Swift

```swift
struct StaticallyCachedState {
    let routingConfig: [String: String]
    let lastRefreshedAt: Double
}

final class IndependentUnit {
    private var cachedState: StaticallyCachedState

    init(cachedState: StaticallyCachedState) {
        self.cachedState = cachedState
    }

    func refresh(newConfig: [String: String], timestamp: Double) {
        cachedState = StaticallyCachedState(routingConfig: newConfig, lastRefreshedAt: timestamp)
    }

    func routeRequest(_ requestKey: String) -> String {
        cachedState.routingConfig[requestKey] ?? "default-backend"
    }
}

let unit = IndependentUnit(
    cachedState: StaticallyCachedState(
        routingConfig: ["search": "search-backend"],
        lastRefreshedAt: 0.0
    )
)
print("routed " + unit.routeRequest("search"))
print("routed on control plane loss " + unit.routeRequest("search"))
```
