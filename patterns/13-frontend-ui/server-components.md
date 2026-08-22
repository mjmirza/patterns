---
name: Server Components
slug: server-components
family: 13-frontend-ui
category: Rendering Strategy
aliases: [React Server Components, RSC]
first_described: "React documentation, React 19, stable"
maturity: canonical
related: [islands-architecture, hooks, progressive-enhancement]
incompatible_with: []
verified: 2026-08-21
---

# Server Components

## 1. Name, aliases, and lineage

The canonical name is Server Components, a component type that
renders ahead of time on the server rather than in the browser, and
whose output ships to the client without any of the component's own
JavaScript, only its rendered result. React's own documentation
defines the idea directly. "Server Components are a new type of
Component that renders ahead of time, before bundling, in an
environment separate from your client app or SSR server." This
separate environment is, in React's own words, "the server in React
Server Components."

The alias **React Server Components** is the full, framework-specific
name, since the pattern originated in and is most closely associated
with React, though the underlying idea, a component that renders on
the server and ships no client JavaScript, has since been adopted by
other frameworks under their own names. **RSC** is the common
abbreviation used throughout React's own documentation and the wider
community of frameworks built on it.

## 2. Problem and context

A component tree rendered entirely on the client, even one that is
server-side rendered for the initial HTML, ships every component's
own JavaScript to the browser for hydration, including components
that only ever fetch and display static or server-only data and never
need any client-side interactivity at all. This forces a real amount
of unnecessary JavaScript, and the libraries those components depend
on, to be downloaded, parsed, and hydrated by the browser, and forces
any component that needs server-only data, a database query, a
file-system read, to either expose that data through a separate API
endpoint or fetch it client-side after the component has already
mounted, introducing a data-fetching waterfall. Server Components
solve this by letting a component render ahead of time in a
server-only environment, with direct access to a data layer with no
API to build, and shipping to the browser only the component's
rendered output, none of the component's own JavaScript or its
server-only dependencies.

## 3. Forces

The pattern balances the following competing pressures.

- **Reducing JavaScript shipped to the browser.** Favored. Because a
  Server Component's own code and its dependencies never ship to the
  client, a page composed largely of Server Components can ship
  noticeably less JavaScript than the same page built entirely from
  client-hydrated components.
- **Direct, secure access to a data layer.** Favored. A Server
  Component can query a database or read a file system directly,
  since it runs in a server-only environment, without needing to
  expose that access through a separate, publicly reachable API
  endpoint.
- **Client-side interactivity.** Sacrificed by Server Components
  themselves, and delegated to Client Components. React's own
  documentation states this constraint directly. Server Components
  are never sent to the browser, so they cannot use interactive APIs
  such as `useState`, which means any genuinely interactive piece of
  the UI must be a Client Component, marked with a directive and
  composed alongside the Server Components that surround it.
- **Eliminating client-side data-fetching waterfalls.** Favored.
  Because a Server Component can fetch its own data directly during
  server rendering, several components that each need their own data
  can be resolved together on the server rather than triggering a
  chain of sequential client-side fetches after mount.

## 4. Applicability and non-applicability

Reach for Server Components when the following hold.

- A real portion of the page's component tree only displays
  data and needs no client-side interactivity, making it a genuine
  candidate to ship zero JavaScript to the browser.
- The application needs to query a database, read a file system, or
  otherwise access server-only resources directly from within a
  component, without building and maintaining a separate API layer
  purely to expose that access to the client.
- The team's framework and hosting infrastructure genuinely support
  Server Components as a stable feature, since the underlying
  implementation APIs a framework or bundler depends on are not
  guaranteed to be stable across minor React releases even though
  Server Components themselves are.

Do NOT reach for Server Components in these cases, and the reason
matters more than the rule.

- **The component is genuinely, pervasively interactive**, needing
  `useState`, event handlers, or any client-only browser API, it must
  be a Client Component regardless, and forcing it toward a Server
  Component boundary it cannot satisfy only adds confusion.
- **The team's framework or hosting setup does not genuinely support
  Server Components as a stable, production-ready feature**, adopting
  the pattern against an unstable or unsupported implementation risks
  breakage the underlying bundler APIs are explicitly not guaranteed
  to avoid across minor versions.
- **The application is a genuinely client-only experience with no
  real server-only data access or JavaScript-reduction need**,
  such as a purely local, offline-first tool, where the server-only
  environment Server Components depend on offers no real benefit.

