---
name: Warm Standby
slug: warm-standby
family: 20-release-deployment
maturity: canonical
category: Deployment
aliases: [Active-Passive Warm Standby, Scaled-Down Standby]
first_described: 'AWS Well-Architected Framework, Reliability Pillar REL13-BP02; AWS Disaster Recovery Whitepaper'
related: [disaster-recovery-pilot-light, blue-green-deployment]
verified: true
---

# Warm Standby

## Name, aliases, lineage

Warm Standby, sometimes called Active-Passive Warm Standby. The name sits between two extremes on the disaster-recovery scale of options, a cold environment that must be built from nothing, and a hot, fully scaled duplicate. AWS names it as one of four disaster-recovery strategies alongside Backup and Restore, Pilot Light, and Multi-Site Active-Active, both in its Disaster Recovery whitepaper and in the Well-Architected Framework's Reliability Pillar, REL13-BP02. Microsoft documents the same mechanism in the Azure Well-Architected Framework's disaster-recovery guidance under the equivalent name, active-passive warm standby, confirming the pattern is a vendor-agnostic industry term rather than an AWS-specific coinage. When the standby environment is scaled all the way up to full production capacity rather than kept partially scaled down, the industry calls that variant hot standby, the boundary case where warm standby meets Multi-Site Active-Active.

## Problem and context

A workload's disaster-recovery plan must strike a balance a Pilot Light strategy cannot always reach. Pilot Light keeps the compute tier fully switched off in the recovery region, which is cheap but means a real failover still has to launch every application server from scratch before it can serve a single request, a process that takes tens of minutes even when everything goes right. Some workloads cannot accept that gap, a payments system, a customer-facing checkout flow, a service with a contractual recovery-time commitment measured in single-digit minutes. At the same time, running a full duplicate production environment around the clock, Multi-Site Active-Active, doubles the steady-state compute bill for capacity that, most of the time, serves no traffic at all. The team needs a recovery environment that is already running and can absorb traffic the moment it is needed, without paying for full production scale every hour it sits idle.

## Forces

Recovery time against steady-state cost, a scaled-down but running environment cuts recovery time to minutes because nothing has to be launched from a cold start, only scaled up, but that running fleet, however small, is a real, continuous bill. Confidence against complexity, because the recovery environment is genuinely live all the time, it can be tested and even sent a slice of real production traffic on an ongoing basis, which builds real confidence a Pilot Light environment cannot offer as easily, but that live environment is also one more running system to patch, monitor, and keep consistent with the primary. Scale-up speed against control-plane reliance, the more of the standby fleet is already provisioned before a disaster, the less the failover path depends on the cloud provider's control plane, auto scaling, image launches, provisioning APIs, being available and fast at the exact moment everything else is going wrong.

## Applicability

Reach for warm standby when the business genuinely needs a recovery time in the minutes, not the tens of minutes a Pilot Light strategy delivers, and the extra steady-state cost of a small, always-running recovery fleet is justified by that requirement. It fits workloads where launching new compute from a cold image under real disaster pressure is itself a risk the team wants to avoid, because the recovery path only has to scale existing capacity rather than create it. It is a strong fit when the team wants to run genuine, regular failover drills, even sending a real slice of production traffic to the standby, without that testing itself carrying the cost of launching a full environment from nothing each time.

### Non-applicability

Do not reach for warm standby when the workload's actual recovery-time requirement is comfortably met by Pilot Light, tens of minutes is enough, paying for continuously running standby compute buys nothing the business asked for. Do not reach for it when the requirement is genuinely zero-downtime failover, that calls for Multi-Site Active-Active, where both regions already serve live traffic and there is no scale-up step at all. Do not reach for it for a workload with no meaningful recovery-time requirement in the first place, backup and restore is simpler, cheaper, and just as appropriate when an hours-long recovery window is genuinely acceptable to the business.

## Structure

