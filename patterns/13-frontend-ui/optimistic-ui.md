---
name: Optimistic UI
slug: optimistic-ui
family: 13-frontend-ui
category: Interaction Pattern
aliases: [Optimistic Updates, Optimistic Rendering]
first_described: "React documentation, useOptimistic hook"
maturity: established
related: [hooks, state-machine-ui, redux]
incompatible_with: []
verified: 2026-08-21
---

# Optimistic UI

## 1. Name, aliases, and lineage

The canonical name is Optimistic UI, a pattern where the interface
immediately shows the expected result of a user's action before the
action's underlying asynchronous request has actually finished, then
reconciles with the real result once it arrives. React's own
documentation for its dedicated `useOptimistic` hook names the idea
and its reasoning directly. "This state is called the optimistic
because it is used to immediately present the user with the result of
performing an Action, even though the Action actually takes time to
complete."

The alias **Optimistic Updates** names the specific act of applying
the expected result before confirmation. **Optimistic Rendering** is
a more render-focused variant of the same name, emphasizing that what
changes first is what the interface displays, not the underlying data
itself.

## 2. Problem and context

A user action that triggers a network request, liking a post,
sending a message, adding an item to a list, commonly leaves the
interface showing its prior, unchanged state until the request
resolves, forcing the user to wait, sometimes for a noticeable
duration on a slow connection, before seeing any visible confirmation
that their action registered at all. This makes an interface feel
sluggish even when the underlying operation is likely to succeed the
overwhelming majority of the time. Optimistic UI solves this by
updating the interface immediately with the expected result the
moment the user acts, rendering that expected state while the real
request is still in flight, and reconciling the display with the
actual server response only once it arrives, either confirming the
optimistic state was correct or rolling it back if the request
ultimately failed.

## 3. Forces

The pattern balances the following competing pressures.

- **Perceived responsiveness.** Favored. The interface reflects the
  user's action the instant they take it, rather than waiting for a
  round trip to a server, making the experience feel immediate
  regardless of actual network latency.
- **Correctness when the underlying action fails.** Sacrificed
  temporarily, and recovered through rollback. Because the optimistic
  state is a prediction, not a confirmed fact, the interface must be
  prepared to revert to the prior state, and inform the user, when the
  real request ultimately fails.
- **Simplicity of interface state.** Sacrificed. An interface using
  Optimistic UI must track both what the server has actually
  confirmed and what has been optimistically predicted but not yet
  confirmed, a real amount of additional state complexity a purely
  request-then-render interface would not need.
- **Confidence that the action will usually succeed.** Favored.
  Optimistic UI is worth its complexity specifically when the
  underlying action is expected to succeed the overwhelming majority
  of the time, so the common case benefits from the immediate feedback
  and the rare failure case is a genuine exception to handle
  gracefully.

## 4. Applicability and non-applicability

Reach for Optimistic UI when the following hold.

- The action being performed is expected to succeed the large
  majority of the time, so immediately showing the expected result is
  correct far more often than it needs correction.
- The perceived responsiveness of the interaction genuinely matters
  to the experience, such as a like button, a chat message, or a list
  item toggle, where a visible delay before any feedback would feel
  sluggish.
- The interface can genuinely roll back to the prior state and inform
  the user gracefully in the rare case the underlying action fails,
  rather than leaving the user confused about what actually happened.

Do NOT reach for Optimistic UI in these cases, and the reason matters
more than the rule.

- **The action has a real chance of failing, or its outcome
  cannot be predicted in advance**, such as a payment charge whose
  actual success depends on a real-time authorization decision, where
  showing a predicted success the interface cannot reliably guarantee
  risks misleading the user.
- **The consequence of the interface being visibly wrong for even a
  moment is unacceptable**, such as a safety-critical control or a
  financial balance display, where a temporarily incorrect optimistic
  state could cause real harm even if it is later corrected.
- **The team cannot build a genuine rollback path**, adopting the
  immediate-feedback benefit of Optimistic UI without a real,
  tested way to revert and inform the user on failure leaves users
  confused when the rare failure case actually occurs.

## 5. Structure

Optimistic UI has three structural parts.

