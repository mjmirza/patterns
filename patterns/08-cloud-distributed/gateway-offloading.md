---
name: Gateway Offloading
slug: gateway-offloading
family: 08-cloud-distributed
category: Cloud and Distributed
aliases: [SSL Offloading, TLS Offloading, Offload Gateway, Termination Proxy]
first_described: "Microsoft patterns and practices, Cloud Design Patterns, 2014"
maturity: canonical
related: [gateway-aggregation, backends-for-frontends, circuit-breaker, rate-limiting, throttling, federated-identity, ambassador]
incompatible_with: []
verified: 2026-08-02
---

# Gateway Offloading

## 1. Name, aliases, and lineage

The canonical name is **Gateway Offloading**, catalogued by Microsoft in its
Azure Architecture Center collection of cloud design patterns. The pattern
page states the intent in one sentence, to "offload shared or specialized
service functionality to a gateway proxy," and it names TLS certificates as
the first concrete example of what gets moved ([Microsoft Learn, Gateway
Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02).

Two informal names lead day-to-day engineering conversation and both
predate the catalog entry by a wide margin. **SSL Offloading** and its
successor term **TLS Offloading** describe the single most common instance
of the pattern, moving the CPU-intensive work of the TLS handshake and bulk
encryption off application servers and onto a dedicated appliance or proxy.
Hardware vendors were selling purpose-built SSL accelerator cards for this
exact job in the late 1990s, long before anyone wrote the words "cloud
design pattern." The Azure catalog entry did not invent the technique, it
gave the general version of the technique, TLS termination plus every other
cross-cutting concern a gateway can absorb, a durable name and a place next
to Gateway Aggregation and Gateway Routing in the pattern literature.

A third informal name, **Termination Proxy**, appears in networking and load
balancer documentation and emphasizes the mechanical act of ending one
connection and starting another, which is the structural core of the
pattern regardless of which concern is being offloaded.

The Azure catalog groups Gateway Offloading with two siblings that share the
word Gateway but solve different problems. Gateway Aggregation fans a single
client call out to several backend services and merges the answers.
Gateway Routing directs a request to one of several backends based on the
request's own content. Gateway Offloading does neither. It changes what the
request looks like, or how it is secured, before handing it to exactly one
backend, or to a backend pool that is otherwise indistinguishable from a
single logical service. The three patterns are commonly implemented on the
same physical device, an API gateway or an application load balancer, which
is why they are frequently confused with each other in casual conversation
even though the Azure catalog treats them as three separate, composable
patterns ([Microsoft Learn, Gateway Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02).

## 2. Problem and context

An application is built as a set of backend instances, whether that is one
service replicated many times or several distinct services behind one
entry point. A handful of concerns are not specific to any one of those
backends and yet every one of them needs the concern handled correctly.
Terminating an inbound TLS connection is the sharpest example, but the same
shape recurs for compressing a response body, validating an authentication
token, rewriting a protocol from HTTP/1.1 to HTTP/2, rate limiting a noisy
client, or writing a structured access log line.

Microsoft's framing of the problem names the administrative cost directly.
"Some features are commonly used across multiple services, and these
features require configuration, management, and maintenance. A shared or
specialized service that is distributed with every application deployment
increases the administrative overhead and increases the likelihood of
deployment error. Any updates to a shared feature must be deployed across
all services that share that feature" ([Microsoft Learn, Gateway Offloading
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02). The same page names the specific pain of certificate
management, saying that "a certificate needed by an application must be
configured and deployed on all application instances. With each new
deployment, the certificate must be managed to guarantee that it doesn't
expire," and generalizes the same problem to "authentication, authorization,
logging, monitoring, or throttling" ([Microsoft Learn, Gateway Offloading
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02).

The TLS instance of the problem carries a second dimension that is purely
about resource cost rather than administration. Azure's own Application
Gateway documentation states it plainly for the CPU angle, "SSL/TLS
processing is very CPU intensive, and is becoming more intensive as key
sizes increase. Removing this work from the backend servers allows them to
focus on what they are most efficient at, delivering content" ([Microsoft
Learn, Enabling end to end TLS on Azure Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/ssl-overview),
verified 2026-08-02). NGINX's own operations guide makes the same point
about the handshake specifically, "SSL operations consume extra CPU
resources. The most CPU-intensive operation is the SSL handshake" ([NGINX
documentation, Configuring HTTPS servers](https://docs.nginx.com/nginx/admin-guide/security-controls/terminating-ssl-http/),
verified 2026-08-02, quoted content). A fleet of application servers that
each negotiate their own TLS sessions is spending cycles on cryptography
instead of on the request the business actually cares about, and that cost
scales with every new instance the fleet adds, whether or not the new
instance is handling more real traffic or simply absorbing the fixed cost
of TLS per connection.

There is also a session-reuse dimension that only a centralizing point can
solve well. Azure's documentation explains that TLS session caching only
helps when the same party sees the repeat connection, "if this is done at
the application gateway, all requests from the same client can use the
cached values. If it's done on the backend servers, then each time the
client's requests go to a different server the client must reauthenticate"
([Microsoft Learn, Enabling end to end TLS on Azure Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/ssl-overview),
verified 2026-08-02). A load balancer that spreads connections across many
backend instances defeats session caching unless the cache itself sits in
front of the load balancing decision, which is exactly where a gateway
lives.

The context in which this problem is real, rather than imagined, has three
parts that usually hold together. First, the concern is genuinely shared by
every request that reaches the backend pool, not specific to one route or
one tenant, because a gateway that offloads a concern half the requests do
not need is applying a blunt instrument to a targeted problem. Second, the
concern requires expertise or infrastructure, PKI management, a rate
limiting algorithm, a compression codec, that the application team should
not have to own and re-implement per service. Third, there is already a
single point in the request path, a load balancer, a reverse proxy, or an
API gateway, that every request already passes through, so offloading the
concern there adds no new network hop, it only adds work at a hop that
already exists.

## 3. Forces

Every use of Gateway Offloading is a negotiation between six pressures, and
the pattern deliberately favors some of them at the expense of others.

**Operational simplicity versus centralization risk.** Moving certificate
management, authentication, and logging into one place removes duplicated
configuration from every backend instance, which is the pattern's whole
selling point. The same move concentrates every one of those concerns
behind a single component. A misconfiguration in the gateway now affects
every backend at once, where a misconfigured certificate on one backend
instance in the old model only affected that one instance.

**Resource cost versus a new bottleneck.** TLS handshakes, gzip
compression, and JSON schema validation for token claims all cost CPU
somewhere. Moving that cost off many small backend instances and onto one
gateway reduces the aggregate CPU spent per request when the gateway is
sized correctly, because the gateway does the work once per connection
rather than the backend doing it once per request-serving instance. It also
creates exactly one place where that cost can become the limiting factor
for the whole system if the gateway is undersized. Azure's own guidance
names this directly as an issue to watch. the gateway must be sized "for
the capacity and scaling requirements of your application and
endpoints," and Microsoft is explicit that the gateway "doesn't become a
bottleneck for the application and can grow with demand" ([Microsoft Learn, Gateway
Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02).

