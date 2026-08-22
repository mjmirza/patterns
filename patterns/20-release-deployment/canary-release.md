---
name: Canary Release
slug: canary-release
family: 20-release-deployment
category: Deployment
aliases: [Canary Deployment, Canary Rollout]
first_described: 'Martin Fowler, CanaryRelease bliki article; Google SRE Workbook'
maturity: canonical
related: [blue-green-deployment, rolling-deployment]
incompatible_with: []
verified: 2026-08-22
---

# Canary Release

## 1. Name, aliases, and lineage

Canary Release. Also called Canary Deployment or Canary Rollout. The pattern is routing a small, gradually increasing fraction of production traffic to a new version of a service, monitoring it closely, and rolling out to all traffic only once it proves healthy. Martin Fowler's own bliki article names the technique directly. canary release is a technique to reduce the risk of introducing a new software version in production by slowly rolling out the change to a small subset of users before rolling it out to the entire infrastructure and making it available to everybody (https://martinfowler.com/bliki/CanaryRelease.html).

The lineage runs from that same risk-reduction goal toward the Google SRE Workbook's more formal, operational framing of the same underlying practice. the workbook defines the practice directly. we define canarying as a partial and time-limited deployment of a change in a service and its evaluation (https://sre.google/workbook/canarying-releases/). Both sources describe the same core idea from two angles, a risk-reduction technique and a formal, evaluated deployment discipline.

## 2. Problem and context

Deploying a new release to all production traffic at once means every user is affected the instant a defect ships, and the defect is only discovered once it has already reached everyone. Even careful pre-release testing cannot catch every real-world condition, a traffic pattern, a data shape, an edge case, that only shows up once a release meets genuine production traffic at scale.

The problem this pattern solves is limiting how much of production traffic a bad release can affect before it is caught, by exposing the new version to only a small slice of real traffic first, watching it closely, and expanding to full traffic only once that small slice proves the release is healthy.

## 3. Forces

- Running both the old and new version simultaneously, even for a small fraction of traffic, means the infrastructure has to support routing a portion of requests to each version cleanly.
- The canary slice has to be genuinely representative of real production traffic, or a defect specific to an underrepresented traffic pattern can slip through undetected.
- Deciding how large the canary slice should be, and how long to observe it, is itself a real trade-off, too small or too short risks missing a real problem, too large or too long delays the full rollout unnecessarily.
- The metrics used to judge the canary healthy have to be chosen carefully, since impact on the outcome the canary is meant to protect is directly proportional to how much traffic is exposed to a real defect during the canary window.
- A canary that shares a stateful backend with the full-traffic version needs the same shared-state care as any parallel-version deployment strategy.

## 4. Applicability and non-applicability

Use Canary Release for a service with enough production traffic volume that a small slice is still meaningful to observe, and where the cost of a bad release reaching all users at once is genuinely high enough to justify the added deployment complexity of a gradual, monitored rollout.

This pattern is a non-applicability fit for a service with too little traffic volume for a small canary slice to be statistically meaningful, where a defect might simply not surface during the canary window regardless of how carefully it is observed. It is also unnecessary overhead for a low-risk, easily-reversible change where the operational cost of gradual rollout and close monitoring outweighs the risk being managed.

## 5. Structure

- Canary version. the new release, initially receiving only a small fraction of production traffic.
- Stable version. the existing, already-proven release, still receiving the majority of traffic during the canary window.
- Traffic splitter. the routing mechanism that directs a configurable fraction of traffic to the canary version and the rest to the stable version.
- Health evaluation. the set of metrics and thresholds used to judge whether the canary is behaving acceptably.
- Rollout progression. the staged sequence of traffic-fraction increases, from the initial small slice up to full traffic, gated by the health evaluation at each stage.

## 6. ASCII structure diagram

```

  Stage 1              Stage 2              Stage 3
  95% stable            75% stable            0% stable
   5% canary            25% canary           100% canary
      |                    |                    |
      v                    v                    v
  healthy? --yes-->   healthy? --yes-->   fully rolled out
      |                    |
      no                   no
      |                    |
      v                    v
  roll back to 100% stable, canary halted

```

## 7. Dynamics