## 5. Structure

Server Components has three structural parts.

- **Server Components**, the default component type, rendered ahead
  of time on the server, with no client-side JavaScript of their own
  shipped to the browser.
- **Client Components**, explicitly marked with a directive, used for
  any piece of the UI that genuinely needs client-side interactivity,
  composed alongside Server Components in the same tree.
- **The server-only environment**, the separate context, distinct
  from the client app and distinct from a traditional server-side
  rendering server, in which Server Components render, with direct
  access to server-only resources such as a database or a file
  system.

## 6. ASCII structure diagram

```
  +----------------------------------------------------------------+
  |  Server-only environment (build time or per-request)            |
  |                                                                   |
  |   ServerComponent (article page)                                 |
  |     |-- fetches data directly from the database                  |
  |     |-- renders ArticleBody (Server Component, static content)   |
  |     |-- renders LikeButton (Client Component, marked directive)  |
  |                                                                   |
  +----------------------------------------------------------------+
                              |
                              v
              rendered output shipped to the browser
                              |
       +----------------------------+   +--------------------------+
       |  ArticleBody's HTML output  |   |  LikeButton's JavaScript  |
       |  (no JavaScript shipped)    |   |  (hydrated, interactive)  |
       +----------------------------+   +--------------------------+
```

## 7. Dynamics

The trace below shows a page composed of a Server Component fetching
data and a Client Component providing interactivity, rendered
together and delivered to the browser.

```
Server rendering

a request arrives for the article page
   |-- the ArticlePage Server Component runs in the server-only
       environment
   |-- it queries the database directly for the article's content,
       with no separate API endpoint needed
   |-- it renders the ArticleBody Server Component with that data
   |-- it renders the LikeButton Client Component, passing the
       article's id as a prop

Composing the response

the server assembles the rendered output
   |-- ArticleBody's rendered HTML is included directly, with no
       JavaScript for ArticleBody shipped to the client
   |-- LikeButton's own JavaScript is included, since it is a Client
       Component and needs to hydrate

Client hydration

the browser receives the composed response
   |-- ArticleBody's HTML is already visible, with nothing to hydrate
   |-- LikeButton's JavaScript hydrates, becoming interactive
   |-- clicking the like button now works, handled entirely by the
       Client Component, with no further involvement from the Server
       Component that rendered it
```

## 8. Implementation variants

**Build-time Server Components.** A Server Component's rendering runs
once, ahead of time, on a build or CI server, producing a static
output baked into the deployed application, appropriate for content
that does not change per request.

**Per-request Server Components.** A Server Component's rendering
runs on a web server for each incoming request, letting it reflect
per-request data, such as a specific user's own content, while still
never shipping its own JavaScript to the client.

**Composing Server and Client Components.** The common production
shape, where a page's overall structure and data-fetching are handled
by Server Components, with small, explicitly marked Client Components
nested inside them for the specific pieces of the UI that genuinely
need interactivity.

**Framework-level Server Component conventions.** A framework built
on top of React's Server Components primitive, providing its own
routing and data-fetching conventions around the underlying Server
and Client Component model, rather than a team implementing the
bundler-level wiring by hand.

## 9. Known production uses

**React's own documentation, defining Server Components and their
constraints.** React's documentation states the core definition
directly. "Server Components are a new type of Component that renders
ahead of time, before bundling, in an environment separate from your
client app or SSR server." It states the interactivity constraint
plainly too. "Server Components are not sent to the browser, so
they cannot use interactive APIs like `useState`," adding that
composing them with a Client Component is how interactivity is added
back in. React documentation, "Server Components,"
https://react.dev/reference/rsc/server-components, verified
2026-08-21.

**React's own documentation, on the data-access and bundle-size
benefit.** The documentation states the direct data-access benefit
plainly. "Server Components can also run on a web server during a
request for a page, letting you access your data layer without having
to build an API." It frames the overall goal as combining two
previously separate architectural models, "the simple request slash
response mental model of server-centric Multi-Page Apps" with the
fluid interactivity of client-centric Single-Page Apps. React
documentation, "Server Components,"
https://react.dev/reference/rsc/server-components, verified
2026-08-21.

## 10. Consequences

Positive.

- A Server Component's own code and its dependencies never ship to
  the browser, so a page composed largely of Server Components can
  ship noticeably less JavaScript than the equivalent page built
  entirely from client-hydrated components.
