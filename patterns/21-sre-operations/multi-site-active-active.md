---
name: Multi-Site Active Active
slug: multi-site-active-active
family: 21-sre-operations
category: Structural
aliases: [Multi-Region Active Active, Active Active Deployment, Multi-Site DR]
first_described: 'AWS, Well-Architected Framework and Disaster Recovery of Workloads on AWS whitepaper'
maturity: canonical
related: [static-stability, service-level-objective]
incompatible_with: []
verified: 2026-08-22
---

# Multi-Site Active Active

## 1. Name, aliases, and lineage

Multi-Site Active Active. Also called Multi-Region Active Active, Active Active Deployment, or Multi-Site DR. AWS's own Well-Architected Framework defines the strategy directly, as one of its named disaster recovery options. Multi-Region (multi-site) active-active, RPO near zero, RTO potentially zero, your workload is deployed to, and actively serving traffic from, multiple AWS Regions (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html). The framework adds the requirement this strategy demands. this strategy requires you to synchronize data across Regions.

The lineage runs from the older passive standby model toward a fully live one. AWS's own disaster recovery whitepaper draws the exact distinction directly. multi-site active or active serves traffic from all regions to which it is deployed, whereas hot standby serves traffic only from a single region, and the other regions are only used for disaster recovery (https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html). This pattern is the fully active end of that spectrum, where every site genuinely serves live production traffic rather than sitting idle waiting for a failover.

## 2. Problem and context

A single-site or passive-standby architecture concentrates real risk in one place. if the active site fails, the system either goes down entirely, or a standby site has to be activated, and that activation itself takes real time, during which the service is unavailable. Even a well tested standby has never actually served live production traffic before the moment it is needed most.

The problem this pattern solves is removing that activation delay and that untested-until-needed risk entirely, by having every site already serving real traffic all the time. AWS's own framing states the target outcome plainly. a recovery point objective near zero and a recovery time objective potentially zero (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html), meaning a site failure causes little to no data loss and little to no downtime, because the remaining sites are already carrying real traffic and simply absorb more of it.

## 3. Forces

- Keeping every site fully active and serving traffic all the time is far more expensive than running a smaller, idle standby site.
- Data written in one site needs to reach every other site quickly and correctly, and that synchronization is genuinely hard to build and operate correctly at low latency.
- A conflict between two sites writing to the same data at nearly the same time needs a resolution strategy, or the data can silently diverge between sites.
- Every site has to be sized to absorb the traffic from any other site that fails, or a real failover still causes overload at the remaining sites.
- Testing and operating a genuinely active-active system is more complex than testing a standby, since every site is live and changes to any one of them can affect real traffic everywhere.

## 4. Applicability and non-applicability

Use Multi-Site Active Active for a workload where a near-zero recovery point and recovery time genuinely matter, and where the cost of running every site fully active is justified by how costly an outage or data loss would be. It fits especially well for a workload that already needs to serve a geographically distributed audience with low latency, since the same multi-site deployment that improves latency also delivers the resilience benefit.

Skip it for a workload where a passive standby's slower recovery time is genuinely acceptable, since the ongoing cost of running every site fully active is real and unnecessary when a much cheaper standby strategy already meets the actual recovery requirement.

## 5. Structure

- Site. an independent deployment of the full workload in its own region or data center, capable of serving live production traffic on its own.
- Traffic distribution. the mechanism that routes real traffic across all active sites, rather than concentrating it in one place.
- Data synchronization. the mechanism that replicates data written in one site to every other site, keeping them consistent enough for correct operation.
- Conflict resolution strategy. the defined rule for handling two sites writing to the same data at nearly the same time.
- Capacity headroom. the extra capacity each site holds so it can absorb the traffic that was previously served by a site that has failed.

## 6. ASCII structure diagram

```
  Traffic distribution
        |
   +----+----+----+
   |         |    |
   v         v    v
 Site A    Site B  Site C
 (active)  (active)(active)
   |         |    |
   +----+----+----+
        |
        v
  Data synchronization
  (Conflict resolution strategy applied)

  Site B fails
        |
        v
  Traffic distribution routes B's share to A and C,
  absorbed by their Capacity headroom
```

## 7. Dynamics

1. Traffic distribution routes real production traffic across every active site simultaneously, matching AWS's own definition of a workload that is deployed to, and actively serving traffic from, multiple regions (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html).
2. Every site processes its share of real traffic independently, writing data locally and relying on data synchronization to replicate that data out to every other site.
3. When two sites write to the same data at nearly the same time, the conflict resolution strategy decides which write wins, or how the two writes are merged, keeping the sites from silently diverging.
4. If one site fails, traffic distribution simply stops routing traffic there and shifts it to the remaining sites, matching the core distinction AWS draws directly. multi-site active or active serves traffic from all regions to which it is deployed (https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html), so the remaining sites, already live and already serving real traffic, simply absorb more of it.
5. Each remaining site's capacity headroom absorbs the added load from the failed site, so the shift causes little to no visible disruption to the person using the service.
6. Once the failed site recovers, data synchronization brings it back into consistency with the others, and traffic distribution resumes routing a share of traffic to it.

