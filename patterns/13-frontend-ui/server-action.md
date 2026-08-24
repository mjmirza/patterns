---
name: Server Action
slug: server-action
family: 13-frontend-ui
category: Data Fetching
aliases: [Server Function, use server]
first_described: "React documentation, Server Functions"
maturity: canonical
related: [server-components, optimistic-ui, prpl-pattern]
incompatible_with: []
verified: 2026-08-21
---

# Server Action

## 1. Name, aliases, and lineage

The canonical name is Server Action, an asynchronous function marked
to run on the server that a Client Component can call directly, most
commonly to handle a form submission or another data mutation.
React's own documentation states the underlying mechanism directly.
"Server Functions allow Client Components to call async functions
executed on the server." Next.js's own documentation narrows the
naming precisely. "A Server Function is an asynchronous function that
runs on the server," and "in an action or mutation context, they are
also called Server Actions," noting explicitly that "a Server Action
is a Server Function used in a specific way, for handling form
submissions and mutations. Server Function is the broader term."

The alias **Server Function** names the general React mechanism,
which becomes a Server Action specifically when used for a form
submission or a mutation. **use server** names the directive that
marks a function this way, the mechanism a developer actually writes
to opt a function into running on the server.

## 2. Problem and context

A traditional client-server data mutation needs a developer to
build and maintain a separate API endpoint, wire a client-side fetch
call to that endpoint, and manually keep the request and response
shapes in sync between the two, real coordination overhead for what
is conceptually a single operation, calling a function that happens
to need to run on the server. A Server Action removes that
coordination overhead by letting a developer write one async
function, mark it to run on the server with the `use server`
directive, and call it directly from client code as if it were a
local function, with React itself handling the network request and
response underneath. React's own documentation names the mechanism
directly. "React will send a request to the server to execute the
function, and return the result," collapsing the separate endpoint,
fetch call, and manual shape-syncing into one function a developer
writes and calls once.

## 3. Forces

The pattern balances the following competing pressures.

- **Reduced coordination overhead for a mutation.** Favored. A single
  async function marked `use server` replaces a separate API
  endpoint plus a client-side fetch call, removing the need to keep
  two separate pieces of code in sync for one conceptual operation.
- **Direct network exposure of the function.** Sacrificed, and
  critical to understand. Next.js's own documentation states this
  directly, as a warning. "Server Functions are reachable via direct
  POST requests, not only through your application's UI. Always
  verify authentication and authorization inside every Server
  Function."
- **Progressive enhancement for forms.** Favored, specifically for
  the form-submission case. Next.js's own documentation notes that
  "Server Components support progressive enhancement by default,
  meaning forms that call Server Actions will be submitted even if
  JavaScript hasn't loaded yet or is disabled."
- **A single, unified round trip for UI and data.** Favored. Next.js's
  own documentation states that "when an action is invoked, Next.js
  can return both the updated UI and new data in a single server
  roundtrip," rather than needing a separate request to refresh the
  UI after the mutation completes.

## 4. Applicability and non-applicability

Reach for a Server Action when the following hold.

- The operation is genuinely a mutation, a form submission, an
  update, a deletion, rather than a data-fetching read that a Server
  Component itself can already handle directly.
- Reducing the coordination overhead of a separate API endpoint plus
  a client-side fetch call is a real, felt benefit for the specific
  operation.
- The team is prepared to treat the resulting function as a genuine,
  directly reachable network endpoint, verifying authentication and
  authorization inside it exactly as Next.js's own documentation
  instructs.

Do NOT reach for a Server Action in these cases, and the reason
matters more than the rule.

- **The operation is a pure data read, not a mutation**, a Server
  Component can usually fetch that data directly during rendering,
  and reaching for a Server Action for a plain read adds a mutation-
  shaped mechanism to an operation that was never a mutation.
- **The function's authentication and authorization checks are not
  genuinely being written inside the function itself**, since Next.js's
  own documentation warns explicitly that the function is reachable
  by direct POST request independent of the application's own UI, a
  Server Action with no internal authorization check is a real
  security gap, not a theoretical one.
