---
name: Client Session State
slug: client-session-state
family: 06-enterprise-application-architecture
category: Base Patterns
aliases: [Cookie-Based Session, Stateless Session Token, Client-Side Session]
first_described: "Fowler, Patterns of Enterprise Application Architecture, 2002"
maturity: canonical
related: [server-session-state, database-session-state, remote-facade, data-transfer-object, identity-field]
incompatible_with: []
verified: 2026-08-02
---

# Client Session State

## 1. Name, aliases, and lineage

The canonical name is Client Session State, one of three sibling patterns
Martin Fowler grouped under the Base Patterns section of *Patterns of
Enterprise Application Architecture*, Addison-Wesley, 2002, alongside Server
Session State and Database Session State. Fowler frames all three as answers
to a single question, where does a web application's session, the sequence of
requests one user makes over a period of interaction, keep the data gathered
so far, given that HTTP itself supplies no such place because each request is
handled as if it were the first ([Fowler's own summary page for the
pattern](https://martinfowler.com/eaaCatalog/clientSessionState.html), verified
2026-08-02, which restates the book's own phrasing, "Stores session state on
the client.").

In day-to-day engineering conversation the pattern is called by several
looser names that mean the same design decision. Cookie-based session is the
name used when the mechanism is an HTTP cookie holding the session identifier
or the session data itself. Stateless session token is the name used when the
payload is a signed or encrypted token such as a JSON Web Token, because the
server keeps no session record between requests and every request carries
everything the server needs to authenticate and authorize it, defined in
Jones, Bradley, and Sakimura, RFC 7519, *JSON Web Token (JWT)*,
https://datatracker.ietf.org/doc/html/rfc7519, verified 2026-08-02, whose
abstract states plainly that a JWT is "a compact, URL-safe means of
representing claims to be transferred between two parties." Client-side
session is the generic term used across frameworks, Rails calls its default
mechanism `ActionDispatch::Session::CookieStore`, Django calls its equivalent
the `signed_cookies` session engine, and both terms are used interchangeably
with the other two here.

The pattern predates Fowler's catalog by years in practice. Cookies
themselves, the transport almost every implementation of Client Session State
relies on, were standardized as HTTP state by the IETF in RFC 2109 in 1997 and
later superseded by RFC 6265, Barth, *HTTP State Management Mechanism*,
https://datatracker.ietf.org/doc/html/rfc6265, verified 2026-08-02, whose
abstract states the header fields "can be used by HTTP servers to store state
(called cookies) at HTTP user agents, letting the servers maintain a stateful
session over the mostly stateless HTTP protocol." Fowler's contribution was
not the cookie mechanism itself, it was naming the architectural choice, that
state lives on the client rather than the server, as one option in a small
family of options, so a team can reason about the trade explicitly rather
than inheriting whatever a framework's default happened to be.

## 2. Problem and context

HTTP, as originally specified, is a stateless request-response protocol. Each
request a browser sends arrives at the server with no memory of any request
that came before it. A shopping cart, a partially completed multi-step form, a
logged-in user's identity, none of that exists unless something explicitly
carries it forward from one request to the next. The moment an application
needs to remember anything about a specific visitor across more than one HTTP
exchange, it needs a session, and that session's data has to live somewhere.

The concrete situation is familiar to anyone who has built a web application
with more than a single stateless page. A user logs in on request one. On
request two, three requests later, the application must know who that user
is without asking them to log in again. A user adds an item to a cart on the
product page, then continues shopping, then checks out, and the cart's
contents must survive across all of those page loads. A multi-step signup
wizard collects a name on step one and an address on step two, and step three
needs both. None of these requests are guaranteed to be handled by the same
server process, especially once an application runs behind a load balancer
across more than one machine, so "the server remembers" is not automatically
true unless the architecture is deliberately built to make it true.

The context in which Client Session State specifically becomes the right
answer, rather than one of its two siblings, is a context where the team has
already decided the session needs to survive server restarts and horizontal
scaling with minimal server-side infrastructure, where the session's contents
are small enough to fit inside an HTTP header's practical size limits, and
where the team is willing to accept that the data, unless encrypted, is
visible to the party holding it. It is the option that trades server-side
storage cost and coordination cost for client-side storage cost and a
different, harder-to-reason-about set of security obligations.

## 3. Forces

- **Statelessness versus memory.** HTTP has no memory. Something must supply
  it. The tension is where that memory lives, on the machine that answers the
  next request (which may not be the machine that answered this one), or
  bundled into the request itself so it travels with the client regardless of
  which server answers.
- **Horizontal scalability versus per-server simplicity.** If session data
  lives on a specific server, in that process's memory for instance, a load
  balancer must route every request in a session back to that same server,
  which is the sticky-session problem. Client Session State sidesteps this
  entirely, because any server that can validate the token can serve any
  request, at the cost of pushing the data itself onto the network on every
  request.
- **Server cost versus client cost.** Server Session State and Database
  Session State pay a server-side storage and lookup cost per active session.
  Client Session State pays a per-request bandwidth cost, the data rides on
  every request, and a client-side storage cost, cookies are capped, and RFC
  6265 section 6.1 notes practical user-agent limits of at least 4096 bytes
  per cookie, verified 2026-08-02.
- **Confidentiality versus transparency.** Data placed on the client is, by
  default, visible to whoever holds the client, unless it is encrypted rather
  than merely encoded or signed. A signed cookie or a signed JWT is tamper
  evident, not secret. Django's own documentation for its `signed_cookies`
  session engine states this without hedging, "The session data is signed
  but not encrypted... When using the cookies backend the session data can
  be read by the client" (Django Software Foundation, *Django documentation,
  How to use sessions*, https://docs.djangoproject.com/en/5.2/topics/http/sessions/,
  verified 2026-08-02).
- **Revocability versus statelessness.** A server-held session can be deleted
  the instant an administrator wants to end it, because the server owns the
  record. A client-held session that the server never records cannot be
  revoked by deleting a server-side row, because there is no server-side row.
  Revocation has to be engineered separately, typically through short
  expiries plus a deny list, which reintroduces the server-side state the
  pattern was chosen to avoid.
- **Cognitive load and team topology.** Client Session State is conceptually
  simple to a single-service team, validate the signature and trust the
  claims, but becomes a coordination problem the moment more than one service
  must independently verify the same token, because now key rotation, clock
  skew tolerance, and claim schema changes have to be agreed and versioned
  across every verifying party.

## 4. Applicability and non-applicability

Reach for Client Session State when:

- The deployment target is horizontally scaled and stateless server
  processes are a design goal, so no request needs to be routed to a
  specific server instance to find its session data.
- The session payload is genuinely small, an identity, a small set of role
  claims, a cart reference by ID rather than a full cart, a CSRF token, a
  handful of UI preferences.
- The application already needs a signed or encrypted token for another
  reason, most commonly authenticating calls between independently deployed
  services, such as an API gateway validating a bearer token issued by an
  identity provider, defined in Jones, Hardt, RFC 6750, *The OAuth 2.0
  Authorization Framework, Bearer Token Usage*,
  https://datatracker.ietf.org/doc/html/rfc6750, verified 2026-08-02, which
  states "any party in possession of a bearer token... can use it to get
  access to the associated resources."
- Operational simplicity for the storage layer matters more than instant
  server-side revocation, no session store to provision, back up, or keep
  available, because the store is the request itself.
- Server-side storage cost genuinely matters at the session's expected
  scale, for example a very high volume of anonymous or short-lived sessions
  where provisioning a session store to hold all of them would be materially
  more expensive than the bandwidth of shipping small tokens.

Do NOT reach for Client Session State when:

- The session must hold data too large to reasonably fit in a cookie or
  header on every request. A shopping cart with dozens of line items, a
  document being edited, or any object graph measured in kilobytes belongs
  on the server, referenced from the client by an identifier, which is
  exactly the shape Database Session State or Server Session State exist to
  provide.
- The data is sensitive and the team is not prepared to encrypt it, not
  merely sign it, and manage the encryption key's lifecycle. Signing proves
  the data was not tampered with, it does not hide the data from the holder.
- Instant, server-enforced revocation is a hard requirement, for example a
  "log out everywhere" or "immediately terminate this compromised session"
  feature with no acceptable propagation delay. A stateless token cannot be
  un-issued, it can only be allowed to expire or checked against a deny
  list, and a deny list is server-side state, which erases the pattern's
  central advantage.
- The client cannot be trusted to return the data unmodified and the
  integrity mechanism is weak or absent. An unsigned cookie an application
  trusts at face value is not Client Session State done correctly, it is a
  forgeable input channel. Fowler's own description of the pattern assumes
  the data is protected against tampering, and most production incident
  writeups involving this pattern trace back to that assumption being
  skipped.
- Regulatory or compliance requirements mandate that personal data never
  leave server-controlled storage, which some data residency and privacy
  regimes effectively require regardless of encryption, because the data
  crosses network boundaries to the client's machine even if unreadable
  there.
- The team needs to change the shape of session data frequently. Every field
  added or removed from a client-held token or cookie is a compatibility
  concern across every process that has already issued a token in the old
  shape and every process that must still accept it during rollout, whereas
  a server-side session store's schema can usually be migrated in place.

## 5. Structure

- **Session Owner** (the client, typically a browser or an API consumer).
  Holds the session state, physically, between requests. Presents it back to
  the server on every subsequent request, carried either automatically, a
  cookie replayed by the browser according to its domain and path scoping
  rules, or explicitly, a bearer token attached to an `Authorization` header
  by the calling code.
- **Session Encoder.** The server-side component that, at the moment the
  session is established or updated, serializes the session's data into a
  transportable representation and, critically, protects it. It signs the
  data so tampering is detectable, encrypts it so its contents are not
  readable by the holder, or both. This is the component responsible for the
  pattern's entire security posture, get it wrong and every other
  participant inherits the flaw.
- **Session Verifier.** The server-side component, invoked on every
  incoming request, that extracts the transported representation, verifies
  its signature or decrypts it, checks any embedded expiry, and reconstructs
  the session data, or rejects the request if verification fails.
- **Transport.** The concrete channel the encoded state rides on, an HTTP
  cookie per RFC 6265, an `Authorization: Bearer` header per RFC 6750, a
  hidden form field, or a query parameter, the least safe of the four,
  because URLs are logged, cached, and appear in browser history.
- **Session Format.** The concrete encoding, a delimited key-value string, a
  base64-encoded serialized object with a MAC, or a structured, standardized
  format such as a JSON Web Token, which itself has three parts, a header
  naming the signing algorithm, a payload of claims, and a signature, per
  RFC 7519 section 3.

## 6. ASCII structure diagram

```
+------------------------------------------------------------------+
|                              Client                               |
|                                                                    |
|   +------------------------------------------------------------+  |
|   |                    Session State (held here)                |  |
|   |  cookie: sid=eyJ1c2VyIjoiNDIiLCJyb2xlIjoiYWRtaW4ifQ.HMAC     |  |
|   +------------------------------------------------------------+  |
+---------------------------------|----------------------------------+
                                   | every request carries the token
                                   v
+------------------------------------------------------------------+
|                          Server (stateless)                       |
|                                                                    |
|   +----------------------+       +--------------------------+     |
|   |   Session Verifier     |------>|   Application logic      |     |
|   |  - checks signature    |      |   (reads decoded claims) |     |
|   |  - checks expiry       |      +--------------------------+     |
|   |  - rejects on failure  |                                       |
|   +----------------------+                                        |
|                                                                    |
|   +----------------------+                                        |
|   |   Session Encoder     |  (on login / state change, produces    |
|   |  - serializes claims   |   a fresh token sent back to client)  |
|   |  - signs / encrypts    |                                       |
|   +----------------------+                                        |
|                                                                    |
|   No per-session row, no session table, no sticky routing.        |
+------------------------------------------------------------------+
```

## 7. Dynamics

The two flows that matter are session establishment and every subsequent
request. A third, less obvious flow, session update, is worth separating out
because it is where most real-world defects appear.

```
LOGIN (session establishment)
------------------------------
Client                    Server
  |  POST /login (creds)     |
  |-------------------------->
  |                           | verify credentials
  |                           | build claims: {user_id, roles, exp}
  |                           | sign (and optionally encrypt) claims
  |  Set-Cookie: sid=<token>  |
  |<--------------------------|
  |  store cookie             |
  |                           |

SUBSEQUENT REQUEST (no server-side lookup)
-------------------------------------------
Client                    Server
  |  GET /orders  Cookie: sid=<token>
  |-------------------------->
  |                           | read token
  |                           | verify signature
  |                           | check exp claim
  |                           |    valid -> proceed with claims as identity
  |                           |    invalid/expired -> 401, no session found
  |  200 OK / 401             |
  |<--------------------------|

SESSION UPDATE (state changes mid-session)
--------------------------------------------
Client                    Server
  |  POST /cart/add {item}   |
  |-------------------------->
  |                           | read current token
  |                           | modify claims (e.g. cart_ref = "c_88f2")
  |                           | re-sign; produce a NEW token
  |  Set-Cookie: sid=<new>    |
  |<--------------------------|
  |  overwrite stored cookie  |
```

The subtlety in the update flow is that Client Session State has no
in-place mutation. Every change to the session produces an entirely new
signed artifact that must be sent back and must replace the old one on the
client. If a client makes two concurrent requests that both modify session
state, whichever response the client applies last silently wins, a lost-update
race with no built-in detection, because there is no shared row a database
transaction could lock. This is a direct consequence of the structure, not an
implementation bug, and it is the single most cited reason large mutable
session data does not belong in Client Session State.

## 8. Implementation variants

- **Signed, opaque cookie value (Rails default).** Rails' default session
  store, `ActionDispatch::Session::CookieStore`, serializes the session hash
  and stores it directly in a cookie rather than storing a reference to a
  server-side record. The Rails Security Guide states this plainly, "Rails
  `CookieStore` saves the session hash in a cookie on the client-side. The
  server retrieves the session hash from the cookie and eliminates the need
  for a session ID" (Rails core team, *Ruby on Rails Security Guide*,
  "Session Storage" section, verified 2026-08-02 via the guide's published
  content). The same guide is explicit about the consequence, "Cookies have a
  size limit of 4 kB. Use cookies only for data which is relevant for the
  session," and "Avoid storing sensitive data in cookies... Persist all data
  that is of more permanent nature on the server side," which is the
  framework's own documentation drawing the applicability boundary from
  dimension 4.
