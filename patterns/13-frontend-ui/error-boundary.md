---
name: Error Boundary
slug: error-boundary
family: 13-frontend-ui
category: Error Handling
aliases: [componentDidCatch, getDerivedStateFromError]
first_described: "React documentation, Error Boundaries"
maturity: canonical
related: [skeleton-and-suspense, optimistic-ui]
incompatible_with: []
verified: 2026-08-21
---

# Error Boundary

## 1. Name, aliases, and lineage

The canonical name is Error Boundary, a component that catches a
rendering error thrown anywhere in its child component tree and
displays a fallback UI instead of letting the error crash the entire
application. React's own documentation states the definition
directly. "An Error Boundary is a special component that lets you
display some fallback UI instead of the part that crashed, for
example, an error message."

The alias **componentDidCatch** names the specific class-component
lifecycle method most implementations use to log the caught error.
**getDerivedStateFromError** names the companion lifecycle method
used to update the component's own state so the fallback UI renders
in response to the error, together the two methods React's own
documentation identifies as the mechanism behind an Error Boundary.

## 2. Problem and context

React's own documentation states the default behavior a rendering
error causes plainly. "By default, if your application throws an
error during rendering, React will remove its UI from the screen."
Without an Error Boundary, a single component failing to render, from
a bug, an unexpected data shape, or any other rendering-time error,
takes down the entire surrounding application rather than only the
part that actually failed. This is a harsh, all-or-nothing outcome
for what is often a localized problem. Error Boundary solves this by
letting a developer wrap a specific part of the UI so a rendering
error inside that part is caught there, showing a fallback for only
that part, while the rest of the application, everything outside the
boundary, keeps working normally.

## 3. Forces

The pattern balances the following competing pressures.

- **Containing failure to a specific part of the UI.** Favored.
  Wrapping a part of the UI in an Error Boundary means a rendering
  error inside it results in a fallback for that specific part rather
  than the entire application disappearing.
- **A working fallback experience rather than a blank screen.**
  Favored. React's own documentation states the direct alternative to
  the default behavior. "To prevent this, you can wrap a part of your
  UI into an Error Boundary," which renders a fallback the developer
  controls rather than an empty page.
- **Coverage across every kind of error.** Sacrificed, and important
  to be precise about. React's own documentation states plainly that
  error boundaries "do not catch errors for event handlers,
  asynchronous code, server side rendering, errors thrown in the
  error boundary itself," a narrower coverage than a developer might
  assume from the name alone.
- **Boilerplate per boundary.** Sacrificed. Each Error Boundary needs
  its own class component implementing the two lifecycle methods, or
  an equivalent wrapper, real code to write and maintain for each
  boundary a developer introduces.

## 4. Applicability and non-applicability

Reach for an Error Boundary when the following hold.

- A specific, identifiable part of the UI, a widget, a section, a
  route, could genuinely fail to render, and the rest of the
  application should keep working if it does.
- The failure is genuinely a rendering-time error, the specific case
  React's own documentation states error boundaries actually catch.
- A real fallback experience, an error message, a retry option,
  can genuinely be shown for that specific part when it fails, rather
  than the fallback itself being equally unhelpful as no fallback at
  all.

Do NOT reach for an Error Boundary in these cases, and the reason
matters more than the rule.

- **The error genuinely occurs in an event handler, asynchronous
  code, or server-side rendering**, React's own documentation states
  directly that an Error Boundary does not catch these, so relying on
  one for these cases leaves the actual error unhandled, needing a
  different mechanism, a try-catch inside the handler itself, or an
  equivalent asynchronous error-handling approach.
- **The error boundary's own render method is where the error would
  occur**, React's own documentation notes an error boundary does not
  catch an error thrown in the boundary itself, so the boundary's own
  fallback rendering logic must stay simple and reliable, since
  nothing catches a failure inside it.
- **There is no real fallback to show for the wrapped part**, if
  a failure in this specific part would make the rest of the page
  meaningless anyway, isolating it with its own boundary may add
  complexity without a genuinely useful containment benefit.

## 5. Structure

An Error Boundary has three structural parts.