Two regions, a primary serving all production traffic and a secondary running a real but scaled-down copy of the same application stack at all times. Both the data tier and the compute tier are live in the secondary region, the data tier through continuous replication from the primary, and the compute tier as an actually running, if small, fleet of application instances behind its own load balancer, capable of serving requests right now at reduced capacity. A failover, manual or automated, triggers two things together, promoting the secondary's data tier to primary if it has not already been promoted, and scaling the secondary's compute fleet up to full production capacity, then repointing traffic at the now fully-scaled secondary region.

## ASCII structure diagram

```
Primary region                    Secondary region (warm)
+--------------------+             +--------------------+
App servers (live)                  App servers (live,
 full capacity, N instances          reduced capacity,
                                     N over 4 instances)
+--------------------+             +--------------------+
        |                                    |
        v                                    v
+--------------------+   continuous  +--------------------+
Primary database        replication   Standby database
 (read/write)  ------------------->     (read replica)
+--------------------+               +--------------------+

Failover: scale secondary app servers to N,
          promote standby DB, repoint traffic.
```

## Dynamics

In steady state, the primary region serves production traffic at full scale while the secondary region runs a genuinely live but small fleet, enough to serve health checks, run smoke tests, and optionally absorb a deliberate slice of real traffic for continuous validation. The database in the secondary region streams replication from the primary continuously, the same as Pilot Light. When failover is declared, the operator or an automated trigger scales the secondary's compute fleet from its reduced count up to the primary's normal production count, using the same auto-scaling or orchestration mechanism the team already exercises during normal traffic growth, then promotes the standby database and repoints traffic. Because the fleet is already running rather than being created from scratch, this scale-up step is materially faster and less failure-prone than the launch-from-image step Pilot Light requires.

## Implementation variants

Fixed-ratio warm standby runs the secondary at a constant fraction of primary capacity, a quarter or a tenth, scaling that fraction up on failover, the simplest variant to reason about and capacity-plan. Traffic-shadowed warm standby additionally mirrors a portion of real production traffic to the secondary continuously, not to serve real users but to keep the standby fleet's caches warm and its health genuinely proven under load, at the cost of the mirroring infrastructure itself. Hot standby is the fully-scaled boundary case, the secondary already runs at full production capacity continuously, which shortens recovery time further at a cost that approaches Multi-Site Active-Active while still keeping the secondary passive, not serving live user traffic, until failover.

## Known production uses

AWS documents warm standby as one of its four named disaster-recovery strategies in both the AWS Disaster Recovery whitepaper and the Well-Architected Framework's Reliability Pillar, recommending it specifically for workloads needing a recovery time in minutes rather than tens of minutes. Microsoft documents the identical mechanism, under the name active-passive warm standby, in the Azure Well-Architected Framework's multi-region disaster-recovery design guidance, confirming the pattern as a standard cross-cloud reference architecture rather than a single vendor's naming choice. Both frameworks position it as the standard middle recommendation for regulated and customer-facing workloads whose recovery-time commitments are tighter than Pilot Light supports but whose budgets cannot sustain a fully duplicated Multi-Site Active-Active deployment.

## Consequences

The benefit is a materially faster, more reliable failover than Pilot Light, because the recovery path is a scale-up of an already-running, already-proven fleet rather than a cold launch from a stored image, and because a genuinely live secondary environment can be tested continuously rather than only during scheduled game days. The cost is a real, continuous compute bill for the standby fleet, smaller than a full duplicate but larger than the near-zero cost of a switched-off Pilot Light compute tier, and a second live environment that must be patched, monitored, and kept genuinely healthy at all times, work that a switched-off environment does not demand between drills.

## Failure modes and misuse

Under-provisioning the standby fleet's ratio is the dominant failure mode, a secondary sized at a tenth of production capacity may itself be too small to serve even the reduced traffic it absorbs for continuous testing, or the scale-up on failover may hit a regional capacity limit the team never checked. A second misuse is letting the secondary's fleet drift out of configuration sync with the primary, since it is genuinely running, it is tempting to patch or update it on a different schedule than the primary, and that drift surfaces exactly when failover asks the secondary to carry full production load. A third misuse is treating warm standby as a substitute for a tested failover runbook, a live secondary fleet is not the same as a verified, rehearsed scale-up and traffic-repoint procedure, and skipping the drill because the environment already looks healthy is a false sense of readiness.

