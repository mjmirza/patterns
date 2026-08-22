---
name: Debounce and Throttle
slug: debounce-and-throttle
family: 13-frontend-ui
category: Event Handling
aliases: [Rate Limiting Input Handlers, Debouncing, Throttling]
first_described: "lodash documentation, debounce and throttle functions"
maturity: canonical
related: [virtual-list, optimistic-ui]
incompatible_with: []
verified: 2026-08-21
---

# Debounce and Throttle

## 1. Name, aliases, and lineage

The canonical name is Debounce and Throttle, two related but distinct
techniques for controlling how often a function runs in response to a
rapidly repeating event, such as typing, scrolling, or resizing.
lodash's own documentation defines each precisely. debounce "creates
a debounced function that delays invoking func until after wait
milliseconds have elapsed since the last time the debounced function
was invoked," while throttle "creates a throttled function that only
invokes func at most once per every wait milliseconds."

The alias **Rate Limiting Input Handlers** names the shared purpose
both techniques serve, controlling the rate at which a handler
actually runs. **Debouncing** and **Throttling** are the gerund forms
commonly used for each technique individually, since they are
frequently discussed and applied separately even though they share a
family and a common problem.

## 2. Problem and context

An event such as a keystroke, a scroll, or a window resize can fire
many times in rapid succession, and attaching an expensive handler
directly to that event, a network request, a heavy recalculation, a
large re-render, runs that expensive work far more often than the
application actually needs. A search box that fires a network request
on every keystroke sends far more requests than the number of times
the user actually pauses to see a result, and a scroll handler that
recalculates a layout on every scroll event runs that recalculation
far more often than the user can perceive a difference. Debounce and
throttle solve this problem in two different, precise ways, debounce
by waiting for the rapid succession of events to genuinely stop before
running the handler once, and throttle by running the handler at a
bounded, regular rate regardless of how fast the underlying events
keep firing.

## 3. Forces

The pattern balances the following competing pressures.

- **Reducing wasted, redundant work.** Favored, by both techniques. A
  handler that would otherwise run on every single rapid-fire event
  instead runs far less often, directly cutting the redundant work of
  responding to events the user has already superseded with a later
  one.
- **Responsiveness during the rapid event sequence.** In tension.
  Throttle favors partial, in-progress feedback, since it "guarantees
  the execution of the function regularly, at least every X
  milliseconds," while debounce favors completeness over immediacy,
  waiting for the sequence to genuinely stop before running the
  handler even once.
- **Correctness of the final state.** Favored by debounce
  specifically. Since debounce fires only after the event sequence
  stops, the handler always runs against the final, settled state
  rather than a possibly stale intermediate one.
- **Predictable, bounded execution frequency.** Favored by throttle
  specifically. Since throttle runs at a fixed rate regardless of
  event frequency, a caller can reason about an upper bound on how
  often the handler executes, a guarantee debounce alone does not
  provide during an event sequence that never actually stops.

## 4. Applicability and non-applicability

Reach for debounce when the following hold.

- The handler should run once, against the final state, only after
  the user has genuinely stopped triggering the event, such as
  waiting for a user to stop typing before sending a search request.
- Running the handler during the rapid event sequence itself provides
  no real value, since only the final result actually matters to the
  user.

Reach for throttle when the following hold.

- The handler provides real, ongoing value even while the event
  sequence is still happening, such as updating a scroll-position
  indicator or a live preview while the user continues scrolling or
  dragging.
- A predictable, bounded execution rate matters more than waiting for
  the sequence to fully settle.

Do NOT reach for either technique in these cases, and the reason
matters more than the rule.

- **The handler is already cheap enough that running it on every raw
  event causes no real, measured cost**, adding debounce or throttle
  to an already-cheap handler adds delay and complexity for no
  corresponding benefit.
- **The user genuinely needs to see every individual event's effect,
  not only the final or periodic state**, such as a drawing or
  annotation tool where every intermediate stroke matters, applying
  either technique would visibly drop input the user expects to see
  reflected.
- **Debounce is applied to a scenario the user experiences as
  ongoing feedback, such as a live progress indicator**, waiting for
  the event sequence to stop before showing anything makes the
  interface feel unresponsive during the exact moment the user is
  actively interacting with it, precisely the case throttle exists
  to serve instead.

