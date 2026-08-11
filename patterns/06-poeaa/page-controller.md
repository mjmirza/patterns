---
name: Page Controller
slug: page-controller
family: 06-poeaa
category: Web Presentation
aliases: [Page-per-Controller, Action Servlet (loosely, when misapplied)]
first_described: "Fowler 2003"
maturity: canonical
related: [front-controller, template-view, transform-view, application-controller, transaction-script, model-view-controller]
incompatible_with: [front-controller]
verified: 2026-08-11
---

# Page Controller

## 1. Name, aliases, and lineage

The canonical name is Page Controller. Martin Fowler named and catalogued it
in "Patterns of Enterprise Application Architecture" (Addison-Wesley, 2003),
placing it among the Web Presentation patterns alongside Front Controller,
Template View, and Transform View. Fowler's own catalog summary states the
pattern is "An object that handles a request for a specific page or action
on a Web site" (Martin Fowler, "Page Controller,"
https://martinfowler.com/eaaCatalog/pageController.html, verified 2026-08-11). Fowler
adds that the controller "may be the page itself, as it often is in server
page environments, or it may be a separate object that corresponds to that
page," which is the earliest and still most precise statement of the two
implementation shapes the pattern takes, the controller merged into the view
template, or the controller as a distinct object.

The pattern is older than Fowler's name for it. CGI scripts in the early
1990s, where a single executable file both parsed an incoming HTTP request
and printed an HTML response, are Page Controller before the term existed.
Fowler is explicit that he is naming an existing, widely practiced idiom
rather than inventing a new technique, which is why the maturity here is
canonical rather than emerging. There is no serious naming dispute in the
literature. Some Java web frameworks of the early 2000s, notably early
Struts, are sometimes loosely called "Page Controller frameworks" by
practitioners, but this is imprecise. Struts implements Front Controller (a
single ActionServlet dispatches every request) with a per-action Action
class that plays a role closer to Page Controller within that dispatch. The
distinction between the two patterns, and where hybrids sit, is covered in
dimension 13.

## 2. Problem and context

A web application must translate an incoming HTTP request into a specific
piece of server-side behavior and a specific response. A team building such
an application quickly reaches the question of where that translation lives.
The most direct answer, and the one that predates any framework, is to give
every distinct URL, or every distinct kind of request, its own piece of code
that owns the full request-to-response lifecycle for that one case, reading
the request's parameters and headers, deciding what domain logic to invoke,
gathering the data the response needs, and handing that data to whatever
renders the page.

This is the context Page Controller answers. It is a natural fit when the
site's structure maps closely onto its URL structure, one URL, one page, one
piece of behavior, which was the dominant shape of the web in the 1990s and
remains the dominant shape of a great many server-rendered sites today. A
`/products/show` request is handled by something that only knows about
showing a product. A `/checkout/confirm` request is handled by something
that only knows about confirming a checkout. Nothing routes between them
except the web server or servlet container's own URL-to-handler mapping,
because there is no separate dispatching layer inside the application. The
pattern's defining trait is the absence of a shared entry point. Each page's
controller is independently reachable and independently deployable in the
sense that adding a new page means adding a new controller, not modifying an
existing one.

## 3. Forces

**Directness against duplication.** A Page Controller for each page keeps
the request-handling logic for that page in one place, easy to read start to
finish. But behavior that is common to many pages, authentication checks, a
shared layout, logging, internationalization, tends to get copied into every
controller unless deliberately factored out, because there is no single
place that every request is guaranteed to pass through.

**Deployability against centralized control.** Because each page's handler
is independently registered with the web server (a servlet mapping, a file
on disk that a URL rewrite rule resolves to, a class the routing table
names), a team can add, remove, or redeploy one page's behavior without
touching any other page's configuration. This is valuable in large teams
working on unrelated pages in parallel. It sacrifices a single place to
apply a cross-cutting policy change, since that policy has to be threaded
through every controller or through a shared base class or filter chain.

**Simplicity against uniform request lifecycle.** A Page Controller can be
as simple as a single function, and for the huge majority of pages on a
typical site (a static informational page, a simple form submission) that
simplicity is a genuine win, no framework indirection to trace through. The
sacrifice is architectural symmetry, since a Front Controller-based system
gives every request the exact same processing pipeline by construction,
while a pure Page Controller system gives every request whatever pipeline
that page's author happened to write, which invites drift.