1. The team deploys the new release as the canary version, alongside the already-running stable version.
2. The traffic splitter routes a small, initial fraction of production traffic to the canary, following the same slowly rolling out the change to a small subset of users discipline (https://martinfowler.com/bliki/CanaryRelease.html).
3. The team observes the canary's health metrics closely for a defined evaluation window, treating this as a partial and time-limited deployment of a change in a service and its evaluation (https://sre.google/workbook/canarying-releases/).
4. If the canary's metrics stay within acceptable thresholds, the traffic splitter increases the canary's traffic fraction to the next stage.
5. This observe-then-expand cycle repeats until the canary receives all traffic, at which point the old stable version is retired, or the canary itself becomes the new stable version.
6. If at any stage the canary's metrics fall outside acceptable thresholds, the traffic splitter routes traffic back to the stable version entirely, halting the canary rollout before it reaches more of production traffic.

## 8. Implementation variants

- Fixed-percentage canary. traffic is split by a simple, fixed percentage at each stage, the most straightforward variant to implement.
- Attribute-based canary. traffic is routed to the canary based on a specific attribute, an internal user, a specific region, rather than a random percentage, letting the team control exactly who sees the new version first.
- Automated progressive delivery. the traffic-fraction increases and the health evaluation are both automated, advancing or rolling back the canary without manual intervention at each stage.
- Shadow-informed canary. real production traffic is mirrored to the canary without actually serving its response to the user, a lower-risk way to observe the canary's behavior against real traffic before it serves any real user at all.

## 9. Known production uses

- Google's own SRE practice, documented in its SRE Workbook, formalizes canarying as a standard part of its release engineering discipline across its services.
- Netflix has publicly described using canary-style deployment as part of its own release process, gradually shifting traffic to a new version while monitoring key health metrics.
- Many organizations running Kubernetes use a canary deployment strategy directly supported by their ingress or service mesh layer, gradually shifting traffic weight toward a new version.

## 10. Consequences

Benefits.

- A defect in the new release affects only the small fraction of traffic routed to the canary, not the entire user base, since impact on the outcome being protected is directly proportional to how much traffic is exposed to a real defect (https://sre.google/workbook/canarying-releases/).
- The team gets real production signal on the new release's behavior before committing to a full rollout.
- A bad release is caught and rolled back automatically, or with minimal manual intervention, before it reaches most of production traffic.

Costs.

- Running the canary and stable versions simultaneously, and routing traffic between them, adds real infrastructure and operational complexity.
- A full canary rollout, staged carefully, takes meaningfully longer than an all-at-once release.
- Choosing the right canary size, evaluation window, and health thresholds requires real judgment, and getting any of them wrong either risks missing a real problem or delays a safe rollout unnecessarily.

## 11. Failure modes

- Canary too small to be meaningful. a traffic slice too small relative to the service's real volume can fail to surface a real defect during the evaluation window.
- Unrepresentative canary traffic. a canary slice that happens to exclude a real traffic pattern or user segment can look healthy while a defect specific to that excluded segment goes completely undetected.
- Wrong health metrics. evaluating the canary against metrics that do not actually reflect the real risk being managed can either miss a genuine regression or flag a healthy canary as unhealthy.
- Stuck partial rollout. a canary left at a partial traffic fraction indefinitely, with no decision to advance or roll back, leaves the deployment in an ambiguous, half-migrated state.

## 12. Trade-off matrix

| Dimension | Canary release | All-at-once release |

|---|---|---|

| Blast radius of a bad release | Small, limited to the canary slice | Full, reaches every user at once |
| Real-production signal before full rollout | Yes | No |
| Rollout time to full traffic | Longer, staged | Immediate |
| Operational complexity | Higher, traffic splitting and monitoring | Lower, single deployment |
| Confidence before full commitment | High, proven against real traffic | Lower, based on pre-release testing alone |

## 13. Related and incompatible patterns

Related to Blue-Green Deployment, an alternative that switches all traffic at once between two complete environments rather than gradually shifting a fraction of it. Related to Rolling Deployment, another gradual strategy, but one that typically replaces instances rather than deliberately holding a stable fraction back for close observation. Not incompatible with Blue-Green Deployment. some organizations run a canary phase inside the green environment's verification step before committing to the full blue-green switch.

## 14. Refactoring path in and out

Introducing it.

1. Confirm the service has enough traffic volume for a small canary slice to be statistically meaningful.
2. Put a traffic splitter in place capable of routing a configurable fraction of traffic to a canary version.
3. Define the health metrics and thresholds the canary must meet at each stage before the traffic fraction advances.
4. Run a full canary rollout end to end, including deliberately triggering a rollback at least once, to confirm the rollback path works before relying on it for a real incident.

Removing it.

1. Confirm the team no longer needs the staged risk-reduction this pattern provides, typically because releases have become low-risk enough, or a different safety mechanism now covers the same need.
2. Remove the traffic-splitting logic, reverting to a single deployment target.
3. Remove the canary-specific health evaluation automation once it is no longer part of the release process.
4. Confirm the replacement release strategy is genuinely in place and tested before the canary infrastructure is fully decommissioned.

## 15. Testing and verification

- Test the traffic splitter directly, asserting it routes the configured fraction of traffic to the canary accurately.
- Test the automated rollback path by deliberately deploying a known-bad canary and confirming it is detected and rolled back within the expected evaluation window.
- Test the health evaluation logic in isolation, asserting it correctly flags a canary outside acceptable thresholds and correctly passes one within them.
- Test the full stage-progression sequence end to end, confirming the traffic fraction actually advances through every defined stage when the canary stays healthy throughout.

## 16. Observability signals

- Canary-specific error rate and latency, tracked separately from the stable version's own metrics, so a canary regression is visible immediately rather than averaged away.
- Traffic fraction currently routed to the canary at each point in the rollout.
- Time spent at each rollout stage, useful for tuning how long an evaluation window actually needs to be.
- Rollback frequency, the rate at which a canary fails its health evaluation and traffic is routed back to the stable version.

## 17. Security and privacy implications

A canary version, receiving a fraction of real production traffic, is itself a real production system and has to be secured to the same standard as the stable version, since a security vulnerability in the canary is a real vulnerability exposed to whatever fraction of real users it is currently serving. An attribute-based canary that deliberately targets a specific user segment has to apply that targeting logic without leaking which users are on the canary to any party who should not know, since canary membership can itself reveal information about a user, such as internal-employee status.

## 18. Code examples

### Swift

```swift

final class CanaryRouter {
    private var canaryTrafficPercent: Int

    init(canaryTrafficPercent: Int) {
        self.canaryTrafficPercent = canaryTrafficPercent
    }

    // Decides whether a given request routes to the canary or stable version.
    func routesToCanary(requestHash: Int) -> Bool {
        let bucket = abs(requestHash) % 100
        return bucket < canaryTrafficPercent
    }

    // Advances the canary's traffic fraction after a healthy evaluation.
    func advance(to newPercent: Int) {
        canaryTrafficPercent = newPercent
    }
}

```

### Kotlin

```kotlin

class CanaryRouter(private var canaryTrafficPercent: Int) {
    // Decides whether a given request routes to the canary or stable version.
    fun routesToCanary(requestHash: Int): Boolean {
        val bucket = Math.abs(requestHash) % 100
        return bucket < canaryTrafficPercent
    }

    // Advances the canary's traffic fraction after a healthy evaluation.
    fun advance(newPercent: Int) {
        canaryTrafficPercent = newPercent
    }
}

```

### Python

```python

class CanaryRouter:
    def __init__(self, canary_traffic_percent):
        self.canary_traffic_percent = canary_traffic_percent

    def routes_to_canary(self, request_hash):
        """Decides whether a given request routes to the canary or stable version."""
        bucket = abs(request_hash) % 100
        return bucket < self.canary_traffic_percent

    def advance(self, new_percent):
        """Advances the canary's traffic fraction after a healthy evaluation."""
        self.canary_traffic_percent = new_percent

```

## 19. References

- Martin Fowler, CanaryRelease, https://martinfowler.com/bliki/CanaryRelease.html
- Google, SRE Workbook, Canarying Releases, https://sre.google/workbook/canarying-releases/
