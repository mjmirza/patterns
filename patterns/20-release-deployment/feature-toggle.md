---
name: Feature Toggle
slug: feature-toggle
family: 20-release-deployment
maturity: canonical
category: Deployment
aliases: [Feature Flag, Feature Switch, Feature Flip]
first_described: 'Pete Hodgson, Feature Toggles (Feature Flags), martinfowler.com'
related: [dark-launch, canary-release]
verified: true
---

# Feature Toggle

## Name and Lineage

Feature Toggle (also called Feature Flag, Feature Switch, or Feature Flip) is a runtime configuration mechanism that lets a code path be turned on or off, or routed differently, without a code deployment. Pete Hodgson's article on martinfowler.com is the canonical, widely-cited definition of the technique, describing it as a powerful means of modifying system behavior without changing code. Feature Toggle is a foundational, general mechanism that many other release patterns in this family are built on top of, Dark Launch hides a feature behind one, Canary Release and Rolling Deployment can use one to control exposure, and it also serves as a standalone operational kill switch.

## Problem and Context

Deploying code and releasing a feature to users are, by default, the same event, the moment a deployment finishes, whatever it contains is live for everyone. This coupling means any problem in a newly deployed feature can only be undone by a redeploy or a rollback, both of which take time, and it also means every other pattern that wants finer control over a feature's exposure (hidden while validating, exposed to a percentage, rolled out gradually) needs its own separate mechanism to express that control. Feature Toggle solves both problems at once, by moving the on/off or which-path decision out of the deployment and into a runtime-checked value, so deploying the code and releasing the feature become two separate, independently controllable events.

## Forces

- The toggle check itself runs on every relevant request, so it must be fast and reliable, a slow or unavailable flag store should not take the whole service down.
- Both code paths (the toggled-on and toggled-off behavior) exist in the codebase simultaneously for as long as the toggle is in place, which is real code to maintain, test, and eventually remove.
- A toggle left in place long after its purpose is served becomes technical debt, an extra branch, an extra test matrix dimension, that nobody is actively using.
- Different toggle categories (a permanent operational switch, a temporary release toggle, an experiment toggle) have different appropriate lifespans, and treating them all the same leads to toggle sprawl.
- The toggle's own state needs a management surface (a config file, a database, a dedicated flag-management service) that is itself simple and reliable enough not to become a new point of failure.

## Applicability

Use a Feature Toggle when deploying code and releasing a feature need to happen at different times, when a feature needs an operational kill switch that can turn it off instantly without a redeploy, or when another release pattern (Dark Launch, Canary Release, an A/B test) needs a runtime-controllable on/off or routing decision to build on.

### Non-applicability

Not the right choice as a permanent substitute for proper configuration management, since a toggle is meant to eventually be removed once its purpose (a release, an experiment, a migration) is complete, an indefinitely-lived toggle for something that is really a long-term configuration option should be modeled as configuration, not a temporary toggle. Not the right choice when the two code paths it would gate are so divergent that maintaining both simultaneously creates more risk and complexity than the coupling it was meant to solve. Not sufficient on its own when what is actually needed is real, monitored, gradual traffic shifting, which is what Canary Release or Rolling Deployment provide on top of a toggle.

## Structure

A flag store (a config file, environment variable, database row, or a dedicated feature-flag service) holds the current state of each toggle, typically a boolean or, for more advanced cases, a targeting rule (a percentage, a user segment). Application code checks the relevant toggle's current value at the point where behavior needs to differ, and branches to the appropriate code path based on that value. The toggle's state can be changed at runtime, through the flag store, without any code deployment.

## ASCII Diagram

```
  request --> [check flag store]
                    |
         +----------+----------+
         v                     v
     flag ON                flag OFF
         |                     |
         v                     v
   [new code path]      [old code path]
         |                     |
         +----------+----------+
                    v
                response
```

## Dynamics

A request reaches a point in the code where behavior is meant to be conditional on a toggle. The code queries the flag store (directly, or through a cached local copy refreshed periodically) for the toggle's current value. Based on that value, execution proceeds down the new code path or the old one. If the toggle's value in the flag store changes, whether by an operator flipping it manually or by an automated rollout process, the very next request to check that toggle observes the new value, with no deployment or restart required.

## Implementation Variants

- **Simple boolean flag.** a config value or environment variable, checked with a plain if/else, suitable for a single team and a small number of toggles.
- **Managed feature-flag service.** a dedicated service (LaunchDarkly, Split, Unleash, or an in-house equivalent) that manages flag state, targeting rules, and rollout percentages centrally, with an SDK the application queries.
- **Percentage / targeting-rule toggle.** the toggle's decision is not simply on or off, but computed from a percentage rollout or a user-segment rule, letting the toggle itself drive a gradual or targeted rollout.
- **Compile-time / build-time toggle.** a less flexible variant where the toggle is resolved at build time rather than runtime, trading runtime flexibility for zero runtime overhead, appropriate when the toggle is genuinely long-lived (a platform-specific build) rather than a short-lived release control.

## Known Production Uses

