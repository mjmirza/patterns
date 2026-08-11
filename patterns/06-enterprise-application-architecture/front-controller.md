---
name: Front Controller
slug: front-controller
family: 06-enterprise-application-architecture
category: Web Presentation
aliases: []
first_described: "Alur, Crupi, Malks 2001; Fowler 2003"
maturity: canonical
related: [page-controller, command, mediator, chain-of-responsibility, application-controller]
incompatible_with: [page-controller]
verified: 2026-08-11
---

# Front Controller

## 1. Name, aliases, and lineage

The canonical name is Front Controller. There is no widely used alias in the
primary literature. Some blog posts call the entry-point file a "front door"
informally, and Azure's Front Door is an unrelated CDN and reverse-proxy
product with a coincidentally similar name, not an alias of this pattern.
Application Controller is a distinct, related pattern, covered under dimension
13, and is sometimes confused with Front Controller by practitioners who have
only skimmed a summary, but the two solve different problems.

The pattern first appears in print in Deepak Alur, John Crupi, and Dan Malks,
*Core J2EE Patterns. Best Practices and Design Strategies*, Prentice Hall,
2001, later expanded in the second edition, Prentice Hall, 2003, in the
Presentation Tier Patterns chapter, Front Controller entry. The three authors
worked at the Sun Java Center and wrote the catalog from patterns they had
observed recurring across J2EE consulting engagements, which is why the
original problem statement is phrased in servlet and JSP terms (Deepak Alur,
John Crupi, Dan Malks, *Core J2EE Patterns. Best Practices and Design
Strategies*, 2nd edition, Prentice Hall, 2003, Presentation Tier Patterns,
"Front Controller").

Martin Fowler catalogued the same pattern independently, under the same name,
in *Patterns of Enterprise Application Architecture*, Addison-Wesley, 2003,
pages 344 to 349, immediately after Page Controller, in the Web Presentation
patterns group. Fowler's own summary states the intent in one line, "A
controller that handles all requests for a Web site" (Martin Fowler, "Front
Controller," martinfowler.com/eaaCatalog/frontController.html, verified
2026-08-11). Fowler credits Sun's Core J2EE Patterns catalog as the origin and
adds the observation that a Front Controller is usefully split into two
collaborating objects, a Handler that owns the single physical entry point and
common preprocessing, and a Command hierarchy that the Handler dispatches to,
which is the shape this entry documents as the default structure.

Because the two catalogs describe the same solution to the same problem under
the same name within two years of each other, and neither disputes the other's
account, this entry treats them as one lineage rather than two competing
definitions. The pattern predates both books as informal practice. A single
CGI script that reads a `PATH_INFO` or query parameter and branches to the
right handler function is Front Controller before either book gave it a name,
the same way Page Controller predates Fowler's name for it. What the two
catalogs added was not the technique but the vocabulary, and a explicit
argument for choosing it deliberately over letting the servlet container or
web server map URLs one-to-one onto handler classes by convention.

## 2. Problem and context

A web application grows past a handful of pages. Each page, or each family of
related actions, gained its own entry point over time, a servlet here, a PHP
script there, an action class registered against its own URL pattern. Every
one of those entry points needs the same handful of things done before its own
logic runs. The user's session needs to be checked. The request's locale needs
to be resolved so the right resource bundle loads. An audit log line needs to
be written. A CSRF token needs to be validated on anything that mutates state.
None of that behavior is specific to any one page, and none of it belongs to
the page's own logic, but because there is no single place where "before any
page runs" code can live, it gets copied into every entry point instead, or
bolted onto a base class that every page controller inherits from and every
new developer has to remember to extend correctly.

The failure mode this produces is specific and observable. A new authentication
requirement ships, and it has to be added to forty controller classes one at a
time, because there was never one place that saw every request. Somebody
misses one, usually the newest and least-trafficked page, and it ships without
the check. Six months later a security audit finds it. The proximate cause was
a missed edit. The real cause is that the application never had a single
choke point through which every request was guaranteed to pass, so "add this
to every request" was a search-and-replace exercise across the whole codebase
instead of an edit to one class.

The context that produces this problem has three recurring features. First,
the application serves many distinct resources or actions from one process,
so the same request-handling machinery, sessions, dispatch, view resolution,
gets reused dozens or hundreds of times. Second, a meaningful amount of
per-request work is genuinely shared across most or all of those resources,
authentication, authorization, internationalization, logging, transaction
demarcation, response compression. Third, the team wants that shared work
enforced, not merely documented, because a convention that depends on every
developer remembering to call a helper method is a convention that will be
forgotten under deadline pressure. Front Controller answers all three by
making the entry point itself, rather than a base class or a coding
convention, the place where shared behavior is guaranteed to run, because a
request that never passes through the Front Controller never reaches any
handler at all.

## 3. Forces

The pattern balances the following competing pressures, and it does not win on
every axis, which is the honest reading of any pattern rather than a marketing
claim for one.

- **Coupling.** Favoured toward the application and against the infrastructure.
  Every handler now depends on the front controller's calling convention
  rather than on the web server's URL-to-file mapping, which is a smaller and
  more stable dependency to hold.
- **Consistency.** Strongly favoured. Because every request funnels through
  one object, the shared preprocessing genuinely runs for every request, not
  for every request whose author remembered to call it. This is the pattern's
  entire reason to exist.
- **Latency.** Mildly sacrificed. There is one extra dispatch hop, and if the
  front controller's shared preprocessing does real work, a database lookup
  for session state, a locale negotiation, that cost is paid on every request
  rather than only where it is needed. In practice this cost is small next to
  network and rendering time, but it is not zero, and it is paid even by
  requests that did not need the check that happened to be running that day.
