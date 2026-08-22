---
name: Rolling Deployment
slug: rolling-deployment
family: 20-release-deployment
maturity: canonical
category: Deployment
aliases: [Rolling Update, Incremental Deployment]
first_described: 'Kubernetes Deployments documentation; Amazon ECS rolling update deployment type'
related: [blue-green-deployment, canary-release]
verified: true
---

# Rolling Deployment

## Name and Lineage

Rolling Deployment (also called Rolling Update or Incremental Deployment) replaces instances of the old version with instances of the new version in small batches, one batch at a time, on the same fleet, rather than switching all traffic at once (as in Blue-Green Deployment) or diverting a small slice to a separate canary group (as in Canary Release). The name and the mechanics are made explicit in the Kubernetes Deployment controller and in the Amazon ECS rolling update deployment type, both of which describe replacing the currently running instances with new ones in a controlled, incremental sequence.

## Problem and Context

A service running on a fixed-size fleet needs to ship a new version without a full outage and without provisioning a second complete environment. Blue-Green Deployment solves the switch-instantly problem by doubling the fleet temporarily, which costs extra capacity and is not always available on infrastructure with fixed quotas. Rolling Deployment solves the same continuity problem within the existing fleet size, by replacing instances a few at a time so the service as a whole never goes down, even though no second environment ever exists.

## Forces

- Continuous availability during the release, no full-stop window.
- No requirement for a second, fully duplicated environment, so infrastructure cost stays close to the steady-state size.
- The two versions coexist in the same fleet during the rollout, so both must be compatible with the same downstream dependencies (shared database schema, shared cache format) for the whole rollout window.
- Rollback is not instant. reversing a rolling deployment means rolling the old version back in over the same batches, which takes time proportional to the batch size and count.
- The batch size controls the trade-off between rollout speed and blast radius. a larger batch finishes faster but exposes more instances to a bad version before the operator or an automated health check notices.

## Applicability

Use Rolling Deployment when the infrastructure cannot or should not double in size for a release, when the new version is schema- and dependency-compatible with the old version for the duration of the rollout, and when a short partial-exposure window (some requests briefly served by v1, some by v2) is acceptable.

### Non-applicability

Not the right choice when the new version has a backward-incompatible database migration or wire-format change that the old version cannot tolerate running alongside, since both versions run concurrently for the length of the rollout. Not the right choice when instantaneous, single-command rollback is required, since Blue-Green Deployment's router flip is faster than rolling the old version back in. Not the right choice when a slow, monitored, small-percentage exposure to a new version is wanted before any broader rollout, which is what Canary Release is for.

## Structure

A deployment controller (Kubernetes Deployment, an ECS service, a load-balanced instance group) holds a desired count of instances running the old version. The controller is told the new version's image or artifact. It launches a batch of new-version instances, waits for them to pass health checks, then terminates an equivalent batch of old-version instances, and repeats until the whole fleet runs the new version. Two tunable parameters control the pace. how many instances launch or terminate per batch, and how much surplus capacity (instances above the desired count) is allowed while both versions coexist.

## ASCII Diagram

```
  Old fleet: [v1][v1][v1][v1]              New fleet: [ ][ ][ ][ ]
                    |
                    v  batch 1 (25%)
  Old fleet: [v1][v1][v1][  ]              New fleet: [v2][ ][ ][ ]
                    | health check passes
                    v  batch 2 (25%)
  Old fleet: [v1][v1][  ][  ]              New fleet: [v2][v2][ ][ ]
                    | health check passes
                    v  continue until 100%
  Old fleet: [  ][  ][  ][  ]              New fleet: [v2][v2][v2][v2]
```

## Dynamics

The operator or a CI/CD pipeline triggers a deployment with the new artifact reference. The controller computes the first batch size from the configured max-unavailable and max-surge (or equivalent) parameters, launches or updates that batch, and waits for each new instance to report healthy. Once the batch passes, the controller terminates the corresponding batch of old instances and computes the next batch. This repeats until zero old instances remain. If a health check fails partway through, the controller can pause or automatically roll back the batches already flipped, restoring the corresponding count of old-version instances.

## Implementation Variants

- Kubernetes Deployment. the built-in rolling update strategy, tuned with maxUnavailable and maxSurge, driven by pod readiness probes.
- AWS ECS rolling update. tuned with minimumHealthyPercent and maximumPercent, driven by ECS task health checks and, optionally, the deployment circuit breaker for automatic rollback.
- Load-balancer-managed rolling update. an instance group behind a load balancer where instances are drained, replaced, and re-registered in fixed-size batches, common on managed autoscaling groups.
- In-place rolling restart. the same binary host is updated and restarted in place rather than replaced with a new instance, used when instances are not cheaply disposable (bare metal, stateful hosts).

## Known Production Uses

Kubernetes Deployment objects default to the rolling update strategy for any workload that does not explicitly opt into Recreate. Amazon ECS services default to the rolling update deployment type unless a service is explicitly configured for blue-green deployment.

## Consequences

### Benefits

