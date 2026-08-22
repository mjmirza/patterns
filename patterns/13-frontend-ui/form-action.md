---
name: Form Action
slug: form-action
family: 13-frontend-ui
category: Composition
aliases: [Action Prop, useActionState, Progressive Form Enhancement]
first_described: "React documentation, form action prop"
maturity: established
related: [server-action, reducer-hook]
incompatible_with: []
verified: 2026-08-21
---

# Form Action

## 1. Name, aliases, and lineage

The canonical name is Form Action, the pattern where a form's own
submission mechanism is wired to a function, rather than to a raw
HTTP request assembled by hand. React's own documentation states the
mechanism directly. "When a function is passed to `action` the
function will handle the form submission in a Transition following
the Action prop pattern. The function passed to `action` may be
async and will be called with a single argument containing the form
data of the submitted form."

The alias **Action Prop** names the specific `action` attribute the
pattern is built around. **useActionState** names the companion hook
most commonly paired with a form action to track its pending state
and its last returned result. **Progressive Form Enhancement** names
the pattern by its most valuable real property, a form built this way
can still work before an application's own JavaScript has loaded, or
without it loading at all.

## 2. Problem and context

A form submitted the traditional way moves the browser to a new
URL and reloads the whole page, while a form submitted through raw
client-side JavaScript needs the developer to manually intercept the
submit event, read every field out of it, build and send the request
by hand, and manage the pending and error state of that request
themselves. A Form Action solves this by letting the form's own
`action` attribute be given a function directly, a function React's
own documentation states is "called with a single argument containing
the form data of the submitted form," so the framework itself handles
gathering the submitted fields, running the function as a proper
transition, and, when paired with the companion state hook, tracking
whether that function is still running and what it most recently
returned, without the developer wiring any of that plumbing by hand.

## 3. Forces

The pattern balances the following competing pressures.

- **Simplicity of the submission wiring.** Favored. The form's own
  `action` attribute becomes the single place the submission logic
  lives, rather than a separate submit-event handler that has to read
  form fields out of the DOM by hand.
- **Progressive enhancement.** Favored, specifically when the action
  given is a Server Function. React's own documentation states this
  directly. "Passing a Server Function to `<form action>` allow users
  to submit forms without JavaScript enabled or before the code has
  loaded, similar to the way forms work when a URL is passed to the
  `action` prop."
- **Built-in pending and result tracking.** Favored, when paired with
  the companion state hook, whose own documentation states its return
  shape directly. "The current state," "a `dispatchAction` function,"
  and "the `isPending` flag that tells you if any dispatched Actions
  for this Hook are pending," giving a form's loading and result state
  for free rather than as hand-rolled component state.
- **Fine-grained control over the submission event itself.** Sacrificed.
  React's own documentation notes plainly that a Server Function is
  something "`onSubmit` does not support," so a case genuinely needing
  to intercept and inspect the raw submit event before deciding
  whether to proceed does not fit this pattern as directly.

## 4. Applicability and non-applicability

Reach for a Form Action when the following hold.

- The form's submission logic is genuinely well modeled as "call this
  one function with the submitted fields," rather than a sequence of
  steps that needs to inspect or cancel the raw submit event itself.
- The form would genuinely benefit from working before the
  application's own JavaScript has loaded, or without it loading at
  all, which the pattern provides for free when the function given is
  a Server Function.
- The pending and last-result state the companion state hook tracks
  is the actual shape of state the form's UI needs, rather than a more
  complex, multi-field validation state the form independently manages.

Do NOT reach for a Form Action in these cases, and the reason matters
more than the rule.

- **The form genuinely needs to inspect or conditionally cancel the raw
  submit event before deciding whether to proceed**, a case the
  pattern's own documentation states plainly a Server Function does not
  support, so a traditional submit-event handler remains the more
  direct fit.
- **The form's real state need is complex, multi-step client validation
  the companion state hook's simple pending-and-last-result shape does
  not model well**, forcing the state hook's shape onto a genuinely
  more complex form adds friction rather than removing it.