## Trade-off matrix

| Strategy | Steady-state cost | Recovery time | Recovery point |
|---|---|---|---|
| Backup and Restore | Lowest | Hours | Last backup interval |
| Pilot Light | Low | Tens of minutes | Near-continuous |
| Warm Standby | Moderate | Minutes | Near-continuous |
| Multi-Site Active-Active | Highest | Seconds or none | Continuous |

## Related and incompatible patterns

Related to Disaster Recovery Pilot Light, the cheaper, slower strategy one step down, which keeps the compute tier switched off entirely rather than scaled down and running. Related to Multi-Site Active-Active, the more expensive, faster strategy one step up, where the secondary already serves live traffic at full scale. Related to Blue-Green Deployment as the mechanism that repoints traffic between two environments, the same repoint step warm standby's failover performs, applied here across regions for disaster recovery rather than within one region for a release. Incompatible with a single-region architecture that has no cross-region replication path at all, warm standby has nothing to run the compute tier against in that case.

## Refactoring path in

Start from an existing Pilot Light setup, cross-region data replication and a stored, deployable image or infrastructure definition for the compute tier already in place. Deploy that compute definition into the secondary region as a genuinely running fleet at a small fraction of production capacity, rather than leaving it switched off, and put it behind its own load balancer so it can serve requests immediately. Next, exercise the scale-up path on a schedule, confirm the secondary's fleet can actually scale from its reduced count to full production capacity within the target recovery time, using real auto-scaling or orchestration rather than a manual, ad hoc launch. Finally, consider routing a deliberate, small slice of real production traffic to the secondary continuously, so its health is proven under real load rather than only during drills.

## Refactoring path out

Moving from warm standby toward Multi-Site Active-Active means scaling the secondary's steady-state fleet all the way up to full production capacity and beginning to route real user traffic to it continuously, removing the scale-up step from the failover path entirely, at the cost of the secondary's steady-state bill rising to match the primary's. Moving the other direction, down to Pilot Light, means scaling the secondary's compute fleet to zero between drills and relying on a stored image or infrastructure definition to relaunch it on failover, appropriate only after confirming the business's actual recovery-time requirement no longer demands a minutes-scale recovery.

## Testing and verification

Verification centers on a real, scheduled failover drill that scales the secondary's already-running fleet up to full production capacity, promotes the database, and repoints traffic, measuring the actual elapsed time against the workload's recovery-time objective rather than trusting the theoretical number. Continuous health checks and, where the team has adopted it, a real slice of shadowed production traffic against the secondary, provide ongoing verification between drills that a Pilot Light strategy's switched-off compute tier cannot offer. Infrastructure-as-code drift checks confirm the secondary's running configuration has not silently diverged from the primary's, since both environments are live and each can be patched independently by mistake.

## Observability signals

Cross-region database replication lag is tracked exactly as it is for Pilot Light, a growing lag erodes the recovery point regardless of how ready the compute tier is. The secondary fleet's own health metrics, error rate, latency, resource utilization, are monitored continuously like any other production fleet, since it genuinely is one. Scale-up time from the standby's reduced capacity to full production capacity is measured on every drill and tracked as a trend, the number that most directly proves whether the recovery-time objective is actually met. Configuration drift between primary and secondary compute definitions is tracked as its own signal, ideally checked automatically rather than only discovered during a drill.

## Security and privacy implications