- **Signed cookie, framework-agnostic (Django `signed_cookies` engine).**
  Django ships four session backends and lets the team choose per
  application, the cookie-based one is explicitly opt-in rather than the
  default, set via `SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"`,
  and it uses Django's cryptographic signing utilities keyed by the
  project's `SECRET_KEY` (Django Software Foundation, *Django documentation,
  How to use sessions*, verified 2026-08-02). Django's default is actually
  the opposite pattern, database-backed sessions. This matters because it
  shows the same framework offering both this pattern and its
  sibling, Database Session State, as first-class, named choices.
  Understanding both siblings is part of correctly implementing either.
- **Standardized claims token (JSON Web Token).** Rather than an
  application-specific serialization, the state is encoded as a JWT, a
  base64url header, a base64url claims payload, and a signature, joined by
  periods, per RFC 7519 section 3. JWTs are the variant most often used
  across service boundaries, because the format is standardized, the same
  library that issues a token in one language can be verified by a library
  in another, and because the standard defines registered claims for
  expiry (`exp`), issuer (`iss`), and audience (`aud`) that give every
  verifying party a common vocabulary for the checks in dimension 15.
- **Encrypted token (not merely signed).** Where confidentiality matters and
  not only integrity, the payload is encrypted rather than only signed,
  either via a JWE (JSON Web Encryption) wrapper around the JWT claims, or
  via an application-level symmetric encryption of the serialized session
  before it is placed in the cookie, as ASP.NET Core's session cookie is.
  Microsoft's documentation states, "The session cookie is encrypted via
  `IDataProtector`" (Microsoft, *Session and app state in ASP.NET Core*,
  https://learn.microsoft.com/en-us/aspnet/core/fundamentals/app-state,
  verified 2026-08-02). This is worth flagging as its own variant because
  ASP.NET Core's built-in "Session state" feature is a hybrid, the cookie
  itself carries only a session identifier, encrypted, while the actual
  session values are cached server-side, keyed by that identifier, which is
  closer to Server Session State than to pure Client Session State. The same
  documentation warns "Don't store sensitive data in session state," a
  caution that applies to the hybrid form for a different reason, a shared
  server-side cache is still one more place the data lives.