## 5. Structure

Debounce and throttle share two structural parts, applied
differently.

- **The wrapped handler**, the original function whose invocation
  frequency needs controlling, unchanged in what it does, only in how
  often it runs.
- **The timing controller**, a wrapper that tracks elapsed time since
  the last invocation or the last event, and decides, according to
  its own specific rule, debounce's reset-on-every-event delay versus
  throttle's fixed-interval gate, whether the current call should run
  the wrapped handler now, later, or not at all.

## 6. ASCII structure diagram

```
  Debounce, wait = 300ms

  event -- event -- event ---------------- (silence) --> fire handler
  |________|________|
    each event resets the 300ms timer,
    handler fires only after 300ms of silence

  Throttle, wait = 300ms

  event -- event -- event -- event -- event -- event
  |____________________________________________________
  fire    (skip)  (skip)   fire    (skip)   fire
  0ms              ~300ms          ~600ms
    handler fires at most once per 300ms window,
    regardless of how often the raw event fires
```

## 7. Dynamics

The trace below shows a user typing into a debounced search box, and
a user scrolling with a throttled position handler.

```
Debounced search input

the user types "r", "e", "a", "c", "t" in quick succession
   |-- each keystroke resets the debounce timer
   |-- while keystrokes keep arriving, the timer never completes,
       so the search request handler never runs
   |-- the user pauses, no keystroke arrives for the configured wait
   |-- the timer completes, the search request finally fires, once,
       with the final value "react"

Throttled scroll handler

the user scrolls continuously down the page
   |-- the first scroll event fires the position handler immediately
   |-- subsequent scroll events arriving within the throttle window
       are skipped, the handler does not run for each of them
   |-- once the window elapses, the next scroll event fires the
       handler again, updating the position indicator
   |-- this repeats at the bounded rate for as long as scrolling
       continues, giving ongoing, periodic feedback rather than a
       single final result
```

## 8. Implementation variants

**Library-provided implementations.** A utility library such as
lodash provides tested, edge-case-hardened debounce and throttle
functions directly, including options for leading and trailing edge
invocation, rather than a team hand-rolling the timer logic.

**Leading-edge versus trailing-edge invocation.** Both debounce and
throttle can be configured to fire on the leading edge of the event
sequence, immediately on the first event, the trailing edge, after
the sequence settles or the interval elapses, or both, changing when
exactly within the sequence the handler actually runs.

**Framework-level hooks.** A UI framework's own surrounding tooling often
provides a hook or composable wrapping the same debounce or throttle
logic, integrated with the framework's own reactivity or state update
cycle rather than a standalone timer.

**RequestAnimationFrame-based throttling.** A variant of throttle
that gates the handler to run at most once per animation frame,
rather than a fixed millisecond interval, useful specifically for
handlers that update visual state a browser would only repaint once
per frame anyway.

## 9. Known production uses

**CSS-Tricks, defining debounce and throttle and their difference.**
The reference article states each technique's core mechanism
directly. "The Debounce technique allow us to group multiple
sequential calls in a single one," while for throttle, "we don't
allow to our function to execute more than once every X
milliseconds," adding that "throttle guarantees the execution of the
function regularly, at least every X milliseconds." CSS-Tricks,
"Debouncing and Throttling Explained Through Examples,"
https://css-tricks.com/debouncing-throttling-explained-examples/,
verified 2026-08-21.

**lodash's own documentation, defining each function precisely.**
lodash states each function's contract directly. debounce "creates a
debounced function that delays invoking func until after wait
milliseconds have elapsed since the last time the debounced function
was invoked," while throttle "creates a throttled function that only
invokes func at most once per every wait milliseconds." lodash,
"Documentation," https://lodash.com/docs/4.17.15, verified
2026-08-21.

## 10. Consequences

Positive.

- Redundant work, a network request, a recalculation, a re-render,
  runs far less often than the raw event rate, directly cutting the
  cost of responding to events the user has already superseded.
- Debounce guarantees the handler runs against the final, settled state
  when it is only the end result that matters, avoiding wasted work
  on intermediate states the user never actually sees.
- Throttle gives a predictable, bounded execution rate, letting a
  caller reason about an upper bound on how often expensive work runs
  even during a continuous, ongoing event sequence.