- **The optimistic state**, the predicted result of the user's
  action, rendered immediately, distinct from the confirmed state the
  server has not yet returned.
- **The pending action**, the actual asynchronous request sent to the
  server, running independently of what the interface is currently
  displaying.
- **The reconciliation step**, the point at which the optimistic
  state and the real, confirmed result converge, either by the real
  result matching the prediction, or by the interface rolling back to
  the prior confirmed state when the action fails.

## 6. ASCII structure diagram

```
  User action
      |
      v
  +--------------------+       +----------------------------+
  | Optimistic state    | <---  | rendered immediately        |
  | (predicted result)  |       +----------------------------+
  +--------------------+
      |
      v
  +--------------------+
  | Pending action       |  (the real request, in flight)
  +--------------------+
      |
      +----------------------+----------------------+
      |                                              |
      v                                              v
  Action succeeds                              Action fails
      |                                              |
      v                                              v
  Real state confirms                     Roll back to prior
  the optimistic prediction                confirmed state,
                                            inform the user
```

## 7. Dynamics

The trace below shows a user liking a post, the interface updating
immediately, and the eventual server confirmation.

```
User interaction

the user clicks the like button on a post
   |-- the optimistic state is set immediately, showing the post as
       liked and incrementing the visible like count
   |-- the actual like request is sent to the server, in the
       background, while the optimistic state is already displayed

Server responds successfully

the server confirms the like was recorded
   |-- the real, confirmed state now matches what the optimistic
       state already predicted
   |-- the interface's displayed state and the confirmed state
       converge, with no visible change needed, since the prediction
       was correct

Server responds with a failure

the server rejects the like request, the action fails
   |-- the interface rolls back the optimistic state, showing the
       post as not liked and reverting the like count
   |-- the user is informed the action did not succeed, so the
       reverted display is not silently confusing
```

## 8. Implementation variants

**React's `useOptimistic` hook.** A dedicated framework primitive
that manages the optimistic state directly, automatically converging
the optimistic and real state in the same render once the underlying
transition completes, with no separate render needed purely to clear
the optimistic value.

**Hand-rolled optimistic state with manual rollback.** A team
implementing the same idea without a dedicated primitive, tracking a
separate piece of optimistic state alongside the confirmed state, and
writing the rollback logic explicitly for the failure case.

**Optimistic mutations in a data-fetching library.** A caching and
data-fetching library's built-in support for declaring an expected
result before a mutation resolves, automatically reconciling the
cache with the real server response once it arrives.

**Optimistic updates combined with a queue for offline support.** A
variant where the optimistic state is applied immediately even while
offline, with the real action queued and sent once connectivity
returns, extending the pattern's immediate-feedback benefit to a
genuinely disconnected state.

## 9. Known production uses

**React's own documentation, defining and explaining the `useOptimistic`
hook.** React's documentation states the core purpose directly.
"`useOptimistic` is a React Hook that lets you optimistically update
the UI." It explains why the predicted state is called optimistic in
its own words. "This state is called the optimistic because it is
used to immediately present the user with the result of performing an
Action, even though the Action actually takes time to complete." React
documentation, "useOptimistic,"
https://react.dev/reference/react/useOptimistic, verified 2026-08-21.

**React's own documentation, on how the optimistic and real state
converge.** The documentation describes the convergence behavior
plainly, noting that when the underlying transition completes, "there
is no extra render to clear the optimistic state," since "the
optimistic and real state converge in the same render when the
Transition completes." React documentation, "useOptimistic,"
https://react.dev/reference/react/useOptimistic, verified 2026-08-21.

## 10. Consequences

Positive.

- The interface reflects the user's action the instant they take it,
  making the experience feel immediate regardless of actual network
  latency, directly addressing the perceived-responsiveness force
  named in dimension 3.
- Framework-level support, such as React's `useOptimistic` hook,
  converges the optimistic and confirmed state in the same render
  once the underlying action completes, avoiding an extra visible
  render purely to clear the prediction.
- The pattern works well specifically for the common case, an action
  expected to succeed the large majority of the time, giving the
  overwhelming majority of interactions a genuinely faster feel.

Negative.

- An interface using Optimistic UI must track both the optimistic and
  the confirmed state, a real amount of additional state complexity a
  purely request-then-render interface would not need.