- **Split payload (reference plus small claims).** A common pragmatic
  compromise, keep a genuinely small, non-sensitive identity claim set on
  the client, user id, a handful of role flags, an expiry, and store any
  larger or more sensitive data server-side, referenced by an opaque ID
  embedded in the client-held claims. This variant deliberately blurs the
  line with Database Session State, and doing so on purpose, with the
  boundary decided per field rather than left implicit, is itself sound
  engineering judgement rather than an anti-pattern.

## 9. Known production uses

- **Ruby on Rails**, in every application using the framework's default
  configuration, stores the entire session hash in a signed, and since Rails
  4 encrypted by default, cookie via `ActionDispatch::Session::CookieStore`,
  documented in the *Ruby on Rails Security Guide*, "Session Storage" section,
  Rails core team, verified 2026-08-02. This is one of the highest-volume
  real-world deployments of the pure client-side variant of the pattern,
  because it is the framework's out-of-the-box behavior rather than an opt-in
  choice.
- **express-session with `connect-redis` versus its `MemoryStore` default**
  illustrates the pattern from the opposite direction, by showing what teams
  reach for instead of pure Client Session State at scale. The express-session
  README states of its bundled default store, "The default server-side
  session storage, `MemoryStore`, is purposely not designed for a production
  environment. It will leak memory under most conditions, does not scale past
  a single process, and is meant for debugging and developing" (TJ Holowaychuk
  and the Express.js contributors, *express-session*,
  https://github.com/expressjs/session, README, verified 2026-08-02). Teams
  hitting that limitation choose between adding a shared server-side store,
  Server Session State via `connect-redis` and similar, or moving the
  session onto the client entirely, this pattern, and the README's own list
  of compatible session stores documents that this exact fork in the road is
  a routine production decision, not a hypothetical one.