Negative.

- Debounce introduces a real, deliberate delay before the handler
  ever runs, which is wrong specifically for a case where the user
  expects immediate, ongoing feedback.
- Throttle can still miss the exact final state if it fires only on a
  fixed interval and the event sequence stops between intervals,
  unless paired with a trailing-edge invocation to catch that final
  state.
- Both techniques add a real timing dependency to the handler's
  invocation, which needs care in testing, since a handler's timing
  is no longer simply tied one-to-one with the raw event.

## 11. Failure modes and misuse

**Using debounce for a scenario the user experiences as ongoing,
real-time feedback, such as a live drag-position indicator.** Symptom.
The interface feels unresponsive or laggy during the exact interaction
the user is actively performing, since debounce withholds the handler
entirely until the interaction stops. Cause. Choosing debounce because
it reduces call frequency, without considering that the specific
scenario needs periodic feedback during the interaction, not only a
final result after it ends. Fix. Use throttle instead, which provides
bounded, periodic feedback throughout the interaction rather than
withholding it until the interaction completes.

**Using throttle for a scenario where only the final, settled state
matters, such as a search-as-you-type box.** Symptom. The handler
fires multiple times during typing, sending redundant, partial
queries the user never intended to see results for, wasting exactly
the request volume the technique was meant to reduce. Cause. Choosing
throttle because it limits call frequency, without considering that
the specific scenario needs to wait for the user to genuinely finish,
not merely to rate-limit intermediate firings. Fix. Use debounce
instead, so the handler runs once, against the final value, only
after the user has stopped typing.

**Creating a new debounced or throttled function on every render or
every call, instead of a single, stable, reused instance.** Symptom.
The debounce or throttle behavior appears not to work at all, since
each new instance starts its own independent timer with no memory of
previous calls, defeating the entire purpose of tracking elapsed time
across calls. Cause. Wrapping the handler inline inside a function
that itself re-runs frequently, rather than creating the wrapped
version once and reusing that same instance across every subsequent
call. Fix. Create the debounced or throttled function once, outside
the code path that runs repeatedly, and reuse that single instance for
every call.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Debounce | Throttle | No rate limiting |
|---|---|---|---|
| Reducing wasted, redundant work | Strong, collapses a rapid sequence into one final call | Strong, bounds the rate to a fixed interval | Weak, every raw event runs the full handler |
| Feedback during the ongoing interaction | Weak, deliberately withholds until the sequence stops | Strong, periodic feedback throughout | Strong, but at the cost of redundant work |
| Correctness of the final state | Strong, always runs against the settled value | Moderate, can miss the exact final state without a trailing-edge call | Strong, but redundantly recomputed many times |
| Predictable, bounded execution rate | Weak during a sequence that never stops | Strong, a fixed upper bound regardless of event rate | Weak, execution rate matches raw event rate exactly |

Reading of the table. Debounce wins specifically when only the final,
settled state matters and immediate feedback during the sequence is
not needed. Throttle wins when the user genuinely benefits from
periodic feedback throughout an ongoing interaction. Neither is a
strict improvement over the other, and applying the wrong one to a
given scenario is precisely the failure mode named in dimension 11.

## 13. Related and incompatible patterns

- **Virtual List.** A complementary technique for the specific case of
  a scroll handler, since a throttled scroll position calculation and
  a virtualized list's rendering logic are frequently used together
  to keep a long, scrolling list responsive.
- **Optimistic UI.** A different response to a related feeling
  problem, showing a predicted result of a user's own action
  immediately rather than delaying feedback until a debounced or
  throttled handler actually runs.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing handler currently attached
directly to a rapidly firing event with no rate limiting.

1. Identify whether the handler's scenario needs a single final
   result, favoring debounce, or ongoing periodic feedback, favoring
   throttle.
2. Wrap the handler once, outside any code path that re-runs on every
   render or every call, using a tested library implementation rather
   than a hand-rolled timer where one is available.
3. Choose the wait interval based on the specific interaction, short
   enough that the delay feels responsive, long enough to genuinely
   collapse the rapid-fire sequence into noticeably fewer calls.
4. For throttle, decide whether a trailing-edge invocation is needed
   to catch the final state after the last event in a sequence that
   stops between intervals.