- A Server Component can access a database or a file system directly,
  removing the need to build and maintain a separate API purely to
  expose that access to a client component.
- Several Server Components can resolve their own data together
  during server rendering, avoiding the sequential client-side
  data-fetching waterfall a fully client-rendered tree would
  otherwise produce.

Negative.

- A Server Component cannot use interactive APIs such as `useState`
  at all, so any genuinely interactive piece of the UI must be
  explicitly split out into a Client Component, adding a real
  server-versus-client boundary a team must reason about for every
  component.
- The underlying bundler and framework implementation APIs Server
  Components depend on are not guaranteed to be stable across minor
  React releases, even though the Server Components feature itself
  is, so adopting the pattern needs a framework or bundler that keeps
  that implementation detail current.
- A team new to the pattern needs to learn a genuinely new mental
  model, deciding for every component whether it belongs on the
  server or the client, a decision a fully client-rendered
  application never had to make.

## 11. Failure modes and misuse

**Marking a component as a Client Component reflexively, out of habit
from a fully client-rendered codebase, when it needs no
interactivity.** Symptom. The page ships JavaScript for a component
that only ever displays data and never needs `useState`, an event
handler, or any client-only API, giving up the JavaScript-reduction
benefit Server Components exist to provide. Cause. Applying the
client directive by default rather than reserving it for components
that genuinely need client-side interactivity. Fix. Default every
component to a Server Component, and mark a component as a Client
Component only when it genuinely needs an interactive API, an event
handler, or a client-only browser feature.

**Attempting to use a client-only interactive API, such as `useState`,
directly inside a Server Component.** Symptom. The component fails to
build or render, since Server Components are never sent to the
browser and cannot use APIs that depend on client-side state and
re-rendering. Cause. Treating a Server Component as functionally
identical to a traditional component, rather than recognizing its
fundamental constraint. Fix. Extract the interactive piece of the
component into its own, explicitly marked Client Component, composed
inside the Server Component rather than mixed directly into it.

**Passing a large amount of server-only data through props into a
Client Component that only needs a small piece of it.** Symptom. The
serialized data passed across the server-to-client boundary grows
larger than necessary, since the entire object was passed down rather
than only the specific fields the Client Component actually needs.
Cause. Passing convenience rather than deliberately narrowing what
crosses the server-to-client boundary. Fix. Pass only the specific
fields a Client Component genuinely needs across the boundary, doing
any further data shaping or filtering in the Server Component before
the data is serialized and sent to the client.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Server Components | Fully client-hydrated components | Islands Architecture | Traditional server-side rendering |
|---|---|---|---|---|
| JavaScript shipped for non-interactive content | Minimal, none for pure Server Components | High, the whole tree hydrates | Minimal, only marked islands | Moderate, still hydrates the whole tree on the client |
| Direct server-only data access without a separate API | Strong, built in | Not applicable, needs a separate API | Not applicable, needs a separate API | Strong, but the whole page is server rendered |
| Client-side interactivity for a genuinely interactive piece | Strong, via composed Client Components | Strong, native | Strong, via islands | Strong, once hydrated |
| Data-fetching waterfall avoidance | Strong, resolved together on the server | Weak, sequential client fetches after mount | Moderate, per-island | Strong, resolved before the response is sent |
| Team learning curve for the server versus client boundary | Real, a genuinely new mental model | Not applicable | Real, a similar boundary concept | Not applicable |

Reading of the table. Server Components win specifically when a page
mixes a real amount of purely static, server-data-driven
content with a smaller amount of genuine interactivity, letting the
static portion ship zero JavaScript while the interactive portion
still works as expected. A genuinely, pervasively interactive
application gains comparatively little from the pattern, since nearly
every component would end up as a Client Component regardless.

## 13. Related and incompatible patterns

- **Islands Architecture.** A closely related, complementary rendering
  strategy addressing the same JavaScript-reduction goal, often
  discussed alongside Server Components, with the distinction that
  islands are explicitly marked interactive regions within an
  otherwise static page, while Server Components default every
  component to server rendering and require an explicit directive to
  opt into client interactivity.
- **Progressive Enhancement.** A related philosophy, building a
  working experience from server-rendered content first and layering
  client-side interactivity on top, which Server Components can be
  seen as a modern, component-scoped implementation of.
- **Hooks.** The mechanism a Client Component composed alongside
  Server Components usually uses internally to manage its own
  client-side state, independent of the Server Components pattern
  itself.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it. Ordered