- **The operation genuinely needs to run many requests in true
  parallel**, Next.js's own documentation notes Server Functions are
  currently dispatched one at a time from the client, so a use case
  that genuinely needs parallel dispatch is better served by a
  dedicated data-fetching approach in a Server Component, or a route
  handler for genuinely parallel work.

## 5. Structure

A Server Action has two structural parts.

- **The server-side function**, an asynchronous function marked with
  the `use server` directive, containing the actual mutation logic
  and, critically, its own authentication and authorization checks.
- **The client-side call site**, a form's `action` prop, a button's
  `formAction` prop, or a direct call inside an event handler,
  invoking the server-side function as if it were local, with the
  underlying framework handling the network request.

## 6. ASCII structure diagram

```
  Client Component

  +----------------------------------------------------------+
  |  <form action={createPost}>                                 |
  |    <input name="title" />                                    |
  |    <button type="submit">Create</button>                     |
  |  </form>                                                     |
  +----------------------------------------------------------+
                              |
                              v
              network request, POST, dispatched
              automatically by the framework
                              |
                              v
  Server-side function, marked "use server"

  +----------------------------------------------------------+
  |  async function createPost(formData) {                       |
  |    verify authentication and authorization                    |
  |    read formData, perform the mutation                        |
  |    return the result                                          |
  |  }                                                            |
  +----------------------------------------------------------+
                              |
                              v
              response, and updated UI, returned
              to the client in a single round trip
```

## 7. Dynamics

The trace below shows a form submitting through a Server Action,
including the authentication check the pattern requires.

```
User submits the form

the user fills the form and clicks submit
   |-- the browser, or the framework's own handling of the form
       action, dispatches a POST request to the marked server
       function
   |-- the server-side function receives the request, along with
       the submitted FormData

Server-side authentication check

the server-side function verifies the current session
   |-- if the session is missing or invalid, the function throws,
       and the mutation never runs, regardless of what the client
       side may have already assumed
   |-- if the session is valid, the function proceeds

Mutation and response

the function performs the actual mutation
   |-- the underlying data is updated
   |-- the function returns a result, and the framework returns
       both that result and updated UI in a single round trip
   |-- the client-side form, or the calling component, receives the
       result and updates accordingly
```

## 8. Implementation variants

**Form action.** A Server Action passed directly to a form's `action`
prop, the case with the strongest progressive-enhancement guarantee,
working even before client-side JavaScript has loaded.

**Button formAction.** A Server Action passed to a specific button's
`formAction` prop, letting a single form dispatch to different server
actions depending on which button the user actually pressed.

**Event handler invocation.** A Server Action called directly inside a
client-side event handler, such as `onClick`, for an interaction that
is not naturally a form submission but still needs to trigger a
server-side mutation.

**Passed as a prop.** A Server Action defined elsewhere is passed down
into a Client Component as a prop, letting the component that
actually renders the interactive element stay decoupled from where
the specific server-side logic is defined.

## 9. Known production uses

**React's own documentation, defining the mechanism.** React states
the definition directly. "Server Functions allow Client Components to
call async functions executed on the server," and describes the
underlying request cycle. "React will send a request to the server to
execute the function, and return the result." React, "Server
Functions," https://react.dev/reference/rsc/server-functions, verified
2026-08-21.

**Next.js's own documentation, on the naming distinction and the
security warning.** Next.js states the Server Function versus Server
Action distinction directly. "A Server Function is an asynchronous
function that runs on the server," and "in an action or mutation
context, they are also called Server Actions." It also states the
security requirement directly, as an explicit warning. "Server
Functions are reachable via direct POST requests, not only through
your application's UI. Always verify authentication and authorization
inside every Server Function." Next.js, "Mutating Data,"
https://nextjs.org/docs/app/getting-started/mutating-data, verified
2026-08-21.

## 10. Consequences

Positive.

- A single async function replaces a separate API endpoint plus a
  client-side fetch call, removing real coordination overhead for a
  conceptually single mutation operation.
- Forms calling a Server Action are submitted even before client-side
  JavaScript has loaded, or when it is disabled, a genuine
  progressive-enhancement guarantee Next.js's own documentation
  states directly.