- **Django's `signed_cookies` session engine** ships as one of four
  first-class, documented backends in a framework used across a very large
  share of production Python web applications. The Django documentation
  names it explicitly and documents its trade-off in the same breath, "The
  session data is signed but not encrypted... When using the cookies backend
  the session data can be read by the client" (Django Software Foundation,
  *Django documentation, How to use sessions*, verified 2026-08-02).
- **OAuth 2.0 bearer tokens and OpenID Connect ID tokens**, most commonly
  implemented as JWTs, are the mechanism by which one deployed service most
  often authenticates a caller's identity to another deployed service
  without either service holding a shared session store, standardized in RFC
  6750, bearer token usage, and RFC 7519, JWT, both IETF specifications
  implemented by essentially every major identity provider, Auth0, Okta,
  AWS Cognito, and Microsoft Entra ID among them, and consumed by API
  gateways across the industry as the default mechanism for stateless,
  horizontally scaled service-to-service and browser-to-API authentication.
- **ASP.NET Core's session cookie**, while the framework's broader "Session
  state" feature is a hybrid, values cached server-side, only the identifier
  and encryption travel to the client, per Microsoft's own documentation
  quoted in dimension 8, documents Client Session State by name as one of
  the recognized approaches to persisting app state, listing it in its
  "Approaches to preserve state" comparison table (Microsoft, *Session and
  app state in ASP.NET Core*, verified 2026-08-02), and its plain cookie
  mechanism, data placed directly in a cookie with no server-side
  counterpart, is documented as a valid, simpler alternative for small
  amounts of data.

## 10. Consequences

Positive:

- Server processes become stateless with respect to session data, which
  removes the need for sticky sessions, session replication, or a shared
  session store, simplifying horizontal scaling and rolling deployments,
  because any instance can serve any request.
- No session storage infrastructure to provision, monitor, back up, or keep
  available, the store's availability guarantee becomes irrelevant because
  there is no store.
- Session lookup cost becomes cryptographic verification, fast, local, and
  deterministic, rather than a network round trip to a session store, which
  removes a class of latency and a class of failure mode, the session store
  being unreachable, entirely.
- The format, when a standard like JWT is used, is verifiable by any party
  holding the correct key, independent of language or framework, which is
  what makes it viable across service and even organizational boundaries.

Negative:

- Data placed on the client is visible to the client unless specifically
  encrypted, and signing alone, the more common choice because it is cheaper
  and simpler than encryption plus key management, only prevents tampering,
  it does not prevent reading, a distinction Django's documentation states
  outright and that is the single most common source of real incidents
  attributed to this pattern.
- Revocation before natural expiry requires additional server-side state, a
  deny list, a version number checked against a stored minimum, or similar,
  which reintroduces exactly the server-side coordination the pattern exists
  to avoid, for the subset of use cases that need it.
- Payload size is bounded by transport limits. RFC 6265 documents practical
  cookie size limits that most browsers enforce around 4096 bytes, and every
  byte of session data is now also a byte of bandwidth on every single
  request that carries it, which compounds at scale in a way server-side
  storage does not.
- Session data staleness is inherent. Because the client holds a snapshot
  taken at issuance time, any change to the underlying truth, a role
  revoked, a permission changed, is not reflected until the token is
  reissued or expires, a lag that server-held session state, refreshed on
  every read, does not have.
- Concurrent updates from the same session, described in dimension 7, have
  no natural conflict detection. The last write the client happens to apply
  wins silently.

## 11. Failure modes and misuse

- **Symptom, users report seeing stale roles or permissions after an
  administrator changed their access.**
  Cause. The client is holding a still-valid, signed token issued before the
  permission change, and the server trusts the claims embedded in the token
  rather than re-checking authoritative state, because that re-check is
  exactly the server-side lookup the pattern was adopted to avoid.
  Fix. Shorten token lifetimes so staleness windows are bounded and
  acceptable, or move authorization-sensitive claims to a server-side check
  triggered by a lightweight reference in the token, a version number or a
  user ID looked up against current state, rather than trusting the claim
  value itself for anything security-critical.