## 8. Implementation variants

- Two-site active active. the simplest form, two fully active sites each capable of absorbing the other's full traffic on failure, a common starting point before expanding further.
- Multi-region active active. three or more active sites, giving a smaller proportional capacity increase needed at each site to absorb any single site's failure.
- Read-local, write-global. reads are served from the nearest active site for low latency, while writes are coordinated across all sites through the data synchronization mechanism.
- Sharded active active. different sites own different partitions of the data as their primary, reducing the amount of cross-site conflict that needs resolving, at the cost of uneven capacity needs per site.

## 9. Known production uses

- AWS's own Well-Architected Framework documents multi-Region active-active as a named disaster recovery strategy with a near zero recovery point and a potentially zero recovery time (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html), the highest resilience tier among AWS's documented DR strategies.
- AWS's own Disaster Recovery of Workloads whitepaper documents the same pattern directly, distinguishing it explicitly from a hot standby strategy by the fact that every deployed region genuinely serves live traffic (https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html).
- Large, globally distributed services across the industry commonly adopt this pattern for their most traffic-critical, highest-value workloads, where the ongoing cost of running every site fully active is justified by both the latency benefit to users and the resilience benefit during a site failure.

## 10. Consequences

### Benefits

- A site failure causes little to no visible disruption, since the remaining sites are already live and already serving real traffic.
- Recovery point and recovery time are both driven toward zero, removing the activation delay and untested-standby risk of a passive strategy.
- The same multi-site deployment that delivers this resilience benefit commonly also improves latency for a geographically distributed audience, since traffic is served from the nearest active site.

### Costs

- Running every site fully active, with real capacity headroom, is genuinely more expensive than running a smaller, idle standby site.
- Building and operating correct, low-latency data synchronization across sites is real, ongoing engineering complexity.
- A conflict resolution strategy has to be designed and maintained correctly, or data can silently diverge between sites in a way that is hard to detect and hard to reconcile after the fact.

## 11. Failure modes and misuse

- Insufficient capacity headroom at the remaining sites, so a real site failure still causes overload rather than a clean absorption of the shifted traffic.
- No genuine conflict resolution strategy, so concurrent writes at different sites silently produce inconsistent data.
- Data synchronization that lags far behind real time, so a site failure still loses meaningful data even though the architecture is labeled active active.
- Adopting this pattern for a workload whose recovery requirements would have been fully met by a much cheaper passive standby strategy, paying the full ongoing cost for a resilience benefit the workload did not actually need.
- Testing failover only in a controlled exercise and never actually verifying real traffic shifts correctly under a genuine, unplanned site failure.

## 12. Trade-off matrix

| Dimension | Passive standby | Multi-site active active |
|---|---|---|
| Recovery point objective | Depends on last replication | Near zero |
| Recovery time objective | Requires an activation step | Potentially zero |
| Ongoing infrastructure cost | Lower, standby is smaller or idle | Higher, every site is fully active |
| Confidence the failover path works | Lower, rarely exercised for real | Higher, every site already serves real traffic |
| Engineering complexity | Lower | Higher, needs real data synchronization |

## 13. Related and incompatible patterns

### Related

- Static Stability. both patterns are about surviving the loss of a site or a zone, but static stability is about each independent unit continuing to operate on its own cached state, while this pattern is about every site actively serving live traffic together.
- Service Level Objective. the near-zero recovery point and recovery time this pattern delivers are a direct lever for meeting a demanding SLO that a passive standby strategy could not realistically achieve.

### Incompatible with

- None directly, though building this pattern with no genuine conflict resolution strategy or insufficient capacity headroom works against its own intent, even though it may still be labeled as active active.

## 14. Refactoring path in and out

### Introducing it

1. Confirm the workload's recovery requirements genuinely justify the ongoing cost of running every site fully active, rather than a cheaper passive standby strategy.
2. Deploy the workload to a second site, and build the data synchronization mechanism that replicates data between the two sites.
3. Design and implement the conflict resolution strategy before routing real write traffic to both sites.
4. Size capacity headroom at each site so it can genuinely absorb the other site's full traffic on failure.
5. Gradually shift real traffic to the new site through traffic distribution, verifying correctness at each step before expanding further, and test a genuine site failure directly, ideally as part of a Game Day exercise.

### Removing it

1. Confirm the workload's recovery requirements have relaxed enough that a cheaper passive standby strategy would genuinely suffice.
2. Shift all traffic to a single primary site, and retire the extra sites' capacity down to a smaller standby footprint.
3. Retire the conflict resolution strategy once writes are no longer accepted at more than one site.