- **Operability.** Favoured. One log line at the top of dispatch, tagged with
  the resolved action name, gives an operator a single place to see every
  request that entered the system, which page or action it was routed to, and
  how long the shared preprocessing took. Without a front controller this view
  has to be reconstructed by correlating logs scattered across every handler.
- **Team topology.** Genuinely mixed, and this is the force most catalogs
  understate. A shared entry point is favoured when one team owns cross-cutting
  concerns and many teams contribute handlers, because the platform team's
  code lives in exactly one place. It is sacrificed the moment the dispatch
  table itself, the mapping from action name to handler, becomes a single file
  that many teams must edit, because that file becomes a permanent source of
  merge conflicts unless the registration is externalized, see dimension 11.
- **Testability.** Favoured for the shared preprocessing, which is now testable
  once instead of once per handler. Mildly sacrificed for the handlers
  themselves, which now need a fake request object matching whatever contract
  the front controller defines, rather than being testable as plain functions
  with plain arguments.
- **Cost of change.** Favoured for adding cross-cutting behavior, one edit
  instead of many. Sacrificed for changing the request or dispatch contract
  itself, because that change now ripples to every handler at once rather than
  being isolated to the one handler that needed it.

A pattern that sacrificed nothing would not be a pattern, it would be a free
lunch. The price of Front Controller is paid in a small latency tax on every
request and in the discipline required to keep the shared entry point from
becoming a bottleneck for the team, not only for the traffic.

## 4. Applicability and non-applicability

Reach for Front Controller when the following hold.

- Many distinct pages or actions in one application need the same
  preprocessing, authentication, locale resolution, audit logging, transaction
  boundaries, applied consistently, and "consistently" has to mean guaranteed,
  not merely documented in a wiki page.
- The team wants one place to add global behavior in the future, request
  throttling, a new security header, a feature flag check, without touching
  every existing handler.
- The application is building its own dispatch layer rather than adopting a
  framework that already provides one, and the team has decided a shared entry
  point earns its complexity, see dimension 8 for the framework case.
- View selection itself is a shared decision that benefits from centralizing,
  for example choosing between a desktop and mobile template family based on
  request headers, which every handler would otherwise have to duplicate.
- The application is a monolith or a single deployable service where "all
  requests" has one honest meaning. A front controller answers the question
  "what happens to every request into this process," and that question is
  only coherent when there is one process.

Do NOT reach for Front Controller in these cases, and the reason matters more
than the rule, per the non-applicability discipline this catalog follows for
every entry.

- **The application has one or two pages and no plausible third.** A Front
  Controller with one registered command is a detour through an abstraction
  that never pays for itself. A plain script or a single handler function does
  the same job with one fewer indirection to trace. Cross reference the code
  smell family entry on speculative generality.
- **The framework already provides one.** Spring MVC, ASP.NET Core, Symfony,
  Ruby on Rails through Rack, and most modern web frameworks ship a front
  controller as their own foundation, see dimension 9. Building a second,
  application-level front controller on top of the framework's own dispatch
  layer produces a framework wrapped around a framework, doubling the
  indirection a reader has to trace to find where a request actually goes, for
  no consistency benefit the framework was not already providing. The honest
  move here is to use the framework's interceptor, middleware, or filter
  mechanism for cross-cutting concerns, which is exactly the extension point
  the framework's own front controller was built to expose.
- **The requests are genuinely heterogeneous in protocol or shape.** A process
  that serves HTTP, a gRPC stream, and a WebSocket connection does not have one
  coherent "all requests" concept. Forcing all three through one dispatcher
  produces a request abstraction so generic it can no longer express what is
  distinctive about each protocol, which is the leaky-abstraction failure this
  pattern is prone to at its edges.
- **The system is a set of independently deployed services rather than one
  process.** Funnelling cross-service traffic through one in-process front
  controller reintroduces a shared, centrally owned bottleneck at exactly the
  boundary microservice architectures exist to remove. The distributed-systems
  descendant of this pattern is an API Gateway, deployed as its own service in
  front of many independently owned backends, not a shared class inside one of
  those backends, see dimension 13.
- **Per-request state genuinely does not compose across actions.** If two
  actions in the same application have almost nothing in common, different
  authentication schemes, different response formats, different transaction
  models, a shared entry point buys consistency the two actions do not
  actually want, and the "shared" preprocessing degenerates into a chain of
  `if` statements asking which flavor of request this is, which is the same
  branching the pattern exists to avoid, only moved one layer up.

## 5. Structure

The pattern is conventionally described as two collaborating objects rather
than one, a distinction Core J2EE Patterns and Fowler both make explicit, even
though a small implementation is free to collapse the two into one class.

- **Handler (the Front Controller proper).** The single object every request
  physically reaches first. Owns the preprocessing that must run for every
  request, session validation, locale resolution, logging, and then hands the
  request to the Dispatcher. In a servlet environment this is one
  `HttpServlet` mapped to `/*` or to a single physical URL such as
  `index.php`. Fowler's structure treats the Handler as the piece that "can be
  changed at runtime through decoration," meaning cross-cutting behavior can
  be added by wrapping the handler rather than editing it, which is the same
  idea as a middleware chain, see dimension 8.
- **Dispatcher.** Resolves which piece of application-specific logic should
  handle this particular request, and forwards control to it. Core J2EE
  Patterns treats the Dispatcher as a distinct participant precisely because
  view management and navigation, deciding which view or handler comes next,
  is a different responsibility from the Handler's shared preprocessing, and
  keeping them separate lets the navigation logic change, for example a
  configuration-file-driven route table replacing a hardcoded switch, without
  touching the shared preprocessing at all.