**Specialization versus coupling.** A dedicated security or platform team
can own the gateway's TLS configuration, WAF rules, and authentication
policy without needing deep knowledge of any one backend's domain logic,
and application teams can stop budgeting time for certificate renewal.
That separation is only healthy while the gateway stays generic. The moment
a gateway rule encodes a decision that depends on domain knowledge, for
example a discount calculation or an order status transition, the gateway
has become a hidden dependency that every backend team must now understand
to reason about their own service, and the specialization the pattern was
meant to buy turns into coupling instead.

**Visibility versus end-to-end confidentiality.** A gateway that terminates
TLS gains plaintext access to headers and bodies, which is exactly what
lets it do content-based routing, structured logging, and request
validation in the same pass. That same plaintext visibility means the
traffic between the gateway and the backend is, by default, unencrypted
unless a second TLS session is deliberately established for that hop. In a
regulated environment, or one where the network between gateway and backend
is not fully trusted, that gap has to be closed with end-to-end TLS, which
gives back some of the CPU savings the offload was meant to capture.

**Consistency versus per-service flexibility.** Centralizing logging and
monitoring at the gateway gives every backend a baseline level of
observability even when a particular service forgot to instrument itself,
which the Azure catalog states as a benefit, "provide some consistency for
request and response logging and monitoring. Even if a service isn't
correctly instrumented, the gateway can be configured to guarantee a
minimum level of monitoring and logging" ([Microsoft Learn, Gateway Offloading
pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02). A gateway that enforces one policy for everyone also
removes a service's ability to make a locally sensible exception, for
example a service that genuinely needs a different rate limit shape than
its neighbors, without a gateway-level carve-out that reintroduces the
per-service configuration the pattern was trying to remove.

**Cost of the platform versus cost per node.** Microsoft's Well-Architected
Framework guidance for this pattern frames the financial trade directly,
saying the pattern "enables you to redirect costs from resources that would
be spent per-node into the gateway implementation. Costs in the centralized
processing model are frequently lower than those of the distributed model"
([Microsoft Learn, Gateway Offloading pattern, Workload design](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02). That is true when the gateway is a managed,
horizontally scaled platform service billed by traffic. It is not
automatically true for a self-hosted gateway that a team must now size,
patch, and keep highly available on its own, which is real infrastructure
spend that did not exist before.

## 4. Applicability and non-applicability

**Reach for Gateway Offloading when the following hold.**

- A concern is genuinely shared across every backend instance behind a
  single entry point, most commonly TLS certificate management and
  handshake processing, per Microsoft's own guidance on when to use the
  pattern, "an application deployment has a shared concern such as SSL
  certificates or encryption" ([Microsoft Learn, Gateway Offloading
  pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02).
- The concern requires specialized skill the application team should not
  have to maintain, for example rotating certificates before expiry, tuning
  a WAF ruleset, or keeping a rate limiting algorithm correct under
  concurrent load. Microsoft names this case explicitly, "you wish to move
  the responsibility for issues such as network security, throttling, or
  other network boundary concerns to a more specialized team" ([Microsoft
  Learn, Gateway Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02).
- The concern has resource requirements that differ sharply from the
  backend's own resource profile, so co-locating it with application logic
  wastes capacity that could be scaled independently.
- A gateway or reverse proxy already sits in the request path for other
  reasons, so adding the offloaded concern there costs no new network hop.
- The concern benefits from being consolidated per connection rather than
  per request, which is true of TLS session caching and is one of the
  clearest, most durable cases for the pattern.

**Do NOT reach for Gateway Offloading when any of the following hold.**

- The concern is domain-specific business logic, even if it happens to run
  early in the request path. Microsoft's own considerations list is
  unambiguous on this point, "business logic should never be offloaded to
  the gateway" ([Microsoft Learn, Gateway Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02). A discount rule, an inventory check, or an
  order-state transition belongs in the service that owns that data, not in
  a proxy configuration file that the whole platform team must edit for one
  business rule.
- Only one backend, or a minority of backends, needs the concern. A gateway
  rule scoped to one route recreates the per-service configuration sprawl
  the pattern exists to remove, and it is easy to lose track of which
  routes carry which exceptions once several teams have each added one.
- End-to-end confidentiality is a hard requirement and the network between
  gateway and backend cannot be trusted or re-encrypted, because a plain
  TLS-terminating gateway leaves that hop in the clear by default.