- **The submission has no realistic case for working without the
  application's JavaScript already loaded**, an internal admin tool
  behind an authenticated session that is never reached before the
  application has fully loaded gains little from the progressive
  enhancement the pattern's Server Function variant specifically
  provides.

## 5. Structure

A Form Action has three structural parts.

- **The form element itself**, whose `action` attribute is given a
  function directly rather than a URL string.
- **The action function**, which receives the submitted form's data as
  its single argument, and may itself be a plain client-side function
  or, when built for progressive enhancement, a Server Function.
- **The companion state hook**, used inside the component to track the
  three values its own documentation defines, the current state, a
  dispatch function to call inside the action, and the pending flag.

## 6. ASCII structure diagram

```
  +--------------------------------------------------------------+
  |  <form action={submitAction}>                                  |
  |                                                                |
  |    submitted FormData is passed into submitAction as its       |
  |    single argument                                             |
  |                                                                |
  |    +---------------------------------------------------+       |
  |    | useActionState(submitAction, initialState)             |       |
  |    |   returns [state, dispatchAction, isPending]           |       |
  |    +---------------------------------------------------+       |
  |                                                                |
  |    while isPending is true, show a loading indicator           |
  |    once resolved, state reflects the action's own return       |
  |  </form>                                                        |
  +--------------------------------------------------------------+
```

## 7. Dynamics

The trace below shows a user submitting a form wired this way.

```
User submits the form

the user fills the form's fields and submits it
   |-- React gathers the submitted fields into a FormData object
   |-- the action function is called with that FormData as its single
       argument, inside a transition

While the action runs

isPending, from the companion state hook, becomes true
   |-- the form's UI can show a loading indicator or disable
       resubmission while the action is still running

The action completes

the action function returns its result
   |-- the companion state hook's tracked state updates to match
       that returned value
   |-- isPending becomes false again, and the form's UI reflects the
       action's actual outcome
```

## 8. Implementation variants

**Client-only action function.** A plain, local async function passed
directly to the form's `action` attribute, running entirely on the
client, no different in principle from a manually wired submit
handler, but with the form-data gathering and pending tracking handled
by the framework.

**Server Function as the action.** The function given to the form's
`action` attribute is itself a Server Function, giving the form the
progressive enhancement React's own documentation names directly, a
submission that works "without JavaScript enabled or before the code
has loaded."

**Action paired with the companion state hook.** The action function is
wrapped by the state hook so the form's component can read its
current state, dispatch it, and read its pending flag directly, rather
than the component managing that state by hand.

## 9. Known production uses

**React's own documentation, defining the mechanism.** React states
the core behavior directly. "When a function is passed to `action`
the function will handle the form submission in a Transition
following the Action prop pattern," and separately clarifies the
progressive-enhancement case for a Server Function given to the
attribute. "Passing a Server Function to `<form action>` allow users
to submit forms without JavaScript enabled or before the code has
loaded." React, "`<form>`,"
https://react.dev/reference/react-dom/components/form, verified
2026-08-21.

**React's own documentation, on the companion state hook.** React
defines the hook's return shape directly. "The current state," "a
`dispatchAction` function that you call inside Actions," and "the
`isPending` flag that tells you if any dispatched Actions for this
Hook are pending." React, "useActionState,"
https://react.dev/reference/react/useActionState, verified 2026-08-21.

## 10. Consequences

Positive.

- The form's own submission logic lives in one function, tied to the
  form element itself, rather than in a separately wired submit-event
  handler that manually reads fields out of the DOM.
- When the action given is a Server Function, the form gains real
  progressive enhancement, working before the application's own
  JavaScript has loaded, or without it loading at all.
- The pending and last-result state most forms actually need is
  tracked by the companion state hook directly, removing the need to
  hand-roll that state as separate component state.

Negative.

- A case genuinely needing to inspect or conditionally cancel the raw
  submit event before deciding whether to proceed does not fit the
  pattern directly, since a Server Function specifically does not
  support that.
- A form with genuinely complex, multi-step client validation may find
  the companion state hook's simple pending-and-last-result shape does
  not model its real state need well.