- **Command (or Action).** The object that holds the behavior specific to one
  request type. Reading form parameters, invoking domain logic, choosing which
  data the view needs. This participant is the Gang of Four Command pattern in
  practice, see dimension 13, and it is where the actual per-page logic lives
  once it has been extracted out of what would otherwise be a single
  monolithic Handler method.
- **View.** Renders the response for the client. Not owned by the Front
  Controller pattern itself, this is a Template View, Transform View, or
  equivalent rendering pattern that the Dispatcher hands control to once a
  Command has finished.
- **Helper.** An optional participant, present in the Core J2EE Patterns
  version of the structure, that assists a Command or a View in gathering
  data or formatting output, factored out so the same data-gathering logic is
  not copied across several Commands that need the same intermediate model.

A minimal implementation collapses Handler and Dispatcher into one class, and
that collapse is common and reasonable at small scale, but naming them
separately in a design discussion keeps "run this for every request" and
"decide which command handles this request" from silently merging back into
one undifferentiated method as the application grows, which is exactly the
failure mode covered in dimension 11.

## 6. ASCII structure diagram

```text
+------------------+        +-------------------+
|      Client      | -----> |  Front Controller  |
+------------------+        |     (Handler)      |
                             |  - auth check      |
                             |  - locale resolve  |
                             |  - request log     |
                             +---------+----------+
                                       |
                                       v
                             +-------------------+
                             |     Dispatcher     |
                             | - route table      |
                             | - view resolution  |
                             +---------+----------+
                                       |
                     +-----------------+-----------------+
                     |                 |                 |
                     v                 v                 v
             +--------------+ +--------------+ +--------------+
             | Command:     | | Command:     | | Command:     |
             | ShowInvoice  | | UpdateOrder  | | ExportReport |
             +------+-------+ +------+-------+ +------+-------+
                    |                |                |
                    v                v                v
             +--------------+ +--------------+ +--------------+
             |    Helper    | |    Helper    | |    Helper    |
             | (optional)   | | (optional)   | | (optional)   |
             +------+-------+ +------+-------+ +------+-------+
                    |                |                |
                    +--------+-------+--------+-------+
                             v
                     +----------------+
                     |      View      |
                     +----------------+
```

## 7. Dynamics

```text
Client                Front Controller       Dispatcher          Command           View
  |                        |                    |                  |                |
  |--- HTTP request ------>|                    |                  |                |
  |                        |-- authenticate() --|                  |                |
  |                        |-- resolve locale --|                  |                |
  |                        |-- log request -----|                  |                |
  |                        |                    |                  |                |
  |                        |--- dispatch(req) ->|                  |                |
  |                        |                    |-- lookup(action)-|                |
  |                        |                    |                  |                |
  |                        |                    |-- execute(req) ->|                |
  |                        |                    |                  |-- build model  |
  |                        |                    |                  |-- pick view -->|
  |                        |                    |                  |                |
  |                        |                    |<-- view name ----|                |
  |                        |                    |                  |                |
  |                        |                    |----- render(model) ------------->|
  |                        |                    |                  |                |
  |<------------------- HTTP response -----------------------------|<--- rendered --|
```

Unmapped-action and error paths are the second, equally important flow this
diagram omits for space. When the Dispatcher finds no Command registered for
the requested action, or a Command raises an exception, the Front Controller
must handle that centrally too, routing to a 404 or 500 view rather than
letting the failure propagate unhandled to the client, and it must do so
without allowing one Command's failure to leave shared state, such as a
partially written session, in an inconsistent condition for the next request,
see dimension 11 for the specific failure this omission produces.

## 8. Implementation variants

- **Class-based Handler plus Dispatcher plus Command, the textbook shape.**
  One servlet or equivalent as the physical entry point, a separate Dispatcher
  object holding a route table, and Command classes implementing a shared
  interface. This is the shape both Core J2EE Patterns and Fowler describe,
  and it is the shape the code examples in this entry implement.
- **Physical versus logical resource.** Core J2EE Patterns distinguishes a
  physical front controller, one literal URL such as `index.php` that every
  request hits through URL rewriting, from a logical front controller, one
  servlet class registered against a wildcard URL pattern such as `/*` while
  the underlying URLs still vary. The physical form is common in PHP, where
  Symfony and WordPress both rewrite every request to one file, see dimension
  9. The logical form is common in Java, where the servlet container's own URL
  matching does the rewriting invisibly.
- **Filter-chain complement for cross-cutting concerns.** Rather than putting
  every piece of shared preprocessing directly in the Handler, a chain of
  filters, servlet `Filter` objects, ASP.NET Core middleware, or Express
  middleware functions, runs before the Handler proper. This composes Front
  Controller with Chain of Responsibility, see dimension 13, and is how most
  production frameworks actually structure the "shared preprocessing" half of
  the pattern, because it lets each concern, authentication, compression,
  CORS, be added, removed, and reordered independently rather than living as
  one growing method body.
- **Middleware pipeline as a dissolved Front Controller.** In Node with
  Express, and in ASP.NET Core's `Program.cs`, the Handler and the filter
  chain merge into one ordered pipeline of middleware functions terminating in
  a router. There is no separate class called "the front controller," the
  pipeline itself plays that role, and the final routing step plays the
  Dispatcher's role. This is a language- and framework-idiomatic variant
  rather than a different pattern, the structural roles from dimension 5 are
  still present, just expressed as function composition instead of class
  composition.
- **Auto-registered dispatch table.** Rather than a hand-maintained switch or
  map from action name to Command, the route table is built by scanning
  annotated classes at startup, Spring's `@RequestMapping` and ASP.NET Core's
  attribute routing both do this. Each team's Command class carries its own
  route declaration, so no team edits a shared file to register a new action,
  which is the direct fix for the merge-conflict failure mode in dimension 11.