- **The boundary component**, implementing `static
  getDerivedStateFromError` to update its own state in response to a
  caught error, and `componentDidCatch` to perform side effects such
  as logging.
- **The wrapped children**, the specific part of the UI whose
  rendering errors the boundary catches.
- **The fallback UI**, rendered by the boundary instead of its
  children once an error has been caught.

## 6. ASCII structure diagram

```
  +----------------------------------------------------------+
  |  ErrorBoundary (class component)                            |
  |    state.hasError = false initially                          |
  |                                                              |
  |    if hasError is false:                                     |
  |      +--------------------------------------------------+    |
  |      | children (the wrapped UI, e.g. <Profile />)          |    |
  |      +--------------------------------------------------+    |
  |                                                              |
  |    if hasError is true (an error was caught):                |
  |      +--------------------------------------------------+    |
  |      | fallback UI (e.g. "Something went wrong")            |    |
  |      +--------------------------------------------------+    |
  +----------------------------------------------------------+
```

## 7. Dynamics

The trace below shows a child component throwing a rendering error
and the boundary catching it and switching to its fallback.

```
Normal rendering

the ErrorBoundary renders its children normally
   |-- state.hasError is false
   |-- the wrapped Profile component renders successfully

A rendering error occurs

the Profile component throws an error during rendering
   |-- React catches the error, since it originated inside the
       boundary's wrapped children
   |-- getDerivedStateFromError is called, returning updated state
       marking hasError as true
   |-- componentDidCatch is called with the error and its component
       stack, letting the boundary log it to an external service

Fallback renders

the boundary re-renders, now with hasError true
   |-- instead of rendering the children again, the boundary renders
       its fallback UI
   |-- the rest of the application, outside the boundary, is
       unaffected and continues rendering normally
```

## 8. Implementation variants

**Class-component boundary with both lifecycle methods.** The
canonical implementation React's own documentation shows directly,
using `getDerivedStateFromError` for the fallback state update and
`componentDidCatch` for logging.

**Reusable, generic error boundary component.** A single Error
Boundary implementation accepts a fallback as a prop, or as a render
function, letting the same boundary component wrap many different
parts of an application with a different fallback for each.

**Nested error boundaries.** Several Error Boundaries wrap different,
nested parts of the UI, so a failure in a deeply nested section is
caught by the nearest surrounding boundary, containing the failure as
locally as possible rather than propagating up to a broader,
less-specific fallback.

**Boundary paired with a reset mechanism.** An Error Boundary tracks
a key or a reset trigger that, when changed, clears its caught-error
state and attempts to render its children again, letting a user
retry after a transient failure rather than being stuck on the
fallback permanently.

## 9. Known production uses

**React's own documentation, defining the pattern and its default
alternative.** React states the definition and the problem it solves
directly. "An Error Boundary is a special component that lets you
display some fallback UI instead of the part that crashed," addressing
the default behavior stated plainly. "By default, if your application
throws an error during rendering, React will remove its UI from the
screen. To prevent this, you can wrap a part of your UI into an Error
Boundary." React, "Component,"
https://react.dev/reference/react/Component, verified 2026-08-21.

**React's legacy documentation, on what error boundaries do not
catch.** The documentation states the limitation directly. "Error
boundaries do not catch errors for event handlers, asynchronous code,
server side rendering, errors thrown in the error boundary itself."
React, "Error Boundaries,"
https://legacy.reactjs.org/docs/error-boundaries.html, verified
2026-08-21.

## 10. Consequences

Positive.

- A rendering error in a specific, wrapped part of the UI results in
  a fallback for only that part, rather than removing the entire
  application's UI from the screen, the default behavior React's own
  documentation names directly.
- `componentDidCatch` gives a boundary a dedicated place to log a
  caught error to an external service, centralizing error reporting
  for whatever part of the UI the boundary wraps.
- Nested boundaries let a failure be contained as locally as possible,
  a deeply nested section's error caught by its nearest boundary
  rather than propagating to a broader fallback than necessary.

Negative.

- Coverage is narrower than the pattern's name might suggest, event
  handlers, asynchronous code, server-side rendering, and errors
  inside the boundary itself are all explicitly uncaught, needing
  separate handling.
