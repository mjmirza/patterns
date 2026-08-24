---
name: Intercepting Filter
slug: intercepting-filter
family: 06-enterprise-application-architecture
category: Web Presentation
aliases: [Filter Chain, Middleware Pipeline]
first_described: "Alur, Crupi, Malks, Core J2EE Patterns, 2001"
maturity: canonical
related: [chain-of-responsibility, decorator, front-controller, pipes-filters]
incompatible_with: []
verified: 2026-08-24
---

# Intercepting Filter

## 1. Name, aliases, and lineage

Intercepting Filter is catalogued in *Core J2EE Patterns. Best Practices
and Design Strategies* by Deepak Alur, John Crupi, and Dan Malks, Prentice
Hall PTR, first edition 2001, second edition 2003.

It parallels the general Pipes and Filters architectural pattern, a chain
of processing elements where the output of each stage becomes the input of
the next, and it borrows its chaining mechanism from the Gang of Four Chain
of Responsibility pattern. The two are related but distinct. classic Chain
of Responsibility, per its own description, supports both a sequential
model, where every handler processes and forwards, and a single-handler
model common in GUI event handling, where exactly one handler claims the
request and the rest never run. Intercepting Filter specializes the
sequential model specifically for the web request and response lifecycle,
with the explicit expectation that every filter in the chain typically
performs its own concern, logging, an authentication check, compression,
rather than exactly one filter alone claiming the request.

## 2. Problem and context

Cross-cutting pre-processing and post-processing concerns, authentication,
logging, compression, encoding, need to run before and after core
request-handling logic without being hardcoded into every handler that
needs them. The Jakarta Servlet Specification states the motivation
directly. filters "intercept requests and responses to transform or use
the information contained in them," with named use cases including
"authentication, logging, image conversion, data compression, encryption,
tokenizing streams, XML transformations, and triggering resource access
events." Core J2EE Patterns' own framing is consistent with this. the
pattern "creates pluggable filters to process common services in a
standard manner without requiring changes to core request processing
code," with filters "easily removable without affecting existing code."

## 3. Forces

Separation of cross-cutting concerns pulls toward independent, reusable
filter classes, at the cost of ordering dependencies between them. Spring
Security's own reference documentation states this precisely. "the order
in which each Filter is invoked is extremely important," because a later
filter's correctness commonly depends on an earlier filter having already
run, authorization depending on authentication having populated the
security context first, for example.

Performance overhead versus flexibility is a documented trade-off.
Wikipedia's summary of the pattern's drawbacks names "Reduced performance
from unnecessarily long interceptor chains" directly, since every filter
in a chain runs on every matching request whether or not that specific
request needs it, unless the chain is conditionally scoped.

Centralization versus distributed configuration is the tension between
wanting each filter independently pluggable and needing one place that
guarantees correct composition and ordering, whether a deployment
descriptor, an annotation, or a configured filter-chain bean.

## 4. Applicability and non-applicability

Reach for Intercepting Filter when multiple, independently varying
cross-cutting concerns must apply uniformly across many endpoints without
embedding that logic in each handler.

Skip it for a single, simple handler with no cross-cutting concerns to
factor out, where a filter chain adds indirection and the performance cost
named in dimension 3 with no separation-of-concerns benefit to offset it.

## 5. Structure

Client. Initiates the request.

Filter. A single processing unit implementing a shared interface, able to
process before and after invoking the next element in the chain. In the
Jakarta Servlet API this is the `Filter` interface, with `init`, `doFilter`,
and `destroy` methods.

FilterChain or FilterManager. Manages the ordered set of filters and
coordinates their invocation. the Jakarta Servlet API's own description of
`FilterChain`. "allows filters to pass control to the next entity in the
chain."

Target. The actual request handler or resource invoked once the chain
completes, a Servlet in the Servlet API, or a route handler or controller
action in other frameworks.

## 6. ASCII structure diagram

```
+----------+
| Client   |
+----------+
     | request
     v
+----------+   +----------+   +----------+
| Filter 1 |-->| Filter 2 |-->| Filter N |
+----------+   +----------+   +----------+
     ^               ^               |
     | response      | response      v
     |    (each filter can process   |
     |     before and after,         v
     |     or short-circuit)   +-----------+
     +--------------------------| Target    |
                                 +-----------+

Each filter can act before calling the next filter, act again after it
returns, or end the chain itself without ever reaching the Target.
```

## 7. Dynamics

A request passes through an ordered chain of filters, each able to process
before and after invoking the next filter or the target. ASP.NET Core's
own middleware documentation states the shape directly. "Each delegate can
perform operations before and after the next delegate." "The next
parameter represents the next delegate in the pipeline. You can typically
perform actions both before and after the next delegate."