- **One front controller per bounded context in a modular monolith.** Rather
  than one dispatch table for the entire application, each module owns a
  smaller front controller scoped to its own URL prefix, with a thin outer
  router mapping prefixes to modules. This keeps the "God class" failure mode
  from dimension 11 bounded to one module rather than the whole application,
  at the cost of duplicating the shared preprocessing setup once per module
  unless that setup is itself factored into a reusable base.

## 9. Known production uses

Spring's `DispatcherServlet` is documented in its own Javadoc as "a central
dispatcher for HTTP request handlers and controllers," implementing the Front
Controller pattern as the foundation of Spring MVC, where "a central Servlet
provides a shared algorithm for request processing, while actual work is
performed by configurable delegate components," the delegate components being
the `@Controller`-annotated classes that play the Command role from dimension
5 (Spring Framework Reference Documentation, "DispatcherServlet,"
docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html,
verified 2026-08-11).

Symfony routes every request through a single `public/index.php` file, and the
project's own documentation states plainly, "the front controller is a
design pattern, it is a section of code that all requests served by an
application run through," and in the default Symfony project skeleton that
role is taken by `index.php` in the `public/` directory, with routing
performed internally once the front controller has been reached (Symfony
Documentation, "Understanding how the Front Controller, Kernel and
Environments Work Together,"
symfony.com/doc/current/configuration/front_controllers_and_kernel.html,
verified 2026-08-11).

WordPress routes every front-end request through `index.php` as well, using
Apache `.htaccess` rewrite rules, or the equivalent Nginx rules, to send any
URL that does not correspond to a real file on disk to that one entry point,
which then loads `wp-blog-header.php` and resolves the request against the
`WP_Query` and template hierarchy (WordPress Developer Resources, "Apache
HTTPD / .htaccess,"
developer.wordpress.org/advanced-administration/server/web-server/httpd/,
verified 2026-08-11). This physical-front-controller shape is the same one
Core J2EE Patterns describes for PHP-style deployments in dimension 8.

Apache Struts, an early and influential Java MVC framework, implemented Front
Controller through its `ActionServlet` class, whose own Javadoc states it
"provides the 'controller' in the Model-View-Controller (MVC) design pattern
for web applications that is commonly known as 'Model 2,'" and describes its
processing as identifying the target action class from the request URI,
instantiating and caching it, then delegating to it, matching the
Handler-plus-Command split from dimension 5 directly (Apache Software
Foundation, "Class ActionServlet," Apache Struts 1.1 API Documentation,
svn.apache.org/repos/asf/struts/archive/trunk/struts-doc-1.1/api/org/apache/struts/action/ActionServlet.html,
verified 2026-08-11).

Jakarta Faces, the specification formerly known as JavaServer Faces, uses
`FacesServlet` as its single entry point for every JSF-managed request, and
the Apache MyFaces implementation of the Jakarta Faces API documents
`FacesServlet` as implementing `jakarta.servlet.Servlet` directly, mapped
against the application's JSF URL pattern, so that every JSF page request
passes through the same servlet instance before the framework's own
navigation handling selects a view (Apache MyFaces Project, "FacesServlet,"
Apache MyFaces Core 3.0 API Documentation,
svn-eu.apache.org/repos/asf/myfaces/site/publish/core30/myfaces-api/apidocs/jakarta/faces/webapp/FacesServlet.html,
verified 2026-08-11).

A sixth data point worth naming for what it shows rather than for a new
framework, Ruby on Rails' `ActionController` classes are Page Controller at
the per-action layer, as documented in this catalog's Page Controller entry,
yet Rails itself sits on top of Rack, whose entire specification is a single
`call(env)` entry point that every Rack-based Ruby web framework, not only
Rails, is required to implement (Rack Specification, GitHub rack/rack
repository, `SPEC.rdoc`, github.com/rack/rack/blob/main/SPEC.rdoc, verified
2026-08-11). Rails is Page Controller built on top of a Front Controller it
does not itself own, which is the clearest evidence in this catalog that the
two patterns operate at different layers of the same stack rather than being
strict rivals at every layer simultaneously, a nuance dimension 13 returns to.

## 10. Consequences

Positive consequences.

- Cross-cutting behavior, authentication, authorization, internationalization,
  logging, transaction demarcation, is written once and is guaranteed to run
  for every request, because a request that skips the front controller cannot
  reach a handler at all.
- Adding new global behavior, a security header, a rate limit, a feature flag
  gate, is a single edit rather than an edit repeated across every existing
  handler, which directly shortens the time between deciding on a policy and
  having it actually enforced everywhere.
- View selection logic that spans many pages, choosing a mobile template
  family, applying a maintenance-mode splash page, can live in one place
  instead of being duplicated into every page's own logic.
- Operability improves. One log statement at the entry point, tagged with the
  resolved action, gives a single, reliable place to instrument request rate,
  latency, and error rate per action, without relying on every handler
  remembering to emit that log line itself.
- Security review is easier to reason about. An auditor asking "is
  authentication checked before every action" has exactly one method to read,
  rather than forty methods to check individually and hope none was missed.

Negative consequences.

- The Handler, if undisciplined, becomes a single class that every developer
  on the team touches, which turns it into a recurring source of merge
  conflicts as the application and the team both grow, unless registration is
  externalized as described in dimension 8.
- A bug in the shared preprocessing affects every action simultaneously. The
  same centralization that makes a security fix easy to apply everywhere also
  makes a security regression easy to introduce everywhere, in one commit.
- The extra indirection, request through Handler through Dispatcher through
  Command, costs a reader something when tracing exactly what happens for one
  specific URL, compared to a Page Controller where the answer is "read this
  one file."
