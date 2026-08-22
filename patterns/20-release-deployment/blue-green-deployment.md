---
name: Blue-Green Deployment
slug: blue-green-deployment
family: 20-release-deployment
category: Deployment
aliases: [Blue Green Release, Red Black Deployment]
first_described: 'Martin Fowler, BlueGreenDeployment bliki article'
maturity: canonical
related: [canary-release, rolling-deployment]
incompatible_with: []
verified: 2026-08-22
---

# Blue-Green Deployment

## 1. Name, aliases, and lineage

Blue-Green Deployment. Also called Blue Green Release or, in some organizations, Red Black Deployment. The pattern is running two identical production environments, conventionally named blue and green, where only one serves live traffic at a time, so a new release can be deployed and verified on the idle environment before traffic switches over instantly. Martin Fowler's own bliki article, the canonical source for this pattern's name, describes the setup directly. you have two production environments, as identical as possible, at any time one of them, let us say blue for the example, is live (https://martinfowler.com/bliki/BlueGreenDeployment.html).

The lineage runs from the same article's description of the release process itself. as you prepare a new release of your software you do your final stage of testing in the green environment, once the software is working in the green environment, you switch the router so that all incoming requests go to the green environment (https://martinfowler.com/bliki/BlueGreenDeployment.html). The pattern's defining property is that the switch itself, from one complete environment to the other, is the release.

## 2. Problem and context

Deploying a new release directly onto the running production environment, in place, risks downtime while the deployment is in progress, and leaves no clean way to undo the change if something goes wrong beyond re-deploying the previous version, which itself takes time and may not even be possible if the deployment process partially corrupted the running environment.

The problem this pattern solves is making a release close to instantaneous from the perspective of live traffic, and making a rollback equally fast, by deploying the new release to a completely separate, already-running environment first, verifying it thoroughly while it carries no live traffic, and only then switching traffic to it, keeping the previous environment fully intact and ready to receive traffic back immediately if needed.

## 3. Forces

- Running two complete production environments simultaneously costs roughly double the infrastructure of running one, for as long as both are kept ready.
- Any data store or persistent state shared between the two environments has to be handled carefully, since a naive schema change that only one environment expects can break the other.
- The traffic switch itself has to be genuinely close to instantaneous, or the pattern's core benefit, a near-zero-downtime release, is undermined.
- A long-lived client connection or an in-flight request active at the exact moment of the switch needs explicit handling, or it can be dropped or routed inconsistently.
- Verifying the idle environment thoroughly before switching requires either synthetic traffic or a way to route a small amount of real traffic to it first, since an environment that has never received real traffic can still hide a problem.

## 4. Applicability and non-applicability

Use Blue-Green Deployment for a release process where near-zero downtime and a fast, reliable rollback matter more than the cost of running two complete environments simultaneously, especially for a stateless or cleanly-separable service where switching traffic between two versions is genuinely safe.

This pattern is a non-applicability fit for a system whose state is deeply, inseparably shared between what would be the blue and green environments, where the doubled-cost environment cannot be made truly independent. It is also often unnecessary for a low-traffic or non-critical service where an in-place deployment's brief downtime is genuinely acceptable, and the added infrastructure cost buys little real benefit.

## 5. Structure

- Blue environment. one of the two complete production environments, conventionally the one currently live at the start of a release cycle.
- Green environment. the other complete production environment, conventionally the one receiving the new release and final verification before the switch.
- Router or load balancer. the single point that directs all live traffic to whichever environment is currently designated live.
- Traffic switch. the deliberate action that changes the router's target from one environment to the other.
- Shared or synchronized data store. whatever persistent state both environments must agree on, handled explicitly so a switch does not desynchronize it.

## 6. ASCII structure diagram

```

  Before the switch                    After the switch
  ------------------                    -----------------
                  +-- BLUE (live)                        +-- BLUE (idle)
  Router --------->|                    Router --------->|
                  +-- GREEN (idle,                       +-- GREEN (live,
                       new release                            switched to)
                       deployed, verifying)

```

## 7. Dynamics

1. The blue environment is currently live, serving all production traffic through the router.
2. The team deploys the new release to the green environment, which currently carries no live traffic.
3. The team runs the final stage of testing against the green environment directly, since as you prepare a new release of your software you do your final stage of testing in the green environment (https://martinfowler.com/bliki/BlueGreenDeployment.html).
4. Once the green environment is verified, the team switches the router so that all incoming requests go to the green environment (https://martinfowler.com/bliki/BlueGreenDeployment.html).
5. The blue environment remains fully intact and ready, so if a problem surfaces after the switch, blue-green deployment gives a rapid way to rollback, switching the router back to the blue environment (https://martinfowler.com/bliki/BlueGreenDeployment.html).
6. Once green is confirmed stable, blue is either retired, kept idle as the standby for the next release cycle, or updated to become the new idle environment for the release after this one.

## 8. Implementation variants

- Full infrastructure duplication. blue and green are each a complete, independently provisioned set of servers, entirely separate hardware or virtual infrastructure.
- Shared infrastructure, separate deployment slot. both environments run on the same underlying infrastructure but in distinct deployment slots, common in platforms that offer a built-in slot-swap mechanism.
- DNS-based traffic switch. the router-equivalent is a DNS record change, trading a slower switch, bound by DNS propagation and client caching, for simpler infrastructure.
- Database-per-environment with a migration bridge. each environment has its own database, kept synchronized or migrated together, avoiding the shared-state coupling risk at the cost of real synchronization complexity.

## 9. Known production uses

- AWS documents blue-green deployment as one of its supported release strategies across several of its own deployment services, letting a workload shift traffic between two identical environments running different application versions.
- Netflix has documented using a blue-green-style deployment approach across parts of its own infrastructure to achieve near-zero-downtime releases.
- Etsy has publicly described using a blue-green-style deployment strategy as part of its continuous delivery practice, favoring the pattern's fast, reliable rollback.

## 10. Consequences

Benefits.

- The traffic switch itself is close to instantaneous, giving a release with near-zero downtime from the perspective of live traffic.
- Rollback is equally fast, since the previous environment stays fully intact and ready to receive traffic back immediately.
- The new release can be verified thoroughly on the idle environment before it ever receives real production traffic.

Costs.

- Running two complete production environments simultaneously roughly doubles infrastructure cost for as long as both are kept ready.
- Any shared or synchronized state between the two environments has to be designed for carefully, or a switch can desynchronize it.
- The switch itself has to genuinely be fast and clean, or in-flight requests active at the exact moment of the switch can be dropped or handled inconsistently.

## 11. Failure modes

- Shared database drift. a schema or data change made against one environment that the other environment does not expect breaks whichever environment receives traffic next.
- Insufficiently verified green environment. an environment that passed synthetic testing but never saw real traffic patterns can still surface a problem the moment the switch happens.
- Dropped in-flight requests at the switch. a request already in progress at the exact moment of the traffic switch can be lost if the switch is not handled gracefully.
- Idle environment left stale. a blue environment kept around as the rollback target, but never refreshed or re-verified, can itself be broken by the time it is actually needed for a rollback.

## 12. Trade-off matrix

| Dimension | Blue-green deployment | In-place deployment |

|---|---|---|

| Downtime during release | Near-zero | Real, however brief |
| Rollback speed | Immediate, switch back | Slower, requires re-deploying the old version |
| Infrastructure cost | Roughly double while both environments are kept ready | Single environment |
| Pre-switch verification against production-shaped traffic | Possible on the idle environment | Not possible without affecting live traffic |
| Shared-state complexity | Real, must be designed for | Simpler, one environment, one state |

## 13. Related and incompatible patterns

Related to Canary Release, an alternative that shifts a small, gradually increasing fraction of traffic to the new version rather than switching everything at once. Related to Rolling Deployment, another alternative that replaces instances of the old version with the new one incrementally rather than maintaining two complete parallel environments. Not incompatible with either. some organizations combine blue-green's clean rollback with a canary-style gradual traffic shift during the verification phase before a full switch.

## 14. Refactoring path in and out

Introducing it.

1. Provision a second, complete production environment, as identical as possible to the existing one.
2. Put a router or load balancer in front of both environments, with the ability to switch which one receives live traffic.
3. Design any shared or persistent state so it can be safely accessed, or kept synchronized, by whichever environment is currently live.
4. Run a full release cycle through the new process, deploying to the idle environment, verifying it, then switching, confirming the rollback path also works before relying on it for a real incident.

Removing it.

1. Confirm the team no longer needs the near-zero-downtime and instant-rollback guarantees this pattern provides, typically because a different deployment strategy now meets the same need at lower cost.
2. Retire the standby environment, or repurpose it, once the team is confident it is no longer needed as a rollback target.
3. Remove the router's dual-environment switching logic, simplifying it back to a single target.
4. Confirm the replacement deployment strategy is genuinely in place and tested before the second environment is fully decommissioned.

## 15. Testing and verification

- Test the traffic switch itself directly, asserting it completes within the expected time budget and that no request is dropped during the switch.
- Test the rollback path explicitly, not only the forward switch, confirming switching back to the previous environment genuinely restores the prior behavior.
- Test the idle environment against production-shaped traffic before the switch, rather than synthetic traffic alone.
- Test the shared or synchronized data store's behavior under both environments accessing it, confirming a schema or data change never breaks the environment not yet expecting it.

## 16. Observability signals

- Traffic switch duration, the direct signal for how close to instantaneous a real switch actually is.
- Error rate on the idle environment during its verification phase, before it ever receives live traffic.
- Error rate spike immediately following a switch, the fastest signal that a rollback may be needed.
- Time since the standby environment was last refreshed, useful for judging whether it is genuinely ready to serve as a rollback target.

## 17. Security and privacy implications

The idle environment, even while carrying no live traffic, is a real production system and has to be secured and patched to the same standard as the live one, since it will become live at the next switch. A shared data store accessed by both environments needs its access controls applied consistently to both, since a security fix applied only to the currently live environment's configuration can silently be undone the next time the idle environment becomes live carrying the old, unpatched configuration.

## 18. Code examples

### Swift

```swift

enum Environment: String {
    case blue
    case green
}

final class TrafficRouter {
    private(set) var live: Environment

    init(live: Environment) {
        self.live = live
    }

    // Switches live traffic to the given environment, the release or rollback action.
    func switchTraffic(to environment: Environment) {
        live = environment
    }
}

```

### Kotlin

```kotlin

enum class Environment { BLUE, GREEN }

class TrafficRouter(private var live: Environment) {
    fun currentLive(): Environment = live

    // Switches live traffic to the given environment, the release or rollback action.
    fun switchTraffic(to: Environment) {
        live = to
    }
}

```

### Python

```python

class TrafficRouter:
    def __init__(self, live):
        self.live = live

    def switch_traffic(self, environment):
        """Switches live traffic to the given environment, the release or rollback action."""
        self.live = environment

```

## 19. References

- Martin Fowler, BlueGreenDeployment, https://martinfowler.com/bliki/BlueGreenDeployment.html