- The team cannot commit to running the gateway itself as a highly
  available, independently scaled component. Microsoft's issues section
  states the operational baseline directly, naming the need to "avoid single
  points of failure by running multiple instances of your gateway"
  ([Microsoft Learn, Gateway
  Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02). A single, unreplicated gateway instance converts a
  distributed system's many independent points of partial failure into one
  point of total failure.
- Introducing the gateway would couple services that were deliberately
  independent. The Azure catalog's closing caution reads, "this pattern
  might not be suitable if it introduces coupling across services"
  ([Microsoft Learn, Gateway Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02), which matters most when the backends behind the
  gateway are owned by genuinely separate teams that do not want a shared
  release schedule for the gateway's configuration.
- The offloaded concern needs data or context that only the backend has,
  for example a business-rule-dependent authorization decision rather than
  a plain token signature check. A gateway can verify that a JWT is
  well-formed and signed by the expected issuer, it should not decide
  whether the user in that token is allowed to discount this specific
  order.

## 5. Structure

The pattern has four participants.

**The client.** Any caller, a browser, a mobile app, or another service,
that opens a connection expecting to reach the backend, and that does not
need to know or care that a gateway sits in the middle of that connection.

**The gateway proxy.** The single component that terminates the
client-facing connection and performs the offloaded work. It owns the TLS
certificate and private key, decrypts inbound traffic, performs any
compression, decompression, authentication check, or protocol translation
configured on it, and then issues a new outbound request or connection to
the backend. It is stateless with respect to business data but frequently
stateful with respect to the offloaded concern itself, holding a TLS
session cache, a rate limit counter, or a compression dictionary.

**The backend pool.** One or more service instances that receive an already
simplified request from the gateway. In the canonical TLS case the backend
receives plain, unencrypted HTTP unless end-to-end TLS is explicitly
configured for that hop, along with headers the gateway injected to carry
forward information the backend still needs, most commonly the original
scheme, the original client address, and the original host.

**The offloaded concern's configuration.** The certificates, the
authentication policy, the rate limit rules, the compression settings. This
is not a running component, it is the artifact that makes the gateway's
behavior correct, and its lifecycle, who owns it, how it is rotated, how it
is tested, is a first-class part of adopting the pattern, not an
afterthought.

A gateway proxy in production almost always offloads more than one concern
at once, and the concerns are commonly layered in a fixed order inside the
same request pipeline, TLS termination first because nothing else in the
pipeline can inspect an encrypted payload, then authentication, then
routing or rate limiting, then compression as the very last step before the
response leaves the gateway, because compressing before any other
transformation risks compressing content that a downstream step still needs
to read in cleartext form.

## 6. ASCII structure diagram

```text
                 encrypted, compressed        plain, uncompressed
                 client connection            internal connection

  +--------+      TLS 1.3 handshake     +-----------------------+
  | Client | -------------------------> |     Gateway Proxy     |
  +--------+ <------------------------- |                       |
                 gzip response          |  - TLS certificate     |
                                        |  - bearer token check  |
                                        |  - rate limit counter  |
                                        |  - gzip encode/decode  |
                                        |  - X-Forwarded-* set   |
                                        +-----------------------+
                                                    |
                                                    | plain HTTP/1.1
                                                    | (or re-encrypted
                                                    |  end-to-end TLS)
                                                    v
                                        +-----------------------+
                                        |     Backend Pool       |
                                        |  instance A            |
                                        |  instance B            |
                                        |  instance C            |
                                        |  (no TLS certs,        |
                                        |   no auth checks,      |
                                        |   no compression code) |
                                        +-----------------------+
```

## 7. Dynamics

The following sequence traces one client request through a gateway that
offloads TLS termination, authentication, and compression, the three most
common concerns bundled together in practice.

```text
Client                Gateway                          Backend
  |                       |                                |
  |--- TCP connect ------>|                                |
  |--- TLS ClientHello -->|                                |
  |<-- ServerCert, ------ |  gateway's own cert, private   |
  |    ServerHello        |  key never leaves this box      |
  |--- Finished --------->|                                |
  |   (TLS session        |                                |
  |    established)       |                                |
  |                       |                                |
  |--- GET /orders/42 --->|                                |
  |    Authorization      |  1. decrypt request             |
  |     Bearer <token>    |  2. validate token signature    |
  |    Accept-Encoding    |     and expiry, no domain       |
  |     gzip              |     logic evaluated here        |
  |                       |  3. set X-Forwarded-Proto https |
  |                       |     set X-Forwarded-For <ip>    |
  |                       |     strip Authorization if the  |
  |                       |     backend trusts the gateway  |
  |                       |     network instead              |
  |                       |------- GET /orders/42 --------->|
  |                       |        plain HTTP, no TLS        |
  |                       |<------ 200 OK, JSON body --------|
  |                       |  4. gzip-encode body since       |
  |                       |     client advertised support    |
  |                       |  5. re-encrypt under the         |
  |                       |     existing TLS session          |
  |<-- 200 OK, gzip body -|                                |
  |                       |                                |
  |--- next request ----->|  reuses cached TLS session ID,  |
  |    same connection    |  skips full handshake cost       |
  |                       |------- GET /orders/43 --------->|
```

Two failure branches matter enough to draw separately, because they explain
most of dimension 11 below.

```text
Failure branch, token missing or invalid
Client                Gateway
  |--- GET /orders/42 --->|
  |    (no Authorization) |
  |                       |  1. decrypt request
  |                       |  2. no valid bearer token found
  |<-- 401 Unauthorized --|  3. request never reaches backend
  |                       |     backend load and logs are
  |                       |     unaffected by the rejection

Failure branch, gateway to backend hop is not re-encrypted
Client                Gateway                 Untrusted network segment
  |--- HTTPS request ---->|                            |
  |                       |------- plain HTTP --------->| <- readable by
  |                       |                              |    anyone with
  |                       |<------ plain HTTP -----------|    access to this
  |<-- HTTPS response ----|                            |    network segment
```

## 8. Implementation variants

**TLS termination only, plain hop to backend.** The gateway holds the
certificate, decrypts, and forwards over plain HTTP. This is the shape in
Azure's own worked example, "using Nginx as the SSL offload appliance, the
following configuration terminates an inbound SSL connection and
distributes the connection to one of three upstream HTTP servers"
([Microsoft Learn, Gateway Offloading pattern, Example](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02). It buys the most CPU savings and is only appropriate
when the network between gateway and backend is trusted, commonly because
it is a private subnet, a service mesh sidecar link, or a single host.

**End-to-end TLS, terminate and re-encrypt.** The gateway decrypts the
client connection, applies whatever offloaded logic depends on plaintext
access such as routing or logging, then opens a fresh, second TLS session
to the backend using the backend's own certificate. Azure's documentation
describes exactly this shape, "when configured with end-to-end TLS
communication mode, Application Gateway terminates the TLS sessions at the
gateway and decrypts user traffic. It then applies the configured rules to
select an appropriate backend pool instance to route traffic to.
Application Gateway then initiates a new TLS connection to the backend
server and re-encrypts data using the backend server's public key
certificate before transmitting the request to the backend" ([Microsoft
Learn, Enabling end to end TLS on Azure Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/ssl-overview),
verified 2026-08-02). This variant gives up some of the pure CPU offload,
because the backend still does one TLS handshake, but it keeps the wire
encrypted end to end and it still buys the gateway-side benefits of
centralized certificate management and content-based routing.

**TLS passthrough, no offload at all.** A load balancer that forwards the
raw encrypted bytes without terminating them is explicitly not this
pattern, and AWS documentation draws the line precisely, "if you need to
pass encrypted traffic to targets without the load balancer decrypting it,
you can create a Network Load Balancer or Classic Load Balancer with a TCP
listener on port 443. With a TCP listener, the load balancer passes
encrypted traffic through to the targets without decrypting it" ([AWS
documentation, Create an HTTPS listener for your Application Load
Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html),
verified 2026-08-02). This is worth naming as a variant precisely because it
is the thing people reach for by habit and it delivers none of Gateway
Offloading's benefits, it only balances connections.

**Sidecar-level TLS offload inside a mesh.** In a service mesh, TLS
termination and re-origination happen per hop rather than once at the
network edge, with each proxy sidecar terminating the inbound mTLS
connection from its neighbor and originating a fresh one outbound. Envoy's
own architecture documentation states that "Envoy supports both TLS
termination in listeners as well as TLS origination when making
connections to upstream clusters" ([Envoy Proxy documentation, TLS
overview](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/security/ssl),
verified 2026-08-02). This variant distributes the pattern across every
sidecar instead of concentrating it in one edge appliance, trading the
single-bottleneck risk for a larger operational surface of many identical
proxies to keep configured correctly.

**Hardware and appliance offload.** Dedicated TLS accelerator hardware, and
managed cloud offerings such as AWS Certificate Manager paired with an
Application Load Balancer or Azure Application Gateway's managed TLS
termination, remove not only the CPU cost but the operational burden of
running the offload software at all. This is the variant Microsoft's
Well-Architected guidance points at when it notes that "in some cases,
offloading completely replaces functionality with a reliable
platform-provided feature" ([Microsoft Learn, Gateway Offloading pattern,
Workload design](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02).

**Compression and protocol offload without TLS.** Not every instance of
this pattern is about encryption. A gateway that only gzip-encodes
responses, or that only translates an inbound HTTP/2 stream into HTTP/1.1
for backends that do not speak the newer protocol, is applying the exact
same structural move, moving a shared, backend-agnostic transformation to
one place, without touching certificates at all. The worked code examples
in the next section demonstrate this narrower variant deliberately, because
it isolates the pattern's shape from the specific mechanics of TLS
handshakes, which are well documented elsewhere and are not, on their own,
what makes this a design pattern rather than a networking feature.