- **Symptom, a user who was logged out, or whose account was disabled,
  continues to successfully make authenticated requests for some time
  afterward.**
  Cause. The pattern has no built-in revocation. A token remains valid to any
  verifier holding the signing key until its embedded expiry passes, and
  "log out" client-side, deleting the local copy, does nothing to a copy an
  attacker may already have captured.
  Fix. Keep token lifetimes short and pair them with a refresh mechanism that
  checks a server-side revocation list at refresh time, accepting that true
  instant revocation reintroduces some server-side state by design. Document
  this trade-off explicitly rather than presenting the system as offering
  instant logout when it does not.

- **Symptom, session data silently reverts to an older value after two
  requests fire close together, for example a shopping cart loses an item
  that was recently added.**
  Cause. The lost-update race described in dimension 7. Two requests each
  read the same starting token, each compute an update independently, and
  each write back a new token, and whichever response the browser processes
  last overwrites the other's change with no conflict detected.
  Fix. Keep client-held session data limited to values that are safe to
  overwrite wholesale, a single current step in a wizard, a single active
  selection, and move anything that accumulates from multiple independent
  writes, a cart with many items, a document with many edits, to
  server-side storage referenced by an ID, where a database transaction can
  serialize the writes.

- **Symptom, a security review flags that sensitive data, an email address,
  an internal user ID, a full name, is readable by simply base64-decoding
  the session cookie or bearer token.**
  Cause. The team implemented signing, integrity, and mistook it for
  encryption, confidentiality. JWTs in particular are commonly
  base64url-encoded but not encrypted by default, and base64 is trivially
  reversible, not a cipher.
  Fix. Classify every claim placed in the token as either non-sensitive,
  safe to leave readable such as a random session ID or a public username,
  or sensitive, must be encrypted such as an email address or an internal
  database ID that should not be exposed, and encrypt the payload, JWE, or
  application-level symmetric encryption before placing data in a cookie,
  whenever any sensitive field is present, per the pattern the ASP.NET Core
  session cookie's `IDataProtector` usage demonstrates.

- **Symptom, cookies silently fail to be sent on cross-site requests that the
  application expected to work, an embedded widget or a redirect flow from a
  payment provider, or, in the opposite direction, a CSRF vulnerability is
  found because a
  session cookie is sent on cross-site requests the application did not
  expect.**
  Cause. The `SameSite` cookie attribute was left at its browser default or
  set incorrectly for the application's actual cross-site usage pattern.
  OWASP's Session Management Cheat Sheet states the requirement directly,
  "Session cookies must explicitly set `SameSite=Strict` (preferred) or
  `SameSite=Lax`" (OWASP Foundation, *Session Management Cheat Sheet*,
  https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html,
  verified 2026-08-02).
  Fix. Choose the `SameSite` value deliberately based on whether the
  application legitimately needs cross-site cookie delivery, rare, and when
  it does, `SameSite=None` requires the `Secure` attribute as well, and test
  the exact cross-site flows the application depends on, not only the
  same-site happy path.

- **Symptom, a penetration test finds that swapping a signed cookie captured
  from user A onto a request as user B, before A's cookie expires, still
  authenticates as A on a different machine, and the application never
  detected the reuse.**
  Cause. Bearer-style client-held tokens are, per RFC 6750's own definition,
  usable by "any party in possession" of them with no proof of origin.
  Nothing about the pattern itself binds a token to the specific browser,
  network, or machine that first received it, unless the application adds
  that binding separately.
  Fix. This is frequently an accepted trade-off rather than a defect,
  because binding a token to a device sacrifices some of the pattern's
  simplicity, but where session hijacking risk is high, pair the token with
  additional signals, an IP or device fingerprint checked at verification
  time, a short expiry paired with refresh-token rotation, understanding
  that these are mitigations, not a structural fix to the bearer property.

## 12. Trade-off matrix

| Force | Client Session State | Server Session State | Database Session State |
|---|---|---|---|
| Server statelessness / horizontal scaling | High. Any instance verifies any token, no sticky routing needed. | Low. Data lives in one process's memory; needs sticky sessions or replication. | High. Any instance can query the shared database or cache. |
| Instant server-side revocation | Low, by default. Requires an added deny list or short expiry to approximate it. | High. Deleting the in-memory entry ends the session immediately. | High. Deleting the row ends the session immediately. |
| Confidentiality of session data | Depends entirely on encryption being explicitly added; signing alone leaves data readable to the holder (Django docs, dimension 3). | High. Data never leaves the server process. | High. Data never leaves the server-managed store. |
| Server-side storage / operations cost | None. No session store to provision or keep available. | Moderate. In-process memory, cheap but not durable or shared. | High. A database or distributed cache must be provisioned, scaled, and kept available. |
| Per-request bandwidth cost | Proportional to session size; every request carries the full state. | None beyond a small session identifier cookie. | None beyond a small session identifier cookie. |
| Payload size cap | Low; practical cookie/header limits (RFC 6265 documents around 4096 bytes for cookies). | High; bounded only by process memory. | High; bounded only by the store's capacity. |
| Cross-service verifiability | High, when a standard format like JWT is used; any holder of the verification key can validate independently. | Low; the session only exists inside the one process that created it. | Moderate; requires network access to the shared store, but any authorized service can query it. |
| Freshness of authorization data | Low; the client holds a snapshot taken at issuance until reissue or expiry. | High; every request reads current in-memory state. | High; every request can read current row state. |
| Resilience to server restart | High; a restarted, stateless server needs no recovery step for existing sessions, they simply keep validating. | Low, unless the store is external to the process; a naive in-memory store loses all sessions on restart. | High; the store survives independently of any one server process. |