Django's own documentation gives the clearest articulation of the
before-and-after symmetry, using an explicit metaphor. "You can think of it
like an onion. each middleware class is a 'layer' that wraps the view... If
the request passes through all the layers of the onion... all the way to
the view at the core, the response will then pass through every layer, in
reverse order, on the way back out."

A filter can also short-circuit the chain entirely rather than forward the
request. Express's own guide states the consequence of not doing so.
"If a middleware function does not end the request-response cycle, it must
call next() to pass control to the next middleware function. Otherwise, the
request will be left hanging."

## 8. Implementation variants

The Jakarta Servlet Filter API, `jakarta.servlet.Filter`, part of the
Jakarta Servlet Specification, version 6.1, Chapter 6, "Filtering," is the
canonical, technology-named realization the pattern is drawn from directly.

Express.js middleware, Node.js. quoted directly from its own guide. "an
Express application is essentially a series of middleware function calls
executed during the request-response cycle." the same before, after, and
short-circuit shape as dimension 7, expressed as `(req, res, next) => {}`.

ASP.NET Core's middleware pipeline, .NET. quoted directly. "Middleware is
software that's assembled into an app pipeline to handle requests and
responses... The ASP.NET Core request pipeline consists of a sequence of
request delegates, called one after the other." configured through `Use`,
`Run`, and `Map`.

Python WSGI middleware and Django middleware. PEP 3333, the WSGI
specification itself, describes middleware precisely. "a single object may
play the role of a server with respect to some application(s), while also
acting as an application with respect to some server(s)," a dual role
achieved by direct nesting rather than a named chain object. Django's own
middleware framework builds on the same idea, described in its own docs as
"a light, low-level 'plugin' system for globally altering Django's input or
output," using the onion metaphor quoted in dimension 7.

Go's `http.Handler` wrapping convention. Go has no dedicated middleware
type or interface, this is a community convention built entirely on the
standard library's own `Handler` interface. Notably, the standard library
itself ships functions with the exact wrap-a-Handler-return-a-Handler
shape that is the idiomatic Go middleware pattern, `TimeoutHandler`,
`StripPrefix`, and `MaxBytesHandler`, each taking a `Handler` and returning
a `Handler`, which is direct evidence this shape is idiomatic Go rather
than only a third-party convention.

## 9. Known production uses

The Jakarta and Java Servlet Filter API itself, implemented by every
Servlet container, Tomcat, Jetty, Undertow among them.

Spring Security's `FilterChainProxy` and `SecurityFilterChain`. quoted
directly from Spring Security's own reference documentation. "Spring
Security's Servlet support is contained within FilterChainProxy.
FilterChainProxy is a special Filter provided by Spring Security that
allows delegating to many Filter instances through SecurityFilterChain."

Express.js's own middleware stack, the entire framework built on this
pattern per dimension 8's quote.

ASP.NET Core's middleware pipeline, Microsoft's own architecture for the
whole framework's request handling, per dimension 8.

Django's middleware framework, a fifth, independently sourced production
system, per dimension 8.

## 10. Consequences

Positive. quoted directly from Wikipedia's summary of the pattern.
"Improved reusability through centralized, pluggable components," and
"Increased flexibility via declarative application and removal of generic
components."

Negative. the same source names "Reduced performance from unnecessarily
long interceptor chains," matching dimension 3's forces analysis, along
with the implicit ordering dependencies documented directly by Spring
Security in dimension 3.

## 11. Failure modes and misuse

Filter ordering bugs are the best documented failure mode. Spring
Security's own reference documentation provides an explicit rule-of-thumb
placement table precisely because misordering is a known, real class of
bug, for example requiring an authorization filter to be placed after the
authentication filters that populate the security context, so that an
authorization check is never reachable by a request that has not yet been
authenticated.

Filters that silently swallow an exception that should propagate, for
example a broad catch block inside a filter's processing step that never
calls the next element and never rethrows, is a widely recognised,
real-world anti-pattern in this space, though no single, directly
citable primary source naming it explicitly was confirmed in this entry's
research. it is stated here as a commonly observed risk rather than a
sourced quote.

Overly long chains making the request path hard to reason about follows
directly from the performance and debuggability cost already documented in
dimension 10. every additional filter is one more place a request can be
silently short-circuited or mutated before it is fully understood.

## 12. Trade-off matrix