- If the shared preprocessing does real work, a session store lookup, a
  database-backed locale resolution, that cost is paid by every request,
  including the ones that did not strictly need it, which is a latency tax the
  pattern accepts in exchange for consistency, per dimension 3.
- Testing a Command in true isolation requires either a fake or mock of
  whatever request and response contract the Front Controller defines, rather
  than testing a plain function against plain arguments, which raises the
  fixed cost of writing the first test for a new action, even though it lowers
  the cost of testing the shared preprocessing itself.

## 11. Failure modes and misuse

**Symptom.** The Handler class has grown to several thousand lines with dozens
of nested conditionals branching on the action name, and business logic for
individual actions is interleaved directly inside those branches.
**Cause.** The Dispatcher and Command participants from dimension 5 were never
separated out. All per-action logic was written inline in the Handler because
that was the path of least resistance for the first few actions, and nobody
refactored before the tenth action landed.
**Fix.** Extract each branch into its own Command object implementing a shared
interface, register them in an explicit route table, and reduce the Handler
to shared preprocessing plus a single call to the Dispatcher. This is the
"Service to Worker" combination Core J2EE Patterns names for exactly this
recovery.

**Symptom.** Adding a new page or action requires editing a shared dispatch
file, and that file is the single most frequent source of merge conflicts in
the codebase, according to the team's own version control history.
**Cause.** Route registration is manual and centralized, every team that adds
an action edits the same switch statement or map literal in the same file.
**Fix.** Move registration to each Command's own module, discovered at startup
through annotation scanning, a decorator registry, or a convention-based file
scan, so adding an action means adding a file, not editing a shared one. This
is the direct justification for the auto-registered variant in dimension 8.

**Symptom.** An unhandled exception in one rarely used action, an export
feature nobody has touched in months, brings down the entire site rather than
returning an error page for just that request.
**Cause.** The Front Controller has no per-command exception boundary. An
uncaught exception propagates out of the Dispatcher's call into the servlet
container or process runtime, which may treat it as fatal depending on the
runtime, or which may leave shared state, a partially updated session
attribute, in an inconsistent state for the next request on the same thread
or worker.
**Fix.** Wrap the Dispatcher's call to each Command in an explicit
try-catch boundary at the Front Controller level, converting any uncaught
exception into a controlled error response, and treat "no Command failure may
escape past the Front Controller" as an invariant enforced by a test, not a
convention hoped for.

**Symptom.** Under load, response times for every action degrade together,
even though monitoring shows only one downstream dependency, say a slow
third-party API called by one specific action, actually degraded.
**Cause.** The Front Controller dispatches every Command onto one shared
thread pool or connection pool with no isolation between actions, so a slow
Command exhausts the shared resource and starves every other action's
requests, a classic resource-exhaustion failure with no fault isolation
between unrelated actions.
**Fix.** Apply a bulkhead per Command or per action category, a dedicated
thread pool or a request timeout scoped to that specific Command, so that one
action's degradation cannot consume the resource every other action also
depends on.

**Symptom.** A security audit or a penetration test finds one endpoint that
skips authentication entirely, even though the team believed every request
passed through the Front Controller's authentication check.
**Cause.** A developer added a new handler through a path that bypasses the
shared entry point, a second servlet mapped directly to its own URL pattern
outside the Front Controller's wildcard mapping, or a static file directory
that the web server serves before the request ever reaches the application.
The Front Controller's guarantee only holds for requests that physically
reach it, and nothing enforced that every new endpoint was registered through
it rather than added beside it.
**Fix.** Enforce a single physical entry point at the infrastructure level, a
web server or reverse proxy configuration that denies any URL not routed
through the Front Controller's own mapping, and add an automated endpoint
enumeration audit that fails the build if a new servlet or route mapping is
registered outside the recognized dispatch mechanism.

## 12. Trade-off matrix

| Force | Front Controller | Page Controller | Mediator (GoF) | API Gateway |
|---|---|---|---|---|
| Coupling of cross-cutting logic | Centralized in one Handler, low duplication | Duplicated per page unless factored into a shared base | Centralized among a fixed set of collaborating objects, not requests | Centralized across independently deployed services |
| Consistency guarantee | Strong, enforced at the single entry point | Weak, depends on every page remembering shared logic | Strong within the object set the mediator knows about | Strong across services, weak within a service's own internal handlers |
| Latency overhead | One extra dispatch hop plus shared preprocessing on every request | None, request goes straight to the owning page | One extra call through the mediator per interaction | A network hop to the gateway plus the hop to the backend |
| Operability, single view of all traffic | Native, one log point per request | Requires log aggregation across many independent handlers | Not applicable, not a request-handling pattern | Native, and usually the primary reason gateways are adopted |
| Team scalability of the shared entry point | Sacrificed unless registration is externalized, see dimension 11 | Favoured, each page is edited independently with no shared file | Sacrificed as the mediator accumulates knowledge of every collaborator | Favoured for backend teams, sacrificed for the gateway-owning team |
| Failure isolation between requests | Requires deliberate bulkheading, see dimension 11 | Native, one page's crash does not touch another's process path | Native within the mediated object set, external to request handling | Native across services, a gateway can circuit-break per backend |

Mediator is included here because both patterns centralize communication that
would otherwise be scattered, but Mediator centralizes collaboration between a
fixed, known set of in-memory objects, while Front Controller centralizes
handling of an open-ended stream of external requests, which is why Mediator
composes at the domain layer and Front Controller composes at the boundary of
a system.

## 13. Related and incompatible patterns