## 13. Related and incompatible patterns

Client Session State's two direct siblings, Server Session State and
Database Session State, are not competitors so much as two other answers to
the same question, where does the data live between requests, and all three
are frequently combined within one application on a per-field basis. An
authentication claim on the client, a shopping cart reference in a
server-side cache, and a completed order in the database is the
split-payload variant described in dimension 8, applied at the application
level. Data Transfer Object is closely related at the implementation level,
because the serialized session payload, whatever transport carries it, is
functionally a DTO, a plain, transport-shaped bundle of fields with no
behavior, assembled on the server before it crosses the process boundary and
disassembled on the way back. Identity Field is related where a session's
client-held claims include a reference to a domain entity's identity,
letting the server re-fetch the full entity from its identity rather than
trusting a stale copy of its fields, which is the mechanism that mitigates
the staleness failure mode in dimension 11. Remote Facade is related in
service-to-service contexts, because the bearer token that authenticates a
call to a remote facade is itself an instance of this pattern, carrying the
caller's identity across the process boundary the facade exists to cross.

Client Session State is not incompatible with any other pattern in the strict
sense of the two being unable to coexist, but it actively works against a
design goal of instant, centrally enforced session termination, a feature
some regulated industries require, and a team that has committed to that
requirement should treat pure Client Session State as unsuitable for the
sessions that requirement covers, reaching instead for Server Session State
or Database Session State for those specific sessions, while still using
Client Session State elsewhere in the same system where it fits.

## 14. Refactoring path in and out

Introducing Client Session State into an application that currently uses
server-held sessions.

1. Inventory every field the current session actually holds and classify
   each as small and safe to expose (an ID, a role name), small but
   sensitive (an email, an internal numeric ID), or large (a cart with many
   items, a document draft). This inventory is the single most important
   step, because it determines what moves and what stays.
2. For the small and safe fields, design the claim shape, choosing a
   standardized format, JWT, if the token will ever be verified outside the
   issuing process, or an application-specific signed format if it will not.
3. Build the encoder and verifier as isolated, independently testable
   components, see dimension 15 for how to test them directly, without HTTP.
4. Cut the application over incrementally, field by field if the framework
   allows it, verifying at each step that removing a field from the
   server-side session and adding it to the client-held claims does not
   change observed behavior, using a feature flag to allow instant rollback.
5. For any sensitive field identified in step 1, add encryption, not only
   signing, before that field moves.
6. For any large field identified in step 1, do not move it. Instead replace
   its server-side session-key lookup with a proper identifier plus a
   dedicated store lookup. This is effectively a partial migration toward
   Database Session State for only that field, which is often the correct
   end state rather than a stopping point on the way to full Client Session
   State.
7. Add expiry handling and, if any revocation requirement exists, a deny-list
   check at verification time, before removing the old server-side session
   path entirely.

Removing Client Session State, moving back toward server-held state,
typically happens for one of two reasons. A revocation requirement emerged
that the pattern cannot satisfy without added infrastructure, or the session
payload grew past the point where shipping it on every request is
acceptable. The path out mirrors the path in. Inventory what the client
currently holds, stand up a server-side store, add a session identifier
cookie, small, safe to leave client-held even after the refactor, move the
data behind that identifier, and cut over incrementally with the two paths
running in parallel behind a flag until the server-side path is proven
correct in production.

## 15. Testing and verification

What becomes easy is that the encoder and verifier are pure functions of
their input, given a claims object and a key, produce a token, given a token
and a key, produce a claims object or an error, so they are trivially unit
testable with no HTTP layer, no database, and no test doubles beyond a fixed
signing key for the test environment. This is a genuine advantage over
Server Session State and Database Session State, where testing session
behavior usually requires either a real store or a fake one that has to
correctly emulate expiry and concurrency semantics.

What becomes harder is that end-to-end tests exercising expiry timing, does
the system correctly reject a token one second past its `exp` claim, does
clock skew between issuer and verifier cause false rejections, need to
either control the clock deterministically inside the test, freezing or
advancing a fake clock rather than sleeping in real time, or generate tokens
with already-expired `exp` claims directly, bypassing the normal issuance
flow. Tests that need to prove revocation works correctly must exercise
whatever deny-list mechanism was added, since the base pattern offers
nothing to test here on its own. Tests for the lost-update race in dimension
7 are notoriously easy to skip and worth writing deliberately. Issue two
concurrent update-session requests from the same starting token and assert
that the application's behavior under that race is the behavior the team
actually intended, last-write-wins accepted, or a rejection when both
responses cannot be reconciled, rather than leaving the outcome
undocumented.

The verifier specifically needs adversarial test cases, not only happy-path
ones. A token signed with a different key must reject. A token with an
altered payload but the original signature must reject. A token using the
`alg=none` header value must reject, a well-documented JWT library
vulnerability class where implementations that trust the algorithm named
inside the token itself can be tricked into skipping verification entirely,
so a correct verifier pins the expected algorithm server-side and never
trusts the token's own claim about which algorithm was used. A token whose
expiry has passed by exactly one second is a boundary case that separates a
correct less-than-or-equal comparison from a working implementation from one
that lets a barely-expired token slip through.

## 16. Observability signals

A healthy deployment of this pattern shows a low, stable rate of
verification failures relative to total requests, because most verification
failures in steady state are simply naturally expired tokens on returning
users, not attacks or bugs. Track verification failures as a rate broken down
by reason, signature mismatch, expired, malformed, or wrong audience or
issuer claim, because each reason implies a different root cause. A spike in
signature mismatches after a deployment usually means a key rotation was not
propagated to every verifying instance simultaneously. A spike in
wrong-issuer failures usually means a misconfigured client pointed at the
wrong identity provider environment, staging tokens presented to
production, or the reverse.