- Each boundary needs real, maintained code, the two lifecycle
  methods and a fallback UI, a cost that grows with the number of
  boundaries introduced.
- A fallback that gives the user no real next step, no retry, no
  clear explanation, can leave a caught error feeling equally as
  unhelpful as the crash it was meant to prevent.

## 11. Failure modes and misuse

**Assuming an Error Boundary catches an error thrown inside an event
handler, such as an onClick callback.** Symptom. The error is not
caught at all, the boundary's fallback never renders, and the error
propagates exactly as it would with no boundary present, since React's
own documentation states plainly that event handler errors are
outside an error boundary's coverage. Cause. Assuming the boundary's
coverage is broader than what React's own documentation explicitly
states. Fix. Handle an event handler's own errors with a direct
try-catch inside the handler itself, reserving the Error Boundary for
genuine rendering-time errors.

**Writing complex, error-prone logic directly inside the boundary's
own fallback rendering path.** Symptom. A failure inside the fallback
rendering itself is not caught by anything, since React's own
documentation states an error boundary does not catch an error thrown
in the boundary itself, so a broken fallback can itself crash the
surrounding UI with no further containment. Cause. Treating the
fallback UI as ordinary application code rather than recognizing it as
the one place with no safety net above it. Fix. Keep an error
boundary's own fallback rendering deliberately simple and reliable,
avoiding complex logic or data dependencies that could themselves
fail.

**Placing a single Error Boundary around the entire application with
no more granular boundaries inside it.** Symptom. Any rendering error
anywhere in the application results in the same, single, broad
fallback, containing the failure at the coarsest possible level rather
than isolating it to the specific part that actually failed. Cause.
Treating one top-level boundary as sufficient coverage, rather than
placing additional, more granular boundaries around the specific
parts of the UI where a contained, localized fallback would serve the
user better. Fix. Add nested Error Boundaries around specific,
independent sections of the UI, so a failure in one section shows a
localized fallback while the rest of the application keeps working.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Error Boundary | No boundary, default behavior | Manual try-catch per component |
|---|---|---|---|
| Containing failure to a specific part of the UI | Strong, when boundaries are placed granularly | Weak, the whole application's UI is removed | Not applicable, try-catch cannot catch a rendering error inside a component's own render |
| A working fallback rather than a blank screen | Strong | Weak, React removes the UI entirely | Not applicable, same reason |
| Coverage across every kind of error | Weak, explicitly excludes event handlers, async code, SSR, and its own render failures | Not applicable | Strong for the specific errors it is written around, but only where it is actually placed |
| Boilerplate per boundary | Moderate, two lifecycle methods and a fallback per boundary | None, no code needed | High, needs a try-catch written into every relevant spot |

Reading of the table. An Error Boundary wins specifically for
rendering-time errors in a component tree, where React's default
whole-application removal is unacceptable and a contained, localized
fallback is a real improvement. It does not replace direct error
handling for event handlers, asynchronous code, or the boundary's
own rendering logic, all of which need their own separate handling.

## 13. Related and incompatible patterns

- **Skeleton and Suspense.** A complementary technique for the loading
  state a component passes through before it either renders
  successfully or throws an error, often paired with an Error
  Boundary so a component shows a skeleton while loading and a
  fallback if it ultimately fails.
- **Optimistic UI.** A different response to a related feeling
  problem, showing a predicted successful result immediately, where
  an Error Boundary's role is to handle the case where the underlying
  operation's rendering ultimately fails rather than succeeds.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an application currently relying on React's
default whole-application removal behavior when a rendering error
occurs.

1. Identify the specific, independent parts of the UI where a
   rendering error should be contained locally rather than taking
   down the entire application.
2. Implement an Error Boundary component with `static
   getDerivedStateFromError` and `componentDidCatch`, or adopt a
   tested, reusable boundary implementation.
3. Wrap each identified part of the UI in its own boundary, with a
   fallback UI relevant to that specific part.
4. Wire `componentDidCatch` to log the caught error to whatever
   external error-reporting service the application already uses.
5. Confirm, through deliberate testing, that a rendering error inside
   each wrapped part results in that part's specific fallback, while
   the rest of the application continues working normally.

