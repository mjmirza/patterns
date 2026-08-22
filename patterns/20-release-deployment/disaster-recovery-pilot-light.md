---
name: Disaster Recovery Pilot Light
slug: disaster-recovery-pilot-light
family: 20-release-deployment
maturity: canonical
category: Deployment
aliases: [Pilot Light DR, Pilot Light Disaster Recovery]
first_described: 'AWS Disaster Recovery Whitepaper; AWS Well-Architected Framework, Reliability Pillar REL13-BP02'
related: [warm-standby, blue-green-deployment]
verified: true
---

# Disaster Recovery Pilot Light

## Name, aliases, lineage

Pilot Light Disaster Recovery. The name comes from the gas-appliance pilot light, a small flame kept burning at all times so the full burner can be lit instantly on demand, rather than starting a cold furnace from nothing. AWS formalized it as one of four named disaster-recovery strategies in its Disaster Recovery whitepaper and carried it into the Well-Architected Framework's Reliability Pillar as REL13-BP02, alongside Backup and Restore, Warm Standby, and Multi-Site Active-Active. It predates AWS's naming, the same core idea (keep the minimum always-on, provision the rest on failover) appears in mainframe and telecom disaster-recovery practice from decades earlier, but AWS's documentation is the widely cited, precisely defined modern source.

## Problem and context

A production workload runs in one region, and that region can fail, a power event, a network partition, a natural disaster, a regional service outage. A full second production environment running warm in a second region at all times is the safest recovery posture, but it also doubles the steady-state compute bill for capacity that sits idle nearly all the time. A pure backup-and-restore strategy is the cheapest, but rebuilding an entire environment from backups after a disaster can take hours, an unacceptable recovery time for a workload with real availability requirements. The team needs a middle path, a real, working recovery environment that costs close to nothing while healthy, and can be switched on fast enough to matter when the primary region actually goes down.

## Forces

Recovery time against steady-state cost. keeping every layer warm shortens recovery to minutes but pays for idle capacity every hour of every day, while keeping nothing but backups minimizes cost but stretches recovery into hours. Data freshness against replication cost. continuous data replication to the recovery region keeps recovery-point objectives tight, but that replication itself runs continuously and costs money and bandwidth regardless of whether a disaster ever happens. Operational readiness against operational complexity. a recovery environment that is genuinely tested and kept in sync with the primary's configuration is trustworthy, but every configuration drift between primary and recovery infrastructure is a failure waiting to be discovered during the one moment it cannot be discovered safely, an actual disaster.

## Applicability

Reach for pilot light when the workload has a genuine, board-level requirement to survive a full regional outage, the business can tolerate a recovery time in the tens of minutes rather than seconds, and the always-on cost of a second full production environment is not justified by the actual probability and impact of a regional failure. It fits stateful systems whose core data must survive intact and current, a database, a message store, a critical configuration store, where continuous replication is affordable even though the compute layer that serves that data is not kept running.

### Non-applicability

Do not reach for pilot light when the workload's recovery time objective is measured in seconds rather than minutes, that requirement calls for warm standby or multi-site active-active instead, both of which keep a scaled-down or full copy of the compute layer running rather than switched off. Do not reach for it when the team lacks the discipline to actually test the failover regularly, an untested pilot light is worse than an honestly cheap backup-and-restore plan, because it creates false confidence while carrying real ongoing replication cost. Do not reach for it for a stateless workload with no meaningful data-replication need, backup-and-restore or a simple redeploy-from-source into a fresh region is simpler and just as fast.

## Structure

Two regions, a primary that serves live production traffic and a recovery region that stays mostly dark. In the recovery region, the data tier, the database replicas, the object storage replication target, the message queue mirror, runs continuously and stays current with the primary through ongoing replication. The compute tier in the recovery region, the application servers, the container fleet, the serverless functions where applicable, exists only as configuration, machine images, and infrastructure-as-code definitions, not as running instances. A failover trigger, manual or automated, launches that compute tier against the already-current data tier and repoints traffic, DNS, a load balancer, a global accelerator, at the newly live recovery region.

## ASCII structure diagram

```
  Primary region                    Recovery region
  +--------------------+             +--------------------+
  | App servers (live) |             | App servers (off)  |
  |  scaled for load   |             |  0 instances,      |
  +----------+---------+             |  AMI/IaC ready     |
             |                       +----------+---------+
             v                                  ^
  +--------------------+   continuous  +--------+-----------+
  | Primary database   |-------------->| Standby database   |
  |  (read/write)      |  replication  |  (read replica)    |
  +--------------------+               +--------------------+

  Failover: promote standby DB, launch app servers
            from AMI/IaC, repoint DNS/load balancer.
```

## Dynamics