- No second, fully duplicated environment is provisioned, keeping steady-state infrastructure cost close to baseline.
- The service stays available throughout the release, since only a batch at a time is ever offline or draining.
- Failure during a batch limits exposure to that batch's size, rather than the whole fleet at once.

### Costs

- Rollback is not instant, it takes roughly the same time as the forward rollout, batch by batch.
- Two versions run side by side for the whole rollout, so every shared dependency (database schema, message format, feature flags) must tolerate both versions concurrently.
- A slow or wedged health check on one batch can stall the whole rollout partway, leaving the fleet in a mixed-version state until it is resolved.

## Failure Modes

- Schema incompatibility. the new version writes a database schema shape the old version cannot read, and the old version fails while both are still running.
- False-positive health checks. an instance reports healthy before it can actually serve real traffic correctly, so a bad batch keeps rolling forward undetected.
- Batch size too large. a max-surge or max-unavailable value that is too aggressive drops available capacity below what live traffic needs, causing latency or errors during the rollout window, not from the new version itself.
- Stuck rollout. a batch that never reaches healthy blocks all further batches, leaving the fleet mixed indefinitely until an operator intervenes.

## Trade-off Matrix

| Dimension | Rolling Deployment | Blue-Green Deployment | Canary Release |
|---|---|---|---|
| Extra infrastructure needed | None (same fleet size) | Full second environment | Small, temporary canary group |
| Rollback speed | Slow (roll back batch by batch) | Instant (router flip) | Fast (route traffic away from canary) |
| Version coexistence window | Whole rollout duration | None (only during cutover) | Whole canary evaluation window |
| Blast radius on a bad release | Proportional to batch size | Whole new environment, but isolated from live traffic until cutover | Limited to the canary traffic percentage |

## Related and Incompatible Patterns

Related to Blue-Green Deployment and Canary Release, both alternative release strategies solving the same continuity problem with different capacity and rollback trade-offs. Incompatible with any release that requires a backward-incompatible schema change deployed atomically, since Rolling Deployment always runs both versions concurrently for part of the rollout.

## Refactoring Path

### Introducing It

Start from a manual full-fleet redeploy (stop everything, deploy, start everything). Introduce a deployment controller that supports a rolling strategy (Kubernetes Deployment, an ECS service, a managed instance group), set a conservative batch size, and add a health check the controller can use to gate each batch.

### Removing It

Move to Blue-Green Deployment when instant rollback becomes a hard requirement and the extra environment cost is acceptable, or to Canary Release when a slower, more closely monitored partial exposure is wanted before a full rollout.

## Testing and Verification

Verify the health check used to gate each batch actually exercises the new version's real request path, not just a liveness ping. Run a rollout against a staging fleet with an intentionally broken batch to confirm the controller halts or rolls back rather than continuing past a failing batch. Verify the batch size and surplus-capacity settings against real traffic load, so capacity never drops below what live traffic needs during the rollout window.

## Observability Signals

Track the count of instances on each version during a rollout, the pass and fail rate of the per-batch health check, the wall-clock time per batch and for the full rollout, and the error rate and latency of the service as a whole during the rollout window compared to its steady-state baseline.

## Security and Privacy Implications

Because both versions run concurrently, any change to an authentication or authorization check must be compatible in both directions for the length of the rollout, or a request served by the old version could apply a stale security rule. Secrets and credentials used by the new version must already be provisioned and valid before the first batch launches, since there is no separate environment cutover step to gate on.

## Code Examples

### Swift

```swift
struct RollingDeploymentController {
    var totalInstances: Int
    var batchSize: Int
    var isHealthy: (Int) -> Bool

    // Rolls forward batch by batch, halting on the first unhealthy batch.
    func rollOut() -> Int {
        var replaced = 0
        while replaced < totalInstances {
            let batch = min(batchSize, totalInstances - replaced)
            guard isHealthy(replaced + batch) else {
                break
            }
            replaced += batch
        }
        return replaced
    }
}
```

### Kotlin

```kotlin
class RollingDeploymentController(
    private val totalInstances: Int,
    private val batchSize: Int,
    private val isHealthy: (Int) -> Boolean
) {
    // Rolls forward batch by batch, halting on the first unhealthy batch.
    fun rollOut(): Int {
        var replaced = 0
        while (replaced < totalInstances) {
            val batch = minOf(batchSize, totalInstances - replaced)
            if (!isHealthy(replaced + batch)) {
                break
            }
            replaced += batch
        }
        return replaced
    }
}
```

### Python

```python
class RollingDeploymentController:
    def __init__(self, total_instances, batch_size, is_healthy):
        self.total_instances = total_instances
        self.batch_size = batch_size
        self.is_healthy = is_healthy

    def roll_out(self):
        # Rolls forward batch by batch, halting on the first unhealthy batch.
        replaced = 0
        while replaced < self.total_instances:
            batch = min(self.batch_size, self.total_instances - replaced)
            if not self.is_healthy(replaced + batch):
                break
            replaced += batch
        return replaced
```

## References

- Kubernetes, Deployments, https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Amazon Web Services, Deploy Amazon ECS services by replacing tasks, https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html
- Amazon Web Services, Deploy Amazon ECS services by replacing tasks (minimumHealthyPercent), https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html
