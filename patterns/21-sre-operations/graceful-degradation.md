---
name: Graceful Degradation
slug: graceful-degradation
family: 21-sre-operations
category: Behavioral
aliases: [Degraded Mode, Fail Soft, Load Shedding With Fallback]
first_described: 'Google, Site Reliability Engineering, Handling Overload and Addressing Cascading Failures chapters, 2016'
maturity: canonical
related: [error-budget, service-level-objective]
incompatible_with: []
verified: 2026-08-22
---

# Graceful Degradation

## 1. Name, aliases, and lineage

Graceful Degradation. Also called Degraded Mode, Fail Soft, or Load Shedding With Fallback. The pattern is the practice of designing a system to keep operating with reduced functionality when a dependency fails or the system is overloaded, rather than failing completely. Google's SRE book describes the foundational strategy directly. one option for handling overload is to serve degraded responses, responses that are not as accurate as or that contain less data than normal responses, but that are easier to compute (https://sre.google/sre-book/handling-overload/).

The lineage runs from simple load shedding toward something more deliberate. dropping excess work entirely is the blunt version of protecting a system from overload, and this pattern is the refined next step. Google's own SRE book frames it as a direct extension of that idea. Graceful degradation takes the concept of load shedding one step further by reducing the amount of work that needs to be performed (https://sre.google/sre-book/addressing-cascading-failures/), rather than simply refusing the work outright.

## 2. Problem and context

When a system is overloaded, or a dependency it relies on fails, the naive response is to fail every request outright. That produces the worst possible outcome for the person using the system. a complete outage, at exactly the moment the system was under the most stress. The problem this pattern solves is that many requests can still be served usefully with a cheaper, less complete, or less accurate response, rather than not served at all.

This matters most in a large-scale distributed system, where an overloaded or failing component can cascade into failing the entire system if nothing intervenes. reducing the work each request demands, rather than either doing the full work or refusing it entirely, gives the system a middle path that keeps it functioning, even if not at its normal quality, through the exact conditions that would otherwise take it down completely.

## 3. Forces

- A degraded response needs to still be genuinely useful to the person receiving it, or serving it is no better than failing the request outright.
- Deciding when to degrade, and by how much, needs a clear signal (load level, dependency health) or the system either degrades too early, wasting normal capacity, or too late, after the cascading failure has already started.
- Building and maintaining a degraded code path is real extra engineering work on top of the normal, full-quality path, and that path needs its own testing to stay correct.
- A person receiving a degraded response needs some way to understand the response is degraded, or the system silently becomes less trustworthy without anyone noticing why.
- Recovering back to full quality once conditions improve needs its own explicit logic, or the system can get stuck running in degraded mode long after the original overload has passed.

## 4. Applicability and non-applicability

Use Graceful Degradation for any request or feature where a partial, cheaper, or less accurate response is still genuinely useful to the person receiving it, especially in a system that experiences real overload or dependency failure in production. It fits particularly well for search, recommendation, or aggregation-style features, where returning a smaller or less precise result set is far better than returning nothing.

Skip it for a request where a partial or degraded answer is actually worse than no answer at all (a financial transaction, a safety critical action), since serving a degraded version of those requests can cause real harm rather than genuinely helping the person waiting on a full, correct result.

## 5. Structure

- Load or health signal. the measured condition (request rate, dependency latency, error rate) that decides whether the system should be operating in normal or degraded mode.
- Degradation trigger. the threshold on the load or health signal at which the system switches from normal mode into degraded mode.
- Degraded response path. the alternative, cheaper, or less complete logic that serves a request when the system is in degraded mode.
- Degradation indicator. the signal, visible to the person or to downstream systems, that marks a response as degraded rather than normal.
- Recovery check. the ongoing check that determines when conditions have improved enough to return the system to normal mode.

## 6. ASCII structure diagram

```
  Load or health signal measured continuously
        |
        v
  crosses Degradation trigger?  ----- no -----> normal, full response path
        |
        yes
        |
        v
  Degraded response path serves a cheaper, marked result
  (Degradation indicator attached)
        |
        v
  Recovery check monitors the signal
        |
        v
  conditions improved?  ----- yes -----> return to normal mode
```

## 7. Dynamics