In steady state, the primary region serves all traffic and writes flow only to the primary database, which streams changes to the recovery region's standby database continuously. Nothing runs in the recovery region's compute tier, so there is no application process to monitor, patch, or pay for there under normal operation. When a disaster is declared, the operator, or an automated health check with a human confirmation gate, triggers failover. the standby database is promoted to primary, the application servers are launched from their pre-built machine images or infrastructure definitions and scaled out to production capacity, and traffic is repointed to the now-live recovery region. Once the primary region recovers, a fail-back follows the same shape in reverse, re-establishing replication back toward the original region before traffic returns there, never an instantaneous flip.

## Implementation variants

Database-only pilot light keeps only the data tier warm and rebuilds every other layer, application servers, caches, queues, from infrastructure-as-code on failover, the cheapest and slowest variant. Multi-tier pilot light additionally keeps a minimal core service, an identity provider or a critical control-plane component, running at low capacity in the recovery region, trading a little more steady-state cost for a faster failover of the pieces most other services depend on. Automated pilot light replaces the manual failover trigger with health-check-driven automation that launches the recovery compute tier and repoints traffic without a human step, trading operational risk of a false-positive failover for a faster recovery time.

## Known production uses

AWS documents pilot light as one of its four named recommended disaster-recovery strategies for workloads running on its platform, in both the AWS Disaster Recovery whitepaper and the Well-Architected Framework's Reliability Pillar, and recommends it specifically for workloads whose recovery time objective is in the tens of minutes. It is a standard reference architecture taught in AWS's own certification material and referenced across AWS partner disaster-recovery guidance for regulated industries, financial services and healthcare workloads in particular, where a documented, tested cross-region recovery plan is often a compliance requirement rather than only an operational preference.

## Consequences

The benefit is a real, working, regularly-testable disaster-recovery posture at a fraction of the cost of running a full duplicate production environment, since the expensive compute layer only runs when it is actually needed. Recovery time objective lands in the tens of minutes rather than the hours a pure backup-and-restore approach requires, because the data tier is already current and only the compute tier needs to launch. The cost is the operational discipline pilot light demands, machine images and infrastructure definitions for the recovery region must be kept in lockstep with whatever changes in the primary region, and the failover path itself must be exercised on a real schedule, both are ongoing work that a warm or fully duplicated environment does not require to the same degree, because a warm environment surfaces drift simply by being live.

## Failure modes and misuse

Configuration drift is the dominant failure mode, the recovery region's machine images or infrastructure-as-code definitions fall behind changes made to the primary over months, and the team discovers the drift only when a real failover launches an outdated, broken application. An untested failover path is a second common misuse, a pilot light strategy that has never actually been failed over in a game day or drill is an assumption, not a verified capability, and the first real disaster is the wrong moment to discover a missing IAM permission or an unregistered DNS record. A third misuse is replicating the data tier without replicating the capacity plan for it, the standby database may be current in data but provisioned at a fraction of the primary's compute size, so promoting it under real failover load reveals it cannot actually serve production traffic.

## Trade-off matrix

| Strategy | Steady-state cost | Recovery time | Recovery point |
|---|---|---|---|
| Backup and Restore | Lowest | Hours | Last backup interval |
| Pilot Light | Low | Tens of minutes | Near-continuous |
| Warm Standby | Moderate to high | Minutes | Near-continuous |
| Multi-Site Active-Active | Highest | Seconds or none | Continuous |

## Related and incompatible patterns

Related to Warm Standby, the next strategy up in cost and recovery speed, which keeps a scaled-down but running compute tier in the recovery region instead of a switched-off one. Related to Blue-Green Deployment and Rolling Deployment, which solve a different problem, safely releasing new code within one environment, rather than recovering an entire environment after a regional failure. Related to Database Replication and Read Replica as the data-tier mechanism that keeps the recovery region's data current. Incompatible with a single-region architecture that has no cross-region replication path for its data tier at all, pilot light has nothing to build on in that case.

## Refactoring path in

Start by standing up cross-region replication for the primary data store alone, a read replica or a managed cross-region replication feature, and confirm it stays current under real production write volume. Next, capture the application tier as a machine image or infrastructure-as-code definition that can be deployed into the recovery region without manual steps, and store it versioned alongside the primary region's own deployment definitions so the two never diverge silently. Finally, write and rehearse an actual failover runbook, promote the standby database, launch the compute tier from the stored definition, repoint traffic, and run it as a scheduled game day rather than leaving it as a document nobody has executed.

## Refactoring path out

Moving from pilot light toward warm standby means keeping the recovery region's compute tier running at reduced capacity instead of fully off, shortening recovery time at the cost of a higher steady-state bill, a change made by adjusting the minimum instance count or scaling configuration in the recovery region rather than restructuring the strategy. Moving the other direction, down to plain backup and restore, means removing the continuous data-tier replication and relying on periodic backups instead, appropriate only after confirming the business's actual recovery time requirement no longer demands a tens-of-minutes recovery.

## Testing and verification