5. Measure the actual reduction in handler invocations against the
   pre-change baseline, confirming the change produced a genuine
   improvement.

Removing the pattern when it stops earning its place, most relevant
when the underlying handler has become cheap enough, or the event
frequency has dropped enough, that rate limiting no longer earns its
added delay and complexity.

1. Confirm, through measurement, that the handler's raw invocation
   frequency and cost genuinely no longer justify rate limiting,
   rather than assuming so without checking.
2. Remove the debounce or throttle wrapper, restoring the handler's
   direct attachment to the raw event.
3. Re-measure to confirm removing the wrapper did not reintroduce a
   genuine performance problem.

## 15. Testing and verification

Easier because of the pattern.

- A test can assert the wrapped handler is called exactly once after
  a rapid sequence of simulated events, directly verifying the
  collapsing behavior debounce and throttle are meant to provide.
- Because the timing logic is isolated inside the wrapper, a test can
  assert the wrapper's own timing behavior, when it fires relative to
  the events it receives, independently of whatever the wrapped
  handler itself does.

Harder because of the pattern.

- Testing debounce or throttle correctly needs controlling the
  passage of time deterministically, such as with fake or mocked
  timers, since a real wall-clock wait in a test suite is slow and
  flaky.
- Verifying leading and trailing edge behavior specifically needs
  distinct test cases for each configuration, since the exact moment
  the handler fires within the sequence differs noticeably between
  them.

Techniques that apply.

- **Fake timer tests.** Use a test environment's fake or mocked timer
  facility to advance time deterministically and assert exactly when
  the wrapped handler fires relative to a simulated event sequence.
- **Call-count assertions.** Simulate a rapid sequence of events and
  assert the wrapped handler was called the expected number of times,
  not once per raw event.
- **Leading and trailing edge case coverage.** Write a dedicated test
  for each configured edge behavior, confirming the handler fires at
  the expected point in the sequence for that specific configuration.
- **Reuse verification.** Assert the same wrapped instance is reused
  across calls, rather than a fresh instance being created on every
  invocation of the surrounding code, catching the specific misuse
  named in dimension 11.

## 16. Observability signals

Debounce and throttle have a genuine, measurable runtime footprint,
since they directly govern how often a real handler actually runs in
response to real user interaction, so a dedicated production signal
is honest here.

What to record.

- The ratio of wrapped-handler invocations to raw event occurrences,
  since a ratio close to one suggests the wrapper is not noticeably
  reducing call frequency, and a ratio approaching zero on a
  debounced handler that never sees the sequence settle may point at
  an interval that never allows the handler to fire at all.
- The delay between the raw event that should trigger the final
  debounced call and that call actually firing, since an
  unexpectedly long delay points at a wait interval mismatched to
  the interaction's real pace.

A healthy state. The wrapped handler fires noticeably less often
than the raw event rate, and for debounce, it consistently fires
shortly after the user genuinely stops the interaction rather than
seeming to hang indefinitely.

A failing state. The wrapped handler fires nearly as often as the raw
event, pointing at a new instance being created on every call rather
than a single, reused wrapper, or a debounced handler that rarely or
never fires, pointing at an interval too long relative to how the
event actually occurs in practice.

## 17. Security and privacy implications

Debounce and throttle are close to neutral for security, being
timing-control techniques rather than data-handling ones, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**Client-side debounce or throttle reduces the FREQUENCY of requests
a well-behaved browser sends, but it provides no actual security
guarantee against a client that bypasses the client-side code
entirely and sends requests directly, so any rate limit that matters
for genuine abuse prevention, rather than merely reducing normal-user
request volume, must be enforced on the server, independent of
whatever debounce or throttle interval the client-side code
applies.** Treating a client-side debounce or throttle interval as a
substitute for server-side rate limiting is a mistake specific to how
easily the two can look similar, since both bound request frequency,
but only the server-side version is enforced against a client that
does not cooperate.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models both debounce and
throttle as generic higher-order functions the way lodash's own
implementation is commonly used, kept free of JSX and any specific
framework's package so the sample compiles as plain TypeScript.
Python shows the conceptual shape of the same two timing controllers
using a minimal, framework-agnostic implementation, since Python has
no browser event loop and therefore no single dominant debounce and
throttle implementation the way TypeScript has lodash and the
browser's own timer APIs. Swift shows the same conceptual shape using
a minimal model, analogous to how a native app might rate-limit a
handler responding to a rapidly repeating gesture or text field
change. Java, Go, and Rust are omitted, since none has a dominant,
idiomatic browser-facing event-handling toolset this specifically
UI-event pattern maps to as directly as TypeScript does.