**Page Controller.** The direct architectural alternative for who owns the
per-request entry point. Where Front Controller places one object between
every request and its handler, Page Controller gives each page or action its
own independent entry point with no shared funnel. The two are marked
incompatible in this catalog at the layer where the choice is made, an
application picks one strategy for owning its request-handling entry points,
not both simultaneously for the same set of requests, because running both at
once means some requests get the consistency guarantee and others do not,
which defeats the reason to adopt Front Controller in the first place. This is
not a contradiction with the fact that a Front Controller dispatches to
Command objects that look, superficially, like independent per-action
handlers, the difference is that those Commands do not own the entry point or
the shared preprocessing, the Front Controller does, which is precisely what
distinguishes them from true Page Controllers.

**Command (Gang of Four).** The participant that plays the "Command" role in
dimension 5 is a direct application of the GoF Command pattern, an object that
encapsulates a request as an object with a uniform `execute` method, so the
Dispatcher can hold a collection of them and invoke any one without knowing
its concrete type. Front Controller is, structurally, Command applied
specifically to HTTP or equivalent inbound requests, with a Handler and
Dispatcher added around it to solve the web-specific problem of routing and
shared preprocessing that a plain Command catalog does not address on its
own.

**Chain of Responsibility (Gang of Four).** Composes with Front Controller at
the shared-preprocessing stage. A chain of filters or middleware, each
deciding whether to handle a cross-cutting concern and pass the request along
or short-circuit it, is the natural shape for authentication, compression, and
similar concerns, and is how most production frameworks implement the
"Handler does shared preprocessing" half of the structure, per the filter-chain
variant in dimension 8, rather than writing it as one large method.

**Mediator (Gang of Four).** Related by the shared instinct to centralize
what would otherwise be scattered, but distinct in scope, as covered in
dimension 12. Worth naming explicitly because the two are frequently confused
in casual conversation, "doesn't Front Controller just mediate between the
pages," when in fact Mediator addresses collaboration between a known,
bounded set of domain objects, while Front Controller addresses an open-ended
stream of external requests arriving over time.

**Application Controller.** A distinct pattern, also from Fowler's Web
Presentation group, that factors the "which command handles this, and which
view comes next" decision out of the Front Controller's Dispatcher into its
own dedicated object, separate from both the Handler and the individual
Commands. Front Controller and Application Controller compose deliberately,
when the Dispatcher's routing logic grows complex enough to need its own state
machine, for a multi-step wizard flow for example, extracting it into an
Application Controller keeps that complexity from bloating the Dispatcher,
which is one direct route out of the "God class" failure mode in dimension 11.

**Dispatcher View and Service to Worker.** Two named macro-patterns from Core
J2EE Patterns, not separate structures but names for common combinations of
Front Controller with View Helper. Service to Worker performs dispatch and
view selection before any significant processing, favoring simpler
controllers with more logic in helpers. Dispatcher View performs the bulk of
processing first and defers view selection until after, favoring more
sophisticated controllers. Both are Front Controller plus View Helper wearing
a name for a specific division of labor between the two, worth knowing because
practitioner discussion of "Front Controller" in J2EE-era literature often
means one of these two specific combinations rather than the bare pattern.

**API Gateway.** The distributed-systems descendant of Front Controller,
applying the same "one guaranteed entry point for shared concerns" idea across
independently deployed services rather than within one process's handler set.
Covered as incompatible in dimension 4's non-applicability list at the
in-process level, once an application has split into services behind a
gateway, adding a second, redundant, in-process front controller inside one
of those services for the same cross-cutting concerns the gateway already
enforces duplicates effort without adding a guarantee the gateway did not
already provide for traffic entering that service from outside.

## 14. Refactoring path in and out

Refactoring in, from a set of independent Page Controllers to a Front
Controller, proceeds incrementally rather than as one large rewrite, using a
strangler-fig approach so the application stays deployable at every step.

1. Identify the cross-cutting behavior currently duplicated, or missing in
   some handlers, across the existing Page Controllers. Write down the exact
   list, this becomes the specification for the new Handler's shared
   preprocessing.
2. Introduce a new physical entry point, a servlet mapped to a wildcard
   pattern, or a new `index.php` behind a URL rewrite, that at first does
   nothing but forward every request unchanged to whichever existing Page
   Controller currently handles that URL. At this step the Front Controller
   exists but performs no shared logic yet, and the application's behavior is
   unchanged, which is the safety property that makes the next steps low risk.
3. Move the cross-cutting behavior identified in step one into the new
   Handler, one concern at a time, starting with the concern that is easiest
   to verify has identical behavior before and after, typically logging.
   After each concern is moved, remove that concern's duplicated logic from
   the existing Page Controllers and confirm behavior is unchanged.
4. As each existing Page Controller's remaining logic is reduced to genuinely
   page-specific work, wrap it in a Command object implementing the shared
   interface the new Dispatcher expects, and register it in the route table
   rather than leaving it addressable by its own independent URL mapping.
5. Once every former Page Controller has been converted to a registered
   Command, remove the old direct URL mappings entirely, so the Front
   Controller's wildcard mapping is the only path any request can take into
   the application, closing the bypass failure mode from dimension 11.

Refactoring out, when a Front Controller has outgrown its usefulness, is the
mirror image and applies in two distinct situations. If the Handler has become
a team-scaling bottleneck, per the merge-conflict symptom in dimension 11, the
first move is not to remove the pattern but to externalize registration,
dimension 8's auto-registered variant, which frequently resolves the actual
pain without abandoning the structure. If instead the application has split
into genuinely independent services, the correct move is to extract an API
Gateway as its own deployed component in front of those services, and let each
service's internal request handling be as simple as it needs to be, which may
mean removing the in-process Front Controller from services that no longer
need to duplicate concerns the gateway now owns.

## 15. Testing and verification

Testing a Front Controller separates cleanly into three layers, and each layer
gets easier or harder in a specific, predictable way once the pattern is in
place.