**Cognitive load against dispatch indirection.** A developer debugging a
specific page's misbehavior with Page Controller can go straight to the file
or class that owns that page, no dispatcher configuration to trace. Fowler
observes this directly. With Page Controller "you can see at a glance in
your Web server's configuration file which URLs go to which handlers"
(Martin Fowler, "Page Controller," https://martinfowler.com/eaaCatalog/pageController.html,
verified 2026-08-11), a lower-cognitive-load path than tracing a Front
Controller's runtime routing table. The cost lands on the team once the
number of pages grows into the hundreds and the same handling logic starts
appearing, copied, across dozens of files.

## 4. Applicability and non-applicability

Reach for Page Controller when the site is structured around a relatively
stable, page-oriented URL space, when different pages genuinely need
different, largely independent processing, when the web server or servlet
container already provides adequate URL-to-handler mapping (so the
application does not need to build its own routing layer), and when the team
is small enough, or disciplined enough, to keep shared behavior in a common
base class or filter without it silently diverging per page. It is also the
natural fit for server-page technologies (classic ASP, JSP, PHP, ERB
templates) where the page itself contains both the logic and the markup,
because in that environment the page-per-controller structure comes for
free rather than requiring extra design work.

Do not reach for it when the application has many pages that share a large
amount of cross-cutting logic (authentication, authorization, localization,
audit logging, request-scoped transaction demarcation), because that logic
either gets duplicated across every controller or has to be extracted into a
disciplined-but-fragile inheritance hierarchy of base controllers; Front
Controller centralizes this concern by construction and is the better fit.
Do not reach for it when the URL space itself needs to be computed or
composed at runtime (deep hierarchical resources, content addressed by a
database-driven slug taxonomy, an API with dozens of resource types and
verbs following a single convention), because per-page registration does not
scale to a URL space that is not enumerable in advance; Front Controller with
a routing table, or a resource-oriented dispatcher, fits better. Do not
reach for it inside a single-page application whose server exposes a JSON
API rather than rendering pages, because the pattern is specifically about
owning the page-rendering lifecycle, which does not exist in that
architecture; a REST or RPC controller layer, still often called
"controller" by the framework but structurally closer to Command or a thin
Front Controller action, is the better fit there.

## 5. Structure

**Controller** owns the full lifecycle for one page or one closely related
family of actions on that page, reading the incoming request's parameters
and headers, invoking whatever domain or service logic the page needs, and
choosing or preparing the view that will render the result. It is the thing
a URL is mapped to directly, no intervening dispatcher inside the
application.