- A mutation and its resulting UI update can return together in a
  single server round trip, rather than needing a separate follow-up
  request to refresh the client's view of the data.

Negative.

- The function is a genuine, directly reachable network endpoint,
  callable by a raw POST request independent of the application's
  own UI, exactly the concern Next.js's own documentation warns about
  explicitly.
- Server Functions are currently dispatched one at a time from the
  client, an implementation detail that matters for a use case
  genuinely needing true parallel execution.
- The convenience of calling a server function as if it were local
  can obscure, for a developer new to the pattern, that a real
  network request and its associated latency and failure modes are
  actually involved.

## 11. Failure modes and misuse

**Writing a Server Action's mutation logic without verifying
authentication or authorization inside the function itself.**
Symptom. Any client capable of sending a raw POST request to the
function's endpoint can trigger the mutation, entirely independent of
whether the application's own UI would have allowed that action.
Cause. Assuming the application's client-side UI, its buttons, its
conditional rendering, is itself a sufficient guard, when Next.js's
own documentation states plainly that the function is reachable
directly by POST request regardless of the UI. Fix. Verify
authentication and authorization inside every Server Action itself,
exactly as Next.js's own documentation instructs, treating the
function as a genuine, independently reachable endpoint rather than
code that only ever runs through the application's own UI.

**Reaching for a Server Action for a pure data-fetching read rather
than a genuine mutation.** Symptom. The application carries a
mutation-shaped mechanism, with its own network round trip and
dispatch semantics, for an operation that a Server Component could
have fetched directly during rendering with no client-triggered
network call at all. Cause. Treating Server Actions as the default
mechanism for any server-side data access, rather than reserving them
specifically for mutations. Fix. Use direct data fetching in a Server
Component for a pure read, reserving Server Actions for genuine
mutations, form submissions, updates, and deletions.

**Assuming Server Functions dispatch and complete in true parallel
when several are called close together.** Symptom. A sequence of
Server Function calls a developer expected to run concurrently
instead completes noticeably slower than expected, one after another.
Cause. Not accounting for Next.js's own stated implementation detail,
that the client currently dispatches and awaits Server Functions one
at a time. Fix. For genuinely parallel work, perform it inside a
single Server Function, or use dedicated Server Component data
fetching, rather than assuming several separately dispatched Server
Function calls will run concurrently.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from
dimension 3.

| Force | Server Action | Separate API endpoint plus client fetch | Client-only mutation, no server round trip |
|---|---|---|---|
| Coordination overhead for a mutation | Weak, one function replaces endpoint plus fetch | Strong overhead, two separate pieces of code to keep in sync | Not applicable, no server involved |
| Progressive enhancement for forms | Strong, works before JavaScript loads | Weak, usually depends on client-side JavaScript | Weak, entirely dependent on client-side JavaScript |
| Direct network exposure requiring its own authorization | Present, must be handled inside the function | Present, but explicit at the endpoint layer by convention | Not applicable, no server endpoint exists |
| Single round trip for UI and data together | Strong | Weak, usually a separate refresh request | Not applicable |

Reading of the table. A Server Action wins specifically for a genuine
mutation where reducing coordination overhead and gaining progressive
enhancement matter, provided the team treats the resulting function
as a real, independently reachable endpoint requiring its own
authorization check. A separate API endpoint remains a reasonable
choice when the endpoint's own explicit boundary is valuable for
other reasons, such as being consumed by a client outside the
application itself.

## 13. Related and incompatible patterns

- **Server Components.** A Server Action is frequently defined
  alongside, and invoked from, a Server Component's rendered form,
  the two patterns forming a common data-mutation-and-render pairing.
- **Optimistic UI.** A Server Action's real network latency is
  frequently paired with an optimistic update on the client, showing
  the mutation's predicted result immediately while the actual Server
  Action call completes in the background.
- **PRPL Pattern.** A Server Action's own network round trip is a
  cost PRPL's broader loading-performance considerations apply to,
  particularly on the constrained mobile networks PRPL is concerned
  with.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing mutation currently implemented as
a separate API endpoint plus a client-side fetch call.

1. Confirm the operation is genuinely a mutation, not a data read a
   Server Component could fetch directly instead.