Removing the pattern when it stops earning its place, most relevant
when a specific part of the UI has become simple and reliable enough
that a dedicated boundary no longer earns its added code.

1. Confirm, through a genuine history of the wrapped part not
   actually failing, that the boundary's containment benefit is no
   longer needed, rather than assuming so without evidence.
2. Remove the specific boundary, letting that part of the UI fall
   back to whatever broader boundary, or the default behavior, would
   otherwise apply.
3. Confirm the surrounding application still behaves acceptably if
   that part were to fail again in the future.

## 15. Testing and verification

Easier because of the pattern.

- A test can deliberately render a component that throws inside a
  boundary and assert the boundary's specific fallback UI renders,
  directly verifying the containment behavior the pattern is meant to
  provide.
- Because `componentDidCatch` is a single, dedicated place errors
  reach, a test can assert that a caught error is correctly passed to
  whatever logging mechanism the boundary wires it to.

Harder because of the pattern.

- Testing an error boundary correctly needs deliberately triggering a
  rendering error inside its children, which needs test tooling aware
  of React's own error-boundary testing patterns, since a raw thrown
  error in a test environment can otherwise surface as an unhandled
  test failure rather than the intended, caught behavior.
- Confirming the boundary genuinely does NOT catch an event handler
  or asynchronous error needs a deliberate negative test, since the
  natural instinct is to test only the cases the boundary is meant to
  catch.

Techniques that apply.

- **Deliberate-throw rendering tests.** Render a component
  specifically designed to throw during rendering inside the
  boundary, asserting the fallback UI appears instead of the
  component's normal output.
- **componentDidCatch logging assertions.** Assert that a caught
  error and its component stack are correctly passed to the logging
  mechanism the boundary is wired to.
- **Negative coverage tests.** Specifically test that an error thrown
  inside an event handler or asynchronous callback within the
  boundary's children is NOT caught by the boundary, confirming the
  documented limitation holds and that error is handled by its own
  separate mechanism instead.
- **Nested boundary isolation tests.** With several nested boundaries
  in place, trigger an error at a specific nesting level and assert
  only the nearest surrounding boundary's fallback renders, while
  boundaries further out remain unaffected.

## 16. Observability signals

An Error Boundary exists specifically to catch and report a genuine
failure, so a dedicated production signal is the expected and honest
form here, not an optional addition.

What to record.

- The rate and identity of errors caught by each boundary, logged
  through `componentDidCatch`, since this is the direct signal of how
  often, and where, rendering is genuinely failing in production.
- Whether a user who hits a boundary's fallback successfully recovers,
  through a retry mechanism or a subsequent successful render, since a
  fallback that never resolves for a user points at a persistent,
  unaddressed underlying problem rather than a transient one.

A healthy state. Boundaries rarely catch an error in practice, and
when one does, the caught error and its component stack are reliably
logged, giving the team a clear signal to investigate and fix the
underlying cause.

A failing state. A specific boundary catches errors at a rate high
enough to indicate a genuine, unresolved bug in the part of the UI it
wraps, or errors are being caught but not reliably reaching the
logging mechanism, leaving the team blind to how often users are
actually hitting the fallback.

## 17. Security and privacy implications

Error Boundary is close to neutral for security, being an
error-containment technique rather than a data-handling one, and
inventing a dedicated attack surface here would be dishonest. One
practical implication is worth naming.

**Because `componentDidCatch` receives the actual error object and
its component stack, and a fallback UI is a natural place to consider
showing the error's own message to the user for debugging
convenience, a boundary that displays a raw error message directly in
its fallback risks exposing internal implementation details, stack
traces, or, in a worse case, sensitive data that happened to be
present in the error's own message, to an end user who was never
meant to see it.** A production fallback UI should show a generic,
user-appropriate message rather than the raw error, while the actual
error detail is sent through the logging mechanism inside
`componentDidCatch` to a system meant for developers to inspect,
keeping the user-facing fallback and the developer-facing error
report deliberately separate.

## 18. References

1. React. "Component".
   https://react.dev/reference/react/Component
   Verified 2026-08-21. Source of the defining pattern quote and the
   default-behavior quote used in dimensions 1, 3, and 9.