Log, at minimum on the verifier side, the outcome of every verification,
accepted or rejected, with the rejection reason, never the token's own
sensitive claim values in plaintext logs, and on the issuer side, the volume
and average size of tokens issued, because payload size creep is a slow,
easy-to-miss failure mode that shows up first as rising average request
bandwidth rather than as an obvious error. A dashboard tracking token size
distribution over time catches the problem of someone adding one more field
to the claims and nobody noticing the cookie is now twice as large, before it
becomes a hard 4096-byte rejection in production.

Where a deny list exists to approximate revocation, its size and lookup
latency are their own signals worth tracking separately, because an unbounded
deny list that is never pruned of entries whose underlying token has already
naturally expired quietly reintroduces the storage growth problem the pattern
was chosen to avoid, with extra steps added.

## 17. Security and privacy implications

This pattern places application state on infrastructure the server does not
control, which is the entire reason it needs its own dedicated security
section rather than inheriting the same posture as server-held state. Three
concerns matter most.

Confidentiality. Unless the payload is encrypted, anything placed in a
client-held token is readable by whoever holds it, which includes the
legitimate user, anyone who gains access to that user's device or browser
storage, and any network intermediary if the transport is not exclusively
HTTPS. RFC 6265's own cookie attributes, `Secure`, send only over an
encrypted connection, and `HttpOnly`, deny JavaScript access to the cookie,
mitigating theft via cross-site scripting, are not defaults, they must be
set explicitly by the application. OWASP's Session Management Cheat Sheet
documents both as required controls, and describes `HttpOnly` as an
attribute that "instructs web browsers not to allow scripts... an ability to
access the cookies via the DOM `document.cookie` object," directly
mitigating token theft through an XSS vulnerability elsewhere in the same
application (OWASP Foundation, *Session Management Cheat Sheet*, verified
2026-08-02).

Integrity. A signature, an HMAC or an asymmetric signature over the payload,
is what makes the client-held data trustworthy at all. Without one, the
client could simply edit the payload before sending it back, grant itself an
admin role, extend its own expiry, and the server would have no way to
detect the tampering. OWASP's entropy requirement, that "session identifiers
must have at least 64 bits of entropy to prevent brute-force session
guessing attacks" (OWASP, same cheat sheet), applies most directly to the
identifier half of session state, but the same logic extends to signing
keys, which must be generated with cryptographically secure randomness and
of sufficient length for the chosen algorithm.

Revocability and privacy retention. Because a stateless client-held session
cannot be forcibly deleted server-side, right-to-be-forgotten and similar
data-subject deletion requirements are harder to satisfy for any personal
data embedded in a long-lived token. The practical mitigation is keeping
personal data out of the token entirely, referencing it by ID instead per
the split-payload variant, so that deleting the server-side record the ID
points to is sufficient, and keeping token lifetimes short enough that any
data that does leak through a token expires promptly on its own regardless
of server-side action. Session fixation, where an attacker forces a victim
to use an attacker-known session identifier, is mitigated per OWASP guidance
by regenerating the session, or issuing a fresh signed token, at every
privilege level change, most importantly at login. The cheat sheet states,
"The session ID must be renewed or regenerated by the web application after
any privilege level change."

## 18. References

- Fowler, Martin. *Patterns of Enterprise Application Architecture*.
  Addison-Wesley, 2002, Base Patterns chapter, Client Session State.
- Fowler, Martin. "Client Session State" pattern summary.
  https://martinfowler.com/eaaCatalog/clientSessionState.html, verified
  2026-08-02.
- Barth, A. RFC 6265, *HTTP State Management Mechanism*. IETF, April 2011.
  https://datatracker.ietf.org/doc/html/rfc6265, verified 2026-08-02.
- Jones, M., Bradley, J., Sakimura, N. RFC 7519, *JSON Web Token (JWT)*.
  IETF, May 2015. https://datatracker.ietf.org/doc/html/rfc7519, verified
  2026-08-02.
- Jones, M., Hardt, D. RFC 6750, *The OAuth 2.0 Authorization Framework,
  Bearer Token Usage*. IETF, October 2012.
  https://datatracker.ietf.org/doc/html/rfc6750, verified 2026-08-02.
- OWASP Foundation. *Session Management Cheat Sheet*.
  https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html,
  verified 2026-08-02.
- Microsoft. "Session and app state in ASP.NET Core."
  https://learn.microsoft.com/en-us/aspnet/core/fundamentals/app-state,
  verified 2026-08-02.
- Django Software Foundation. "How to use sessions." Django documentation,
  version 5.2. https://docs.djangoproject.com/en/5.2/topics/http/sessions/,
  verified 2026-08-02.
- Rails core team. "Security" guide, "Sessions" and "Session Storage"
  sections. Ruby on Rails Guides. https://guides.rubyonrails.org/security.html,
  verified 2026-08-02.
- Holowaychuk, TJ, and the Express.js contributors. "express-session"
  README. https://github.com/expressjs/session, verified 2026-08-02.

## Code examples

### TypeScript (Node.js, no framework, HMAC-signed session cookie)