LaunchDarkly (https://launchdarkly.com/blog/what-are-feature-flags/), a dedicated commercial feature-management platform, documents feature flags as removing the stress and risk around software releases, explicitly framing disabling a flag as an instant, redeploy-free way to stop a problematic feature's execution. Pete Hodgson's martinfowler.com article, the canonical reference on the technique, is widely cited across the continuous-delivery community as the definition of feature toggling.

## Consequences

### Benefits

- Deploying code and releasing a feature become two separate, independently controllable events.
- A problematic feature can be turned off instantly, without a redeploy or a rollback, directly reducing the time a bad feature affects production.
- Other release patterns (Dark Launch, Canary Release, gradual rollouts, A/B tests) can build on a toggle as their underlying control mechanism, rather than each inventing its own.

### Costs

- Both code paths a toggle gates exist simultaneously in the codebase for as long as the toggle is in place, adding real maintenance and testing surface.
- A toggle left in place after it is no longer needed becomes technical debt that nobody is actively using but that still adds complexity.
- The flag store itself becomes a dependency the application relies on, and a slow or unreliable flag store can degrade the whole service if not handled carefully (caching, safe defaults on failure).

## Failure Modes

- **Toggle sprawl.** the number of live toggles grows unchecked, with no process to retire ones whose purpose has been served, until the codebase carries far more conditional branches than anyone can reason about.
- **Flag-store outage taking down the service.** the application has no safe default or cached fallback for when the flag store itself is slow or unavailable, so a flag-store problem becomes a service-wide outage.
- **Divergent, untested code paths.** the toggled-off path (or the toggled-on path, for a rarely-enabled toggle) is not exercised by tests as often as the default path, so it silently breaks and is only discovered when the toggle is finally flipped.
- **Combinatorial explosion.** multiple toggles interact in ways nobody explicitly tested, so a particular combination of toggle states produces unexpected behavior.

## Trade-off Matrix

| Dimension | Feature Toggle | Blue-Green Deployment | Canary Release |
|---|---|---|---|
| Requires a redeploy to change exposure | No, flips at runtime | No cutover redeploy, but requires the second environment already deployed | No, traffic percentage adjusts at runtime |
| Granularity of control | Per-feature, can be per-user or per-segment | Whole environment, all traffic at once | Traffic percentage, environment-level |
| Adds long-lived code complexity | Yes, if not retired | No | No |
| Can serve as the mechanism another pattern builds on | Yes (Dark Launch, gradual rollouts) | No | No |

## Related and Incompatible Patterns

Related to Dark Launch, which typically uses a Feature Toggle to keep a live-running feature's user-facing surface hidden, and to Canary Release, which can use a toggle's targeting rules to control what percentage or segment of traffic sees the new behavior. Incompatible with treating a toggle as a permanent configuration mechanism, since a toggle is meant to be temporary and eventually retired once its release, experiment, or migration purpose is complete.

## Refactoring Path

### Introducing It

Start from a codebase where a risky change ships directly with its deployment, all or nothing. Introduce a flag store (even a simple config value to start) and wrap the risky change's entry point in a check against it, so the change can be deployed with the toggle off, then enabled separately once ready.

### Removing It

Once a toggle's purpose (a release, an experiment, a migration) is complete and the toggle has been on (or off) long enough to be trusted permanently, remove the toggle check and the now-dead alternate code path entirely, so the codebase does not carry indefinite toggle debt.

## Testing and Verification

Verify both the toggled-on and toggled-off code paths are exercised by automated tests, not just the default state, so a divergent path does not silently break. Verify the application behaves safely (a sensible default, no outage) when the flag store itself is slow or unavailable. Verify a toggle's state change is observed promptly by the running application, without requiring a restart or redeploy.

## Observability Signals

Track the current state of every live toggle and how long it has been in that state, to catch toggles that have been left unchanged long past their expected lifespan. Track the latency and error rate of the flag-store lookup itself, since it sits on the request path for every toggle-gated feature. Track which code path (toggled-on or toggled-off) actually executes in production, to confirm the toggle behaves as configured.

## Security and Privacy Implications

Access to change a toggle's state should be controlled and audited, since flipping a toggle can change production behavior for every user instantly, with the same operational weight as a deployment. A toggle that gates a security-sensitive code path (an authentication check, an authorization rule) needs the same scrutiny as any other security control, and should never default to the less-secure state if the flag store is unavailable.

## References

- Pete Hodgson, Feature Toggles (Feature Flags), https://martinfowler.com/articles/feature-toggles.html
- LaunchDarkly, What are feature flags, https://launchdarkly.com/blog/what-are-feature-flags/

## Code Examples

### Swift

```swift
struct FeatureToggle {
    var isEnabled: (String) -> Bool

    // Runs the new or old code path based on the flag's current value,
    // checked fresh on every call, with no deployment required to flip it.
    func run(flag: String, newPath: () -> String, oldPath: () -> String) -> String {
        return isEnabled(flag) ? newPath() : oldPath()
    }
}
```

### Kotlin

```kotlin
class FeatureToggle(private val isEnabled: (String) -> Boolean) {
    // Runs the new or old code path based on the flag's current value,
    // checked fresh on every call, with no deployment required to flip it.
    fun run(flag: String, newPath: () -> String, oldPath: () -> String): String {
        return if (isEnabled(flag)) newPath() else oldPath()
    }
}
```

### Python

```python
class FeatureToggle:
    def __init__(self, is_enabled):
        self.is_enabled = is_enabled

    def run(self, flag, new_path, old_path):
        # Runs the new or old code path based on the flag's current value,
        # checked fresh on every call, with no deployment required to flip it.
        return new_path() if self.is_enabled(flag) else old_path()
```