## 15. Testing and verification

- Test a genuine site failure directly, confirming traffic distribution correctly shifts load to the remaining sites and capacity headroom absorbs it without visible disruption.
- Test the conflict resolution strategy directly, with deliberately concurrent writes to the same data at different sites, confirming the outcome matches the intended resolution rule.
- Measure the actual data synchronization lag under real load, confirming the real recovery point objective matches what the architecture claims to deliver.
- Periodically re-run the site-failure test as the workload evolves, confirming the active active design has not silently regressed as new features or dependencies were added.

## 16. Observability signals

- Track data synchronization lag between sites continuously, as a primary measure of the real, current recovery point objective.
- Track how quickly traffic distribution actually shifts load away from a failing site, as a measure of the real recovery time objective.
- Track how often the conflict resolution strategy actually resolves a genuine concurrent write, and how it resolved each one, to catch a resolution rule that is behaving unexpectedly.

## 17. Security and privacy implications

- Data replicated across multiple sites through data synchronization needs to satisfy the same data residency and cross-border transfer requirements at every site it lands in, not only at the site where it was first written.
- Access control and authorization decisions need to be consistent across every active site, since a person's permissions should not silently differ depending on which site happens to serve their request.
- The channel carrying data synchronization between sites is a real, high-value target, and should be encrypted and authenticated with the same rigor as any other inter-service communication carrying production data.

## 18. References

- AWS Well-Architected Framework, Reliability Pillar, planning for disaster recovery (https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html)
- AWS Whitepaper, Disaster Recovery of Workloads on AWS, disaster recovery options in the cloud (https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html)

## Code examples

### Python

```python
from dataclasses import dataclass, field


@dataclass
class Site:
    name: str
    healthy: bool
    capacity_headroom: float


class TrafficDistribution:
    def __init__(self, sites):
        self.sites = sites

    def active_sites(self):
        return [s for s in self.sites if s.healthy]

    def can_absorb_failure_of(self, failed_site_name):
        remaining = [s for s in self.active_sites() if s.name != failed_site_name]
        total_headroom = sum(s.capacity_headroom for s in remaining)
        return total_headroom >= 1.0 / max(len(self.sites) - 1, 1)


sites = [
    Site("us-east", True, 0.5),
    Site("eu-west", True, 0.5),
    Site("ap-south", True, 0.5),
]
distribution = TrafficDistribution(sites)
print('active', [s.name for s in distribution.active_sites()])
print('can absorb eu-west failure', distribution.can_absorb_failure_of("eu-west"))
```

### Kotlin

```kotlin
data class Site(
    val name: String,
    val healthy: Boolean,
    val capacityHeadroom: Double,
)

class TrafficDistribution(private val sites: List<Site>) {
    fun activeSites(): List<Site> = sites.filter { it.healthy }

    fun canAbsorbFailureOf(failedSiteName: String): Boolean {
        val remaining = activeSites().filter { it.name != failedSiteName }
        val totalHeadroom = remaining.sumOf { it.capacityHeadroom }
        val requiredShare = 1.0 / maxOf(sites.size - 1, 1)
        return totalHeadroom >= requiredShare
    }
}

fun main() {
    val sites = listOf(
        Site("us-east", true, 0.5),
        Site("eu-west", true, 0.5),
        Site("ap-south", true, 0.5),
    )
    val distribution = TrafficDistribution(sites)
    println("active " + distribution.activeSites().map { it.name })
    println(
        "can absorb eu-west failure " + distribution.canAbsorbFailureOf("eu-west")
    )
}
```

### Swift

```swift
struct Site {
    let name: String
    let healthy: Bool
    let capacityHeadroom: Double
}

struct TrafficDistribution {
    let sites: [Site]

    func activeSites() -> [Site] {
        sites.filter { $0.healthy }
    }

    func canAbsorbFailure(of failedSiteName: String) -> Bool {
        let remaining = activeSites().filter { $0.name != failedSiteName }
        let totalHeadroom = remaining.reduce(0.0) { $0 + $1.capacityHeadroom }
        let requiredShare = 1.0 / Double(max(sites.count - 1, 1))
        return totalHeadroom >= requiredShare
    }
}

let sites = [
    Site(name: "us-east", healthy: true, capacityHeadroom: 0.5),
    Site(name: "eu-west", healthy: true, capacityHeadroom: 0.5),
    Site(name: "ap-south", healthy: true, capacityHeadroom: 0.5),
]
let distribution = TrafficDistribution(sites: sites)
print("active " + distribution.activeSites().map { $0.name }.description)
print(
    "can absorb eu-west failure "
    + String(distribution.canAbsorbFailure(of: "eu-west"))
)
```