2. Write a single async function containing the mutation logic,
   marked with the `use server` directive.
3. Add explicit authentication and authorization checks inside the
   function itself, never relying on the calling UI as the only
   guard.
4. Wire the function to its call site, a form's `action` prop, a
   button's `formAction` prop, or a direct call inside an event
   handler.
5. Remove the now-redundant separate API endpoint and client-side
   fetch call, confirming the resulting mutation still behaves
   correctly, including its authentication and authorization
   behavior.

Removing the pattern when it stops earning its place, most relevant
when a mutation genuinely needs to be consumed by a client outside
the application itself, where a conventional, explicitly documented
API endpoint serves better.

1. Confirm, rather than assume, that an external consumer genuinely
   needs to call this operation outside the application's own client
   code.
2. Convert the Server Action into a conventional API endpoint with
   its own explicit route and documented contract.
3. Update the application's own client code to call that endpoint
   directly, confirming the resulting behavior, including
   authentication and authorization, is unchanged.

## 15. Testing and verification

Easier because of the pattern.

- A Server Action, being a single async function, can be tested
  directly by calling it with a given input and asserting its
  behavior, including its authentication check, without needing to
  spin up a full API route or an HTTP client.
- Because a Server Action's logic lives in one place rather than
  split across an endpoint definition and a separate client-side
  fetch call, a test covering that one function covers the full
  mutation logic directly.

Harder because of the pattern.

- Verifying the pattern's progressive-enhancement claim, that a form
  calling a Server Action submits correctly even before client-side
  JavaScript loads, needs a test environment that can genuinely
  simulate a no-JavaScript or slow-JavaScript scenario, rather than
  the JavaScript-always-loaded assumption a typical component test
  makes.
- Because the function is directly, network-reachable independent of
  the application's own UI, testing its authentication and
  authorization behavior specifically needs a test that calls it
  directly, bypassing the UI entirely, to confirm the check genuinely
  guards the function rather than only appearing to because the UI
  happens to hide the button.

Techniques that apply.

- **Direct function tests.** Call the Server Action directly with
  various inputs, including an unauthenticated or unauthorized
  context, asserting it behaves correctly, including refusing the
  mutation when authentication or authorization fails.
- **Progressive-enhancement integration tests.** Test the form's
  actual submission behavior in an environment simulating no or
  delayed client-side JavaScript, confirming the mutation still
  completes.
- **Bypass-the-UI security tests.** Specifically test invoking the
  Server Action with an input an authorized UI would never actually
  produce, confirming the function's own internal checks, not the
  UI's restrictions, are what actually prevent an unauthorized
  mutation.
- **Round-trip integration tests.** Test the full path from form
  submission through the Server Action to the resulting UI update,
  confirming the single-round-trip behavior works correctly together.

## 16. Observability signals

A Server Action is a genuine server-side operation with real
network, latency, and authorization implications, so a dedicated
production signal is honest and expected here.

What to record.

- The rate of authentication and authorization failures for each
  Server Action, since Next.js's own documentation names direct POST
  reachability as a real concern, and a rising rate of failed checks
  may indicate a probing or abusive client rather than normal usage.
- The latency of each Server Action call, since this directly governs
  how the mutation feels to a real user, and a regression here points
  at a specific mutation's underlying logic, or the network path
  itself, having degraded.

A healthy state. Authentication and authorization checks pass for the
overwhelming majority of genuine, UI-driven calls, and latency stays
within an expected range for the specific mutation being performed.

A failing state. A Server Action shows an unusually high rate of
authentication or authorization failures, pointing at either a
misconfigured check or a client attempting to call the function
directly outside the application's own UI, or a specific Server
Action's latency has regressed, pointing at a problem in its own
mutation logic or the underlying data layer it depends on.

## 17. Security and privacy implications

Server Action carries the single most important, explicitly stated
security implication of any pattern in this family, worth restating
directly rather than softening.