- Debugging what a form action actually did is a step removed from
  reading a plain submit-event handler's code directly, since the
  gathering of fields into FormData and the transition wrapping are
  handled by the framework rather than written out explicitly.

## 11. Failure modes and misuse

**Treating a Form Action as identical to a Server Action, and
conflating their responsibilities.** Symptom. A team assumes wiring a
form's `action` attribute automatically gives it the network-boundary
security properties a Server Function marked `'use server'`
specifically carries, when the action given was actually a plain
client function. Cause. Confusing the general form-action mechanism,
which can accept either a client function or a Server Function, with
the specific security and network semantics that only apply when the
function given genuinely is a Server Function. Fix. Be explicit about
which kind of function a given form's action attribute is wired to,
and treat the network-boundary security properties as belonging
specifically to a genuine Server Function, never assumed from the
form-action mechanism alone.

**Ignoring the pending state the companion hook already provides, and
allowing duplicate form submissions.** Symptom. A user, uncertain
whether their first click registered, clicks the submit button again
before the first submission has resolved, creating a duplicate
submission. Cause. Not disabling the submit control, or not showing a
clear loading indicator, while the tracked pending flag is true. Fix.
Use the companion state hook's pending flag to disable the submit
control, or otherwise make it visually clear a submission is already
in progress, for as long as that flag remains true.

**Building a form-action function whose signature does not actually
match what the form supplies.** Symptom. The action function throws,
or silently receives unexpected data, because it was written expecting
a different argument shape than the FormData object the form actually
passes it. Cause. Writing the action function against an assumed
argument shape rather than the documented one, a single FormData
argument containing the submitted fields. Fix. Write the action
function to accept the documented FormData argument directly, reading
the submitted fields out of it rather than assuming a different,
pre-parsed shape.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Form Action | Manual submit-event handler | Native HTML form with a URL action |
|---|---|---|---|
| Simplicity of the submission wiring | Strong, the framework gathers fields and manages the transition | Moderate, the developer reads fields and manages state by hand | Strong for the wiring itself, but offers no way to run application logic before moving to a new page |
| Progressive enhancement | Strong, specifically when the action is a Server Function | Weak, entirely dependent on JavaScript having loaded | Strong, works with no JavaScript at all, but cannot run application logic client-side first |
| Built-in pending and result tracking | Strong, provided directly by the companion state hook | Weak, must be hand-rolled as separate component state | Not applicable, the browser's own navigation replaces any in-page state |
| Fine-grained control over the raw submit event | Weak, a Server Function specifically does not support this | Strong, the developer has full control of the event | Weak, the browser's own default submission behavior applies |

Reading of the table. A Form Action wins specifically when the
submission is well modeled as calling one function with the submitted
fields, and progressive enhancement is a genuine, valued property. A
manual submit-event handler remains the right choice when a case
genuinely needs to inspect or cancel the raw submit event itself
before proceeding.

## 13. Related and incompatible patterns

- **Server Action.** A Form Action given a genuine Server Function is
  the specific combination that gains both the form-wiring benefits
  of this pattern and the network-boundary security properties a
  Server Function carries. The two patterns compose directly, but are
  not the same thing, a Form Action is the broader mechanism, a Server
  Action is a specific kind of function that mechanism can accept.
- **Reducer Hook.** The companion state hook's own current-state,
  dispatch-function, and pending-flag shape closely mirrors a reducer
  hook's own state-and-dispatch pattern, applied specifically to the
  lifecycle of an action.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to a form currently wired to a manual
submit-event handler.

1. Confirm the form's submission logic is genuinely well modeled as
   calling one function with the submitted fields, rather than a
   sequence of steps needing to inspect or cancel the raw submit event.
2. Write the action function to accept the documented single FormData
   argument, reading the submitted fields out of it.
3. Wire that function directly to the form's `action` attribute,
   removing the separate submit-event handler.
4. Add the companion state hook to track the action's current state,
   its dispatch function, and its pending flag, wiring the form's UI
   to reflect that pending flag while the action is running.