The Command objects, once genuinely extracted per dimension 5, are the
easiest thing in the system to test, because each one is a small object with
one method and a narrow, explicit contract. A unit test constructs the
Command directly, supplies a fake request, and asserts on the returned view
name and model data, with no need to boot the Handler, the Dispatcher, or any
web server at all. This is a direct benefit of the pattern, logic that used to
live inline in a giant conditional, hard to isolate, becomes trivially
isolatable once extracted.

The Dispatcher's route table is tested as data rather than as behavior. A
parameterized test iterates every registered action name and asserts it
resolves to the expected Command class, which catches a route accidentally
left unregistered, or two routes accidentally mapped to the same action name,
far earlier than an integration test would.

The Handler's shared preprocessing is tested through contract tests that are
independent of any specific Command. A request with no valid session is
rejected regardless of which action it targets, and a request in an
unsupported locale falls back to the default regardless of which action it
targets. These tests exercise the Front Controller directly, with a minimal
stub Command registered purely so the test can observe whether control ever
reached it, which is the observable signal that the shared check ran, or
correctly did not, before the Command was invoked.

What genuinely gets harder is the full request-to-response integration test,
because it now requires whatever request and response fakes the framework or
the application's own Front Controller contract defines, a `MockHttpServletRequest`
in a Spring MVC test, or an equivalent test double for a hand-rolled
implementation. Teams that skip building this fake, and instead only ever test
against a real running server, pay for that gap with slower test suites and a
weaker signal about where in the stack a failure actually occurred.

## 16. Observability signals

The single entry point is the pattern's biggest observability gift, and it
should be spent deliberately rather than left implicit. At minimum, the
Handler should attach a request identifier and the resolved action name to
every log line and trace span for that request, at the earliest possible
point in dispatch, so that correlating logs across the shared preprocessing
and the Command's own logic is a matter of filtering on one identifier rather
than reconstructing a timeline from timestamps.

A per-action request counter and latency histogram, tagged by the resolved
action name, gives a dashboard that answers which action is slow and which
action's error rate just changed without needing to instrument each Command
separately, because the Front Controller is the one place that already knows
both which action was requested and how long the whole request took.

A healthy Front Controller shows a roughly uniform latency distribution across
actions once request-specific work is excluded from the comparison, a small,
stable p95 for the shared preprocessing itself, and an unmapped-action or
404-from-dispatch counter that stays near zero. An unhealthy one shows one of
two distinct shapes. Either one action's error rate or latency climbs while
every other action stays flat, which points at the resource-isolation failure
in dimension 11, or the unmapped-action counter sustains a rise, which points
at route table drift, a client calling an action that was renamed or removed
without a compatibility redirect being added.

## 17. Security and privacy implications

The centralization that makes Front Controller valuable for security review
also makes it a single, high-value target. Because authentication,
authorization, and input validation for the entire application funnel through
one class, a defect in that one class is a defect in every action
simultaneously, which is a materially different risk profile from a defect in
one Page Controller, whose blast radius is one page. The correct response is
not to avoid centralizing these checks, avoiding centralization is what
produced the "one endpoint quietly skips auth" failure this pattern exists to
prevent, but to treat the Handler's shared preprocessing as the single highest
priority code in the application for review, static analysis, and test
coverage, precisely because its blast radius is total.

The dispatch table must fail closed. An action name that does not match any
registered Command should resolve to a 404 by default, never to an implicit
fallthrough that grants access to something unintended, and this default
should be covered by an explicit test asserting that an unrecognized action
never reaches any Command handler.

Centralized request logging, one of the pattern's clearest operational
benefits per dimension 16, is also a place where a single mistake now affects
every logged request rather than one handler's worth of logs. A Front
Controller that logs full request bodies or headers for debugging purposes
without a redaction step will log credentials, session tokens, or personal
data from every single action that happens to pass a sensitive value in its
request, which is a wider exposure than the same mistake made inside one
individual Page Controller, and the fix is the same discipline applied once,
at the one place logging happens, rather than repeated per handler, redact
known-sensitive header and parameter names before any request detail is
written to a log.

Finally, because the pattern guarantees every request passes through one
choke point, that guarantee only holds if the infrastructure itself enforces
that no request can reach a handler by any other physical path, per the bypass
failure mode in dimension 11. A web server configuration, or a reverse proxy
rule, that allows a request to reach a handler class directly, bypassing the
Front Controller's own URL mapping, silently invalidates every security
property this pattern was adopted to provide, which makes the infrastructure
configuration itself part of the pattern's actual security boundary, not
merely an operational detail outside it.

## 18. References

- Deepak Alur, John Crupi, Dan Malks, *Core J2EE Patterns. Best Practices and
  Design Strategies*, 2nd edition, Prentice Hall, 2003, Presentation Tier
  Patterns, "Front Controller."
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2003, pages 344 to 349, "Front Controller."
- Martin Fowler, "Front Controller,"
  https://martinfowler.com/eaaCatalog/frontController.html, verified
  2026-08-11.
- Spring Framework Reference Documentation, "DispatcherServlet,"
  https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html,
  verified 2026-08-11.
- Symfony Documentation, "Understanding how the Front Controller, Kernel and
  Environments Work Together,"
  https://symfony.com/doc/current/configuration/front_controllers_and_kernel.html,
  verified 2026-08-11.
- WordPress Developer Resources, "Apache HTTPD / .htaccess," Advanced
  Administration Handbook,
  https://developer.wordpress.org/advanced-administration/server/web-server/httpd/,
  verified 2026-08-11.
- Apache Software Foundation, "Class ActionServlet," Apache Struts 1.1 API
  Documentation,
  https://svn.apache.org/repos/asf/struts/archive/trunk/struts-doc-1.1/api/org/apache/struts/action/ActionServlet.html,
  verified 2026-08-11.