2. React (legacy docs). "Error Boundaries".
   https://legacy.reactjs.org/docs/error-boundaries.html
   Verified 2026-08-21. Source of the what-is-not-caught quote used
   in dimensions 3, 4, 9, and 11.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models an error boundary the
way React's own class-component implementation structures it, kept
free of JSX and any specific framework's package so the sample
compiles as plain TypeScript, representing the render output as a
plain string result. Python shows the conceptual shape of the same
catch-and-fallback logic using a minimal, framework-agnostic
implementation, since Python has no browser-facing component model
and therefore no single dominant error-boundary implementation the
way TypeScript has React's own Component class. Swift shows the same
conceptual shape using a minimal model, analogous to how a native
app's own view layer might catch a rendering-time failure in a
specific section and show a fallback view instead of crashing the
whole screen. Java, Go, and Rust are omitted, since none has a
dominant, idiomatic browser-facing component framework this
specifically UI-error-containment pattern maps to as directly as
TypeScript does.

### TypeScript

```typescript
interface RenderResult {
  output: string;
}

function renderChildTree(shouldThrow: boolean): RenderResult {
  if (shouldThrow) {
    throw new Error("child render failed");
  }
  return { output: "Profile rendered successfully" };
}

class ErrorBoundary {
  private hasError = false;
  private lastError: Error | null = null;

  private logError(error: Error): void {
    console.log("componentDidCatch logged:", error.message);
  }

  render(shouldThrow: boolean): RenderResult {
    if (this.hasError) {
      return { output: "Fallback: something went wrong" };
    }
    try {
      return renderChildTree(shouldThrow);
    } catch (error) {
      this.hasError = true;
      this.lastError = error as Error;
      this.logError(this.lastError);
      return { output: "Fallback: something went wrong" };
    }
  }
}

const boundary = new ErrorBoundary();
console.log(boundary.render(false).output);

const failingBoundary = new ErrorBoundary();
console.log(failingBoundary.render(true).output);
console.log(failingBoundary.render(false).output);
```

### Python

```python
from dataclasses import dataclass


@dataclass
class RenderResult:
    output: str


def render_child_tree(should_throw: bool) -> RenderResult:
    if should_throw:
        raise RuntimeError("child render failed")
    return RenderResult(output="Profile rendered successfully")


class ErrorBoundary:
    def __init__(self) -> None:
        self.has_error = False
        self.last_error: Exception | None = None

    def _log_error(self, error: Exception) -> None:
        print("componentDidCatch logged:", str(error))

    def render(self, should_throw: bool) -> RenderResult:
        if self.has_error:
            return RenderResult(output="Fallback: something went wrong")
        try:
            return render_child_tree(should_throw)
        except Exception as error:
            self.has_error = True
            self.last_error = error
            self._log_error(error)
            return RenderResult(output="Fallback: something went wrong")


if __name__ == "__main__":
    boundary = ErrorBoundary()
    print(boundary.render(False).output)

    failing_boundary = ErrorBoundary()
    print(failing_boundary.render(True).output)
    print(failing_boundary.render(False).output)
```

### Swift

```swift
struct RenderResult {
    let output: String
}

enum RenderError: Error {
    case childRenderFailed
}

func renderChildTree(shouldThrow: Bool) throws -> RenderResult {
    if shouldThrow {
        throw RenderError.childRenderFailed
    }
    return RenderResult(output: "Profile rendered successfully")
}

final class ErrorBoundary {
    private var hasError = false

    private func logError(_ error: Error) {
        print("componentDidCatch logged: " + String(describing: error))
    }

    func render(shouldThrow: Bool) -> RenderResult {
        if hasError {
            return RenderResult(output: "Fallback: something went wrong")
        }
        do {
            return try renderChildTree(shouldThrow: shouldThrow)
        } catch {
            hasError = true
            logError(error)
            return RenderResult(output: "Fallback: something went wrong")
        }
    }
}

let boundary = ErrorBoundary()
print(boundary.render(shouldThrow: false).output)

let failingBoundary = ErrorBoundary()
print(failingBoundary.render(shouldThrow: true).output)
print(failingBoundary.render(shouldThrow: false).output)
```