5. If progressive enhancement is a genuine goal, confirm the action
   function given is actually a Server Function, rather than a plain
   client-only function.

Removing the pattern when it stops earning its place, most relevant
when a form's real submission logic has grown to genuinely need
fine-grained control over the raw submit event the pattern does not
support.

1. Confirm, concretely, which part of the raw submit event the form's
   logic now genuinely needs to inspect or cancel, rather than
   assuming the pattern no longer fits without checking.
2. Replace the form action with a manual submit-event handler that
   reads the needed fields directly, restoring full control of the
   event.
3. Reintroduce the pending and result state the companion hook
   previously tracked as explicit component state, so the form's
   loading and result UI keeps working after the removal.

## 15. Testing and verification

Easier because of the pattern.

- A test can call the action function directly with a constructed
  FormData object and assert its return value, verifying the form's
  actual submission logic independent of the DOM or any simulated
  click and submit sequence.
- Because the companion state hook exposes a plain pending flag, a
  test asserting a loading indicator is shown during submission does
  not need to intercept a raw network request to do so.

Harder because of the pattern.

- Verifying the progressive-enhancement property, that the form
  genuinely still works before the application's JavaScript has
  loaded, needs a test environment that can simulate that condition
  directly, a category of test easy to omit if only the
  JavaScript-loaded case is tested.
- Confirming the action function's argument really is the documented
  FormData shape, rather than an assumed, differently structured one,
  needs a deliberate check against the real, framework-supplied
  argument rather than a hand-constructed mock.

Techniques that apply.

- **Direct action-function unit tests.** Call the action function with
  a constructed FormData object and assert its return value and any
  side effects, independent of the surrounding form and DOM.
- **Pending-state UI tests.** Assert the form's loading indicator, or
  disabled submit control, correctly reflects the companion state
  hook's pending flag while the action is running.
- **Progressive-enhancement tests.** Where the action given is a
  Server Function, verify the form still functions correctly in an
  environment simulating no client-side JavaScript having loaded.
- **Duplicate-submission tests.** Assert that submitting the form a
  second time while the first submission's action is still pending
  does not produce a duplicate side effect.

## 16. Observability signals

What to record.

- Submission failure rate, the share of form-action invocations whose
  returned state indicates an error, since a rising failure rate
  points at a real problem with either the submitted data's validity
  or the action function's own handling of it.
- Time spent pending, the duration between an action's dispatch and
  its resolution, since a form whose pending state lingers unusually
  long degrades the very UX benefit the companion state hook exists to
  provide.

A healthy state. The overwhelming majority of form-action invocations
resolve quickly and successfully, and the pending state a user
actually experiences stays short enough that the loading indicator
reads as brief feedback rather than a stall.

A failing state. A rising share of form-action invocations resolve to
an error state, pointing at a validation or handling problem, or the
time spent pending grows long enough that the form's loading state
begins to read as broken or unresponsive rather than working as
intended.

## 17. Security and privacy implications

**When the function given to a form's `action` attribute is a genuine
Server Function, the same reachable-from-anywhere security posture a
Server Action carries applies here directly, and the form-action
wiring itself does not add or remove any of that responsibility.** A
Server Function reachable through a form's action is reachable the
same way any other Server Function is, and must independently validate
and authorize every submission it receives, exactly as it would if
invoked outside a form entirely, never trusting that arriving through
a form's own submission implies the request came from that form or
from an authorized user.

**A form-action function that trusts the shape or contents of the
submitted FormData without validating it is a genuine input-validation
gap**, since a submitted form's fields are, exactly like any other
network input, fully controllable by the party submitting the request,
and the action function must validate the submitted data itself rather
than assuming it matches whatever shape the form's own client-side
markup happened to define.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the form action and its
companion state tracking directly, kept free of JSX and any specific
package's imports so the sample compiles as plain TypeScript. Python
shows the conceptual shape of the same action-function-with-tracked-
state logic, since Python has no browser-facing form-action mechanism
of its own but the same "call one function with the submitted fields,
track its pending and result state" shape is a genuinely portable one.
Swift shows the same conceptual shape using a minimal model, analogous
to how a native app's own form-submission handler might track a
submission's pending state and last result. Java, Go, and Rust are
omitted, since none has a dominant, idiomatic browser-facing
form-submission model this specific composition pattern maps to as
directly as TypeScript does.