- When the underlying action fails, the interface must roll back and
  inform the user gracefully, and a poorly built rollback path leaves
  the user confused about what actually happened to their action.
- An action whose outcome cannot be reliably predicted, or whose
  failure carries a real cost if shown incorrectly even briefly, is
  poorly suited to the pattern, since the whole benefit depends on the
  prediction usually being correct.

## 11. Failure modes and misuse

**Applying Optimistic UI to an action with a real chance of
failing, without a genuine, tested rollback path.** Symptom. When the
action fails, the interface either stays stuck showing the incorrect
optimistic state, or reverts with no explanation, leaving the user
confused about whether their action actually happened. Cause. Adopting
the immediate-feedback benefit of the pattern without building and
testing the rollback and user-notification path for the failure case.
Fix. Before applying Optimistic UI to an action, build and test the
specific rollback behavior for when that action fails, including how
the user is informed.

**Optimistically predicting a result the server is actually likely to
change, such as a computed value the server recalculates
differently.** Symptom. The optimistic state frequently disagrees
with the real, confirmed result once it arrives, causing a visible
flicker or correction on nearly every action, defeating the
perceived-smoothness benefit the pattern exists to provide. Cause.
Choosing to optimistically predict a value the server does not
actually echo back unchanged the large majority of the time. Fix.
Reserve Optimistic UI for actions whose result is genuinely
predictable from the client's own input, and let the server compute
and own any value the client cannot reliably predict.

**Losing track of which pieces of interface state are optimistic and
which are confirmed, letting a stale optimistic prediction leak into
a later, unrelated render.** Symptom. A prediction from an earlier
action is still visible after a later, unrelated action has already
changed the real state, since the optimistic and confirmed state were
not correctly reconciled. Cause. Managing optimistic state by hand
without a mechanism that guarantees convergence once the
corresponding action resolves. Fix. Use a framework primitive, such
as React's `useOptimistic` hook, that ties the optimistic state
directly to its corresponding transition and guarantees convergence,
or, if managing it by hand, be rigorous about clearing the optimistic
value the moment its corresponding action resolves, one way or the
other.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Optimistic UI | Request-then-render (wait for confirmation) | A loading spinner during the request | State Machine UI |
|---|---|---|---|---|
| Perceived responsiveness | Strong, immediate | Weak, a visible wait before any feedback | Moderate, feedback is immediate but not the result itself | Not directly applicable, a different concern |
| Correctness when the action fails | Needs a genuine rollback path | Strong, nothing shown until confirmed | Strong, nothing incorrect is shown | Not directly applicable |
| Interface state complexity | Real, tracks optimistic and confirmed state | Low, only the confirmed state exists | Low, only a boolean loading flag | Not directly applicable |
| Fit for an action with unpredictable outcome | Weak, the prediction is often wrong | Strong | Strong | Not directly applicable |
| Fit for a high-confidence, frequent action | Strong | Weak, unnecessary wait for a likely-successful action | Moderate, better than nothing but still a wait | Not directly applicable |

Reading of the table. Optimistic UI wins specifically for a frequent,
high-confidence action whose result the client can predict reliably,
where perceived responsiveness genuinely matters and a real rollback
path can be built. An action whose outcome is genuinely uncertain, or
whose incorrect display carries real cost, is better served by
waiting for confirmation, with or without a loading indicator.

## 13. Related and incompatible patterns

- **Hooks.** The mechanism, such as React's `useOptimistic`, that most
  modern implementations of the pattern are built directly on top of.
- **State Machine UI.** A complementary approach for modeling the
  overall interaction states, idle, pending, succeeded, failed, that
  an Optimistic UI implementation's rollback and reconciliation logic
  can be structured around.
- **Redux.** A state-management pattern that can hold both the
  optimistic and confirmed state explicitly as separate pieces of a
  centralized store, an alternative to a framework-level primitive
  for teams already using Redux as their primary state layer.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a frequent, high-confidence user action that
currently waits for server confirmation before showing any visible
change.

1. Confirm the action is expected to succeed the large majority of
   the time, and that its result can genuinely be predicted from the
   client's own input.
2. Identify the specific piece of interface state that should update
   immediately, and separate it conceptually from the confirmed state
   the server will eventually return.