```typescript
import { createHmac, timingSafeEqual } from "node:crypto";

interface SessionClaims {
  userId: string;
  roles: string[];
  exp: number;
}

const SECRET = "test-signing-key-do-not-use-in-production";

function base64url(input: Buffer): string {
  return input.toString("base64url");
}

function sign(payload: string): string {
  return base64url(createHmac("sha256", SECRET).update(payload).digest());
}

function encodeSession(claims: SessionClaims): string {
  const payload = base64url(Buffer.from(JSON.stringify(claims)));
  const signature = sign(payload);
  return `${payload}.${signature}`;
}

type VerifyResult =
  | { ok: true; claims: SessionClaims }
  | { ok: false; reason: "malformed" | "bad_signature" | "expired" };

function verifySession(token: string): VerifyResult {
  const parts = token.split(".");
  if (parts.length !== 2) {
    return { ok: false, reason: "malformed" };
  }
  const [payload, signature] = parts;
  const expected = sign(payload);
  const a = Buffer.from(signature);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) {
    return { ok: false, reason: "bad_signature" };
  }
  const claims: SessionClaims = JSON.parse(
    Buffer.from(payload, "base64url").toString("utf8"),
  );
  if (claims.exp < Math.floor(Date.now() / 1000)) {
    return { ok: false, reason: "expired" };
  }
  return { ok: true, claims };
}

function main(): void {
  const claims: SessionClaims = {
    userId: "user-42",
    roles: ["reader"],
    exp: Math.floor(Date.now() / 1000) + 3600,
  };

  const token = encodeSession(claims);
  console.log("issued token:", token);

  const verified = verifySession(token);
  if (verified.ok) {
    console.log("verified claims:", verified.claims);
  } else {
    console.log("rejected:", verified.reason);
  }

  const tampered = token.slice(0, -1) + (token.endsWith("A") ? "B" : "A");
  const tamperedResult = verifySession(tampered);
  console.log("tampered token result:", tamperedResult);
}

main();
```

### Python (dataclass session, HMAC-signed, expiry checked)

```python
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, asdict

SECRET = b"test-signing-key-do-not-use-in-production"


@dataclass
class SessionClaims:
    user_id: str
    roles: list[str]
    exp: int


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(payload: str) -> str:
    digest = hmac.new(SECRET, payload.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def encode_session(claims: SessionClaims) -> str:
    payload = _b64url_encode(json.dumps(asdict(claims)).encode("utf-8"))
    signature = _sign(payload)
    return f"{payload}.{signature}"


class VerifyError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def verify_session(token: str) -> SessionClaims:
    parts = token.split(".")
    if len(parts) != 2:
        raise VerifyError("malformed")
    payload, signature = parts
    expected = _sign(payload)
    if not hmac.compare_digest(signature, expected):
        raise VerifyError("bad_signature")
    data = json.loads(_b64url_decode(payload))
    claims = SessionClaims(**data)
    if claims.exp < int(time.time()):
        raise VerifyError("expired")
    return claims


def main() -> None:
    claims = SessionClaims(user_id="user-42", roles=["reader"], exp=int(time.time()) + 3600)
    token = encode_session(claims)
    print("issued token:", token)

    verified = verify_session(token)
    print("verified claims:", verified)

    tampered = token[:-1] + ("B" if token.endswith("A") else "A")
    try:
        verify_session(tampered)
    except VerifyError as e:
        print("tampered token rejected:", e.reason)


if __name__ == "__main__":
    main()
```

### Go (HMAC-signed session token, standard library only)

```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

var secret = []byte("test-signing-key-do-not-use-in-production")

type SessionClaims struct {
	UserID string   `json:"user_id"`
	Roles  []string `json:"roles"`
	Exp    int64    `json:"exp"`
}

var (
	ErrMalformed    = errors.New("malformed token")
	ErrBadSignature = errors.New("bad signature")
	ErrExpired      = errors.New("session expired")
)

func sign(payload string) string {
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte(payload))
	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}

func encodeSession(c SessionClaims) (string, error) {
	body, err := json.Marshal(c)
	if err != nil {
		return "", err
	}
	payload := base64.RawURLEncoding.EncodeToString(body)
	return payload + "." + sign(payload), nil
}

func verifySession(token string) (SessionClaims, error) {
	var claims SessionClaims

	dot := -1
	for i, r := range token {
		if r == '.' {
			dot = i
			break
		}
	}
	if dot < 0 {
		return claims, ErrMalformed
	}
	payload := token[:dot]
	signature := token[dot+1:]

	expected := sign(payload)
	if !hmac.Equal([]byte(signature), []byte(expected)) {
		return claims, ErrBadSignature
	}

	body, err := base64.RawURLEncoding.DecodeString(payload)
	if err != nil {
		return claims, ErrMalformed
	}
	if err := json.Unmarshal(body, &claims); err != nil {
		return claims, ErrMalformed
	}
	if claims.Exp < time.Now().Unix() {
		return claims, ErrExpired
	}
	return claims, nil
}

func main() {
	claims := SessionClaims{
		UserID: "user-42",
		Roles:  []string{"reader"},
		Exp:    time.Now().Add(time.Hour).Unix(),
	}

	token, err := encodeSession(claims)
	if err != nil {
		panic(err)
	}
	fmt.Println("issued token:", token)

	verified, err := verifySession(token)
	if err != nil {
		fmt.Println("rejected:", err)
	} else {
		fmt.Printf("verified claims: %+v\n", verified)
	}

	tampered := token[:len(token)-1] + "X"
	if _, err := verifySession(tampered); err != nil {
		fmt.Println("tampered token rejected:", err)
	}
}
```

Java, Rust, and Kotlin are not included as separate samples here. The pattern
translates directly, an HMAC over a serialized payload, verified with a
constant-time comparison, checked against an expiry claim, with no
language-specific idiom that changes its shape the way, for example, a
closure changes Strategy. Three languages across two runtime styles,
event-loop JavaScript-family and compiled statically-typed Go, plus
dynamically-typed Python, is sufficient to show the pattern is not tied to
any one runtime model, and adding a fourth nearly identical HMAC
implementation would not add new information.