- Apache MyFaces Project, "FacesServlet," Apache MyFaces Core 3.0 API
  Documentation,
  https://svn-eu.apache.org/repos/asf/myfaces/site/publish/core30/myfaces-api/apidocs/jakarta/faces/webapp/FacesServlet.html,
  verified 2026-08-11.
- Rack, "Rack Specification," `SPEC.rdoc`,
  https://github.com/rack/rack/blob/main/SPEC.rdoc, verified 2026-08-11.

## Code examples

The four examples below implement the same shape, a Handler that
authenticates the request, a Dispatcher holding a route table keyed by action
name, and a Command interface that individual actions implement, so the
structural roles from dimension 5 can be compared line for line across
languages.

### Java

```java
import java.util.HashMap;
import java.util.Map;

interface Command {
    String execute(Map<String, String> params);
}

final class Dispatcher {
    private final Map<String, Command> commands = new HashMap<>();

    void register(String action, Command command) {
        commands.put(action, command);
    }

    String dispatch(String action, Map<String, String> params) {
        Command command = commands.get(action);
        if (command == null) {
            return "view:404";
        }
        return "view:" + command.execute(params);
    }
}

final class FrontController {
    private final Dispatcher dispatcher = new Dispatcher();

    void register(String action, Command command) {
        dispatcher.register(action, command);
    }

    String handle(String action, Map<String, String> params) {
        authenticate(params);
        return dispatcher.dispatch(action, params);
    }

    private void authenticate(Map<String, String> params) {
        if (!params.containsKey("session")) {
            throw new IllegalStateException("no session");
        }
    }
}

final class ShowInvoiceCommand implements Command {
    public String execute(Map<String, String> params) {
        return "invoice-detail";
    }
}

public class FrontControllerDemo {
    public static void main(String[] args) {
        FrontController front = new FrontController();
        front.register("showInvoice", new ShowInvoiceCommand());

        Map<String, String> params = new HashMap<>();
        params.put("session", "abc123");
        System.out.println(front.handle("showInvoice", params));
    }
}
```

### TypeScript

```typescript
type Params = Record<string, string>;

interface Command {
  execute(params: Params): string;
}

class Dispatcher {
  private readonly commands = new Map<string, Command>();

  register(action: string, command: Command): void {
    this.commands.set(action, command);
  }

  dispatch(action: string, params: Params): string {
    const command = this.commands.get(action);
    if (!command) {
      return "view:404";
    }
    return "view:" + command.execute(params);
  }
}

class FrontController {
  private readonly dispatcher = new Dispatcher();

  register(action: string, command: Command): void {
    this.dispatcher.register(action, command);
  }

  handle(action: string, params: Params): string {
    this.authenticate(params);
    return this.dispatcher.dispatch(action, params);
  }

  private authenticate(params: Params): void {
    if (!params.session) {
      throw new Error("no session");
    }
  }
}

class ShowInvoiceCommand implements Command {
  execute(_params: Params): string {
    return "invoice-detail";
  }
}

const front = new FrontController();
front.register("showInvoice", new ShowInvoiceCommand());

const result = front.handle("showInvoice", { session: "abc123" });
console.log(result);
```

### Python

```python
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class Request:
    action: str
    session: Optional[str] = None
    params: Dict[str, str] = field(default_factory=dict)


class Dispatcher:
    def __init__(self) -> None:
        self._commands: Dict[str, Callable[[Request], str]] = {}

    def register(self, action: str, command: Callable[[Request], str]) -> None:
        self._commands[action] = command

    def dispatch(self, request: Request) -> str:
        command = self._commands.get(request.action)
        if command is None:
            return "view:404"
        return "view:" + command(request)


class FrontController:
    def __init__(self) -> None:
        self._dispatcher = Dispatcher()

    def register(self, action: str, command: Callable[[Request], str]) -> None:
        self._dispatcher.register(action, command)

    def handle(self, request: Request) -> str:
        self._authenticate(request)
        return self._dispatcher.dispatch(request)

    def _authenticate(self, request: Request) -> None:
        if not request.session:
            raise PermissionError("no session")


def show_invoice(request: Request) -> str:
    return "invoice-detail"


front = FrontController()
front.register("showInvoice", show_invoice)

result = front.handle(Request(action="showInvoice", session="abc123"))
print(result)
```

### Go

```go
package main

import (
	"errors"
	"fmt"
)

type Request struct {
	Action  string
	Session string
	Params  map[string]string
}

type Command func(r Request) string

type Dispatcher struct {
	commands map[string]Command
}

func NewDispatcher() *Dispatcher {
	return &Dispatcher{commands: make(map[string]Command)}
}

func (d *Dispatcher) Register(action string, c Command) {
	d.commands[action] = c
}

func (d *Dispatcher) Dispatch(r Request) string {
	command, ok := d.commands[r.Action]
	if !ok {
		return "view:404"
	}
	return "view:" + command(r)
}

type FrontController struct {
	dispatcher *Dispatcher
}

func NewFrontController() *FrontController {
	return &FrontController{dispatcher: NewDispatcher()}
}

func (f *FrontController) Register(action string, c Command) {
	f.dispatcher.Register(action, c)
}

func (f *FrontController) Handle(r Request) (string, error) {
	if r.Session == "" {
		return "", errors.New("no session")
	}
	return f.dispatcher.Dispatch(r), nil
}

func showInvoice(r Request) string {
	return "invoice-detail"
}

func main() {
	front := NewFrontController()
	front.Register("showInvoice", showInvoice)

	req := Request{Action: "showInvoice", Session: "abc123"}
	result, err := front.Handle(req)
	if err != nil {
		panic(err)
	}
	fmt.Println(result)
}
```