steps, most relevant to an existing fully client-rendered application
where a real portion of the component tree only displays data
and never needs client-side interactivity.

1. Confirm the team's framework and hosting infrastructure genuinely
   support Server Components as a stable, production-ready feature.
2. Inventory the existing component tree and classify each component
   as genuinely interactive or purely data-displaying.
3. Convert the purely data-displaying components to Server Components
   by default, removing any client directive they previously carried.
4. Explicitly mark the genuinely interactive components as Client
   Components, composing them inside the surrounding Server
   Components.
5. Move any direct database or file-system access that previously
   went through a separate API endpoint directly into the relevant
   Server Component, removing the now-unnecessary API layer where
   appropriate.

Removing the pattern when it stops earning its place, most relevant
when a framework or hosting migration no longer supports it, or when
the application has grown pervasively interactive enough that nearly
every component would need to be a Client Component regardless.

1. Confirm the migration or the interactivity growth is genuine,
   rather than assuming so without review.
2. Convert the remaining Server Components to Client Components,
   rebuilding any direct data access they relied on as a separate API
   layer the client can call.
3. Remove the server-versus-client component boundary from the
   codebase once the migration to a fully client-rendered model is
   complete.

## 15. Testing and verification

Easier because of the pattern.

- A Server Component's rendered output can be asserted directly
  against the data it was given, with no need to simulate a browser
  environment or hydration at all, since it never runs on the client.
- Because a Server Component's data access happens directly rather
  than through a separate API, a test can assert the component's
  behavior against a given data-layer state without needing to mock
  an HTTP layer between them.

Harder because of the pattern.

- Testing that a Server Component and a composed Client Component
  genuinely work together, that the data passed across the
  server-to-client boundary is correctly serialized and received,
  needs a test environment that can exercise both sides of that
  boundary together.
- Verifying that a component correctly stays on the server, and never
  accidentally ships its own JavaScript to the client, needs an
  inspection of the actual client bundle output, not only a
  behavioral test of the component's rendered result.

Techniques that apply.

- **Isolated Server Component rendering tests.** Render a Server
  Component directly against a given data-layer state and assert its
  output, with no browser simulation needed.
- **Isolated Client Component tests.** Test a Client Component's own
  interactive behavior directly, independent of the Server Component
  that composes it, treating its props as the boundary.
- **Bundle-inspection tests.** Assert the built client bundle does not
  include a specific Server Component's own code, catching a
  regression where a component that should have stayed server only
  accidentally became part of the client bundle.
- **Full composed integration tests.** Render the full page, Server
  and Client Components together, and assert the end-to-end behavior,
  confirming the boundary between them works correctly in practice.

## 16. Observability signals

Server Components has a genuine runtime footprint, since it directly
governs what renders on the server versus what ships to and hydrates
in the browser, so a dedicated production signal is honest here.

What to record.

- The size of the client JavaScript bundle actually shipped for a
  given page, broken down by which components contributed to it,
  since a Server Component that accidentally ends up in the client
  bundle is a direct, measurable regression against the pattern's
  core benefit.
- The server-side rendering time for a page's Server Components,
  since direct data access happening inside the render itself, rather
  than a separate client-side fetch, means a slow data query now
  directly extends the server's response time rather than being
  hidden behind a later client-side loading state.

A healthy state. The client bundle for a given page contains
JavaScript only for its genuinely interactive Client Components, with
no Server Component's own code present, and the server's rendering
time stays within an acceptable budget for the data access its Server
Components perform.

A failing state. A Server Component's own code appearing in the
client bundle, pointing at a component that should have stayed server
only being marked or composed incorrectly, or the server's rendering
time growing unexpectedly, pointing at a slow, unbounded data query
happening directly inside a Server Component's render with no
timeout or caching in place.

## 17. Security and privacy implications

Server Components carries a real security implication, since a
Server Component's direct access to server-only resources, and the
data it passes across the boundary to a Client Component, both touch
what reaches an untrusted client directly.

**Any data a Server Component fetches and passes as a prop to a
Client Component crosses the server-to-client boundary and becomes
visible in the browser, so a Server Component that fetches more data
than a Client Component actually needs, or that passes a sensitive
field through by convenience rather than deliberate narrowing, can
leak that data to the client even though the Server Component's own
code never ships.** Because a Server Component's direct database or
file-system access removes the natural filtering an API endpoint
would otherwise provide, a team should treat every prop passed from a
Server Component to a Client Component as data that will reach the
browser, and deliberately narrow what is fetched and passed to
exactly what the Client Component needs, never passing a full
data-layer object through by default.