3. Apply the optimistic update immediately when the user acts, using
   a framework primitive such as `useOptimistic` where available, or a
   hand-rolled optimistic state alongside the confirmed state.
4. Build and test the rollback path explicitly, confirming the
   interface correctly reverts to the prior confirmed state and
   informs the user when the underlying action fails.
5. Verify the optimistic and confirmed state converge correctly on
   success, with no stale prediction left visible after the real
   result arrives.

Removing the pattern when it stops earning its place, most relevant
when the underlying action's failure rate has grown high enough that
the rollback experience is now common rather than rare.

1. Confirm the action's actual failure rate has genuinely grown high
   enough to undermine the pattern's value, rather than assuming so
   without review.
2. Revert the interaction to a request-then-render model, showing a
   loading indicator while the action is pending rather than a
   predicted result.
3. Remove the optimistic state tracking and its rollback logic once
   the migration to the simpler model is complete.

## 15. Testing and verification

Easier because of the pattern.

- The optimistic update itself, the interface's immediate response to
  a user action, can be tested directly and synchronously, with no
  need to wait for or mock an asynchronous request to verify the
  interface reacted correctly.
- Because the pattern requires an explicit rollback path, that path
  becomes a first-class, directly testable piece of behavior, rather
  than an implicit, easy-to-overlook edge case in a request-then-render
  interface.

Harder because of the pattern.

- Testing the full convergence behavior, that the optimistic and
  confirmed state correctly reconcile once the real action resolves,
  needs simulating both the immediate optimistic render and the later
  asynchronous resolution together.
- Testing the rollback path specifically needs simulating the
  underlying action's failure, which is an easy case to under-test
  compared to the success path a team naturally exercises more often
  during normal development.

Techniques that apply.

- **Immediate-render tests.** Trigger the user action and assert the
  optimistic state renders correctly, without waiting for or resolving
  the underlying asynchronous request.
- **Success-convergence tests.** Resolve the underlying request
  successfully and assert the optimistic and confirmed state converge
  correctly, with no stale prediction left visible.
- **Failure-rollback tests.** Reject the underlying request and assert
  the interface correctly rolls back to the prior confirmed state and
  informs the user, the specific case most likely to be under-tested.
- **Rapid-repeated-action tests.** Trigger the action multiple times
  in quick succession and assert each optimistic update and its
  eventual convergence or rollback is handled correctly, catching a
  race condition a single-action test would miss.

## 16. Observability signals

Optimistic UI has a genuine runtime footprint, since it directly
governs what a real user sees before an action is actually confirmed,
so a dedicated production signal is honest here.

What to record.

- The rollback rate, how often an optimistically predicted action
  ultimately fails and needs to be reverted, since a rollback rate
  that is not genuinely rare undermines the pattern's core assumption
  and signals either an unreliable underlying action or an
  inappropriate application of the pattern.
- The time between the optimistic update and the real, confirmed
  result actually arriving, since a growing gap signals the
  underlying request is slow enough that the user may notice a
  correction even when the prediction is ultimately right.

A healthy state. The rollback rate stays low and the gap between the
optimistic update and the real confirmation stays short enough that
users rarely, if ever, notice a visible correction.

A failing state. A rollback rate that is not genuinely rare, pointing
at an unreliable underlying action or a pattern applied where the
outcome is not actually predictable, or a growing gap between the
optimistic update and the real confirmation, pointing at a slow
underlying request that undermines the perceived-responsiveness
benefit the pattern exists to provide.

## 17. Security and privacy implications

Optimistic UI carries a real implication, since the interface
displays a predicted result before the server has actually confirmed
or authorized the underlying action.