| Alternative | Relationship |
|---|---|
| Chain of Responsibility, GoF | Structural ancestor of the chaining mechanism. classic Chain of Responsibility supports both a sequential model and a single-handler model, refactoring.guru's own description of the latter being that "it's either only one handler that processes the request or none at all," common in GUI event handling. Intercepting Filter specializes the sequential model for the web request lifecycle |
| Decorator, GoF | Wraps a single target and cannot short-circuit. refactoring.guru's own comparison. "The CoR handlers can execute arbitrary operations independently of each other. They can also stop passing the request further at any point. On the other hand, various Decorators can extend the object's behavior while keeping it consistent with the base interface... decorators aren't allowed to break the flow of the request" |
| Aspect-Oriented Programming | A more general, language or framework-level cross-cutting mechanism. Spring's own AOP documentation describes it as operating at "method execution level," with pointcut expressions that "enable advice to be targeted independently of the object-oriented hierarchy." Intercepting Filter operates strictly at the HTTP request and response boundary, before any application object is reached at all |
| Embedding cross-cutting logic directly in each handler | The anti-pattern this pattern solves, see dimension 2 |

## 13. Related and incompatible patterns

Chain of Responsibility, the structural ancestor, see dimension 1 and 12.

Front Controller, commonly combined at the head of a filter chain in J2EE
presentation-tier architecture, dispatching to a target after the chain's
pre-processing has run. the precise wording of Core J2EE Patterns' own
cross-reference between the two was not independently reconfirmed for this
entry and is stated here as a well-established, commonly cited pairing
rather than a directly quoted book passage.

Decorator, related structurally but unable to short-circuit, distinguished
in dimension 12.

Pipes and Filters, the general architectural style this pattern
specializes for the web request and response lifecycle specifically.

## 14. Refactoring path in and out

Extracting scattered cross-cutting logic, duplicated authentication
checks, duplicated logging calls, out of individual handlers and into a
filter or middleware chain is the direct value proposition already
evidenced by the problem statement in dimension 2 and the reusability
consequence in dimension 10. this is stated as reasoned, standard practice
rather than a single directly cited step-by-step source.

Collapsing an over-engineered filter chain back into direct handling
applies when the cross-cutting need genuinely disappears, for example a
single-tenant internal tool that no longer needs pluggable authentication
strategies, the mirror image of dimension 4's non-applicability case.

## 15. Testing and verification

Each filter can be unit tested in isolation by substituting a mock chain
or mock next-handler, a structural property visible directly in every
implementation variant covered in dimension 8. Express middleware's
`(req, res, next)` signature makes `next` trivially mockable. ASP.NET
Core's `Use` delegate takes an awaitable `next.Invoke(context)`, equally
mockable. Go's wrap-a-Handler functions are testable by passing a stub
`Handler`.

Integration testing is separately needed to verify correct ordering and
interaction between filters, since no single filter's unit test can prove
the chain as a whole is composed correctly, directly motivated by the
ordering-bug evidence in dimension 11.

## 16. Observability signals

Per-filter timing and latency instrumentation is the natural, structurally
obvious signal, since any filter can time its own call to the next element
in the chain. this is stated as reasoned inference from the verified
before-and-after wrapping shape in dimension 7, rather than a citation to
one specific, named tracing tool.

Filter-chain-position or ordering logs, useful for debugging an ordering
bug of the kind documented in dimension 11, follow the same reasoning.

## 17. Security and privacy implications

This is one of the most security-relevant patterns in the catalog.
authentication and authorization filters are a primary, real-world use
case, and Spring Security's entire filter-chain model is built around
exactly this. Its own reference documentation states the underlying risk
directly and precisely. "Since a Filter impacts only downstream Filter
instances and the Servlet, the order in which each Filter is invoked is
extremely important." Spring Security backs this with a concrete placement
table, exploit-protection filters after the security-context filter,
authentication filters after the logout filter, authorization filters
after the anonymous-authentication filter, making misordered security
filters a real, documented, and directly citable vulnerability class rather
than a theoretical concern.

## 18. References

1. Deepak Alur, John Crupi, Dan Malks, *Core J2EE Patterns. Best
   Practices and Design Strategies*, Prentice Hall PTR, first edition,
   2001, second edition, 2003.
2. Jakarta Servlet Specification, version 6.1, Chapter 6, "Filtering."
   `https://jakarta.ee/specifications/servlet/6.1/jakarta-servlet-spec-6.1`,
   verified 2026-08-24.
3. Spring Security reference documentation, Servlet architecture.
   `https://docs.spring.io/spring-security/reference/servlet/architecture.html`,
   verified 2026-08-24.
4. Express.js, "Using middleware."
   `https://expressjs.com/en/guide/using-middleware.html`, verified
   2026-08-24.