**A Server Action is a genuine, independently network-reachable
endpoint, callable by a direct POST request regardless of the
application's own client-side UI, and Next.js's own documentation
states this as an explicit warning, that authentication and
authorization must be verified inside every Server Function, never
assumed from the fact that the application's UI would not normally
expose that action to an unauthorized user.** A Server Action that
performs a sensitive mutation, deleting a resource, changing a
permission, modifying another user's data, without its own internal
authentication and authorization check is a genuine, directly
exploitable vulnerability, not a theoretical one, since an attacker
does not need to interact with the application's UI at all to invoke
the function, only to send a correctly shaped POST request to its
endpoint.

## 18. References

1. React. "Server Functions".
   https://react.dev/reference/rsc/server-functions
   Verified 2026-08-21. Source of the defining mechanism quotes used
   in dimensions 1, 2, and 9.
2. Next.js. "Mutating Data".
   https://nextjs.org/docs/app/getting-started/mutating-data
   Verified 2026-08-21. Source of the Server Function versus Server
   Action distinction and the direct-POST-reachability security
   warning quotes used in dimensions 1, 3, 9, 11, and 17.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models a server-side function
and its authorization check the way React's own Server Functions and
Next.js's own Server Actions are structured, kept free of JSX and any
specific framework's package so the sample compiles as plain
TypeScript. Python shows the conceptual shape of the same
mutation-with-authorization-check logic using a minimal,
framework-agnostic implementation, since Python has no single
dominant Server Action implementation the way TypeScript has React's
own Server Functions. Swift shows the same conceptual shape using a
minimal model, analogous to how a native app's own networking layer
might perform a server-side mutation with its own authorization check
enforced server-side rather than trusted from the client. Java, Go,
and Rust are omitted, since none has a dominant, idiomatic
browser-facing component framework this specifically client-calls-
server pattern maps to as directly as TypeScript does.

### TypeScript

```typescript
interface Session {
  userId: string | null;
}

interface CreatePostInput {
  title: string;
  content: string;
}

interface CreatePostResult {
  success: boolean;
  postId?: string;
  error?: string;
}

function getCurrentSession(): Session {
  return { userId: "user-123" };
}

async function createPost(input: CreatePostInput): Promise<CreatePostResult> {
  const session = getCurrentSession();
  if (session.userId === null) {
    return { success: false, error: "unauthorized" };
  }

  const postId = "post-" + Date.now().toString();
  console.log("creating post:", input.title, "for user:", session.userId);

  return { success: true, postId };
}

async function main(): Promise<void> {
  const result = await createPost({ title: "Hello", content: "First post" });
  console.log("result:", result);
}

main();
```

### Python

```python
import asyncio
from dataclasses import dataclass
from typing import Optional


@dataclass
class Session:
    user_id: Optional[str]


@dataclass
class CreatePostInput:
    title: str
    content: str


@dataclass
class CreatePostResult:
    success: bool
    post_id: Optional[str] = None
    error: Optional[str] = None


def get_current_session() -> Session:
    return Session(user_id="user-123")


async def create_post(input_data: CreatePostInput) -> CreatePostResult:
    session = get_current_session()
    if session.user_id is None:
        return CreatePostResult(success=False, error="unauthorized")

    post_id = "post-generated"
    print(f"creating post: {input_data.title} for user: {session.user_id}")

    return CreatePostResult(success=True, post_id=post_id)


async def main() -> None:
    result = await create_post(CreatePostInput(title="Hello", content="First post"))
    print("result:", result)


if __name__ == "__main__":
    asyncio.run(main())
```

### Swift

```swift
struct Session {
    let userId: String?
}

struct CreatePostInput {
    let title: String
    let content: String
}

struct CreatePostResult {
    let success: Bool
    let postId: String?
    let error: String?
}

func getCurrentSession() -> Session {
    Session(userId: "user-123")
}

func createPost(_ input: CreatePostInput) async -> CreatePostResult {
    let session = getCurrentSession()
    guard let userId = session.userId else {
        return CreatePostResult(success: false, postId: nil, error: "unauthorized")
    }

    let postId = "post-generated"
    print("creating post: " + input.title + " for user: " + userId)

    return CreatePostResult(success: true, postId: postId, error: nil)
}

func main() async {
    let result = await createPost(CreatePostInput(title: "Hello", content: "First post"))
    print("result: " + String(result.success))
}

await main()
```