**An optimistic update must never be treated as if it were a genuine
authorization or a confirmed state change, since the interface's
prediction is purely a client-side guess and the server's own
validation and authorization remain the actual source of truth for
whether the action is genuinely permitted and genuinely happened.**
Because a user could, in principle, observe an optimistic state that
implies an action succeeded before the server has actually validated
or authorized it, any code that depends on the action having actually
happened, granting access, decrementing a limited resource, recording
a payment, must key off the server's real, confirmed response, never
off the client's optimistic prediction, which exists purely to
improve perceived responsiveness and carries no authority of its own.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the optimistic update,
the pending action, and the rollback the way React's own
`useOptimistic` hook structures the concept, kept free of JSX and any
specific framework's package so the sample compiles as plain
TypeScript. Python shows the same conceptual split using a minimal,
framework-agnostic optimistic-state manager with an explicit rollback
function, since Python has no single dominant Optimistic UI framework
the way TypeScript has React. Swift shows the pattern using a
minimal, analogous model where a predicted state is applied
immediately and reconciled or rolled back once an asynchronous result
resolves, closely analogous to how optimistic updates are reasoned
about in a native app's view model. Java, Go, and Rust are omitted,
since none has a dominant, idiomatic UI-component framework this
specifically frontend interaction pattern maps to as directly as
TypeScript and Swift do.

### TypeScript

```typescript
interface LikeState {
  liked: boolean;
  count: number;
}

async function sendLikeRequest(postId: string): Promise<boolean> {
  console.log("sending like request for", postId);
  return true;
}

class OptimisticLikeController {
  private confirmedState: LikeState;
  private optimisticState: LikeState;

  constructor(initial: LikeState) {
    this.confirmedState = initial;
    this.optimisticState = initial;
  }

  getDisplayState(): LikeState {
    return this.optimisticState;
  }

  async like(postId: string): Promise<void> {
    this.optimisticState = { liked: true, count: this.confirmedState.count + 1 };

    const succeeded = await sendLikeRequest(postId);

    if (succeeded) {
      this.confirmedState = this.optimisticState;
    } else {
      this.optimisticState = this.confirmedState;
    }
  }
}

const controller = new OptimisticLikeController({ liked: false, count: 10 });
controller.like("post-1").then(() => {
  console.log("final state:", controller.getDisplayState());
});
console.log("immediate state:", controller.getDisplayState());
```

### Python

```python
import asyncio
from dataclasses import dataclass, replace


@dataclass
class LikeState:
    liked: bool
    count: int


async def send_like_request(post_id: str) -> bool:
    print(f"sending like request for {post_id}")
    return True


class OptimisticLikeController:
    def __init__(self, initial: LikeState) -> None:
        self.confirmed_state = initial
        self.optimistic_state = initial

    def get_display_state(self) -> LikeState:
        return self.optimistic_state

    async def like(self, post_id: str) -> None:
        self.optimistic_state = replace(
            self.confirmed_state, liked=True, count=self.confirmed_state.count + 1
        )

        succeeded = await send_like_request(post_id)

        if succeeded:
            self.confirmed_state = self.optimistic_state
        else:
            self.optimistic_state = self.confirmed_state


async def main() -> None:
    controller = OptimisticLikeController(LikeState(liked=False, count=10))
    print("immediate state:", controller.get_display_state())
    await controller.like("post-1")
    print("final state:", controller.get_display_state())


if __name__ == "__main__":
    asyncio.run(main())
```

### Swift

```swift
struct LikeState {
    var liked: Bool
    var count: Int
}

func sendLikeRequest(postId: String) async -> Bool {
    print("sending like request for " + postId)
    return true
}

final class OptimisticLikeController {
    private var confirmedState: LikeState
    private var optimisticState: LikeState

    init(initial: LikeState) {
        confirmedState = initial
        optimisticState = initial
    }

    func getDisplayState() -> LikeState {
        optimisticState
    }

    func like(postId: String) async {
        optimisticState = LikeState(liked: true, count: confirmedState.count + 1)

        let succeeded = await sendLikeRequest(postId: postId)

        if succeeded {
            confirmedState = optimisticState
        } else {
            optimisticState = confirmedState
        }
    }
}

let controller = OptimisticLikeController(initial: LikeState(liked: false, count: 10))
print("immediate state: " + String(describing: controller.getDisplayState()))

Task {
    await controller.like(postId: "post-1")
    print("final state: " + String(describing: controller.getDisplayState()))
}
```

## 18. References

1. React documentation. "useOptimistic".
   https://react.dev/reference/react/useOptimistic
   Verified 2026-08-21. Source of the defining sentence and the
   convergence-behavior explanation quoted in dimensions 1 and 9.