1. The system continuously measures its load or health signal, tracking request rate, dependency latency, or error rate as the input that will decide whether degradation is needed.
2. When the signal crosses the degradation trigger, the system switches from its normal path into the degraded response path, serving requests it would otherwise have refused or delayed under the strain.
3. Google's own framing describes the mechanism directly. serving a degraded response means the response is not as accurate as or contains less data than a normal response, but is easier to compute (https://sre.google/sre-book/handling-overload/), which is exactly the trade that lets the system keep functioning under load it could not otherwise sustain.
4. Each degraded response carries a degradation indicator, so the person or downstream system receiving it can tell it is not the normal, full-quality response.
5. The recovery check continues monitoring the load or health signal, and once conditions genuinely improve, the system returns to its normal response path.
6. Because this pattern extends load shedding rather than replacing it, a system may still shed some requests entirely even while serving others in degraded mode, reducing the amount of work performed at every level rather than in one single blunt cutoff (https://sre.google/sre-book/addressing-cascading-failures/).

## 8. Implementation variants

- Reduced-accuracy responses. serving a cheaper, approximate answer (a cached or sampled result) instead of the full, precise computation, the shape Google's own book describes directly.
- Feature-level degradation. disabling a specific, non-essential feature (a recommendation panel, a secondary widget) while keeping the core request path fully functional.
- Stale-data fallback. serving the last known good cached value when a live dependency is failing, rather than failing the request outright.
- Tiered degradation. multiple discrete degradation levels, each shedding progressively more work as the load or health signal worsens, rather than a single binary normal-or-degraded switch.

## 9. Known production uses

- Google's own SRE practice documents serving degraded responses as a standard strategy for handling overload, in the freely available SRE book's Handling Overload chapter (https://sre.google/sre-book/handling-overload/).
- The same book's Addressing Cascading Failures chapter documents graceful degradation as a deliberate extension of load shedding, used specifically to prevent an overloaded component from cascading into a wider system failure (https://sre.google/sre-book/addressing-cascading-failures/).
- Large-scale search, recommendation, and aggregation systems across the industry commonly implement a version of this pattern, returning a smaller or approximate result set under load rather than failing the request entirely.

## 10. Consequences

### Benefits

- A person receiving a degraded response gets something genuinely useful, rather than an outright failure, exactly during the conditions when the system is under the most stress.
- Reducing the work each request demands under load helps prevent an overloaded component from cascading into a wider system failure.
- A tiered degradation design gives the system a graduated response to worsening conditions, rather than a single blunt cutoff between fully working and fully failed.

### Costs

- Building and testing a separate degraded response path is real, ongoing engineering work on top of the normal path.
- A poorly tuned degradation trigger can degrade the system too early, wasting capacity, or too late, after a cascading failure has already started.
- A degraded response that is not clearly marked as degraded can silently erode trust in the system's results without anyone knowing why.

## 11. Failure modes and misuse

- Serving a degraded response for a request where a partial answer is actually worse than no answer at all, such as a financial or safety critical action.
- No degradation indicator, so a degraded response is silently treated as a normal one downstream, hiding a real quality problem.
- No recovery check, so the system stays in degraded mode long after the original overload or dependency failure has cleared.
- A degradation trigger tuned so conservatively that the system degrades too late to actually prevent the cascading failure it was meant to stop.
- Letting the degraded response path rot from lack of testing, so it silently breaks and is only discovered during a real overload, exactly when it is needed most.

## 12. Trade-off matrix

| Dimension | Reduced-accuracy responses | Feature-level degradation |
|---|---|---|
| Person-facing impact | A less precise but still useful answer | A missing secondary feature, core path intact |
| Engineering complexity | Higher, needs a genuinely cheaper computation | Lower, often a simple feature flag |
| Effectiveness under severe overload | High, reduces core computation cost | Moderate, core path cost is unchanged |
| Risk of confusing the person | Higher if not clearly marked | Lower, an absent feature is usually self-evident |

## 13. Related and incompatible patterns

### Related

- Error Budget. time spent serving degraded responses (or failing outright without this pattern) both consume the same error budget, so this pattern is a direct lever for protecting it.
- Service Level Objective. a well designed degraded response can count toward meeting an SLO even under conditions where a full-quality response would not be possible at all.

### Incompatible with

- None directly, though serving a degraded response for a request where a partial answer is actively harmful works against the pattern's own intent, even though it is still labeled as graceful degradation.

## 14. Refactoring path in and out

### Introducing it

1. Identify the requests or features where a partial, cheaper, or less accurate response is still genuinely useful to the person receiving it.
2. Define the load or health signal and the degradation trigger threshold that will decide when the system switches into degraded mode.
3. Build the degraded response path, and attach a clear degradation indicator so the response is never silently mistaken for a normal one.
4. Build the recovery check so the system returns to normal mode once conditions genuinely improve, rather than staying degraded indefinitely.
5. Test the degraded path directly, under simulated overload, confirming it behaves correctly before the system depends on it during a real one.

### Removing it

1. Confirm the request or feature the degraded path covers no longer experiences the overload or dependency failure conditions that made degradation necessary.
2. Retire the degraded response path and its trigger logic, keeping the normal path as the sole implementation.
3. Remove the degradation indicator and any downstream logic that was reading it.

## 15. Testing and verification

- Test the degraded response path directly, under simulated load or a simulated dependency failure, confirming it produces a genuinely usable result rather than a broken one.
- Test the degradation trigger's threshold explicitly, confirming the system switches into degraded mode at exactly the intended signal level, not earlier or later.
- Test the recovery check, confirming the system genuinely returns to normal mode once the load or health signal improves.
- Periodically exercise the degraded path in production, even when not strictly needed, confirming it has not silently rotted since it was last genuinely required.

## 16. Observability signals

- Track how often the system is operating in degraded mode versus normal mode, as a primary measure of how often real overload or dependency failure conditions are actually occurring.
- Track how quickly the system returns to normal mode after conditions improve, confirming the recovery check is genuinely responsive rather than leaving the system stuck degraded.
- Track the person-facing quality difference between a normal and a degraded response, confirming the degraded path is still genuinely useful rather than a token gesture.

## 17. Security and privacy implications

- A degraded response must never bypass an access control or authorization check that the normal response path enforces, even under load, since the pressure to keep responding quickly should never come at the cost of a security check.
- A cached or stale-data fallback used as a degraded response should respect the same data retention and freshness requirements as the normal path, rather than silently serving data past its intended lifetime.
- The degradation indicator itself should not leak internal system health details to an untrusted caller beyond what the person genuinely needs to know their response is degraded.

## Code examples

### Python

```python
from dataclasses import dataclass


@dataclass
class LoadSignal:
    current_load: float
    trigger_threshold: float

    @property
    def should_degrade(self):
        return self.current_load >= self.trigger_threshold


@dataclass
class Response:
    data: object
    degraded: bool


def full_response(request):
    return Response(data="full precise result", degraded=False)


def degraded_response(request):
    return Response(data="cheaper approximate result", degraded=True)


def handle_request(request, signal):
    if signal.should_degrade:
        return degraded_response(request)
    return full_response(request)


signal = LoadSignal(current_load=0.95, trigger_threshold=0.90)
response = handle_request("search query", signal)
print('degraded', response.degraded)
print('data', response.data)
```

### Kotlin

```kotlin
data class LoadSignal(
    val currentLoad: Double,
    val triggerThreshold: Double,
) {
    val shouldDegrade: Boolean
        get() = currentLoad >= triggerThreshold
}

data class Response(val data: String, val degraded: Boolean)

fun fullResponse(request: String): Response =
    Response("full precise result", degraded = false)

fun degradedResponse(request: String): Response =
    Response("cheaper approximate result", degraded = true)

fun handleRequest(request: String, signal: LoadSignal): Response {
    return if (signal.shouldDegrade) degradedResponse(request) else fullResponse(request)
}

fun main() {
    val signal = LoadSignal(currentLoad = 0.95, triggerThreshold = 0.90)
    val response = handleRequest("search query", signal)
    println("degraded " + response.degraded)
    println("data " + response.data)
}
```

### Swift

```swift
struct LoadSignal {
    let currentLoad: Double
    let triggerThreshold: Double

    var shouldDegrade: Bool {
        currentLoad >= triggerThreshold
    }
}

struct ResponseData {
    let data: String
    let degraded: Bool
}

func fullResponse(request: String) -> ResponseData {
    ResponseData(data: "full precise result", degraded: false)
}

func degradedResponse(request: String) -> ResponseData {
    ResponseData(data: "cheaper approximate result", degraded: true)
}

func handleRequest(request: String, signal: LoadSignal) -> ResponseData {
    signal.shouldDegrade ? degradedResponse(request: request) : fullResponse(request: request)
}

let signal = LoadSignal(currentLoad: 0.95, triggerThreshold: 0.90)
let response = handleRequest(request: "search query", signal: signal)
print("degraded " + String(response.degraded))
print("data " + response.data)
```

## 18. References

- Google, Site Reliability Engineering, Handling Overload chapter (https://sre.google/sre-book/handling-overload/)
- Google, Site Reliability Engineering, Addressing Cascading Failures chapter (https://sre.google/sre-book/addressing-cascading-failures/)