Three runnable examples follow, one per language, each demonstrating a
gateway that offloads authentication and response compression from a
backend that implements neither. Each was executed against the toolchain
noted and produced the output shown.

### TypeScript, Node.js 23.11.0, tsc 7.0.2, executed 2026-08-02

```typescript
// Gateway Offloading in TypeScript, built only on Node's http and zlib
// modules so the example runs without a package manager.

import * as http from "http";
import * as zlib from "zlib";
import type { AddressInfo } from "net";

function startBackend(): http.Server {
  const server = http.createServer((req, res) => {
    const body = `order-service reply for ${req.url}`;
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(body);
  });
  server.listen(0);
  return server;
}

function startGateway(backendPort: number): http.Server {
  const server = http.createServer((req, res) => {
    if (req.headers.authorization !== "Bearer demo-token") {
      res.writeHead(401);
      res.end("unauthorized");
      return;
    }

    const upstream = http.request(
      { host: "127.0.0.1", port: backendPort, path: req.url, method: "GET" },
      (upstreamRes) => {
        const chunks: Buffer[] = [];
        upstreamRes.on("data", (c: Buffer) => chunks.push(c));
        upstreamRes.on("end", () => {
          const raw = Buffer.concat(chunks);
          const acceptsGzip = (req.headers["accept-encoding"] ?? "").includes(
            "gzip"
          );
          if (acceptsGzip) {
            const compressed = zlib.gzipSync(raw);
            res.writeHead(200, { "Content-Encoding": "gzip" });
            res.end(compressed);
          } else {
            res.writeHead(200);
            res.end(raw);
          }
        });
      }
    );
    upstream.end();
  });
  server.listen(0);
  return server;
}

function main(): void {
  const backend = startBackend();
  const backendPort = (backend.address() as AddressInfo).port;
  const gateway = startGateway(backendPort);
  const gatewayPort = (gateway.address() as AddressInfo).port;

  const req = http.request(
    {
      host: "127.0.0.1",
      port: gatewayPort,
      path: "/orders/42",
      method: "GET",
      headers: { Authorization: "Bearer demo-token", "Accept-Encoding": "gzip" },
    },
    (res) => {
      const chunks: Buffer[] = [];
      res.on("data", (c: Buffer) => chunks.push(c));
      res.on("end", () => {
        const raw = Buffer.concat(chunks);
        const encoding = res.headers["content-encoding"];
        const body = encoding === "gzip" ? zlib.gunzipSync(raw) : raw;
        console.log("status:", res.statusCode);
        console.log("content-encoding:", encoding);
        console.log("body:", body.toString());

        const req2 = http.request(
          { host: "127.0.0.1", port: gatewayPort, path: "/orders/42", method: "GET" },
          (res2) => {
            res2.on("data", () => {});
            res2.on("end", () => {
              console.log("unauthenticated status:", res2.statusCode);
              backend.close();
              gateway.close();
            });
          }
        );
        req2.end();
      });
    }
  );
  req.end();
}

main();
```

Compiled with `tsc --target es2020 --module commonjs --lib es2020 --types
node --strict gateway.ts` and run with `node gateway.js`. The run produced
this output.

```text
status: 200
content-encoding: gzip
body: order-service reply for /orders/42
unauthenticated status: 401
```

### Go, go1.26.4 darwin/arm64, executed 2026-08-02

```go
package main

import (
	"compress/gzip"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"strings"
)

// backend is a plain, unauthenticated HTTP handler. It knows nothing about
// TLS, tokens, or compression. It only produces content.
func backend(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "order-service reply for %s, forwarded-proto=%s",
		r.URL.Path, r.Header.Get("X-Forwarded-Proto"))
}

// gzipResponseWriter wraps the ResponseWriter so the gateway can compress
// whatever the backend writes, without the backend knowing compression
// happened.
type gzipResponseWriter struct {
	http.ResponseWriter
	gz *gzip.Writer
}

func (g gzipResponseWriter) Write(b []byte) (int, error) {
	return g.gz.Write(b)
}

// offloadingGateway terminates the client-facing concerns, authentication,
// compression negotiation, and the X-Forwarded-* header contract, then
// forwards a plain request to the backend over a proxy the backend never
// sees as anything but a normal caller.
func offloadingGateway(backendURL *url.URL) http.Handler {
	proxy := httputil.NewSingleHostReverseProxy(backendURL)
	proxy.ModifyResponse = func(resp *http.Response) error {
		resp.Header.Del("Content-Length")
		return nil
	}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer demo-token" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		r.Header.Set("X-Forwarded-Proto", "https")
		r.Header.Set("X-Forwarded-For", r.RemoteAddr)

		if strings.Contains(r.Header.Get("Accept-Encoding"), "gzip") {
			w.Header().Set("Content-Encoding", "gzip")
			gz := gzip.NewWriter(w)
			defer gz.Close()
			proxy.ServeHTTP(gzipResponseWriter{ResponseWriter: w, gz: gz}, r)
			return
		}
		proxy.ServeHTTP(w, r)
	})
}

func main() {
	be := httptest.NewServer(http.HandlerFunc(backend))
	defer be.Close()

	beURL, err := url.Parse(be.URL)
	if err != nil {
		log.Fatal(err)
	}

	gw := httptest.NewServer(offloadingGateway(beURL))
	defer gw.Close()

	req, _ := http.NewRequest("GET", gw.URL+"/orders/42", nil)
	req.Header.Set("Authorization", "Bearer demo-token")
	req.Header.Set("Accept-Encoding", "gzip")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()

	fmt.Println("status:", resp.Status)
	fmt.Println("content-encoding:", resp.Header.Get("Content-Encoding"))

	var reader io.Reader = resp.Body
	if resp.Header.Get("Content-Encoding") == "gzip" {
		gzr, err := gzip.NewReader(resp.Body)
		if err != nil {
			log.Fatal(err)
		}
		defer gzr.Close()
		reader = gzr
	}
	body, _ := io.ReadAll(reader)
	fmt.Println("body:", string(body))

	req2, _ := http.NewRequest("GET", gw.URL+"/orders/42", nil)
	resp2, err := http.DefaultClient.Do(req2)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("unauthenticated status:", resp2.Status)
}
```

Run with `go run main.go`. The run produced this output.

```text
status: 200 OK
content-encoding: gzip
body: order-service reply for /orders/42, forwarded-proto=https
unauthenticated status: 401 Unauthorized
```

The `ModifyResponse` hook that strips the backend's `Content-Length` header
before compressing is not decoration. Without it, the gateway would forward
the backend's original, uncompressed length while writing fewer, compressed
bytes onto the wire, and the client would truncate the response waiting for
bytes that never arrive. This is a concrete, working instance of the
mismatched-content-length failure documented in dimension 11.

### Python, Python 3.14.6, executed 2026-08-02

