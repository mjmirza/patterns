---
name: Regional Evacuation
slug: regional-evacuation
family: 21-sre-operations
category: Behavioral
aliases: [Zonal Shift, Traffic Draining, Zone Evacuation]
first_described: 'AWS, Amazon Application Recovery Controller zonal shift documentation'
maturity: canonical
related: [multi-site-active-active, static-stability]
incompatible_with: []
verified: 2026-08-22
---

# Regional Evacuation

## 1. Name, aliases, and lineage

Regional Evacuation. Also called Zonal Shift, Traffic Draining, or Zone Evacuation. The pattern is the operational practice of deliberately, quickly, and safely draining all live traffic out of a specific region or availability zone when that zone is impaired or about to fail, moving it to healthy zones or regions, as a controlled operational action rather than an automatic failover. AWS names the mechanism directly in its Application Recovery Controller documentation. Amazon Application Recovery Controller zonal shift allows you to shift traffic for a supported resource away from an impaired availability zone in an AWS Region to healthy availability zones in the same Region (https://docs.aws.amazon.com/r53recovery/latest/dg/arc-zonal-shift.html).

The lineage runs directly from the architecture that makes it possible toward the operational tooling that actually performs it. a multi-site active active deployment gives a system more than one healthy place to send traffic, and Regional Evacuation is the procedure and tooling that actually moves traffic there quickly and safely when a specific site starts to fail, rather than leaving that decision to an unassisted, ad-hoc manual response during a real incident.

## 2. Problem and context

A multi-site architecture removes a single point of failure at the architectural level, but it does not by itself give an operator a fast, safe, well tested way to actually act on a failing zone. Without dedicated evacuation tooling, moving traffic away from an impaired zone during a real incident means improvising a change under pressure, with no prior practice and real risk of getting it wrong at exactly the worst moment.

AWS's own guidance names the specific, narrow purpose this tooling serves. a zonal shift moves traffic away from an availability zone on a temporary basis, to mitigate an impairment (https://docs.aws.amazon.com/r53recovery/latest/dg/route53-arc-best-practices.zonal-shifts.html). The problem this pattern solves is giving operators a fast, pre-built, pre-tested way to perform exactly that traffic move, so reacting to a failing zone is a rehearsed, low-risk action rather than an improvised one.

## 3. Forces

- Evacuating a zone needs to be fast, since the value of the action is directly tied to how quickly it removes traffic from the impaired zone.
- The remaining healthy zones need enough spare capacity to absorb the evacuated zone's traffic, or the evacuation itself causes a new overload elsewhere.
- An evacuation action needs a clear, deliberate reversal path, since it is meant to be a temporary mitigation, not a permanent change to where traffic is served.
- Deciding when to evacuate needs a clear signal or a human judgment call, and either one needs to happen fast enough for the action to matter.
- The evacuation tooling itself needs to be tested and trusted, since a mechanism that fails during the one real incident it is needed for provides no benefit at all.

## 4. Applicability and non-applicability

Use Regional Evacuation for any system already built on a multi site or multi zone architecture, where a plausible failure mode is one specific zone or region becoming impaired while the rest of the system stays healthy, and where quickly moving traffic away from that impaired zone genuinely mitigates the impact. It fits especially well as the operational companion to a Multi-Site Active Active or Static Stability design, turning the architecture's theoretical resilience into a fast, practiced, real action.

Skip it for a single site system with nowhere else to evacuate traffic to, since the pattern depends entirely on healthy capacity existing elsewhere to absorb the shift. It is also not a substitute for fixing the underlying impairment. evacuation buys time and reduces impact, it does not resolve the problem that made the zone unhealthy in the first place.

## 5. Structure

- Impaired zone. the specific region or availability zone currently experiencing the failure or degradation that motivates the evacuation.
- Evacuation trigger. the mechanism, automated or operator initiated, that starts the traffic shift away from the impaired zone.
- Target capacity. the healthy zones or regions the shifted traffic moves to, sized with enough spare capacity to absorb it.
- Reversal path. the explicit, tested mechanism for restoring traffic to the previously impaired zone once it recovers.
- Duration limit. the temporary, bounded nature of the shift, since it is meant to mitigate an impairment, not become a permanent routing change.

## 6. ASCII structure diagram

```
  Impaired zone detected
        |
        v
  Evacuation trigger fires
  (automated or operator initiated)
        |
        v
  traffic shifts to Target capacity
  (healthy zones, with spare headroom)
        |
        v
  Duration limit tracked, mitigation is temporary
        |
        v
  impaired zone recovered?  ----- yes -----> Reversal path restores traffic
        |
        no
        |
        v
  evacuation continues, reassessed regularly
```

## 7. Dynamics

1. The impaired zone is identified, either through an automated health signal or an operator's own judgment during an active incident.
2. The evacuation trigger fires, initiating the traffic shift, matching AWS's own description of shifting traffic for a supported resource away from an impaired availability zone to healthy availability zones in the same region (https://docs.aws.amazon.com/r53recovery/latest/dg/arc-zonal-shift.html).
3. Traffic moves to the target capacity in the healthy zones, which absorb it using the spare headroom they were sized to hold.
4. The duration limit is tracked from the moment the shift begins, reflecting the guidance that this action moves traffic away on a temporary basis, to mitigate an impairment (https://docs.aws.amazon.com/r53recovery/latest/dg/route53-arc-best-practices.zonal-shifts.html).
5. The team works to correct the underlying impairment in the affected zone while traffic continues to be served safely elsewhere.
6. Once the zone is confirmed healthy again, the reversal path restores traffic to it, matching the same guidance's own recommendation to restore the resource for the application to service as soon as the underlying problem has been corrected.

## 8. Implementation variants

- Zone level evacuation. the narrowest scope, shifting traffic away from a single impaired availability zone within a region, matching AWS's own zonal shift mechanism directly.
- Full region evacuation. a broader action moving all traffic away from an entire impaired region to one or more healthy regions, used for a more severe, region-wide impairment.
- Automated evacuation. the evacuation trigger fires automatically based on a defined health signal crossing a threshold, without waiting for a person to initiate it.
- Operator initiated evacuation. a person makes the call to evacuate based on their own judgment during an active incident, using pre-built tooling to execute the shift quickly once the decision is made.

## 9. Known production uses

- AWS's Application Recovery Controller ships zonal shift as a first class, named capability for shifting traffic away from an impaired availability zone (https://docs.aws.amazon.com/r53recovery/latest/dg/arc-zonal-shift.html), used directly by AWS customers as a built-in evacuation mechanism.
- AWS's own best practices guidance documents the temporary, mitigation-focused nature of a zonal shift directly (https://docs.aws.amazon.com/r53recovery/latest/dg/route53-arc-best-practices.zonal-shifts.html), including the explicit expectation that the resource is restored to normal service once the underlying problem is corrected.
- Large-scale, multi-zone and multi-region operators across the industry commonly build or adopt equivalent evacuation tooling as the operational companion to their multi-site architecture, treating a fast, tested traffic shift as a standard incident response tool rather than an improvised action.

## 10. Consequences

### Benefits

- An impaired zone's impact on real users is reduced quickly, since traffic is actively moved to healthy capacity rather than left to keep hitting the impaired zone.
- A pre-built, pre-tested evacuation mechanism is far more trustworthy under real incident pressure than an improvised, ad-hoc traffic change invented in the moment.
- The temporary, reversible nature of the action means the team can act quickly without committing to a permanent architectural change, and can restore normal routing cleanly once the impairment is resolved.

### Costs

- Building and maintaining the evacuation trigger and reversal path is real, ongoing engineering work.
- The target capacity in the healthy zones has to be genuinely sized to absorb the evacuated traffic, or the evacuation itself creates a new overload.
- The tooling needs to be tested regularly to stay trusted, which takes real, ongoing operational discipline.

## 11. Failure modes and misuse

- Evacuating traffic to healthy zones that do not actually have enough spare capacity, causing a new overload in the very zones meant to absorb the shift.
- No clear reversal path, so traffic stays evacuated long after the impaired zone has genuinely recovered.
- An evacuation trigger, automated or manual, that fires too slowly to meaningfully reduce the impact of a fast-moving impairment.
- Treating the evacuation itself as the fix, rather than a temporary mitigation, and never actually correcting the underlying problem in the impaired zone.
- Evacuation tooling that has not been tested since it was built, discovered to be broken only during the real incident it was meant to help with.

## 12. Trade-off matrix

| Dimension | Zone level evacuation | Full region evacuation |
|---|---|---|
| Blast radius mitigated | One availability zone | An entire region |
| Speed of the shift | Faster, narrower scope | Slower, larger scope to move |
| Capacity needed elsewhere | Lower, absorbed within the region | Higher, absorbed in other regions |
| Typical trigger severity | A single zone impairment | A region-wide impairment |
| Good default starting scope | Yes | Reserved for more severe incidents |

## 13. Related and incompatible patterns

### Related

- Multi-Site Active Active. the architecture that makes evacuation possible in the first place, since there has to be healthy capacity elsewhere for the shifted traffic to land on.
- Static Stability. an independent unit designed for static stability continues operating correctly even while its zone is being evacuated, since it never depended on real-time coordination with the rest of the system to begin with.

### Incompatible with

- None directly, though evacuating traffic to a zone with insufficient spare capacity works against this pattern's own intent, even though the action is still labeled as an evacuation.

## 14. Refactoring path in and out

### Introducing it

1. Confirm the system is already built on a multi-site or multi-zone architecture with genuine spare capacity in its healthy zones.
2. Build the evacuation trigger, deciding whether it fires automatically on a defined health signal, is operator initiated, or both.
3. Build the reversal path, so restoring traffic to a recovered zone is just as fast and well tested as evacuating it in the first place.
4. Test the evacuation directly, ideally as part of a Game Day exercise, confirming target capacity genuinely absorbs the shifted traffic without a new overload.
5. Document the evacuation procedure in the relevant runbook, so an operator knows it exists and when to use it during a real incident.

### Removing it

1. Confirm the underlying multi-site architecture is being retired, or the system no longer has more than one site to evacuate traffic between.
2. Retire the evacuation trigger and reversal path.
3. Remove the evacuation procedure from the runbook, so an operator does not reach for a mechanism that no longer exists.

## 15. Testing and verification

- Test a genuine evacuation directly, confirming the trigger fires correctly and traffic actually moves to the target capacity within the intended time.
- Verify target capacity genuinely absorbs the evacuated traffic under real load, confirming the healthy zones do not become overloaded by the shift.
- Test the reversal path explicitly, confirming traffic restores correctly to a zone once it is marked healthy again.
- Periodically re-run the evacuation test as the system evolves, confirming the mechanism has not silently broken as new dependencies were added.

## 16. Observability signals

- Track how quickly the evacuation trigger actually moves traffic once it fires, as the primary measure of how fast the mechanism genuinely reduces impact.
- Track target capacity utilization during and after an evacuation, confirming the healthy zones absorb the shift without becoming overloaded themselves.
- Track how long an evacuation stays active before the reversal path restores normal traffic, flagging any evacuation left active for an unusually long time as a signal the underlying impairment may not actually be getting fixed.

## 17. Security and privacy implications

- The evacuation trigger is a high-privilege operational control that can change where real production traffic is served, and access to it should be scoped and audited with the same rigor as any other action that can change production routing quickly and broadly.
- Traffic shifted to a different zone or region during an evacuation still needs to satisfy the same data residency and cross-border transfer requirements at its new destination as it did at the impaired zone.
- Every evacuation and reversal action should be logged with enough detail (who or what triggered it, when, and why) to reconstruct exactly what happened after a real incident.

## 18. References

- AWS, Application Recovery Controller, zonal shift (https://docs.aws.amazon.com/r53recovery/latest/dg/arc-zonal-shift.html)
- AWS, Application Recovery Controller best practices, zonal shifts (https://docs.aws.amazon.com/r53recovery/latest/dg/route53-arc-best-practices.zonal-shifts.html)

## Code examples

### Python

```python
from dataclasses import dataclass


@dataclass
class Zone:
    name: str
    healthy: bool
    spare_capacity: float


class Evacuation:
    def __init__(self, zones):
        self.zones = zones
        self.evacuated_from = None

    def evacuate(self, impaired_zone_name):
        target = self.pick_target()
        if target is None:
            raise RuntimeError("no healthy zone with spare capacity")
        self.evacuated_from = impaired_zone_name
        return target.name

    def pick_target(self):
        candidates = [z for z in self.zones if z.healthy and z.spare_capacity > 0]
        if not candidates:
            return None
        return max(candidates, key=lambda z: z.spare_capacity)

    def restore(self):
        self.evacuated_from = None


zones = [
    Zone("us-east-1a", False, 0.0),
    Zone("us-east-1b", True, 0.4),
    Zone("us-east-1c", True, 0.3),
]
evacuation = Evacuation(zones)
target = evacuation.evacuate("us-east-1a")
print('evacuated to', target)
```

### Kotlin

```kotlin
data class Zone(
    val name: String,
    val healthy: Boolean,
    val spareCapacity: Double,
)

class Evacuation(private val zones: List<Zone>) {
    var evacuatedFrom: String? = null
        private set

    fun evacuate(impairedZoneName: String): String {
        val target = pickTarget()
            ?: throw IllegalStateException("no healthy zone with spare capacity")
        evacuatedFrom = impairedZoneName
        return target.name
    }

    private fun pickTarget(): Zone? {
        return zones.filter { it.healthy && it.spareCapacity > 0 }.maxByOrNull { it.spareCapacity }
    }

    fun restore() {
        evacuatedFrom = null
    }
}

fun main() {
    val zones = listOf(
        Zone("us-east-1a", false, 0.0),
        Zone("us-east-1b", true, 0.4),
        Zone("us-east-1c", true, 0.3),
    )
    val evacuation = Evacuation(zones)
    val target = evacuation.evacuate("us-east-1a")
    println("evacuated to " + target)
}
```

### Swift

```swift
struct Zone {
    let name: String
    let healthy: Bool
    let spareCapacity: Double
}

enum EvacuationError: Error {
    case noHealthyZoneWithSpareCapacity
}

final class Evacuation {
    private let zones: [Zone]
    private(set) var evacuatedFrom: String?

    init(zones: [Zone]) {
        self.zones = zones
    }

    func evacuate(impairedZoneName: String) throws -> String {
        guard let target = pickTarget() else {
            throw EvacuationError.noHealthyZoneWithSpareCapacity
        }
        evacuatedFrom = impairedZoneName
        return target.name
    }

    private func pickTarget() -> Zone? {
        zones.filter { $0.healthy && $0.spareCapacity > 0 }
            .max { $0.spareCapacity < $1.spareCapacity }
    }

    func restore() {
        evacuatedFrom = nil
    }
}

let zones = [
    Zone(name: "us-east-1a", healthy: false, spareCapacity: 0.0),
    Zone(name: "us-east-1b", healthy: true, spareCapacity: 0.4),
    Zone(name: "us-east-1c", healthy: true, spareCapacity: 0.3),
]
let evacuation = Evacuation(zones: zones)
let target = try evacuation.evacuate(impairedZoneName: "us-east-1a")
print("evacuated to " + target)
```
