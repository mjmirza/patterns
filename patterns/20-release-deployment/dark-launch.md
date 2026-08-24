---
name: Dark Launch
slug: dark-launch
family: 20-release-deployment
maturity: canonical
category: Deployment
aliases: [Dark Launching, Silent Launch, Invisible Release]
first_described: 'Martin Fowler, DarkLaunching bliki article; Facebook Engineering, Facebook Chat (2008)'
related: [shadow-traffic, canary-release]
verified: true
---

# Dark Launch

## Name and Lineage

Dark Launch (also called Dark Launching, Silent Launch, or Invisible Release) deploys new backend behavior to production and calls it live, from real existing users and real production traffic, without the resulting output or user interface ever being shown. Martin Fowler's bliki article names the technique directly, and Facebook Engineering's own account of the 2008 Chat launch is the widely-cited origin, where Facebook Chat ran live against real users for weeks with no chat UI drawn on the page, purely to validate the backend under genuine production load before a single person ever saw it.

## Problem and Context

A team building a feature with real backend load implications (new servers, new data paths, new query patterns) cannot fully know how that backend behaves under genuine production scale until it actually carries genuine production traffic. Staging environments and synthetic load tests approximate real conditions but never replicate them exactly. Shadow Traffic solves a similar problem by mirroring a COPY of traffic to a separate deployed version whose response is discarded, but that still requires a second running deployment and cannot use the single, already-shipped code path. Dark Launch solves the real-scale validation problem more directly, the real code runs, in the single live deployment, executing for real, but the corresponding user-facing surface stays hidden or unwired, so no user ever sees or interacts with it.

## Forces

- The new code path is exercised for real, against real production traffic and data, so any bug it has produces a real effect on real production state, not a discarded shadow response.
- A feature flag, config toggle, or an unwired UI element is needed to keep the corresponding user-facing surface hidden while the backend runs live.
- Because the backend genuinely executes, this validates real-world load-bearing capacity in a way a shadow copy or synthetic test cannot fully replicate.
- Any user-visible side effect (an email sent, a notification pushed, data displayed elsewhere) must be suppressed or the dark-launched feature is not actually invisible.
- Removing the flag and turning the feature visible is a separate, later step, and the code must have already proven itself stable under real load before that step happens.

## Applicability

Use Dark Launch when a new feature's backend has real scale or load implications that can only be proven under genuine production traffic, and when the feature's user-facing surface (UI, output, notification) can be cleanly hidden behind a flag or toggle while its backend code still runs for real.

### Non-applicability

Not the right choice when the new code cannot be safely run against real production data without a real, unsuppressable user-visible effect (an email, an SMS, a payment), since a dark launch that leaks a visible side effect is not actually invisible. Not the right choice when the goal is to test a completely SEPARATE deployed version rather than exercising the real, single, already-shipped code path, which is what Shadow Traffic is for. Not the right choice when real user-facing behavior and reaction, not just backend load, need to be observed, which is what Canary Release is for.

## Structure

The new backend code, including any new data access, computation, or downstream call, is deployed and merged into the live, single running service. A feature flag or configuration toggle controls whether the corresponding user-facing surface (a UI element, an API response field, a notification) is shown or wired up. With the flag off, the backend code still executes on every relevant request (or on a percentage of them), but its output never reaches the user-visible surface.

## ASCII Diagram

```
  User request --> [App server, new code path executes for real]
                          |
                          +--- writes / reads real production data
                          |
                          v
                    Feature flag: OFF
                          |
                          v
                  UI renders as if the
                  new feature does not exist
```

## Dynamics

A real user's request reaches the live service, which now includes the new code path merged into its normal request handling. The new code executes for real, reading and writing real production data exactly as it would once fully launched. A feature flag check determines whether the resulting output is surfaced to that user, and while the flag is off, the result is computed but never rendered or returned in any user-visible form. The team observes the backend's real performance, error rate, and resource usage under this genuine load. Once confidence is established, the flag is flipped on, gradually or all at once, and the previously-hidden output becomes visible for the first time, with the backend already proven under real conditions.

## Implementation Variants

- **Feature-flagged backend, hidden UI.** the canonical form. the backend code runs live, a feature flag keeps the UI element unrendered.
- **Simulated interaction, no UI at all.** as in the original Facebook Chat launch, the backend simulates the real interaction pattern (queries, connections) that the eventual UI would trigger, with literally no UI element drawn.
- **API-level dark launch.** a new API field or endpoint is computed and populated in the response payload, but the client is not yet updated to read or display it.
- **Percentage-gated dark launch.** the new code path runs for only a percentage of real traffic, controlled the same way a canary's traffic percentage is, but with the output still hidden for all of it.

## Known Production Uses

Facebook Engineering's own account of the 2008 Facebook Chat launch (https://engineering.fb.com/2008/05/13/web/facebook-chat/) describes simulating real user connections, presence queries, and message sends against live chat servers with no chat UI element drawn on the page, specifically to validate the backend under real user-scale load before any user ever saw the feature. Martin Fowler's bliki names Dark Launching as an established technique for calling new or changed backend behavior from existing users without those users being able to tell it is being called.

## Consequences

### Benefits