Because the secondary region's compute tier is genuinely running and, in the traffic-shadowed variant, may handle real production requests, it carries the full production security posture at all times, patching, access control, network policy, not a reduced posture appropriate to an idle environment. The secondary's data tier holds a full, current copy of production data continuously, the same encryption-at-rest, encryption-in-transit, and data-residency obligations as the primary apply without exception. IAM roles, credentials, and secrets provisioned for the secondary region's live fleet must be managed and rotated on the same schedule as the primary's, a live environment that receives less day-to-day attention than the primary is exactly where stale credentials or drifted access policy tend to accumulate unnoticed.

## Code examples

### Swift

```swift
struct WarmStandbyFleet {
    let name: String
    var currentInstanceCount: Int
    let steadyStateInstanceCount: Int
    let fullCapacityInstanceCount: Int
}

enum WarmStandbyError: Error {
    case alreadyAtFullCapacity
    case replicationTooStale
}

final class WarmStandbyController {
    private var fleet: WarmStandbyFleet
    private var replicationLagSeconds: Int

    init(fleet: WarmStandbyFleet, replicationLagSeconds: Int) {
        self.fleet = fleet
        self.replicationLagSeconds = replicationLagSeconds
    }

    func scaleUpForFailover() throws {
        guard fleet.currentInstanceCount < fleet.fullCapacityInstanceCount else {
            throw WarmStandbyError.alreadyAtFullCapacity
        }
        guard replicationLagSeconds < 30 else {
            throw WarmStandbyError.replicationTooStale
        }
        fleet.currentInstanceCount = fleet.fullCapacityInstanceCount
    }

    func scaleBackToSteadyState() {
        fleet.currentInstanceCount = fleet.steadyStateInstanceCount
    }
}
```

### Kotlin

```kotlin
data class WarmStandbyFleet(
    val name: String,
    var currentInstanceCount: Int,
    val steadyStateInstanceCount: Int,
    val fullCapacityInstanceCount: Int,
)

class WarmStandbyController(
    private var fleet: WarmStandbyFleet,
    private var replicationLagSeconds: Int,
) {
    fun scaleUpForFailover() {
        check(fleet.currentInstanceCount < fleet.fullCapacityInstanceCount) {
            "Fleet is already at full capacity"
        }
        check(replicationLagSeconds < 30) {
            "Replication lag too high to fail over safely"
        }
        fleet.currentInstanceCount = fleet.fullCapacityInstanceCount
    }

    fun scaleBackToSteadyState() {
        fleet.currentInstanceCount = fleet.steadyStateInstanceCount
    }
}
```

### Python

```python
from dataclasses import dataclass


@dataclass
class WarmStandbyFleet:
    name: str
    current_instance_count: int
    steady_state_instance_count: int
    full_capacity_instance_count: int


class AlreadyAtFullCapacityError(Exception):
    pass


class ReplicationTooStaleError(Exception):
    pass


class WarmStandbyController:
    def __init__(self, fleet: WarmStandbyFleet, replication_lag_seconds: int) -> None:
        self._fleet = fleet
        self._replication_lag_seconds = replication_lag_seconds

    def scale_up_for_failover(self) -> None:
        if self._fleet.current_instance_count >= self._fleet.full_capacity_instance_count:
            raise AlreadyAtFullCapacityError("Fleet is already at full capacity")
        if self._replication_lag_seconds >= 30:
            raise ReplicationTooStaleError(
                "Replication lag too high to fail over safely"
            )
        self._fleet.current_instance_count = self._fleet.full_capacity_instance_count

    def scale_back_to_steady_state(self) -> None:
        self._fleet.current_instance_count = self._fleet.steady_state_instance_count
```

## References

- Amazon Web Services, AWS Well-Architected Framework, Reliability Pillar, REL13-BP02 Use defined recovery strategies to meet the recovery objectives, Warm standby definition and its distinction from Pilot Light, https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html
- Amazon Web Services, Disaster Recovery of Workloads on AWS, Recovery in the Cloud, Warm Standby section, https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html
- Microsoft, Azure Well-Architected Framework, Develop a disaster recovery plan for multi-region deployments, active-passive warm standby, https://learn.microsoft.com/en-us/azure/well-architected/design-guides/disaster-recovery