Verification is a scheduled, real failover drill, a game day, that promotes the standby database, launches the recovery region's compute tier from its stored image or infrastructure definition, and confirms the application actually serves traffic correctly against the promoted database, not a simulation or a checklist review. Automated infrastructure-as-code validation, plan-and-diff checks that compare the recovery region's definition against the primary region's live configuration, catches drift between drills rather than only at drill time. Recovery time is measured directly during each drill, from the moment failover is declared to the moment the application is serving verified traffic, and tracked over time to confirm it stays within the workload's actual recovery time objective as the system grows.

## Observability signals

Cross-region replication lag is the single most important ongoing signal, a growing lag means the recovery point objective is silently eroding even though nothing else looks wrong. Drift between the primary region's live infrastructure and the recovery region's stored machine image or infrastructure definition is tracked as its own metric, ideally checked automatically rather than discovered during a drill. Time-to-recover from the most recent game day is tracked as a trend, not a one-time number, so a creeping recovery time is caught before it matters. Alerting exists on the primary region's own health so failover is triggered by signal, not by someone noticing the outage independently.

## Security and privacy implications

The recovery region's data tier holds a full, current copy of production data at all times, so it carries the exact same access-control, encryption-at-rest, and encryption-in-transit requirements as the primary, a recovery region that is treated as a lower-security afterthought is a real data-exposure risk, not a theoretical one. Cross-region replication traffic itself must be encrypted in transit and, for regulated data, may be constrained by data-residency rules that limit which regions are legally eligible as a recovery target. IAM roles and secrets used to launch the recovery region's compute tier must be provisioned and rotated on the same schedule as the primary region's, a stale or over-privileged recovery-region credential is exactly the kind of thing an infrequently-used environment tends to accumulate.

## Code examples

### Swift

```swift
enum DisasterRecoveryState {
    case healthy
    case failingOver
    case failedOver
}

struct RecoveryRegion {
    let name: String
    var computeInstanceCount: Int
    var databaseReplicationLagSeconds: Int
}

final class PilotLightController {
    private(set) var state: DisasterRecoveryState = .healthy
    private var recoveryRegion: RecoveryRegion

    init(recoveryRegion: RecoveryRegion) {
        self.recoveryRegion = recoveryRegion
    }

    func triggerFailover(targetInstanceCount: Int) throws {
        guard recoveryRegion.databaseReplicationLagSeconds < 60 else {
            throw FailoverError.replicationTooStale
        }
        state = .failingOver
        recoveryRegion.computeInstanceCount = targetInstanceCount
        state = .failedOver
    }
}

enum FailoverError: Error {
    case replicationTooStale
}
```

### Kotlin

```kotlin
enum class DisasterRecoveryState { HEALTHY, FAILING_OVER, FAILED_OVER }

data class RecoveryRegion(
    val name: String,
    var computeInstanceCount: Int,
    var databaseReplicationLagSeconds: Int,
)

class PilotLightController(private var recoveryRegion: RecoveryRegion) {
    var state: DisasterRecoveryState = DisasterRecoveryState.HEALTHY
        private set

    fun triggerFailover(targetInstanceCount: Int) {
        check(recoveryRegion.databaseReplicationLagSeconds < 60) {
            "Replication lag too high to fail over safely"
        }
        state = DisasterRecoveryState.FAILING_OVER
        recoveryRegion.computeInstanceCount = targetInstanceCount
        state = DisasterRecoveryState.FAILED_OVER
    }
}
```

### Python

```python
from dataclasses import dataclass
from enum import Enum, auto


class DisasterRecoveryState(Enum):
    HEALTHY = auto()
    FAILING_OVER = auto()
    FAILED_OVER = auto()


@dataclass
class RecoveryRegion:
    name: str
    compute_instance_count: int
    database_replication_lag_seconds: int


class ReplicationTooStaleError(Exception):
    pass


class PilotLightController:
    def __init__(self, recovery_region: RecoveryRegion) -> None:
        self.state = DisasterRecoveryState.HEALTHY
        self._recovery_region = recovery_region

    def trigger_failover(self, target_instance_count: int) -> None:
        if self._recovery_region.database_replication_lag_seconds >= 60:
            raise ReplicationTooStaleError(
                "Replication lag too high to fail over safely"
            )
        self.state = DisasterRecoveryState.FAILING_OVER
        self._recovery_region.compute_instance_count = target_instance_count
        self.state = DisasterRecoveryState.FAILED_OVER
```

## References

- Amazon Web Services, Disaster Recovery of Workloads on AWS, Disaster Recovery Options in the Cloud, https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html#pilot-light
- Amazon Web Services, AWS Well-Architected Framework, Reliability Pillar, REL13-BP02 Use defined recovery strategies to meet the recovery objectives, https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html
- Amazon Web Services, AWS Well-Architected Framework, Reliability Pillar, the ordered list of DR strategies by increasing cost, complexity, and decreasing RTO and RPO, https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html#rel_planning_for_recovery_disaster_recovery