5. Microsoft, "ASP.NET Core Middleware."
   `https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/`,
   verified 2026-08-24.
6. PEP 3333, Python Web Server Gateway Interface v1.0.1, "Middleware.
   Components that Play Both Sides." verified 2026-08-24.
7. Django Software Foundation, "Middleware."
   `https://docs.djangoproject.com/en/stable/topics/http/middleware/`,
   verified 2026-08-24.
8. Go standard library, `net/http` package documentation.
   `https://pkg.go.dev/net/http`, verified 2026-08-24.
9. Wikipedia, "Intercepting Filter pattern," consulted for the
   consequences summary, verified 2026-08-24.
10. refactoring.guru, "Chain of Responsibility," consulted for the
    sequential-versus-single-handler distinction and the Decorator
    comparison, verified 2026-08-24.
11. Spring Framework reference documentation, Aspect-Oriented
    Programming with Spring.
    `https://docs.spring.io/spring-framework/reference/core/aop.html`,
    verified 2026-08-24.

**Evidence grade.** high

**Most solid findings.** The Jakarta Servlet Specification's own filter
motivation and interface shape, fetched and quoted directly. the
Spring Security ordering-risk quote and its concrete placement table,
directly on point for dimension 17. and the four independent,
official-documentation-sourced production uses in dimension 9.

**Unverified or unclear.** Core J2EE Patterns' own exact cross-reference
wording between Intercepting Filter and Front Controller was not
independently reconfirmed in this entry's research. the exception
swallowing failure mode and the specific per-filter tracing tooling in
dimension 16 are stated as well-known practice rather than pinned to a
single citation.

## Code

### TypeScript

```typescript
interface MwRequest {
  method: string;
  path: string;
  headers: { authorization?: string };
}

interface MwResponse {
  status(code: number): { send(body: string): void };
}

type NextFunction = () => void;

function requestLogger(req: MwRequest, _res: MwResponse, next: NextFunction): void {
  console.log(req.method + " " + req.path);
  next();
}

function requireAuth(req: MwRequest, res: MwResponse, next: NextFunction): void {
  if (!req.headers.authorization) {
    res.status(401).send("unauthorized");
    return;
  }
  next();
}

interface App {
  use(middleware: (req: MwRequest, res: MwResponse, next: NextFunction) => void): void;
}

function registerMiddleware(app: App): void {
  app.use(requestLogger);
  app.use(requireAuth);
}
```

### Python

```python
class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(request.method, request.path)
        response = self.get_response(request)
        return response


class RequireAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.headers.get("Authorization"):
            return HttpResponseUnauthorized()
        return self.get_response(request)
```

### Java

```java
import java.io.IOException;

class ServletException extends Exception {
}

interface ServletRequest {
}

interface ServletResponse {
}

interface HttpServletRequest extends ServletRequest {
    String getMethod();
    String getRequestURI();
}

interface FilterChain {
    void doFilter(ServletRequest request, ServletResponse response)
            throws IOException, ServletException;
}

interface Filter {
    void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException;
}

public class RequestLoggingFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response,
                          FilterChain chain) throws IOException, ServletException {
        HttpServletRequest http = (HttpServletRequest) request;
        System.out.println(http.getMethod() + " " + http.getRequestURI());
        chain.doFilter(request, response);
    }
}
```

### Go

```go
package middleware

import "net/http"

func RequestLogger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		println(r.Method, r.URL.Path)
		next.ServeHTTP(w, r)
	})
}

func RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r)
	})
}
```

### C#

```csharp
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

public class HttpRequest
{
    public string Method { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
    public Dictionary<string, string> Headers { get; set; } = new Dictionary<string, string>();
}

public class HttpResponse
{
    public int StatusCode { get; set; }
}

public class HttpContext
{
    public HttpRequest Request { get; set; } = new HttpRequest();
    public HttpResponse Response { get; set; } = new HttpResponse();
}

public class RequestDelegate
{
    private readonly Func<HttpContext, Task> _next;
    public RequestDelegate(Func<HttpContext, Task> next)
    {
        _next = next;
    }
    public Task Invoke(HttpContext context) => _next(context);
}

public static class MiddlewarePipeline
{
    public static void RequestLogger(HttpContext context, RequestDelegate next)
    {
        Console.WriteLine($"{context.Request.Method} {context.Request.Path}");
        next.Invoke(context);
    }

    public static void RequireAuth(HttpContext context, RequestDelegate next)
    {
        if (!context.Request.Headers.ContainsKey("Authorization"))
        {
            context.Response.StatusCode = 401;
            return;
        }
        next.Invoke(context);
    }
}
```