## Code examples

Three languages and frameworks where the pattern is genuinely
idiomatic in different ways. TypeScript models the server-versus-client
component split the way React's own Server Components structure it,
kept free of JSX and any specific framework's package so the sample
compiles as plain TypeScript. Python shows the same conceptual split
using a minimal, framework-agnostic server-side rendering function
that fetches data directly and produces a static output alongside a
separate, explicitly marked interactive component's client bundle
reference, since Python has no single dominant Server Components UI
framework the way TypeScript has React. Swift shows the pattern using
a minimal, analogous model where a server-rendered view produces
static content composed with a client-marked interactive view,
closely analogous to how the server-versus-client boundary is reasoned
about in a hybrid native and web context. Java, Go, and Rust are
omitted, since none has a dominant, idiomatic UI-component framework
this specifically frontend rendering pattern maps to as directly as
TypeScript and Swift do.

### TypeScript

```typescript
interface Article {
  id: string;
  title: string;
  body: string;
}

function fetchArticleFromDatabase(id: string): Article {
  return { id, title: "Example Article", body: "Static article content." };
}

function renderServerArticleBody(article: Article): string {
  return "<article><h1>" + article.title + "</h1><p>" + article.body + "</p></article>";
}

interface ClientLikeButton {
  articleId: string;
  isInteractive: true;
}

function renderClientLikeButton(articleId: string): ClientLikeButton {
  return { articleId, isInteractive: true };
}

function renderServerArticlePage(articleId: string): { html: string; clientComponents: ClientLikeButton[] } {
  const article = fetchArticleFromDatabase(articleId);
  const html = renderServerArticleBody(article);
  const clientComponents = [renderClientLikeButton(article.id)];
  return { html, clientComponents };
}

const page = renderServerArticlePage("article-1");
console.log(page.html);
console.log("client components to hydrate: " + page.clientComponents.length);
```

### Python

```python
from dataclasses import dataclass


@dataclass
class Article:
    id: str
    title: str
    body: str


def fetch_article_from_database(article_id: str) -> Article:
    return Article(id=article_id, title="Example Article", body="Static article content.")


def render_server_article_body(article: Article) -> str:
    return f"<article><h1>{article.title}</h1><p>{article.body}</p></article>"


@dataclass
class ClientLikeButton:
    article_id: str
    is_interactive: bool = True


def render_client_like_button(article_id: str) -> ClientLikeButton:
    return ClientLikeButton(article_id=article_id)


def render_server_article_page(article_id: str) -> tuple[str, list[ClientLikeButton]]:
    article = fetch_article_from_database(article_id)
    html = render_server_article_body(article)
    client_components = [render_client_like_button(article.id)]
    return html, client_components


if __name__ == "__main__":
    html, client_components = render_server_article_page("article-1")
    print(html)
    print("client components to hydrate:", len(client_components))
```

### Swift

```swift
struct Article {
    let id: String
    let title: String
    let body: String
}

func fetchArticleFromDatabase(id: String) -> Article {
    Article(id: id, title: "Example Article", body: "Static article content.")
}

func renderServerArticleBody(article: Article) -> String {
    "<article><h1>" + article.title + "</h1><p>" + article.body + "</p></article>"
}

struct ClientLikeButton {
    let articleId: String
    let isInteractive = true
}

func renderClientLikeButton(articleId: String) -> ClientLikeButton {
    ClientLikeButton(articleId: articleId)
}

func renderServerArticlePage(articleId: String) -> (html: String, clientComponents: [ClientLikeButton]) {
    let article = fetchArticleFromDatabase(id: articleId)
    let html = renderServerArticleBody(article: article)
    let clientComponents = [renderClientLikeButton(articleId: article.id)]
    return (html, clientComponents)
}

let page = renderServerArticlePage(articleId: "article-1")
print(page.html)
print("client components to hydrate: " + String(page.clientComponents.count))
```

## 18. References

1. React documentation. "Server Components".
   https://react.dev/reference/rsc/server-components
   Verified 2026-08-21. Source of the defining sentence, the
   interactivity constraint, and the data-access and architecture
   quotes in dimensions 1, 3, and 9.