```python
"""
Gateway Offloading, demonstrated with only the standard library.

A backend thread answers plain HTTP with no compression, no auth check.
A gateway thread terminates those two cross-cutting concerns, it checks
a bearer token and gzip-compresses the body, then forwards to the
backend as a plain, uncompressed, unauthenticated internal call.
"""

import gzip
import http.client
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class Backend(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"order-service reply for {self.path}".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


class Gateway(BaseHTTPRequestHandler):
    backend_port: int = 0

    def do_GET(self):
        if self.headers.get("Authorization") != "Bearer demo-token":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"unauthorized")
            return

        conn = http.client.HTTPConnection("127.0.0.1", Gateway.backend_port)
        conn.request("GET", self.path)
        upstream = conn.getresponse()
        raw = upstream.read()
        conn.close()

        accepts_gzip = "gzip" in self.headers.get("Accept-Encoding", "")
        if accepts_gzip:
            payload = gzip.compress(raw)
            self.send_response(200)
            self.send_header("Content-Encoding", "gzip")
        else:
            payload = raw
            self.send_response(200)

        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass


def start(handler_cls, port=0):
    server = HTTPServer(("127.0.0.1", port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main():
    backend_server = start(Backend)
    Gateway.backend_port = backend_server.server_address[1]
    gateway_server = start(Gateway)
    gateway_port = gateway_server.server_address[1]

    conn = http.client.HTTPConnection("127.0.0.1", gateway_port)
    conn.request(
        "GET",
        "/orders/42",
        headers={"Authorization": "Bearer demo-token", "Accept-Encoding": "gzip"},
    )
    resp = conn.getresponse()
    body = resp.read()
    encoding = resp.getheader("Content-Encoding")
    print("status:", resp.status)
    print("content-encoding:", encoding)
    decoded = gzip.decompress(body) if encoding == "gzip" else body
    print("body:", decoded.decode())
    conn.close()

    conn2 = http.client.HTTPConnection("127.0.0.1", gateway_port)
    conn2.request("GET", "/orders/42")
    resp2 = conn2.getresponse()
    resp2.read()
    print("unauthenticated status:", resp2.status)
    conn2.close()

    backend_server.shutdown()
    gateway_server.shutdown()


if __name__ == "__main__":
    main()
```

Run with `python3 gateway.py`. The run produced this output.

```text
status: 200
content-encoding: gzip
body: order-service reply for /orders/42
unauthenticated status: 401
```

Java, Rust, and Swift were not written up here. The pattern's substance is
in the protocol-level transformation, terminate one connection, apply a
cross-cutting rule, open a second connection, and that shape is
network-library idiom rather than language idiom. A Java example would
repeat the same `HttpServer` plus manual header manipulation shown in
Python, and a Rust example would repeat the same `hyper` or raw
`TcpListener` plumbing shown in Go, without surfacing a genuinely different
facet of the pattern. The three languages above were chosen because they
span a compiled, statically typed systems language with an idiomatic
reverse-proxy type in its standard library, an interpreted, dynamically
typed scripting language with only bare sockets, and a transpiled,
statically typed language built specifically for the async I/O shape this
pattern requires, which together cover the range of implementations a reader
is likely to meet in production.

## 9. Known production uses

1. **Azure Application Gateway.** Microsoft's own managed load balancer is
   the reference implementation the Gateway Offloading catalog entry is
   written against, and it documents TLS termination as its default mode,
   stating that "Application Gateway supports TLS termination at the
   gateway," after which, by default, traffic reaches the backend servers
   unencrypted ([Microsoft Learn, Enabling end to end TLS on Azure
   Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/ssl-overview),
   verified 2026-08-02).

2. **AWS Application Load Balancer.** AWS documents the same termination
   behavior for its HTTPS listeners, "the load balancer uses a server
   certificate to terminate the front-end connection and then decrypt
   requests from clients before sending them to the targets" ([AWS
   documentation, Create an HTTPS listener for your Application Load
   Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html),
   verified 2026-08-02), and it draws the explicit line against the pattern
   with its Network Load Balancer TCP passthrough mode for traffic that
   must stay encrypted end to end without gateway involvement.

3. **NGINX.** The open source reverse proxy is the appliance Microsoft's
   own Gateway Offloading example uses to demonstrate the pattern, with a
   worked `ssl_certificate` and `proxy_pass` configuration that terminates
   TLS and forwards plain HTTP, setting `X-Forwarded-Proto https` and
   `X-Real-IP` so the backend can still reconstruct facts about the
   original client ([Microsoft Learn, Gateway Offloading pattern,
   Example](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
   verified 2026-08-02).

4. **Envoy Proxy.** Envoy is the default data plane for Istio and is used
   standalone as an edge and sidecar proxy across many CNCF projects. Its
   own documentation states it "supports both TLS termination in listeners
   as well as TLS origination when making connections to upstream
   clusters" ([Envoy Proxy documentation, TLS overview](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/security/ssl),
   verified 2026-08-02), which is the terminate-and-re-encrypt variant
   described in dimension 8, applied per hop across a mesh rather than once
   at a single network edge.