### TypeScript

```typescript
interface SubmissionResult {
  ok: boolean;
  message: string;
}

type ActionState = {
  result: SubmissionResult | null;
  pending: boolean;
};

async function submitAction(formData: Map<string, string>): Promise<SubmissionResult> {
  const email = formData.get("email");
  if (!email || !email.includes("@")) {
    return { ok: false, message: "A valid email is required." };
  }
  return { ok: true, message: "Submission accepted." };
}

async function dispatchAction(
  state: ActionState,
  formData: Map<string, string>,
  runAction: (data: Map<string, string>) => Promise<SubmissionResult>,
): Promise<ActionState> {
  const pendingState: ActionState = { result: state.result, pending: true };
  const result = await runAction(formData);
  return { result, pending: false };
}

async function main(): Promise<void> {
  let state: ActionState = { result: null, pending: false };

  const validFormData = new Map([["email", "user@example.com"]]);
  state = await dispatchAction(state, validFormData, submitAction);
  console.log("valid submission:", state);

  const invalidFormData = new Map([["email", "not-an-email"]]);
  state = await dispatchAction(state, invalidFormData, submitAction);
  console.log("invalid submission:", state);
}

main();
```

### Python

```python
import asyncio
from dataclasses import dataclass


@dataclass
class SubmissionResult:
    ok: bool
    message: str


@dataclass
class ActionState:
    result: SubmissionResult | None
    pending: bool


async def submit_action(form_data: dict[str, str]) -> SubmissionResult:
    email = form_data.get("email")
    if not email or "@" not in email:
        return SubmissionResult(ok=False, message="A valid email is required.")
    return SubmissionResult(ok=True, message="Submission accepted.")


async def dispatch_action(
    form_data: dict[str, str],
    run_action,
) -> ActionState:
    result = await run_action(form_data)
    return ActionState(result=result, pending=False)


async def main() -> None:
    valid_form_data = {"email": "user@example.com"}
    valid_state = await dispatch_action(valid_form_data, submit_action)
    print("valid submission:", valid_state)

    invalid_form_data = {"email": "not-an-email"}
    invalid_state = await dispatch_action(invalid_form_data, submit_action)
    print("invalid submission:", invalid_state)


if __name__ == "__main__":
    asyncio.run(main())
```

### Swift

```swift
struct SubmissionResult {
    let ok: Bool
    let message: String
}

struct ActionState {
    let result: SubmissionResult?
    let pending: Bool
}

func submitAction(formData: [String: String]) async -> SubmissionResult {
    guard let email = formData["email"], email.contains("@") else {
        return SubmissionResult(ok: false, message: "A valid email is required.")
    }
    return SubmissionResult(ok: true, message: "Submission accepted.")
}

func dispatchAction(
    formData: [String: String],
    runAction: ([String: String]) async -> SubmissionResult
) async -> ActionState {
    let result = await runAction(formData)
    return ActionState(result: result, pending: false)
}

func run() async {
    let validFormData = ["email": "user@example.com"]
    let validState = await dispatchAction(formData: validFormData, runAction: submitAction)
    print("valid submission: " + (validState.result?.message ?? "no result"))

    let invalidFormData = ["email": "not-an-email"]
    let invalidState = await dispatchAction(formData: invalidFormData, runAction: submitAction)
    print("invalid submission: " + (invalidState.result?.message ?? "no result"))
}

await run()
```

## 18. References

1. React. "`<form>`".
   https://react.dev/reference/react-dom/components/form
   Verified 2026-08-21. Source of the defining and progressive-
   enhancement quotes used in dimensions 1, 2, 3, and 9.
2. React. "useActionState".
   https://react.dev/reference/react/useActionState
   Verified 2026-08-21. Source of the companion state hook's return-
   shape quotes used in dimensions 3, 5, and 9.