**Request and Response** are the platform-provided objects (an HTTP request
and response, or the framework's wrapper around them) the controller reads
parameters and headers from, and writes status codes, headers, and a body
to, or hands off to a view for rendering.

**View** is the presentation artifact, a template, a JSP, an ERB file, a
render function, that the controller selects and supplies with data once its
own work is done. Fowler treats View selection as part of the controller's
job but the view's own rendering logic as a separate concern, most often
Template View or Transform View.

**Handler registration** is the mechanism, external to the application's own
code, that maps a URL or a request pattern to a specific controller
instance or class, most commonly a servlet container's `web.xml` or
`@WebServlet` annotation, a web server's URL-rewrite or file-path
convention, or a thin routing table that is nonetheless one-to-one with
pages rather than a general-purpose dispatcher.

**Shared base controller (optional but common)** is a superclass or mixin
that several page controllers inherit from to share genuinely common
behavior, most often authentication checks or a common way of loading
session state, and it is the pattern's usual answer to the duplication force
named in dimension 3, though it is not part of Fowler's original structure
and is an implementation choice teams add on top of the pattern.

## 6. ASCII structure diagram

```text
                 URL / request path
                        |
                        v
        +---------------------------------+
        |  Handler registration            |
        |  (servlet mapping, URL rewrite,   |
        |   or 1:1 routing table)           |
        +---------------------------------+
                        |
      -------------------------------------------
      |                 |                 |
      v                 v                 v
+-----------+     +-----------+     +-----------+
| Page       |     | Page       |     | Page       |
| Controller |     | Controller |     | Controller |
| /products  |     | /checkout  |     | /account   |
+-----------+     +-----------+     +-----------+
      |                 |                 |
      v                 v                 v
  domain / service logic invoked by each controller
      |                 |                 |
      v                 v                 v
+-----------+     +-----------+     +-----------+
|   View     |     |   View     |     |   View     |
| (template) |     | (template) |     | (template) |
+-----------+     +-----------+     +-----------+
```

Contrast with Front Controller, where every URL passes through a single
dispatcher before reaching a per-page handler. Page Controller has no such
shared box, each controller is registered independently.

## 7. Dynamics

```text
1. HTTP request arrives at the web server or servlet container.
2. Handler registration resolves the request path directly to one
   Page Controller instance or class, with no intervening dispatch step
   inside the application.
3. The controller reads request parameters, headers, session state,
   and path segments needed to understand what was asked for.
4. The controller invokes whatever domain, service, or data-access
   logic the page requires, possibly several calls, possibly none
   for a purely static page.
5. The controller decides which view should render the result and
   what data that view needs (a model, in the loose sense).
6. The controller hands control to the view, either by forwarding
   the request (server-side include or template render) or by
   writing the response body itself if it is also the page.
7. The view renders using the data the controller supplied.
8. The response is returned to the client.

   Error path. If step 4 raises a domain error, the controller
   catches it and chooses an error view or redirect rather than
   letting the exception propagate to a generic handler, because
   there is no guaranteed shared error-handling layer to catch it.
```

## 8. Implementation variants

**Merged controller and view.** The controller logic lives directly inside
the page template, for example a JSP with embedded Java scriptlets, a
classic ASP page with inline VBScript, or a PHP file that both queries the
database and prints HTML. Fowler names this as one of the two shapes
explicitly. It is the simplest to write for a small page and the hardest to
keep clean as the page grows, because there is no structural boundary
preventing markup and logic from interleaving.

**Separate controller object, page as pure view.** The controller is a
distinct class (a servlet, an ASP.NET code-behind class, a Rails controller
action) that does no rendering itself and instead populates a model or a
set of request attributes, then forwards to a template that only renders.
This is the shape that scales better and is what most production frameworks
converge on even when they nominally still call it Page Controller.

**Controller per action rather than strictly per page.** Many real systems
relax "one controller per page" to "one controller class per closely related
group of pages or actions," most visibly ASP.NET MVC and Rails, where a
single controller class exposes several action methods and each action
plays the Page Controller role for one specific request, while the class as
a whole groups related actions the way a resource groups related verbs.
Fowler anticipates this relaxation in the book text, describing multi-method
controllers as a legitimate variation rather than a different pattern.

**Base controller inheritance.** A common ancestor class implements shared
behavior (session validation, common headers, exception translation) and
every page controller extends it, overriding a single template method (an
abstract `handleRequest`, `doGet`, or similar) to supply page-specific logic.
This is the most common answer in practice to the duplication force from
dimension 3, and it reappears independently across nearly every Page
Controller implementation examined for this entry.

## 9. Known production uses

ASP.NET Web Forms compiles every `.aspx` file into a class that derives from
`System.Web.UI.Page`, which itself derives from `System.Web.UI.TemplateControl`
and implements `System.Web.IHttpHandler`. Each compiled Page class is the
controller for exactly one page and owns that page's lifecycle events
(`Page_Load`, `Page_PreRender`, and the rest), matching Fowler's structure
precisely (Microsoft, "Page Class (System.Web.UI)," Microsoft Learn,
https://learn.microsoft.com/en-us/dotnet/api/system.web.ui.page?view=netframework-4.8.1,
verified 2026-08-11).

The Jakarta Servlet specification's `HttpServlet` class, mapped to a URL
pattern via a `@WebServlet` annotation or a `web.xml` servlet-mapping entry,
is the classic Java example of the pattern. A subclass overrides `doGet` or
`doPost`, reads the `HttpServletRequest`, and forwards to a JSP for
rendering, with each servlet independently registered against its own URL
pattern and no shared dispatching servlet required by the specification
itself (Eclipse Foundation, Jakarta Servlet 4.0 specification,
`https://jakarta.ee/specifications/servlet/4.0/apidocs/javax/servlet/http/httpservlet`,
verified 2026-08-11).

Ruby on Rails controller actions implement the pattern at the per-action
granularity described in dimension 8. A `ProductsController#show` method
owns the full request lifecycle for that one action, reading params,
loading the record, and rendering a view, and the Rails routing layer maps
URLs to these controller-action pairs one to one rather than through a
general-purpose front-end dispatch object that the application itself
defines (Ruby on Rails Guides, "Action Controller Overview,"
https://guides.rubyonrails.org/action_controller_overview.html, retrieved from
Rails project documentation, verified 2026-08-11).

## 10. Consequences

Positive. Each page's behavior is easy to locate, read start to finish, and
reason about in isolation, because nothing else in the application is
required to understand it. Adding a new page is additive, a new file or
class plus a registration entry, and does not risk modifying behavior for
any existing page. The mapping from URL to code is often visible directly in
configuration (a servlet-mapping element, a routes file entry), which
shortens the path from "which URL is broken" to "which file handles it."
Server-page technologies let the simplest pages be extremely small, with no
framework machinery in between the request and the response.

Negative. Cross-cutting concerns, authentication, logging, localization,
consistent error handling, have no single enforcement point and tend to
duplicate across controllers unless a disciplined base-class hierarchy is
maintained, and even then the discipline itself is a maintenance cost.
Testing an individual page controller in isolation from the web container
can be awkward when the controller reads directly from a servlet request
object rather than a decoupled parameter set, because the test then needs a
mock of the container's API surface. As a site grows past a few dozen pages,
the sheer number of independently registered handlers becomes its own
navigation problem, the opposite failure of the "one shared dispatcher to
reason about" property Front Controller offers. Pages that need to compose
sub-behaviors, a checkout flow spanning several steps with shared state,
tend to accrete session-management logic inside individual page controllers
rather than in one coordinating place.

## 11. Failure modes and misuse

**Symptom.** A security check (an authentication or authorization gate) is
present on most pages but missing on one newly added page. **Cause.** The
check lives copy-pasted into each controller's beginning rather than in a
shared, enforced location, and the new controller's author either forgot to
copy it or copied an outdated version. **Fix.** Extract the check into a
servlet filter, an ASP.NET HTTP module, a Rails `before_action` on a shared
base controller, or an equivalent mechanism the container enforces
regardless of whether the controller author remembers to call it. This is
frequently the point where a team decides to migrate toward Front Controller
instead, per dimension 14.

**Symptom.** The same three or four lines of code (loading the current
user from session, setting a common response header, formatting a date the
same way) appear, subtly different, in a large number of controllers, and a
bug fix in one copy does not propagate to the others. **Cause.** No shared
base controller or utility layer was ever established, or one exists but new
controllers are being written without extending it. **Fix.** Introduce or
enforce a common base controller and move the duplicated logic there once.
This is a mechanical refactor (Extract Superclass, then Pull Up Method) with
low risk once the duplication is identified.

**Symptom.** Business logic (validation rules, calculations, decisions about
what to show) is embedded directly inside the controller or, in merged
implementations, inside the page template itself, and the same rule has to
be re-verified or re-implemented for a second entry point (an API, a batch
job) that needs the same logic. **Cause.** Page Controller only prescribes
where request handling lives, not where domain logic lives, and it is easy
to let the two collapse into the same object when the controller is the only
consumer of that logic at first. **Fix.** Extract the domain logic into a
Transaction Script or a Domain Model object that the controller calls, so a
future second entry point can call the same object without duplicating
the rule. Fowler's own broader argument in the book is that Page Controller
should be a thin coordinating layer over a separate domain logic layer, not
a place where domain logic itself is written.

**Symptom.** A merged controller-and-view page (a JSP full of scriptlets, a
large PHP file) becomes difficult for a designer to edit without breaking
functionality, or difficult for a developer to edit without breaking
markup. **Cause.** The merged variant from dimension 8 was chosen for a page
whose complexity outgrew what that variant tolerates well. **Fix.** Split
the page into a separate controller object and a pure view template
(Fowler's second variant), moving all logic out of the template. This is the
in-pattern refactor covered in dimension 14, distinct from migrating away
from Page Controller entirely.

## 12. Trade-off matrix

| Force | Page Controller | Front Controller | Transaction Script (as the sole layer, no separate controller) |
|---|---|---|---|
| Cross-cutting concern enforcement | Weak by default; relies on shared base class or filter | Strong; single entry point applies policy uniformly | Not applicable; no request-handling layer exists to enforce anything |
| Directness for a small, page-oriented site | High; a page's handler is easy to find | Lower; requires tracing a routing table | High for the logic itself, but conflates request handling with the script |
| Scalability of the URL space | Poor for large, dynamic, or resource-style URL spaces | Good; a routing table can express hierarchical or parameterized routes | Not applicable |
| Independent deployability of one page's behavior | High; adding a page does not touch existing registrations | Lower; often requires updating a central routing configuration | High, but at the cost of duplicating request-parsing per script |
| Testability in isolation from the container | Depends on implementation; poor if the controller reads the raw request object directly | Depends similarly, but a well-factored front controller often normalizes the request before dispatch | Poor; the script usually mixes I/O and logic |

## 13. Related and incompatible patterns

**Front Controller** is the pattern Page Controller is most often compared
and contrasted against, and Fowler places them side by side deliberately.
Front Controller funnels every request through one shared object before
dispatching to page-specific logic, which is the direct answer to Page
Controller's weak cross-cutting enforcement, at the cost of an extra layer
of indirection. The two are architecturally mutually exclusive at the level
of whether there is one shared entry point for every request or not, which
is why this entry lists Front Controller as incompatible, though many real
frameworks blend the two by using a thin Front Controller purely for
routing while still instantiating a distinct, page-scoped controller object
per request, which is the multi-method-controller variant from dimension 8.

**Template View** and **Transform View** are the natural partners for
rendering once a Page Controller has finished its work and needs to hand
data to a presentation layer. Fowler pairs Page Controller with either of
these two view patterns in the book's own worked examples rather than with
any single prescribed view technology.

**Application Controller** addresses the navigation and flow-control
problem that neither Page Controller nor Front Controller solves well on
its own, deciding which page or view should come next in a multi-step
process. A team using Page Controller for a checkout flow that spans several
pages often introduces an Application Controller once the flow logic starts
leaking into individual page controllers, which is one of the misuse
symptoms in dimension 11.

**Transaction Script** and **Domain Model** are the domain-logic layers a
well-factored Page Controller delegates to rather than absorbs. The failure
mode in dimension 11 of business logic collapsing into the controller is
precisely the case where this separation was not maintained.

**Model-View-Controller**, the broader architectural pattern both Page
Controller and Front Controller specialize, is the umbrella. Fowler
explicitly frames both as concrete controller strategies within an
MVC-shaped system rather than as alternatives to MVC itself.

## 14. Refactoring path in and out

Introducing Page Controller into code that lacks it typically starts from a
codebase where request handling and rendering are not yet clearly separated
at all, a monolithic script or a single large handler that dispatches
internally with conditional logic on the request path. The path in starts
with identifying each distinct logical page or action currently handled
inside the monolith. Next, for each one, extract its handling logic into its
own function, class, or file (Extract Method followed by Extract Class, in
Fowler's refactoring vocabulary). Then register each extracted piece with
the web server or container against its own URL, removing the corresponding
branch from the original dispatch conditional. Finally, once every branch
has been extracted, delete the now-empty original dispatcher. This can be
done incrementally, one page at a time, with the old dispatcher and the new
per-page handlers coexisting during the migration, which keeps the
refactor low-risk.

The path out, migrating from Page Controller to Front Controller once the
duplication and enforcement problems from dimension 11 become costly, starts
by introducing a single dispatcher object or servlet that every request will
eventually pass through. Next, move the cross-cutting logic that is
currently duplicated across page controllers (authentication, common
headers, error translation) into that dispatcher, one concern at a time,
verifying after each move that the previously duplicated behavior still
happens for every page. Then, once the dispatcher owns every cross-cutting
concern, change each page's handler registration to route through the
dispatcher instead of being registered directly with the container, and
convert each page controller into whatever unit the dispatcher expects (a
Command object, a strategy keyed by URL, a controller method the dispatcher
looks up). Finally, remove the direct container-level registrations once the
dispatcher has taken over all of them. Both directions benefit from doing
one page at a time and running the existing test suite (per dimension 15)
after each page's migration rather than attempting the whole site in one
change.

## 15. Testing and verification

A Page Controller is easiest to test when its dependency on the raw
container request and response objects is minimized. If the controller
extracts the parameters it needs into plain values before calling any
domain logic, that domain logic can be unit tested with no web container at
all, which is the majority of the useful test coverage for most pages. What
becomes harder is testing the controller's own request-handling glue, the
part that actually reads the request object and writes the response,
because that code is coupled to the web platform's API. The usual technique
is either an in-process fake of the request and response objects (many
frameworks ship a test double for exactly this, for example Servlet API
mocking libraries, or ASP.NET's test-friendly `HttpContext` abstractions) or
an integration test that starts a real, lightweight instance of the
container and drives it with real HTTP requests, accepting the slower
feedback loop in exchange for testing the actual registration and dispatch
path. Because each controller is independently registered, integration
tests can also target one page in isolation without needing the whole
site's routing configured, which is a genuine testing advantage over a
Front Controller whose dispatch table needs to be present even to test one
route. Shared base-controller logic (dimension 8) should be tested once,
against the base class or through a minimal concrete subclass built only
for the test, rather than re-verified in every page controller that
inherits it.

## 16. Observability signals

At minimum, log the resolved page or controller identity alongside the
request path, method, status code, and duration for every request, because
with independently registered handlers there is no single place that
naturally centralizes this logging, unlike a Front Controller where request
logging is often written once in the dispatcher. A per-controller or
per-page metric tag (a route or action name) is required to make dashboards
usable at all, since raw URL paths alone tend to carry too many distinct
values, dynamic segments, and query strings, to aggregate cleanly on their
own. A healthy instance of the pattern in production shows a roughly even
distribution of request counts, latencies, and error rates across pages
that ought to behave similarly, with any single page's error rate rising in
isolation while others remain flat, since that isolation is the pattern's
operational strength, a bug in one page controller should not affect any
other page's metrics. A failing or misused instance shows the opposite
signature described in dimension 11, several pages' error rates or
latencies moving together after a shared dependency change, which is the
observable symptom of duplicated cross-cutting logic that was updated in
some controllers but not others.

## 17. Security and privacy implications

The pattern's most consequential security implication is structural. Since
there is no single enforced entry point, an authentication or authorization
check protecting most of a site's pages is only as strong as the discipline
that keeps every new page controller including it, which is exactly the
failure mode described first in dimension 11 and is a documented real-world
class of vulnerability (a forgotten access check on one specific page or
action, sometimes called broken access control at the level of an
individual endpoint rather than the whole application). Applications relying
on Page Controller for anything beyond the simplest, uniformly public site
should treat the absence of a container-enforced check as the default risk
and mitigate it with a servlet filter, an HTTP module, or an equivalent
mechanism the platform runs on every request, rather than trusting each
controller's author to remember. Input handling has no special implication
from this pattern specifically, standard request-parameter validation and
output encoding apply exactly as they would under any other controller
pattern, but a merged controller-and-view implementation (dimension 8, the
scriptlet-in-template variant) raises the risk of accidentally mixing
untrusted request data directly into rendered markup without the encoding
step being visually obvious in the code, since logic and presentation are
interleaved in the same file. This entry has no further pattern-specific
data-handling concern beyond what applies to any request-handling code.

## 18. References

1. Martin Fowler, "Patterns of Enterprise Application Architecture,"
   Addison-Wesley, 2003, Web Presentation patterns chapter, Page Controller
   section.
2. Martin Fowler, "Page Controller," martinfowler.com catalog page,
   https://martinfowler.com/eaaCatalog/pageController.html, verified 2026-08-11.
3. Microsoft, "Page Class (System.Web.UI)," Microsoft Learn,
   https://learn.microsoft.com/en-us/dotnet/api/system.web.ui.page?view=netframework-4.8.1,
   verified 2026-08-11.
4. Eclipse Foundation, Jakarta Servlet 4.0 API specification, HttpServlet,
   https://jakarta.ee/specifications/servlet/4.0/apidocs/javax/servlet/http/httpservlet,
   verified 2026-08-11.
5. Ruby on Rails Guides, "Action Controller Overview,"
   https://guides.rubyonrails.org/action_controller_overview.html, verified 2026-08-11.
6. Spring Framework Reference Documentation, "Handler Methods,"
   https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods.html,
   verified 2026-08-11, cited in dimension 13's discussion of the
   Front-Controller-with-per-action-handler hybrid.

## Code examples

### TypeScript, framework-agnostic, one controller function registered per route

```typescript
interface Product {
  id: string;
  name: string;
  price: number;
}

interface PageRequest {
  path: string;
  params: Record<string, string>;
}

interface PageResponse {
  status: number;
  body: string;
}

const catalog: Record<string, Product> = {
  p1: { id: "p1", name: "Kettle", price: 42 },
};

function productShowController(req: PageRequest): PageResponse {
  const product = catalog[req.params.id];
  if (!product) {
    return { status: 404, body: "Product not found" };
  }
  return {
    status: 200,
    body: `<h1>${product.name}</h1><p>${product.price}</p>`,
  };
}

function healthController(_req: PageRequest): PageResponse {
  return { status: 200, body: "ok" };
}

type Handler = (req: PageRequest) => PageResponse;

const registration: Record<string, Handler> = {
  "/products": productShowController,
  "/health": healthController,
};

function dispatch(path: string, params: Record<string, string>): PageResponse {
  const controller = registration[path];
  if (!controller) {
    return { status: 404, body: "No page controller registered" };
  }
  return controller({ path, params });
}

const shown = dispatch("/products", { id: "p1" });
console.log(shown.status, shown.body);
const health = dispatch("/health", {});
console.log(health.status, health.body);

export { productShowController, healthController, dispatch };
```

### Python, WSGI-style, one class per page

```python
from http import HTTPStatus


class ProductShowController:
    catalog = {"p1": {"id": "p1", "name": "Kettle", "price": 42}}

    def handle(self, product_id):
        product = self.catalog.get(product_id)
        if product is None:
            return HTTPStatus.NOT_FOUND, "Product not found"
        body = f"<h1>{product['name']}</h1><p>{product['price']}</p>"
        return HTTPStatus.OK, body


class HealthController:
    def handle(self):
        return HTTPStatus.OK, "ok"


ROUTES = {
    "/health": HealthController(),
}


def dispatch(path, product_id=None):
    if path == "/health":
        controller = ROUTES["/health"]
        return controller.handle()
    if path.startswith("/products/"):
        controller = ProductShowController()
        return controller.handle(product_id)
    return HTTPStatus.NOT_FOUND, "No page controller registered"


if __name__ == "__main__":
    status, body = dispatch("/products/", product_id="p1")
    print(status, body)
    status, body = dispatch("/health")
    print(status, body)
```

### Java, HttpServlet-shaped, one class per URL pattern

```java
import java.util.HashMap;
import java.util.Map;

class Product {
    final String id;
    final String name;
    final double price;

    Product(String id, String name, double price) {
        this.id = id;
        this.name = name;
        this.price = price;
    }
}

abstract class PageController {
    abstract String handle(Map<String, String> params);
}

class ProductShowController extends PageController {
    private final Map<String, Product> catalog = new HashMap<>();

    ProductShowController() {
        catalog.put("p1", new Product("p1", "Kettle", 42.0));
    }

    @Override
    String handle(Map<String, String> params) {
        Product product = catalog.get(params.get("id"));
        if (product == null) {
            return "404 Product not found";
        }
        return "<h1>" + product.name + "</h1><p>" + product.price + "</p>";
    }
}

class HealthController extends PageController {
    @Override
    String handle(Map<String, String> params) {
        return "ok";
    }
}

public class PageControllerDemo {
    public static void main(String[] args) {
        Map<String, String> params = new HashMap<>();
        params.put("id", "p1");
        PageController products = new ProductShowController();
        System.out.println(products.handle(params));

        PageController health = new HealthController();
        System.out.println(health.handle(params));
    }
}
```

Go and Rust are omitted here. Both languages' idiomatic web-handler style
(`http.HandlerFunc` in Go, `async fn` route handlers in most Rust web
frameworks) is structurally identical to the TypeScript and Python examples
above, a function registered against a single route, so a fourth and fifth
language example would not show a genuinely different implementation shape
for this pattern, only the same idiom in different syntax.