5. **Kubernetes Ingress.** The Kubernetes API itself documents SSL
   termination as one of the three defining capabilities of an Ingress
   resource, alongside load balancing and name-based virtual hosting
   ([Kubernetes documentation, Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/#tls),
   verified 2026-08-02), and every major Ingress controller implementation,
   ingress-nginx, the AWS Load Balancer Controller, and Traefik among them,
   implements this by terminating client TLS at the controller and
   forwarding plain HTTP to pod IPs by default.

## 10. Consequences

**Positive.**

- Certificate lifecycle work concentrates in one place instead of
  replicating across every backend instance, which Microsoft's catalog
  states directly reduces both administrative overhead and deployment
  error risk ([Microsoft Learn, Gateway Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02).
- Backend instances spend their CPU budget on application logic instead of
  cryptographic handshakes, which both Azure's and NGINX's documentation
  name as the direct payoff of moving TLS work off the application tier
  ([Microsoft Learn, Enabling end to end TLS on Azure Application
  Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/ssl-overview);
  [NGINX documentation, Configuring HTTPS servers](https://docs.nginx.com/nginx/admin-guide/security-controls/terminating-ssl-http/),
  both verified 2026-08-02).
- TLS session caching becomes effective, because every client's repeat
  connections land at the same terminating point instead of being spread
  across independently-caching backend instances.
- A minimum, consistent level of logging and monitoring exists for every
  request even when a specific backend team forgot to instrument their
  service, per Microsoft's stated benefit ([Microsoft Learn, Gateway
  Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02).
- Specialized concerns, security hardening, WAF rule tuning, protocol
  negotiation, can be owned by a team with the right expertise, without
  every application team re-implementing the same concern to a different
  standard.
- Fine-grained TLS version and cipher policy can be enforced centrally,
  which is how a platform can raise its minimum TLS version fleet-wide in
  one change, the way Azure enforced TLS 1.2 as the minimum across
  Application Gateway on a single published date rather than coordinating
  the change across every backend team separately.

**Negative.**

- The gateway becomes a single point of failure unless it is deployed with
  redundancy, and Microsoft states this as a mandatory consideration rather
  than an optional one, "avoid single points of failure by running multiple
  instances of your gateway" ([Microsoft Learn, Gateway Offloading
  pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02).
- The gateway becomes a capacity limit for the whole system if it is
  undersized, and every backend behind it inherits that limit regardless
  of how much headroom the backends themselves have.
- Traffic between gateway and backend is unencrypted by default in the
  simplest deployment shape, which is a real exposure on any network
  segment that is not fully trusted, and closing that gap costs back some
  of the CPU savings the pattern was adopted for.
- A gateway that grows beyond cross-cutting concerns into domain logic
  becomes a shared, hard-to-test dependency for every team behind it, and
  Microsoft's own guidance treats this as a misuse to actively avoid rather
  than a natural extension of the pattern ([Microsoft Learn, Gateway
  Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
  verified 2026-08-02).
- Debugging shifts in character. A problem that used to be visible on one
  backend instance's logs may now originate at the gateway, and a team
  without access to the gateway's configuration or logs cannot fully
  diagnose a request that failed before it reached their service.
- Adding the pattern where it was not present before is itself a migration
  with its own risk, every backend's assumptions about the scheme, client
  IP, and headers it receives must be re-checked against what the gateway
  now injects or strips.

## 11. Failure modes and misuse

**Symptom.** Every request reaching a service that logs client IPs shows
the gateway's own IP address, and IP-based rate limiting or geoblocking
that used to work per real client now applies to the whole gateway as one
address.
**Cause.** The gateway terminates the client's connection and opens its own
connection to the backend, so from the backend's point of view the peer
address on the socket is the gateway, not the original client, unless the
gateway explicitly carries the original address forward in a header.
**Fix.** Configure the gateway to set `X-Forwarded-For` and
`X-Forwarded-Proto` on every forwarded request, per the pattern in
Microsoft's own NGINX example, and configure the backend framework to trust
that header only when it comes from the known gateway address, never from
an arbitrary client, or a malicious client can spoof its own IP by setting
the header itself before the request reaches an untrusted-by-default proxy.

**Symptom.** A response the gateway compresses arrives at the client
truncated, or the client hangs waiting for bytes that never come, even
though the gateway logs show a `200` status.
**Cause.** The backend's original `Content-Length` header describes the
uncompressed body size. If the gateway compresses the body but forwards the
original header unchanged, the client reads exactly that many bytes and
either stops early, because the compressed body is shorter, or waits
forever for bytes that will never arrive, because the compressed body ends
before the declared length is reached. This is not a hypothetical, it is
the exact bug reproduced and fixed in dimension 8's Go example, where
`resp.Header.Del("Content-Length")` had to be added before the fix worked.
**Fix.** Strip or recompute `Content-Length` whenever a gateway transforms
a response body, or switch to chunked transfer encoding, which does not
depend on a pre-declared length at all.

**Symptom.** Requests that used to succeed start failing intermittently
with backend health checks reporting the backend as unreachable, right
after end-to-end TLS was turned on between gateway and backend.
**Cause.** The backend's certificate does not chain to a CA the gateway
trusts, or the certificate's common name does not match the hostname the
gateway is configured to expect. Azure's documentation is explicit about
this exact failure path, describing that the gateway "will then check to
see if the certificate of the issuing CA was issued by a trusted CA, and so
on until either a trusted CA is found... or no trusted CA can be found (at
which point the application gateway will mark the backend unhealthy)"
([Microsoft Learn, Enabling end to end TLS on Azure Application
Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/ssl-overview),
verified 2026-08-02).
**Fix.** Upload the backend's full certificate chain, root and
intermediates, to the gateway's trusted root store, and confirm the
hostname the gateway's backend HTTP setting sends as SNI matches the
certificate's common name exactly.

**Symptom.** A gateway configuration change, meant to add a new discount
rule for a marketing promotion, ships and now every team whose service
sits behind the same gateway has to review the change before their next
deploy, and the platform team fields questions about business rules they
did not write.
**Cause.** Business logic was offloaded to the gateway instead of a
backend service. Microsoft's own considerations section names this exact
failure by prohibition rather than description, stating flatly, "business
logic should never be offloaded to the gateway" ([Microsoft Learn, Gateway
Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02), precisely because the gateway is shared
infrastructure and a domain rule embedded in it has an implicit blast
radius across every team that depends on the gateway.
**Fix.** Move the rule into the owning service. If the rule genuinely needs
to run before the request reaches that service, for example a feature flag
that should short-circuit routing, keep the gateway's role limited to the
mechanical act of routing on a flag value it does not interpret, and let
the owning service decide what the flag means.

**Symptom.** A load test shows the backend fleet sitting well under its
CPU budget while p99 latency climbs and the gateway's own CPU utilization
approaches 100 percent.
**Cause.** The gateway was sized for the traffic volume at rollout time and
traffic grew, or the gateway is doing more per-request work than it was
sized for, most commonly because TLS session caching was not configured
and every connection is paying the full handshake cost. Microsoft's issues
list names this risk directly and ties gateway capacity planning to the
whole application's scaling requirements ([Microsoft Learn, Gateway
Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02).
**Fix.** Scale the gateway horizontally behind a network load balancer that
itself does not terminate TLS, enable TLS session ticket or session ID
caching, and confirm the gateway's own metrics, not only the backend
fleet's, are part of the standard capacity dashboard.

## 12. Trade-off matrix

| Force | Gateway Offloading | TLS Passthrough (no offload) | Sidecar Mesh (Envoy-style) | Per-service TLS termination |
|---|---|---|---|---|
| Backend CPU cost per connection | Low, TLS and compression work moves off the backend entirely | Unchanged, backend still terminates its own TLS | Low at the app container, but every sidecar still pays a handshake cost | High, every instance pays full handshake cost |
| Certificate management surface | One place | One place at the network load balancer, but the backend still separately manages its own cert for the passthrough target | Many, one per sidecar, but commonly automated via a mesh control plane | Many, one per backend instance, manual or per-team automated |
| End-to-end confidentiality | Requires explicit re-encryption to hold, off by default | Held automatically, the load balancer never sees plaintext | Held automatically via per-hop mTLS | Held automatically, no intermediate decryption point |
| Single point of failure risk | Real, mitigated only by running the gateway itself redundantly | Lower, a TCP passthrough load balancer is simpler and has less to misconfigure | Distributed, no single sidecar failure takes down the whole mesh | None at the network layer, though a shared certificate bug can still hit every instance at once |
| Operational ownership | Centralized, one team can own gateway policy | Split, load balancer team owns balancing, backend team still owns TLS | Distributed but standardized, platform team owns mesh config, applied uniformly | Fully decentralized, every backend team owns its own TLS stack |
| Content-based routing possible | Yes, gateway sees plaintext | No, load balancer cannot inspect encrypted bytes | Yes, at each sidecar | Not applicable, there is no intermediary |
| Best fit | Many backends, shared TLS or cross-cutting policy, trusted internal network or willingness to re-encrypt | Regulated traffic that must never be decrypted before reaching its final destination | Zero-trust internal networks needing per-hop mTLS without a single edge bottleneck | Small deployments where a shared gateway is not yet justified, or hard isolation between backends is required |

## 13. Related and incompatible patterns