- Real-world scale and load-bearing behavior is validated using genuine production traffic, which staging and synthetic load tests cannot fully replicate.
- Backend bugs and performance problems are found and fixed before any user ever sees the feature, so the eventual visible launch starts from an already-proven backend.
- Because the code path is the real, single deployed version, no separate shadow deployment or comparison infrastructure is required.

### Costs

- The new code genuinely executes against real production data, so a bug in it has a real effect on production state, unlike a shadow copy whose response is discarded.
- Keeping a user-facing surface reliably hidden while its backend runs requires careful flag and UI discipline, and any leak (a stray notification, a visible API field) breaks the invisibility.
- The feature flag or toggle itself becomes a piece of long-lived infrastructure to manage and eventually remove.

## Failure Modes

- **Leaked visibility.** a notification, an email, or a UI element the team forgot to gate slips out to real users before the intended launch, revealing the feature early.
- **Real side effects mistaken for safe.** an operation assumed harmless (a database write, a cache update) has a downstream effect the team did not anticipate, since the dark-launched code runs for real, not against discarded output.
- **Flag left on indefinitely.** the dark launch validates successfully but the flag is never flipped to visible, or never cleaned up, leaving dead, unused-but-executing code running against production traffic.
- **Confusing load signals.** if the dark-launched code path is more expensive than the eventual real feature will be (because it simulates interactions rather than truly matching future usage patterns), the load validation itself can be misleading.

## Trade-off Matrix

| Dimension | Dark Launch | Shadow Traffic | Canary Release |
|---|---|---|---|
| Code path exercised | The real, single deployed version | A separate, mirrored deployed version | The real, single deployed version |
| Response visible to any real user | No, hidden behind a flag | No, discarded entirely | Yes, for the canary percentage |
| Validates real-world load | Yes, using genuine traffic | Yes, using a mirrored copy of genuine traffic | Yes, using genuine traffic for the canary slice |
| Validates real user reaction | No | No | Yes, for the canary slice |

## Related and Incompatible Patterns

Related to Shadow Traffic (both hide the new code's output from real users while it runs under real conditions, but Dark Launch runs the real single deployment while Shadow Traffic mirrors a copy to a separate one) and Canary Release (which exposes a small percentage of real users to the new version's actual visible output, unlike Dark Launch's fully hidden surface). Incompatible with a feature whose backend cannot be run without a real, unsuppressable user-visible side effect, since that side effect would make the dark launch not actually dark.

## Refactoring Path

### Introducing It

Start from building and testing a feature only in staging before any production exposure. Introduce a feature flag or configuration toggle around the feature's user-facing surface, merge the backend code into the live deployment with the flag off, and let it run against real traffic while confirming its output stays hidden and its backend behaves correctly under real load.

### Removing It

Once the backend has proven itself under real production conditions, flip the feature flag on, either all at once or gradually as in a Rolling Deployment or Canary Release of visibility itself, then remove the now-unneeded flag once the feature is fully and permanently visible.

## Testing and Verification

Verify the feature's user-facing surface genuinely stays hidden while the flag is off, by inspecting the actual UI, API response, and any notification path a real user could observe. Verify the backend code executes correctly against real production data by monitoring its error rate, latency, and resource usage under real traffic. Verify no unsuppressed side effect (an email, a push notification, a visible field) leaks out while the feature is meant to be dark.

## Observability Signals

Track the error rate, latency, and resource usage of the dark-launched code path separately from the rest of the service. Track the volume of real traffic actually exercising the new code path, to confirm the intended load validation is genuinely happening. Track any signal that the hidden surface has leaked (an unexpected support ticket, a stray log line showing user-visible output), which would indicate the dark launch is not actually dark.

## Security and Privacy Implications

Because the dark-launched code runs against real production data for real users, it must meet the same data-handling, access-control, and privacy requirements as any other live production code, there is no relaxed bar just because the output is hidden. Any logging or telemetry added to observe the dark-launched path must not itself become an unintended way the hidden feature's existence or behavior leaks to someone who should not see it.

## References

- Martin Fowler, DarkLaunching, https://martinfowler.com/bliki/DarkLaunching.html
- Facebook Engineering, Facebook Chat (2008), https://engineering.fb.com/2008/05/13/web/facebook-chat/

## Code Examples

### Swift

```swift
struct DarkLaunchGate {
    var isFlagEnabled: () -> Bool
    var runNewBackend: () -> String

    // The new backend always runs for real; only the visible
    // result is withheld while the flag stays off.
    func handle() -> String? {
        let result = runNewBackend()
        return isFlagEnabled() ? result : nil
    }
}
```

### Kotlin

```kotlin
class DarkLaunchGate(
    private val isFlagEnabled: () -> Boolean,
    private val runNewBackend: () -> String
) {
    // The new backend always runs for real; only the visible
    // result is withheld while the flag stays off.
    fun handle(): String? {
        val result = runNewBackend()
        return if (isFlagEnabled()) result else null
    }
}
```

### Python

```python
class DarkLaunchGate:
    def __init__(self, is_flag_enabled, run_new_backend):
        self.is_flag_enabled = is_flag_enabled
        self.run_new_backend = run_new_backend

    def handle(self):
        # The new backend always runs for real; only the visible
        # result is withheld while the flag stays off.
        result = self.run_new_backend()
        return result if self.is_flag_enabled() else None
```