### TypeScript

```typescript
function debounce<T extends (...args: never[]) => void>(
  fn: T,
  waitMs: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>): void => {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      fn(...args);
    }, waitMs);
  };
}

function throttle<T extends (...args: never[]) => void>(
  fn: T,
  waitMs: number
): (...args: Parameters<T>) => void {
  let lastCallTime = 0;

  return (...args: Parameters<T>): void => {
    const now = Date.now();
    if (now - lastCallTime >= waitMs) {
      lastCallTime = now;
      fn(...args);
    }
  };
}

const search = (query: string): void => {
  console.log("searching for:", query);
};

const debouncedSearch = debounce(search, 300);

const updatePosition = (position: number): void => {
  console.log("updating position:", position);
};

const throttledUpdatePosition = throttle(updatePosition, 300);

debouncedSearch("r");
debouncedSearch("re");
debouncedSearch("react");

throttledUpdatePosition(10);
throttledUpdatePosition(20);
throttledUpdatePosition(30);
```

### Python

```python
import time
from typing import Callable


def debounce(fn: Callable[..., None], wait_seconds: float) -> Callable[..., None]:
    state = {"last_call_time": 0.0}

    def wrapped(*args, **kwargs) -> None:
        state["last_call_time"] = time.monotonic()
        scheduled_time = state["last_call_time"]

        def maybe_run() -> None:
            if state["last_call_time"] == scheduled_time:
                fn(*args, **kwargs)

        time.sleep(0)
        maybe_run()

    return wrapped


def throttle(fn: Callable[..., None], wait_seconds: float) -> Callable[..., None]:
    state = {"last_call_time": 0.0}

    def wrapped(*args, **kwargs) -> None:
        now = time.monotonic()
        if now - state["last_call_time"] >= wait_seconds:
            state["last_call_time"] = now
            fn(*args, **kwargs)

    return wrapped


def search(query: str) -> None:
    print(f"searching for: {query}")


def update_position(position: int) -> None:
    print(f"updating position: {position}")


if __name__ == "__main__":
    throttled_update_position = throttle(update_position, 0.3)
    throttled_update_position(10)
    throttled_update_position(20)
    throttled_update_position(30)
```

### Swift

```swift
import Foundation

final class Debouncer {
    private var workItem: DispatchWorkItem?
    private let wait: TimeInterval

    init(wait: TimeInterval) {
        self.wait = wait
    }

    func call(_ action: @escaping () -> Void) {
        workItem?.cancel()
        let newItem = DispatchWorkItem(block: action)
        workItem = newItem
        DispatchQueue.main.asyncAfter(deadline: .now() + wait, execute: newItem)
    }
}

final class Throttler {
    private var lastCallTime: Date = .distantPast
    private let wait: TimeInterval

    init(wait: TimeInterval) {
        self.wait = wait
    }

    func call(_ action: () -> Void) {
        let now = Date()
        if now.timeIntervalSince(lastCallTime) >= wait {
            lastCallTime = now
            action()
        }
    }
}

func search(_ query: String) {
    print("searching for: " + query)
}

func updatePosition(_ position: Int) {
    print("updating position: " + String(position))
}

let throttler = Throttler(wait: 0.3)
throttler.call { updatePosition(10) }
throttler.call { updatePosition(20) }
throttler.call { updatePosition(30) }
```

## 18. References

1. CSS-Tricks. "Debouncing and Throttling Explained Through Examples".
   https://css-tricks.com/debouncing-throttling-explained-examples/
   Verified 2026-08-21. Source of the defining debounce and throttle
   quotes used in dimensions 1, 3, and 9.
2. lodash. "Documentation".
   https://lodash.com/docs/4.17.15
   Verified 2026-08-21. Source of the precise function-contract quotes
   used in dimensions 1 and 9.