**Gateway Aggregation** is the sibling pattern most often confused with
this one because both live in the same Microsoft catalog family and both
are commonly hosted on the same physical gateway. Gateway Aggregation fans
one client call out into several backend calls and merges the results,
which changes how many backends a single client request touches. Gateway
Offloading changes what a single request looks like before it reaches
exactly one backend or backend pool. The two compose cleanly, a gateway can
terminate TLS, check a bearer token, and then fan the now-decrypted,
now-authenticated request out to three backend services in the same
request lifecycle.

**Backends for Frontends** shapes the response contract per client type,
mobile, web, or a partner API, and commonly sits behind or alongside a
Gateway Offloading layer rather than replacing it, because BFF is about
response shaping and Gateway Offloading is about connection-level and
cross-cutting request handling. A BFF instance still benefits from having
its own TLS termination and authentication handled by an offloading layer
in front of it.

**Circuit Breaker** and **Bulkhead** protect the gateway itself, and
protect the backend from the gateway, once the gateway has become a
critical path component. A gateway that offloads authentication by calling
out to a separate token-issuing service needs a circuit breaker around that
call, or a slow token service degrades every request the gateway handles,
not only the ones that would have failed authentication anyway.

**Rate Limiting** and **Throttling** are two of the concerns most
frequently offloaded into the same gateway that terminates TLS, because
both need visibility into every request across every backend to enforce a
limit correctly, which is exactly the vantage point a terminating gateway
already has.

**Federated Identity** and Gateway Offloading combine when the offloaded
authentication concern is not a simple bearer token check but a full OIDC
or SAML flow, in which case the gateway becomes the relying party that
terminates the identity protocol on behalf of every backend, the same
structural move as terminating TLS, applied to an authentication protocol
instead of a transport protocol.

**Ambassador** is a narrower, per-service variant of the same idea, a
sidecar deployed alongside one service instance rather than shared across
a whole pool. Where Gateway Offloading centralizes a concern for many
backends behind one shared component, Ambassador decentralizes the same
kind of cross-cutting logic, retries, circuit breaking, TLS, back down to
one sidecar per instance, trading the single point of failure for
per-instance operational overhead. The two are not incompatible, a mesh
architecture frequently uses Ambassador-style sidecars at the backend edge
and a Gateway Offloading-style edge proxy at the internet-facing edge at
the same time, each terminating TLS for a different hop.

No pattern in this catalog is flatly incompatible with Gateway Offloading
in the way that, for example, two conflicting locking strategies would be.
The closest thing to an incompatibility is architectural rather than
technical, a system built on strict end-to-end encryption with no trusted
intermediary, such as a design that deliberately avoids any component that
can read plaintext between two parties, cannot adopt the plain-hop variant
of this pattern at all and can only use the re-encrypting variant, which
weakens the "no intermediary can read the plaintext" property it was
otherwise providing.

## 14. Refactoring path in and out

**Introducing the pattern into a system that does not have it.**

1. Identify the concern to offload first by finding the one that is most
   duplicated and least differentiated across services. Certificate
   management is almost always the highest-value first target, because it
   is both the most duplicated and the most error-prone concern named in
   dimension 2's sourced problem statement.
2. Stand up the gateway in parallel with the existing direct-to-backend
   path rather than cutting over immediately, routing a small percentage of
   traffic or a single non-critical route through it first.
3. Configure the gateway to inject `X-Forwarded-Proto`, `X-Forwarded-For`,
   and `X-Forwarded-Host` on every request it forwards, and audit every
   backend service for any code that reads the raw scheme or the raw
   socket peer address directly, since that code will now read the
   gateway's values instead of the client's unless it is updated to trust
   the forwarded headers.
4. Move certificates off backend instances only after the gateway path has
   proven correct end to end, including for the failure branches in
   dimension 7, an unauthenticated request and a malformed token, because a
   premature cutover that removes backend certificates before the gateway
   is trusted leaves no fallback path.
5. Add the redundancy the pattern requires, per dimension 4's
   non-applicability caution, before removing the old direct path
   entirely, since a single gateway instance is now a single point of
   failure for every backend that depends on it.
6. Offload the next concern, authentication, rate limiting, or
   compression, only after the first concern is stable in production,
   rather than bundling several new cross-cutting behaviors into one
   cutover.

**Removing the pattern, or scoping it back, once it has stopped earning its
place.**

1. Identify what actually forced the removal. The two most common triggers
   are the gateway acquiring business logic it should never have held, per
   dimension 11's fourth failure mode, or a hard requirement for
   end-to-end confidentiality that the terminating gateway cannot satisfy
   without re-encryption.
2. If the trigger is business logic creep, extract the offending rule back
   into the owning service first, and confirm the gateway's remaining
   configuration is purely mechanical, TLS, headers, rate limits, before
   deciding whether the gateway itself should be removed or simply
   corrected.
3. If the trigger is a confidentiality requirement, evaluate the
   re-encrypting end-to-end TLS variant from dimension 8 before removing
   the gateway outright, since it preserves the certificate-management and
   routing benefits while closing the plaintext gap.
4. If the gateway is being removed entirely, restore certificate
   management, authentication, and any other offloaded concern to each
   backend instance before decommissioning the gateway, not after, so
   there is no window where a request reaches a backend with neither the
   gateway's protection nor the backend's own.
5. Remove the gateway's traffic share gradually, the same way it was
   introduced, rather than in one cutover, and keep the forwarded-header
   trust logic in backend services intact until the last request has
   stopped arriving through the old gateway path, since removing that
   trust logic too early will misattribute the scheme and client address
   for any request that still transits the gateway during the transition
   window.

## 15. Testing and verification

Testing a gateway that offloads cross-cutting concerns splits cleanly into
two layers, and conflating them is the most common testing mistake with
this pattern.

**Testing the gateway in isolation.** Stand the gateway up against a
minimal, purpose-built backend double, exactly the shape demonstrated in
dimension 8's three code examples, where the backend handler does nothing
but echo back what it received. This isolates the gateway's own behavior,
does it reject a request with no token, does it correctly set the
forwarded headers, does it compress only when the client advertised
support, from the backend's behavior, and it is the only reliable way to
assert the negative cases, an unauthenticated request never reaching the
backend at all, which is exactly what the Go and Python examples above
assert by checking a `401` status and, in a fuller test, by asserting the
backend double received zero calls for that request.

**Testing the backend assuming the gateway's contract.** The backend
should never be tested with real TLS or a real authentication flow in its
own unit or integration suite, because by the time a request reaches the
backend, TLS is already terminated and the token is already validated. What
the backend's tests must cover instead is its trust boundary, does it
correctly read `X-Forwarded-Proto` to decide whether to set a secure
cookie, does it correctly use `X-Forwarded-For` for its own logging without
trusting a client-supplied version of the same header from outside the
gateway's network. A backend test suite that includes a fake `Authorization`
header check duplicates work the gateway already does and gives a false
sense that the backend enforces its own security when in production it
never sees an unauthenticated request in the first place.

**Testing the header-spoofing boundary explicitly.** Because backends
trust the gateway's forwarded headers, a security-relevant test must assert
that the backend is unreachable except through the gateway's network path,
or that the backend itself strips and re-sets forwarded headers on any
request that did not arrive from the gateway's known address range. This
is not covered by testing the gateway or the backend individually, it is a
property of the deployment topology and it is most reliably verified with
a network policy test or an integration test that attempts to reach the
backend directly and asserts the connection is refused or the spoofed
header is dropped.

**Testing the content-length and compression interaction.** Dimension 11's
second failure mode is exactly the kind of bug that only shows up under a
real network round trip, not under a mock that hands the response body to
the test as an in-memory byte slice. An integration test should assert
that a full round trip through a real TCP connection, decompressing
whatever the gateway actually wrote to the wire, produces the expected
body, which is precisely what all three code examples in dimension 8 do by
running real `HTTPServer` instances on real sockets rather than mocking the
transport layer.

**Testing failover.** With multiple gateway instances behind a network
load balancer, a test should kill one gateway instance mid-load-test and
assert that in-flight requests to the surviving instances are unaffected
and that TLS session caching, where used, degrades gracefully rather than
forcing every client to a full handshake simultaneously, which would itself
be a load spike on the surviving instances at the exact moment they can
least afford one.

## 16. Observability signals

**At the gateway.** TLS handshake rate and handshake latency percentiles,
separated from full handshakes and resumed handshakes via session cache,
because a rising ratio of full handshakes to resumed handshakes with a
stable client population is a leading indicator that the session cache is
undersized or is being evicted too aggressively before it can be reused.
Certificate expiry date as a continuously exported metric, not only an
alert that fires once close to expiry, so a dashboard can show the whole
fleet's certificate health at a glance. Request rate broken down by
authentication outcome, accepted, rejected for missing token, rejected for
invalid signature, rejected for expired token, because a spike in one
specific rejection reason usually points at a specific root cause, a
client shipping stale tokens after a deploy, or a key rotation that
invalidated tokens signed under the old key before every client had
refreshed.

**Correlation.** Every request the gateway forwards should carry a
correlation identifier the gateway generates or propagates, which Azure's
own guidance names directly, "if you need to track transactions, consider
generating correlation IDs for logging purposes" ([Microsoft Learn, Gateway
Offloading pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading),
verified 2026-08-02). Without this, a request that fails at the backend
cannot be traced back to the specific gateway instance and client
connection that produced it, and a request that fails at the gateway,
before it ever reaches a backend, leaves no trace in any backend's logs at
all, which makes gateway-side logging the only record of that failure
class.

**At the backend.** The distribution of `X-Forwarded-Proto` and
`X-Forwarded-For` values received, which should show exactly the gateway's
known address as the only source, ever, in a correctly locked-down
deployment, and any deviation is either a misconfiguration or an attempted
bypass of the gateway that should be investigated immediately rather than
silently accepted.

**A healthy instance looks like** a steady, low ratio of full to resumed
TLS handshakes, a rejection-reason distribution led by expected token
expiry rather than signature failures, gateway CPU utilization with
comfortable headroom above the traffic's peak, and every backend request
carrying the same, single known gateway IP as its forwarded source.

**A failing instance looks like** a climbing full-handshake ratio with flat
client counts, a rejection-reason distribution shifting toward signature
failures after a deploy, correlating with a key rotation that was not
coordinated with token issuance, gateway CPU pinned near its limit while
backend CPU sits idle, and, most seriously, backend requests arriving with
forwarded headers from an address outside the known gateway range, which
indicates the gateway is being bypassed.

## 17. Security and privacy implications

The gateway that terminates TLS holds the private key for the domain's
certificate, which makes it the single highest-value target in the whole
request path for an attacker who wants to read or manipulate traffic for
that domain. Compromising the gateway compromises every backend behind it
simultaneously, which is the direct security cost of the same
centralization that makes certificate management operationally simpler.
This is not a hypothetical trade-off, it is the same coin as dimension 3's
operational simplicity versus centralization risk, viewed through a
security lens instead of an operations lens.

Plaintext exposure between gateway and backend is a real and easily
overlooked privacy and confidentiality gap. Any personal data, an
authentication token, a payment field, a health record, that transits that
hop in the plain-hop variant of the pattern is readable by anyone with
visibility into that network segment, which matters in a shared cloud
network, a multi-tenant Kubernetes cluster's pod network, or any
environment where the assumption "internal traffic is trusted" does not
actually hold. This is precisely why the end-to-end TLS variant exists, and
why regulated data flows, payment card data, health records, or any data
covered by a data-in-transit encryption requirement, commonly cannot use
the plain-hop variant at all without a documented compensating control
around the internal network segment itself.

Forwarded headers are an authentication bypass surface if the backend does
not validate their source. `X-Forwarded-For` and `X-Forwarded-Proto` are
plain, unsigned HTTP headers, and any client that can reach the backend
directly, bypassing the gateway, can set them to whatever value it wants.
A backend that trusts a client-controlled `X-Forwarded-Proto` header to
decide whether to mark a cookie `Secure`, or that trusts
`X-Forwarded-For` for IP-based access control, without also confirming
the request could only have arrived through the gateway, has reintroduced
exactly the vulnerability the gateway was meant to close. This is the
security angle behind failure mode one in dimension 11 and the
header-spoofing test in dimension 15, and it is the single most common
security defect specific to this pattern, because it is invisible in a
system that has never had a request reach the backend by any path other
than through the gateway, and only becomes exploitable the moment that
assumption breaks, which it will, whether through a misconfigured network
policy, a debug port left open, or a second entry point added later by a
team that did not know the header-trust assumption existed.

Consolidating authentication at the gateway does raise the security bar for
every backend, no backend can accidentally skip its own auth
check this way, which is a genuine positive, but it also means a bug in the
gateway's token validation logic is now a single point of failure for
authentication across the entire system, rather than an isolated bug in
one service. The blast radius of a gateway authentication defect is
strictly larger than the blast radius of the same class of defect in one
backend's own, independently-written auth code.

## 18. References

- Microsoft Learn, "Gateway Offloading pattern," Azure Architecture Center.
  https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-offloading,
  verified 2026-08-02.
- Microsoft Learn, "Enabling end to end TLS on Azure Application Gateway."
  https://learn.microsoft.com/en-us/azure/application-gateway/ssl-overview,
  verified 2026-08-02.
- AWS Documentation, "Create an HTTPS listener for your Application Load
  Balancer," Elastic Load Balancing User Guide.
  https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html,
  verified 2026-08-02.
- NGINX Documentation, "Configuring HTTPS servers," NGINX Admin Guide.
  https://docs.nginx.com/nginx/admin-guide/security-controls/terminating-ssl-http/,
  verified 2026-08-02.
- Envoy Proxy Documentation, "TLS overview," Architecture Overview,
  Security. https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/security/ssl,
  verified 2026-08-02.
- Kubernetes Documentation, "Ingress," Services, Load Balancing, and
  Networking. https://kubernetes.io/docs/concepts/services-networking/ingress/#tls,
  verified 2026-08-02.
- Microsoft Learn, "Gateway Aggregation pattern," Azure Architecture
  Center, cited here for the sibling-pattern boundary described in
  dimension 1 and dimension 13.
  https://learn.microsoft.com/en-us/azure/architecture/patterns/gateway-aggregation,
  verified 2026-08-02.
